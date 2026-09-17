# Acceptance Evidence

This register supports the numbered criteria in M1–M5. Follow
[EXECUTION.md](EXECUTION.md) for what each evidence kind must contain.
M1 acceptance is recorded below. M2 implementation evidence will be recorded
separately; no M2 acceptance is implied by M1 approval.

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

## Recording rules

- Add one row per criterion/kind/artifact, using the exact acceptance ID.
- Kind is `document`, `replay`, `live`, `owner`, `integration`, or `release`.
- Artifact is a repository-relative file path in backticks, without an anchor.
  The file should identify the relevant section, commands, version, and results.
- Result is `pass`, `fail`, or `pending`. A checked criterion requires a
  `pass` row for every evidence kind specified by its checkbox.
- Owner evidence is a real statement/reference with its scope, not an AI's
  interpretation presented as the owner's words.
- Append rows in chronological order. The last row for a criterion/kind is
  current; a later `fail` or `pending` invalidates an earlier `pass`. Uncheck
  affected criteria until the rerun/review passes. One current artifact may
  collect several test results or supporting records.
- Supersede stale evidence when the behavior or requirement changes. Remove
  the empty-register notice above once evidence is actually recorded.
- Passing the static roadmap checker is not evidence that the scenario pack,
  live trial, integration, or owner review has passed.
