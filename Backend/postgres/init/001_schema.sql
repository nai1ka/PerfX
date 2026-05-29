CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ── Users & Projects ───────────────────────────────────────────────────────────

CREATE TABLE users (
    id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email         TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL
);

CREATE TABLE projects (
    id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name         TEXT NOT NULL,
    package_name TEXT NOT NULL,
    user_id      UUID REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE (user_id, name),
    UNIQUE (user_id, package_name)
);

-- ── Version catalogue (populated by background sync from ClickHouse) ───────────

CREATE TABLE version_releases (
    id           UUID    PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id   UUID    REFERENCES projects(id) ON DELETE CASCADE,
    version_code INT     NOT NULL,
    version_name TEXT    NOT NULL,
    first_seen_at TIMESTAMP WITH TIME ZONE,
    sample_count BIGINT  NOT NULL DEFAULT 0,
    UNIQUE (project_id, version_code)
);

-- ── Regressions ───────────────────────────────────────────────────────────────

CREATE TABLE regressions (
    id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id   UUID REFERENCES projects(id) ON DELETE CASCADE,

    metric_id    TEXT NOT NULL,
    screen_name  TEXT NOT NULL,
    device_cohort TEXT NOT NULL,

    -- Version pair
    baseline_version_code INT  NOT NULL,
    baseline_version_name TEXT NOT NULL,
    current_version_code  INT  NOT NULL,
    current_version_name  TEXT NOT NULL,

    -- Statistics (filled by detector; NULL until then)
    baseline_p50      DOUBLE PRECISION,
    current_p50       DOUBLE PRECISION,
    degradation_percent DOUBLE PRECISION,

    baseline_ci_lower DOUBLE PRECISION,
    baseline_ci_upper DOUBLE PRECISION,
    current_ci_lower  DOUBLE PRECISION,
    current_ci_upper  DOUBLE PRECISION,

    sample_count_baseline INT,
    sample_count_current  INT,

    -- Lifecycle
    status          TEXT NOT NULL DEFAULT 'open'
        CHECK (status IN ('open', 'acknowledged', 'resolved')),
    resolution_type TEXT
        CHECK (resolution_type IN ('fixed', 'rolled_back', 'superseded', 'expected', 'false_positive')),

    acknowledged_at TIMESTAMP WITH TIME ZONE,
    resolved_at     TIMESTAMP WITH TIME ZONE,
    detected_at     TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- One open regression per (project, metric, screen, cohort, version pair)
    UNIQUE (project_id, metric_id, screen_name, device_cohort,
            baseline_version_code, current_version_code)
);
