# Brief: phase1-generators — Phase 1, data generators

## Objective

Implement PLAN.md Phase 1 exactly as registered (read PLAN.md Section 6 in full, Phase 1, Section 3, Appendix B/C first). Deliverables:

- `src/stencil/data.py`: pure-function generators for Task A, Task B, and Task M per Section 6 — named streams per Section 3 (`rules`, `cues`, `operands`, `distractors`, `keys`, `values`, `queries`, `delays`), rule tables from `seed_rules` alone, example streams from `seed_data`; `cue_blind_bayes(config)` (exactly 1/k for k<=16, 1/16 for k=32); `receptive_field()` interplay per Section 1 conventions; every generator yields `(tokens, loss_mask, metadata)` under the causal alignment contract (loss_mask[p] true iff tokens[p+1] is an answer token).
- ORCHESTRATOR-AUTHORED FIXTURES, already committed at `tests/fixtures/task_a_k2_n8_seed0.json` and `tests/fixtures/task_m_p4_q2_seed0.json` (hand-executed from the registered constructions BEFORE this brief, per the v1.6 TDD-conform protocol). DO NOT MODIFY THEM. Your generators must reproduce them exactly; on any mismatch, adjudicate against the registered construction in PLAN.md and report — NEVER regenerate or edit a fixture. The fixture JSON's docstring-recorded conservative readings (cue token = 1+rule_index, operand token = 34+index, distractor token = 50+draw over 14, key token = 1+index, scalar `torch.randint(0, high, (1,), generator=g)` draws, one continuing generator per stream across a fixture's sequences, Task M miniature gap=0) are binding for fixture reproduction.
- `scripts/make_data_samples.py` writing `results/data_samples.md`: 3 decoded samples per task and placement.
- `Makefile` target `gate-1`: all Phase 1 tests plus ruff; keep `gate-0` intact and green.

## Tests first (TDD, rule 1 — write each failing test, run it, watch it fail, then implement)

Exactly the registered Phase 1 list, named verbatim:
- `test_task_a_exact_output` (against the committed fixture)
- `test_rules_are_permutations`
- `test_vocab_ranges_disjoint`
- `test_distractor_rule_independence` (10,000 resamples, 5 sigma)
- `test_rules_latin_rectangle` (incl. `cue_blind_bayes` exact values; k=32 two-per-answer balance)
- `test_loss_mask_positions` (all three tasks)
- `test_task_b_active_rule_tracking` (most-recent-cue semantics on constructed cases)
- `test_task_m_bindings` (against the committed fixture)
- `test_task_m_gap_exceeds_receptive_field` (strictly greater than `receptive_field()`)

Non-vacuity discipline (AGENTS.md): assertions must fail loudly when vacuous; statistical tests assert their sample counts.

## Allowlist

See phase1-generators.allow. Do not touch PLAN.md, plan/, tools/, AGENTS.md, README.md, or tests/fixtures/ (read-only inputs).

## Acceptance

`make gate-1` green (all Phase 1 tests + ruff) AND `make gate-0` still green. Run both and show the output before finishing. Generate `results/data_samples.md` and name it in your handoff.

## Ledger handoff

Do not edit the ledger yourself. End your final message with: files created/changed, test results verbatim, any registered-spec ambiguity with the conservative reading chosen, AND every residual choice exercised (v1.10 — any formula/ordering/detail the spec leaves open that you decided, even if it feels minor).
