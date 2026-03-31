CREATE DATABASE IF NOT EXISTS metrics;

CREATE TABLE IF NOT EXISTS metrics.metric_records
(
    project_id String,
    package_name String,

    ts DateTime64(3, 'UTC'),
    metric_id LowCardinality(String),
    metric_type LowCardinality(String), 
    screen_name LowCardinality(String),
    value Float64,

    app_version LowCardinality(String),
    os_version LowCardinality(String),
    device_model LowCardinality(String),
    received_at DateTime DEFAULT now()
)
ENGINE = MergeTree
PARTITION BY toDate(ts)
ORDER BY (project_id, metric_id, ts);