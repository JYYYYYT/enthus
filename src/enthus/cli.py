"""A local duplex terminal, with explicit host controls outside model output."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import time
from dataclasses import asdict
from pathlib import Path
from typing import TextIO

from .decider import OllamaDecider, offline_decide
from .models import Settings
from .runtime import Runtime
from .store import Store
from .source import Wikipedia

HELP = """Write a message and press Enter. Host controls:
  /start            Grant initiative for 24 hours (does not clear mute)
  /stop             Cancel initiative; direct conversation remains available
  /mute [minutes]   Mute unsolicited output; omit duration for indefinite mute
  /resume           Clear mute (does not renew an expired/cancelled grant)
  /budget N         Set remaining decision-call allowance explicitly
  /query-budget N   Set remaining source-query allowance explicitly
  /topic KEY TEXT   Set/correct a current topic note (does not grant research)
  /drop-topic KEY   Disable a topic and cancel its exploration
  /status           Show persisted state and unresolved deliveries
  /resolve ID sent|failed  Record a verified outcome; never resends the action
  /help             Show these controls
  /quit             Exit; interrupted work remains recoverable
EOF drains queued work before exiting. /quit interrupts immediately.
Model-interpreted mute/stop is experimental; slash commands are deterministic.
Errors and blocked deliveries are recorded in /status; no unsolicited alerts.
"""


def host_command(store: Store, line: str, now: float) -> str:
    parts = line.split()
    command = parts[0][1:]
    if command == "help" and len(parts) == 1:
        return HELP
    if command == "status" and len(parts) == 1:
        return json.dumps({**asdict(store.state()), "unknown_deliveries": store.unknown_actions(),
                           "topics": [asdict(topic) for topic in store.topics()],
                           "wikipedia": store.settings.wikipedia}, indent=2, ensure_ascii=False)
    if command == "topic" and len(parts) >= 3:
        store.set_topic(parts[1], line.split(maxsplit=2)[2], now)
        return "Current topic recorded. Older claims are retained as history; research authority is unchanged."
    if command == "drop-topic" and len(parts) == 2:
        store.drop_topic(parts[1], now)
        return "Topic disabled and its exploration cancelled. History is retained."
    if command in {"start", "stop", "resume"} and len(parts) == 1:
        store.control(command, now)
        if command == "start":
            return f"Initiative granted for {store.settings.grant_seconds:g} seconds. Existing mute is preserved."
        if command == "stop":
            return "Initiative cancelled. Direct replies remain available."
        return "Mute cleared. Cancelled or expired initiative stays closed; /start grants it again."
    elif command == "mute" and len(parts) in {1, 2}:
        store.control(command, now, float(parts[1]) * 60 if len(parts) == 2 else None)
        duration = f"for {parts[1]} minutes" if len(parts) == 2 else "until /resume"
        return f"Unsolicited conversation muted {duration}. Direct replies remain available."
    elif command in {"budget", "query-budget"} and len(parts) == 2:
        store.control(command, now, float(parts[1]))
        return f"Remaining allowance updated. Decisions: {store.state().remaining_calls}; queries: {store.state().remaining_queries}."
    elif command == "resolve" and len(parts) == 3 and parts[2] in {"sent", "failed"}:
        if parts[1] not in store.unknown_actions():
            raise ValueError("Only an unknown delivery can be resolved by the host")
        store.finish_action(parts[1], parts[2], now, "Host verified delivery outcome")
    else:
        raise ValueError("Unknown control or wrong arguments; use /help")
    return "Control recorded."


async def run(args: argparse.Namespace) -> None:
    settings = Settings(timezone=args.timezone, wikipedia=args.wikipedia)
    decide = (OllamaDecider(args.model, settings, args.ollama_url)
              if args.mode == "ollama" else offline_decide)
    store = Store(args.database, settings)
    transport: asyncio.ReadTransport | None = None
    pipe: TextIO | None = None
    worker: asyncio.Task[None] | None = None
    stopped = asyncio.Event()

    async def send(text: str, identity: str) -> None:
        # Flush is our local acknowledgement; a crash around it is still unknown.
        print(f"\nEnthus [{identity}]: {text}", flush=True)

    source = Wikipedia(args.wikipedia, settings.source_timeout) if args.wikipedia else None
    runtime = Runtime(store, decide, send, search=source)

    async def work() -> None:
        while not stopped.is_set():
            acted = await runtime.step()
            # Diagnostics stay inspectable through /status. Turning errors into
            # unsolicited terminal messages would bypass disturbance controls.
            if not acted:
                await asyncio.sleep(0.1)

    try:
        print(f"Enthus M2b | {args.mode} | {args.database}\n"
              "Initiative requires /start. Use /status to inspect restored controls.", flush=True)
        if args.mode == "offline":
            print("OFFLINE DIAGNOSTIC: synthetic replies; no live model or autonomous queries.", flush=True)
        if source:
            print(f"Research source: {args.wikipedia}.wikipedia.org (short queries only). Topics and /start are required.", flush=True)
        print(HELP, flush=True)
        loop = asyncio.get_running_loop()
        reader = asyncio.StreamReader(limit=65536)
        # Duplicate stdin so shutting down this terminal adapter does not close
        # a host process's stream. This MVP supports POSIX terminals and pipes.
        pipe = os.fdopen(os.dup(sys.stdin.fileno()), "r")
        transport, _ = await loop.connect_read_pipe(lambda: asyncio.StreamReaderProtocol(reader), pipe)
        worker = asyncio.create_task(work())
        while True:
            incoming = asyncio.create_task(reader.readline())
            completed, _ = await asyncio.wait({incoming, worker}, return_when=asyncio.FIRST_COMPLETED)
            if worker in completed:
                incoming.cancel()
                await asyncio.gather(incoming, return_exceptions=True)
                await worker  # Propagate a shell failure instead of silently losing the worker.
                break
            try:
                raw = incoming.result()
            except ValueError:
                print("System: Input line exceeded the terminal limit.", flush=True)
                continue
            if not raw:
                stopped.set()
                await worker
                await runtime.drain()
                break
            line = raw.decode("utf-8", errors="replace").strip()
            if line == "/quit":
                break
            if not line:
                continue
            try:
                if line.startswith("/"):
                    print(f"System: {host_command(store, line, time.time())}", flush=True)
                else:
                    store.submit(line, time.time())
            except ValueError as exc:
                print(f"System: {exc}", flush=True)
    finally:
        if worker is not None and not worker.done():
            worker.cancel()
            await asyncio.gather(worker, return_exceptions=True)
        if transport is not None:
            transport.close()
        elif pipe is not None:
            pipe.close()
        store.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Enthus persistent conversation prototype")
    parser.add_argument("--database", type=Path, default=Path(".enthus/state.sqlite3"))
    parser.add_argument("--mode", choices=("offline", "ollama"), default="offline")
    parser.add_argument("--model", help="Explicit installed Ollama model; no automatic downloads")
    parser.add_argument("--ollama-url", default="http://127.0.0.1:11434")
    parser.add_argument("--timezone", default="Asia/Shanghai")
    parser.add_argument("--wikipedia", choices=("en", "zh"), help="Enable one read-only Wikipedia source")
    args = parser.parse_args()
    if args.mode == "ollama" and not args.model:
        parser.error("--model is required in ollama mode")
    try:
        asyncio.run(run(args))
    except KeyboardInterrupt:
        pass
    except (OSError, RuntimeError, ValueError) as exc:
        parser.exit(1, f"Enthus: {exc}\n")
