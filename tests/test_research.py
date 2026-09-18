"""Replay bounded initiative, correction, provenance and source outcome routing."""

from __future__ import annotations

import asyncio
import io
import json
import sqlite3
import tempfile
import unittest
from dataclasses import asdict, replace
from pathlib import Path
from unittest.mock import patch

from enthus.decider import parse_decision
from enthus.models import Context, Evaluation, NarrowControl, Note, Query, SourceItem, SourceResult, Speak, Wait
from enthus.runtime import Runtime
from enthus.source import Wikipedia
from enthus.store import Store
from test_runtime import Harness


PACK = json.loads((Path(__file__).parent / "scenarios/m2b.json").read_text())


def source_fixture() -> SourceResult:
    data = dict(PACK["source"])
    data["items"] = tuple(SourceItem(**item) for item in data["items"])
    return SourceResult(**data)


class ResearchTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.h = Harness(Path(self.temp.name) / "research.sqlite3")
        self.h.settings = replace(self.h.settings, wikipedia="en")
        self.h.restart()
        self.h.runtime.search = self.search
        self.queries: list[str] = []
        self.h.store.set_topic("games", "I am making a small puzzle game.", self.h.now)
        self.h.store.control("start", self.h.now)
        self.h.now += 60

    def tearDown(self) -> None:
        self.h.store.close()
        self.temp.cleanup()

    async def search(self, query: str) -> SourceResult:
        self.queries.append(query)
        return replace(source_fixture(), query=query)

    def query(self) -> None:
        self.h.decisions.append(Evaluation(Query("games", "puzzle design", "Investigate shared topic"), "recorded-v2"))

    def finding(self) -> None:
        self.h.decisions.append(Evaluation(Speak("A relevant recorded finding.", "Grounded in excerpt",
                                                 (source_fixture().items[0].id,)), "recorded-v2"))

    async def test_source_outcome_scenario_pack(self) -> None:
        for index, case in enumerate(PACK["cases"]):
            with self.subTest(case=case["name"]):
                h = Harness(Path(self.temp.name) / f"case-{index}.sqlite3", self.h.settings)
                try:
                    h.store.set_topic("games", "A small puzzle game", h.now)
                    h.store.control("start", h.now)
                    h.now += 60

                    async def search(query: str) -> SourceResult:
                        if case["outcome"] == "error":
                            raise TimeoutError("Recorded source timeout")
                        result = source_fixture()
                        if case["outcome"] == "empty":
                            return replace(result, items=(), response='{"synthetic":true,"pages":[]}')
                        if case["outcome"] == "irrelevant":
                            return replace(result, items=(replace(result.items[0], excerpt="An unrelated historical building."),),
                                           response='{"synthetic":true,"outcome":"irrelevant"}')
                        return result

                    h.runtime.search = search
                    for decision in case["decisions"]:
                        h.decisions.append(Evaluation(parse_decision(json.dumps(decision)), "recorded-v2", 30, 20))
                    await h.runtime.drain()
                    self.assertFalse(h.decisions)
                    self.assertEqual(len(h.sent), case["expected_messages"])
                    self.assertEqual(h.store.state().remaining_queries, 19)
                    self.assertEqual(h.store.state().remaining_calls, 6)
                    self.assertIsNone(h.store.state().last_error)
                    query_action = h.store.db.execute("SELECT * FROM actions WHERE kind='query'").fetchone()
                    result_event = h.store.db.execute("SELECT * FROM events WHERE kind='result'").fetchone()
                    self.assertEqual(result_event["follow_up_id"], query_action["follow_up_id"])
                    self.assertEqual(json.loads(result_event["body"])["action_id"], query_action["id"])
                    self.assertEqual(result_event["status"], "done")
                    self.assertEqual(h.contexts[1].event.follow_up_id, query_action["follow_up_id"])
                    self.assertEqual(len(h.contexts[1].observations), 1)
                    if case["expected_messages"]:
                        self.assertIn(source_fixture().items[0].url, h.sent[0][0])
                        h.store.submit("How could I use that idea?", h.now)
                        h.speak("We can continue the same idea.")
                        await h.runtime.drain()
                        self.assertEqual(h.contexts[-1].observations[0].items[0].id, source_fixture().items[0].id)
                        self.assertIn(source_fixture().items[0].url, h.contexts[-1].messages[-2].text)
                finally:
                    h.store.close()

    async def test_mute_blocks_delivery_but_research_continues(self) -> None:
        h = self.h
        h.store.control("mute", h.now)
        self.query()
        self.finding()
        await h.runtime.drain()
        self.assertEqual(self.queries, ["puzzle design"])
        self.assertEqual(h.sent, [])
        self.assertEqual(len(h.store.observations(h.now)[0].items), 1)
        self.assertTrue(h.store.state().initiative_enabled)

    async def test_cancel_during_query_keeps_late_result_out_of_context(self) -> None:
        h = self.h

        async def late(query: str) -> SourceResult:
            h.store.control("stop", h.now)
            return source_fixture()

        h.runtime.search = late
        self.query()
        await h.runtime.drain()
        self.assertEqual(h.sent, [])
        self.assertEqual(h.store.state().remaining_queries, 19)
        self.assertFalse(h.store.state().initiative_enabled)
        self.assertEqual(h.store.observations(h.now)[0].items, ())
        self.assertEqual(h.store.db.execute("SELECT status FROM events WHERE kind='result'").fetchone()[0], "done")

    async def test_correction_cancels_queued_finding_and_preserves_history(self) -> None:
        h = self.h
        self.query()
        self.finding()
        for _ in range(3):
            await h.runtime.step()
        self.assertIsNotNone(h.store.pending_action())
        h.store.set_topic("games", "I now prefer cooperative board games.", h.now)
        await h.runtime.drain()
        self.assertEqual(h.sent, [])
        self.assertEqual(h.store.observations(h.now), ())
        self.assertEqual(h.store.db.execute("SELECT count(*) FROM topic_history WHERE key='games'").fetchone()[0], 2)
        h.restart()
        self.assertIn("cooperative", h.store.topics()[0].text)

    async def test_repeated_source_reference_does_not_repeat_opening(self) -> None:
        h = self.h
        self.query()
        self.finding()
        await h.runtime.drain()
        h.now += 60
        self.query()
        self.finding()
        await h.runtime.drain()
        self.assertEqual(len(h.sent), 1)
        self.assertEqual(len(self.queries), 2)
        self.assertIn("already shared", h.store.state().last_error)

    async def test_ungrounded_result_message_is_rejected(self) -> None:
        self.query()
        self.h.speak("I discovered something with no citation.")
        await self.h.runtime.drain()
        self.assertEqual(self.h.sent, [])
        self.assertIn("references", self.h.store.state().last_error)

    async def test_two_query_ceiling_is_hard_and_persists(self) -> None:
        h = self.h
        for _ in range(3):
            self.query()
        await h.runtime.drain()
        self.assertEqual(len(self.queries), 2)
        self.assertEqual(h.store.state().remaining_queries, 18)
        row = h.store.db.execute("SELECT status,queries,calls FROM explorations").fetchone()
        self.assertEqual(tuple(row), ("closed", 2, 3))
        h.restart()
        self.assertEqual(h.store.state().remaining_queries, 18)

    async def test_zero_global_query_budget_never_dispatches(self) -> None:
        h = self.h
        h.store.control("query-budget", h.now, 0)
        self.query()
        await h.runtime.drain()
        self.assertEqual(self.queries, [])
        self.assertEqual(h.sent, [])

    async def test_query_requires_host_source_grant_and_topic(self) -> None:
        h = self.h
        h.store.control("stop", h.now)
        h.store.submit("Tell me something", h.now)
        self.query()
        await h.runtime.drain()
        self.assertEqual(self.queries, [])
        self.assertIn("grant", h.store.state().last_error)

    async def test_pending_result_survives_restart_without_requery(self) -> None:
        h = self.h
        self.query()
        await h.runtime.step()
        await h.runtime.step()
        self.assertEqual(len(self.queries), 1)
        h.restart()
        h.runtime.search = self.search
        self.finding()
        await h.runtime.drain()
        self.assertEqual(len(self.queries), 1)
        self.assertEqual(len(h.sent), 1)

    async def test_interrupted_query_recovers_as_failure_without_retry(self) -> None:
        h = self.h
        self.query()
        await h.runtime.step()
        action = h.store.pending_action()
        self.assertTrue(h.store.reserve_query(action, h.now))
        h.restart()
        h.runtime.search = self.search
        h.decisions.append(Evaluation(Wait(None, "Interrupted source; no evidence"), "recorded-v2"))
        await h.runtime.drain()
        self.assertEqual(self.queries, [])
        self.assertEqual(h.store.unknown_actions(), [])
        self.assertEqual(h.store.state().remaining_queries, 19)
        self.assertIn("interrupted", h.contexts[-1].observations[0].error)

    async def test_exploration_expiry_rejects_late_source_result(self) -> None:
        h = self.h

        async def delayed(query: str) -> SourceResult:
            h.now += h.settings.exploration_seconds
            return source_fixture()

        h.runtime.search = delayed
        self.query()
        await h.runtime.step()
        await h.runtime.step()
        self.assertEqual(h.store.observations(h.now)[0].items, ())
        self.assertEqual(h.store.db.execute("SELECT status FROM explorations").fetchone()[0], "closed")

    async def test_model_notes_require_current_user_evidence_and_respect_override(self) -> None:
        h = self.h
        event_id = h.store.submit("I am also learning astronomy.", h.now)
        h.decisions.append(Evaluation(Speak("Noted.", "User evidence"), "recorded-v2", notes=(
            Note("space", "Learning astronomy", event_id), Note("games", "Dislikes all games", event_id))))
        await h.runtime.drain()
        topics = {topic.key: topic for topic in h.store.topics()}
        self.assertEqual(topics["space"].user_event_id, event_id)
        self.assertIn("puzzle", topics["games"].text)
        h.now += 60
        h.decisions.append(Evaluation(Wait(None, "No user evidence"), "recorded-v2",
                                      notes=(Note("space", "Dislikes astronomy", event_id),)))
        await h.runtime.drain()
        self.assertEqual({t.key: t.text for t in h.store.topics()}["space"], "Learning astronomy")

    async def test_duplicate_completion_is_idempotent(self) -> None:
        h = self.h
        self.query()
        await h.runtime.step()
        action = h.store.pending_action()
        await h.runtime.step()
        h.store.finish_query(action, source_fixture(), h.now)
        self.assertEqual(h.store.db.execute("SELECT count(*) FROM events WHERE kind='result'").fetchone()[0], 1)

    async def test_user_linked_narrowing_controls_acknowledge_and_do_not_widen(self) -> None:
        h = self.h
        event_id = h.store.submit("Please leave me alone for a while.", h.now)
        h.decisions.append(Evaluation(Wait(None, "Respect user request"), "recorded-v2",
                                      control=NarrowControl("mute", event_id)))
        await h.runtime.drain()
        self.assertEqual(h.store.state().mute_until, -1)
        self.assertIn("until /resume", h.sent[0][0])
        self.assertTrue(h.store.state().initiative_enabled)
        event_id = h.store.submit("Stop investigating this.", h.now)
        h.decisions.append(Evaluation(Query("games", "puzzle design", "An inconsistent paired action"), "recorded-v2",
                                      control=NarrowControl("stop", event_id)))
        await h.runtime.drain()
        self.assertFalse(h.store.state().initiative_enabled)
        self.assertEqual(self.queries, [])
        self.assertIn("initiative cancelled", h.sent[-1][0])
        with self.assertRaises(ValueError):
            NarrowControl("start", event_id)

    async def test_source_or_wake_cannot_invoke_user_controls(self) -> None:
        h = self.h
        h.decisions.append(Evaluation(Wait(None, "No user control"), "recorded-v2",
                                      control=NarrowControl("stop", "invented-user-event")))
        await h.runtime.drain()
        self.assertTrue(h.store.state().initiative_enabled)
        self.assertEqual(h.sent, [])

    async def test_v1_migration_preserves_existing_conversation_and_budget(self) -> None:
        path = Path(self.temp.name) / "old.sqlite3"
        with sqlite3.connect(path) as db:
            db.executescript("""
                CREATE TABLE state(id INTEGER PRIMARY KEY, data TEXT NOT NULL);
                CREATE TABLE events(seq INTEGER PRIMARY KEY,id TEXT UNIQUE,kind TEXT,body TEXT,status TEXT,attempts INTEGER DEFAULT 0,created_at REAL);
                CREATE TABLE messages(seq INTEGER PRIMARY KEY,role TEXT,body TEXT,origin TEXT UNIQUE,created_at REAL);
                CREATE TABLE decisions(id TEXT PRIMARY KEY,event_id TEXT,context TEXT,result TEXT,disposition TEXT,created_at REAL);
                CREATE TABLE actions(id TEXT PRIMARY KEY,event_id TEXT,revision INTEGER,body TEXT,unsolicited INTEGER,status TEXT,created_at REAL,sent_at REAL,error TEXT);
                PRAGMA user_version=1;
            """)
            state = asdict(self.h.store.state())
            del state["remaining_queries"]
            state["remaining_calls"] = 3
            db.execute("INSERT INTO state VALUES(1,?)", (json.dumps(state),))
            db.execute("INSERT INTO messages(role,body,origin,created_at) VALUES('user','Earlier conversation','old-event',1)")
        store = Store(path, self.h.settings)
        try:
            self.assertEqual(store.db.execute("PRAGMA user_version").fetchone()[0], 2)
            self.assertEqual(store.state().remaining_calls, 3)
            self.assertEqual(store.state().remaining_queries, 20)
            self.assertEqual(store.messages()[0].text, "Earlier conversation")
        finally:
            store.close()

    async def test_reconnect_uses_restored_topic_and_nonresponse_does_not_change_it(self) -> None:
        h = self.h
        h.restart()
        h.runtime.search = self.search
        h.speak("For your small puzzle game, would discussing one constraint help?")
        await h.runtime.drain()
        self.assertEqual(h.contexts[-1].topics[0].key, "games")
        self.assertEqual(self.queries, [])
        h.now += 60
        h.decisions.append(Evaluation(Wait(None, "No worthwhile follow-up; no reminder"), "recorded-v2"))
        await h.runtime.drain()
        self.assertEqual(len(h.sent), 1)
        self.assertEqual(h.store.topics()[0].revision, 1)

    async def test_per_exploration_model_budget_blocks_further_research(self) -> None:
        h = self.h
        h.settings = replace(h.settings, exploration_calls=2)
        h.restart()
        h.runtime.search = self.search
        self.query()
        self.query()
        await h.runtime.drain()
        self.assertEqual(len(self.queries), 1)
        self.assertEqual(h.store.db.execute("SELECT calls FROM explorations").fetchone()[0], 2)


class SourceAdapterTests(unittest.IsolatedAsyncioTestCase):
    async def test_real_adapter_parses_recorded_mediawiki_response(self) -> None:
        body = {"query": {"pages": [{"pageid": 10, "lastrevid": 20, "title": "Puzzle design",
                                      "index": 1, "extract": "A synthetic excerpt."}]}}
        with patch("enthus.source.build_opener") as opener:
            opener.return_value.open.return_value = io.BytesIO(json.dumps(body).encode())
            result = await Wikipedia("en")("puzzle design")
        self.assertEqual(result.items[0].url, "https://en.wikipedia.org/w/index.php?oldid=20")
        self.assertEqual(json.loads(result.response), body)
        self.assertIn("gsrlimit=3", result.request_url)
        self.assertIn("gsrsearch=puzzle+design", result.request_url)

    async def test_oversize_response_is_rejected(self) -> None:
        with patch("enthus.source.build_opener") as opener:
            opener.return_value.open.return_value = io.BytesIO(b"x" * 262145)
            with self.assertRaises(ValueError):
                await Wikipedia("en")("puzzle design")

    async def test_api_error_response_is_retained(self) -> None:
        with patch("enthus.source.build_opener") as opener:
            opener.return_value.open.return_value = io.BytesIO(b'{"error":{"code":"maxlag"}}')
            result = await Wikipedia("en")("puzzle design")
        self.assertIn("maxlag", result.error)
        self.assertIn("maxlag", result.response)
        self.assertEqual(result.items, ())


if __name__ == "__main__":
    unittest.main()
