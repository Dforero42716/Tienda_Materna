import json
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import subprocess
import ssl
import time
import urllib.parse
import urllib.request

from env_loader import env_flag_enabled, load_env
from openclaw_guard import openclaw_executable, require_openclaw_ready

import os

load_env()


API_BASE = "https://api.telegram.org/bot{token}/{method}"
LOG_DIR = Path(__file__).resolve().parent / "logs"
LOG_FILE = LOG_DIR / "telegram_bot.log"
CATEGORY_CALLBACK_PREFIX = "category:"
OPENCLAW_AGENT_ID = os.environ.get("MUNDO_MATERNO_OPENCLAW_AGENT")
OPENCLAW_AGENT_TIMEOUT = int(os.environ.get("MUNDO_MATERNO_OPENCLAW_AGENT_TIMEOUT", "600"))


def setup_logging():
    LOG_DIR.mkdir(exist_ok=True)

    logger = logging.getLogger("mundo_materno.telegram")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=1_000_000,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    return logger


logger = setup_logging()


def describe_message(message):
    user = message.get("from", {})
    chat = message.get("chat", {})
    return {
        "message_id": message.get("message_id"),
        "chat_id": chat.get("id"),
        "chat_type": chat.get("type"),
        "user_id": user.get("id"),
        "username": user.get("username"),
        "first_name": user.get("first_name"),
    }


def telegram_request(token, method, payload=None):
    data = None
    headers = {}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    request = urllib.request.Request(
        API_BASE.format(token=token, method=method),
        data=data,
        headers=headers,
        method="POST" if payload is not None else "GET",
    )
    context = None
    if env_flag_enabled("TELEGRAM_INSECURE_SKIP_TLS_VERIFY"):
        logger.warning("Telegram TLS certificate verification is disabled by TELEGRAM_INSECURE_SKIP_TLS_VERIFY.")
        context = ssl._create_unverified_context()

    with urllib.request.urlopen(request, timeout=60, context=context) as response:
        result = json.loads(response.read().decode("utf-8"))
        if not result.get("ok", True):
            logger.warning("Telegram API returned non-ok response method=%s response=%s", method, result)
        return result


def send_message(token, chat_id, text, reply_markup=None):
    max_len = 3900
    chunks = [text[i:i + max_len] for i in range(0, len(text), max_len)] or [text]
    for index, chunk in enumerate(chunks):
        payload = {"chat_id": chat_id, "text": chunk}
        if index == 0 and reply_markup:
            payload["reply_markup"] = reply_markup
        telegram_request(token, "sendMessage", payload)
    logger.info("Sent reply chat_id=%s chunks=%s chars=%s", chat_id, len(chunks), len(text))


def _extract_agent_text(payload):
    result = payload.get("result") if isinstance(payload, dict) else None
    payloads = result.get("payloads") if isinstance(result, dict) else None
    if not isinstance(payloads, list):
        return ""

    lines = []
    for item in payloads:
        if not isinstance(item, dict):
            continue
        text = item.get("text")
        if isinstance(text, str) and text.strip():
            lines.append(text.strip())
        media_url = item.get("mediaUrl")
        if isinstance(media_url, str) and media_url.strip():
            lines.append(f"MEDIA:{media_url.strip()}")
        media_urls = item.get("mediaUrls")
        if isinstance(media_urls, list):
            for url in media_urls:
                if isinstance(url, str) and url.strip():
                    lines.append(f"MEDIA:{url.strip()}")

    return "\n".join(lines).strip()


def run_openclaw_agent(text, chat_id):
    require_openclaw_ready()

    args = [
        openclaw_executable(),
        "agent",
        "--session-key",
        f"mundo-materno-telegram-{chat_id}",
        "--message",
        text,
        "--json",
    ]
    if OPENCLAW_AGENT_ID:
        args[2:2] = ["--agent", OPENCLAW_AGENT_ID]

    result = subprocess.run(
        args,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        text=True,
        timeout=OPENCLAW_AGENT_TIMEOUT,
        check=False,
    )

    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip()
        raise RuntimeError(f"OpenClaw agent failed: {detail}")

    stdout = (result.stdout or "").strip()
    if not stdout:
        return "OpenClaw no devolvio una respuesta."

    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError:
        return stdout

    response = _extract_agent_text(payload)
    if response:
        return response

    if isinstance(payload, dict) and payload.get("status") == "in_flight":
        run_id = payload.get("runId")
        if isinstance(run_id, str) and run_id.strip():
            return f"OpenClaw ya tiene una respuesta en proceso para esta conversacion. Run ID: {run_id}"
        return "OpenClaw ya tiene una respuesta en proceso para esta conversacion."

    summary = payload.get("summary") if isinstance(payload, dict) else None
    if isinstance(summary, str) and summary.strip():
        return summary.strip()

    return "OpenClaw termino el turno, pero no devolvio texto para enviar por Telegram."


def handle_callback_query(token, callback_query):
    callback_id = callback_query.get("id")
    data = callback_query.get("data", "")
    message = callback_query.get("message", {})
    chat = message.get("chat", {})
    chat_id = chat.get("id")

    if callback_id:
        telegram_request(token, "answerCallbackQuery", {"callback_query_id": callback_id})

    if not chat_id:
        logger.warning("Callback without chat_id data=%r", data)
        return

    try:
        require_openclaw_ready()
    except RuntimeError as exc:
        logger.error("OpenClaw dependency blocked callback chat_id=%s error=%s", chat_id, exc)
        send_message(token, chat_id, str(exc))
        return

    if data.startswith(CATEGORY_CALLBACK_PREFIX):
        category = data[len(CATEGORY_CALLBACK_PREFIX):].strip()
        logger.info("Category callback chat_id=%s category=%r", chat_id, category)
        response = run_openclaw_agent(f"productos de la categoria {category}", chat_id)
        send_message(token, chat_id, response)
        return

    logger.warning("Unknown callback chat_id=%s data=%r", chat_id, data)
    send_message(token, chat_id, "No pude reconocer esa opcion.")


def handle_message(token, message):
    chat_id = message["chat"]["id"]
    text = message.get("text", "").strip()
    context = describe_message(message)
    logger.info("Incoming message context=%s text=%r", context, text)

    if not text:
        send_message(token, chat_id, "Escribe una consulta de inventario.")
        return

    try:
        require_openclaw_ready()
    except RuntimeError as exc:
        logger.error("OpenClaw dependency blocked request context=%s error=%s", context, exc)
        send_message(token, chat_id, str(exc))
        return

    if text.startswith("/start"):
        text = "hola"

    if text.startswith("/help"):
        text = "ayuda"

    response = run_openclaw_agent(text, chat_id)
    logger.info("Inventory response chat_id=%s chars=%s", chat_id, len(response))
    send_message(token, chat_id, response)


def main():
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError("Configura TELEGRAM_BOT_TOKEN en .env.")

    openclaw_status = require_openclaw_ready()
    logger.info("OpenClaw dependency ready: %s", openclaw_status)

    me = telegram_request(token, "getMe")
    username = me.get("result", {}).get("username", "desconocido")
    logger.info("Bot de Telegram iniciado username=@%s log_file=%s", username, LOG_FILE)
    print(f"Bot de Telegram iniciado: @{username}")
    print(f"Log: {LOG_FILE}")
    print("Presiona Ctrl+C para detenerlo.")

    offset = None
    try:
        while True:
            params = {"timeout": 30}
            if offset is not None:
                params["offset"] = offset
            query = urllib.parse.urlencode(params)
            updates = telegram_request(token, f"getUpdates?{query}")

            update_count = len(updates.get("result", []))
            if update_count:
                logger.info("Received updates count=%s", update_count)

            for update in updates.get("result", []):
                offset = update["update_id"] + 1
                message = update.get("message")
                callback_query = update.get("callback_query")
                if message:
                    try:
                        handle_message(token, message)
                    except Exception as exc:
                        logger.exception("Error handling message context=%s", describe_message(message))
                        send_message(token, message["chat"]["id"], f"Error: {exc}")
                elif callback_query:
                    try:
                        handle_callback_query(token, callback_query)
                    except Exception as exc:
                        message = callback_query.get("message", {})
                        chat_id = message.get("chat", {}).get("id")
                        logger.exception("Error handling callback_query data=%r", callback_query.get("data"))
                        if chat_id:
                            send_message(token, chat_id, f"Error: {exc}")

            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Bot detenido por el usuario.")
        raise
    except Exception:
        logger.exception("Bot stopped unexpectedly.")
        raise


if __name__ == "__main__":
    main()
