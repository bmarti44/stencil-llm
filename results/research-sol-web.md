# Stencil deep-web research: making the wave mechanism improve benchmark scores

**Research date:** 2026-09-02  
**Scope:** frozen Qwen3-1.7B, CPU-compatible interventions, with the sealed single-turn IFEval-style result treated as closed  
**Bottom line:** the evidence favors changing the wave from an unconditional *attention-amplitude controller* into a constrained *state/route selector*. If a positive attention dose is retained, it should be treated as a small, dynamically rejected perturbation, not as a per-head mass floor.

## Evidence notation and search method

- **[V] Verified-opened:** I opened the primary paper, official paper page, or official technical report and checked the cited claim there. All quantitative literature claims in this report are [V] unless expressly marked otherwise.
- **[R] Registered/local:** supplied in the research brief or checked in the repository's read-only source. These are not claims from the web.
- **[I] Inference:** my calculation or synthesis from [V]/[R] evidence.
- **[M] Memory-only:** recalled but not verified in an opened source. No numeric [M] claim is used to rank the proposals or set a decision threshold.

I opened more than 40 primary paper/report pages, well above the requested 15-source minimum. The citation ledger at the end identifies the sources actually used. I did not use survey snippets or search-result summaries as quantitative evidence. I did not run a model or GPU process, and I made no repository change other than writing this report.

## Executive finding

Three facts should govern the next phase.

1. **The current intervention is substantially stronger than the closest published analogue.** SpotLight adds a bias of \(\log(\tau/\psi)\) when the current span mass \(\psi\) is below target \(\tau\); the Stencil deficit hook uses the exact log-odds correction \(\operatorname{logit}(\tau)-\operatorname{logit}(\psi)\), subject to a cap. SpotLight's update produces

   \[
   \psi' = \frac{\tau}{1+\tau-\psi} < \tau,
   \]

   whereas Stencil reaches \(\psi'=\tau\) whenever the cap does not bind. At \(\psi=.01\), SpotLight's nominal targets .10 and .30 yield actual masses .0917 and .2326; exact correction yields .10 and .30. Stencil then reapplies that floor across layers 20–27. **[I/R]** The operation preserves token ranking *within* a uniformly biased span; its main distortion is rigid mass reallocation between the span and everything else, repeated across heterogeneous heads and layers.

2. **The most relevant published success now includes an explicit rejection mechanism.** Directer tests a tentative instruction intervention, compares the steered and raw next-token distributions, and backs off steered layers when the result leaves a plausibility region. On rewritten IFEval, its Qwen2.5-3B mean rose from 63.9 to 67.1; on Llama-3.1-8B, prompt/instruction scores rose from 73.5/81.5 to 78.8/84.8. Fixed SpotLight and PASTA settings could regress badly, while tuned settings recovered. [Directer, arXiv:2603.06745](https://arxiv.org/abs/2603.06745) **[V]** This is the best direct argument for a trust-region wave, but it is not an untouched-official-IFEval result: Directer rewrote prompts with GPT-4o-mini, and SpotLight likewise used rewritten prompts. That caveat matters.

3. **Availability has stronger evidence than amplification.** Locally, lossless instruction-span pinning recovered 62% of the eviction loss (+20 points), while adding positive bias caused degeneration in 13/20 cases. **[R]** FlowKV, MemDecay, and an ACL 2026 study of cache compression independently show that preserving turn or defense/instruction state can recover large multi-turn losses. This suggests that the current bottleneck under cache pressure is often “the state is unavailable,” not “the surviving state needs more attention.” [FlowKV, arXiv:2505.15347](https://arxiv.org/abs/2505.15347), [MemDecay, arXiv:2607.10582](https://arxiv.org/abs/2607.10582), [Pitfalls of KV-Cache Compression, arXiv:2510.00231](https://arxiv.org/abs/2510.00231) **[V/I]**

The practical recommendation is therefore:

- first, make the ledger control **which active constraints remain losslessly available** and remove stale ones;
- second, if amplitude steering is tested again, add **raw-versus-steered distribution rejection and dose/layer backoff**;
- third, test a **held-out, causal head/layer subset with a bounded mass increment**, not an all-head mass floor.

The sealed single-turn line should stay closed. The next confirmatory endpoint should be clustered, late-turn Multi-IF performance, with truncation/repetition as co-primary safety constraints.

## 1. Attention steering: what has actually improved relevant benchmarks?

### Direct evidence on IFEval or multi-turn instruction following

| Method | Intervention and selectivity | Relevant verified result | Important limitation |
|---|---|---|---|
| **SpotLight** | At each query, if highlighted-span attention is below a target, add \(\log(\tau/\psi)\) to all span logits; official setting uses target .10 over all heads/layers. | Rewritten IFEval, Qwen2.5-3B: prompt/instruction loose .42/.53 baseline to .53/.62. Qwen2.5-7B: .47/.59 to .54/.66. Custom MT-IFEval average degradation from first to last turn fell from 18.2% to 9.3%; final-turn performance improved 25.7% relative on average. | Prompts were rewritten to separate task text and instructions. It is not the untouched IFEval distribution. Extreme targets produced incoherence; refusal steering hurt benign accuracy. [arXiv:2505.12025](https://arxiv.org/abs/2505.12025) **[V]** |
| **Directer** | Tentatively scales instruction-span KV states, checks the steered next-token distribution against the raw distribution, and progressively removes sensitive layers when implausible. | Rewritten IFEval: Qwen2.5-3B mean 63.9→67.1; 7B 72.4→74.4; 14B 81.6→83.5. Llama-3.1-8B prompt/instruction 73.5/81.5→78.8/84.8. | Rewritten prompts; March 2026 preprint. Adds about 16% throughput overhead. It is a close design analogue, not independent proof on this Qwen3 implementation. [arXiv:2603.06745](https://arxiv.org/abs/2603.06745) **[V]** |
| **PASTA** | Post-softmax multiply non-highlighted attention by \(\alpha=.01\), then renormalize, only in profiled heads. | No official IFEval result in the original paper. Large gains occur on custom JSON formatting, pronoun, BiasBios, and CounterFact tasks; Llama-7B's reported multi-task average was 67.29→95.46. | The published gains depend on task-profiled head sets and custom tasks. The paper selected 25/53/86 heads for Llama-7B at three profiling cutoffs; all-head intervention was worse. \(.01\) means a 100× relative odds change, not a gentle 1% adjustment. [arXiv:2311.02262](https://arxiv.org/abs/2311.02262) **[V/I]** |
| **GUIDE** | Add a fixed logit offset to tagged tokens at every layer; tags come from the prompt. | Mistral-7B French summarization 29.4→60.4 at offset 2; needle retrieval 87.0→92.1 near offset 1; JSON Jaccard improved about 30% near offset 3. | Not IFEval. Offsets above 5 often caused nonsensical output. A logit offset of 2 is already 7.4× in odds; 5 is 148×. [arXiv:2409.19001](https://arxiv.org/abs/2409.19001) **[V/I]** |
| **InstABoost** | Multiply post-softmax instruction attention by \(M\) and renormalize, over all heads. | Across 15 steering tasks, the useful region was behavior-dependent; the study swept \(M=1\ldots20\). Its examples show quality declining gradually at high \(M\), while latent steering and high-target SpotLight could collapse abruptly. | Not IFEval; behavior-strength tasks do not establish general instruction following. At SpotLight target .4, a qualitative example ignored the question and repeated the requested emotion; at InstABoost \(M=19\), fluency was rated 1/2. [arXiv:2506.13734](https://arxiv.org/abs/2506.13734) **[V]** |

SpotLight is the closest published control law to Stencil. Its IFEval numbers are genuinely positive, but they do not refute the local sealed null because four consequential differences remain:

1. SpotLight uses an *under-correcting* mass update; Stencil uses exact odds correction. **[I]**
2. SpotLight's successful IFEval input was rewritten into explicitly marked regions; Stencil's governing spans come from the ledger/salience pipeline. **[V/R]**
3. The model families and sizes differ; SpotLight's smallest directly reported Qwen IFEval model is Qwen2.5-3B, not Qwen3-1.7B. **[V]**
4. The local result includes a sharp safety failure—cap truncations rose 3→12 and 13/20 biased pinned-cache cases degenerated—that should dominate a small score trend. **[R]**

Directer is more informative for the redesign than SpotLight's raw gain. On Llama-3.1-8B rewritten IFEval, official PASTA at .01 scored 66.7/75.5 versus the 73.5/81.5 baseline; tuning PASTA to .1 produced 76.5/83.4. Official SpotLight at target .3 scored 59.7/71.3; tuning it to .1 produced 76.3/83.6. Directer produced 78.8/84.8. **[V]** Two conclusions follow:

- “Published method” is not a safe dose. A setting that works for one model/task can be strongly harmful on another.
- Rejection/backoff provides something that deficit gating does not. Deficit gating answers “is current attention mass low?”; Directer asks “did the proposed intervention make the next-token distribution implausible?” The latter is much closer to the observed failure mode.

SpotLight's own ablations complicate a blanket “only a few heads” rule: one head in one layer or all heads in one layer was often worse than baseline; one head across layers helped; its dynamic all-layer/all-head rule was best on its tasks. **[V]** PASTA and AutoPASTA, however, found that indiscriminately steering more heads can degrade results. The robust synthesis is not “always sparse” but **select by causal utility and constrain the output distribution**.

### Adjacent methods that are often cited but are not IFEval evidence

- **AutoPASTA** automatically finds a supporting sentence, then applies PASTA to a moderate number of heads and the top 3–6 layers. On Llama-3-8B, Natural Questions exact match reached 40.51, +9.94 over its best baseline; on HotpotQA, directly highlighting the gold sentence produced 58.08 EM/75.41 F1 versus 42.58/63.30 without the identified highlight. More steered heads could hurt. This is open-book QA, not instruction following. [arXiv:2409.10790](https://arxiv.org/abs/2409.10790) **[V]**
- **Selective Prompt Anchoring (SPA)** is a two-forward-pass decoding contrast between the original and a masked prompt, activated after generated code fails tests. It improved Pass@1 by as much as 12.9 points across code benchmarks; DeepSeek-Coder-1.3B HumanEval improved 66.4→70.1. It does not edit internal attention and has no IFEval result. [arXiv:2408.09121](https://arxiv.org/abs/2408.09121) **[V]**
- **Attention Buckets** aggregates parallel RoPE configurations for tool use and RAG; it does not report IFEval or multi-turn instruction persistence. [arXiv:2312.04455](https://arxiv.org/abs/2312.04455) **[V]**
- **Attention Instruction** inserts index labels and asks a model which documents to attend to; it is a prompting/retrieval method, not an internal pre-softmax bias and not an instruction-following benchmark result. [arXiv:2406.17095](https://arxiv.org/abs/2406.17095) **[V]**
- **Found in the Middle** calibrates retrieval scores by subtracting positional bias estimated from dummy documents; it reports gains up to 15 percentage points on RAG QA. **Ms-PoE**, a different “found in the middle” line, applies head-specific RoPE rescaling and reports up to 3.8 points on ZeroSCROLLS. Neither tests constraint adherence. [arXiv:2406.16008](https://arxiv.org/abs/2406.16008), [arXiv:2403.04797](https://arxiv.org/abs/2403.04797) **[V]**
- **Context-aware decoding (CAD)** contrasts logits with and without context and reported a 14.3% factuality improvement in summarization. This directly changes output logits and is evidence for a two-pass contrast, not evidence that instruction-span attention should be raised. [arXiv:2305.14739](https://arxiv.org/abs/2305.14739) **[V]**
- **Instruction Position Matters** trains with the instruction after the input and reported up to 9.7 BLEU improvement on zero-shot WMT translation. It is a training/layout result, not an inference-time wave result. [arXiv:2308.12097](https://arxiv.org/abs/2308.12097) **[V]**

These methods are relevant mechanism analogies, but counting them as “attention steering improves IFEval” would be category error.

## 2. Why the current late-layer, all-head deficit mechanism can degenerate

### The intervention imposes an absolute mass floor on incomparable heads

Natural attention mass on a span is not calibrated across heads, layers, query positions, or span lengths. Some heads specialize in recent syntax, delimiters, copying, induction, or output formatting; low mass on the governing instruction can be the correct behavior for that head at that generation step. The exact-deficit rule treats every low value as a deficiency and reallocates mass until the same target is reached. **[I]**

GUIDE directly compared a learned influence score with raw attention for identifying useful tokens. Its influence score reached about .74 AUC and .72 correlation, while raw attention was around chance in two of three comparisons. [arXiv:2409.19001](https://arxiv.org/abs/2409.19001) **[V]** That is consistent with the local deficit gate's failure: attention mass is an observable, not a reliable estimate of causal need. The failed EV gate (AUC ≈ .5) supplies local evidence that the available controller features do not identify beneficial generation steps. **[R]**

### Exact correction is more aggressive than its target number suggests

For a uniformly biased span, adding \(b\) to its logits changes its total mass from \(\psi\) to

\[
\psi' = \frac{e^b\psi}{e^b\psi + 1-\psi}.
\]

SpotLight sets \(b=\log(\tau/\psi)\); Stencil sets \(b=\operatorname{logit}(\tau)-\operatorname{logit}(\psi)\). The latter is larger by \(-\log(1-\tau)+\log(1-\psi)\), reaches the target exactly, and is applied again in each selected layer. **[I/R]** It is therefore misleading to compare only the visible target \(\tau\). The comparable quantities are:

- relative span/non-span odds multiplier \(e^b\);
- absolute mass change \(\Delta\psi\);
- raw-versus-steered next-token divergence;
- the number of affected head × layer × token decisions.

PASTA's “.01” is likewise not a small dose. Multiplying non-highlighted attention by .01 is equivalent to adding \(\log(100)=4.605\) to highlighted-versus-other logits before normalization. **[I]** Directer's finding that PASTA .01 can regress IFEval is therefore unsurprising.

### Repeating the correction through eight late layers changes computation, not just retrieval

The outputs of layers 20–27 are sequential inputs to one another. Reapplying a span floor at each layer repeatedly substitutes instruction-span value vectors for whatever each layer would naturally read. The total effect cannot be computed by multiplying eight independent mass changes because representations and attention distributions change after each intervention, but it is a repeated, state-dependent perturbation. **[I]** Late attention heads are not interchangeable, and shared span selection does not establish that the selected value direction is useful for every head.

A uniform span offset preserves the natural logit differences among tokens *inside* that span. It does **not** literally make the span tokens uniform. In the very-high-bias limit, however, it removes almost all outside competition and leaves the head operating only over that local token set; a token-specific static field can also alter within-span ranking. **[I/R]** This distinction matters because the likely failure is not simple “flattening.” It is forced cross-region reallocation and repeated value injection.

### Instruction text is not an executable constraint representation

An instruction may say “do not use the letter e,” “answer in exactly three bullets,” or “ignore the former rule.” Re-reading its lexical tokens is not equivalent to applying the predicate at the correct decoding steps. Raising attention can encourage copying, topical repetition, or renewed processing of a stale instruction. It cannot by itself encode negation, supersession, or a finite-state obligation such as “exactly N occurrences.” **[I]** The ledger is therefore most valuable as an explicit state machine—active, replaced, deleted, satisfied—not merely as a list of text spans.

### Autoregressive errors can self-reinforce

Once a perturbation changes one token, that token enters the recent context and can alter subsequent attention and logits. A small initial distortion can therefore grow into a loop or early loss of task content. This is a plausible autoregressive feedback mechanism, but the literature does **not** justify the strong statement “low attention entropy causes inference-time repetition.” **[I]**

The entropy-collapse paper shows that concentrated attention accompanies loss spikes and divergence *during training*, not that an inference-time span boost causes repetitive decoding. [arXiv:2303.06296](https://arxiv.org/abs/2303.06296) **[V]** “Repetition In, Repetition Out” emphasizes training-data patterns and greedy/MAP decoding; its attention dropout is a training intervention. [arXiv:2310.10226](https://arxiv.org/abs/2310.10226) **[V]** On-the-Fly Attention Modulation instead attributes some degeneration to insufficient/dysfunctional attention and improves text by redistributing it, which cuts against a one-directional entropy story. [ACL Findings 2021](https://aclanthology.org/2021.findings-acl.107/) **[V]**

The defensible conclusion is narrower: **large or badly located steering is empirically known to cause nonsense, relevance loss, or repetition** in GUIDE, SpotLight/Directer, InstABoost, and activation-steering work; Stencil's own 13/20 failure is the strongest evidence for this exact implementation. The entropy-to-repetition causal chain remains unproven.

### What a safe positive dose must change

A safer controller should satisfy all of the following:

1. Use a **mass-increment cap**, not only a target floor: for example, \(\Delta\psi\le .01\) or .02 in the initial grid.
2. Apply a fractional correction \(b=\lambda[\operatorname{logit}(\tau)-\operatorname{logit}(\psi)]\), with small \(\lambda\), and cap \(|b|\). The final values must be chosen on development data and frozen before confirmation.
3. Select head/layer groups by held-out *causal utility*—improved likelihood of compliant reference tokens or improved constraint state with low output divergence—not by high or low raw attention alone.
4. Compare the candidate next-token distribution with the raw distribution and reject/back off when Jensen–Shannon divergence, top-token plausibility, or entropy change leaves a development-calibrated trust region.
5. Stop steering once a ledger item is satisfied or superseded, and never steer deleted items.
6. Preserve within-span ranking; do not replace it with uniform value averaging.
7. Log presses, rejected presses, \(\Delta\psi\), KL/JS divergence, entropy change, and selected head/layer IDs. A “deficit existed” counter is not evidence that the intervention helped.

## 3. KV-cache preservation: what the literature really supports

### Generic cache-compression evidence

- **H2O** retains recent tokens and accumulated heavy hitters. With only 20% of the OPT-30B cache, it reported COPA 84 versus 85 with full cache, OpenBookQA 43.0 versus 43.2, PIQA 78.45 versus 78.51, and WinoGrande 69.06 versus 70.24. These are generic tasks, not persistent instruction tests. [arXiv:2306.14048](https://arxiv.org/abs/2306.14048) **[V]**
- **SnapKV** selects per-head tokens using an observation window. A 1,024-token cache beat H2O with 4,096 tokens on 11/16 LongBench datasets; Command-R RAG retained 98.8% of full-cache performance at 5–10× compression. It does not identify instructions as a privileged semantic class. [arXiv:2404.14469](https://arxiv.org/abs/2404.14469) **[V]**
- **PyramidKV** allocates larger cache budgets to early layers and fewer tokens in deeper layers. It matched full-cache LongBench at about 12% cache and improved TREC by 20.5 points at 0.7% cache; Llama-2-70B needle retrieval stayed at 100 with 128 entries in the reported setting. Again, no persistent-instruction endpoint. [arXiv:2406.02069](https://arxiv.org/abs/2406.02069) **[V]**
- **StreamingLLM** keeps initial “attention sink” tokens plus a recent window, enabling stable generation to four million tokens and reporting up to 22.2× speedup. Its central finding is that initial sink tokens can be semantically unimportant. Keeping the first few tokens is not equivalent to pinning an instruction. [arXiv:2309.17453](https://arxiv.org/abs/2309.17453) **[V]**

These papers establish that eviction policy matters, but they do not by themselves support an instruction-specific claim.

### Direct instruction and multi-turn evidence

**FlowKV** is the closest independent multi-turn analogue. It isolates each turn's compression so that a previously compressed cache is not recursively compressed. On Qwen2.5-7B's three-turn instruction-following benchmark, full-cache turn scores were 76.30/60.72/51.19. A 50%-cache SnapKV baseline scored 76.49/17.33/21.96; adding FlowKV produced 76.49/56.72/49.67. On Llama-3.1-8B, full cache scored 73.41/64.49/56.62, SnapKV 76.15/37.08/29.39, and SnapKV+FlowKV 76.15/61.93/54.95. [arXiv:2505.15347](https://arxiv.org/abs/2505.15347) **[V]**

The size-matched appendix is particularly relevant. For Qwen2.5-1.5B, full-cache scores were 42.02/30.18/26.23. With 10% SnapKV they were 44.13/14.21/12.45; FlowKV restored them to 44.13/29.80/26.23. At 30% cache, 43.82/14.35/12.88 became 43.82/30.19/25.79; at 50%, 44.71/14.46/12.72 became 44.71/28.55/25.94. **[V]** This is large recovery without positive instruction-span amplification.

**MemDecay** explicitly measured semantic-region lifetimes and protection. For Qwen2.5-1.5B/3B, estimated half-lives were roughly 150/148 tokens for system material, 27/31 for user content, and 14/14 for scratch content in the reported setup. With 50% cache, explicit pinning passed 24/24 short and 21/24 long system probes, reaching the full-cache ceiling on the short set; streaming cache passed only 0–2/24. [arXiv:2607.10582](https://arxiv.org/abs/2607.10582) **[V]** The probe set is small (eight scenarios/96 probes), and this is a July 2026 preprint, so it is corroboration rather than a definitive benchmark.

**Pitfalls of KV-Cache Compression** evaluates five methods on all 541 modified IFEval cases with Llama-3.1-8B and Qwen2.5-14B. It finds that some constraint classes can be almost entirely ignored under compression, and that whitelisting defense/instruction tokens at the same total cache budget reduces both instruction degradation and leakage. [arXiv:2510.00231](https://arxiv.org/abs/2510.00231) **[V]** This directly supports semantic protection rather than an attention-mass boost.

### Is Stencil's 62% recovery plausible?

Yes. **[I]** It is neither implausibly large nor obviously at the ceiling:

- FlowKV often recovers most of a 25–40-point late-turn loss.
- MemDecay's explicit system pinning can reach full-cache performance on a small probe suite.
- Stencil recovered 20 points, or 62% of its registered eviction gap. **[R]**

The comparisons are not apples-to-apples: cache budgets, models, turn construction, and scoring differ. The safe conclusion is that a 20-point recovery is within the range of independent findings, not that it reproduces a particular paper.

The strongest next cache experiment is not “pin then amplify.” It is **active-state pinning**: pin losslessly at every layer; do not recompress prior turns; and retire or replace entries when the ledger marks an instruction as superseded. Compare this with equal-budget recency, heavy-hitter, and random-span controls. That tests whether the ledger's semantic selection matters.

## 4. Benchmarks for the next phase

| Benchmark | What it measures | Scale and verified anchor | Fit for Stencil | Caveat |
|---|---|---|---|---|
| **Multi-IF** | Accumulation of compatible constraints across three turns, eight languages. | 4,501 conversations; 909 English. Llama-3.1-8B average fell .688→.542 from turn 1 to 3; English .801→.641. Official Qwen3 report: Qwen3-1.7B thinking IFEval/Multi-IF 72.5/51.2, non-thinking 68.2/44.7. [paper](https://arxiv.org/abs/2410.15553), [Qwen3 report](https://arxiv.org/abs/2505.09388) **[V]** | **Best immediate confirmation set.** Exact/verifiable, current local pipeline, direct small-model anchor. | Only three turns; primarily accumulation, not deletion/replacement. Official Qwen template/runtime may differ from the hand-rolled trunk. |
| **SysBench** | System-instruction persistence for five turns, including aligned/misaligned requests and dependent/parallel constraints. | 500 system messages, 2,500 turns; checklist judge reported 94% human agreement. Qwen2-7B total instruction-success rate 26.9; dependent scenario success 52.5 at round 1→1.1 at round 5. Llama-3.1-8B dependent 62.9→6.7. [arXiv:2408.10943](https://arxiv.org/abs/2408.10943) **[V]** | Best established test of durable system rules and user conflict. | LLM-judge component; no Qwen3-1.7B baseline. |
| **EvolIF** | Dynamic dialogue state: add, delete, and modify topics, instructions, and constraints; switching and backtracking. | 150 dynamic dialogues, 9 rule-based and 3 subjective constraint types. Qwen3-235B reported episode duration 10.02 and robustness 47.47; GPT-5 19.32/66.4. [arXiv:2511.03508](https://arxiv.org/abs/2511.03508) **[V]** | **Best conceptual test of a ledger.** It distinguishes active from stale rules. | Small set, large-model/generator-judge burden, no 1.7B baseline; release status should be rechecked before operational planning. |
| **IFBench** | Generalization to unseen, verifiable instruction types. | 58 constraints; at publication even leading Qwen3-32B/Claude-4 systems were below 50% under the main strict measure. [arXiv:2507.02833](https://arxiv.org/abs/2507.02833) **[V]** | Best unsaturated, programmatic single-turn generalization audit. | Does not test long-lived state; the sealed single-turn line makes it secondary here. |
| **FollowBench** | Increasing constraint complexity, levels 1–5. | 820 instructions. Qwen-Chat-7B hard success fell 55.9 at level 1→23.3 at level 5. [arXiv:2310.20410](https://arxiv.org/abs/2310.20410) **[V]** | Useful stress test for many constraints. | Single-turn and hybrid rule/GPT-4 evaluation; older model set. |
| **CFBench** | Chinese complex instructions across 200 scenarios/50 task types. | 1,000 examples, 10 broad and 25 fine categories. [arXiv:2408.01122](https://arxiv.org/abs/2408.01122) **[V]** | Multilingual complexity audit. | Not an aged-instruction benchmark; no useful Qwen3-1.7B anchor. |
| **MT-Eval** | Multi-turn recollection, expansion, refinement, and follow-up. | 168 dialogues, 1,170 turns, mean 6.96 turns. [arXiv:2401.16745](https://arxiv.org/abs/2401.16745) **[V]** | Broader conversational robustness. | LLM-judged and not centered on atomic constraints. |
| **LongMemEval** | Long-history information extraction, temporal reasoning, knowledge updates, and abstention. | 500 questions; 115k-token and 1.5m-token settings. Llama-3.1-8B fell .710 oracle→.454 long-context. [arXiv:2410.10813](https://arxiv.org/abs/2410.10813) **[V]** | Good secondary check for state availability and updates. | Memory QA, not instruction adherence. |

### Recommended benchmark order

1. **Multi-IF English (909 conversations)** for the next single confirmatory experiment. It has the closest endpoint, a Qwen3-1.7B published anchor, deterministic constraint checks, and an existing local path. Use turn 2–3 as the primary endpoint and cluster inference by conversation.
2. **SysBench** after the mechanism passes Multi-IF, because its five-turn system/user conflicts test the persistence claim more directly.
3. **EvolIF** for the ledger's add/delete/modify semantics, after confirming that the released artifacts and judging cost are workable.

IFBench is likely the least saturated exact-verifier benchmark, but it is a generalization audit rather than evidence about waves or memory. It should not be used to reopen the closed single-turn claim.

## 5. Activation and representation steering

The web evidence does **not** reveal a mature activation-steering method that reliably raises the untouched, aggregate official IFEval score of a 1–2B model. The positive results are narrower.

**Stolfo et al., “Improving Instruction-Following in Language Models through Activation Steering.”** The method forms a difference-in-means residual-stream direction from prompted versus unprompted examples and dynamically maps the current projection toward the mean instructed projection. It selects one layer by sweep and applies the vector through generation. The paper evaluates augmented IFEval subsets—163 format and 203 keyword examples—on Phi-3 Mini, Gemma-2-2B/9B, and Mistral-7B. Without textual instructions, steering raises accuracy roughly from 10% toward 30% across models; with instructions already present, statistically significant improvement appears in only two of four models. The paper reports occasional nonsensical/repetitive generations and small quality losses. [arXiv:2410.12877](https://arxiv.org/abs/2410.12877) **[V]** This is evidence for task-specific latent control, not a generic official-IFEval gain.

**SAIF.** It selects 15 sparse-autoencoder features in the last layer for Gemma-2 and Llama-3-8B. On a custom XNLI-derived suite, Llama's French instruction reached roughly 30% strict/65% loose compliance; one feature did almost nothing, about 15 worked best, and adding more introduced noise/decline. [arXiv:2502.11356](https://arxiv.org/abs/2502.11356) **[V]** It uses an LLM judge and is not official IFEval.

**AxBench** provides an important negative baseline: over a broad concept-steering suite, prompting scored .894 overall, ReFT .741, rank-one ReFT .543, difference-in-means .239, and SAE steering .165. [arXiv:2501.17148](https://arxiv.org/abs/2501.17148) **[V]** Sparse features are not automatically precise controls.

**Inference-Time Intervention (ITI)** selects truthful attention-head directions and increased Alpaca's TruthfulQA score from 32.5 to 65.1, with a helpfulness tradeoff. [arXiv:2306.03341](https://arxiv.org/abs/2306.03341) **[V]** This is strong evidence that head-local interventions can control a behavior, but truthfulness is not instruction following and the tradeoff is germane.

**In-Context Vectors (ICV)** extracts a task direction from demonstrations and reports gains on style, safety, role-play, and formatting tasks, but not an aggregate official IFEval score for a 1–2B model. [arXiv:2311.06668](https://arxiv.org/abs/2311.06668) **[V]**

The practical lesson is that residual/SAE steering does not escape the same problem as attention bias: a direction can be behaviorally potent but poorly localized, task-specific, and destructive at high dose. If tested, it should use the same held-out layer selection and raw-versus-steered trust region as the attention variant. It should not be presented as evidence-backed replacement for the current controller.

## 6. Decoding changes and the estimand

### Why a repetition penalty is not a valid rescue

A repetition penalty directly changes logits for previously generated tokens. It can independently prevent loops, alter exact-string constraints, change response length, and improve or hurt benchmark scores. If applied only to the wave arm, the comparison estimates “wave plus anti-repetition decoder versus baseline,” not the wave. If applied to both arms, it estimates the wave under a new decoder, which can be useful but no longer answers whether the existing wave helps under the registered decoding regime. **[I]**

The same warning applies to no-repeat n-grams, contrastive search, Look-back Decoding, EOS suppression, and minimum-length constraints. Look-back Decoding explicitly chooses tokens using divergence between current and historical output distributions to reduce repetition and topic drift; contrastive search adds a degeneration penalty. They are real decoders, not neutral safety belts. [Look-back Decoding](https://aclanthology.org/2023.emnlp-main.66/), [Contrastive Search](https://arxiv.org/abs/2202.06417) **[V]**

### Legitimate primary controls

- Use identical tokenizer, template, greedy/sampling settings, stop strings, maximum tokens, and precision in every arm.
- Increase `max_new_tokens` identically in every arm if the scientific target includes completions longer than the current cap. Keep “hit the cap” as a recorded failure/safety outcome. The current 3→12 statistic is cap truncation (`len(out) >= max_new`), not evidence of early EOS. **[R]**
- Pre-register separate rates for cap truncation, early EOS/empty output, repeated n-gram loops, invalid format, and mean/upper-tail output length.
- If a continuation protocol is needed, resume from the same KV state with no new natural-language prompt, concatenate before grading, and apply identically to every arm. Increasing the common cap is cleaner.
- Run any anti-degeneration decoder only as a **separate 2×2 factorial secondary study**: wave on/off × decoder on/off. Report the interaction and all four cells. Do not use it to declare the wave rescued.

## 7. Ranked redesigns

### 1. Wave-TR: a raw-versus-steered trust-region controller

**Design.** Keep the ledger-selected active span, but replace the exact mass floor with a candidate perturbation and rejection/backoff loop:

1. Compute the raw next-token distribution.
2. Compute a candidate using fractional odds correction, a hard \(\Delta\psi\) cap, and a preselected layer/head group.
3. Compare candidate and raw distributions using Jensen–Shannon divergence, candidate-token raw probability, entropy change, and top-token rank change.
4. If outside a development-calibrated plausibility region, halve the dose and/or remove the most sensitive layer group. If no candidate is safe, emit the raw distribution.
5. Never press for satisfied/superseded ledger items.

This adapts Directer's strongest idea while retaining Stencil's explicit attention mechanism. The trust criterion operates at the point where failure becomes behaviorally relevant—the output distribution—rather than treating low span mass as proof of need. Use nested backoff over four two-layer groups (20–21, 22–23, 24–25, 26–27), not all eight by default. Freeze the order and thresholds after development.

**Why it may avoid degeneration.** Extreme local effects are rejected; safe candidates can retain a small causal nudge; zero-dose is an allowed action. It directly addresses Directer's fixed-dose regressions and Stencil's truncation/loop failures.

**Confirmatory test.** Multi-IF English, all 909 conversations, unchanged base decoding. Select one Wave-TR configuration on a disjoint development set. Primary endpoint: conversation-clustered mean of the four official turn-2/3 instruction-following metrics. Require:

- improvement of at least **+2.0 absolute points** over pin-only/base as predeclared, with a one-sided paired randomization test below .05 and a 95% cluster-bootstrap interval above zero;
- cap-truncation risk difference whose one-sided 95% upper bound is no more than **+1.0 point**;
- repeated-loop and invalid-output risk differences whose one-sided 95% upper bounds are each no more than **+1.0 point**.

Use one confirmatory configuration; do not test a grid and report the winner on the same 909 conversations.

**Evidence-based expectation.** Directer improved Qwen2.5-3B rewritten-IFEval mean by +3.2 points and Llama-3.1-8B prompt/instruction by +5.3/+3.3. Given the smaller model, different benchmark, prompt rewrite caveat, and local null, a defensible forecast is **+1 to +3 points**, not SpotLight's +11 prompt points. **[V/I]**

**Failure meaning.** If a safely accepted dose measurably raises selected-span mass but produces <2 points and the interval excludes +2, amplification is not practically useful here. If unsafe candidates dominate and safe candidates are effectively zero, the feasible perturbation set is empty for this implementation.

### 2. Wave-Memory: make the ledger select persistent active state, not extra mass

**Design.** Turn “wave selects” into a routing operation:

- pin KV entries for active constraint spans losslessly at every layer;
- never recursively recompress them;
- give them a fixed, separately accounted budget;
- on add/modify/delete events, atomically update the active set and retire stale slots;
- use natural attention over visible active slots—no positive bias in the primary variant;
- compare against equal-budget recency, heavy-hitter, and random-span pinning.

The controller's learned job becomes active-state selection and replacement. This retains the conceptual thesis that a small mechanism selects governing information, while avoiding repeated substitution of its value vectors into every late head.

**Why it may avoid degeneration.** It changes availability, not the natural computation over available tokens. The local pin-only result already improved scores without the 13/20 amplified-cache failures. **[R]**

**Confirmatory test.** First use the registered cache-pressure multi-turn setup, then SysBench/EvolIF for replacements and conflicts. Primary outcomes:

- recover at least **50% of the full-cache minus equal-budget-eviction gap** on active-constraint satisfaction;
- stale/deleted-rule false-adherence no more than **+2 points** versus full cache;
- no more than **+1 point** increase in cap truncation or loop rate;
- active semantic pinning beats equal-budget random-span pinning with paired \(p<.05\).

**Evidence-based expectation.** Local pinning already recovered 62%/+20 points. FlowKV recovered roughly 28–39 late-turn points over recursive SnapKV in its Qwen2.5-7B setting and nearly closed the full-cache gap; the 1.5B appendix also nearly closed it. Under genuine eviction pressure, **10–20 points** is plausible; with a full cache, the expected gain is approximately zero. **[R/V/I]**

**Failure meaning.** If oracle-correct active spans, pinned losslessly, fail to beat equal-budget nonsemantic policies under known eviction loss, the ledger is not selecting the needed state. If active pinning works but positive attention never adds value, the memory-availability mechanism survives but the attention-amplification version of the wave does not.

### 3. Wave-HS: held-out causal head/layer selection with a bounded rank-preserving dose

**Design.** Profile a small candidate set without using confirmatory examples:

1. On development completions, intervene one head/layer group at a time with a tiny bounded mass increment.
2. Score change in likelihood of compliant reference tokens or a differentiable constraint proxy, minus penalties for raw-output JS divergence, attention-entropy change, and base-token likelihood loss.
3. Retain only stable positive groups across folds; freeze them.
4. Apply uniform logit offsets within the chosen span so native within-span ranking remains intact.
5. Use an oracle-span ablation before trusting salience selection; include same-length random-span and shuffled-ledger negative controls.

This is closer to PASTA/ITI/SEKA's head-local strategy than the present all-head rule. SEKA's recent spectral analysis also finds sensitive heads concentrated in mid-to-late layers rather than uniformly distributed; on Qwen3-4B CounterFact it reported 57.70 baseline, 97.16 PASTA, and 99.02 SEKA, though this is model editing, not IFEval. [arXiv:2603.01281](https://arxiv.org/abs/2603.01281) **[V]**

**Why it may avoid degeneration.** Heads that do not causally benefit are left untouched, the mass shift is bounded, and negative controls expose gains due only to generic perturbation or length.

**Confirmatory test.** Multi-IF English late-turn metrics, with the same +2-point efficacy and +1-point safety margins as Wave-TR. The primary comparison is Wave-HS versus the same pin-only/base condition. A mechanistic secondary endpoint requires both (a) increased target-span causal contribution in selected heads and (b) improved satisfaction of the corresponding active constraint.

**Evidence-based expectation.** PASTA's large gains are on task-specific custom endpoints and use a strong 100× odds reweighting; SpotLight's Qwen2.5-3B rewritten-IFEval gain is larger but conflicts with the local sealed result. A conservative forecast is **+0.5 to +2 points**. **[V/I]** This is lower-confidence than the first two designs.

**Failure meaning.** If oracle spans and a cross-validated positive head set raise attention but not compliance, salience is not the bottleneck and head sparsity does not rescue the amplification thesis.

## What to run first

No model run was performed for this report. The next execution should be a staged, foreground CPU study, not a new sealed sweep.

### Stage A — replay/teacher-forced safety map on development data

Use existing, nonconfirmatory Multi-IF development examples and cached or CPU-computed baseline states. Compare:

- raw baseline;
- current exact correction;
- fractional correction with \(\lambda\in\{.1,.25,.5\}\);
- \(\Delta\psi\) caps in \(\{.01,.02\}\);
- four two-layer groups and a small number of held-out causal head groups;
- Wave-TR rejection/backoff.

Record per step: original and final span mass, odds multiplier, output JS/KL divergence, entropy change, raw probability of the candidate token, top-token rank change, and constraint-token log-likelihood. This stage chooses ranges; it makes no benchmark claim.

### Stage B — 128-conversation generated pilot

Run baseline/pin-only, Wave-TR, and Wave-Memory on a balanced, nonconfirmatory set. Stop the amplitude branch if either condition holds:

- cap truncation, repeated-loop, or invalid-output rate exceeds baseline by more than 2 points; or
- fewer than 5% of proposed presses survive the trust region, making the mechanism operationally equivalent to baseline.

Use the pilot to freeze one Wave-TR configuration and one active-memory policy. Do not tune on the final 909.

### Stage C — one sealed Multi-IF confirmation

Confirm only the two strongest frozen variants:

1. pin-only/active Wave-Memory versus the equal-budget baseline;
2. Wave-TR versus its matched no-positive-dose control.

Cluster all inference by conversation. Publish every press/rejection counter and every truncation/loop case. Keep turn 1 as a negative/low-need control and turns 2–3 as the primary endpoint. If neither variant crosses its predeclared efficacy and safety thresholds, stop the amplification line rather than trying another target on the same confirmation set.

## Explicit falsification criteria

The broad metaphor “waves select” is too flexible to falsify unless tied to a local operational claim. The testable Stencil claim should be:

> In frozen Qwen3-1.7B, selectively increasing the causal contribution of the correct active instruction representation, within a predeclared output-divergence budget, improves late-turn verifiable constraint satisfaction by at least 2 absolute points without more than a 1-point increase in truncation, looping, or invalid output.

Treat the claim as falsified for this model/mechanism if all of the following occur:

1. **Oracle-span Wave-HS fails:** with known-correct governing spans and held-out positive heads, the upper confidence bound is below +2 points.
2. **Trust-region Wave-TR fails:** it either produces no safe nonzero dose or a measurable safe attention shift without compliant-score improvement.
3. **Mediation fails:** span mass/contribution rises, but targeted constraint satisfaction does not; random or shuffled spans perform similarly.
4. **Availability explains the gain:** lossless active-state pinning recovers performance, but every positive dose is neutral or harmful.

That result would not disprove every possible biological “wave” analogy. It would disprove the actionable claim that extra late-layer attention to instruction text is the missing causal resource in this frozen model. The surviving engineering result would be semantic memory routing, not attention amplification.

## Citation ledger: opened primary sources and checked numbers

“No relevant score” means the paper was opened and does not report the requested standard IF endpoint; it is included to prevent adjacent evidence from being misclassified.

| Source | Year / venue | Opened source | Exact checked result relevant here |
|---|---:|---|---|
| SpotLight: Attention-based Prompting | 2025 preprint | [arXiv:2505.12025](https://arxiv.org/abs/2505.12025) | Rewritten IFEval Qwen2.5-3B .42/.53→.53/.62 prompt/instruction; MT-IFEval average turn degradation 18.2%→9.3%; target .10 default. |
| Directer | 2026 preprint | [arXiv:2603.06745](https://arxiv.org/abs/2603.06745) | Rewritten IFEval Qwen2.5-3B mean 63.9→67.1; Llama-3.1-8B 73.5/81.5→78.8/84.8; ≈16% throughput overhead. |
| PASTA | 2023 preprint / later conference version | [arXiv:2311.02262](https://arxiv.org/abs/2311.02262) | \(\alpha=.01\); Llama-7B profiled head counts 25/53/86; custom multi-task average 67.29→95.46. No official IFEval. |
| GUIDE: Pay Attention to What Matters | 2024 preprint | [arXiv:2409.19001](https://arxiv.org/abs/2409.19001) | Mistral-7B French 29.4→60.4 at offset 2; needle 87.0→92.1; offsets >5 often nonsensical. |
| InstABoost | 2025 preprint | [arXiv:2506.13734](https://arxiv.org/abs/2506.13734) | Multiplier swept 1–20; high-strength examples show relevance/fluency loss; no official IFEval. |
| AutoPASTA | 2024 preprint | [arXiv:2409.10790](https://arxiv.org/abs/2409.10790) | Llama-3-8B NQ EM 40.51 (+9.94); HotpotQA direct 42.58/63.30 versus identified highlight 58.08/75.41. |
| Selective Prompt Anchoring | 2025, ICML | [arXiv:2408.09121](https://arxiv.org/abs/2408.09121) | Up to +12.9 Pass@1; DeepSeek-Coder-1.3B HumanEval 66.4→70.1. No IF benchmark. |
| Attention Buckets | 2024, ACL | [arXiv:2312.04455](https://arxiv.org/abs/2312.04455) | Tool/RAG evaluations; no IFEval, Multi-IF, or instruction-persistence score. |
| Attention Instruction | 2024 preprint | [arXiv:2406.17095](https://arxiv.org/abs/2406.17095) | Multi-document QA prompt-index method; no internal-bias IF score. |
| Found in the Middle (calibration) | 2024 preprint | [arXiv:2406.16008](https://arxiv.org/abs/2406.16008) | Up to +15 points on RAG QA; no IF benchmark. |
| Ms-PoE / Found in the Middle | 2024 preprint | [arXiv:2403.04797](https://arxiv.org/abs/2403.04797) | Up to +3.8 on ZeroSCROLLS; no IF benchmark. |
| Context-aware Decoding | 2023 preprint | [arXiv:2305.14739](https://arxiv.org/abs/2305.14739) | +14.3% factuality in summarization; output-logit contrast, not IF. |
| Instruction Position Matters | 2024, Findings ACL | [arXiv:2308.12097](https://arxiv.org/abs/2308.12097) | Up to +9.7 BLEU on zero-shot WMT translation; training/layout intervention. |
| Stabilizing Transformer Training by Preventing Attention Entropy Collapse | 2023 preprint | [arXiv:2303.06296](https://arxiv.org/abs/2303.06296) | Training stability/loss-spike evidence; no inference repetition rate or IF score. |
| Repetition In, Repetition Out | 2023 preprint | [arXiv:2310.10226](https://arxiv.org/abs/2310.10226) | Training-data/decoding analysis; no evidence that an inference span floor causes repetition. |
| On-the-Fly Attention Modulation | 2021, Findings ACL | [ACL Anthology](https://aclanthology.org/2021.findings-acl.107/) | Attention redistribution for degeneration; not an IF benchmark. |
| H2O | 2023, NeurIPS | [arXiv:2306.14048](https://arxiv.org/abs/2306.14048) | OPT-30B at 20% cache: COPA 84 vs full 85; OBQA 43.0 vs 43.2; PIQA 78.45 vs 78.51. |
| SnapKV | 2024, NeurIPS | [arXiv:2404.14469](https://arxiv.org/abs/2404.14469) | 1,024 cache beat H2O-4,096 on 11/16 LongBench tasks; Command-R retained 98.8% at 5–10× compression. |
| PyramidKV | 2024 preprint | [arXiv:2406.02069](https://arxiv.org/abs/2406.02069) | ≈12% cache matched full LongBench; +20.5 TREC at 0.7%; 100 needle score with 128 entries in reported Llama-70B setting. |
| StreamingLLM | 2024, ICLR | [arXiv:2309.17453](https://arxiv.org/abs/2309.17453) | Stable generation to 4M tokens and up to 22.2× speedup; sink tokens need not be semantically important. |
| FlowKV | 2025 preprint | [arXiv:2505.15347](https://arxiv.org/abs/2505.15347) | Qwen2.5-7B full 76.30/60.72/51.19; SnapKV-50 76.49/17.33/21.96; +FlowKV 76.49/56.72/49.67. |
| MemDecay | 2026 preprint | [arXiv:2607.10582](https://arxiv.org/abs/2607.10582) | Explicit pinning at 50% cache: 24/24 short, 21/24 long system probes; streaming 0–2/24. |
| Pitfalls of KV-Cache Compression | 2026, ACL | [arXiv:2510.00231](https://arxiv.org/abs/2510.00231) | All 541 modified IFEval cases; whitelisting instruction/defense tokens reduces degradation at equal budget. |
| Multi-IF | 2025, NAACL | [arXiv:2410.15553](https://arxiv.org/abs/2410.15553) | 4,501 three-turn conversations, 909 English; Llama-3.1-8B .688 turn 1→.542 turn 3. |
| Qwen3 Technical Report | 2025 report | [arXiv:2505.09388](https://arxiv.org/abs/2505.09388) | Qwen3-1.7B thinking IFEval/Multi-IF 72.5/51.2; non-thinking 68.2/44.7. |
| SysBench | 2024 preprint | [arXiv:2408.10943](https://arxiv.org/abs/2408.10943) | 500 system messages/2,500 turns; Qwen2-7B dependent success 52.5 round 1→1.1 round 5. |
| IFBench | 2025, NeurIPS Datasets & Benchmarks | [arXiv:2507.02833](https://arxiv.org/abs/2507.02833) | 58 unseen constraints; leading systems below 50% on the principal strict evaluation at publication. |
| FollowBench | 2024, ACL | [arXiv:2310.20410](https://arxiv.org/abs/2310.20410) | 820 instructions; Qwen-Chat-7B hard success 55.9 level 1→23.3 level 5. |
| CFBench | 2024 preprint | [arXiv:2408.01122](https://arxiv.org/abs/2408.01122) | 1,000 Chinese examples, 200 scenarios, 50 task types, 10/25 broad/fine categories. |
| MT-Eval | 2024 preprint | [arXiv:2401.16745](https://arxiv.org/abs/2401.16745) | 168 dialogues, 1,170 turns, 6.96 turns average. |
| LongMemEval | 2025, ICLR | [arXiv:2410.10813](https://arxiv.org/abs/2410.10813) | 500 questions; Llama-3.1-8B .710 oracle→.454 long-context. |
| EvolIF | 2026 preprint | [arXiv:2511.03508](https://arxiv.org/abs/2511.03508) | 150 dialogues; Qwen3-235B duration/robustness 10.02/47.47; GPT-5 19.32/66.4. |
| Activation Steering for Instruction Following | 2024 preprint | [arXiv:2410.12877](https://arxiv.org/abs/2410.12877) | Augmented subsets: 163 format/203 keyword examples; significant with-instruction gain in only 2/4 models; occasional nonsense/repetition. |
| SAIF | 2025 preprint | [arXiv:2502.11356](https://arxiv.org/abs/2502.11356) | 15 SAE features best in reported sweep; custom Llama French ≈30% strict/65% loose; not official IFEval. |
| AxBench | 2025, ICML | [arXiv:2501.17148](https://arxiv.org/abs/2501.17148) | Overall prompting .894, ReFT .741, rank-one ReFT .543, DiffMean .239, SAE .165. |
| Inference-Time Intervention | 2023, NeurIPS | [arXiv:2306.03341](https://arxiv.org/abs/2306.03341) | Alpaca TruthfulQA 32.5→65.1, with helpfulness tradeoff; no IF score. |
| In-Context Vectors | 2024, Findings ACL | [arXiv:2311.06668](https://arxiv.org/abs/2311.06668) | Style/safety/role/format evaluations; no official aggregate IFEval result for 1–2B. |
| SEKA | 2026, ICLR | [arXiv:2603.01281](https://arxiv.org/abs/2603.01281) | Qwen3-4B CounterFact 57.70 baseline, 97.16 PASTA, 99.02 SEKA; not IF. |
| Look-back Decoding | 2023, EMNLP | [ACL Anthology](https://aclanthology.org/2023.emnlp-main.66/) | Explicit output-distribution decoder for repetition/topic drift; no neutral safety-only interpretation. |
| Contrastive Search | 2022 preprint | [arXiv:2202.06417](https://arxiv.org/abs/2202.06417) | Explicit degeneration-penalizing decoder; no neutral safety-only interpretation. |

## Verification boundary

All numbers used in the argument and proposal forecasts above came from opened primary sources or the user-supplied/local registered facts. I have intentionally not promoted remembered claims about unnamed “salience heads,” generic RAG gains, or unpublished plugin/tool results. The main unavoidable cross-paper limitation is heterogeneity: several attention-steering papers rewrite prompts, use custom tasks, use LLM judges, or report relative rather than absolute gains. Their numbers establish feasibility and failure modes, not an expected effect transferable without discount to Stencil.
