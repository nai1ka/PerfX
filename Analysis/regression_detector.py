"""
Performance Regression Detection Service — entry point.

Runs every minute, queries ClickHouse for aggregated percentile data,
applies Rolling Window Percentile Shift + Mann-Whitney U test to confirm
regressions, and writes confirmed regressions to PostgreSQL.
"""

import logging
import time

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

        log.info("Sleeping 60 s until next run.")
        time.sleep(60)


if __name__ == "__main__":
    main()
