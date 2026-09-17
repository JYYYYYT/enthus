# Enthus

**A proactive decision layer for LLM applications.**

Enthus explores how an AI can remember shared topics, investigate relevant
questions, and start a worthwhile conversation without a new instruction.
Choosing silence and responding to feedback are part of that behavior.

## First proof

The first prototype will be a conversational companion: one user, one chat
surface, a small memory store, and one queryable information source. It will
continue shared topics, share grounded discoveries, and reconnect when the
timing and content justify it. It must also respect muting, avoid repeated
messages, and recover after a restart.

## Long-term deliverable

After validating the experience, a work scenario will test which mechanisms
generalize. Those shared mechanisms will become an embeddable decision core
with a replaceable standalone runtime. Memory, tools, and persona can be
supplied by the host; the reference chat application demonstrates the complete
experience. The prototype is not a commitment to a general chatbot platform
or a full memory framework.

Python and SQLite are the starting point. API names remain provisional until
the scenarios justify stable contracts.

## Status

**M1 is approved. M2 is in progress.** The M2a foundation provides a duplex
terminal, bounded recent context, SQLite persistence, explicit waits, and
budget/mute/cancel/restart controls. It has recorded replays and a terminal
process test; it does not yet prove worthwhile live initiative.

Queryable information, topic notes, and grounded initiative are the next M2b
checkpoint. M3 evaluates sustained experience; M4 tests a work scenario before
extracting reusable interfaces.

- [Roadmap.md](Roadmap.md) — vision, architecture, and milestone order
- [docs/roadmap/M1.md](docs/roadmap/M1.md) — scenarios and design strain log
- [docs/roadmap/](docs/roadmap/) — all milestones, M1 through M5

## Try the foundation

Use Python 3.11+ on macOS or Linux. There are no runtime dependencies to install.
From the repository root:

```sh
PYTHONPATH=src python3.11 -m enthus --mode offline
```

Offline mode produces clearly labeled synthetic replies and chooses silence
on wakes. It tests mechanics, not intelligence. State survives exit in the
ignored `.enthus/state.sqlite3` file. Use `/help` and `/status` to inspect the
controls, `/start` to grant initiative, and `/quit` to exit.

An optional local Ollama adapter requires an explicitly chosen installed model.
Read [the M2a guide](docs/M2a.md) for that invocation, recovery semantics, and
current limitations. No real model/source trial has passed yet.

```sh
PYTHONPATH=src python3.11 -m unittest discover -s tests -v
python3 -m unittest discover -s scripts -p 'test_*.py'
python3 scripts/check_roadmap.py
```

[M2a evidence](docs/evidence/M2a-foundation.md) records the exact tested scope
and the remaining S11–S25 gaps.

## Contributor entry point

Read [AGENTS.md](AGENTS.md) and its required documents before implementing.
Other AI tools may need an explicit instruction to load that file. Follow the
scope, evidence, and handoff rules in
[EXECUTION.md](docs/roadmap/EXECUTION.md), and run
`python3 scripts/check_roadmap.py` before reporting completion. A passing static
check does not replace scenario tests or owner evaluation.

## License

[Apache-2.0](LICENSE)
