# Execution Contract

This document makes the roadmap executable by a fresh contributor. It governs
scope and evidence, not class design. The user's explicit instructions remain
authoritative; already authorized work does not require repeated confirmation.

## Preserve the product proof

The first proof is worthwhile proactive conversation without an assigned work
task. The following do not satisfy it:

- A deployment monitor, task scheduler, or tool framework built first.
- A notifier that cannot receive a reply in the original conversation context.
- A script that always greets on a timer, or always waits to avoid mistakes.
- Hard-coded or replayed messages presented as live model initiative.
- A model-generated claim of discovery with no supporting retrieval record.
- More messages or a higher reply rate presented as evidence of value alone.

M2 must exercise both a worthwhile opening and justified silence, actual
information acquisition, and the user's continuation of an opening. M3 adds
sustained owner judgement. Work-first validation remains M4 unless the user
explicitly changes the direction.

## Scope and change decisions

Before implementation, identify the current milestone/checkpoint, scenario or
acceptance IDs, a small deliverable, and its verification. Infrastructure work
must explain which such behavior it enables. Avoid speculative extensibility.

Routine choices such as filenames, internal records, a simple adapter, or a
test fixture can be made autonomously. Record dependencies and configuration
where the milestone requires them. A future milestone's example is not an
instruction to implement it now.

Changes to the primary product proof, milestone order, user-visible behavior,
hard constraints, or acceptance standards are design changes. Record the
conflict and proposal in M1's strain log and update affected documents. If the
user has already authorized the change, cite that instruction and proceed.
Otherwise keep the proposal distinct from the accepted contract, complete
unaffected work, and obtain the missing product decision before implementing
the conflicting behavior. Do not amend a test or criterion solely to declare
the current implementation successful.

Keep scenario and acceptance IDs stable. If a criterion is replaced, record
the old requirement, the reason, and the new ID instead of silently reusing
its old evidence. Changed behavior invalidates affected evidence until rerun
or re-reviewed. Documentation cleanup alone does not invalidate all evidence.

## Acceptance evidence

Each milestone checkbox has an ID such as `M2-E3` and required evidence kinds
in parentheses. A checkbox is checked only when each kind has a passing entry
in [EVIDENCE.md](EVIDENCE.md) backed by an inspectable artifact.

| Kind | Required content |
|---|---|
| `document` | The actual design/report and relevant section or review notes; a promise to write it is insufficient. |
| `replay` | Scenario IDs, command, fixture/config version, observed result, and assertions checked. Recorded model outputs establish runtime regression behavior only. |
| `live` | Date, actual model/source/channel, configuration/version, input context, decisions, outputs, and usage. Identify simulated inputs separately. |
| `owner` | The owner's dated statement or a traceable conversation reference, what was reviewed, and the scope of acceptance or rejection. Never invent or expand an endorsement. |
| `integration` | Host setup, reproducible invocation, observed output, and lifecycle ownership. An illustrative snippet alone is not integration evidence. |
| `release` | The produced release artifact and its verifiable location/version. A local build is not proof of publication. |

Record only the acceptance actually expressed by the user. An instruction to
proceed can authorize a documented plan; it cannot establish that an unrun live
trial, recovery test, or integration has happened. Another AI's favorable review
cannot stand in for the owner's experience judgement.

A single owner statement may cover several criteria when its scope is explicit.
Reference it for each covered criterion; do not request repeated approvals for
the same accepted material. M1-E2/E3/E4 require both the documented review
material and the owner's acceptance of the behavior, dispositions, and scope.

Before M2 acceptance, keep a coverage map for every S11–S25 scenario with:
scenario ID, fixture/test path, actual observed outcome, evidence kind, and
remaining gap. Add S1–S10 in M4. Positive and negative branches matter: a test
that accepts either Act or Wait for every input is not behavioral validation.
Fixtures must make the expected constraint/state outcome specific; live
semantic choices are reviewed separately rather than forced into exact wording.

Evidence artifacts must identify the code/config version they validate and
separate passing, failing, and unrun checks. Use synthetic or redacted records
in the repository; a private owner-review artifact may contain a reference and
minimal acceptance excerpt rather than an entire private conversation.

## Handoff and phase transitions

Keep a short `M<n>-NOTES.md` alongside the active milestone. Update it at the
end of a meaningful work chunk, including unfinished work; it is not a second
roadmap. Record:

- Milestone/checkpoint and scenario/acceptance IDs addressed.
- Concrete changes and commands/evidence, with actual outcomes.
- Decisions made and their source; unresolved issues or required owner input.
- The next smallest authorized action and any work explicitly out of scope.
- Current milestone status; a draft or internal demo is not completion.

A milestone can become `complete` only with all criteria checked and backed
by evidence. Update its status, Roadmap's table, and its handoff together. The
next milestone may start only after predecessors are complete, unless an
explicit user scope change revises the plan. Record such revisions honestly;
they do not turn unfinished checks into passing checks.

## Static consistency check

Run from the repository root:

```sh
python3 scripts/check_roadmap.py
```

The check detects inconsistent phase status, skipped prerequisites, missing
scenario walkthroughs, malformed acceptance IDs, checked criteria lacking
declared evidence, missing evidence files, and incomplete completion records.
It also checks local documentation links. Pipe-table padding and the common
hyphen/en-dash/em-dash heading separators are tolerated; scenario IDs and
their uniqueness remain strict. This is a small contract checker, not a full
Markdown parser or formatter. Run its regression tests after changing it:

```sh
python3 -m unittest discover -s scripts -p 'test_*.py'
```

The checker does not run application tests,
verify an artifact's truth, authenticate owner statements, or prove initiative
quality. It is a local check, not an installed CI or branch-protection rule.

Other AI tools may not automatically load AGENTS.md. Give a new assistant this
explicit starting instruction:

> Read AGENTS.md and its required documents first. Identify the active milestone,
> relevant scenario/acceptance IDs, and the next smallest authorized deliverable.
> Work within that scope, record evidence and handoff notes, and run
> `python3 scripts/check_roadmap.py` before reporting completion.
