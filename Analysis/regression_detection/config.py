# ── ClickHouse ────────────────────────────────────────────────────────────────

CH_HOST = "localhost"
CH_PORT = 8123
CH_USER = "metrics_user"
CH_PASSWORD = "metrics_pass"
CH_DATABASE = "metrics"

# ── PostgreSQL ────────────────────────────────────────────────────────────────

PG_HOST = "localhost"
PG_DB = "perfx"
PG_USER = "perfx_user"
PG_PASSWORD = "perfx_pass"

# ── Detection parameters ──────────────────────────────────────────────────────

# Baseline window: [now - BASELINE_WINDOW_MINUTES  …  now - CURRENT_WINDOW_MINUTES]
# Current  window: [now - CURRENT_WINDOW_MINUTES   …  now]
BASELINE_WINDOW_MINUTES = 10   # 7 days
CURRENT_WINDOW_MINUTES  = 2        # last 24 h

# Default relative P95 degradation threshold (15 %).
# Per-project/metric overrides come from the Postgres `thresholds` table.
DEFAULT_P95_THRESHOLD = 0.15
DEFAULT_P_VALUE       = 0.05

# Minimum raw samples per window required before running Mann-Whitney U test.
MIN_SAMPLES = 30
