def get_regressions_query(limit: int = 100) -> str:
    return f"""
    SELECT
        project_id,
        package_name,
        metric_id,
        screen_name,
        baseline_version,
        current_version,
        delta_p50,
        delta_p95,
        p_value,
        is_regression,
        detected_at
    FROM regressions
    ORDER BY detected_at DESC
    LIMIT {limit}
    """


def get_metrics_query(
    project_id: str,
    metric_id: str,
    screen_name: str,
    minutes_back: int = 60
) -> str:
    filters = []

    if project_id:
        filters.append(f"project_id = '{project_id}'")
    if metric_id:
        filters.append(f"metric_id = '{metric_id}'")
    if screen_name:
        filters.append(f"screen_name = '{screen_name}'")

    where_clause = " AND ".join(filters) if filters else "1 = 1"

    return f"""
    SELECT
        ts,
        project_id,
        package_name,
        app_version,
        metric_id,
        screen_name,
        device_cohort,
        value
    FROM metric_records
    WHERE {where_clause} AND ts >= now() - INTERVAL {minutes_back} MINUTE
    ORDER BY ts DESC
    """


def get_dashboard_counts_query() -> str:
    return """
    SELECT
        count() AS total_rows
    FROM metric_records
    """


def get_latest_regressions_count_query() -> str:
    return """
    SELECT
        count() AS regressions_count
    FROM regressions
    WHERE is_regression = 1
    """


def get_project_status_query(project_id: str) -> str:
    return f"""
    SELECT
        count()                    AS total_rows,
        max(ts)                    AS last_ingested,
        uniq(metric_id)            AS unique_metrics,
        uniq(screen_name)          AS unique_screens
    FROM metric_records
    WHERE project_id = '{project_id}'
    """


def get_project_metrics_query(project_id: str) -> str:
    """Returns distinct (metric_id, screen_name, device_cohort) combos."""
    return f"""
    SELECT DISTINCT metric_id, screen_name, device_cohort
    FROM metric_records
    WHERE project_id = '{project_id}'
    ORDER BY metric_id, screen_name, device_cohort
    """


def get_custom_plot_query(
    project_id: str,
    metric_id: str,
    screen_name: str,
    device_cohort: str,
    minutes_back: int,
    aggregation: str,
    bucket_minutes: int,
) -> str:
    agg_fn = {
        "P50": "quantile(0.50)(value)",
        "P95": "quantile(0.95)(value)",
        "Avg": "avg(value)",
        "Max": "max(value)",
    }.get(aggregation, "quantile(0.95)(value)")

    cohort_filter = (
        f"AND device_cohort = '{device_cohort}'"
        if device_cohort != "All" else ""
    )

    return f"""
    SELECT
        toStartOfInterval(ts, INTERVAL {bucket_minutes} MINUTE) AS bucket,
        {agg_fn} AS metric_value
    FROM metric_records
    WHERE
        project_id  = '{project_id}'
        AND metric_id   = '{metric_id}'
        AND screen_name = '{screen_name}'
        {cohort_filter}
        AND ts >= now() - INTERVAL {minutes_back} MINUTE
    GROUP BY bucket
    ORDER BY bucket
    """


def get_thresholds_query() -> str:
    return """
    SELECT
        project_id,
        package_name,
        metric_id,
        screen_name,
        device_cohort,
        p50_threshold,
        p95_threshold,
        p_value_threshold,
        updated_at
    FROM alert_thresholds
    ORDER BY updated_at DESC
    LIMIT 200
    """