# SLAB-2 Amendment 6 + fresh rerun for gpt-6-astra (2026-09-07): fix the indentation failure, then re-run

BRIAN HAS AUTHORIZED THIS: "fix the indentation issue and rerun". The frozen 64-episode result (SHA 95fa7fc0)
STANDS as FAIL and is never rescored, never reinterpreted, and its bank is spent. This is a SUCCESSOR with a new
recipe, a new bank and an honest lineage. Read results/larger-test/RESULTS.md and its addendum,
results/larger-test-review-opus.md and results/larger-test-review-astra.md before anything else.

WHAT ACTUALLY BROKE (from the literal outputs both reviews quote; fix THIS, not a paraphrase of it):
every non-write in the run was an indentation SyntaxError - R 48, T 51, N 2 - and 9 of the 10 differential-breakage
episodes first failed exactly on their indent-change round. The literal shapes are (a) INTERNAL inconsistency inside
one function, e.g. a docstring at four spaces followed by a body at two spaces; and (b) a top-level `def` emitted
with leading indentation, e.g. `"    return x\n\n  def step_3(x):"`, giving "unindent does not match any outer
indentation level". So the model, told to change indent width, produces HYBRID output against its four-space prior,
and sometimes indents a top-level definition. Note that Python permits different widths in different functions, so
this is not merely a conflict with untouched code.

PART 1 (CPU) - register "SLAB-2 Amendment 6" in tests/fixtures/slab2_cpu_report.md BEFORE any code, then:
1. SCOPED EDIT PROTOCOL (both reviewers' converged fix): the model emits only the function it is asked to change,
   and the harness splices it at the correct top-level position so a stray leading indent on a `def` cannot occur.
   Arm-neutral: identical protocol and identical instructions for R, N, T and Q.
2. ONE SYNTAX REPAIR TURN, arm-neutral: when a submission does not parse, return the exact interpreter error with
   the offending line, and allow exactly one repair attempt before the round is scored. A real agent gets its
   syntax error back; the frozen run terminally counted it as breakage with no repair path, which is the harness
   being unrealistic rather than the model being incompetent. Count and report repairs used per arm; a round that
   still fails after its one repair is breakage.
3. RE-DERIVE THE HARM CLAUSE PROPERLY, applying your own pilot-7 lesson: any candidate breakage bar must be applied
   to its own NEGATIVE CONTROL at the registered episode unit before being frozen, and must be DEV-calibrated. The
   old bar came from a design memo that disclaims it and was never calibrated. Also make the metric match its own
   definition this time: state explicitly whether semantic test failures are in or out, and use one definition
   everywhere. Brian's objection is registered and must be addressed in the design: an arm that IGNORES a style
   change cannot break the file, so a naive breakage bar penalises exactly the compliance the primary rewards.
   Design the clause so it cannot be satisfied merely by non-compliance - for example, score breakage only on rounds
   where the arm actually attempted the obligation, or report compliance-conditioned breakage - and justify your
   choice in the registration.
4. KEEP THE PRIMARY IDENTICAL so the two runs are comparable: per-obligation adherence at the obligation's change
   round, episode-paired, within-episode averaging before the sign, exact one-sided R > N, Holm over the three
   families, delivery as the predeclared primary. Carry forward the registered caveat that the format family
   tolerates only one adversarial flip before losing significance, and report the cross-run reproducibility control
   again.
5. FRESH EVALUATION BANK: regenerate 64 episodes from the procedural generator with NEW seeds and template
   realizations, mechanically disjoint from the spent bank and from the DEV episodes; assert disjointness and record
   the receipts. Data-lineage line first: fit-on none; development-on the DEV episodes only; evaluated-on the new
   frozen bank, opened once.
6. Tests for every item; run tests/test_focus_slab2*.py + tests/test_no_side_effect_imports.py; commit with explicit
   pathspecs; record the new pinned green SHA.
PART 2 (GPU <= 1.5 h) - a DEV pilot on the 8 DEV episodes, arms R/N/T/Q, verifying the fix before the real run.
PRE-WRITTEN READING: FIX-CONFIRMED = zero indentation SyntaxErrors that survive the repair turn in every arm, and
per-lane execution 8/8 in every arm, and the primary still computable with nonzero denominators for >= 2 families.
Otherwise report the failing item and STOP; do not proceed to the rerun.
PART 3 (GPU <= 12 h) - only if PART 2 reads FIX-CONFIRMED: the full 64-episode rerun on the fresh bank, arms R/N/T
plus Q on the pre-registered 16-episode subset, 16 rounds, the qualified vLLM image, isolated checkout of the frozen
SHA verified before GPU access, determinism replay first, cooperative deadline 11.5 h, records preserved before
aggregates, never drop an episode, verdict computed by a frozen reading function.
Outputs under results/larger-test-v2/ (REGISTRATION.md committed first, then RESULTS.md, records <= 10 MB each);
DEV pilot under results/quick-checks/composition-pilot-8/; items in results/quick-checks/README.md; WORKLOG.
Commit with explicit pathspecs (git add -f); no push; stop/rm only your own container; never signal any process;
never read anything under data/bench; never touch results/larger-test/ or its frozen bytes.
