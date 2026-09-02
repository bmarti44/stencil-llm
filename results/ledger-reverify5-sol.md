# Sol xhigh verification round 5 of the ledger runner (after fix round 4), 2026-09-01 — slice LAUNCH (falsification-only); 909 cohort DO-NOT-LAUNCH (two HIGH)

## Round 5 verdict

The Round 4 fix works, but I found **two new HIGH validity gaps**. No new critical findings.

### Verified

- The original 606/605 pooled exploit is now invalid:
  - Clustered mean: −0.6601 points
  - Lower bound: −4.6739
  - Result: `primary_claim_valid=false`
  - Exact sole reason: `text_not_clustered_better_than_base_selected`

- Coverage is tight:
  - 180/1,805 unselected = 9.9723%: passes.
  - 181/1,805 unselected = 10.0277%: fails `ledger_coverage_below_0.90`.
  - No `>10%` coverage bypass was found.

- [clustered_lower_bound](/home/bmarti44/stencil-llm/src/stencil/stats.py:276) is exactly `-clustered_bound(-diffs).upper_bound`. Exact float equality held across 304 constructed shapes and cluster sizes 2–909.

- The bound is not excessively strict. A conservative 545/909 case—text better in 59.96% of conversations and worse in every remaining conversation—passed:
  - Mean: +19.9120 points
  - Lower bound: +14.4472
  - Full record valid

### New HIGH findings

1. **Selected-only clustering still launders a full-estimand conversation reversal.**

   A complete 909-record/1,805-outcome artifact passed every gate with:

   - Coverage: 1,625/1,805 = 90.0277%
   - Overall pooled text/base: 180 improvements versus 179 regressions
   - Selected clustered lower bound: +8.2786 points
   - Full eligible conversation mean: **−0.6601 points**
   - Conversations: text better in 90, worse in 179, tied in 640
   - `primary_claim_valid=true`

   The remaining 9.9723% unselected cells recreate the Round 4 Simpson reversal because [the clustered gate](/home/bmarti44/stencil-llm/scripts/ledger_eval.py:450) covers selected cells only. The fix needs a clustered text-versus-base lower bound over **all eligible outcomes**, while optionally retaining the selected-subset check.

2. **A completely ineffective neural arm can be primary-valid.**

   Another complete record passed every gate with eligible accuracy:

   - Base: 0/909
   - Text: 5/909 = 0.5501%
   - Neural: **0/909**
   - Specificity: 0/909

   Text’s clustered lower bound was +0.0359 points, while text-minus-neural’s NI upper bound was 1.0642 points, yielding `primary_claim_valid=true`. This violates the plan’s requirement that neural “must do something at all.” A registered conversation-clustered neural-versus-base superiority gate is needed.

### Executed evidence

- Focused CPU suite: **61 passed**
- Exact preflight:
  - 113 conversations, 221 turns
  - 719 entries, 449 aged entries
  - 841 control constructions
  - 81/85 eligible linked = 95.2941%
  - One disclosed incomplete control at conversation 145, turn 2
  - Zero errors
- HEAD: `d5371d8abc636c47406802518cb62ca1af434aa8`
- Worktree remained clean.
- No model was loaded, no GPU process was started, and the forbidden IFEval input file was not accessed.

**113-conversation falsification-only diagnostic: LAUNCH.** The new flaws can create false positive/non-falsification outcomes, but the slice is mechanically forbidden from establishing NI and remains operationally fit as a one-way rejection screen.

**Full 909 cohort: DO-NOT-LAUNCH.** The runner is not fit for confirmatory use while either HIGH can produce `primary_claim_valid=true`.
206,453
