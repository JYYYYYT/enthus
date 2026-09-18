# Continuous presence direction revision

Date: 2026-09-18. Pre-change HEAD:
`80f976fd9e169a5f2428d5d8e01021828e126e30`.

The owner authorized the proposed roadmap changes and asked for stronger
continuous-presence wording to prevent future AI contributors from drifting.
[REVISIONS](../history/REVISIONS.md) records the conversation reference, English
translation, retired requirements, replacement IDs, and evidence boundaries.
This artifact documents the revision, not live acceptance or new owner review.

## Scope

Roadmap CP1-CP7 defines continuous co-presence; M1 S26-S35 supplies observable
behaviors and traceability. M2's first proof is a bounded shared session; M3
adds cross-session continuity and only justified A behavior; M4 selects a second
scenario from demonstrated needs; M5 releases the reproducible companion and
only independently justified components. One project, separate timescales.

The unchanged M1-E1 through M1-E4 refer to the recorded 2026-09-17 approval.
The previous Roadmap is preserved in [pre-presence-roadmap.txt](pre-presence-roadmap.txt)
as a byte-for-byte snapshot from the pre-change HEAD, after historical status
updates. It is not claimed to be byte-identical to the pre-approval hash in
[M1 acceptance](M1-acceptance.md). That original record remains authoritative
about precisely what the owner accepted. M1's original scenarios, walkthrough,
and dispositions are preserved in the
[archived specification](../history/M1-2026-09-17.md).

All new M2-M5 criteria start unchecked. A statement approving this direction
cannot establish detailed behavior review, product tests, model integration,
market value, or milestone completion. M2-E7 also needs concrete session/model
configuration before its live run, so this revision alone cannot satisfy it.

## Initial revision verification

- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_roadmap.py`: passed structural,
  local-link, CP/scenario/criterion, and retirement-reference validation.
- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s scripts -p 'test_*.py' -v`:
  16 passed. New cases reject a missing presence scenario/definition, broken
  traceability, reuse of a retired ID, invalid replacements, and an attempt to
  approve a new criterion using only retired evidence. Existing owner-evidence
  and milestone-order tests remain in the suite.
- `git diff --check`: passed.

These checks do not certify semantic fidelity, authenticate owner approval, or
test presence. Product runtime tests were not rerun because product code was
unchanged. No model connection, actual sensor session, live trial, commit, push,
or release is part of this change. New M2 acceptance remains pending.

## Documentation consolidation

The owner subsequently requested concise, human-readable current documents and
a short active handoff. Historical scenarios, completed notes, old implementation
choices, and revision details moved to `docs/history/`. Current acceptance IDs,
wording, evidence kinds, checkbox states, and milestone statuses are unchanged.
The updated checker verifies both current and archived scenario sets, allows
completed handoffs in the archive, and requires the active handoff in the
current documentation directory.

Cleanup verification:

- Roadmap validation and `git diff --check`: passed.
- Checker regression suite: **19 passed**, including archive integrity,
  separation of old/current scenarios, and current versus completed handoffs.
- Audited all 22 Markdown files for local links/anchors and English prose;
  confirmed the historical Roadmap snapshot still matches the pre-change HEAD.
- Compared all 28 acceptance criteria against the pre-cleanup working files:
  wording, evidence kinds, checkbox states, and milestone statuses are unchanged.
- The same ten current-reading documents contain about 57% fewer words after
  removing repetition and moving history out of the main reading path.

Product code is unchanged; product tests and live/media trials were not rerun.
No new acceptance, implementation, commit, or publication is claimed.
