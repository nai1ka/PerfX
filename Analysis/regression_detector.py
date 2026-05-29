"""
Performance Regression Detection Service — entry point.

Runs every POLL_INTERVAL_SECONDS (default: hourly), queries ClickHouse for
per-version median values, compares consecutive mature versions using the
relative median-shift formula:

    Δ = (median_current − median_baseline) / median_baseline

and writes confirmed regressions to PostgreSQL.  Open regressions are
auto-closed when superseded by a newer version or when the affected version
stops receiving traffic.
"""

import logging
import time

from regression_detection.config import POLL_INTERVAL_SECONDS
from regression_detection.db import get_ch_client, get_pg_conn
from regression_detection.detector import run_detection

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)


def main() -> None:
    log.info("Regression detector starting up.")

    while True:
        pg_conn = None
        try:
            ch_client = get_ch_client()
            pg_conn = get_pg_conn()
            run_detection(ch_client, pg_conn)
        except Exception as exc:
            log.error("Detection run failed: %s", exc, exc_info=True)
        finally:
            if pg_conn is not None:
                pg_conn.close()

        log.info("Sleeping %ds until next run.", POLL_INTERVAL_SECONDS)
        time.sleep(POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
