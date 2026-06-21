"""
Version-based regression detector.

Algorithm
---------
For every (project_id, metric_id, screen_name, device_cohort) group:

1. Pull mature versions (sample_count ≥ MIN_SAMPLES_PER_VERSION) from
   ClickHouse, together with their per-group P95 values.

2. Sort versions by version_code.  For each consecutive pair
   (baseline_version, current_version) compute the relative P95 shift:

       Δ = (P95_current − P95_baseline) / P95_baseline

   If Δ > DEFAULT_P95_THRESHOLD → UPSERT an 'open' regression into
   Postgres (updates stats if the regression already exists and is open;
   leaves acknowledged/resolved rows untouched).
"""

import logging
import os
from collections import defaultdict
from typing import Optional

from .config import (
    DEFAULT_P95_THRESHOLD,
    MIN_SAMPLES_PER_VERSION,
    PERCEIVED_METRICS,
)
from .notifier import send_regression_alert
from .queries import (
    MATURE_MEDIANS_QUERY,
    PG_UPSERT_REGRESSION,
)

log = logging.getLogger(__name__)


def resolve_threshold() -> float:
    """Return the active regression threshold.

    Checks DETECTION_THRESHOLD_OVERRIDE env var first; falls back to
    DEFAULT_P95_THRESHOLD from config.  Used by E3 sensitivity sweep.
    """
    override = os.environ.get("DETECTION_THRESHOLD_OVERRIDE")
    if override is not None:
        try:
            return float(override)
        except ValueError:
            log.warning("Invalid DETECTION_THRESHOLD_OVERRIDE=%r; using default.", override)
    return DEFAULT_P95_THRESHOLD


# ── Helpers ───────────────────────────────────────────────────────────────────

def _fetch_mature_medians(ch_client) -> dict:
    """
    Query ClickHouse for all (group, version) combinations that have at least
    MIN_SAMPLES_PER_VERSION data points.

    Returns a dict:
        (project_id, metric_id, screen_name, device_cohort)
            → sorted list of (version_code, version_name, p95, count)
    """
    query = MATURE_MEDIANS_QUERY.format(
        min_samples=MIN_SAMPLES_PER_VERSION,
        perceived_metrics=PERCEIVED_METRICS,
    )
    rows = ch_client.query(query).result_rows

    groups: dict = defaultdict(list)
    for (project_id, metric_id, screen_name, device_cohort,
         version_code, version_name, p95, cnt) in rows:
        key = (str(project_id), str(metric_id), str(screen_name), str(device_cohort))
        groups[key].append((int(version_code), str(version_name), float(p95), int(cnt)))

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
                       baseline_cnt, current_cnt) -> bool:
    """Returns True if this was a new regression (not an update of existing)."""
    with pg_conn.cursor() as cur:
        cur.execute(PG_UPSERT_REGRESSION, (
            project_id, metric_id, screen_name, device_cohort,
            baseline_vc, baseline_vn,
            current_vc, current_vn,
            baseline_med, current_med, delta_pct,
            baseline_cnt, current_cnt,
        ))
        row = cur.fetchone()
    pg_conn.commit()
    return bool(row and row[0])


# ── Detection pass ────────────────────────────────────────────────────────────

def _detect_regressions(ch_client, pg_conn, groups: dict,
                        dry_run: bool = False) -> Optional[list]:
    """
    Iterate all consecutive version pairs per group and UPSERT regressions
    when the median shift exceeds the threshold.

    When dry_run=True, skip all Postgres writes and return a list of decision
    dicts instead of None.
    """
    threshold = resolve_threshold()
    total_pairs = 0
    regressions_found = 0
    decisions = [] if dry_run else None

    for (project_id, metric_id, screen_name, device_cohort), versions in groups.items():
        if len(versions) < 2:
            continue

        for i in range(len(versions) - 1):
            baseline_vc, baseline_vn, baseline_p95, baseline_cnt = versions[i]
            current_vc,  current_vn,  current_p95,  current_cnt  = versions[i + 1]
            total_pairs += 1

            if baseline_p95 <= 0:
                continue

            delta = (current_p95 - baseline_p95) / baseline_p95
            would_alert = delta > threshold

            log.debug(
                "%s | %s | %s | %s  v%d→v%d  baseline_p95=%.2f  current_p95=%.2f  Δ=%.1f%%",
                project_id, metric_id, screen_name, device_cohort,
                baseline_vc, current_vc,
                baseline_p95, current_p95, delta * 100,
            )

            if dry_run:
                decisions.append({
                    "group_key": f"{project_id}|{metric_id}|{screen_name}|{device_cohort}",
                    "project_id": project_id,
                    "metric_id": metric_id,
                    "screen_name": screen_name,
                    "device_cohort": device_cohort,
                    "baseline_version_code": baseline_vc,
                    "current_version_code": current_vc,
                    "baseline_p95": round(baseline_p95, 4),
                    "current_p95": round(current_p95, 4),
                    "delta_pct": round(delta * 100, 2),
                    "threshold_used": threshold,
                    "would_alert": would_alert,
                })
                if would_alert:
                    regressions_found += 1
            elif would_alert:
                regressions_found += 1
                log.warning(
                    "REGRESSION: %s | %s | %s | %s  v%d→v%d  Δ=+%.1f%%",
                    project_id, metric_id, screen_name, device_cohort,
                    baseline_vc, current_vc, delta * 100,
                )
                is_new = _upsert_regression(
                    pg_conn,
                    project_id, metric_id, screen_name, device_cohort,
                    baseline_vc, baseline_vn,
                    current_vc,  current_vn,
                    baseline_p95, current_p95, round(delta * 100, 2),
                    baseline_cnt, current_cnt,
                )
                if is_new:
                    send_regression_alert(
                        pg_conn,
                        project_id, metric_id, screen_name, device_cohort,
                        baseline_vn, current_vn,
                        baseline_p95, current_p95, round(delta * 100, 2),
                    )

    log.info(
        "Detection: %d regression(s) found out of %d consecutive version pairs.",
        regressions_found, total_pairs,
    )
    return decisions


# ── Entry point ───────────────────────────────────────────────────────────────

def run_detection(ch_client, pg_conn, dry_run: bool = False) -> Optional[list]:
    """Run one detection pass.

    In dry_run mode pg_conn may be None; no Postgres writes occur and a list of
    decision dicts is returned (suitable for JSON serialisation).
    """
    log.info("Starting regression detection run (dry_run=%s).", dry_run)

    groups = _fetch_mature_medians(ch_client)

    if not groups:
        log.info("No mature versions found — skipping.")
        return [] if dry_run else None

    decisions = _detect_regressions(ch_client, pg_conn, groups, dry_run=dry_run)

    log.info("Detection run complete.")
    return decisions
