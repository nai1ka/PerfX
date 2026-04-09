from .config import BASELINE_WINDOW_MINUTES, CURRENT_WINDOW_MINUTES

# ── ClickHouse ────────────────────────────────────────────────────────────────

PERCENTILE_QUERY = f"""
SELECT
    project_id,
    metric_id,
    screen_name,
    device_cohort,
    quantileIf(0.95)(value,
        ts >= now() - INTERVAL {BASELINE_WINDOW_MINUTES} MINUTE
        AND ts <  now() - INTERVAL {CURRENT_WINDOW_MINUTES} MINUTE
    ) AS baseline_p95,
    quantileIf(0.95)(value,
        ts >= now() - INTERVAL {CURRENT_WINDOW_MINUTES} MINUTE
    ) AS current_p95,
    countIf(
        ts >= now() - INTERVAL {BASELINE_WINDOW_MINUTES} MINUTE
        AND ts <  now() - INTERVAL {CURRENT_WINDOW_MINUTES} MINUTE
    ) AS baseline_count,
    countIf(
        ts >= now() - INTERVAL {CURRENT_WINDOW_MINUTES} MINUTE
    ) AS current_count
FROM metric_records
GROUP BY project_id, metric_id, screen_name, device_cohort
HAVING baseline_p95 > 0 AND current_p95 > 0
"""

RAW_SAMPLES_QUERY = """
SELECT value
FROM metric_records
WHERE
    project_id    = '{project_id}'
    AND metric_id     = '{metric_id}'
    AND screen_name   = '{screen_name}'
    AND device_cohort = '{device_cohort}'
    AND ts >= now() - INTERVAL {window_minutes} MINUTE
    {extra_filter}
ORDER BY ts
"""

# ── PostgreSQL ────────────────────────────────────────────────────────────────

PG_THRESHOLDS_QUERY = """
SELECT project_id::text, metric_id, screen_name, threshold_value
FROM thresholds
"""

PG_INSERT_REGRESSION = """
INSERT INTO regressions
    (project_id, metric_id, screen_name, device_cohort,
     baseline_p95, current_p95, degradation_percent, p_value)
VALUES
    (%s, %s, %s, %s, %s, %s, %s, %s)
"""
