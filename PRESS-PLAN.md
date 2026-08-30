# PRESS-PLAN v2 — making autonomous press timing work

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

H1. Span-level address API: the selector-arm address callable returns an
    exact token span (or NULL); the runner applies THAT span verbatim.
    The type->authoritative-span redirect survives as the separately
    named "structured" arm (deployment baseline, in every replay).
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
- negative fixtures: 13,060,000+i, i<160 (component false-selection
  trials; independence unit = SESSION: a trial fails if any false
  selection occurs in it; 0/160 -> U95 = 1-0.05^(1/160) = 1.86%)
- dev replay: 13,100,000+i, i<24
- sealed validation: 13,200,000+i, i<96 (one named autonomous finalist
  only, chosen at the pre-val review; all other policies are
  exploratory — multiplicity is handled by naming, not by testing many)

## Registered ladder

### T0 — Trace + diagnostics (one GPU trace pass, then offline)

- T0.1 TRACE PASS (GPU, deterministic): replay base + selector arms on
  the trace seeds with H1-H4 in place. Per candidate event store: h20
  state, timing logits, every candidate span with source label
  (live/superseded/distractor), all registered score variants, chosen
  candidate, rejection reason, counterfactual cell. This is the input
  to everything offline. (Replaces the false "no new GPU runs" claim.)
- T0.2 Score-policy matrix (offline on the trace): raw max, top1-top2,
  top1-logsumexp(rest), normalized cosine, live-minus-best-same-type
  (provenance CEILING), structured eligibility. Metric registered for
  G0: recall on active events at the threshold where session-level
  U95(false selection) <= 5% on the negative fixtures, computed
  select-then-bound (score family chosen on trace sessions; the bound
  evaluated on the untouched fixture block). Tie-break: higher AUPRC
  (active vs all). CEILING FAILURE := provenance-ceiling recall < 0.50
  at that same bound.
- T0.3 Per-press cost/benefit (GPU, paired single-intervention
  rollouts): from a common prefix, one rollout with exactly ONE press
  and one without, to the end of the work; over >=200 paired events per
  condition (correct-span-correct-moment, wrong-span, wrong-moment)
  measure per-press benefit B and per-press harm H on the same unit
  (adherence of that work's opportunities; parse/exec deltas reported
  alongside, converted only by a utility weight registered BEFORE the
  runs: 1 broken work = 2 adherence misses). p* := H/(B+H), symbolic —
  src/stencil/press_stats.py takes B,H as required inputs, no default
  constants. If B <= 0 the mechanism claim itself is re-examined before
  proceeding.
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
  no-ops). Arms: base, reactive (learned-free), reactive-oracle ceiling
  (same trigger, oracle moments — bounds what reactivity CAN recover),
  structured. Report conditional recovery on the eligible denominator
  AND whole-session lift; per-cell metrics on pressed turns reported
  separately (spillover disclosure). Label: controller-visible
  triggering (feedback may be compacted out of the model window).

GATE G0 (mechanical): let R_auto = best autonomous family's T0.2 recall,
R_ceil = provenance-ceiling recall, both at the registered bound.
- R_ceil < 0.50: representation lacks the signal -> skip T1; go to T2
  bakeoff + T3 with the structured arm as champion.
- R_ceil >= 0.50 and R_auto >= 0.5*R_ceil: proceed to T1 with that
  family.
- R_ceil >= 0.50 and R_auto < 0.5*R_ceil: run the DEFERRED attention-
  mass scan (one instrumented pass; qwen3.py last-row attention summary
  registered as a harness change then) as the one additional family; if
  it also misses 0.5*R_ceil, skip T1 as above.
T0.5 decision (mechanical, on conditional recovery of the reactive arm
as a fraction of the reactive-oracle ceiling): >=0.5 -> reactive
pressing is a registered component of the final recipe; <0.5 ->
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
level U95(false selection) <= 5% on the untouched negative fixtures;
positive lookalike margin on >=90% of active events.

Behavioral decision table (24-session dev replay; closure computed from
raw paired numerators on identical seeds, never rounded rates):
- Precondition: oracle-base headroom >= 0.10 on these seeds, else
  INCONCLUSIVE (headroom does not bind; no verdict about the scorer).
- closure >= 0.50 AND paired-validity harm within the T0.3 budget:
  PASS -> T1 finalist candidate.
- closure in [0.25, 0.50): ONE registered fallback — retrain once with
  hard-negative reweighting (weight 4x, preregistered), re-judge
  against the same table; no second fallback.
- closure < 0.25 (or fallback misses): the discriminative-scorer line
  CLOSES (honest negative); T2/T3 continue as separate lines.

### T2 — Controller-state bakeoff (head-only; Brian's oscillator,
controlled; runs regardless of T1)

Equal-parameter contenders on recomputed trace features: (a) per-slot
complex oscillator bank; (b) static per-memory embedding + MLP; (c)
leaky/EMA integrator; (d) keyed latch / tiny GRU; (e) null-oscillator
(free-running periodic, generator-matched periods). Task: press
classification per counterfactual cell. Robustness: insert 0/32/128
inert tokens before decision moments; phase-scramble at eval.
Mechanical verdict: the oscillator PROCEEDS to a generation pilot only
if it beats ALL of (b)-(e) on the T0.2 metric and degrades <10% rel.
under both probes; a tie (within the metric's fixture-level U95) with
the latch ships the latch and records the tie.

### T3 — Rhythm-default press (generation pilot; only after T2 verdict)

Shared scheduler period T in {4,8} steps, raised-cosine envelope; per
live entry a phase offset and gain (magnitude from the T0.3 harm
curve); slot assignment from the T2 winner (or round-robin if T2 ships
the latch). Gate: dev replay closure >= 0.25 at the T0.3 validity
budget else the line closes. Inverted-default variant only if the plain
rhythm passes. Full objective/grids get fresh preregistration + review
before launch (registered promise, sol finding 6).

### T4 — Fork-and-judge (conditional; only if T1 or T3 produce
useful-but-unsafe coverage, defined as recall >= 0.5*R_ceil but
validity harm > the T0.3 budget)

Deterministic prefix-recomputation forks (Qwen3.forward has no KV
cache; "rollback" = re-decode from the fork point, deterministic
greedy). Fork at proposed presses, decode both branches to the close of
the local syntactic unit (registered boundary: the earliest of
def-name end / docstring close / annotation end, via the existing
parser), select by syntax-only verifier first; learned verifier and
oracle ceiling as comparison arms (oracle never the reported result).
Byproduct: per-moment press-advantage labels.

### Structured arm (in EVERY replay from T0 on)

Press iff the parser-timed moment's type has an active authoritative
ledger entry (provenance from the session state). The deployable,
security-safe recipe and the ceiling all autonomous arms are judged
against. Ships regardless of science outcome.

## Frozen rules

- Risk policy: gates use U95(session-level false-selection rate) <= 5%
  on independent negative fixtures — the exact Clopper-Pearson one-sided
  bound from the OBSERVED count (k > 0 allowed; 0/160 gives 1.85%,
  k=3/160 gives 4.77%, k=4/160 gives 5.63% and fails; computed by
  src/stencil/press_stats.py, test-pinned). Behavioral
  validity harm is judged against the T0.3 per-press budget. Zero-FP
  appears nowhere as a gate.
- One sealed validation (13.2M seeds) for one named finalist; judged
  as-is; a miss closes the program per its line's table.
- Every replay reports applied press counts (H2 logs) and paired
  parse/exec vs base.
- No top-level work in imported scripts (test enforced). All new
  helpers TDD'd red-first.
- Reviews: sol + fable at (i) this v2 before harness work [round 2],
  (ii) G0, (iii) T1/T3 preregistration details, (iv) pre-validation
  finalist naming, (v) close. Loop only while high/critical remain.
- Halting is success; every closed line gets an autopsy in WORKLOG.

## Program verdicts

WIN: a named autonomous policy closing >= 0.5 of oracle headroom on
sealed validation within the T0.3 validity budget. HONEST MAP: the
discriminative, rhythm, and state lines each closed by their tables,
leaving structured + event-triggered pressing as the documented recipe
with the autonomy boundary quantified from both sides.
