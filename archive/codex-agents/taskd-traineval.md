# Brief: taskd-traineval — Task D training loss, multi-family eval, sealing, report

## Objective

Complete the Task D pipeline per `plan/taskd/PLAN-TASKD.md` (read in full; the metrics and decision-table definitions are frozen to the token). The generator from the previous pass is landed and fixture-verified; build on it, do not restructure it.

1. **Registered clarification (implement + test; ledgered by the orchestrator): refresh blocks never split a query block** — if a reinsert-128 final-coordinate multiple falls inside a 4-token query block, the refresh inserts immediately BEFORE the block's QRY token instead (deterministic, applies to prequery trivially). Update the exact-position test accordingly (multiples not inside query blocks keep exact positions; displaced ones sit at the QRY boundary; count preserved at 31).
2. **Training** (`src/stencil/train.py`): task-"d" separate-target loss — cross-entropy of `logits[p]` vs `targets[p]` at the Q=16 operand positions (non-vacuity: assert targets ≠ input tokens at every masked position, count==16×batch); curriculum per the plan (gap bounds only, linear integer interpolation, floor, steps 0-8k→12k); CUDA-graph path must remain bitwise (extend `test_train_two_runs_bitwise_short` with a task-d case; the graph consumes the fixed 16/32 event tensors + validity mask).
3. **Eval** (`src/stencil/evaluate.py`): multi-family loop — for each of {id-control, drought, burst} at the VALIDATION offset and, separately gated, the FINAL offset (eval_seed_offset×2+1): 10,000 sequences, per the frozen metrics: sequence-weighted exact-match; accuracy by core-coordinate decision-axis bins ([0,64],(64,128],(128,252],(252,512],(512,1024],(1024,2048],(2048,∞)) with numerators/denominators recorded; accuracy vs global update count; first-crossing survival with the NA rule; error-conditioned stale-slot excess with the registered null (|{superseded-rule outputs ≠ active}|/15 over wrong answers); tail(c, family, seed) as defined in V1; injected-token overhead. All written per family into eval.json. **Sealing**: the final-offset eval REFUSES to run unless `results/TASKD-FLEET-FROZEN` exists (created only by the orchestrator after all training/retry decisions); test the refusal.
4. **Cells + report**: `scripts/run_matrix.py` cells `d:{contender}:s{seed}` for m1, m1b, b2, b3k, b3, b4, reinsert128, prequery (reinsert policies as b0_local-class configs); `scripts/make_report.py` Task D section rendering the per-family curves, adoption-reliability column, cost axis, and the decision-table inputs (NOT the verdict — the orchestrator applies the decision procedure and documents it).

## Tests first (TDD, rule 1 — per-test red)

Loss non-vacuity; bitwise two-run with task d; per-metric hand-computed miniatures (esp. the stale null and survival-NA rule); sealing refusal; refresh-displacement rule; matrix cell enumeration (24 cells, exact keys). Run only your own/touched tests.

## Allowlist

taskd-traineval.allow (src/*, scripts/*, tests/*, configs/*, caches). Do not touch PLAN.md, plan/, tools/, AGENTS.md, README.md, tests/fixtures/*.

## Acceptance

Your tests green, ruff clean. No training runs — pilots are the orchestrator's.

## Ledger handoff

Do not edit the ledger. End with: files changed, red/green pairs, metric-formula locations, ambiguities + conservative readings, residual choices (v1.10).
