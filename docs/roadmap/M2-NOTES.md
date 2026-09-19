# M2 — Current handoff

**Checkpoint:** M2-P1. **Behavior:** CP1-CP7, starting with S26/S31.
**Acceptance:** M2-E7 through M2-E12 remain unchecked.

## Implemented

A local browser/Python prototype connects selected screen and microphone streams
to Gemini Live. It provides explicit start, speech/sensor/session stops, bounded
media and lifetime, metadata traces, and no reconnect. The thin baseline comes
first; no new semantic initiative policy is claimed. Start instructions are in
[README](../../README.md); configuration and coverage are in the
[P1 run sheet](../evidence/M2-presence-p1.md).

The earlier terminal/source prototype remains available and unchanged.

## Verified and unresolved

54 Python tests and four JavaScript replay tests pass, including the synthetic
WebSocket bridge and late-grant cancellation. Browser idle state and sketch
interaction were inspected without accessing sensors. Roadmap checks pass.
No real Gemini call, media session, latency measurement, or owner experience
review has run: the host has no configured API key. Full S31 controls, semantic
staleness, conservative monetary accounting, and actual media behavior remain
gaps. Resource caps alone are not a verified dollar ceiling.

## Next step

Make Gemini access available locally; verify the selected model and spending
accounting. Run the bounded baseline through actual granted screen/microphone
input, starting with S26/S31, and export metadata. Inspect the two-second playback
queue and browser capture behavior against real provider pacing before expanding
P2. Do not mark P1 complete from the synthetic checks.

The owner authorized the presence direction and concise documentation. No new
scope approval is needed for that work; model access and actual capture grants
must still be available. M3, full A expansion, and framework extraction remain
outside the current checkpoint.
