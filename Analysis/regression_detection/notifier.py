"""
Telegram notification helper.

Sends a message to the chat_id associated with a project when a regression
is confirmed.  Uses the Bot API directly via requests (no extra library needed).
"""

import logging
import os

import requests

log = logging.getLogger(__name__)

_TELEGRAM_API = "https://api.telegram.org/bot{token}/sendMessage"

METRIC_LABELS = {
    "cpuUsage": "CPU Usage",
    "frameTime": "Frame Time",
    "memoryUsage": "Memory Usage",
    "startupTime": "Startup Time",
    "interactionLatency": "Interaction Latency",
}


def _bot_token() -> str | None:
    return os.getenv("TELEGRAM_BOT_TOKEN")


def _fetch_chat_id(pg_conn, project_id: str) -> int | None:
    with pg_conn.cursor() as cur:
        cur.execute(
            "SELECT telegram_chat_id FROM projects WHERE id = %s",
            (project_id,),
        )
        row = cur.fetchone()
    if row and row[0]:
        return int(row[0])
    return None


def send_regression_alert(
    pg_conn,
    project_id: str,
    metric_id: str,
    screen_name: str,
    device_cohort: str,
    baseline_vn: str,
    current_vn: str,
    baseline_p95: float,
    current_p95: float,
    delta_pct: float,
) -> None:
    token = _bot_token()
    if not token:
        return

    chat_id = _fetch_chat_id(pg_conn, project_id)
    if not chat_id:
        return

    metric_label = METRIC_LABELS.get(metric_id, metric_id)
    text = (
        f"🚨 *Regression detected*\n\n"
        f"*Metric:* {metric_label}\n"
        f"*Screen:* `{screen_name}`\n"
        f"*Cohort:* {device_cohort}\n"
        f"*Versions:* {baseline_vn} → {current_vn}\n"
        f"*P95:* {baseline_p95:.1f} → {current_p95:.1f} ms\n"
        f"*Degradation:* +{delta_pct:.1f}%"
    )

    try:
        resp = requests.post(
            _TELEGRAM_API.format(token=token),
            json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"},
            timeout=10,
        )
        if not resp.ok:
            log.warning("Telegram API error %d: %s", resp.status_code, resp.text)
    except requests.RequestException as exc:
        log.warning("Failed to send Telegram notification: %s", exc)
