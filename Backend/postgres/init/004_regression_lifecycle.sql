-- Backfill columns that the backend model selects but that pre-date this
-- table's current shape. Init scripts only run on a fresh volume, so existing
-- deployments need this migration applied manually (see note below).
ALTER TABLE regressions
    ADD COLUMN IF NOT EXISTS closed_at         TIMESTAMP WITH TIME ZONE,
    ADD COLUMN IF NOT EXISTS baseline_ci_lower DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS baseline_ci_upper DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS current_ci_lower  DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS current_ci_upper  DOUBLE PRECISION;
