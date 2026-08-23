# Brief: phase3-perf — apply the cross-reviewed optimization plan (human-directed)

## Objective

Apply the optimizations selected from the three-agent research at `results/perf-research.md` — READ IT FIRST, especially Report C's empirical findings (dispatch counts, the demonstrated bitwise CUDA-graph capture, the verified receptive-field truncation). Constraints unchanged and absolute: fp32; run-to-run bitwise determinism; every new fast path equality- or bitwise-gated with its oracle retained. Apply IN THIS ORDER (each with its gate green before the next):

1. **Static loss + sync removal** (`src/stencil/train.py`): decision positions computed on CPU at collate as a fixed index tensor (they sit at registered offsets); `masked_answer_loss` gathers instead of boolean-masking (bitwise-identical — assert it in a test); `lm_head`+`final_norm` restricted to decision rows (grads elsewhere exactly zero — assert); loss accumulated device-side, synced every 50 steps for metrics.jsonl (metrics values unchanged — same tensors, batched readback); kill every `.item()`/implicit sync in the step (b4's `max_cues` precomputed/padded).
2. **CUDA-graph capture of forward+backward** (`train.py`): static input buffers, capture after warmup on the capture stream with `torch.autograd.graph.set_override_stale_capture_stream(True)` and loss refs freed (Report C's recipe); AdamW + grad-clip stay OUTSIDE the graph; graph path selected by flag, eager retained as oracle. New test `test_graph_step_bitwise_equals_eager`: N steps graphed vs eager, losses and all parameter values bitwise equal (torch.equal — Report C demonstrated this holds).
3. **Receptive-field truncation** (`src/stencil/model.py`): for strictly banded variants ONLY (not b0_full, not b4), run the transformer blocks on the last `n_layers*(window-1)+1` tokens (controller stays full-sequence; gates sliced to match). Untruncated path retained as oracle; new test `test_truncated_equals_full` at rtol 1e-5, atol 1e-7 on logits at decision positions AND parameter grads, for b0_local and m1; plus the structural bitwise-invariance assertion (randomizing tokens outside the cone leaves decision logits bitwise unchanged in the full path). `evaluate.py` keeps the full path.
4. **Chunked LTI scan** (`src/stencil/oscillator.py`): replace the per-position Python loops in the scan path with the chunked matmul form — chunk C=64; `M^C` by repeated squaring; intra-chunk drive as one einsum against a precomputed (C, pairs, 2) weight; intra-chunk outputs as a causal per-mode matmul; fixed-order inter-chunk composition; hoist the `-a` negation. Sequential oracle unchanged; the EXISTING registered test 5 gate (rtol 1e-5, atol 1e-8) must pass — extend its counter if case count changes. No atomics anywhere; state the fixed reduction order.
5. **Co-tenancy** (`scripts/run_matrix.py`): `--jobs N` bounded process pool (default 1); DONE-marker semantics already make it safe. New test: pool of 2 fake fast cells completes both and writes both DONE markers (tmp dirs). The bitwise solo-vs-paired PROBE on a real short cell is the orchestrator's job — do not run training yourself.
6. **Cheap cleanups**: RoPE cos/sin cached as buffers (bitwise-identical — assert); AdamW `foreach=True` (NUMERICS SHIFT vs single-tensor path — permitted now because zero evidence runs exist; note it prominently in your handoff for the ledger).

REJECTED by the cross-review — do NOT implement: FlexAttention (open fp32→TF32 regression), torch.compile (deferred; determinism gaps).

## Tests first (TDD, rule 1 — per-test red)

Each numbered item's test red before its implementation. Run ONLY your own/touched tests plus the scan gate — the orchestrator owns the full suite. Report a timing probe: s/step for m1 and b0_local at (2048,8) batch 8, before vs after, 20 timed steps.

## Allowlist

See phase3-perf.allow. Do not touch PLAN.md, plan/, tools/, AGENTS.md, README.md, tests/fixtures/*.

## Acceptance

New/touched tests green, registered test 5 green, ruff clean, timing table reported. Full suite + gate-2 + pilot are the orchestrator's.

## Ledger handoff

Do not edit the ledger. End with: files changed, per-item red/green pairs, the timing table, the fixed-reduction-order and no-atomics statements for items 2/4, the foreach-AdamW numerics note, spec ambiguities, residual choices (v1.10).
