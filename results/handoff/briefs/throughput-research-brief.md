# Deep web research for gpt-6-astra: a legitimate 3-10x throughput path for the larger test on the GB10 (2026-09-06)

Problem: the composition DEV pilot (results/quick-checks/composition-pilot/README.md) measured HF eager/SDPA MoE
decode at 10.8 tok/s (Qwen3-30B-A3B bf16, 5-11k context, greedy, retained KV, one sequence) -> the registered larger
test projects to 20.8 GPU-h sequential against Brian's 12 GPU-h budget; padded batch-4 through our adapter was NOT
byte-invariant and slower. KEY FACT: the SHIPPED mechanism (arm R = register + every-request rendering) uses NO custom
attention mask and NO router bias — it is plain greedy generation over a rendered prompt. Arms N and T likewise. So
the larger test does not need the custom HF path for the trunk; it needs (a) a fast serving backend for plain
greedy generation with prefix caching, (b) an equivalence check that the backend reproduces the HF package path's
greedy outputs on a few rounds (or a disclosed tolerance), and (c) the controller running outside the backend.
Platform: NVIDIA GB10 (DGX Spark class), aarch64, driver 580.159.03, CUDA 13.0 toolkit, torch 2.13.0+cu130, compute
capability (12,1); no vllm/sglang/llama.cpp currently installed; ~120 GB unified memory; model weights local at
models/qwen3-30b-a3b-hf (57 GB bf16). Constraints: no benchmark data; do not install anything in this pass; CPU only;
web search allowed and expected.
Research and report (results/throughput-research-astra.md):
1. vLLM on GB10/sm_121/aarch64/CUDA 13 as of today: official wheels or container (NGC / vllm docker for arm64 +
   Blackwell), known issues, MoE kernel support for Qwen3-30B-A3B, expected decode tok/s single-stream and at batch
   4-8 with prefix caching, greedy determinism guarantees (batch invariance flags), quantisation options that keep
   greedy outputs close (bf16 preferred; FP8 changes outputs — say so).
2. SGLang same questions. 3. llama.cpp (server) with a bf16/Q8_0 GGUF of Qwen3-30B-A3B on GB10: build flags for
   sm_121, expected tok/s, prompt caching, greedy determinism; note that Q8_0 changes outputs vs bf16.
4. TensorRT-LLM / NIM for GB10 if realistic within a day.
5. Within-HF options: static KV cache + torch.compile, flash-attention/SDPA kernels for sm_121, fused MoE kernels
   (grouped_mm already used), continuous batching via generate() — what is realistic without a fork.
6. For each: install effort (hours), risk, throughput multiplier vs 10.8 tok/s, output-equivalence expectation vs the
   HF bf16 path, and whether prefix caching handles our every-request rendered block (it changes each request ->
   only the earlier history is cacheable; quantify).
7. RECOMMENDATION: the single path to try first, a fallback, and the exact equivalence protocol (N rounds, greedy,
   compare token ids; report divergence rate; decision rule for "same mechanism").
Cite real URLs you opened; mark unverified items. No repo edits except the report; never read anything under
data/bench; do not launch any model or install packages.
