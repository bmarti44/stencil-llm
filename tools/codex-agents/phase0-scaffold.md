# Brief: phase0-scaffold — Phase 0, scaffold and determinism harness

## Objective

Implement PLAN.md Phase 0 exactly as registered (read PLAN.md sections "3. Determinism contract", "Phase 0", and Appendix A first; plan/PROTOCOL.md governs process but your scope is only what this brief lists). Deliverables:

- `pyproject.toml` (uv-managed; deps: torch, pytest, ruff, numpy, matplotlib) and package skeleton `src/stencil/` with `determinism.py`, `config.py` (frozen flat dataclass per Appendix A with the registered loader validation), and the canonical-JSON + run_id hashing per Section 3 (the four-term formula, verbatim).
- `configs/test_tiny.json` with the registered contents (variant b0_local, d_model 64, L 2, H 2, d_ff 256, w 16, vocab 64, task copy = predict-previous-token over the operand range, batch 8, 200 steps, Phase 3 optimizer block, fp32, all seeds 0).
- A minimal train loop (`src/stencil/train.py`) sufficient for the copy task: embedding + single linear head is enough for Phase 0 — the real transformer is Phase 2; loss over positions 1 onward; named-stream RNG per Section 3; writes results/<run_id>/config.json, metrics.jsonl, env.json (with both identity hashes), DONE marker; refuses existing run dirs per the registered --force semantics.
- `Makefile` with `verify` and `gate-0` targets; `scripts/verify_determinism.py`.

## Tests first (TDD, rule 1 — write each failing test, run it, watch it fail, then implement)

- `tests/test_determinism.py::test_determinism_two_runs_bitwise` (200 steps twice in-process, bitwise-identical loss sequences; @pytest.mark.determinism)
- `tests/test_config.py::test_config_hash_stable` (key-order independence + the registered known answer: canonical_json({"b": 2, "a": 1.5}) == b'{"a":1.5,"b":2}', sha256 hand-computed and hardcoded BEFORE implementing)
- `tests/test_config.py::test_seed_isolation` (seed_data change leaves init state_dict bytes identical and changes the first batch; seed_init the reverse)

## Allowlist

See phase0-scaffold.allow. Do not touch PLAN.md, plan/, tools/, AGENTS.md, README.md.

## Acceptance

`make gate-0` green: the three tests plus `ruff check .` pass. Run it and show the output before finishing.

## Ledger handoff

Do not edit the ledger yourself (the wrapper records provenance automatically). End your final message with: files created, test results verbatim, any registered-spec ambiguity you hit and the conservative reading you chose.
