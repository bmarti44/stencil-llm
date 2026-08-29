# TIMED-SELECTOR-PLAN — per-moment governance of code generation (GOVERNING; Brian-approved 2026-08-29)

Successor to AGENTIC-PLAN (stopped at its G1 gate: the always-on oracle is
the registered negative). The timed per-moment spotlight is the research
object, entering with unusually strong development evidence: span-specific
(wrong sentence 16 pts below base), time-specific (random moments = no
effect), fresh-seed stable (+22.9), and its sole validity defect traced to
one detector false positive with a verified one-line fix (parse-gated +20.8
at b=4, validity intact). Reviews: results/agentic-g1-review-sol.md,
results/qwen/g1-fable-review-report.json.

## Registered instruments (before any run)

- **AST-based scorer contract**: ast.parse/compile gate; ast.get_docstring;
  per-argument annotation coverage (unannotated args count as
  non-compliant); named target-function policy; deterministic execution
  test of the requested operation (subprocess, timeout); raw generated
  code in every evidence record. Missed moments and invalid code stay in
  denominators. PAIRED validity criterion with registered tolerance:
  parse-rate degradation 0 cases allowed at the selected config.
- **Session-layout randomization**: obligation order, block position, and
  count randomized per session; held-out obligation TYPES in val/final
  (anti-memorization + anti-regex-distillation, per fable's measured trap:
  fixed template offsets let an address head score ~100% contentlessly).
- **Seed spaces**: dev 12.3M, val 12.4M, final untouched 12.5M.
- Determinism setup imported before torch in every script.

## Phases

**T0 — Oracle confirmation under the honest instruments (half day).**
The timed oracle with the opening-quote moment fix, on FRESH dev seeds,
AST scorer, registered grid b in {2,4}. Gates: parse-gated mean compliance
lift >= +15; paired parse-rate degradation == 0; wrong-sentence and
random-moment controls at their measured signatures (harm / no-effect).

**T1 — Learned timing + learned address (the S2-equivalents).**
Timing head over frozen h20 states: labels {none, prefix, doc, hint} from
the structured generator (NOT from the regex; register the label rule);
trained on both base and oracle rollouts; evaluated on OWN rollouts.
Address scorer as in S2 over randomized layouts. Factorial triage arms
(sol's table): off/off, oracle/oracle, learned/oracle, oracle/learned,
learned/learned, always-on/oracle (known destructive control),
shuffled/wrong (non-vacuity). Plus the parser-timed contentless selector
as a named engineering baseline. Gates: moment precision >= 0.95
(precision primary — one false activation breaks syntax), recall >= 0.8;
conditional address accuracy >= 0.9; learned/learned closes >= 0.5 of the
paired base->oracle gain with parse-rate degradation == 0.

**T2 — Scripted-session benchmark (the former G2, inheriting its full
registration list from results/agentic-g1-review-sol.md "What G2 must
register") -> runtime -> registered comparison -> 7B**, each phase gated
as before; T2 is built only after T1 passes.

## Stop conditions
1. T0 misses (the fix does not survive fresh seeds + honest scoring).
2. T1: learned timing cannot reach precision 0.95 after one registered
   capacity fallback, or learned/learned closure < 0.5 with both factorial
   diagnosings pointing at learning (not wiring).
3. Any unregistered rescue. On stop: full autopsy; the SELECTOR program's
   published results stand unaffected (sol: the short-answer/long-
   generation distinction is mechanistically sound).

## T2 CONTRACT (draft for the registered design review — no runs until both
## reviewers clear it)

**Fixture.** One tiny Python module (2-3 stub functions) + the deterministic
AST/exec checker as the "environment" (hash-pinned). No external tools.

**Sessions (fully scripted, seeded).** Turn types: user instruction turns
(add/update/clear obligations: naming, docstring-opener, annotation-type,
plus one process rule), work requests (write/modify a named function),
deterministic environment feedback (checker findings on the previous work
turn, templated), distractor turns (quoting conflicting/superseded values in
prose), and compaction events at fixed turns (context truncated to the last
K turns; what survives is arm policy). Strata: 20/40/60 turns; obligations
accumulate 6-12 with 2-5 updates incl. one reversal; 1-3 compactions.

**Governance opportunities** are emitted by the GENERATOR (which obligations
apply to each work request), independent of any detector. Scoring: AST/exec
checker; missed moments and invalid code count as nonadherent — denominators
never shrink.

**Arms.** base; selector (T1 learned/learned, retrained on T2 train split,
tau recalibrated on calib split then frozen); oracle selector (ceiling);
pinned-ledger prompt; full-ledger re-insertion at each work turn
(token-charged). Compaction-summary baseline DEFERRED (registered: requires
a summarizer policy; revisit at G4-equivalent). Standing controls:
wrong-span, rate-matched random-timing, zero-selector bitwise identity.

**Held-out generality.** Val/final sessions include one obligation type
absent from training (registered: "every function body ends with a comment
'# reviewed'"). Expectation registered NOW: the detector may safely ABSTAIN
on unseen types (scores as base behavior there); a false press is a
failure. Precision stays primary.

**Metrics.** Per-opportunity adherence (micro) + per-session macro;
stale-action rate (obeying a superseded obligation); conflict adoption;
parse/exec validity (paired); cumulative prompt tokens per arm; activation
rate; per-example JSON with full transcript, ledger states, activations,
and checker results.

**Gates.** (1) selector closes >= 0.5 of the base->oracle adherence gap on
val; (2) cost-adjusted: selector adherence >= re-insertion adherence - 2pts
at <= 50% of its cumulative prompt tokens, OR beats it outright; (3) paired
parse loss == 0; (4) stale-action rate <= half of base's. Final untouched
seeds only if val gates pass.

**Seeds.** dev 12.6M / train 12.65M / calib 12.7M / val 12.75M / final
12.8M (untouched).

**Stop.** Gates missed after one registered tau/dose recalibration => stop;
autopsy; T0/T1 results stand.
