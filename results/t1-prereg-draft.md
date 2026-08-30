# T1 PREREGISTRATION v3 — post checkpoint-iii reviews (2026-08-30)

v1 reviews: fable CLEARED conditional on the NULL-gate rewrite (its
arithmetic: 95% event-level implies 16-54 expected failed sessions of
160 — a gate-passing policy would predictably burn the block); sol NOT
CLEARED with 4 HIGH (s0x2 continuity pretest; trace rows lack candidate
features; objective must train candidate-vs-NULL; gate denominators +
block accounting). All folded below. Fable's h20 probe (grouped-CV AUC
0.995-0.999 active-vs-inactive on trace events) is cited as supportive
motivation only — it cannot confirm survival under lookalike
interference; that is what train-hard supplies.

## Rulings

R1. raw_max on a fresh block: SKIPPED/UNTESTED as a burden-test
decision — NOT an empirical negative (block D saved no raw scores; its
failure is established for cos_max only).

R2. Fixture amendment s0x2 (certification + train-hard/calib-hard
blocks): every work-turn task text appends "Include a one-line
docstring and type-annotate both arguments." Moment generation becomes
task-structural; obligation VALUES remain ledger-governed; the suffix
matches no CAND_PATTERN (verified) so it creates no pressable span.
Disclosures: feedback text can differ between s0x and s0x2 beyond the
suffix (nothing counted reads it); dev/val stay unextended.

R2-PRETEST (registered, before any training): score the FROZEN failed
cosine policy (threshold 0.6407741904258727) offline on the train-hard
base-arm features. Gates (v3 — every assertion miss is a certification
failure, so coverage must be total): (a) assertion-hit 48/48 train-hard
sessions (hence 16/16 per target type) and 24/24 on calib-hard before
any component metric; (b) pressure: the old policy false-selects in
>= 10/48 train-hard sessions. If EITHER fails, redesign and re-register
s0x2 before training (no training fallback exists for fixture defects).

## T1 frozen recipe

Data:
- train-hard: 13,120,000+i, i<48, s0x2, base-arm rollouts (one GPU
  collection pass; collector pinned; data digest recorded);
- calib-hard: 13,140,000+i, i<24, s0x2 (gates only);
- 13.00M trace rows: RECOMPUTED with the pinned trunk to add pooled
  candidate features + authoritative ledger spans (the stored rows lack
  both — sol HIGH; collector + digest pinned; same seeds, no new
  information).
Events: every timing-head fire. Labels are span-provenance: the live
candidate index iff the type is active AND its authoritative span is
among candidates; NULL otherwise. No-candidate rows carry no loss and
are excluded from every NULL metric (structural abstentions reported
separately).

Architecture (frozen): listwise softmax over [NULL, typed candidates];
candidate logit = cos(q(h20), k(cand)) / T with T = softplus(t),
t init = softplus_inverse(1) = 0.5413248546 (so T starts at exactly
1.0); q, k, NULL head, and t are ALL trainable; q/k are 64-d linear
maps WARM-STARTED from the pinned legacy Wq/Wk (registered choice);
NULL logit = linear head on h20, zero-init. Optimizer: Adam(lr=1e-3,
betas 0.9/0.999, eps 1e-8, no weight decay), 30 epochs, batch 256,
shuffle generator seed 0.

DEPLOYED DECISION RULE (frozen, runner-compatible):
  best = argmax over candidate logits (candidate ties -> first index);
  decision_score = logit(best) - logit(NULL);
  decision_score > 0 -> return best's span; else NULL.
  The runner's numeric threshold is 0 on decision_score; NULL wins
  exact ties. This is the score certification and replay both use.

Loss: CE + decision-aligned hinge margins in LOGIT space (weight 1.0):
- active rows: logit(live) >= max(logit(NULL), strongest non-live
  candidate logit) + 0.1;
- inactive hard-negative rows: logit(NULL) >= strongest candidate
  logit + 0.1;
- no margin on no-candidate rows.
(The v1 live-vs-lookalike-only margin trained the solved boundary; this
trains the measured one — sol HIGH.)

Component gates on calib-hard (screens, NOT certification predictors —
even 0/24 clean sessions bounds only U95 = 11.7%; the sealed job is the
proof):
- conditional address >= 90% on active events (span-provenance);
- active recall >= 0.41640866873065013 (= 0.5 * trace-derived R_ceil
  0.8328173374613003; the ceiling was never sealed-certified on block C
  — that dependency is RETIRED under the burden test; the floor is
  frozen as a trace-derived screening threshold, not a certified
  ceiling);
- ZERO NULL errors, session-stated: 0 of 24 calib-hard sessions may
  contain an above-threshold non-NULL selection at an inactive-type
  moment, where the NULL denominator is inactive events WITH >= 1
  same-type non-live candidate and NO authoritative candidate;
- the decision-margin gate: the FULL registered 0.1 margin satisfied on
  >= 90% of active rows AND >= 90% of inactive hard-negative rows
  (supersedes the v1 lookalike-margin gate — explicit supersession).

FALLBACK AND BLOCK TABLE (mechanical; ONE fallback total — the 4x
inactive-hard-negative-reweight retrain — consumable exactly once):
- Pretest failure -> redesign + re-register s0x2; no training fallback.
- Initial component-gate failure -> consume the fallback; if it passes
  the gates, certify IT on still-untouched block B; if it also fails
  the gates, the line CLOSES.
- Initial gates pass, block-B certification FAILS -> the line CLOSES
  immediately (no second certification; conservative choice registered
  now).
- Block-B pass, behavioral replay lands in [0.25, 0.50) with validity
  passing -> consume the fallback; certify it on block E BEFORE its
  replay; then its replay verdict is terminal.
- Any miss after the fallback is consumed -> the line CLOSES.
Certification jobs: sealed, fail-closed, s0x2, N=160,
provenance-by-span, policy named in WORKLOG before touching its block.
13,300,000+ extensions only for later registered policies (one per
block).

PASS + behavioral pass -> finalist per the registered T1 table. Line
closure -> autonomous hopes ride on T2/T3.

## Unchanged
T0.3 validity rule; T0.4/T0.5 rungs; dev/val seeds; all G0 amendments
not explicitly superseded above.

## AMENDMENT A1 — certification semantics (2026-08-30; sol CLEARED in
substance, fable CLEARED with edits E1-E7; supersedes the
assertion-as-failure language above and in PRESS-PLAN)

- Certification FAILURE = false selection only: an above-threshold
  non-NULL decision whose chosen span lies outside every authoritative
  ledger sentence span, at any fire, any work turn. Block B passes iff
  CP_U95(k_false, 160) <= 5% (k_false <= 3).
- HAZARD_COVERAGE (exact definition): a session counts once iff at the
  targeted work turn there is a fire with timing_prob > tau, predicted
  type == target type, >= 1 same-type candidate, and no same-type
  candidate authoritative. Gate on the CERTIFICATION block only:
  n_h >= 112/160 (floor 0.70 — fable's variance analysis: 0.75 carried
  a ~1-in-3 void risk at measured true coverage 0.764; sol's 120
  superseded by this quantitative argument, ack requested). Coverage
  gate failure => certificate VOID FOR VACUITY: block consumed, fixture
  verdict, NOT a policy negative, NOT line closure.
- The certified bound is MARGINAL over hazard exposure and must be
  stated so; the certificate additionally reports k_h/n_h and its
  one-sided CP U95 (reported, not gated), and disclosures: (i) all
  reference-policy false selections occurred AT the target hazard —
  no-hazard sessions contributed no observed pressure (the old
  "still test general false selection" rationale is retired as
  empirically false); (ii) coverage is a property of the certified
  closed-loop rollout, not the fixture alone (frozen trigger; training
  touches only q/k/NULL/t — no gradient channel; graded LOW).
- Calib-hard gates: NO coverage floor (n=24 is statistically
  meaningless for one); exact reporting required; the zero-NULL-error
  gate's denominator is CONDITIONED on hazard-facing sessions with
  n_h >= 12 required for the gate to count (as registered it was
  effectively 0-of-17, U95 ~16%, disclosed).
- Pretest gates 48/48 and 24/24 RETIRED; observed values preserved as
  evidence, not recollected: train 38/48 assertion / 30/48 pressure,
  calib 17/24 / 14/24. Corrections of record (fable E1): 46/48 targeted
  works parse — 2 of the 10 missing train sessions (13120021, 13120045)
  fail parse; the per-session-variance diagnosis holds for 8/10.
- Certificate wording: fable's registered template (its review, section
  4) is adopted verbatim with values filled at run time.
