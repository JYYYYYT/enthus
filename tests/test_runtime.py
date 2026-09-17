"""Replay concrete transitions against real SQLite, with only model/time/send faked."""

from __future__ import annotations

import asyncio
import json
import tempfile
import unittest
from collections import deque
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

from enthus.decider import parse_decision
from enthus.models import Context, Evaluation, Settings, Speak, Wait
from enthus.runtime import Runtime
from enthus.store import Store


class Harness:
    def __init__(self, path: Path, settings: Settings | None = None) -> None:
        self.path = path
        self.settings = settings or Settings(initial_calls=8, wake_interval=60, grant_seconds=3600,
                                             cooldown_seconds=0, active_chat_seconds=0, quiet_start=0, quiet_end=0)
        self.now = datetime(2026, 9, 18, 4, tzinfo=timezone.utc).timestamp()
        self.store = Store(path, self.settings)
        self.decisions: deque[Evaluation] = deque()
        self.contexts: list[Context] = []
        self.sent: list[tuple[str, str]] = []
        self.runtime = Runtime(self.store, self.decide, self.send, lambda: self.now)

    async def decide(self, context: Context) -> Evaluation:
        self.contexts.append(context)
        if not self.decisions:
            raise AssertionError("Unexpected evaluation: fixture has no next decision")
        return self.decisions.popleft()

    async def send(self, text: str, identity: str) -> None:
        self.sent.append((text, identity))

    def speak(self, text: str = "A recorded reply.") -> None:
        self.decisions.append(Evaluation(Speak(text, "Recorded fixture"), "recorded-v1", 10, 5))

    def restart(self) -> None:
        self.store.close()
        self.store = Store(self.path, self.settings)
        self.runtime = Runtime(self.store, self.decide, self.send, lambda: self.now)


class RuntimeTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.h = Harness(Path(self.temp.name) / "state.sqlite3")

    def tearDown(self) -> None:
        self.h.store.close()
        self.temp.cleanup()

    async def test_recorded_scenario_pack(self) -> None:
        pack = json.loads((Path(__file__).parent / "scenarios/m2a.json").read_text())
        for index, case in enumerate(pack["cases"]):
            with self.subTest(scenario=case["name"]):
                h = Harness(Path(self.temp.name) / f"scenario-{index}.sqlite3")
                try:
                    for step in case["steps"]:
                        if "user" in step:
                            h.store.submit(step["user"], h.now)
                        elif "control" in step:
                            h.store.control(step["control"], h.now, step.get("value"))
                        elif "advance" in step:
                            h.now += step["advance"]
                        elif "decision" in step:
                            h.decisions.append(Evaluation(parse_decision(json.dumps(step["decision"])), "recorded-v1", 10, 5))
                        elif "drain" in step:
                            await h.runtime.drain()
                        elif "step" in step:
                            self.assertTrue(await h.runtime.step())
                        elif "restart" in step:
                            h.restart()
                        elif "expect" in step:
                            for field, expected in step["expect"].items():
                                actual = ({"sent": len(h.sent), "history": len(h.store.messages()),
                                           "last_context_messages": len(h.contexts[-1].messages) if h.contexts else 0,
                                           "wake_in": h.store.state().wake_at - h.now if h.store.state().wake_at else None}.get(field)
                                          if field in {"sent", "history", "last_context_messages", "wake_in"}
                                          else getattr(h.store.state(), field))
                                self.assertEqual(actual, expected, field)
                    self.assertFalse(h.decisions, "Every recorded decision must be consumed")
                    self.assertFalse(h.store.state().last_error and "AssertionError" in h.store.state().last_error)
                finally:
                    h.store.close()

    async def test_duplicate_input_is_exact_and_coalesces_triggers(self) -> None:
        h = self.h
        h.store.submit("First", h.now, "same-id")
        h.store.submit("First", h.now, "same-id")
        with self.assertRaises(ValueError):
            h.store.submit("Different", h.now, "same-id")
        h.store.submit("Second", h.now)
        h.speak()
        await h.runtime.drain()
        self.assertEqual(len(h.contexts), 1)
        self.assertEqual([m.text for m in h.contexts[0].messages], ["First", "Second"])
        self.assertEqual(len(h.sent), 1)

    async def test_stop_during_evaluation_discards_late_result(self) -> None:
        h = self.h
        h.store.control("start", h.now)
        h.now += 60

        async def late(context: Context) -> Evaluation:
            h.store.control("stop", h.now)
            return Evaluation(Speak("Too late", "Recorded stale result"), "recorded-v1")

        h.runtime.decide = late
        await h.runtime.drain()
        self.assertEqual(h.sent, [])
        self.assertFalse(h.store.state().initiative_enabled)
        self.assertEqual(h.store.db.execute("SELECT disposition FROM decisions").fetchone()[0], "stale")

    async def test_user_correction_invalidates_queued_direct_reply(self) -> None:
        h = self.h
        h.store.submit("I like chess.", h.now)
        h.speak("A chess suggestion.")
        await h.runtime.step()
        h.store.submit("Actually I meant checkers.", h.now)
        h.speak("A checkers suggestion.")
        await h.runtime.drain()
        self.assertEqual([text for text, _ in h.sent], ["A checkers suggestion."])
        self.assertEqual(h.contexts[-1].messages[-1].text, "Actually I meant checkers.")

    async def test_unknown_send_blocks_until_host_resolves_without_resend(self) -> None:
        h = self.h
        h.store.submit("Hello", h.now)
        h.speak()

        async def ambiguous(text: str, identity: str) -> None:
            h.sent.append((text, identity))
            raise TimeoutError("Ack lost after writing")

        h.runtime.send = ambiguous
        await h.runtime.drain()
        identity = h.store.unknown_actions()[0]
        h.restart()
        self.assertFalse(await h.runtime.step())
        self.assertEqual(len(h.store.messages()), 1)
        h.store.finish_action(identity, "sent", h.now)
        await h.runtime.drain()
        self.assertEqual(len(h.sent), 1)
        self.assertEqual(len(h.store.messages()), 2)
        self.assertEqual(h.store.db.execute("SELECT count(*) FROM events WHERE kind='outcome'").fetchone()[0], 1)

    async def test_crash_after_dispatch_is_unknown_on_restart(self) -> None:
        h = self.h
        h.store.submit("Hello", h.now)
        h.speak()
        await h.runtime.step()
        action = h.store.pending_action()
        self.assertIsNotNone(action)
        h.store.sending(action)
        h.restart()
        self.assertEqual(h.store.unknown_actions(), [action.id])
        self.assertFalse(await h.runtime.step())
        self.assertEqual(h.sent, [])

    async def test_interrupted_model_attempt_is_charged_and_recovers(self) -> None:
        h = self.h
        h.store.submit("Hello", h.now)
        entered = asyncio.Event()

        async def blocked(context: Context) -> Evaluation:
            entered.set()
            await asyncio.Event().wait()
            raise AssertionError("Unreachable")

        h.runtime.decide = blocked
        task = asyncio.create_task(h.runtime.step())
        await entered.wait()
        task.cancel()
        with self.assertRaises(asyncio.CancelledError):
            await task
        h.restart()
        self.assertEqual(h.store.state().remaining_calls, 7)
        h.speak()
        await h.runtime.drain()
        self.assertEqual(h.store.state().remaining_calls, 6)
        self.assertEqual(len(h.sent), 1)

    async def test_quiet_hours_and_active_chat_do_not_spend_calls(self) -> None:
        h = self.h
        h.settings = replace(h.settings, quiet_start=22, quiet_end=9, active_chat_seconds=300, grant_seconds=86400)
        h.restart()
        h.now = datetime(2026, 9, 18, 15, tzinfo=timezone.utc).timestamp()  # 23:00 Shanghai.
        h.store.control("start", h.now)
        h.now += 60
        await h.runtime.drain()
        self.assertEqual(h.store.state().remaining_calls, 8)
        self.assertEqual(datetime.fromtimestamp(h.store.state().wake_at, timezone.utc).hour, 1)
        h.now = h.store.state().wake_at
        h.store.submit("Good morning", h.now)
        h.speak()
        await h.runtime.drain()
        h.now += 60
        await h.runtime.drain()
        self.assertEqual(len(h.contexts), 1)
        self.assertEqual(h.store.state().wake_at, h.store.state().last_user_at + 300)

    async def test_daily_limit_and_cooldown_are_dispatch_gates(self) -> None:
        h = self.h
        h.settings = replace(h.settings, daily_openings=1, cooldown_seconds=600, grant_seconds=172800)
        h.restart()
        h.store.control("start", h.now)
        h.now += 60
        h.speak("First opening")
        await h.runtime.drain()
        h.now += 60
        await h.runtime.drain()
        self.assertEqual(len(h.sent), 1)
        self.assertEqual(h.store.state().remaining_calls, 7)
        self.assertGreater(h.store.state().wake_at, h.now + 600)

    async def test_grant_expiry_before_dispatch_cancels_output(self) -> None:
        h = self.h
        h.store.control("start", h.now)
        h.now += 60
        h.speak()
        await h.runtime.step()
        h.now += 3600
        await h.runtime.drain()
        self.assertEqual(h.sent, [])
        self.assertFalse(h.store.state().initiative_enabled)

    async def test_muted_pending_opening_never_sends_after_resume(self) -> None:
        h = self.h
        h.store.control("start", h.now)
        h.now += 60
        h.speak("Stale opening")
        await h.runtime.step()
        h.store.control("mute", h.now)
        await h.runtime.drain()
        h.store.control("resume", h.now)
        h.now += 60
        h.decisions.append(Evaluation(Wait(None, "No fresh reason"), "recorded-v1"))
        await h.runtime.drain()
        self.assertEqual(h.sent, [])

    async def test_wait_cannot_increase_host_frequency(self) -> None:
        h = self.h
        h.store.control("start", h.now)
        h.now += 60
        h.decisions.append(Evaluation(Wait(1, "Try sooner"), "recorded-v1"))
        await h.runtime.drain()
        self.assertEqual(h.store.state().wake_at, h.now + 60)

    async def test_model_failure_is_charged_and_does_not_spin(self) -> None:
        h = self.h
        h.store.submit("Hello", h.now)

        async def fail(context: Context) -> Evaluation:
            raise ValueError("Malformed decision")

        h.runtime.decide = fail
        await h.runtime.drain()
        self.assertEqual(h.store.state().remaining_calls, 7)
        self.assertIn("Malformed decision", h.store.state().last_error)
        self.assertFalse(await h.runtime.step())
        self.assertEqual(h.sent, [])

    async def test_single_owner_and_context_bound(self) -> None:
        h = self.h
        with self.assertRaisesRegex(RuntimeError, "Another Enthus"):
            Store(h.path, h.settings)
        for number in range(25):
            h.store.submit(f"{number}:" + "x" * 1000, h.now)
        history = h.store.messages()
        self.assertLessEqual(len(history), 20)
        self.assertLessEqual(sum(len(m.text) for m in history), 12000)
        self.assertTrue(history[-1].text.startswith("24:"))

    async def test_timed_mute_during_evaluation_preserves_future_wake(self) -> None:
        h = self.h
        h.store.control("start", h.now)
        h.now += 60

        async def interrupted_by_mute(context: Context) -> Evaluation:
            h.store.control("mute", h.now, 120)
            return Evaluation(Speak("Obsolete", "Before the mute"), "recorded-v1")

        h.runtime.decide = interrupted_by_mute
        await h.runtime.drain()
        self.assertEqual(h.sent, [])
        self.assertEqual(h.store.state().wake_at, h.now + 60)
        h.now += 60
        await h.runtime.drain()
        self.assertEqual(h.store.state().wake_at, h.now + 60)
        h.now += 60
        h.runtime.decide = h.decide
        h.decisions.append(Evaluation(Wait(None, "Reevaluated after mute"), "recorded-v1"))
        await h.runtime.drain()
        self.assertEqual(h.store.state().remaining_calls, 6)

    async def test_real_model_timeout_spends_one_attempt(self) -> None:
        h = self.h
        h.settings = replace(h.settings, model_timeout=0.01)
        h.restart()
        h.store.submit("Hello", h.now)

        async def slow(context: Context) -> Evaluation:
            await asyncio.sleep(1)
            return Evaluation(Speak("Too late", "Slow model"), "recorded-v1")

        h.runtime.decide = slow
        await h.runtime.drain()
        self.assertEqual(h.store.state().remaining_calls, 7)
        self.assertIn("TimeoutError", h.store.state().last_error)
        self.assertEqual(h.sent, [])

    async def test_real_send_timeout_is_unknown(self) -> None:
        h = self.h
        h.settings = replace(h.settings, send_timeout=0.01)
        h.restart()
        h.store.submit("Hello", h.now)
        h.speak()

        async def slow(text: str, identity: str) -> None:
            h.sent.append((text, identity))
            await asyncio.sleep(1)

        h.runtime.send = slow
        await h.runtime.drain()
        self.assertEqual(len(h.store.unknown_actions()), 1)
        h.restart()
        await h.runtime.drain()
        self.assertEqual(len(h.sent), 1)


if __name__ == "__main__":
    unittest.main()
