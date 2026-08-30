# PRESS-PLAN v3.2 — making autonomous press timing work

Governing plan for the post-TIMED-SELECTOR program. Question: can the
WHEN-to-press decision be made autonomous, now that the mechanism
(spotlight, +14.5 val) is proven and the failure is precisely
diagnosed?

v2 after review round 1 (sol NOT CLEARED 6 HIGH, fable NOT CLEARED
3 HIGH; results/press-plan-review-sol.md + fable transcript in WORKLOG).
Changelog: honest trace-collection rung replaces the "no new GPU runs"
claim; span-level address API registered (the old harness silently
redirected any selected type to the authoritative span — autonomous
wrong-candidate selection was unexpressible, and "WHERE proven 130/130"
is downgraded to a calibration-set claim pending the theta/out-of-ledger
rejection split); symbolic p* from paired single-press B/H (constants
removed); complete decision tables; session-level independence units;
concrete seed freeze; structured baseline folded into every replay;
bakeoff promoted ahead of generation-heavy rungs; P0.2 deferred; beta
sweep demoted; old 12.96M/941-fire data demoted to legacy exploration.

v3 after review round 2 (sol 6 HIGH, fable 3 HIGH + mediums, both NOT
CLEARED; results/press-plan-review2-sol.md + WORKLOG). Changelog: the
validity BUDGET is now one registered formula (T0.3) cited by every
gate; p* demoted to a reporting quantity (scores are not calibrated
probabilities — operating thresholds maximize Delta-U on selection data);
negative fixtures split select/certify (threshold chosen on trace
negatives, certified ONCE per policy on block A; block B reserved for
post-G0 finalists); T0.5's ceiling replaced (it equaled its own test arm
by construction) with the full-oracle arm restricted to the same
eligible denominator + headroom precondition; T2 phase-scramble
criterion inverted (a real phase code MUST degrade >=20% when scrambled;
<10% only for inert-token insertion) and the tie made computable (0.02
absolute recall); sealed validation gains the same headroom>=0.10
precondition as dev with closure defined from raw paired numerators; T4
requires a registered incremental boundary detector (none exists today)
inside its own preregistration; H1 registers the full callable contract
(span-or-NULL + diagnostics; guards applied and logged by the runner);
T1 table completed (high-closure/over-budget cell -> T4 trigger;
INCONCLUSIVE gets one reserve re-draw then closes); rounding and test
fixture labels corrected.

v3.1 after review round 3 (fable CLEARED; sol 2 HIGH): certification is
one-policy-per-block — G0 compares on trace only and certifies the one
pre-named winner on block A; adaptive successors consume fresh reserve
blocks (C/D pool); the certification failure event is defined
pre-structural-guard; T0.5 gets its subtraction formula
(recovery_closure over a frozen base-arm eligible set) with the
headroom precondition on that exact denominator; the earlier
Bonferroni-over-families rule is superseded by one-policy-per-block.

v3.2 after review round 4 (sol 2 HIGH): T0.1 is trace-only — every
certification is one sealed collection+bound job run after its policy
is named (block A was previously replayed before naming); the
provenance ceiling certifies on its own block C (its R_ceil sets G0's
bar); T0.5's metric moved from the violation IDs to each episode's
DOWNSTREAM SET (all later active opportunities of the violated type,
frozen from the base arm) — the old formula scored opportunities the
reactive arm could never repair.

Grounding: results/timed-selector-report.md,
results/research-timing-{design-sol,neuro-fable,ml-fable,crossfield-fable}.md.
Harness: frozen Qwen3-1.7B, T2b generator (interference="s0"), existing
scorers; h20 features are RECOMPUTED by forward passes (no feature cache
exists on disk).

## Diagnosis being attacked

1. Zero-false-press is the Neyman-Pearson alpha=0 corner: for an
   imperfect score the only feasible policy is "never press" (observed
   14/14794). It asserted infinite false-press cost; the true per-press
   cost is unknown (the oracle arm's 7/409 parse-lost is a per-WORK
   policy aggregate, not a per-press cost) and will be measured (T0.3).
2. The controller was untrainable by construction: timing labels from
   syntax alone; the address head never saw a null case; 0/18 bounds
   false-press only at 15.3% (one-sided 95%).
3. Deterministic checker feedback is a free error signal no arm
   consumes.
4. Biology never learns "when" as a free binary under asymmetric
   penalty: default rhythms + learned phase/gain; opponent Go/NoGo with
   post-hoc criterion; event-triggered detectors.

## Harness registration (before any rung; red/green TDD)

H1. Span-level address API: the selector-arm policy callable returns
    (candidate_span | None, diagnostics) where diagnostics carries the
    raw scores and candidate set; the RUNNER applies the registered
    guards (threshold, ledger-membership) to the returned candidate,
    applies the surviving span verbatim, and logs the guard verdict —
    guards no longer live inside the callables. The
    type->authoritative-span redirect survives as the separately named
    "structured" arm (deployment baseline, in every replay).
H2. Press-event logging in the runner: per generation step record
    pre-guard decision (candidate or NULL), guard rejections split by
    reason (below-threshold vs out-of-ledger), applied presses, and the
    applied span. "Never/always" claims must cite these records.
H3. Wrong-span non-vacuity test: a fixture proving a deliberately wrong
    span is actually applied and actually changes logits (exact-zero
    lesson: vacuous instrumentation fails loudly).
H4. Trace writer: the T0.1 pass persists per-event records (below).

## Frozen seeds (registered now; 12.9xM blocks incl. the 941-fire audit
are LEGACY EXPLORATION — never evidence)

- trace/train: 13,000,000+i, i<48 (dev split)
- calibration: 13,030,000+i, i<24
- negative fixtures block A: 13,060,000+i, i<160 (G0-stage
  certification; independence unit = SESSION: a trial fails if any
  false selection occurs in it; 0/160 -> U95 = 1.85%). Single-use:
  thresholds are SELECTED on trace-session negatives, then certified
  ONCE per policy on this block at the frozen threshold — a failed
  certification fails that policy, no re-tuning on the block.
- negative fixtures block B: 13,070,000+i, i<160 (T1 finalist's
  component gate — one policy)
- negative fixtures block C: 13,080,000+i, i<160 (the provenance
  CEILING's certification — its R_ceil sets G0's bar and the ceiling-
  failure branch, so it certifies like any policy, on its own block)
- reserve fixture pool: blocks D 13,090,000+i and E 13,095,000+i,
  i<160 each. RULE (v3.1/v3.2): every certification covers exactly ONE
  policy, named in WORKLOG before its block is touched, and runs as one
  sealed collection+bound job; adaptively-designed successors (G0's
  attention fallback, T1's retrained fallback, the T2 winner) each
  consume a fresh block from the pool; when the pool is empty, further
  certifications require a registered pool extension (13,300,000+)
  recorded before use
- dev replay: 13,100,000+i, i<24; reserve dev block: 13,110,000+i,
  i<24 (used only by T1's INCONCLUSIVE re-draw)
- sealed validation: 13,200,000+i, i<96 (one named autonomous finalist
  only, chosen at the pre-val review; all other policies are
  exploratory — multiplicity is handled by naming, not by testing many)

## Registered ladder

### T0 — Trace + diagnostics (one GPU trace pass, then offline)

- T0.1 TRACE PASS (GPU, deterministic): replay base + selector arms on
  the TRACE SEEDS ONLY, with H1-H4 in place. Fixture blocks are never
  touched here: each certification (block A included) is one sealed
  job — collection + bound computation together — run only AFTER its
  single policy is named in WORKLOG (v3.2 ordering fix). Per candidate event store: h20 state, timing
  logits, every candidate span with source label
  (live/superseded/distractor), all registered score variants, chosen
  candidate, rejection reason, counterfactual cell. This is the input
  to everything offline. (Replaces the false "no new GPU runs" claim.)
- T0.2 Score-policy matrix (offline on the trace): raw max, top1-top2,
  top1-logsumexp(rest), normalized cosine, live-minus-best-same-type
  (provenance CEILING), structured eligibility. For each family, the
  operating threshold is SELECTED on trace-session negatives (no
  guarantee claimed there). The G0 comparison (recall, tie-break) runs
  ENTIRELY on trace data; then exactly ONE winning family — named in
  WORKLOG before block A is touched — is certified once on block A:
  session-level U95(false selection) <= 5%. FAILURE EVENT definition
  (applies to every certification): any non-NULL decision surviving the
  numeric threshold BEFORE the ledger-membership guard — the structural
  guard may not trivialize certification. If the named family fails
  certification, that family is dead; the runner-up may be certified on
  a FRESH reserve block only. G0 metric: recall on active trace events
  at the certified
  threshold. Tie-break: higher AUPRC (active vs all). CEILING FAILURE
  := provenance-ceiling recall < 0.50 at its certified threshold.
- T0.3 Per-press cost/benefit (GPU, paired single-intervention
  rollouts): from a common prefix, one rollout with exactly ONE press
  and one without, to the end of the work; >=200 paired events per
  condition (correct-span-correct-moment, wrong-span, wrong-moment).
  REGISTERED UTILITY (the definition every later gate cites):
    U(work) := (# adherent active opportunities in the work)
               - 2 * BROKEN(work),
    BROKEN(work) := 1 if the pressed/policy branch loses parse OR exec
    relative to its paired unpressed/base branch, else 0.
  Outputs: B := mean paired Delta-U per correct-span/correct-moment
  press; H := mean paired Delta-U LOSS per press, pooled over the
  wrong-span and wrong-moment conditions weighted by their observed
  frequencies in the trace. p* := H/(B+H) is a REPORTING quantity only
  (raw scores are not calibrated probabilities); operating thresholds
  are always chosen by maximizing total Delta-U on selection data.
  VALIDITY RULE (the "T0.3 budget" used by T1/T3/T4/validation): a
  replay passes iff, from raw paired numerators,
    Delta-U_total >= 0.8 * (adherence gain vs base),
  i.e. validity losses erode at most 20% of the adherence gain, AND
  Delta-U_total > 0. If B <= 0 the mechanism claim itself is
  re-examined before proceeding.
- T0.4 Theta sweep on the trained selector (GPU dev replays, ~5 points
  below registered theta): adherence + paired validity vs applied press
  rate (from H2 logs). Purpose: was the collapse the constraint or the
  representation?
- T0.5 Event-triggered baseline (GPU dev replay, no learning): rule —
  when checker feedback flags moment class c at env turn e, press
  type-c parser-timed moments (_oracle_moment) on subsequent work turns
  while c remains active-in-ledger; per-type refractory: stop after the
  first later work turn scores c adherent; update/clear resets the
  trigger. Registered denominator: violations with >=1 later active
  opportunity of the same type (last-turn violations are recorded
  no-ops). Arms: base, reactive (learned-free), full oracle (the
  existing per-moment oracle arm — its conditional recovery RESTRICTED
  to the same eligible denominator is the ceiling; v3 fix: the old
  "reactive-oracle" ceiling was the test arm itself), structured.
  Precondition: oracle-base headroom >= 0.10 on these seeds, else the
  rung is INCONCLUSIVE. Report conditional recovery on the eligible
  denominator AND whole-session lift; per-cell metrics on pressed turns
  reported separately (spillover disclosure). Label: controller-visible
  triggering (feedback may be compacted out of the model window).

GATE G0 (mechanical): let R_auto = best autonomous family's T0.2 recall,
R_ceil = provenance-ceiling recall, both at the registered bound.
- R_ceil < 0.50: representation lacks the signal -> skip T1; go to T2
  bakeoff + T3 with the structured arm as champion.
- R_ceil >= 0.50 and R_auto >= 0.5*R_ceil: proceed to T1 with that
  family.
- R_ceil >= 0.50 and R_auto < 0.5*R_ceil: run the DEFERRED attention-
  mass scan (one instrumented pass; qwen3.py last-row attention summary
  registered as a harness change then) as the one additional family —
  certified on a FRESH reserve block, never block A; if it reaches
  0.5*R_ceil at that certified threshold, proceed to T1 with it; if it
  also misses, skip T1 as above.
T0.5 decision (mechanical; only if its precondition held). Frozen from
the BASE arm alone (v3.2): each base-arm violation episode (type c
violated at work turn w, feedback at the next env turn e) maps
deterministically to its DOWNSTREAM SET — every active opportunity of
type c at work turns after e in the session (all-later, registered;
the reactive arm's refractory shapes its pressing, never the metric).
The eligible evaluation set is the union of downstream sets over
episodes with a nonempty downstream set; every arm is scored on
exactly those opportunity IDs. With A_x := raw adherent count of arm x
on that set,
  recovery_closure := (A_reactive - A_base) / (A_oracle - A_base),
precondition (A_oracle - A_base) / |set| >= 0.10 on this exact
denominator, else INCONCLUSIVE. recovery_closure >= 0.5 -> reactive
pressing is a registered component of the final recipe; < 0.5 ->
recorded negative; no middle band.

### T1 — Joint candidate-or-null scorer (head-only training)

Listwise softmax over [NULL, cand_1..cand_n] (normalized query-key +
null head over h_t); targets: governing entry at active opportunities,
NULL everywhere else (ordinary tokens, obligation-free syntax moments,
cleared/stale-only, distractor-only); margin term vs the strongest
same-type lookalike (hard negatives mined from the trace). Features
recomputed h20 (trunk frozen).

Component gates (on trace/calib, before any generation): conditional
address >=90% on active events with the span-level API (this also
finally measures WHERE autonomously); recall >= 0.5*R_ceil; session-
level U95(false selection) <= 5% certified once on fixture block B;
positive lookalike margin on >=90% of active events.

Behavioral decision table (24-session dev replay; closure :=
(adherent_policy - adherent_base) / (adherent_oracle - adherent_base)
from raw paired numerators on identical seeds, never rounded rates):
- Precondition: oracle-base headroom >= 0.10 on these seeds, else
  INCONCLUSIVE -> one re-draw on the reserve dev block (13.11M); if
  headroom still < 0.10 there, the discriminative line closes as
  headroom-unbound (environment no longer supports the failure regime).
- closure >= 0.50 AND the T0.3 validity rule passes: PASS -> T1
  finalist candidate.
- closure >= 0.25 AND the validity rule FAILS ("useful but unsafe"):
  NOT a finalist; this is T4's registered trigger.
- closure in [0.25, 0.50) with validity passing: ONE registered
  fallback — retrain once with hard-negative reweighting (weight 4x,
  preregistered), re-judge against this same table; no second fallback.
- closure < 0.25 (or the fallback lands below 0.50 without triggering
  T4): the discriminative-scorer line CLOSES (honest negative); T2/T3
  continue as separate lines.

### T2 — Controller-state bakeoff (head-only; Brian's oscillator,
controlled; runs regardless of T1)

Equal-parameter contenders on recomputed trace features: (a) per-slot
complex oscillator bank; (b) static per-memory embedding + MLP; (c)
leaky/EMA integrator; (d) keyed latch / tiny GRU; (e) null-oscillator
(free-running periodic, generator-matched periods). Task: press
classification per counterfactual cell. Robustness probes (v3 — the
directions differ by design): inert-token insertion (0/32/128 tokens
before decision moments) must degrade the oscillator's metric < 10%
relative (a press schedule must not depend on arbitrary token count);
phase-scramble at eval must degrade it >= 20% relative (a genuine phase
code MUST be hurt by scrambling — < 20% means the phase is decorative
and the claim fails regardless of ranking). Mechanical verdict: the
oscillator PROCEEDS to a generation pilot only if it beats ALL of
(b)-(e) on the T0.2 metric by > 0.02 absolute recall AND passes both
probes; within 0.02 of the best non-oscillatory contender is a
registered TIE -> ship that contender and record the tie; every other
outcome (oscillator loses by > 0.02, or wins but fails a probe) ships
the best non-oscillatory contender. T2's full
details (dimensions, parameter matching, optimizer, exact paired
comparison) get their own preregistration + review before launch.

### T3 — Rhythm-default press (generation pilot; only after T2 verdict)

Shared scheduler period T in {4,8} steps, raised-cosine envelope; per
live entry a phase offset and gain (magnitude from the T0.3 harm
curve); slot assignment from the T2 winner (or round-robin if T2 ships
the latch). Gate: dev replay closure >= 0.25 AND the T0.3 validity rule
passes, else the line closes. Inverted-default variant only if the
plain rhythm passes. Full objective/grids get fresh preregistration +
review before launch (registered promise, sol finding 6).

### T4 — Fork-and-judge (conditional; registered trigger = a T1 or T3
dev replay with closure >= 0.25 whose T0.3 validity rule FAILS)

Deterministic prefix-recomputation forks (Qwen3.forward has no KV
cache; "rollback" = re-decode from the fork point, deterministic
greedy). Fork at proposed presses, decode both branches to the close of
the local syntactic unit, select by syntax-only verifier first; learned
verifier and oracle ceiling as comparison arms (oracle never the
reported result). NO online boundary detector exists today
(_oracle_moment detects unit BEGINNINGS; ast_moments needs completed
code): T4's own preregistration must register and TDD a deterministic
incremental end-of-unit detector before launch — T4 cannot start
without that review. Byproduct: per-moment press-advantage labels.

### Structured arm (in EVERY replay from T0 on)

Press iff the parser-timed moment's type has an active authoritative
ledger entry (provenance from the session state). The deployable,
security-safe reference baseline reported beside every autonomous arm
(closure itself is defined against the oracle). Ships regardless of
science outcome.

## Frozen rules

- Risk policy: gates use U95(session-level false-selection rate) <= 5%
  on independent negative fixtures — the exact Clopper-Pearson one-sided
  bound from the OBSERVED count (k > 0 allowed; 0/160 gives 1.85%,
  k=3/160 gives 4.77%, k=4/160 gives 5.63% and fails; computed by
  src/stencil/press_stats.py, test-pinned). Fixture blocks are
  single-use per policy (select on trace negatives, certify once).
  Behavioral validity is judged by the T0.3 VALIDITY RULE
  (Delta-U_total >= 0.8 * adherence gain, and > 0). Zero-FP appears
  nowhere as a gate.
- One sealed validation (13.2M seeds) for one named finalist; judged
  as-is; a miss closes the program per its line's table. Validation
  precondition mirrors dev: oracle-base headroom >= 0.10 on the val
  seeds from raw numerators, else the validation is INCONCLUSIVE and
  the program closes without a win claim (no reseeding). Closure on
  val uses the same registered formula as T1's table.
- Every replay reports applied press counts (H2 logs) and paired
  parse/exec vs base.
- No top-level work in imported scripts (test enforced). All new
  helpers TDD'd red-first.
- Reviews: sol + fable at (i) this plan before harness work [round 3
  reviews v3], (ii) G0, (iii) T1/T2/T3/T4 preregistration details,
  (iv) pre-validation finalist naming, (v) close. Loop only while
  high/critical remain.
- Halting is success; every closed line gets an autopsy in WORKLOG.

## Program verdicts

WIN: the named autonomous finalist, on a sealed validation whose
headroom precondition holds, reaches closure >= 0.50 (registered
formula, raw numerators) with the T0.3 validity rule passing. HONEST
MAP: the
discriminative, rhythm, and state lines each closed by their tables,
leaving structured + event-triggered pressing as the documented recipe
with the autonomy boundary quantified from both sides.
