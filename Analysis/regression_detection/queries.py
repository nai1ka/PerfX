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
    median(value) AS med,
    count()       AS cnt
FROM metric_records
GROUP BY
    project_id, metric_id, screen_name, device_cohort, version_code, version_name
HAVING cnt >= {min_samples}
ORDER BY
    project_id, metric_id, screen_name, device_cohort, version_code
"""

# Check whether a specific (group, version) still has recent traffic.
# Call with .format(project_id=..., metric_id=..., screen_name=...,
#                   device_cohort=..., version_code=..., quiet_hours=...).
RECENT_TRAFFIC_QUERY = """
SELECT count() AS cnt
FROM metric_records
WHERE
    project_id    = '{project_id}'
    AND metric_id     = '{metric_id}'
    AND screen_name   = '{screen_name}'
    AND device_cohort = '{device_cohort}'
    AND version_code  = {version_code}
    AND ts >= now() - INTERVAL {quiet_hours} HOUR
"""

# ── PostgreSQL ────────────────────────────────────────────────────────────────

# Insert a new regression or refresh its statistics if it is still open.
PG_UPSERT_REGRESSION = """
INSERT INTO regressions (
    project_id, metric_id, screen_name, device_cohort,
    baseline_version_code, baseline_version_name,
    current_version_code,  current_version_name,
    baseline_p50, current_p50, degradation_percent,
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
    baseline_p50          = EXCLUDED.baseline_p50,
    current_p50           = EXCLUDED.current_p50,
    degradation_percent   = EXCLUDED.degradation_percent,
    sample_count_baseline = EXCLUDED.sample_count_baseline,
    sample_count_current  = EXCLUDED.sample_count_current
WHERE regressions.status = 'open'
"""

# Fetch open regressions that are old enough to be eligible for auto-close.
# Bind: (quiet_hours,)
PG_OPEN_REGRESSIONS = """
SELECT
    id::text,
    project_id::text,
    metric_id,
    screen_name,
    device_cohort,
    current_version_code
FROM regressions
WHERE status = 'open'
  AND detected_at <= NOW() - INTERVAL '%s hours'
"""

# Supersede open regressions for a group whose current version is no longer
# the latest mature version.
# Bind: (project_id, metric_id, screen_name, device_cohort, max_version_code)
PG_CLOSE_SUPERSEDED = """
UPDATE regressions
SET
    status          = 'resolved',
    resolution_type = 'superseded',
    resolved_at     = NOW()
WHERE status = 'open'
  AND project_id    = %s::uuid
  AND metric_id     = %s
  AND screen_name   = %s
  AND device_cohort = %s
  AND current_version_code < %s
"""

# Close a single regression as rolled-back.
# Bind: (regression_id,)
PG_CLOSE_ROLLED_BACK = """
UPDATE regressions
SET
    status          = 'resolved',
    resolution_type = 'rolled_back',
    resolved_at     = NOW()
WHERE id = %s::uuid
"""
