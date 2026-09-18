"""Single-owner SQLite state and outbox for the M2a conversation loop."""

from __future__ import annotations

import fcntl
import json
import sqlite3
from dataclasses import asdict, replace
from pathlib import Path
from typing import cast
from uuid import uuid4

from .models import (Action, Context, Evaluation, Event, Finish, Message, Note, Observation,
                     Query, Settings, SourceItem, SourceResult, Speak, State, Topic, Wait, topic_key)


class Store:
    """Keep state transitions synchronous and short on one event-loop thread."""

    def __init__(self, path: Path, settings: Settings) -> None:
        path = path.expanduser().resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        self.settings = settings
        self._lock = path.with_suffix(path.suffix + ".lock").open("a")
        try:
            fcntl.flock(self._lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            self._lock.close()
            raise RuntimeError("Another Enthus process owns this database") from None
        try:
            self.db = sqlite3.connect(path)
            self.db.row_factory = sqlite3.Row
            version = self.db.execute("PRAGMA user_version").fetchone()[0]
            if version not in (0, 1, 2):
                raise RuntimeError(f"Unsupported database version: {version}")
            self.db.execute("PRAGMA foreign_keys = ON")
            self.db.execute("PRAGMA journal_mode = WAL")
            self.db.execute("PRAGMA synchronous = FULL")
            self.db.executescript("""
                CREATE TABLE IF NOT EXISTS state (id INTEGER PRIMARY KEY CHECK(id=1), data TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS events (
                    seq INTEGER PRIMARY KEY, id TEXT UNIQUE NOT NULL, kind TEXT NOT NULL,
                    body TEXT NOT NULL, status TEXT NOT NULL, attempts INTEGER NOT NULL DEFAULT 0,
                    created_at REAL NOT NULL);
                CREATE TABLE IF NOT EXISTS messages (
                    seq INTEGER PRIMARY KEY, role TEXT NOT NULL, body TEXT NOT NULL,
                    origin TEXT UNIQUE NOT NULL, created_at REAL NOT NULL);
                CREATE TABLE IF NOT EXISTS decisions (
                    id TEXT PRIMARY KEY, event_id TEXT NOT NULL REFERENCES events(id),
                    context TEXT NOT NULL, result TEXT NOT NULL, disposition TEXT NOT NULL,
                    created_at REAL NOT NULL);
                CREATE TABLE IF NOT EXISTS actions (
                    id TEXT PRIMARY KEY REFERENCES decisions(id), event_id TEXT NOT NULL REFERENCES events(id),
                    revision INTEGER NOT NULL, body TEXT NOT NULL, unsolicited INTEGER NOT NULL,
                    status TEXT NOT NULL, created_at REAL NOT NULL, sent_at REAL, error TEXT);
                CREATE INDEX IF NOT EXISTS events_pending ON events(status, seq);
                CREATE INDEX IF NOT EXISTS actions_pending ON actions(status, created_at);
                CREATE TABLE IF NOT EXISTS topics (
                    key TEXT PRIMARY KEY, note TEXT NOT NULL, revision INTEGER NOT NULL,
                    user_event_id TEXT NOT NULL, authority TEXT NOT NULL, enabled INTEGER NOT NULL,
                    updated_at REAL NOT NULL);
                CREATE TABLE IF NOT EXISTS topic_history (
                    key TEXT NOT NULL, revision INTEGER NOT NULL, note TEXT NOT NULL,
                    user_event_id TEXT NOT NULL, authority TEXT NOT NULL, enabled INTEGER NOT NULL,
                    created_at REAL NOT NULL, PRIMARY KEY(key, revision));
                CREATE TABLE IF NOT EXISTS explorations (
                    id TEXT PRIMARY KEY, topic TEXT NOT NULL REFERENCES topics(key),
                    topic_revision INTEGER NOT NULL, status TEXT NOT NULL, reason TEXT,
                    expires_at REAL NOT NULL, calls INTEGER NOT NULL, queries INTEGER NOT NULL,
                    unsolicited INTEGER NOT NULL);
                CREATE TABLE IF NOT EXISTS observations (
                    action_id TEXT PRIMARY KEY REFERENCES actions(id),
                    follow_up_id TEXT NOT NULL REFERENCES explorations(id),
                    data TEXT NOT NULL, response TEXT, request_url TEXT, created_at REAL NOT NULL);
                CREATE TABLE IF NOT EXISTS action_sources (
                    action_id TEXT NOT NULL REFERENCES actions(id), source_id TEXT NOT NULL,
                    PRIMARY KEY(action_id, source_id));
            """)
            with self.db:
                # sqlite3's implicit transactions start on DML, not ALTER TABLE.
                # Begin explicitly so a crash cannot leave half a v1 migration.
                self.db.execute("BEGIN IMMEDIATE")
                if version < 2:
                    self.db.execute("ALTER TABLE events ADD COLUMN follow_up_id TEXT NOT NULL DEFAULT 'main'")
                    self.db.execute("ALTER TABLE actions ADD COLUMN kind TEXT NOT NULL DEFAULT 'message'")
                    self.db.execute("ALTER TABLE actions ADD COLUMN follow_up_id TEXT NOT NULL DEFAULT 'main'")
                    self.db.execute("ALTER TABLE actions ADD COLUMN refs TEXT NOT NULL DEFAULT '[]'")
                    self.db.execute("PRAGMA user_version = 2")
                initial = State(0, settings.initial_calls, False, None, None, None, None, None, None, settings.initial_queries)
                self.db.execute("INSERT OR IGNORE INTO state VALUES(1, ?)", (json.dumps(asdict(initial)),))
                stored = json.loads(self.db.execute("SELECT data FROM state WHERE id=1").fetchone()[0])
                if "remaining_queries" not in stored:
                    stored["remaining_queries"] = settings.initial_queries
                    self._put(State(**stored))
                # An interrupted model attempt remains charged; a send may have escaped.
                self.db.execute("UPDATE events SET status='pending' WHERE status='processing'")
                self.db.execute("UPDATE actions SET status='interrupted' WHERE kind='query' AND status='sending'")
                self.db.execute("UPDATE actions SET status='unknown', error='Process stopped during delivery' WHERE status='sending'")
        except BaseException:
            if hasattr(self, "db"):
                self.db.close()
            self._lock.close()
            raise

    def close(self) -> None:
        self.db.close()
        self._lock.close()

    def state(self) -> State:
        return State(**json.loads(self.db.execute("SELECT data FROM state WHERE id=1").fetchone()[0]))

    def _put(self, state: State) -> None:
        self.db.execute("UPDATE state SET data=? WHERE id=1", (json.dumps(asdict(state)),))

    def submit(self, text: str, now: float, event_id: str | None = None) -> str:
        if not text.strip() or len(text) > self.settings.max_user_characters:
            raise ValueError(f"Input must contain 1..{self.settings.max_user_characters} characters")
        identity = event_id or str(uuid4())
        with self.db:
            previous = self.db.execute("SELECT kind, body FROM events WHERE id=?", (identity,)).fetchone()
            if previous:
                if previous["kind"] != "user" or previous["body"] != text:
                    raise ValueError("An event ID cannot be reused for different input")
                return identity
            count = self.db.execute("SELECT count(*) FROM events WHERE status='pending'").fetchone()[0]
            if count >= 32:
                raise ValueError("Input queue is full; allow pending work to finish")
            self.db.execute("INSERT INTO events(id,kind,body,status,created_at) VALUES(?, 'user', ?, 'pending', ?)", (identity, text, now))
            self.db.execute("INSERT INTO messages(role,body,origin,created_at) VALUES('user',?,?,?)", (text, identity, now))
            state = self.state()
            self._put(replace(state, revision=state.revision + 1, last_user_at=now))
        return identity

    def control(self, command: str, now: float, value: float | None = None) -> None:
        with self.db:
            state = self.state()
            updates: dict[str, object] = {"revision": state.revision + 1}
            if command == "start":
                updates.update(initiative_enabled=True, expires_at=now + self.settings.grant_seconds,
                               wake_at=now + self.settings.wake_interval)
            elif command == "stop":
                updates.update(initiative_enabled=False, wake_at=None, expires_at=None)
                self.db.execute("UPDATE events SET status='done' WHERE kind='wake' AND status='pending'")
                for row in self.db.execute("SELECT id FROM explorations WHERE status='active'").fetchall():
                    self._close_exploration(row[0], "Host cancelled initiative")
            elif command == "mute":
                updates["mute_until"] = -1 if value is None else now + value
            elif command == "resume":
                updates["mute_until"] = None
                if state.initiative_enabled and state.wake_at is None:
                    updates["wake_at"] = now + self.settings.wake_interval
            elif command in {"budget", "query-budget"}:
                if value is None or value < 0 or not float(value).is_integer():
                    raise ValueError("Budget must be a nonnegative integer")
                updates["remaining_calls" if command == "budget" else "remaining_queries"] = int(value)
                updates["last_error"] = None
            else:
                raise ValueError("Unknown control")
            if command == "mute" and value is not None and not 0 < value <= 31536000:
                raise ValueError("Mute duration must be positive and at most one year")
            self._put(replace(state, **updates))
            self.db.execute("INSERT INTO events(id,kind,body,status,created_at) VALUES(?, 'control', ?, 'done', ?)",
                            (str(uuid4()), json.dumps({"command": command, "value": value}), now))

    def enqueue_due(self, now: float) -> None:
        with self.db:
            state = self.state()
            if not state.initiative_enabled:
                return
            if state.expires_at is not None and now >= state.expires_at:
                self._put(replace(state, initiative_enabled=False, wake_at=None, revision=state.revision + 1))
            elif state.wake_at is not None and now >= state.wake_at:
                self.db.execute("INSERT INTO events(id,kind,body,status,created_at) VALUES(?, 'wake', '', 'pending', ?)", (str(uuid4()), now))
                self._put(replace(state, wake_at=None))

    def claim(self) -> Event | None:
        with self.db:
            row = self.db.execute("SELECT * FROM events WHERE status='pending' AND kind='user' ORDER BY seq DESC LIMIT 1").fetchone()
            if row:
                # Coalesce triggers, not conversation history, so rapid typing is retained.
                self.db.execute("UPDATE events SET status='done' WHERE status='pending' AND kind='user' AND seq<?", (row["seq"],))
            else:
                row = self.db.execute("SELECT * FROM events WHERE status='pending' AND kind IN ('result','wake') ORDER BY CASE kind WHEN 'result' THEN 0 ELSE 1 END, seq LIMIT 1").fetchone()
            if not row:
                return None
            self.db.execute("UPDATE events SET status='processing' WHERE id=?", (row["id"],))
            return Event(row["id"], row["kind"], row["body"], row["follow_up_id"])

    def reserve_call(self, event: Event) -> bool:
        with self.db:
            state = self.state()
            if event.follow_up_id != "main":
                exploration = self.exploration(event.follow_up_id)
                if exploration is None or exploration["status"] != "active" or exploration["calls"] >= self.settings.exploration_calls:
                    self._close_exploration(event.follow_up_id, "Exploration decision budget exhausted or closed")
                    return False
                self.db.execute("UPDATE explorations SET calls=calls+1 WHERE id=?", (event.follow_up_id,))
            if state.remaining_calls <= 0:
                self._put(replace(state, initiative_enabled=False, wake_at=None, last_error="Decision budget exhausted; use /budget to grant more"))
                self.db.execute("UPDATE events SET status='done' WHERE id=?", (event.id,))
                self._close_exploration(event.follow_up_id, "Shared decision budget exhausted")
                return False
            self._put(replace(state, remaining_calls=state.remaining_calls - 1))
            self.db.execute("UPDATE events SET attempts=attempts+1 WHERE id=?", (event.id,))
            return True

    def messages(self) -> tuple[Message, ...]:
        rows = self.db.execute("SELECT role,body FROM messages ORDER BY seq DESC LIMIT ?", (self.settings.context_messages,)).fetchall()
        selected: list[Message] = []
        remaining = self.settings.context_characters
        for row in rows:
            if len(row["body"]) > remaining:
                break
            selected.append(Message(row["role"], row["body"]))
            remaining -= len(row["body"])
        return tuple(reversed(selected))

    def defer(self, event: Event, until: float | None) -> None:
        with self.db:
            state = self.state()
            self.db.execute("UPDATE events SET status='done' WHERE id=?", (event.id,))
            self._put(replace(state, wake_at=until if state.initiative_enabled else None))

    def record(self, context: Context, evaluation: Evaluation | None, now: float, error: str | None = None) -> None:
        with self.db:
            state = self.state()
            stale = state.revision != context.state.revision
            identity = str(uuid4())
            result = {"error": error} if evaluation is None else {"type": type(evaluation.decision).__name__, **asdict(evaluation)}
            self.db.execute("INSERT INTO decisions VALUES(?,?,?,?,?,?)", (
                identity, context.event.id,
                json.dumps({"snapshot": asdict(context), "settings": asdict(self.settings)}),
                json.dumps(result), "stale" if stale else "error" if error else "accepted", now,
            ))
            event_status = "pending" if stale and context.event.kind in {"user", "result"} else "done"
            self.db.execute("UPDATE events SET status=? WHERE id=?", (event_status, context.event.id))
            if stale:
                # A timed mute/control can arrive while a wake is evaluating.
                # Its result is obsolete, but the enabled follow-up still needs
                # a fresh evaluation opportunity after this consumed wake.
                if context.event.kind == "wake" and state.initiative_enabled and state.wake_at is None:
                    self._put(replace(state, wake_at=now + self.settings.wake_interval))
                return
            wake = now + self.settings.wake_interval if state.initiative_enabled else None
            if evaluation is None:
                self._put(replace(state, wake_at=wake, last_error=error))
                self._close_exploration(context.event.follow_up_id, "Evaluation failed")
                return
            acknowledgement = ""
            control = evaluation.control
            if control is not None and context.event.kind == "user" and control.user_event_id == context.event.id:
                if control.command == "mute":
                    state = replace(state, mute_until=-1 if control.seconds is None else now + control.seconds,
                                    revision=state.revision + 1)
                    duration = "until /resume" if control.seconds is None else f"for {control.seconds:g} seconds"
                    acknowledgement = f"[Control: unsolicited conversation muted {duration}; direct replies remain available.]"
                else:
                    state = replace(state, initiative_enabled=False, wake_at=None, expires_at=None, revision=state.revision + 1)
                    wake = None
                    for row in self.db.execute("SELECT id FROM explorations WHERE status='active'").fetchall():
                        self._close_exploration(row[0], "User requested cancellation")
                    acknowledgement = "[Control: initiative cancelled; direct replies remain available.]"
                self._put(state)
            for note in evaluation.notes:
                if context.event.kind == "user" and note.user_event_id == context.event.id:
                    self._note(note, now, "model")
            state = self.state()
            decision = evaluation.decision
            # A control acknowledgement is a direct response, never an unsolicited
            # exception. Do not let a paired query/finish undo the user's boundary.
            if acknowledgement:
                text = decision.text if isinstance(decision, Speak) else ""
                decision = Speak((text[:1700] + "\n" + acknowledgement).strip(), "Acknowledge user control")
            if isinstance(decision, Speak):
                unsolicited = self.unsolicited(context.event)
                items = self.reference_items(decision.references, now)
                invalid = (len(items) != len(set(decision.references))
                           or (context.event.kind == "result" and not decision.references)
                           or (unsolicited and self.already_shared(decision.references)))
                if invalid:
                    self.db.execute("UPDATE decisions SET disposition='rejected' WHERE id=?", (identity,))
                    self._put(replace(state, wake_at=wake, last_error="Missing, stale or already shared source references"))
                    self._close_exploration(context.event.follow_up_id, "Invalid finding candidate")
                    return
                text = decision.text
                if items:
                    text += "\n\nSources:\n" + "\n".join(item.url for item in items)
                self.db.execute("INSERT INTO actions(id,event_id,revision,body,unsolicited,status,created_at,follow_up_id,refs) VALUES(?,?,?,?,?,'pending',?,?,?)",
                                (identity, context.event.id, state.revision, text, unsolicited, now,
                                 context.event.follow_up_id, json.dumps(decision.references)))
                self.db.executemany("INSERT INTO action_sources VALUES(?,?)", [(identity, ref) for ref in set(decision.references)])
            elif isinstance(decision, Query):
                error = self._propose_query(identity, context, decision, now)
                if error:
                    self.db.execute("UPDATE decisions SET disposition='rejected' WHERE id=?", (identity,))
                    self._close_exploration(context.event.follow_up_id, error)
                    self._put(replace(state, wake_at=wake, last_error=error))
                    return
            elif isinstance(decision, Wait):
                # A model may slow observation down, but cannot raise host frequency.
                wake = now + max(self.settings.wake_interval, decision.seconds) if state.initiative_enabled and decision.seconds is not None else None
                self._close_exploration(context.event.follow_up_id, "Wait; retain observations for later context")
            elif isinstance(decision, Finish):
                if context.event.follow_up_id == "main":
                    state = replace(state, initiative_enabled=False)
                    wake = None
                self._close_exploration(context.event.follow_up_id, decision.reason)
            self._put(replace(state, wake_at=wake, last_error=None))

    def interrupted(self, event: Event) -> None:
        with self.db:
            self.db.execute("UPDATE events SET status='pending' WHERE id=? AND status='processing'", (event.id,))

    def pending_action(self) -> Action | None:
        row = self.db.execute("SELECT * FROM actions WHERE status='pending' ORDER BY created_at, rowid LIMIT 1").fetchone()
        return None if row is None else self._action(row)

    def discard_action(self, action: Action, reason: str, until: float | None, stale: bool = False) -> None:
        with self.db:
            self.db.execute("UPDATE actions SET status='cancelled', error=? WHERE id=?", (reason, action.id))
            self._close_exploration(action.follow_up_id, reason)
            state = self.state()
            if stale and not action.unsolicited and action.follow_up_id == "main":
                self.db.execute("UPDATE events SET status='pending' WHERE id=?", (action.event_id,))
            if not stale and action.unsolicited:
                self._put(replace(state, wake_at=until if state.initiative_enabled else None))

    def sending(self, action: Action) -> None:
        with self.db:
            self.db.execute("UPDATE actions SET status='sending' WHERE id=? AND status='pending'", (action.id,))

    def finish_action(self, action_id: str, status: str, now: float, error: str | None = None) -> None:
        if status not in {"sent", "failed", "unknown"}:
            raise ValueError("Unsupported delivery outcome")
        with self.db:
            row = self.db.execute("SELECT * FROM actions WHERE id=?", (action_id,)).fetchone()
            if row is None or row["status"] not in {"sending", "unknown"}:
                raise ValueError("Only in-flight or unknown actions can be resolved")
            self.db.execute("UPDATE actions SET status=?, sent_at=?, error=? WHERE id=?", (status, now if status == "sent" else None, error, action_id))
            if status != "unknown":
                self._close_exploration(row["follow_up_id"], "Delivery " + status)
            if status == "sent":
                self.db.execute("INSERT OR IGNORE INTO messages(role,body,origin,created_at) VALUES('assistant',?,?,?)", (row["body"], action_id, now))
                if row["unsolicited"]:
                    self._put(replace(self.state(), last_opening_at=now))
            # Send acknowledgements are terminal observations, not reasons to speak again.
            self.db.execute("INSERT INTO events(id,kind,body,status,created_at) VALUES(?, 'outcome', ?, 'done', ?) ON CONFLICT(id) DO UPDATE SET body=excluded.body", (
                "outcome:" + action_id, json.dumps({"action_id": action_id, "follow_up_id": row["follow_up_id"], "status": status, "error": error}), now,
            ))

    def unknown_actions(self) -> list[str]:
        return [row[0] for row in self.db.execute("SELECT id FROM actions WHERE status='unknown' ORDER BY created_at")]

    def opening_count(self, since: float) -> int:
        # An unconfirmed attempt still consumes a slot until the host verifies failure.
        return cast(int, self.db.execute("SELECT count(*) FROM actions WHERE kind='message' AND unsolicited=1 AND status IN ('sending','sent','unknown') AND COALESCE(sent_at,created_at)>=?", (since,)).fetchone()[0])

    @staticmethod
    def _action(row: sqlite3.Row) -> Action:
        return Action(row["id"], row["event_id"], row["revision"], row["body"], bool(row["unsolicited"]),
                      row["kind"], row["follow_up_id"], tuple(json.loads(row["refs"])))

    def exploration(self, identity: str) -> sqlite3.Row | None:
        return self.db.execute("SELECT * FROM explorations WHERE id=?", (identity,)).fetchone()

    def unsolicited(self, event: Event) -> bool:
        row = self.exploration(event.follow_up_id)
        return bool(row["unsolicited"]) if row else event.kind == "wake"

    def _close_exploration(self, identity: str, reason: str) -> None:
        if identity == "main":
            return
        self.db.execute("UPDATE explorations SET status='closed', reason=? WHERE id=? AND status='active'", (reason, identity))
        self.db.execute("UPDATE events SET status='done' WHERE follow_up_id=? AND status IN ('pending','processing')", (identity,))
        self.db.execute("UPDATE actions SET status='cancelled', error=? WHERE follow_up_id=? AND status='pending'", (reason, identity))

    def research_allowed(self, now: float) -> bool:
        state = self.state()
        return bool(self.settings.wikipedia and state.initiative_enabled and state.expires_at is not None
                    and now < state.expires_at)

    def maintain_research(self, now: float) -> None:
        with self.db:
            for row in self.db.execute("SELECT * FROM explorations WHERE status='active'").fetchall():
                topic = self.db.execute("SELECT revision,enabled FROM topics WHERE key=?", (row["topic"],)).fetchone()
                if (not self.research_allowed(now) or now >= row["expires_at"] or not topic
                        or not topic["enabled"] or topic["revision"] != row["topic_revision"]):
                    self._close_exploration(row["id"], "Grant, topic or exploration expired/revoked")
        for row in self.db.execute("SELECT * FROM actions WHERE status='interrupted'").fetchall():
            self.finish_query(self._action(row), None, now, "Query interrupted before durable result")

    def set_topic(self, key: str, text: str, now: float, enabled: bool = True) -> None:
        note = Note(key, text, str(uuid4()))
        with self.db:
            self.db.execute("INSERT INTO events(id,kind,body,status,created_at) VALUES(?,'control',?,'done',?)",
                            (note.user_event_id, json.dumps({"topic": key, "text": text, "enabled": enabled}), now))
            self._note(note, now, "host", enabled)

    def drop_topic(self, key: str, now: float) -> None:
        topic_key(key)
        row = self.db.execute("SELECT note FROM topics WHERE key=?", (key,)).fetchone()
        if row is None:
            raise ValueError("Unknown topic")
        self.set_topic(key, row[0], now, False)

    def _note(self, note: Note, now: float, authority: str, enabled: bool = True) -> None:
        old = self.db.execute("SELECT * FROM topics WHERE key=?", (note.key,)).fetchone()
        if old and authority == "model" and old["authority"] == "host":
            return  # A model summary never silently replaces an explicit correction.
        if old and old["note"] == note.text and bool(old["enabled"]) == enabled and old["authority"] == authority:
            return
        count = self.db.execute("SELECT count(*) FROM topics WHERE enabled=1").fetchone()[0]
        if enabled and (old is None or not old["enabled"]) and count >= 16:
            if authority == "host":
                raise ValueError("At most sixteen enabled topics; drop one first")
            return
        revision = old["revision"] + 1 if old else 1
        values = (note.key, note.text, revision, note.user_event_id, authority, int(enabled), now)
        self.db.execute("INSERT INTO topics VALUES(?,?,?,?,?,?,?) ON CONFLICT(key) DO UPDATE SET note=excluded.note,revision=excluded.revision,user_event_id=excluded.user_event_id,authority=excluded.authority,enabled=excluded.enabled,updated_at=excluded.updated_at", values)
        self.db.execute("INSERT INTO topic_history VALUES(?,?,?,?,?,?,?)",
                        (note.key, revision, note.text, note.user_event_id, authority, int(enabled), now))
        for row in self.db.execute("SELECT id FROM explorations WHERE status='active' AND topic=?", (note.key,)).fetchall():
            self._close_exploration(row[0], "Topic corrected")
        state = self.state()
        wake = state.wake_at
        if state.initiative_enabled and wake is None:
            wake = now + self.settings.wake_interval
        self._put(replace(state, revision=state.revision + 1, wake_at=wake))

    def topics(self) -> tuple[Topic, ...]:
        return tuple(Topic(row["key"], row["note"], row["revision"], row["user_event_id"], row["authority"])
                     for row in self.db.execute("SELECT * FROM topics WHERE enabled=1 ORDER BY updated_at DESC,key LIMIT 8"))

    def observations(self, now: float) -> tuple[Observation, ...]:
        rows = self.db.execute("""SELECT o.data FROM observations o JOIN explorations e ON e.id=o.follow_up_id
            JOIN topics t ON t.key=e.topic WHERE t.enabled=1 AND t.revision=e.topic_revision AND o.created_at>=?
            ORDER BY o.created_at DESC,o.rowid DESC LIMIT 3""", (now - 86400,)).fetchall()
        result: list[Observation] = []
        for row in reversed(rows):
            data = json.loads(row[0])
            data["items"] = tuple(SourceItem(**item) for item in data["items"])
            result.append(Observation(**data))
        return tuple(result)

    def context(self, event: Event, now: float) -> Context:
        return Context(event, self.state(), self.messages(), now, self.topics(), self.observations(now), self.research_allowed(now))

    def reference_items(self, refs: tuple[str, ...], now: float) -> tuple[SourceItem, ...]:
        known = {item.id: item for observation in self.observations(now) for item in observation.items}
        return tuple(known[ref] for ref in dict.fromkeys(refs) if ref in known)

    def already_shared(self, refs: tuple[str, ...]) -> bool:
        return any(self.db.execute("SELECT 1 FROM action_sources s JOIN actions a ON a.id=s.action_id WHERE s.source_id=? AND a.status IN ('sent','sending','unknown') LIMIT 1", (ref,)).fetchone() for ref in refs)

    def _propose_query(self, identity: str, context: Context, query: Query, now: float) -> str | None:
        if not self.research_allowed(now):
            return "Research requires a source and current host grant"
        topic = self.db.execute("SELECT * FROM topics WHERE key=? AND enabled=1", (query.topic,)).fetchone()
        if topic is None:
            return "Research must reference an enabled topic"
        follow_up = context.event.follow_up_id
        if follow_up == "main":
            if self.db.execute("SELECT 1 FROM explorations WHERE status='active'").fetchone():
                return "Only one active exploration is allowed"
            follow_up = str(uuid4())
            self.db.execute("INSERT INTO explorations VALUES(?,?,?,'active',NULL,?,1,0,?)",
                            (follow_up, query.topic, topic["revision"], min(now + self.settings.exploration_seconds,
                             self.state().expires_at), self.unsolicited(context.event)))
        else:
            row = self.exploration(follow_up)
            if row is None or row["status"] != "active" or row["topic"] != query.topic:
                return "Cannot redirect or reopen an exploration"
        self.db.execute("INSERT INTO actions(id,event_id,revision,body,unsolicited,status,created_at,kind,follow_up_id) VALUES(?,?,?,?,?,'pending',?,'query',?)",
                        (identity, context.event.id, self.state().revision, json.dumps(asdict(query)),
                         self.unsolicited(context.event), now, follow_up))
        return None

    def reserve_query(self, action: Action, now: float) -> bool:
        with self.db:
            row, state = self.exploration(action.follow_up_id), self.state()
            if (not self.research_allowed(now) or row is None or row["status"] != "active"
                    or now >= row["expires_at"] or row["queries"] >= self.settings.exploration_queries
                    or row["calls"] >= self.settings.exploration_calls
                    or state.remaining_queries <= 0 or state.remaining_calls <= 0):
                self._close_exploration(action.follow_up_id, "Research scope or budget exhausted")
                self.db.execute("UPDATE actions SET status='cancelled',error='Research scope or budget exhausted' WHERE id=?", (action.id,))
                return False
            self._put(replace(state, remaining_queries=state.remaining_queries - 1))
            self.db.execute("UPDATE explorations SET queries=queries+1 WHERE id=?", (action.follow_up_id,))
            self.db.execute("UPDATE actions SET status='sending' WHERE id=?", (action.id,))
            return True

    def finish_query(self, action: Action, result: SourceResult | None, now: float, error: str | None = None) -> None:
        with self.db:
            current = self.db.execute("SELECT status FROM actions WHERE id=?", (action.id,)).fetchone()
            if current is None or current[0] not in {"sending", "interrupted"}:
                return  # Duplicate completion must not enqueue a second evaluation.
            row = self.exploration(action.follow_up_id)
            query = json.loads(action.text)["query"]
            active = row["status"] == "active" and now < row["expires_at"] and self.research_allowed(now)
            observation = Observation(action.id, action.follow_up_id, row["topic"], query, now,
                                      result.items if result and active else (), error if active else "Late result discarded")
            self.db.execute("INSERT INTO observations VALUES(?,?,?,?,?,?)", (
                action.id, action.follow_up_id, json.dumps(asdict(observation)),
                result.response if result else None, result.request_url if result else None, now))
            self.db.execute("UPDATE actions SET status=?,error=? WHERE id=?", ("failed" if error else "done", error, action.id))
            if not active:
                self._close_exploration(action.follow_up_id, "Late result after closure/expiry")
            self.db.execute("INSERT INTO events(id,kind,body,status,created_at,follow_up_id) VALUES(?,'result',?,?,?,?)",
                            ("result:" + action.id, json.dumps({"action_id": action.id, "follow_up_id": action.follow_up_id}),
                             "pending" if active else "done", now, action.follow_up_id))
