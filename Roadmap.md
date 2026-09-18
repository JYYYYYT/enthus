# Enthus — Roadmap

> A companion for continuous co-presence and continuity across shared experiences.

## Product direction

The companion participates in an unfolding shared environment without requiring
the user to turn every change into a prompt. It may notice, comment, ask,
respond, or remain quietly available. Later sessions build on actual shared
experiences. Whether this participation is welcome is part of acceptance.

One product has two complementary modes:

- **B — Co-presence:** perceive and participate during an explicitly enabled session.
- **A — Background follow-up:** investigate or reconnect under a separate bounded grant.

Build B first, then cross-session continuity, then only the A behavior that use
justifies. A session can include long quiet periods. Bounded sessions are the
MVP's test boundary, not a requirement to reset after each reply or a ceiling
on future duration. A generic framework or AGI claim is not a delivery goal.

## Continuous presence contract

These clauses define continuous presence. [M1](docs/roadmap/M1.md) translates
them into observable scenarios; implementation shortcuts must preserve them.

- **CP1 — Shared environment.** Fresh visual/audio observations arrive without
  a new user message, manual upload, or per-observation instruction. Sampling
  and event-driven capture are allowed with measured freshness/missed-event limits.
  Web queries or chat-history retrieval alone do not satisfy this requirement.
- **CP2 — Presence survives a reply.** Output completion and silence leave the
  granted session receptive to later changes. End, expiry, revoked permission,
  or failure are explicit states. No endless generation or end-token removal
  is required; keeping a process alive alone proves nothing.
- **CP3 — Interaction is interruptible.** Input continues during generation and
  playback. The host promptly stops playback and invalidates queued/stale output.
  Slow research cannot block listening or stop controls. Queuing interruptions
  until an old reply finishes is insufficient.
- **CP4 — Participation is selective.** A relevant event can prompt a grounded
  contribution without a question. Silence remains receptive. Constant scene
  narration, compulsory greetings, and avoiding every opportunity all fail.
  Observing a scene does not prove the user's intention or feelings.
- **CP5 — Scope is explicit.** Show what is shared; distinguish stopping speech,
  sensing, the session, and background work. Session access does not authorize
  all-day recording. Memory restoration cannot reactivate sensors. Disconnection
  or exhaustion must be visible, never presented as continued observation.
- **CP6 — One companion spans time scales.** A and B share history, preferences,
  grants, and activity identity, with separate execution needs. Session end
  preserves history but grants no background work. Background results enter
  current context and are reconsidered before they can interrupt.
- **CP7 — Prove the experience.** Use live participation, sampled silence, and
  owner review. Compare with a thin direct-model baseline and identify native
  provider capabilities. Replay success, message volume, or human likeness
  cannot establish experience value.

A **shared session** is a granted period with selected inputs, limits, and stop
conditions. **Co-presence** is the experience of participating together;
**continuous presence** is the capability to remain receptive across turns.
Runtime continuity does not imply consciousness or a self-preservation goal.

## First prototype

One user, one shared visual surface, bidirectional voice, one model/provider
path, bounded context, and one local host. A game or sketch is an example;
M2-P1 selects the activity. Use existing model capabilities, either native
realtime or a measured composition. A media-capable UI is allowed. Desktop
control, all-day sensing, durable raw-media recording, multi-provider support,
and a generic plugin system are outside the first proof.

## Architecture

Live reception, interruption, and playback remain responsive while background
work runs. Both use shared context and explicit activity identity. These are
responsibilities, not required classes or separate products.

- **Host-owned effects:** inference proposes content/actions; the host controls
  capture, playback, tools, persistence, and cancellation. `evaluate()` stays
  effect-free without having to contain the whole live session. No extra model
  decision or durable transaction is required for every media chunk.
  Decisions select concrete next steps, not an abstract initiative score.
- **Hard gates:** host-granted scope, budgets, and disturbance limits cannot be
  overridden by model scores. Stops remain effective during late results and
  reconnects. Speech, sensor, session, and follow-up controls follow M1 S31.
- **Freshness and identity:** timestamp/version observations and outputs; route
  outcomes by action/follow-up ID, not semantic similarity. Reject obsolete
  output and keep media buffers bounded instead of replaying a growing queue.
- **Truthful state:** distinguish generated, queued, played, cancelled, and
  uncertain output. Playback does not prove the user heard it. Keep exact
  execution state separate from evidence-backed memory; current corrections
  override older claims. AI speech and nonresponse do not establish preferences.
- **Bounded recovery:** reconcile unknown effects rather than blindly retrying.
  Host restart leaves capture off; interrupted speech is not automatically
  replayed. Enforce duration, media/context, and usage/spending limits; call
  counts alone cannot bound a streaming session. Label estimates and expose
  exhausted/degraded state without a compulsory model-generated farewell.

Python, async-first host code, and SQLite are the starting point. Record reasons
for dependencies before adding them. Style/persona is data and cannot override
controls. Topics organize knowledge; concerns express reasons to pay attention;
neither grants a mandate. Follow-ups identify bounded activity. Retrieval and
memory frameworks are introduced only after demonstrated need.

## Validation and milestones

Bring a bounded live check forward, with controls from the start. Compare using
the same model, sensory access, activity, and basic context where possible;
record differences. Review grounding, participation, missed opportunities,
interruption/staleness latency, continuity, burden, and cost. Record numeric
targets before trials. Replays check mechanics, live tests check interaction,
and owner review checks value; a small trial does not establish market demand.

| Milestone | File | Goal | Status |
|---|---|---|---|
| M1 | [M1.md](docs/roadmap/M1.md) | Behavior specification; historical approval retained | complete |
| M2 | [M2.md](docs/roadmap/M2.md) | Bounded continuous co-presence | in progress |
| M3 | [M3.md](docs/roadmap/M3.md) | Cross-session continuity and sustained value | pending |
| M4 | [M4.md](docs/roadmap/M4.md) | Second scenario and evidenced reuse | pending |
| M5 | [M5.md](docs/roadmap/M5.md) | Reproducible companion and justified components | pending |

M1's completion covers its 2026-09-17 approval only; current S26-S35 behavior
is accepted through M2/M3. M4 chooses its second scenario from actual needs;
deployment watch is optional. M5 releases the companion; independent integration
must justify any separately published library.

For work state, read the active milestone's handoff. [EXECUTION](docs/roadmap/EXECUTION.md)
owns the evidence process. [History](docs/history/README.md) preserves earlier
decisions and approvals; it does not override this plan.
