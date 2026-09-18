# Execution and evidence

## Work within the current contract

Roadmap CP1-CP7 defines the product proof. Before implementation, name the
active checkpoint, applicable CP/scenario/acceptance IDs, smallest result, and
verification. Use the relevant M1 scenarios; historical scenarios apply only
when the current milestone enables their behavior.

Work one milestone at a time. Resolve routine details autonomously. Changes to
scope, order, observable behavior, or hard constraints must be recorded in M1's
strain log and the owning documents before coding. Follow existing user
authorization; request a missing product decision only when necessary.

Keep IDs stable. A replaced requirement gets a new ID and a mapping in the
[revision ledger](../history/REVISIONS.md). Retired evidence stays historical.
Editorial cleanup does not invalidate unchanged evidence; changed behavior
requires new verification. Never change a criterion merely to pass existing code.

## Evidence required for acceptance

Every checkbox declares an ID and evidence kinds. Check it only when every kind
has a passing row and inspectable artifact in [EVIDENCE.md](EVIDENCE.md).

| Kind | Required record |
|---|---|
| document | The actual design/report and relevant material, not a promise. |
| replay | Scenario IDs, code/config version, fixtures, command, observed results, and asserted transitions. |
| live | Date, actual model/inputs/output path, configuration, traces, usage, and observed results; label injected or replayed inputs. |
| owner | The owner's statement/reference and exact reviewed scope. AI opinion, silence, and permission to proceed are not acceptance. |
| integration | Reproducible setup/invocation, observed result, and lifecycle ownership. |
| release | Published artifact location and version; a local build is insufficient. |

A scoped owner statement may support multiple criteria; do not repeatedly ask
for approval already given. The 2026-09-18 direction change authorizes work but
does not certify new scenarios or live results. M1's earlier approval remains
limited to its recorded material.

Maintain a coverage map with each applicable scenario, fixture/test, outcome,
evidence kind, and gap. Include positive and negative cases. A fixture allowing
either speech or silence for every input cannot prove selection. Record trial
targets before evaluating; version and explain later changes.

Live traces distinguish observations, proposed/played/uncertain output, stop
latency, permissions, and usage. Mark provider-native behavior and baseline
differences. Do not present synthetic media as live evidence or playback as
proof of being heard. Use synthetic/redacted public artifacts or minimal private
review references. Passing, failing, and unrun checks must remain distinguishable.

## Handoff and phase changes

Keep only the active milestone's `M<n>-NOTES.md` in the default reading path.
It records current state, actual verification, known problems, and the next
smallest step. Link to details rather than repeat the roadmap or work history.
Archive completed handoffs in `docs/history/`; read them only when needed.

Completion requires all current criteria checked with evidence, matching status
in the milestone and Roadmap, and a completion handoff. Then the next milestone
may start. An explicit scope revision can change the plan but cannot turn unrun
work into a pass. Update evidence and the active handoff at each work chunk.

## Checks

Run `python3 scripts/check_roadmap.py` after documentation or status changes.
If the checker changes, also run:

```sh
python3 -m unittest discover -s scripts -p 'test_*.py'
```

The checker validates links, IDs, traceability, phase order, and evidence
references, including archived records. It cannot authenticate evidence or judge
semantic fidelity, model quality, or owner approval. Report those limits and
state what was not run. Product tests are selected for the implementation changed.
