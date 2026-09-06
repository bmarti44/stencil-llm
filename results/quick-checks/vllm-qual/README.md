# vLLM qualification — QUALIFIED via concurrency 4

**2026-09-06, gpt-6-astra.** Passes the user's amended backend gate: all64 complete
outputs match across B1 first, B1 warm repeat and concurrency4. **HF differs5/64**
(R1/16, N2/16, T1/16, O1/16). Single-stream decode at5–11k is18.709/18.733tok/s,
only1.728/1.730x the HF10.827 baseline, so the20tok/s branch fails. **Concurrency4
measures39.912tok/s aggregate and projects7.845GPU-h <=12**, including charged
qualification and a measured reload. Single-stream projects12.558h >12.
This is backend qualification on frozen16-round DEV00; it does **not** clear the
larger test's long-episode, controller, hidden-recovery or other eligibility gates.

| Pass | Completed | Wall seconds | Output tokens | Aggregate tok/s | 5–11k decode tok/s per stream | Prefix-token hit rate |
|---|---:|---:|---:|---:|---:|---:|
|B1 first|64/64|827.615|17,031|20.578|18.709|95.5277%|
|B1 warm repeat|64/64|815.533|17,031|20.883|18.733|99.8202%|
|Concurrency4 warm|64/64|426.710|17,031|39.912|9.877|99.8202%|
|Concurrency8, partial short prompts only|9/64|51.147|2,222|43.443 (partial)|unmeasured|99.0393%|

The5–11k subset has27 cases per full pass; all64 prompt lengths span511–11050.
B1 decode is a token-weighted average, not a per-call minimum. Full per-call timing,
IDs, streaming chunks, stop reasons and usage are in [records.jsonl](records.jsonl).
The full passes each retain10 cap hits; no truncation case was dropped.
Fresh prefill measured13,753KV tokens/16.712request-s =822.920tok/s in B1 first;
553/6.221 =88.891 in B1 warm;553/13.754 =40.205 in concurrency4. Warm prefill rates
have tiny residual work and fixed overhead; overlapping request durations at C4 are
not kernel wall time. Raw before/after `.prom` counters match all completed calls.

**Concurrency8 is INCOMPLETE and gets no budget or usage credit.** The fixed report
configuration has max-num-seqs4: sampled maxima are4 running/4 queued, not8 active
sequences. Nine calls finished and match B1;55 were never submitted after the
cooperative stop-new-work boundary. This is neither a full64-case C8 measurement nor
8-active-sequence qualification. The runner reserved cleanup time and finished at
42.592GPU-minutes, below45; it did not extend the cap to complete this diagnostic.

**Startup:** preregistration22cbbfa9; correctionba6f22e4. Initial backend=None failed
before weight loading (28.364s). One documented remedy, explicit TRITON_ATTN, loaded
successfully; no second remedy or utilization/context reduction was needed. Exact
ARM64 image digest `sha256:3dbe092ec5b2cef63b6104d33fa75d6ce53a7870962529ada69f78bbbc38e776`,
local image ID `sha256:ffa30d66ff5c9346c6389507cc529827fc9934a6d2ee37855934f94fe1061cdc`,
vLLM0.19.2rc1.dev134+gfe9c3d6c5. BF16 weights, auto KV inherits bf16 model dtype,
TRITON_ATTN and TRITON unquantized MoE, prefix blocks16, CUDA graphs enabled.
Weights load333.734s/56.88GiB; ready-from-launch399.460s; KV pool24.38GiB/266,240tokens.
All launch args, environment, read-only mount and resolved configuration are retained
in [registration.json](registration.json), [initial-attempts.json](initial-attempts.json),
[attempts.json](attempts.json) and both timestamped server logs. No server fallback,
model substitution, model modification or package/environment installation occurred.

**Cost:** prior pilot5385.346s + Day5b1362.257s + this check2555.495s + measured
reload399.460s =9702.559s fixed. Future workload uses64(R+N)+16(O+T),25% reserve.
B1 per-arm episode seconds R/N/O/T =165.317/149.987/160.569/353.492; projected12.558h.
C4 weighted output count588,384 divided by39.9123328tok/s, plus measured callback
overhead, projects7.845h. No rate is inferred by multiplying B1 by four. These are
short frozen-workload projections: the nested arm mix,32-round histories, changed
controller feedback and HF hidden-state recovery remain unmeasured. In particular,
7.845h does not certify that the fully instrumented larger experiment fits12h.

**Cleanup and validation:** both owned containers stopped/removed; RUNNING.flag and
READY removed.201 API calls completed;55 explicit unsubmitted deadline rows make256
scheduled records.171 normal stops +30 cap hits. CPU audit rechecks source/frozen
hashes, returned prompt IDs, every output token/EOS/cap, streaming counts/timings,
raw server counters, comparisons, projections and container cleanup. The actual
streaming consumer also passed synthetic EOS and cap512 smoke cases. See
[audit.json](audit.json), [summary.json](summary.json), [lifecycle.json](lifecycle.json)
and [initial-lifecycle.json](initial-lifecycle.json). No data/bench or evaluation
content, fitting, other process/container signals, or push. Only owned Docker
stop/rm performed. The exact conditional larger-run protocol follows below.

# Registration — written before GPU execution

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

## Larger-run equivalence protocol (conditional, not a launch authorization)

1. Freeze one image digest, explicit attention/MoE backends, bf16 checkpoint and KV,
   tokenizer/config hashes, invariant env, scheduler/cache settings, cap512 and both
   stop IDs for **all R/N/O/T arms**. Never mix HF controls with vLLM treatment or
   choose backend by arm/outcome. R retains the shipped register/renderer/controller
   semantics; O retains its registered oracle role; N/T retain their definitions.
   The controller stays outside serving, using exact rendered IDs and unchanged
   checker/executor feedback between rounds. No custom masks, router bias, grammar,
   prompt rearrangement or template substitution. B8 is unavailable unless its exact
   server configuration and output invariance are separately qualified.
2. Before evaluation, freeze a DEV-only subset by shape: DEV00/01/06/07, checkpoints
   0/5/10/15 for short histories and0/5/10/15/20/26/31 for long, all four arms.
   Obtain input IDs through the actual `models/stencil-package` custom-generation
   entry and original RetainedDecoder, checking rendered UTF-8 bytes and IDs before
   generation. Validate retained versus cold HF on the first checkpoint of each
   history/arm and after a registered render removal/reinstatement. Compare each
   vLLM output with HF on the identical anchored prompt, including EOS/END/cap,
   disclose count/positions by arm and context; HF differences are not exclusions.
   Diagnose claimed near ties by teacher-forcing the shared prefix and reporting
   both token logits/gaps; do not infer near ties solely from a small mismatch count.
3. For this subset require vLLM B1 cold/warm, B4 in forward and reverse frozen order,
   and B1 after restart/reprime to match exactly. Record actual scheduled concurrency
   and cached tokens. No skipped failures, padding duplicates or silent cache reset.
   Then run the four full DEV episodes through each backend with its own prior
   answers fed forward, preserving every action/state/stop/outcome; cross-backend
   trajectories may differ, but within-backend repeats must match. This qualification
   checks only anchored DEV00, not those unrun long/controller/restart conditions.
4. Recover hidden states in a **separate HF teacher-forced prefill**, after unloading
   vLLM: feed each exact prompt concatenated with the actual vLLM output IDs. Save
   one-based post-block residuals at layers8/16/24/32/40: last prompt-token vector,
   and mean over all body-token positions excluding the terminal EOS/END. Forward
   the final body token even on cap hits; never substitute the previous position
   that predicted it. Accumulate bf16 vectors in float32 and cast to float16 to match
   the pilot artifact convention; record counts, positions, dtype and hashes.
   These are HF activations conditioned on vLLM tokens, not vLLM internal states.
   Compare against original HF prompt/body artifacts on exact-output subset cases,
   including a cap hit, and disclose retained/cold numeric differences. Validate any
   chunked/cached recovery against full teacher forcing before using it.
5. Measure that recovery, reloads, callbacks, full16/32-round DEV trajectories and
   the actual64/64/16/16 arm schedule before approving <=12h. Add all prior pilot,
   qualification and validation spend, plus measured reloads and25% future reserve.
   Independent episodes can occupy lanes; dependent rounds cannot be sent ahead.
   This check cannot resolve the composition pilot's other eligibility failures.

The requested ship wording is conditional on completed evidence: "vLLM-served outputs
diverge from the HF package path on k/64 DEV prompts; both implement the same rendered-
prompt mechanism." The64 denominator includes all four arms; state R's own k_R/16
separately. Add "at greedy near-ties" only if logit-gap measurements support it.

## Measurement definitions

Per-call decode tok/s excludes TTFT: tokens after the first streamed token chunk,
divided by time between first and last token chunks. The raw chunks and timestamps
allow rechecking coalescing; all output tokens (including EOS) count toward cap512.
The5–11k gate uses token-weighted decode rate on actual5000–11050-token prompts,
separately in both B1 passes. It is not a claim that every individual call exceeds20.
Pass aggregate includes prefill, streaming, HTTP and client scheduling wall time.
Prefix hit rate is the delta of server cached-token queries divided by all queried
tokens. Fresh prefill rate is actual computed KV tokens divided by summed request
prefill-phase seconds; at concurrency these durations overlap, so this is not a
GPU kernel-throughput measurement. Raw Prometheus snapshots are retained.

B1 cost uses the larger per-arm sum of observed call times across both repeats.
B4 cost uses the measured pass output-token/wall rate and actual per-arm output counts,
weighted64(R+N)+16(O+T). Both add the original measured per-episode callback overhead
(R/N/T/O0.631/0.511/0.501/0.486s), all prior pilot spend, this check's full GPU-held time,
one measured cold-server reload, and25% reserve on future work. B4 is a projection
at the observed four-arm token mix, not a measurement of the full nested arm schedule.
No hidden-recovery or long-episode speedup is credited; their costs remain unknown.

## HF comparison: completed first pass

**5/64 diverge (7.8125%);59/64 exact.** By arm: R1/16, N2/16, T1/16, O1/16.
First differing output indices are zero-based and include the terminal token:

| Frozen index | Arm / round | First difference | HF / vLLM output length |
|---:|---|---:|---:|
|0|R /0|191|198 /266|
|1|N /0|90|203 /282|
|2|T /0|0|193 /277|
|3|O /0|191|198 /266|
|45|N /11|22|205 /205|

R/O add a delivery artifact object; N0 changes validation code and verbose report
content; T0 changes formatting, documentation and report/delivery structure; N11
changes indentation. These are not uniformly formatting-only differences. The
[first-difference IDs and text diffs](hf-divergences.jsonl) disclose every mismatch.
All five cases end normally, not by an EOS/cap mismatch. No logits were requested,
so greedy near-tie gaps are **unmeasured**. The defensible claim is: vLLM differs from
the HF package path on5/64 DEV prompts (R alone1/16), using the same rendered-prompt
mechanism with a different numerical realization. This is not byte parity or a
claim that downstream execution remains unchanged. No evaluation data were used.

The amended ruling supports a within-backend mechanism comparison: using one frozen
backend identically for treatment and controls avoids confounding arm with backend.
It does not establish that an effect size, tool trajectory, or probe trained on HF
transfers to vLLM. A larger result must identify the serving backend as part of the
experimental setup; generalization to HF remains a separate question. Fable's review
of the ruling is pending, and this quick check supplies evidence for that review.

Validation note: server logs and Prometheus snapshots retain trailing whitespace as captured; whitespace checks apply to authored code/docs/JSON, excluding those raw `.log`/`.prom` artifacts.
