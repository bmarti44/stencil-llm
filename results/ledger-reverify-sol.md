# Sol xhigh re-verification of the ledger fix round (HEAD after 71-test fix), 2026-09-01 — DO-NOT-LAUNCH

## Verdict

**DO-NOT-LAUNCH** the diagnostic slice, even as a falsification screen. The specificity arm is guaranteed to crash on conversation 145 turn 2, and two primary-validity/statistical defects remain.

## Prior findings

1. **Partially resolved — CRITICAL remains.**  
   The original 200-cell empty-ledger attack and four-record partial run now return `primary_claim_valid=false`. However, the completeness check only counts 909 unique `ci` values; it does not validate identities, keys, or expected turns ([ledger_eval.py](/home/bmarti44/stencil-llm/scripts/ledger_eval.py:295)). I obtained `true` from:

   - 909 records with entirely wrong conversation IDs;
   - 909 one-turn records, despite the real cohort requiring **1,805** late turns;
   - a run where base timed out on **100%** of turns—the 2% gate excludes base;
   - a run with half of eligible constraints unselected, because another entry was active and text failed the same half.

2. **Partially resolved — HIGH remains.**  
   Eligible cells are now aged/fixable only and averaged within conversation before clustering ([ledger_eval.py](/home/bmarti44/stencil-llm/scripts/ledger_eval.py:271)). My hand calculation for cluster values 1–10 gave 7.255072013301 versus implementation 7.255072013290.

   But the claimed 95% t bound undercovers: for 909 independent clusters with pure degradation exactly at the 2-point margin, the code declares NI with 0–12 harmed clusters. The exact boundary false-pass probability is **8.31%**, not 5%. All-zero data produce a zero-width upper bound of 0 ([stats.py](/home/bmarti44/stencil-llm/src/stencil/stats.py:212)).

3. **Resolved.**  
   The exact CPU preflight passed all **113 conversations / 221 turns**, including conversation 769 turns 2 and 3: 719 entries, 449 aged, 85 eligible, real segmenter on every turn, zero errors. The preflight correctly occurs before model/CUDA loading ([ledger_eval.py](/home/bmarti44/stencil-llm/scripts/ledger_eval.py:409)).

4. **Partially resolved — HIGH remains.**  
   Linkage, direct neural-vs-specificity reporting, and same-dose matched controls were added. Across 467 returned diagnostic control cases, I found zero width mismatches and zero overlaps with any ledger/control span.

   However, conversation 145 turn 2 has exactly two aged entries of widths 34 and 19. Its longest non-ledger run is 31 tokens, so both possible selection orders raise `ValueError` ([ledger.py](/home/bmarti44/stencil-llm/src/stencil/ledger.py:299)). Frozen `top_k=2` guarantees both entries are selected. The CPU preflight does not test this control construction.

5. **Open — MEDIUM.**  
   There is no change since `747be31` in `salience.py`, its weights, or salience tests. The inconsistent labels remain, along with the benchmark-agnostic claim. The amendment discloses failed blind recall, but does not independently adjudicate labels or establish wholly disjoint training/blind samples.

6. **Resolved in code/test design.**  
   Neural prompt length is measured and checked at runtime ([ledger_eval.py](/home/bmarti44/stencil-llm/scripts/ledger_eval.py:495)); asymmetric NI and consumer-path tests were added; the empty-ledger test now checks token IDs and callback execution ([test_ledger.py](/home/bmarti44/stencil-llm/tests/test_ledger.py:355)). CPU result: **54 passed, 2 GPU tests skipped**. Per the session rule, I did not execute the GPU bitwise test.

7. **Partially resolved — MEDIUM.**  
   The previously named provenance dependencies are now hashed and resume mismatch tests pass ([ledger_eval.py](/home/bmarti44/stencil-llm/scripts/ledger_eval.py:41)). But `wave.py`, `bench.py`—including EOS and biased-layer definitions—and `determinism.py` remain unhashed, so behavior can still change across resume without detection.

## FIX-ROUND readings

- **Origin-turn linkage: PASS as disclosed.** All 221 diagnostic turns used `origin_turn`; reciprocal linkage had zero errors. Its leniency is material: 41/85 eligible constraints came from turns introducing multiple IDs, 26 had multiple linked entries, and 4 had no entry.
- **`ledger.matched_nonledger_control`: FAIL operationally.** Returned controls are width-matched and disjoint, but construction is impossible on the guaranteed conversation-145 selection.
- **Fail-closed credit: PASS narrowly.** An unselected raw neural pass becomes a credited failure and raw rate remains reported. It does not prevent the overall claim from passing when text also fails those cells.

## New high/critical findings

- **CRITICAL:** incomplete/wrong-identity artifacts and 100% base-timeout artifacts can still be primary-valid.
- **HIGH:** the registered clustered “95%” bound has 8.31% boundary false-pass probability in a simple registered-size case.
- **HIGH:** the diagnostic specificity arm is guaranteed to crash on conversation 145 turn 2.

No repository files were changed; final `git status` was clean.
tokens used
154,556
## Verdict

**DO-NOT-LAUNCH** the diagnostic slice, even as a falsification screen. The specificity arm is guaranteed to crash on conversation 145 turn 2, and two primary-validity/statistical defects remain.

## Prior findings

1. **Partially resolved — CRITICAL remains.**  
   The original 200-cell empty-ledger attack and four-record partial run now return `primary_claim_valid=false`. However, the completeness check only counts 909 unique `ci` values; it does not validate identities, keys, or expected turns ([ledger_eval.py](/home/bmarti44/stencil-llm/scripts/ledger_eval.py:295)). I obtained `true` from:

   - 909 records with entirely wrong conversation IDs;
   - 909 one-turn records, despite the real cohort requiring **1,805** late turns;
   - a run where base timed out on **100%** of turns—the 2% gate excludes base;
   - a run with half of eligible constraints unselected, because another entry was active and text failed the same half.

2. **Partially resolved — HIGH remains.**  
   Eligible cells are now aged/fixable only and averaged within conversation before clustering ([ledger_eval.py](/home/bmarti44/stencil-llm/scripts/ledger_eval.py:271)). My hand calculation for cluster values 1–10 gave 7.255072013301 versus implementation 7.255072013290.

   But the claimed 95% t bound undercovers: for 909 independent clusters with pure degradation exactly at the 2-point margin, the code declares NI with 0–12 harmed clusters. The exact boundary false-pass probability is **8.31%**, not 5%. All-zero data produce a zero-width upper bound of 0 ([stats.py](/home/bmarti44/stencil-llm/src/stencil/stats.py:212)).

3. **Resolved.**  
   The exact CPU preflight passed all **113 conversations / 221 turns**, including conversation 769 turns 2 and 3: 719 entries, 449 aged, 85 eligible, real segmenter on every turn, zero errors. The preflight correctly occurs before model/CUDA loading ([ledger_eval.py](/home/bmarti44/stencil-llm/scripts/ledger_eval.py:409)).

4. **Partially resolved — HIGH remains.**  
   Linkage, direct neural-vs-specificity reporting, and same-dose matched controls were added. Across 467 returned diagnostic control cases, I found zero width mismatches and zero overlaps with any ledger/control span.

   However, conversation 145 turn 2 has exactly two aged entries of widths 34 and 19. Its longest non-ledger run is 31 tokens, so both possible selection orders raise `ValueError` ([ledger.py](/home/bmarti44/stencil-llm/src/stencil/ledger.py:299)). Frozen `top_k=2` guarantees both entries are selected. The CPU preflight does not test this control construction.

5. **Open — MEDIUM.**  
   There is no change since `747be31` in `salience.py`, its weights, or salience tests. The inconsistent labels remain, along with the benchmark-agnostic claim. The amendment discloses failed blind recall, but does not independently adjudicate labels or establish wholly disjoint training/blind samples.

6. **Resolved in code/test design.**  
   Neural prompt length is measured and checked at runtime ([ledger_eval.py](/home/bmarti44/stencil-llm/scripts/ledger_eval.py:495)); asymmetric NI and consumer-path tests were added; the empty-ledger test now checks token IDs and callback execution ([test_ledger.py](/home/bmarti44/stencil-llm/tests/test_ledger.py:355)). CPU result: **54 passed, 2 GPU tests skipped**. Per the session rule, I did not execute the GPU bitwise test.

7. **Partially resolved — MEDIUM.**  
   The previously named provenance dependencies are now hashed and resume mismatch tests pass ([ledger_eval.py](/home/bmarti44/stencil-llm/scripts/ledger_eval.py:41)). But `wave.py`, `bench.py`—including EOS and biased-layer definitions—and `determinism.py` remain unhashed, so behavior can still change across resume without detection.

## FIX-ROUND readings

- **Origin-turn linkage: PASS as disclosed.** All 221 diagnostic turns used `origin_turn`; reciprocal linkage had zero errors. Its leniency is material: 41/85 eligible constraints came from turns introducing multiple IDs, 26 had multiple linked entries, and 4 had no entry.
- **`ledger.matched_nonledger_control`: FAIL operationally.** Returned controls are width-matched and disjoint, but construction is impossible on the guaranteed conversation-145 selection.
- **Fail-closed credit: PASS narrowly.** An unselected raw neural pass becomes a credited failure and raw rate remains reported. It does not prevent the overall claim from passing when text also fails those cells.

## New high/critical findings

- **CRITICAL:** incomplete/wrong-identity artifacts and 100% base-timeout artifacts can still be primary-valid.
- **HIGH:** the registered clustered “95%” bound has 8.31% boundary false-pass probability in a simple registered-size case.
- **HIGH:** the diagnostic specificity arm is guaranteed to crash on conversation 145 turn 2.

No repository files were changed; final `git status` was clean.
