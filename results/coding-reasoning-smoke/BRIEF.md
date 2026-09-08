# Qwen thinking and named-tool compatibility check

2026-09-08. Prospective CPU implementation brief; not launch-ready until the
finished code, tests, preview and resource plan receive independent review.
Research decision: ../coding-competence/research-next/report-source.md, accepted
by Astra xhigh at96/100, commit747ba8bc. Sol xhigh implements; Astra xhigh reviews.

Lineage: fit-on=none; semantic DEV/evaluation=none. Use one newly embedded
trivial API fixture solely to check native reasoning/tool/history compatibility.
No old competence cases, responses or larger-test examples are read or replayed.
The fixture is implementation test scaffolding, not a Kimi semantic data bank.
Any later semantic bank must be freshly authored by Kimi K3 through Ollama with
disjoint provenance and separate prospective qualification.

## Scope and fixed behavior

Write only these files:

- scripts/qwen_thinking_tool_smoke.py
- tests/test_qwen_thinking_tool_smoke.py
- tools/run_qwen_thinking_tool_smoke.py
- tests/test_run_qwen_thinking_tool_smoke.py

Root owns this brief, results/coding-reasoning-smoke/RESOURCE-PLAN.md and ledger.
Do not edit any existing frozen code/data/result. Native coder, no wrapper or
restorer. No GPU job, inference, semantic data generation, downloads or server
launch during implementation. Commit only your four paths after targeted checks.

Implement a small standalone compatibility check, not a general experiment
framework. Reuse NativeToolClient transport/deadline/receipt helpers and
coding_competence_dev.consume_action without mutating their globals. Override
only the fixed request/exchange behavior needed here. Reuse the existing owned
run_lifecycle unchanged through its plan and CLI interfaces. Preserve its port
and ownership-label contract. Do not call old bank-specific artifact validators.
Bind every reused source helper by hash in the new freeze/preview.

The new driver accepts the existing lifecycle CLI shape: --input is an exact
built-in fixture identifier, not a semantic data path; --output-dir, --base-url,
--model, --deadline-seconds have their existing meanings. Reject arbitrary fixture
identifiers. Embed a tiny pure-Python module and two requests replacing the same
authenticated function. Disclose actual consumer restrictions before call one.
Apply the first actual source with consume_action, preserve its actual module,
then issue call two with the genuine assistant invocation, ID-matched tool result
and current module. Feedback says only what compile/apply checked. Do not execute
generated code or claim semantic correctness. No fabricated success, reference
reset, retry, repair, or extra generation after either failure.

Exactly two generations, each preceded by native /v1/chat/completions/render
with the exact same JSON bytes as its generation request. Settings fixed:

- Existing local Qwen3-30B-A3B, pinned image and model identity as run-01.
- qwen3 reasoning parser; hermes tool parser and auto-tool-choice enabled.
- Explicit reasoning boundaries <think> and </think>, no transition phrase.
- Nonstreaming; forced replace_function; parallel tool calls disabled.
- enable_thinking=true; temperature0.6, top_p0.95, top_k20, min_p0; seed20260908.
- thinking_token_budget512; max_tokens2048 including reasoning and final action;
  context32768; return_token_ids=true. Do not set include_reasoning=false.
- Total owned reservation1200seconds; startup600; cleanup60. Hard lifecycle
  timeout contains stalled HTTP/driver work; all phases share the reservation.

## Required evidence and gates

Before each decode, require valid integer render prompt IDs, exact named argument
schema, the actual2048 context reserve, and the resolved native sampling/budget
settings. A render rejection must prevent its generation. Validate precise
supported fields against the pinned serving implementation; never silently drop
an unsupported setting. Persist raw requests/responses, byte hashes/lengths,
pending/partial receipts and technical errors before leaving a failure path.

For each completion require matching render/completion prompt IDs, exact usage
and complete output-ID accounting, one named action, and the pin's supported
successful finish reason. Length/cap, transport or schema failures terminate
the check. Preserve raw reasoning in receipts, but replay only final tool output
and genuine tool feedback in the second request, following Qwen's history guidance.

Load only the existing tokenizer files with local-files-only behavior; never
load model weights on the CPU path. Pin and validate the single-token reasoning
boundaries. From raw output IDs and the exact pinned parser convention, verify
nonempty reasoning, its ending before final tool content, and observed reasoning
tokens within512. Verify cold and post-tool prompt boundary state from actual
render IDs; unexpected earlier end markers are an incompatibility, not a reason
to modify history after launch. Reject missing, ambiguous or inconsistent
boundary/accounting evidence. Raw response reasoning must be present as well.

Distinguish an observed count below the allowance from reaching its boundary.
Neither observation alone proves that budget forcing caused termination; no
forced-truncation claim without direct evidence. Overall token and wall limits
remain hard bounds regardless. This smoke does not establish that512 reasoning
tokens are adequate for semantic coding tasks.

A PASS means both recorded native calls, observed reasoning bounds, exact tool
schema, compile/apply continuity, accounting and owned cleanup all pass. Complete
compile/apply failure is NO-GO for this technical combination; missing evidence,
cap/transport/time/cleanup failure is INCOMPLETE. Neither is automatic-focus or
worker-competence evidence. Report partial progress honestly, no silent skipping.

## Launcher and validation

Launcher defaults to dry-run; --execute is the sole inference switch. Dry-run
creates no container or model request. Use a new run-* direct child under
results/coding-reasoning-smoke, a unique owned container and RUNNING.flag, exclusive
review lock, current GPU/container/flag conflict checks, local-image-only startup,
clean tracked frozen files, exact trunk hashes, and immediate owned PID registration.
Reuse tested lifecycle/process helpers rather than copying cleanup machinery.
Freeze the embedded fixture's source, new code, reused helpers, tokenizer/trunk,
settings, prospective documents, preview and accepted readiness review before
startup. Do not falsely bind unrelated old semantic data. Existing processes
must never be stopped. Save complete server/driver/cleanup receipts.

Write focused tests first through the actual new consumer paths: valid cold and
post-tool nonstreaming exchanges; authentic history excluding raw reasoning;
same-body render/generation and total-token reserve before decode; missing or
mismatched IDs/usage/schema/settings; absent, ambiguous, over-budget or misplaced
reasoning boundaries; malformed action and compile rejection; durable partial
transport failure; no extra calls after failure. Test launcher plan/driver wiring,
dry-run safety, frozen source/fixture checks and owned failure cleanup using fake
processes/clocks. Reuse existing lifecycle tests where no behavior changed; avoid
the full suite. No real model request in tests.

Acceptance commands:

    .venv/bin/python -m pytest -q tests/test_qwen_thinking_tool_smoke.py tests/test_run_qwen_thinking_tool_smoke.py
    .venv/bin/ruff check scripts/qwen_thinking_tool_smoke.py tools/run_qwen_thinking_tool_smoke.py tests/test_qwen_thinking_tool_smoke.py tests/test_run_qwen_thinking_tool_smoke.py

Smoke-invoke both new --help paths and the launcher's dry-run/preview mode.
If a pinned response field or reusable interface contradicts this brief, report
the exact source evidence promptly; root will make a prospective decision before
launch. Do not expand architecture or switch to streaming to work around it.

Return stable hashes, actual targeted test results, exact preview command and
artifact, and any remaining source-qualified limitation. Root updates ledger
with native agent/model/effort and test/commit receipts; author-disjoint Astra
reviews the complete implementation and resource plan before execution.
