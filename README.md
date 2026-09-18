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

**M2 is in progress; live audiovisual presence is not implemented yet.**
The existing terminal prototype has topic memory, bounded Wikipedia queries,
persistent state, and budget/mute/cancel controls. It has recorded tests and a
source probe, but no successful live-model experience acceptance.

Next: choose one shared activity and model/media path, then demonstrate fresh
input after a reply ends and a working stop. See [M2](docs/roadmap/M2.md) for the
plan and [current handoff](docs/roadmap/M2-NOTES.md) for the working state.

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
