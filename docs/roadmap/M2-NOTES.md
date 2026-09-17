# M2 Working Handoff

## Status and scope

M2 is in progress. M1 owner acceptance is recorded in
`docs/evidence/M1-acceptance.md`. The owner authorized the next implementation
step and, after a quota interruption, explicitly requested continuation.
M2a's internal foundation is implemented; no M2 exit criterion is checked.
This work supports M2-E1/E2/E5, with partial S11–S25 mechanics only.

## Delivered

- Python 3.11+, standard-library runtime and small typed internal records.
- Duplex terminal with explicit host controls, an offline diagnostic, and an
  optional local Ollama structured-output adapter. No implicit model download.
- SQLite events, recent conversation, decisions, call accounting, outbox,
  controls, waits, and restart reconciliation under a single-process lock.
- Pure decision/result separation from effects; current snapshot revisions
  invalidate stale results. Hard gates run before evaluation and delivery.
- Unknown sends require host resolution; no automatic resend. Model failures
  and interruptions remain charged. Error state is inspectable via `/status`.
- Recorded scenario pack, async failure tests, and actual terminal subprocess
  replay with a second process confirming persisted conversation and mute.

Concrete defaults and their rationale are in M2.md; usage is in `docs/M2a.md`.
These choices are reversible prototype details, not public framework APIs.

## Verification (2026-09-18)

- `PYTHONPATH=src python3.11 -m unittest discover -s tests -v`: 22 tests passed,
  including a five-case recorded scenario pack and the CLI process test.
- `python3 -m unittest discover -s scripts -p 'test_*.py'`: 11 tests passed.
- `python3 scripts/check_roadmap.py`: structural/evidence references passed.
- `python3.11 -m compileall -q src`: passed.

See `docs/evidence/M2a-foundation.md` for the precise coverage and source hash
manifest. None of these results establishes conversation quality or owner
acceptance. No package publication or live information retrieval was run.
Changes remain in the working tree; no commit or push was performed.

An environment probe found the installed Ollama CLI crashing in its Metal/MLX
startup, and the sandbox blocked a local HTTP probe. The optional adapter was
tested with recorded wire responses only. Do not present it as a successful
live session. A working service and an explicit model selection are still
needed before M2d's real-model acceptance.

## Lessons and next smallest step

A timed mute arriving during a wake evaluation can invalidate the result and
accidentally erase the next wake. The shell now schedules a fresh opportunity
within the existing grant; a regression replay covers this race. This is an
implementation repair within the accepted architecture, not a new scope rule.

Proceed to M2b: first record one actual queryable source and its host-granted
scope, per-exploration budget, expiry, and active-count cap in M2.md. Then build
one complete query -> linked pending outcome -> reevaluation -> share or silence
path. Retain provenance and allow the user's reply in the same context.
Add bounded topic notes and explicit corrections; keep execution IDs separate
from semantic topic grouping. Add natural-language control interpretation with
hard host validation before claiming S15/S25 behavior in ordinary conversation.

M2a currently uses only the `main` follow-up. Send acknowledgements are terminal
events; query results in M2b must instead schedule recoverable reevaluation.
Preserve the outbox and exact IDs rather than introducing a second runtime.
Do not add vector storage, generic plugins, work monitoring, M3 trials, or a
stable public API in this next step. Complete M2b/M2c/M2d before marking M2 done.
