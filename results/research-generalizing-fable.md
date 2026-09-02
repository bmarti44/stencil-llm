# Deep research: a selection mechanism that generalizes — fable, 2026-09-02

Brief: scratchpad/research-generalizing-selection.md. CPU only; no model or GPU process launched; no repo file other
than this report written. Evidence tags: [V] = read in the cited source (full text / html / extracted PDF text);
[S] = from a search snippet or tool summary only, not opened in full; [I] = my inference or arithmetic. Repo
numbers come from results/agentic-salience-review-fable.md (R1–R9), results/h1p-review-fable.md and
src/stencil/salience2.py:36-60. Local scratch: scratchpad/fable-research/ (extracted paper texts).

## 0. Bottom line (ranked)

1. DO FIRST — G0 as an audit, not as a training set. Compute the label-free leave-one-out (LOO) need oracle on
   three corpora and measure how much of the oracle's recoverable loss each ZERO-training policy already captures
   (recency, "all prior user turns", query-agnostic attention mass, KVzip, the linguistic finder). The literature
   says the cheapest structural policies are hard to beat once the query is hidden (Sec. 1.2), so the burden test
   for G1 is "beats the best structural proxy corpus-held-out", not "beats random". If a structural proxy recovers
   >= 0.8 of the oracle, ship it and skip G1.
2. THEN G1, but as a TWO-time-scale probe, not a write-time importance score alone: (a) write-time admission
   (which spans survive eviction) and (b) read-time selection (which surviving spans are echoed now, scored from
   the CURRENT turn's hidden state). Only (b) corresponds to Miller's "waves select" (Sec. 5); (a) is a synaptic
   retention prior. Train on G0 labels, evaluate corpus-held-out, with a positional-shuffle control (residual-stream
   signals drift with position — Sec. 2.3). Budget: hours on GB10 for ~1k conversations (Sec. 4.4, [I]).
3. Self-echo / self-summary: run as a REPORTED arm only. At frontier scale it ties simple observation masking and
   lengthens trajectories 13–15%; repeated compaction is unstable; nobody has shown it beats a learned selector on
   agentic benchmarks because nobody has compared them (Sec. 3). On a 1.7B/4B trunk the summarizer is the weak
   trunk itself.
4. Precondition for ANY of the above on BFCL: the harness fix (prefix sink for the <tools> block; a budget that
   actually evicts) from results/agentic-salience-review-fable.md F1 — otherwise there is no retention effect to
   measure in 3 of 4 categories (R3–R5) and the 4th is a schema-loss test.
Do-not-do list: Sec. 7.

## 1. Which retention/selection methods generalize across task types? Where do heavy hitters fail?

1.1 Multi-turn / shared-context collapse of attention-based eviction [V].
- SCBench (Li et al., ICLR 2025; https://arxiv.org/html/2412.10319): on Llama-3.1-8B at 1/32 compression,
  SnapKV on Retrieval.KV "drops from 100% to approximately 3% by turn 2", StreamingLLM "collapses to 0.4%";
  "sub-O(n) memory methods suffer in multi-turn scenarios" because "important KVs remain stable within a turn,
  [but] vary significantly between queries". Dynamic sparse attention with O(n) memory (MInference) averages 42.5
  vs StreamingLLM 15.5 across turns. All methods degrade with compression; sub-O(n) methods "exhibit significant
  drop at 1/4 compression rates".
- Query-visibility audit (Luo, Liang, Xuan 2026; https://arxiv.org/pdf/2607.11942; 144,300 paired RULER-8192
  evaluations on three 7–9B models): under the query-AGNOSTIC protocol "only KeyDiff beats a best-of-3 trivial
  baseline consistently (31/36 cells), and the most widely deployed method, SnapKV, loses to 'keep the start and
  the recent window' on average (−0.066)"; the query-aware inflation is "+0.198 for SnapKV (the question sits
  inside its 64-token observation window) down to +0.011 for KeyDiff". Two hazards: eager-vs-sdpa attention
  backend shifts uncompressed RULER by −0.22 to −0.29 ("larger than most method-vs-baseline gaps"; H2O's rank is
  withdrawn), and RULER "8192" overflows gemma-2 by up to 30%. IMPLICATION for Stencil: every attention-mass
  baseline (G2) must be scored BEFORE the later turn exists, and the same attention backend must be used for all
  arms (the Qwen3 trunk is ours, so this is controllable, but it must be stated).

1.2 Instruction-following failures of eviction [V].
- The Pitfalls of KV Cache Compression (Chen, Geh, Grover, ..., ACL 2026; https://arxiv.org/abs/2510.00231;
  extracted text): five policies (StreamingLLM, H2O, K-Norm, SnapKV, TOVA) on Llama3-8B and Qwen2.5-14B, 541
  IFEval prompts, only the query compressed. Pitfall 1 "Instructions do not degrade at the same rate"; Pitfall 5
  "KV cache eviction disproportionally targets certain instructions, often causing them to be ignored by the LLM";
  "StreamingLLM and SnapKV show a particularly stark bias" (they keep the last instruction and evict the defense
  system prompt); Pitfall 6 "Eviction corresponding to the wrong tokens can play a critical role". Fix that works:
  a manual keyword whitelist forced into the keep set, and "fair" eviction balancing evicted fraction per
  instruction. Pitfall 2: effects "highly depend on eviction policy and model". (Exact curves are figures; the
  text gives no single headline number.)
- When Attention Closes (2026; https://arxiv.org/pdf/2605.12922; extracted text): the Goal Accessibility Ratio
  (attention from generated tokens to system-prompt goal tokens) "declines monotonically with conversation turn
  across every LLM architecture" (10 architectures, pooled Kendall τ = −0.75), by "27% to 48% of its turn-1 value"
  over 50 turns. Forcing closure with a 4096 sliding window collapses 20-fact recall on Mistral-7B to 11.2% at T=50
  and information retention at T=50 to 0.0% (LLaMA-3.1-8B) / 6.0% (Qwen-2.5-7B). KEY FOR G1: "Linear probes on
  residual representations recover per-episode recall outcomes with AUC up to 0.99 across all four primary
  architectures (input embedding: chance)" — the probe is read at the position immediately before the response,
  i.e. a READ-time need signal exists linearly in the residual stream. Depth "varies dramatically by architecture
  (from layer 2 to layer 27)".
- Dormant tokens (Transactional Attention, 2026; https://arxiv.org/abs/2604.11288) [V abstract]: at K=16 (0.4% of a
  4K context) "six baselines — H2O, TOVA, SnapKV, StreamingLLM, PyramidKV, and DynamicKV — achieve 0% credential
  retrieval"; credentials/API keys/config values "receive near-zero attention but become essential at generation
  time". Their fix is hand-built anchor patterns ("key:", "password:") — i.e., exactly the task-specific regex
  Stencil is trying to leave behind, and it "sustains 100% accuracy across 200 function-calling trials" only on
  that structure.
- Epiphany-Aware KV Eviction (2026; https://arxiv.org/pdf/2606.26472; extracted text) [V]: counterfactual
  occlusion labels (32-token window replaced by padding, answer regenerated; "important fraction ≈0.20 on
  MATH-500 and 0.52–0.64 on AIME"); attention "is a noisy proxy for importance: attention sinks absorb weight
  regardless of content, and filler tokens attract weight while being generated yet are never referenced again".
  Their hidden-state-change score reaches 72% on MATH-500 at a 4096 budget vs H2O 67% (H2O "collapses" to 5% at
  1024). Caveat they discovered: "Any importance signal read from the residual stream over a long generation is
  exposed to the same [positional] drift" — they fix it with a causal rolling z-score.
- Reasoning-only counterpoint (Hold Onto That Thought, https://arxiv.org/html/2512.12008v1) [S]: on eight
  reasoning sets, cumulative attention (H2O, SnapKV-D) is the best signal because "reasoning models consistently
  retain a larger proportion of critical tokens". So heavy hitters are fine when the needed tokens are re-attended
  continuously (chain-of-thought) and fail when need is DELAYED (instructions, credentials, multi-turn queries).
  Stencil's problem is the delayed case.

1.3 Query-agnostic and learned methods that do transfer [V unless marked].
- KVzip (Kim et al., NeurIPS 2025 oral; https://arxiv.org/html/2505.23416; https://github.com/snu-mllab/KVzip):
  importance = attention received when the model is prompted to RECONSTRUCT its own context from the cache;
  "≈94% performance retention on SCBench with only 30% of KV slots" [S]; query-aware baselines "suffer significant
  performance degradation even at a 90% cache budget ratio under multi-query scenarios" [V]. Cost: "nc/m forward
  passes (m = 2K chunk)", "approximately doubles the initial prefill" [V]. Fails on Retr.Prefix-Suffix. Supports
  Qwen2.5/3 (README), so it is a runnable G2 baseline on Qwen3-1.7B/4B. Fast KVzip (https://www.arxiv.org/pdf/
  2601.17668) replaces the reconstruction pass with a trained gate [S].
- Learning to Evict / KV Policy (Apple, ICML 2026; https://arxiv.org/html/2602.10238v1;
  https://github.com/apple/ml-learning-to-evict): per-head 2-layer MLPs (~650K params each, 112 agents for
  Qwen2.5-7B) scoring from key, value and position ONLY ("avoiding queries or past attention scores"); reward =
  −(future attention mass of evicted tokens) over all budgets; REINFORCE with leave-one-out baseline; "~6,000
  samples from RULER; ~4,500 from OASST2", "less than 30 minutes on a single node of 8 NVIDIA H100"; zero-shot to
  BoolQ/ARC/GovReport/MMLU/HellaSwag "rank at or near the top". Notable: "supervised alternatives (differentiable
  sorting surrogates) fail to learn an effective policy". Benchmarks are RULER + OASST2 perplexity — no agentic or
  instruction-following eval.
- TRIM-KV / Cache What Lasts (https://arxiv.org/html/2512.03324): learned WRITE-time retention gate β per token
  with geometric decay β^(t−i), distilled from the frozen model (KL + NTP) on OpenR1-Math-220k (564M tokens,
  4×H100), gate params only. LongMemEval-S: 44.8% at 32K budget vs 27.6–27.8% for StreamingLLM/SnapKV [S];
  AIME24 75.8% at 4K budget vs 65.5% full cache. The closest published analogue to G1(a) and evidence that a
  write-time gate trained on ONE domain (math) transfers to a chat-memory benchmark.
- ForesightKV (https://arxiv.org/html/2602.03203v2): "Golden Eviction" labels = max future attention per KV;
  MLP scorer; stage-2 GRPO with reward "on low-entropy tokens experiencing large loss increases post-eviction"
  (the only published loss-delta-shaped signal I found); Qwen3-4B at 1K budget 54.5 vs R-KV 2K 44.8 on AIME24;
  trained on math, "generalization to GPQA, LiveCodeBench, LongBench".
- LookaheadKV (Samsung; https://research.samsung.com/blog/LookaheadKV-...): learnable lookahead tokens + LoRA
  trained by KL to the true response's attention; MT-Bench "on par or better" multi-turn; 16K→32K length transfer.
- LU-KV (ICML 2026; https://arxiv.org/html/2602.08585): oracle importance = max over future steps of attention ×
  ‖vW_O‖; offline head-budget profiling; RULER-16K (Mistral+SnapKV) 29.5% → 70.0%; "consistent trend in optimal
  local-to-global compression ratios across diverse tasks".
- IndexMem (ICML 2026; https://arxiv.org/abs/2605.25475) [S]: learned indexer + latent memory for evicted tokens;
  RULER +25 points under aggressive eviction.
- Program-evolved policies (CacheCraft; https://arxiv.org/html/2608.14555) [S]: a fixed 3-signal scorer wins every
  RULER cell but "underperforms on long-document comprehension"; conclusion is "benchmark-specific re-evolution
  ... rather than universal weights". Transfer of hand/evolved heuristics is regime-specific.
- Agentic KV management, the only two papers with agent benchmarks: SideQuest (https://arxiv.org/html/
  2602.22603v1) [V summary]: the model itself flags stale TOOL OUTPUTS in an auxiliary thread, trained on 215
  hindsight-labelled traces (last-reference time of each tool output); gpt-oss-20b: FRAMES −2 pts, BrowseComp −5
  pts at 56–65% peak-token reduction, while "H2O, SnapKV, R-KV suffer precipitous drops". Practical Online KV
  Compaction for LLM Agents (https://arxiv.org/html/2608.00902) [V summary]: BrowseComp-Plus and WideSearch on
  Qwen3.5-27B / Gemma-4-31B; "delayed future-turn queries consistently outperform immediate proxies (all four
  model-benchmark pairs)"; "immediate compaction often hurts"; compressed agents "repeat searches (21% vs 12%
  duplicate queries)"; simple token eviction "remains surprisingly competitive".
- NO paper evaluates KV eviction on BFCL v3/v4, τ-bench, MT-bench-101 or LongMemEval-with-eviction except TRIM-KV
  on LongMemEval [I: searched 6 phrasings]. A Stencil result there would be first — and unsupported by priors.

## 2. Counterfactual / loss-based salience and learned retention policies

2.1 LOO attribution is an established, expensive, non-additive oracle [V].
- ContextCite (Cohen-Wang et al. 2024; https://arxiv.org/abs/2409.00729) [S]: random ablation masks over context
  sources, forward pass per mask, Lasso surrogate mapping mask → Δ log p(response).
- AttriBoT (Paulo et al., ICLR 2025; https://arxiv.org/html/2411.15102v1) [V]: LOO = log p(R|Q,C) − log p(R|Q,C∖s);
  exact LOO "requires |C|+1 forward passes"; tricks: KV caching of the shared prefix (~2×), hierarchical
  paragraph→sentence attribution (speedup ≈ sources per group), proxy models ("smaller models' LOO scores show high
  correlation (R=0.97) with target model attributions"); ">300× speedup" overall, "30× faster than response
  generation itself". Relevance: G0 on Qwen3-1.7B is the proxy-model trick applied to itself — cheap — and the
  hierarchical trick (turn-level first, then sentence-level only inside high-scoring turns) is the right cost cut.
- Attention-output-error criteria (CAOTE, ICLR 2026, https://arxiv.org/abs/2504.14051 [S]; CriticalKV
  https://arxiv.org/pdf/2502.03805 [S]) are closed-form one-step perturbation proxies: "boosts Needle-in-Haystack
  recall by up to 60% at tight budgets" on top of H2O/TOVA/SnapKV, <0.1% prefill FLOPs. They still inherit the
  attention signal (query-aware), so they do not solve delayed need.
- Redundancy hazard [I]: LOO of a span whose literal also appears elsewhere (tool output, earlier assistant echo)
  is ≈0 for BOTH copies. In BFCL, 891 later-turn literals come from an earlier user turn but only 781 are absent
  from every earlier tool output (R6); the sole-source condition of the mechanical oracle (R7) must be carried into
  G0, e.g. leave-group-out over verbatim-duplicate spans, or the hierarchical (turn-then-span) protocol.

2.2 Learned retention policies (what they measured; did any transfer) [V unless marked]. Summary table:
| method | label | scored from | trained on | held-out transfer shown | agentic/IF eval |
| KVP (Apple) | future attention rank | K,V,pos | RULER 6k / OASST2 4.5k | zero-shot 5 tasks | OASST2 ppl only |
| TRIM-KV | distillation + capacity | hidden state at write | OpenR1-Math | LongMemEval, LongProc | LongMemEval |
| ForesightKV | future attn + loss-RL | K,V,attn feats | math | GPQA, LCB, LongBench | none |
| LookaheadKV | true-response attn | lookahead tokens | 16K seqs | 32K, MT-Bench | MT-Bench |
| LU-KV | oracle attn×value | offline head profile | synthetic 4k | LongBench/RULER | none |
| SideQuest | last-reference of tool outputs | model's own thread | 215 traces | BrowseComp (OOD −5) | agentic search |
| Stencil probe (repo) | clause labels | layer-20 residual | b3 + Multi-IF | LOCO F1 0.898/0.883; IFBench 0.684 | Multi-IF |
Reading: every transferring method scores from something available at write time (K/V/hidden state) and is trained
against a FUTURE-derived target; none is trained on loss-delta directly except ForesightKV's RL stage. None was
tested on tool-use. The repo's own probe (salience2.py:45-51) transfers as well as the linguistic finder across
instruction corpora (Gate 3: 0.684 vs 0.676) while being worse in-domain — consistent with "priors in the hidden
state generalize; surface rules fit the corpus".

2.3 Hidden-state-as-signal caveats [V]: positional drift of residual norms (Epiphany paper, 1.2); architecture-
specific probe depth (When Attention Closes: layer 2 to 27); Stencil's probe is welded to layer 20 of 1.7B — on 4B
the layer must be re-selected, not assumed.

2.4 Agent memory modules — evidence that they do NOT generalize and are confounded [V].
- LongMemEval (Wu et al. 2024; https://arxiv.org/html/2410.10813): long-context readers lose 30–55% vs oracle
  retrieval (GPT-4o 0.870 → 0.606; Llama-3.1-70B 0.744 → 0.334); gains come from indexing choices (session
  decomposition, fact-augmented keys +9.4% recall, time-aware query expansion +11.3%).
- MemDelta (2026; https://arxiv.org/abs/2606.29914; extracted text): "verbatim RAG matches full-context
  GPT-4o-mini (47.2% vs. 49.8%, p = 0.34)"; "agent self-memory (42%) underperforms basic retrieval (47%)"; Mem0's
  "+11pp" over RAG "was an embedding confound" (Mem0 72.7 vs cloud-RAG 73.9 "at 50× the cost").
- Cross-scenario generality of memory systems (2026; https://arxiv.org/pdf/2606.04315; extracted text): eight
  systems on five scenario families: "No method dominates", "existing memory systems struggle on agentic
  trajectories" (schemas drop step/action evidence; passive retrieval cannot surface it); the best generality is an
  agent harness that self-manages flat text files via tool calls (AutoMEM).
- MemoryAgentBench (ICLR 2026; https://arxiv.org/abs/2507.05257) [S]: "No single-memory paradigm is sufficient
  across all competencies".
Implication: Mem0/A-MEM/MemGPT-style stores are not comparators for a retention mechanism inside the trunk; they
are pipelines whose measured gains are dominated by embedding/model swaps.

## 3. Does self-echo / self-summary beat learned selectors on long-horizon agentic work? Latency?

- The Complexity Trap (JetBrains, NeurIPS-25 DL4Code; https://arxiv.org/html/2508.21433) [V]: SWE-bench Verified,
  raw / observation-masking / LLM-summary: Qwen3-Coder-480B 53.4 / 54.8 / 53.8; Gemini-2.5-Flash 32.8 / 35.6 /
  36.0; Qwen3-32B 17.0 / 15.0 / 16.0. Both halve cost; summarization lengthens trajectories ~15% "by obscuring
  natural stopping signals". Masking is the stronger default for the smallest model tested.
- SelfCompact (2026; https://arxiv.org/abs/2606.23525) [V abstract]: model decides when to compact via a rubric;
  "up to 18.1 points" on competition math and "5–9 points" on agentic search at "30–70% lower per-question cost"
  vs fixed-interval summarization (7 models, 6 benchmarks). ACON (https://arxiv.org/abs/2510.00615) [V abstract]:
  natural-language-optimized compression guidelines; peak tokens −26–54%; "smaller language models achieved up to
  46% performance improvement" (context distraction). TRACE / execution-instability study on AppWorld
  (https://arxiv.org/html/2608.06503v1) [V summary]: repeated compression widens the gap between solved-once and
  solved-twice; "blocked actions (+0.108 at first step post-compaction)"; TRACE 77.1% / Pass² 67.3 vs prompting
  71.4 / 59.5. Compaction is a recurring intervention with its own failure modes, not a free lunch.
- RL-trained consolidation (MEM1, https://arxiv.org/abs/2506.15841 [V abstract]: MEM1-7B 3.5× the EM of
  Qwen2.5-14B on 16-objective QA at 3.7× less memory; Memory-as-Action https://arxiv.org/abs/2510.12635 [S]) beats
  full-context but requires end-to-end RL of the trunk — off the table for a frozen trunk.
- Latency: every self-summary arm adds a full generation per compaction (SelfCompact reports cost, not wall-clock;
  SideQuest runs a parallel thread and claims net throughput +83.9% only because pruning pays it back) [V/S]. On a
  1.7B trunk generating the summary is cheap in FLOPs but the summary quality is bounded by the trunk (Qwen3-4B
  BFCL multi-turn baseline 15.75% [S, FunReason-MT], repo expects 1.7B ~8–10%).
- Head-to-head learned-selector vs self-summary on the SAME agentic benchmark: none found [I]. The closest is
  SideQuest (self-driven staleness) vs H2O/SnapKV/R-KV (attention selectors), where self-driven wins — but the
  selector baselines there are the ones already known to fail on delayed need.
Answer: self-echo is a legitimate reported arm and a plausible fallback for tool outputs (Sec. 6, arm E), not the
primary mechanism, and it must be scored with the trajectory-length and repeat-call diagnostics.

## 4. Smallest experiment that would show G1 generalizes

4.1 Corpora (three, in-repo or open):
- C1 Multi-IF (data/bench/multiif_en.jsonl, 909 sessions): persistent style/format constraints; later turns are
  gold-checkable (IFEval checkers).
- C2 BFCL v3 multi-turn NON-cohort (704 cases excluding dev 32 + sealed 64; data/bench/bfcl_v3_mt): tool schemas,
  parameters, tool outputs; later gold turns = ground-truth calls rendered as <tool_call> JSON with REAL executor
  outputs (already reproducible on CPU per R3).
- C3 a third, style-shifted dialogue corpus with gold later turns: APIGen-MT-5k (Salesforce, 5k verified multi-turn
  tool trajectories, https://huggingface.co/datasets/Salesforce/APIGen-MT-5k — check license before use) or, if
  license blocks, OASST2 (Apache-2.0; generic chat, later assistant turns as targets, perplexity-only eval).
  Rotation: train on two, test on the third, all three rotations; the publishable claim is the held-out-corpus AUC
  and recovery, never the pooled number.

4.2 Oracle definition — use BOTH, with the loss delta primary:
- G0-loss (label-free, all corpora): for span s in turn u and later gold turn t, δ(s,t) = NLL_t(context ∖ s) −
  NLL_t(context), teacher-forced on the trunk, restricted to the later turn's ARGUMENT/answer tokens where a
  structure exists (tool-call JSON values; the constrained answer) and to the full turn otherwise. Span unit =
  the finder's unit (sentence/clause for user text; tool-output records for tool turns; schema entries for the
  <tools> block). Hierarchical: score turns first, then spans inside turns whose δ_turn > τ (AttriBoT). Redundancy:
  remove all verbatim duplicates of s together (leave-group-out) so sole-source spans are not masked (R6/R7).
- G0-prov (BFCL only, verifiable): the mechanical provenance oracle R7 — a span RETAINS iff a later ground-truth
  call uses a literal present in the span and absent from the later turn's own user text — extended to tool-output
  records. Report Spearman(δ, prov) as the sanity check that the loss oracle finds what the executor needs.
- Position control: δ must be compared against a position-matched null (same span index, shuffled label) because
  residual-stream signals drift with position (Sec. 2.3).

4.3 Probe, floors, controls.
- G1a write-time admission probe: logistic/2-layer MLP on the span's mean layer-L residual at its OWN turn (L
  re-selected per trunk by a 5-layer sweep on C1 dev, not assumed 20), target = δ top-quantile. G1b read-time
  selection probe: same features concatenated with the CURRENT turn's last-token residual (the "When Attention
  Closes" AUC-0.99 position), target = δ for THIS later turn. Report both; G1b is the Miller-shaped one.
- Floors (register before looking): held-out-corpus AUROC ≥ 0.80 for G1a and ≥ 0.85 for G1b (chance 0.5;
  When-Attention-Closes gets 0.99 in-distribution, TRIM-KV/KVP transfer suggests 0.8 is reachable [I]); and
  RECOVERY ≥ 0.5 where recovery = (NLL_evicted − NLL_arm) / (NLL_evicted − NLL_full) on later gold turns at a
  matched pin budget (the continuous estimand; H1′ pass rates were 44/14/48 of 56 → recovery 0.77 for pinned_echo,
  results/h1p-review-fable.md).
- Controls at the SAME budget, all scored query-agnostic (before the later turn exists): random spans (existing
  control), recency (StreamingLLM), "all prior user turns" (the ADOPT-MINIMAL rule), attention-mass heavy hitters
  (H2O/SnapKV with the observation window ending at the CURRENT user turn), KVzip reconstruction score (supported
  on Qwen3), the linguistic finder. Falsifier for G1: it does not beat the best structural control corpus-held-out
  with LB > 0 (paired by conversation, cluster-robust).
- Confirmatory (after the floors): pinned+echo vs control on the sealed BFCL cohort and Leg B, unchanged.

4.4 Cost on one GB10, ~1k conversations [I — arithmetic, not measured]: BFCL non-cohort final prompts median
5.9k tokens (long_context 8.9k, max 72k; cap G0 at 16k or skip overflowers). ~30 spans per conversation
(≈20 user sentences + ≈10 tool records) → ~30k teacher-forced forwards of ≈6k tokens on 1.7B ≈ 2·1.7e9·6e3 ≈ 2e13
FLOPs each → 6e17 FLOPs; at an effective 50–100 TFLOP/s bf16 that is 2–3 h, 4–6 h with attention overhead and
prefix-cache misses; 2× on 4B. Hierarchical scoring (turn-level first) cuts it 2–4×. Feature extraction is one
forward per conversation (already paid inside the oracle pass); probe fitting on ~30k rows is CPU minutes. So yes:
hours, provided long_context is capped. The repo's memory note "GB10 ~0.4 steps/s at hard cell" is a training
figure and not comparable.

## 5. Miller framing check

What Miller actually claims (verbatim where possible) [V, extracted texts and open articles]:
- Storage: "spiking-induced changes in synaptic weights, 'impressions' left in the network" hold the items between
  bursts; "Multiple items can be simultaneously held by multiplexing in time their brief bouts of activity"
  (Working Memory 2.0, Neuron 2018, Miller-Lundqvist-Bastos PDF, p. 464).
- Control: "(top-down) deep-layer beta regulates the expression of (bottom-up) gamma in superficial layers, thus
  gating the access of sensory information to working memory and controlling its maintenance"; "beta can turn on
  and off the 'faucet' of gamma-related working memory reactivations"; "To clear out working memory, beta power and
  coupling increases" (WM 2.0, pp. 470–471).
- Granularity: "with the spatiotemporal pattern of beta changing with top-down information, beta's inhibitory
  effects can act selectively and direct the flow of sensory information"; "content-specific 'beta ensembles'";
  and explicitly "This requires control at the level of individual ensembles, not just a general gating mechanism"
  (WM 2.0 p. 469, 471). Lundqvist et al. 2018 (Nat Commun; PMC5785952): "In anticipation of having to use an object
  for the match decision, there was an increase in gamma and spiking information about that object and reduced
  beta bursting. This readout signal was only seen before relevant test objects ... When the objects were no
  longer needed, beta increased and gamma decreased together with object spiking information"; "cortical beta as a
  spatiotemporal filter, dictating when and where sensory information is encoded". Lundqvist 2016 (Neuron):
  "gamma bursts could gate access to, and prevent interference of, working memories".
- Miller 2018 (MIT News): waves "carry our knowledge and goals ... and regulate the higher frequency gamma waves
  that handle the new sensory information"; Miller 2026 (MIT News, 2026-09-01): "Synapses store representations,
  while wave dynamics help determine which representations are active at any given time"; beta waves act as
  "mobile stencils" governing where and when gamma can engage local cortex.
Mapping verdict:
- Defensible: KV columns of a span = the synaptic "impression" (passive, stored); the decision of which stored
  spans are re-activated for the CURRENT response (pin + echo, chosen from the current state, item-level) = the
  beta-gated, anticipatory, object-specific readout. Miller's selection is READ-time and need-anticipating ("in
  anticipation of having to use an object"), at item/ensemble granularity, and includes CLEARING when no longer
  needed (eviction). That is G1b plus eviction, applied per span.
- Decoration: calling a WRITE-time importance score (G1a, TRIM-KV-style "how important is token i for the long
  run") a "wave" — Miller's waves do not decide at encoding what will be stored; storage is the synaptic default
  and the wave decides what is expressed now. Also decoration: any claim about oscillation frequency, laminar
  structure or "traveling" (the 2022/2025 traveling-wave papers, https://pmc.ncbi.nlm.nih.gov/articles/PMC8827486/,
  https://www.pnas.org/doi/10.1073/pnas.2415573122, are about spatial organization of readout in cortex, with no
  computational analogue in a KV cache).
- The dead-amplification result (H1) is consistent with Miller: his gating is inhibitory/selective (beta suppresses
  the non-selected), not a gain boost on the selected; retention + selective re-expression is the closer analogue.

## 6. Concrete spec (G0 / G1 / G2), smallest version

Phase A (CPU + one GPU pass, no training): G0-loss + G0-prov on C1, C2, C3 (capped at 16k tokens). Outputs per
span: δ, provenance flag, position, role (user/tool/schema/assistant). Register: the redundancy rule, the cap, the
span unit, the later-turn token restriction. Report: oracle mass by role per corpus (expect tool outputs to carry a
large share in BFCL long_context — R3/R6 — which would already falsify a user-turn-only finder as a generalizing
mechanism).
Phase B (G2, zero training): recovery-at-budget of recency, all-user-turns, query-agnostic H2O/SnapKV, KVzip,
linguistic finder, random — against the G0 oracle's own recovery (oracle-pinned = ceiling). If the best structural
policy ≥ 0.8 of oracle: stop, adopt it, move to the confirmatory legs.
Phase C (G1): fit G1a/G1b in the 3 held-out rotations; floors of 4.3; positional-shuffle null; report per-role
AUROC (the schema role is trivially separable and must be excluded from the headline).
Phase D (confirmatory, only if C passes): BFCL sealed cohort and Leg B with the H1′ arms (base | ledger = G1
pin+echo | random-span control from tool/assistant text) after the harness fixes (F1/F3 of my earlier review).
Arm E (reported only): self-echo = the trunk writes a ≤ 64-token "what I still need" note at each turn, injected
as echo; diagnostics: trajectory length, duplicate tool calls (the 21% vs 12% signature), NLL recovery.

## 7. Do not do this

- Do not use attention-mass heavy hitters (H2O/SnapKV/TOVA/PyramidKV) as the automatic finder: multi-turn collapse
  (SCBench), instruction eviction bias (Pitfalls), 0% on dormant tokens, and they lose to "start + recent window"
  once the query is hidden.
- Do not score any attention baseline with the later turn visible (query-aware +0.198 inflation), and do not mix
  attention backends across arms (−0.22 to −0.29 shift).
- Do not present a regex/anchor class family (K2, "key:"/"password:") as generalizing; the literature's own fixes
  of this kind are task-specific by construction (Transactional Attention, Pitfalls whitelist).
- Do not train and evaluate a probe on corpora that share templates (salience2 F2 finding); corpus-held-out or
  nothing. Do not reuse layer 20 on Qwen3-4B without a sweep.
- Do not read a raw residual-norm or LOO score without a position-matched null (drift).
- Do not use single-span LOO where literals are duplicated across turns (masking); use leave-group-out.
- Do not run any BFCL retention arm before the <tools> prefix sink and an actually-evicting budget are in place;
  in base/missing_* nothing is evicted (R3) and in long_context the schema goes first (R4/R5).
- Do not use pass-rate as the primary estimand for the G phases at n = 64 with base competence 8–16%; use NLL
  recovery on gold later turns, pass-rate as confirmatory.
- Do not compare against Mem0/MemGPT/A-MEM/Zep pipelines (embedding/model confounds, 50× cost) — they are not the
  same object.
- Do not retrain the trunk (gist/ICAE/AutoCompressor/MEM1/MemAct-style) — off-charter for a frozen trunk and their
  compression fails outside the fine-tuning distribution ("cannot be used with the original untuned LLM").
- Do not call a write-time importance probe "waves select"; reserve the phrase for read-time, per-span,
  need-anticipating selection with clearing.

## 8. Verification ledger

Opened and read (full text, html, or pdftotext): SCBench html; KVzip html + GitHub; Learning to Evict html;
query-visibility audit PDF; Pitfalls PDF (ACL 2026 version); When Attention Closes PDF; Epiphany PDF; MemDelta
PDF; cross-scenario memory PDF; LU-KV PDF/html; AttriBoT html; LongMemEval html; Complexity Trap html; TRIM-KV
html; ForesightKV html; Expected Attention html; Working Memory 2.0 PDF; Lundqvist 2016 PDF; Lundqvist 2018
(Europe PMC XML); MIT News 2018 and 2026 items; risk-of-KV-compression html (LongBench-v2 only, not agentic).
Snippet-only [S]: Transactional Attention (abstract), SideQuest (html summary), Practical Online Compaction (html
summary), Hold Onto That Thought, IndexMem, CacheCraft, Fast KVzip, MemoryAgentBench, MEM1, ACON, SelfCompact
(abstract), FunReason-MT Qwen3-4B baseline, APIGen-MT license. Inferred [I]: cost arithmetic (4.4), redundancy
hazard (2.1), floors (4.3), absence claims ("no paper evaluates eviction on BFCL/τ-bench") after six search
phrasings.
