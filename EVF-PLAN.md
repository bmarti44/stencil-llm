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
