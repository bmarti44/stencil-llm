# Brief: taskd-generator — Task D generator, config, b3k module, role masks

## Objective

Implement the Task D data generator and supporting modules EXACTLY per the frozen generation law in `plan/taskd/PLAN-TASKD.md` (read it in FULL first — the law is registered to the token; sol reviewed it through 7 rounds and implementation review will check you against it). The orchestrator's hand-executed miniature fixture is committed at `tests/fixtures/task_d_miniature.json` (sha256 36cb50fe…, provenance `tests/fixtures/hand_execution_task_d.py` whose docstring's conservative readings are BINDING). DO NOT MODIFY THE FIXTURE; mismatches are adjudicated against the plan, never by regenerating.

Deliverables:
1. `src/stencil/data.py`: `task_d(config)` per the law — 4 slots at full scale, parameterized so the miniature (slots=2, L_core=256, updates=3, Q=4, gaps U{16..48}) reproduces the fixture EXACTLY (tokens, targets, update list, query metadata, no-op indices, reinsert-64 expansion). Full-scale params from config: L_core 3848, updates 12 (train; eval families: drought 3, burst 8 with the registered cluster construction (3,3,2), offsets/intra/inter bounds per the plan), Q=16 four-token query blocks, family gap bounds, USLOT 29..32 / QSLOT 60..63 / task-D distractors 50..59, separate targets array (answers NEVER in the input; PAD=0 at answer positions), gap-vector rejection (64 redraws + registered final-gap-scale fallback, occurrences counted in metadata), reinsertion expansion in final coordinates (reinsert-128: exactly 31 refresh blocks before each final multiple of 128, zero filler — exact-position test; prequery: 16 blocks + 120 trailing distractors; others: 248 trailing distractors), schedule id = (family, offset, sequence index) in CORE coordinates.
2. `src/stencil/config.py`: task "d" fields + Appendix-A-style validation (negative-case tests per rule); curriculum fields (gap-bound interpolation only; update count fixed at 12).
3. `src/stencil/oscillator.py` (or a new module honoring the registered layout): **B3k keyed latch** — four 32-dim registers (128 total), an update event `[USLOT_d][CUE_r]` overwrites ONLY slot d's register (write vector = W_e·embed of the CUE token, per-slot W_e in R^{32x256} N(0,0.02), pathway stream), queries/distractors never write; same RMS-gate readout plumbing as m1/b3. Bypass flag for the bitwise identity test.
4. Role-mask correctness: b3 (single latch) and b4 (retention) trigger on cue-range tokens (1..32) ONLY — QSLOT tokens 60..63 must not write the latch nor join b4's retained set (regression tests).
5. Event-tensor contract: fixed width 16 events / 32 positions + validity mask everywhere the cue-consuming modules or graphs touch.

## Tests first (TDD, rule 1 — per-test red, one at a time)

- `test_task_d_miniature_exact` (fixture-exact: tokens, targets, updates, queries, no-op indices, reinsert-64 expansion, seed scan chooses seed 0).
- `test_task_d_no_answer_in_input` (input stream contains PAD at every answer position; targets differ from inputs at all masked positions — non-vacuous).
- `test_task_d_fixed_shapes` (final length 4096, Q=16, event tensor 16/32 + mask, across all three families and all reinsert policies).
- `test_task_d_reinsert_positions` (reinsert-128: exactly 31 blocks, each immediately before a final-coordinate multiple of 128; prequery: one block immediately before each query).
- `test_task_d_active_rule_resolution` (constructed cases: supersession, no-op reset, per-slot independence).
- `test_b3k_slot_isolation` (an update writes only its slot's register; QSLOT tokens write nothing) + `test_b3k_gate_identity_bitwise` (bypass 1.0 recovers b0_local bitwise).
- `test_b3_b4_role_masks` (QSLOT tokens leave b3 latch and b4 retention untouched).
- Config validation negative cases. Non-vacuity counters throughout.

Run ONLY your own tests + directly touched existing ones; the orchestrator owns the full suite.

## Allowlist

taskd-generator.allow. Do not touch PLAN.md, plan/, tools/, AGENTS.md, README.md, tests/fixtures/* (read-only).

## Acceptance

Your tests green, ruff clean. No training runs.

## Ledger handoff

Do not edit the ledger. End with: files changed, per-test red/green pairs, any plan ambiguity + conservative reading, residual choices (v1.10).
