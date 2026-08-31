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
- Eligibility/readout: content-addressed reactivation cue.
- EVF monitor: ACC/EVC analog.
- No-focus/refractory state: beta-like protection and inhibition.
- Short applied focus: gamma-like expression/readout burst.
- Native response processing: bottom-up/current-stream computation.

This is an analogy, not a claim that transformer steps literally implement beta or gamma frequencies.

## Training labels

All labels can be computed offline without humans.

### Obligation-state labels

Run existing deterministic verifiers on every response prefix to derive:

- not applicable;
- pending;
- satisfied;
- newly violated;
- still recoverable;
- no longer recoverable.

Use canonical, base, wave, and minimal-violation mutation prefixes.

### Intervention-utility labels

At exposed training prefixes, execute paired short rollouts:

- native;
- weak correct-span focus;
- wrong-span focus.

Define registered utility, for example:

\[
U = \Delta \text{constraint progress}
-2\,\mathbf 1[\text{other constraint regresses}]
-\lambda\mathrm{JS}
-\mu\mathbf 1[\text{truncation/loop}].
\]

Positive action label: focused rollout has \(U>0\).  
Negative action label: \(U\le0\), especially low-`ψ` cases where focus harms.

This directly trains the question you care about.

### Required generalization split

Hold out:

- complete constraint families;
- topics;
- phrasing templates;
- obligation values;
- response carriers.

If the tracker is trained and tested within the same constraint taxonomy, it is an automatic IFEval policy, not a general focus mechanism.

## Registration-quality gate sketch

### Offline discrimination gate

Before any full generation run:

- At least 100 helpful and 100 harmful paired intervention opportunities.
- Whole-topic and whole-constraint-family held-out folds.
- Compare at matched firing rate against:
  - `ψ<τ`;
  - entropy-only;
  - readout-margin-only;
  - obligation-state-only;
  - counterfactual-KL-only.
- Require:
  - PPV lower confidence bound ≥0.70;
  - recall lower confidence bound ≥0.50;
  - net predicted utility at least 2× the `ψ<τ` gate;
  - no family with negative net utility.

The present 15/12 set is sufficient for a kill screen, not certification.

### Safe-dose interval

Reject another knife-edge optimum. Pre-register a small grid and require at least three adjacent doses—for example nominal dose and ±25%—to all show:

- positive paired utility;
- no truncation excess;
- no significant regression increase;
- same qualitative firing decisions.

If only one dose works, the mechanism is not deployable even if its mean score wins.

### Behavioral gate

On fresh prompt-disjoint generation:

- Existing `+2.0 points` and exact McNemar gate;
- repairs/regressions reported raw;
- regression count no more than half the repair count;
- matched-cost entropy, `ψ`, and periodic-refresh controls;
- tracker shuffle and rule-key permutation must bind;
- zero-focus output must be bitwise base.

For long-horizon evaluation, additionally require lift to increase or remain stable with turn/distractor distance.

## Fastest decisive pilot

Do not build the full GRU first.

1. Reconstruct token-level prefixes for the existing base and wave records.
2. Identify the first obligation-sensitive divergence using verifier-prefix states and minimal mutations.
3. Teacher-force those prefixes once through Qwen and cache:
   - `h20`;
   - W2 rule logits;
   - entropy/margin trajectories;
   - natural attention summaries.
4. Run one additional weak-focus forward at each selected prefix to obtain KL and distribution shifts.
5. Produce verifier-derived pending/urgency labels.
6. Fit a regularized logistic EVF probe with leave-topic and leave-family-out folds.
7. Test whether it reaches approximately \(r_+\ge.60,\ r_-\le.25\) on the 15/12 anatomy.

Kill it immediately if:

- focused-vs-native KL is indistinguishable on repairs and regressions **and**
- obligation state does not add held-out discrimination;
- performance disappears when constraint families are held out;
- the gate works only by recognizing constraint type or response position;
- safe-dose behavior remains a narrow peak.

Only if this cheap probe separates the anatomy should you collect the larger paired-rollout set and train the recurrent version.

## Honesty boundary

This architecture is fully automatic at inference only if:

- rule spans are selected by the learned autonomous WHERE mechanism;
- the tracker receives natural-language rules and generated text, not constraint IDs;
- no vendored checker or future response is consulted;
- thresholds are frozen before evaluation;
- no generator metadata describes which obligation is active.

Using checkers to create offline supervision is not an inference oracle. It is supervised training, and must be disclosed as such.

The harder honesty issue is generality: a tracker trained on code-verifiable IFEval families may simply internalize those verifiers. The claim becomes genuinely task-general only after held-out-family and natural long-horizon transfer. Until then, the accurate claim is:

> “A tiny frozen-trunk controller learned, from automatically verified counterfactual experience, when a transient rule reactivation was expected to help.”

That is still scientifically meaningful. It directly targets the isolated bottleneck and is substantially closer to Miller’s predictive, context-cued control loop than the current attention-deficit threshold.
tokens used
7,315,049
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
- Eligibility/readout: content-addressed reactivation cue.
- EVF monitor: ACC/EVC analog.
- No-focus/refractory state: beta-like protection and inhibition.
- Short applied focus: gamma-like expression/readout burst.
- Native response processing: bottom-up/current-stream computation.

This is an analogy, not a claim that transformer steps literally implement beta or gamma frequencies.

## Training labels

All labels can be computed offline without humans.

### Obligation-state labels

Run existing deterministic verifiers on every response prefix to derive:

- not applicable;
- pending;
- satisfied;
- newly violated;
- still recoverable;
- no longer recoverable.

Use canonical, base, wave, and minimal-violation mutation prefixes.

### Intervention-utility labels

At exposed training prefixes, execute paired short rollouts:

- native;
- weak correct-span focus;
- wrong-span focus.

Define registered utility, for example:

\[
U = \Delta \text{constraint progress}
-2\,\mathbf 1[\text{other constraint regresses}]
-\lambda\mathrm{JS}
-\mu\mathbf 1[\text{truncation/loop}].
\]

Positive action label: focused rollout has \(U>0\).  
Negative action label: \(U\le0\), especially low-`ψ` cases where focus harms.

This directly trains the question you care about.

### Required generalization split

Hold out:

- complete constraint families;
- topics;
- phrasing templates;
- obligation values;
- response carriers.

If the tracker is trained and tested within the same constraint taxonomy, it is an automatic IFEval policy, not a general focus mechanism.

## Registration-quality gate sketch

### Offline discrimination gate

Before any full generation run:

- At least 100 helpful and 100 harmful paired intervention opportunities.
- Whole-topic and whole-constraint-family held-out folds.
- Compare at matched firing rate against:
  - `ψ<τ`;
  - entropy-only;
  - readout-margin-only;
  - obligation-state-only;
  - counterfactual-KL-only.
- Require:
  - PPV lower confidence bound ≥0.70;
  - recall lower confidence bound ≥0.50;
  - net predicted utility at least 2× the `ψ<τ` gate;
  - no family with negative net utility.

The present 15/12 set is sufficient for a kill screen, not certification.

### Safe-dose interval

Reject another knife-edge optimum. Pre-register a small grid and require at least three adjacent doses—for example nominal dose and ±25%—to all show:

- positive paired utility;
- no truncation excess;
- no significant regression increase;
- same qualitative firing decisions.

If only one dose works, the mechanism is not deployable even if its mean score wins.

### Behavioral gate

On fresh prompt-disjoint generation:

- Existing `+2.0 points` and exact McNemar gate;
- repairs/regressions reported raw;
- regression count no more than half the repair count;
- matched-cost entropy, `ψ`, and periodic-refresh controls;
- tracker shuffle and rule-key permutation must bind;
- zero-focus output must be bitwise base.

For long-horizon evaluation, additionally require lift to increase or remain stable with turn/distractor distance.

## Fastest decisive pilot

Do not build the full GRU first.

1. Reconstruct token-level prefixes for the existing base and wave records.
2. Identify the first obligation-sensitive divergence using verifier-prefix states and minimal mutations.
3. Teacher-force those prefixes once through Qwen and cache:
   - `h20`;
   - W2 rule logits;
   - entropy/margin trajectories;
   - natural attention summaries.
4. Run one additional weak-focus forward at each selected prefix to obtain KL and distribution shifts.
5. Produce verifier-derived pending/urgency labels.
6. Fit a regularized logistic EVF probe with leave-topic and leave-family-out folds.
7. Test whether it reaches approximately \(r_+\ge.60,\ r_-\le.25\) on the 15/12 anatomy.

Kill it immediately if:

- focused-vs-native KL is indistinguishable on repairs and regressions **and**
- obligation state does not add held-out discrimination;
- performance disappears when constraint families are held out;
- the gate works only by recognizing constraint type or response position;
- safe-dose behavior remains a narrow peak.

Only if this cheap probe separates the anatomy should you collect the larger paired-rollout set and train the recurrent version.

## Honesty boundary

This architecture is fully automatic at inference only if:

- rule spans are selected by the learned autonomous WHERE mechanism;
- the tracker receives natural-language rules and generated text, not constraint IDs;
- no vendored checker or future response is consulted;
- thresholds are frozen before evaluation;
- no generator metadata describes which obligation is active.

Using checkers to create offline supervision is not an inference oracle. It is supervised training, and must be disclosed as such.

The harder honesty issue is generality: a tracker trained on code-verifiable IFEval families may simply internalize those verifiers. The claim becomes genuinely task-general only after held-out-family and natural long-horizon transfer. Until then, the accurate claim is:

> “A tiny frozen-trunk controller learned, from automatically verified counterfactual experience, when a transient rule reactivation was expected to help.”

That is still scientifically meaningful. It directly targets the isolated bottleneck and is substantially closer to Miller’s predictive, context-cued control loop than the current attention-deficit threshold.
