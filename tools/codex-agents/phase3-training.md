# Brief: phase3-training — training/eval infrastructure + pilot readiness

## Objective

Make the Phase 3 matrix runnable exactly as registered — read PLAN.md Phase 3, Section 6 (Loss and eval), Section 3, and Section 4's layout first. Deliverables:

- `src/stencil/train.py` extended (or `training.py` if cleaner under the registered layout — state the choice): full-variant training on Tasks A/B/M per the registered block (AdamW 0.9/0.95/1e-8/wd 0.1 with no decay on biases/norms/oscillator params, lr 3e-4 cosine to 3e-5, warmup 500, 20k steps, batch 64, grad clip 1.0, fp32, fresh data every step from the seeded generators, named streams per Section 3). Run-directory policy, run_id, env.json, metrics.jsonl, DONE marker: reuse the Phase 0 machinery unchanged.
- `src/stencil/evaluate.py`: the frozen Section 6 eval — 10,000 fresh eval-stream sequences per cell (seed_data + eval_seed_offset), final checkpoint only, exact-match pooled over answer-decision positions, per-seed JSON `{cell, variant, seed, n_sequences, n_answers, accuracy}`; plus the H4 first-answer-per-sequence exact binomial machinery fields needed later (record per-sequence first-answer correctness in the JSON).
- `scripts/run_matrix.py`: executes the registered 114-run matrix (8 variants Task A cells + sanity + Task M set), DONE-marker skip/resume semantics per Section 3, per-run timeout parameter, `--only` filter for the pilot.
- `scripts/make_report.py`: writes `results/summary.md` (mean and min-seed accuracy per cell) and the stale-rule analytic null where Task B cells exist. Minimal now; Phase 5 extends.
- `Makefile`: `pilot` target = M1 at (2048, 8) seed 0 to completion via run_matrix `--only`.

## Tests first (TDD, rule 1 — per-test red)

- `test_train_two_runs_bitwise_short`: 50 steps of the REAL M1 model on Task A (2048,8) twice in-process, bitwise-identical losses (determinism contract applies to every entrypoint; @pytest.mark.determinism).
- `test_eval_exact_match_correctness`: constructed-logits case where the exact-match count is hand-computable; asserts pooled accuracy and n_answers exactly.
- `test_eval_uses_eval_stream`: eval batches differ from train batches under the same seed_data and share the rule table (seed_rules isolation per Section 6).
- `test_run_matrix_resume`: a DONE-marked cell is skipped; an interrupted cell restarts fresh (tmp dirs).
- Non-vacuity counters throughout; negative cases for any new validation.

## Feasibility pass (phase2 retro binding)

State steps/sec measured on a 50-step probe and the implied 20k-step wall clock per run; flag if the 114-run matrix projection exceeds the 72 GPU-hour budget at that rate (the registered pilot will refine this — your probe is a sanity bound, not the projection of record).

## Allowlist

See phase3-training.allow. Do not touch PLAN.md, plan/, tools/, AGENTS.md, README.md, tests/fixtures/*.json, tests/fixtures/*.npz.

## Acceptance

Full suite green + ruff. Do NOT launch the pilot or any 20k-step run — the orchestrator launches the pilot with its registered write-ahead projection entry.

## Ledger handoff

Do not edit the ledger. End with: files changed, red/green pairs, the steps/sec probe figure, spec ambiguities with conservative readings, residual choices (v1.10).
