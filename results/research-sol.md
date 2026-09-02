# Stencil deep-research report: making the wave mechanism improve instruction-following scores

**Research date:** 2026-09-02  
**Researcher:** sol  
**Access status:** Web access was available. I opened the primary paper, official project page, or proceedings PDF for every claim marked **[V]** below. Claims marked **[I]** are my inference from those sources or from the verified Stencil results in the brief. I found no material claim below that relies only on memory; nomenclature that I could not map confidently to a primary paper is identified explicitly rather than guessed.

No repository code was changed, and no GPU, CUDA, model, or background process was run for this research.

## Executive conclusion

The literature does **not** support a general rule that increasing instruction-span attention across every head will improve instruction following. It supports a narrower rule:

> Preserve access to instruction information, then intervene only where a causally useful, bounded intervention does not force the decoder away from tokens that the unmodified model considers plausible.

The evidence most relevant to Stencil is:

1. **The closest successful attention-bias result is conditional and not directly comparable.** SpotLight reports substantial gains on rewritten IFEval, ManyIFEval, and a new MT-IFEval using an all-head/all-layer deficit rule at `tau=0.1`. Its correction is slightly weaker than Stencil's exact target-mass correction, and its IFEval prompts were rewritten to separate task and constraint spans. This is therefore a promising mechanism result, but not an independent replication on official IFEval. **[V]**
2. **Static or broadly applied steering often degenerates.** PASTA, DIRECTER, activation steering, InstABoost, and the VerIFY instruction-attention intervention all report an over-steering regime: irrelevant context is suppressed, task accuracy falls, or output becomes incoherent/repetitive. Dynamic layer selection, a small dose, a base-logit plausibility gate, and explicit fluency checks are the recurring safeguards. **[V]**
3. **Instruction-aware KV retention is better supported for Stencil's actual success case.** Generic cache-compression work mostly optimizes perplexity or QA, but newer direct tests show that instruction/defense tokens are often evicted disproportionately and that whitelisting or pinning them restores behavior. These papers do not provide an apples-to-apples “fraction of eviction gap recovered,” so Stencil's 62% cannot be numerically benchmarked against them; it is nevertheless qualitatively in line with the reported direction and magnitude. **[V]**
4. **There is no published baseline I could locate for Qwen3-1.7B on the relevant aged-constraint benchmarks.** The closest small-model intervention result is DIRECTER on Qwen2.5-3B: mean rewritten-IFEval prompt/instruction accuracy rises from 63.9 to 67.1 (+3.2 points). Multi-IF, SysBench, and VerIFY publish 7B/8B-or-larger baselines. **[V]**
5. **The present single-turn mechanism is already falsified for its registered use.** The sealed +0.39-point, `p=0.39` result plus a fourfold truncation increase is evidence against all-head late-layer span amplification as a general single-turn remedy. **[I from the verified Stencil facts]** The broader “waves select” hypothesis remains testable under context pressure, but it should now predict selective retention or bounded, causally targeted control—not more attention everywhere.

## 1. What the attention-steering papers actually show

### 1.1 Named instruction-following benchmarks

Only two opened attention-steering papers report gains on the named IFEval/LIFBench family, and both alter important evaluation details.

#### SpotLight: closest to Stencil's deficit hook

SpotLight adds a common bias to a designated span only when its current attention mass `psi` is below `tau`. It uses every attention head and layer, greedy decoding, and a fixed `tau=0.1` across its main experiments. On its rewritten 541-row IFEval, loose prompt/instruction accuracy changes as follows: Qwen2.5-3B `.42/.53 -> .53/.62`, Mistral-7B `.35/.47 -> .40/.53`, Qwen2.5-7B `.47/.59 -> .54/.66`, Llama-3.1-8B `.42/.55 -> .51/.62`, Granite-8B `.41/.54 -> .48/.60`, Llama-3.1-70B `.45/.57 -> .54/.64`, and Qwen2.5-72B `.49/.61 -> .55/.67`. The authors summarize average relative improvements of 26% at prompt level and 17% at instruction level. On ManyIFEval, Qwen2.5-3B changes from `.15/.53` to `.19/.62`; on the authors' five-turn MT-IFEval, the average late-turn drop falls from 18.2% to 9.3%, with a reported 25.7% relative gain on the final turn. **[V]** ([arXiv:2505.12025](https://arxiv.org/html/2505.12025))

The comparability caveat is substantial: a stronger model rewrote the original IFEval prompts so that task text and constraint text could be separately marked, and MT-IFEval is a new dataset constructed by the authors. This is not a score on the official, unchanged IFEval distribution. **[V]**

SpotLight's update also differs mathematically from Stencil's exact odds correction. For old span mass `psi`, it adds `log(tau/psi)`, yielding

`psi' = tau / (1 + tau - psi)`,

which is below `tau` whenever `psi < tau`. Stencil's exact correction adds

`log[tau(1-psi) / (psi(1-tau))]`,

which makes `psi' = tau`. Thus Stencil is slightly stronger at the same threshold. **[I, algebra applied to the verified algorithms]** SpotLight also reports that high thresholds eventually hurt benign relevance/accuracy and can make generation incoherent. Its comparison found PASTA with a strong fixed setting could make Qwen-7B and Llama-8B refuse all benign requests. **[V]**

#### DIRECTER: strongest safety pattern and the closest small-model number

DIRECTER scales instruction-token keys, ranks layers using one-time attention-sensitivity profiling, and decides at each decoding step whether a steered candidate remains plausible under the unsteered model. Its default key scale is `alpha=100`; a steered token is accepted only when its base-model probability is at least `beta=0.5` times the base top-token probability. When that test fails, it reduces the candidate layer set. **[V]** ([arXiv:2603.06745](https://arxiv.org/html/2603.06745))

For Llama-3.1-8B, the paper reports rewritten-IFEval prompt/instruction accuracy of `73.5/81.5 -> 78.8/84.8` (+5.3/+3.3 points). Across those two scores, three LIFBench scores, and two format-sensitive GSM scores, the mean rises from 70.0 to 76.5 (+6.5 points). For Qwen2.5-3B, mean rewritten-IFEval prompt/instruction accuracy rises `63.9 -> 67.1` (+3.2 points); Qwen2.5-7B rises `72.4 -> 74.4`, Qwen2.5-14B `81.6 -> 83.5`, and Llama-3.2-1B only `61.3 -> 61.6`. **[V]**

DIRECTER is especially relevant because its ablations reproduce Stencil's hazard. Default PASTA and SpotLight settings over-steer badly; tuned weaker versions recover. On Llama-8B, the paper's seven-score mean is 62.3 for default PASTA versus 71.0 when tuned, and 59.4 for default SpotLight versus 72.1 when tuned. Adding a fixed intervention to progressively more layers causes a steep performance decline; dynamic per-token layer selection is the main protection. Reverse-ranked, random-layer, and random-token controls are worse than its causally ranked selection. **[V]**

Again, the paper rewrites IFEval prompts to separate instructions cleanly, using `gpt-4o-mini`. The effect is credible evidence for the mechanism, but it is not an official-IFEval replication. **[V]**

### 1.2 Methods that do not report gains on IFEval, IFBench, Multi-IF, FollowBench, or LongBench

This negative result matters because several names in the brief are frequently described more broadly than their actual experiments.

- **PASTA** profiles a task-specific subset of heads and reduces non-highlighted attention probability by `alpha=.01`, followed by renormalization. On LLaMA-7B, it uses 25, 53, or 86 of 1,024 heads in representative settings; the broad optimum is roughly 50–100 heads. It reports custom JSON-format, pronoun-resolution, BiasBios, and CounterFact tasks—not IFEval or a long-context instruction benchmark. LLaMA-7B average task accuracy rises from 73.45 few-shot to 85.89 task-agnostic PASTA and 95.46 multi-task PASTA; GPT-J rises `59.65 -> 77.80 -> 85.22`. All-head steering is worse, and too many heads or `alpha=0` can sacrifice prediction accuracy and fluency. **[V]** ([ICLR 2024, arXiv:2311.02262](https://arxiv.org/html/2311.02262))
- **AutoPASTA** has an LLM identify the sentence to highlight, then applies PASTA. It reports an average +7.95% result for Llama-3-70B-Instruct on open-book QA, not a named instruction-following benchmark. It uses selected heads and `delta=log(100)`; highlighting the whole context or too many heads is worse than selecting the target sentence. **[V]** ([arXiv:2409.10790](https://arxiv.org/html/2409.10790))
- **Attention Instruction** is a prompting method that tells the model which document to use. It reports roughly +4 to +10 points for Llama-2 on multi-document QA, while deliberately naming the wrong span can cost about 25 points. It does not intervene in attention tensors and does not report an instruction-following benchmark. **[V]** ([arXiv:2406.17095](https://arxiv.org/html/2406.17095))
- **Attention Buckets** runs multiple RoPE configurations and confidence-weights their output distributions. It is not instruction-span reweighting. On ToolBench, ToolLLaMA with DFSDT-Retriever moves from `67.3/63.1` pass/win rate to `71.3/71.5`; no requested benchmark is reported. **[V]** ([arXiv:2312.04455](https://arxiv.org/html/2312.04455))
- **SPA (Steering for code generation)** combines original and masked-anchor output streams. CodeGen-350M HumanEval rises `15.3 -> 20.1` and MBPP `19.6 -> 27.4`; DeepSeekCoder-1.3B HumanEval rises `66.4 -> 70.1`. This is code generation, not instruction adherence. **[V]** ([arXiv:2408.09121](https://arxiv.org/html/2408.09121))
- **Context-Aware Decoding (CAD)** contrasts logits with and without context. It reports a 21% relative ROUGE-L gain for LLaMA-30B on CNN/DailyMail and factuality gains, not IFEval or a multi-turn adherence test. **[V]** ([arXiv:2305.14739](https://arxiv.org/html/2305.14739))
- **Found in the Middle** estimates positional attention bias using a content-free calibration example, subtracts it, and redistributes attention while preserving document-relative information. On Natural Questions retrieval, Recall@3 changes from `.3638 -> .7427` at 10 documents and `.2052 -> .6832` at 20 documents; the paper reports middle-position QA gains of roughly 6–15 points. It is RAG/QA, not instruction adherence. **[V]** ([arXiv:2406.16008](https://arxiv.org/html/2406.16008))
- **Ms-PoE** applies head-selective RoPE scales selected by position-awareness. On ZeroSCROLLS, Llama-2-7B average rises `15.0 -> 16.6`, StableBeluga-7B `16.5 -> 19.1`, Vicuna-7B `15.0 -> 18.8`, and Vicuna-7B-16K `21.6 -> 24.9`. A head-specific position-aware setting outperforms a uniform scale on multi-document QA (`65.3` versus `63.1`). It is useful evidence for head selectivity, but not an adherence result. **[V]** ([arXiv:2403.04797](https://arxiv.org/html/2403.04797))
- **InstABoost** applies a small fixed additive instruction bias and explicitly tunes its multiplier on held-out data with a fluency gate. On its 15 behavior tasks—not IFEval—it reports task-type success values of `.925/.880/.594/.625/.620` for AI-persona, emotion, jailbreak, QA, and toxicity, versus PASTA `.885/.823/.000/.560/.580` and SpotLight `.790/.927/.025/.580/.580`. Strong settings cause the model to ignore the user's question or repeat. **[V]** ([arXiv:2506.13734](https://arxiv.org/html/2506.13734))

I could not map **“LLMs are not robust to buried instructions,” “instruction attention,” “Tell your model where to attend,”** or **“Direct Instruction Steering”** to unique primary titles with enough confidence to cite them as separate papers. The closest verified matches are SpotLight, Attention Instruction, PASTA/AutoPASTA, DIRECTER, and Stolfo et al.'s activation-steering paper. **[V: negative title search; no invented attribution]**

## 2. Why the present all-head, late-layer span dose degenerates

### Mechanistic diagnosis

Adding the same logit bias to every token in a span does **not** by itself make attention uniform within that span; relative scores inside the span remain ordered. The damaging uniformity is across **head purpose**: every head is forced toward the same group-level target even if that head normally carries recent syntax, copying, delimiter, positional, or task-content information. **[I]**

For a head whose natural instruction mass is extremely small, an exact odds correction supplies a very large positive logit shift. Applying that to all heads at layers 20–27 changes eight consecutive residual updates at every generated token. In late layers, those updates are close to the output decision, leaving fewer downstream blocks to repair lost content or a prematurely reinforced token pattern. The repeated intervention can therefore create a feedback loop: an instruction-biased output changes the next query, which triggers another correction, and repetition or failure to emit EOS compounds. **[I]**

This diagnosis is supported by direct intervention evidence, not merely an “attention entropy” slogan:

- PASTA finds a broad optimum around 50–100 selected heads and reports that all-head/too-many-head settings can improve rule compliance while degrading the underlying prediction and fluency. **[V]**
- DIRECTER shows that fixed steering degrades sharply as more layers are included, while per-token layer reduction and a base-probability acceptance test avoid much of the damage. **[V]**
- VerIFY's Instruction Guided Attention (IGA) explicitly mixes instruction and context attention streams with weight `alpha`. At `alpha=.8` and `1.0`, constraint scores may rise but outputs become gibberish or repetitive; `.6` is the largest setting the authors regard as meaningful. Even at `.6`, Gemma-7B average exact constraint accuracy falls `56.67 -> 40.95`, although Gemma-2-27B rises `46.43 -> 83.12`. The sign is model-size dependent. **[V]** ([Findings of EACL 2026 paper/PDF](https://aclanthology.org/2026.findings-eacl.254.pdf))
- Stolfo et al. observe that stronger residual-stream instruction vectors trade constraint compliance for repetitive, nonsensical, or factually wrong output; only two of four models improve in the with-instruction condition. **[V]** ([ICLR 2025, arXiv:2410.12877](https://arxiv.org/html/2410.12877))
- InstABoost reports the same relevance/fluency frontier and therefore tunes strength with a held-out fluency constraint. **[V]**

The attention-entropy literature is only supporting context. Zhai et al. causally connect very low attention entropy to training instability and show that artificially sharpening attention during training can reduce accuracy or cause divergence. It does **not** establish that low inference-time attention entropy causes repetition in Stencil. **[V]** ([ICML 2023, arXiv:2303.06296](https://arxiv.org/html/2303.06296))

### Mitigations supported by the sources

1. **Select heads and layers by causal effect, not by natural low mass alone.** A head attending little to the instruction is not necessarily deficient; it may be doing another job. PASTA's profiling and DIRECTER's attention-sensitivity ranking are the strongest templates. **[V/I]**
2. **Cap the change, not just the target mass.** Pre-register a maximum per-head increase in span mass or a maximum KL divergence from the base attention distribution. A target `tau` alone permits arbitrarily large corrections when `psi` is near zero. **[I]**
3. **Preserve the base model's token plausibility.** DIRECTER's `beta=.5` test provides direct evidence that a base-logit trust region can protect output while retaining gains. **[V]**
4. **Use only instruction-token subsets that are active now.** The ledger should exclude satisfied, revoked, quoted, or irrelevant constraints. AutoPASTA's sentence-versus-whole-context result supports token-subset selectivity. **[V/I]**
5. **Make degeneration an acceptance gate.** Fluency, task relevance, repetition, EOS rate, and truncation must be co-primary or non-inferiority endpoints during dose selection. Optimizing adherence first and inspecting degeneration afterward selects the wrong operating point. **[I, consistent with InstABoost and Stolfo et al.]**
6. **Do not count ordinary softmax renormalization as a mitigation.** Any logit bias is renormalized by softmax. The problem is where the removed probability mass comes from and whether the affected head was causally useful, not whether probabilities sum to one. **[I]**

SpotLight is an important counterexample to any blanket claim that all-head steering must fail: its all-head/all-layer `tau=.1` setting performs better than its single-head/layer variants on its rewritten datasets. The correct conclusion is therefore model-, prompt-marking-, and dose-dependent. Stencil's sealed harm result remains the controlling evidence for this exact implementation and model. **[V/I]**

## 3. KV retention under context pressure

### What generic cache methods measure

- **StreamingLLM** retains the first four “attention sink” tokens plus a recent window. These are positional sink tokens, not semantically identified instructions. For Llama-13B, a 1,024-token rolling window has perplexity 58.07 while `4 sinks + 1,020 recent` has 5.40. In concatenated one-shot ARC streams, Llama-2-7B ARC-E/ARC-C goes from `71.25/53.16` with full context to `3.58/1.39` with a plain window and `71.34/55.03` with StreamingLLM. This shows preservation of streaming competence, not aged instruction adherence. **[V]** ([ICLR 2024, arXiv:2309.17453](https://arxiv.org/html/2309.17453))
- **H2O** keeps accumulated heavy hitters plus recent tokens. At a 20% cache budget on OPT-30B, full-cache versus H2O scores are COPA `85.0/84.0`, OpenBookQA `43.2/43.0`, PIQA `78.51/78.45`, and WinoGrande `70.24/69.06`. It has no instruction-adherence endpoint. **[V]** ([NeurIPS 2023, arXiv:2306.14048](https://arxiv.org/html/2306.14048))
- **SnapKV** selects tokens from an observation window near the end of the prompt. It reports that 1,024 entries (about 92% compression in its LongBench setting) retain performance well, and 4,096 entries (about 68% compression) are nearly lossless. It does not identify or score instruction tokens separately. **[V]** ([arXiv:2404.14469](https://arxiv.org/html/2404.14469))
- **PyramidKV** allocates larger budgets to lower layers and progressively smaller budgets to higher layers. It reports LongBench performance comparable to full cache while retaining roughly 12% of cache at size 2,048, and explores extreme 0.7% retention. Again, no adherence endpoint. **[V]** ([arXiv:2406.02069](https://arxiv.org/html/2406.02069))

Prefix/prompt caching is orthogonal: it reuses already computed prompt K/V to reduce prefill cost. Unless its cache policy also prevents eviction during decoding, it does not make the model follow the prompt more faithfully. **[I]**

### Direct instruction-retention evidence

The strongest direct paper is **Pitfalls of KV Cache Compression for Instruction-Following Models**. It converts IFEval constraints into system-prompt directives/defenses and tests Llama-3 and Qwen-2 with StreamingLLM, H2O, K-norm, SnapKV, and TOVA. It finds that semantically coupled instructions can decay at different rates: defense tokens may be evicted while a directive remains, producing leakage. Instruction order also changes survival. Whitelisting the defense span substantially improves defense/leakage behavior with little loss of the directive up to a reported compression ratio around `.7`; the paper's key results are curves rather than a single comparable recovery percentage. **[V]** ([arXiv:2510.00231](https://arxiv.org/abs/2510.00231), [opened author PDF](https://starai.cs.ucla.edu/papers/ChenArxiv25.pdf))

**MemDecay** plants facts in system and non-system regions and tests Qwen2.5-1.5B/3B. System-token attention half-lives are 148–189 decoding steps versus 14–16 for scratchpad content. Pinning system facts reaches the full-cache ceiling on 24/24 short and 21/24 long probes, while no baseline exceeds 13/24. It also exposes the cost of indiscriminate pinning: at a 50% long-context budget on Qwen-3B, overall/non-system scores are `.91/.92` full-cache, `.58/.60` H2O, and `.39/.22` for a policy that protects system content at the expense of older non-system content. **[V]** ([arXiv:2607.10582](https://arxiv.org/html/2607.10582))

VerIFY's appendix also tests a sliding-window scheme that permanently retains instruction tokens; the authors report that it can overemphasize the instruction relative to the evaluation content. This is a warning to pin instructions without also reserving fair capacity for task evidence. **[V]**

**Assessment of Stencil's 62% recovery:** it is directionally and roughly magnitude-consistent with whitelisting and system-span pinning, especially MemDecay's movement from at most 13/24 to 21–24/24. It is **not** valid to say “the literature also gets 62%,” because none of the opened papers uses Stencil's matched-control eviction gap, sessions, or aged-constraint score. **[I]** Stencil's result is currently the more directly relevant quantitative evidence for its exact setting.

## 4. Which multi-turn/long-horizon benchmarks are useful now

| Benchmark | Open? | What it measures | Published small-model baseline? | Saturation / suitability |
|---|---:|---|---|---|
| **Multi-IF** ([arXiv:2410.15553](https://arxiv.org/html/2410.15553)) | Yes | 4,501 three-turn conversations in eight languages; compatible constraints accumulate across turns | No Qwen3-1.7B-class baseline found; Llama-3.1-8B is closest | Llama-8B average falls `.688 -> .615 -> .542` from turn 1 to 3; Qwen2.5-72B `.837 -> .715 -> .609`. Good for accumulated/aged constraints; weak on explicit revocation/replacement. **[V]** |
| **SysBench** ([ICLR 2025, arXiv:2408.10943](https://arxiv.org/html/2408.10943)) | Yes | 500 system messages, five turns, aligned/misaligned and dependent/parallel user requests, 2–3 constraints | Llama-3.1-8B is closest | Llama-8B CSR/ISR/SSR is `66.5/46.9/24.9`; Qwen2.5-72B `80.4/66.2/42.8`; top SSR is only 54.4. Excellent unsaturated standing-instruction/conflict test; uses an LLM judge, reported 94% human agreement. **[V]** |
| **VerIFY** ([Findings EACL 2026](https://aclanthology.org/2026.findings-eacl.254.pdf)) | Yes | 28 exactly verifiable instruction types across 1–50 intervening turns and ten output formats | Gemma-7B is the smallest reported | About 2.8K–4.9K tokens at 50 turns. Directly measures aged constraints and has severe degradation; no instruction updates/revocations. Best exact long-horizon adherence diagnostic. **[V]** |
| **IFBench** ([NeurIPS 2025, arXiv:2507.02833](https://arxiv.org/html/2507.02833)) | Yes | 300 prompts with 58 new, out-of-distribution verifiable constraints; optional three-message rewrite form | Qwen2.5-7B reported; paper notes IFEval saturation even around 2B | Qwen2.5-7B is `74.7` on IFEval but `31.3` on IFBench before RLVR; frontier models remain below 50. Least saturated precise single-turn generalization test, but not an aging benchmark. **[V]** |
| **LIFBench** ([ACL 2025, arXiv:2411.07037](https://arxiv.org/html/2411.07037)) | Yes | 2,766 long-context instructions, 11 tasks, six context-length intervals, automated rule/rubric scoring | No 1–3B result located in the opened paper | Good long-context single-turn test; does not isolate aged or updated conversational constraints. **[V]** |
| **FollowBench** ([arXiv:2310.20410](https://arxiv.org/html/2310.20410)) | Yes | Five constraint types with difficulty levels L1–L5 | Older model set; no Qwen3-class baseline | Useful difficulty gradient, but single-turn and substantially LLM-judge based. **[V]** |
| **CFBench** ([arXiv:2408.01122](https://arxiv.org/html/2408.01122)) | Yes | Chinese-first benchmark, 1,000 examples, more than 200 scenarios, 50 tasks, ten primary constraint categories | No relevant Qwen3-1.7B baseline found | Hard constraint-following, especially strict instruction score; single-turn and language-specific. **[V]** |
| **LongMemEval** ([ICLR 2025, arXiv:2410.10813](https://arxiv.org/html/2410.10813)) | Yes | 500 long-term memory questions: extraction, multi-session reasoning, temporal reasoning, knowledge update, abstention | Not an adherence baseline | Good for changed facts/preferences and memory retrieval, but it does not score persistent output constraints. **[V]** |
| **MT-Eval** ([EMNLP 2024, arXiv:2401.16745](https://arxiv.org/html/2401.16745)) | Yes | 1,170 multi-turn queries testing recollection, expansion, refinement, and follow-up | No relevant small baseline located | Broad conversational quality, not a clean standing-constraint endpoint. **[V]** |
| **LIFEBench** ([arXiv:2505.16234](https://arxiv.org/html/2505.16234)) | Yes | 10,800 requested output lengths from 16 to 8,192 words | Multiple models, but not an aged-constraint benchmark | Useful as an explicit truncation/refusal stress test and harm endpoint, not as the primary wave test. **[V]** |

The least saturated combination for Stencil is therefore **IFBench for novel constraint generalization**, **VerIFY or SysBench for aged standing constraints**, and **Multi-IF for accumulating conversational constraints**. No single public benchmark cleanly combines long aging, addition, replacement, and revocation with exact deterministic scoring. A small registered add/revoke supplement may be scientifically justified, but it should not replace the public benchmarks. **[I]**

## 5. Activation and representation alternatives

### Verified IFEval-adjacent evidence

**Stolfo et al., “Improving Instruction-Following through Activation Steering”** derives one residual-stream vector per instruction type from the mean difference between compliant and non-compliant demonstrations, selects one layer on held-out data, and applies the vector at all generated positions. It tests Phi-3 Mini, Gemma-2-2B/9B, and Mistral-7B on augmented subsets of IFEval rather than the full official suite. Without the textual instruction, accuracy is roughly raised from about 10% to about 30%; with the instruction present, only two of four models improve. Stronger coefficients produce repetition, nonsense, factual errors, and quality loss. Representative selected layers include Phi layer 12 for length and layers 24/28 for word constraints, and Gemma-2-2B layers 22/24. **[V]** ([arXiv:2410.12877](https://arxiv.org/html/2410.12877))

**SAIF** uses sparse-autoencoder features to steer Gemma-2-2B/9B and Llama-3-8B. Its translation, summarization, and keyword tasks are inspired by IFEval but are a custom XNLI-derived test judged by GPT-4o-mini; it does not demonstrate an official IFEval gain. In a representative sweep, fewer than five features have almost no effect, around 15 features reaches roughly `.70` loose and `.25` strict success, and 30 features can decline. **[V]** ([arXiv:2502.11356](https://arxiv.org/html/2502.11356))

**Apple's representation-engineering study** reports improvement over random steering on a modified IFEval-Simple task without a broad quality compromise, but generalization across instruction types is poor. I opened the official Apple research page; the OpenReview PDF was unavailable during this pass, so I do not quote an exact table number. **[V for the qualitative official-page claim; exact effect unverified]** ([official page](https://machinelearning.apple.com/research/do-llms-know-internally), [OpenReview record](https://openreview.net/forum?id=qIN5VDdEOr))

ITI-style head intervention was introduced for truthfulness, and classic representation engineering/in-context-vector papers test behavior, style, truthfulness, sentiment, or task induction. I found no opened primary result showing an official IFEval gain on a Qwen3-1.7B-class model. They should not be presented as documented IFEval fixes. **[V: scope check of the opened instruction-steering sources]**

### Implication for Stencil

Residual steering is not a free escape from degeneration. It moves the intervention from attention probabilities to the residual stream, but the same strength/quality frontier remains. Its advantages are that only one causally selected layer need be modified and strength can be bounded continuously; its disadvantage is that instruction-specific vectors do not generalize reliably. **[V/I]** A residual alternative is worth a third-line experiment, not the first rescue attempt.

## 6. Legitimate decoding-time treatment of truncation and repetition

A hidden repetition penalty is unacceptable because it directly modifies the probability of history-matching tokens—the exact failure endpoint attributed to the wave. It can improve completion length or strict formatting independently of instruction selection, making any treatment effect uninterpretable. It may also hurt legitimate repeated strings, counts, JSON keys, quotation, or phrase-frequency constraints. **[I]**

Legitimate options are:

1. **Use the same larger `max_new_tokens` in every arm**, chosen before unblinding, and report EOS completion, max-cap termination, tokens generated, repeated n-gram rate, and strict instruction score separately. This removes an infrastructure ceiling without preferentially repairing the wave arm. **[I]**
2. **Make a base-model plausibility gate part of the registered mechanism.** DIRECTER supplies the precedent: compare the proposed steered token to the unsteered distribution and fall back/reduce intervention when its base probability is below a fixed ratio. This is scientifically interpretable as a trust region on wave control, not a generic anti-repetition patch. **[V/I]**
3. **If nucleus, contrastive, or another decoder is studied, use a fully crossed factorial design**: base versus wave under the same decoder settings and seeds, with the wave-by-decoder interaction reported. Holtzman et al. show that likelihood-maximizing decoding can produce repetitive text, and contrastive decoding/search papers reduce degeneration in open-ended generation, but none establishes an instruction-adherence benefit here. **[V/I]** ([nucleus sampling, arXiv:1904.09751](https://arxiv.org/abs/1904.09751), [contrastive search, arXiv:2210.14140](https://arxiv.org/abs/2210.14140), [contrastive decoding, arXiv:2210.15097](https://arxiv.org/abs/2210.15097))
4. **Use hard constrained decoding only as a separately named method** for constraints that are mechanically expressible. It is a valid product intervention but cannot be credited to the wave mechanism. **[I]**
5. **Use a repetition/truncation detector as a stop-loss or diagnostic, not as evidence of score improvement.** Its triggered cases must still count as wave failures in the primary analysis. **[I]**

## 7. Citation table: exact opened-source results

“Named IF?” means an actual IFEval/IFBench/Multi-IF/FollowBench/LIFBench-family score, not a custom task merely described as instruction following.

| Paper | Year / venue / ID | Opened source | Exact reported result used here | Named IF? / intervention selectivity |
|---|---|---|---|---|
| PASTA | ICLR 2024, arXiv:2311.02262 | [HTML](https://arxiv.org/html/2311.02262) | LLaMA-7B custom-task avg `73.45 -> 85.89 -> 95.46`; GPT-J `59.65 -> 77.80 -> 85.22` | No; profiled subset, `alpha=.01`, roughly 50–100 heads best |
| AutoPASTA | 2024, arXiv:2409.10790 | [HTML](https://arxiv.org/html/2409.10790) | Llama-3-70B-Instruct open-book QA average +7.95% | No; selected sentence and heads, `delta=log(100)` |
| Attention Instruction | 2024, arXiv:2406.17095 | [HTML](https://arxiv.org/html/2406.17095) | Llama-2 multi-document QA about +4 to +10 points; wrong document about -25 points | No; prompt-only document identifier |
| Attention Buckets | 2023/24, arXiv:2312.04455 | [HTML](https://arxiv.org/html/2312.04455) | ToolBench pass/win `67.3/63.1 -> 71.3/71.5` | No; multiple RoPE/output streams |
| SpotLight | EACL 2026, arXiv:2505.12025 | [HTML](https://arxiv.org/html/2505.12025) | Rewritten IFEval Qwen2.5-3B `.42/.53 -> .53/.62`; final-turn MT-IFEval +25.7% relative | Yes, but rewritten/new datasets; all heads/layers, `tau=.1` |
| DIRECTER | 2026, arXiv:2603.06745 | [HTML](https://arxiv.org/html/2603.06745) | Llama-8B rewritten IFEval `73.5/81.5 -> 78.8/84.8`; Qwen2.5-3B mean `63.9 -> 67.1` | Yes, rewritten; dynamic selected layers, `alpha=100`, `beta=.5` |
| SPA | 2024, arXiv:2408.09121 | [HTML](https://arxiv.org/html/2408.09121) | CodeGen-350M HumanEval `15.3 -> 20.1`, MBPP `19.6 -> 27.4` | No; output-stream mixture |
| Found in the Middle | 2024, arXiv:2406.16008 | [HTML](https://arxiv.org/html/2406.16008) | NQ Recall@3 `.3638 -> .7427` (10 docs), `.2052 -> .6832` (20 docs) | No; position-calibrated attention |
| Ms-PoE | 2024, arXiv:2403.04797 | [HTML](https://arxiv.org/html/2403.04797) | ZeroSCROLLS Vicuna-7B `15.0 -> 18.8`; head-aware MDQA `65.3` vs uniform `63.1` | Long-context, not IF; head-specific RoPE scales |
| CAD | 2023, arXiv:2305.14739 | [HTML](https://arxiv.org/html/2305.14739) | LLaMA-30B CNN/DM ROUGE-L +21% relative | No; context/no-context logit contrast |
| InstABoost | 2026 revision, arXiv:2506.13734 | [HTML](https://arxiv.org/html/2506.13734) | Five task-type successes `.925/.880/.594/.625/.620`; high dose loses relevance/fluency | No; fixed all-layer/head bias, validation-tuned small multiplier |
| Activation steering (Stolfo et al.) | ICLR 2025, arXiv:2410.12877 | [HTML](https://arxiv.org/html/2410.12877) | Without instruction, augmented-subset accuracy roughly `10% -> 30%`; with instruction only 2/4 models improve | Modified IFEval subsets; one selected residual layer |
| SAIF | 2025, arXiv:2502.11356 | [HTML](https://arxiv.org/html/2502.11356) | Representative 15-feature setting roughly `.70` loose / `.25` strict; 30 can decline | No official IFEval; selected SAE features |
| VerIFY / IGA | Findings EACL 2026 | [PDF](https://aclanthology.org/2026.findings-eacl.254.pdf) | Gemma-7B avg `56.67 -> 40.95`; Gemma-2-27B `46.43 -> 83.12`; `alpha>.6` incoherent | Exact aged constraints; all-head/layer two-stream attention |
| Attention entropy collapse | ICML 2023, arXiv:2303.06296 | [HTML](https://arxiv.org/html/2303.06296) | Low-temperature attention intervention reduces training accuracy/can destabilize | Not IF; training evidence only |
| StreamingLLM | ICLR 2024, arXiv:2309.17453 | [HTML](https://arxiv.org/html/2309.17453) | Llama-13B window PPL `58.07` vs 4-sink PPL `5.40`; Llama-7B ARC `3.58/1.39 -> 71.34/55.03` | No adherence; 4 sink tokens + recent window |
| H2O | NeurIPS 2023, arXiv:2306.14048 | [HTML](https://arxiv.org/html/2306.14048) | OPT-30B full/H2O at 20%: COPA `85/84`, OBQA `43.2/43.0` | No adherence; heavy hitters + recent |
| SnapKV | 2024, arXiv:2404.14469 | [HTML](https://arxiv.org/html/2404.14469) | 1,024 entries/about 92% compression retains LongBench well; 4,096/about 68% nearly lossless | No adherence; observation-window selection |
| PyramidKV | 2024, arXiv:2406.02069 | [HTML](https://arxiv.org/html/2406.02069) | Size 2,048/about 12% retained is comparable to full on LongBench | No adherence; layer-pyramidal budget |
| KV compression pitfalls | 2025/26, arXiv:2510.00231 | [PDF](https://starai.cs.ucla.edu/papers/ChenArxiv25.pdf) | Whitelisting defense tokens preserves defense/leakage with little directive loss to compression ratio about `.7` | Yes, converted IFEval instructions; token whitelist |
| MemDecay | 2026, arXiv:2607.10582 | [HTML](https://arxiv.org/html/2607.10582) | Pinned system facts `24/24` short, `21/24` long vs no baseline above `13/24` | Planted memory/adherence probes; system pinning |
| Multi-IF | 2024, arXiv:2410.15553 | [HTML](https://arxiv.org/html/2410.15553) | Llama-8B turn averages `.688/.615/.542`; Qwen-72B `.837/.715/.609` | Yes; three-turn accumulated constraints |
| SysBench | ICLR 2025, arXiv:2408.10943 | [HTML](https://arxiv.org/html/2408.10943) | Llama-8B CSR/ISR/SSR `66.5/46.9/24.9`; top SSR 54.4 | Yes; five-turn system/user conflicts |
| IFBench | NeurIPS 2025, arXiv:2507.02833 | [HTML](https://arxiv.org/html/2507.02833) | Qwen2.5-7B IFEval/IFBench `74.7/31.3`; after RLVR `89.1/45.9` | Yes; 58 novel constraints, mostly single-turn |
| LIFBench | ACL 2025, arXiv:2411.07037 | [HTML](https://arxiv.org/html/2411.07037) | 2,766 instructions, 11 tasks, six length intervals | Yes; long single-turn context |
| LongMemEval | ICLR 2025, arXiv:2410.10813 | [HTML](https://arxiv.org/html/2410.10813) | 500 questions spanning five long-term-memory abilities | No output-adherence score; includes knowledge update |

## 8. Ranked redesigns

### 1. Make the wave select what survives: ledger-controlled, budget-fair KV retention

**Change.** Stop adding attention bias. Have the 264K controller emit retention priority for currently active ledger spans. Pin their K/V through eviction while reserving fixed capacity for recent tokens, task evidence, and non-instruction heavy hitters. Add explicit ledger operations for `add`, `satisfy`, `replace`, and `revoke`; revoked spans immediately lose protection. Preserve positions exactly as in the successful Stencil pinning experiment.

**Why it should not degenerate.** It changes availability, not the model's native attention distribution. If an instruction is irrelevant at a decoding step, the model remains free to assign it low mass. A fair non-instruction reserve addresses MemDecay's and VerIFY's warning that indiscriminate system/instruction pinning can evict task evidence. **[V/I]**

**Benchmark.** Primary: late-turn exact instruction-level score on Multi-IF, clustered by conversation. Secondary: SysBench SSR and a small registered add/replace/revoke supplement; VerIFY at 25 and 50 turns as an aging stress test. Official unchanged IFEval should be a negative control: little or no gain is expected when there is no eviction pressure.

**Preregistered proof gate.** Against a cache-size- and recency-matched eviction control: at least **+5.0 absolute points** on the late-turn primary, with a conversation-clustered 95% CI wholly above zero; at least 50% of the full-cache gap recovered; truncation no more than +1.0 point, repeated-output failure no more than +1.0 point, and task-answer quality non-inferior by a predeclared 2-point margin. Report the result even if the harm gate fails.

**Expected effect.** **5–15 points on pressure-exposed late turns [I]**, based primarily on Stencil's own verified +20-point matched-control result and 62% gap recovery. External evidence supports direction, not this numerical interval: MemDecay reports at most 13/24 to 21–24/24 on planted system facts, and the KV-pitfalls paper shows large whitelisting gains in its curves. Do not expect a single-turn IFEval improvement.

**Falsifier.** If the active span is demonstrably present in cache, native attention can retrieve it in full-cache controls, and pinning's 95% CI rules out a +2-point late-turn benefit under real eviction pressure, then “wave selection through memory availability” is practically falsified for this model. If it helps only static constraints but fails registered replacement/revocation, the ledger-selection claim is falsified even if simple pinning remains useful.

### 2. Replace exact all-head dosing with a DIRECTER-style sparse trust-region controller

**Change.** On a development split, causally rank `(layer, head)` sites by the paired change in strict constraint success when only that site receives an instruction-span perturbation. Freeze a small set—initially at most 5–10% of heads and no more than two late/mid layers. At decoding time:

- steer only the currently active minimal ledger span;
- cap each selected head's mass increase (development candidates: `+0.02` absolute and `tau<=.10`) and cap attention KL from baseline;
- preserve within-span score ordering;
- compare the proposed token with an unsteered shadow distribution;
- accept it only when `p_base(proposed) >= 0.5 * p_base(base_top1)`; otherwise halve the active site set or emit the base token.

This is a wave mechanism with an explicit trust region. The threshold and fallback must be frozen before the sealed run.

**Why it should not degenerate.** Unneeded heads are untouched, the correction cannot explode when natural mass is nearly zero, and a token that the base model finds implausible cannot be repeatedly fed back into generation. This combines PASTA's head selectivity with DIRECTER's strongest ablated safeguard. **[V/I]**

**Benchmark.** Primary: official, unchanged IFBench strict score, because it is unsaturated and exact. Confirmatory: official unchanged IFEval and Multi-IF turn 3. Use the same decoder and generation ceiling in every arm.

**Preregistered proof gate.** At least **+2.0 absolute points** on IFBench with paired 95% CI above zero; same-sign effect on Multi-IF turn 3; no more than +1.0 point truncation or repetition, and no material task-answer regression. Head/layer profiling rows must be disjoint from evaluation rows. Compare against an equally sparse random-site control and against the old exact-odds hook.

**Expected effect.** **2–4 points [I]** on a small model. The anchor is DIRECTER's +3.2-point rewritten-IFEval mean on Qwen2.5-3B, +2.0 on Qwen2.5-7B, and only +0.3 on Llama-1B. The expected interval deliberately discounts the rewritten prompts and smaller Qwen3-1.7B capacity.

**Falsifier.** If causal sites change attention as intended and pass the plausibility/harm gates, yet two exact public benchmarks both have 95% upper bounds below +2 points, then the useful effect of attention-wave amplitude control is falsified for frozen Qwen3-1.7B. Continuing to search doses after that would be post hoc mechanism rescue.

### 3. Move the control surface to one residual layer with constraint-specific, mean-matched vectors

**Change.** Learn small residual vectors for a limited, preregistered set of verifiable constraint families (length, casing, JSON/schema, inclusion/exclusion). Select one causally effective layer per family on development data. Let the controller emit only a bounded scalar that moves the current residual toward the compliant-example mean; activate it only while the relevant ledger item is active and the unsteered representation is below a frozen deficit threshold. Apply no attention bias.

**Why it may degenerate less.** One intervention site avoids forcing every head and avoids eight consecutive corrections. Mean matching gives a natural cap rather than an unbounded logit shift. It can still degenerate at high strength, so a base-logit plausibility gate and a held-out fluency/non-inferiority gate remain mandatory. **[V/I]**

**Benchmark.** Primary: the matching official IFBench constraint families; confirm on official IFEval subsets selected before training vectors. Use Multi-IF only for constraint families whose ledger state can be carried across turns.

**Preregistered proof gate.** At least **+2.0 points** macro-averaged across the frozen families with a paired CI above zero, improvement in at least half the individual families, and no more than 2 points task-quality loss or +1 point truncation/repetition. Include random-vector, wrong-family-vector, and no-vector controls.

**Expected effect.** **0–3 points [I], with high risk of zero.** Stolfo et al. improve the with-instruction setting in only two of four models and document a quality frontier; SAIF and Apple's study use modified/custom tasks. This is ranked third because no opened source shows a robust official-IFEval gain on a model this small.

**Falsifier.** If correct-family vectors measurably move the representation toward compliant states but do not improve exact compliance, or if every effective strength violates the quality gate, then the “wave as an activation selector” version is falsified for those constraint families.

## 9. What to run first

Run **redesign 1, pinning-only**, before another attention-dose search. It has the strongest Stencil evidence, the cleanest causal interpretation, and the lowest degeneration risk.

### First experiment

Use the existing 909-conversation, three-turn Multi-IF base with one fixed generation ceiling large enough that ordinary base truncation is not the dominant endpoint (for example 2,048, applied identically to all arms). Freeze four arms:

1. matched eviction control;
2. generic cache policy at the same budget (for example H2O-like heavy-hitter + recent);
3. active-ledger pinning with a fixed fair reserve for non-instruction evidence;
4. full cache, as the recoverable-gap ceiling.

Do **not** include attention bias in the first confirmatory run; its independent effect is already known to be harmful in the pinning setting. First run a small disjoint development/shadow set only to validate artifact fields and select the fixed budget split, then seal the complete evaluation. The primary estimand is `(ledger pin - matched eviction)` on turn-3 strict instruction accuracy, with conversation-clustered uncertainty. The secondary estimand is fraction of the full-cache gap recovered. Truncation, EOS, repeated n-grams, task correctness, per-ledger-item age, retention status, and natural attention to each retained span must be written per work item in the same run.

If that passes, test redesign 2 on official IFBench and unchanged IFEval before taking it into Multi-IF. If it fails with a narrow confidence interval, do not compensate by opening another dose grid: move once to the third, different control surface, then apply the global falsification rule below.

### Global stop rule for the wave hypothesis

The narrow single-turn all-head-bias hypothesis is already closed. For the broader hypothesis—“a learned wave-like selector can improve frozen Qwen3-1.7B adherence”—declare it practically falsified if:

1. ledger retention under verified eviction pressure rules out a +2-point late-turn benefit;
2. sparse trust-region attention steering rules out a +2-point benefit on both IFBench and an aged-constraint benchmark; and
3. the best preregistered residual selector either rules out +2 points or can achieve it only by violating the truncation/repetition/task-quality gates.

That stop rule distinguishes “no evidence” from “evidence of no practically useful effect” by requiring reasonably narrow confidence intervals and confirming that each intervention actually changed its intended intermediate variable. It also prevents degeneration from being traded silently for a nominal constraint-score gain.

## Bottom line

The best-supported next move is not a stronger wave. It is a **different meaning of selection**: keep active instructions available in the KV cache while leaving native attention intact. If amplitude steering is revisited, the literature's successful pattern is sparse causal sites, a small bounded dose, minimal active spans, and a per-token base-model trust region. A decoder-side repetition penalty would obscure the causal question. A clean failure of retention, safe sparse steering, and one-layer activation selection—under registered harm gates and with verified intermediate effects—would be sufficient reason to retire the wave hypothesis for frozen Qwen3-1.7B rather than search indefinitely for another dose.
