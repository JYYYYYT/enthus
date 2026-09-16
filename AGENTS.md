# AGENTS.md

Rules for any AI agent (or human contributor) working in this repository.
These rules exist to keep a multi-session, milestone-driven project coherent.

## Where to start

Every fresh session, before touching anything, read in this order:

1. [Roadmap.md](Roadmap.md) — vision, architecture, constraints.
2. The current milestone file in [docs/roadmap/](docs/roadmap/) — the one whose
   status is `in progress`.
3. Any `NOTES.md` left by the previous milestone.

Do not improvise a design that contradicts these documents. If reality
contradicts them, change the documents first (see "Architecture changes").

## Language rules

- **All natural language in this repository is English**: code comments,
  docstrings, documents, commit messages, PR descriptions. No exceptions.
- **Code must carry comments written for human readers.** Explain intent and
  non-obvious decisions ("why", "what invariant this protects"), never
  restate what the code already says.

## Milestone discipline

- Work on one milestone at a time, in order. Do not build abstractions a
  later milestone owns — e.g. no generic plugin interfaces during M2.
- A milestone is done only when every exit criterion in its file is checked
  off. Partial work is reported as partial.
- When a milestone completes: update its `Status:` line, update the table in
  [Roadmap.md](Roadmap.md), and write a short `NOTES.md` for the next
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
  options; there is no free-floating "proactiveness" number.
- **Pluggable surfaces use `typing.Protocol`.** Never force users to inherit
  from a base class to satisfy an interface.
- **The framework never interprets event payload semantics.** Meaning-making
  lives in Attention and policies.
- **Persona is data, not code.** The framework stays persona-neutral.
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
  asserted decisions, not mocks-only unit tests.
