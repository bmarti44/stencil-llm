# Sol xhigh: first source-replay implementation stage

Read accepted SPEC.md, DATA-CONTRACT.md, QUALIFICATION-BRIEF.md and canonical
review-astra.md before implementing. First stage only: original-source renderer,
IDs-only native client and two-call mechanical qualification. No scored project
runner or general memory framework. Fit-on none; CPU unit-test stand-ins are
only software checks, never experimental authoring or fit/evaluation examples.
The actual scientific/qualification data author is Kimi K3 via Ollama.

Allowed new files (no frozen existing source edits):
- src/stencil/source_replay.py
- src/stencil/focus/native_source_selector.py
- scripts/source_replay_qualification.py
- tools/run_source_replay_qualification.py
- tests/test_source_replay.py
- tests/test_native_source_selector.py
- tests/test_source_replay_qualification.py
- tests/test_run_source_replay_qualification.py

Use the reuse boundaries in ../source-evidence-research/feasibility-sol.md
and readiness-sol.md if present. No wrappers. The root owns ledger/spec/data;
you own only the allowlisted implementation/tests. Do not commit; report exact
diff, validation and limitations for root's explicit-path archive. Do not wait
on a wrapper lock. Other agents may read and root may edit its own documents.

Write meaningful failing tests first for the real consumers:
1. Original text/role/ID/order preservation through JSON escaping and native
   user evidence serialization; empty selection; duplicate/unknown/over-count
   IDs; UTF-8 boundaries; no input mutation; explicit ephemeral separation.
2. Selector payload/schema/forced tool/nonthinking/fixed cap and exact raw
   request reuse for rendering and generation. Mock actual transport receipts,
   reject mismatched prompt IDs/schema/usage, wrong tool, malformed arguments,
   duplicate IDs, cap finish reason, overruns; accept valid stop at cap.
3. Fixture public/private separation through the actual request builders, exact
   action consumer and sandbox references; two-call plan, incremental records,
   wrong actual behavior distinguished from technical failure, deadline/partial
   result paths, no repeated model call and no silent resume after existing output.
4. Launcher dry default, local existing image --pull=never, current bound files
   and fixture hashes, plan-directed unchanged run_lifecycle reuse, actual
   receipt/terminal validation including cleanup/whole deadline and600second cap.

Keep worker NativeToolClient unchanged. Its perform method is worker-specific;
the selector must validate its own exact schema/tool/cap, without monkeypatching
module globals or pretending its tool is replace_function. Reuse low-level
transport/persistence helpers where semantically identical, no generic client
refactor. Both native pairs have the shared180second deadline described in SPEC.
Use the frozen worker SYSTEM_PROMPT, with no old manual-reminder CURRENT_PROMPT.
Qualification worker receives its original source/request/module/target and
ephemeral evidence only, no expected outputs or reference. Empty selection is
valid. A valid but behaviorally wrong worker patch is measured separately.

The launcher uses the existing tools/run_coding_competence.py::run_lifecycle
plan interface and driver CLI (--input, --output-dir, --base-url, --model,
--deadline-seconds). Preserve original local container settings and pinned image.
Narrow environment readiness must inspect only owned/live resources and current
code/data/asset metadata, never reopen old data or claim a new full weight hash.
No shell wrapper, duplicate lifecycle implementation, whole-repository git
cleanliness gate, old review/artifact gate or repeated old benchmark preflight.
Bound every reused implementation dependency in the freeze. Reject missing
acceptance evidence/different hashes; no acceptance by filename alone. Root will
supply final approved data/code-review receipts before launch. Dry plan may
show missing artifacts and must never start a service.

All script bodies are under main guards; no imports with top-level work. Support
direct absolute-path --help from outside repository. Append-only/exclusive run
paths and durable partial-call records are necessary for the one-shot run.
Do not mark a call or whole run COMPLETE before actual final deadline checks;
late exit/cleanup invalidates eligibility. Reuse existing lifecycle tests as
design evidence; write narrowly for the new consuming path.

Acceptance commands (targeted only; do not run full pytest):
.venv/bin/python -m pytest -q tests/test_source_replay.py tests/test_native_source_selector.py tests/test_source_replay_qualification.py tests/test_run_source_replay_qualification.py
.venv/bin/python -m ruff check <the eight allowlisted files>
.venv/bin/python -m ruff format --check <the eight allowlisted files>
git diff --check
Smoke direct --help and nonexecuting dry plan from /tmp as applicable. Capture
actual red/green results; use pipefail if piping test output. No model weights,
tokenizer loads, GPU/container startup, network/API/Ollama calls, new data,
package installation or actual qualification during this implementation task.
If a concrete ambiguity blocks a minimal implementation, message root promptly
and continue unaffected work. Do not expand scope into the later paired runner.
