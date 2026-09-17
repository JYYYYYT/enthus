# M2a: Running the conversation foundation

This checkpoint implements mechanics for the conversational MVP. It is an
experimental local application, not the extracted public framework. M2b still
needs retrieval, topic memory, and grounded proactive conversation.

## Run

Use Python 3.11+ on macOS or Linux. The prototype uses POSIX file locking and
terminal/pipe input; Windows and redirected regular-file stdin are not supported.
No runtime packages are required. From the repository root:

```sh
PYTHONPATH=src python3.11 -m enthus --mode offline
```

Offline replies explicitly identify themselves as synthetic diagnostics.
A wake chooses an event-only wait; it does not manufacture conversation.
The SQLite database defaults to `.enthus/state.sqlite3`. Use `--database PATH`
for a separate conversation. Two processes cannot share an active database.

The optional local model adapter uses Ollama's
[chat endpoint](https://docs.ollama.com/api/chat) and
[structured output format](https://docs.ollama.com/capabilities/structured-outputs).
With a running local service and a model you have already installed:

```sh
PYTHONPATH=src python3.11 -m enthus --mode ollama --model YOUR_INSTALLED_MODEL
```

The command never installs a model. An unavailable service or invalid model
response consumes one attempt and records an error visible through `/status`.
The adapter has replay coverage; no successful live-model trial is recorded.
It cannot retrieve sources or truthfully claim new discoveries at this stage.

## Controls

| Input | Meaning |
|---|---|
| Ordinary text | Append a user message and evaluate in recent shared context. |
| `/start` | Grant initiative for 24 hours; preserve any existing mute. |
| `/stop` | Cancel initiative, including queued output; keep direct chat. |
| `/mute` | Suppress unsolicited conversation until `/resume`. |
| `/mute 30` | Suppress unsolicited conversation for 30 minutes. |
| `/resume` | Clear mute; do not renew a cancelled or expired grant. |
| `/budget 100` | Explicitly set the remaining model-call allowance to 100. |
| `/status` | Inspect persisted controls, remaining calls, last error and unknown action IDs. |
| `/resolve ID sent` | Confirm that an ambiguous action was delivered; add it to confirmed history. |
| `/resolve ID failed` | Confirm non-delivery; unblock processing without resending that action. |
| `/help` | Show command help. |
| `/quit` | Interrupt processing and exit with recoverable state. |

An EOF drains queued work and exits. A local HTTP request already running in a
worker thread can take up to its timeout to finish during shutdown; its late
response cannot commit state or send. Slash commands are deterministic host
controls. Natural-language mute/cancel intent recognition remains M2 work;
typing a request in prose does not reliably set those controls yet.

The terminal prints complete messages asynchronously, with action IDs for
reconciliation. It is deliberately plain: output can visually interleave with
unfinished input, and it has no rich line editor. The input itself remains in
the terminal's input stream. Live owner review must assess its usability.

## Internal path

1. The shell commits input and its exact event ID to SQLite.
2. It applies hard gates and reserves one call before model evaluation.
3. The decider receives bounded context and returns `Speak`, `Wait`, or `Finish`.
4. The shell persists the decision and any pending message together, then
   rechecks current controls before dispatch.
5. Successful delivery commits confirmed assistant history and a terminal
   outcome event carrying the action ID and the single `main` follow-up ID.

`models.py` contains the small typed records; `store.py` owns transactions;
`runtime.py` owns evaluation and delivery sequencing; `decider.py` contains
the diagnostic and local-model adapters; `cli.py` owns terminal lifecycle.
These are internal boundaries, not a generic plugin contract.

Controls and new input invalidate older decisions by revision. Multiple pending
user events coalesce into one evaluation while preserving original messages.
This invalidation establishes freshness of the snapshot, not semantic quality.

Before a model call, budget is durably reserved. Failure, timeout, interruption,
and restart never refund that attempt. A model cannot increase the host's
evaluation frequency, remaining budget, scope, or delivery quota. The exact
defaults are in [M2](roadmap/M2.md).

Before sending, the action becomes `sending`. A crash or unacknowledged send
becomes `unknown`, not a retry. Processing pauses until the host inspects the
terminal/action and resolves its outcome. There is no universal exactly-once
delivery guarantee. The terminal's flush is a local acknowledgement, not proof
that a human read the message.

Confirmed messages form recent context: at most 20 messages and 12,000
characters, keeping each selected message whole. Older messages remain stored
but are not automatically included. Persistent records are local plaintext;
this checkpoint does not implement a retention/deletion or backup workflow.

## Verification and limits

```sh
PYTHONPATH=src python3.11 -m unittest discover -s tests -v
python3 scripts/check_roadmap.py
```

Tests use real SQLite and recorded decisions with a controllable clock, plus
a real CLI subprocess exercised through two-way pipes. They do not run a live
model or external source. See [the evidence report](evidence/M2a-foundation.md)
for the S11–S25 coverage map. The next checkpoint must add actual retrieval and
pending result feedback, small source-backed topic notes, correction handling,
and conversational initiative; shell correctness alone does not fulfill M2.
