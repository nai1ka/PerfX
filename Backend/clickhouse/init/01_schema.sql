CREATE DATABASE IF NOT EXISTS metrics;

CREATE TABLE IF NOT EXISTS metrics.metric_records
(
    project_id   String,
    package_name String,

    ts           DateTime64(3, 'UTC'),
    metric_id    LowCardinality(String),
    metric_type  LowCardinality(String),
    screen_name  LowCardinality(String),
    value        Float64,

    version_name LowCardinality(String),
    version_code Int32 DEFAULT 0,
    os_version   LowCardinality(String),
    device_model LowCardinality(String),
    device_cohort LowCardinality(String) DEFAULT 'Unknown',
    received_at  DateTime DEFAULT now()
)
ENGINE = MergeTree
PARTITION BY toDate(ts)
ORDER BY (project_id, metric_id, version_code, ts);
