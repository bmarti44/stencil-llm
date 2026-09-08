# Independent native reasoning client review — Astra

2026-09-08. Native Astra, xhigh, explicitly selected by the user; author-disjoint.
Purpose: check the shared client against `CLIENT-BRIEF.md` and the accepted
automatic-pilot design, especially native request fidelity, argument/history
validation, token accounting, failure evidence and deadline propagation. The
threat model is trusted but fallible callers, transport and model outputs, not a
malicious same-user agent. The moving automatic runtime, fresh semantic data,
launcher and experiment readiness are outside this review. No server/model call,
generated-code execution, old-bank replay or implementation edit was performed.

## Round 1 — 95/100; client accepted with one low finding

One open low finding; zero open medium, high or critical findings. This accepts
the bounded client implementation at the hashes below. It is not acceptance of
the moving runtime or authorization to launch the pilot.

Stable implementation handoff: commit `821cb555`.

| Reviewed input | SHA-256 |
| --- | --- |
| `src/stencil/focus/native_reasoning_tool.py` | `ec6d4967f0e3887f50ef9c57f00a3b3733e6ec4af79f040b8740324cbea2f831` |
| `tests/test_native_reasoning_tool.py` | `950abea6a352b7d57b096efa9702420ffa5d2ca26a408a3ea6a662e7562593aa` |
| `CLIENT-BRIEF.md` | `dddc4b9234a4684bb2c1531d9aba3d3a2f5ac518d52211a3bff594fce1c181b7` |
| `DESIGN.md` | `6891d83ad2f6aac7d88bbec3d88a7c6337dd9337d011a1a95c9ccb3c3f9be1dc` |
| Reused `scripts/coding_competence_run.py` | `4e39d6f0fea4234643447bc1a31a2fb2caad7f1c5e35803537585c1d43812c94` |
| Reused `src/stencil/focus/slab.py` | `3f3a9f04ee9bae3395c3fdf5d3011e2b8cca4b930332a72dd2edafce7de04b59` |
| Local `tokenizer.json` | `aeb13307a71acd8fe81861d94ad54ab689df773318809eed3cbe794b4492dae4` |
| Local `generation_config.json` | `2325da0f15bb848e018c5ae071b7943332e9f871d6b60e2ed22ca97d4cb993d2` |

The last two inputs are under `models/qwen3-30b-a3b-hf/`; tokenizer loading does
not load model weights or materialize a semantic bank.

### Finding 1 — low, open: null tool ID matches the absent-pending-call sentinel

At `native_reasoning_tool.py:327`, `_validate_history` compares the tool result's
`tool_call_id` with `pending_id`, but does not require an actual pending call.
An orphan result with `tool_call_id: null` therefore passes when `pending_id` is
also `None`. I reproduced this through the public `payload` consumer with a
user message followed by:

```json
{"role":"tool","tool_call_id":null,"name":"replace_function","content":"orphan result"}
```

The payload retained the orphan unchanged; the existing fake-native exchange
then completed both HTTP stages and returned COMPLETE. This is an input-history
validation gap, not an observed live-server or normal-runtime failure. Ordinary
history built from the client's validated nonempty returned call IDs does not
exercise it. A malformed caller history should fail locally before spending a
render/generation attempt, rather than depend on downstream native validation.

Require a non-null pending call before accepting a tool result, with a focused
`payload` regression for this case. A broader history framework is unnecessary.

### Verified behavior

The frozen request specification stores canonical schema text and returns fresh
schema/tool dictionaries. It checks supported names and exact schemas, numeric
sampling settings and the cap/budget/context relationships. `record_focus` uses
the current nonempty unique visible-ID enum and returns generic validated
arguments; it does not incorrectly require `source`. Both result shapes reject
unexpected argument keys and invalid field types. Empty focus is structurally
possible and remains a semantic omission question under the registered review;
the client does not manufacture content or claim citation entailment.

Payload construction forces the named native tool, disables parallel and
streamed calls, requests raw token IDs and enables native thinking with the
specified allowance. The same immutable request bytes are sent to render and
generation. Render validation checks the actual schema, registered sampling
values and thinking budget, allowing omitted `min_p` only for equivalent zero.
It rejects a prompt containing a reasoning boundary and checks the complete
output reserve against context before sending the generation request.

Completion validation checks a single named tool call, matching prompt IDs,
integer usage totals, full output-ID counts and cap/finish status. Reasoning must
have one opening token at index zero, one closing token, nonempty content within
the allowance and an exact local decode matching the native reasoning field.
Final IDs must decode to the exact argument string, including whitespace; a
single actual terminal EOS is accounted for separately and interior EOS is
rejected. No `.strip()` reconciliation, output repair or extra generation is
introduced. The returned assistant history contains final tool data, excluding
the native reasoning field. Raw response evidence still preserves reasoning.

The transport and receipt machinery are reused unchanged. PENDING state is
persisted before calls; returned bytes, partial reads and failures survive in the
exchange. The client rechecks inherited deadline/receipt reserve before HTTP
stages and does not retry. A socket timeout is not an absolute lifecycle
watchdog: final runtime/launcher review must still establish the shared hard
reservation and cleanup. The client also cannot prove that a caller supplied
only public history or that the visible-ID enum matches the authentic prefix;
those are integration responsibilities.

### Independent validation and limits

- `.venv/bin/pytest -q tests/test_native_reasoning_tool.py`: **15 passed in
  0.19 seconds**.
- Ruff on the two reviewed implementation/test files: **PASS**.
- Additional ephemeral CPU checks reused the synthetic native exchange with the
  real local tokenizer. Empty reasoning, repeated opening and repeated closing
  boundaries failed with `reasoning_boundaries`; an oversized rendered prompt
  failed with `capacity` after one render and zero generations; the wrong
  rendered thinking allowance failed with `render_settings` before generation.
  An expired receipt reserve persisted ERROR with `deadline` and zero HTTP calls.
  The orphan-null-history case above was accepted and is finding 1.

The targeted suite also exercises both schemas, visible-ID rejection, exact
history preservation, the 1,024-token reasoning boundary and 1,025-token
rejection, whitespace, wrong schema/name/prompt IDs/usage, output overflow,
native default handling and incomplete raw HTTP evidence. These are consumer
checks using fake transport, not fresh evidence that the real server executes
the new selector schema or 1,024 allowance. Reaching the allowance does not prove
the cause of termination; the receipt correctly records that limitation.

Final runtime review must verify callers use this payload path, keep selector
calls cold, preserve actual worker tool continuity, enforce the public/private
boundary and stop/account for failures. None of the client validation establishes
reminder usefulness, semantic competence, automatic parity or the larger goal.
