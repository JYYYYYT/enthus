# Enthus — Roadmap

> A proactive decision layer for LLM applications.
> Read this file first, then the milestone whose status is `in progress`.

## Vision

Build an AI experience that remembers shared topics, explores relevant
questions, and initiates worthwhile conversation without a fresh instruction
or an assigned work task. It should also choose silence, respect boundaries,
and change its behavior when the user gives feedback.

The first proof is a conversational companion with continuity and initiative.
Whether that experience is welcome must be tested with the project owner.
A functioning event loop alone does not establish product value.

Timers and external events are both valid wake-up mechanisms. Initiative
comes from choosing what to investigate or say in context, not from avoiding
scheduled execution.

## Positioning and delivery order

The long-term deliverable remains a narrow, open-source decision module for
chatbots, companions, assistants, and agent workflows. Its working question:

> Given our shared context, what has changed, and the resources available,
> should I investigate, speak, wait, or end this follow-up?

First build a reference chat application that makes the behavior observable.
Then validate it in sustained use. Only after a second, work-oriented scenario
should shared behavior become reusable public interfaces.

The release must support:

1. **Embedded use:** a host calls the decision core and owns scheduling,
   persistence, tools, and lifecycle.
2. **Standalone use:** a reference run shell provides those services.

These are release goals, not two runtimes to build during M2. The project
must demonstrate its differentiation through behavior and integration value,
without assuming existing frameworks lack every supporting capability.

## MVP scope

One user, one bidirectional chat surface, one queryable information source,
one decision model, a small memory store, and a single-process runtime.
The three initiative behaviors are:

- Continue a meaningful shared topic with something concrete to add.
- Investigate and share a relevant new finding.
- Reconnect at an appropriate opportunity, when there is a worthwhile opening.

The user can reply naturally, correct remembered information, mute unsolicited
conversation, or stop exploration. A presence event or elapsed interval never
requires a greeting. Research that finds nothing useful may end silently.

## Working architecture

```text
User messages / source events / due wake-ups / action outcomes
                         |
                         v
              Run shell: ingest, dedupe, route by ID
                         |
                         v
              Context: background + recent records
                       + relevant topics + current state
                         |
                         v
              Decision: investigate / speak / wait / end
                         |
                         v
              Run shell: validate limits, persist, execute
                         |
                         v
              Chat output / information-source tool
                         |
                         +-- linked outcome --> ingestion

SQLite stores state, events, decisions, actions, and memory.
Feedback updates stored preferences and the shell's future wake-up choices.
```

`Execute(action)`, `Wait(until, wake_on)`, and `Complete(reason)` remain
working decision forms. Investigating and speaking are different actions.
Ending an exploration does not delete its topic or end the conversation.
Names and type boundaries are provisional until M4/M5.

### Working glossary

| Term | Meaning in this roadmap |
|---|---|
| **Topic** | A subject grouping related conversation and knowledge; it does not itself authorize activity. |
| **Concern** | A continuing reason to pay attention, such as an interest, question, or commitment; a conceptual motivation. |
| **Follow-up** | A tracked unit of ongoing activity, with an ID, state, limits, and wake conditions; the shell routes its action outcomes here. |
| **Exploration** | A bounded follow-up that gathers information to resolve a question; it may end without a message. |
| **Candidate** | A proposed next action, such as a query or message; it is not executed until selected and validated. Deferred candidates retain enough state for reconsideration. |
| **Opening** | The conversational content of an unsolicited first turn; before delivery it is a message candidate, and after delivery it has an action/delivery record. |

These distinctions do not require six classes or tables. M2 may represent a
concern and its follow-up in one record. Topic links provide context; follow-up
and action IDs provide execution identity. Closing an exploration or discarding
a candidate does not delete the topic or end the user's conversation.

### Boundaries that matter now

- **Decision and execution are separate.** Evaluation may call a model but
  does not send messages, invoke world-facing tools, or schedule real timers.
- **Constraints are hard gates.** The host grants tool scope, model/exploration
  budgets, and notification limits. Decisions cannot enlarge those grants.
  The shell rechecks cancellation and applicable limits before execution.
- **Silence is explicit.** Waiting includes a time or event condition; an
  unproductive exploration may close with no user-facing message.
- **Evaluate concrete next steps.** One decider can compare investigation,
  speaking, waiting, and ending. Separate Attention, Policy, and Arbiter
  plugins are not MVP requirements.
- **Results return by identity.** Action outcomes carry stable action and
  follow-up IDs. Semantic memory retrieval does not route execution results.
- **Investigation value and speaking value differ.** A useful discovery may
  be held or discarded as a conversational candidate. Before delayed delivery,
  recheck freshness, relevance, mute state, and duplication.
- **Personality is configuration.** Tone and initiative preferences can vary;
  the reference application's generated content remains part of acceptance.

### Topics, memory, and ongoing attention

A topic groups related conversation or knowledge. A concern describes an
ongoing reason to pay attention. They may be linked, but are not identical:
mentioning a topic does not create a work assignment or authorize new access.

M2 may use small topic records and bounded exploration records instead of a
general Task/Interest class hierarchy. Interests may become inactive, be
corrected, or be removed; they are not required to live forever.

Minimal memory consists of bounded core background, recent original records,
and selected topic notes with provenance. Exact delivery, budget, and action
state remain structured records. A vector service and recursive lifetime
summarization are not prerequisites. A host may later supply memory retrieval.

### Run-shell reliability

- Persist pending actions, waits, budgets, and notification state in M2.
- Process each follow-up sequentially; coalesce repeated incoming signals.
- Commit an outcome and its pending follow-up event together, then consume
  pending events recoverably. Reject stale or cancelled execution.
- Cap steps, elapsed time, and spending, including model calls and exploration.
- Use stable idempotency keys where supported. Unknown external outcomes
  require verification or host intervention, not blind retry. Do not promise
  universal exactly-once effects.
- Resource exhaustion stops activity and becomes visible state. Status
  delivery obeys notification settings; there is no blanket terminal-message
  exception to mute or disturbance limits.

## Validation strategy

- **M2: behavioral feasibility.** Demonstrate the conversation loop on a live
  chat surface and replay the conversation/reliability scenarios from M1.
- **M3: experience value.** Review sustained use for substance, continuity,
  timing, grounding, and burden. Compare against a simple scheduled check-in
  baseline under comparable resource and notification limits.
- **M4: generality.** Add deployment watch as a second scenario and extract
  the shared decision core only after seeing what both families require.
- **M5: adoption.** Stabilize supported contracts, package the library, and
  demonstrate embedded and standalone use.

Record actual interventions and sampled withheld opportunities. Reply rate
and message volume are not standalone success metrics. Deterministic replay
checks constraints and recovery; live evaluation checks model behavior and
the experience. Neither substitutes for the other.

## Milestones

| Milestone | File | Goal | Status |
|---|---|---|---|
| M1 | [M1.md](docs/roadmap/M1.md) | Revised behavior specification: conversation first | in progress |
| M2 | [M2.md](docs/roadmap/M2.md) | Proactive conversation MVP | pending |
| M3 | [M3.md](docs/roadmap/M3.md) | Sustained experience validation and refinement | pending |
| M4 | [M4.md](docs/roadmap/M4.md) | Work scenario, generality, and core extraction | pending |
| M5 | [M5.md](docs/roadmap/M5.md) | Public API stabilization and open-source release | pending |

## Project constraints and working agreements

- Python, async-first, single process for the MVP. SQLite is the initial
  persistence backend. Document a concrete reason for each dependency.
- Keep implementation boundaries clear without a generic plugin system in
  M2/M3. Established extension interfaces use `typing.Protocol`.
- Code is typed throughout; public releases ship `py.typed`. Comments explain
  intent and invariants. All repository prose, comments, and commits use English.
- Work one milestone at a time. Architecture conflicts go in M1's strain log,
  then into the affected design documents before implementation changes.
- Preserve scenario IDs for traceability. Revised acceptance needs renewed
  review; authorization to edit documents does not mark the owner's review done.
- Completion requires every exit criterion, synchronized status lines, and
  a short `NOTES.md` for the next milestone. Read Roadmap, the active milestone,
  and any such handoff notes at the start of a new session.
