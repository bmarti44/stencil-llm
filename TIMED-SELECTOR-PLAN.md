# TIMED-SELECTOR-PLAN — per-moment governance of code generation (DRAFT, pending Brian's go)

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
