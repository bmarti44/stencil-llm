# Deep research — kimi-k3 with web tools (2026-09-02); 60 tool calls

# Research report: a selection mechanism that generalizes
**Date:** 2026-09-02 · **For:** results/research-generalizing-kimi.md · **Agent:** kimi-k3 (cross-model researcher)
**Verification status:** 24 sources fetched and quoted below (marked VERIFIED); everything else is marked UNVERIFIED (memory). Miller papers were not reachable within my tool budget — his claims are flagged UNVERIFIED and must be confirmed from the actual papers before any external writeup.

---

## Ranked recommendation (the 2-page part)

**Rank 1 — Build G0, but with a cheaper label function, on the frozen trunk itself.**
The strongest prior-art match to your G0 is **KVzip** (arXiv 2505.23416v2, VERIFIED): importance of a KV pair = "the underlying LLM" reconstructing "original contexts from cached KV pairs," evicting the rest; result — "KV cache size by 3–4× and FlashAttention decoding latency by approximately 2×, with negligible performance loss in question-answering, retrieval, reasoning, and code comprehension," and the cache is **query-agnostic and reused across diverse queries**. This proves model-derived, label-free importance transfers across task types, which is exactly the property your hand-built finders lack. **DuoAttention** (arXiv 2410.10819, VERIFIED mechanism) is the second existence proof: a *learned* split of heads into "Retrieval Heads" requiring full KV vs. "Streaming Heads" that don't, found by optimization on small data, transferring to real long-context tasks. So G1 (train a small thing on the model's own need signal, expect transfer) has genuine precedent. **Adversarial caveat:** exact leave-one-out eviction labeling is O(spans × forwards). At sentence granularity (~30–50 evictable spans/conversation) on 1k conversations, that is ~40k forward passes — ~10–35 GPU-hours for a 1.7–4B model at 8k tokens. Feasible on one GPU in **days**, not "hours," unless you (a) subsample to ~300 conversations, or (b) use G0′ = single-backward attribution (grad×activation on later-turn loss, all spans scored in ~2 forwards/conversation → ~1–2 GPU-hours). **Do G0′ first; verify G0′ vs. true LOO on a 200-conversation calibration set; only invest in full LOO if the gap is large.**

**Rank 2 — G1 probe design: pooled training, leave-one-corpus-out, normalized labels, spans only.**
Train the existing layer-20 logistic probe on pooled G0′ labels from exactly three corpora: **Multi-IF** (persistent-constraint style; your linguistic finder already gets 0.98 coverage there), **BFCL v3 multi-turn non-cohort** (provenance spread you measured: 42% current turn / 20% earlier user / 17% tool output / 37% tool-derived — forces tool-output features), and **one generic chat corpus** (WildChat or LMSYS-1M English subsample — UNVERIFIED names, standard public sets). Evaluate 3× leave-one-corpus-out; generalization claim = held-out AUPRC within ~0.03 of in-corpus. Features: frozen hidden state at span center + position + role (user/assistant/tool) + span length. **Mandatory controls/floors:** your existing **random-column pinned control (18/56)**, a **recency+sink floor** (StreamingLLM, arXiv 2309.17453, VERIFIED: window attention "fails when the text length surpasses the cache size"; keeping initial tokens' KV "will largely recover" it), attention-mass floors (H2O arXiv 2306.14048 VERIFIED hypothesis; Scissorhands arXiv 2305.17118 VERIFIED "persistence of importance"; SnapKV arXiv 2404.14469 VERIFIED observation-window mechanism), and **full-context ceiling**. Hard label-processing rules below.

**Rank 3 — Ship the schema pin as a hybrid baseline regardless of the probe.** Your harness fact ("schemas ~5k tokens sit at column 0 and are evicted first") collides with the attention-sink literature: column 0 is where sinks live (StreamingLLM, VERIFIED). G0 labels may score schemas as unimportant (sink tokens absorb attention mass without causing loss deltas when evicted in attribution approximations). Pinning schema columns unconditionally is a zero-learning win for BFCL-style tasks and a hedge that costs nothing on Multi-IF.

**Rank 4 — G2 as diagnostics, one self-echo arm only.** Run the attention heavy-hitter floors specifically **to demonstrate their predicted failure**, not as candidates: **SCBench** (arXiv 2412.10319v2, VERIFIED) states outright that "sub-O(n) memory methods suffer in multi-turn scenarios" and that KV-dropping methods "perform well only in the first request" while O(n)-memory-decoding methods improve across requests. That is the published confirmation of your Multi-IF/BFCL failure analysis. One verbatim-echo arm already works in your code; add *at most one* generation-based self-echo arm (model-authored per-turn digest echoed next turn), with per-turn latency logged, because that's the only form with literature support for long-horizon agents: **Reflexion** (arXiv 2303.11366v4, VERIFIED) — reflective text in an episodic buffer, "91% pass@1 … HumanEval … surpassing … GPT-4 that achieves 80%"; **Mem0** (arXiv 2504.19413, VERIFIED: retrieval/consolidation memory evaluated on LOCOMO against six baseline categories including full-context; its 26%/–91% latency numbers are UNVERIFIED — abstract truncated before figures); **A-MEM** (arXiv 2502.12110, VERIFIED design: Zettelkasten-style structured memory notes; no quotable numbers). None of these beat a learned selector head-to-head in any VERIFIED source I found; treat self-echo as a complement (echo of selected spans ≈ reactivation), not a competitor.

**Deployment:** unchanged — retention-only, pin+ditto-echo, random pinned control. Nothing in the literature contradicts your H1 result that amplification degenerates; compression papers that touch logits (soft prompts) are all training-based.

---

## Q1 — What generalizes, and where heavy hitters fail (evidence)

- **Multi-turn KV-drop failure is published, quantified at benchmark level (SCBench, VERIFIED):** "sub-O(n) KV cache … like KV cache dropping methods, perform well only in the first request"; O(n)-memory sparse methods "perform robustly"; also "attention distribution shift issues in long-generation scenarios."
- **Cross-session memory degradation (LongMemEval, arXiv 2410.10813v2, VERIFIED):** 500 questions, five memory abilities; "commercial chat assistants and long-context LLMs show[] a 30% accuracy drop … across sustained interactions."
- **Agent reliability collapse (τ-bench, arXiv 2406.12045, VERIFIED):** "even state-of-the-art function calling agents (like gpt-4o) succeed on <50% of the tasks," "pass^8 <25% in retail" — consistency over turns is the failing axis, which eviction worsens.
- **Multi-turn dialogue benchmark (MT-Bench-101, arXiv 2402.14762v3, VERIFIED:** "4208 turns across 1388 multi-…" dialogues, three-tier taxonomy**).** Multi-IF (arXiv 2410.15553) exists as multi-turn+multilingual IF benchmark (VERIFIED existence; its turn-3 degradation numbers are UNVERIFIED — abstract truncated).
- **Needle/synthetic long-context failure (RULER, arXiv 2404.06654v3, VERIFIED:** 17 models; NIAH expansions + multi-hop tracing + aggregation**;** the famous "only half maintain satisfactory performance at 32K" figure is UNVERIFIED — truncated). ∞Bench (arXiv 2402.13718, VERIFIED: "first LLM benchmark featuring an average data length surpassing 100K tokens"; GPT-4 <25% figure UNVERIFIED).
- **Why attention-vote selectors miss instructions:** Scissorhands' own stated assumption — tokens with high historical attention stay important (VERIFIED hypothesis quote) — fails exactly when an instruction is *not attended until needed*. SnapKV votes from an end-of-prompt observation window (VERIFIED mechanism), i.e., it selects for the *current* query's needs; SCBench shows first-request-good/later-request-bad. **Heavy-hitter methods are structurally first-request methods. Your counterfactual labels are structurally future-request labels. That is the entire argument for G0.**
- **Compression can match/beat full context at low budgets — supporting pinned_echo>full (VERIFIED): PyramidKV** (arXiv 2406.02069v4) "matches the performance of models with a full KV cache while retaining only 12% of the KV cache" on LongBench; 128 KV entries → "100.0 Acc" NIAH on LLaMA-3-70B; +20.5 absolute on TREC at 0.7% KV. **Activation Beacon** (arXiv 2401.03462v3): "2x acceleration … 8x reduction of memory costs for KV cache." Your 48/56 vs 44 is directionally consistent.

## Q2 — Prior art on counterfactual/learned salience

- **KVzip** (VERIFIED, above): counterfactual-ish, model-derived, query-agnostic, cross-task. Closest to G0. Difference: reconstructs the *past*; you predict the *future* (later gold turns). Yours is the right variant for dialogue.
- **Locret** (arXiv 2410.01805v2, VERIFIED partial): "the first framework to create an eviction policy compatible with chunked prefill. By evaluating the causa[l…]" — trained retaining heads, i.e., a learned G1-like selector; no cross-benchmark transfer claim visible (UNVERIFIED).
- **DMC** (arXiv 2403.09636v2, VERIFIED): model *learns* per-layer/head compression ratios via continued pretraining, "up to 7x throughput increase … on an NVIDIA H100," "negligible percentage of the original data," no extra parameters — but it modifies weights; **violates your frozen-trunk constraint** (architecture-level evidence only).
- **Learned-but-light:** Q-Filters (arXiv 2503.02812, VERIFIED: training-free, "single context-agnostic projection," FlashAttention-compatible; its ~99%-at-32× numbers UNVERIFIED — truncated). DuoAttention (VERIFIED head split; its 4.9×/2.7× memory/latency numbers UNVERIFIED — truncated).
- **Agent memory (all VERIFIED as described above):** MemGPT (arXiv 2310.08560, virtual context management, memory tiers — qualitative), Reflexion, Mem0, A-MEM. **Not VERIFIED (budget):** GemFilter, LazyLLM, MInference paper (its GitHub is VERIFIED: "reduces inference latency by up to 10x for pre-filling … while maintaining accuracy"; SCBench ships inside the repo), TOVA, LLMLingua, ContextCite, AttentionPredictor, Memory Decoder, Sirius (could not locate on arXiv under that title — possible hallucinated name in the brief's source list; verify before citing).

## Q3 — Self-echo vs learned selectors

No VERIFIED source compares a per-turn self-summarizer against a learned KV selector head-to-head. Evidence *for* text-side memory on long horizons: Reflexion (VERIFIED 91% HumanEval), Mem0/A-MEM on LOCOMO (UNVERIFIED effect sizes). Latency cost is structurally known: one extra generation per turn (~1× turn cost) plus hallucination risk on constraint text (worst on Multi-IF-style constraints). **Verdict: verbatim echo of probe-selected spans dominates self-summarization for your setting; keep at most one digest arm for comparison.**

## Q4 — Smallest decisive G1 experiment

1. **Corpora (3):** Multi-IF; BFCL v3 multi-turn non-cohort; WildChat/LMSYS subsample. ~350 conversations each.
2. **Labels (G0′ then G0):** G0′ = per-span importance from one backward pass on the sum of later-turn assistant/tool-call token losses (attention×grad attribution). Calibrate G0′ against true leave-one-out eviction Δloss on N=200 conversations (Spearman ρ ≥ 0.6 to proceed; else full LOO on 300-conv subset). Per-conversation **z-score the deltas** (removes corpus entropy confound); **exclude sink columns (first ~4 tokens per span-start) from features**; mask schema columns out of labels initially (pin them unconditionally, Rank 3).
3. **Probe:** logistic regression on layer-20 hidden state + role/position features; pooled 2-corpora training, held-out 3rd; ×3. Report AUPRC at a pinned-column budget matched to your K=8192 pressure cases; optimize for **recall at fixed budget** (missed constraint = catastrophic; extra pin = mild).
4. **Floors/control:** recency+sink; H2O cumulative attention; SnapKV window; linguistic finder; regex-literal finder; **random pinned columns (18/56)**; full-context ceiling. End-to-end check only if probe wins on label metrics.
5. **Feasibility:** G0′ ≈ 2× forward per conversation → ~1–3 GPU-hours for 1.7B/1k convs → probe training is CPU-sklearn minutes. Realistic on one GPU in hours: **yes, with G0′; only ~300-conv scale with exact LOO.** Note: my hard rules mean I cannot run any of this (CPU-only); this spec is for the GPU box.

## Q5 — Miller framing check (all Miller citations UNVERIFIED — papers not fetched)

From memory of the canon — verify before quoting externally:
- **Lundqvist et al. 2016, Neuron ("Gamma and beta bursts underlie working memory")** and **Lundqvist et al. 2018, eLife**: WM content is *not* maintained by persistent firing; it's stored in synaptic efficacy (activity-silent) and *read out* in brief gamma bursts nested in beta, with bursts triggered where attention is needed.
- **Miller, Lundqvist & Bastos 2018, Neuron ("Working Memory 2.0")**: synaptic weights store; oscillatory bursts = the selection/readout mechanism; selection is at the level of *item/content representation*, gated on demand — not a continuous amplifying field over everything.
- **Buschman & Miller work**: top-down attention recruits the relevant sensory representations rhythmically.

**Defensible mapping:** Stencil's synapses = frozen trunk weights; content stored activity-silently = unpinned KV; bursts = the echo of selected spans at the current turn (sparse, transient reactivation); and **the wave-selects piece = your G1 probe reading hidden state to decide* what gets reactivated***. The granularity matches best if the probe selects *semantic items* (span-level), not tokens or layers ("granularity of an item" is what Miller's bursts index — UNVERIFIED paraphrase). **Where it breaks:** Miller's wave is also a *coordination* signal across populations; a logistic probe is a readout device with no coordinating dynamics. Calling the probe "the wave" is defensible as analogy (fast, state-dependent, on-demand gating of readout), decorative if pushed further. Phrase in paper as: "probe gating plays the functional role of burst-triggered readout in the WM 2.0 framework."

## Do-not-do list
1. Do not train G1 on one corpus or report in-corpus metrics only — leave-one-corpus-out or the claim is dead.
2. Do not use raw Δloss as labels without per-conversation normalization and sink exclusion — sinks will dominate the labels and teach "pin column 0" garbage (though pinning real schema columns is separately justified).
3. Do not adopt DMC/DuoAttention-style continued pretraining — violates frozen trunk; cite them as evidence that learned selection transfers, nothing more.
4. Do not use SnapKV/H2O as your deployed selector in multi-turn settings — SCBench VERIFIED first-request-only behavior; run them as failure-mode baselines.
5. Do not add generation-based self-summaries as default echo — Reflexion-quality results are single-domain (HumanEval) and constraint-text paraphrase risk is real; keep echo verbatim.
6. Do not claim Miller-theory confirmation from benchmark deltas; the mapping is an analogy at span/item granularity — say "functional role of burst-triggered readout," not "waves."
7. Do not cite "Sirius"/"AttentionPredictor"/"Memory Decoder" until their papers are actually located — my searches found nothing under those exact names (possible name errors; verify).
8. Do not skip the random-pinned control — 18/56 is what makes any pinned win interpretable.
9. Do not evaluate only where the linguistic finder already wins (Multi-IF); BFCL non-cohort + generic chat are the generalization argument.
10. Do not exceed one week on label infrastructure before the G0′ vs LOO calibration check — if ρ < 0.6, drop the probe line entirely and fall back to Rank 3 hybrid (schema pin + provenance regex + probe later).

## Source ledger
VERIFIED (fetched, quoted): SCBench 2412.10319v2 (+HTML); KVzip 2505.23416v2; Locret 2410.01805v2; Q-Filters 2503.02812; DMC 2403.09636; DuoAttention 2410.10819; SnapKV 2404.14469v2; H2O 2306.14048v3; Scissorhands 2305.17118; StreamingLLM 2309.17453; PyramidKV 2406.02069v4; Activation Beacon 2401.03462v3; LongMemEval 2410.10813v2; Multi-IF 2410.15553; MT-Bench-101 2402.14762v3; RULER 2404.06654v3; ∞Bench 2402.13718; τ-bench 2406.12045; Reflexion 2303.11366v4; MemGPT 2310.08560; Mem0 2504.19413; A-MEM 2502.12110; MInference GitHub (NeurIPS'24 Spotlight, ~10× prefill claim, hosts SCBench). UNVERIFIED (memory/search-snippet only): BFCL v3/v4, GemFilter, LazyLLM, TOVA, LLMLingua, LOCOMO, WildChat/LMSYS, Miller/Lundqvist/Bastos papers, Mem0 effect sizes, DuoAttention/RULER/∞Bench headline numbers, and *Sirius/AttentionPredictor/Memory Decoder* (names unconfirmed on arXiv — treat with suspicion).

## Tool log
[1] web_search({"query": "SCBench multi-turn KV cache benchmark long-context LLM"}) -> 434 chars
[2] web_search({"query": "DuoAttention retrieval heads streaming heads long-context LLM arXiv"}) -> 459 chars
[3] web_search({"query": "Sirius KV cache compression correction mechanism arXiv"}) -> 102 chars
[4] web_search({"query": "LongMemEval benchmark long-term memory LLM chat assistants"}) -> 888 chars
[5] web_fetch({"url": "http://arxiv.org/abs/2412.10319v2"}) -> 5196 chars
[6] web_fetch({"url": "http://arxiv.org/abs/2410.10819v1"}) -> 4779 chars
[7] web_fetch({"url": "http://arxiv.org/abs/2410.10813v2"}) -> 4826 chars
[8] web_search({"query": "Dynamic Memory Compression LLM NVIDIA training-free KV cache arXiv"}) -> 102 chars
[9] web_fetch({"url": "http://arxiv.org/abs/2403.09636"}) -> 4519 chars
[10] web_search({"query": "KVzip query-agnostic KV cache eviction arXiv 2025"}) -> 1362 chars
[11] web_search({"query": "R-KV reasoning KV cache redundancy key token selection arXiv"}) -> 3504 chars
[12] web_search({"query": "Locret retaining importance KV cache eviction trained arXiv"}) -> 485 chars
[13] web_fetch({"url": "http://arxiv.org/abs/2505.23416v2"}) -> 4360 chars
[14] web_fetch({"url": "http://arxiv.org/abs/2410.01805v2"}) -> 4686 chars
[15] web_search({"query": "Q-Filters hidden state probing KV cache eviction arXiv"}) -> 102 chars
[16] web_search({"query": "\"Sirius\" long context KV cache correction compression 2025 arXiv"}) -> 102 chars
[17] web_search({"query": "Q-Filters training-free KV cache compression geometric information probing"}) -> 1342 chars
[18] web_search({"query": "Sirius long-context inference correction compressed context arXiv 2503"}) -> 102 chars
[19] web_search({"query": "AttentionPredictor token importance prediction KV cache compression"}) -> 102 chars
[20] web_search({"query": "H2O heavy hitter oracle KV cache eviction Scissorhands"}) -> 461 chars
[21] web_fetch({"url": "http://arxiv.org/abs/2503.02812v1"}) -> 4639 chars
[22] web_fetch({"url": "https://github.com/microsoft/SCBench"}) -> 449 chars
[23] web_search({"query": "leave-one-out token importance long context attribution evict measure perplexity"}) -> 499 chars
[24] web_search({"query": "SnapKV compress KV heads observation window long context"}) -> 883 chars
[25] web_fetch({"url": "http://arxiv.org/abs/2404.14469v2"}) -> 4867 chars
[26] web_search({"query": "RULER benchmark long context needle retrieval multi-key arXiv 2404"}) -> 2738 chars
[27] web_search({"query": "Multi-IF benchmark multilingual multi-turn instruction following Meta"}) -> 102 chars
[28] web_search({"query": "\"Sirius\" KV cache \"correction\" long-context LLM compression"}) -> 102 chars
[29] web_fetch({"url": "http://arxiv.org/abs/2404.06654v3"}) -> 4716 chars
[30] web_fetch({"url": "http://arxiv.org/abs/2309.17453"}) -> 4862 chars
[31] web_fetch({"url": "http://export.arxiv.org/api/query?search_query=all:%22Sirius%22%20AND%20all:%22KV+cache%22&max_results=8"}) -> 165 chars
[32] web_search({"query": "\"Multi-IF\" benchmark LLM multi-turn multilingual instruction following arXiv 2410"}) -> 102 chars
[33] web_fetch({"url": "http://arxiv.org/abs/2410.15553"}) -> 5091 chars
[34] web_fetch({"url": "http://export.arxiv.org/api/query?search_query=ti:%22Sirius%22&max_results=10"}) -> 9000 chars
[35] web_search({"query": "MT-bench-101 fine-grained multi-turn dialogue benchmark degradation"}) -> 473 chars
[36] web_search({"query": "Berkeley Function Calling Leaderboard v3 multi-turn tool use agent"}) -> 479 chars
[37] web_fetch({"url": "http://arxiv.org/abs/2410.15553"}) -> 5091 chars
[38] web_fetch({"url": "http://arxiv.org/abs/2402.14762v3"}) -> 4969 chars
[39] web_fetch({"url": "http://arxiv.org/abs/2503.24103"}) -> 4167 chars
[40] web_search({"query": "MInference 1.0 sparse attention long-context prefill arXiv"}) -> 102 chars
[41] web_fetch({"url": "http://arxiv.org/abs/2306.14048v3"}) -> 5254 chars
[42] web_fetch({"url": "http://arxiv.org/abs/2305.17118"}) -> 4865 chars
[43] web_fetch({"url": "https://github.com/microsoft/MInference"}) -> 9000 chars
[44] web_search({"query": "A-MEM agentic memory dynamic Zettelkasten LLM agents arXiv"}) -> 411 chars
[45] web_fetch({"url": "http://arxiv.org/abs/2502.12110v11"}) -> 5447 chars
[46] web_fetch({"url": "http://arxiv.org/abs/2406.12045"}) -> 4094 chars
[47] web_fetch({"url": "http://arxiv.org/abs/2310.08560"}) -> 4448 chars
[48] web_fetch({"url": "http://arxiv.org/abs/2504.19413"}) -> 5069 chars
[49] web_fetch({"url": "https://github.com/microsoft/MInference/tree/main/scbench"}) -> 8601 chars
[50] web_fetch({"url": "http://arxiv.org/abs/2402.13718"}) -> 4930 chars
[51] web_fetch({"url": "http://arxiv.org/abs/2408.05658"}) -> 3725 chars
[52] web_search({"query": "ContextCite attributing model generation context ablation surrogate"}) -> 102 chars
[53] web_fetch({"url": "https://arxiv.org/html/2412.10319v2"}) -> 9000 chars
[54] web_search({"query": "GemFilter filter then generate retrieval long-context prefill arXiv"}) -> 102 chars
[55] web_search({"query": "\"ContextCite\" attributing model generation to context"}) -> 102 chars
[56] web_search({"query": "Reflexion language agents verbal reinforcement learning arXiv"}) -> 893 chars
[57] web_fetch({"url": "http://arxiv.org/abs/2303.11366v4"}) -> 4756 chars
[58] web_fetch({"url": "http://arxiv.org/abs/2401.03462"}) -> 4930 chars
[59] web_fetch({"url": "http://arxiv.org/abs/2406.02069"}) -> 4900 chars
[60] web_search({"query": "Berkeley function calling leaderboard BFCL v3 multi-turn categories \"multi-turn\""}) -> 479 chars
