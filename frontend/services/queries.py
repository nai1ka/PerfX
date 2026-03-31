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
    package_name: str,
    metric_id: str,
    screen_name: str,
    limit: int,
) -> str:
    filters = []

    if package_name:
        filters.append(f"package_name = '{package_name}'")
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
        value
    FROM metric_records
    WHERE {where_clause}
    ORDER BY ts DESC
    LIMIT {limit}
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