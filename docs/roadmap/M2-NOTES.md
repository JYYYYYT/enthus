# M2 Working Handoff

## Status and authorization

M2 is in progress. M1 approval is recorded in `docs/evidence/M1-acceptance.md`.
After the M2a foundation, the owner requested the next step. M2b's bounded
source/memory/outcome mechanics are now implemented. All M2 exit criteria
remain unchecked; live model behavior and owner quality review are pending.

The current work supports M2-E1/E2/E5 and partial S11–S25. It builds on the
committed M2a snapshot `60cedbc`. This chunk is uncommitted; no push occurred.

## Delivered in M2b

- One optional Wikipedia edition (`--wikipedia en|zh`), using only read-only
  search and bounded introductory extracts. No new runtime dependency.
- Topic notes with exact user evidence, separate current/history records,
  explicit host correction precedence, disabled topics and bounded context.
- One active exploration with exact IDs, per-exploration query/model counters,
  expiry, shared query allowance and a current host grant.
- Durable query actions and outcomes committed with pending result events.
  Restart consumes recorded outcomes; interrupted reads become failures without
  automatic requery. Closed/expired work cannot resurrect from a late result.
- Source-linked message candidates, stored revision URLs, exact-reference dedupe
  and delivery revalidation. Research can continue during delivery mute.
- User-turn-only model proposals for narrowing controls (mute/stop), with a
  shell-generated acknowledgement. They cannot enable/resume or grant resources.
  Slash controls remain deterministic; live intent interpretation is unproven.
- Atomic schema 1 -> 2 migration, preserving prior conversation and model budget.
- Replay pack plus real public source probe, kept distinct in the evidence.

Host defaults, source scope and limits are in M2.md; commands and constraints
are in `docs/M2b.md`. `docs/M2a.md` and its evidence describe the older snapshot.

## Verification (2026-09-18)

- `PYTHONPATH=src python3.11 -m unittest discover -s tests -v`: 44 passed,
  including the existing CLI subprocess and four new source-outcome cases.
- `python3 -m unittest discover -s scripts -p 'test_*.py'`: 11 passed.
- `python3 scripts/check_roadmap.py`: passed structural/reference checks.
- `python3.11 -m compileall -q src scripts/probe_source.py`: passed.
- `git diff --check`: passed.
- Final-adapter real probe: English Wikipedia query `puzzle game`, three
  results with revision URLs. Network sandbox initially blocked the request;
  the authorized read-only probe outside it succeeded. Timestamp, source hash
  and response metadata are in `docs/evidence/M2b-source-probe.json`.

`docs/evidence/M2b-initiative.md` contains the current S11–S25 coverage map and
`M2b-source-sha256.txt` identifies exact tested sources/config/fixtures.
The source probe used synthetic public query text, no model or private chat.
No live model conversation, Chinese-edition probe, owner quality approval,
package release or publication was performed.

## Important implementation facts

The model still returns only concrete actions and data. Store/runtime own all
state transitions and external operations. Query acknowledgements cause one
recoverable evaluation; send acknowledgements are terminal. Never route by
semantic topic similarity. `main` is the continuing conversation; each bounded
exploration has its own ID, and finishing it does not end the conversation.

A timed-out HTTP worker can finish after the shell stops waiting. The source
adapter tracks it and refuses overlapping source requests; its late response
cannot commit state by itself. Runtime cancellation/expiry decides whether a
result can become context. Unknown message delivery remains host-resolved.

No architecture revision was needed: the result-routing strain resolution and
S15/S25 distinction were implemented. M1's strain log now links the evidence.
Current topic notes override historical claims, but choosing the right topic
key and interpreting quoted/ambiguous language still need live evaluation.

## Next smallest step

M2c: fill the remaining replay branches identified by the coverage map before
claiming complete S11–S25 coverage. Prioritize crash/transaction fault injection,
quiet-hour/cooldown boundaries with queued findings, weak-signal/cadence cases,
ordinary-language control/correction interpretation fixtures, and repeated
findings whose source revisions or wording differ. Avoid a generic plugin layer.

Then M2d needs a working local model service, an explicitly selected installed
model, and actual source-backed terminal conversations under the recorded limits.
The previous M2a Ollama startup problem was not re-investigated in this chunk;
do not assume it is fixed. Review genuine initiative, justified silence,
continuity, grounding and burden with the owner. No M3 trial or M4 work scenario
starts until M2's exit criteria are met.
