# PRESS-PLAN — making autonomous press timing work

Governing plan for the post-TIMED-SELECTOR program. Question: can the
WHEN-to-press decision be made autonomous, now that the mechanism
(spotlight, +14.5 val) and the WHERE (address, 130/130) are proven and
the failure is precisely diagnosed?

Grounding: results/timed-selector-report.md (the honest negative),
results/research-timing-{design-sol,neuro-fable,ml-fable,crossfield-fable}.md
(4-lane research, 2026-08-30). Harness: frozen Qwen3-1.7B
(src/stencil/qwen3.py), T2b session generator (interference="s0"),
existing scorers and paired parse/exec machinery, cached h20 features.

## Diagnosis being attacked (from the closed program + research)

1. Zero-false-press is the Neyman-Pearson alpha=0 corner: for any
   imperfect score the only feasible policy is "never press" (observed:
   14/14794). The constraint asserted infinite false-press cost; the
   actual cost is measurable (~1.7% paired validity per press event).
2. The controller was untrainable by construction: timing labels came
   from syntax alone (obligation-blind by design); the address head
   never saw a null case (relative rank only — its absolute score
   cannot calibrate a rejection rule); 0/18 calibration bounds false
   press only at ~15% (95% one-sided).
3. The deterministic checker feedback is a free error signal no arm
   consumes (event-triggered control / cholinergic detector / ripple
   state-triggering all say: trigger on detected events).
4. Biology never learns "when" as a free binary under asymmetric
   penalty: the rhythm presses by default; learning sets phase and gain
   (Han et al. 2025 Neuron; Lundqvist bursts; PBWM opponent gating).

## Registered ladder (ranked by expected information per GPU-hour)

Order is a dependency ladder: each rung's result gates the next. All
runs on dev/train seeds unless marked; val seeds stay sealed until one
pre-registered validation per surviving policy. Every rung reports
paired parse/exec vs base (Gate-3 style) alongside adherence.

### P0 — Diagnostics on existing artifacts (no training, no new GPU runs*)

*P0.4 needs generation replays; the rest is cached-features/logs work.

- P0.1 Score-policy matrix (sol A0): at the 941 logged timing fires,
  instrument all candidate scores and evaluate offline: raw max
  (baseline), top1-top2, top1-logsumexp(rest), normalized cosine,
  live-minus-best-same-type-distractor (provenance CEILING, not
  autonomous), structured eligibility (press iff predicted type has an
  active ledger entry). ROC/PR per counterfactual cell
  (active/absent/cleared/stale_only).
- P0.2 Attention-mass liveness scan (Attention Tracker replication):
  per head, attention mass from press-moment token to live vs
  distractor spans over cached sessions; rank heads by separation;
  liveness score = summed mass over top-k heads. Training-free.
- P0.3 Empirical false-press cost: inject deliberate wrong-span and
  wrong-moment presses across seeded dev sessions; measure adherence +
  validity damage per press event -> empirical cost C and the Bayes
  press threshold p* = 0.017C/(14.5+0.017C). Also bias-magnitude sweep
  (beta x {0.25,0.5,1.0}) at mistimed moments: if damage is superlinear
  in magnitude, soft pressing is structurally safe.
- P0.4 Threshold sweep on the already-trained selector: sweep theta
  below the registered value at ~5 operating points, replay 24 dev
  sessions each; plot adherence and paired validity vs press rate. If
  the curve peaks above base at nonzero press rate, the constraint
  (not the representation) caused the collapse.
- P0.5 Event-triggered baseline (no learning): press for the implicated
  obligation on the work turn AFTER the checker flags its violation
  (reactive; one turn late; near-zero false press by construction),
  with a refractory rule. Single dev replay. Decisive either way: >8
  pts recovered => the learned-controller framing was solving the
  wrong problem; ~0 => violations are unrecoverable once flagged and
  prediction is genuinely required.

GATE G0: proceed to P1 with whichever score family is nondominated in
P0.1/P0.2; carry C and p* from P0.3 as the registered risk budget
(replacing zero-false-press everywhere downstream). If the provenance
ceiling in P0.1 fails too, the representation lacks the signal — skip
to P2/P4 (redesigns) directly.

### P1 — Joint candidate-or-null scorer (head-only, ~30 min training)

Sol's A1. One listwise softmax over [NULL, cand_1..cand_n]: normalized
query-key scores + a null head over h_t. Targets: the governing entry
at real active opportunities; NULL at ordinary tokens, obligation-free
syntax moments, cleared/stale-only types, distractor-only contexts.
Margin term: live entry must beat the strongest same-type quoted/stale
lookalike (hard negatives mined from our own logs — the exact
distractors that defeated max-score). Trained on cached h20 features.

Component gates before any generation run: conditional address >=90%;
active press recall >=50%; zero false presses over >=300 registered
negative opportunities (a real ~1% bound, not 0/18); positive lookalike
margin on >=90% of active cases. Then one 24-session dev replay:
closure >=0.5 of oracle headroom, lift >=10 pts, paired validity
disclosed. Ablation: retrain without provenance/layout cues + a
perturbed-ledger-layout split; if only the provenance version works,
record honestly as "structured selection works, autonomous recognition
does not".

STOP RULE (autonomous line): if the joint scorer cannot reach 50%
active recall at the registered false-press bound, or component success
fails to convert to >=0.25 behavioral closure on dev, the autonomous
line closes (honest negative #2) and the program continues on P0.5 /
P5 (structured + event-triggered deployment recipe) only.

### P2 — Rhythm-default press: learn phase and gain, not whether
(the Miller-faithful redesign; neuro lane #1)

Remove the binary decision entirely. A shared scheduler of period T
(~4-8 steps) presses by default with a raised-cosine envelope; each
live ledger entry has a learned phase offset phi_i and scalar gain g_i
(soft bias, magnitude from P0.3's safety curve). The learner never
decides whether — only where in phase and how strongly. Inverted-
default variant (Chen 2026 spatial computing): standing negative bias
on non-ledger context, released over the scheduled span — the null
action then costs something. Dev replay vs base/oracle/reinsertion;
watch load-smearing at higher ledger sizes (do not hard-partition).

### P3 — Fork-and-judge with KV rollback (policy + label factory)

At proposed press moments (from P1's scorer at aggressive threshold, or
P2's schedule), fork pressed vs unpressed continuations from the same
KV checkpoint to the close of the local syntactic unit; keep the branch
the deterministic checker scores higher. Branch selectors evaluated:
syntax-only, learned (logit/hidden deltas), oracle (ceiling ONLY —
never the reported result). Byproduct: exhaustive per-moment
press-advantage labels — the supervised dataset for a press-utility
head (press only when predicted benefit beats predicted harm by a
calibrated margin). ~10-20 GPU-h pilot; run only if P1 generates
useful-but-unsafe coverage or P2 needs a safety filter.

### P4 — Oscillator-per-memory bakeoff (Brian's proposal, controlled)

Cached-feature contest, equal parameter budgets, no generation until a
winner: (a) independent per-slot complex oscillator bank z_j (identity/
age/urgency in phase, values stay in text); (b) static per-memory
embedding + MLP; (c) leaky/EMA integrator; (d) keyed latch / tiny GRU.
Task: press classification per counterfactual cell. Robustness probes:
insert 0/32/128 inert tokens before decision moments (phase-aliasing
trap); phase-scramble at eval (if scrambling does not hurt, the
oscillator is decorative). PROCEED to generation only if the oscillator
beats ALL non-oscillatory controls and survives both probes; if the
latch ties it, ship the latch and record the tie. Null-oscillator
control from the crossfield lane: free-running periodic pressing with
generator-matched periods must also be beaten (else it is a cron job).

### P5 — Structured-eligibility deployment ceiling (always run; cheap)

No theta, no learned liveness: press iff the parser-timed moment's type
has an active authoritative ledger entry (focus.set/clear provenance).
One dev replay. This is the deployable, security-safe recipe (quoted
text cannot acquire authority) and the ceiling every autonomous policy
is measured against. Product answer regardless of science outcome.

## Frozen rules

- Risk budget: the P0.3-derived (C, p*) replaces zero-false-press in
  every calibration; calibrated thresholds use >=300 negatives (grid +
  binomial bounds; conformal/LTT only where its assumptions hold and
  are stated).
- Seeds: train/calib/dev from fresh 13.0xM blocks (registered at P0
  launch); one sealed val run per surviving policy, judged as-is.
- Every rung reports press counts and paired parse/exec vs base;
  "never/always" claims require direct instrumentation (press-audit
  lesson).
- No script imported by another script does top-level work
  (tests/test_no_side_effect_imports.py enforces).
- Reviews: sol xhigh + fable at (i) this plan before P0 launch,
  (ii) G0, (iii) any registration of a val run, (iv) close. Loop only
  while high/critical findings remain.
- Halting is success: each stop rule closes its line with a full
  autopsy; P5 ships regardless.

## What would count as the program's win

Any autonomous policy (P1-P4) that on sealed validation closes >=0.5 of
oracle headroom at the registered risk budget with paired validity
disclosed — or a clean pair of honest negatives that leaves P5 +
event-triggered pressing as the documented deployment recipe, with the
autonomy boundary mapped as precisely as TIMED-SELECTOR mapped the
constraint boundary.
