# Brief: phase2-fixes — implement the v1.26 amended contracts

## Objective

Bring gate-2 green under PLAN.md as amended by v1.26 (landed by Human Adjudication 5 — read the v1.26 entries in PLAN.md's index, plan/AMENDMENTS.md, and the amended Phase 2 test 1/test 2 text and Section 5.3 FIRST). Three changes, no others:

1. `test_oscillator_matches_discrete_closed_form`: the fp32-vs-fp64 comparison becomes rtol 1e-4 with per-case atol = 1e-4 x max|fp64 reference| over that case's trajectory. The fp64-vs-closed-form bound (rtol 1e-9, atol 1e-12) is UNCHANGED.
2. `test_discrete_invariant_conserved`: the continuous-H trend bound becomes |slope| < 1e-4 x H_0 per window. The H_d drift bounds and the 4x excursion cap are UNCHANGED.
3. `src/stencil/model.py` Section 5.3 gate: the gate projection reads the parameter-free RMS-normalized control state `c_hat_t = c_t / sqrt(mean(c_t^2) + 1e-8)` (mean over the 128 dims); `c_t` itself is unchanged everywhere else. Update `test_cue_unreachable_exact_zero_grad` expectations only insofar as they now pass — the registered case list and assertions are unchanged; also verify the bitwise tests (3, 6) still pass with the normalization in place (the gate-identity bypass must bypass BEFORE the sigmoid as registered, so normalization must not break bitwise identity when bypassed).

## Tests first (TDD, rule 1)

Run the three failing tests first and show them failing under the OLD contracts' code; apply the changes; show all green. If any other test regresses (e.g. bitwise identity through the normalization path), report and fix within the amended spec — never weaken.

## Allowlist

See phase2-fixes.allow. Do not touch PLAN.md, plan/, tools/, AGENTS.md, README.md, tests/fixtures/*.json.

## Acceptance

`make gate-2` green with ONLY test 4's loud JAX skip; `make gate-1` and `make gate-0` green. Show all three verbatim.

## Ledger handoff

Do not edit the ledger. End with: files changed, verbatim gate output, executed-case counts for the three amended tests, and every residual choice exercised (v1.10).
