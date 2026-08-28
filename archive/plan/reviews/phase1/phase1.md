# Phase1 Review — phase1

**Score:** 95 / 100
**Verdict:** PASS (≥90)
**Reviewer model:** codex/gpt-5.6-sol
**Date:** 2026-08-22

## Round log

### Round 2 — 2026-08-22 (codex/gpt-5.6-sol)
- Score: 95 / 100 (delta vs prior round: +11)
- Addressed since prior round:
  - Commit `ae807a9` changed the governed Phase 1 row to `in progress` at `README.md:50` and recorded both the original lens omission and the generic-lens fallback rationale at `plan/LEDGER.md:16`, closing findings 1 and 4.
  - Commit `1384ab1` moved Task A's independent production draws into the helper actually called by `task_a` at `src/stencil/data.py:134-177`; `tests/test_data.py:93-143` now exercises that helper with real seeded streams and pins the production path at registered N=128, closing finding 2.
  - Commit `1384ab1` added exact in-memory structure validation and stale-file checking at `scripts/make_data_samples.py:74-156`, tests it at `tests/test_data.py:352-364`, and binds both check and regeneration to G1 at `Makefile:10-15`, closing finding 3.
  - Commit `1384ab1` narrowed Ruff's exclusion to `tools` at `pyproject.toml:23-25`, corrected both executable fixture-provenance programs, and preserved the pre-implementation Task A and Task M fixture hashes exactly, closing finding 5.
  - The fix pass also added the independently authored Task B fixture assertion at `tests/test_data.py:231-285` and loader-validation coverage at `tests/test_config.py:70-157`. Independent replay matched every token, mask bit, metadata field, and the cue-redraw case in both Task B fixture sequences without importing the production generator.
- New or remaining:
  - No open Phase 1 findings. The remaining work is the governed acceptance/gate transition after the companion review is current, not a Phase 1 implementation defect.

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

1. **Medium (resolved 2026-08-22: the status row now records Phase 1 as in progress) — The governed status table never entered Phase 1.** `README.md:50` now says `in progress`, consistent with the state-transition rule at `PLAN.md:98` and the explanation at `README.md:58`; `plan/LEDGER.md:16` also records the correction and its recurrence. The late update cannot reconstruct the historical interval, but the governed current state is no longer false and the miss is auditable.

2. **Medium (resolved 2026-08-22: the guard now exercises the shared production helper and a registered-grid production stream) — The distractor-independence regression guard bypasses the production Task A sampler.** `_sample_task_a_example` owns cue, operand, and distractor sampling at `src/stencil/data.py:134-156`, and `task_a` calls it with the three named generators at `src/stencil/data.py:159-177`. `tests/test_data.py:93-120` drives that same helper for the fixed-distractor frequency check, while `tests/test_data.py:123-143` calls the public production stream at N=128 and independently replays all three named streams. The original N-dependent coupling escape no longer passes G1.

3. **Medium (resolved 2026-08-22: G1 now validates, regenerates, and diff-checks the required artifact) — Gate G1 does not bind its required generated artifact.** `scripts/make_data_samples.py:74-137` renders the four exact sections and enforces samples 1–3 in each; its `--check` path compares the committed bytes to the deterministic rendering at `scripts/make_data_samples.py:140-156`. `Makefile:10-15` runs that check, regenerates, and rejects a diff, while `tests/test_data.py:352-364` separately guards the section/sample cardinality. An absent, stale, hand-edited, or structurally incomplete `results/data_samples.md` now fails G1.

4. **Low (resolved 2026-08-22: the omission, selected fallback, and rationale are now recorded) — The Phase 1 review launch omits the required lens decision and rationale.** `plan/LEDGER.md:16` explicitly confesses the first-launch omission, identifies distributional/leakage as the natural bespoke lens, records that Round 1 covered that ground, and fixes the generic lens for this continuing review; `plan/LEDGER.md:13` carries that decision into Round 2. This restores an auditable decision consistent with the continuity requirement at `plan/PROTOCOL.md:19`.

5. **Low (resolved 2026-08-22: Ruff now includes the fixture programs and they pass without changing fixture bytes) — Ruff passes by excluding Phase 1's executable fixture provenance.** `pyproject.toml:23-25` now excludes only `tools`, so both Python programs under `tests/fixtures` are in the advertised repository lint run. The prior violations are corrected at `tests/fixtures/hand_execution.py:37-39` and `tests/fixtures/hand_execution.py:91`; the Task A and Task M JSON SHA-256 values remain exactly `4d7cde28…` and `b338f8bb…`, respectively.

## Recommendations

1. Make no further Phase 1 implementation changes before acceptance. Once the required companion review is current and acceptance passes, follow `plan/PROTOCOL.md:20` and the queued transition at `plan/LEDGER.md:13`: land the `gate(G1)` commit and change `README.md:50` from `in progress` to green in that same commit.

## Evidence consulted

- `PLAN.md` in full, especially Sections 1–6, Phase 1, Appendix B, Appendix C, and Appendix G; `plan/PROTOCOL.md`, the topmost `plan/LEDGER.md` state, `AGENTS.md`, and `README.md`.
- The complete current Phase 1 surface: `src/stencil/data.py`, `scripts/make_data_samples.py`, `tests/test_data.py`, `tests/test_config.py`, both executable fixture-provenance programs, all three JSON fixtures, `results/data_samples.md`, `configs/test_tiny.json`, `Makefile`, `pyproject.toml`, and the Phase 1 topic/artifact manifests.
- Read-only git history and diffs through commits `ae807a9` and `1384ab1`, including the fix allowlist/brief and fixture history. The Task A and Task M fixture hashes are byte-identical to commit `68b9d92`; the Task B fixture hash is `ce0df859…`.
- `results/logs/codex-agent-phase1-fixes.log`: production-path and artifact tests were observed failing before implementation; the loader-validation tests passed immediately and were honestly identified as missing coverage rather than implementation defects; a corrupted artifact failed `--check`; final G1 and G0 runs were green with 32 total tests.
- Independent Task B fixture audit using only PLAN/ledger conventions, SHA-256 stream derivation, and raw Torch generators: exact reconstruction of both sequences, including every token, loss-mask bit, metadata field, and the single consecutive-cue redraw.
- Independent read-only replay: all 12 Phase 1 data tests passed, `scripts/make_data_samples.py --check` passed, `ruff check --no-cache .` passed, `git diff --check` passed, and the worktree was clean before this canonical review-file update.
