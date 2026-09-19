"""Bounded session state, independent of model transport and browser devices."""

from __future__ import annotations

import base64
import math
import time
import uuid
from collections import deque
from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class LiveLimits:
    seconds: float = 120
    input_audio_bytes: int = 3_840_000
    frames: int = 120
    frame_bytes: int = 100_000
    output_audio_bytes: int = 2_880_000
    observation_age: float = 1
    queue_seconds: float = 2
    send_timeout: float = 1
    setup_timeout: float = 10
    heartbeat_timeout: float = 5


class SessionEnded(Exception):
    """A visible stop condition, safe to report without transport credentials."""


@dataclass
class LiveSession:
    limits: LiveLimits = field(default_factory=LiveLimits)
    session_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    started: float = field(default_factory=time.monotonic)
    active: bool = True
    grants: dict[str, bool] = field(default_factory=lambda: {"audio": True, "video": True})
    versions: dict[str, int] = field(default_factory=lambda: {"audio": 0, "video": 0})
    audio_bytes: int = 0
    frame_count: int = 0
    output_bytes: int = 0
    output_turn: int = 1
    chunk: int = 0
    last_frame: float = -math.inf
    invalid_outputs: set[int] = field(default_factory=set)
    trace: deque[dict[str, Any]] = field(default_factory=lambda: deque(maxlen=4096))

    def record(self, kind: str, **data: Any) -> dict[str, Any]:
        event = {"kind": kind, "session_id": self.session_id,
                 "at": time.time(), "elapsed": time.monotonic() - self.started, **data}
        self.trace.append(event)
        return event

    def configuration(self) -> dict[str, Any]:
        return {"session_id": self.session_id, "limits": asdict(self.limits)}

    def require_active(self) -> None:
        if not self.active:
            raise SessionEnded("session_ended")
        if time.monotonic() - self.started >= self.limits.seconds:
            raise SessionEnded("duration_limit")

    def stop(self, reason: str) -> dict[str, Any]:
        self.active = False
        self.grants = {"audio": False, "video": False}
        return self.record("ended", reason=reason)

    def revoke(self, sensor: str) -> dict[str, Any]:
        self.require_active()
        if sensor not in self.grants:
            raise ValueError("unknown sensor")
        self.grants[sensor] = False
        # Any pending response may depend on the now-revoked input.
        self.invalid_outputs.add(self.output_turn)
        return self.record("revoked", sensor=sensor, output_id=self.output_turn)

    def stop_speech(self, outputs: list[int]) -> dict[str, Any]:
        self.require_active()
        valid = {n for n in outputs if type(n) is int and 1 <= n <= self.output_turn}
        self.invalid_outputs.update(valid)
        return self.record("cancelled", output_ids=sorted(valid))

    def observation(self, message: dict[str, Any]) -> dict[str, Any] | None:
        self.require_active()
        sensor = message.get("sensor")
        if sensor not in self.grants:
            raise ValueError("unknown sensor")
        if not self.grants[sensor]:
            self.record("dropped", sensor=sensor, reason="revoked")
            return None
        captured = message.get("captured_at")
        if not isinstance(captured, (int, float)) or not math.isfinite(captured):
            raise ValueError("invalid capture time")
        age = time.time() - captured
        if not -0.1 <= age <= self.limits.observation_age:
            self.record("dropped", sensor=sensor, reason="stale")
            return None
        encoded = message.get("data")
        if not isinstance(encoded, str):
            raise ValueError("invalid media")
        raw = base64.b64decode(encoded, validate=True)
        if sensor == "audio":
            if not raw or len(raw) > 6400 or len(raw) % 2:
                raise ValueError("invalid audio chunk")
            if self.audio_bytes + len(raw) > self.limits.input_audio_bytes:
                raise SessionEnded("input_audio_limit")
            self.audio_bytes += len(raw)
            mime = "audio/pcm;rate=16000"
        else:
            now = time.monotonic()
            if now - self.last_frame < 1:
                self.record("dropped", sensor=sensor, reason="frame_rate")
                return None
            if not raw.startswith(b"\xff\xd8") or len(raw) > self.limits.frame_bytes:
                raise ValueError("invalid frame")
            if self.frame_count >= self.limits.frames:
                raise SessionEnded("frame_limit")
            self.last_frame = now
            self.frame_count += 1
            mime = "image/jpeg"
        self.versions[sensor] += 1
        self.record("observation", sensor=sensor, version=self.versions[sensor],
                    captured_at=captured, bytes=len(raw))
        return {"realtimeInput": {sensor: {"data": encoded, "mimeType": mime}}}

    def provider_message(self, message: dict[str, Any]) -> list[dict[str, Any]]:
        self.require_active()
        events: list[dict[str, Any]] = []
        if "usageMetadata" in message:
            events.append(self.record("usage", provider=message["usageMetadata"]))
        if "goAway" in message:
            raise SessionEnded("provider_go_away")
        content = message.get("serverContent", {})
        if content.get("interrupted"):
            self.invalid_outputs.add(self.output_turn)
            events.append(self.record("interrupted", output_id=self.output_turn))
        for part in content.get("modelTurn", {}).get("parts", []):
            inline = part.get("inlineData")
            if not inline:
                continue
            if inline.get("mimeType") not in ("audio/pcm;rate=24000", "audio/pcm;rate=24000;channels=1"):
                raise SessionEnded("unsupported_output_format")
            raw = base64.b64decode(inline["data"], validate=True)
            if not raw or len(raw) % 2:
                raise ValueError("invalid output audio")
            self.output_bytes += len(raw)
            if self.output_bytes > self.limits.output_audio_bytes:
                raise SessionEnded("output_audio_limit")
            self.chunk += 1
            metadata = self.record("generated", output_id=self.output_turn, chunk_id=self.chunk,
                                   bytes=len(raw), latest_observations=dict(self.versions))
            # Latest observations are a dispatch watermark, not model acknowledgement.
            if self.output_turn in self.invalid_outputs:
                events.append(self.record("discarded", output_id=self.output_turn,
                                          chunk_id=self.chunk, reason="invalidated"))
            else:
                events.append({**metadata, "kind": "audio", "data": inline["data"]})
        if content.get("turnComplete"):
            events.append(self.record("turn_complete", output_id=self.output_turn))
            self.output_turn += 1
        return events
