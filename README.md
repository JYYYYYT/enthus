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

Early, pre-code. **M1: behavior specification** is in progress. The roadmap
has been revised to validate proactive conversation in M2, refine the
experience in M3, and extract reusable interfaces with a work scenario in M4.
The revised specification still requires owner review.

- [Roadmap.md](Roadmap.md) — vision, architecture, and milestone order
- [docs/roadmap/M1.md](docs/roadmap/M1.md) — scenarios and design strain log
- [docs/roadmap/](docs/roadmap/) — all milestones, M1 through M5

## License

[Apache-2.0](LICENSE)
