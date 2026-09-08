# Staged preparation: bounded code-review fixes

2026-09-08. Root task brief. Canonical Astra Round2 is terminal REJECT84/100;
High#1 and Medium#2/#3 are independently reproduced and govern this work. No science/prompt/data changes.

Use the same native Sol xhigh implementation handle. Read the archived protocol,
latest ledger STATE, accepted PREPARATION.md and canonical review Round2 first.
The existing four-file candidate is archived at9e6b9cdc. Reviewer is Astra xhigh;
only the reviewer writes results/source-replay-staged/review-astra.md.

## Scope and objective

Fix the three independently reproduced preparation failure paths:

1. Enforce the registered absolute per-request and whole-job deadlines in the
   real transport path. urllib socket inactivity timeouts plus an after-return
   check do not bound an indefinitely trickling response; unbounded future waits
   and executor shutdown must not defeat the budget. Use a small standard-library
   solution, with explicit cleanup of only processes/resources this tool owns.
   Preserve available partial/raw evidence and publish INCOMPLETE on timeout;
   never start a later stage, retry, or publish late preparation success.
2. Preserve HTTP error status, headers and available exact returned body through
   the real urllib HTTPError path, not only injected transport dictionaries.
3. Reject malformed authored types without escaping the preparation state
   machine. In particular private_checks[0].behavior=[] currently triggers
   TypeError in reused screen._check, leaving job.json IN_PROGRESS with no
   terminal after8requests. Preserve received evidence, write honest terminal
   status and all16slot states, and make no dependent/replacement requests.
   Unexpected local validation errors must also preserve records and produce
   INCOMPLETE, without coercing malformed author content.

Allowlist: src/stencil/source_replay_authoring.py,
tools/prepare_source_replay.py, tests/test_source_replay_authoring.py,
tests/test_prepare_source_replay.py. A minimal fix to reused
src/stencil/source_replay_screen.py and its tests/test_source_replay_screen.py
is also allowed if needed for malformed-type validation. All other code, exact
prompts/specification, qualified helpers and scientific launcher stay unchanged.
Do not invent a new review parser, framework, package or broad security project.

## Tests and validation

Write consuming regression tests first and report the initial red results.
Exercise the actual transport path: HTTPError with an available body, and a
trickled local socketpair/real HTTPResponse or equivalent CPU-only controlled
transport that proves an absolute bound and cleanup. No HTTP generation call,
external network request or actual service probe. Assert terminal/partial/raw
receipts, no late success, and attempts/unattempted slots as applicable. Exercise
malformed behavior through the actual synthetic driver, not a stand-alone
producer-only validator test. Reuse existing synthetic fixture content only.

Required command:
PYTHONPATH=src .venv/bin/python -m pytest -q tests/test_source_replay_authoring.py tests/test_prepare_source_replay.py tests/test_source_replay_screen.py

Run targeted Ruff/format and whitespace checks, plus absolute-path --help and
default dry-plan invocation from /tmp. No full pytest. Do not repeat unchanged
checks after they pass unless a later change or failure justifies it.

## Lineage and handoff

Fit-on: none. Synthetic code-validation fixtures only; no evaluation-source,
benchmark, stopped-bank, response, trained-adapter or future authoring data may
be opened or used. In particular do not search results/source-replay recursively;
only its named governing documents may be read. The earlier accidental metadata
search exposure remains disclosed in the ledger and review; do not repeat it.

No model/API/tokenizer/container/preflight or real authoring launch. No commits;
root archives explicit paths and maintains ledger/status. Return exact changed
paths/hashes, red-to-green evidence, static checks, any scoped limitation and
terminal handoff. If implementing transport supervision changes the required
freeze dependencies or launch invocation, state the exact necessary delta;
prefer keeping the accepted four-file interface and17subject freeze.
