import json
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import time
import urllib.parse
import urllib.request

from env_loader import load_env
from main import preguntar

import os

load_env()


API_BASE = "https://api.telegram.org/bot{token}/{method}"
LOG_DIR = Path(__file__).resolve().parent / "logs"
LOG_FILE = LOG_DIR / "telegram_bot.log"
MUTATING_PREFIXES = (
    "vender ",
    "registrar venta ",
    "agregar stock ",
    "agregar unidades ",
    "iniciar dia",
    "iniciar día",
    "abrir dia",
    "abrir día",
    "empezar dia",
    "empezar día",
    "cerrar dia",
    "cerrar día",
)


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


def is_mutating_command(text):
    normalized = text.lower().strip()
    return any(normalized.startswith(prefix) for prefix in MUTATING_PREFIXES)


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
    with urllib.request.urlopen(request, timeout=60) as response:
        result = json.loads(response.read().decode("utf-8"))
        if not result.get("ok", True):
            logger.warning("Telegram API returned non-ok response method=%s response=%s", method, result)
        return result


def send_message(token, chat_id, text):
    max_len = 3900
    chunks = [text[i:i + max_len] for i in range(0, len(text), max_len)] or [text]
    for chunk in chunks:
        telegram_request(token, "sendMessage", {"chat_id": chat_id, "text": chunk})
    logger.info("Sent reply chat_id=%s chunks=%s chars=%s", chat_id, len(chunks), len(text))


def handle_message(token, message):
    chat_id = message["chat"]["id"]
    text = message.get("text", "").strip()
    context = describe_message(message)
    logger.info("Incoming message context=%s text=%r", context, text)

    if not text:
        send_message(token, chat_id, "Escribe una consulta de inventario.")
        return

    if text.startswith("/start"):
        send_message(
            token,
            chat_id,
            "Hola, soy Mundo Materno. Preguntame por inventario, ventas, stock, categorias, tallas o colores.",
        )
        return

    if text.startswith("/help"):
        send_message(
            token,
            chat_id,
            "Ejemplos:\n"
            "- cuantos productos hay\n"
            "- ventas de hoy\n"
            "- iniciar dia\n"
            "- productos en talla M\n"
            "- productos en color negro\n"
            "- producto mas vendido",
        )
        return

    if is_mutating_command(text) and os.environ.get("MUNDO_MATERNO_ALLOW_MUTATIONS") != "1":
        logger.warning("Blocked mutating command context=%s text=%r", context, text)
        send_message(
            token,
            chat_id,
            "Comando bloqueado: esta accion modifica inventario, ventas o el dia operativo.",
        )
        return

    response = preguntar(text)
    logger.info("Inventory response chat_id=%s chars=%s", chat_id, len(response))
    send_message(token, chat_id, response)


def main():
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError("Configura TELEGRAM_BOT_TOKEN en .env.")

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
                if message:
                    try:
                        handle_message(token, message)
                    except Exception as exc:
                        logger.exception("Error handling message context=%s", describe_message(message))
                        send_message(token, message["chat"]["id"], f"Error: {exc}")

            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Bot detenido por el usuario.")
        raise
    except Exception:
        logger.exception("Bot stopped unexpectedly.")
        raise


if __name__ == "__main__":
    main()
