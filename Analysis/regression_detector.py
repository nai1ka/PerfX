"""
Performance Regression Detection Service — entry point.

Runs every POLL_INTERVAL_SECONDS (default: hourly), queries ClickHouse for
per-version P95 values, compares consecutive mature versions using the
relative P95-shift formula:

    Δ = (P95_current − P95_baseline) / P95_baseline

and writes confirmed regressions to PostgreSQL.
"""

import argparse
import json
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
    parser = argparse.ArgumentParser(description="PerfX regression detector")
    parser.add_argument(
        "--once", action="store_true",
        help="Run detection once and exit (useful for scripted evaluation)",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Compute detections but do not write to Postgres; print JSON to stdout",
    )
    args = parser.parse_args()

    if args.once or args.dry_run:
        log.info("Regression detector: single-shot run (dry_run=%s).", args.dry_run)
        pg_conn = None
        try:
            ch_client = get_ch_client()
            if not args.dry_run:
                pg_conn = get_pg_conn()
            result = run_detection(ch_client, pg_conn, dry_run=args.dry_run)
            if args.dry_run and result is not None:
                print(json.dumps(result, indent=2))
        except Exception as exc:
            log.error("Detection run failed: %s", exc, exc_info=True)
            raise
        finally:
            if pg_conn is not None:
                pg_conn.close()
        return

    log.info("Regression detector starting up (continuous mode).")
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
