# Brief: phase2-models — Phase 2, models and plumbing proofs

## Objective

Implement PLAN.md Phase 2 exactly as registered. Read FIRST and in full: PLAN.md Section 5 (5.1-5.5), Phase 2, Section 3, Appendix A/B/C/G; the Phase 2 test list is the contract — every case, tolerance, seed, and stream name is registered there and must be restated in each test's docstring (non-vacuity rule v1.9/v1.10: count executed cases, assert equals registered count; `None` gradients fail; nonzero-trajectory assertions before bitwise comparisons). Deliverables:

- `src/stencil/model.py`: base transformer per 5.1 (all six variants share it); `src/stencil/cell.py` (or within model.py): the unified oscillator cell per 5.2 with the discrete invariant `H_d` helper, `zero_damping` bypass flag (test 3), gate-identity bypass flag (test 6), stability-bound helper (test 2b); gate application per 5.3; the six variants per 5.4 built from Appendix A configs; parameter matching per 5.5 + `scripts/make_params.py` writing `results/params.md`.
- Tests 1, 2, 2b, 3, 6, 7, 8, 9 from the Phase 2 list, verbatim names, in registered order, TDD-first. Test 5 (scan) does NOT apply — do not implement a parallel scan; sequential is the oracle.
- Test 4 (`test_cell_matches_jax_fixtures`) + `scripts/gen_jax_fixtures.py` per the registered pinned-oracle workflow (Appendix G). The coder sandbox has NO network: write the script and the test, mark the test `@pytest.mark.skipif` on the fixture npz's absence with a LOUD skip reason ("jax fixtures not yet generated — orchestrator runs scripts/gen_jax_fixtures.py"), and report this in the handoff. The orchestrator will run the script (network) and re-run the suite; the test must then pass with zero code changes.
- `Makefile` `gate-2`: tests 1-9 (4 skips only until fixtures exist; 2b included) plus ruff; `gate-0`/`gate-1` stay green.

## Fixture surface (phase1 retro binding)

Every registered fixture stream (`fixtures:init`, `fixtures:input`, `fixtures:a`, `fixtures:b`, `fixtures:glu`) derives via the Section 3 named-stream scheme. Closed-form references (matrix-power discrete solution, forced particular solution, modal decay for the damped case — verify the exact modal decay analytically and record it in a code comment per test 2's registration) are computed in-test in fp64, never committed as opaque data.

## Validation surface (phase1 retro binding)

Every new validation/assertion surface (stability bound, config-variant consistency for the new fields, bypass-flag exclusivity) must name its NEGATIVE-case tests in the handoff — at least one failing case per rule.

## Allowlist

See phase2-models.allow. Do not touch PLAN.md, plan/, tools/, AGENTS.md, README.md, tests/fixtures/*.json.

## Acceptance

`make gate-2` green (with only test 4 skipped, loudly), `make gate-1` and `make gate-0` green. Run all three and show output before finishing.

## Ledger handoff

Do not edit the ledger. End your final message with: files created/changed, verbatim gate output, the analytically derived modal decay factor with its derivation sketch, per-test case counts (registered vs executed), spec ambiguities with conservative readings, and every residual choice exercised (v1.10 — lowest-index/lexicographic/first-in-stream defaults).
