# M2b Bounded Initiative Evidence

Date: 2026-09-18. Scope: M2b's source/memory/outcome mechanics. M2 remains in
progress; M2-E1/E2/E3/E4/E5/E6 are not marked complete by this work.

## Version and configuration

Working tree based on `60cedbc` (the committed M2a foundation). Exact code,
configuration and replay files are identified by `M2b-source-sha256.txt` in
this directory. Fixture version: `m2b-v1-synthetic` in
`tests/scenarios/m2b.json`. Runtime: Python 3.11, macOS, standard-library SQLite.
Defaults are recorded in [M2](../roadmap/M2.md); replay tests override time,
grant and cadence explicitly. Source: one selected Wikipedia edition (`en`
in the probe). Model decision fixtures are synthetic and labeled `recorded-v2`.

## Observed results

| Check | Result | Interpretation |
|---|---|---|
| `PYTHONPATH=src python3.11 -m unittest discover -s tests -v` | 44 tests passed | M2a regressions plus M2b mechanics, including four source-outcome cases. |
| `python3 -m unittest discover -s scripts -p 'test_*.py'` | 11 tests passed | Documentation checker regressions. |
| `python3 scripts/check_roadmap.py` | Passed | Structural/evidence-reference consistency only. |
| `python3.11 -m compileall -q src scripts/probe_source.py` | Passed | Source compiles under the target interpreter. |
| `git diff --check` | Passed | No whitespace errors in tracked changes. |

The recorded pack asserts a two-evaluation query/result path, one source
attempt charged, exact action/exploration linkage and consumed result events.
Its relevant-result branch sends one opening with a stored source URL; the
subsequent user turn retains that evidence. Empty, irrelevant and error branches
send nothing. These are specific shell outcomes, not empirical model choices.

Additional cases prove muted research with suppressed delivery; cancellation
and expiry rejecting late results; topic corrections retaining history while
invalidating candidates; reference deduplication; missing-citation rejection;
shared and per-exploration budgets; result recovery without another query;
idempotent completion; and interrupted read recovery as a recorded failure.
Schema migration preserves an existing conversation and its remaining model
budget. Narrowing controls must reference the current user event; wake data
cannot invoke them. The shell supplies explicit mute/cancel acknowledgements.

## Actual source probe (separate from model acceptance)

The sandbox initially rejected an ordinary HTTP attempt with `Operation not
permitted`. An authorized read-only network probe outside that sandbox
successfully queried `puzzle game` against English Wikipedia and returned three
extracts with revision links. The repeatable final-adapter probe is recorded
in `docs/evidence/M2b-source-probe.json`, including timestamp, source-code hash,
request URL, response hash/size and item metadata. No private conversation was
sent. No model participated and no outbound chat message was sent.

Invocation:

```sh
PYTHONPATH=src python3.11 scripts/probe_source.py --language en --query 'puzzle game' --output docs/evidence/M2b-source-probe.json
```

The probe validates source connectivity/parsing, not M2-E3's three live
initiative behaviors. Chinese-edition connectivity was not probed.

## Updated S11–S25 coverage

Paths below are relative to `tests/`. Each result remains partial for full M2
acceptance. The prior M2a report is historical; this report supersedes its
current coverage assessment, not its recorded results.

| Scenario | Replay | Observed behavior | Remaining gap |
|---|---|---|---|
| S11 | `test_research.py::test_reconnect_uses_restored_topic_and_nonresponse_does_not_change_it` | Restored topic supports a recorded opening; next opportunity waits. | Real opportunity/content judgement. |
| S12 | Existing quiet-hours test and muted-research test | Delivery stays gated while bounded observation can continue. | Full deferred-candidate freshness matrix. |
| S13 | Model-note and restored-topic tests | Notes require current user evidence; no notes from nonresponse/wakes. | Explicit weak-signal aggregation/cadence scenarios and live judgement. |
| S14 | Existing daily-limit/cooldown replay | Ceiling blocks unsolicited delivery; source calls are separately bounded. | More time-boundary combinations in M2c. |
| S15 | Muted-research and narrowing-control tests | Research survives mute; speech is blocked; direct control acknowledgement describes resume. | Real interpretation of duration, quoted requests and ambiguity. |
| S16 | `scenarios/m2b.json`, relevant case | Granted, topic-linked wake starts a query without a work task. | Actual model origination and usefulness. |
| S17 | Same case | Source IDs checked, stored URLs attached to the opening. | Semantic entailment and live grounding review. |
| S18 | Pack empty/irrelevant/error cases | Specific recorded decisions produce no message. | Live model restraint with those outcomes. |
| S19 | Pack continuation; existing terminal subprocess | Reply sees original source context and confirmed opening. | Live back-and-forth after unsolicited delivery. |
| S20 | Reconnection/nonresponse test | No additional message or topic revision after recorded wait. | Broader no-reminder/no-dislike interpretation fixtures. |
| S21 | Correction/history and model-note override tests | Canonical correction invalidates old candidates and observations. | Alias resolution and ordinary-language correction quality. |
| S22 | Duplicate-completion/reference and exact-event tests | One result event; identical source reference not shared twice. | Same underlying discovery across changed revisions/wording. |
| S23 | Result restart, interrupted query, migration and prior send-recovery tests | No automatic requery/resend; budgets/history survive. | Full crash-point matrix and transaction fault injection. |
| S24 | Query/model budget tests and prior zero-budget case | Shared/per-exploration limits block extra work without a farewell. | Full cost/grant combinations and live usage inspection. |
| S25 | Late-cancelled query and queued-candidate tests | Closed exploration never reactivates; late items excluded from context. | Live natural-language cancellation and wider concurrency cases. |

No owner approval of conversation quality or complete M2 acceptance is recorded.
Next: finish M2c's missing replay branches, then run actual model/source/chat
examples under the documented configuration and obtain M2d owner review.
