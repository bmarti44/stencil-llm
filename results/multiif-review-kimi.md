# KIMI-K3 CROSS-MODEL REVIEW — Stencil bench-wave / EVF program

I have read everything: BENCH-WAVE-PLAN v1→v4.5, EVF-PLAN (E0 kill, decision rule, E2), AGENTS.md, both sol research/post-mortem files, the CTRB/causal-moments/EVF/generator source, the tests, the E0 artifact, the calibration and dev-gate JSONs, and the WORKLOG chain. I recomputed every number I could check from the text. Findings below, graded, then the verdict.

---

## THE HEADLINE COMPUTATION (Question 2 — the most important item)

**Claim under review:** base Multi-IF strict-prompt 0.708 → 0.525 → 0.323 while inst-level moves only 0.769 → 0.752 → 0.694, interpreted as "focus-retention failure, huge headroom for the wave."

**The strict-prompt decay is exactly what conjunction arithmetic predicts from the observed inst-level rates.** Under a naive independence model, strict-prompt_t ≈ inst_t^(n_t) with n_t the cumulative constraint count. Solving for implied n at each turn:

- Turn 1: ln(0.708)/ln(0.769) = **n₁ ≈ 1.31**
- Turn 2: ln(0.525)/ln(0.752) = **n₂ ≈ 2.26**
- Turn 3: ln(0.323)/ln(0.694) = **n₃ ≈ 3.09**

The independence-conjunction model reproduces the observed strict-prompt values **to within rounding at all three turns simultaneously**, and the implied counts grow by +0.95, +0.83 per turn — internally consistent with Multi-IF's add-~1-instruction-per-turn construction. This is not a coincidence a "focus collapse" story would naturally produce.

**Decomposition of the 38.5-point strict drop (turn 1 → turn 3):**

- Hold per-constraint rate at turn-1's 0.769, let only the count grow: strict₃ = 0.769^3.09 = **0.444**. So **~26.4 points (69%) of the drop is pure constraint accumulation at zero per-constraint degradation.**
- The remaining **~12.1 points (31%)** tracks the inst-level decline 0.769 → 0.694 (−7.5 pts per constraint).

So the *maximum* drift-attributable headroom is the 7.5-point per-constraint decline — and that decline is itself un-decomposed: it can come from (a) composition (turn-3's cumulative list includes turn-1 constraints like min-sentences/max-words that are structurally hostile to a short "add a closing" follow-up), (b) response length growth and truncation at max_new=1024 (the dev-gate records show this model degenerates into repetition loops at long lengths — loops in turn-1/2 history then pollute turn-3 context), (c) the model not inferring that earlier constraints still bind (a *comprehension* failure, not an attention failure — real Multi-IF turns do not carry an explicit "still applies" marker), and only (d) attentional neglect of drifted instructions. The wave-addressable fraction is (d), which is currently **unmeasured and bounded above by ~7.5 points, not 38.5**.

Caveats I checked that do not rescue the "huge headroom" reading: positive within-response constraint correlation would push strict *above* the independence prediction (observed: it matches), and constraint-difficulty heterogeneity pushes it *below* (Jensen) — the exact fit suggests these roughly cancel, leaving no room for a large super-additive collapse term. The decisive check is free: the per-item records exist, so the conjunction prediction vs. observed, per constraint-origin-turn × family, with length/truncation breakdowns, can be computed offline in hours. **Until that decomposition is in the artifact, every headroom claim in E2's motivation is unsupported.**

---

## FINDINGS

### CRITICAL-1 — The pivot's motivating datum is misread arithmetic
As above. The interpretation "focus-retention failure, huge headroom" is not licensed by 0.708→0.525→0.323 vs 0.769→0.752→0.694. The numbers are fully explained by conjunction over accumulating constraints plus a modest per-constraint decline of unknown etiology. If E2 proceeds on the 38.5-point framing, any small positive will be over-read and any design choice tuned to "late-turn strict-prompt" will be chasing a mechanically manufactured target. **Required before any CTRB training: the offline decomposition (P1 below) registered as the headroom map.**

### HIGH-2 — E2's primary endpoint is confounded by own-history divergence (the single biggest misleading-positive channel)
The registered primary is turn-3 strict-prompt paired delta, CTRB-wave vs the recorded base arm, **each arm consuming its own history**. The plan itself registers the caveat ("late-turn arm differences are NOT clean local treatment effects") and then stakes the primary claim on exactly that comparison. A gate whose bursts at turns 1–2 produce shorter, cleaner, less loopy histories can improve turn-3 outcomes *without any turn-3 focus effect* — history length, loop content, and structure are all mediators. A positive here cannot distinguish "focus restored at turn 3" from "the wave tidied the context." The fix is cheap and the materials already exist: **the causal primary must be the gate intervening at turn 3 (and turn 2) on replayed, identical base histories** — the recorded base arm's responses are frozen on disk. Own-history becomes the secondary policy-level endpoint. The E2 text already mandates replayed base histories for the *training* anatomy; extending the same discipline to the *evaluation* is the difference between an interpretable result and a Rorschach positive.

### HIGH-3 — Span-semantics mismatch between CTRB training and Multi-IF eval
CTRB's features and q/k addressing are trained on synthetic sessions whose spans are `Constraint:`-marker sentences (`constraint_spans_of`, `b3_gen_mt` prompts all use "Constraint: …" phrasings). Real Multi-IF prompts have no such markers; the v4.5 Multi-IF arm design uses **whole user-message spans**. The six registered trajectory features include `span_attention`, `delta5_span_attention`, and `address_stability` — all of whose distributions shift when spans go from one sentence to an entire user turn (mass is mechanically higher; stability across 2–3 large spans differs from stability across many small ones). The hazard gate's threshold, validated on synthetic holdout, is miscalibrated on the eval distribution by construction. Additionally, without a heuristic-span control arm (e.g., most-recent-user-turn), a positive cannot be attributed to the learned WHERE — the v4.5 learned-vs-heuristic addressing ablation was registered and never run, so this attribution debt is already outstanding. **Pin the eval span semantics to the training semantics (or retrain features on user-turn spans), and add the heuristic-WHERE arm.**

### HIGH-4 — The mod-9 "diagnostic slice" is an unsealed inspection channel on the benchmark
"Conversations with key hash mod 9 == 0 (~100) are the disclosed in-distribution diagnostic slice; the PRIMARY claim is staked entirely on the remaining ~809." Disclosure is good; it is not sufficient. If *any* design, go/no-go, threshold, or "the gate looks sane" decision is conditioned on model outputs or scores from those ~100 real Multi-IF conversations before the primary is sealed, the one-shot integrity of the 809 is compromised invisibly — you will never be able to enumerate the decisions the slice influenced. **Register the temporal firewall: the mod-9 slice is scored only inside the same sealed run as the primary, inspected only after adjudication; any earlier inspection reclassifies the run as exploratory.**

### HIGH-5 — Causal-moment labels are high-variance and the sampling scheme biases the moment distribution
`label_causal_moment` applies a 4-token +1.0 burst and measures the outcome at **end-of-rollout, up to ~1000 tokens later**, as a per-constraint count difference. Under deterministic greedy decoding the branches diverge chaotically (the smoke test asserts `branches_differ` as a *success* criterion — i.e., the pipeline certifies that butterfly effects are present); the sign of the final adherence difference is therefore a high-variance proxy for the burst's local causal effect, with a large neutral mass. The hazard gate can learn "fire where trajectories are unstable" rather than "fire where focus helps." Compounding this, `--conflict-top` importance-samples high-conflict moments for label collection with **no registered reweighting and no registered procedure for setting the firing threshold on the natural moment distribution** — a gate trained on conflict-enriched moments and thresholded at 0.5 will over-fire (or mis-fire) at deployment rates. Register: shorter-horizon utility labels (per-constraint progress within k tokens) or a reported label-noise budget; importance weighting or threshold-on-natural-validation; and the safe-dose plateau (0.5/1.0/2.0 all non-harmful) demonstrated on synthetic holdout *before* benchmark exposure, as the WHEN spec already requires.

### MEDIUM-6 — "Amplitude solved / WHERE solved / WHEN is the bottleneck" overreads each joint
- **Amplitude:** "2x force = 0 extra repairs" shows amplitude is *not the limiting factor for repairs* in one 27-item anatomy — while the dose sweep simultaneously showed harm avoidance required *reducing* dose to x0.25. "Solved" is the wrong word both ways.
- **WHERE:** K-perm binding shows the internal win depends on the learned field. But on free generation the learned addressing never produced a win to attribute: the span-supervised proxy sat at base level and the CE wave *failed its own synthetic dev gate* (0.755 vs base 0.865). The v3.3 addendum already scoped the causal claim to the "training objective package," and the addressing ablation that would have tested it died with the confirmation. WHERE is "validated on the internal harness," full stop.
- **WHEN:** the entire quantitative case is a policy-level, outcome-aware oracle chooser worth +7.5 pts = **15 items** on n=200, followed by E0's registered kill showing cheap trajectory features don't harvest it across families. "WHEN is the bottleneck" is a reasonable hypothesis; presented as "established" (EVF-PLAN's header says exactly that) it is one 15-item oracle screen wearing a crown.

### MEDIUM-7 — The pivot pattern, stated plainly
Three single-turn recipe failures were each followed by re-scoping (dose → trigger → labels → arena); the registered stop-loss ("failure CLOSES the single-turn line") was superseded by user directive *mid-run*, before the outcome was known, with sol's estimated pass odds at ~32% — recorded honestly as ABANDONED-BY-RULING, but the kill discipline is ultimately discretionary. And the brutal ledger fact: **the wave has never significantly beaten base on any free-generation task, including its own in-distribution synthetic dev set**; its only decisive win is the sealed out-of-reach internal task (+18.5, reproduction-audited 96/96 — that win is real). Multi-IF is an *in-context, in-reach* regime — precisely the regime where this controller has repeatedly gone par-or-harmful, and where the program's own B2 probes showed off-distribution firing hurts. The pivot is defensible **only** as a cheap scope test with the corrected (CRITICAL-1) headroom framing and a de-confounded endpoint (HIGH-2). As currently motivated, it is motivated reasoning with good bookkeeping.

### MEDIUM-8 — Synthetic↔Multi-IF mismatches beyond the kwargs firewall
(a) `b3_gen_mt` appends an explicit "Every earlier constraint from this conversation still applies" sentence; real Multi-IF requires *inferring* persistence. The gate trains on an easier interpretation problem than the eval poses. (b) The held-out families (punctuation, startend, language) are absent from all training data but present in Multi-IF; the E2 family-holdout gate can pass within the five trained families while the gate behaves arbitrarily on the three never-trained ones. Register per-family eval reporting with the explicit prior that benefit concentrates in trained families. (c) Shape-mirroring Multi-IF's structure is taxonomy-level adaptation — legitimate under the firewall norm, but the eval is then not fully OOD; scope transfer claims accordingly.

### MEDIUM-9 — The amendment pattern on infrastructure gates
Twice, a registered criterion proved unpassable and was amended via reviewer ruling (the 0.5 logit-magnitude bound → recorded-fail-but-accepted at 0.6955/0.7679; KV token-by-token parity → bounded-drift acceptance). Each ruling is individually defensible (bf16 kernel drift is real; identity rests on hashes and top-1). The pattern to watch is that *process* gates get amended while *claim* gates get honored (dev-gate FAIL, B2 FAIL ×2, E0 kill all stand). That is the right asymmetry — keep it, and keep the failed magnitude gates on the record exactly as v3.1 did.

### LOW-10 — The x0.5 dose-sweep number is prose-only
Third violation of the per-row-records rule, disclosed, and it fed the v4.5 motivation. The playbook lesson keeps recurring because the rule is enforced at seal time but not at exploration time.

### LOW-11 — E0's gate was near-unpassable by construction
n=27, 11 features, leave-one-family-out — the kill was close to foregone. Fine for kill-fast purposes (and it was honored, which is what matters), but it means E0's failure is weak evidence *against* WHEN-learnability, just as the 15-item oracle is weak evidence *for* it. The honest state of knowledge is "timing headroom exists at policy level; moment-level learnability is untested with adequate power." E2's causal labels are the right correction to E0's real flaw (policy-divergence labels); say that, and don't say more.

### LOW-12 — Cross-model decay anchors are conjunction-confounded too
"Published models decay 88→71" (o1-preview) vs this model's 38.5-point drop: under conjunction mechanics, a higher per-constraint rate mechanically produces a smaller strict-prompt decay at identical constraint counts. The "instruction forgetting" literature partly measures arithmetic; do not anchor headroom or cross-model comparisons on raw strict-prompt decay.

### What the record shows is solid (for the balance sheet)
The contamination machinery (single-use invariant, sealed jobs, hash-verified resume, atomic per-work records, mechanical leak firewalls) is genuinely strong; the statistics loop *worked* (reviewers killed the Clopper-Pearson plug-in with type-I 0.45–0.50 and it was replaced with a validated Tango construction); negative results are recorded as findings, not buried (B2 ×2, dev-gate, E0, the failed magnitude gate); the CTRB smoke script is explicitly labeled "plumbing-smoke-not-evidence"; determinism is tested bitwise through the consumer path. This is rare discipline and it is why the failures above are diagnosable at all.

---

## WHAT I WOULD DO DIFFERENTLY (registered, in order, before any CTRB training run)

- **P1 (free, hours, no GPU):** Offline decomposition of the recorded base Multi-IF arm — per-constraint pass rate by constraint-origin turn × family; response length, truncation, and timeout rates per turn; observed strict-prompt vs the conjunction prediction. Published as the registered headroom map. If the per-constraint decline concentrates in composition/length/truncation, the arena claim dies *now*, cheaply.
- **P2:** Re-stake the E2 primary: gate intervention at turn 2/3 **on replayed identical base histories** (causal primary), own-history as secondary policy endpoint, and constraint-level paired McNemar on inst-level as co-primary (escapes the conjunction mechanics entirely).
- **P3:** Eval arms must include a heuristic-WHERE control (most-recent-user-turn span), a random-WHEN control (matched fire rate), and the zero-dose bitwise-base check. Without these, attribution of any positive is impossible.
- **P4:** Pin eval span semantics to training semantics, or retrain features on user-turn spans; register the choice.
- **P5:** Temporal firewall on the mod-9 slice (sealed-run-only scoring, post-adjudication inspection).
- **P6:** Label-noise budget + importance reweighting (or threshold-on-natural-distribution) for the conflict-sampled harvest; safe-dose plateau on synthetic holdout pre-exposure.
- **P7:** Register expected discordant volume at turn 3, minimum fire-rate reporting, and per-family reporting including the three never-trained families.

**Single biggest risk of a misleading positive:** HIGH-2, accelerated by CRITICAL-1 — a small true policy-level improvement mediated by history-shaping side effects, measured on a conjunction-inflated target, and read as "the wave restores focus on drifting instructions." The fix (P2) costs one re-registration and uses records that already exist.

---

## BOTTOM-LINE VERDICT

**Process: scientifically defensible — exemplary, in fact.** Registration culture, sealed execution, honest negative reporting, and a review loop that demonstrably catches real bugs (the compat-matrix sorted-pair bug, the lm-eval drift, the random-seed rows, the dead CP statistic) are all functioning as designed.

**Science: conditionally defensible, currently over-stated.** The internal out-of-reach win is real and audited. The single-turn line is an honest, well-autopsied negative. But the multi-turn pivot is currently motivated by a misread of conjunction arithmetic as focus collapse; the "amplitude/WHERE solved, WHEN is the bottleneck" chain is a plausible narrative wearing the word "established"; and the E2 design as registered can produce an uninterpretable positive through the own-history confound, the span-semantics mismatch, and the diagnostic-slice channel.

**Ruling: proceed with E2 only after P1–P5 are folded into the registration, with the claim re-scoped to its defensible form:** *"a conflict-triggered attention burst can recover some fraction of a modest late-turn per-constraint adherence decline"* — a claim worth testing, roughly one-fifth the size of the one currently on the banner. If P1's decomposition shows the per-constraint decline is composition/length/truncation rather than neglect, the correct scientific output of this program is the honest boundary statement the WORKLOG already half-wrote in August: the wave wins where information is provably out of reach, and has no demonstrated value where the model can already read the prompt.