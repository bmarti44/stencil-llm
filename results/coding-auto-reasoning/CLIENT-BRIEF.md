# Sol xhigh: shared native reasoning tool client

CPU implementation only. Fit-on: none; development uses synthetic transport
fixtures, no semantic bank or benchmark. No model call, authoring or server.
Read archive/plan/PROTOCOL.md and DESIGN.md. Preserve frozen predecessor files.

Allowlist:
- src/stencil/focus/native_reasoning_tool.py
- tests/test_native_reasoning_tool.py

Extract the smallest parameterized client needed by DESIGN.md. Reuse unchanged
NativeToolClient HTTP/deadline/raw-receipt machinery from coding_competence_run
and the accepted thinking smoke's exact native validation logic. No global
monkeypatches, copied experiment loop, generic agent framework or old file edits.
Use an immutable request specification carrying tool name/schema, total cap,
reasoning allowance, context, sampling and seed. Support replace_function and
record_focus, including a current visible-source enum in the latter schema.
The latter returns generic validated tool arguments; do not require a source key
for all tools. Both use forced named native tools and final-only history.

Preserve exact same request bytes for render and generation; exact schema/native
nondefault sampling checks; returned prompt IDs, usage and generated IDs; unique
reasoning boundaries and exact decoded reasoning/final arguments; terminal EOS;
empty/over-budget reasoning rejection; ambiguity and output-cap rejection.
Native default omission is valid only when equivalent to the registered default.
Pending and raw receipts must survive failure. No semantic validation by regex,
manual substitution, hidden reference, repair call or causal forcing claim.

Write focused consuming-path tests first. Exercise both named schemas through
fake native HTTP with real tokenizer; 1024 reasoning boundary and 1025 rejection;
correct final whitespace/EOS, wrong schema/name/ID/usage, cap failure, and exact
history behavior. Reuse synthetic transport fixtures without evaluating old data.
Tests must not import code that executes model or semantic jobs at module import.
Acceptance: .venv/bin/pytest -q tests/test_native_reasoning_tool.py, and Ruff on
the two files. Commit only these explicit paths, then report hashes, tests,
actual model/effort and limitations. Root owns ledger and independent Astra review.
