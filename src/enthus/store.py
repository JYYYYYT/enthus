"""Single-owner SQLite state and outbox for the M2a conversation loop."""

from __future__ import annotations

import fcntl
import json
import sqlite3
from dataclasses import asdict, replace
from pathlib import Path
from typing import cast
from uuid import uuid4

from .models import Action, Context, Evaluation, Event, Finish, Message, Settings, Speak, State, Wait


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
            if version not in (0, 1):
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
                PRAGMA user_version = 1;
            """)
            with self.db:
                initial = State(0, settings.initial_calls, False, None, None, None, None, None, None)
                self.db.execute("INSERT OR IGNORE INTO state VALUES(1, ?)", (json.dumps(asdict(initial)),))
                # An interrupted model attempt remains charged; a send may have escaped.
                self.db.execute("UPDATE events SET status='pending' WHERE status='processing'")
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
            elif command == "mute":
                updates["mute_until"] = -1 if value is None else now + value
            elif command == "resume":
                updates["mute_until"] = None
                if state.initiative_enabled and state.wake_at is None:
                    updates["wake_at"] = now + self.settings.wake_interval
            elif command == "budget":
                if value is None or value < 0 or not float(value).is_integer():
                    raise ValueError("Budget must be a nonnegative integer")
                updates.update(remaining_calls=int(value), last_error=None)
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
                row = self.db.execute("SELECT * FROM events WHERE status='pending' AND kind='wake' ORDER BY seq LIMIT 1").fetchone()
            if not row:
                return None
            self.db.execute("UPDATE events SET status='processing' WHERE id=?", (row["id"],))
            return Event(row["id"], row["kind"], row["body"])

    def reserve_call(self, event: Event) -> bool:
        with self.db:
            state = self.state()
            if state.remaining_calls <= 0:
                self._put(replace(state, initiative_enabled=False, wake_at=None, last_error="Decision budget exhausted; use /budget to grant more"))
                self.db.execute("UPDATE events SET status='done' WHERE id=?", (event.id,))
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
            event_status = "pending" if stale and context.event.kind == "user" else "done"
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
                return
            decision = evaluation.decision
            if isinstance(decision, Speak):
                self.db.execute("INSERT INTO actions(id,event_id,revision,body,unsolicited,status,created_at) VALUES(?,?,?,?,?,'pending',?)",
                                (identity, context.event.id, state.revision, decision.text, context.event.kind == "wake", now))
            elif isinstance(decision, Wait):
                # A model may slow observation down, but cannot raise host frequency.
                wake = now + max(self.settings.wake_interval, decision.seconds) if state.initiative_enabled and decision.seconds is not None else None
            elif isinstance(decision, Finish):
                state = replace(state, initiative_enabled=False)
                wake = None
            self._put(replace(state, wake_at=wake, last_error=None))

    def interrupted(self, event: Event) -> None:
        with self.db:
            self.db.execute("UPDATE events SET status='pending' WHERE id=? AND status='processing'", (event.id,))

    def pending_action(self) -> Action | None:
        row = self.db.execute("SELECT * FROM actions WHERE status='pending' ORDER BY created_at, rowid LIMIT 1").fetchone()
        return None if row is None else Action(row["id"], row["event_id"], row["revision"], row["body"], bool(row["unsolicited"]))

    def discard_action(self, action: Action, reason: str, until: float | None, stale: bool = False) -> None:
        with self.db:
            self.db.execute("UPDATE actions SET status='cancelled', error=? WHERE id=?", (reason, action.id))
            state = self.state()
            if stale and not action.unsolicited:
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
            if status == "sent":
                self.db.execute("INSERT OR IGNORE INTO messages(role,body,origin,created_at) VALUES('assistant',?,?,?)", (row["body"], action_id, now))
                if row["unsolicited"]:
                    self._put(replace(self.state(), last_opening_at=now))
            # Send acknowledgements are terminal observations, not reasons to speak again.
            self.db.execute("INSERT INTO events(id,kind,body,status,created_at) VALUES(?, 'outcome', ?, 'done', ?) ON CONFLICT(id) DO UPDATE SET body=excluded.body", (
                "outcome:" + action_id, json.dumps({"action_id": action_id, "follow_up_id": "main", "status": status, "error": error}), now,
            ))

    def unknown_actions(self) -> list[str]:
        return [row[0] for row in self.db.execute("SELECT id FROM actions WHERE status='unknown' ORDER BY created_at")]

    def opening_count(self, since: float) -> int:
        # An unconfirmed attempt still consumes a slot until the host verifies failure.
        return cast(int, self.db.execute("SELECT count(*) FROM actions WHERE unsolicited=1 AND status IN ('sending','sent','unknown') AND COALESCE(sent_at,created_at)>=?", (since,)).fetchone()[0])
