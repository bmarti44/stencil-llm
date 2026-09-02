# Sol xhigh verification round 3 of the ledger runner (after fix round 2), 2026-09-01 — DO-NOT-LAUNCH (one HIGH)

## Round-3 verdict

**DO-NOT-LAUNCH** the diagnostic slice yet. The crash and provenance fixes work, but the new majority-selection gate remains gameable, producing a new **HIGH** validity finding.

| Round-2 finding | Status | Executed evidence |
|---|---|---|
| Specificity crash, conversation 145 turn 2 | **Resolved** | Exact CPU preflight completed 841 ordered control constructions. Conversation 145/2 was recorded as the sole incomplete control, without raising. Both selection orders passed the focused test. Impossible spans now return `None`/`"none"` and are excluded from the specificity comparison ([ledger.py](/home/bmarti44/stencil-llm/src/stencil/ledger.py:306), [ledger_eval.py](/home/bmarti44/stencil-llm/scripts/ledger_eval.py:597)). |
| Four validity-gate constructions | **Partially resolved** | Using the real 909-record/1,805-turn identity: wrong IDs failed `records_identity`; 909 one-turn records failed `expected_turns_present`; 100% base timeout failed the all-arm 2% gate; 903/1,805 unselected eligible outcomes failed the strict-majority gate. However, the adjacent 902/1,805 construction passed—see new HIGH below. |
| Clustered-bound false-pass | **Partially resolved** | Exact registered-size calculation reproduced plain t and percentile passing with 0–12 harmed clusters, false-pass **8.309737%**; correction passed only 0–11, false-pass **4.898494%** ([stats.py](/home/bmarti44/stencil-llm/src/stencil/stats.py:255)). But with 85 eligible outcomes across 43 clusters, an exact zero-point observed difference gives `100/43 = 2.325581` upper bound, so it cannot pass the strict 2-point margin. This is acceptable only if the slice remains strictly a one-way falsification screen, never positive NI evidence. |
| Unhashed dependencies | **Resolved** | `wave.py`, `bench.py`, and `determinism.py` are hashed ([ledger_eval.py](/home/bmarti44/stencil-llm/scripts/ledger_eval.py:60)); focused tests verified that changing any corresponding hash makes resume fail closed. |

### New HIGH

The strict-majority threshold at [ledger_eval.py](/home/bmarti44/stencil-llm/scripts/ledger_eval.py:387) merely moves the prior attack by one outcome:

- 903/1,805 unselected: invalid, selected fraction 49.9723%.
- 902/1,805 unselected: **primary-valid**, selected fraction 50.0277%.
- Text was made to fail exactly on the unselected outcomes, so fail-closed neural scoring added no penalty.
- Every other gate passed; corrected upper bound was 0.1100 points.

Thus almost half the eligible estimand can remain untested while `primary_claim_valid=true`. This is a **HIGH** continuation of the non-vacuity problem. No new critical finding.

The exact project-environment preflight reported 113 conversations, 221 turns, 719 entries, 449 aged entries, 85 eligible constraints, and zero errors. Focused CPU suite: **67 passed, 2 GPU tests skipped**. No model was loaded and `git status` remained clean.

**Final verdict: DO-NOT-LAUNCH**, including as a falsification screen, until the selection-coverage gate no longer admits the 50.0277% construction or the registered claim is explicitly narrowed to justify it.
tokens used
138,672
## Round-3 verdict

**DO-NOT-LAUNCH** the diagnostic slice yet. The crash and provenance fixes work, but the new majority-selection gate remains gameable, producing a new **HIGH** validity finding.
