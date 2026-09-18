# Contributor guide

These rules apply to AI agents and human contributors. Explicit user instructions
take precedence. Keep documents concise and readable; each rule has one owner.

## Start here

Read in order:

1. [Roadmap.md](Roadmap.md): product meaning and architecture.
2. The milestone marked `in progress` in [docs/roadmap/](docs/roadmap/).
3. [EXECUTION.md](docs/roadmap/EXECUTION.md): evidence and phase rules.
4. That milestone's current `M<n>-NOTES.md`: state and next step.

Read the relevant [M1 scenarios](docs/roadmap/M1.md) before implementation and
[EVIDENCE.md](docs/roadmap/EVIDENCE.md) when recording or reviewing acceptance.
[History](docs/history/README.md) is reference material, not default startup reading.

Roadmap owns product scope; M1 owns observable behavior; milestones own their
deliverables; EXECUTION owns evidence. Handoffs report state and cannot override
these contracts. Repair conflicts in the owning documents before coding.

## Working rules

- State the active checkpoint, applicable CP/scenario/acceptance IDs, and smallest
  observable result before implementing. This is progress reporting, not approval.
- Preserve Roadmap CP1-CP7. A terminal, timer, manual image upload, or always-on
  process cannot substitute for continuous co-presence. Report capability gaps
  instead of quietly redefining the goal. The model never widens its mandate.
- Work one milestone at a time. Choose reversible implementation details within
  scope autonomously; do not invent plugin surfaces or future milestones' work.
- For architecture changes, record the conflict in M1's strain log and revise
  Roadmap and the affected milestone first. Already-authorized changes need no
  repeated permission; scope changes and acceptance remain distinct.
- Follow EXECUTION for tests, evidence, completion, and handoff. Never use another
  AI's opinion or silence as owner approval. Keep unrun work visibly pending.
- Before finishing, update relevant evidence and the current handoff, run
  `python3 scripts/check_roadmap.py`, and report passed, unrun, and remaining work.

## Code and documentation

- All repository prose, comments, docstrings, commits, and PR text use English.
- Use typed Python, async-first host code, and intent-focused comments. Public
  functions/interfaces are fully annotated; Python packages ship `py.typed`.
- Prefer standard tooling. Record a concrete reason in the active milestone
  before adding a model/media/UI dependency. Custom model training and a
  multi-vendor compatibility platform are not first-prototype requirements.
- Use `typing.Protocol` for demonstrated extension surfaces; do not require
  consumers to inherit a base class or invent a generic plugin registry.
- Generic routing uses IDs/metadata; application context and decision logic
  interpret payload meaning. Persona is configuration. Follow Roadmap's rules
  for inference/effects, grants, freshness, cancellation, and partial output.
- Scenario replays test state transitions and constraints. Live evidence and
  owner review test model behavior and experience; neither replaces the other.
- Keep the current contract in its owning document. Archive obsolete plans and
  completed handoffs; do not maintain parallel explanations of current policy.
