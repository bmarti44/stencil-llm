# Check 47 for gpt-6-astra (GPU): is Qwen 3.8 27B (dense) the better trunk for the larger test and the ship? (2026-09-06)

Brian's question: should we be using Qwen 3.8 27B instead of Qwen3-30B-A3B? The MoE was chosen for the expert-routing
experiments, which are now CLOSED (40k/40l); the mechanism (register + every-request renderer) is trunk-agnostic.
Local weights: /home/bmarti44/models/qwen3.8-27b-fp8 (29 GB safetensors, FP8; architecture
Qwen3_5ForConditionalGeneration / text model qwen3_5_text, 64 layers, hidden 5120, MTP layer 1, eos 248044) and
GGUF Q4/Q6/Q8 under /home/bmarti44/models/qwen3.8-27b; NO bf16 HF checkpoint locally (disk: 163 GB free at 96%).
Screen (cap 40 GPU-minutes; RUNNING.flag under results/quick-checks/check47/; stop/rm only your own container):
1. Feasibility: does the qualified vLLM image (vllm/vllm-openai:cu130-nightly, the digest in results/quick-checks/
   vllm-qual/) support the qwen3_5 architecture with the FP8 checkpoint on GB10 (check the registry inside the
   image WITHOUT the GPU first: `docker run --rm --entrypoint python <image> -c ...`; then start the server). If
   it does not load, try the text-only config path; if still not, report NOT LOADABLE with the error and stop.
2. The same DEV-00 and DEV-01 episodes as pilot 4 (read results/quick-checks/composition-pilot-4/README.md for
   the current harness and its outcomes on the MoE), arm R only (register + renderer; gold events in DEV), same
   cap/EOS semantics (map the new eos id), concurrency 4 where possible: report executed-call rate, caps, final
   success, per-kind violations and round-0 indent compliance, decode tok/s per stream and aggregate, seconds per
   call, and the projected cost of the larger test (R/N x64 + O/T x16) at the measured rates against 12 GPU-h.
3. Also run the 32 check-40k JavaScript tasks text-only (hidden tests) for a direct competence comparison with the
   MoE's 16/32 (same harness; disclosed second look; no selection).
Pre-written reading: SWITCH-CANDIDATE if (executed rate >= the MoE's on the same episodes AND final success or
violation counts better AND the projection fits <= 12 GPU-h at bf16-equivalent cost — note FP8 is faster than the
bf16 ship checkpoint would be; state the bf16 estimate) -> recommend downloading the bf16 checkpoint (~54 GB;
needs Brian's disk approval) and re-qualifying the backend + renderer golden on it before the larger test; else
STAY on the MoE with the numbers. Data lineage: DEV episodes + the 40k task bank only; no benchmark data.
Outputs under results/quick-checks/check47/ (README with readings, records <= 10 MB, summary); item 47 in
results/quick-checks/README.md; WORKLOG (<= 6 lines). Commit with explicit pathspecs; no push; never signal any
process other than your container; never read anything under data/bench.
