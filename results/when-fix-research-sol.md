OpenAI Codex v0.147.0
--------
workdir: /home/bmarti44/stencil-llm
model: gpt-5.6-sol
provider: openai
approval: never
sandbox: read-only
reasoning effort: medium
reasoning summaries: none
session id: 01a04889-69ae-7751-b3f2-de2e74e382e4
--------
user
DEEP RESEARCH: HOW TO FIX THE WHEN - MILLER-INSPIRED (Brian's directive; xhigh; use web search heavily and go DEEP into the neuroscience this time - your prior WHEN design doc (results/b3-when-design-sol.md) and research file are known; do NOT repeat them, build on the E0 EVIDENCE). E0 evidence to build on: the counterfactual features (kl_focus/js/obligation_shift) carried ~no held-out decision signal; the signal that DID exist lives in trajectory dynamics - margin COLLAPSE precedes a useful intervention (AUC 0.706, direction-flipped), attention-mass 0.706, entropy rise 0.683 - but nothing transfers across constraint families at n=27. RESEARCH MANDATE: (1) The Lundqvist/Miller burst literature specifically: in their working-memory data (gamma bursts at encoding and readout, beta as the default hold state), what TRIGGERS a gamma burst - what upstream signal or state predicts burst onset, in their computational models (Lundqvist et al. 2016/2018, Miller/Lundqvist/Bastos reviews, spiking network models)? Is burst timing content-cued, demand-cued (readout imminent), or intrinsically stochastic with task-modulated rate? Cite specifics. (2) Fries' communication-through-coherence and Bastos' predictive-routing: what determines WHEN a channel opens? Map each to autoregressive-transformer analogs honestly. (3) Conflict-monitoring computational models (Botvinick ACC, expected value of control by Shenhav): EVC is literally 'expected value of control' - our EVF was its analog and its cheap features failed; what do EVC models use as the CONFLICT signal, and is our margin-collapse finding (low margin_delta5 -> repair) exactly their prediction? If so, the fix may be conflict-TRAJECTORY features with better labels, not new mechanisms. (4) ML analogs discovered since your last pass: entropy/uncertainty-triggered intervention papers, learned halting/ACT-style controllers, metacognition probes in LLMs (models predicting their own upcoming failure - cite the strongest ones), speculative-decoding-style verify-then-commit as a WHEN mechanism. (5) SYNTHESIS: given E0's specific failure (weak counterfactual features, transferable-ish conflict dynamics, tiny n), the corrections review you just completed, and Miller's actual timing story - what is the single most promising REGISTERED-QUALITY next design for the WHEN gate, and what offline evidence (computable from our recorded data or cheap new synthetic paired runs) would justify it BEFORE any training? Be blunt about whether the Miller-faithful path and the empirically-promising path are the same path or diverging.
codex
I’ll treat E0’s margin-collapse result as the datum to explain, not restart the earlier EVF survey. I’m going to trace burst onset from the original Lundqvist/Miller recordings and their spiking models, then compare coherence/predictive-routing and conflict-control models at the level of their actual triggering variables. The synthesis will end in one preregistrable design with a pre-training evidence gate.
exec
/bin/bash -lc "sed -n '1,360p' results/b3-when-design-sol.md 2>/dev/null || true; sed -n '1,420p' results/research-wave-generation.md; sed -n '1,320p' EVF-PLAN.md; tail -n 120 WORKLOG.md" in /home/bmarti44/stencil-llm
 succeeded in 0ms:
OpenAI Codex v0.147.0
--------
workdir: /home/bmarti44/stencil-llm
model: gpt-5.6-sol
provider: openai
approval: never
sandbox: read-only
reasoning effort: medium
reasoning summaries: none
session id: 01a04889-69ae-7751-b3f2-de2e74e382e4
--------
user
DESIGN QUESTION FROM BRIAN (xhigh, web search enabled — use academic sources deeply): HOW DO WE ACCURATELY DETERMINE WHEN TO APPLY FOCUS — Miller-faithful, and fully AUTOMATIC (no human intervention, no oracle labels at inference, no task-specific wiring)? Context you know: the WHEN problem is now isolated as THE bottleneck (amplitude solved: 2x force = 0 extra repairs; WHERE solved: K-perm kills the benefit; the psi<tau attention trigger makes 12 bad calls per 15 good — a symptom-based trigger, not a diagnosis; oracle WHEN ceiling +7.5 vs +1.5 harvested). Brian's framing: 'the problem is not how much focus, the problem is WHEN to focus.' Your task, three parts: (1) MILLER-FAITHFUL MECHANISMS: go back to the neuroscience — in Miller's framework (beta/gamma interplay, top-down beta carrying task rules gating bottom-up gamma; working-memory reactivation timing), what precisely determines WHEN a rule is re-asserted? Map each candidate neural timing mechanism to an implementable analog on a frozen transformer with a tiny controller: e.g. conflict/error signals (ACC analog: rising next-token entropy or divergence between the model's committed trajectory and the rule's demands), phase-like periodic refresh (is there any defensible analog of oscillatory duty cycles in autoregressive steps?), content-addressable reactivation (the rule reasserts when the current state RESEMBLES contexts where the rule was learned to matter). Which is most faithful AND most implementable? (2) AUTOMATIC WHEN-SIGNALS available at inference with zero human input, ranked by expected precision: decoder entropy/margin trajectories; KL between the model's next-token distribution and a rule-conditioned counterfactual (two-forward probe); the model's own uncertainty about the governing instruction (readout head on h20 — we already proved focus is linearly readable, W2 100% non-NULL accuracy); verifier-free obligation-state estimation (a tiny recurrent state tracking which obligations look satisfied from the generated text so far — learnable from our verified data with per-obligation labels we can compute offline); attention-mass trends (the failed one — why exactly does it underperform, and does its failure predict which alternatives will work?). For each: what would the gate's precision/recall on our 15-repair/12-regression anatomy plausibly be, what does the literature say (cite), and what is the cheapest decisive pilot on our existing recorded data (we have every response, per-item, both arms, plus minimal-violation mutation pairs)? (3) THE SYNTHESIS: propose ONE concrete Miller-faithful automatic WHEN architecture for the wave (controller stays tiny, trunk frozen, deterministic verification culture) with a registered-quality spec sketch: inputs, training labels (computable offline from our data — no human annotation), firing rule, safe-dose interval requirement, and the pilot that would falsify it fastest. Be blunt about what is genuinely automatic vs what smuggles in an oracle.
codex
I’ll separate biological fidelity from engineering usefulness. The key test is whether a signal predicts the *counterfactual value of intervention*—repair versus regression—not merely correlates with low attention or uncertainty. I’m tracing Miller’s actual control loop first, then I’ll map inference-time signals onto the recorded 15/12 discordant anatomy and design one falsifiable gate.
web search: 
web search: Earl Miller beta gamma working memory top down beta task rules gamma bursts reactivation review primary paper ...
web search: 
web search: anterior cingulate cortex conflict monitoring error likelihood cognitive control Botvinick primary paper PMC ...
web search: 
web search: language model uncertainty entropy margin predicts errors selective generation primary paper semantic entropy Nature 2024 ...
web search: 
web search: language model intervention gate counterfactual KL divergence conditioned unconditioned instruction adherence decoding primary paper ...
web search: 
web search: 'readout'
web search: 
web search: working memory retrocue reactivation gamma beta prioritized item primary study Miller lab ...
web search: 
web search: site:aclanthology.org obligation tracking generated text constraints satisfied recurrent state neural decoder ...
web search: 
web search: Miller Cohen 2001 integrative theory prefrontal cortex cognitive control task rules guided activation pdf ...
codex
## Bottom line

The most Miller-faithful automatic answer is not “focus whenever attention is low” and not “refresh every \(N\) tokens.” It is:

> Reactivate a rule when the current processing state predicts that the rule is relevant, insufficiently expressed, and that a short reactivation has positive expected value.

In implementation terms, this means a tiny learned **Expected Value of Focus** gate combining:

1. content-addressed relevance: which stored rule matches the current processing state;
2. obligation state: is that rule still pending, threatened, or nearing its last safe execution point;
3. a counterfactual probe: does a weak focused forward change the trajectory in a direction predicted to help;
4. intervention cost: how much does it disturb the model’s native distribution?

That is closer to Miller’s control account than any single observable such as entropy, attention mass, or a clock.

## 1. What actually determines WHEN in Miller’s framework

### The neuroscience does not contain a periodic refresh clock

Miller and Cohen’s foundational account says that PFC representations of goals and task rules provide bias signals that guide processing along currently relevant pathways. Context and internal state activate the appropriate “rulemap”; the rule representation then biases competition elsewhere. [Miller & Cohen, 2001](https://www.annualreviews.org/content/journals/10.1146/annurev.neuro.24.1.167), [Miller’s rulemap account](https://pmc.ncbi.nlm.nih.gov/articles/PMC3898679/)

The later beta/gamma account adds temporal structure:

- Deep-layer alpha/beta carries top-down and inhibitory control.
- Superficial gamma is associated with expression, encoding, or readout of working-memory content.
- Beta protects or suppresses; gamma bursts briefly express selected content.
- When content is about to be needed, beta falls and content-specific gamma/spiking rises.
- When it is no longer needed, beta rises and gamma/content expression falls. [Working Memory 2.0](https://pmc.ncbi.nlm.nih.gov/articles/PMC8112390/)

Critically, the bursts are not a metronome. Single-trial gamma bursts were irregular; apparent slow periodicity emerged after averaging. [Gamma and beta bursts underlie working memory](https://pmc.ncbi.nlm.nih.gov/articles/PMC5220584/)

The strongest empirical answer to WHEN is therefore **anticipation of use**. In Miller’s sequence task, the relevant object’s gamma and informative spiking increased before the expected test object, with reduced beta; this occurred only before relevant tests. [Gamma and beta bursts during working-memory readout](https://pubmed.ncbi.nlm.nih.gov/29374153/)

So the biologically defensible mapping is:

| Neural idea | Transformer analog | Verdict |
|---|---|---|
| Learned context predicts impending need | Current hidden state retrieves a rule-use prototype | Most Miller-faithful |
| ACC-like conflict or expected control value | Predict intervention utility from native/focused counterfactuals | Best automatic firing decision |
| Beta hold / gamma burst | Default no-focus state plus short, gated focus burst | Faithful actuator schedule |
| Periodic replay | Refractory/eligibility schedule, never the decision itself | Supporting mechanism only |
| Low attention mass | “Rule is visually quiet” | Symptom, not diagnosis |

### Conflict monitoring complements Miller

The ACC conflict-monitoring account proposes that incompatible response tendencies signal a need for more top-down control. The Expected Value of Control formulation goes further: choose the identity and intensity of control by predicted benefit minus its cost. [Conflict monitoring and cognitive control](https://pubmed.ncbi.nlm.nih.gov/11488380/), [Expected Value of Control](https://pmc.ncbi.nlm.nih.gov/articles/PMC3767969/)

That is almost exactly your measured problem:

\[
\operatorname{EVF}(s,r)=
\mathbb{E}[\text{utility with focus}-\text{utility without focus}\mid s,r]
-\operatorname{cost}(\text{focus}).
\]

The current `ψ<τ` trigger estimates neither term. It estimates only whether a span received little native attention.

### Content-addressable reactivation is the best biological/engineering bridge

In the rulemap account, external and internal context cues complete the relevant rule representation. Activity-silent working-memory research likewise finds that latent contents can be reactivated by appropriate cues or “pings.” [Activity-silent working memory review](https://pmc.ncbi.nlm.nih.gov/articles/PMC10158524/)

For Stencil:

- Each rule/memory has a learned key \(k_m\).
- Current `h20` produces a query \(q_t\).
- Similarity retrieves the likely relevant rule.
- A separate utility gate decides whether retrieving it into active processing is worth doing now.

This separates WHERE from WHEN correctly. Similarity selects the candidate; it must not itself authorize intervention. The PRESS program already demonstrated why: lookalike contexts can retrieve the right type without establishing that the rule is live.

### Where an oscillator still fits

An oscillator could provide:

- a refractory period after a burst;
- time-division multiplexing among several memories;
- an eligibility window for probing dormant rules;
- a weak “do not let this rule go unexamined forever” prior.

It should not directly command a press. Fixed token-period refresh is less Miller-faithful than a predictive gate and would replay the same false-positive problem periodically.

## 2. Automatic inference-time signals

First, precision and recall cannot be identified completely from the 15/12 anatomy. Among outcome-changing calls, the present gate’s conditional positive predictive value is:

\[
15/(15+12)=55.6\%.
\]

That omits all fired-but-no-effect calls, so the true per-fire precision is lower. Recall is unknown because we do not know how many helpful opportunities the policy failed to activate.

For any proposed gate, let:

- \(r_+\): fraction of the 15 helpful interventions retained;
- \(r_-\): fraction of the 12 harmful interventions retained.

Then:

\[
\mathrm{PPV}=\frac{15r_+}{15r_+ + 12r_-},\qquad
\mathrm{net}=15r_+-12r_-.
\]

The present net is \(+3\). A useful pilot target is approximately \(r_+\ge .60,\ r_-\le .25\): nine repairs, three regressions, PPV 75%, net \(+6\).

The ranges below are design priors, not measured claims.

### 1. Obligation-state estimate plus counterfactual utility

Expected performance: highest precision; target 75–85% PPV at 55–75% recall.

Maintain a learned state per selected rule:

- inactive/not applicable;
- pending;
- partially satisfied;
- satisfied;
- threatened or nearly impossible;
- remaining response-budget fraction.

The tracker consumes the natural-language rule representation, `h20`, and the generated prefix. It does not call a verifier at inference.

This attacks the actual distinction between your repairs and regressions. A keyword rule that has already been satisfied does not need focus even if prompt attention is low. A required placeholder still absent near the response boundary does.

Mention Flags established the basic idea of updating per-constraint states as generation proceeds, although its mechanism uses explicit lexical matching and is narrower than the required learned tracker. [Mention Flags](https://aclanthology.org/2021.acl-long.9/) NeuroLogic similarly tracks partially satisfied logical constraints, but as an explicit decoding algorithm. [NeuroLogic](https://aclanthology.org/2021.naacl-main.339/)

Cheap pilot:

1. Use your checkers to produce per-prefix pending/satisfied labels offline.
2. Include canonical, base, wave, and minimal-violation prefixes.
3. Train a 64–128-dimensional GRU using rule text plus prefix `h20`.
4. Hold out whole constraint families, not rows.
5. Evaluate whether its pending/urgency score separates the 15 repairs from 12 regressions.

If it cannot generalize state across held-out families, it is a learned IFEval checker, not a general focus controller.

### 2. Signed rule-conditioned counterfactual

Expected performance:

- KL alone: high recall, only roughly 55–65% PPV.
- KL plus predicted progress: plausible 70–85% PPV.

At a candidate moment compute:

- \(P_0\): ordinary next-token distribution;
- \(P_1\): weak, safe-dose focused distribution.

Then measure:

- symmetric KL or Jensen–Shannon divergence;
- top-\(k\) overlap;
- change in probability assigned to tracker-predicted progress;
- native-distribution cost;
- whether the focused distribution sharpens or destabilizes.

The important correction is that **large KL is not a reason to focus**. It says the actuator has leverage. The 15 repairs and 12 regressions are both likely high-leverage events. The gate needs a signed value estimate:

\[
\widehat{\Delta U}_t
=
\widehat V(P_1,s_t,r)-\widehat V(P_0,s_t,r)
-\lambda D_{\mathrm{JS}}(P_1,P_0).
\]

This is an inference-time intervention experiment, not an oracle: both forwards are produced automatically by the same frozen model. The oracle enters only if an inference-time checker or future ground truth is consulted.

Cheap pilot:

- Teacher-force the stored base prefixes through normal and weak-focus forwards.
- Cache \(P_0,P_1\) at the first divergence and obligation-sensitive positions.
- Test KL alone, signed tracker progress, and their combination against helpful/harmful labels.
- Use leave-topic and leave-constraint-family-out folds.

If KL is equally high on repairs and regressions, that is expected. If the signed tracker delta also cannot separate them, kill the architecture.

### 3. Uncertainty of the governing-rule readout

Expected on B3: potentially high precision when it fires, but probably under 30% recall.

You already proved the focused rule is linearly readable with 100% non-NULL accuracy. That makes a readout-margin gate attractive but also predicts a likely null result here: the model generally knows which rule exists. The problem is applying it at the right generative moment.

Useful features are:

- margin between the selected rule and runner-up;
- entropy over rule identities;
- change in margin over recent tokens;
- inconsistency between current readout and the recurrent rule state.

This should become much more useful on Multi-IF or compaction streams, where the governing rule may genuinely fade or compete with stale rules.

CAST shows that hidden-state patterns can condition whether activation steering is applied, although its prompt-category refusal task is much easier than token-level obligation timing. [Conditional Activation Steering](https://arxiv.org/abs/2409.05907)

Cheap pilot: replay stored prefixes, record W2 logits by token, and compare pre-divergence margin trajectories for repairs versus regressions. If both remain confidently correct, rule-readout uncertainty cannot solve B3 and should be retained only for long-horizon use.

### 4. Decoder entropy and margin trajectories

Expected: 50–60% PPV and 40–70% recall alone.

Raw entropy is task-general and free. It is also nonspecific:

- Fluent wording choices can have high entropy but pose no rule risk.
- A model can confidently omit a keyword.
- Entropy rises at punctuation, enumeration, and ordinary branch points.
- Low top-1 margin indicates competing tokens, not necessarily conflict with a rule.

Use temporal surprise rather than absolute entropy:

\[
z_t = \frac{H_t-\operatorname{median}(H_{t-w:t-1})}
{\operatorname{MAD}(H_{t-w:t-1})+\epsilon}.
\]

Also useful:

- top-1/top-2 margin collapse;
- entropy acceleration;
- disagreement among a few deterministic perturbed forwards;
- entropy localized to tracker-predicted obligation boundaries.

Semantic entropy can detect some confabulations and support selective abstention, but it targets uncertainty over answer meaning rather than instruction compliance. [Semantic entropy](https://www.nature.com/articles/s41586-024-07421-0)

More relevant is Attribution-Guided Decoding: its adaptive variant uses entropy to decide when guidance is warranted and reports Llama-3.1 instruction success improving from 66.0% to 79.1%. But entropy is used as a coarse economizer around a rule-specific attribution mechanism, not as a complete diagnosis. [Attribution-Guided Decoding](https://proceedings.iclr.cc/paper_files/paper/2026/hash/da30215ee52c1daaaaddada8137cfd0b-Abstract-Conference.html)

Cheap pilot: teacher-force every stored response, extract entropy/margin windows before the first helpful or harmful divergence, and fit only a three-feature logistic baseline. This is the baseline every richer gate must beat.

### 5. Attention-mass level or trend

Measured conditional PPV: 55.6% among outcome-changing calls; true per-fire PPV lower.

It failed because attention mass answers the wrong question:

> “How much is this head currently reading this span?”

The desired question is:

> “Would forcing this head to read the span improve expected task utility now?”

Low mass has many benign explanations:

- the head is irrelevant to instruction transport;
- the rule has already been integrated into the residual stream;
- a different layer/head read it earlier;
- the obligation is satisfied;
- the current token needs local response context;
- the rule matters later, not now.

A falling trend may be marginally better than a fixed threshold, but it remains unsigned. Worse, your dose experiment shows that more intervention creates no additional repairs: the limitation is not failure to detect sufficiently low attention.

What its failure predicts: raw entropy, readout uncertainty, or context similarity will also fail if treated as sufficient conditions. Each is a symptom. A successful gate must estimate **counterfactual benefit** or at least combine relevance with pending obligation state.

## 3. One concrete architecture

I recommend a **Predictive Reactivation / Expected Value of Focus gate**.

### State

For each autonomously identified rule span \(m\):

- `key_m`: existing learned address key;
- `rule_m`: pooled rule representation;
- `z_m ∈ R^128`: recurrent obligation/progress state;
- `age_m`: tokens since last reactivation;
- `burst_m`: current burst/refractory state.

No type ID, checker state, or generator metadata is available at inference.

### Inputs per generation step

Cheap path, every token:

- current `h20`;
- decoder entropy, top-1 margin, and their recent deltas;
- learned rule-readout logits and margin;
- selected rule key similarity;
- natural attention-mass summaries, retained only as features;
- per-rule recurrent state;
- normalized response length and remaining model budget.

The controller updates:

\[
z_{m,t}=\operatorname{GRU}(z_{m,t-1},
[h^{20}_t,\operatorname{rule}_m,\operatorname{embed}(y_t)]).
\]

It predicts:

- \(p_{\text{pending}}\);
- \(p_{\text{relevant-now}}\);
- \(p_{\text{already-satisfied}}\);
- urgency/last-safe-opportunity;
- probability that a focus burst will help or harm.

### Two-stage firing

Stage 1: cheap eligibility screen.

Probe only when:

\[
p_{\text{pending}}\,
p_{\text{relevant-now}}\,
p_{\text{need}}
>\theta_{\text{probe}}.
\]

Stage 2: automatic counterfactual.

Compute the weak focused forward \(P_1\), compare with native \(P_0\), and estimate:

\[
\widehat{\mathrm{EVF}} =
p_{\text{pending}}
\left[
\widehat V(P_1,z_m)-\widehat V(P_0,z_m)
\right]
-\lambda D_{\mathrm{JS}}(P_1,P_0)
-c_{\text{compute}}.
\]

Fire only if a calibrated lower confidence bound on EVF is positive. If it fires, use the already-computed \(P_1\); otherwise use \(P_0\).

A burst lasts one token by default and can continue for a small registered maximum—say four tokens—only while EVF remains positive. Then enter a short refractory state. This gives irregular, task-cued bursts rather than continuous attention pressure.

### Neural mapping

- Stored rule and recurrent state: activity-silent/task-rule representation.
# Research: making the wave controller help on open-ended generation
Date: 2026-08-31. Scope: web/arXiv survey for the wave-controller program (frozen Qwen3-1.7B trunk, 264k-param pre-softmax attention bias in layers 20-27, instruction-span pointing). Our empirical facts taken as given: +18.5 pts when the pointed-at info is out of attention's reach; -4.6 pts (best recipe) on IFEval-style free generation; root causes (a) teacher-forced CE rewards imitation, (b) always-on bias starves attention over the model's own recent output, (c) no static gain dose beats base.

## Headline finding

The literature does NOT support the strong scope hypothesis ("attention steering can only help when information is out of reach"). It supports a sharper claim: **static, always-on attention biases fail on instruction following for models that already read the prompt, while closed-loop, deficit-triggered biases show positive IFEval deltas at 3B-72B scale.** SpotLight (arXiv 2505.12025) is the existence proof, and its authors' diagnosis of static methods is word-for-word ours: static biases "ignore the model's natural attention distributions and potentially break generation by over-steering when the attention is already adequate." Our root causes (b) and (c) are a rediscovery of this; the published fix is a per-step feedback law, not a better static dose.

---

## Q2. Attention steering at inference (answered first — it carries the headline)

### PASTA — arXiv 2311.02262 (ICLR'24)
- Method: post-hoc reweighting at a profiled subset of attention heads; upweight user-marked spans, downweight the rest. Static (constant strength for the whole generation), inference-only.
- Measured: synthetic instruction tasks (Pronouns Changing, JSON Formatting), context-conflict/bias tasks. GPT-J-6B: 39.9% -> ~93% compliance on Pronouns Changing (+53 pts); LLaMA-7B JSON formatting 96.6% format / 85.1% prediction accuracy.
- Scale/conditions: base (non-instruction-tuned or weakly tuned) 6-7B models, tasks where the base model largely ignores the instruction — i.e., huge headroom. Requires per-model head profiling (~1000 examples).
- Mapping to us: this is the regime where our wave already wins. PASTA's wins are on models/tasks with instruction-reading deficits; it is not evidence a static bias helps a competent instruction-tuned model. Consistent with our -4.6.

### SpotLight — "Spotlight Your Instructions: Instruction-following with Dynamic Attention Steering", arXiv 2505.12025 — THE key paper
- Method: per-decoding-step, per-query-position feedback. Compute the post-softmax attention proportion on the highlighted spans, psi_current(i) = sum_{j in S} A_ij / sum_k A_ik. If psi_current < psi_target, add pre-softmax bias B_ij = log(psi_target / psi_current(i)) on span keys; otherwise bias = 0. Applied across all layers/heads (no profiling). Bias vanishes exactly when attention is already adequate — so the model's attention over its own recent output is untouched whenever it is doing fine.
- Measured, instruction-tuned models 3B-72B (Qwen2.5-3B/7B/72B, Llama-3.1-8B/70B, Granite-3.1-8B, Mistral-7B):
  - IFEval (prompt/instr-level): Qwen-3B 0.42/0.53 -> 0.53/0.62 (PASTA: 0.42/0.55); Qwen-7B 0.47/0.59 -> 0.54/0.66; Llama-8B 0.42/0.55 -> 0.51/0.62. So +7 to +11 pts prompt-level on IFEval, on models that already read the prompt, where PASTA gives +0 to +3.
  - ManyIFEval (many simultaneous instructions): >30% prompt-level accuracy improvement.
  - HotpotQA: +10% vs base, +6% vs PASTA (EM/F1). WildJailbreak refusal +6-10%.
- Failure mode acknowledged: at high target strengths, relevance degrades ("over-focus").
- Mapping to us: direct. Our controller is a learned static-dose version of what SpotLight does with a closed-loop rule. The delta between PASTA-on-IFEval (~0) and SpotLight-on-IFEval (+7..+11) is the measured value of conditionality. Strong candidate: keep our learned span-pointer and gain geometry, but multiply it by a per-step deficit term (or replace amplitude with the log-ratio law) so the bias is zero whenever attention on the spans already meets target. This addresses (b) and (c) without retraining the trunk.

### InstABoost — "Instruction Following by Principled Boosting Attention", arXiv 2506.13734
- Constant additive pre-softmax bias B on instruction tokens, all layers/heads (exponential multiplicative boost e^B on those keys). Llama-3-8B-Instruct, Gemma-7B-it, 15 steering tasks (persona, emotion, jailbreak-resistance, truthfulness, QA). Matches/outperforms latent-steering baselines, avoids fluency collapse; but documents an "instruction over-focus" failure where boosting suppresses benign competing rules — a constant bias again pays a tax. No IFEval numbers.
- Mapping: corroborates that a well-placed constant pre-softmax bias is viable for categorical behaviors but degrades when the task needs balanced attention — same tension we hit.

### AutoPASTA — "Model Tells Itself Where to Attend", arXiv 2409.10790
- Model self-identifies key context sentences, then PASTA-style steering on them. +7.95% avg for Llama-3-70B-Instruct on open-book QA (faithfulness/grounding). Not IFEval; the target is context the model under-uses — again the "out of reach / under-attended" regime.

### Selective Prompt Anchoring (SPA) — arXiv 2408.09121 (ICML'25)
- Documents attention dilution: models pay progressively less attention to the user prompt as more tokens are generated, and links this to errors. Fix: logit-level anchoring (contrast logits with and without prompt masked, scale the difference) — the whole prompt, applied through decoding. Pass@1 up to +12.9% across 6 code LLMs / 6 benchmarks.
- Mapping: evidence that prompt-attention decay during generation is a real, exploitable failure — but SPA acts on logits, not attention, so it cannot starve self-attention over recent output the way our bias does. Also note their anchoring strength is small and tuned; large strengths hurt.

### Conditions where steering helps vs hurts (synthesis for Q2)
- Helps: instruction-reading deficit (weak/base models — PASTA), attention dilution over long generations (SPA), under-attended context (AutoPASTA), many simultaneous constraints (SpotLight/ManyIFEval), positional degradation (found-in-the-middle).
- Hurts/neutral: static bias on competent instruction-tuned models at ordinary prompt lengths (PASTA's ~0 on IFEval; our -4.6; InstABoost over-focus; broad activation-steering literature: "Analysing the Safety Pitfalls of Steering Vectors" arXiv 2603.24543, "Forecasting Side Effects of Activation Steering" arXiv 2608.11227, "Minimizing Collateral Damage in Activation Steering" arXiv 2605.01167 all report collateral capability loss from unconditional interventions).

---

## Q1. Training objectives that make steering help open-ended generation

### RLVR / GRPO with constraint checkers as reward (mature at 1-8B; applied to full models, not yet to tiny controllers)
- "Generalizing Verifiable Instruction Following" — arXiv 2507.02833 (IFBench). GRPO with per-constraint verifier functions as outcome reward; IFEval categories saturate (>90%) under IF-RLVR; gains concentrate on deterministic format/length/punctuation constraints, limited on semantic ones. Trains 7-8B policies.
- VerIF — arXiv 2506.09942. Rule-based code verification + LLM verification (QwQ-32B) as reward; VerInstruct (~22k instances); SOTA IF at comparable size, general capabilities "unaffected."
- IFDecorator — arXiv 2508.04632. Wraps IF-RLVR with difficulty curriculum + intent checks to prevent reward hacking of verifiers.
- MDP-GRPO — arXiv 2606.06058. Stabilizes GRPO for multi-constraint IF (per-constraint credit).
- Mapping: the reward machinery is exactly our deterministic-verification culture (we already own machine checkers). Nothing published trains a 264k-param attention controller with GRPO on a frozen trunk — the nearest neighbors are below — so this is open ground, and cheap: the policy has 264k params, rollouts are the cost.

### On-policy / RL-trained lightweight controllers over frozen trunks
- Guiding Giants (WAS) — arXiv 2505.20309. Trainable lightweight controller reads intermediate activations, emits a global scale + per-layer weights modulating a precomputed steering vector, per-token at inference. Trained discriminatively (harmful vs benign), not RL, but it is the published "stateful gain schedule for a frozen LLM" blueprint. Llama/Mistral, safety benchmarks (ToxicChat refusal up significantly).
- VSPO — arXiv 2605.15604. Uses steering vectors at varying intensities to generate on-policy rollouts feeding GRPO — steering as an exploration device for RLVR.
- Policy Gradient Steering — arXiv 2607.27574. Formulates steering itself as RL: accumulate policy gradients of a behavioral objective over a few rollouts into a removable task vector.
- EAST — arXiv 2406.00244. Entropy-weighted steering vector to control an agent's action-entropy — precedent for uncertainty-coupled intervention strength.
- Mapping: combine WAS's architecture (controller reads decoding-time hidden state, outputs time-varying gain) with IF-RLVR's reward (our checkers). GRPO over rollouts scores the controller, not the trunk. This attacks root cause (a) head-on: reward constraint execution, not imitation of canonical responses.

### Contrast pairs with machine-verified minimal violations — yes, there is literature
- MuSC — arXiv 2502.11541 (ACL'25). Builds negatives by constraint mutation (Constraint-Dropout / Constraint-Negate / Constraint-Substitute) and — crucially — does token-aware preference optimization: dynamic token-level supervision concentrating the preference gradient on the tokens where the pair differs. Self-generated pairs, no GPT-4 teacher. Significant gains on complex + general IF benchmarks at 7-8B.
- "From Complex to Simple" — arXiv 2404.15846. DPO triplets where negatives fail specified constraints; shows the discrimination signal from constraint-failing negatives is what teaches multi-constraint following.
- Automatic Pair Construction for Contrastive Post-training — arXiv 2310.02263 (NAACL'24 Findings). Curriculum from easy to hard contrast pairs.
- Mapping: our machine-verified minimal violation mutations are a strictly better version of MuSC's negatives (ours are verified-minimal). The published recipe to exploit them is token-level DPO/preference loss on the controller only — the gradient localizes on exactly the violating tokens, which teacher-forced CE cannot do. This is the highest-leverage supervised objective available to us short of RL.

### KL-preserving / side-effect-bounded steering objectives
- "Steering Without Side Effects" — arXiv 2406.15518 (KL-budgeted post-deployment control; steer only flagged cases).
- Minimizing Collateral Damage in Activation Steering — arXiv 2605.01167; Forecasting Side Effects — arXiv 2608.11227. Frame: constrain KL(steered || base) off-target while maximizing on-target effect.
- Mapping: cheap addition to any of the above — add a KL(wave || base) penalty on tokens where the verifier says base is already compliant. With attenuating gain converging to base from below, an explicit off-target KL anchor is likely necessary for any static component to be net-nonnegative.

### Scheduled sampling for controllers
- No paper trains an attention-steering controller with scheduled sampling specifically. The general exposure-bias literature (Bengio et al. 2015; Confidence-Aware Scheduled Sampling, arXiv 2107.10427) transfers: our root cause (a) is textbook exposure bias — the controller never sees its own downstream consequences under teacher forcing. The field's actual cure at LM scale has been on-policy RL (above), not scheduled sampling; recommend going straight to rollouts.

---

## Q3. State-conditional / adaptive gating — the stateful version exists in pieces

- SpotLight (2505.12025): state = current attention distribution; fire only on deficit. Simplest, proven on IFEval. (See Q2.)
- CAST — "Programming Refusal with Conditional Activation Steering", arXiv 2409.05907 (ICLR'25, IBM). Condition vectors gate behavior vectors by hidden-state similarity: "if condition then steer." Prompt-conditional rather than decoding-state-conditional, but the gating machinery (project hidden state onto a learned condition direction, threshold) is reusable per-step.
- Guiding Giants WAS (2505.20309): learned controller network reads activations during generation, emits time-varying, layer-resolved gain. The closest published artifact to "our wave with a brain."
- EAST (2406.00244): entropy of the action distribution as the state variable driving steering.
- FLARE — arXiv 2305.06983: intervene (retrieve) only when next-sentence token confidence is low — the canonical "intervene when about to fail" decoding loop.
- Entropy-informed decoding — arXiv 2605.09745: entropy + entropy-variance triggers for inserting interventions at high-uncertainty points.
- Steering Vector Fields — arXiv 2602.01654: replaces a global static vector with a context-dependent field refreshed from evolving hidden states; explicitly stronger on long-form generation, and documents that vanilla static vectors lose effectiveness as context grows.
- Nobody has published: a learned gate that tracks unmet obligations (pending placeholders, counts, case constraints) and fires span-pointing only for the still-unsatisfied constraint. The ingredients (verifiable per-constraint state + conditional gating) all exist separately; the combination is open.

## Q4. The scope hypothesis — supported in weak form, refuted in strong form

Supporting evidence (steering wins where attention is degraded/insufficient):
- Found-in-the-Middle — arXiv 2406.16008 (ACL'24 Findings): attention calibration against U-shaped positional bias; up to +15 pts on long-context RAG/retrieval tasks. Gains exist precisely because attention mis-allocates.
- Focus Directions — arXiv 2503.23306: KQ-space directions at "contextual heads" fix long-context task misalignment.
- "Don't Lose Focus" — arXiv 2605.06342: steering's harm concentrates in attention rerouting; key-orthogonal projection preserves NIAH performance — i.e., naive steering hurts exactly when sparse high attention on important distant tokens must be preserved. (Mechanistically kin to our root cause (b).)
- PASTA's gains living on weak models/synthetic tasks; AutoPASTA's on under-used context; SPA's on diluted prompt attention over long code generations; our own +18.5 out-of-reach result.
- Multi-turn decay: Multi-IF (arXiv 2410.15553) — accuracy drops monotonically with turns (o1-preview 88% -> 71% by turn 3, "instruction forgetting"); "Measuring and Controlling Instruction (In)stability" — arXiv 2402.10962: system-prompt drift within 8 rounds in LLaMA2-70B-chat/GPT-3.5, attributed to attention decay, mitigated by split-softmax (an attention-budget intervention on the system prompt — mechanistically our wave's cousin, and it helps there); MMMT-IF — arXiv 2409.18216 (instructions dispersed across long dialogues); "When Attention Closes" — arXiv 2605.12922.
- Steering Vector Fields (2602.01654): static vectors work <2K tokens, degrade with context — dose-response of staticness with context length.

Refuting the strong form: SpotLight's +7..+11 IFEval prompt-level on instruction-tuned 3B-70B models shows in-reach instruction following IS improvable by attention steering — provided the intervention is closed-loop. So: scope determines how much headroom exists; the control law determines whether you can collect it without paying the always-on tax. Our data (-4.6 with the best static recipe; convergence to base from below as gain attenuates) is exactly what this literature predicts for a stateless spotlight, and is not evidence the mechanism is scope-limited.

## Q5. Neuroscience-inspired oscillation/top-down models — candid: no LM-benchmark wins yet

- Neural Wave Machines — Keller & Welling, ICML 2023 (PMLR v202): locally coupled oscillatory RNNs with traveling waves; wins on synthetic sequence tasks, not LMs.
- Traveling Waves Encode the Recent Past — arXiv 2309.08045: wave-based RNNs solve longer sequence tasks, learn faster — again synthetic memory tasks.
- Traveling Waves Integrate Spatial Information — arXiv 2502.06034; spacetime perspective — arXiv 2409.13669. Same story.
- Gated Attention for LLMs — arXiv 2505.06708 (NeurIPS'25, Qwen team; 1.7B dense & 15B MoE, 3.5T tokens): head-specific sigmoid gate after SDPA improves quality, stability, and removes attention sinks. Not oscillatory and requires pretraining, but it is the strongest evidence that a learned multiplicative gate on attention output is beneficial at exactly our trunk's scale (Qwen 1.7B) — supports "gate, don't bias, and make it input-dependent."
- Verdict: Miller-flavored oscillation-gated selection has no published empirical win on real LM benchmarks. Our program is ahead of that literature, not behind it; cite it as inspiration, not evidence.

---

## Ranked shortlist — three concrete next steps

1. **Close the loop: deficit-triggered wave (SpotLight-ize the controller).** Keep the learned span pointer and layer placement; replace the static gain with per-step conditional amplitude: measure post-softmax attention mass on the pointed spans at each query position, fire only when below a target, with strength log(psi_target/psi_current) or controller-predicted. Bias is exactly zero when attention is adequate — root causes (b) and (c) die by construction. SpotLight's IFEval numbers (+7..+11 prompt-level, 3B-8B instruction-tuned) are the preregisterable prior that this recipe has positive expected delta on the exact benchmark where we now lose. Cheapest experiment: pure inference-time change, our existing harness verifies it deterministically. (arXiv 2505.12025; corroboration 2506.13734, 2408.09121.)

2. **Retrain the controller on-policy with our verifiers as reward, plus token-level contrast on our minimal-violation mutations.** Two-stage: (i) token-aware preference optimization (MuSC-style, arXiv 2502.11541; 2404.15846) on our machine-verified minimal violation pairs — gradient localizes on violating tokens, killing the imitation bias of teacher-forced CE (root cause a); (ii) GRPO on rollouts with per-constraint checker rewards (IF-RLVR recipe: 2507.02833, 2506.09942, 2508.04632), policy = 264k controller only, trunk frozen — unpublished combination, cheap at our scale, and our deterministic-verification culture is precisely the reward infrastructure this literature assumes. Add an off-target KL(wave || base) anchor on already-compliant tokens (2406.15518, 2605.01167).

3. **Preregister the scope-graded battery where the mechanism should win even in static form, with turn/length/distractor load as the registered moderator.** Predicted ordering of wave delta: Multi-IF later turns (arXiv 2410.15553; frontier models drop 17 pts by turn 3) > ManyIFEval high-constraint-count cells (SpotLight got +30% there) > MMMT-IF dispersed instructions (2409.18216) > system-prompt-stability self-chats (2402.10962 protocol) > long-context IF / NIAH-with-constraints (found-in-the-middle regime, 2406.16008) >> single-turn IFEval (expected ~0 or negative for static wave). A monotone delta-vs-load curve crossing zero is a publishable confirmation of the weak scope hypothesis and defines the wave's deployment envelope; pairing it with step 1 tests whether closed-loop control flattens the curve's negative end to >= 0.

## Secondary citations index
PASTA 2311.02262 | SpotLight 2505.12025 | InstABoost 2506.13734 | AutoPASTA 2409.10790 | SPA 2408.09121 | Found-in-the-Middle 2406.16008 | Focus Directions 2503.23306 | Don't Lose Focus 2605.06342 | Steering Vector Fields 2602.01654 | CAST 2409.05907 | Guiding Giants WAS 2505.20309 | EAST 2406.00244 | FLARE 2305.06983 | Entropy-informed decoding 2605.09745 | IF-RLVR/IFBench 2507.02833 | VerIF 2506.09942 | IFDecorator 2508.04632 | MDP-GRPO 2606.06058 | MuSC 2502.11541 | From Complex to Simple 2404.15846 | Pair construction 2310.02263 | Steering w/o Side Effects 2406.15518 | Collateral damage 2605.01167 | Side-effect forecasting 2608.11227 | Safety pitfalls 2603.24543 | Multi-IF 2410.15553 | MMMT-IF 2409.18216 | Instruction (in)stability / split-softmax 2402.10962 | When Attention Closes 2605.12922 | VSPO 2605.15604 | Policy Gradient Steering 2607.27574 | Gated Attention 2505.06708 | Neural Wave Machines (Keller & Welling, ICML'23) | Traveling waves 2309.08045, 2502.06034.

Caveats: Multi-IF id (2410.15553) cited from memory plus a search snippet reporting the 88->71 o1-preview turn decay — verify id before preregistering. Several 26xx-series ids are 2026 preprints not yet peer-reviewed. SpotLight numbers transcribed from the paper's HTML (prompt-level/instr-level pairs); re-verify Table values before quoting in a registered document.
# EVF — Predictive Reactivation / Expected Value of Focus (the WHEN program)

Authorized by Brian 2026-08-31 ("kill what is currently running and run
this new program instead — red/green TDD, deterministic proof it's
implemented correctly"), superseding the v4.5 confirmation mid-run (its
partial records are retained untouched under results/qwen/
b3-deficit-conf-s0/; the seed-0 sealed attempt is recorded ABANDONED-
BY-RULING, not failed). Design: sol xhigh spec, results/
b3-when-design-sol.md. BENCH-WAVE-PLAN.md machinery (data freezes,
verifier vendoring, stats) is inherited; the single-turn stop-loss is
superseded by this authorization.

## The isolated bottleneck (established)

Amplitude solved (2x force = 0 extra repairs). WHERE solved (K-perm
kills the benefit). WHEN is open: the psi<tau attention trigger makes
12 bad calls per 15 good; oracle WHEN ceiling +7.5pts vs +1.5 harvested.

## Phase E0 — the decisive pilot probe (kill-fast; THIS phase only is
authorized to run before its gate reports)

Data: the recorded calibration discordants (t30-b3 vs base, 15 repairs
+ 12 regressions) + concordant controls, from
results/qwen/b3-deficit-cal/ per-item records. No new generation on any
frozen evaluation stream; teacher-forced feature passes only.

Per discordant row:
1. Find the FIRST divergence token between the base and wave responses
   (shared prefix p; the WHEN decision that mattered happened there).
2. Teacher-force prompt+shared-prefix through the trunk once; cache at
   the divergence point (and at 2 matched control points in concordant
   rows): h20; decoder entropy, top-1 margin and their deltas over the
   last 5 tokens; the frozen wave's rule-readout features (per-span q/k
   scores: max, margin between top-2 spans); natural attention-mass
   summary on the governing span (layers 20-27 mean).
3. One additional weak-focus forward (the selected t30-b3 field scaled
   to b=1.0 on the governing span) at the same prefix; cache
   KL(P1||P0), JS divergence, and the obligation-token probability
   shift (mean delta log-prob of the row's obligation-span tokens).
4. Labels: repair=1, regression=0 (verifier-derived, offline).

Probe: L2-regularized logistic regression (deterministic solver, fixed
seed), leave-one-topic-out AND leave-one-constraint-family-out folds.

GATE E0 (registered): held-out repair recall r+ >= 0.60 with
regression fire-rate r- <= 0.25 on the 15/12 anatomy, in BOTH fold
schemes. KILL immediately if: focused-vs-native divergence features are
indistinguishable between repairs and regressions AND obligation/
readout features add no held-out discrimination; or performance
disappears under family holdout; or the probe works only via constraint
type or response position.

## Phase E1 (only if E0 passes; separate go)

Recurrent obligation tracker (GRU 128/rule) + two-stage firing
(eligibility screen -> one-token counterfactual -> calibrated
lower-confidence-bound EVF > 0), bursts <= 4 tokens + refractory;
labels from offline verifier-scored counterfactual rollouts; safe-dose
interval requirement (a BROAD non-harmful tau/threshold plateau, not
one winning scalar) and behavioral gates per sol's spec sections
(offline discrimination, safe-dose, behavioral) — registered in full
before any E1 training run.

## Process

Red/green TDD throughout: every component gets a failing test first;
deterministic proof = bitwise-identical feature extraction across two
runs, fixed-seed probe fits, and fixture-exact tests for divergence
finding and label derivation. Reviews: sol + fable on the E0 result
before any E1 work. Playbook governs (per-item records from the first
row of anything evaluative; git add -f for results; smoke before
sealing).

## E0 verdict + REGISTERED post-Multi-IF decision rule (sol post-mortem,
registered BEFORE Multi-IF results are seen; 2026-08-31)

E0: KILLED per its registered criterion (fable: all numbers bitwise-
verified, zero findings). Post-mortem (results/e0-corrections-sol.md):
the question was causally blurred (policy-divergence labels, not
moment-level treatment effects), plus family-grouping and omitted-
controls flaws. NEVER: E0-with-more-rows; further tuning on the 27;
E1 as originally specced.

DECISION RULE for the running Multi-IF (base / deficit-wave /
static25), registered now:
1. static25 helps late turns, deficit-wave does not -> actuator has
   multi-turn value, WHEN is the blocker: launch the causal-moment
   protocol (frozen moment, branch A=0/A=1 single burst, deterministic
   rollout to verifier endpoint, ITE labels helpful/harmful/neutral;
   identical replayed base histories; session/topic + changed-family
   splits; the FIXED three-feature conflict probe (margin_delta5,
   attn_mass_span, entropy_delta5) is the pre-registered primary
   mechanistic endpoint).
2. deficit-wave helps -> do NOT build EVF; replicate + characterize
   the simple gate in its arena first.
3. neither helps but an oracle chooser over recorded arm outputs shows
   substantial late-turn lift -> timing headroom exists; run the
   causal-moment branches next (policy-level oracle is only a screen).
4. neither helps and the oracle has negligible lift -> do not fund a
   larger WHEN learner; establish moment-level actuator headroom first.
Caveat registered: each arm consumes its own history, so late-turn arm
differences are NOT clean local treatment effects; any training
anatomy must replay identical base histories before branching.
  first-keyword + numeric-control positions; most CE is filler/fixed-template/
  response-local. Prescription: obligation VALUES must vary per row and derive
  from the prompt; canonicals should be frozen-Qwen greedy outputs minimally
  edited for compliance; EOS supervision; obligation-token weighting.
- v4.3 DESIGN (both curators + fable's causal analysis):
  1. Base texts = frozen Qwen greedy responses to 40 topics x 3 task phrasings
     (120 texts), minimally EDITED per row for compliance; edit spans recorded
     as obligation spans in the dataset.
  2. Obligation values randomized per row and SPECIFIED in the prompt
     (exact title text, postscript phrase, placeholder names).
  3. Mutations rebuilt minimal+targeted (single-constraint violations).
  4. Trainer: EOS in targets; obligation-span CE upweighting.
  5. Topic split 30 train / 10 dev-only (true generalization holdout).
  6. beta_max 1.0 at retrain (fable).

## 2026-08-31 — v4.4 pilot: gate FAIL again (base 0.8418, wave-s0 0.7959)

- The full rework (curated natural data, obligation-weighted CE + EOS,
  beta_max 1.0) cut the harm from -11.0pts to -4.6pts — direction right,
  outcome still a FAIL vs the registered base+2 gate. Dev task CE 1.50
  (vs 4.46 old recipe): the objective now concentrates where the prompt
  matters, yet free-generation adherence still degrades.
- Dose sweep on the retrained wave running (x0.5, x0.25). If NO dose beats
  base+2, both the amplitude story and the objective story are closed for
  this recipe family, and the program-level question goes to the reviewers
  and Brian: the emerging scope hypothesis is that the wave mechanism helps
  when focus-critical information is PROVABLY OUT OF REACH (W3 sealed win:
  +18.5pts with the ledger chunk-deleted) and is parity-to-harmful when the
  base model can already read the prompt (all B3 gates, both B2 probes).
  That is a coherent boundary for the theory, not a failure of the toy-scale
  results — but it bounds the IFEval claim as registered.

## 2026-08-31 — dose sweep: the wave HELPS at low dose (+1.5pts above base)

- v4.4 wave-s0 on dev-v43: gain x1.0 -> 0.7959, x0.5 -> 0.8214, x0.25 ->
  0.8571 vs base 0.8418. NON-MONOTONE: quarter-dose BEATS base by +1.5pts
  (gate needs +2.0). First positive generation-time delta of the program.
- Academic research (results/research-wave-generation.md): the strong scope
  hypothesis is REFUTED — SpotLight (2505.12025) reports positive IFEval
  deltas at 3-8B via DEFICIT-TRIGGERED steering (bias only when per-step
  attention to instruction spans is deficient; zero otherwise); its published
  critique of static bias predicts our x1.0 result. Contrast-pair training
  literature exists for our mutation pairs (MuSC 2502.11541); GRPO-with-
  checker-reward mature at this scale; obligation-state gating unpublished
  (open ground). Ranked: (1) deficit-triggered wave, (2) token-aware contrast
  + GRPO on the 264k controller, (3) scope-graded battery registration.

## 2026-08-31 — sol results review: sweep legit-but-unauditable; data EXHAUSTED; deficit-trigger registered as the LAST rescue

- A (accuracy): x1.0 arm fully audited (165/196 base, 156/196 wave, 6 fixes/15
  regressions). x0.5/x0.25 numbers plausible but NOT auditable — I ran the
  sweep without per-row records (the playbook rule violated a third time;
  lesson: EVERY evaluative run writes records, exploratory or not). n=196
  cannot distinguish +1.5 from +2.0 (best-case paired p=0.125); the gate miss
  is exactly one item. Post-hoc scaling = legitimate exploration, NOT a gate
  result (registered operating point was beta 1.0; x0.25 chosen after seeing
  this dev set; seed 0 only).
- B (data): EXHAUSTED — registered ruling: no v4.5 data curation. Residual
  label note (12.8% weighted-token fraction; 1.6% pathological rows) documented
  for any future objective reuse; cannot explain a one-item miss.
- C (path): REGISTER deficit-triggered steering (SpotLight-adapted): frozen
  v4.4 Wq/Wk select the governing constraint span; per step/layer/head compute
  post-softmax mass psi on it; zero bias if psi >= tau; else uniform span bias
  min(b_max, logit(tau) - logit(psi)) (exact odds correction — sol corrected
  the research note's log-ratio). Deterministic battery: zero-deficit ->
  BITWISE base logits; forced deficit -> finite nonzero; uncapped post-bias
  mass == tau; full intervention logging. tau from a frozen grid on a NEW
  calibration stream; ONE confirmation on >= 512 fresh prompt-disjoint rows;
  gate +2.0pts AND one-sided exact McNemar p < 0.05; seed-1 replication before
  sealed IFEval. STOP-LOSS: iteration 3 is the LAST single-turn rescue — no
  recalibration after confirmation; failure CLOSES the line; contrast/GRPO
  would need Brian's separate authorization.

## 2026-08-31 — fable verification: numbers ACCURATE, +1.5 NOT significant; v4.5 launched

- Fable reproduced x0.25 BIT-FOR-BIT (168/196 = 0.857143, fresh code path);
  base/wave-s0 rescored 0-mismatch; training record + shas verified; no
  contamination. STATISTICS: 7-vs-4 discordants -> McNemar p=0.549, delta CI
  [-1.8, +4.8]pt; ~1900 paired rows to confirm ANY positive effect. The honest
  statement: quarter-dose is indistinguishable from base AND from the gate at
  n=196. FINDING-1 fixed: v4.4 checkpoint was working-tree-only, now committed.
  FINDING-2 stands: x0.5 sweep number is WORKLOG-prose-only (descriptive).
- Confirmation stream extended 512 -> 1024 PRE-RUN on the power analysis
  (registered in the manifest note). Deficit-gate mechanism committed with
  4/4 battery (bitwise-base at zero deficit; exact odds correction verified
  numerically). Calibration chain launched: v4.4 seed-1 training then the
  one-shot tau x b_max grid on cal-v45.

## 2026-08-31 — Brian's ruling: Multi-IF is the decisive experiment; "go from there" on its data

- sol xhigh eval+research (results/b3-eval-research-sol.md): confirmation pass
  odds ~32%; scalar deficit thresholds condemned (15 repairs / 12 regressions,
  amplitude not the missing ingredient; oracle WHEN-chooser ceiling +7.5);
  untried families mapped (retrieval branch, obligation tracker, causal WHEN
  labels); constrained decoding named the honest single-turn ceiling; MMMT-IF
  +22.3pt from re-appending dispersed instructions = published proof the
  multi-turn failure is FOCUS/RETRIEVAL — the wave's arena.
- ORDER: sealed confirmation completes as registered (stop-loss honored either
  way), then Multi-IF three arms (base / deficit-wave user-turn spans /
  static-x0.25) regardless of outcome. Next program decisions wait for
  Multi-IF data (Brian).

## 2026-08-31 — BRIAN'S RULING: v4.5 confirmation killed mid-run; EVF program authorized

- Confirmation seed-0 stopped at Brian's direction (~100/1024 base records
  retained untouched; recorded ABANDONED-BY-RULING). EVF-PLAN.md committed:
  Phase E0 = kill-fast pilot probe on the recorded 15/12 calibration anatomy
  (registered gate r+>=0.60 / r-<=0.25 under topic AND family holdout);
  E1 (GRU tracker + two-stage EVF firing) gated on E0 + separate go.
  Red/green TDD + deterministic proofs required throughout.

## 2026-08-31 — EVF E0 pilot: registered gate FAIL (family-holdout kill criterion triggered)

- 15/12 anatomy, 11 registered features, deterministic probe. Topic folds:
  r+ 0.733 / r- 0.417 (needs <=0.25). Family folds: r+ 0.733 / r- 0.667 —
  near-indiscriminate under family holdout -> the registered kill criterion
  fires. Per-item features committed (results/qwen/e0-pilot.json).
- Honest caveats for the review: n=27 is tiny for 11 features; the gate was
  registered knowing this. The pre-registered sol+fable review of the E0
  result convenes before ANY next step.

web search: 
web search: Lundqvist 2016 gamma and beta bursts underlie working memory Neuron PMC burst timing model attractor stochastic task events ...
web search: 
web search: Lundqvist Herman Lansner 2011 working memory attractor dynamics gamma bursts synaptic facilitation noise replay trigger full text ...
web search: 
web search: Fries communication through coherence 2005 2015 gamma phase effective connectivity attention channel opens primary paper PMC ...
web search: 
web search: Botvinick 2001 conflict monitoring computational model conflict measure product response unit activations energy equation ...
web search: 
web search: site:aclanthology.org LLM hidden states predict own errors before generating answer metacognition probe ...
web search: 
web search: Kadavath language models mostly know what they know 2022 calibration PMLR ...
web search: 
web search: Graves Adaptive Computation Time recurrent neural networks 2016 arxiv halting probability ponder cost ...
web search: 
web search: speculative decoding verify candidate tokens target model acceptance exact distribution Leviathan 2023 ICML PMLR ...
web search: 
web search: 
web search: 
web search: "Theta and Gamma Power Increases" "background noise" attractor network model full text ...
codex
## Bottom line

The neuroscience does not support “an oscillator decides when to focus.” In the Lundqvist/Miller work, oscillation is primarily the implementation of transient access, not the upstream decision variable.

The best reading is:

> Keep memories latent by default; emit a brief content-specific burst when current processing predicts imminent, behaviorally relevant readout.

E0’s best signal—margin collapse plus entropy rise while the governing span is already receiving attention—is strikingly compatible with conflict monitoring and predictive routing. It suggests a better gate:

> Press when the model is actively consulting the right rule but its output trajectory is entering competition—not when attention to the rule is merely low.

That is different from the failed deficit trigger. I recommend a tiny conflict-hazard gate trained on exact single-burst causal labels, optionally using an uncommitted four-token native lookahead. Do not revive the KL-based EVF gate, and do not build a periodic oscillator.

## 1. What triggers bursts in the Lundqvist/Miller account?

There are three distinct answers, depending on task epoch.

### Encoding: external input pushes an assembly into an attractor

In the Lundqvist attractor model, stimulus input makes one memory assembly slightly more excitable than competing assemblies. Fast recurrent excitation and inhibition produce a short gamma attractor state; synaptic augmentation records a latent trace. Gamma is therefore triggered by a content-bearing external cue plus the assembly’s competitive excitability. [Lundqvist et al., 2016](https://pmc.ncbi.nlm.nih.gov/articles/PMC5220584/)

The transformer analog is straightforward:

- new instruction tokens activate a memory representation;
- their hidden-state/key representation is stored;
- no continuing press is necessary.

This is the part your focus cache already solved.

### Delay: stochastic reactivation from latent excitability

During maintenance, the model does not contain a learned “this memory is needed now” classifier. Previously activated assemblies retain elevated effective connectivity through short-term synaptic augmentation. Background excitation or noise can push one over threshold; lateral competition makes it win; inhibition, synaptic depression, and fatigue terminate it. Other assemblies then become eligible.

Consequently:

- reactivations are irregular on individual trials;
- increased memory load raises burst rate, not burst duration;
- slow periodicity appears much cleaner after trial averaging than within a trial;
- latent synaptic state determines which content is easiest to reactivate, while noise helps determine exact onset.

The 2011 model implements cyclic reactivation of up to six items through synaptic augmentation, with each reactivation accompanied by gamma and the noncoding state associated with alpha/beta. [Lundqvist, Herman & Lansner, 2011](https://direct.mit.edu/jocn/article/23/10/3008/5308/Theta-and-Gamma-Power-Increases-and-Alpha-Beta) Related activity-silent models explicitly show that a nonspecific readout pulse or background noise can reactivate the facilitated assembly. [Mongillo, Barak & Tsodyks](https://barak.net.technion.ac.il/files/2012/11/synapticmemory.pdf)

This is the source of the “oscillator per memory” intuition—but it is not a precise WHEN solution. It is a probabilistic refresh mechanism.

A literal transformer implementation would periodically or stochastically sample stored memories. That could help retention, but it would replay PRESS’s false-positive problem. It does not know whether pressing improves the current token.

### Readout: behaviorally relevant demand modulates burst rate

The 2018 experiment is the decisive one. Gamma bursting and informative spiking ramped before memories were needed for comparison to forthcoming test objects. Critically:

- equally predictable sample presentations did not produce the ramp;
- the ramp represented the particular memory needed for the next decision;
- after an early non-match made the second comparison irrelevant, the second-memory ramp disappeared and beta increased;
- erroneous behavioral plans were preceded by corresponding abnormal gamma/beta dynamics.

Therefore, gamma ramping was not a generic clock and not mere event anticipation. It tracked imminent, behaviorally relevant readout. The authors infer volitional/task-demand control, but they do not identify a single upstream neuron or scalar that triggers each burst. [Lundqvist et al., 2018](https://pmc.ncbi.nlm.nih.gov/articles/PMC5785952/)

The strongest honest summary is:

| Epoch | Burst trigger |
|---|---|
| Encoding | Content-bearing sensory input |
| Delay refresh | Latent assembly excitability plus background drive/noise |
| Purposeful readout | Task state predicting imminent behavioral use |
| Burst termination | Feedback inhibition, fatigue, depression |
| Content selection | Most excitable/relevant facilitated assembly wins |

For Stencil, the relevant part is purposeful readout, not stochastic refresh.

## 2. Fries and Bastos: what opens a channel?

### Communication-through-coherence does not provide the upstream selector

In Fries’ CTC account, a channel becomes effective when a presynaptic population’s gamma rhythm arrives during the receiving population’s excitable phase. The winning input entrains the receiver; the resulting inhibition shuts out competitors. Attention can increase the relevant population’s gamma strength or frequency, giving it an entrainment advantage. [Fries, 2015](https://pmc.ncbi.nlm.nih.gov/articles/PMC4605134/)

But CTC largely assumes that a top-down attentional system has selected the representation. It explains how that selection becomes effective connectivity. It does not fully explain why attention selected it at that moment.

Transformer mapping:

- selected prompt span = presynaptic representation;
- current generation state = receiver;
- attention-logit bias = increased effective coupling;
- competing prompt/local-response inputs = rival channels.

There is no meaningful literal gamma phase in an autoregressive token index. Tokens are task events, not biological milliseconds. Adding sine waves would be decorative unless phase carries an independently useful state.

CTC validates the actuator shape—brief, selective coupling—but does not solve Stencil’s WHEN classifier.

### Predictive routing supplies a better trigger: stimulus-specific mismatch

Bastos’ predictive-routing results sharpen the timing story:

- predictable stimuli increase deep-layer alpha/beta and feedback;
- predicted pathways are selectively inhibited;
- unexpected stimuli escape that pathway-specific inhibition;
- superficial gamma, spiking, and feedforward communication increase for the prediction error;
- the strongest effect occurs after transitions from predictable to unpredictable stimuli.

Thus a channel opens when incoming processing violates a content-specific prediction, not simply because its baseline attention is low. [Bastos et al., 2020](https://pmc.ncbi.nlm.nih.gov/articles/PMC7733827/)

Transformer analog:

1. The instruction/rule supplies a top-down prediction about the acceptable trajectory.
2. The native decoder begins committing to a continuation.
3. Conflict between the native continuation and task-conditioned trajectory rises.
4. The governing rule channel receives a brief gain increase.

E0’s raw `KL(P_focus || P_native)` failed because it measured how much the actuator could move the distribution. That is leverage, not prediction error and not signed utility. Both repairs and regressions can have large KL.

Margin collapse is closer to predictive error: incompatible continuations are becoming simultaneously competitive.

## 3. Is E0’s margin collapse what Botvinick predicts?

Approximately yes—more directly than the original EVF features.

Botvinick’s conflict monitor measures simultaneous activation of incompatible response units. Formally it used Hopfield energy:

\[
C=-\sum_{i,j} a_i a_j w_{ij}.
\]

For two mutually inhibitory responses with equal negative weights, conflict is proportional to \(a_1a_2\). It is low when one response dominates and high when both are active. [Botvinick et al., 2001](https://www.krigolsonteaching.com/uploads/4/3/8/4/43848243/botvinik_2001.pdf)

If the top two decoder alternatives contain most probability mass:

- falling top-1/top-2 margin implies greater coactivation;
- entropy rise implies a broader competing response set;
- their temporal derivatives indicate conflict is developing now.

So the direction-flipped E0 result—lower `margin_delta5` predicts repair—is exactly the qualitative prediction of response-conflict monitoring.

There are two important caveats.

First, token alternatives are not necessarily incompatible task responses. `"however"` versus `"but"` is not meaningful conflict. A better task-conditioned conflict signal would distinguish:

- native/local continuation pressure;
- rule-consistent continuation pressure;
- competing obligations.

Second, conflict only says “more control may be needed.” It does not say that this particular press, span, or dose will help. Shenhav’s EVC model evaluates:

\[
EVC(s,c)=
\sum_o P(o\mid s,c)V(o)-Cost(c),
\]

using state, predicted outcomes, control identity, and intensity. Conflict is one monitoring input among errors, delay, negative feedback, and other signals. [Shenhav, Botvinick & Cohen, 2013](https://pmc.ncbi.nlm.nih.gov/articles/PMC3767969/)

Therefore E0 did not refute EVC. It showed that:

- raw one-step distribution displacement is not a good EVC estimator;
- the first-divergence label was causally blurred;
- low-dimensional response-conflict dynamics may be a better eligibility signal.

### The attention-mass direction matters

E0’s positive attention-mass AUC is particularly interesting. Taken literally, repairs were more likely when the model was already reading the selected rule span—not when it had ignored it.

That suggests this two-factor condition:

\[
\text{rule engaged} \quad\land\quad \text{response conflict rising}.
\]

Mechanistically:

- high/rising rule attention says the current step is rule-relevant;
- margin collapse says the rule-conditioned and default trajectories are competing;
- a small burst may tip an already active competition;
- low rule attention may mean the rule is irrelevant now, so forcing it displaces needed response-local context.

This is nearly the opposite of `attention_mass < tau`.

The evidence is only 27 cases, so this remains a hypothesis. But it is the most coherent hypothesis E0 produced.

## 4. ML analogs

### Entropy-triggered intervention: promising pattern, noisy sensor

Several recent systems use changes in uncertainty, rather than absolute uncertainty, to trigger extra computation or context repair.

ERGO monitors abrupt next-token entropy increases and triggers prompt consolidation in multi-turn tasks, reporting a 56.6% average improvement over its baselines. It is a 2025 workshop result and its intervention is much more explicit than Stencil’s, so treat the effect size cautiously. [ERGO](https://arxiv.org/abs/2510.14077)

The broader lesson is credible: temporal uncertainty changes can be more actionable than a global threshold. But entropy remains nonspecific. The gate needs content engagement or task relevance alongside it.

### Learned halting shows how to train the router, not what its signal should be

Adaptive Computation Time learns a halting probability through task loss plus a cost for additional computation. It allocates more recurrent steps around hard-to-predict boundaries. [Graves, 2016](https://arxiv.org/abs/1603.08983)

CALM similarly adapts transformer depth per generation step using confidence measures and reports up to roughly 3× compute reduction while controlling quality degradation. Its authors explicitly identify the hard part: translating sequence-level quality requirements into local token decisions. [CALM](https://arxiv.org/abs/2207.07061)

Mixture-of-Depths demonstrates that learned token-level routers can allocate transformer compute dynamically under a fixed budget. [Raposo et al., 2024](https://arxiv.org/abs/2404.02258)

These support a tiny learned gate, but none solves your label problem. Training a halting/gain head on final adherence without exact moment attribution would recreate E0’s causal blur.

### Hidden-state probes can predict failure—but diagnosis and repair are different

The strongest relevant findings are:

- Kadavath et al. found models can predict whether they know an answer and partially generalize across tasks, but calibration degrades on new tasks. [Language Models Mostly Know What They Know](https://arxiv.org/abs/2207.05221)
- A large 2024 probing study reported 84.3% average pre-generation hallucination-risk accuracy across many datasets. [Ji et al.](https://arxiv.org/abs/2407.03282)
- A narrow prompt-leakage study found pre-generation hidden-state probes above 90% AUROC across its tested models and held-out attacks. [Dong et al., EMNLP 2025](https://aclanthology.org/2025.emnlp-main.1082/)
- A particularly relevant 2026 study found hidden-state probes could detect whether question-asking was needed, but interventions remained about as likely to harm correct trajectories as repair incorrect ones. [What Am I Missing?](https://arxiv.org/abs/2605.31561)

That final detection/recovery gap is E0’s lesson in another form. Predicting “this trajectory looks risky” is easier than predicting “this actuator will improve it.”

### Speculative verify-then-commit is useful, but its guarantee does not transfer automatically

Standard speculative decoding drafts several tokens and lets the target model accept or reject them while preserving the target distribution exactly. [Leviathan et al., ICML 2023](https://proceedings.mlr.press/v202/leviathan23a.html)

A Stencil analog would be:

1. Generate 2–4 native tokens into a scratch KV cache.
2. Observe the native margin/entropy/attention trajectory.
3. If it remains safe, commit the draft.
4. If conflict rises, discard the scratch suffix and regenerate it with a short focus burst.

Advantages:

- it turns coincident conflict into a prospective signal;
- it avoids externally committing the first bad token;
- it directly tests whether conflict is transient or worsening;
- it resembles “readout imminent” better than a single current-token snapshot.

But it is not lossless speculative decoding. Its verifier predicts task utility, not equality to the original distribution. It must be described as transactional lookahead with a learned gate. It costs extra forwards and still needs causal labels.

## 5. Recommended design: Conflict-Triggered Readout Bursts

This is the single most promising successor.

### Policy shape

Default state is hold/no intervention—the beta-like state.

At each generation step:

1. Existing frozen Wq/Wk selects the candidate rule span.
2. Collect a fixed trajectory feature vector:

\[
x_t=[
\Delta_5 C_t,\;
\Delta_5 H_t,\;
-\Delta_5 M_t,\;
A_t,\;
\Delta_5 A_t,\;
R_t
]
\]

where:

- \(C_t=\sum_{i<j}^{k}p_i p_j\): top-\(k\) conflict energy;
- \(H_t\): decoder entropy;
- \(M_t=p_{(1)}-p_{(2)}\): top-two margin;
- \(A_t\): natural attention mass on the selected span;
- \(R_t\): Wq/Wk address stability/margin.

3. A tiny temporal gate—a logistic hazard model first, not a GRU—estimates the benefit of one burst.
4. If hazard exceeds a calibrated threshold, optionally native-draft four tokens into scratch state and re-evaluate the trajectory.
5. If confirmed, discard the draft and apply one fixed safe-dose burst for at most four tokens.
6. Enter a fixed refractory interval.
7. Otherwise commit the native token(s).

No oscillatory phase is needed. The refractory interval captures the useful part of burst scheduling without pretending autoregressive positions are gamma cycles.

### Why this attacks E0’s measured failure

It replaces:

- low attention → press

with:

- selected rule is engaged;
- response competition is growing;
- the conflict trajectory predicts that a local burst has positive causal value.

It drops KL/JS and canonical `obligation_shift` from the firing inputs. Those may remain diagnostics, but E0 says they should not drive the gate.

### Training labels

At a fixed native prefix, produce two deterministic branches:

- `A=0`: no burst;
- `A=1`: exactly one registered burst to the frozen selected span, then identical ordinary decoding.

Continue to a verifier-resolvable endpoint and compute:

\[
\Delta U=U(A=1)-U(A=0).
\]

Labels:

- helpful: \(\Delta U>0\);
- harmful: \(\Delta U<0\);
- neutral: \(\Delta U=0\).

Use the actual changed verifier family, not `combo[0]`. Keep neutral opportunities because they determine deployment firing rate and cost.

The verifier is allowed only to construct offline labels. At inference the gate sees model-internal dynamics and text-derived span keys only. The honest claim would be “automatically deployed, verifier-supervised during training,” not unsupervised control.

## 6. Evidence required before training the gate

Do this in two steps.

### Step A: free temporal replay on existing records

Before new generation, replay all 27 discordants plus the registered concordant controls across every token.

Freeze the E0-inspired score before looking:

\[
S_t=
z(-\Delta_5 M_t)+
z(\Delta_5 H_t)+
z(A_t).
\]

Tests:

- Does \(S_t\) rise 1–8 tokens before repair divergences?
- Is the rise absent or smaller before regression divergences?
- Does shifting each trajectory by ±16 tokens destroy the association?
- Does permuting trajectories within response-length/family bins destroy it?
- Does the result survive grouping by the verifier that actually changed?
- Is the attention term positive, confirming engagement rather than deficit?

This cannot justify controller training by itself because the labels remain policy-level. It determines whether the E0 AUC is truly temporal or just a static row characteristic.

Kill the conflict path immediately if the signal is not temporally localized before the outcome-changing region.

### Step B: fresh causal branch pilot, still before gate training

Use a fixed fresh synthetic block—suggestion: 400 rows.

For every base trajectory:

- choose two prespecified conflict local maxima separated by at least eight tokens;
- choose two response-position-matched low-conflict controls;
- branch each moment into no-burst and one-burst rollouts;
- use frozen WHERE, dose, burst length, and decoding;
- retain all helpful/harmful/neutral outcomes;
- treat the session, not the branch, as the independence unit.

Pre-register these screens:

1. At least 40 helpful and 40 harmful causal moments; otherwise `INCONCLUSIVE`, not an adaptive extension.
2. Fixed \(S_t\) causal-benefit AUC ≥0.65 with cluster-aware lower 95% bound >0.50.
3. A threshold chosen on the first 200 rows must retain ≥60% of helpful events and admit ≤25% of harmful events on the untouched second 200.
4. Net raw \(\sum\Delta U>0\).
5. No held-out causal family may show a statistically clear sign reversal.
6. High-conflict maxima must outperform matched low-conflict controls; otherwise the signal is merely correlated with interesting token positions.
7. A four-token scratch lookahead must improve discrimination by a registered minimum—say AUC +0.03—or it is cut and the immediate gate ships.

Only after these pass should the logistic hazard gate be trained behaviorally. A GRU, ACT controller, oscillator, or full `h20` probe is a later fallback, not the first model.

## Final judgment

The Miller-faithful and empirically promising paths mostly converge at the level that matters:

- latent/default hold;
- irregular, brief reactivation;
- content selection separated from timing;
- burst rate controlled by imminent behavioral relevance;
- no continuous forcing;
- no periodic refresh as the decision rule.

They diverge on the exact sensor.

Miller/Lundqvist does not show that ACC-like response conflict directly triggers PFC gamma bursts. Its computational delay models use facilitated attractors, background drive, competition, and noise; the readout experiments establish demand sensitivity without identifying the upstream trigger.

E0 supplies a plausible engineering sensor that the neuroscience leaves unspecified: response-conflict trajectory while the correct rule channel is engaged.

So the honest synthesis is:

> The burst policy is Miller-faithful; the margin/entropy hazard is Botvinick/Bastos-inspired and empirically motivated, not a demonstrated biological gamma trigger.

That is still a coherent mechanism. It is also the shortest path to a decisive result. A per-memory oscillator would preserve the metaphor but evade the measured problem. A causally labeled conflict-triggered burst gate directly attacks it.
tokens used
7,636,273
## Bottom line

The neuroscience does not support “an oscillator decides when to focus.” In the Lundqvist/Miller work, oscillation is primarily the implementation of transient access, not the upstream decision variable.

The best reading is:

> Keep memories latent by default; emit a brief content-specific burst when current processing predicts imminent, behaviorally relevant readout.

E0’s best signal—margin collapse plus entropy rise while the governing span is already receiving attention—is strikingly compatible with conflict monitoring and predictive routing. It suggests a better gate:

> Press when the model is actively consulting the right rule but its output trajectory is entering competition—not when attention to the rule is merely low.

That is different from the failed deficit trigger. I recommend a tiny conflict-hazard gate trained on exact single-burst causal labels, optionally using an uncommitted four-token native lookahead. Do not revive the KL-based EVF gate, and do not build a periodic oscillator.

## 1. What triggers bursts in the Lundqvist/Miller account?

There are three distinct answers, depending on task epoch.

### Encoding: external input pushes an assembly into an attractor

In the Lundqvist attractor model, stimulus input makes one memory assembly slightly more excitable than competing assemblies. Fast recurrent excitation and inhibition produce a short gamma attractor state; synaptic augmentation records a latent trace. Gamma is therefore triggered by a content-bearing external cue plus the assembly’s competitive excitability. [Lundqvist et al., 2016](https://pmc.ncbi.nlm.nih.gov/articles/PMC5220584/)

The transformer analog is straightforward:

- new instruction tokens activate a memory representation;
- their hidden-state/key representation is stored;
- no continuing press is necessary.

This is the part your focus cache already solved.

### Delay: stochastic reactivation from latent excitability

During maintenance, the model does not contain a learned “this memory is needed now” classifier. Previously activated assemblies retain elevated effective connectivity through short-term synaptic augmentation. Background excitation or noise can push one over threshold; lateral competition makes it win; inhibition, synaptic depression, and fatigue terminate it. Other assemblies then become eligible.

Consequently:

- reactivations are irregular on individual trials;
- increased memory load raises burst rate, not burst duration;
- slow periodicity appears much cleaner after trial averaging than within a trial;
- latent synaptic state determines which content is easiest to reactivate, while noise helps determine exact onset.

The 2011 model implements cyclic reactivation of up to six items through synaptic augmentation, with each reactivation accompanied by gamma and the noncoding state associated with alpha/beta. [Lundqvist, Herman & Lansner, 2011](https://direct.mit.edu/jocn/article/23/10/3008/5308/Theta-and-Gamma-Power-Increases-and-Alpha-Beta) Related activity-silent models explicitly show that a nonspecific readout pulse or background noise can reactivate the facilitated assembly. [Mongillo, Barak & Tsodyks](https://barak.net.technion.ac.il/files/2012/11/synapticmemory.pdf)

This is the source of the “oscillator per memory” intuition—but it is not a precise WHEN solution. It is a probabilistic refresh mechanism.

A literal transformer implementation would periodically or stochastically sample stored memories. That could help retention, but it would replay PRESS’s false-positive problem. It does not know whether pressing improves the current token.

### Readout: behaviorally relevant demand modulates burst rate

The 2018 experiment is the decisive one. Gamma bursting and informative spiking ramped before memories were needed for comparison to forthcoming test objects. Critically:

- equally predictable sample presentations did not produce the ramp;
- the ramp represented the particular memory needed for the next decision;
- after an early non-match made the second comparison irrelevant, the second-memory ramp disappeared and beta increased;
- erroneous behavioral plans were preceded by corresponding abnormal gamma/beta dynamics.

Therefore, gamma ramping was not a generic clock and not mere event anticipation. It tracked imminent, behaviorally relevant readout. The authors infer volitional/task-demand control, but they do not identify a single upstream neuron or scalar that triggers each burst. [Lundqvist et al., 2018](https://pmc.ncbi.nlm.nih.gov/articles/PMC5785952/)

The strongest honest summary is:

| Epoch | Burst trigger |
|---|---|
| Encoding | Content-bearing sensory input |
| Delay refresh | Latent assembly excitability plus background drive/noise |
| Purposeful readout | Task state predicting imminent behavioral use |
| Burst termination | Feedback inhibition, fatigue, depression |
| Content selection | Most excitable/relevant facilitated assembly wins |

For Stencil, the relevant part is purposeful readout, not stochastic refresh.

## 2. Fries and Bastos: what opens a channel?

### Communication-through-coherence does not provide the upstream selector

In Fries’ CTC account, a channel becomes effective when a presynaptic population’s gamma rhythm arrives during the receiving population’s excitable phase. The winning input entrains the receiver; the resulting inhibition shuts out competitors. Attention can increase the relevant population’s gamma strength or frequency, giving it an entrainment advantage. [Fries, 2015](https://pmc.ncbi.nlm.nih.gov/articles/PMC4605134/)

But CTC largely assumes that a top-down attentional system has selected the representation. It explains how that selection becomes effective connectivity. It does not fully explain why attention selected it at that moment.

Transformer mapping:

- selected prompt span = presynaptic representation;
- current generation state = receiver;
- attention-logit bias = increased effective coupling;
- competing prompt/local-response inputs = rival channels.

There is no meaningful literal gamma phase in an autoregressive token index. Tokens are task events, not biological milliseconds. Adding sine waves would be decorative unless phase carries an independently useful state.

CTC validates the actuator shape—brief, selective coupling—but does not solve Stencil’s WHEN classifier.

### Predictive routing supplies a better trigger: stimulus-specific mismatch

Bastos’ predictive-routing results sharpen the timing story:

- predictable stimuli increase deep-layer alpha/beta and feedback;
- predicted pathways are selectively inhibited;
- unexpected stimuli escape that pathway-specific inhibition;
- superficial gamma, spiking, and feedforward communication increase for the prediction error;
- the strongest effect occurs after transitions from predictable to unpredictable stimuli.

Thus a channel opens when incoming processing violates a content-specific prediction, not simply because its baseline attention is low. [Bastos et al., 2020](https://pmc.ncbi.nlm.nih.gov/articles/PMC7733827/)

Transformer analog:

1. The instruction/rule supplies a top-down prediction about the acceptable trajectory.
2. The native decoder begins committing to a continuation.
3. Conflict between the native continuation and task-conditioned trajectory rises.
4. The governing rule channel receives a brief gain increase.

E0’s raw `KL(P_focus || P_native)` failed because it measured how much the actuator could move the distribution. That is leverage, not prediction error and not signed utility. Both repairs and regressions can have large KL.

Margin collapse is closer to predictive error: incompatible continuations are becoming simultaneously competitive.

## 3. Is E0’s margin collapse what Botvinick predicts?

Approximately yes—more directly than the original EVF features.

Botvinick’s conflict monitor measures simultaneous activation of incompatible response units. Formally it used Hopfield energy:

\[
C=-\sum_{i,j} a_i a_j w_{ij}.
\]

For two mutually inhibitory responses with equal negative weights, conflict is proportional to \(a_1a_2\). It is low when one response dominates and high when both are active. [Botvinick et al., 2001](https://www.krigolsonteaching.com/uploads/4/3/8/4/43848243/botvinik_2001.pdf)

If the top two decoder alternatives contain most probability mass:

- falling top-1/top-2 margin implies greater coactivation;
- entropy rise implies a broader competing response set;
- their temporal derivatives indicate conflict is developing now.

So the direction-flipped E0 result—lower `margin_delta5` predicts repair—is exactly the qualitative prediction of response-conflict monitoring.

There are two important caveats.

First, token alternatives are not necessarily incompatible task responses. `"however"` versus `"but"` is not meaningful conflict. A better task-conditioned conflict signal would distinguish:

- native/local continuation pressure;
- rule-consistent continuation pressure;
- competing obligations.

Second, conflict only says “more control may be needed.” It does not say that this particular press, span, or dose will help. Shenhav’s EVC model evaluates:

\[
EVC(s,c)=
\sum_o P(o\mid s,c)V(o)-Cost(c),
\]

using state, predicted outcomes, control identity, and intensity. Conflict is one monitoring input among errors, delay, negative feedback, and other signals. [Shenhav, Botvinick & Cohen, 2013](https://pmc.ncbi.nlm.nih.gov/articles/PMC3767969/)

Therefore E0 did not refute EVC. It showed that:

- raw one-step distribution displacement is not a good EVC estimator;
- the first-divergence label was causally blurred;
- low-dimensional response-conflict dynamics may be a better eligibility signal.

### The attention-mass direction matters

E0’s positive attention-mass AUC is particularly interesting. Taken literally, repairs were more likely when the model was already reading the selected rule span—not when it had ignored it.

That suggests this two-factor condition:

\[
\text{rule engaged} \quad\land\quad \text{response conflict rising}.
\]

Mechanistically:

- high/rising rule attention says the current step is rule-relevant;
- margin collapse says the rule-conditioned and default trajectories are competing;
- a small burst may tip an already active competition;
- low rule attention may mean the rule is irrelevant now, so forcing it displaces needed response-local context.

This is nearly the opposite of `attention_mass < tau`.

The evidence is only 27 cases, so this remains a hypothesis. But it is the most coherent hypothesis E0 produced.

## 4. ML analogs

### Entropy-triggered intervention: promising pattern, noisy sensor

Several recent systems use changes in uncertainty, rather than absolute uncertainty, to trigger extra computation or context repair.

ERGO monitors abrupt next-token entropy increases and triggers prompt consolidation in multi-turn tasks, reporting a 56.6% average improvement over its baselines. It is a 2025 workshop result and its intervention is much more explicit than Stencil’s, so treat the effect size cautiously. [ERGO](https://arxiv.org/abs/2510.14077)

The broader lesson is credible: temporal uncertainty changes can be more actionable than a global threshold. But entropy remains nonspecific. The gate needs content engagement or task relevance alongside it.

### Learned halting shows how to train the router, not what its signal should be

Adaptive Computation Time learns a halting probability through task loss plus a cost for additional computation. It allocates more recurrent steps around hard-to-predict boundaries. [Graves, 2016](https://arxiv.org/abs/1603.08983)

CALM similarly adapts transformer depth per generation step using confidence measures and reports up to roughly 3× compute reduction while controlling quality degradation. Its authors explicitly identify the hard part: translating sequence-level quality requirements into local token decisions. [CALM](https://arxiv.org/abs/2207.07061)

Mixture-of-Depths demonstrates that learned token-level routers can allocate transformer compute dynamically under a fixed budget. [Raposo et al., 2024](https://arxiv.org/abs/2404.02258)

These support a tiny learned gate, but none solves your label problem. Training a halting/gain head on final adherence without exact moment attribution would recreate E0’s causal blur.

### Hidden-state probes can predict failure—but diagnosis and repair are different

The strongest relevant findings are:

- Kadavath et al. found models can predict whether they know an answer and partially generalize across tasks, but calibration degrades on new tasks. [Language Models Mostly Know What They Know](https://arxiv.org/abs/2207.05221)
- A large 2024 probing study reported 84.3% average pre-generation hallucination-risk accuracy across many datasets. [Ji et al.](https://arxiv.org/abs/2407.03282)
- A narrow prompt-leakage study found pre-generation hidden-state probes above 90% AUROC across its tested models and held-out attacks. [Dong et al., EMNLP 2025](https://aclanthology.org/2025.emnlp-main.1082/)
- A particularly relevant 2026 study found hidden-state probes could detect whether question-asking was needed, but interventions remained about as likely to harm correct trajectories as repair incorrect ones. [What Am I Missing?](https://arxiv.org/abs/2605.31561)

That final detection/recovery gap is E0’s lesson in another form. Predicting “this trajectory looks risky” is easier than predicting “this actuator will improve it.”

### Speculative verify-then-commit is useful, but its guarantee does not transfer automatically

Standard speculative decoding drafts several tokens and lets the target model accept or reject them while preserving the target distribution exactly. [Leviathan et al., ICML 2023](https://proceedings.mlr.press/v202/leviathan23a.html)

A Stencil analog would be:

1. Generate 2–4 native tokens into a scratch KV cache.
2. Observe the native margin/entropy/attention trajectory.
3. If it remains safe, commit the draft.
4. If conflict rises, discard the scratch suffix and regenerate it with a short focus burst.

Advantages:

- it turns coincident conflict into a prospective signal;
- it avoids externally committing the first bad token;
- it directly tests whether conflict is transient or worsening;
- it resembles “readout imminent” better than a single current-token snapshot.

But it is not lossless speculative decoding. Its verifier predicts task utility, not equality to the original distribution. It must be described as transactional lookahead with a learned gate. It costs extra forwards and still needs causal labels.

## 5. Recommended design: Conflict-Triggered Readout Bursts

This is the single most promising successor.

### Policy shape

Default state is hold/no intervention—the beta-like state.

At each generation step:

1. Existing frozen Wq/Wk selects the candidate rule span.
2. Collect a fixed trajectory feature vector:

\[
x_t=[
\Delta_5 C_t,\;
\Delta_5 H_t,\;
-\Delta_5 M_t,\;
A_t,\;
\Delta_5 A_t,\;
R_t
]
\]

where:

- \(C_t=\sum_{i<j}^{k}p_i p_j\): top-\(k\) conflict energy;
- \(H_t\): decoder entropy;
- \(M_t=p_{(1)}-p_{(2)}\): top-two margin;
- \(A_t\): natural attention mass on the selected span;
- \(R_t\): Wq/Wk address stability/margin.

3. A tiny temporal gate—a logistic hazard model first, not a GRU—estimates the benefit of one burst.
4. If hazard exceeds a calibrated threshold, optionally native-draft four tokens into scratch state and re-evaluate the trajectory.
5. If confirmed, discard the draft and apply one fixed safe-dose burst for at most four tokens.
6. Enter a fixed refractory interval.
7. Otherwise commit the native token(s).

No oscillatory phase is needed. The refractory interval captures the useful part of burst scheduling without pretending autoregressive positions are gamma cycles.

### Why this attacks E0’s measured failure

It replaces:

- low attention → press

with:

- selected rule is engaged;
- response competition is growing;
- the conflict trajectory predicts that a local burst has positive causal value.

It drops KL/JS and canonical `obligation_shift` from the firing inputs. Those may remain diagnostics, but E0 says they should not drive the gate.

### Training labels

At a fixed native prefix, produce two deterministic branches:

- `A=0`: no burst;
- `A=1`: exactly one registered burst to the frozen selected span, then identical ordinary decoding.

Continue to a verifier-resolvable endpoint and compute:

\[
\Delta U=U(A=1)-U(A=0).
\]

Labels:

- helpful: \(\Delta U>0\);
- harmful: \(\Delta U<0\);
- neutral: \(\Delta U=0\).

Use the actual changed verifier family, not `combo[0]`. Keep neutral opportunities because they determine deployment firing rate and cost.

The verifier is allowed only to construct offline labels. At inference the gate sees model-internal dynamics and text-derived span keys only. The honest claim would be “automatically deployed, verifier-supervised during training,” not unsupervised control.

## 6. Evidence required before training the gate

Do this in two steps.

### Step A: free temporal replay on existing records

Before new generation, replay all 27 discordants plus the registered concordant controls across every token.

Freeze the E0-inspired score before looking:

\[
S_t=
z(-\Delta_5 M_t)+
z(\Delta_5 H_t)+
z(A_t).
\]

Tests:

- Does \(S_t\) rise 1–8 tokens before repair divergences?
- Is the rise absent or smaller before regression divergences?
- Does shifting each trajectory by ±16 tokens destroy the association?
- Does permuting trajectories within response-length/family bins destroy it?
- Does the result survive grouping by the verifier that actually changed?
- Is the attention term positive, confirming engagement rather than deficit?

This cannot justify controller training by itself because the labels remain policy-level. It determines whether the E0 AUC is truly temporal or just a static row characteristic.

Kill the conflict path immediately if the signal is not temporally localized before the outcome-changing region.

### Step B: fresh causal branch pilot, still before gate training

Use a fixed fresh synthetic block—suggestion: 400 rows.

For every base trajectory:

- choose two prespecified conflict local maxima separated by at least eight tokens;
- choose two response-position-matched low-conflict controls;
- branch each moment into no-burst and one-burst rollouts;
- use frozen WHERE, dose, burst length, and decoding;
- retain all helpful/harmful/neutral outcomes;
- treat the session, not the branch, as the independence unit.

Pre-register these screens:

1. At least 40 helpful and 40 harmful causal moments; otherwise `INCONCLUSIVE`, not an adaptive extension.
2. Fixed \(S_t\) causal-benefit AUC ≥0.65 with cluster-aware lower 95% bound >0.50.
3. A threshold chosen on the first 200 rows must retain ≥60% of helpful events and admit ≤25% of harmful events on the untouched second 200.
4. Net raw \(\sum\Delta U>0\).
5. No held-out causal family may show a statistically clear sign reversal.
6. High-conflict maxima must outperform matched low-conflict controls; otherwise the signal is merely correlated with interesting token positions.
7. A four-token scratch lookahead must improve discrimination by a registered minimum—say AUC +0.03—or it is cut and the immediate gate ships.

Only after these pass should the logistic hazard gate be trained behaviorally. A GRU, ACT controller, oscillator, or full `h20` probe is a later fallback, not the first model.

## Final judgment

The Miller-faithful and empirically promising paths mostly converge at the level that matters:

- latent/default hold;
- irregular, brief reactivation;
- content selection separated from timing;
- burst rate controlled by imminent behavioral relevance;
- no continuous forcing;
- no periodic refresh as the decision rule.

They diverge on the exact sensor.

Miller/Lundqvist does not show that ACC-like response conflict directly triggers PFC gamma bursts. Its computational delay models use facilitated attractors, background drive, competition, and noise; the readout experiments establish demand sensitivity without identifying the upstream trigger.

E0 supplies a plausible engineering sensor that the neuroscience leaves unspecified: response-conflict trajectory while the correct rule channel is engaged.

So the honest synthesis is:

> The burst policy is Miller-faithful; the margin/entropy hazard is Botvinick/Bastos-inspired and empirically motivated, not a demonstrated biological gamma trigger.

That is still a coherent mechanism. It is also the shortest path to a decisive result. A per-memory oscillator would preserve the metaphor but evade the measured problem. A causally labeled conflict-triggered burst gate directly attacks it.
