import logging

from scipy.stats import mannwhitneyu

from .config import (
    BASELINE_WINDOW_MINUTES,
    CURRENT_WINDOW_MINUTES,
    DEFAULT_P95_THRESHOLD,
    DEFAULT_P_VALUE,
    MIN_SAMPLES,
)
from .queries import (
    PERCENTILE_QUERY,
    RAW_SAMPLES_QUERY,
    PG_THRESHOLDS_QUERY,
    PG_INSERT_REGRESSION,
)

log = logging.getLogger(__name__)


def load_thresholds(pg_conn) -> dict:
    """
    Returns a dict keyed by (project_id, metric_id, screen_name) ->
    p95_threshold (float). screen_name may be None for project-wide rules.
    """
    thresholds: dict = {}
    try:
        with pg_conn.cursor() as cur:
            cur.execute(PG_THRESHOLDS_QUERY)
            for project_id, metric_id, screen_name, value in cur.fetchall():
                thresholds[(project_id, metric_id, screen_name)] = value
        log.info("Loaded %d threshold overrides from Postgres.", len(thresholds))
    except Exception as exc:
        log.warning("Could not load thresholds: %s - using defaults.", exc)
    return thresholds


def resolve_threshold(
    thresholds: dict,
    project_id: str,
    metric_id: str,
    screen_name: str,
) -> float:
    """
    Threshold fallback chain:
      1. exact  (project_id, metric_id, screen_name)
      2. project-wide (project_id, metric_id, None)
      3. DEFAULT_P95_THRESHOLD
    """
    return (
        thresholds.get((project_id, metric_id, screen_name))
        or thresholds.get((project_id, metric_id, None))
        or DEFAULT_P95_THRESHOLD
    )


def fetch_raw_values(
    ch_client,
    project_id: str,
    metric_id: str,
    screen_name: str,
    device_cohort: str,
    window_minutes: int,
    extra_filter: str = "",
) -> list[float]:
    query = RAW_SAMPLES_QUERY.format(
        project_id=project_id,
        metric_id=metric_id,
        screen_name=screen_name,
        device_cohort=device_cohort,
        window_minutes=window_minutes,
        extra_filter=extra_filter,
    )
    return [row[0] for row in ch_client.query(query).result_rows]


def validate_regression(
    baseline_values: list[float],
    current_values: list[float],
    baseline_p95: float,
    current_p95: float,
    p95_threshold: float,
) -> tuple[bool, float | None]:
    """
    Step 1 - Rolling Window Percentile Shift:
        Flags if relative P95 degradation exceeds p95_threshold.
    Step 2 - Mann-Whitney U test:
        Statistically confirms the shift is not random noise (a = 0.05).

    Returns (is_regression, p_value).
    """
    delta = (current_p95 - baseline_p95) / baseline_p95
    if delta <= p95_threshold:
        return False, None

    if len(baseline_values) < MIN_SAMPLES or len(current_values) < MIN_SAMPLES:
        log.debug(
            "Percentile shift flagged but not enough samples "
            "(baseline=%d, current=%d) - skipping Mann-Whitney.",
            len(baseline_values),
            len(current_values),
        )
        return False, None

    _, p_value = mannwhitneyu(
        current_values, baseline_values, alternative="greater"
    )
    return (p_value < DEFAULT_P_VALUE), p_value


def save_regression(
    pg_conn,
    project_id: str,
    metric_id: str,
    screen_name: str,
    device_cohort: str,
    baseline_p95: float,
    current_p95: float,
    degradation_percent: float,
    p_value: float,
) -> None:
    with pg_conn.cursor() as cur:
        cur.execute(PG_INSERT_REGRESSION, (
            project_id,
            metric_id,
            screen_name,
            device_cohort,
            float(baseline_p95),
            float(current_p95),
            float(degradation_percent),
            float(p_value),
        ))
    pg_conn.commit()


def run_detection(ch_client, pg_conn) -> None:
    log.info("Starting regression detection run.")
    thresholds = load_thresholds(pg_conn)

    agg_rows = ch_client.query(PERCENTILE_QUERY).result_rows
    log.info("Aggregation returned %d cohort groups.", len(agg_rows))

    regressions_found = 0

    for row in agg_rows:
        (
            project_id, metric_id, screen_name, device_cohort,
            baseline_p95, current_p95, _baseline_count, _current_count,
        ) = row

        p95_thr = resolve_threshold(
            thresholds, project_id, metric_id, screen_name
        )
        delta_p95 = (current_p95 - baseline_p95) / baseline_p95

        log.debug(
            "%s | %s | %s | %s  baseline=%.2f current=%.2f delta=%.1f%%",
            project_id, metric_id, screen_name, device_cohort,
            baseline_p95, current_p95, delta_p95 * 100,
        )

        if delta_p95 <= p95_thr:
            continue

        log.info(
            "P95 shift %+.1f%% for %s / %s / %s / %s - fetching raw samples.",
            delta_p95 * 100, project_id, metric_id, screen_name, device_cohort,
        )

        baseline_values = fetch_raw_values(
            ch_client, project_id, metric_id, screen_name, device_cohort,
            window_minutes=BASELINE_WINDOW_MINUTES,
            extra_filter=(
                f"AND ts < now() - INTERVAL {CURRENT_WINDOW_MINUTES} MINUTE"
            ),
        )
        current_values = fetch_raw_values(
            ch_client, project_id, metric_id, screen_name, device_cohort,
            window_minutes=CURRENT_WINDOW_MINUTES,
        )

        is_regression, p_value = validate_regression(
            baseline_values, current_values,
            baseline_p95, current_p95,
            p95_thr,
        )

        if is_regression and p_value is not None:
            regressions_found += 1
            log.warning(
                "REGRESSION CONFIRMED: %s | %s | %s | %s  "
                "delta_p95=%.1f%%  p_value=%.4f",
                project_id, metric_id, screen_name, device_cohort,
                delta_p95 * 100, p_value,
            )
            save_regression(
                pg_conn,
                project_id=project_id,
                metric_id=metric_id,
                screen_name=screen_name,
                device_cohort=device_cohort,
                baseline_p95=baseline_p95,
                current_p95=current_p95,
                degradation_percent=delta_p95 * 100,
                p_value=p_value,
            )
        else:
            log.debug(
                "No regression for %s / %s / %s / %s (p_value=%s).",
                project_id, metric_id, screen_name, device_cohort, p_value,
            )

    log.info(
        "Run complete - %d regression(s) confirmed out of %d cohort groups.",
        regressions_found, len(agg_rows),
    )
