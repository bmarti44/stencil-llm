# Web research: making a small frozen model apply stated coding conventions

**Date:** 2026-09-11 (filed 2026-09-12) · **Author:** Claude Opus 5 (research agent, web-only)
**Scope:** everything EXCEPT attention steering (PASTA/SpotLight), MemoryCode follow-ups, and
MemGPT/Mem0-style memory — those are covered by a sibling report.
**Target setting:** frozen Qwen3-1.7B (optionally 4B), greedy decoding, 4–8 regex-checked coding
conventions stated earlier in a long session, restated 1–2 sentences before the request; current
result = 0/16 strict compliance on both arms while the model paraphrases the rule in prose.

---

## Executive summary (ranked by likelihood of lifting a 1.7B–4B model off a zero-strict floor)

1. **Regex/grammar-constrained decoding applied only at identifier-declaration positions** is the
   single intervention with a *mechanical* guarantee, near-zero serving overhead (XGrammar, 2411.15100),
   and it is the one thing that cannot "forget" a rule; but every measured study says it costs quality,
   and the cost is largest at the smallest sizes (Qwen2.5-1.5B: 26% → 22% when constrained, 2502.09061).
2. **Generate → regex-check → re-generate with the exact violation text** (external verifier, never
   self-critique) is the best-evidenced cheap win at 1–3B: execution-feedback refinement at 1–3B gives
   >4 SD gains, but *only* on mechanically identifiable error classes (NameError/SyntaxError), not on
   semantic ones (2604.21950) — a convention violation is exactly that mechanical class.
3. **RLVR (GRPO) on synthetic, held-out-split convention data**, not SFT/DPO: +17 pp on *unseen*
   constraints vs +9.8 pp on in-domain IFEval (IFBench, 2507.02833). This is the only adaptation with
   published out-of-domain generalization evidence; it is also the only one that yields a real HF artifact.
4. **Switch Qwen3 thinking OFF for these constraints.** Qwen3-1.7B IFEval prompt-strict drops 62.48 →
   58.96 with thinking ON, and the "Precision (exact local form)" constraint class — which is precisely
   what `gn_` prefixes and "name contains a digit" are — loses ~8.5 pp at class level while "Planning"
   constraints gain (2606.09662). Free, and currently probably working against you.
5. **Constraint design beats prompt formatting.** The only controlled study of encoding form found a
   *null* result for verbose-prose vs compact-header vs exemplar encodings (Cliff's δ < 0.01), while
   constraint *type* moved compliance 9 pp and counter-intuitive constraints opposing model defaults
   failed at **10–100%** vs **99%+** for conventional ones (2604.07192). `gn_` is a counter-intuitive
   constraint; rewording it will not help.
6. **Model size is the strongest single lever available for free:** 1.7B → 4B is +13.7 pp IFEval
   non-thinking (68.2 → 81.2) and +9.4 pp thinking (72.5 → 81.9) in Qwen's own report (2505.09388).
7. **Few-shot exemplars of the convention being applied are weaker than the instruction itself** for
   style (combined > instructions > examples, 2511.13972), and small models provably ignore in-context
   evidence that contradicts pretraining priors — overriding semantic priors is an emergent ability of
   scale (2303.03846). This is the cleanest explanation for "verbalizes but does not apply".
8. **Self-critique without the regex will not work at this size:** moral/reasoning self-correction turns
   positive only above ~3.8B parameters and is net-negative at ~1B (2410.23496); small LMs need strong
   external verifiers (2404.17140, ACL Findings 2024).
9. **Expect the floor, and stop scoring strict-only.** Qwen3-1.7B scores 44.2% on a *single* Coding-Style
   constraint and 44.8% overall on MultiCodeIF; hard satisfaction across multiple simultaneous
   constraints collapses from 54.5% to 18.8% for the whole model pool (2507.00699). 0.44^4 ≈ 3.7%, so
   0/16 strict on 4 conventions is the *predicted* value, not an anomaly.
10. **With n = 16, a strict-zero arm cannot detect anything below ≈17 pp** (rule of three / exact binomial:
    0/16 → 95% upper bound 1 − 0.05^(1/16) = 17.1%). Score per-convention per-item (64+ binary outcomes),
    report partial credit alongside strict, and pair with McNemar on matched items.

---

## Q1 — Decoding-time constraint enforcement

### Does the machinery exist for style/naming constraints?
Yes, and it is production-grade, but **nobody has published a benchmark of it on style/convention
constraints.** The engines all compile regex → FSM or CFG → pushdown automaton and mask logits:

- **XGrammar** ([arXiv 2411.15100](https://arxiv.org/abs/2411.15100), Nov 2024; [MLC blog](https://blog.mlc.ai/2024/11/22/achieving-efficient-flexible-portable-structured-generation-with-xgrammar), 2024-11-22): splits the vocabulary into
  context-independent tokens (prechecked, cached) and context-dependent tokens; **up to 3.5× faster than
  prior engines on JSON-schema and 10× on CFG-guided generation, up to 100× in microbenchmarks, and
  ~zero TPOT overhead end-to-end** (14× / 80× end-to-end on H100). Cost is therefore *not* latency.
- **Outlines** (FSM from regex), **llguidance/guidance**, **SGLang** (compressed FSM,
  [LMSYS, 2024-02-05](https://www.lmsys.org/blog/2024-02-05-compressed-fsm/)), **vLLM** — all accept a raw regex, so
  `def gn_[a-z_]+\(` or `class [A-Za-z]*[0-9][A-Za-z0-9]*\b` is expressible today with no training.
- **Sketch-Guided Constrained Decoding** ([2401.09967](https://arxiv.org/abs/2401.09967), v4 2024-07-22) does it without logit
  access, via a local auxiliary model that rewrites an unconstrained "sketch".
- **Context-sensitive** constraints (variable scope, types, "every call site uses the same name")
  require more than a regex: a dynamic tree-of-parsers emitting a per-step regex
  ([2508.15866](https://arxiv.org/abs/2508.15866), 2025-08-20), or a type-aware prefix automaton
  ([2504.09246](https://arxiv.org/abs/2504.09246), PLDI 2025).

### Measured gains where constrained decoding was actually evaluated on code
- **Type-constrained decoding** (2504.09246, PLDI 2025): 94% of compile errors in LLM TypeScript are type
  errors; enforcing types **halves compilation errors**, raises functional correctness **+3.5–5.5%
  relative**, and improves functionally-correct repair of non-compiling code **+37% relative**.
- **Secure code generation** ([2405.00218](https://arxiv.org/abs/2405.00218), v3 2024-07-20): constrained decoding beats
  prefix tuning for security *without* a specialized dataset, and beats GPT-4; importantly, **prefix
  tuning bought security by sacrificing functional correctness** — a direct warning for Q5.

### Measured quality costs (the honest part)
- **"Let Me Speak Freely?"** ([2408.02442](https://arxiv.org/abs/2408.02442), Aug 2024): JSON-mode constrained decoding
  cost **−27.4 pp on GSM8K for GPT-3.5-Turbo (76.60 → 49.25), −25.8 pp for LLaMA-3-8B (74.73 → 48.90),
  −63.1 pp for Claude-3-Haiku**; Last-Letter-Concatenation **−42.1 pp for LLaMA-3-8B (70.07 → 28.00)**.
  Classification *gained* (DDXPlus +11 to +19 pp). Lesson: format restriction helps when the answer space
  is small, hurts when the model must reason in the constrained channel.
- **CRANE** ([2502.09061](https://arxiv.org/abs/2502.09061), v4 2025-09-05), greedy-ish 8-shot GSM-Symbolic, verified in the
  paper's tables: **Qwen2.5-1.5B-Instruct 26% unconstrained-CoT → 22% constrained → 31% CRANE**;
  Llama-3.1-8B 30 → 26 → 33; DeepSeek-R1-Distill-Llama-8B 21 → 13 → 31. Degradation from hard constraints
  is worst at the smallest size; the fix is to *interleave* free and constrained regions rather than
  constrain throughout.
- **Distribution distortion is intrinsic**, not an implementation bug: grammar-constrained decoding is
  greedy token masking and yields grammatical outputs whose likelihoods are not proportional to the
  model's own distribution (**Grammar-Aligned Decoding / ASAp**, [2405.21047](https://arxiv.org/abs/2405.21047), NeurIPS 2024).
- **Constrainer misalignment can be catastrophic**: "The Alignment Problem in Constrained Code
  Generation" ([2606.21619](https://arxiv.org/abs/2606.21619), Jun 2026), 7 LMs, 2 languages, 3 benchmarks — when the
  constrainer is *incomplete*, unconstrained decoding significantly beats constrained, and incompleteness
  pushes the model into low-probability regions, causing timeouts and **functional-correctness loss of up
  to 97%**. A hand-written naming regex is almost certainly incomplete w.r.t. "valid Python".
- **Constraint tax / priority inversion**: with JSON-schema masks plus tool calling, multiple open-weight
  models stop calling tools entirely because tool-call tokens become unreachable under the mask
  ([2606.25605](https://arxiv.org/abs/2606.25605), Jun 2026). Mitigation: two-pass execution — generate freely, then
  constrain only the part that must conform.
- **Grammar keys are themselves an instruction channel**: changing only schema-key wording under
  constrained decoding substantially moves accuracy, and **Qwen models benefit more from schema-level
  instructions than LLaMA does** ([2604.14862](https://arxiv.org/abs/2604.14862), Apr 2026) — relevant because a
  convention-bearing grammar may itself carry the instruction.
- **Negative constraints** ("never use X") need different machinery: complement/intersection of regexes
  explodes the automaton; **NCO** ([2605.10065](https://arxiv.org/abs/2605.10065), May 2026) does online pattern matching
  with soft masking instead.

### Verdict for this project
Constrained decoding is the only guaranteed route, but applying it to a whole function body imports the
2606.21619 failure mode. The defensible design is **two-pass / sketch**: let the model write freely, then
re-emit only the declaration tokens under a regex (or generate a name-bearing skeleton under constraint
and fill bodies unconstrained). Note also that this is a *decoding harness*, not a model artifact — if the
deliverable must be an HF model whose unmodified twin is the control, constrained decoding fails the
fairness frame unless both arms get the same decoder.

---

## Q2 — Inference-time self-correction loops for constraints

**The key distinction in the literature is intrinsic self-critique (fails) vs external verifier (works).**
A regex checker is a perfect external verifier, which puts this project on the favorable side.

- **Intrinsic self-correction fails**: LLMs struggle to self-correct reasoning without external feedback
  and sometimes degrade ([2310.01798](https://arxiv.org/abs/2310.01798), ICLR 2024).
- **Size threshold ~3.8B**: across Llama-2 and Phi-3 families, *all* models above 3.8B gain from
  self-correction while smaller ones do not improve and get worse (1B explicitly); at 335M/775M the models
  cannot even produce the required answer format ([2410.23496](https://arxiv.org/abs/2410.23496), TrustNLP 2025). Safety/
  instruction alignment mattered more than size (Phi-3-3.8B beat all Llama-2 sizes).
- **Small LMs need strong verifiers**: ≤13B models self-correct well with a GPT-4-based verifier but the
  *self*-verifier (deciding *when* to correct) is the bottleneck ([2404.17140](https://arxiv.org/abs/2404.17140),
  ACL Findings 2024).
- **Best direct evidence at your scale — "Feedback Over Form"** ([2604.21950](https://arxiv.org/abs/2604.21950),
  2026-04-23): 1–3B pipelines, local inference, HumanEval + sanitized MBPP. **Self-refinement with
  execution feedback improves code generation by more than 4 standard deviations on both benchmarks**, but
  "the gains are narrow in mechanism: refinement fixes many runtime errors (especially NameError and
  SyntaxError), but rarely fixes logic errors such as AssertionError." Two more transferable findings:
  **early stopping is essential — without it every iteration is net-negative**; and **refiner capability
  matters more than generator identity** (a 1.5B generator + 3B refiner matched 3B doing both). Also:
  "Preliminary text-only pipeline experiments without execution feedback did not show gains at this scale"
  — i.e. the *mechanical* signal is what carries the loop, not the prose.
- **Constraint-repair, measured on code conventions — MultiCodeIF** ([2507.00699](https://arxiv.org/abs/2507.00699), Jul
  2025; 2,021 tasks, 14 languages, 9 constraint categories incl. Coding Style = naming conventions,
  indentation, brace style): with structured feedback naming the violated constraints,
  **average constraint satisfaction rises 63.0% → 83.4% over four repair rounds** (metric: IFRepair@k =
  HSR after the k-th repair). The repair curve is reported for the frontier models; the paper does **not**
  publish a per-round curve for Qwen3-1.7B, which is the honest gap in the literature for your exact case.
- **CYCLE** ([2403.18746](https://arxiv.org/abs/2403.18746), OOPSLA 2024) trains 350M/1B/2B/3B code LMs to self-refine:
  up to **+63.5%** code-generation improvement, and CYCLE-2.7B refined **27.6% more** previously-failed
  APPS samples than the vanilla model, which could not refine its own wrong predictions at all. I.e. at
  ≤3B, self-refinement is a *trained* capability, not a free prompting capability.
- **Plateau/regression is real**: in an IaC feedback loop, effectiveness plateaus around the 5th iteration
  and old errors spawn new ones ([2411.19043](https://arxiv.org/abs/2411.19043), Nov 2024).
- **Do not dress the loop in constrained decoding**: forcing structured reflection through Outlines on
  Qwen3-8B did **not** improve self-correction and instead produced "structure snowballing" — near-perfect
  syntactic alignment with no semantic error detection ([2604.06066](https://arxiv.org/abs/2604.06066), 2026-04-07).
- **Checklist-style verification works when the verifier is competent**: checklist-based soft verification
  moved IFEval **73.89 → 84.20 (+10.3)** with a GPT-OSS-20B verifier and **85.00 (+11.1)** with a 120B
  verifier ([2510.14842](https://arxiv.org/abs/2510.14842)); TICK/STICK shows self-generated checklists drive
  in-context self-improvement via refinement or best-of-N ([2410.03608](https://arxiv.org/abs/2410.03608), Oct 2024).
  Both use large verifiers — at 1.7B the regex must play that role.

**Verdict:** a *single* targeted repass, with the exact regex violation quoted and a hard stop after one
or two rounds, is the highest-expected-value cheap intervention. Caveat for fairness: it is a scaffold,
so the control arm must get the identical loop with the identical verifier.

---

## Q3 — Prompt-side interventions

### What is measured to help
- **Instructions beat examples for style; combined beats both.** "Show and Tell"
  ([2511.13972](https://arxiv.org/abs/2511.13972), Nov 2025), 160 paired Python programs, two-turn protocol:
  combined prompts gave the strongest initial control *and* the best "expansion discipline" (constraint
  survival into turn 2); instructions alone gave large initial effects with moderate discipline;
  **examples alone gave modest initial effects and no expansion discipline.** Caveat: frontier-class
  models, not sub-4B.
- **Re-reading (RE2)** ([2309.06275](https://arxiv.org/abs/2309.06275), EMNLP 2024): repeat the question in the input.
  davinci-003 gains averaged **+3.81 / +2.51 / +1.85** points (arithmetic/commonsense/symbolic) with
  Vanilla+RE2 and **+2.22 / +1.23 / +5.25** with CoT+RE2. But it **succeeded in only ~71% of ChatGPT
  experiments** (AQUA −5.12, MultiArith −1.16), and the authors attribute failures to disrupting an
  instruction-tuned model's learned pattern. Non-IFT Llama-2-13B/70B improved consistently. Small, noisy,
  and untested on sub-4B instruct models.
- **EchoPrompt** ([2309.10687](https://arxiv.org/abs/2309.10687)): "let's repeat the question before answering" — the
  closest published analogue to *constraint verbalization*; substantial gains across four causal LM
  families, no consistent gains on multiple-choice. Note your model already verbalizes the rule correctly
  and still violates it, so the mechanism EchoPrompt targets (query understanding) is not your bottleneck.
- **Bridge constraints / constraint graphs**: making primary constraints more salient via auxiliary
  derived constraints **cut constraint violations 39% vs standard prompting** while preserving reasoning
  ([2606.03624](https://arxiv.org/abs/2606.03624), Jun 2026) — on large reasoning models.
- **System vs user placement**: SysBench ([2408.10943](https://arxiv.org/abs/2408.10943), v2 2024-10-22) is the
  academic instrument here — 500 system messages × 5 turns, metrics CSR (per-constraint), ISR (all
  constraints for an instruction), SSR (multi-turn stability) — and names *constraint violation,
  instruction misjudgement and multi-turn instability* as the three failure modes. It documents wide
  cross-model variance but does **not** give a clean "system beats user" rule; the only placement claims
  I found for sub-4B models (Qwen2.5-Coder-3B flipping compliance by placement) are blog-grade
  ([tianpan.co, 2026-04-14](https://tianpan.co/blog/2026/04/14/the-instruction-position-problem)) and should be treated as
  a hypothesis to test locally, not a citable result.

### What is measured NOT to help (and should change your current setup)
- **Rewording / compacting / re-encoding the rules: null result.** 2604.07192 (Apr 2026), 6 rounds,
  11 models, 16 tasks, 830+ invocations: compact structured constraint headers cut constraint tokens ~71%
  and full prompt tokens 25–30%, but **no statistically significant CSR difference across three encoding
  forms or four propagation modes; Cliff's δ < 0.01, 95% CI ±2.6 pp.** The variance lived elsewhere:
  **constraint type (Δ = 9 pp normal vs counter-intuitive), and counter-intuitive constraints opposing
  model defaults failed at 10–100% while conventional constraints hit 99%+ regardless of encoding.**
  The paper's own conclusion: "engineering effort toward compliance is better directed at constraint
  design than prompt formatting." It also reports that **model self-assessments systematically
  overestimate compliance relative to rule-based scoring, revealing a gap between constraint
  understanding and execution** — i.e. your verbalize-but-don't-apply observation, replicated.
- **Chain-of-thought / thinking mode hurts exactly this constraint class.** 2606.09662 (Jun 2026) studies
  IFEval with **Qwen3 1.7B–32B using same-weights Thinking ON/OFF**: aggregate change is small
  (−0.55 to −3.52 pp) but 10–20% of prompts flip. Verified from the paper's table: **Qwen3-1.7B 62.48
  (OFF) → 58.96 (ON), −3.52 pp**, the largest drop in the family. Constraints split into **Planning**
  (global counting, structure, coordination — improves under thinking) and **Precision** (exact local
  form — consistently worsens). A `gn_` prefix or "class name contains a digit" is a Precision constraint.
  The paper also reports an **execution gap**: for Planning constraints, trace relevance to the constraint
  has near-zero correlation with final compliance (r ≈ 0.02), and for Precision constraints the
  correlation is *negative* (r ≈ −0.05), with failing instances having *higher* mean trace relevance than
  passing ones. Talking about the rule more is anti-predictive of obeying it.
- **More reasoning capacity trades against controllability** in general: MathIF
  ([2505.14810](https://arxiv.org/abs/2505.14810), May 2025) — models tuned on long distilled CoT or
  reasoning-oriented RL degrade in instruction adherence, worse as generation length grows, and simple
  interventions recover obedience only at a reasoning cost.

---

## Q4 — Model-size thresholds for constraint following

### Table: size vs constraint-following score
All Qwen3 / baseline IFEval numbers verified directly from the Qwen3 Technical Report HTML
([2505.09388](https://arxiv.org/abs/2505.09388), 2025-05-14), Tables 17–20, metric = **IFEval strict prompt-level**.

| Model | Params | IFEval strict-prompt (non-thinking) | IFEval strict-prompt (thinking) | Other constraint scores |
|---|---|---|---|---|
| Qwen3-0.6B | 0.6B | **54.5** | **59.2** | — |
| Qwen3-1.7B | 1.7B | **68.2** | **72.5** | MultiCodeIF avg 44.8%; **Coding Style 44.2%**; Non-functional 2% |
| Qwen3-4B | 4B | **81.2** | **81.9** | — |
| Qwen3-8B | 8B | **83.0** | **85.0** | — |
| Qwen3-14B | 14B | 84.8 | 85.4 | — |
| Qwen3-32B | 32B | 83.2 | 85.0 | — |
| Gemma-3-1B-IT | 1.0B | 54.5 | — | — |
| Qwen2.5-1.5B-Instruct | 1.5B | 42.5 | — | CRANE/GSM-Sym 26% uncon. / 22% constrained |
| Qwen2.5-3B-Instruct | 3.1B | 58.2 | — | — |
| Phi-4-mini | 3.8B | 68.6 | — | self-correction threshold model (2410.23496) |
| Qwen2.5-7B-Instruct | 7B | 71.2 | — | CodeIF CSR 0.153 easy / 0.104 hard |
| LLaMA-3.1-8B-Instruct | 8B | 75.0 | — | — |
| Gemma-3-12B-IT | 12B | 80.2 | — | — |
| Qwen2.5-14B-Instruct | 14B | 81.0 | — | — |
| Llama-3.2-3B | 3B | — | — | MultiCodeIF avg 46.8%, Coding Style 43.8% |
| DS-R1-Distill-Qwen-1.5B | 1.5B | — | 39.9 | — |
| DS-R1-Distill-Llama-8B | 8B | — | 59.0 | — |
| Qwen2.5-72B-Instruct | 72B | 74.7 (IFEval) | — | **IFBench (held-out constraints) 31.3** |
| Tülu-3-70B | 70B | 81.1 (IFEval) | — | **IFBench 25.5** |

Second axis — **number of simultaneous constraints** (ManyIFEval / StyleMBPP,
[2509.21051](https://arxiv.org/abs/2509.21051), EMNLP Findings 2025): GPT-4o prompt-level all-satisfied
**94% (n=1) → 57% (n=5) → 21% (n=10)** while per-instruction success stays ~85–90%; StyleMBPP 93% (n=1) →
68% (n=6); **Gemma2-2B reaches near-zero by n=10**; o3-mini-high holds 78% at n=10. Third axis —
**constraint difficulty**: MulDimIF ([2505.07591](https://arxiv.org/abs/2505.07591), v2 2026-04-15), 18 LLMs:
average accuracy **80.82% at Level I → 36.76% at Level IV**.

### At what size does "apply an arbitrary naming convention stated once" become reliable?
No paper answers this exactly. The convergent estimate from the numbers above:

- **1.7B: not reliable at all.** 44.2% on *one* coding-style constraint (2507.00699). Four independent
  conventions at that rate → 0.442⁴ ≈ **3.8%** strict, so **0/16 is the expected observation**, and the
  upper 95% bound at n=16 (17%) does not even exclude the predicted value. Nothing is broken.
- **4B: partially reliable.** +13 pp IFEval over 1.7B; still below the ~60% per-constraint rate that
  would make 4-way strict compliance routine.
- **8B–14B with a verifier loop: reliable enough to be useful.** IFEval 83–85; CodeIF/CIFE strict
  adherence for strong models is still only 39–66% ([2512.17387](https://arxiv.org/abs/2512.17387), Dec 2025), so even
  frontier models do not get multi-constraint strict compliance for free.
- **No size makes arbitrary, unseen constraints safe without verification:** Qwen2.5-72B 74.7 IFEval but
  **31.3** IFBench; Tülu-3-70B 81.1 → **25.5** (2507.02833).

### Why do small models verbalize but not apply?
Four independent, mutually consistent findings:

1. **Semantic priors dominate in-context/stated evidence below a scale threshold.** Overriding semantic
   priors is an *emergent ability of model scale*: small LMs ignore flipped labels and fall back on
   pretraining priors, while large models can override them; and instruction tuning **strengthens the use
   of semantic priors more than it strengthens learning new input-label mappings**
   ([2303.03846](https://arxiv.org/abs/2303.03846), Mar 2023). "Prefix every function with `gn_`" is a flipped label
   against a very strong Python prior. This is the best mechanistic account of your exact symptom.
2. **Counter-intuitive constraints fail at 10–100% vs 99%+ for conventional ones, independent of how they
   are phrased**, and models *self-report* compliance they did not achieve (2604.07192).
3. **An execution gap between trace/verbalization and output compliance** is directly measured: trace
   relevance is uncorrelated (Planning, r ≈ 0.02) or anti-correlated (Precision, r ≈ −0.05) with
   compliance; activation patching across 1.7B–14B restores Precision flips more often than Planning flips
   (32–58% vs 14–40% mean layer restoration) (2606.09662).
4. **Instruction-following was historically an emergent property.** Wei et al. found instruction tuning
   *hurt* fully-held-out tasks at 8B and below, with benefits emerging at 66B+ (reported in The Flan
   Collection, [2301.13688](https://arxiv.org/abs/2301.13688)); OPT-IML ([2212.12017](https://arxiv.org/abs/2212.12017)) did not
   reproduce the threshold, so treat this as directional. Also relevant: small models benefit
   disproportionately from *demonstrations* rather than *instructions*, with the gain coming from
   inference-time context rather than training (2212.01907 and follow-ups).

Knowing-doing gap framing, if you want the agentic literature: LLMs produce correct rationales
(~87%) and then take the non-optimal action (58% greedy vs 21% optimal), and RL fine-tuning on
self-generated rationales narrows it ([2504.16078](https://arxiv.org/abs/2504.16078), Apr 2025).

---

## Q5 — Cheap adaptation that keeps the control fair

### What works, with numbers
- **RLVR > SFT/DPO for generalization to unseen constraints. IFBench** ([2507.02833](https://arxiv.org/abs/2507.02833),
  v3 2025-11-11): 58 new out-of-domain verifiable constraints + 29 hand-annotated training constraints and
  verifier functions. Finding: **most models strongly overfit to the small IFEval constraint set and do
  not generalize.** IF-RLVR results: **Tülu-3-8B IFEval 82.4 → 92.2 (+9.8), IFBench 28.9 → 45.9 (+17.0)**;
  Qwen2.5-7B reaches IFEval 87.8 / IFBench 54.7. GRPO with verifiable IF rewards consistently beat DPO on
  the same data. This is the single most relevant result for "LoRA/RL on synthetic convention data, tested
  on held-out convention types."
- **VerIF** ([2506.09942](https://arxiv.org/abs/2506.09942), EMNLP 2025): rule-based code verification + reasoning-LLM
  verification, VerInstruct ≈ 22k instances; SOTA among comparable-size models, **generalizes to unseen
  constraints**, and general capabilities unaffected. Directly transferable recipe: your regex *is* the
  rule-based half.
- **AutoIF** ([2406.13542](https://arxiv.org/abs/2406.13542), ICLR 2025): LLM writes the instruction, the verification
  *code*, and unit tests for the code; execution-feedback rejection sampling → SFT/DPO. First method past
  **90% IFEval loose-instruction accuracy** without hurting general/math/code. Demonstrated on Qwen2 and
  LLaMA3 (7–8B+), including strong-to-weak distillation.
- **Conifer** ([2404.02823](https://arxiv.org/abs/2404.02823), Apr 2024): GPT-4-curated multi-level constrained
  instruction data + easy-to-hard progressive learning; the **7B model beats SOTA open 7B models on
  IFEval/FollowBench/InFoBench and exceeds some 10×-larger models on certain metrics.**
- **CRAB / constraint back-translation** ([2410.24175](https://arxiv.org/abs/2410.24175), v2 2025-04-29): instead of
  asking a model to *satisfy* hard constraints (which it does badly, so the data is noisy), take existing
  high-quality responses and have Llama3-70B *add the constraints the response already satisfies*. Cheaper,
  less noisy, and useful as an auxiliary training objective. For your case: mine real repos for code that
  already happens to follow a convention, then synthesize the instruction.
- **Multi-constraint training generalizes to out-of-domain compositions**: training on instructions with
  multiple constraints improves complex-instruction understanding and **generalizes to compositions of
  out-of-domain constraints** while maintaining general ability ([2404.15846](https://arxiv.org/abs/2404.15846),
  v2 2024-06-18).
- **Where the gain lives, mechanically**: MulDimIF reports that improvement from its generated data
  "stem[s] largely from parameter updates in attention modules, which strengthen constraint recognition
  and adherence" (2505.07591) — a useful convergence with the sibling report's attention-steering angle.

### Risks, with evidence
- **Constraint-type overfitting is the default outcome, not an edge case** (2507.02833). Mitigation is
  structural: hold out whole *convention families* (not instances), and report both splits.
- **Prefix tuning bought security at the price of functional correctness** on CodeGuard+
  ([2405.00218](https://arxiv.org/abs/2405.00218)) — the same trap awaits a LoRA tuned only on "apply the convention":
  you will need a correctness metric in the same harness or you will ship a model that renames everything
  and computes the wrong thing.
- **Reasoning-oriented RL can degrade obedience** (2505.14810); if you RL on conventions, watch IFEval/
  HumanEval as regression gates.
- **Honest gap:** I found **no** published LoRA/prefix-tuning result for "apply a stated naming convention"
  at 1.7B–4B on held-out convention types. Everything above is 7B+. Treat the IFBench/VerIF deltas as an
  upper bound for your scale, not a forecast.

### Fairness note
"Same model unmodified" is only a fair control for a *weights* intervention (LoRA merged, RLVR). For
constrained decoding, a repair loop, or prompt restructuring, the control must receive the identical
scaffold minus the one manipulated factor, or you are measuring the scaffold.

---

## Q6 — Evaluation design

### Is strict all-or-nothing standard?
**It is standard, and it is never reported alone.** Every major benchmark publishes a strict/hard metric
*and* a per-constraint metric:

| Benchmark | Strict metric | Partial-credit metric |
|---|---|---|
| IFEval ([2311.07911](https://arxiv.org/abs/2311.07911)) | prompt-level strict (all verifiable instructions in a prompt) | instruction-level strict; plus loose variants of both |
| FollowBench ([2310.20410](https://arxiv.org/abs/2310.20410), ACL 2024) | HSR (all constraints) | SSR (per-constraint), by difficulty level |
| SysBench ([2408.10943](https://arxiv.org/abs/2408.10943)) | ISR (all constraints of an instruction) | CSR (per-constraint); SSR for multi-turn stability |
| InFoBench ([2401.03601](https://arxiv.org/abs/2401.03601)) | — | **DRFR**: decompose the instruction into atomic requirements and score each |
| CodeIF ([2502.19166](https://arxiv.org/abs/2502.19166), ACL-Industry 2025) | CSR (completely satisfied) | SSR (avg fraction), RSR (prerequisite-aware), CCSR (longest satisfied run) |
| MultiCodeIF ([2507.00699](https://arxiv.org/abs/2507.00699)) | HSR | per-category accuracy; IFRepair@k across rounds |
| CIFE ([2512.17387](https://arxiv.org/abs/2512.17387)) | strict adherence | partial adherence; **C2A** = joint correctness+compliance |
| ManyIFEval/StyleMBPP ([2509.21051](https://arxiv.org/abs/2509.21051)) | all-instructions-satisfied | per-instruction accuracy |

**What papers do when small models floor.** Three moves, all applicable:
1. **Report the per-constraint rate as the primary number** and strict as secondary — this is what keeps
   Qwen3-1.7B legible (44.2% Coding Style, 44.8% average) where its strict score would be near zero
   (2507.00699). CodeIF's RSR (prerequisite-aware) and CCSR (longest consecutive satisfied run) are
   purpose-built partial-credit metrics for exactly this.
2. **Vary the number of constraints and fit a curve** rather than reporting one floored cell. 2509.21051
   fits a logistic regression on instruction count: **MAE 0.04 ± 0.03 (ManyIFEval), 0.06 ± 0.05
   (StyleMBPP), Pearson > 0.98**, and generalizes to unseen instruction counts (MAE 0.03 ± 0.04 predicting
   n=10 from n≤9). Notably, the naive independent-probability model (∏pᵢ) **underestimates** degradation,
   so do not justify a floor with p⁴ alone. **Recommended sample sizes from that paper: ~500 samples
   (50 task descriptions × instruction count) for ManyIFEval, ~300 for StyleMBPP**; beyond that,
   diminishing returns.
3. **Decompose to atomic, independently verifiable requirements** (DRFR, 2401.03601) so each item yields
   several binary outcomes instead of one.

### Floor effects and minimum detectable effect — concrete guidance for your 16+16 design
- **0/16 is statistically uninformative about small effects.** Exact one-sided 95% upper bound for 0/16 is
  1 − 0.05^(1/16) = **17.1%** (the "rule of three" approximation, 3/n, gives 18.8%). So your current
  negative result is consistent with any true compliance rate up to ~17%, and a paired design at n=16 can
  only detect improvements larger than that.
- **Treat the eval as a designed experiment.** "Adding Error Bars to Evals"
  ([2411.00640](https://arxiv.org/abs/2411.00640), Nov 2024) gives the formulas you want: conceptualize questions as
  drawn from a super-population, use **paired/clustered analysis for two-model comparisons** (variance of
  the difference, not of each arm), and plan n from the target MDE. Two of its recommendations matter here:
  pair on items (same task, same seed, same prompt skeleton), and cluster standard errors when multiple
  binary outcomes come from one generation.
- **Practical prescription for this project:**
  - Score **per convention per item** → 16 items × 4–8 conventions = 64–128 paired binary outcomes, with
    item-clustered bootstrap CIs. Primary metric: per-constraint satisfaction rate. Secondary: strict.
  - Use **McNemar's exact test** on the discordant pairs for the paired strict comparison; with a floored
    baseline, the discordant count *is* the evidence, and b=0, c=k reduces to a sign test — k ≥ 5
    one-sided discordant flips gives p ≤ 0.031.
  - **Escape the floor by construction**: run a 1-constraint condition and a 2-constraint condition
    alongside 4+. If the 1-constraint rate is ~44% (the literature's prior for 1.7B), you have a
    measurable baseline with real headroom; if the 4-constraint rate is 0, you learn nothing.
  - **Include an oracle ceiling and a mechanical floor**: (a) an oracle arm with the convention already
    applied in a one-shot exemplar, (b) a deterministic post-hoc renamer, which gets 100% by construction
    and bounds how much credit any model-side intervention can claim.
  - Power: to detect 44% → 60% per-constraint with 80% power at α=0.05 (paired, moderate correlation) you
    need on the order of 150–250 paired constraint-level observations — reachable with 40 items × 4
    conventions, not with 16 items × strict scoring.

---

## Would NOT work, and why

1. **Rewording the rules — compacting them, bulleting them, making them imperative, moving them around in
   the prompt.** Directly measured null: three encoding forms × four propagation modes, 11 models, 830+
   invocations, **Cliff's δ < 0.01, CI ±2.6 pp** (2604.07192). Your restated-1-2-sentences arm already
   tested the strongest version of this and got zero. Stop spending rounds here.
2. **Any intrinsic self-critique ("check your code against the rules") without running the regex.**
   Below ~3.8B, self-correction is net-negative (2410.23496); small LMs need strong external verifiers
   (2404.17140); and the model's self-assessment of compliance is systematically inflated relative to
   rule-based scoring (2604.07192). You would be asking the faulty component to be the judge.
3. **Turning thinking ON, or adding CoT/"plan then code", to get compliance.** Precision constraints are
   the class that thinking degrades (−8.5 pp at class level), Qwen3-1.7B loses 3.52 pp prompt-strict, and
   trace relevance to the constraint is *negatively* correlated with compliance for this class
   (2606.09662). MathIF shows the same tension at scale (2505.14810). Plan-then-code may help the
   *structural* conventions ("use the @timer decorator on every public function" is Planning-flavored) but
   will hurt the lexical ones.
4. **Grammar-constraining the whole function body to a hand-written naming grammar.** Incomplete
   constrainers lose up to **97% functional correctness** and induce timeouts by pushing the model into
   low-probability regions (2606.21619); JSON-mode-style blanket restriction cost 25–63 pp on reasoning
   tasks (2408.02442); constrained decoding hurt the 1.5B model most (2502.09061); masks can make whole
   behaviors unreachable (2606.25605). Constrain only the declaration spans, two-pass.
5. **Few-shot exemplars of the convention as the primary lever.** Examples alone gave modest initial
   effect and **no** persistence across a turn (2511.13972), and below the scale threshold models ignore
   in-context evidence that contradicts their priors (2303.03846) — which is the definition of `gn_`.
6. **Constrained decoding as a cure for a broken reflection loop.** Outlines-structured reflection on
   Qwen3-8B produced no self-correction gain and a new failure mode, "structure snowballing": perfect
   surface form, zero semantic error detection (2604.06066).
7. **Long unbounded repair loops.** Without early stopping, every iteration is net-negative at 1–3B
   (2604.21950); IaC loops plateau by round 5 and spawn new errors from old ones (2411.19043). One or two
   rounds, hard stop, keep the first compliant output.
8. **SFT or DPO on a handful of convention types, then claiming generality.** This is the documented
   overfitting mode — 70B-class models at IFEval 74–81 collapse to IFBench 25–31 on unseen constraints
   (2507.02833). If you train, train with verifiable rewards and hold out whole convention families.
9. **Prefix tuning as the cheap weight-side option.** It achieved its target property while sacrificing
   functional correctness, and was beaten by training-free constrained decoding (2405.00218).
10. **Reporting strict-only at n=16.** A 0/16 arm cannot exclude a true rate of 17%, so any "no effect"
    conclusion from that design is unsupported (rule of three; 2411.00640 for the planning framework).

---

## Sources

Constrained decoding: [2411.15100](https://arxiv.org/abs/2411.15100) · [MLC blog 2024-11-22](https://blog.mlc.ai/2024/11/22/achieving-efficient-flexible-portable-structured-generation-with-xgrammar) · [XGrammar docs](https://xgrammar.mlc.ai/docs/start/constrained_decoding.html) · [LMSYS compressed FSM](https://www.lmsys.org/blog/2024-02-05-compressed-fsm/) · [2405.21047](https://arxiv.org/abs/2405.21047) · [2502.09061](https://arxiv.org/abs/2502.09061) · [2408.02442](https://arxiv.org/abs/2408.02442) · [2504.09246](https://arxiv.org/abs/2504.09246) · [2508.15866](https://arxiv.org/abs/2508.15866) · [2405.00218](https://arxiv.org/abs/2405.00218) · [2401.09967](https://arxiv.org/abs/2401.09967) · [2606.21619](https://arxiv.org/abs/2606.21619) · [2606.25605](https://arxiv.org/abs/2606.25605) · [2604.14862](https://arxiv.org/abs/2604.14862) · [2605.10065](https://arxiv.org/abs/2605.10065) · [2604.06066](https://arxiv.org/abs/2604.06066)

Self-correction / feedback loops: [2310.01798](https://arxiv.org/abs/2310.01798) · [2404.17140](https://aclanthology.org/2024.findings-acl.924/) · [2410.23496](https://arxiv.org/abs/2410.23496) · [2604.21950](https://arxiv.org/abs/2604.21950) · [2403.18746](https://arxiv.org/abs/2403.18746) · [2411.19043](https://arxiv.org/abs/2411.19043) · [2410.03608](https://arxiv.org/abs/2410.03608) · [2510.14842](https://arxiv.org/abs/2510.14842)

Prompting: [2309.06275](https://arxiv.org/abs/2309.06275) · [2309.10687](https://arxiv.org/abs/2309.10687) · [2511.13972](https://arxiv.org/abs/2511.13972) · [2604.07192](https://arxiv.org/abs/2604.07192) · [2606.03624](https://arxiv.org/abs/2606.03624) · [2606.09662](https://arxiv.org/abs/2606.09662) · [2505.14810](https://arxiv.org/abs/2505.14810)

Scale & mechanism: [2505.09388](https://arxiv.org/abs/2505.09388) · [2303.03846](https://arxiv.org/abs/2303.03846) · [2212.01907](https://arxiv.org/abs/2212.01907) · [2301.13688](https://arxiv.org/abs/2301.13688) · [2212.12017](https://arxiv.org/abs/2212.12017) · [2504.16078](https://arxiv.org/abs/2504.16078)

Adaptation: [2507.02833](https://arxiv.org/abs/2507.02833) · [2506.09942](https://arxiv.org/abs/2506.09942) · [2406.13542](https://arxiv.org/abs/2406.13542) · [2404.02823](https://arxiv.org/abs/2404.02823) · [2410.24175](https://arxiv.org/abs/2410.24175) · [2404.15846](https://arxiv.org/abs/2404.15846) · [2505.07591](https://arxiv.org/abs/2505.07591)

Evaluation: [2311.07911](https://arxiv.org/abs/2311.07911) · [2310.20410](https://arxiv.org/abs/2310.20410) · [2401.03601](https://arxiv.org/abs/2401.03601) · [2408.10943](https://arxiv.org/abs/2408.10943) · [2502.19166](https://arxiv.org/abs/2502.19166) · [2503.22688](https://arxiv.org/abs/2503.22688) · [2507.00699](https://arxiv.org/abs/2507.00699) · [2512.17387](https://arxiv.org/abs/2512.17387) · [2509.21051](https://arxiv.org/abs/2509.21051) · [2407.03387](https://arxiv.org/abs/2407.03387) · [2411.00640](https://arxiv.org/abs/2411.00640)

**Verification note.** Numbers marked as verified (Qwen3 IFEval Tables 17–20; Qwen3-1.7B 62.48/58.96/−3.52;
Qwen2.5-1.5B 26/22/31; MultiCodeIF 44.2 / 44.8 / 63.0 / 83.4 / 54.5 / 18.8) were extracted by parsing the
papers' own HTML tables. Numbers from PDF-only sources and from WebFetch summaries of long HTML tables
(CodeIF CSR 0.153/0.104; ManyIFEval 94/57/21; IFBench 82.4→92.2 and 28.9→45.9; CRANE non-1.5B rows;
MultiCodeIF per-round repair curve) were read from a single extraction pass and should be re-checked
against the paper before being quoted in a registration.
