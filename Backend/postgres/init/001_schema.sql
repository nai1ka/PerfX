CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL
);

CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    package_name TEXT NOT NULL UNIQUE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE thresholds (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,

    metric_id TEXT NOT NULL,
    screen_name TEXT,

    threshold_value DOUBLE PRECISION
);

CREATE TABLE regressions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    
    metric_id TEXT NOT NULL,
    screen_name TEXT NOT NULL,
    device_cohort TEXT NOT NULL,
    
    baseline_p95 DOUBLE PRECISION,
    current_p95 DOUBLE PRECISION,
    degradation_percent DOUBLE PRECISION,
    p_value DOUBLE PRECISION,

    detected_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);