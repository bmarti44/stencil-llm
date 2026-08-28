# Brief: phase3-banded — banded windowed attention (equality-gated optimization, human-ruled)

## Objective

Replace the full quadratic masked SDPA in the window-64 attention path with a banded implementation of the SAME mathematics, under the same discipline as the registered scan optimization (ledger, Human Touchpoint 3 round 2). Read `src/stencil/model.py`'s attention, PLAN Section 5.1, and the scan precedent in `src/stencil/oscillator.py` first. Profile fact: b0_local costs 0.152 s/step at batch 8 seq 2051 — the attention is the wall.

- Banded attention for the window-64 variants (all except b0_full; b4's cue-global positions are a banded kernel PLUS gathered global columns for cue positions — implement both): block/unfold the sequence into overlapping chunks so each query attends its 64-token causal window (and, for b4, the cue positions), computing only O(T·w) scores instead of O(T²). Keep fp32; no approximations; the softmax over exactly the same key set as the masked implementation.
- KEEP the full-mask implementation verbatim as the oracle, selected by an internal flag (default banded in training; oracle exercised by tests) — mirror the scan's pattern.
- New test `test_banded_equals_masked_attention`: both paths on N(0,1) inputs (batch 4, length 512 AND a length-2051 case, m per config), fp32, stream `fixtures:input` seed 0, for b0_local, b1, m1, and b4 (its global-cue columns included): allclose rtol 1e-5, atol 1e-7, plus an exact same-key-set structural assertion (the banded mask reproduces the oracle mask row-for-row on a small case). Non-vacuity counters.
- Determinism: the banded path must be deterministic (fixed chunking by sequence length, no atomics); `test_train_two_runs_bitwise_short`, Phase 0 determinism, and the bitwise gate-identity/damping-zero tests must stay green with banded active. NOTE: the exact-zero Jacobian proof (test 7) runs on the model — verify it still passes with the banded path active for at least one (variant, seed, N) case in your own run; its full run is the orchestrator's.
- Measure and report verbatim: s/step at (2048, 8) batch 8 for b0_local and m1, banded vs masked, plus the implied full-batch-64 steps/sec.

## Tests first (TDD, rule 1 — per-test red)

New equality test red before the banded path exists. Run ONLY your own/touched tests — the orchestrator owns the full suite (do not run it; prior coders timed out doing so).

## Allowlist

See phase3-banded.allow. Do not touch PLAN.md, plan/, tools/, AGENTS.md, README.md, tests/fixtures/*.

## Acceptance

New/touched tests green, ruff clean, the timing table reported. Full suite + gate-2 are the orchestrator's job.

## Ledger handoff

Do not edit the ledger. End with: files changed, red/green pairs, the timing table, the determinism argument, spec ambiguities, residual choices (v1.10).
