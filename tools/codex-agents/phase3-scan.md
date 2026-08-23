# Brief: phase3-scan — parallel scan for the controller cells (pre-registered optimization)

## Objective

Implement the parallel scan that PLAN.md Phase 2 test 5 pre-registers as optional and equality-gated ("The sequential loop is the oracle forever"). Motivation on the record (ledger, human ruling): the sequential per-token Python loop yields 0.20 steps/sec at (2048, 8) — the matrix projects 20-40x over the registered 72 GPU-hour budget; the human ruled optimize-then-re-pilot. Read PLAN.md Phase 2 test 5, Section 5.2, and the current `src/stencil/oscillator.py` first.

- `src/stencil/oscillator.py`: add a parallel path for `OscillatorCell` and `DecayCell` (both are linear recurrences — the oscillator's one-step map is the affine transition already written closed-form in tests/test_models.py's oracle; use `torch.associative_scan` if available in torch 2.13, else a hand-rolled log-time blocked/Blelloch scan on the 2x2 modal transitions; fp32 end-to-end, GPU-resident, no Python per-token loop). B3's cue-latch is a prefix operation (last-cue-position gather) — vectorize it too (cummax on cue-position indices, one gather; no scan library needed).
- KEEP the sequential implementation verbatim as the oracle; selection via an internal flag defaulting to the scan path in training, with the sequential path exercised by tests.
- `tests/test_models.py`: implement the registered `test_scan_equals_sequential` exactly as PLAN Phase 2 test 5 registers it: rtol 1e-5, atol 1e-8, N(0,1) inputs (batch 4, length 512, m 64), fp32, stream `fixtures:input` seed 0, both cells (+ the latch's vectorized-vs-loop equality, exact). Non-vacuity counter.
- Determinism: `test_train_two_runs_bitwise_short` and Phase 0's determinism tests must stay green with the scan path active (same-machine bitwise: the scan must be deterministic — fixed reduction order, no atomics). The bitwise M1-vs-M1b and gate-identity tests must also stay green.
- Measure and report: steps/sec at (2048, 8) batch 64 for 50 steps, scan vs sequential, on the GPU.

## Tests first (TDD, rule 1 — per-test red)

test_scan_equals_sequential written and red (scan path absent) before implementing. Run ONLY the tests your changes touch plus the new ones — the orchestrator runs the full suite after landing (do NOT run the whole 48-minute suite; three prior coders timed out doing exactly that).

## Allowlist

See phase3-scan.allow. Do not touch PLAN.md, plan/, tools/, AGENTS.md, README.md, tests/fixtures/*.

## Acceptance

New/touched tests green, ruff clean, the steps/sec comparison reported verbatim. Full suite is the orchestrator's job.

## Ledger handoff

Do not edit the ledger. End with: files changed, red/green pairs, the measured speedup, determinism argument for the scan (why reduction order is fixed), spec ambiguities, residual choices (v1.10).
