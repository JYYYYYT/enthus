# M2a Foundation Evidence

Date: 2026-09-18. Scope: the internal M2a checkpoint, supporting M2-E1/E2/E5.
All M2 acceptance criteria remain pending. M1 acceptance is separate.

## Version and environment

Implementation version: `0.0.1`, uncommitted working tree based on `db0cf7f`.
The exact code, test, fixture, and configuration contents are identified in
`docs/evidence/M2a-source-sha256.txt`; this is a source snapshot, not a release.
Fixture version: `m2a-v1` in `tests/scenarios/m2a.json`.
Execution: macOS, Python 3.11, SQLite from the standard library. Runtime defaults
are `Settings` in `src/enthus/models.py` and documented in M2.md. Replay fixtures
override time/limits explicitly in `tests/test_runtime.py`.

## Observed checks

| Command | Observed result | What it establishes |
|---|---|---|
| `PYTHONPATH=src python3.11 -m unittest discover -s tests -v` | 22 tests passed | Real SQLite state transitions, five-case recorded scenario pack, adapter parsing, and terminal subprocess behavior. |
| `python3 -m unittest discover -s scripts -p 'test_*.py'` | 11 tests passed | Existing documentation-checker regression suite. |
| `python3 scripts/check_roadmap.py` | Passed | Structure, milestone order, evidence paths; no runtime/owner-proof claim. |
| `python3.11 -m compileall -q src` | Passed | Source compiles under the target interpreter. |

The subprocess test sends two ordinary user turns separated by an observed
assistant reply, mutes unsolicited output, exits, and starts another process
with the same database. It observes context lengths of 1, 3 and 5, six durable
conversation messages, 97 remaining calls, and unchanged indefinite mute.
All three assistant replies are explicitly labeled offline diagnostics.

Recorded model tests exercise the actual Ollama request/response adapter with
an in-memory HTTP response. They assert the model name, structured format,
512-token generation limit, context serialization, and recorded token counts.
Malformed actions, additional grant fields, oversized text, non-finite waits,
and missing usage fail instead of being treated as valid model decisions.

## Scenario coverage map

Every row is partial or unrun for M2 acceptance. A recorded decision is an
assertion input, not proof that a real model will select it appropriately.

| Scenario | Fixture / test in `tests/` | Observed outcome | Kind | Remaining gap |
|---|---|---|---|---|
| S11 | `scenarios/m2a.json`, silent wake case | Wake persists an explicit wait and emits nothing. | replay, partial | Meaningful reconnection selection and owner timing review. |
| S12 | `test_runtime.py::test_quiet_hours_and_active_chat_do_not_spend_calls` | Quiet wake deferred to 09:00 without spending a call. | replay, partial | Candidate freshness/relevance after delayed source findings. |
| S13 | No semantic fixture yet | Not run. | pending | User-evidence interest aggregation and cadence changes. |
| S14 | `test_runtime.py::test_daily_limit_and_cooldown_are_dispatch_gates` | One allowed opening; later wake blocked without another model call. | replay, partial | Full conversational quota/cooldown branches and live timing. |
| S15 | Pack mute case; `test_timed_mute_during_evaluation_preserves_future_wake` | Mute persists across reply/restart; timed mute drops stale output and keeps a future wake. | replay, partial | Natural-language intent and research continuing independently of delivery mute. |
| S16 | No query fixture yet | Not run. | pending | Bounded autonomous origination and real retrieval. |
| S17 | No query fixture yet | Not run. | pending | Grounded discovery with inspectable source references. |
| S18 | Pack silent wait case | Timed and event-only waits emit no message; timed wait survives restart. | replay, partial | Empty, irrelevant, and failed retrieval outcomes. |
| S19 | Pack context case; `test_cli.py` | Same-context turns and restored history confirmed; active-chat gate blocks openings. | replay, partial | Reply to a genuinely model-initiated, source-backed topic. |
| S20 | No semantic fixture yet | Not run. | pending | Nonresponse does not create a dislike or a follow-up reminder. |
| S21 | `test_runtime.py::test_user_correction_invalidates_queued_direct_reply` | Old candidate cancelled; only response to the newer snapshot delivered. | replay, partial | Persistent topic correction precedence and semantic interpretation. |
| S22 | `test_runtime.py::test_duplicate_input_is_exact_and_coalesces_triggers` | Same event ID produces one history entry; rapid triggers retain history and evaluate once. | replay, partial | Same discovery under different source events/candidate IDs. |
| S23 | Pack restart cases; runtime unknown/crash/interrupted/timeout cases | Budget/waits/mute recover; unknown send blocks; verified sent result adds history without resend. | replay, partial | Retrieval recovery and broader crash-point coverage in M2c. |
| S24 | Pack exhaustion case; model failure/timeout tests | Zero allowance disables initiative without farewell; failed/interrupted calls remain charged. | replay, partial | Per-exploration budgets and actual live usage review. |
| S25 | Pack stop case; `test_stop_during_evaluation_discards_late_result` | Queued and late outputs cannot reactivate cancelled initiative. | replay, partial | Independently cancelled exploration, late source result, and natural-language intent. |

## Not run and limitations

- No successful live Ollama session. An installed CLI probe crashed during
  Metal/MLX startup; a local HTTP probe was blocked by the sandbox. Adapter
  tests use recorded responses, not an external service.
- No queryable source, topic notes, preference learning, or natural-language
  control interpretation. Slash controls are the current reliable path.
- No owner review of message quality, terminal typing ergonomics, or burden.
- No full crash matrix, package install/release, or external channel integration.
- POSIX terminal and duplex-pipe use only. The two-way pipe test does not prove
  the interactive terminal is pleasant to use.

Next: configure and implement M2b's one-source initiative loop. M2-E2 needs full
S11–S25 coverage, and M2-E3/E4 require actual live examples and owner judgement.
