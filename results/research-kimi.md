# Deep research — kimi-k3, no web access (2026-09-02)

# Stencil deep research report — making the wave mechanism move benchmarks

**Scope and verification note (read first).** I have no web access in this session. **I have not opened any URL.** Every citation below is `[from memory]`; I give arXiv IDs so a colleague can verify. Confidence tags per claim: **[high]** = I'd bet on the ID and the headline number; **[med]** = ID/number approximately right, verify; **[low]** = existence/plausibility only. Where I genuinely cannot verify a title (several items in the brief list are things I cannot match to a paper I know), I say so rather than invent an ID. Effect sizes I'm unsure of are marked `(?)`.

One honest headline up front: **to my memory, no published paper reports IFEval/IFBench/Multi-IF/FollowBench gains from attention-reweighting interventions.** The documented gains from this mechanism family are on adjacent tasks (bias elicitation, long-context retrieval, TruthfulQA). The IF-family gains in the literature come from (a) data (Tülu-3 IF-augmented, Conifer), (b) RLVR (IFBench/IF-RLVR), and (c) one activation-steering paper (Stolfo et al.). That should calibrate expectations below.

---

## RQ1 — Attention steering/re-weighting: what's actually documented

### Verified-from-memory inventory

| Method | What it does | Documented task gains | IF-family gains? | Degeneration handling |
|---|---|---|---|---|
| **PASTA** — "Tell Your Model Where to Attend: Post-hoc Attention Steering for LLMs", Zhang et al., ICLR 2024, arXiv **2311.02211** [high] | Profile a **small subset of heads**, add attention-score boost on user-marked token spans at **prefill**, renormalize | BiasAsker stereotype-rate reduction (large, `?`); LLaMA-7B reasoning/QA gains single-digit pts `(?)` | **None** [high] | Head-selectivity *is* the design; they report non-monotonic dose-response — over-steering hurts [med] |
| **AutoPASTA** — Chen(?) et al., 2024, arXiv 2406.x — ID needs verification [low] | Automates head/span selection via an optimization objective | Same task families as PASTA `(?)` | None known | Automated selection to keep dose minimal `(?)` |
| **"Found in the Middle"** — Hsieh et al., ACL-findings(?) 2024, arXiv **2406.16008** [med] | Estimate **positional** attention bias, *multiply* attention by inverse positional weight (calibration), conservative/bounded | Mid-position long-doc QA gains, up to ~10+ pts on worst positions `(?)` | None | Multiplicative + bounded factors; no degeneration reported `(?)` |
| **"Attention Instruction: Amplifying Attention in the Middle via Prompting"** — 2024, arXiv **2406.17095** [med] | Append an "attend to X" pseudo-instruction (prompting only, no logits) | LLaMA-2-70B long-doc gains, sometimes large `(?)` | None | Prompting — structurally incapable of degeneration-by-bias |
| **RE2 re-reading** — Xu et al. 2023, arXiv **2309.06275** [med] | "Read the question again" prompt suffix | Reasoning benchmarks, +1–3 pts `(?)` | None | n/a |
| **StreamingLLM** — Xiao et al., ICLR 2024, arXiv **2309.17453** [high] | Keep sink tokens + sliding window | Enables streaming; *removing* sinks → pplx explosion [high] | None | Inverse lesson for us: sinks are load-bearing |
| **Lost in the Middle** — Liu et al. 2023, TACL 2024, arXiv **2307.03172** [high] | Diagnostic only | — | None | U-shaped attention/perf curve |
| **CAD (context-aware decoding)** — Shi et al., NAACL 2024, arXiv **2305.14735** [high] | Contrastive decoding w/ vs. w/o context | Hallucination↓, knowledge-conflict QA↑ | None | Adaptive weighting; fluency preserved at tuned α `(?)` |

### Items in the brief I cannot match to a real paper
- **"Attention buckets"** — no arXiv paper by this name that I can verify [low]. Possibly confusion with StreamingLLM's window+buckets or RoPE boundary work ("Base of RoPE Bounds Context Length", arXiv 2405.14591 [low]).
- **"LLMs are not robust to buried instructions"** — I cannot verify this title [low]. Closest canonical references: Lost-in-the-Middle (2307.03172) and Attention Instruction (2406.17095). There is prompt-injection literature (e.g., "Ignore This Title…", arXiv 2403.14781 [low]) but it's adversarial, not adherence.
- **"SPA"** — ambiguous [low]. Could be "Selective Prompt Anchoring" (I recall a ~2024 preprint on amplifying user-prompt attention during generation; cannot verify ID) or something else entirely. Flag for a real search.
- **AutoPASTA arXiv ID** — I won't invent digits; EMNLP-2024-era, search the title.

### The consistent anti-degeneration design pattern across the ones I *can* verify
1. **Head-selective**: single-digit numbers of heads, found by profiling or causal methods, not all-head.
2. **Prefill-time or step-gated**, not every step unconditionally.
3. **Renormalize** post-softmax so total mass is preserved.
4. **Span-subset**: boost the few load-bearing tokens (entities, constraint keywords), not every token in the instruction.
5. **Small effective mass shift**: the documented successes move span mass modestly; every paper's dose sweep shows a peak-then-degrade curve.

Your mechanism violates 1, 2, 4, and 5 simultaneously (uniform over span, all heads, layers 20–27, exact-odds correction ⇒ effective gain ≈ 1/p which is 10–100× when natural mass ≪ τ). The sealed-set result (+0.39, 4× truncations) is exactly what this literature's dose-sweep tails look like. That's [my inference from the verified pattern], not a single citable experiment.

---

## RQ2 — Why does uniform all-head late-layer bias degenerate?

The literature gives three converging mechanistic accounts:

**(a) You've manufactured a second attention sink.** Boosted key columns absorb mass exactly like the positional sinks in StreamingLLM (2309.17453) [high]. Massive activations concentrate on sink tokens (Sun et al., "Massive Activations…", arXiv 2402.17762 [med-high]); sink dynamics are studied empirically in Gu et al., "When Attention Sink Emerges…", arXiv 2410.10781 [med]. A forced sink *mid-sequence* starves the heads doing local structure/induction in the generation region. **[This specific consequence — artificial mid-sequence sink from bias — is my inference, not a documented result I can cite.]**

**(b) Copy/repetition via over-attention on already-seen text.** Induction/copy heads (Olsson et al., "In-context Learning and Induction Heads", arXiv 2209.11895 [med-high]) boosted indiscriminately increase verbatim-copy probability of the very instruction span you're boosting → restating constraints, then loops. Overconfident, low-entropy distributions produce degenerate repetition loops under greedy decoding (Holtzman et al., "Curious Case…", arXiv 1904.09751 [high]; unlikelihood analysis: Welleck et al., arXiv 1908.04319 [high]). Attention-entropy collapse specifically is linked to instability by Zhai et al., "Stabilizing Transformer Training by Preventing Attention Entropy Collapse" (σReparam, arXiv 2303.06296 [med]) — training-side, but the entropy-collapse → pathology link transfers.

**(c) Softmax nonlinearity amplifies "exact odds correction" beyond calibrated doses.** When natural mass p ≪ τ, odds-correction multiplies logits by log(τ(1−p)/p(1−τ)) — routinely several logits' worth. After renormalization this is an absolute mass shift the PASTA-line papers never attempt.

**Documented mitigations** (each verified above): probe/causally select K heads (ITI 2306.03341 [high]; Function Vectors, Todd et al. 2310.15213 [med]; Patchscopes, 2401.06102 [med]); cap the post-shift span mass; restrict tokens; keep deficit gating but add a **dose ceiling** independent of τ.

**Cheap autopsy to distinguish (a)/(b)/(c) on your 12 truncations [my recommendation, not a citation]:** check whether truncations are repetition-loop budget exhaustion (favors (b)) vs. on-topic non-termination; measure per-head attention entropy at layers 20–27 with bias on/off (favors (a)/(c) if entropy collapses broadly, favors selective-head fix if collapse is uniform).

---

## RQ3 — KV retention of instructions under pressure

| Method | ID [conf] | What it measures | Adherence of retained instructions measured? |
|---|---|---|---|
| H2O (heavy-hitter eviction) | 2306.14048 [high] | PPL + downstream QA/summarization | **No** [med-high] |
| SnapKV | 2404.14469 [high] | LongBench, near-full-KV at ~5–15% budget `(?)` | No |
| PyramidKV | 2406.02069 [med] | LongBench; comparable at ~10% budget `(?)` | No |
| Ada-KV (adaptive per-head budget) | 2407.11550 [med-low] | LongBench | No |
| Quest / MInference | 2401.06104 / 2407.02490 [med] | Sparse *compute*, full KV retained | n/a |
| Prompt Cache | 2311.04934 [med] | Reuse of attention states for repeated modules | No |
| LLMLingua / LongLLMLingua | 2309.08368 / 2310.06839 [med-high] | **Compression** alternative; QA under 2–6× compression, sometimes *beats* uncompressed `(?)` | Indirectly (QA) |
| Activation Beacon / ICAE | 2401.03462 / 2308.03358 [med] | Soft-token compression of context | No |

**On your 62% figure:** I can't find a published adherence-of-retained-instruction number to compare against — **this looks like a genuine gap, and your +20-pts-over-control pinning result may be one of the first adherence-based retention measurements** [my assessment]. For calibration: retrieval-family tasks on LongBench recover ~90–100% of full-KV performance at 10–20% budgets under SnapKV/PyramidKV `(?)`, but those are retrieval, not constraint adherence, so 62% is not obviously out of line or obviously great. Note the serving-world cheat: if the governing span can live in the *prefix*, automatic prefix caching (vLLM/SGLang) makes retention trivial — so your eval's non-prefix placement of instructions is what keeps it scientifically interesting. Keep it.

---

## RQ4 — Multi-turn / aged-constraint benchmarks that exist now

| Benchmark | ID [conf] | Open? | Aged/updated constraints? | Saturation status from memory | Qwen3-1.7B-class baselines published? |
|---|---|---|---|---|---|
| IFEval | 2311.07911 [high] | ✓ | No (single-turn) | Saturated for frontier, not for 1.7B | Qwen3 tech report (2505.09388, [med]) reports larger-model IFEval; 1.7B unlikely |
| **Multi-IF** (Meta) | 2410.15569 [high] | ✓ (HF) | Turn-level accumulation of IFEval constraints across 3 turns | Turn-3 still discriminative; ~10–20 pt drop turn1→turn3 typical `(?)` | Predates Qwen3 (Apr 2025); Qwen2/Llama-3 baselines exist |
| **IFBench / IF-RLVR** ("Generalizing Verifiable Instruction Following", Pyatkin/Lambert et al., AI2, Jul 2025) | **2507.02836** [med] | ✓ | New held-out constraint types | **Least saturated** — most models <50–60 prompt-strict `(?)` | Not to my knowledge |
| SysBench | 2408.10943 [med-high] | ✓ | System-message constraints re-checked over turns; violation tracking | Medium | No |
| FollowBench | 2310.20410 [med-high] | ✓ | Difficulty-leveled constraints | GPT-4 ~→60% at L5 `(?)`; mid | No |
| CFBench ("Comprehensive Constraints-Following") | 2024; **ID unverified** [low] | ✓(?) | Checklist scoring | Medium | No |
| InfoBench (DRFR decomposition) | 2401.03601 [med-high] | ✓ | No aging; needs LLM judge | Medium | No |
| LongMemEval | 2410.10813 [med-high] | ✓ | Aged *facts* over ~115k-token histories, not constraints | Discriminative | No |
| MT-Bench-101 | 2402.14762 [med] | ✓ | No aging focus | Medium | No |
| "LLMs Get Lost in Multi-Turn Conversation" (Laban et al. 2025) | 2505.06120 [med-high] | ✓ | Sharded instructions across turns; avg ~**39%** performance drop multi vs. single-turn `(?)` | Fresh | No |
| ManyIFEval / StyleIFEval (≤10 simultaneous constraints) | Sakana AI, 2025, blog+code, **no arXiv ID verified** [low] | ✓(?) | Constraint-count scaling | Fresh; explicitly designed for small-model headroom | Unknown |

**Recommendation:** primary = **Multi-IF turn-2/3** (your base already truncates there — real defect, real headroom) + **IFBench** for generalization; **SysBench** is the best off-the-shelf *aged-constraint* match to your ledger design. All are open; Qwen3-1.7B numbers will be new, which is fine — publish base+arm pairs.

---

## RQ5 — Activation/steering alternatives with documented IF-family gains

| Method | ID [conf] | Documented effect | Degeneration profile |
|---|---|---|---|
| **Stolfo et al., "Improving Instruction-Following in Language Models through Activation Steering"** | **2410.12877** [med-high] | **IFEval gains on open models** via residual-stream "instruction-following direction" from contrast pairs; per my memory, single-digit-point gains on 7B-class models `(?)` — verify exact numbers | Coherence/fluency degrade at large α; fine at tuned α `(?)`; they sweep α and report the tradeoff |
| ITI | 2306.03341 [high] | TruthfulQA 32.5→65.1 on LLaMA-7B [med-high] | Mild at tuned α; fluency loss at high α; head-selective (top-K by probe) |
| Refusal direction (Arditi et al.) | 2406.11717 [high] | Single-direction erasure/addition works on ~13 open models | Minimal side effects at matched norm |
| Representation Engineering (Zou et al.) | 2310.01405 [high] | Honesty/utility control vectors | Documented off-topic/style drift at strong control magnitudes |
| In-context vectors | 2311.06668 [med-high] | ICL task vectors, transfers, controllable | Minor `(?)` |
| Function vectors (Todd et al.) | 2310.15213 [med-high] | Head-derived task vectors causally trigger ICL tasks | — |
| SAE steering | Gemma Scope 2408.05147 [med-high]; Scaling Monosemanticity (Anthropic, May 2024, transformer-circuits, no arXiv) [high] | Feature clamping steers behavior (Golden Gate demo) | **Documented coherence collapse at strong clamps** |
| **"Direct Instruction Steering"** | — | **Cannot verify** [low] | — |

**Bottom line:** exactly one memory-verified paper (Stolfo) shows IF-specific steering gains, with a degeneration profile that is *quantified and controllable*, which is more than the attention-bias literature offers for IF. That's the strongest adjacent precedent for a redesign.

---

## RQ6 — Decoding-time fixes: what's legitimate next to the wave

**Why repetition penalty (or frequency/presence penalties) is an illegitimate co-intervention here:**
1. It manipulates the degeneration endpoint directly — any truncation/repetition change becomes unattributable to the wave. Both arms get it ⇒ still confounded by **interaction** (the wave arm generates more penalty-triggering repeats, so its distribution is warped more).
2. It's **double-edged on the primary metric**: many verifiable constraints require verbatim repetition (quoted text, "repeat the prompt", keyword counts). A penalty degrades exactly the constraints the wave is supposed to help — a two-direction confound.
3. It's global and serving-dependent, so results don't transfer.

**Legitimate alternatives, ranked by cleanliness:**
1. **Fix the budget artifact first.** Your Multi-IF base truncates 10% at max_new=1024. Moving to 2048/4096 and reporting completion rate is **measurement hygiene, not an intervention** — validators are mostly length-agnostic. Do this before any mechanism claim.
2. **Constrained decoding for the formalizable subset** (Outlines 2307.09715 [med]; llguidance 2411.15147 [med]; SGLang 2312.07104 [med]; Synchromesh 2201.11227 [med]): pure token mask + renormalize — provably does not reweight allowed tokens. It would trivially "solve" format constraints, which means it evaluates the *solver*, not the wave: only legitimate as explicitly ablated co-intervention.
3. **No-repeat-n-gram blocking** (Paulus et al. 2017 lineage; standard in HF): deterministic, surgical, minimal distribution shift — but must be applied to both arms, and you should **report blocker-hit rate as an outcome** (if the wave arm hits it more, the wave is still degenerating and you're laundering the symptom).
4. **Mirostat / target-perplexity** (2008.17492 [med]) and **Min-p** (2407.01082 [med]): principled anti-loop decoding, but global — same confound concerns as penalties, milder. Not recommended for a mechanism paper.
5. **Post-hoc loop-breaker** (detect cycle → truncate → one retry) with retry rate reported as a metric.

**Root-fix preference:** the honest fix is to scope/cap the bias so degeneration doesn't occur; decoding patches treat the symptom and invite exactly the reviewer objection this brief anticipates.

---

## RQ7 — Three ranked redesigns (with gates and falsifiers)

### #1 — "PASTA-in-Stencil": head-selective, token-subset, capped-dose wave (highest priority)
**What changes:** (i) find 3–10 heads across layers 20–27 by **causal patching** (Patchscopes-style) on deficit trials, ranked by causal effect on constraint-relevant token logprob; (ii) apply pre-softmax additive bias to only those heads; (iii) boost only **verbatim constraint tokens** (the ledger's load-bearing spans), not whole instructions; (iv) keep deficit gating but **cap post-shift span mass** (e.g., ≤2× natural, hard ceiling ~0.10–0.15 absolute) and renormalize.
**Why it shouldn't degenerate:** every documented success in RQ1 uses exactly this quadruple (selective heads, subset tokens, prefill/gated timing, renormalization); every documented failure looks like your current design.
**Benchmark + preregistered gate:** Multi-IF turns 2–3, English, with KV pinning ON as the constant background; primary = prompt-level strict accuracy on aged constraints; paired bootstrap, gate **+2.5 pts with p<0.05** and non-inferiority on truncation/repetition (Δ ≤ +1 pt), fluency guardrail (output pplx under base model ≤ +5%).
*Power check [my arithmetic, not a citation]:* at n=2727 paired binary outcomes with ~25% discordance, MDE at 80% power ≈ 2 pts — well-powered. **Expected effect from literature adjacency: +2–4 pts `(?)`.** PASTA-line papers show this magnitude on targeted span tasks; there is no IF-specific precedent, so this is an extrapolation.

### #2 — Swap the mechanism layer: residual-stream steering vector instead of attention bias (keep ledger + gate)
**What changes:** extract an instruction-following direction (Stolfo-style contrast pairs, or function-vector aggregation), add α·d at mid layers (below your wave band), norm-capped, gated by the same deficit signal.
**Why it shouldn't degenerate:** bypasses softmax renormalization entirely (no manufactured sink, no entropy-collapse channel); degeneration profile is documented and controllable via α sweep.
**Benchmark + gate:** sealed conf set (1024) as secondary, IFBench as primary generalization check; gate **+2 pts strict prompt-level**, non-inferiority on degeneration metrics. **Expected +1.5–3 pts `(?)`** from the one IF-specific precedent.

### #3 — Positional-calibration wave ("Found in the Middle" applied to aged spans)
**What changes:** instead of *adding* attraction, **remove positional bias**: multiplicative, bounded calibration factors estimated per layer/head, applied only when deficit gate fires and only on pinned columns. This is the purest test of "waves select": correct under-attention rather than inject attention.
**Why it shouldn't degenerate:** bounded multiplicative factors are the most conservative documented intervention in this family.
**Benchmark + gate:** must beat **KV-pinning-only control** by ≥ +1.5 pts on aged constraints (this is the incremental-selection-over-storage test). **Expected +1–2 pts `(?)`** — smallest, but highest evidence value per unit risk.

*(Deliberately not proposed: decode-time logit boosts on required keyword tokens or constrained decoding. They'd raise scores but abandon the hypothesis; keep them as the honest "control-line replacement" if all three fail.)*

### Falsification criteria for the wave hypothesis
Your existing results have **already falsified the strong version** (uniform all-head odds-corrected selection) — twice, with two degeneration signatures. The live, weaker hypothesis is "selective micro-dose selection helps where storage is intact." It is falsified if:
- **F1 (diagnostic falsifier, runs first):** on trials where instruction tokens are retained (pinned), natural span attention-mass **does not correlate** with success. Then under-attention was never the bottleneck and no dose reshape can help.
- **F2:** redesign #1 shows **no additive gain over pinning alone** while #2 (representation-space selection) does gain → attention-weight selection specifically is dead at this scale; the Miller framing survives only transposed to feature space.
- **F3:** all three redesigns fail their gates **and** an oracle (forced span mass ≥ τ with perfect scope) also fails → capacity, not selection, is the binding constraint at 1.7B. Close the line; publish the negative with the degeneration taxonomy — that is a citable result nobody else has (nobody has published adherence-of-retained-tokens or wave-degeneration data).

---

## Citation table (all [from memory]; URLs provided for your verification — I opened none)

| Paper | Year | arXiv | [conf] | Key number as I recall it |
|---|---|---|---|---|
| Tell Your Model Where to Attend (PASTA) | 2023/ICLR24 | 2311.02211 | high | Head-selective span steering; non-monotonic dose |
| Found in the Middle | 2024 | 2406.16008 | med | Mid-position gains up to ~10+ pts `(?)` |
| Attention Instruction | 2024 | 2406.17095 | med | +pts on mid-buried QA via prompt only `(?)` |
| StreamingLLM | 2023 | 2309.17453 | high | 4 sink tokens; removal → pplx explosion |
| Lost in the Middle | 2023 | 2307.03172 | high | U-shaped position accuracy |
| IFEval | 2023 | 2311.07911 | high | 25 verifiable constraint types |
| Multi-IF | 2024 | 2410.15569 | high | 3-turn; ~10–20 pt t1→t3 drop `(?)` |
| IFBench/IF-RLVR | 2025 | 2507.02836 | med | Most models <~50–60 strict `(?)` |
| SysBench | 2024 | 2408.10943 | med-high | Turn-wise system-constraint decay |
| FollowBench | 2023 | 2310.20410 | med-high | GPT-4 L1→L5 drop `(?)` |
| LongMemEval | 2024 | 2410.10813 | med-high | 500 Qs over ~115k-token histories |
| Lost in Multi-Turn (Laban) | 2025 | 2505.06120 | med-high | ~−39% aptitude multi vs single `(?)` |
| InfoBench | 2024 | 2401.03601 | med-high | DRFR judge metric |
| H2O | 2023 | 2306.14048 | high | Heavy-hitter eviction; ~20% budget near-lossless `(?)` |
| SnapKV | 2024 | 2404.14469 | high | Near-full-KV on LongBench at small budget `(?)` |
| PyramidKV | 2024 | 2406.02069 | med | ~10% budget parity `(?)` |
| LongLLMLingua | 2023 | 2310.06839 | med-high | Compression can beat original on long-doc QA `(?)` |
| Prompt Cache | 2023 | 2311.04934 | med | Attention-state reuse |
| Stolfo, IF activation steering | 2024 | 2410.12877 | med-high | **IFEval gains via residual-stream direction `(?)`** |
| ITI | 2023 | 2306.03341 | high | TruthfulQA 32.5→65.1 (LLaMA-7B) |
| Refusal direction | 2024 | 2406.11717 | high | Single-direction intervention |
| RepE | 2023 | 2310.01405 | high | Control vectors; high-magnitude drift |
| In-context Vectors | 2023 | 2311.06668 | med-high | ICL compression to one vector |
| Function Vectors | 2023 | 2310.15213 | med-high | Head-derived causal task vectors |
| Holtzman, degeneration | 2019 | 1904.09751 | high | Overconfident decoding → repetition |
| Welleck, unlikelihood | 2019 | 1908.04319 | high | Repetition mechanism+fix |
| Induction heads | 2022 | 2209.11895 | med-high | Copy heads |
| σReparam (entropy collapse) | 2023 | 2303.06296 | med | Entropy-collapse instability link |
| Massive activations | 2024 | 2402.17762 | med-high | Sink-token activation structure |
| Attention-sink empirics (Gu) | 2024 | 2410.10781 | med | Sink emergence conditions |
| CAD | 2023 | 2305.14735 | high | Context-contrastive anti-hallucination |
| Tülu 3 (IF-augmented data) | 2024 | 2411.15124 | high | IFEval ↑ for 8B via data `(?)` |
| Conifer | 2024 | 2404.02823 | med | Complex-if SFT improves IFEval-like metrics `(?)` |
| RE2 | 2023 | 2309.06275 | med | Re-read prompting |
| Patchscopes | 2024 | 2401.06102 | med | Causal inspection/patching |
| Gemma Scope | 2024 | 2408.05147 | med-high | SAE steering resources |
| Scaling Monosemanticity | 2024 | transformer-circuits (no arXiv) | high | Feature clamping; coherence collapse at high dose |
| Outlines / llguidance / SGLang / Synchromesh | 2022–24 | 2307.09715 / 2411.15147 / 2312.07104 / 2201.11227 | med | Mask-based constrained decoding |
| Mirostat / Min-p | 2020/2024 | 2008.17492 / 2407.01082 | med | Anti-degeneration sampling |
| **Unverified (do not cite without search):** AutoPASTA ID; CFBench ID; "attention buckets"; "SPA"; "LLMs are not robust to buried instructions"; "Direct Instruction Steering"; ManyIFEval/StyleIFEval |  |  | low |  |

---

## What to run first (ordered, cheap→expensive)

1. **[Hours] Budget hygiene:** max_new 1024→2048 on Multi-IF; re-report base truncation. Not an intervention.
2. **[Hours] Falsifier F1 diagnostic:** on pinned trials, correlate natural span attention-mass with success. If flat, stop — the wave premise is dead at this scale regardless of redesign.
3. **[Day] Truncation autopsy:** classify the 12 sealed-set truncations (loop vs. truncation shape); per-head attention-entropy at layers 20–27, bias on/off. Tells you which of (a)/(b)/(c) in RQ2 you're fighting.
4. **[1–2 days] Head-finding** by causal patching on deficit trials (feeds redesign #1), and direction extraction (feeds #2), both on a **256-row dev slice you carve from non-sealed data** — do not touch the sealed set until preregistered finals.
5. **[Days] Dose-response with the four scoping constraints** (#1) on the dev slice, degeneration gate enforced *before* moving to Multi-IF.

One-line summary for the project log: *the literature says your mechanism family works only when it is head-selective, token-selective, gated, and mass-capped — every degeneration you saw is a documented tail of the dose sweep — and the one paper with actual IFEval gains from inference-time intervention steered the residual stream, not the attention matrix.*

— kimi-k3