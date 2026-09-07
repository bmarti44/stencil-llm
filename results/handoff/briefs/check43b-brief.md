# Quick check 43b for gpt-6-astra: SUM vs PRODUCT routing, norm-matched dose at the decision token (~12 GPU-min) — 2026-09-05

Source: results/check43-review-fable.md (the check-43 null is a DOSE-SCALE artifact: the SUM/PRODUCT direction has unit
norm 0.72 vs 5.22 for the language direction; alpha 3 moved only marginal 8th/9th-expert swaps; and the SUM/PRODUCT
decision happens at the identity literal `0`/`1` after `acc = ` (generation index ~21 on 15/16 donors), not at the
prompt tail). Do fable's item 10 exactly: teacher-force the existing 32 check-43 donor outputs; profile raw router
logits at the generated tokens around the identity-literal position (report which positions); build the direction as
in check 43 but NORM-MATCH the band to the check-40c alpha-3 band norm (~9x the current b); -b (PRODUCT) sign on the
8 setup prompts with a breakage gate (malformed <= 1/8), plus +b and OFF and one shuffled-direction control at the
same norm. Bounded-interpreter checker as in check 43. READING (fixed before running): CONCEPT SELECTED if -b yields
executable PRODUCT on >= 6/8 with malformed <= 1/8 and shuffled PRODUCT <= 1/8; MARGINAL >= 3/8; else CLOSE
concept-level routing on this trunk (state plainly). Cap 0.4 GPU-h. RUNNING.flag protocol; never signal. Unregistered,
disclosed; outputs under results/quick-checks/check43b/; item 43b in results/quick-checks/README.md (4 lines);
WORKLOG entry (<= 5 lines). Commit with explicit pathspecs (git add -f for results); no push. Foreground only; never
terminate or signal any process; never read the sealed IFEval input file or the sealed BFCL cohort contents; nothing
fit or trained.

## ADDITIONS from results/astra-results-review.md (independent full review, 2026-09-05):
- Include a known-working JS actuator SANITY CONTROL in the same runtime (frozen 40c JS direction, alpha 3, 8 uncued
  tasks; must give >= 6/8 JS or the run is INVALID).
- Measure the neutral OFF default on the setup prompts BEFORE selection (do not infer it from sign-flip identity).
- Contextualize perturbation magnitudes against the successful JS band (norms ~6.8 and ~10.2) rather than assuming
  equal norm = equal efficacy; predeclare the finite setup grid.
- Retain both signs and stable matched shuffled controls; record actual dispatch/mixture changes and malformed outputs.
- If a safe setup cell exists, evaluate the ONE frozen choice on fresh banks with two seeds and both languages
  (Python + JavaScript), scoring complete executable programs, paired address specificity, and collateral failures;
  stop mechanically if no safe setup cell. Cap rises to 0.75 GPU-h for the two-seed final.
