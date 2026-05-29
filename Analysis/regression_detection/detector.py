"""
Version-based regression detector.

Algorithm
---------
For every (project_id, metric_id, screen_name, device_cohort) group:

1. Pull mature versions (sample_count ≥ MIN_SAMPLES_PER_VERSION) from
   ClickHouse, together with their per-group medians.

2. Sort versions by version_code.  For each consecutive pair
   (baseline_version, current_version) compute the relative median shift:

       Δ = (median_current − median_baseline) / median_baseline

   If Δ > DEFAULT_MEDIAN_THRESHOLD → UPSERT an 'open' regression into
   Postgres (updates stats if the regression already exists and is open;
   leaves acknowledged/resolved rows untouched).

3. Auto-close — superseded:
   If a newer mature version exists for the same group, all open regressions
   whose current_version_code is less than that max are resolved as
   'superseded'.

4. Auto-close — rolled back:
   For open regressions older than ROLLED_BACK_QUIET_HOURS, check whether
   the current version still has any recent traffic in ClickHouse.  If not,
   resolve as 'rolled_back'.
"""

import logging
from collections import defaultdict

from .config import (
    DEFAULT_MEDIAN_THRESHOLD,
    MIN_SAMPLES_PER_VERSION,
    ROLLED_BACK_QUIET_HOURS,
)
from .queries import (
    MATURE_MEDIANS_QUERY,
    RECENT_TRAFFIC_QUERY,
    PG_UPSERT_REGRESSION,
    PG_OPEN_REGRESSIONS,
    PG_CLOSE_SUPERSEDED,
    PG_CLOSE_ROLLED_BACK,
)

log = logging.getLogger(__name__)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _fetch_mature_medians(ch_client) -> dict:
    """
    Query ClickHouse for all (group, version) combinations that have at least
    MIN_SAMPLES_PER_VERSION data points.

    Returns a dict:
        (project_id, metric_id, screen_name, device_cohort)
            → sorted list of (version_code, version_name, median, count)
    """
    query = MATURE_MEDIANS_QUERY.format(min_samples=MIN_SAMPLES_PER_VERSION)
    rows = ch_client.query(query).result_rows

    groups: dict = defaultdict(list)
    for (project_id, metric_id, screen_name, device_cohort,
         version_code, version_name, med, cnt) in rows:
        key = (str(project_id), str(metric_id), str(screen_name), str(device_cohort))
        groups[key].append((int(version_code), str(version_name), float(med), int(cnt)))

    # Sort each group by version_code ascending (ClickHouse ORDER BY already
    # does this, but enforce it here for safety).
    for key in groups:
        groups[key].sort(key=lambda x: x[0])

    log.info(
        "ClickHouse: %d mature (group, version) entries across %d groups.",
        sum(len(v) for v in groups.values()),
        len(groups),
    )
    return groups


def _upsert_regression(pg_conn, project_id, metric_id, screen_name,
                       device_cohort, baseline_vc, baseline_vn,
                       current_vc, current_vn,
                       baseline_med, current_med, delta_pct,
                       baseline_cnt, current_cnt) -> None:
    with pg_conn.cursor() as cur:
        cur.execute(PG_UPSERT_REGRESSION, (
            project_id, metric_id, screen_name, device_cohort,
            baseline_vc, baseline_vn,
            current_vc, current_vn,
            baseline_med, current_med, delta_pct,
            baseline_cnt, current_cnt,
        ))
    pg_conn.commit()


# ── Detection pass ────────────────────────────────────────────────────────────

def _detect_regressions(ch_client, pg_conn, groups: dict) -> None:
    """
    Iterate all consecutive version pairs per group and UPSERT regressions
    when the median shift exceeds the threshold.
    """
    total_pairs = 0
    regressions_found = 0

    for (project_id, metric_id, screen_name, device_cohort), versions in groups.items():
        if len(versions) < 2:
            continue

        for i in range(len(versions) - 1):
            baseline_vc, baseline_vn, baseline_med, baseline_cnt = versions[i]
            current_vc,  current_vn,  current_med,  current_cnt  = versions[i + 1]
            total_pairs += 1

            if baseline_med <= 0:
                continue

            delta = (current_med - baseline_med) / baseline_med

            log.debug(
                "%s | %s | %s | %s  v%d→v%d  baseline=%.2f  current=%.2f  Δ=%.1f%%",
                project_id, metric_id, screen_name, device_cohort,
                baseline_vc, current_vc,
                baseline_med, current_med, delta * 100,
            )

            if delta > DEFAULT_MEDIAN_THRESHOLD:
                regressions_found += 1
                log.warning(
                    "REGRESSION: %s | %s | %s | %s  v%d→v%d  Δ=+%.1f%%",
                    project_id, metric_id, screen_name, device_cohort,
                    baseline_vc, current_vc, delta * 100,
                )
                _upsert_regression(
                    pg_conn,
                    project_id, metric_id, screen_name, device_cohort,
                    baseline_vc, baseline_vn,
                    current_vc,  current_vn,
                    baseline_med, current_med, round(delta * 100, 2),
                    baseline_cnt, current_cnt,
                )

    log.info(
        "Detection: %d regression(s) found out of %d consecutive version pairs.",
        regressions_found, total_pairs,
    )


# ── Auto-close: superseded ────────────────────────────────────────────────────

def _close_superseded(pg_conn, groups: dict) -> None:
    """
    For each group, find the latest mature version_code.  Any open regression
    in that group whose current_version_code is strictly less than that max is
    now superseded by a newer release.
    """
    closed = 0
    with pg_conn.cursor() as cur:
        for (project_id, metric_id, screen_name, device_cohort), versions in groups.items():
            if not versions:
                continue
            max_vc = versions[-1][0]   # already sorted ascending
            cur.execute(PG_CLOSE_SUPERSEDED, (
                project_id, metric_id, screen_name, device_cohort, max_vc,
            ))
            closed += cur.rowcount
    pg_conn.commit()
    if closed:
        log.info("Auto-closed %d regression(s) as superseded.", closed)


# ── Auto-close: rolled back ───────────────────────────────────────────────────

def _close_rolled_back(ch_client, pg_conn) -> None:
    """
    For every open regression that is older than ROLLED_BACK_QUIET_HOURS,
    check whether its current version still has recent ClickHouse traffic.
    If not, resolve it as 'rolled_back'.
    """
    with pg_conn.cursor() as cur:
        cur.execute(PG_OPEN_REGRESSIONS, (ROLLED_BACK_QUIET_HOURS,))
        open_regressions = cur.fetchall()

    if not open_regressions:
        return

    log.info(
        "Rolled-back check: %d open regression(s) older than %dh.",
        len(open_regressions), ROLLED_BACK_QUIET_HOURS,
    )

    closed = 0
    with pg_conn.cursor() as cur:
        for (reg_id, project_id, metric_id,
             screen_name, device_cohort, current_vc) in open_regressions:

            traffic_query = RECENT_TRAFFIC_QUERY.format(
                project_id=project_id,
                metric_id=metric_id,
                screen_name=screen_name,
                device_cohort=device_cohort,
                version_code=current_vc,
                quiet_hours=ROLLED_BACK_QUIET_HOURS,
            )
            result = ch_client.query(traffic_query).result_rows
            recent_count = result[0][0] if result else 0

            if recent_count == 0:
                cur.execute(PG_CLOSE_ROLLED_BACK, (reg_id,))
                closed += 1
                log.info(
                    "Auto-closed regression %s as rolled_back (v%d silent for %dh).",
                    reg_id, current_vc, ROLLED_BACK_QUIET_HOURS,
                )

    pg_conn.commit()
    if closed:
        log.info("Auto-closed %d regression(s) as rolled_back.", closed)


# ── Entry point ───────────────────────────────────────────────────────────────

def run_detection(ch_client, pg_conn) -> None:
    log.info("Starting regression detection run.")

    groups = _fetch_mature_medians(ch_client)

    if not groups:
        log.info("No mature versions found — skipping.")
        return

    _detect_regressions(ch_client, pg_conn, groups)
    _close_superseded(pg_conn, groups)
    _close_rolled_back(ch_client, pg_conn)

    log.info("Detection run complete.")
