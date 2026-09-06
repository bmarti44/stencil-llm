# Automatic register updater: options A–E, second opinion (fable, 2026-09-06)

Brief: scratchpad `updater-research-brief.md` (Brian: "can a classifier finish the automatic bit — chat context +
current rules + instruction in, new instructions out? Could a LoRA on the model itself do it?"). Independent of
astra's memo; same structure. CPU only, web research; no installs, no model launches; nothing under data/bench read.
"Opened" = I fetched the page; "unverified" = search snippet only; "est." = my arithmetic, not a measurement.

Local facts used (checked on this box, no GPU touched): PEFT 0.18.1, transformers 5.2.0, trl 0.29.1, torch 2.11+cu128
installed; qualified vLLM image 0.19.2rc1 (results/quick-checks/vllm-qual/README.md); GB10 shows 119 GB total,
~90 GB in use while the pilot server is up. Ship form = one HF snapshot, frozen trunk, HF `custom_generate`
dispatch that owns the decode loop and the session (models/stencil-package/README.md).

Bars (from the brief): admission overlap recall >= 85% at precision >= 95%, payload/quoted FA <= 3%, non-user FA = 0;
relations accuracy >= 94% with supersedes recall >= 85%; SETUP FA turns <= 2/96 with 36/36 admits.

Where we actually are (local, re-read): admission v1 sentence-pair 78.7% overlap recall (check44b), token-BIO v2
64.2% on held-out-3 with DEV 93.7% (check44c); relations v2 96% on held-out-2 but 73% supersedes recall on the
harder held-out-3 with the miss families already enumerated (bare value+temporal 13, withdraw+replace 12,
meta-override cut by threshold 10, task-scoped override 8, "actually B" 3). Frozen 1.7B JSON extractor 2.75%
recall — but check44 RESULTS says 289/314 raw candidates were rejected as non-verbatim because the token filter
corrupted string endings (apostrophe/comma suffixes, tabs); that number is an operational failure, not a ceiling.

---

## A. LoRA / adapter on the TRUNK (Qwen3-30B-A3B MoE) as the register updater

What it is: train a LoRA on the trunk to map (register JSON + message [+ 2 prior user sentences]) -> ops list;
serve it as a second "personality" of the same weights, switched per request.

Evidence (opened unless marked):
- PEFT on Qwen3-MoE: attention modules are ordinary `nn.Linear` (q/k/v/o); experts in transformers v5 are fused
  3-D `nn.Parameter`s (`mlp.experts.gate_up_proj`, `down_proj`) reached only via `LoraConfig(target_parameters=...)`
  (PEFT docs, "Targeting nn.Parameter directly", https://huggingface.co/docs/peft/main/developer_guides/lora).
  The same page warns that unmerged expert-LoRA inference in HF is "substantially" slower (PEFT materialises every
  expert's delta), that all adapters must target the same parameter set, and points to vLLM >= 0.11.2 for serving.
- vLLM: `Qwen3MoeForCausalLM` gained `SupportsLoRA` in PR #20932 (merged 2025-07-17; attention/shared layers only,
  warning for FusedMoE) and FusedMoE expert LoRA in PR #21229 (merged 2025-10-21, shipped v0.11.2; max tested rank
  64; follow-up bugs for Qwen3 MoE variants without shared experts). Issue #40005 (2026-04) states Qwen3-MoE LoRAs
  including expert weights load fine while Qwen3.5-MoE did not; 2-D (per-expert) vs 3-D (fused/PEFT) adapter
  layouts are declared by the caller with `--enable-mixed-moe-lora-format` and `is_3d_lora_weight`, which vLLM
  "does not inspect" — a wrong declaration silently gives wrong outputs (docs, https://docs.vllm.ai/en/latest/features/lora/).
  Our qualified 0.19.2rc1 is well past 0.11.2, so both attention-only and expert LoRA are serveable in principle.
- Prefix cache: the block hash includes the LoRA id (https://docs.vllm.ai/en/stable/design/prefix_caching/), so a
  LoRA request cannot reuse the base model's cached context. Every updater call = one full re-prefill of the
  conversation with the adapter, on top of the generation prefill. (Also issues #3264, #30931 on same-name reuse.)
- Activated LoRA (IBM): NeurIPS 2025 paper (arXiv 2504.12397, opened HTML v4): adapts only tokens after an
  invocation string so the base KV cache is reused; attention-only (q/k/v), rank 32 recommended; accuracy vs LoRA
  on 7 SFT tasks median diff 0.0%, mean 0.6% favouring LoRA, p = 0.8; intrinsics within 1-2 F1 (jailbreak 92.5 vs
  94.3). Lives in PEFT as `LoraConfig(alora_invocation_tokens=[...])`: CAUSAL_LM only, cannot merge, no beam
  search, KV reuse through `DynamicCache` + `disable_adapter()` in HF `generate` (PEFT docs, opened). Known bug:
  zero gradients with gradient checkpointing (PEFT issue #2826; workaround `gradient_checkpointing=False`). The
  vLLM PR #19710 was auto-closed unmerged on 2026-02-09 (maintainers: "niche"); the IBM serving paper
  (arXiv 2512.17910, 58x latency, 100x TTFT) is a vLLM extension whose code I could not find upstream
  (unverified: whether a public fork exists). IBM/activated-lora repo is deprecated in favour of PEFT.
  Tested bases: Llama 3.2 1B/3B, 3.1 8B, Mistral 7B. No MoE base anywhere in the aLoRA literature (unverified
  that PEFT aLoRA has ever been run on Qwen3-MoE; attention-only makes it architecturally plausible).
- Training on GB10: NVIDIA forum thread (opened) reports bf16 LoRA (r=16, attention+MLP experts) on
  Qwen3.5-35B-A3B on a DGX Spark at ~72 GB peak with ~47 GB headroom, after CUBLAS/illegal-access fixes on the
  PyTorch 25.10 -> 26.03 containers, and an adapter-layout mismatch with vLLM fused MoE ("vLLM expects per-expert
  tensors, Unsloth produces fused"). HF discussion Qwen3-30B-A3B-Instruct-2507 #25 (opened): QLoRA died at step 0
  with expert targets, ran after dropping expert modules (PyTorch issue #168329). No published tokens/s for a 30B
  MoE LoRA on GB10; the only GB10 LoRA number I found is 451 tok/s stock -> 3,461 tok/s tuned on Qwen3.5-2B
  (forum, opened; the slowness there was GatedDeltaNet fallback, not sm_121 per se).
- Small-data structured-extraction LoRAs on 30B-class models: none found with numbers. Nearest: LDST (LLaMA-7B,
  attention-only r=8 LoRA, 8-bit) matches ChatGPT on SGD/MultiWOZ JGA and beats T5-XXL by 6-27 points; 1% of
  MultiWOZ 2.4 gives 46.8 JGA vs 40.0 for the 11B baseline (arXiv 2310.14970, opened). Attention-only LoRA is
  enough for slot/state extraction there.
- Attention-only vs experts on MoE: MoE-Sieve (arXiv 2603.24044, unverified) always trains attention and finds
  LoRA on the top-25% routed experts matches full expert LoRA; no paper isolates attention-only on Qwen3-30B-A3B.

Effort (est.): CPU data conversion to the ops format 3-4 h (shared with B); training script 2-3 h (PEFT + TRL are
installed; no Unsloth needed for attention-only); vLLM serving smoke 1-2 h (`--enable-lora`, adapter dir in the
snapshot); HF ship-path smoke with `PeftModel` + `disable_adapter()` inside our custom_generate 2-3 h; aLoRA variant
+1-2 h (invocation tokens, gc off). The vLLM pilot server must be stopped for training (61 GB bf16 weights + ~10 GB
adapter/optimizer/activations does not fit beside a 90 GB server).

GPU cost (est.): 10k examples x ~500 tokens = ~5M tokens/epoch. Attention-only, bf16, 3B active params: 1.5-4k tok/s
plausible on GB10 -> 20-60 min/epoch. Expert LoRA via `target_parameters`: unknown, likely 2-5x slower (PEFT
materialises all 128 experts' deltas); budget-breaking risk. Inference: one extra full prefill per message under
vLLM (no cache sharing); near zero extra prefill under HF aLoRA.

Expected accuracy vs bars: highest ceiling of all options in principle (3B-active trunk, best language
understanding on the box; relations is a 5-way classification given the rule, where even bge-small reaches 96% on
ordinary phrasing). With ~10k authored examples, fine-tuned generative extractors of 1-8B reach 94-97 F1 on
schema-bound IE (merchant IE paper, arXiv 2606.08051, opened: Qwen3.5-0.8B 94.75, 4B 96.60, LLaMA-8B 96.95). I
expect the relations bars to be reachable and admission recall to land wherever the DATA coverage puts it (see E);
the trunk does not fix the held-out coverage gap that took v2 from 93.7% DEV to 64% held-out.

Ship-form fit: good on paper (one snapshot, frozen trunk, adapter safetensors alongside; our custom_generate owns
the cache so aLoRA's base->adapter->base pattern is exactly our loop). Two real fits: HF path (aLoRA, KV reuse,
slow MoE inference if experts are adapted, so attention-only) and vLLM path (plain LoRA, per-request `lora_request`,
no cache reuse, expert LoRA OK but layout pitfalls). aLoRA cannot serve on vLLM today.

Risks: (1) trunk generation with adapter off is unchanged by construction (separate weights) but must be
instrumented, not asserted — bitwise-compare 50 fixed prompts base vs `disable_adapter()`/no-lora-request
(AGENTS.md "claim only what the artifact measures"); (2) latency: full re-prefill per message under vLLM;
(3) MoE training fragility on GB10 (step-0 crashes with expert targets; sm_121 kernel mismatches); (4) budget: a
30B run that stalls burns the GPU-hour; (5) contamination: fit only on kimi/Opus/astra authored corpora,
scenario-disjoint DEV, one held-out look; held-out-3 has been opened twice already — prefer a fresh fable
held-out-4 for a GO decision; never data/bench.

## B. LoRA on a SMALL dense model (Qwen3-1.7B/4B/8B) as a dedicated updater

Evidence (opened): MemReader (arXiv 2604.07877) is the closest analogue to our updater: Qwen3-4B (and 0.6B),
7k SFT + 3k GRPO trajectories distilled from a Gemini-3-Flash teacher, action set add/buffer/search/ignore;
extraction recall 96.57 / F1 98.21 and "update correctness" 94.55% on HaluMem; outperforms GPT-4o-mini on LOCOMO;
models + code public (MemTensor/MemOS). Merchant IE (above): 0.8B-8B LoRA all within 2.2 F1 of each other at
95-97. ETLCH (arXiv 2509.08381, abstract): a 1B LLaMA LoRA on 100-1,000 samples/task beats strong baselines on
JSON/KG/NER extraction. "Sub-Billion, Super-Frontier" (arXiv 2606.22606, HTML opened): tuned 0.5B-3B relation
extractors 0.83-0.84 micro-F1 vs 0.69 GPT-5.4 / 0.66 Claude Sonnet 4.6 zero-shot — caveat: frontier models were
zero-shot only, and the authors say the gain is "targeted task adaptation", i.e. data. LDST (above): 7B, r=8,
attention-only, on par with ChatGPT for DST. DST/GRPO on small LLMs (OpenReview SLLZPhnEz6, unverified).

Effort: data conversion shared with A (3-4 h); TRL SFT script 1-2 h (dense model, no MoE pitfalls, gc allowed);
eval harness reuse from check44b/c (metrics exist). Serving: a second local model in the snapshot (1.7B ~3.4 GB,
4B ~8 GB bf16) loaded by our custom_generate, or a second vLLM server (memory fine beside the trunk).

GPU cost (est.): 1.7B: ~5M tokens/epoch at 8-15k tok/s -> 6-10 min/epoch, 3 epochs < 30 min. 4B: ~2-3x that; 3
epochs ~45-60 min. Inference ~0.3-0.6 s/message for a 1-2k-token prompt (est.).

Expected accuracy: relations bars likely (classification given the rule; the small model sees the same authored
distribution the 96% bge-small saw). Admission: bounded by data coverage exactly as A; a generative decoder removes
the sentence-splitter ceiling (all 31 two-rule messages in check44b were lost to one candidate) and the BIO
confidence filter (291 -> 247 in 44c), which is where 20+ recall points went. My expectation: 75-90% overlap recall
on held-out-3 with a 4B, wide band because of the held-out family shift.

Ship-form fit: good (extra weights in the same snapshot; frozen trunk untouched; no adapter switching, no cache
tricks). Latency additive but small.

Risks: a second model to load and keep in memory; JSON validity (small models "frequently emit JSON that doesn't
match" per Graphiti, cited in reuse memo) — mitigated by schema-constrained decoding or strict parse + journal;
same contamination rules; verbatim-span decoding must be tested with a whitespace/punctuation-normalised matcher
(check44's lesson) before blaming the model.

## C. Discriminative alternatives not yet tried

Evidence: DeBERTa-v3-large remains more sample-efficient than ModernBERT-large in controlled comparisons
(snippets, unverified; 90.7 vs 69.8 on a structural-generalisation task). GLiNER fine-tunes on ~3k examples work
but recall lags precision (cyber NER F1 0.80 / recall 0.74; Label Studio and Medium posts, unverified);
GLiNER-multitask / GLiNER-Relex (arXiv 2605.10108, opened) do joint span + relation with label prompts and are
open source — a pairwise+span joint model exists off the shelf. Span labelling with LLMs (arXiv 2601.16946,
opened): tagging is a robust baseline; "LogitMatch" constrained decoding forces outputs to be valid input spans —
directly relevant to any generative arm.

Effort: 2-4 h to swap the encoder in the existing check44c BIO trainer (deberta-v3-large / GLiNER-large); GPU
10-25 min per fit. Expected: +3-8 recall points over bge-small (est.); does not by itself address multi-rule and
cue-less misses, which are semantic coverage gaps (44c DEV 93.7% shows the encoder can learn the authored
distribution). Ship fit: excellent (CPU, ~100 ms). Risk: more of the same; the same DEV/held-out gap.

## D. Prompted frozen trunk with constrained decoding (check 46)

Evidence: zero-shot 27-30B extraction sits far below fitted models on span tasks (Gemma3-27B 41.3 F1 on medical IE,
medRxiv 2026, unverified; frontier zero-shot RE 0.66-0.69 vs tuned 0.83, opened). Few-shot closes part of the gap
but I found no 30B-class few-shot result at >= 85% span recall with >= 95% precision on a novel label spec.
Format constraints: "Let Me Speak Freely?" (EMNLP 2024 industry, arXiv 2408.02442, opened) — strict JSON hurts
reasoning-heavy tasks and HELPS classification-like tasks (slot filling, intent); recommended scratchpad +
validated final field. JSONSchemaBench (arXiv 2501.10868) benchmarks xgrammar/outlines etc. Our own check44 shows
the decoder, not the model, produced most of the 1.7B failure (289/314 non-verbatim rejections from suffix bytes).

Effort: as briefed (<= 45 GPU-min, ~900 generations). Expected: relations near or above 90% few-shot (5-way
decision given the rule, classification-like); admission 55-80% overlap recall, precision probably below 95% on
payload negatives (the 1.7B proposed rules on 91/102 payload negatives before validation) — PARTIAL is the modal
outcome (est.). Ship fit: perfect (no new weights) but the most expensive per message (full context + register +
few-shots through the trunk, plus one extra prefill unless the updater and generation prompts share a prefix).
Risks: prompt iteration leakage (cap 3 iterations on fit-corpus DEV as briefed); the constrained schema must let
spans be verbatim (use a normalised matcher and journal raw vs matched separately, or LogitMatch-style span
constraint); thinking off.

## E. Anything else — is more hand-written data the real lever?

Evidence: every fitted result on our banks shows a DEV->held-out cliff (admission 93.7 -> 64.2; relations DEV 94.7-
95.2 -> 87.1 on held-out-3 while 95.2 on held-out-2), and the miss families are enumerated and small (five
relations families; two-rule messages 25/62 and 27/62 recall in 44b). That is under-coverage, not capacity.
Literature agrees that adaptation data, not model size, carries the gain (arXiv 2606.22606; ETLCH's largest gains at
the smallest data scale; merchant IE 0.8B within 2.2 F1 of 8B). Synthetic-diversity paper (arXiv 2511.01490,
opened) says multi-source synthetic data beats single-source. Memory-write research shows learned/distilled writers
work (MemReader; SAGE novelty gate arXiv 2605.30711, unverified; "Agentic Memory" RL-trained ops, unverified) but
all rely on teacher-labelled data at ~10k scale. RECAST (arXiv 2505.19030) offers a constraint-type taxonomy;
lineage unknown — do not fit on it without provenance. NLSI (arXiv 2311.09796) is applicability, not admission.
Instruction-hierarchy work is about obeying, not extracting.

What the data lever costs: 1-2k new kimi rows targeted at the named families (cue-less standing rules, two-rule
messages with distinct keys, withdraw+replace, bare value+temporal, task-scoped override of global) written from
the label specs only (no probe/held-out exemplars — memory rule), Opus/astra audited; CPU-cheap refits of the
existing bge-small heads (10-20 GPU-min) tell within a day whether coverage moves held-out recall. A legal
multiplier: MemReader-style distillation — run the frozen trunk (check 46 prompt) over AUTHORED inputs only and
audit its ops as training labels; lineage line: fit-on = authored inputs + trunk-proposed, human-audited labels;
evaluate-on = fresh fable held-out; never benchmark prompts or responses.

---

## RANKED TOP-3 (each <= 1 GPU-h, GO bars pre-written)

1. Check 46 as queued, with the decoder fixed (frozen trunk, few-shot, no fitting). Change from the brief:
   (a) scratchpad-free strict JSON is fine for the relations op, but for spans use a whitespace/punctuation-
   normalised verbatim matcher and journal raw/normalised/rejected counts separately; (b) report per-family
   recall (single, two-rule, rule+payload; the five relations miss families). Budget 45 GPU-min.
   GO = the brief's bars (admission >= 85% recall at >= 95% precision, payload/quoted FA <= 3%, non-user 0;
   relations >= 94% with supersedes recall >= 85%; SETUP <= 2/96 FA with 36/36 admits) -> automatic proposal path.
   PARTIAL = passing half goes automatic. Either way the outputs give the ceiling reading and the teacher for (2).
2. Small dense generative updater LoRA — Qwen3-1.7B first (already used locally in check44), 4B if the 1.7B is
   within 10 points of the bars. Fit-on = kimi/Opus/astra authored corpora converted to (register JSON + message ->
   ops list), scenario-proxy-disjoint DEV 10%; r=16 attention+MLP, 3 epochs, bf16, TRL SFT; budget <= 1 GPU-h
   including a held-out pass. GO = same bars on a FRESH fable held-out-4 (held-out-3 as disclosed secondary) plus
   p95 <= 1 s/message on GB10. NO-GO with DEV >= 90% and held-out < 80% = coverage; go to the data lever, not a
   bigger model.
3. Attention-only aLoRA on the trunk (option A, HF ship path), only if Brian wants one set of weights or (2)
   passes and we want to drop the second model. r=32 on q/k/v(/o), invocation string = a special-token-delimited
   marker after the register block, gradient checkpointing off, vLLM server stopped during training; abort at 45
   min if throughput < 1.5k tok/s. Budget <= 1 GPU-h. GO = (2)'s accuracy bars AND bitwise-identical base outputs
   with the adapter disabled on 50 fixed prompts AND a vLLM `--enable-lora` load smoke of the same adapter as a
   plain LoRA (for the server path, accepting the re-prefill cost) — "unchanged trunk" is a measurement, not a claim.

Not in the top-3: C (encoder upgrade) is a 20-minute side bet worth running while (2) trains; D-with-fitting on the
trunk's own outputs is the data multiplier for (2), not a separate check.

## Plain language for Brian: is a LoRA on the trunk the right bet?

It is a sound bet but not the first one. A LoRA is a separate weight file, so the trunk's generation is untouched
when it is off — that part of the worry is solved by construction, and we can prove it bitwise. The machinery
exists today: PEFT can train attention-only LoRAs on Qwen3-30B-A3B, vLLM 0.11.2+ (we run 0.19) serves them, and
IBM's activated-LoRA in PEFT lets our own custom_generate loop reuse the conversation's KV cache so the updater
call costs almost nothing extra — but only on the HF path; vLLM closed the aLoRA PR, so on the server every updater
call re-prefills the whole context with the adapter. The 30B MoE is also the most fragile thing to train on this
box (step-0 crashes with expert modules, fused-vs-per-expert layout traps, and one stalled run eats the GPU-hour).
Meanwhile the published evidence says model size barely matters once you fit on ~10k good examples (0.8B to 8B
extractors land within ~2 F1 of each other; a fine-tuned Qwen3-4B memory writer beats GPT-4o-mini), and our own
numbers say the missing recall is coverage — the held-out families we never wrote enough of — not model capacity.
So: run check 46 to get the zero-fit ceiling, fine-tune a small dense updater on the authored data next (cheap,
robust, fits the snapshot), and reserve the trunk LoRA as the consolidation step once the data and the bars are
proven. Without the extra cue-less / multi-rule / withdraw-and-replace data, none of the three will clear 85%.

## Unverified / not found
- No public tokens/s for LoRA training of a 30B MoE on GB10; the est. above is from dense numbers and active-param
  scaling. No published aLoRA on any MoE base. IBM's vLLM aLoRA serving code: not found upstream. MoE-Sieve, SAGE,
  DST-GRPO, DeBERTa-vs-ModernBERT and GLiNER blog numbers are from snippets only. No 30B-class few-shot span
  extractor reported at >= 85% recall / 95% precision on a custom spec.
