# Resource plan — pending data, implementation and readiness verification

2026-09-08. No new worker run is authorized by this draft. Fit-on none;
development-on two fresh Kimi/Ollama projects; evaluated-on none. Kimi cloud
authoring uses the already authorized local Ollama endpoint and is recorded
separately. No new model, paid API or external compute is acquired.

The complete candidate ceiling is 3600 seconds of owned GPU reservation. Its
completed technical smoke consumed 516.914703271992 seconds, established by
the audited lifecycle in ../coding-reasoning-smoke/run-01/lifecycle.json.
The prospective automatic pilot reserves at most 3000 seconds, including a
600-second startup limit and 60-second cleanup reserve, using the unchanged
owned lifecycle. Combined ceiling charge: 3516.914703271992 seconds. Remaining
headroom to 3600: 83.085296728008 seconds. No later run is assumed to fit.

Two projects x three requests x (one selection + at most two editing calls)
gives at most 18 native render/generation pairs. All calls use a 2048 total
completion cap and 1024 thinking allowance, with context 32768. At the maximum
reasoning span, two reasoning delimiters and one terminal EOS leave 1021 tokens
for final arguments. Accepted reference edits and complete focus objects must
each leave at least 128 of these tokens unused. All six actual reference pairs
will be checked before freeze; task simplification is not a capacity remedy.

The previous richer-context worker produced 5777 completion tokens over
307.08357315306785 generation HTTP seconds: 18.812468347567442 effective tokens/s.
The tiny technical smoke is not substituted as an optimistic throughput estimate.
At this historical rate, 18 x 2048 tokens require 1959.551469744624 seconds.
Adding 600 startup + 60 cleanup + 120 for other work gives 2739.551469744624
seconds, leaving 260.448530255376 inside the reservation. This is a feasibility
estimate, not a bound on growing prompts or future performance. CPU preflight
cost, prompt sizing and independent review remain pending.

The hard shared monotonic deadline bounds actual startup, native rendering,
generation, sandbox checks, receipt writes and cleanup. The driver receives the
remaining allowance after startup minus cleanup reserve. Before every decode,
the actual same-byte render must pass native schema/settings/ID/context checks
with the full output reserve. Unknown future focus/module/history cannot be
claimed to fit from a local preview; overflow or technical failure terminates
the batch as INCOMPLETE. No prompt truncation, retry, cap increase or deadline
extension is available after the freeze.

Reuse the already present Qwen3-30B-A3B model and pinned local image
vllm/vllm-openai@sha256:3dbe092ec5b2cef63b6104d33fa75d6ce53a7870962529ada69f78bbbc38e776,
with the tested qwen3 reasoning/Hermes tool configuration. Preserve the accepted
weight size/mtime manifest and metadata hash qualification without claiming a
new full-weight hash pass. Final source/data/preview/review hashes and exact
container/driver commands will be bound before execution. No wrapper, other
run flag, container or GPU process may be active at launch. Register every
owned process immediately and clean up only resources this invocation creates.

Status: DRAFT. Await reviewed Kimi data, settled client/driver/launcher, zero-call
CPU preview, independent readiness acceptance, tracked freeze and exclusivity
checks. The broader automatic-focus goal and fresh larger paired proof remain
outstanding regardless of this pilot's result.
