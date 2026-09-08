# Coding competence prerequisite — prospective preparation

2026-09-08. Follows the accepted [research decision](../coding-self-cue/research-reset/report-source.md).
This is new DEV preparation, not permission to replay or repair the parked
same-response screen. Goal: qualify the worker/environment with independently
correct manual reminders before preparing a learned automatic interpreter.
No automatic-focus or broad-competence claim follows from this prerequisite.

Four wholly new Kimi K3/Ollama projects, three connected requests each. Each
starts with a real working helper and three target stubs. New functions must
use actual earlier dependencies. Include meaningful validation, ordering and
scope requirements plus a real standing-rule change and later use. Do not
simplify away integration to fit a token cap. All code is one pure Python
module with synchronous, single-argument functions and JSON inputs/outputs;
reuse the existing seccomp consumer's allowed Python subset. No imports or
external resources. Each edit replaces exactly the current requested function.

Use native chat tool calls with named forced `replace_function` tool choice.
Expose one `replace_function` function tool, additionalProperties false, with
arguments exactly `{ "source": STRING }`, where source is the entire current
target function, beginning with its def at column zero. The current path and
symbol come from the authenticated request, not generated identifiers. No
Markdown fences, inferred corrections, extraction from prose or synthesized
function bodies. The protocol adapter may pass this exact source through the
existing strict function parser/splicer; structural wrapping needed by that
parser is interface conversion, not a repair of generated text. Compile before
applying; retain valid-but-wrong code and leave prior state on rejection.

At most three model calls per request, including the first candidate. Exactly
one tool invocation is eligible per call; no parallel actions. Each valid action
runs cumulative public functional checks on actual current code in the existing
sandbox. Return a concise native tool result with apply status, current module
and only public check outcomes. If submission applies and all public checks
pass, end the request; otherwise permit another candidate until the third.
A parse, compile or public-check failure consumes its call and may receive the
same fixed feedback policy. A transport, malformed-usage or output-cap failure
ends that request with technical-incomplete status; no recovery call. No hidden
result influences stopping, feedback or a subsequent model request.

After the public stopping rule or attempt limit ends the request, execute its
registered private terminal checks once against actual code: initial helper
checks and cumulative stable private functionality, plus only the current
obligation checks. Record every result in the same run. Carry the actual code
and all genuine action/observation history into the next request. Failed code
is never replaced by a reference. A later request does not erase an earlier
failed endpoint. Check identities and terminal module hashes make the exact
consumer and scored artifact auditable.

Authentic authored source messages and requests retain their user/assistant
roles. Native assistant tool calls and tool results retain their actual roles
and matching IDs. Correct manual reminders appear in an ephemeral current-only
user block for all attempts of that request; remove that block before the next
request. It is an evaluation control, not newly adopted standing instruction.
The first call and all later calls see actual current code. No reference patch,
private cases/expected values, oracle labels, mutants, private pass/fail or
private-error text enters any model request. Public cases are an explicit
separate development artifact, visible to the worker. Their full expected
outputs must be invariant to the standing-rule distinctions under study. Public and private input
cases must be disjoint, and public functionality must not supply the hidden
standing-rule answer to a future automatic/H comparison.

Prospective eligibility requires all 12 terminal requests and all four entire
projects to pass private functionality and obligation checks, independent
source/dependency review, no unresolved technical failure, zero human repair
and complete accounting within the frozen resource budget. Report all attempts,
including repaired format failures, and first-attempt/terminal outcomes. Four
perfect projects prove feasibility only. Failure parks this operating point;
no extra attempts, cap/prompt repair or easier replacement bank on these cases.
Success permits the distinct learned-interpreter preparation, not a success
claim for automatic focus. Adequate fresh larger validation remains necessary.

Pinned starting candidate: existing Qwen3-30B-A3B model and serving image,
non-thinking, temperature 0, seed 20260908, context 32768. Native tool protocol,
server parser flags, exact request tokenization and code hashes require explicit
preflight verification. Candidate per-call cap 1024 and reservation 2700 seconds
(startup 600, execution allowance 120, cleanup 60) are provisional until reference
actions have at least 128 native generation tokens headroom, all contexts fit,
and measured CPU/resource estimates are accepted. Hard existing authorization
ceiling remains 3600 seconds. No launch before reviewed data, implementation,
preflight, exact freeze and ownership/resource checks.

Record write-ahead call receipts, exact native request/raw response bytes and
hashes, tool arguments/IDs, apply decisions, actual pre/post modules, genuine
history, all public/terminal-private outcomes, token accounting, timing and
technical errors. Persist partial output on interruption, including unfinished
checks and unattempted slots. Register every owned background PID and remove
only owned resources. Prior run artifacts and frozen inputs remain unchanged.
Fit-on none; DEV-on wholly new Kimi conversations; evaluated-on none. No data
or responses from any previous evaluation or spent DEV project are fit data.
