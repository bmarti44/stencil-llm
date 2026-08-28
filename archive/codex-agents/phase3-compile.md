# Brief: phase3-compile — scoped torch.compile on the scan region (human-directed: target ~3-day matrix)

## Objective

The M1-class runs dominate the matrix (~150 of ~220 projected GPU-hours) and their GPU time is thousands of tiny scan-composition kernels (GPU 95% busy but latency-bound). Fuse them with a NARROWLY SCOPED torch.compile — the deferred lever, now de-risked empirically. Read results/perf-research.md (Report C's compile risk notes: pytorch#113707, #174386, autotune nondeterminism) and src/stencil/oscillator.py first.

1. Compile ONLY the scan path (the blocked-scan function(s) inside `OscillatorCell`/`DecayCell`) — never the whole model, never the training step: `torch.compile(fn, fullgraph=True, dynamic=False)` with `torch._inductor.config.deterministic = True` (and the `TORCHINDUCTOR_DETERMINISTIC=1` env in the trainer), autotune OFF (no max-autotune; `coordinate_descent_tuning=False`). Compiled path behind a flag, default OFF until the orchestrator's probes pass; eager blocked-scan retained (it is itself gated against the sequential oracle).
2. CUDA-graph compatibility: the compiled region must be capturable inside the existing step graph (cudagraph-safe: no dynamic shapes, no CPU syncs). If capture + compile conflict, fall back to compile-outside-graph for the scan region and graph the rest — measure both arrangements.
3. Tests: (a) `test_compiled_scan_equals_oracle` — compiled scan vs the SEQUENTIAL oracle at the registered test-5 tolerance (rtol 1e-5, atol 1e-8), same registered cases; (b) `test_compiled_scan_deterministic` — two invocations in-process bitwise; the cross-PROCESS cold-cache bitwise probe is the orchestrator's. (c) `test_train_two_runs_bitwise_short` must pass with the compiled flag ON.
4. Timing hooks only (a small benchmark script or flag) — do NOT run timing measurements; the projection-of-record pilot owns the GPU. The orchestrator times after it completes.

## Tests first (TDD, rule 1)

Equality/determinism tests red (flag absent) before implementing. Run only your own/touched tests (CPU-heavy parts fine; keep GPU usage brief — a pilot run owns the GPU).

## Allowlist

See phase3-compile.allow. Do not touch PLAN.md, plan/, tools/, AGENTS.md, README.md, tests/fixtures/*.

## Acceptance

New tests green (compiled flag on), ruff clean. No timing claims.

## Ledger handoff

Do not edit the ledger. End with: files changed, red/green pairs, compile configuration exactly as set (all inductor flags), the capture-compatibility finding, residual choices (v1.10).
