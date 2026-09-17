"""Exercise the actual local-model wire adapter without claiming a live model run."""

from __future__ import annotations

import io
import json
import unittest
from unittest.mock import patch

from enthus.decider import OllamaDecider, parse_decision
from enthus.models import Context, Event, Message, Settings, Speak, State


class DeciderTests(unittest.IsolatedAsyncioTestCase):
    async def test_structured_request_and_recorded_response(self) -> None:
        context = Context(Event("event-1", "user", "Hello"),
                          State(1, 9, False, None, None, None, 100, None, None),
                          (Message("user", "Hello"),), 100)
        recorded = {"done": True, "message": {"content": json.dumps({
            "kind": "speak", "text": "Hello there.", "seconds": None, "reason": "Reply to user",
        })}, "prompt_eval_count": 100, "eval_count": 20}
        with patch("enthus.decider.urlopen", return_value=io.BytesIO(json.dumps(recorded).encode())) as http:
            result = await OllamaDecider("fixture-model", Settings())(context)
        self.assertIsInstance(result.decision, Speak)
        self.assertEqual((result.input_tokens, result.output_tokens), (100, 20))
        request = http.call_args.args[0]
        payload = json.loads(request.data)
        self.assertEqual(request.full_url, "http://127.0.0.1:11434/api/chat")
        self.assertFalse(payload["stream"])
        self.assertEqual(payload["options"]["num_predict"], 512)
        self.assertEqual(payload["model"], "fixture-model")
        self.assertEqual(json.loads(payload["messages"][1]["content"])["event"]["id"], "event-1")

    async def test_missing_usage_is_not_reported_as_zero(self) -> None:
        context = Context(Event("1", "wake", ""),
                          State(1, 9, True, None, 200, None, None, None, None), (), 100)
        recorded = {"done": True, "message": {"content": json.dumps({
            "kind": "wait", "text": None, "seconds": None, "reason": "No new evidence",
        })}}
        with patch("enthus.decider.urlopen", return_value=io.BytesIO(json.dumps(recorded).encode())):
            with self.assertRaises(KeyError):
                await OllamaDecider("fixture-model", Settings())(context)

    def test_untrusted_decisions_cannot_add_actions_or_authority(self) -> None:
        cases = [
            {"kind": "speak", "text": "hi", "seconds": None, "reason": "reply", "budget": 1000},
            {"kind": "execute", "text": "shell command", "seconds": None, "reason": "do work"},
            {"kind": "speak", "text": "x" * 2001, "seconds": None, "reason": "too long"},
            {"kind": "wait", "text": None, "seconds": float("nan"), "reason": "bad clock"},
            {"kind": "wait", "text": None, "seconds": True, "reason": "bad clock"},
            {"kind": "finish", "text": "A farewell", "seconds": None, "reason": "must stay silent"},
        ]
        for data in cases:
            with self.subTest(data=data), self.assertRaises(ValueError):
                parse_decision(json.dumps(data))

    def test_adapter_rejects_remote_or_credential_urls(self) -> None:
        for url in ("https://example.com", "http://user:secret@localhost:11434", "http://localhost/path"):
            with self.subTest(url=url), self.assertRaises(ValueError):
                OllamaDecider("fixture-model", Settings(), url)


if __name__ == "__main__":
    unittest.main()
