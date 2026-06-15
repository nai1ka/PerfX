import os

# ── ClickHouse ────────────────────────────────────────────────────────────────

CH_HOST = os.getenv("CH_HOST", "localhost")
CH_PORT = int(os.getenv("CH_PORT", "8123"))
CH_USER = os.getenv("CH_USER", "metrics_user")
CH_PASSWORD = os.getenv("CH_PASSWORD", "metrics_pass")
CH_DATABASE = os.getenv("CH_DATABASE", "metrics")

# ── PostgreSQL ────────────────────────────────────────────────────────────────

PG_HOST = os.getenv("PG_HOST", "localhost")
PG_PORT = int(os.getenv("PG_PORT", "5432"))
PG_DB = os.getenv("PG_DB", "perfx")
PG_USER = os.getenv("PG_USER", "perfx_user")
PG_PASSWORD = os.getenv("PG_PASSWORD", "perfx_pass")

# ── Detection parameters ──────────────────────────────────────────────────────

# Minimum raw samples per (project, metric, screen, cohort, version) group
# before that version is considered "mature" and eligible for comparison.
# Set to a small value for local testing; production intent: 1000.
MIN_SAMPLES_PER_VERSION = 10

# Relative P95 degradation threshold (15 %).
# A regression is flagged when:
#   Δ = (P95_current − P95_baseline) / P95_baseline > threshold
DEFAULT_P95_THRESHOLD = 0.15

# Seconds between detector runs.
POLL_INTERVAL_SECONDS = 30 # must be 3600
