# Brief: phase0-fixes — Phase 0 review fix pass (round 1)

## Objective

Resolve the code findings from the Phase 0 review round 1 (`plan/reviews/phase0/phase0.md` sol, `plan/reviews/phase0/phase0-kimi.md` kimi — read both first; PLAN.md Section 3 and Phase 0 govern). Do NOT edit the review files. Fixes:

1. (High, sol#1/kimi#1) `src/stencil/determinism.py`: set `CUBLAS_WORKSPACE_CONFIG` to the registered `:4096:8` UNCONDITIONALLY (replace `setdefault`), still before `import torch`. Record the effective value in `env.json` (`src/stencil/train.py`). Add a fresh-process regression test (subprocess with a poisoned ambient value, e.g. `:16:8`) asserting the forced final value and `torch.are_deterministic_algorithms_enabled()`. Note the entrypoint-first-import discipline in the module docstring.
2. (Medium, sol#2/kimi#2) Extend the permanent test suite, mock-free: `config_hash` called directly; a four-term `run_id` test recomputing the preimage independently from a fixed `GitIdentity`; a temporary REAL git repo fixture covering `git_identity` framing and the full `run` policy — artifact quartet (config.json, env.json, metrics.jsonl, DONE) with exactly 200 metric rows, dirty-tree refusal, `--allow-dirty` stamping, existing-dir refusal without `--force`, same-git-state `--force` replacement, different-state `--force` refusal. Add all new tests to the `make gate-0` selection (or make gate-0 run the whole suite).
3. (Low, kimi#5) Non-vacuity anchor in `tests/test_determinism.py` AND `scripts/verify_determinism.py`: assert post-training parameters differ from seeded init (or `losses[0] != losses[-1]`).
4. (Low, kimi#6) `src/stencil/config.py` `git_identity`: handle untracked symlinks via lstat (frame the link target like tools/amend.sh does; a dangling symlink must not crash), and align the diff command flags to `--binary --full-index --no-textconv --no-ext-diff`.

## Allowlist

See phase0-fixes.allow. Do not touch PLAN.md, plan/, tools/, AGENTS.md, README.md.

## Tests first (TDD, rule 1)

For each fix, write or extend the failing test first, watch it fail (the cuBLAS poison test must fail against current `setdefault`; the run-policy tests must fail only if behavior is actually broken — if one passes immediately, say so rather than weakening it), then fix.

## Acceptance

`make gate-0` green including every new test, plus `ruff check .`. Run it and show the output before finishing.

## Ledger handoff

Do not edit the ledger yourself. End your final message with: files changed, test results verbatim, which review findings each change resolves, and any spec ambiguity with the conservative reading chosen.
