"""Effect shell: serialize decisions, then recheck authority before delivery."""

from __future__ import annotations

import asyncio
import time
from collections.abc import Awaitable, Callable
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from .models import Action, Context, Evaluation
from .store import Store

Decide = Callable[[Context], Awaitable[Evaluation]]
Send = Callable[[str, str], Awaitable[None]]


class Runtime:
    def __init__(self, store: Store, decide: Decide, send: Send,
                 clock: Callable[[], float] = time.time) -> None:
        self.store = store
        self.decide = decide
        self.send = send
        self.clock = clock
        self._step_lock = asyncio.Lock()

    def initiative_gate(self, now: float) -> tuple[str | None, float | None]:
        """A retry time is a request to reevaluate, never permission to send."""
        state, config = self.store.state(), self.store.settings
        if not state.initiative_enabled or state.expires_at is None or now >= state.expires_at:
            return "Initiative grant is closed", None
        if state.mute_until == -1:
            return "Muted until explicit resume", None
        blockers: list[tuple[str, float]] = []
        if state.mute_until is not None and state.mute_until > now:
            blockers.append(("Temporarily muted", state.mute_until))
        local = datetime.fromtimestamp(now, ZoneInfo(config.timezone))
        start, end = config.quiet_start, config.quiet_end
        quiet = (start <= local.hour < end if start < end
                 else local.hour >= start or local.hour < end if start > end else False)
        if quiet:
            until = local.replace(hour=end, minute=0, second=0, microsecond=0)
            if until <= local:
                until += timedelta(days=1)
            blockers.append(("Quiet hours", until.timestamp()))
        for reason, previous, interval in (
            ("Active conversation", state.last_user_at, config.active_chat_seconds),
            ("Opening cooldown", state.last_opening_at, config.cooldown_seconds),
        ):
            if previous is not None and previous + interval > now:
                blockers.append((reason, previous + interval))
        midnight = local.replace(hour=0, minute=0, second=0, microsecond=0)
        if self.store.opening_count(midnight.timestamp()) >= config.daily_openings:
            blockers.append(("Daily opening limit", (midnight + timedelta(days=1)).timestamp()))
        if not blockers:
            return None, None
        reason, until = max(blockers, key=lambda item: item[1])
        return reason, until if until < state.expires_at else state.expires_at

    async def step(self) -> bool:
        """Perform at most one evaluation or delivery; controls remain responsive."""
        async with self._step_lock:
            # The terminal cannot prove that an interrupted write was unseen.
            if self.store.unknown_actions():
                return False
            now = self.clock()
            self.store.enqueue_due(now)
            action = self.store.pending_action()
            if action is not None:
                await self._deliver(action)
                return True
            event = self.store.claim()
            if event is None:
                return False
            if event.kind == "wake":
                reason, until = self.initiative_gate(now)
                if reason is not None:
                    self.store.defer(event, until)
                    return True
            if not self.store.reserve_call(event):
                return True
            context = Context(event, self.store.state(), self.store.messages(), now)
            try:
                result = await asyncio.wait_for(self.decide(context), self.store.settings.model_timeout)
                if not isinstance(result, Evaluation):
                    raise ValueError("Decider must return a validated Evaluation")
            except asyncio.CancelledError:
                self.store.interrupted(event)
                raise
            except Exception as exc:
                self.store.record(context, None, self.clock(), f"{type(exc).__name__}: {exc}"[:500])
            else:
                self.store.record(context, result, self.clock())
            return True

    async def _deliver(self, action: Action) -> None:
        if action.revision != self.store.state().revision:
            self.store.discard_action(action, "Context or controls changed", None, stale=True)
            return
        if action.unsolicited:
            reason, until = self.initiative_gate(self.clock())
            if reason is not None:
                self.store.discard_action(action, reason, until)
                return
        self.store.sending(action)
        try:
            await asyncio.wait_for(self.send(action.text, action.id), self.store.settings.send_timeout)
        except asyncio.CancelledError:
            self.store.finish_action(action.id, "unknown", self.clock(), "Delivery interrupted")
            raise
        except Exception as exc:
            # Without an acknowledgement, even a timeout might have delivered.
            self.store.finish_action(action.id, "unknown", self.clock(), f"{type(exc).__name__}: {exc}"[:500])
        else:
            self.store.finish_action(action.id, "sent", self.clock())

    async def drain(self, max_steps: int = 64) -> int:
        """Bound a diagnostic/replay run so an unexpected loop fails visibly."""
        for count in range(max_steps):
            if not await self.step():
                return count
        raise RuntimeError("Drain exceeded its step limit")
