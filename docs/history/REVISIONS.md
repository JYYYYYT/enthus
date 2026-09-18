# Roadmap revision ledger

## 2026-09-18: continuous co-presence becomes the first proof

Authorization: the project owner, in conversation
`01a0aa48-b451-7f70-b9c3-1868116ca4d6`, after the proposed roadmap revision.
English translation of the instruction:

> Make the changes as you suggested; strengthen the expression of continuous
> presence that we discussed, so other AI assistants do not drift in their
> interpretation.

This authorizes the direction and documentation revision: one Enthus product,
continuous co-presence first, cross-session continuity next, and bounded
background follow-up where experience justifies it. It does not certify newly
written scenarios, unrun live sessions, implementation, or milestone completion.
The detailed new behaviors receive live/owner review under the active criteria;
this scope authorization is sufficient to plan and implement within that scope.

### Why the contract changes

The old terminal/source MVP could pass without observing a changing shared
environment or handling interruptions. A required deployment-watch scenario
and a predetermined decision-library release also forced extraction before
its relevance to the revised experience had been established. M2 now tests
presence; M3 tests continuity and sustained value; M4 tests evidenced reuse;
M5 releases a reproducible companion and only justified components.

### Evidence and history

- M1-E1 through M1-E4 retain their historical 2026-09-17 scope. The accepted
  hashes and owner statement remain in [M1 acceptance](../evidence/M1-acceptance.md).
  M1's new S26-S35 supplement is not covered by that old approval.
- Pre-revision repository snapshot: `80f976fd9e169a5f2428d5d8e01021828e126e30`.
  Old M2a/M2b choices are in [M2-LEGACY.md](M2-LEGACY.md); their tests/source
  probe establish only their recorded scope. No live presence evidence exists.
- M2-E1 through M2-E6, M3-E1 through M3-E6, M4-E1 through M4-E6, and M5-E1
  through M5-E12 are retired, not passed. Their original requirements and
  replacement IDs appear below. Evidence rows for retired IDs remain historical.
- Replacement IDs require new evidence. Old replay results may be cited for
  unchanged mechanics with their actual version, never relabeled as live proof.
- Original S1-S25 IDs remain available. [M1](../roadmap/M1.md) assigns current applicability;
  deployment watch and full background exploration are no longer prerequisites
  for the first presence experiment. New scenarios are S26-S35.

### Retired acceptance requirements

The original wording and evidence kinds are preserved below. Replacement means
scope supersession, not equivalence or satisfaction; all replacements begin
unchecked. Removing an obsolete delivery obligation does not claim it succeeded.

| Retired ID | Evidence kinds | Original requirement | Replaced by |
|---|---|---|---|
| M2-E1 | document | Host configuration and dependency choices recorded before live use. | M2-E7 |
| M2-E2 | replay | S11–S25 covered by replayable scenarios, including mute, duplicate events, cancellation, resource exhaustion, and restart with an unknown send outcome. | M2-E9 |
| M2-E3 | live | Three initiative behaviors demonstrated in the live bidirectional surface; the user can continue an AI-initiated topic with its original evidence. | M2-E8 |
| M2-E4 | owner | Owner reviewed live examples for substance, continuity, grounding, timing, and burden; shortcomings recorded rather than hidden by scripted replays. | M2-E8, M2-E12 |
| M2-E5 | document | Decision/outcome records include enough provenance, state, and usage data to diagnose failures and support M3's trial. | M2-E11 |
| M2-E6 | document | Architectural strain recorded in M1 and a short `M2-NOTES.md` written for M3. | M2-E12 |
| M3-E1 | live, owner | Trial protocol recorded and completed; duration and evidence limitations documented, with owner review of interventions and sampled withheld cases. | M3-E7, M3-E8 |
| M3-E2 | document | Comparison with the scheduled baseline written, including tradeoffs, costs, and cases where the MVP provided no advantage. | M3-E11 |
| M3-E3 | live | Explicit feedback demonstrably changes later behavior (S13/S21), while nonresponse does not trigger reminders or an unsupported preference claim. | M3-E8, M3-E9 |
| M3-E4 | replay | Observed reliability failures fixed and S11–S25 regression pack passes. | M3-E10 |
| M3-E5 | owner | Owner judges the experience worth continuing, with unresolved weaknesses recorded. Technical correctness alone cannot satisfy this criterion. | M3-E12 |
| M3-E6 | document | A `M3-NOTES.md` handoff identifies evidenced extension needs for M4; no public API is frozen merely because the trial has ended. | M3-E12 |
| M4-E1 | replay, document | S1–S10 pass on the work scenario, with baseline comparison and costs. | M4-E7, M4-E8 |
| M4-E2 | replay, owner | S11–S25 pass after extraction; owner checks representative live openings and replies for conversational regressions. | M4-E10 |
| M4-E3 | integration | The reference runtime and an independently driven host exercise the same decision core without duplicate lifecycle ownership. | M4-E9, M4-E11 |
| M4-E4 | document | Each proposed public contract maps to an exercised scenario and a concrete integration need. Shared contracts are identified; family-specific adapters remain separate and experimental unless independently justified. | M4-E9 |
| M4-E5 | document | A comparison explains which abstractions held, which changed, and why; strain log and Roadmap synchronized with implemented findings. | M4-E9 |
| M4-E6 | document | A `M4-NOTES.md` handoff identifies the narrow surface ready for M5 review. | M4-E12 |
| M5-E1 | release | Package published to PyPI with a resolved name, typed public API, and `py.typed`. | M5-E13 |
| M5-E2 | document | README explains the conversation-first evidence and long-term module positioning, with a small embedded example and a standalone chat example. | M5-E14 |
| M5-E3 | document | API reference, configuration guide, and recovery/serialization contracts. | M5-E14, M5-E18 |
| M5-E4 | document | Traceability from public interfaces to M1 scenarios and M4 integration needs. | M5-E18 |
| M5-E5 | integration | Integration example using an existing agent workflow's lifecycle and persistence, without forcing it to run a competing Enthus scheduler. | M5-E15 |
| M5-E6 | document | Contribution guide, license, changelog, and explicit scope boundaries. | M5-E16 |
| M5-E7 | document | Summarized M3 owner-trial findings and M4 baseline comparison, with limitations and without exposing private conversation history. | M5-E17 |
| M5-E8 | integration | A new consumer can embed the core using only the public documentation; demonstrate the target of a basic integration in under an hour. | M5-E15 |
| M5-E9 | replay | Both scenario families run as CI-replayable tests with versioned fixtures; live evaluation is documented separately and is not presented as deterministic. | M5-E17 |
| M5-E10 | integration | Embedded and standalone usage agree on decision semantics and identify one owner for state, scheduling, and retries in each mode. | M5-E18 |
| M5-E11 | document | Known limits are explicit: initiative selection is heuristic, inferred preferences are fallible, small owner trials do not establish broad appeal, and external exactly-once effects depend on downstream capabilities. | M5-E14 |
| M5-E12 | document | Remaining automatic-origination and retrieval experiments are labeled experimental rather than implied to be solved by a generic interface. | M5-E18 |

## Presence architecture decisions recorded on 2026-09-18

The following preserves the original reasoning now summarized in current M1.
It is a design record, not evidence that the changes were implemented.

10. **Continuous presence was reduced to asynchronous initiative (2026-09-18).**
    A terminal/source loop could satisfy the old M2 without fresh environmental
    perception, interruption, or shared experience. **Authorized revision:**
    Roadmap CP1-CP7 and S26-S35 define the first proof; M2 tests B, M3 adds
    cross-session continuity and only justified A behavior. Original acceptance
    remains scoped to its recorded version; new criteria use new IDs.
11. **A snapshot decision loop cannot own every interaction timescale.** A
    serial evaluation/query/send path delays interruption and fresh context.
    **Design revision:** separate live reception/playback/control from slow
    background work, sharing explicit identity, context, and grants. Streaming
    inference proposes output under host-controlled delivery; no per-frame
    durable transaction or second LLM gate per audio chunk is required.
    Validate cancellation, partial playback, and stale-output behavior in M2.
12. **Mute, budgets, and delivery records had text-turn semantics.** A mute
    could mean playback, unsolicited speech, or sensing; one model-call count
    cannot bound a long stream; a generated utterance may never be fully played.
    **Design revision:** S28-S32 separate controls, time/usage bounds, session
    identity, and observed output progress. Preserve conservative unknown-effect
    handling without automatically replaying speech or reactivating capture.
13. **Extraction and comparison were predetermined.** A scheduled check-in
    baseline and deployment-watch extraction could validate A while missing B.
    **Authorized revision:** compare a thin realtime-model baseline in M2/M3;
    choose M4's second scenario from observed reuse needs. M5 releases the
    reproducible companion, and components only when independently justified.


## 2026-09-18: documentation consolidation

The owner instructed keeping a short current handoff, directly revising current
contracts, and keeping the documents concise and intuitive for humans as well
as AI contributors. English translation of the instruction:

> Do it, and keep the documents concise and intuitive. They are for people
> to read as well as AI.

Current documents were shortened without changing CP1-CP7, active scenario IDs,
acceptance requirements, or status. Old S1-S25, completed handoffs, implementation
choices, and this ledger now live in `docs/history/`, outside default startup
reading. Earlier evidence stays in `docs/evidence/`. The checker covers both
current and archived identity so that moving text cannot erase obligations or
turn historical approval into new acceptance.
