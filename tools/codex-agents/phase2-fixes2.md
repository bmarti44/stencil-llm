# Brief: phase2-fixes2 — Phase 2 review round-1 fixes (sol 58, kimi 73)

## Objective

Resolve the code findings from `plan/reviews/phase2/phase2.md` (sol) and `phase2-kimi.md` (kimi) — read both in full first. Fixes, in severity order:

1. (sol#1 High) `tests/test_models.py::_closed_form` must be the REGISTERED closed form, not a step-loop recurrence: for each step k, `state_k = M^k s_0 + (I - M)^{-1} (I - M^k) d` (fp64; `torch.linalg.matrix_power`; handle the G=0, A→0 edge only if a registered case needs it — none does). The implementation must share NO loop structure with the production cell. Keep tolerances exactly as amended (v1.26).
2. (sol#2/kimi#1 High) `scripts/gen_jax_fixtures.py`: the worker must EXECUTE the pinned checkouts' code — `sys.path` the cloned repos and import/call their cell implementations (tk-rusch/linoss for undamped, jaredbmit/damped-linoss for damped), mapping the registered parameters to the upstream API. If the upstream equations differ materially from PLAN Section 5.2's registered update, DO NOT silently adapt either side: print the exact discrepancy (equations side by side) and exit nonzero — Section 5.2 registers that as an amendment trigger. You cannot run this script (no network); make it correct by inspection of the pinned repos' READMEs/papers as cited in PLAN Appendix G, state your API-mapping assumptions explicitly in the handoff, and the orchestrator will execute it. Do not modify tests/fixtures/jax_cells.npz.
3. (sol#4/kimi#2 Medium) Test 7 must draw the registered EVAL stream: apply `eval_seed_offset` to `seed_data` in `_task_a_config` (or equivalent) so the docstring and the draws agree; fix the docstring.
4. (sol#5/kimi#3 Medium) Restore the registered Section 4 layout: split `src/stencil/model.py` into `src/stencil/oscillator.py` (OscillatorCell, DecayCell, controller, sequential oracle), `src/stencil/gates.py` (gate projection/application incl. B1's headwise gate), and `src/stencil/model.py` (base transformer + variants). Pure move/refactor — all tests must stay green with identical numerics (bitwise where tests assert bitwise).
5. (sol#7/kimi#4 Low) Replace both `assert 1 == 1` placeholders with real executed-case counters.
6. (kimi#5 Low) Pathway modules draw from a named derived stream: `named_generator(seed_init, "pathway")` (registration of the stream name rides the in-flight v1.27 amendment — implement now, flag in handoff). Test 6's bitwise shared-module property must still hold; if this changes pathway init draws, that is expected (no training runs exist).

## Tests first (TDD, rule 1 — PER-TEST red observed, sol#6)

For every behavioral change, run the specific test red (or show the new assertion failing against the old code) BEFORE the fix, and paste each red/green pair in the handoff — file-level ordering is not sufficient (sol finding #6 dinged exactly this).

## Allowlist

See phase2-fixes2.allow. Do not touch PLAN.md, plan/, tools/, AGENTS.md, README.md, tests/fixtures/*.json, tests/fixtures/*.npz.

## Acceptance

Full suite `uv run pytest -q` green EXCEPT `test_cell_matches_jax_fixtures`, which may fail or pass against the old npz — report its status truthfully either way (the orchestrator regenerates the npz with the corrected generator afterward); `ruff check .` clean. Do NOT run `make gate-2` (32-minute Jacobian — the orchestrator runs it once after the npz regeneration).

## Ledger handoff

Do not edit the ledger. End with: files changed, per-test red/green evidence, verbatim suite output, the upstream API-mapping assumptions from item 2, spec ambiguities with conservative readings, and every residual choice exercised (v1.10).
