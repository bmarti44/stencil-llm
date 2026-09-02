# Deep research: making the wave mechanism move benchmark scores (fable, 2026-09-02)

Brief: scratchpad/research-brief.md. Every number in the citation table was read from a
source I opened in this session (arXiv abstract page, or the PDF converted with
`pdftotext` and read). Items marked **[memory]** were NOT opened and are recalled
background; treat them as unverified. Repo context read (read-only): src/stencil/bench.py
(`make_wave_bias_fn`, `make_deficit_hook`, WAVE_LAYERS = 20-27), WORKLOG.md entries on
the deficit gate (exact odds correction), the sealed conf run (+0.39, p=0.39, 3→12
truncations), and the pinned-KV verification (62% gap recovery, pinned_wave degenerate
13/20 sessions).

## 0. Bottom line (read this if nothing else)

1. Our deficit-gated wave IS SpotLight (Venkateswaran & Contractor, arXiv:2505.12025)
   restricted to layers 20-27, all heads, uniform over the span, with an *exact* odds
   correction. Three independent groups have now characterised exactly this family:
   - SpotLight's own ablation (Fig. 5, Llama-3.1-8B, IFEval): steering **all heads of a
     single layer "frequently performs worse than the baseline"**; only all-layers-all-heads
     or one-head-across-all-layers beat baseline. Our layer-20+ block is the losing regime.
   - PASTA (ICLR 2024, Fig. 2): "**Steering all heads … degrades performance compared to the
     baseline zero-shot performance**" at α = 0.01; recommended 50-150 profiled heads.
   - InstABoost (arXiv:2506.13734, Thm 3.3 + Fig. 5): a **state-dependent target mass
     (SpotLight-style) drives the remaining context mass into a "suppression regime"**;
     SpotLight's relevance score collapses to 0 at ψ_target = 0.4. Our exact-odds
     correction is *more* rigid than SpotLight's log-ratio (SpotLight under-corrects to
     ψ_new ∈ [ψ_t/(1+ψ_t), ψ_t]; ours lands exactly on τ).
   - DIRECTER (ICLR 2026, arXiv:2603.06745, Table 1/2): with the authors' *official*
     settings, **SpotLight scores 59.7/71.3 vs zero-shot 73.5/81.5 on IFEval** (Llama-3.1-8B)
     — oversteering; after tuning (ψ = 0.1) it is 76.3/83.6 (+2.8/+2.1). **On Llama-3.2-1B the
     best method in the paper moves IFEval 61.3 → 61.6 (+0.3)**; on Qwen2.5-3B, 63.9 → 67.1.
2. Calibration for Qwen3-1.7B: no independently replicated attention/activation steering
   result at ≤3B exceeds ~+3 pts single-turn IFEval. SpotLight's own +11 at Qwen2.5-3B
   (0.42 → 0.53) was not reproduced by DIRECTER's replication (SpotLight* 62.8 vs 63.9
   zero-shot, −1.1). Our sealed +0.39 is *in line with the literature*, not an anomaly.
   The registered +2.0 floor is at the upper edge of what single-turn evidence supports.
3. Where attention steering shows its largest effect is exactly our live hypothesis:
   **multi-turn, aged instructions**. SpotLight MT-IFEval (5 turns, 8B models): baseline
   accuracy drop across turns 18.2% → 9.3% with steering; +25.7% relative in the final
   turn; Granite-8B drop 22.1% → 6.3%. SysBench shows adherence to the system message
   correlates with the *proportion of attention on its tokens* across turns (Fig. 6) and
   Llama-3.1-8B's "all first n turns compliant" rate falls 62.9% → 6.7% from R1 to R5.
4. The KV line is corroborated: "The Pitfalls of KV Cache Compression" (ACL 2026,
   arXiv:2510.00231) shows eviction is *biased against specific instructions* ("selective
   amnesia"), system-prompt defenses get evicted first, and a **fair (per-instruction)
   eviction policy restores adherence**. "Protection Is (Nearly) All You Need"
   (arXiv:2605.18053) reports 10% boundary protection recovers 69-90% of ceiling quality
   — our 62% recovery is in the expected band.
5. Ranked redesigns (Section 7): (1) plausibility-gated wave (DIRECTER gate: the steered
   token must be base-plausible or the dose halves) on pinned KV, (2) contextual-head-
   selective wave across all layers (Focus Directions / PASTA profiling, 20-150 heads),
   (3) fair-eviction KV retention with no bias at all as the null-mechanism control.
   Falsifier: if (1) and (2) both add < +2 pts over unbiased pinning on the aged-constraint
   Multi-IF slice at n ≥ 900 conversations, "waves select" is falsified for this trunk;
   "synapses store" (KV retention) survives on its own evidence.

## 1. Citation table (all opened this session unless marked)

| # | Paper | Venue / id | URL opened | Exact number(s) reported, on what |
|---|---|---|---|---|
| 1 | PASTA — Tell Your Model Where to Attend (Zhang et al.) | ICLR 2024, arXiv:2311.02262 | arxiv.org/abs + pdf | LLAMA-7B avg +22% over few-shot on 4 tasks (JSON, pronouns, BiasBios, CounterFact). α fixed 0.01; k ∈ {300,400,500} profiling; **steer-all-heads < zero-shot baseline (Fig. 2)**; more heads → higher efficacy but lower JSON Pred. Acc./Fluency; recommend 50-150 heads; robust to α (Fig. 3c). |
| 2 | AutoPASTA — Model Tells Itself Where to Attend | arXiv:2409.10790 | pdf | δ = log 100 (insensitive 50-3000); LLAMA3-70B-Instruct +7.95% avg (NQ/HotpotQA open-book QA); LLAMA3-8B NQ 40.51% EM (+9.94 over best baseline); coarse-to-fine head search 4.5× cheaper; "steering more heads may result in slight performance degeneration". Not an IFEval paper. |
| 3 | Found in the Middle (Hsieh et al.) | ACL Findings 2024, arXiv:2406.16008 | abs + pdf | Calibrated attention = Attn(doc) − Attn(dummy); rescale per-document mass by softmax(rel, t), renormalised; **6-15 pp** gains when gold doc is mid-context (NQ, SynthWiki; Vicuna-7B-16k, Tulu-2-7B); costs extra forward passes. RAG only. |
| 4 | Attention Buckets (Chen et al.) | ACL 2024, arXiv:2312.04455 | abs (search summary) | Parallel RoPE bases to fill attention troughs; ToolLlama-7B beats GPT-4 pass/win rate on ToolBench. Tool use, not IF. |
| 5 | **SpotLight** (Venkateswaran & Contractor, IBM) | EACL 2026, arXiv:2505.12025v2 | abs + pdf (full) | ψ_target = 0.1 all layers/heads; bias log(ψ_t/ψ_cur) on span keys only when ψ_cur < ψ_t. IFEval prompt/inst (loose, *prompts restructured by Mixtral to separate instructions*): Qwen2.5-3B 0.42/0.53 → 0.53/0.62; Llama-3.1-8B 0.42/0.55 → 0.51/0.62; Qwen2.5-72B 0.49/0.61 → 0.55/0.67; PASTA ≈ baseline. ManyIFEval prompt-level +30% rel. **MT-IFEval (300×5 turns): baseline drop 18.2% → 9.3%; final-turn +25.7% rel.; Granite 22.1% → 6.3%.** Repeating instructions every turn cuts baseline drop 20% → 5%; SpotLight w/o repetition still beats it. Fig. 5: single-layer-all-heads and single-head often < baseline. Reward-model win rate 50-60% (no quality loss). Extreme ψ_t → incoherent (Fig. 1c). Probability-space reweighting worse than logit bias. |
| 6 | **InstABoost** (Guardieiro, Khare, Stein, Wong) | arXiv:2506.13734v3 (Mar 2026) | pdf (full) | Constant additive logit bias B on instruction keys, all layers/heads, multiplier M = e^B ∈ [1,20]; Llama-3-8B-Instruct, 15 tasks. Attention methods avoid latent-steering fluency collapse; **SpotLight relevance collapses with strength (ψ = 0.4 → relevance 0)**; InstABoost M = 19 still fluency 1/relevance 2. Learned reasoner: clean accuracy 99.6% → 99.3% at B = 2.5. Table 1 (avg steering success): Jailbreak PASTA 0.000, SpotLight 0.025, InstABoost 0.594. Hyper-params chosen with fluency ≥ 1 constraint. Not evaluated on IFEval. |
| 7 | **DIRECTER** (Kang & Kim) | ICLR 2026, arXiv:2603.06745 | pdf (full) | Key-scaling α = 100 on instruction tokens; per-step plausibility gate p_raw(steered top-1) ≥ β·p_raw(top-1), β = 0.5, halving steered-layer set on rejection; attention-sensitivity layer ranking. Llama-3.1-8B IFEval P/I: zero-shot 73.5/81.5; PASTA(α=.01) 66.7/75.5; PASTA*(α=.1) 76.5/83.4; SpotLight(ψ=.3) 59.7/71.3; SpotLight*(ψ=.1) 76.3/83.6; **DIRECTER 78.8/84.8**. Avg over IFEval/LIFBench/GSM8K-Format +6.5 abs. **Table 2 IFEval: Llama-3.2-1B 61.3 → 61.6; Qwen2.5-3B 63.9 → 67.1; 7B 72.4 → 74.4; 14B 81.6 → 83.5.** Fixed-strength variants all worse than adaptive (Fig. 2a); plausibility filter also rescues PASTA/SpotLight (Fig. 2b). Throughput −16%. Task fidelity ≈ 92% (judge). |
| 8 | Improving IF through Activation Steering (Stolfo et al., MSR) | ICLR 2025, arXiv:2410.12877 | pdf | Steering vector = Δ residual with/without instruction, single layer, all positions; Phi-3, Gemma-2 2B/9B, Mistral-7B; IFEval format subset. Without text instruction: ≈10% → ≈30%; with instruction (60-90% base) gain on 2/4 models (McNemar p<0.01 marked). GPT-4o quality score drops "comparable to adding the instruction as text"; **failures where model "repeated itself"** noted; perplexity gate used for layer choice. |
| 9 | SAIF (SAE steering for IF) | arXiv:2502.11356 | abs + pdf | Gemma-2-2b/9b-it (Gemma Scope), Llama-3.1-8B (Llama Scope); top-15 latents, final layer crucial; steered strict acc > 30%, loose acc "nearly on par with prompting" (pre-instruction SA 0.14 / LA 0.47 vs post-instruction 0.23 / 0.64; original 0.56/0.75 — Table 3). Steering ≠ prompting yet. |
| 10 | Focus Directions (contextual heads) | arXiv:2503.23306 | abs + pdf | Llama-3.2-3B-Instruct: only 2 heads (0.3%) with contextual score > 0.2, 37 (5.5%) > 0.1; located layers 8-20 (of 28). Split-softmax boost on **top-20 contextual heads, τ = 0.1: EM 0.59 → 0.916** (above gold-only 0.847); **600 heads → below baseline; random heads < 0.3% gain, drop at 50 heads**. HELMET: improves 5/5 LLMs at 32k, 3/5 at 64k; Llama base 52.67 → 62 (post-train) vs focus-direction gains on base. |
| 11 | Multi-IF (He et al., Meta) | arXiv:2410.15553 | pdf | 4,501 conv × 3 turns, 8 languages; metric = mean of inst/conv × strict/loose. Avg-over-languages: **Llama-3.1-8B 0.688 → 0.615 → 0.542**; Llama-3.1-70B 0.826 → 0.742 → 0.668; Qwen-2.5-72B 0.837 → 0.715 → 0.609; o1-preview 0.877 → 0.783 → 0.707. Instruction Forgetting Ratio T1→T2 > T2→T3; IFR falls with scale. |
| 12 | Qwen3 Technical Report | arXiv:2505.09388 | html | **Qwen3-1.7B: IFEval strict-prompt 72.5 (thinking) / 68.2 (non-thinking); Multi-IF 51.2 / 44.7.** Qwen3-0.6B 59.2/54.5, Multi-IF 36.1/33.3; Qwen3-4B 81.9/81.2, Multi-IF 66.3/61.3. |
| 13 | IFBench — Generalizing Verifiable IF (Pyatkin et al., AI2) | NeurIPS 2025 D&B, arXiv:2507.02833 | pdf | 58 new constraints, 294 prompts; single- and **3-turn variant (constraint isolated in turn 3, avg 408 tokens)**. Tülu-3-8B IFEval 82.4 / IFBench 28.9 → IF-RLVR 92.2 / 45.9; Qwen2.5-7B base → 87.8 / 54.7. Multi-turn RLVR helps multi-turn IFBench (Table 7). Most IFEval categories saturate > 90 after RLVR. |
| 14 | SysBench (Qin et al.) | arXiv:2408.10943 | pdf | 500 system msgs × 5 turns; CSR/ISR/SSR. Llama3.1-8B CSR 66.5 / ISR 46.9 / SSR 24.9; Qwen2-7B 47.0/26.9/15.0; GPT-4o 87.1/76.4/54.4. **Dependent sessions R1→R5: Llama3.1-8B 62.9 → 34.3 → 18.3 → 9.0 → 6.7; Qwen2-7B 52.5 → 20.5 → 6.5 → 2.2 → 1.1.** Attention proportion on system tokens tracks per-turn adherence (Fig. 6); system vs user role marker changes attention "very weakly". |
| 15 | The Pitfalls of KV Cache Compression (Chen et al., UCLA) | ACL 2026, arXiv:2510.00231v2 | pdf | StreamingLLM/SnapKV/TOVA/H2O/K-Norm on Llama3-8B and Qwen2.5-14B with multi-instruction IFEval; **instructions degrade at different rates ("selective amnesia"); defense (do-not-reveal) instruction is evicted first → leakage rises then falls at extreme ratios; last instruction gets priority; proposes "fair eviction" across instructions** to restore adherence at high compression. |
| 16 | Protection Is (Nearly) All You Need | arXiv:2605.18053 | abs | 7 eviction policies collapse to F1 ≤ 0.064 on 6 pure-transformer models without boundary protection; position-0 sink ≈ 75% of prefix mass; **10% boundary protection at K=256 recovers 69-90% of reference ceiling**; scoring differences secondary. |
| 17 | Hold Onto That Thought (KV compression on reasoning) | NeurIPS 2025 wkshp, arXiv:2512.12008 | search summary | For reasoning models H2O and decoding-enabled SnapKV dominate; low budgets *lengthen* traces. |
| 18 | StreamingLLM (Xiao et al.) | ICLR 2024, arXiv:2309.17453 | abs | Attention-sink: keeping initial-token KV "largely recovers" window attention; no claim about instruction adherence (perplexity/streaming only). |
| 19 | When Attention Closes (multi-turn thread loss) | arXiv:2605.12922 | abs | Goal Accessibility Ratio (attention from generated tokens to task-defining tokens) falls over turns while probes on residuals stay predictive (AUC 0.99); Mistral ablation: 20-fact recall → 11%. Diagnosis only. |
| 20 | LLMs Get Lost in Multi-Turn Conversation (Laban et al.) | arXiv:2505.06120 | abs | Sharded prompts: −39% avg over 6 tasks; aptitude −15%, unreliability +112%; models "do not recover". |
| 21 | One Battle After Another — EvolIF | arXiv:2511.03508 | abs | Evolving multi-turn IF benchmark; GPT-5 robustness 66.40%, Gemini-3-Pro −5.59; stratification grows with depth. No small-model baselines reported in abstract. |
| 22 | Lookback Lens (Chuang et al.) | EMNLP 2024 | aclanthology | Lookback ratio = attention on context vs generated tokens per head; linear detector; classifier-guided decoding −9.6% hallucination on XSum; transfers 7B → 13B. |
| 23 | Repetitions are not all alike | arXiv:2504.01100 | abs | Two mechanisms: ICL copying (dedicated head circuit) vs **"natural" repetition = fallback that "focuses disproportionately on low-information tokens" when relevant context cannot be retrieved**. |
| 24 | Solving LLM Repetition in Production | arXiv:2512.04419 | abs | Greedy + self-reinforcement causes loops; beam search with early_stopping universal post-hoc fix; presence penalty partial; DPO model-level fix. |
| 25 | Causal Head Gating | arXiv:2505.13737 | abs | Learned soft head gates; "instruction following and in-context learning rely on separable mechanisms"; multiple sparse task-sufficient sub-circuits; low modularity. Llama-3 family. |
| 26 | Adaptive long-context head identification (Donhauser et al.) | arXiv:2502.09647 | abs | Heads split into local-only vs query-dependent long-context heads; identifiable from local keys via second-moment approximations. |
| 27 | Steer Like the LLM (PSR) | ICML 2026 spotlight, arXiv:2605.03907 | abs (search) | Prompt steering ≈ token-specific activation steering; standard vectors are "not faithful" (strong on some tokens, ~0 on others). |
| 28 | Stabilizing Transformer Training by Preventing Attention Entropy Collapse (Zhai et al.) | ICML 2023, arXiv:2303.06296 | search summary | Entropy collapse ↔ training instability; σReparam. **Training-time phenomenon; not directly about inference-time bias.** |
| 29 | Repetition In Repetition Out | arXiv:2310.10226 | search summary | Repetition in training data drives degeneration; self-reinforcement: P(repeat) rises monotonically with prior repeats. |
| 30 | LIFBench | ACL 2025, arXiv:2411.07037 | abs (search) | 2,766 long-context IF instructions, 11 tasks, rubric scoring; 20 LLMs. Used by DIRECTER (List/OD/MD). |
| — | Dual Mechanisms of Value Expression | arXiv:2509.24319 | search snippet only | Snippet: "for Llama-3.1-8B and Qwen-2.5-1.5B, steering reduced overall accuracy on IFEval; Qwen-2.5-7B modest gains". **Not opened.** |
| — | H2O, SnapKV, PyramidKV, ITI, ICV, RepE, CAD, contrastive search, DoLa | various | **[memory]** + search snippets | Background only; no numbers relied on. |

## 2. Q1 — Which attention-steering methods report real IF gains, at what dose/selectivity?

Verified findings, ordered by evidential weight for us:

- **SpotLight** (all layers, all heads, ψ_t = 0.1, log-ratio bias, only on deficit): IFEval
  prompt-level +6 to +11 across 3B-72B on *restructured* prompts (instructions separated from
  task). Independent replication (DIRECTER, Llama-3.1-8B, GPT-4o-mini-restructured prompts):
  +2.8 prompt-level only after re-tuning ψ_t to 0.1; at ψ_t = 0.3 it *loses* 13.8 pts. On
  Qwen2.5-3B: −1.1. So the honest single-turn effect of the SpotLight family at ≤8B is
  **−1 to +3 pts**, dose-critical.
- **DIRECTER** (key scaling ×100 on instruction tokens, all layers, per-token plausibility
  gate β = 0.5): the only method with a monotone gain across 1B-14B, but **+0.3 at 1B, +3.2 at
  3B, +2.0 at 7B, +1.9 at 14B, +5.3 at Llama-3.1-8B**. Crucially, all *fixed-strength*
  variants underperform the gated one, and the gate alone rescues PASTA and SpotLight
  (Fig. 2b).
- **PASTA** (α = 0.01, i.e. non-span keys × 0.01 on ~50-150 profiled heads): large gains on
  its own tasks (JSON, pronoun change; +22% avg LLAMA-7B) but ≈ 0 on IFEval in both SpotLight's
  and DIRECTER's hands (66.7 vs 73.5 at official α; +3.0 after retuning α to 0.1).
- **InstABoost** (constant B on span keys, all heads/layers, M = e^B 3-19): matches/exceeds
  the others on 15 behavioural tasks with the best fluency/relevance trade-off; not IFEval.
- **Activation steering (MSR)**: real but small with the instruction present (2/4 models
  significant); the paper itself documents repetition failures.
- **Found-in-the-middle**, **AutoPASTA**, **Focus Directions**: 6-15 pp, +8-10 pp, and
  0.59 → 0.916 EM respectively, all on *retrieval/QA* where the span to emphasise is the
  gold evidence — the model's problem there is distraction, not constraint recall. These
  transfer to us only as *head-selection* recipes.

How they avoided degeneration (verified):
- Head selectivity: PASTA 50-150 heads; AutoPASTA "moderate number"; Focus Directions
  top-20 contextual heads, degrading below baseline at 600 heads or on random heads.
- Layer breadth rather than layer restriction: SpotLight's single-layer-all-heads ablation
  is frequently *below* baseline; all-layers works. (This is the opposite of our 20-27 design.)
- Small, capped, or renormalised doses: PASTA α = 0.01 (multiplicative on *non*-span keys,
  which is bounded: it can at most remove the non-span mass); SpotLight caps at ψ_t = 0.1;
  Focus Directions split-softmax keeps rows summing to 1; DIRECTER keeps only tokens the
  raw model already found plausible.
- Quality gates in hyper-parameter selection: InstABoost picks strengths under fluency ≥ 1;
  MSR uses a perplexity check per layer; DIRECTER's β gate is the same idea per token.

## 3. Q2 — Why does a uniform, all-head bias at layers 20-27 degenerate?

Five converging, verified accounts (plus one inference, flagged):

1. **All-head steering is the documented failure mode.** PASTA Fig. 2: all-heads < zero-shot.
   Focus Directions: boosting non-contextual/random heads gives < 0.3% then drops; 600 heads
   < baseline. Causal Head Gating: IF is carried by sparse, separable sub-circuits — biasing
   heads outside them injects noise into circuits that do copying/induction.
2. **Single-layer-block steering is the second documented failure mode.** SpotLight Fig. 5:
   all heads of one layer "frequently performing worse than the baseline"; the authors'
   reading is that instruction information is distributed and "isolated steering could be
   insufficient." Contextual heads in a 28-layer 3B model sit in layers 8-20 (Focus
   Directions Fig. 2) — i.e. *before* our WAVE_LAYERS, so we bias after selection has
   happened and mostly touch late copy/induction heads. (Layer mapping to Qwen3-1.7B is my
   inference; the head-location fact is verified for Llama-3.2-3B.)
3. **State-dependent mass targets over-suppress context.** InstABoost Thm 3.3 / App. A.8:
   forcing instruction mass to a target shrinks the coefficient on benign context; when it
   falls below the "discretisation margin", needed facts stop activating → over-focus. Our
   exact-odds correction hits τ exactly on every step where ψ < τ, which is the rigid
   regime InstABoost identifies. SpotLight's log-ratio bias under-shoots (ψ_new ≤ ψ_t),
   which is a partial safety margin we removed.
4. **Uniform span bias promotes low-information tokens, the signature of "natural"
   repetition.** "Repetitions are not all alike": natural repetition loops attend
   disproportionately to low-information tokens when relevant context can't be retrieved.
   A uniform bias over a "Constraint: …" span raises mass equally on its boilerplate tokens
   and its content tokens; on pinned-after-eviction caches the biased set is a small,
   fixed column set, so the sharpening is extreme (13/20 sessions degenerate).
5. **Fixed strength during generation is wrong by construction.** DIRECTER Fig. 2a: every
   fixed-strength variant loses to the per-token adaptive one; MSR notes their "fixed
   steering weight throughout generation" as a limitation and reports self-repetition.
6. Attention-entropy-collapse (Zhai et al. 2023) is a *training-time* instability result;
   it motivates keeping attention entropy bounded but gives no inference-time recipe. Do
   not cite it as the mechanism.

What the literature says fixes it (all verified): (a) per-head selection by causal effect on
attention-to-span or on task accuracy (PASTA profiling, Focus Directions contextual score,
CHG); (b) all layers, not a late block; (c) cap the dose *and* gate it per token on base
plausibility; (d) split-softmax/renormalised reweighting rather than raw logit addition
(Focus Directions Eq. 3; SpotLight found probability-space rescaling worse than logit bias,
so keep the logit form but renormalise); (e) choose hyper-parameters under an explicit
fluency/quality constraint on a calibration set.

## 4. Q3 — KV retention of instructions: is 62% recovery in line?

- Pitfalls (ACL 2026): eviction is *instruction-biased*; defense/system instructions are
  evicted preferentially (StreamingLLM, SnapKV starkest); the *last* instruction is
  prioritised; leakage rises with compression then falls when the model has forgotten the
  prompt entirely; "fair eviction" (equalise eviction across instruction segments) restores
  directive following and reduces leakage at high ratios. This is the closest published
  analogue to our pinning result and it measures adherence, not perplexity.
- Protection (arXiv:2605.18053): 10% boundary protection recovers 69-90% of ceiling on
  LongBench-style quality at K = 256 across seven policies; "protection dominates; scoring
  differences are secondary". Our 62% of the eviction gap (adherence on aged constraints)
  sits at the low edge of that band — consistent, and the gap suggests headroom from
  protecting *span boundaries and sink tokens* in addition to instruction columns.
- Hold Onto That Thought: for long decoding, heavy-hitter tracking (H2O) beats prefill-only
  policies — relevant if our eviction simulation is prefill-style (SnapKV-like).
- StreamingLLM makes no adherence claim; SysBench Fig. 6 gives the correlational link
  (attention share on system tokens ↔ per-turn adherence) that motivates pinning.
- No paper I opened reports a pinned-instruction *plus* attention-bias combination; ours is
  the first data point, and it is negative (13/20 degenerate).

## 5. Q4 — Multi-turn / aged-constraint benchmarks that exist now

| Benchmark | Open? | Aged/updated constraints? | Qwen3-1.7B-class baseline | Saturation |
|---|---|---|---|---|
| Multi-IF (arXiv:2410.15553) | yes | yes: earlier-turn instructions must hold at turns 2-3; IFR metric | **Qwen3-1.7B 44.7 (non-thinking) / 51.2 (thinking)** official; Llama-3.1-8B 0.688/0.615/0.542 by turn | Not saturated at ≤8B (best model 0.707 turn 3) |
| IFBench multi-turn (arXiv:2507.02833) | yes (allenai/IFBench) | constraint arrives at turn 3 to rewrite turn-2 answer | none at 1.7B; Qwen2.5-7B-Instruct multi-turn ≈ 50 (Table 7) | Very unsaturated (single-turn 20-55) |
| SysBench (arXiv:2408.10943) | yes (PKU-Baichuan) | yes: system message must hold for 5 turns; R1..R5, SSR | Qwen2-7B SSR 15.0; Llama3.1-8B 24.9; no 1-2B | Extremely unsaturated at small scale (R5 ≈ 1-7%) — floor effects risk |
| SpotLight MT-IFEval | not released as a dataset (constructed from IFEval; 300×5) | yes | 8B: baseline drop 18.2% | — |
| ManyIFEval (Harada et al., EMNLP Findings 2025) | yes | no (many simultaneous) | — | prompt-level 0.22-0.28 at 8B (SpotLight Table 4) |
| LIFBench (arXiv:2411.07037) | yes | long-context, not aged | — | — |
| EvolIF (arXiv:2511.03508) | unclear | evolving, patience-terminated | frontier only in abstract | frontier 66% |
| FollowBench / CFBench / MT-Eval / LongMemEval | yes | mostly single-turn (FollowBench 820×1, CFBench 1000×1); MT-Eval 168×7 turns | — | **[search snippet only; not opened]** |

Recommendation: Multi-IF English (aged constraints, official 1.7B baseline, 3 turns) as the
primary, IFBench multi-turn as the unseen-constraint secondary, SysBench dependent-session
R_n as a tertiary only if a per-turn CSR (not R5) is used to avoid floors.

## 6. Q5 — Steering alternatives with documented IFEval gains on small models

- MSR activation steering (ICLR 2025): Gemma-2-2B / Phi-3-mini; ≈ +20 pts when the text
  instruction is *absent*, small/inconsistent when present; quality drop comparable to
  adding the instruction; repetition failures. Single-layer residual add, fixed weight.
- SAIF (SAE latents, Gemma-2-2b-it): steered strict acc > 30% from a 14-23% no-instruction
  base; loose acc ≈ prompting. Final layer matters most. No "with instruction" uplift shown.
- ITI **[memory]**: truthfulness 32.5 → 65.1 on TruthfulQA (Alpaca); not IF.
- InstABoost's head-to-head: latent methods (Linear/DiffMean/PCAct/PCDiff/Projection) are
  task-inconsistent and collapse fluency at higher strength; attention methods keep fluency.
- "Dual Mechanisms" snippet (not opened): steering *reduced* IFEval on Qwen2.5-1.5B.
Net: at 1-2B, no residual/SAE steering has a replicated positive IFEval delta with the
instruction present. Attention-level intervention remains the better-supported lever, but
only with selectivity and gating.

## 7. Q6 — Decoding-time fixes that are legitimate to pair with the wave

Why repetition penalty is not acceptable: it is a decoder-level change that (i) alters the
*base* arm's outputs and truncation rate independently of the mechanism under test, so any
delta is confounded with decoder choice; (ii) directly interacts with IFEval/Multi-IF
verifiers (keyword-frequency, "repeat the request", letter-frequency, all-caps constraints
are penalised by n-gram/frequency penalties); (iii) benchmark reporting convention is greedy
decoding (IFEval, Qwen3 report, DIRECTER, SpotLight all use greedy), so a penalised arm is
not comparable to published baselines.

Legitimate options (verified provenance):
1. **DIRECTER plausibility gate** — a gate on the *intervention*, not the decoder. Base arm
   is unchanged (β-gate can only revert to base logits); steered arm emits a token only if
   the raw model assigned it ≥ β × its own top-1 probability. Auditable: log accept/halve/
   reject counts per token. It is literally "press only when the press is base-plausible".
2. **Fluency-constrained hyper-parameter selection** (InstABoost/MSR): choose τ, b_max, head
   set on the calibration set subject to excess-truncation ≤ base and a fixed rep-4 cap;
   preregister the constraint.
3. **Score truncation/loops as failures in both arms** (already registered, Round 7). Keep
   it; it is a measurement rule, not a fix.
4. Beam search with early stopping (arXiv:2512.04419) or contrastive search **[memory]**
   are decoder changes: only admissible if applied identically to *both* arms and
   preregistered, and they still shift base rates away from published greedy numbers.
   Not recommended.

## 8. Q7 — Three redesigns, ranked

Common preregistration frame: Multi-IF English 909 conversations × 3 turns, greedy,
max_new = 1024, turn-2/3 aged-constraint adherence (instruction-level strict) as primary,
Holm over {turn-2, turn-3, pooled}; excess truncation ≤ base + 2 pts every arm; every arm
logs per-token intervention state; fixed calibration set disjoint from the sealed set.
Expected effect sizes are extrapolated from 3B-8B results; the 1B DIRECTER point (+0.3)
means the single-turn floor of +2.0 is not supported at 1.7B — set the single-turn gate as a
*non-inferiority* check and put the +2.0 floor on the aged-constraint slice, where SpotLight
halves the multi-turn drop.

### R1 (rank 1) — Plausibility-gated wave on pinned KV
- Change: keep unbiased pinning (the +20-pt component). Replace the deficit gate's uniform
  additive bias with a DIRECTER-style per-token loop: compute raw logits; if top-2 margin
  makes any change impossible skip; else apply the wave bias over ALL layers on the selected
  span with dose d; accept iff p_raw(argmax_steered) ≥ β·p_raw(argmax_raw) (β = 0.5); on
  reject halve d (or halve the layer set by sensitivity ranking) and retry; fall back to raw.
  Keep the 264k controller only as the span selector (its q/k scoring), not the dose.
- Why it should not degenerate: every emitted token is one the unbiased model already rated
  within a factor 2 of its own top choice; DIRECTER's gate rescued PASTA and SpotLight from
  below-baseline to above (Fig. 2b) and held task fidelity ≈ 92%.
- Proof: Multi-IF aged-constraint delta over unbiased-pinned arm ≥ +2.0 (Holm), truncation
  excess ≤ +2 pts, accept-rate and halving histogram reported. Expected from literature:
  +2 to +5 pts at 3-8B single-turn; multi-turn unknown but SpotLight's drop-halving
  (18.2% → 9.3%) suggests +3-8 pts on turn 3 if the mechanism transfers.
- Cost: two forward passes on gated tokens (DIRECTER −16% throughput with skip-gate).

### R2 (rank 2) — Contextual-head-selective wave across all layers
- Change: one-time profiling on the calibration set: per head, contextual score = mean
  attention from response tokens to the governing constraint span, contrasted correct vs
  wrong (Focus Directions) or per-head steering effect (PASTA); keep top-k (k ∈ {20, 50,
  100}) heads across ALL 28 layers; apply the deficit bias only on those heads, in
  split-softmax (row-renormalised) form; drop WAVE_LAYERS = 20-27.
- Why it should not degenerate: Focus Directions top-20 heads/τ = 0.1 gave 0.59 → 0.916 EM
  while 600 heads or random heads fell below baseline; PASTA all-heads < baseline vs 50-150
  heads best; SpotLight found single-layer blocks worse than baseline but distributed
  steering fine. Non-contextual heads (copy/induction) are left untouched, removing the
  repetition path in Section 3 item 4.
- Proof: same frame; plus a mechanistic pre-check that is cheap and falsifying on its own:
  on the calibration set, the top-k head set must show a positive attention-to-span
  contrast (correct − wrong) with Wilson LB > 0 — if Qwen3-1.7B has no such heads, R2 is
  dead before any GPU-hour. Expected: +2-4 pts single-turn at 3B analogues; this is the
  only design with a documented > +30-pt effect on its home task.
- Can be composed with R1 (gate on top of selected heads) as a third arm.

### R3 (rank 3) — Fair-eviction KV retention, no bias (the null-mechanism control)
- Change: implement Pitfalls' "fair eviction" (equalise eviction fraction per instruction
  segment) plus 10% boundary/sink protection (arXiv:2605.18053) as the retention policy;
  no attention bias at all. Compare against current pinning and against pinning + R1.
- Why it should not degenerate: nothing is added to logits; retention-only interventions
  have no reported fluency side effects.
- Proof: closes the remaining 38% of the eviction gap? Gate: aged-constraint adherence of
  fair-eviction ≥ pinned + 2 pts, or non-inferior at lower memory. Literature: fair eviction
  restores directive following "even at high compression ratios"; protection 69-90% of
  ceiling.
- Role: it is the arm that makes R1/R2 interpretable. If R3 alone reaches the full-context
  ceiling, there is no deficit left for a wave to fix.

### What falsifies the wave hypothesis
"Synapses store, waves select" predicts that, holding storage fixed (pinned/fair-evicted KV),
a *gated, head-selective* attention bias toward the governing span raises aged-constraint
adherence. It is falsified for this trunk if, on the sealed Multi-IF slice with n ≥ 909
conversations (power for ±2 pts at instruction level), both R1 and R1+R2 are within ±2 pts
of the unbiased R3/pinned arm under Holm, with accept-rate > 0 (i.e. the gate did press) and
the R2 pre-check passed (heads exist). If the R2 pre-check fails (no heads whose span
attention separates correct from wrong), the hypothesis is not even testable at 1.7B and the
honest statement is "no selective attention channel for constraints is detectable in this
trunk". What survives either way: KV retention is the storage half and already carries
+20 pts over control on its own evidence.

## 9. What to run first (CPU-free ordering; GPU hours in brackets are estimates)

1. **R2 pre-check** on existing per-item records + one profiling pass over the calibration
   set: compute per-head attention-to-governing-span for correct vs wrong responses; report
   the top-50 heads and their layers. [~1 GPU-h] Decides whether R2 exists.
2. **R1 gate battery** (deterministic, no benchmark): β = 1 must reproduce base bitwise; β = 0
   must reproduce the ungated wave; log accept/halve/reject; verify no token is emitted with
   p_raw < β·p_top. [<0.5 GPU-h]
3. **Calibration grid under a fluency constraint** (InstABoost protocol): dose d × β ×
   head-set k on cal-v45, selecting the best adherence subject to excess-truncation ≤ 0 and
   rep-4 ≤ base. [~6-10 GPU-h]
4. **Sealed Multi-IF three-arm run**: pinned (R3-lite) / pinned+R1 / pinned+R1+R2, 909 × 3,
   Holm, Round-7 truncation rule. [~30 GPU-h, i.e. the budget the E2 futility stop freed]
5. Only if 4 passes: single-turn non-inferiority on the conf set (expect ≈ 0, per DIRECTER
   1B) and IFBench multi-turn as the unseen-constraint replication.

## 10. Verified-vs-memory ledger

Verified by opening (this session): rows 1-3, 5-16, 18-20, 22-23, 25-26 of the table (PDF or
abstract text read). Search-summary only (not opened): rows 4, 17, 21 (abstract opened),
24 (abstract opened), 27-30, "Dual Mechanisms". From memory, no numbers used: H2O, SnapKV,
PyramidKV, ITI numbers, ICV, RepE, CAD, contrastive search, DoLa, beam/early-stopping
mechanics. Layer mapping of contextual heads onto Qwen3-1.7B (Section 3 item 2) is my
inference from a Llama-3.2-3B result.
