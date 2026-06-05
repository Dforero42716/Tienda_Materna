import io
import types
import urllib.error
import unittest
from unittest.mock import patch

import telegram_inventory_bot as bot


class TelegramInventoryBotTests(unittest.TestCase):
    def setUp(self):
        bot.SESSION_TOKEN_BY_CHAT.clear()
        bot.LOCAL_FALLBACK_BY_CHAT.clear()

    def test_extracts_payload_text_without_ids(self):
        payload = {
            "runId": "4f921555-9e0a-4cc7-a975-cb9b43aa2899",
            "sessionId": "b5f4f2a4-6cab-4ea1-9288-dad3ef52c357",
            "status": "ok",
            "result": {
                "payloads": [
                    {"text": "Hola Yaneth"},
                    {"mediaUrl": "https://example.test/image.png"},
                ],
            },
        }

        self.assertEqual(
            bot._extract_agent_text(payload),
            "Hola Yaneth\nMEDIA:https://example.test/image.png",
        )

    def test_session_reset_generates_fresh_key(self):
        chat_id = 123
        first = bot._session_key_for_chat(chat_id)
        bot.reset_openclaw_session(chat_id)
        second = bot._session_key_for_chat(chat_id)
        bot.reset_openclaw_session(chat_id)
        third = bot._session_key_for_chat(chat_id)

        self.assertEqual(len({first, second, third}), 3)

    def test_context_overflow_retries_then_falls_back(self):
        calls = []

        def fake_run(*args, **kwargs):
            calls.append(args[0])
            return types.SimpleNamespace(
                returncode=0,
                stdout='{"status":"ok","result":{"payloads":[{"text":"Context overflow: prompt too large for the model."}]}}',
                stderr="",
            )

        with patch.object(bot, "require_openclaw_ready", return_value="ok"), \
             patch.object(bot, "openclaw_executable", return_value="openclaw.cmd"), \
             patch.object(bot.subprocess, "run", side_effect=fake_run), \
             patch.object(bot, "run_local_inventory_fallback", return_value="MENU OK") as fallback:
            response = bot.run_openclaw_agent("hola", 123)

        self.assertEqual(response, "MENU OK")
        self.assertEqual(len(calls), 2)
        fallback.assert_called_once_with("hola", 123, "openclaw-agent-context-overflow-response")

    def test_reset_command_rotates_and_replies_with_menu(self):
        sent = []

        message = {
            "message_id": 1,
            "chat": {"id": 123, "type": "private"},
            "from": {"id": 456, "first_name": "Yaneth"},
            "text": "/reset",
        }

        with patch.object(bot, "require_openclaw_ready", return_value="ok"), \
             patch.object(bot, "run_openclaw_agent") as agent, \
             patch.object(bot, "send_message", side_effect=lambda _token, chat_id, text, reply_markup=None: sent.append((chat_id, text))):
            bot.handle_message("token", message)

        self.assertEqual(len(sent), 1)
        self.assertEqual(sent[0][0], 123)
        self.assertIn("Hola Yaneth", sent[0][1])
        self.assertIn("Comandos disponibles", sent[0][1])
        agent.assert_not_called()

    def test_hola_replies_with_menu_without_agent(self):
        sent = []
        message = {
            "message_id": 1,
            "chat": {"id": 123, "type": "private"},
            "from": {"id": 456, "first_name": "Marycruz"},
            "text": "Hola",
        }

        with patch.object(bot, "require_openclaw_ready", return_value="ok"), \
             patch.object(bot, "run_openclaw_agent") as agent, \
             patch.object(bot, "send_message", side_effect=lambda _token, chat_id, text, reply_markup=None: sent.append((chat_id, text))):
            bot.handle_message("token", message)

        self.assertEqual(len(sent), 1)
        self.assertEqual(sent[0][0], 123)
        self.assertIn("Hola Marycruz", sent[0][1])
        self.assertIn("Comandos disponibles", sent[0][1])
        agent.assert_not_called()

    def test_telegram_request_translates_409_conflict(self):
        error = urllib.error.HTTPError(
            url="https://api.telegram.org/botTOKEN/getUpdates",
            code=409,
            msg="Conflict",
            hdrs={},
            fp=io.BytesIO(b'{"description":"terminated by other getUpdates request"}'),
        )

        with patch.object(bot.urllib.request, "urlopen", side_effect=error):
            with self.assertRaises(bot.TelegramConflictError) as context:
                bot.telegram_request("TOKEN", "getUpdates?timeout=30")

        self.assertIn("HTTP 409 Conflict", str(context.exception))
        self.assertIn("otro proceso", str(context.exception))

    def test_clear_telegram_webhook_drops_pending_updates(self):
        with patch.object(bot, "telegram_request", return_value={"ok": True}) as request:
            response = bot.clear_telegram_webhook("TOKEN")

        self.assertEqual(response, {"ok": True})
        request.assert_called_once_with(
            "TOKEN",
            "deleteWebhook?drop_pending_updates=true",
            timeout=20,
        )


if __name__ == "__main__":
    unittest.main()
