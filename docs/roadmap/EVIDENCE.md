# Acceptance Evidence

This register supports the numbered criteria in M1–M5. Follow
[EXECUTION.md](EXECUTION.md) for what each evidence kind must contain.
No acceptance evidence has been recorded yet. Pending checkboxes remain pending.

## Register

| Criterion | Kind | Artifact | Result |
|---|---|---|---|

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
