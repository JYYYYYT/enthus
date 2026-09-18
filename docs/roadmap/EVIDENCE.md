# Acceptance Evidence

Checkmarks require the evidence kinds declared in each criterion; see
[EXECUTION](EXECUTION.md). M1 approval covers its original specification only.
New presence criteria remain unchecked. Retired IDs and scope changes are in
[the historical ledger](../history/REVISIONS.md).

## Register

| Criterion | Kind | Artifact | Result |
|---|---|---|---|
| M1-E1 | owner | `docs/evidence/M1-acceptance.md` | pass |
| M1-E2 | owner | `docs/evidence/M1-acceptance.md` | pass |
| M1-E3 | owner | `docs/evidence/M1-acceptance.md` | pass |
| M1-E4 | owner | `docs/evidence/M1-acceptance.md` | pass |
| M1-E2 | document | `docs/roadmap/M1.md` | pass |
| M1-E3 | document | `docs/roadmap/M1.md` | pass |
| M1-E4 | document | `Roadmap.md` | pass |
| M2-E1 | document | `docs/evidence/M2a-foundation.md` | pending |
| M2-E2 | replay | `docs/evidence/M2a-foundation.md` | pending |
| M2-E5 | document | `docs/evidence/M2a-foundation.md` | pending |
| M2-E1 | document | `docs/evidence/M2b-initiative.md` | pending |
| M2-E2 | replay | `docs/evidence/M2b-initiative.md` | pending |
| M2-E5 | document | `docs/evidence/M2b-initiative.md` | pending |
| M1-E4 | document | `docs/evidence/pre-presence-roadmap.txt` | pass |
| M2-E7 | document | `docs/evidence/continuous-presence-revision.md` | pending |
| M1-E2 | document | `docs/history/M1-2026-09-17.md` | pass |
| M1-E3 | document | `docs/history/M1-2026-09-17.md` | pass |

M1 document rows now point to archived material; the original owner statement
and accepted hashes remain authoritative. Prior M2 rows describe the terminal/
source prototype, not live presence.

## Register rules

Append rows; the latest result for an ID/kind applies. Artifacts use repository-
relative paths. A new failure or pending rerun invalidates an older pass. Keep
retired evidence historical and never reuse its ID for changed requirements.
A static check verifies references, not the truth of the evidence.
