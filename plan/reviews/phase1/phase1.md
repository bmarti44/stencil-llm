# Phase1 Review — phase1

**Score:** 84 / 100
**Verdict:** CONDITIONAL PASS (75–89)
**Reviewer model:** codex/gpt-5.6-sol
**Date:** 2026-08-22

## Round log

### Round 1 — 2026-08-22 (codex/gpt-5.6-sol)
- Score: 84 / 100 (delta vs prior round: +84)
- Addressed since prior round:
  - Initial round; there are no prior findings to close.
  - Commit `68b9d92` committed the two fixtures before `src/stencil/data.py` or `tests/test_data.py` existed; commit `701833f` left both fixture hashes unchanged and added the implementation. The coder log records each of the nine named tests failing before its corresponding implementation and then passing.
  - Independent reconstruction from the registered seed derivation and draw order exactly matched both Latin rows, all four Task A fixture sequences, and all four Task M fixture sequences. The first Task A draws were cue 0, operand 1, distractors `[3, 1, 1, 4, 5, 2, 10, 0]`; the first Task M draws were keys `[20, 7, 13, 2]`, values `[7, 13, 10, 12]`, and query positions `[2, 1]`.
  - The current implementation matches the registered vocabulary, Latin-square construction, scalar draw sequences, causal masks, Task B cue switching, and strict beyond-window distance convention. Independent replay passed all 16 tests and Ruff; the worktree was clean before this review file was written.
- New or remaining:
  - README still reports Phase 1 as not started despite two ledger entries establishing that it was launched and its code landed.
  - The distractor-independence test samples cues itself and invokes an explicit-draw constructor, so it does not protect the production `task_a` sampling path on the registered grid.
  - `gate-1` does not generate or validate the required decoded-sample artifact.
  - The review launch does not record the required lens selection/rationale and uses the generic fallback despite this being a distribution-sensitive generator change.
  - Ruff excludes all of `tests/fixtures`, hiding the Phase 1 fixture-provenance Python program from the advertised repository lint check.

## Findings

1. **Medium — The governed status table never entered Phase 1.** `README.md:50` still says `not started`, while `plan/LEDGER.md:16` records the Phase 1 launch and `plan/LEDGER.md:13` records landed code. This violates the explicit state-transition rule at `PLAN.md:98` and the README's own explanation at `README.md:58`. The eventual green gate commit cannot retroactively make the required in-progress state truthful during the phase.

2. **Medium — The distractor-independence regression guard bypasses the production Task A sampler.** `tests/test_data.py:90-110` creates its own `cues` generator and feeds a fixed list into `make_task_a_example`; it never calls `task_a` or `generate`. The production stream creation and joint cue/operand/distractor sampling it is meant to protect live separately at `src/stencil/data.py:134-156`. The N=8 exact fixture at `tests/test_data.py:38-56` limits a second guard to four miniature sequences, so a regression that couples distractors to the cue only on registered N values 128/512/2048 would leave every G1 test green while invalidating the construction claim. The current implementation is correct by inspection; the permanent gate is not testing that fact on the scientific grid.

3. **Medium — Gate G1 does not bind its required generated artifact.** `PLAN.md:346` makes generated `results/data_samples.md` part of G1, and `scripts/make_data_samples.py:67-104` is the only code that renders it. `Makefile:10-12` runs only the nine tests and Ruff: it remains green if the artifact is absent, stale, hand-edited, or contains the wrong number of sections. The committed `results/data_samples.md:1-83` is currently reproducible and contains three samples for Task A, Task B, and both Task M placements, but the gate does not preserve that property.

4. **Low — The Phase 1 review launch omits the required lens decision and rationale.** `plan/PROTOCOL.md:19` requires the write-ahead entry to name the chosen adaptive lens and rationale, explicitly identifying distributional/leakage review as the natural generator lens. `plan/LEDGER.md:13` records commands, paths, and the fixture hand-check but neither a bespoke lens nor a rationale for using the generic fallback at `tools/codex-prompts/review-phase.md:1-11`. This round covered the missing distributional checks directly, so the omission is procedural rather than an uncovered scientific defect.

5. **Low — Ruff passes by excluding Phase 1's executable fixture provenance.** `pyproject.toml:23-25` excludes the entire `tests/fixtures` directory after the coder encountered violations in the newly committed `tests/fixtures/hand_execution.py`, including the overlong seed derivation at `tests/fixtures/hand_execution.py:37` and unqualified `zip` at `tests/fixtures/hand_execution.py:89`. The script is not production code and its output was independently verified, but `ruff check .` no longer means all Phase 1 Python artifacts were checked and future executable fixture tooling in that directory will also be silently skipped.

## Recommendations

1. Change `README.md:50` to `in progress` in the fix commit; only change it to green in the accepted `gate(G1)` commit, preserving the state sequence required by `PLAN.md:98`.

2. Refactor the cue/distractor draw step at `src/stencil/data.py:145-156` into the real helper used by `task_a`, and drive that helper with real seeded generators plus fixed distractor draws in `tests/test_data.py:90-110`. Add a registered-grid production-stream assertion so an N-dependent coupling cannot hide behind the N=8 fixture.

3. Add a check mode to `scripts/make_data_samples.py:67-104` that renders in memory and compares against `results/data_samples.md`, including exactly three samples in each of the four required sections; invoke it from `Makefile:10-12`.

4. Record the generic-lens omission and fallback rationale in `plan/LEDGER.md`; retain the already-selected lens for this topic, and use a purpose-built distributional/leakage rubric at the first launch of future generator reviews as required by `plan/PROTOCOL.md:19`.

5. Fix `tests/fixtures/hand_execution.py:37-89` and remove the broad `tests/fixtures` exclusion at `pyproject.toml:24`, or narrow the exclusion to non-Python generated fixture formats.

## Evidence consulted

- `PLAN.md` in full, especially Sections 1–6, Phase 1, Appendix B, Appendix C, and Appendix G; `plan/PROTOCOL.md`, the topmost `plan/LEDGER.md` state, `AGENTS.md`, and `README.md`.
- Phase 1 source and artifacts line by line: `src/stencil/data.py`, `scripts/make_data_samples.py`, `tests/test_data.py`, `tests/fixtures/hand_execution.py`, both committed JSON fixtures, `results/data_samples.md`, `configs/test_tiny.json`, `Makefile`, `pyproject.toml`, and the Phase 1 topic/artifact manifests.
- Read-only git history and diffs for commits `68b9d92` and `701833f`; fixture hashes were identical across the two commits, and neither generator source nor data tests existed in the fixture commit.
- `results/logs/codex-agent-phase1-generators.log`: each registered test was added before its corresponding implementation, observed failing, then observed passing; final `make gate-1` and `make gate-0` runs were green.
- Independent fixture audit using only the registered SHA-256 seed derivation and raw Torch generators: exact reconstruction of two Latin rows, four Task A sequences, and four Task M sequences.
- Independent read-only replay: `16 passed in 3.23s`, `ruff check --no-cache .` passed, `git diff --check` passed, and the worktree was clean before the canonical review file update.
