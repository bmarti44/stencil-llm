# Stencil custom generation scaffold

Days 1–2 CPU scaffold, not a complete downloadable model. No weights are copied.
The controller currently imports `stencil.focus` from this checkout/installed
Stencil package. Before shipping one HF snapshot, bundle these modules alongside
the trunk, tokenizer/config, approved classifier assets and experimental tensor;
fill every manifest hash and validate local-only loading. That packaging and
model-backed validation have not been performed by this CPU build.

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
Each accepted generation request consumes one of three tombstone requests even
if decoding raises. Rendering alone is pure and does not advance that clock.

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
