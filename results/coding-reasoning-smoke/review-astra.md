# Thinking/tool compatibility readiness — Astra

2026-09-08. Independent Astra xhigh reviewer, explicitly selected by the user;
same native reviewer session throughout this review. Root authors prospective
documents; Sol authors implementation. Reviewer writes this file only. Scope:
honest native compatibility, compile/apply continuity, accounting, prospective
resource limits and ownership. Trusted-but-fallible threat model; no malicious
same-user hardening. No model launch, generated-code execution, semantic case
replay or additional agent was used for this preliminary review.

## Preliminary source review — final readiness pending

**Status: PENDING. No final score or launch-readiness acceptance.** Stable new
implementation, tests, preview and resource-plan hashes have not been handed
off. Those files have not been reviewed. Numbered implementation findings have
not yet been opened; later findings must retain their numbers across rounds.

Prospective brief at commit `8404fd2e`, SHA-256
`a2aa571383bd15706433ddd8e8886359f9b84972fc88b9be27c19825592bc598`.
The exact serving pin inspected is `fe9c3d6c5`. The observations below constrain
the implementation review; they do not demonstrate the live combination works.

### Token and history evidence

The pinned nonstreaming serving path returns the complete `output.token_ids`
in `choices[0].token_ids`, separately from extracted reasoning and named tool
arguments. Completion usage is the length of those generated IDs. The named
tool path supports `stop` as its successful finish reason. Streaming is
unnecessary for complete token accounting.
[Pinned serving source](https://github.com/vllm-project/vllm/blob/fe9c3d6c5/vllm/entrypoints/openai/chat_completion/serving.py).

The local original tokenizer has single-token boundaries 151667/151668. With
thinking enabled, its generation suffix does not pre-open the reasoning span.
With the specified fixture and final-only history, cold and post-tool prompts
should contain no historical reasoning markers. A unique generated start/end
pair supports counting tokens strictly between them, excluding delimiters;
the decoded span must agree with returned reasoning, and decoded final content
must agree with the named raw arguments after exact terminal-token treatment.
Repeated, misplaced or ambiguous spans cannot support a PASS. The Qwen parser
can parse reasoning without a generated start, so parser success alone is
insufficient to establish an unambiguous budget-active span.
[Pinned Qwen parser](https://github.com/vllm-project/vllm/blob/fe9c3d6c5/vllm/reasoning/qwen3_reasoning_parser.py).

The budget processor initializes its counter from any tokens after an open
prompt start. Thus, if an implementation permits that alternative prompt
state, generated tokens and initialized budget tokens must be distinguished.
The brief appropriately separates an observed bound from proof that forcing
caused termination. The source also explicitly provisions output IDs for the
budget processor under asynchronous scheduling; the endpoint tests' use of
`--no-async-scheduling` does not itself prove the inherited default unsupported.
[Budget processor](https://github.com/vllm-project/vllm/blob/fe9c3d6c5/vllm/v1/sample/logits_processor/builtin.py),
[GPU runner](https://github.com/vllm-project/vllm/blob/fe9c3d6c5/vllm/v1/worker/gpu_model_runner.py).

### Render propagation qualification sent to root

`thinking_token_budget` is a supported request field passed into sampling
parameters. Native render returns those resolved parameters and the rendered
IDs. However, `SamplingParams` omits default values during serialization:
`PydanticMsgspecMixin._serialize_msgspec` calls `msgspec.to_builtins`. Therefore
**an absent render `min_p` legitimately means its pinned default 0.0**; rejecting
that absence would reject valid native output. The implementation should resolve
that exact documented omission and reject a different supplied value. The
requested nondefault temperature, top_p, top_k, seed, max_tokens and
thinking_token_budget must be explicitly present and correct. Missing
nondefault settings cannot be filled in from the desired request.
[Request propagation](https://github.com/vllm-project/vllm/blob/fe9c3d6c5/vllm/entrypoints/openai/chat_completion/protocol.py),
[parameter defaults](https://github.com/vllm-project/vllm/blob/fe9c3d6c5/vllm/sampling_params.py),
[serializer](https://github.com/vllm-project/vllm/blob/fe9c3d6c5/vllm/v1/serial_utils.py),
[render response](https://github.com/vllm-project/vllm/blob/fe9c3d6c5/vllm/entrypoints/serve/render/api_router.py).

The pinned grammar manager defers its mask while reasoning is active and
uses the prompt's latest boundary to initialize that state. Actual cold and
post-tool render IDs, unchanged request bytes, final-only history and exact
argument schema are consequently meaningful prospective checks. A successful
render alone cannot prove engine budget forcing or final grammar correctness.
[Grammar manager](https://github.com/vllm-project/vllm/blob/fe9c3d6c5/vllm/v1/structured_output/__init__.py).

### Local assumptions and pending checks

The inherited consumer structurally validates and compiles submitted source and
the spliced module without executing generated functions. The brief correctly
limits feedback and success claims to that operation and requires actual first
module continuity into call two. Final review must check that the first prompt
discloses the consumer restrictions and neither failure triggers another call.

Recomputed illustrative sizing is
`4096 / 18.812468347567442 + 780 = 997.727941082736` seconds, leaving
202.272058917264 seconds against 1200. This supports a bounded attempt, not a
worst-case completion guarantee. The final plan must preserve shared startup,
driver and cleanup deadlines and contain stalled HTTP work externally.

Existing inspected helper hashes:

| File | SHA-256 |
|---|---|
| `scripts/coding_competence_run.py` | `4e39d6f0fea4234643447bc1a31a2fb2caad7f1c5e35803537585c1d43812c94` |
| `scripts/coding_competence_dev.py` | `695e9e6228d6ed540d0235442ec3aa515ff1f00b6f3ad303ba76354feaa407a0` |
| `scripts/coding_worker_dev.py` | `41c33ad88fc1fca8d123a71580683d3f478d96c4f1f2f41889303f40c7551b26` |
| `tools/run_coding_competence.py` | `020d112e0980a38cff153dc396058d09b51a00ccfda80083aea3b1b0196c432f` |
| Local `tokenizer_config.json` | `d5d09f07b48c3086c508b30d1c9114bd1189145b74e982a265350c923acd8101` |

Final readiness remains pending the stable handoff and independent targeted
verification. Neither these source observations nor a future compatibility
PASS would establish useful semantic reasoning or automatic-focus parity.

### Source-preparation completion — 2026-09-08

Root prospectively incorporated the documented-default interpretation and the
exact no-open-prompt boundary convention. Reviewed updated brief SHA-256:
`b825673131c68c2436b9c3cc91df2c7ce8beb8a6912eca04f52ac125086db8b5`.
These clarifications agree with the checked native sources and local tokenizer.
The original brief hash above remains the historical source-review snapshot.
No unresolved prospective source contradiction was found. Source preparation
is complete; final scored readiness will resume on a stable implementation,
test, preview and resource-plan handoff, without waiting or polling here.

## Round 1 — complete implementation review, 2026-09-08

**Score: 89/100. Disposition: REVISIONS REQUESTED.** Open findings: critical 0,
high 0, medium 1, low 0. Root independently reproduced finding #1 and requested
its narrow correction before acceptance. No launch-readiness acceptance applies
to this snapshot. Acceptance threshold remains 90/100 and zero open
high/critical findings; severity is not inflated to encode the score.

Stable implementation commit: `181cdf70995affc1b0361d6bb1ac7b85c32b1259`.

| Reviewed artifact | SHA-256 |
|---|---|
| `scripts/qwen_thinking_tool_smoke.py` | `aa40011d5459e7e19455fe5baf828473cf65e478c64cc86a068ea366c1056746` |
| `tests/test_qwen_thinking_tool_smoke.py` | `e15a522d07043d8ecc4c820b3a8addb6a90ba1895c2ac1f4ebec573e990f6456` |
| `tools/run_qwen_thinking_tool_smoke.py` | `5fff5f12750bf30c3b16b3a20d66f6134b66810d41d5b66e24b2ce04d9b83650` |
| `tests/test_run_qwen_thinking_tool_smoke.py` | `a2b008f56ee00f94007d67398dae5ac608a3e431742d06be5ce18445b99277e7` |
| `BRIEF.md` | `b825673131c68c2436b9c3cc91df2c7ce8beb8a6912eca04f52ac125086db8b5` |
| `RESOURCE-PLAN.md` | `65093ef7d879e5ace88d8fe44f265e04619198528bf4ffada4d240cc623ef7a1` |
| `preview.json` | `d979623276e11f29dbb8d822f4dfee3d441b155e07f540ee9988522c5083e0fc` |

### Findings

**#1 — Medium: rejecting an existing run directory overwrites its lifecycle
receipt.** In launcher `main`, `run.mkdir(..., exist_ok=False)` raises for an
existing run. The enclosing exception handler then tests `run.exists()` and
writes `INCOMPLETE_BEFORE_SERVER` into that existing directory's `lifecycle.json`.
An ordinary mistaken reuse of a completed path therefore destroys a prior
receipt even though no server was started. This violates the new-run and
preserved-evidence contract.

Independently reproduced through `main` using a temporary existing run, a
sentinel lifecycle receipt, mocked preparation/PID registration, and a lifecycle
stub that must never be reached. Result: original bytes not preserved; receipt
replaced with `INCOMPLETE_BEFORE_SERVER`; zero lifecycle/process/model launches.
Root independently obtained the same result. Correction: write failure receipts
only into a directory successfully created by this invocation, preserve all
existing run bytes, and retain cleanup of this invocation's newly reserved flag.
Verify the actual `main` rejection path with a focused preservation test.

### Verified behavior and meaningful checks

Independently ran exactly the two registered targeted test files: **20 passed
in 1.84 seconds**. Ruff passed on all four new files. These tests use fake HTTP
and the real local tokenizer/compile-and-splice consumer; generated functions
are not executed. They cover actual cold/post-tool history, same-body rendering
and completion, omitted default min_p, wrong nondefault settings/schema/context,
prompt-ID and usage disagreement, missing end, duplicate start, misplaced
prefix, 513-token reasoning, compile rejection, durable partial HTTP bytes,
dry-run safety and the reused lifecycle's driver/cleanup wiring. They are not
an exhaustive response or operating-system fault matrix.

An additional bounded CPU check exercised the real consumer with exactly 512
reasoning IDs on both synthetic responses. It passed two calls, recorded
`budget_boundary_reached`, and kept `termination_cause_proven=false`. This
complements the suite's explicit 513-token rejection. No GPU/server request,
semantic-bank read, generated-code execution or old-case replay occurred.

The native adapter checks the nondefault settings and exact argument schema
before decode, resolves only the documented omitted min_p default, checks the
actual 2048-token reserve, and rejects prompt reasoning markers. Full output
IDs must match usage; a unique initial start/end pair, nonempty matching
reasoning text and an exact decoded final suffix are required. The parent's
whitespace correction is present: comparison uses unchanged raw arguments,
with one configured terminal EOS treated separately. The targeted newline/EOS
test verifies this behavior. Strict observed-bound checks do not prove native
forcing caused termination.

The first prompt now discloses the relevant syntactic restrictions, including
nested definitions and prohibited statements/builtins. The schedule applies
the first actual source, preserves its module and helper, and sends its genuine
assistant invocation and ID-matched compile/apply feedback into the second
request. Raw reasoning stays in receipts and is absent from replayed messages.
The feedback explicitly says the code was not executed. Failures stop remaining
generations; compile/apply rejection is NO-GO, while native evidence/cap/transport
failure is INCOMPLETE. Pending call records preserve interrupted work, rather
than asserting it completed.

The CPU preview recomputes exactly equal to the canonical artifact, including
all 14 source/tokenizer hashes, request bytes/base64/hash and fixture digest.
The launcher's actual preview validator accepts it. Cold serialized JSON counts
353 local tokens, or 2401 with the output reserve; it is explicitly not an
authoritative prompt count. Later generated history is unknown until actual
rendering. Resource arithmetic remains 997.72794108 illustrative seconds against
1200, without a promised worst-case rate.

Launcher inspection confirms the pinned local image/model, explicit native
reasoning configuration, forced named-tool driver settings, original ownership
label/port compatibility, dry-run default, clean tracked input checks, exact
metadata snapshots, trunk-receipt validation and pre-start resource recheck.
It reuses the previously reviewed lifecycle unchanged: forwarded driver timeout
leaves the 60-second cleanup reserve inside the shared 1200-second deadline;
cleanup/evidence failure overrides success. The prior lifecycle timeout tests
were not rerun because that helper did not change. Trunk verification reuses the
accepted digest manifest with size/mtime checks; it does not rehash model
weights on each launch.

Readiness acceptance belongs to root after reading the final score/findings and
committing the accepted snapshot. The launcher binds exact review bytes and
does not infer approval from prose substrings. The disclosed code-before-tests
sequence is not described as TDD. Apart from #1, this review found no further
consequential defect within the fixed compatibility scope. The correction,
updated launcher/test hashes and refreshed preview/resource bindings remain
required before final acceptance.

## Round 2 — final readiness, 2026-09-08

**Score: 96/100. Disposition: ACCEPTED for the specified bounded compatibility
check.** Open findings: critical 0, high 0, medium 0, low 0. The 90/100 threshold
and zero-open-high/critical condition are satisfied. The preliminary pending
status and Round 1 score/finding above remain historical records.

**#1 — Medium (resolved 2026-09-08).** Correction commit
`3c89fd111d6cdfc25789f457cc63f2527446c162` sets `run_created` only after this
invocation successfully creates the directory, and writes its pre-server
failure receipt only when that condition holds. The actual `main` regression
now rejects an existing run without changing the sentinel lifecycle bytes,
without entering the lifecycle, and without leaving the newly reserved flag.
This directly closes the reproduced failure. The diff changes only this narrow
launcher path and its regression test; no driver changes or new scope.

Independently ran the targeted launcher test file: **7 passed in 0.72 seconds**.
Ruff passed for the changed launcher and test. The unchanged driver and driver
tests retain the Round 1 verification. No model/server calls or generated-code
execution occurred during this delta review.

Final exact SHA-256 bindings:

| Artifact | SHA-256 |
|---|---|
| `scripts/qwen_thinking_tool_smoke.py` | `aa40011d5459e7e19455fe5baf828473cf65e478c64cc86a068ea366c1056746` |
| `tests/test_qwen_thinking_tool_smoke.py` | `e15a522d07043d8ecc4c820b3a8addb6a90ba1895c2ac1f4ebec573e990f6456` |
| `tools/run_qwen_thinking_tool_smoke.py` | `e91c6075782cf304bf4d25e24672ca646024d1311ac86d2cc4183c4ce09dd0a4` |
| `tests/test_run_qwen_thinking_tool_smoke.py` | `c77efcdd8029eaa1ed034f356a005de7864cbe95fdeb134f398d925d3e810412` |
| `BRIEF.md` | `b825673131c68c2436b9c3cc91df2c7ce8beb8a6912eca04f52ac125086db8b5` |
| `RESOURCE-PLAN.md` | `82064e6e32d1593f1cce361acc00a6e6d28ca3af31b0211b23b9cb80c3b43db7` |
| `preview.json` | `0cda62aaf01276ea694eff8ee6a9860590d49dd26b274c4cbcb3d98a391b91bc` |

The canonical preview again equals the independently recomputed CPU preview,
and the launcher's actual preview consumer accepts it. Compared with archived
`preview-r1.json`, only the two changed launcher/test hashes differ. Fixture,
request, settings, token counts and resource fields are exactly unchanged.
The revised resource plan binds this preview and correction commit without
changing the prospective limits. The remaining helper/tokenizer bindings stay
as recorded in the canonical preview and preceding review.

This readiness disposition covers one attempt with at most two generations,
2048 total output tokens and an observed 512-token reasoning bound per call,
inside the owned 1200-second reservation. Root must commit and freeze this
accepted snapshot and use the launcher's immediate exclusivity checks before
execution. It grants no extra attempts, larger allowance or later semantic run.
The live combination remains unmeasured until that attempt: native evidence,
compile/apply continuity and complete owned cleanup determine its result.
Even a PASS would establish neither semantic coding competence, adequate
reasoning for semantic tasks, automatic-focus parity, nor that budget forcing
caused termination. Preserve this accepted report unchanged during the run;
any terminal audit belongs in a separate artifact.
