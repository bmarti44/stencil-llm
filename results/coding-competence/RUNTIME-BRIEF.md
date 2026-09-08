# Sol xhigh runtime implementation brief — after CPU files settle

Parent-owned brief, 2026-09-08. Read PROTOCOL.md, DATA-CONTRACT.md and
NATIVE-CONTRACT.md. Use their accepted semantics; raise an actual ambiguity
before inventing another gate. This work is CPU implementation/testing only,
not a model/server/experiment launch. Preserve all prior frozen files.

Allowlist for the next coder unit:
- scripts/coding_competence_run.py
- tests/test_coding_competence_run.py

Reuse the settled new CPU consumer and existing receipt/sandbox helpers.
A small standalone native decoder is needed because the old decoder fixes a
768 cap and rejects tool roles. Do not refactor the old frozen runner or build
an agent framework. Launcher integration is a subsequent narrow process task.

Implement one named forced replace_function action. Before each prospective
model action, send identical JSON bytes to the authoritative render endpoint;
verify token IDs/context and named argument grammar. Record auxiliary HTTP
receipts separately. Then send the same bytes to completions and preserve raw
wire bytes, usage, returned IDs and native call. Require exact prompt-ID/usage
agreement and registered successful stop finish. Preserve length/invalid bodies
before technical rejection. No local normalization can stand in for authoritative
rendering. Reuse HTTP timeout/error receipt mechanics where practical. Pending
receipts must exist before requests; all writes and partials need durability.

New public/private loader is the only source of worker-visible data. Build
chronological source prefixes without future messages or future public cases.
Manual recap is a current-only block for all attempts, removed before the next
request. Tool calls/results and submitted source remain their actual native
history; actual current code is visible. Never stringify the full document or
private scoring objects into a prompt. Use each project's own accumulated state.

At most three candidate calls/request. JSON-valid native source that fails
function/compile validation leaves prior module, returns a factual tool error,
and can use remaining attempts. Applied code runs cumulative public checks and
returns only those outcomes. Stop a request only on applied+all-public-pass or
attempt exhaustion; no private pass/fail can select an attempt or stop a request.
Then run terminal private initial/cumulative functionality/current obligation
checks ONCE against actual final code, preserving all expected IDs/results.
A later request cannot erase a failed endpoint. No gold reset. Technically
complete requests continue the project even when private scores fail.

Any technical failure terminates the entire run. Save current receipts/state,
mark unfinished checks and remaining planned requests incomplete/unattempted,
and make no further generation. Do not replay malformed argument JSON by
repairing, dropping, synthesizing or relabeling its history. Technical failures
include render/context/schema mismatch, transport, output cap, malformed native
wire and token accounting. Python source errors in otherwise valid native calls
are consumer failures, not transport errors. Public sandbox errors remain public
feedback; private execution errors fail the endpoint and never enter history.

Enforce a hard monotonic deadline including request/check/receipt reserves.
Persist each check result as it completes; a timeout cannot lose already
completed work. Record all 12 planned request identities and actual attempts,
not 36 fictional executed slots. Summarize attempted/terminal/unattempted work,
public and private outcomes, first/terminal submissions, errors, tokens and
latencies by project, with accounting distinct from scientific pass. CLI exit
0 for passing recorded mechanical prerequisites (independent source review
still pending), 1 for complete no-go, 2 for incomplete technical evidence.
Name the driver flag mechanical_go; final competence_go needs source review
and launcher lifecycle/accounting, and cannot be asserted by the driver alone.

CPU preview accepts reviewed data and uses exact JSON argument response bytes
for reference token headroom (including an EOS allowance), source hashes, CPU
execution timing, and conservative context/resource bounds. Local prompt sizes
are provisional until native render comparison; do not label them exact cold
requests or replace unknown future worker states with oracle states. No silent
context truncation. Repeated current-module observations must be accounted for
in bounds. Default settings are the prospective constants, not tunable via
post-output rescue flags. Main-guarded direct absolute CLI works from /tmp.

Write meaningful targeted tests first for the consuming paths: a fake HTTP
server returning actual render/completion shapes with the real tokenizer and
real sandbox; two/three-action repairs with genuine tool history; private/future
sentinels absent from every exact outgoing payload; current reminder removal;
real accumulated wrong-state behavior; cap/invalid-JSON/token-mismatch technical
stop with remaining requests accounted; and partial per-check persistence under
a deadline. Test source parsing/compile through the new consumer, not a mirror.
Run only `.venv/bin/pytest -q tests/test_coding_competence_run.py` and Ruff on
these two files. Stop edits when stable and report hashes/tests/limitations to
root for independent Astra readiness review. Do not launch any server, call
Kimi, execute evaluation banks or write the ledger; root owns orchestration.
