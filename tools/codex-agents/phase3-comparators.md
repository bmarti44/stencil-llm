# Brief: phase3-comparators — B3/B4 implementation (Phase 3's first registered deliverable)

## Objective

Implement the v1.27 comparator variants exactly as registered — read PLAN.md Section 5.4 (B3/B4 rows + the registered-not-implemented paragraph), 5.5, Section 3 (`pathway` stream), Appendix A (enum note), G3.7/H5, and Appendix C first. This lands and is reviewed BEFORE any training run launches. Deliverables:

- `src/stencil/model.py` (+ `gates.py`/`oscillator.py` as fits the registered layout): variant `b3` — cue-latch register `r_t = W_e · embed(x_t)` if `x_t` in cue range (tokens 1..32) else `r_{t-1}`, `r_0 = 0`, `W_e in R^{128 x 256}` N(0, 0.02) no bias (drawn from the `pathway` stream like other pathway modules), feeding the IDENTICAL RMS-normalized gate readout as M1 (same 5.3 plumbing/shapes, including the gate-identity bypass flag); variant `b4` — B0-local except positions holding cue-range tokens are globally attendable from all later positions (mask-only; zero new parameters; no gate pathway).
- `src/stencil/config.py`: loader accepts `b3`/`b4` per the Appendix A enum note (b3 has pathway/gate fields like m1 minus oscillator fields — osc_* must be null for b3/b4; validation rules per the Appendix A matrix, with negative-case tests per rule).
- `scripts/make_params.py` + `results/params.md`: extend to eight rows (B3 matched within 1 percent per 5.5; B4 records B0-local's count with a mask-only note).
- Proof-test extensions (registered in 5.4): `test_param_match_within_1pct` → eight configs; B3 added to `test_gate_identity_recovers_baseline_bitwise` (bypass 1.0 recovers B0-local bitwise) and to `test_cue_unreachable_exact_zero_grad` (B3's Jacobian at unreachable placements: NONZERO through the latch path — the cue is in-range for the latch); B4 added to the same test with the FLIPPED registered expectation (nonzero — its cue is globally attendable, that is its purpose) and to `test_cue_reachable_when_close`.

## Tests first (TDD, rule 1 — PER-TEST red observed and pasted)

Each extension run red before implementation (missing-variant failures count as red). Non-vacuity: every extended test's executed-case counter updated to its new registered count.

## Feasibility pass (phase2 retro binding)

Any new numeric expectation you introduce (there should be none beyond registered ones) gets an explicit feasibility argument in the handoff. Verify B3's latch magnitudes cannot saturate its gate (embeddings are N(0,~1)-scale; the RMS normalization bounds preactivations by construction — state this check's result).

## Allowlist

See phase3-comparators.allow. Do not touch PLAN.md, plan/, tools/, AGENTS.md, README.md, tests/fixtures/*.json, tests/fixtures/*.npz.

## Acceptance

Full suite green (`uv run pytest -q`) including all extensions, `make gate-2` NOT required (orchestrator runs it once post-landing), ruff clean. Show verbatim output.

## Ledger handoff

Do not edit the ledger. End with: files changed, per-test red/green pairs, the eight params.md counts, the latch-saturation feasibility statement, spec ambiguities with conservative readings, and every residual choice exercised (v1.10).
