# Enthus — Roadmap

> A proactive decision layer for LLM applications.
> This file is the master reference. Read it first in any fresh session,
> then read the milestone file for the current phase.

## Vision

Today's AI systems fall into two categories:

- **Reactive**: a human asks, the model answers. The loop is driven by the human.
- **Mechanical**: cron-style triggers fire fixed logic on a schedule. No judgment.

What science-fiction assistants have — and what is missing — is an **autonomous
loop**: continuously perceive, decide *whether* to act or stay silent, act, and
feed the outcome back into memory. This project builds that missing piece.

## Positioning

Enthus serves **LLM-powered applications** — chatbots, companions,
assistants, and agent workflows alike: anything built around a language
model that must keep perceiving and judging while nobody is prompting it.

Enthus is **not** an agent framework. It does not compete with LangGraph,
AutoGen, or CrewAI. It is a narrow, embeddable, low-level module that
answers one question those frameworks leave unanswered:

> Given what I currently care about, what has changed, and what resources I
> have left — should I act now, wait, or stop?

Two usage modes must both be supported:

1. **Embedded**: a host application (e.g. a LangGraph workflow) calls the
   decision core directly — one call in, one decision out — and keeps its own
   scheduling, persistence, and lifecycle.
2. **Standalone**: an application uses the full runtime (decision core plus
   the default run shell) out of the box.

The decision core is the product. The run shell is a replaceable reference
implementation.

## Core Architecture

The system is organized around **Concerns** — things the system continues to
care about even when no new event arrives. Events are stimuli; Concerns are
state. A concern may be a goal, a commitment, an open question, or an interest.

```text
Event streams --> Attention (dedupe, weak-signal accumulation, coarse filter)
                     | updates state
                     v
              Concern set  <-- scheduled wake-ups (next_check_at)
                     |
                     v
              Decision core: evaluate(snapshot)
                1. Propose candidate actions (policies propose here)
                2. Hard-constraint filter (budget / permission / idempotency)
                3. Compare and select ONE next step
                     |
                     v
              Decision: Execute(action) | Wait(until, wake_on) | Complete(reason)
                     |
                     v
              Run shell (persistence, scheduling, idempotent execution)
                     |
                     v
              Host agent / tools (do the actual work)
```

Key structural rules:

- **The decision core never touches the world.** `evaluate()` returns a
  decision; the shell persists and executes it. This keeps the core testable
  and embeddable.
- **Constraints are hard gates.** Budget exhaustion or missing permission can
  never be overridden by a high score from any policy.
- **Silence is first-class.** `Wait` is an explicit, inspectable decision with
  wake conditions — not the absence of a decision.
- **Policies propose, the arbiter disposes.** Policies do not see each other.
  Semantics live in policies; arithmetic lives in the arbiter.
- **Candidate actions, not abstract scores.** Policies evaluate concrete
  options ("check recent changes" vs "notify now" vs "wait two minutes"),
  never a free-floating "proactiveness score".

### Concern taxonomy

| | Task concern | Interest concern |
|---|---|---|
| Example | Watch a deployment until stable | User is lately into sci-fi worldbuilding |
| Success condition | Yes — closes when met | None — never "completes" |
| Lifecycle | complete / cancel / expire | decay / refresh only |
| Budget | task budget | separate "wandering" budget |
| Purpose | Get the job done | Stay present ("aliveness") |

### Persona

Personality is **data, not code**: a config object holding tone, per-policy
weights and thresholds, and interest lists. The framework stays
persona-neutral; swapping configs swaps the "person". Persona affects both
*what is said* (draft generation) and *when to speak* (thresholds).

## Validation Strategy

Architecture decisions must be earned by scenarios, not by intuition.

- **M2** validates *correctness* with a work scenario (deployment watch),
  measured against a baseline of "fixed-interval check + simple rules".
- **M4** validates *generality* with the aliveness family (interest concerns,
  persona, social initiative) on the same architecture.
- Only parts exercised by both scenario families may stabilize into the
  public API (M5).

## Project Constraints

- Language: **Python**, async-first, `typing.Protocol` for all pluggable
  interfaces (no forced inheritance).
- **Code carries type annotations throughout.** Every public function,
  dataclass, and interface is fully typed; the package ships `py.typed` so
  consumers get the same checking. Types are part of the interface contract.
- **All natural language in the repo is English**: code comments, docstrings,
  documents, commit messages.
- Code must carry comments written for human readers — explain intent and
  non-obvious decisions, not restate the code.
- The framework never interprets event payload semantics; meaning-making
  lives in Attention and policies.
- The model may draft concerns, but budget and action scope are granted by
  the host and can never be widened by the model itself.

## Milestones

| Milestone | File | Goal | Status |
|---|---|---|---|
| M1 | [M1.md](docs/roadmap/M1.md) | Behavior specification: 15 scenarios | in progress |
| M2 | [M2.md](docs/roadmap/M2.md) | Prototype: deployment-watch scenario | pending |
| M3 | [M3.md](docs/roadmap/M3.md) | Extract the decision core + persistence | pending |
| M4 | [M4.md](docs/roadmap/M4.md) | Aliveness family: interest concerns + persona | pending |
| M5 | [M5.md](docs/roadmap/M5.md) | Public API stabilization and open-source release | pending |

## Working Agreements

- Implement milestone by milestone, in order. Do not build M3 abstractions
  during M2.
- After each milestone, revisit this roadmap and the architecture notes;
  record every place reality strained the design.
- A fresh session should read: `Roadmap.md` → current milestone file → any
  `NOTES.md` left by the previous milestone.
