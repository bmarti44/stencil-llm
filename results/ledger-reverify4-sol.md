# Sol xhigh verification round 4 of the ledger runner (after fix round 3), 2026-09-01 — DO-NOT-LAUNCH (one HIGH: pooled non-vacuity)

**DO-NOT-LAUNCH** the 113-conversation diagnostic slice, even as a falsification-only screen. One new **HIGH** remains; no new critical findings.

### Verified fixes

- The 1,805-outcome constructions now fail correctly:

| Unselected | Selected | Coverage | Result | Reasons |
|---:|---:|---:|---|---|
| 901 | 904 | 50.0831% | INVALID | `ledger_coverage_below_0.90`, `unselected_not_all_failing` |
| 902 | 903 | 50.0277% | INVALID | both reasons |
| 903 | 902 | 49.9723% | INVALID | both reasons |

- Coverage boundary behaved exactly:

  - 180/1,805 untested = 9.9723%: coverage gate passes.
  - 181/1,805 untested = 10.0277%: fails `ledger_coverage_below_0.90`.
  - Therefore no internally consistent record can leave more than 10% unselected while satisfying [the coverage gate](/home/bmarti44/stencil-llm/scripts/ledger_eval.py:422).

- Exact equality or inferiority of text versus base on the selected subset fails `text_beats_base_selected`.

- Cohort sizes 1, 112, 113, and 908 were all primary-invalid with `falsification_only_slice`; completeness, identity, expected-turn, coverage, and selected-subset conditions remained independently reported.

- Three partial-run laundering attempts all failed:

  - Own 113-record identity: falsification-only.
  - Claiming 909 with full identity: incomplete, wrong record set, missing expected turns.
  - Claiming 909 with slice identity: incomplete and not a registered cohort.

  The production summary correctly uses the slice’s identity and size at [ledger_eval.py:675](/home/bmarti44/stencil-llm/scripts/ledger_eval.py:675).

### New HIGH: pooled non-vacuity still launders a worse clustered result

The selected-subset gate only requires pooled `n01 > n10` at [ledger_eval.py:416](/home/bmarti44/stencil-llm/scripts/ledger_eval.py:416). I constructed a complete 909-conversation/1,805-outcome record satisfying every gate with:

- Pooled text-vs-base: 606 improvements, 605 regressions.
- Pooled improvement: only +0.0554 points.
- Exploratory McNemar p-value: 0.5.
- Conversation-clustered mean text-minus-base: **−0.6601 points**.
- Text better in 303 conversations but worse in 605.
- `primary_claim_valid=true`, with no failure reasons.

Thus text can be worse than base on the registered conversation unit while the non-vacuity gate calls it better. This is a **HIGH** continuation of the validity problem. A registered conversation-clustered superiority test on selected eligible outcomes is needed before launch.

### Executed checks

- Focused CPU suite: **39 passed**.
- Exact CPU preflight: **81/85 = 95.2941%** linked coverage; 113 conversations, 221 turns, 841 control constructions, zero errors.
- CUDA was hidden for every Python command; no Qwen/controller load occurred.
- HEAD: `903208c332befd9ec11b9e93ecf2b8d9df9a3430`.
- Worktree and index remained clean. The initial `uv run` refreshed one installed environment package but changed no tracked or untracked repository content.

**Final verdict: DO-NOT-LAUNCH the 113-conversation falsification-only diagnostic slice.**
tokens used
124,643
