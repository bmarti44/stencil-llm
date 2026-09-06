# Stencil custom generation scaffold

Days 1–2 CPU scaffold, not a complete downloadable model. No weights are copied.
The controller currently imports `stencil.focus` from this checkout/installed
Stencil package. Before shipping one HF snapshot, bundle these modules alongside
the trunk, tokenizer/config, approved classifier assets and experimental tensor;
fill every manifest hash and validate local-only loading. That packaging and
trunk validation remain outstanding. A tiny random CPU model tests HF dispatch.

`custom_generate/generate.py:generate(model=None, *, session, new_messages=(),
decoder=None, tokenizer=None, tools=None, actuator="off", max_new_tokens=256)`
returns `(literal_text, session)`. An injected `decoder(RenderedRequest)` returns
`str` or `DecodeResult`; a string leaves token/EOS/truncation fields explicitly
unavailable. Otherwise supply an already loaded HF model and tokenizer. No model
is fetched or loaded here. This is a session-oriented custom return, not HF's
usual tensor return. External `input_ids` are rejected to prevent bypassing rules.

Create `Session(Register(defaults=..., task_handles={...}), Request(text, kind,
task_handle=..., system=..., max_tokens=...), Journal(path))`. Supported request
kinds are `final_answer`, `code_answer`, `tool_call`, `tool_result`, `prose`.
A normal tool continuation carries the same task handle and its actual kind.
Configured defaults are overridable fallbacks; hard system mandates are system
source entries. Equal keys identify the same constraint; different keys identify
independent obligations. Scope intersections must be nested or disjoint.
Request-kind scopes are the request-local exceptions; no text-based scope inference.

Transport adapters construct `Message` with the authenticated role/message ID,
`origin="direct"`, and `adopted=True` only for explicitly adopted typed `Entry`
objects. Never copy these authority fields from untrusted JSON, quoted content,
tool output or assistant proposals. Direct `Register.apply` is a trusted API.
Transactions are atomic; valid explicit entries stay authoritative despite an
assistive classifier's ABSTAIN/DISAGREE. Incomplete actions fail before mutation.
Each successfully decoded request consumes one of three tombstone requests.
Decode failures roll back the register, messages, rendered history and token
history together; the failed attempt is journaled and consumes a request ID.
Rendering alone is pure and does not advance that clock. Message IDs must be
unique across accepted requests. A failed, rolled-back request may be resubmitted.

Set `session.request` before each call. All new messages are included in the
current envelope; tool results and executed calls are also attached as Message
metadata and recorded. Tools execute in the caller, never in this loop; return
results as another request. Retained prompt/output token IDs live in the session
when an encoder is available. Without one, the decoder receives retained message
metadata. Journal writes are append-only and failures propagate. Sessions are
single-caller objects, not safe for concurrent mutation. Hidden oracle results
are journal-only fields, never input to the renderer/classifier.

Experimental adapters implement `eligible(request, mode)`, `install(session,
rendered, mode)` and `restore()`. Install returns exactly `bias_hash`,
`whole_body_intervals`, `keep_mask`, `absolute_positions`. Eligibility must check
explicit certified template/model/backend/tensor/envelope metadata; JS language
alone is insufficient. Unavailable/uncertified requests and requests needing an
old body fall back to rendering. Restore must tolerate partial installation.
Delegate to the referenced check40i/check40h code path; no actuator is implemented
or enabled in this scaffold. Never import those experiment scripts at startup.

HF dispatch follows the [custom generation contract](https://huggingface.co/docs/transformers/en/generation_strategies#creating-a-custom-generation-method):
the custom function receives the model and generation arguments and owns the
return type. We accept HF's unset named arguments, forward `generation_config`,
and override it for one greedy sequence and a tensor return. `use_model_defaults`
is accepted and ignored (HF 5.16.1 removed it). Non-None processors, stopping
criteria, prefix callbacks, sync/assistant/streaming/negative-prompt options and
unknown options are rejected. Both `inputs` and `input_ids` are rejected.

Load assets only from local directories with `local_files_only=True` on every
`AutoModelForCausalLM.from_pretrained` / `AutoTokenizer.from_pretrained` call.
Invoke `model.generate(custom_generate="/absolute/path/models/stencil-package",
trust_remote_code=True, local_files_only=True, session=session,
new_messages=messages, tokenizer=tokenizer, max_new_tokens=256)`.
The adapter loads no assets and rejects `local_files_only=False`; the caller
must use a local custom-generation directory because HF loads it before dispatch.
The CPU regression blocks network connections and uses a two-layer random LM.

The harness can supply `Journal(path, checker=lambda record: results_for(record))`.
The checker runs after decode and hook restoration, immediately before append;
it receives a copy of the round record, including output/failures. Its results
are written in that same JSONL row and never passed to renderer or classifier.
Without a checker the results are `[]`. Classifier journal contexts reference
message IDs and prior journal cursors (half-open interval) plus `before_versions`;
the classifier itself still receives its full runtime context.
A same-key system rule always takes precedence over a user task rule while
both apply; the latter is journaled with a shadowed reason and winning version.
Exact value/text echo checks are redundant transport integrity checks against
`target_version`, not interpretation of the rule prose.

The composition DEV pilot injects `stencil.focus.retained_decode.RetainedDecoder`
through this same custom-generation dispatch. It retains actual KV within each
session and supports independently masked batch lanes; it does not change the
renderer or enable an actuator. `scripts/composition_pilot.py` owns sandboxed tools,
same-run hidden checks and optional residual capture. The default convenience
backend above still re-prefills; retained KV requires the explicit decoder adapter.
This local pilot does not change the scaffold-only snapshot status.
The [DEV pilot](../../results/quick-checks/composition-pilot/README.md) did not
qualify: batch4 was not byte-invariant, cost exceeded budget, and tool envelopes
failed. Its decoder adapter is not a batch-parity or shipping certificate.
