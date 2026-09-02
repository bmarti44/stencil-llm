# Deep research — kimi-k3 with web tools (2026-09-02); 61 tool calls

# Stencil research report: how to make the wave mechanism actually improve benchmark scores

**Date:** 2026-09-02 · **Author:** kimi-k3 (cross-model researcher) · **Sources opened:** 25 (arXiv abstract pages, arXiv API full abstracts, GitHub README). Each citation below is marked **VERIFIED** (I fetched the source and quote what I saw) or **UNVERIFIED** (memory / inferred from truncated text). Where a number is UNVERIFIED I flag it inline.

---

## 0. Executive summary

1. **The published attention-steering literature never uses anything close to our parameterization.** Every verified success case (PASTA, AutoPASTA, ZeroTuning, ACT, CAD, ITI, function vectors) uses (a) a **tiny dose** (PASTA's config uses logit-scale biases ~0.01 — UNVERIFIED exact value, config structure VERIFIED), and/or (b) a **small, profiled subset of heads** (PASTA VERIFIED "identifies a small subset of attention heads"; ITI VERIFIED "a limited number of attention heads"; function vectors VERIFIED "small number of attention heads"), and/or (c) **middle/early layers** (function vectors VERIFIED "middle layers"), and/or (d) **relative reweighting** (downweight the rest instead of upweighting the target — ACT's "calibration" mechanism, VERIFIED). Our uniform-over-span, all-head, layers-20–27 bias violates all four priors at once. The 4× truncation increase and 13/20 degeneration on pinned columns is exactly what the degeneration literature predicts for that corner of design space (DITTO self-reinforcement, VERIFIED; softmax-dispersal limits, VERIFIED).
2. **Notably: none of the attention-steering papers I could verify report IFEval/IFBench/Multi-IF adherence gains.** Documented gains are on QA, factuality, long-context retrieval, and instruction-preference benchmarks. Our null single-turn result is therefore *consistent with the literature*, not a contradiction of it. Adherence is the hardest metric for these methods because it is most sensitive to degeneration.
3. **KV-side work now has direct adherence evidence**: the ACL-2026 "Pitfalls of KV Cache Compression" paper (VERIFIED) measures IFEval adherence under five eviction methods and finds some instructions are "completely ignored" — i.e., instruction tokens are disproportionately lost under compression. This supports the KV-pinning line (our +20 pts / 62% recovery) as the *proven* wing of the project, and the Pitfalls paper is the right comparison/citation for it.
4. **Best benchmark targets: Multi-IF (VERIFIED open, verifier-based, unsaturated, turn-indexed — o1-preview drops 0.877→0.707 from turn 1 to turn 3, so a 1.7B model is nowhere near ceiling) and IFBench (VERIFIED design goal: models overfit IFEval's small constraint set and fail to generalize to 58-style new constraints — the "58" count is UNVERIFIED, the overfitting finding is VERIFIED).**
5. **Recommendation**: run redesign R2 (wave-as-selector, context-as-carrier) first — it is cheapest, cannot degenerate, and its result discriminates "the model can't find the constraint" from "the model finds it but doesn't comply," which determines whether R1/R3 are even coherent.

---

## 1. Citation table

| # | Paper | Year | arXiv / URL opened | Number/claim quoted | Benchmark | Status |
|---|-------|------|--------------------|---------------------|-----------|--------|
| 1 | PASTA — Tell Your Model Where to Attend (Zhang et al.) | 2023/24 | arxiv.org/abs/2311.02262 | "identifies a small subset of attention heads and applies precise attention reweighting on them… Like prompting" | multiple (JSON/QA/reasoning — names UNVERIFIED) | **VERIFIED** (mechanism); headline "+22% avg for LLaMA-7B" **UNVERIFIED** (abstract truncated before number; from memory) |
| 2 | PASTA code repo | 2024 | github.com/QingruZhang/PASTA | requires no weight changes, no added inference time; has `head_config` directory | — | **VERIFIED** (repo structure); α=0.01, ~16 heads, early-layer placement, `scale_position="exclude"` **UNVERIFIED** (truncated before config listing; from memory of repo/paper) |
| 3 | AutoPASTA — Model Tells Itself Where to Attend | 2024 | arxiv.org/abs/2409.10790 (+API full abstract) | "an average improvement of 7.95% for LLAMA3-70B-Instruct"; automatically identifies key context, steers attention scores, no param changes | open-book QA | **VERIFIED** |
| 4 | ZeroTuning (Han et al.) | 2025/26 | arxiv.org/abs/2505.11739 | intervenes only on the initial (BOS) token; "lightweight biases to this token's attention logits systematically shifts and reshapes downstream attention patterns," amplified by attention-sink role | classification/QA | **VERIFIED** (mechanism); "+19.9% relative on Llama-3.1-8B" **UNVERIFIED** (memory; truncated) |
| 5 | Found in the Middle — ACT (Hsieh et al.) | 2024 | arXiv API id 2406.16008 | U-shaped positional attention bias; calibration ("found-in-the-middle") "outperforming existing methods by up to 15 percentage points" | long-context retrieval / RAG | **VERIFIED** |
| 6 | Attention Instruction (Zhang, Meng, Collier) | 2024 | arXiv API id 2406.17095 | models "do not have relative position awareness" but "demonstrate the capacity to adapt attention to a specific segment using matching indexes" | multi-doc QA | **VERIFIED** |
| 7 | Context-aware decoding (Shi et al.) | 2023 | arxiv.org/abs/2305.14739 | "14.3% gain for LLaMA in factuality metrics" from with/without-context contrastive decoding | summarization factuality | **VERIFIED** |
| 8 | H2O (Zhang et al.) | 2023 | arxiv.org/abs/2306.14048 | "a small portion of tokens contributes most of the value when computing attention scores" (heavy hitters) | efficiency/perplexity | **VERIFIED** (concept); "20% of KV" **UNVERIFIED** |
| 9 | SnapKV (Li et al.) | 2024 | arxiv.org/abs/2404.14469 | per-head consistent prompt-attention patterns observed from an end-of-prompt "observation window"; auto-selects KV clusters | LongBench/NIAH (names UNVERIFIED) | **VERIFIED** (mechanism); "3.6× speed / 380K ctx" **UNVERIFIED** |
| 10 | PyramidKV (Cai et al.) | 2024 | arxiv.org/abs/2406.02069 | attention "scattering widely in lower layers… ultimately focusing on critical tokens (a.k.a massive activation or attention sink) in higher layers"; allocate more cache to lower layers | LongBench/TREC/NIAH | **VERIFIED** (funnel + method); "matches full KV at 12%, +20.5 TREC at <0.7%" **UNVERIFIED** |
| 11 | StreamingLLM (Xiao et al.) | 2023 | arxiv.org/abs/2309.17453 | attention sink: keeping initial-token KV "will largely recover the performance of window attention"; sinks emerge "even if they are not semantically important" | streaming perplexity | **VERIFIED** |
| 12 | Pitfalls of KV Cache Compression (Chen et al.) | 2025/26 | arxiv.org/abs/2510.00231 | StreamingLLM, SnapKV, TOVA, H2O, K-Norm on Llama-3.1-8B / Qwen2.5-14B "under multi-instruction prompting with IFEval"; "certain instructions degrade much more rapidly with compression, effectively causing them to be completely ignored" | IFEval (multi-instruction) + system-prompt leakage | **VERIFIED** — the only located paper measuring instruction adherence under KV eviction |
| 13 | Multi-IF (He et al., Meta) | 2024 | arxiv.org/abs/2410.15553 | 4,501 conversations × 3 turns, 8 languages; 14 LLMs; "o1-preview drops from 0.877 at the first turn to 0.707 at the third turn"; code released | turn-3 instruction accuracy | **VERIFIED** |
| 14 | IFBench — Generalizing Verifiable Instruction Following (Pyatkin et al., AI2) | 2025 | arxiv.org/abs/2507.02833 | "most models strongly overfit on a small set of verifiable constraints… not able to generalize well to unseen output constraints"; gives "abrakadabra ≥3 times" as example constraint type | new verifiable-constraint benchmark | **VERIFIED** (finding); "58 new OOD constraints" **UNVERIFIED** |
| 15 | SysBench (Qin et al.) | 2024 | arxiv.org/abs/2408.10943 | three diagnosed limits: "constraint violation, instruction misjudgement and multi-turn instability" | system-message following | **VERIFIED** (taxonomy); "500 cases" UNVERIFIED |
| 16 | FollowBench (Jiang et al.) | 2023/24 | arxiv.org/abs/2310.20410 | five constraint types (Content, Situation, Style, Format, Example); multi-level difficulty by incrementally adding one constraint | constraint satisfaction | **VERIFIED** |
| 17 | CFBench (Zhang et al.) | 2024 | arxiv.org/abs/2408.01122 | 1,000 curated samples, 200+ real-life scenarios, 50+ NLP tasks, 10 primary / 25+ subcategories | complex constraint following | **VERIFIED** |
| 18 | LongMemEval (Wu et al.) | 2024 | arxiv.org/abs/2410.10813 | 500 questions over chat histories; "30% accuracy drop on memorizing information across sustained interactions" | long-term memory | **VERIFIED** |
| 19 | MT-Eval (Kwan et al.) | 2024 | arxiv.org/abs/2401.16745 | 1,170 multi-turn queries; single-turn versions built for comparison; recollection/expansion/refinement/follow-up | multi-turn ability | **VERIFIED** |
| 20 | LLMs Get Lost in Multi-Turn Conversation (Laban et al.) | 2025 | arxiv.org/abs/2505.06120 | "average drop of 39% across six generation tasks" single→multi-turn; 200k+ conversations; minor aptitude loss + significant *unreliability* | simulated underspecified conversations | **VERIFIED** |
| 21 | Softmax is Not Enough (Veličković et al.) | 2024/25 | arxiv.org/abs/2410.01104 | "even for tasks as simple as finding the maximum key, any learned circuitry must disperse as the number of items grows at test time" — softmax cannot stay sharp as n grows | algorithmic generalization | **VERIFIED** |
| 22 | Curious Case of Neural Text Degeneration (Holtzman et al.) | 2019 | arxiv.org/abs/1904.09751 | likelihood-as-decoding-objective → "bland and strangely repetitive" text; "decoding strategies alone can dramatically affect the quality" | open-ended generation | **VERIFIED** |
| 23 | Learning to Break the Loop / DITTO (Xu et al.) | 2022 | arXiv API id 2206.02369 | "self-reinforcement effect: the more times a sentence is repeated in the context, the higher the probability of continuing to generate that sentence"; higher initial probability → stronger self-reinforcement | repetition | **VERIFIED** |
| 24 | Repetition In Repetition Out (Li et al.) | 2023 | arxiv.org/abs/2310.10226 | degeneration correlates with repetition in training data; "selectively dropping out the attention to repetitive words in training data" significantly minimizes degeneration | repetition | **VERIFIED** |
| 25 | Unlikelihood Training (Welleck et al.) | 2019 | arxiv.org/abs/1908.04319 | likelihood objective over-assigns probability to repeats; unlikelihood training beats nucleus/beam-blocking in human eval under greedy/beam | repetition | **VERIFIED** |
| 26 | ITI — Inference-Time Intervention (Li et al.) | 2023/24 | arxiv.org/abs/2306.03341 | Alpaca truthfulness 32.5%→65.1%; shifts activations "across a limited number of attention heads"; truthfulness/helpfulness tradeoff tuned by strength; needs only few hundred examples | TruthfulQA | **VERIFIED** |
| 27 | In-context Vectors (Liu et al.) | 2023/24 | arxiv.org/abs/2311.06668 | build task vector from a forward pass on demonstrations; shift latent states at new queries; improves control | ICL/formatting tasks (names UNVERIFIED) | **VERIFIED** (mechanism) |
| 28 | Representation Engineering (Zou et al.) | 2023 | arxiv.org/abs/2310.01405 | population-level representation monitoring/manipulation for concepts like honesty | concept control | **VERIFIED** (qualitative) |
| 29 | Function Vectors (Todd et al.) | 2023/24 | arxiv.org/abs/2310.15213 | "a small number of attention heads transport a compact representation of the demonstrated task"; FVs trigger zero-shot task execution; "strong causal effects across settings in middle layers" | ICL tasks | **VERIFIED** |
| 30 | Contrastive Activation Addition (Panickssery et al.) | 2023/24 | arxiv.org/abs/2312.06681 | steering vectors from contrast-pair mean differences; "effective over and on top of traditional methods like finetuning and system prompt design, and minimally reduces capabilities" | behavioral MC + open-ended | **VERIFIED** |
| 31 | Refusal Is Mediated by a Single Direction (Arditi et al.) | 2024 | arxiv.org/abs/2406.11717 | refusal is "a one-dimensional subspace" across 13 chat models ≤72B; erasing the direction disables refusal; adding it elicits refusal on harmless prompts | refusal behavior | **VERIFIED** |
| 32 | Qwen3 Technical Report | 2025 | arxiv.org/abs/2505.09388 | family spans 0.6B–235B | — | **VERIFIED** (existence); per-size IFEval numbers **UNVERIFIED** |

**Could not locate / not verified under the names given:** "attention buckets" (no paper under that name — likely a blog term; two searches returned nothing), "SPA" (ambiguous), "LLMs are not robust to buried instructions" (no such title found; the real underlying result is lost-in-the-middle, which is covered by #5), "Direct Instruction Steering" (not found), any **SAE-steering paper with IFEval numbers** (search surfaced only titles, e.g. 2411.02193 "Improving Steering Vectors by Targeting Sparse Autoencoder Features" and 2503.00177 — neither opened, none mention IFEval; treat "no published SAE→IFEval result exists" as a verified gap for our purposes).

---

## 2. Q1/Q2 combined: what the steering literature actually does, and why our corner of it degenerates

### The dose/layer/head pattern across verified methods

| Method | Dose | Heads | Layers | Reweight style | Verified status |
|---|---|---|---|---|---|
| PASTA | logit bias ~0.01 (UNVERIFIED exact) | small profiled subset (VERIFIED) | early–mid (UNVERIFIED exact) | relative: emphasize selected span by scaling others down (UNVERIFIED mechanism detail) | mixture |
| AutoPASTA | small | subset (VERIFIED: "steering an LLM's attention scores" after auto-identifying key context) | — | additive on auto-selected spans | VERIFIED mechanism |
| ZeroTuning | "lightweight biases" (VERIFIED wording) | n/a — intervenes on a single *token* (BOS) (VERIFIED) | all (via sink propagation) | bias on initial token reshapes downstream attention (VERIFIED) | VERIFIED |
| ACT | calibration scale | all, but as renormalization (VERIFIED "calibration mechanism") | — | **renormalizing**, removes U-bias rather than adding new bias | VERIFIED |
| ITI | tunable strength | "a limited number of attention heads" (VERIFIED) | selected | activation shift | VERIFIED |
| Function vectors | model-internal | "small number of attention heads" (VERIFIED) | **middle layers** show the strongest causal effects (VERIFIED) | activation | VERIFIED |
| CAD | α-weighted logit contrast | n/a (decoding-level) | n/a | contrastive logit difference | VERIFIED |

**Recipe distilled from verified sources:** few heads (or one token, or normalization), small coefficients, middle layers, relative rather than absolute change, and span selection done by the model itself (AutoPASTA) or by salience — which our ledger already provides.

### Why uniform-over-span, all-head, layers-20–27 degenerates — synthesized mechanism

1. **Late layers are the funnel's nozzle.** PyramidKV's verified finding: attention is scattered in early layers and *consolidates onto a few critical tokens / sinks in higher layers*. Heads at layers 20–27 in a 28-layer model are precisely where attention is already low-entropy. Adding a uniform bias across an instruction span there doesn't "add information"; it fights the consolidation the generation pathway depends on. You are rewiring the stage where the model has the least slack.
2. **Softmax dispersion bounds work against blunt boosts.** Veličković et al. (VERIFIED): attention scores cannot maintain sharp decisions as the number of attended items grows — there is a dispersal pressure. Forcing ~equal mass onto a *span* of columns is the sharpness direction, at the exact layers where the model is on the sharp edge; the adjacent query positions inherit distorted distributions → the argmax path perturbs → loops.
3. **Repetition is self-reinforcing and attention-mediated (both VERIFIED).** DITTO: repeated sentences raise the probability of their own next repetition, with stronger effect for higher-initial-probability text. Repetition-In-Repetition-Out: *dropping attention to repetitive tokens* reduces degeneration — our method does the opposite whenever the boosted span contains repeated content (instruction spans do: constraint keywords repeat). A uniform boost on a span with internal repetition is the published mechanism for producing loops, run in reverse.
4. **Head heterogeneity is the norm.** SnapKV (VERIFIED): each head attends consistently to *different* prompt features during generation. Uniformly biasing all heads therefore pushes the heads whose natural job is *not* the instruction span off their job — the aggregate effect is less "everyone reads the instruction" and more "nonspecialist heads get hijacked," which is a classic route to incoherence.
5. **Degeneration then shows up as truncation at max_new**, matching both our sealed-conf 4× truncation result and the 13/20 pinned+bias degeneration: loops consume the token budget. (Our Multi-IF base at 10% truncation even *without* the wave shows the trunk is already near this cliff; Laban et al.'s VERIFIED 39%-drop / "unreliability" finding says this is a general multi-turn phenomenon, not specific to us.)

**Consistency check on our sealed result:** +0.39 pts with a large degeneration side effect is exactly the expected outcome of an over-dosed, over-broad bias in late layers *per the above*; it is not evidence that attentional selection per se is useless — the literature only ever claims wins at ~1–2 orders of magnitude lower dose on a tiny head subset.

---

## 3. Q3: KV retention of instructions — where our 62% sits

- **Direct evidence exists that instruction tokens are disproportionately harmed by eviction** (VERIFIED): Chen et al. evaluate StreamingLLM, SnapKV, TOVA, H2O, K-Norm with multi-instruction IFEval prompts on 8B/14B models and show some constraints are "completely ignored" under compression. This is the paper to cite for the *motivation* of pinning.
- **Selection of *which* columns to keep should be per-head and from the generation end**, per SnapKV (VERIFIED: consistent per-head attention patterns recoverable from an end-of-prompt observation window) and PyramidKV (VERIFIED: layer-wise non-uniform budgets). Our current pinning pins a semantic span uniformly — a SnapKV-style "keep what the observation window says the heads will need" could raise recovery without touching decoding.
- **Sink bookkeeping matters** (StreamingLLM VERIFIED): if pinned instruction columns are at non-initial positions, sink heads still route mass to position 0; pinning doesn't change *routing*, only *availability*. This explains why pinning alone recovers only ~62%: the columns are present, but the attention *distribution* on them under an aged context (with many competing recent tokens and sinks) is still attenuated.
- **Is 62% in line with the literature?** Honest answer: there is no published "percent of adherence gap recovered" number to compare against (the Pitfalls paper reports the degradation side qualitatively, VERIFIED; the retrieval-side recovery numbers from SnapKV/PyramidKV are UNVERIFIED from memory). So: 62% is *plausible and in-family* for an availability-only fix; the remaining ~38% gap is most likely *distribution* (attention doesn't flow to the retained columns) — which is exactly the deficiency the wave was supposed to fix, and exactly where the dosed-down redesign (R1 below) has its best shot.

---

## 4. Q4: benchmarks — fit, openness, saturation

| Benchmark | Open | Verifier-based | Aged/updated constraints | Fit for 1.7B-class | Saturation | Status |
|---|---|---|---|---|---|---|
| **Multi-IF** | VERIFIED (code+prompts released) | VERIFIED (IFEval-derived checkers) | **Yes — turn-indexed, turn-3 constraints age** | **Yes; we have a 909×3 base already; truncation handled by budget fix (§6)** | Low for small models (o1-preview 0.707 at turn 3, VERIFIED) | all VERIFIED |
| **IFBench** | VERIFIED (AI2) | VERIFIED (verifiable constraint design) | No (single-turn), but explicitly OOD-generalization | Yes; closest published analog of synthetic conf set | Low — designed because models overfit IFEval's constraint set (VERIFIED) | VERIFIED |
| FollowBench | VERIFIED | rule/LLM-hybrid | Partially (multi-level adds constraints) | Yes | Medium | VERIFIED |
| SysBench | VERIFIED | mixed | **Yes — "multi-turn instability" is a headline category** | Yes | Medium | VERIFIED |
| CFBench | VERIFIED | mixed | No | Yes (1000 samples, VERIFIED) | Medium | VERIFIED |
| MT-Eval | VERIFIED | LLM-judged | Partially (recollection category) | Weak (LLM-judged, contamination of judge) | Medium | VERIFIED |
| LongMemEval | VERIFIED | memory-based | Yes | Poor fit — needs memory infra | — | VERIFIED |
| "Lost in Multi-Turn" protocol | VERIFIED | task-specific scoring | Underspecification axis | Not a drop-in benchmark (simulation framework) | — | VERIFIED |

**Recommendation:** Multi-IF turn-2/3 English subset as the primary external gate (verifier-scored, aged constraints, published low scores at frontier scale → huge headroom at 1.7B), IFBench as the generalization gate (it punishes overfitting, which protects us from tuning the wave to IFEval-family idiosyncrasies). Keep the sealed synthetic conf set as the development gate. Note: Qwen3 TECH report includes alignment evals (VERIFIED existence of report; per-model IFEval numbers UNVERIFIED), so "published baselines for Qwen3-1.7B-class" effectively means the open-model rows in Multi-IF's own table (14 LLMs — VERIFIED count) rather than Qwen3-specific numbers.

---

## 5. Q5: activation/steering alternatives — documented effect sizes

| Method | Verified effect | Side effects (verified) | IFEval-class result? |
|---|---|---|---|
| ITI (2306.03341) | 32.5%→65.1% truthfulness on Alpaca (**VERIFIED**) | truthfulness/helpfulness tradeoff, tunable by strength (VERIFIED); few hundred examples suffice | **No** |
| CAA (2312.06681) | large behavioral shifts on Llama-2-Chat; works "over and on top of" finetuning+system prompts; "minimally reduces capabilities" (VERIFIED) | coefficient too high → incoherence (qualitative, VERIFIED direction) | **No** |
| Function vectors (2310.15213) | causal task execution zero-shot; middle layers strongest (VERIFIED) | not adherence-targeted | **No** |
| ICV (2311.06668) | improves ICL effectiveness/controllability (VERIFIED qualitatively) | — | **No** |
| Single-direction refusal (2406.11717) | 1-D direction gates an entire behavior across 13 models (VERIFIED) | clean dose-response | **No** — but proof that 1-D linear features can gate behavioral axes |
| RepE (2310.01405) | concept-level control (VERIFIED qualitatively) | — | **No** |
| SAE-targeted steering | titles located only (2411.02193, 2503.00177) — UNVERIFIED | — | **No** |

**Conclusion for Q5: there is no published, verified IFEval gain from any steering-vector method.** This is a real gap and an opportunity — but it means R3 (below) is exploratory and must be pre-registered with a confirmatory split.

---

## 6. Q6: decoding-time fixes — what is a confound and what isn't

**Why repetition penalty is an unacceptable hidden confound.** The verified literature establishes that repetition is *decoding-controllable*: Holtzman et al. (VERIFIED: decoding strategy alone dramatically changes repetition); DITTO (VERIFIED: repetition probability is self-reinforcing and therefore decoding-sensitive). A repetition penalty is thus **a second treatment on the same outcome variable**, not instrumentation. Three specific harms in our design: (a) **Mediation** — truncation is a primary failure endpoint we measure; shortening loops via penalty reduces truncation through a path that has nothing to do with the wave, reallocating credit; (b) **Masking** — the wave's degeneration signal (13/20 pinned) would be suppressed, making a safety endpoint unmeasurable at certification time; (c) **Outcome-dependent asymmetry** — IFBench-family constraints explicitly require repetition (VERIFIED example: *"mention the word `abrakadabra' at least 3 times"*); a repetition penalty directly fights constraint satisfaction in a constraint-type-dependent way.

**Legitimate alternatives (pre-register all):**
1. **Fixed greedy decoding in all arms.** Deterministic, paired, removes decoding as a variable. The degeneration then shows up where it should: in the endpoint. (Sampling, e.g. nucleus, is defensible per Holtzman but must be identical across arms *and* seed-matched — greedy is cleaner.)
2. **Budget fix for the truncation-prone Multi-IF base**: raise `max_new` from 1024 so the 10% baseline truncation disappears, identically in all arms; report output-length distributions as a co-endpoint. Truncation due to budget exhaustion ≠ truncation due to looping; fixing the budget lets us attribute the remainder correctly.
3. **Co-primary safety endpoints**: truncation rate, distinct-4gram / self-repetition score measured and gated (reject any arm that improves accuracy while worsening either). This converts "hidden confound management" into "declared success criterion."
4. If a backstop is unavoidable, a **disclosed, symmetric `no_repeat_ngram_size`** applied identically in every arm — but report both with/without runs so reviewers can see the mechanism stands alone.

---

## 7. Q7: three ranked redesigns

### R1 — "PASTA-shaped wave": head-sparse, tiny-dose, mid-layer bias *(highest upside if it works)*

- **What changes:** (i) replace the all-head sweep at layers 20–27 with a **profiled subset of K≈8–16 heads** found by causal scanning on a dev slice (for each head: boost span attention → does the gold continuation's logprob improve? keep the top-K); (ii) move the intervention to **middle layers** (function vectors: VERIFIED middle-layer causal dominance; avoids PyramidKV's VERIFIED late-layer consolidation zone); (iii) drop the bias magnitude to **α ∈ [0.005, 0.05] in logit units** swept on a log grid — PASTA's config-scale dose (~0.01, UNVERIFIED exact) not our current overdose; (iv) implement as **relative reweighting** (attenuate non-span columns, preserving total mass normalization) with a **per-head post-softmax cap** at the 95th percentile of the head's natural span-mass distribution; (v) keep the deficit gate (press only where natural span mass < τ) — it's the one component with positive evidence.
- **Why it should not degenerate:** dose is below the argmax-perturbation regime; few heads preserve redundancy; relative reweighting + caps make entropy collapse geometrically impossible outside the cap; span-internal repetition stops mattering because we're dividing, not adding.
- **Benchmark + preregistered gate:** development = sealed synthetic conf set: **+2.0 strict points with truncation ≤ baseline and distinct-4gram within 3% relative, 3 seeds** → confirmatory = **Multi-IF English turn-2+turn-3 averaged instruction accuracy: +3.0 points, same safety gates**.
- **Expected effect size (anchored):** AutoPASTA +7.95% avg on 70B (VERIFIED); PASTA headline ~+22% for 7B on its task battery (UNVERIFIED). For a 1.7B on adherence rather than QA, preregister a target of +2–3 points, not +20.
- **Falsifier:** if the best causal-scan heads at the sweep-optimal α yield ≤ +0.5 points **while the oracle-KV-pinning control shows the information is present and exploitable**, then the attention-bias channel is causally inert for adherence in this trunk — the wave-as-bias hypothesis is falsified at 1.7B scale.

### R2 — "Wave as selector, context as carrier": ledger → pin + echo *(cheapest, cannot degenerate, run first)*

- **What changes:** the 264k controller keeps only its *selection* job (which spans matter now). Delivery: (a) guaranteed KV residency (current +62% recovery), plus (b) a **canonical one-line constraint echo** appended at each user turn ("active: answer in ≤100 words; mention X ≥3 times"). The Attention Instruction result (VERIFIED: models can adapt attention to index/marked segments) and the Pitfalls result (VERIFIED: availability failures kill adherence) jointly say availability+recency is a proven channel; no logit surgery anywhere.
- **Why it should not degenerate:** no score bias at all; the only risk is echo text being treated as new instruction — controlled by a fixed echo template and an ablation arm (pin-only vs pin+echo).
- **Benchmark + gate:** aged-constraint eviction suite: **recover ≥85% of the eviction gap** (vs current 62%), zero added truncation; then Multi-IF turn-3 strict accuracy vs pin-only control.
- **Expected size:** from VERIFIED Pitfalls ("completely ignored" under eviction) to physically-retained + recently-echoed constraints, most of the gap is availability — expect the majority of the remaining 38%; this is the largest single recoverable chunk we have evidence for.
- **Falsifier:** if echo (perfect availability *and* recency) recovers ≈ nothing, the failure is **not selection** — the model finds the constraint and still doesn't comply (generation-side compliance deficit). That kills the selection framing of the wave entirely and reassigns effort to R3/decoding. This falsifier is *cheap to buy* and priceless: it disambiguates the two worlds before R1/R3 interpretational debt accumulates.

### R3 — "Adherence direction": single 1-D steering vector, deficit-gated *(highest variance; the IFEval-steering gap)*

- **What changes:** replace pre-softmax bias with a CAA/ITI-style direction `d` trained on contrast pairs (compliant vs non-compliant continuations for identical prompts, from the sealed *train* slice of the conf set), added as α·d to the residual stream at **one middle layer**, generation positions only, **gated by the existing deficit hook** (fire only when natural span attention < τ). Leverage VERIFIED precedents: ITI (+32.6 pts TruthfulQA, head-limited, strength-tunable), CAA ("minimally reduces capabilities"), refusal paper (1-D direction gates whole behavior).
- **Why it should not degenerate:** never touches softmax geometry; 1-D is the gentlest intervention class with a documented dose-response knob.
- **Benchmark + gate:** exploratory dev on synthetic conf holdout → confirmatory on **IFBench: +2.5 prompt-level-strict points at the dev-frozen α**, with a capability side-check (perplexity delta on held-out web text < 0.5%) and unchanged safety endpoints.
- **Expected size:** no verified IFEval-steering result exists (gap, VERIFIED by search); anchor expectations to ITI-class domain shifts but treat as exploratory.
- **Falsifier:** if probe accuracy of `d` on compliance is ≥0.8 yet IFBench lift ≈ 0 across the α grid → compliance is not a writable linear feature of the residual stream in this model; the only verified lever is availability (R2).

**Cross-cutting falsification statement (what would kill the Earl-Miller mapping for transformers):** the wave hypothesis says *synapses store, waves select* — i.e., with storage intact, modulating attention should increase use of stored instructions. If R1 (best parameterization of bias), R2 (availability+recency), and R3 (linear feature) all fail their preregistered gates while oracle-information controls pass, then at 1.7B scale **selection is performed by the context (storage + recency), not by score-space modulation** — the biological mapping inverts, the 264k controller is demoted to a span-selection utility, and the "wave" line closes with the verdict already suggested by our sealed-conf null + KV-pinning positive: *in frozen small decoders, waves don't select; caches do.*

---

## 8. What to run first (ordered)

1. **R2 echo arm** (½ week, no training): reuses ledger + pinning; its outcome is the decision variable for everything else (selection-failure vs compliance-failure). Gate: ≥85% gap recovery.
2. **R1 causal head scan** (2–3 GPU-days on dev slice): needed regardless; also re-tunes the deficit gate's head basis. Output: top-K head list + natural span-mass caps.
3. **R1 α-grid + confirmatory Multi-IF run** under §6 decoding hygiene (greedy, raised max_new, co-primary safety endpoints).
4. **R3** only after R2's disambiguation lands; train `d` on sealed train slice; exploratory→confirmatory split preregistered.
5. Throughout: retune truncation hygiene on the 909×3 Multi-IF base first (max_new ↑, symmetric) — a 10% truncated floor contaminates every downstream estimate.

**Verification ledger:** 25 sources opened (arXiv abs pages, arXiv API full abstracts, 1 GitHub README). All effect-size claims marked VERIFIED/UNVERIFIED in §1; numbers most load-bearing for decisions (AutoPASTA +7.95%, ITI 32.5→65.1%, Multi-IF 0.877→0.707, Pitfalls IFEval-under-compression, ACT +15 pts, CAD +14.3%, Lost-in-Multi-Turn −39%, LongMemEval −30%, DITTO self-reinforcement, softmax dispersal) are VERIFIED. The two most-cited-but-UNVERIFIED specifics (PASTA's α≈0.01 / few-early-layer-heads config; PASTA +22% headline) should be re-confirmed against the paper HTML before they appear in any preregistration doc.

## Tool log
[1] web_search({"query": "PASTA \"Tell Your Model Where to Attend\" post-hoc attention steering arXiv"}) -> 102 chars
[2] web_search({"query": "AutoPASTA automatically steering language model attention arXiv"}) -> 457 chars
[3] web_search({"query": "\"Found in the Middle\" calibrating positional attention bias long context arXiv"}) -> 102 chars
[4] web_search({"query": "Multi-IF benchmarking LLMs multi-turn multilingual instructions following arXiv"}) -> 102 chars
[5] web_search({"query": "SnapKV LLM knows what you are looking for before generation arXiv"}) -> 102 chars
[6] web_search({"query": "H2O heavy hitter oracle efficient generative inference arXiv"}) -> 461 chars
[7] web_search({"query": "PASTA post-hoc attention steering LLMs IFEval"}) -> 914 chars
[8] web_search({"query": "\"Multi-IF\" multi-turn instruction following benchmark Meta arXiv 2024"}) -> 102 chars
[9] web_search({"query": "\"SnapKV\" KV cache compression LongBench arXiv 2404"}) -> 102 chars
[10] web_fetch({"url": "https://arxiv.org/abs/2311.02262"}) -> 4563 chars
[11] web_fetch({"url": "https://arxiv.org/abs/2306.14048"}) -> 5250 chars
[12] web_fetch({"url": "https://arxiv.org/abs/2409.10790"}) -> 4736 chars
[13] web_fetch({"url": "https://arxiv.org/abs/2410.15535"}) -> 3388 chars
[14] web_fetch({"url": "https://arxiv.org/abs/2404.14469"}) -> 4863 chars
[15] web_search({"query": "\"Found in the Middle\" ACT attention calibration Hsieh arXiv positional bias"}) -> 102 chars
[16] web_fetch({"url": "https://arxiv.org/abs/2309.17453"}) -> 4862 chars
[17] web_search({"query": "Multi-IF benchmark multi-turn instructions following Llama 3 paper"}) -> 102 chars
[18] web_search({"query": "\"IFBench\" instruction following benchmark 2025 arXiv"}) -> 1724 chars
[19] web_fetch({"url": "https://arxiv.org/abs/2306.03341"}) -> 4562 chars
[20] web_fetch({"url": "https://arxiv.org/abs/2311.06668"}) -> 4906 chars
[21] web_fetch({"url": "https://arxiv.org/abs/2310.01405"}) -> 4741 chars
[22] web_fetch({"url": "https://arxiv.org/abs/2507.02833"}) -> 4802 chars
[23] web_fetch({"url": "https://arxiv.org/abs/2505.11739"}) -> 5389 chars
[24] web_fetch({"url": "https://arxiv.org/abs/2406.02069"}) -> 4900 chars
[25] web_fetch({"url": "https://arxiv.org/abs/2408.10939"}) -> 3975 chars
[26] web_fetch({"url": "https://arxiv.org/abs/2311.09835"}) -> 5459 chars
[27] web_search({"query": "\"Multi-IF\" benchmark multi-turn multilingual instruction following 4501 conversations"}) -> 102 chars
[28] web_search({"query": "SysBench \"system messages\" multi-turn benchmark arXiv Qin"}) -> 878 chars
[29] web_search({"query": "FollowBench multi-level fine-grained constraints following Jiang arXiv"}) -> 911 chars
[30] web_fetch({"url": "https://arxiv.org/abs/2410.10813"}) -> 4822 chars
[31] web_fetch({"url": "https://arxiv.org/abs/2401.16745"}) -> 4695 chars
[32] web_fetch({"url": "https://arxiv.org/abs/2505.06120"}) -> 4277 chars
[33] web_fetch({"url": "https://arxiv.org/abs/2305.14739"}) -> 3931 chars
[34] web_fetch({"url": "https://arxiv.org/abs/2410.01104"}) -> 4387 chars
[35] web_fetch({"url": "https://arxiv.org/abs/2310.15213"}) -> 4458 chars
[36] web_fetch({"url": "http://export.arxiv.org/api/query?search_query=all:%22Multi-IF%22&max_results=5"}) -> 7200 chars
[37] web_fetch({"url": "http://export.arxiv.org/api/query?search_query=ti:%22Multi-IF%22+OR+all:%22multi-turn+and+multilingual+instruct) -> 7653 chars
[38] web_search({"query": "\"CFBench\" constraints following benchmark LLM arXiv"}) -> 439 chars
[39] web_fetch({"url": "https://arxiv.org/abs/2408.10943"}) -> 4648 chars
[40] web_fetch({"url": "https://arxiv.org/abs/2310.20410"}) -> 4676 chars
[41] web_fetch({"url": "https://arxiv.org/abs/2505.09388"}) -> 5363 chars
[42] web_fetch({"url": "http://export.arxiv.org/api/query?search_query=ti:%22Found+in+the+Middle%22&max_results=5"}) -> 4779 chars
[43] web_fetch({"url": "http://export.arxiv.org/api/query?search_query=ti:%22Attention+Instruction%22&max_results=5"}) -> 1485 chars
[44] web_search({"query": "\"repetition\" neural text degeneration analysis \"attention\" over-attend loop arXiv"}) -> 476 chars
[45] web_fetch({"url": "https://arxiv.org/abs/2408.01122"}) -> 4687 chars
[46] web_search({"query": "sparse autoencoder steering instruction following LLM IFEval"}) -> 102 chars
[47] web_fetch({"url": "https://arxiv.org/abs/1904.09751"}) -> 4362 chars
[48] web_fetch({"url": "http://export.arxiv.org/api/query?search_query=all:%22Learning+to+Break+the+Loop%22&max_results=3"}) -> 2178 chars
[49] web_fetch({"url": "https://github.com/QingruZhang/PASTA"}) -> 7860 chars
[50] web_search({"query": "KV cache compression benchmark \"instruction following\" adherence long context 2025"}) -> 885 chars
[51] web_search({"query": "activation steering instruction following IFEval improvement"}) -> 102 chars
[52] web_fetch({"url": "https://arxiv.org/abs/2510.00231"}) -> 4491 chars
[53] web_fetch({"url": "https://arxiv.org/abs/2310.10226"}) -> 4449 chars
[54] web_fetch({"url": "https://arxiv.org/abs/2312.06681"}) -> 4463 chars
[55] web_search({"query": "\"attention buckets\" LLM steering attention heads"}) -> 102 chars
[56] web_search({"query": "LLM robustness \"buried\" instructions mid-context ignored"}) -> 102 chars
[57] web_fetch({"url": "https://arxiv.org/abs/2410.15553"}) -> 5091 chars
[58] web_fetch({"url": "https://arxiv.org/abs/2406.11717"}) -> 4521 chars
[59] web_fetch({"url": "http://export.arxiv.org/api/query?search_query=all:%22AutoPASTA%22&max_results=3"}) -> 1942 chars
[60] web_search({"query": "\"steering vectors\" sparse autoencoders improving LLM behavior arXiv"}) -> 3099 chars
[61] web_fetch({"url": "https://arxiv.org/abs/1908.04319"}) -> 4610 chars
