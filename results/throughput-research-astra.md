# GB10 throughput research: preserve the rendered-prompt mechanism

**Decision report for Brian — 2026-09-06.** CPU-only research; no installation, model execution, training, or benchmark/evaluation-data access. Fit-on: none. Local evidence read: the composition-pilot README, model configuration, and governing/resume documents. This report is the only repository edit; the user's explicit scope overrides ledger/additional research-artifact instructions. Root PLAN.md and plan/PROTOCOL.md are absent; their archived counterparts were consulted. Proposed experiments below are recommendations, not experiments performed or an amendment to the registered test.

## Recommendation and strength of evidence

**Try official vLLM CUDA-13.0 serving first, using the exact local bf16 checkpoint, bf16 KV, plain token-ID prompts, automatic prefix caching, and `VLLM_BATCH_INVARIANT=1`. Keep the controller, register, renderer, checker, and executor outside the server. Start at concurrency 1, qualify concurrency 4, and use 8 only if measured throughput improves. Fallback: SGLang bf16 in its official Spark CUDA-13 container.** Neither requires the custom attention-mask/router-bias machinery because R, N, and T use ordinary greedy generation over rendered prompts.

There is a legitimate **approximately 3× candidate**, and a credible **3–10× aggregate-throughput exploration**, but **no verified 3–10× result for this exact bf16 checkpoint at 5–11k context with HF-identical outputs**. Closely related, first-person GB10 reports put bf16 serving near 30 tok/s; upstream llama.cpp measurements reach 47 tok/s single-stream and 97 aggregate at concurrency 8, but use a Q8 Coder checkpoint. Those qualifications materially affect the decision. Do not substitute FP8/Q8/NVFP4 performance for bf16 performance. Evidence details and opened URLs follow.

The original [pilot](quick-checks/composition-pilot/README.md) remains INELIGIBLE/INCOMPLETE for reasons beyond speed: truncation, all rejected envelopes, and incomplete long-episode validation. Backend acceleration resolves only a cost obstacle; it does not make that recipe eligible.

## Cost arithmetic: the actual speedup required

Pilot sequential wall time was 1,601.766 s, of which decode occupied 1,539.544 s (**96.12%**) and prefill 58.295 s (**3.64%**). Removing all remaining prefill would improve this episode by only **1.038×**. The baseline already retained KV, so prefix caching cannot be credited as a new full-prefill saving.

Using the pilot's 20.794 h projection, keep spent time and its reload allowance fixed:

```text
F = 5385.346/3600 + 322.758/3600 = 1.585584 h
W = 20.794 - F = 19.208416 h       # future work including existing 25% reserve
d = 1539.544/1601.766 = 0.961154
H(s) = F + W * [(1-d) + d/s]
```

| Decode speedup s | Approximate total GPU-hours H(s) |
|---:|---:|
| 2× | 11.56 |
| 3× | 8.49 |
| 4× | 6.95 |
| 5× | 6.02 |
| 10× | 4.18 |

**Derived, not a new measured projection:** about **1.91× decode speedup** clears 12 h under these assumptions; 2× leaves little qualification headroom. New backend loads, compilation/warmup, equivalence checks, pilot work, and any extra instrumentation must be added. The short pilot's decode fraction is only a proxy for the weighted larger workload. Changed outputs can change lengths and costs. Ultimately recompute using completed per-arm/per-length episodes and the actual scheduler, including idle lanes and controller waits; never divide the whole 20.794 h by a headline tok/s multiplier.

## Comparison for this checkpoint and workload

Setup hours below are **engineering estimates**, not measured installation times. They cover a working server/adapter and initial checks, excluding a full new DEV qualification. Rates are output decode tok/s; B4/B8 means **aggregate**, not each user's rate. All comparisons divide by the user's rounded 10.8 tok/s baseline.

| Path | Setup effort; risk | B1; B4/B8 expectation at 5–11k | Multiplier expectation | HF bf16 output expectation |
|---|---|---|---|---|
| vLLM, exact bf16 | 2–4 h; medium | **Planning hypothesis:** 20–35 B1; B4/B8 unknown. Target 40–100 aggregate for a useful batching trial; unverified | B1 1.85–3.24×; aggregate target 3.70–9.26× is not evidence | Same weights; high numerical similarity plausible, exact IDs unproven; batch-invariance beta must be tested |
| SGLang, exact bf16 | 2–6 h; medium | **Planning hypothesis:** 20–35 B1; B4/B8 unknown; same 40–100 aggregate trial target, not a forecast | Same numerical hypotheses; deterministic backend may cost speed | Same weights; no HF equality guarantee; caching/determinism conflict with FlashInfer |
| llama.cpp, BF16 GGUF | 1–3 h; medium | Unknown at all three concurrencies; **20–35 B1 is only a bandwidth-based planning hypothesis** | Hypothesized B1 1.85–3.24×; batch unknown | Weight precision retained; execution, activation/KV precision and tokenizer mapping require checks |
| llama.cpp, Q8_0 GGUF | 1–3 h; medium implementation risk, greater equivalence risk | **Measured sibling proxy at 8k:** 47.20; 71.69/97.39. Exact-model 200–512-token decode remains unverified | Proxy 4.37×; 6.64×/9.02× | Quantization changes weights and can change greedy IDs; not an exact-bf16 replacement |
| TensorRT-LLM, exact bf16 | 2–6 h, possibly >1 day; medium/high | Exact GB10 configuration unknown B1/B4/B8 | Unknown; no throughput credit before measurement | Model supported generally; exact kernels and HF equality unverified |
| NIM, exact checkpoint | No verified within-day route; high fit risk | Unknown | Unknown | No verified Spark profile for this exact model; Qwen3-32B is different |
| HF static cache + compile | 1–3 h; medium | Planning hypothesis 11–22 B1; batch unknown | Roughly 1–2× hypothesis | Least architectural displacement, but changed reductions still may change IDs |
| HF native continuous batching API | 2–6 h; medium/high integration risk | Unknown B1/B4/B8; trial target 11–32 aggregate | Roughly 1–3× aggregate hypothesis | New attention/scheduling path; no batch/HF equivalence guarantee |

Why 20–35 bf16 tok/s is a reasonable experiment rather than a promise: a crude 3B-active ×2-byte weight-stream model at Spark's approximately 273 GB/s gives 45.5 tok/s before attention, dispatch, and other traffic. It is **not a rigorous ceiling**: embedding/output weights, expert reuse, cache residency, and routing distribution alter actual bytes/token. The first-person bf16 measurements below provide a stronger directional anchor. No measured batching curve supports multiplying B1 by four or eight.

## 1. vLLM

**Official availability is established; exact artifact qualification remains to do.** The [vLLM GPU installation documentation](https://docs.vllm.ai/en/stable/getting_started/installation/gpu/) advertises aarch64 wheels, including CUDA 13.0 variants, plus Docker. Its wheel recipe uses `manylinux_2_28_aarch64`; binaries are tied to their bundled PyTorch/CUDA versions. Do not install a wheel over the user's torch 2.13.0 environment and assume ABI compatibility. A separate container avoids that dependency conflict. Wheel existence is documented; this research did not download a wheel or inspect a container manifest/digest.

The dated [vLLM/Inferact Spark article, June 1, 2026](https://vllm.ai/blog/2026-06-01-vllm-dgx-spark) explicitly identifies **`vllm/vllm-openai:cu130-nightly`** as its official Spark image track and requires sm_121-specific validation and a reproducible pin. That example serves Nemotron NVFP4, not our Qwen bf16, so it establishes platform deployment rather than our performance. Use its CUDA-13.0 track with a verified ARM64 manifest, then record the selected digest. Keep CUDA graphs enabled initially; disabling them globally discards a potential decode benefit.

NGC is another official option: [25.11 notes](https://docs.nvidia.com/deeplearning/frameworks/vllm-release-notes/rel-25-11.html) specify CUDA 13.0.2/vLLM 0.11.0, but that is old and does not establish today's determinism features. [26.08 notes, updated August 31](https://docs.nvidia.com/deeplearning/frameworks/vllm-release-notes/rel-26-08.html) use CUDA **13.4.1**, not 13.0. Do not equate “newest container” with “qualified on this host.” NVIDIA's [CUDA 13.0 Update 2 release notes](https://docs.nvidia.com/cuda/archive/13.0.2/cuda-toolkit-release-notes/index.html) list driver 580.95.05 and a CUDA-13.x minor-compatibility floor of R580. The supplied 580.159.03 is suitable for a 13.0 route; later-runtime/JIT compatibility must be checked rather than declared impossible or guaranteed. Host toolkit version does not replace container userspace.

**MoE:** upstream [Qwen3 MoE implementation](https://raw.githubusercontent.com/vllm-project/vllm/main/vllm/model_executor/models/qwen3_moe.py) uses vLLM's FusedMoE machinery. A working bf16 route is cuBLAS linear operations plus Triton MoE and a compatible attention backend. Generic B200/GB200 “Blackwell support” does not establish GB10 support; NVIDIA [lists GB10 at compute capability 12.1](https://developer.nvidia.com/cuda/gpus). Inspect the selected kernels in startup logs. Do not import an sm_100-only DeepGEMM/FlashAttention recipe or assume the sm_100 architecture list in an ARM build example includes sm_121.

**Performance evidence:** experimenter flash3's [February 9–10 Spark measurements](https://forums.developer.nvidia.com/t/fp4-on-dgx-spark-why-it-doesnt-scale-like-youd-expect/360142) report Qwen3-Coder-30B-A3B bf16 around **30.6 tok/s** on an updated vLLM path, versus an earlier 28.8 result constrained to eager/V0. SGLang bf16 is 31.1–31.7. The author's [February 14 follow-up](https://forums.developer.nvidia.com/t/fp4-on-dgx-spark-why-it-doesnt-scale-like-youd-expect/360142?page=2) discloses zero-context testing. These are **first-person community measurements, not NVIDIA certification**, use another checkpoint and software stack, and lack the required 5–11k/batch/cache/invariance matrix. They support a roughly 3× trial, not a measured 3× claim here. Exact bf16 B4/B8 evidence was not found.

**Determinism:** [vLLM batch-invariance documentation](https://docs.vllm.ai/en/latest/features/batch_invariance/) calls the feature beta, enables it with `VLLM_BATCH_INVARIANT=1`, and lists Qwen3-30B-A3B among tested models. Its hardware floor includes NVIDIA CC≥8.0, but the page is not an exact GB10 release certification. A historical [B200 compile-related invariance failure, issue 32992](https://github.com/vllm-project/vllm/issues/32992), illustrates why a flag is insufficient; that report is sm_100/Qwen2.5, not evidence our sm_121 model fails today. [Reproducibility guidance](https://docs.vllm.ai/en/latest/usage/reproducibility/) limits reproducibility to the same hardware/version and distinguishes scheduling controls from numeric invariance. No upstream guarantee says vLLM bf16 greedy equals HF bf16 greedy.

**Known GB10 operational issue:** [issue 46307, June 21](https://github.com/vllm-project/vllm/issues/46307) reports startup profiling exceeding `gpu_memory_utilization` on a bf16 Gemma MoE, GB10, and the same 580.159.03 driver. It is a different model/branch, so not proof of Qwen failure. It does show that 0.7 is not a hard process memory cap. Keep startup token/sequence limits modest and measure system headroom; NGC release notes independently warn about unified-memory OOM. Do not remedy this by silently shortening allowed requests.

**Quantization:** keep weights and KV bf16 initially. FP8 weights, FP8 KV, INT8, AWQ and NVFP4 all change arithmetic; none guarantees greedy identity, and format support does not establish a fast sm_121 kernel. FP8 is a possible later disclosed variant, not a precision-preserving optimization. No calibration/fitting on evaluation inputs or their outputs is permitted.

## 2. SGLang

NVIDIA's [Spark SGLang instructions](https://build.nvidia.com/spark/sglang/instructions) provide **`lmsysorg/sglang:latest-cu130`**, recommend `--attention-backend flashinfer`, describe automatic prefix reuse and `--enable-cache-report`, and discuss memory fractions around 0.7–0.75. This is the preferred isolated installation route; native aarch64 wheel/kernel compatibility for the user's existing torch stack was not verified. Pin the container digest and validate exact bf16 MoE loading. Historical hand-patched Spark images are not prerequisites established for today's release.

[NVIDIA SGLang 26.08 notes, August 31](https://docs.nvidia.com/deeplearning/frameworks/sglang-release-notes/rel-26-08.html) explicitly list Spark and contain SGLang 0.5.17, FlashInfer 0.6.17, CUDA 13.4.1 and prerelease torch 2.14. Their CUDA-12 introductory boilerplate conflicts with the component list; use the component list. This NGC image is not the same as the cu130 track, and runtime compatibility remains untested here.

**Critical qualification:** [SGLang deterministic-inference documentation](https://docs.sglang.io/docs/advanced_features/deterministic_inference) supplies `--enable-deterministic-inference` and a Qwen3-30B-A3B example. Its feature table says deterministic **FlashInfer does not support Radix Cache**; deterministic Triton and FA3 do. The generic claim of caching compatibility is therefore backend-dependent. FA3 is not the GB10 answer. Candidate fallback configuration is Triton + deterministic inference + Radix Cache, **unverified on this exact GB10 stack**. Alternatively FlashInfer + Radix Cache may pass empirical token checks, but lacks that combined documented guarantee. Never silently disable prefix reuse and retain a cached cost estimate.

The bf16 speed proxy is the community measurement cited in §1; no exact B1/B4/B8 validation was found. FP8/NVFP4 are supported in portions of the stack, but reduce output-equivalence confidence and historically had sm_121 kernel/loader problems. Do not count speculative DFlash/EAGLE speeds as plain greedy baseline speed or assume a Coder drafter is a drop-in match for these weights.

## 3. llama.cpp server

NVIDIA's [upstream llama.cpp Spark playbook](https://github.com/NVIDIA/dgx-spark-playbooks/blob/main/nvidia/llama-cpp/README.md) supplies the following CUDA-13 build options; it estimates a 5–10-minute compile, excluding conversion/integration. These commands are **proposed only, not executed**:

```bash
cmake -S /ABS/PINNED/llama.cpp -B /ABS/PINNED/llama.cpp/build \
  -DGGML_CUDA=ON -DGGML_NATIVE=ON -DCMAKE_CUDA_ARCHITECTURES=121a-real
cmake --build /ABS/PINNED/llama.cpp/build --config Release -j 8
```

The playbook also mentions plain `121` in troubleshooting; the concrete build recipe uses `121a-real`. Check the pinned CMake/CUDA toolchain accepts it and inspect the emitted target. Do not copy sm_100 flags.

The [upstream HF-to-GGUF converter](https://raw.githubusercontent.com/ggml-org/llama.cpp/master/convert_hf_to_gguf.py) supports a local model directory and `--outtype bf16` or `q8_0`. Convert **models/qwen3-30b-a3b-hf**, not a similarly named downloadable Coder/Instruct-2507 GGUF. BF16 preserves weight precision, not necessarily every tensor storage detail or inference arithmetic; inspect conversion metadata, tokenizer IDs, RoPE settings, and cache/activation precision. Q8_0 changes weights. Full GPU offload is feasible in principle with the stated memory; confirm actual residency and peak allocation.

The strongest nearby measurement is the [llama.cpp repository's DGX Spark benchmark](https://github.com/ggml-org/llama.cpp/blob/master/benches/dgx-spark/dgx-spark.md), dated February 5, 2026: build `11fb327bf`/b7941, aarch64, driver 580.95.05/CUDA 13, **Qwen3-Coder-30B-A3B-Instruct Q8_0**, GPU offload, flash attention, **32 generated tokens**, no shared prefill.

| Prompt length | B1 decode | B4 aggregate | B8 aggregate |
|---:|---:|---:|---:|
| 4,096 | 53.51 | 83.79 | 120.36 |
| 8,192 | 47.20 | 71.69 | 97.39 |

At 8k, B4/B8 per-stream rates are 17.92/12.17 tok/s. This demonstrates useful aggregate gains without faster individual replies. It does **not** measure our bf16 model, 512-token tails, the registered workload, or HF equivalence. No matching BF16 GGUF GB10 measurement was found.

[Server documentation](https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md) supports continuous batching, token-ID prompts, returned token IDs, slots, and `cache_prompt:true` common-prefix reuse. It explicitly warns that prompt/decode batch differences can yield different logits when caching. Temperature zero and a fixed seed are not batch-invariance guarantees. Use raw `/completion`, `return_tokens:true`, fixed sampler/penalty settings, and explicit slot policy during qualification. Test the exact cache type; a BF16 weight file does not establish BF16 KV computation. Allocate context per live slot and verify reported per-slot capacity rather than assuming the total `--ctx-size` belongs to every request.

## 4. TensorRT-LLM and NIM

**TensorRT-LLM is realistic to investigate within a day, but not the first choice here.** NVIDIA's [single-Spark serving recipe](https://build.nvidia.com/spark/trt-llm/instructions) uses `nvcr.io/nvidia/tensorrt-llm/release:1.3.0rc13` and `trtllm-serve`. Direct HF loading through its PyTorch workflow avoids a mandatory offline engine build; its example includes a bf16 MoE, but not this checkpoint. The [supported-model matrix](https://nvidia.github.io/TensorRT-LLM/models/supported-models.html) lists Qwen3MoeForCausalLM/Qwen3-30B-A3B. Architecture support and a Spark recipe separately are not certification of their exact combination.

The [KV reuse documentation](https://nvidia.github.io/TensorRT-LLM/advanced/kv-cache-reuse.html) describes shared prefix blocks. This has the same first-changed-token restriction as other causal caches. A [GB10 Qwen3 NVFP4 load failure, issue 12762](https://github.com/NVIDIA/TensorRT-LLM/issues/12762), concerns scale/export compatibility in an earlier release candidate, not proof bf16 fails. Exact bf16 sm_121 kernel, B1/B4/B8 performance, and batch/HF equality remain **unverified**. Do not import B200 throughput or undocumented environment-variable fixes as evidence. Two to six hours is a reasonable setup allowance only if the official image loads cleanly; a kernel-debugging detour can exceed a day.

**NIM is not a verified exact-model fallback.** The [NIM support matrix, updated September 4, 2026](https://docs.nvidia.com/nim/large-language-models/latest/reference/support-matrix.html) lists **Qwen3-32B NIM for DGX Spark**, not a certified Qwen3-30B-A3B Spark profile. The dense 32B model cannot replace these weights while preserving the experiment. No exact custom-checkpoint within-day recipe, comparable performance, or equality guarantee was established.

## 5. Within Hugging Face without a fork

**Static cache + compile:** [HF cache documentation](https://huggingface.co/docs/transformers/main/kv_cache) describes `cache_implementation="static"` and automatic decode compilation for greedy/sample generation. Fixed allocation can waste attention work on unused positions; bounded shape buckets reduce recompilation but must preserve the registered context limit. Retained KV is already in the baseline. Current [Qwen3MoE source](https://raw.githubusercontent.com/huggingface/transformers/main/src/transformers/models/qwen3_moe/modeling_qwen3_moe.py) advertises fullgraph compilation and SDPA/Flash/Flex support. These are mutable upstream-main capabilities, not verification of the installed package or custom retained decoder.

**MoE fusion:** [HF experts-backend documentation](https://huggingface.co/docs/transformers/main/experts_interface) says bf16 `grouped_mm` supports compilation without CUDA-graph modes, while `batched_mm` supports all modes. Current main switches grouped_mm to batched_mm during low-token GPU decode. Since grouped_mm is already used here, recommending it again yields no new gain; inspect whether that decode switch is already present before budgeting any benefit. SonicMoE/DeepGEMM advertisements for newer architectures are not evidence of usable sm_121 kernels. A no-fork upgrade or supported backend switch is plausible; a promised 3–10× gain is not established.

**Attention:** ordinary SDPA already works in the pilot. It is a dispatcher, so “SDPA” does not identify which fused kernel actually ran. The [FlashAttention project](https://github.com/Dao-AILab/flash-attention) describes FA3 for H100/H800; do not substitute it for a GB10 kernel. FA4 advertises Blackwell, but [June 13 issue 2649](https://github.com/Dao-AILab/flash-attention/issues/2649) reports an sm_121 TMA-output dispatch problem in 4.0.0b16. The issue is displayed closed; the opened evidence does not establish the first fixed release. Exact aarch64 wheel and model-path compatibility still need verification. Keep working SDPA unless a specific alternative is qualified.

**Continuous batching exists upstream, through a different API.** [HF continuous-batching documentation](https://huggingface.co/docs/transformers/main/continuous_batching) now supplies `generate_batch()` and `ContinuousBatchingManager`, paged attention, prefix sharing, and optional graphs/compile. `attn_implementation="paged|sdpa"` avoids an additional FlashAttention dependency. Ordinary `generate()` remains a finite batch, not a continuously refilled scheduler. Integration with the external controller and a compatible Transformers version is required; opening several threads around current `generate()` is not this feature. No exact-model GB10 performance/invariance result was found. The model config's recorded `transformers_version=4.51.0` is checkpoint metadata, not the installed version.

## 6. Prefix reuse with a changing every-request render

All valid causal prefix caches reuse an **identical token prefix**. They cannot reuse later history whose causal antecedents changed, even if its text is identical. For current prompt IDs P and a retained prior sequence Q, let L be their longest common prefix. A block cache of size B can reuse approximately `C = B*floor(L/B)` tokens, subject to residency and implementation-specific partial-block reuse. Fresh prefill is `len(P)-C`; record actual hit counts rather than inferring them from text length. [vLLM's prefix-cache documentation](https://docs.vllm.ai/en/latest/features/automatic_prefix_caching/) explicitly limits the gain to prefill, not output decoding.

For the stated layout `[unchanged earlier history H][new render R][new request U]`, only the prefix through H and any initial unchanged render tokens is cacheable. **Illustration, not a measured renderer size:** at 10,000 tokens, H=8,000 and R+U=2,000 permits roughly 80% prompt reuse. If the first change occurs after only a 500-token system prefix, reuse is about 5%, even if 8,000 later history tokens are unchanged. Do not relocate the render to improve this number: layout is frozen and changes model semantics. Exact L/hit fractions were not measured in this research; the pilot README does not supply them.

| Path | Cache behavior for the changing block |
|---|---|
| vLLM APC | Resident identical prefix blocks only; new render and causal suffix re-prefill |
| SGLang Radix | Same restriction; deterministic FlashInfer cannot currently combine with Radix per docs |
| llama.cpp slots | Common prefix in selected/reused slot; cache residency/slot assignment matters |
| TensorRT-LLM | Shared prefix blocks; exact enablement depends on serving configuration |
| NIM | Profile/backend dependent; no verified exact-model route |
| HF retained/static cache | Client must truncate invalid suffix to L and recompute; static allocation alone does not implement cross-request APC |
| HF continuous-batching API | Prefix sharing exists upstream; exact integration/version unverified |

The read local configuration has 48 layers, four KV heads and head_dim 128. An unquantized two-byte K/V cache therefore costs `48*4*128*2*2 = 98,304 bytes/token` (96 KiB), excluding allocator/metadata overhead. At 11,562 tokens this is **1.059 GiB per independent sequence**, approximately **8.47 GiB for eight** without sharing; at 32768 it is 3 GiB/sequence, 24 GiB for eight. The 57GB weights plus KV fit the stated pool in principle, but weights, startup scratch, graph pools, cached inactive prefixes, OS, and controller share that same memory. Avoid concurrent HF/backend model loads during qualification.

## 7. Exact equivalence and throughput protocol to register before running

This is a proposed **small exact screen followed by qualification**, using only authored DEV/synthetic inputs disjoint from evaluation. No fitting, tuning, prompt rescue, quantization calibration, or backend selection using evaluation prompts/responses. All backend and threshold choices are frozen before these checks; changes require a disclosed rerun, not dropping failures.

1. **Freeze 24 paired rounds:** four authored DEV histories, six fixed checkpoints each, covering approximately 5k, 8k, 11k contexts and at least one transition beyond round 16 in a 32-round history. Include render additions/removals/reinstatement. Run R, N, T for each: **72 distinct arm-round prompts**. Include O as 24 additional cases if it remains in the larger test. Select by shape/event coverage, not model output. Freeze exact prompt IDs, renderer bytes, checkpoint/tokenizer hashes, package revision, RoPE, dtype, stop IDs, cap 512 including EOS, and generation settings. Previously saved DEV output can be reused only with exact input/config provenance; otherwise obtain the HF reference through the original package/RetainedDecoder path.

2. **Assert the API boundary before comparing models.** Submit exact integer prompt IDs using a native/offline API or raw completions endpoint. Obtain actual output IDs, including EOS, from the backend; decoded-text retokenization is insufficient. Disable automatic chat-template insertion, reasoning/tool parsers, structured decoding, speculative decoding, penalties not present in HF, and quantized KV. Preserve the existing thinking/template behavior through the prompt IDs. Use greedy argmax: HF `do_sample=False`; serving temperature 0 with neutral sampling filters and matched stop handling. Fixed seed is metadata, not a numeric-equality guarantee.

3. **Use anchored replay first.** Each backend receives the same HF-derived history at each checkpoint, regardless of its previous answer. This isolates backend differences from the downstream consequences of an earlier mismatch. Verify HF retained-cache replay against a cold full-prompt replay on the first checkpoint of each history/arm (12 comparisons; 16 with O); a mismatch is a reference/cache-semantics issue to disclose before attributing differences to the new server.

4. **Test schedule and cache invariance.** For each of the 72 prompts, run B1 cold, B1 warm, B4 warm in two fixed request orders, and B8 warm in two fixed orders: **432 backend generations** (576 with O). Reset the reusable-prefix cache between cold cases; use a separate cache-prime pass rather than assuming the cold answer leaves identical residency. Count prime calls and startup work in the cost. Fill concurrent lanes with different frozen cases, not duplicate padding. Repeat the B1-warm matrix once after a server restart and re-priming: another 72 generations (96 with O). Record actual active-batch shapes, not just client concurrency. An early divergence can stop strict qualification; preserve and report all attempted cases and mark the rest unrun.

5. **Report exact differences.** Primary divergence is complete-output mismatch including length/EOS: `D = number of nonidentical ID sequences / number of paired cases`. Report it separately for HF↔backend, cold↔warm, B1↔B4, B1↔B8, and restart, split by arm and context. Also report first differing index, prefix agreement, EOS/cap mismatches, token-level positional mismatch with missing positions counted, and decoded-byte differences. Token-wise mismatch after the first divergence is descriptive, not independent evidence. Optional top-two logit gaps at the first mismatch diagnose near ties; teacher-force the common prefix to compare logits without conflating divergent histories.

6. **Decision rule:** strict drop-in acceptance requires **0 output-ID divergences**, correct stop/cap handling, and no controller/renderer changes in every completed condition used by the eventual test. This establishes observed equality on the screen, not universal equivalence. Even 0/72 gives an illustrative independent-case 95% upper bound of about 4.1% divergence; histories are correlated, making that bound optimistic. “Same mechanism” additionally requires that R still registers/renders every request, N/T preserve their definitions, and no mask/router bias, prompt rearrangement, grammar constraint, or model substitution has been introduced.

7. **If exact equality fails:** do not silently call “close” a pass. Default numerical tolerance is zero. A bf16 backend with unchanged controller can still implement the **same conceptual mechanism with a changed numerical realization**, but the report must state its measured D and require a pre-evaluation amendment/new backend baseline for all arms. No universal 1% token threshold establishes scientific equivalence for path-dependent tool actions. FP8/Q8/NVFP4 additionally change model precision and require that disclosure even if this small screen happens to match. If the registered test requires literal HF outputs, any divergence rejects that backend configuration.

8. **Then close the controller loop and measure real cost.** Before a larger launch, run complete prespecified DEV episodes covering both 16 and 32 rounds, independently in HF and candidate backends with their own answers fed forward. Compare tool envelopes, controller states, executed actions, stop reasons, and outcomes. The backend must return text/IDs to the unchanged controller between rounds; next rounds of one episode cannot be batched ahead of that dependency. Fill four/eight lanes from independent episode/arm states with fixed accounting. Report aggregate output tokens divided by actual wall time, decode-only rate, TTFT, cached/new prompt tokens, active concurrency, length distributions, cold-start cost, memory, and every required callback. Recompute the existing weighted arm-count projection with 25% reserve and all spent/qualification costs; accept the budget only at ≤12 GPU-h and all other registered eligibility gates satisfied.

If the larger test requires the pilot's internal hidden-state artifacts, ordinary serving APIs do not automatically reproduce those measurements. Account for a supported extraction path or separately registered replay cost; do not drop instrumentation and claim the same measured workload. This is a scope question for the implementation brief, not a reason to retain a custom mask/router path that the shipped mechanism does not use.

## Concrete first trial and stop-loss

Resolve the official `vllm/vllm-openai:cu130-nightly` track to an ARM64 image digest before installation. Mount the exact local model read-only. Proposed initial arguments, **not run here**:

```text
environment: VLLM_BATCH_INVARIANT=1
model: /model                         # local weights mounted read-only
--dtype bfloat16
--kv-cache-dtype auto                 # verify logs resolve to bf16
--tensor-parallel-size 1
--max-model-len 32768
--max-num-seqs 4
--max-num-batched-tokens 2048
--gpu-memory-utilization 0.70
--enable-prefix-caching
--generation-config vllm
```

These are candidate flags, not a validated launch recipe. Confirm the pinned CLI supports the combination; chunked prefill must handle prompts larger than the scheduling-token budget without truncating them. Set every required generation option explicitly rather than inheriting an unrelated model generation_config. Let the invariant-mode implementation select supported kernels initially and record them. Qualify concurrency 1 before 4; 8 is a separate measured configuration. If invariance forces a slower compatible attention path, measure that path rather than quoting the faster nonqualifying one.

Allow at most **two hours of setup/debugging** to obtain a clean bf16 vLLM server before switching to the SGLang fallback. Do not spend a day porting kernels. For SGLang, first check whether the pinned Triton deterministic+Radix combination works on GB10; otherwise choose and disclose the caching/determinism tradeoff before measurement. If neither preserves required outputs at an acceptable total cost, keep the larger test blocked under its existing recipe. llama.cpp Q8 is an attractive later precision-change experiment with strong nearby throughput evidence, not the default equivalence fallback.

## Evidence audit and remaining gaps

All external links cited above were opened on 2026-09-06. Dated release notes and measurements are identified inline; `main`, `master`, `stable`, `latest`, and Docker nightly tags are mutable, and an exact release/digest was **not** certified in this pass. Source provenance is attached to the relevant claim rather than an uncited performance ranking. First-person forum measurements are labeled as such; manufacturer/project documents establish feature availability, not independent performance verification.

| Material claim | Evidence/confidence | Remaining gap and next check |
|---|---|---|
| Official ARM64/CUDA13 Spark vLLM route | Official GPU docs + dated Spark article; high for availability | Inspect chosen manifest/digest and actual sm_121 bf16 kernel launch |
| Approximately 3× bf16 opportunity | First-person Coder proxy + local baseline; moderate/low transfer confidence | Exact checkpoint, 5–11k, invariant settings, 200–512 generated tokens |
| 4–9× llama.cpp opportunity | Upstream 8k Q8 Coder benchmark; high for reported proxy, low for bf16 transfer | Exact local conversion; longer decode; byte/ID differences |
| Caching with changed render | Causal dependency + documented prefix semantics; high | Measure actual L/hits; do not credit illustrative 80% |
| Invariant serving can replace HF exactly | No cross-backend guarantee; unverified | Frozen anchored and closed-loop protocol above |
| SGLang cache/invariance combination | Explicit backend compatibility table; high | GB10 Triton deterministic+Radix runtime validation |
| TRT/NIM within-day exact-model gain | General support only; low/unknown | Exact Spark profile/kernel/load/performance |
| HF optimization gain | Current upstream features documented; local compatibility unknown | Installed-source check; no double counting grouped_mm/retained KV |

Searches covered official vLLM ARM64/CUDA13 wheels and Spark recipes, Qwen3MoE kernels and batch invariance, exact GB10 bf16/B4/B8 measurements, SGLang deterministic/Radix compatibility, llama.cpp Spark builds/benchmarks/server/converter, TensorRT-LLM/NIM Spark model matrices, and HF cache/experts/batching/attention support. Follow-up prioritized precision/context mismatches, CUDA runtime/driver differences, GB10-specific failures, and contradictory support wording. Research stopped after these gaps were either resolved or explicitly bounded; further broad searches mostly yielded different checkpoints, quantized configurations, speculative decoding, or datacenter GPUs. No report rate is a newly measured local backend result. Markdown structure, arithmetic, and file scope were checked; no visual rendering was needed for this text artifact.
