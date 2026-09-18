# M2b: Bounded source-backed initiative

The application can now query one Wikipedia edition, retain source evidence,
and evaluate whether it is worth sharing. Topics organize context; explicit
exploration IDs route results and enforce lifecycle/budget rules. These are
internal prototype records, not an extracted plugin framework.

## Run with a local model

Python 3.11+ on macOS/Linux; no runtime dependencies. Start a local Ollama
service with a model you have already chosen and installed, then run:

```sh
PYTHONPATH=src python3.11 -m enthus --mode ollama --model YOUR_INSTALLED_MODEL --wikipedia en
```

Use `--wikipedia zh` for the Chinese edition. Without this flag no source is
enabled. The source receives the short query, not the conversation. The local
model receives bounded recent messages, current notes and selected source
extracts. No model is automatically selected or downloaded.

In the terminal, for example:

```text
/topic games I am making a small puzzle game and enjoy elegant game rules.
/start
I am thinking about how to make one simple mechanic interesting.
```

This creates context and a bounded grant; it is not a task assignment or an
obligation to send a message. A due wake can query, speak, wait, or finish.
To investigate, the model must name an enabled topic. To share a finding from
a result event, it must cite IDs from stored source evidence. The shell attaches
the corresponding revision links. Empty, irrelevant and failed queries can
finish silently. A reply from the user includes the same recent source context.

Wikipedia supplies background knowledge; a recently fetched excerpt is not
necessarily newly published information. The prompt distinguishes these.
Existence of a citation does not prove the generated prose follows from it.
Actual conversation quality and semantic grounding still need live review.

## Memory and controls

- `/topic KEY TEXT` sets or corrects a current note. Keys use lowercase ASCII
  letters, digits, hyphens or underscores; note text can use any language.
  Earlier revisions remain in history. A correction closes that topic's active
  exploration and invalidates stale candidates/evidence in future context.
- `/drop-topic KEY` disables the topic and cancels its exploration. It does
  not delete historical data.
- On user turns only, the model can draft small notes referring to that exact
  user event. Host-authored topic corrections take precedence. Assistant text,
  source results and nonresponse cannot produce authoritative preference notes.
- `/mute` suppresses unsolicited speech until `/resume`; `/mute 30` sets a
  thirty-minute mute. Bounded research may continue. `/stop` cancels initiative
  and research; direct chat stays available.
- Experimental model interpretation can propose only `mute` or `stop` from
  the current user turn, with a deterministic control acknowledgement attached
  by the shell. It cannot resume, add budget, enable a source or widen scope.
  Use slash commands when deterministic control matters; ordinary-language
  interpretation has recorded-output tests but has not passed live review.
- `/budget N` sets remaining model-call attempts; `/query-budget N` sets
  remaining source attempts. `/status` shows state, source, topics and unknown
  deliveries. Neither a user reply nor a restart replenishes or resumes grants.

At most sixteen topics are enabled, with the eight most recently updated in
context. Context adds at most three query outcomes from the last 24 hours,
filtered to current topic revisions, alongside M2a's bounded recent messages.
This is small structured memory; semantic similarity and full-history prompts
are not required. Separate topic aliases still depend on the model choosing
the correct key and need live correction tests.

## Limits and recovery

Defaults: one active exploration, two source attempts and four model attempts
per exploration, ten-minute exploration expiry, twenty shared source attempts
and one hundred shared model attempts. The originating query decision counts
toward the exploration allowance. Initial defaults do not refill at restart.
All M2a delivery ceilings, active-chat pauses, quiet hours and grant expiry still
apply. Source responses are at most 256 KiB and three 1,200-character extracts.

The shell gives source calls ten seconds to return. A worker already inside a
socket read may finish later; its result has no authority after cancellation.
The adapter tracks that worker and refuses a parallel request while it ends.
Read-loop deadlines and socket timeouts bound the remaining read; shutdown may
wait for that worker. Source failures consume attempts and enter context as
failures, with no automatic network retry.

Query action, exploration counters, source outcome and pending reevaluation
events are durable. A process interrupted before recording a source result
recovers a failure for that same action ID. It does not issue the query again
automatically. Cancelled/expired results remain audit records with no usable
items in context. Sending still uses the M2a outbox: an ambiguous send must be
resolved by the host and is never blindly resent.

The database migrates from schema 1 to schema 2 in place. Existing conversation,
model-call allowance and controls are preserved. Model observations include
source IDs, excerpts and retrieval time; raw successful/API-error responses
and request URLs remain in the observation record for inspection. Transport
failures have an error record but no completed response snapshot.

## Verify

```sh
PYTHONPATH=src python3.11 -m unittest discover -s tests -v
python3 scripts/check_roadmap.py
```

An explicit public-source probe, independent of any conversation or model:

```sh
PYTHONPATH=src python3.11 scripts/probe_source.py --language en --query 'puzzle game'
```

The [evidence report](evidence/M2b-initiative.md) distinguishes synthetic
decision/source replays from the actual source probe. No successful live model
session or owner experience acceptance is claimed. M2c must complete scenario
and failure coverage before M2d's live conversation acceptance.
