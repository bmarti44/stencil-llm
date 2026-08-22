# Brief: phase1-fixes — Phase 1 review fix pass (round 1)

## Objective

Resolve the code findings from Phase 1 review round 1 (`plan/reviews/phase1/phase1.md` sol, `phase1-kimi.md` kimi — read both first). Do NOT edit review files, PLAN.md, plan/, README.md. Fixes:

1. (Medium, sol#2/kimi#2) Production-path independence guard: refactor the per-sequence cue/operand/distractor draw step into the helper `task_a` itself uses; drive the 10,000-resample frequency test through that helper with real seeded generators; add a production-stream assertion on at least one registered grid point (N=128 or 512) so an N-dependent coupling cannot hide behind the N=8 fixture.
2. (Medium, sol#3/kimi#3) Bind the G1 artifact: `make gate-1` must regenerate `results/data_samples.md` via scripts/make_data_samples.py and fail if the regenerated content differs from the committed file (e.g. `git diff --exit-code results/data_samples.md`) or if any task/placement section lacks its 3 samples.
3. (Low, sol#5/kimi#5) Narrow the ruff exclusion: lint `tests/fixtures/*.py` (fix the lint violations in `hand_execution.py` WITHOUT changing its behavior — the fixture JSONs are hash-pinned in the ledger; after editing, rerun it into a temp dir and assert byte-identical output to the committed fixtures, show that in your handoff); keep excluding only non-Python fixture data if needed. `tools/` stays excluded.
4. (Low, kimi#6) NEW ORCHESTRATOR-AUTHORED FIXTURE `tests/fixtures/task_b_r2_k8_seed0.json` (provenance `tests/fixtures/hand_execution_task_b.py`, hand-executed from the ledgered Task B schedule WITHOUT reading data.py). Add `test_task_b_exact_output` asserting `task_b` reproduces it exactly (R=2, k=8, delays U{32..256}, seed_rules=0, seed_data=0, 2 sequences, incl. loss_mask and the cue-redraw case). DO NOT MODIFY THE FIXTURE. On mismatch: adjudicate against PLAN.md Section 6 + the ledgered schedule and REPORT the discrepancy — never regenerate. If the generator's schedule genuinely differs from the ledgered one, that is a finding to report, not to paper over.
5. (Low, kimi#7) Loader-validation tests: tmp-JSON `load_config` cases exercising the Appendix A rules — unknown-field rejection, `damping_learnable`/variant consistency, osc_* null for non-oscillatory, per-task required/null matrix, `period_max >= 2 x longest delay`, task_placement enum. At least one failing case per rule.

## Allowlist

See phase1-fixes.allow. tests/fixtures/*.json are read-only inputs (lint-fix the .py provenance only, output-preserving per item 3).

## Tests first (TDD, rule 1)

New tests written first and observed failing where behavior is genuinely absent (the artifact-binding check must fail when data_samples.md is hand-corrupted in a scratch check; the Task B fixture test's first run is the adjudication itself). If a test passes immediately, say so — do not weaken it.

## Acceptance

`make gate-1` and `make gate-0` green. Run both and show output before finishing.

## Ledger handoff

Do not edit the ledger. End your final message with: files changed, verbatim test output, the byte-identity proof for item 3, per-finding resolution mapping, spec ambiguities with conservative readings, and every residual choice exercised (v1.10).
