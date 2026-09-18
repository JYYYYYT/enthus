"""Small internal records; no plugin hierarchy is needed for the prototype."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Literal
from zoneinfo import ZoneInfo


@dataclass(frozen=True)
class Settings:
    timezone: str = "Asia/Shanghai"
    initial_calls: int = 100
    wake_interval: float = 900
    grant_seconds: float = 86400
    daily_openings: int = 2
    cooldown_seconds: float = 21600
    active_chat_seconds: float = 300
    quiet_start: int = 22
    quiet_end: int = 9
    model_timeout: float = 30
    send_timeout: float = 10
    context_messages: int = 20
    context_characters: int = 12000
    max_user_characters: int = 4000
    wikipedia: str | None = None
    initial_queries: int = 20
    exploration_queries: int = 2
    exploration_calls: int = 4
    exploration_seconds: float = 600
    source_timeout: float = 10

    def __post_init__(self) -> None:
        ZoneInfo(self.timezone)
        if self.wikipedia not in {None, "en", "zh"}:
            raise ValueError("Wikipedia language must be en or zh")
        for name in ("initial_queries", "exploration_queries", "exploration_calls"):
            if type(getattr(self, name)) is not int or getattr(self, name) < 0:
                raise ValueError(f"{name} must be a nonnegative integer")
        for value in (self.exploration_seconds, self.source_timeout):
            if not math.isfinite(value) or value <= 0:
                raise ValueError("Research time limits must be positive and finite")
        for name in ("initial_calls", "daily_openings"):
            value = getattr(self, name)
            if type(value) is not int or value < 0:
                raise ValueError(f"{name} must be a nonnegative integer")
        for name in ("wake_interval", "grant_seconds", "model_timeout", "send_timeout",
                     "context_messages", "context_characters", "max_user_characters"):
            value = getattr(self, name)
            if not math.isfinite(value) or value <= 0:
                raise ValueError(f"{name} must be positive and finite")
        for name in ("context_messages", "context_characters", "max_user_characters"):
            if type(getattr(self, name)) is not int:
                raise ValueError(f"{name} must be an integer")
        if self.context_characters < max(2000, self.max_user_characters):
            raise ValueError("Context must fit at least one complete message")
        for name in ("cooldown_seconds", "active_chat_seconds"):
            value = getattr(self, name)
            if not math.isfinite(value) or value < 0:
                raise ValueError(f"{name} must be nonnegative and finite")
        if not all(type(hour) is int and 0 <= hour <= 23 for hour in (self.quiet_start, self.quiet_end)):
            raise ValueError("Quiet hours must be integers in 0..23")


@dataclass(frozen=True)
class State:
    revision: int
    remaining_calls: int
    initiative_enabled: bool
    wake_at: float | None
    expires_at: float | None
    mute_until: float | None  # -1 means muted until an explicit resume.
    last_user_at: float | None
    last_opening_at: float | None
    last_error: str | None
    remaining_queries: int = 20


@dataclass(frozen=True)
class Message:
    role: Literal["user", "assistant"]
    text: str


@dataclass(frozen=True)
class Event:
    id: str
    kind: Literal["user", "wake", "result"]
    text: str
    follow_up_id: str = "main"


@dataclass(frozen=True)
class Context:
    event: Event
    state: State
    messages: tuple[Message, ...]
    now: float
    topics: tuple[Topic, ...] = ()
    observations: tuple[Observation, ...] = ()
    research_enabled: bool = False


@dataclass(frozen=True)
class Speak:
    text: str
    reason: str
    references: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.text, str) or not self.text.strip() or len(self.text) > 2000:
            raise ValueError("A message must contain 1..2000 characters")
        _reason(self.reason)
        if (not isinstance(self.references, tuple) or len(self.references) > 3
                or any(not isinstance(ref, str) or not ref or len(ref) > 160 for ref in self.references)):
            raise ValueError("Use up to three source IDs")


@dataclass(frozen=True)
class Wait:
    seconds: float | None
    reason: str

    def __post_init__(self) -> None:
        if self.seconds is not None and (
            isinstance(self.seconds, bool) or not math.isfinite(self.seconds)
            or not 1 <= self.seconds <= 86400
        ):
            raise ValueError("Wait must be event-only or between 1 and 86400 seconds")
        _reason(self.reason)


@dataclass(frozen=True)
class Finish:
    reason: str

    def __post_init__(self) -> None:
        _reason(self.reason)


def _reason(value: str) -> None:
    if not isinstance(value, str) or not value.strip() or len(value) > 500:
        raise ValueError("A decision needs a brief reason of at most 500 characters")


@dataclass(frozen=True)
class Query:
    topic: str
    query: str
    reason: str

    def __post_init__(self) -> None:
        topic_key(self.topic)
        if not isinstance(self.query, str) or not self.query.strip() or len(self.query) > 200:
            raise ValueError("A query needs 1..200 characters")
        _reason(self.reason)


def topic_key(key: str) -> None:
    if not isinstance(key, str) or re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,39}", key) is None:
        raise ValueError("Topic keys use 1..40 lowercase letters, digits, underscores or hyphens")


@dataclass(frozen=True)
class Note:
    key: str
    text: str
    user_event_id: str

    def __post_init__(self) -> None:
        topic_key(self.key)
        if not isinstance(self.text, str) or not self.text.strip() or len(self.text) > 600:
            raise ValueError("A topic note needs 1..600 characters")
        if not isinstance(self.user_event_id, str) or not self.user_event_id:
            raise ValueError("A note needs a user event reference")


@dataclass(frozen=True)
class Topic:
    key: str
    text: str
    revision: int
    user_event_id: str
    authority: str


@dataclass(frozen=True)
class SourceItem:
    id: str
    title: str
    url: str
    excerpt: str
    revision: int


@dataclass(frozen=True)
class SourceResult:
    query: str
    request_url: str
    items: tuple[SourceItem, ...]
    response: str
    error: str | None = None


@dataclass(frozen=True)
class Observation:
    action_id: str
    follow_up_id: str
    topic: str
    query: str
    retrieved_at: float
    items: tuple[SourceItem, ...]
    error: str | None


Decision = Speak | Wait | Finish | Query


@dataclass(frozen=True)
class NarrowControl:
    command: Literal["mute", "stop"]
    user_event_id: str
    seconds: float | None = None

    def __post_init__(self) -> None:
        if self.command not in {"mute", "stop"} or not isinstance(self.user_event_id, str) or not self.user_event_id:
            raise ValueError("Only user-linked mute/stop controls are accepted")
        if self.seconds is not None and (self.command != "mute" or type(self.seconds) not in (int, float)
                                         or not math.isfinite(self.seconds) or not 0 < self.seconds <= 31536000):
            raise ValueError("Only mute can carry a duration, at most one year")


@dataclass(frozen=True)
class Evaluation:
    decision: Decision
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    notes: tuple[Note, ...] = ()
    control: NarrowControl | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.decision, (Speak, Wait, Finish, Query)):
            raise ValueError("Unsupported decision")
        if not isinstance(self.model, str) or not self.model.strip():
            raise ValueError("Model identity is required")
        for count in (self.input_tokens, self.output_tokens):
            if type(count) is not int or count < 0:
                raise ValueError("Usage counts must be nonnegative integers")
        if not isinstance(self.notes, tuple) or len(self.notes) > 2 or any(not isinstance(n, Note) for n in self.notes):
            raise ValueError("At most two validated notes per evaluation")
        if self.control is not None and not isinstance(self.control, NarrowControl):
            raise ValueError("Invalid narrowing control")


@dataclass(frozen=True)
class Action:
    id: str
    event_id: str
    revision: int
    text: str
    unsolicited: bool
    kind: str = "message"
    follow_up_id: str = "main"
    references: tuple[str, ...] = ()
