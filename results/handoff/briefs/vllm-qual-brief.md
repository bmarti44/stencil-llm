# vLLM qualification for gpt-6-astra (GPU): does a fast backend reproduce the HF path and how fast is it? (2026-09-06)

Your report results/throughput-research-astra.md recommends vLLM bf16 (official cu130 track) with
VLLM_BATCH_INVARIANT=1, automatic prefix caching, plain token-id prompts, controller outside. The image
vllm/vllm-openai:cu130-nightly has been pulled locally (docker 29, CDI GPU nvidia.com/gpu=0; ~120 GB unified memory;
model at /home/bmarti44/stencil-llm/models/qwen3-30b-a3b-hf, bf16, mount read-only). Run the qualification protocol
from your report, exactly, as a registered quick check (results/quick-checks/vllm-qual/):
1. Pre-write the reading in README: QUALIFIED = the 64 frozen DEV-00 sequential prompts of the composition pilot
   (results/quick-checks/composition-pilot/records.jsonl: prompt token ids + greedy output ids, cap 512) reproduce
   token-for-token through vLLM greedy (temperature 0, same cap, same EOS handling) with divergence count 0/64 — or,
   if not zero, first-divergence positions with a disclosed analysis and a STOP unless <= 1/64 diverge after the
   first 64 output tokens (formatting near-tie); AND single-stream decode >= 20 tok/s at 5-11k context (>= 1.84x the
   HF eager 10.827) with prefix-cache hit rate reported; ELSE NOT QUALIFIED with the failing item.
2. Start the server in docker (write results/quick-checks/vllm-qual/RUNNING.flag first; the GPU must be idle — wait
   for any other RUNNING.flag to clear), with the arguments proposed in your report (record the resolved image
   digest, all flags, env, and the server log). If the server fails to start (e.g. the GB10 memory-profiling issue
   you cited), try at most two documented remedies (gpu_memory_utilization / max-model-len), record each, and stop.
3. Replay the 64 prompts as raw token ids via the completions API (prompt as token ids; logprobs off; max_tokens
   512; stop on EOS id 151645 / END 151643 as in the HF records); compare ids; then measure throughput: single-stream
   decode tok/s per call, and aggregate at concurrency 4 and 8 (same prompts), plus prefill tok/s and cache hit rate.
4. Stop and remove YOUR container at the end (docker stop/rm of the container you started is allowed; never touch
   any other process or container). Remove the RUNNING.flag. Cap 45 GPU-minutes.
5. Report the projection for R/N x64 + O/T x16 at the measured single-stream and concurrency-4 rates against
   12 GPU-h (no unmeasured credit), and the exact equivalence protocol for the larger run (which arms may run on
   vLLM; how the HF package path is re-validated on a subset; hidden-state recovery by teacher-forced HF prefill).
Commit README/records/summary (git add -f) + item in results/quick-checks/README.md (5 lines) + WORKLOG (<= 6 lines)
with explicit pathspecs; no push; never read anything under data/bench; DEV-00 prompts only (no evaluation episodes).

AMENDMENT (orchestrator, 2026-09-06, after the grouped_mm gate: 60/64 exact, 4 round-0 divergences, all later
rounds identical): cross-backend byte parity is NOT a validity requirement for the larger test — the mechanism does
not depend on a kernel; validity requires ONE frozen backend used identically across all arms with run-to-run
determinism. Therefore: (a) report the cross-backend divergence count/positions vs the frozen HF records as a
DISCLOSED number, not a gate; (b) QUALIFIED = run-to-run determinism (replay the 64 prompts TWICE through vLLM with
VLLM_BATCH_INVARIANT=1, once single-stream and once at concurrency 4; all three passes must be token-identical to
each other) AND single-stream decode >= 20 tok/s (or concurrency-4 aggregate that brings the R/N x64 + O/T x16
projection <= 12 GPU-h with measured numbers only); (c) the ship-package equivalence claim is then "vLLM-served R
diverges from the HF package path on k/64 DEV prompts at greedy near-ties; both are the same mechanism" — state k.
Fable will review this ruling; if it is wrong the run is still informative.
