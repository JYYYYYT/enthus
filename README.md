# Enthus

**A proactive decision layer for LLM applications** — an embeddable module
that gives a language-model application continuous perception and autonomous
judgment: *when* to act, *when* to keep investigating, *when* to wait, and
*when* it is worth interrupting a human.

## Why

Today's LLM applications are either reactive (a human asks, the model
answers) or mechanical (cron fires fixed logic on a schedule). Neither can
do what a good assistant — human or fictional — actually does: keep
perceiving the world without being prompted, keep caring about something
while no new input arrives, gather information on its own initiative, stay
silent when there is nothing worth saying, and speak up at the right moment.

Enthus is the missing piece between "the model can reason" and "the
application acts on its own judgment".

## What it is

- A **decision core**: one call in (`evaluate(context)`), one decision out
  (`Execute` / `Wait` / `Complete`), organized around *concerns* — things
  the application keeps caring about even when no new event arrives.
- **Continuous perception**: event streams and scheduled wake-ups keep the
  system aware; attention decides what deserves a deeper look, and the
  system can actively acquire information it was never given.
- A **replaceable run shell** for standalone use: persistence, scheduling,
  idempotent execution.
- Persona-neutral by design; personality is configuration, not code.

## What it is not

- Not an agent framework. It does not compete with LangGraph, AutoGen, or
  CrewAI — it is built to be called *from* them, or from any LLM-powered
  application.
- Not a memory system, not a persona engine, not a chatbot.

## Status

Early, pre-code. The project is currently at **M1: behavior specification** —
15 concrete scenarios that define what the system must do before any
interface is designed. See the roadmap:

- [Roadmap.md](Roadmap.md) — vision, architecture, working agreements
- [docs/roadmap/M1.md](docs/roadmap/M1.md) — behavior specification (current)
- [docs/roadmap/](docs/roadmap/) — all milestones, M1 through M5

## License

[Apache-2.0](LICENSE)
