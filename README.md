# Enthus

**An AI companion that shares the moment and remembers the experience.**

Enthus explores **continuous co-presence**: while you share an activity, the
companion keeps seeing and listening across conversational turns. It can notice
something worth discussing, accept an interruption, or stay quietly available.
Later conversations can build on what you experienced together.

For example, while looking at a game or sketch together, it might connect a new
detail to your earlier discussion without waiting for another question. It should
also know when a comment would get in the way. This is the experience we are
building toward, not a claim about the current implementation.

## Direction

One companion combines live participation with continuity across sessions.
Background research or follow-up is added only when it improves that experience.
Start with one user, one shared visual surface, and voice interaction; compare
against a simple direct-model baseline before adding machinery.

Continuous presence means remaining receptive within the user's chosen scope.
It does not require constant speech, endless generation, or all-day recording.
The precise behavior is defined in [Roadmap](Roadmap.md#continuous-presence-contract).

## Current state

**M2-P1 has a local browser prototype; real audiovisual experience is unverified.**
It connects selected screen/microphone input to Gemini Live, with separate speech,
sensor, and session stops, bounded media, and metadata traces. Synthetic bridge
and playback tests pass. Model access, real capture, interruption latency, and
owner review are still pending. Selective initiative is not yet established.

See [M2](docs/roadmap/M2.md) for the plan and the
[current handoff](docs/roadmap/M2-NOTES.md) for remaining work.

## Try the presence prototype

Python 3.11+ and a browser supporting screen capture and AudioWorklet (start with
Chrome). Install the optional live dependency in a local environment:

```sh
python3.11 -m venv .venv
.venv/bin/python -m pip install -e '.[live]'
.venv/bin/enthus-live --prompt-key
```

Enter a Gemini API key at the hidden terminal prompt; it is not saved. Alternatively
set `GEMINI_API_KEY` in the host environment. Open `http://127.0.0.1:8765`, then
explicitly start sharing a sketch tab/window and microphone. Use headphones.
Without a key, omit `--prompt-key` to inspect the UI with capture disabled.

The default model is `gemini-3.8-live`; `ENTHUS_LIVE_MODEL` can select another
compatible Live model. Availability must be checked against your account.
Sessions end after 120 seconds and never reconnect automatically. This is a thin
model baseline, not accepted co-presence. Read the short
[run sheet](docs/evidence/M2-presence-p1.md) for limits, controls, cost limitations,
and the first live check. Export metadata explicitly if recording a trial.

## Try the existing terminal

Python 3.11+ on macOS/Linux, no runtime dependencies. From the repository root:

```sh
PYTHONPATH=src python3.11 -m enthus --mode offline
```

This produces synthetic diagnostic replies; it is not the presence demo.
Use `/help`, `/status`, and `/quit`. For the optional local-model/source setup,
see the [terminal guide](docs/history/M2b.md).

## Read and contribute

- [Roadmap](Roadmap.md): product meaning, architecture, and milestones.
- [Behavior scenarios](docs/roadmap/M1.md): what must be observable.
- [AGENTS.md](AGENTS.md): contributor workflow and coding rules.
- [Evidence](docs/roadmap/EVIDENCE.md): what has actually been verified.
- [History](docs/history/README.md): earlier plans and implementation guides.

[Apache-2.0 license](LICENSE).
