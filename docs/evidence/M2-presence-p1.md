# M2-P1 run sheet

Status: local implementation and synthetic checks complete; no live or owner acceptance.

## Configuration recorded before live use

Activity: discuss and edit a game-layout sketch in one user-selected browser
window/tab. Start sharing explicitly; draw a change after a reply ends without
asking another question. Host: local Python 3.11+, browser Web Audio and screen
capture; headphones recommended. No desktop control or background work.

Provider: Gemini Live v1beta WebSocket, default `gemini-3.8-live`. An environment
override must name another compatible Live model and be recorded in the trial.
Account availability and actual model version remain unverified. The exact
prompt and setup are versioned with the host source. Optional `aiohttp` serves
the UI and proxies streaming media; the API key stays on the host.

| Limit or target | P1 value |
|---|---|
| Session / simultaneous sessions | 120 seconds / 1 |
| Input audio | Mono PCM16 at 16 kHz; 100 ms chunks; 3.84 MB total |
| Visual input | JPEG, at most 1 fps, longest edge 768 px; 100 KB/frame, 120 frames |
| Observation age / outbound browser backlog | 1 second / 128 KB; end on congestion |
| Generated audio / playback queue | 60 seconds total PCM16 at 24 kHz / 2 seconds |
| Context / per-response generation | Compression at 8,192 tokens to 4,096; 2,048 output tokens |
| Connect/setup / blocked send / heartbeat | 10 seconds / 1 second / 5 seconds |
| Explicit playback stop / provider-interruption handling | Target 100 ms / 100 ms after event receipt |
| Spoken interruption end-to-end | Target 500 ms; measurement pending |
| Resource exhaustion | Close session, invalidate output, stop sensors; no reconnect |

These are configured limits or targets, not measured outcomes. Duration, media,
and queue limits are enforced separately. Cost must be recorded from provider
usage and billing: media-only estimates exclude repeated context and reasoning.
A verified conservative monetary bound remains an E7 gap; do not claim a strict
dollar ceiling or run unattended paid trials.

## Controls and retained data

Start grants only the browser-selected visual surface and microphone for this
session. Stop speech clears playback and suppresses the unfinished turn; it
does not claim to stop provider computation. Stop screen/microphone revokes that
input for the session; resuming requires a new explicit session. End stops all
session inputs/output. There is no background worker in this path, so session
end is also stop-all for this prototype. Host/browser restart starts idle.
Mute-unsolicited while allowing direct replies is still a P2 gap.

Only bounded, session-local metadata is retained by Enthus: timestamps, stream
versions, output/chunk IDs, control events, playback reports, and provider usage.
No raw media or transcript is written to disk. Browser playback reports are not
proof of hearing. Export metadata explicitly for a trial; provider retention
follows the account's own terms. Failure closes the connection without replay.

## Trial and coverage

First measure the thin baseline with this same host, model, prompt, capture,
and limits. P1 adds no semantic initiative policy; do not manufacture a baseline
advantage. Later Enthus changes repeat the same activity and record differences.
Use two 120-second runs: change the sketch after a completed reply; interrupt;
revoke one sensor; end. Record capture/receipt/output/playback/stop timestamps,
missed and unwanted contributions, queue overruns, usage, and estimated cost.

| Behavior | Current check | Remaining evidence |
|---|---|---|
| CP1/CP2, S26 | Reply completion preserves session and later input in replay | Actual new sketch change, later grounded use |
| CP3/CP5, S28/S31 | Local stop and revoked-input/late-output rejection in replay | Audible stop latency, full control branches |
| CP2/CP5, S32 | Bounded media/time, disconnect, restart-off replay | Actual provider and device failures |
| CP4, S27/S30/S35 | Provider prompt only | Selective initiative, silence, corrections; no pass claimed |
| CP3, S29 | Queue bound and control invalidation only | Semantic staleness detection |
| CP6, S33/S34 | Disabled in P1 | M3 continuity and separately granted follow-up |
| CP7 | Baseline protocol above | Comparison, measured contribution, owner review |
| S15/S20-S25 | No background topic/research path, persistence, or preference inference | P2 map of applicable conversation branches |

## References

Checked 2026-09-19: [protocol](https://ai.google.dev/api/live),
[capabilities](https://ai.google.dev/gemini-api/docs/live-api/capabilities),
[pricing](https://ai.google.dev/gemini-api/docs/pricing).
Native duplex audio, VAD and sampled vision must be credited to the provider.

## Verification — 2026-09-19

Code: working-tree P1 additions based on `759d706`; Python 3.11.15,
aiohttp 3.14.3, Node 24. Synthetic fixtures are embedded in the test files;
they contain silent PCM bytes, a JPEG marker, and protocol messages, not real
recordings. These prove routing/control behavior, not model perception.

```sh
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v
node --test tests/test_player.mjs tests/test_capture.mjs
python3 scripts/check_roadmap.py
```

- Python: 54 passing tests (44 prior tests plus 10 P1 tests). The first sandboxed
  attempt could not bind loopback sockets; rerunning with local socket access
  passed, using only a synthetic provider.
- JavaScript: four passing replays. Partial playback stays uncertain; cancelled
  chunks cannot revive; queues are bounded; End/expiry during the permission
  picker disposes of a late grant without requesting the microphone.
- Browser: actual local UI loaded with capture disabled because no key exists;
  sketch obstacle interaction rendered correctly. No screen/microphone grant
  or actual media/model test was performed. Final reload reported no browser
  script errors. The temporary preview server was stopped after inspection.
- Editable installation with `.[live]`, the `enthus-live --help` entry point,
  and access to all four browser assets passed.
- Roadmap structure/evidence reference check passed. E7-E12 remain pending:
  full coverage, monetary bound, live observations, baseline comparison, trace
  adequacy for live failures, and owner review are not yet established.
