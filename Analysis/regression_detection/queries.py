# ── ClickHouse ────────────────────────────────────────────────────────────────

# Returns one row per (project, metric, screen, cohort, version) that has at
# least {min_samples} data points.  Call with .format(min_samples=...).
MATURE_MEDIANS_QUERY = """
SELECT
    project_id,
    metric_id,
    screen_name,
    device_cohort,
    version_code,
    version_name,
    quantile(0.95)(value) AS p95,
    count()               AS cnt
FROM metric_records
WHERE metric_id IN {perceived_metrics}
GROUP BY
    project_id, metric_id, screen_name, device_cohort, version_code, version_name
HAVING cnt >= {min_samples}
ORDER BY
    project_id, metric_id, screen_name, device_cohort, version_code
"""

# ── PostgreSQL ────────────────────────────────────────────────────────────────

# Insert a new regression or refresh its statistics if it is still open.
PG_UPSERT_REGRESSION = """
INSERT INTO regressions (
    project_id, metric_id, screen_name, device_cohort,
    baseline_version_code, baseline_version_name,
    current_version_code,  current_version_name,
    baseline_p95, current_p95, degradation_percent,
    sample_count_baseline, sample_count_current,
    detected_at, status
) VALUES (
    %s, %s, %s, %s,
    %s, %s,
    %s, %s,
    %s, %s, %s,
    %s, %s,
    NOW(), 'open'
)
ON CONFLICT (project_id, metric_id, screen_name, device_cohort,
             baseline_version_code, current_version_code)
DO UPDATE SET
    baseline_p95          = EXCLUDED.baseline_p95,
    current_p95           = EXCLUDED.current_p95,
    degradation_percent   = EXCLUDED.degradation_percent,
    sample_count_baseline = EXCLUDED.sample_count_baseline,
    sample_count_current  = EXCLUDED.sample_count_current
WHERE regressions.status = 'open'
RETURNING (xmax = 0) AS inserted
"""

