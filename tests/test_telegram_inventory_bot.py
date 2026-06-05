import types
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

    def test_reset_command_rotates_and_replies_with_fresh_hola(self):
        sent = []

        message = {
            "message_id": 1,
            "chat": {"id": 123, "type": "private"},
            "from": {"id": 456, "first_name": "Yaneth"},
            "text": "/reset",
        }

        with patch.object(bot, "require_openclaw_ready", return_value="ok"), \
             patch.object(bot, "run_openclaw_agent", return_value="MENU OK") as agent, \
             patch.object(bot, "send_message", side_effect=lambda _token, chat_id, text, reply_markup=None: sent.append((chat_id, text))):
            bot.handle_message("token", message)

        self.assertEqual(sent, [(123, "MENU OK")])
        agent.assert_called_once_with("hola", 123)


if __name__ == "__main__":
    unittest.main()
