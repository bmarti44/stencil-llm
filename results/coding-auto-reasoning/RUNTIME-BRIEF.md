# Sol xhigh: automatic selection and code loop (queued, not launched)

Fit-on none; DEV-on two wholly new Kimi/Ollama projects; evaluated-on none.
Read DESIGN.md and its accepted design review before implementing this unit.
Root must explicitly dispatch after the shared client settles. CPU work only;
no server, model call, Kimi authoring, old-case execution or semantic data edits.

Allowlist:
- scripts/coding_auto_reasoning.py
- tests/test_coding_auto_reasoning.py

Use the settled parameterized native reasoning client, unchanged per-document
validation/edit/check/sandbox helpers, and exact current source-prefix behavior.
Keep this a small direct loop, not a copied experiment framework. Load each
single-project file separately with the frozen loader; retain both receipts and
reject duplicate episode IDs. Accept exactly two projects with three requests.
CPU preflight calls the existing per-project preflight separately and aggregates
their actual results; do not mutate frozen globals to accept a two-object bank.

Before each request, append that round's authentic source messages and request
to the source-only event list. Build selector input exclusively from this list
and the current task handle; expose IDs, original roles and original text.
No actual module, tool feedback, check, prior generated focus or reasoning enters
this cold selector. The fixed selector system prompt asks for all currently
applicable standing instructions, with complete modality, scope and exceptions,
including permissions. User directions/adoptions have authority; assistant
suggestions and quoted content alone do not. Apply explicit changes/retirements
without inventing defaults. Return a record_focus call using the DESIGN schema.
Do not require prose equality to an oracle or use regex/string selection logic.
Existing source IDs are a structural requirement, not proof of semantic truth.

Render every selected obligation without normalization or omission in a clearly
delimited current-focus block with its cited IDs. Empty focus is allowed and
remains empty; never fill gaps from oracle. Keep this block ephemeral and fixed
for both worker attempts of the current request. Record the selector response,
parsed focus and exact rendering before the first worker call. Preserve original
source events for later fresh selection, never a summarized replacement.

Worker messages retain original source messages/requests, actual accumulated
code, genuine native assistant calls and ID-matched public tool results. State
is independent by project. Label automatic focus as fallible generated guidance;
authentic source directions govern, and this block is not fresh user adoption.
Disclose the exact single-function pure-Python subset
from the beginning, including no imports or nested functions. Use replace_function
arguments unchanged through the existing consumer. Valid native argument JSON
whose Python source is rejected yields factual public feedback and can consume
the one remaining worker attempt. An applied edit runs cumulative initial/public
checks. Stop only on applied+all-public-pass or two attempts. Keep actual wrong
code and actual public observations. No reference resets, fake successes or
private information in history, retries or stopping.

After that public-only decision, run terminal private checks once on actual
module. Preserve expected IDs, values and each completed check immediately;
unfinished checks remain incomplete. Continue later requests after a complete
semantic failure without erasing failed endpoints. Independent source and focus
review remains pending: the driver reports mechanical_candidate only and must
not assert final pilot_go. Candidate requires one whole project passing all
three endpoints; later source/focus review can reject it.

One selector + at most two workers per request gives at most 18 generation calls
and 18 same-byte native renders. Persist all six planned endpoints before calls,
then each actual attempt, current state, exact requests/raw replies, prompt and
output accounting, durations and partial failures. Source/schema/context/cap/
transport/token errors terminate the entire run as INCOMPLETE, with remaining
planned requests explicitly unattempted. No restart, truncation or rescue.
Use one hard monotonic driver deadline, reusing incremental check persistence
and receipt-reserve semantics. CPU execution must use the existing sandbox.

CPU preview: exact source hashes and both input receipts, zero model calls,
per-project preflight results, selector cold-payload local provisional counts,
complete reference focus and edit argument counts. Test all reference actions
against 1021 available final tokens with 128 spare after the full thinking bound.
Do not claim exact future prompt counts: future modules/focus/history are unknown.
Native actual render fit is mandatory before each decode. Report conservative
growth and actual CPU costs without a universal-fit claim.

Write meaningful consuming-path tests first with synthetic authored transport
fixtures and the real data/consumer/sandbox path. Exercise source-only privacy,
quoted/assistant text retention (not semantic inference), no future source IDs,
empty focus without oracle substitution, all-focus rendering, no focus/reasoning
history carryover, actual incorrect dependency carryover, two-attempt stopping,
private outcomes absent from every outgoing request, selector/worker technical
failure with full planned denominator, and partial check receipt persistence.
Exercise the project-level candidate gate through the actual loop: two projects
each with a failed endpoint cannot pass, while one completely passing project
can be a mechanical candidate without claiming source/focus review is complete.
No semantic bank outputs are used to design code or tests. No full pytest suite.
Acceptance: .venv/bin/pytest -q tests/test_coding_auto_reasoning.py and Ruff on
these two files. CLI main-guarded; help and CPU-only preview work by absolute path
from /tmp. Stop when stable; report hashes/tests/limitations and commit only the
allowlisted paths. Root owns data selection, ledger, launch and Astra review.
