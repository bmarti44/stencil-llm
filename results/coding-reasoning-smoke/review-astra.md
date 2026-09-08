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
