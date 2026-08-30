codex
The best next move is not an oscillator. It is to repair the learning problem: the current system trains one head to recognize Python syntax and another only to rank positive candidates, then asks an untrained absolute score to decide whether any candidate should be used.

That failure is almost inevitable:

- Timing labels come from `ast_moments`, irrespective of whether a governing obligation exists, so obligation-blindness is taught by construction: [t2_train_selector.py](/home/bmarti44/stencil-llm/scripts/t2_train_selector.py:98).
- Address training explicitly discards null cases and trains CE only where a correct candidate exists: [t2_train_selector.py](/home/bmarti44/stencil-llm/scripts/t2_train_selector.py:165). Candidate CE learns relative rank; adding a constant to every candidate logit leaves the loss unchanged. It cannot calibrate an absolute max-score rejection rule.
- The resulting enormous score scale and perfect 130/130 positive ranking can coexist with useless abstention. They are not contradictory.
- Zero false presses on 18 calibration cases is weak evidence: even 0/18 gives a one-sided 95% false-press upper bound around 15%. Max-plus-epsilon bought empirical calibration safety by eliminating nearly all coverage.

## Top three by expected information per GPU-hour

| Rank | Experiment | Cost | Decisive question |
|---|---|---:|---|
| 1 | Score-policy matrix using the existing heads | No training; one feature collection and ~15-minute dev replay | Does the existing representation already separate live from quoted candidates under a relative/provenance-aware score? |
| 2 | Joint candidate-or-null scorer with hard negatives | Head-only training on cached h20 features; likely under 30 minutes | Does directly teaching “press this memory or press nothing” solve both blockers? |
| 3 | Tentative counterfactual press with a utility/safety filter | Extra forwards only at proposed moments; likely under one hour for dev | Can harmful presses be detected locally without an oracle obligation scorer? |

I would not register a full oscillator run before those three.

## 1. Joint candidate-or-null scorer with hard lookalike negatives

**Mechanism.** Replace the independent timing/address/threshold stack with one memory-conditioned decision:

```text
current h20 state + every candidate span
    -> scores [NULL, candidate_1, ..., candidate_n]
    -> either abstain or press exactly one span
```

A minimal implementation is:

```python
q = normalize(Wq(h_t))
k_j = normalize(Wk(candidate_j))
s_j = q @ k_j / temperature
s_null = null_head(h_t)
```

Train a listwise softmax over `[s_null, s_1, …, s_n]`. The target is the governing ledger entry only at a real decision opportunity with that obligation active; it is `NULL` at ordinary tokens, obligation-free syntax moments, cleared types, stale-only types, and distractor-only contexts. Add a margin term requiring the live entry to beat the strongest same-type quoted/stale entry. This is the “dustbin” pattern used for partial matching in [SuperGlue](https://openaccess.thecvf.com/content_CVPR_2020/html/Sarlin_SuperGlue_Learning_Feature_Matching_With_Graph_Networks_CVPR_2020_paper.html), not a post-hoc threshold over a classifier never trained on no-match cases.

**Why it attacks the failure.** Timing becomes conditional on the actual memory candidates, so a syntax moment with no applicable memory maps to `NULL`. Hard negatives directly teach the distinction that defeated max-score calibration: authoritative `prefix=foo` versus a format-identical quoted `prefix=bar`. Dense retrieval work similarly depends on hard negatives because easy/random negatives do not teach fine distinctions; see [DPR](https://aclanthology.org/2020.emnlp-main.550/).

**Cheap falsifier.** Cache Qwen h20 states and candidate span features once on fresh T2b train/calibration/dev blocks. Train only this small head. Before generation, require:

- Conditional address accuracy ≥90%.
- Active press recall ≥50%.
- Zero false presses over at least 300 registered absent/cleared/stale-only opportunities, giving roughly a 1% one-sided upper confidence bound—not merely 0/18.
- Same-type lookalike margin positive on ≥90% of active cases.

Then run 24 dev sessions once. Require closure ≥0.5, adherence lift ≥10 points, and disclose paired parse/exec losses.

**Main risk.** It may learn fixed templates, ledger layout, or provenance markers rather than semantic applicability. Run a version without explicit source/provenance bits and an intentionally perturbed-layout split. If only the provenance-bit version works, the honest result is “structured ledger selection works,” not autonomous instruction recognition.

## 2. Relative-margin and provenance-aware score retrofit

**Mechanism.** Before retraining anything, evaluate score functions that are invariant to the pathological absolute scale:

```text
top1 − top2
authoritative-live − best same-type distractor
top1 − logsumexp(other candidates)
cosine similarity after q/k normalization
candidate score − learned/fixed NULL score
```

Restrict ranking to candidates of the timing head’s predicted type. As an explicit ceiling, use the ledger tracker’s known authoritative span and compute:

```python
margin = score(live_span) - max(score(same_type_quoted_spans))
```

Also run a structured-policy baseline: if the predicted type has an active authoritative ledger span, press it; otherwise abstain. That uses deployment-visible ledger provenance rather than pretending raw similarity can rediscover authority.

**Why it attacks the failure.** The present threshold asks “is this maximum large?” when the useful question is “does the authoritative candidate beat its closest confusable alternative?” Relative margins cancel norm and candidate-set shifts. The structured arm cleanly tells you whether everything except autonomous authority detection is already sufficient.

**Cheap falsifier.** Instrument all candidate scores at each of the 941 timing fires and run an offline grid over score rule, threshold, and beta. Report ROC/PR by active, absent, cleared, and stale-only cell. Only behaviorally replay nondominated policies on the 24-session dev set. No head training is needed.

**Main risk.** `live-minus-distractor` uses authoritative provenance and is therefore a ceiling, not autonomous selection. Top1-minus-top2 is autonomous but can be confidently wrong when all candidates are lookalikes. If every autonomous margin has poor active/null separation while the provenance ceiling works, retraining with explicit null labels is mandatory.

This is my number-one experiment because it reveals within minutes whether useful geometry already exists.

## 3. Counterfactual tentative press and exact rollback

**Mechanism.** At a proposed press, compute both next-token distributions:

```text
base logits
spotlighted logits
```

Because the spotlight touches only the current prediction row, if both arms choose the same greedy token, their future token histories reconverge exactly. If the argmax differs, briefly maintain two branches until the local syntactic unit closes—function identifier, docstring opener, or annotation—and choose base or pressed using a safety/utility filter. The first filter should know only generic validity, not the expected obligation value.

**Why it attacks the failure.** It permits an aggressive first-stage selector without committing every uncertain press. That directly separates two questions currently entangled by the zero-FP threshold:

1. Can we generate enough potentially useful presses?
2. Can we reject the harmful subset after observing their immediate causal effect?

**Cheap falsifier.** On fixed dev seeds, lower theta until proposed coverage is substantial, then evaluate three deterministic branch selectors:

- Syntax-only verifier.
- Learned verifier using branch logits/hidden-state deltas.
- Oracle scorer as an upper bound only.

Measure helpful, harmful, and neutral changed-argmax events. If the oracle branch selector succeeds but syntax-only and learned filters cannot separate help from harm, rollback does not solve autonomy. If syntax-only removes most parse/exec damage while retaining adherence gains, it is immediately useful.

**Main risk.** Local syntactic validity may not predict delayed semantic drift. Lowering theta may also make dual-branch generation expensive. The oracle branch selector must never become the reported learned result.

## 4. Calibrated selective prediction instead of empirical zero-FP

**Mechanism.** Treat pressing as selective prediction: maximize coverage subject to a registered risk bound. Risk should be behavioral—for example, “base parsed/executed but the pressed branch did not”—rather than “a score crossed a threshold on an absent example.” Train or calibrate a rejection head jointly, as in [SelectiveNet](https://proceedings.mlr.press/v97/geifman19a), then select its operating point on a sufficiently large calibration set. [Conformal Risk Control](https://openreview.net/pdf?id=33XGfHLtZg) is relevant if the loss and threshold family satisfy its assumptions; otherwise use fixed-grid binomial confidence bounds and say exactly that.

**Why it attacks the failure.** A hard 0/18 calibration rule optimized the wrong endpoint: virtually zero coverage. Selective prediction exposes the actual tradeoff. Raw discriminative confidence is often a poor novelty/no-match score, which is also the motivation behind energy-based alternatives in [Energy-based OOD detection](https://proceedings.neurips.cc/paper/2020/hash/f5496252609c43eb8a3d147ab9b9c006-Abstract.html).

**Cheap falsifier.** Sweep the existing contaminated and registered score thresholds over fixed exploratory seeds and plot:

```text
coverage
false presses by counterfactual cell
adherence lift
paired parse/exec losses
```

If no threshold produces even 20–30% useful coverage before validity damage rises, calibration alone is dead; do not spend a training run on it. The earlier unsafe-threshold result—only +0.3 adherence points—already makes me skeptical.

**Main risk.** Risk guarantees do not automatically survive distribution shift, and relaxing “zero false press” may be unacceptable in code generation. The correct safety unit is probably per work or per session, not per token.

## 5. Counterfactual press-utility head

**Mechanism.** Train a policy to predict the causal value of pressing, not merely whether an obligation exists. At each candidate moment, generate paired short branches with and without the spotlight and label the intervention:

```text
helpful: adherence improves without validity loss
harmful: validity/adherence worsens
neutral: scored outcome unchanged
```

Input features can include current h20, selected candidate embedding, relative margin, and the base-versus-pressed logit delta. At inference, press only when predicted benefit exceeds predicted harm by a calibrated margin.

**Why it attacks the failure.** “Is this syntax?” and “does this span look relevant?” are proxies. The desired decision is “will pressing this memory improve this generation now?” This directly optimizes that decision.

**Cheap falsifier.** Collect counterfactual labels on 24–48 T2b training sessions at syntax fires only. Fit a linear model first; then a two-layer MLP only if linear separation is weak. On fresh dev events, require useful AUPRC and a clear separation between beneficial and harmful interventions before running complete sessions.

**Main risk.** The labels are scorer- and template-specific, and delayed effects make short branches myopic. If it needs full-work rollouts to label every press, training data becomes expensive and the policy may simply distill the synthetic checker.

## 6. Per-memory oscillators or phase-coded slots

**Mechanism.** Give every live ledger entry an independent small complex state rather than superposing all memories in one resonator:

```text
z_j ∈ C^4
write/update: reset amplitude and phase for slot j
hold:         z_j <- ρ_j exp(iω_j) z_j
clear:        z_j <- 0
query:        r_j(t) = Re(q_t* · z_j)
```

The oscillator carries no value; text remains in the ledger. It carries slot identity, age, urgency, or phase. A joint current-state/oscillator coherence score proposes a press, and the proven address head supplies the text span. Separate oscillators genuinely fix the repo’s earlier superposition failure—one resonator preserved slot 0 and destroyed slots 1–3: [WORKLOG.md](/home/bmarti44/stencil-llm/WORKLOG.md:160).

Oscillatory phase multiplexing has real precedent: Lisman and Idiart placed different memories in different high-frequency subcycles of a slower rhythm ([Science paper](https://www.ucl.ac.uk/brain-sciences/sites/brain_sciences/files/lisman95-oscillatory-memory.pdf)), while [Phased LSTM](https://proceedings.neurips.cc/paper/2016/hash/5bce843dd76db8c939d5323dd3e54ec9-Abstract.html) used oscillation to schedule sparse updates for event-based streams.

**Why it might attack the failure.** Unlike the obligation-blind timing head, each press decision would be conditioned on a persistent state belonging to a specific active memory. Updates and clears can reset individual states without cross-memory destruction.

But the skepticism is important: T2b already knows memory identity and address. Its decision moments are irregular token events, not periodic phenomena. A per-slot active bit plus an MLP may do exactly the same job without phase drift. Oscillation does not create semantic applicability.

**Cheap falsifier.** Train controller heads only on cached h20 sequences, with no Qwen training. Freeze four equal-parameter contenders:

- Independent oscillator bank.
- Static per-memory embedding plus MLP.
- Leaky/EMA evidence integrator.
- Keyed latch or tiny GRU.

Test active/absent/cleared/stale-only press classification and then insert 0, 32, and 128 semantically inert tokens before decision moments. Also phase-scramble oscillators at evaluation. Proceed to generation only if the oscillator beats all nonoscillatory controls and remains invariant to inert token insertion.

**Main risk.** Phase aliasing makes behavior depend on arbitrary token count, compaction, or formatting. If amplitude/reset carries the useful signal and phase can be scrambled without effect, the oscillator is decorative. If the latch ties it, choose the latch.

## 7. Structured decision boundaries as the deployment baseline

**Mechanism.** Use a structured focus API and runtime decision hooks:

```text
focus.set/clear establishes authoritative live entries
parser/tool runtime identifies decision boundary and type
selector chooses among currently live matching entries
```

For code, parser state already provides excellent timing. For agentic work, analogous boundaries are message generation, tool selection, plan revision, commit, and handoff—not arbitrary token positions.

**Why it attacks the failure.** It removes both learned ambiguities: provenance identifies what is live, and runtime structure identifies when governance matters. The neural component only ranks active entries.

**Cheap falsifier.** Remove theta, use exact active-ledger eligibility plus parser timing, and replay T2b dev. This should be done even if the goal is autonomous pressing because it establishes the achievable ceiling of a deployable structured system.

**Main risk.** It does not prove autonomous discovery. It is nevertheless likely the most useful near-term product and the security-safe route: retrieved or quoted text cannot silently acquire authority.

## What I would register

A short head-only sprint:

1. **A0 — Policy matrix:** current heads; raw max, normalized margin, top1–top2, live–distractor ceiling, and structured eligibility. No training.
2. **A1 — Joint null scorer:** normalized candidate-or-null model trained with same-type hard negatives.
3. **A2 — Behavioral dev replay:** only nondominated A0/A1 policies, with press counts and paired adherence/parse/exec evidence.
4. **Optional A3 — Counterfactual branch filter:** only if A1 generates useful but unsafe coverage.

Stop the autonomous line if the joint scorer cannot achieve at least 50% active-event recall while keeping 0 false presses across ≥300 registered counterfactual negatives, or if component success fails to yield meaningful behavioral closure.

Brian’s oscillator idea is worth including only as a cached-feature contender against matched latch/EMA/GRU controls. The toy transplant result proves oscillatory state can carry identity. It does not answer the present question, because identity and address are already the solved parts; the missing variable is whether a particular memory should govern this particular generation event.
