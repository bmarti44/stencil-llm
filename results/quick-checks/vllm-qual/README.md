# vLLM qualification — registered before GPU execution

Fit/train-on: none. Test-on: the 64 frozen sequential authored DEV-00 prompts only,
anchored to original HF histories. No evaluation episodes or data/bench reads.

The 2026-09-06 user amendment supersedes cross-backend parity as a gate.
QUALIFIED requires all 64 complete outputs (including EOS/END and length) identical
across three passes: B1 first, B1 repeat, B4 repeat, VLLM_BATCH_INVARIANT=1;
AND B1 decode >=20 tok/s on 5–11k prompts OR measured B4 aggregate yielding
R/N x64 + O/T x16 <=12 GPU-h. Otherwise NOT QUALIFIED, naming failed/unmeasured items.
HF mismatch count and zero-based first positions are disclosure, not a gate.
Near-tie interpretation requires evidence; mismatches alone do not establish logit gaps.
B8 is an additional measured diagnostic, not authorized for larger use absent invariance.

Greedy raw integer completions: temperature0, top_p1, top_k-1, min_p0,
repetition_penalty1, frequency/presence_penalty0, max_tokens512 including stop token,
stop_token_ids [151645,151643], ignore_eos false, logprobs off; no chat/parser/template.
HF records store body separately from EOS: append the recorded EOS for exact comparison.
Preserve actual server token IDs, never retokenize text. Freeze the original record order.
Measure per-call TTFT/decode duration, server prefill/decode counters and cache hits;
aggregate output tokens / actual pass wall time at B4 and B8 (client concurrency disclosed).
No cache-rate estimate substituted for counters. B4 server initially max-num-seqs4;
B8 client concurrency on that server is queueing diagnostic, not eight active sequences.

Initial report flags: bf16 weights, auto (bf16) KV, TP1, max-model-len32768,
max-num-seqs4, max-num-batched-tokens2048, gpu-memory-utilization0.70,
automatic prefix caching, generation-config vllm, invariant env1. Read-only model mount.
At most two startup remedies: reduce utilization to0.60; then max-model-len16384
(still exceeds frozen max11050+512), retaining0.60. No kernel patch or backend change.
If a non-memory incompatibility makes those remedies irrelevant, stop without futile retries.
45 GPU-minutes includes startup, all calls and cleanup; cooperative runner stops its own
container only, reserving cleanup time. No other process/container touched; no push.

Projection: charge prior pilot5385.346s + Day5b1362.257s + current qualification,
measured server reload, and25% reserve on weighted per-arm measured future call costs.
Short16-round frozen replay is a diagnostic; 32-round/controller/hidden-recovery costs
remain unmeasured and receive no acceleration credit or full-run eligibility claim.

## Startup correction, before remedy execution
Initial attempt failed before weights load: invariant mode rejects backend=None and
explicitly requests FLASH_ATTN/TRITON_ATTN (or MLA variants). The original report's
automatic selection is incompatible with this pinned image. Registration's memory-only
remedy list is corrected based on that startup evidence: remedy1 explicitly selects
TRITON_ATTN, retaining all other settings; remedy2 only if needed reduces utilization
to0.60 and max length16384. This is a disclosed pre-generation configuration correction,
not an outcome-selected kernel. At most three total starts, with original28.364s charged.
