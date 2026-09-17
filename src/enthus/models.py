"""Small internal records; no plugin hierarchy is needed for the prototype."""

from __future__ import annotations

import math
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

    def __post_init__(self) -> None:
        ZoneInfo(self.timezone)
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


@dataclass(frozen=True)
class Message:
    role: Literal["user", "assistant"]
    text: str


@dataclass(frozen=True)
class Event:
    id: str
    kind: Literal["user", "wake"]
    text: str


@dataclass(frozen=True)
class Context:
    event: Event
    state: State
    messages: tuple[Message, ...]
    now: float


@dataclass(frozen=True)
class Speak:
    text: str
    reason: str

    def __post_init__(self) -> None:
        if not isinstance(self.text, str) or not self.text.strip() or len(self.text) > 2000:
            raise ValueError("A message must contain 1..2000 characters")
        _reason(self.reason)


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


Decision = Speak | Wait | Finish


@dataclass(frozen=True)
class Evaluation:
    decision: Decision
    model: str
    input_tokens: int = 0
    output_tokens: int = 0

    def __post_init__(self) -> None:
        if not isinstance(self.decision, (Speak, Wait, Finish)):
            raise ValueError("Unsupported decision")
        if not isinstance(self.model, str) or not self.model.strip():
            raise ValueError("Model identity is required")
        for count in (self.input_tokens, self.output_tokens):
            if type(count) is not int or count < 0:
                raise ValueError("Usage counts must be nonnegative integers")


@dataclass(frozen=True)
class Action:
    id: str
    event_id: str
    revision: int
    text: str
    unsolicited: bool
