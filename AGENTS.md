# AGENTS.md

Rules for any AI agent (or human contributor) working in this repository.
These rules exist to keep a multi-session, milestone-driven project coherent.

## Where to start

Every fresh session, before touching anything, read in this order:

1. [Roadmap.md](Roadmap.md) — vision, architecture, constraints.
2. The current milestone file in [docs/roadmap/](docs/roadmap/) — the one whose
   status is `in progress`.
3. [EXECUTION.md](docs/roadmap/EXECUTION.md) — scope and evidence rules.
4. The active and previous milestone's `M<n>-NOTES.md`, if present in
   `docs/roadmap/`, and [EVIDENCE.md](docs/roadmap/EVIDENCE.md).

Do not improvise a design that contradicts these documents. If reality
contradicts them, change the documents first (see "Architecture changes").

The user's explicit instructions take precedence over repository plans.
Within the repository, Roadmap owns product scope and milestone order, M1
owns observable behavior, each milestone owns its deliverables, and EXECUTION
owns the evidence process. Notes and examples cannot override those contracts.
If they conflict, identify the conflict and repair the documents consistently;
do not silently choose whichever interpretation makes implementation easiest.

## Execution discipline

- Before implementing, state the active milestone/checkpoint, relevant scenario
  or acceptance IDs, and the smallest observable result of this work. A brief
  progress message is sufficient; this is not a request for approval.
- Read and follow EXECUTION.md. Each checked acceptance item needs the specified
  evidence types in EVIDENCE.md. An owner review must come from the owner;
  another AI's approval or silence is not a substitute. Record the scope of
  the user's actual acceptance without implying unrun tests or trials occurred.
- Choose routine, reversible implementation details autonomously within the
  authorized scope. Record concrete choices rather than reopening settled ones.
- Do not start a later milestone's implementation while prerequisite acceptance
  remains incomplete. In-scope planning and review may continue while owner
  review is pending. An explicit user-directed scope change is recorded first;
  it does not retroactively make unmet criteria pass.
- Before finishing a work chunk, run `python3 scripts/check_roadmap.py`, update
  relevant evidence and the active `M<n>-NOTES.md`, and report what passed,
  what was not run, and the exact remaining work. Do not claim that this static
  check proves runtime behavior, live quality, or genuine owner approval.

## Language rules

- **All natural language in this repository is English**: code comments,
  docstrings, documents, commit messages, PR descriptions. No exceptions.
- **Code must carry comments written for human readers.** Explain intent and
  non-obvious decisions ("why", "what invariant this protects"), never
  restate what the code already says.

## Milestone discipline

- Work on one milestone at a time, in order. Do not build abstractions a
  later milestone owns — e.g. no generic plugin system during M2 or M3.
- The first product proof is proactive conversation without an assigned
  work task. M2 builds that experience, M3 evaluates it, and M4 uses a work
  scenario to test generality before extracting reusable interfaces.
- A milestone is done only when every exit criterion in its file is checked
  off. Partial work is reported as partial.
- When a milestone completes: update its `Status:` line, update the table in
  [Roadmap.md](Roadmap.md), and write a short `M<n>-NOTES.md` for the next
  session (what was learned, what the next milestone must do differently).

## Architecture invariants

These are the load-bearing rules. Violating them silently is the worst
possible contribution.

- **The decision core never touches the world.** `evaluate()` returns a
  decision; it never sends messages, mutates external systems, or schedules
  real timers. The run shell acts on decisions.
- **Constraints are hard gates.** Budget, permission, and disturbance limits
  can never be overridden by a policy score.
- **Silence is first-class.** Waiting is an explicit decision with wake
  conditions, not the absence of output.
- **Candidate actions, not abstract scores.** Policies compare concrete
  options; there is no free-floating "proactiveness" number. Separate
  policies, an Attention class, and an Arbiter class are not required.
- **Established pluggable surfaces use `typing.Protocol`.** Never force
  users to inherit from a base class. Do not invent plugin surfaces before
  scenarios demonstrate the need for them.
- **The framework never interprets event payload semantics.** Meaning-making
  lives in application context construction and decision logic; generic
  routing, persistence, and scheduling use explicit IDs and metadata.
- **Persona is data, not code.** The framework stays persona-neutral.
- **Conversation quality is part of acceptance.** The reference application
  owns the usefulness, grounding, continuity, and timing of its messages,
  even when a host-supplied model generates them.
- **The model never widens its own mandate.** Budgets and action scopes are
  granted by the host; model-drafted concerns cannot exceed them.

## Architecture changes

When an implementation fights the architecture, the architecture may be
wrong — but the change must be explicit:

1. Add an entry to the **strain log** in [docs/roadmap/M1.md](docs/roadmap/M1.md)
   describing the conflict.
2. Propose the revision in the relevant milestone file before coding it.
3. Keep [Roadmap.md](Roadmap.md) in sync with whatever is decided.

## Code conventions

- Python, async-first. Standard tooling only; do not introduce a dependency
  without a stated reason in the milestone file.
- **Code carries type annotations throughout.** Every public function,
  dataclass, and interface is fully typed; the package ships `py.typed`.
  Untyped public code is treated as unfinished.
- Scenario packs are the test suite: replayable event sequences with
  asserted state transitions and constraint behavior. Recorded model outputs
  make regression replays reproducible; live model behavior and conversation
  quality also require owner review. Passing a replay is not proof of a
  desirable conversational experience.
