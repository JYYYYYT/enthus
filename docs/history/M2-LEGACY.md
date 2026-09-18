# Historical M2a/M2b implementation choices

These choices describe the terminal/source prototype at commit
`80f976fd9e169a5f2428d5d8e01021828e126e30`, before the 2026-09-18 presence revision.
They remain useful when running or maintaining that code. They are not the
current product proof, live-session defaults, or next implementation plan.
Old acceptance IDs mentioned below are retired; see [REVISIONS.md](REVISIONS.md).
Use [M2.md](../roadmap/M2.md) and [M2-NOTES.md](../roadmap/M2-NOTES.md) for current work.

## M2a implementation choices (2026-09-17)

- Runtime: Python 3.11+, standard library only. SQLite operations stay small and
  execute on the single event-loop thread; model HTTP runs in a worker thread.
  Packaging uses setuptools; it is a build tool, not a runtime dependency.
- Surface: interactive local terminal, one persistent conversation and one
  initiative follow-up. Deterministic slash commands provide host controls;
  natural-language interpretation of those controls is later M2 work.
- Model: optional local Ollama `/api/chat` with schema-constrained output,
  non-streaming responses, temperature 0, and a 512-token generation ceiling.
  The user selects an installed model explicitly; never download one implicitly.
  An explicitly selected offline diagnostic decider verifies mechanics only.
- Local state: `.enthus/state.sqlite3` by default, excluded from version control.
  One process owns a database at a time; startup takes an exclusive local lock.
- Context: last 20 user/confirmed-assistant messages, at most 12,000 characters;
  a single user message is limited to 4,000 characters. Model output is bounded
  to 2,000 characters. No source retrieval or claimed discovery in M2a.
- Limits: 100 decision-call attempts per persisted conversation, including failed
  or interrupted attempts; no automatic refill at restart. A host budget command
  explicitly sets a new remaining allowance. Model timeout is 30 seconds.
- Initiative: enabled only by an explicit `/start`; 15-minute check interval,
  24-hour grant, 2 initiations per local calendar day, 6-hour cooldown, and
  5-minute active-chat quiet period. Quiet hours are 22:00–09:00 in the configured
  timezone (default Asia/Shanghai). Bare `/mute` lasts until `/resume`.
- Delivery: persist before dispatch; unknown delivery outcomes are held for host
  resolution, never retried automatically. Terminal output has no downstream
  idempotency guarantee. A send timeout uses a 10-second limit.
- Decision records currently use `Speak`, `Wait`, and `Finish`: the concrete
  M2a equivalents of executing a message, waiting, and closing the single
  initiative follow-up. `Wait` cannot shorten the host's check interval.
  Closing initiative leaves direct conversation and history available.
- Send acknowledgements are terminal outcome events with explicit action and
  follow-up identity (`main` for this single conversation). They do not trigger
  another model call. Query outcomes must become pending reevaluation events in
  M2b, using the same identity-based routing principle.
- Diagnostics are persisted and shown by `/status`, not sent as unsolicited
  error/farewell messages. Ambiguous delivery blocks further evaluation until
  the host resolves it; marking it failed does not automatically resend it.
- M2a uses a fake clock and recorded decisions to test S15/S19/S22–S25 mechanics.
  These are partial scenario proofs, not full S11–S25 or live acceptance.
- The actual queryable information source and topic-note policy are selected in
  M2b. M2-E1 remains pending until that live-use configuration is complete.

M2a implementation and replay results are recorded in
[M2a foundation evidence](../evidence/M2a-foundation.md) and
[M2-NOTES.md](../roadmap/M2-NOTES.md). All M2 exit criteria remain unchecked: a completed
internal foundation does not establish full scenario or live acceptance.

## M2b implementation choices (2026-09-18)

- Source: Wikipedia's read-only MediaWiki search plus introductory extracts,
  using the standard-library HTTP client. The host explicitly enables `en` or
  `zh` via `--wikipedia`; no arbitrary endpoints, crawling, or credentials.
  Only the short query is transmitted, not the conversation. See the official
  [search API](https://www.mediawiki.org/wiki/API:Search) and
  [extract API](https://www.mediawiki.org/wiki/Extension:TextExtracts#API).
- Research requires the source flag, a current `/start` grant, and an enabled
  topic. One active exploration, two query attempts and four model attempts
  per exploration (including its originating decision), ten-minute expiry,
  and twenty source attempts per persisted conversation. `/query-budget N`
  explicitly replenishes the shared allowance. Timeouts/interruption count.
- Each HTTP request is bounded to ten seconds and 256 KiB, with at most three
  1,200-character extracts. Store query, request URL, retrieval time, page ID,
  revision, source URL and response snapshot; errors/empty results are outcomes.
- Exploration IDs route query outcomes through durable pending events. Terminal
  sends remain terminal acknowledgements. No new framework/plugin abstraction.
  Interrupted read-only requests become recorded failures for reevaluation,
  not automatic retries; closed/expired explorations reject late results.
- `/topic KEY TEXT` sets an explicit current topic note (up to 600 characters);
  `/drop-topic KEY` disables it without deleting history. Up to sixteen enabled
  topics, eight in context. Model-drafted notes may accompany a user-turn
  decision, must reference that exact user event, and cannot overwrite a
  host-authored correction. No notes originate from assistant text/nonresponse.
- Topic history retains previous claims separately from the current note.
  Corrections invalidate pending decisions and close affected explorations.
  Context adds up to three recent query outcomes (within 24 hours), with only
  current topic revisions eligible. User replies retain the source evidence.
- `Speak` can cite source IDs from context; the shell checks them and attaches
  stored source URLs. An exploration's finding cannot be shared without a
  source reference. Exact repeated references in unsolicited output are blocked.
  Citation existence is not proof that the prose is entailed; live review is
  still required. Wikipedia is background knowledge, not a news freshness feed.
- Observation and delivery are separate gates once research is enabled. Mute,
  quiet hours and delivery quotas can suppress speech while bounded research
  continues. Cancel/expiry revoke research as well. A gated candidate is
  discarded; later evaluation can reconsider its still-current observations.
- Natural-language control interpretation is not certified by this checkpoint;
  deterministic slash controls remain the reliable contract until dedicated
  intent fixtures and live review are added. No M2 acceptance is inferred.
- A user-turn model response may also propose a narrowing control (`mute` with
  a bounded duration or `stop`), tied to that exact user event. The shell applies
  it atomically with the reply and emits a deterministic direct acknowledgement.
  Wake/source data cannot invoke controls; the model cannot resume, grant budget,
  enable a source or widen scope. Recorded interpretation fixtures do not prove
  accurate natural-language understanding; live intent review remains pending.
