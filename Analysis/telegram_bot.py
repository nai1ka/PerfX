"""
PerfX Telegram Bot.

Commands:
  /connect <project_id>  — link this chat to a PerfX project
  /disconnect            — unlink this chat from the project
  /status                — show which project is connected

Run:
  TELEGRAM_BOT_TOKEN=<token> python telegram_bot.py
"""

import logging
import os
import sys

import psycopg2
import requests

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
API = f"https://api.telegram.org/bot{TOKEN}"

PG_DSN = {
    "host": os.getenv("PG_HOST", "localhost"),
    "port": int(os.getenv("PG_PORT", "5432")),
    "dbname": os.getenv("PG_DB", "perfx"),
    "user": os.getenv("PG_USER", "perfx_user"),
    "password": os.getenv("PG_PASSWORD", "perfx_pass"),
}


def _send(chat_id: int, text: str) -> None:
    requests.post(
        f"{API}/sendMessage",
        json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"},
        timeout=10,
    )


def _pg_conn():
    return psycopg2.connect(**PG_DSN)


def _handle_connect(chat_id: int, project_id: str) -> None:
    try:
        conn = _pg_conn()
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE projects SET telegram_chat_id = %s WHERE id = %s RETURNING name",
                (chat_id, project_id),
            )
            row = cur.fetchone()
        conn.commit()
        conn.close()
    except Exception as exc:
        log.error("DB error in /connect: %s", exc)
        _send(chat_id, "⚠️ Database error. Please try again later.")
        return

    if row:
        _send(chat_id, f"✅ Connected to project *{row[0]}*.\nYou'll receive regression alerts here.")
    else:
        _send(chat_id, "❌ Project not found. Check the project ID in PerfX dashboard.")


def _handle_disconnect(chat_id: int) -> None:
    try:
        conn = _pg_conn()
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE projects SET telegram_chat_id = NULL WHERE telegram_chat_id = %s RETURNING name",
                (chat_id,),
            )
            row = cur.fetchone()
        conn.commit()
        conn.close()
    except Exception as exc:
        log.error("DB error in /disconnect: %s", exc)
        _send(chat_id, "⚠️ Database error. Please try again later.")
        return

    if row:
        _send(chat_id, f"🔌 Disconnected from project *{row[0]}*.")
    else:
        _send(chat_id, "This chat is not connected to any project.")


def _handle_status(chat_id: int) -> None:
    try:
        conn = _pg_conn()
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, name FROM projects WHERE telegram_chat_id = %s",
                (chat_id,),
            )
            row = cur.fetchone()
        conn.close()
    except Exception as exc:
        log.error("DB error in /status: %s", exc)
        _send(chat_id, "⚠️ Database error. Please try again later.")
        return

    if row:
        _send(chat_id, f"📊 Connected to project *{row[1]}*\n`{row[0]}`")
    else:
        _send(chat_id, "This chat is not connected to any project.\nUse `/connect <project_id>` to link it.")


def _process_update(update: dict) -> None:
    message = update.get("message") or update.get("channel_post")
    if not message:
        return

    chat_id: int = message["chat"]["id"]
    text: str = message.get("text", "").strip()

    if text.startswith("/connect"):
        parts = text.split(maxsplit=1)
        if len(parts) < 2 or not parts[1].strip():
            _send(chat_id, "Usage: `/connect <project_id>`\n\nFind your project ID in the PerfX dashboard.")
            return
        _handle_connect(chat_id, parts[1].strip())

    elif text.startswith("/disconnect"):
        _handle_disconnect(chat_id)

    elif text.startswith("/status"):
        _handle_status(chat_id)

    elif text.startswith("/start"):
        _send(
            chat_id,
            "👋 *PerfX Regression Bot*\n\n"
            "I'll notify you when a performance regression is detected.\n\n"
            "To get started, link this chat to your project:\n"
            "`/connect <project_id>`\n\n"
            "Find your project ID in the PerfX dashboard.",
        )


def main() -> None:
    if not TOKEN:
        log.error("TELEGRAM_BOT_TOKEN is not set.")
        sys.exit(1)

    log.info("PerfX Telegram bot starting (long-polling).")
    offset = 0

    while True:
        try:
            resp = requests.get(
                f"{API}/getUpdates",
                params={"offset": offset, "timeout": 30},
                timeout=35,
            )
            data = resp.json()
        except requests.RequestException as exc:
            log.warning("getUpdates error: %s", exc)
            continue

        for update in data.get("result", []):
            try:
                _process_update(update)
            except Exception as exc:
                log.error("Error processing update %s: %s", update.get("update_id"), exc)
            offset = update["update_id"] + 1


if __name__ == "__main__":
    main()
