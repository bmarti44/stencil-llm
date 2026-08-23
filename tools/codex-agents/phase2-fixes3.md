# Brief: phase2-fixes3 — close sol round-2 findings 10 and 11 (JAX oracle, final)

## Objective

Two fixes in `scripts/gen_jax_fixtures.py` and `tests/test_models.py`. Read sol round 2 in `plan/reviews/phase2/phase2.md` first.

1. (High #10) The FULL registered cases must run through the genuine upstream pipelines, not a locally constructed affine adapter. Registered basis (PLAN.md test-4 registration): inputs/params via the named fixture streams, length 512, seeds {0,1}, both dampings — INITIAL STATES ARE NOT REGISTERED, and production cells initialize to zeros (Section 5.2 tensor table), so the conservative reading is ZERO initial states, which the upstream entry points support. Therefore: generate the fixture trajectories by calling `apply_linoss_imex` (undamped) and `DampedIMEX1Layer._recurrence` (damped) on the full 512-step inputs; recover z exactly via the registered identity z_{k+1} = (y_{k+1} - y_k)/dt (exact for this update, not an approximation — state it in a comment). DELETE the `upstream_state_scan` affine adapter and the nonzero-initial machinery; drop the `fixtures:init` arrays from the archive (or store explicit zeros). Keep the 3-step `verify_upstream_equations` probe as a fast equation cross-check, but the FIXTURES must come from the full upstream pipelines. Update the source-array builder accordingly.
2. (Medium #11) `test_cell_matches_jax_fixtures` must reconstruct every scientific input and parameter from the registered named streams IN-TEST (fixtures:input/a/b/glu, zero initials), assert byte/exact equality with the archive's stored copies (provenance check), then compare trajectories at the registered tolerances.

## Tests first (TDD, rule 1 — per-test red)

Show test 4's new stream-reconstruction assertions failing against the CURRENT npz where identity changes (initial states), then the rest green after your changes except the trajectory comparison, which stays red until the orchestrator regenerates the npz — say so explicitly. Show a syntax/structure self-check for the worker (you cannot execute it — no network; state your API assumptions).

## Allowlist

See phase2-fixes3.allow. Do not touch PLAN.md, plan/, tools/, AGENTS.md, README.md, tests/fixtures/*.json, tests/fixtures/*.npz.

## Acceptance

Full suite green EXCEPT test 4 (expected red against the stale npz — report its exact failure); ruff clean. Do not run make gate-2.

## Ledger handoff

Do not edit the ledger. End with: files changed, red/green evidence, upstream API assumptions, conservative readings, residual choices (v1.10).
