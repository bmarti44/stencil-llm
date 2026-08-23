# Phase 3 performance research — three-agent cross-review (2026-08-23)

Commissioned by human direction. Agents: Claude Opus (max effort, web research + on-machine empirical probes), codex gpt-5.6-sol @ xhigh (code close-read), kimi-k3 (independent analysis, source inlined). Orchestrator cross-ranking and the applied decision live in the ledger and tools/codex-agents/phase3-perf.md.

---
## Report A: sol @ xhigh
# Performance report

## Executive conclusion

M1’s remaining slowdown is dominated by the oscillator controller, specifically launch-heavy eager execution inside the “parallel” scan.

At batch 8, the recorded banded timings are:

- B0-local: 0.112 s/step
- M1: 0.316 s/step

That attributes roughly 65% of M1 wall time to the controller and gating path. At batch 64, 0.40 steps/s versus the roughly 1.1-step/s baseline gives the same conclusion and establishes a hard upper bound of about 2.75× if controller overhead vanished entirely.

The current scan still executes:

- 256 Python iterations to summarize blocks;
- 256 Python iterations to replay blocks;
- two oscillator cells;
- therefore 1,024 Python iterations per M1 forward, each containing several eager fp32 operations, followed by a correspondingly fragmented backward graph.

My first three actions would be:

1. Compile the oscillator controller, then the full model, with static shapes and `fullgraph=True`.
2. If compilation does not reduce controller time by at least roughly 3×, replace the two scan loops with a deterministic fused device-side scan and fixed-order backward.
3. Remove step-level graph breaks/synchronizations and CUDA-graph the complete forward/backward/clip/AdamW step.

A realistic combined target is approximately 0.7–1.0 steps/s, not the product of the individual speedups below.

Expected speedups are estimates relative to the current path and are not additive.

## Ranked recommendations

| Rank | Optimization | Expected effect |
|---:|---|---:|
| 1 | Compile controller/full model | 1.25–1.7× whole-M1 |
| 2 | Deterministic fused blocked scan if compilation is insufficient | 1.6–2.3× whole-M1 from current; smaller incremental gain after compilation |
| 3 | Capture-safe step plus CUDA Graph | 1.10–1.35× incremental |
| 4 | True block-sparse/window attention kernel | 1.05–1.20× M1; 1.3–2.0× local baselines |
| 5 | Normalize/project all gates once; pack controller GLU | 1.03–1.10× M1 |
| 6 | Fused or foreach AdamW | 1.02–1.08× |
| 7 | Cache RoPE/masks and pack QKV; remove unused outputs | 1.03–1.10× combined |
| 8 | Vectorized/prefetched data and asynchronous metric logging | 1.03–1.06× |
| 9 | B2/B4-specific obvious overheads | Potentially 1.2–1.6× for those variants |
| 10 | Two-run matrix co-tenancy | 0–20% aggregate, highly profile-dependent |

## 1. Compile the controller, then the model

The best low-intrusion experiment is `torch.compile` around [OscillatorController.forward](/home/bmarti44/stencil-llm/src/stencil/oscillator.py:470), initially without compiling the optimizer or data path.

Why it should help:

- Both 256-step loops in [OscillatorCell._forward_scan](/home/bmarti44/stencil-llm/src/stencil/oscillator.py:217) have static trip counts.
- The nine-block recursive scan has static depth.
- The four transformer layers and five attention chunks are static loops.
- Most of the scan body is pointwise arithmetic suitable for vertical fusion.
- The controller’s GLU, RMS normalization, gates, residuals, GELU, and RoPE contain many additional fusion opportunities.

For M1, the model forward has no inherent data-dependent graph break. The B4-only `.item()` branch is not taken because M1 passes `cue_mask=None` into banded attention. Static Python loops should be specialized/unrolled; the risk is an extremely large FX/AOTAutograd graph, not a semantic graph break.

Recommended sequence:

1. Compile only `model.controller` with `fullgraph=True, dynamic=False`.
2. Inspect graph breaks and generated-kernel count.
3. Try the complete `StencilTransformer`.
4. Prefer normal compilation for fusion; use manual CUDA Graph capture later rather than immediately selecting a reduce-overhead mode.

PyTorch recommends `fullgraph=True` specifically to expose graph breaks. Static loops can be specialized, while data-dependent tensor control cannot. [PyTorch compile guidance](https://docs.pytorch.org/docs/stable/user_guide/torch_compiler/compile/programming_model.fullgraph_true.html)

Determinism/fp32 risk: medium. Inductor may introduce FMA or remove intermediate roundings. PyTorch 2.13 automatically enables its deterministic compiler mode when deterministic algorithms are active, disabling numerically sensitive autotuning, but this does not promise equality with eager output. [Deterministic algorithms documentation](https://docs.pytorch.org/docs/main/generated/torch.use_deterministic_algorithms.html)

Equality gate:

- Keep the eager model callable as the oracle.
- Compare compiled/eager forward output and input/parameter gradients at lengths 512 and 2051, fp32, with `rtol=1e-5` and the existing per-operation `atol`.
- Assert every candidate output, gradient, and optimizer state remains fp32.
- Run two candidate 50-step M1 trainings and require bitwise-equal losses and final `state_dict`s.
- Retain the existing bitwise M1/M1b zero-damping and gate-identity tests.

## 2. Fuse the blocked oscillator scan device-side

If compilation does not collapse the scan adequately, the main implementation change belongs in [OscillatorCell._forward_scan](/home/bmarti44/stencil-llm/src/stencil/oscillator.py:217).

The current scan is block-parallel, but it is not launch-efficient:

- Lines 257–267 perform many eager operations 256 times.
- Lines 279–286 repeat another recurrence 256 times.
- M1 does this twice.
- Each stored `y` and `z` is later copied into a stack.
- At length 2051, padding to 2304 causes about 12% useless tail work.
- The homogeneous transition is redundantly represented across all nine blocks even though it is identical for every block.
- The nine blocks require eight logical affine compositions. [_scan_affine_2x2](/home/bmarti44/stencil-llm/src/stencil/oscillator.py:50) implements these with a depth-four recursive tree, but each mathematical composition expands into many tiny eager kernels, slices, stacks, and concatenations.

A good fused design would use:

1. One device program per `(batch, block, mode)` that loops through the 256 positions locally and emits the block affine summary.
2. One small kernel per `(batch, mode)` that serially composes the eight inter-block transitions in a fixed order. With only nine blocks, a serial device loop is cheaper than an eager recursive tree.
3. One output kernel that replays each block locally and writes the trajectories.
4. A special partial-tail path so the ninth block executes only its three or four real positions.
5. A custom backward with fixed-order reductions. Parameter-gradient atomics must not be used.

The installed internal associative-scan implementation is not sufficient: its own 2.13 source marks it prototype and unsupported by autograd. It is therefore not a drop-in training solution.

Expected speedup: 1.6–2.3× for the complete current M1 step. The theoretical ceiling is about 2.75–2.83× because the base transformer remains.

Determinism/fp32 risk: high. A Triton/CUDA backward could easily introduce nondeterministic atomic accumulation or fast-math differences. Use IEEE fp32 operations, fixed reduction trees, and no atomics. Emit per-batch/block partial gradients and reduce them deterministically.

Equality gate:

- Preserve `_forward_sequential` permanently.
- Extend `test_scan_equals_sequential` beyond its current forward-only check to compare gradients for inputs, `B`, `a_raw`, and `g_raw`.
- Test zero and nonzero initial states, both damping modes, lengths 512 and 2051.
- Use `rtol=1e-5`, `atol=1e-8` for trajectories and a justified small absolute tolerance for gradients.
- Run the candidate twice bitwise, including final parameters after a short real training.
- Re-run the JAX fixture, damping-zero bitwise, stability, and energy tests.

## 3. Make the step CUDA-graph eligible

The M1 compute graph is fundamentally captureable, but [train_model](/home/bmarti44/stencil-llm/src/stencil/train.py:162) is not captureable as written.

Current blockers and barriers:

- [masked_answer_loss](/home/bmarti44/stencil-llm/src/stencil/train.py:109) converts `torch.any(decisions)` into Python control, forcing a device synchronization.
- Boolean indexing with `logits[..., decisions]` produces a data-dependent output shape.
- `float(loss.detach())` at line 195 synchronizes every step.
- The callback performs JSON serialization and `flush()` every step.
- New GPU input tensors are allocated by `.to()` each step rather than copied into static buffers.
- AdamW uses `capturable=False`.
- The LR is a changing Python float stored in optimizer dictionaries.
- Task B can produce changing padded lengths, although the registered Task A/M matrix cells have fixed lengths.

Required changes:

- Have `Batch` carry fixed-shape decision positions and targets. Gather `[batch, decisions, vocab]` logits directly instead of using a boolean mask.
- Use static GPU token/decision buffers and `copy_` each new batch into them.
- Store the LR in a CUDA scalar tensor accepted by a capturable optimizer.
- Capture forward, selected loss, backward, clipping, and optimizer update.
- Copy losses asynchronously to a pinned CPU ring and write them in chunks. Do not call `.item()` every step.
- Keep data generation and static-buffer fills outside capture.

CUDA Graphs are appropriate here because they replay the whole kernel sequence with one CPU launch. They require fixed shapes/addresses, prohibit `.item()`, and prohibit dynamic CPU/GPU control. [PyTorch CUDA Graph constraints](https://docs.pytorch.org/docs/stable/notes/cuda.html)

Expected speedup: 1.2–1.6× on the current eager scan, or roughly 1.10–1.35× after compiler fusion.

Determinism/fp32 risk: low to medium. A graph normally replays the same kernels in the same order. The optimizer and any new loss-gather formulation are the main numerical changes.

Equality gate:

- Compare one eager and graphed step from identical model/optimizer states: loss, all gradients, optimizer states, and updated parameters.
- Require candidate-vs-oracle `rtol=1e-5`.
- Require two complete graphed 50-step runs to be bitwise identical.
- Verify chunked `metrics.jsonl` contains exactly the same ordered `(step, loss, lr)` records.
- Test capture at both registered Task A and Task M shapes.

## 4. Replace the pseudo-banded attention with true sparse attention

The current query block is 512 tokens: [Attention.__init__](/home/bmarti44/stencil-llm/src/stencil/model.py:17) sets `8 * window`.

For length 2051 and window 64, the five SDPA calls compute about 1,145,542 query-key pairs per head. Only about 129,248 pairs are actually allowed. Thus the current path still computes roughly 8.9× the ideal local-window work.

The existing GB10 sweep already tested blocks of 1, 2, 4, 8, and 16 windows and found eight windows fastest. Simply changing 512 to 64 would reduce arithmetic but lose badly to extra launches. I would retain 512 for this implementation.

The next useful step is a different kernel:

- First test PyTorch 2.13 `flex_attention` with a cached block mask for `q >= k` and `q-k < 64`.
- Use a 64-token sparse block.
- Enable the deterministic block-sparse backward metadata available in the installed 2.13 implementation.
- If fp32 FlexAttention is not competitive or cannot satisfy determinism, use a custom deterministic local-attention kernel.
- For B4, precompute padded cue positions separately; its batch-dependent global columns complicate a reusable block mask.

Expected speedup: 1.3–2.0× for B0-local/B1, but only 1.05–1.20× for M1 because attention is now about one-third of M1 wall time.

Determinism/fp32 risk: medium/high. Sparse attention changes softmax accumulation order. SDPA backends also have distinct determinism characteristics; with strict deterministic mode PyTorch selects or forces deterministic paths, but equality across backends is not bitwise. [PyTorch reproducibility and SDPA](https://docs.pytorch.org/docs/stable/notes/randomness.html)

Equality gate:

- Keep the current banded SDPA path and full-mask path as oracles.
- Retain the existing eight forward cases at `rtol=1e-5`, `atol=1e-7`.
- Add backward comparisons for Q, K, V, projection weights, and input.
- Require two short training runs to remain bitwise deterministic.
- Retain the B4 exact key-set reconstruction.

## 5. Fuse controller GLU and gate projection

Two concrete redundancies exist.

First, [project_control_gate](/home/bmarti44/stencil-llm/src/stencil/gates.py:18) recomputes the RMS normalization of the full `[B,T,128]` control tensor once per transformer layer. That is four identical square/reduce/sqrt/divide paths and four corresponding backward graphs.

Normalize once before the block loop, flatten `gate_weight` from `[L,H,128]` to `[L*H,128]`, and compute all 16 gates with one linear projection and one sigmoid. Reshape to `[B,T,L,H]`.

Second, [OscillatorController.forward](/home/bmarti44/stencil-llm/src/stencil/oscillator.py:470) performs two separate 64→64 linears for the GLU. Pack `W_a` and `W_b` into one 64→128 projection, split it, and fuse sigmoid/multiply through compilation.

LayerNorm itself is already a fused PyTorch operation. I would not replace it with a custom norm or RMSNorm—the latter changes the model. Let the compiler fuse residual/normalization epilogues where legal.

Expected speedup: 1.03–1.10× M1.

Determinism/fp32 risk: medium. Reusing one normalization changes gradient accumulation order; packed GEMMs may use a different tiling.

Equality gate:

- Compare all gates, logits, control/input gradients, and gate weights against the current functions.
- Require `rtol=1e-5`.
- Keep `test_gate_identity_recovers_baseline_bitwise` bitwise.
- Verify the packed initialization consumes exactly the same RNG values or convert existing separate parameters without changing initialization order.

## 6. Enable foreach or fused AdamW

[_optimizer](/home/bmarti44/stencil-llm/src/stencil/train.py:127) explicitly forces the slowest AdamW implementation:

```python
foreach=False,
fused=False,
```

M1 has roughly 52 parameter tensors, many tiny. The single-tensor AdamW path issues multiple kernels for each tensor. Try, in order:

1. `foreach=True, fused=False`
2. `foreach=False, fused=True`
3. `fused=True, capturable=True` for CUDA Graph capture

PyTorch 2.13 documents fp32 support for fused AdamW and describes fused as providing vertical and horizontal fusion. [AdamW documentation](https://docs.pytorch.org/docs/stable/generated/torch.optim.AdamW)

Gradient clipping already defaults to the faster foreach implementation on CUDA, so it is not the first optimizer-side target.

Expected speedup: 1.02–1.08× whole step, potentially more after the controller is accelerated.

Determinism/fp32 risk: medium. Both are eligible in fp32, but the deterministic flag is not a promise that fused output equals the old optimizer numerically. It should fail loudly for known unsupported nondeterminism, but empirical bitwise testing remains mandatory.

Equality gate:

- Feed identical synthetic gradients to reference and candidate AdamW states for 100 updates.
- Compare parameters and moment buffers after every update at `rtol=1e-5`.
- Test both weight-decay groups.
- Require two real candidate trainings to match each other bitwise.

## 7. Remove smaller recomputation and memory traffic

Specific opportunities:

- [_rope](/home/bmarti44/stencil-llm/src/stencil/model.py:37) recomputes frequencies, positions, angles, sine, and cosine independently for Q and K in every layer. Build one device/dtype-specific RoPE cache and share it across all layers.
- Banded masks and `arange` tensors are reconstructed in every layer. Cache the five local masks for a fixed run length.
- Q, K, and V are three separate projections reading the same normalized activation. A packed QKV parameter reduces GEMM launches and input traffic.
- [StencilTransformer.forward](/home/bmarti44/stencil-llm/src/stencil/model.py:325) computes a cue mask for every variant, although M1, M1b, B0, B1, and B2 do not use it in attention. Construct it only for B3/B4.
- The first oscillator cell returns and stacks its entire `z1` trajectory even though `OscillatorController` discards it.
- The model produces final-norm and LM-head logits for all 2051 positions, then trains on one Task A position or eight Task M positions. Select hidden states before final norm/head.
- The final answer token is not required as a causal input; the current trainer forwards the full token sequence and slices logits afterward.

Expected combined speedup: 1.03–1.10×.

Risk: low for mask/cue/output removal; medium for packed QKV and RoPE cache. Compute the cache on the target GPU in fp32—CPU-generated trigonometric values may not equal the retained CUDA path closely enough.

Equality gate: selected logits and all relevant gradients against the current full-logit path, plus the existing attention, Jacobian, and gate-identity tests.

## 8. Data pipeline and metric overlap

The current pipeline is entirely synchronous:

- `next_examples` creates 64 Python examples, metadata dictionaries, and padded CPU tensors.
- Task A performs roughly 131,000 scalar `torch.randint` calls per batch.
- CPU tensors are pageable.
- `.to(device)` is not nonblocking.
- The GPU is synchronized before the next batch is generated.
- Metrics are flushed every step.

Because measured data generation is 6%, its standalone Amdahl ceiling is only 1.064×. It is still worth hiding after GPU launch overhead is reduced.

Recommended change:

- Use a single deterministic producer and a two- or three-slot pinned-memory ring.
- Preserve the original generator schedule exactly.
- Copy the next batch with `non_blocking=True`.
- Drop training metadata that is never consumed.
- Vectorize draws only if a stream-continuation equality test proves that vector and scalar calls consume exactly the same RNG sequence.
- Batch metric writes and use asynchronous scalar D2H copies.

Equality gate:

- Old and new producers must emit byte-identical tokens, masks, and subsequent generator states for multiple batches.
- Run both through the exact training consumer, not merely the generator.
- Verify identical metrics ordering and no missing final chunk.

## 9. Variant-specific issues

### B2

[DecayCell._forward_scan](/home/bmarti44/stencil-llm/src/stencil/oscillator.py:349) calls the `decay` property inside both 256-step loops. The property executes `sigmoid(raw)` every time—twice per iteration in the first loop and once per iteration in the second, approximately 768 sigmoids per forward.

Hoist:

```python
decay = self.decay
```

once before both loops. Do the same in `_forward_sequential`.

This could improve B2 by 1.2–1.6× depending on its controller share. Output should remain bitwise equal; gradients may differ slightly because a single sigmoid node receives accumulated gradients.

### B4

[_forward_banded](/home/bmarti44/stencil-llm/src/stencil/model.py:99) computes:

```python
int(cue_mask.sum(dim=1).max().item())
```

once per layer, then sorts all sequence positions once per layer. That is four mandatory GPU→CPU synchronizations and four redundant sorts.

Build fixed-width padded cue-position/validity tensors once per batch, preferably on the CPU where tokens originate, and reuse them in all layers. This also removes B4’s `torch.compile` and CUDA Graph blocker.

Expected B4 gain: roughly 1.05–1.20×.

## 10. Matrix scheduling

[execute_pending](/home/bmarti44/stencil-llm/scripts/run_matrix.py:122) runs all 114 cells serially, each in a blocking subprocess.

Two concurrent runs could fill GPU launch gaps, but the earlier 94% utilization report suggests limited headroom. It may instead create context-switching and memory-pressure losses.

I would test two-way concurrency only after the single-run path is optimized:

- Measure aggregate steps/s for two representative cells.
- Require each concurrent run to reproduce a solo run bitwise.
- Cap concurrency explicitly; never derive it from CPU count.
- Preserve separate run directories and the current restart semantics.

Expected aggregate gain: 0–20%; possible regression if kernels already saturate the GPU.

## Final assessment

The scan optimization improved asymptotic parallelism but left the dominant implementation problem intact: its sequential work moved from 2051 host iterations to two sets of 256 host iterations per cell, still producing thousands of tiny eager fp32 kernels and a very fragmented backward graph.

The best near-term path is:

1. Compile the controller and inspect the generated kernel count.
2. Fuse the scan only if compilation fails to collapse those loops.
3. Remove the dynamic loss/sync/logging surfaces and graph the entire step.
4. Then pursue true block-sparse attention and gate/optimizer fusion.

No files were changed during this audit.
---
## Report B: kimi-k3
# Diagnosis (before the list)

Both variants are **launch/dispatch-bound, not math-bound**. The trunk is ~2.5 TFLOP/step fp32 (GEMMs ~0.83 fwd, banded SDPA math-path ~0.4, ×3 for bwd) — under ~150 ms of ideal GPU work on GB10. The measured 0.91 s/step baseline leaves ~0.75 s of overhead; the oscillator adds ~1.6 s on top. That delta matches its launch count: `_forward_scan` runs **two 256-iteration Python loops × ~8–12 tiny kernels × 2 cells** plus the recursive `_scan_affine_2x2` interleave (stack/flatten/cat storms) — ≈8k launches forward, and autograd re-dispatches ~2× that backward: **~25–30k launches/step on aarch64 with deterministic-mode guards**. That's the 1.6 s. Conclusions: kill launches structurally (scan rewrite) *and* kill the rest of dispatch (CUDA graphs). Everything below preserves fp32; nothing touches math semantics beyond what you already gate at rtol 1e-5.

---

## Ranked optimizations

### 1 ★ — Whole-step CUDA-graph capture of the training step
**Change:** `train.py::train_model` (new graph runner), plus its enablers: `next_examples` (pad collate to fixed `context_len=2052`, pinned staging + `non_blocking` H2D), `masked_answer_loss` (boolean indexing → `F.cross_entropy(reduction='none') * mask / mask.sum()`; boolean indexing is a host sync and a dynamic shape — both uncapturable), `_optimizer` (`AdamW(..., capturable=True)`, lr as a CUDA fp32 tensor updated via `fill_`), grads preallocated with `set_to_none=False` and zeroed **inside** the capture via `torch._foreach_zero_`, loss readback via a fixed pinned D2H memcpy node (capturable) — so exactly one sync per step remains.
**Expected:** m1/m1b: 2.5 s → ~0.3–0.45 s (**~6–8×**); baselines: 0.91 → ~0.55–0.65 s (**~1.4–1.7×**). Replay turns ~30k CPU dispatches into GPU-side scheduling at ~1–2 µs/kernel. Bonus: prefetch the next `next_examples` batch on a CPU thread during async replay → the 6% datagen cost disappears. One-time capture cost (~seconds, CPU-bound over the big scan graph — see #2) amortized over 20k steps × 114 runs.
**Determinism/fp32 risk:** Low-numeric (replays the *same* kernels cuBLAS picked under your fixed workspace config → expect bitwise vs eager). Padding to 2052 is bitwise-safe at valid positions: causal attention, position-independent LayerNorm/gates, prefix-only scans, masked loss — pad tokens contribute nothing upstream. The CE rewrite changes summation order (extra exact zeros) → ulps only. b4 caveat: `.item()` on `max_cues` in `_forward_banded`/`_banded_layout` is uncapturable; use a static cue cap (pad with `valid=false`) and gate b4 at 1e-5; m1/m1b/b0–b3 pass `cue_mask=None` to attention, unaffected.
**Gate:** (a) one eager step vs one replay step on identical static buffers → loss bitwise; (b) 128-step metric trajectory vs retained oracle (bitwise for m1/m1b/b0; rtol 1e-5 where the CE/cue-cap path changed); (c) two same-seed replay runs → bitwise `metrics.jsonl` diff.

### 2 ★ — Replace both 256-step scan loops with a table-driven LTI rollout (matmuls, not loops)
**Change:** `oscillator.py::_forward_scan` internals (keep the old path behind a flag as CI oracle); new helper shared with `DecayCell._forward_scan`. Each cell is **LTI per pair**: `s_{t+1} = M s_t + c f_t`, `M = [[1-a/d, 1/d], [-a/d, 1/d]]`, `d = 1+dt·g`, `c = (dt²/d, dt/d)`. Build a power table `M^j, j<256` by **two-level lifting** (15 sequential 2×2 matmuls for `M^r`, 15 for `E^q=(M^{16})^q`, then one broadcast matmul `E^q·M^r` → `(256, pairs, 2,2)`); `w_j = M^j·c`; intra-block response = per-pair causal convolution via a gathered `(pairs, 256, 256)` lower-tri Toeplitz and **one `bmm`** ((p, 576, 256)@(p, 256, 512) ≈ 9.7 GFLOP); inter-block = 9-step sequential recurrence with constant `M^{256}` (D = slice of conv output); combine entry-state contributions with one broadcast matmul against the table. DecayCell gets the scalar analog (batch-128 `bmm`). **Avoid trig closed forms** (sin/cos of kθ up to ~201 rad in fp32 risks >1e-5 arg-reduction error); multiply-based tables have *fewer* rounding steps than the current loop.
**Expected:** controller launches ~26k → ~1.1k/step. Eager: 2.5 → ~1.2 s (**~2×**). Combined with #1: controller replay ~free; m1 end-state ~0.35–0.45 s/step ⇒ **total ~5.5–7× on m1/m1b**.
**Risk:** Reassociated fp32 sums → expect ≤1e-6; gather backward is `scatter_add` (deterministic path exists under `use_deterministic_algorithms`); `bmm`/broadcast-matmul deterministic under your cuBLAS pinning.
**Gate:** (y,z) trajectories and grads wrt `a_raw, g_raw, B, inputs` vs current `_forward_scan` at **rtol 1e-5 / atol 1e-8**, adversarially at T=8 and T=4096 (smallest sinθ); 64-step end-to-end losses at 1e-5; `discrete_invariant` drift on m1 unchanged; `assert_stable` retained.

### 3 ★ — Run ≥2 training processes concurrently per GB10
**Change:** launch/run harness only (no code). After #1, each run is CPU-light and the GPU is far from saturated (3.2M-param model, ~8 GB peak incl. math-path attention intermediates).
**Expected:** **~1.6–1.9× fleet throughput** on the 114-run sweep; for the ~2 s-step current code, concurrency still helps during CPU dispatch stalls (~1.3–1.5×).
**Risk:** None numeric — separate processes, per-process cuBLAS workspaces, deterministic kernels; only SM/bandwidth contention.
**Gate:** bitwise-diff `metrics.jsonl` of one seed run solo vs run concurrently (must be identical).

### 4 — Fused, capturable AdamW (+foreach zero), keep the decay/no-decay partition
**Change:** `_optimizer`: `fused=True, capturable=True`. Enabler for #1; standalone value: ~560 optimizer kernels → ~40.
**Expected:** standalone ~1.02–1.05× eager (dispatch-dominated variants a bit more); mostly matters inside the graph.
**Risk:** Fused AdamW is elementwise-same-formula (no new reductions) → expect bitwise; lr as fp32 device tensor rounds identically to the eager CPU-scalar path (both downconvert the float64 lr to fp32 opmath) — verify cheaply.
**Gate:** 1-step and 32-step param trajectories vs oracle AdamW run: bitwise expected, else 1e-5; confirm `use_deterministic_algorithms` doesn't reject the fused kernel (it isn't on the nondeterministic list).

### 5 — Cache RoPE tables and banded masks/layouts (bitwise-free wins)
**Change:** `Attention._rope` (cache `(length, θ, head_dim)` cos/sin as buffers; q/k and all 4 layers share one table), `_banded_layout`/`_forward_banded` mask construction (cache the `(512, 575)` local lag mask once — it's start-invariant: `0 ≤ 63+i-j < 64` — and the 3-row tail mask).
**Expected:** ~150–250 kernels + autograd nodes saved per step (cos/sin become grad-free constants); ~1.03–1.08× eager, small but free under graphs.
**Risk:** None — identical values reused (cos/sin are deterministic elementwise); keep the **bool** cached mask for bitwise identity; an fp32 additive-bias variant is optional, 1e-5-gated.
**Gate:** bitwise on one logged step's per-layer attention outputs.

### 6 — Hoist control-path normalization; batch gate projections across layers
**Change:** `gates.py::project_control_gate` + `StencilTransformer.forward_embeddings`: `normalized_control` is layer-independent but computed 4×/step — hoist it; replace the per-layer `einsum('btc,hc->bth')` loop with one pre-loop `einsum('btc,lhc->blth')` sliced per block (same for `project_b1_gate` with `'btd,lhd->blth'`).
**Expected:** ~30–40 fewer launches and one 67 MB intermediate instead of four; ~1.02–1.04×.
**Risk:** Batched `(l·h)` strided-batched GEMM vs four single GEMMs — same K-length reduction, cuBLAS may retile → ulps at worst.
**Gate:** per-layer gate tensors vs oracle at rtol 1e-5 (bitwise likely).

### 7 — Fuse Q/K/V into one GEMM per layer
**Change:** `Attention.__init__`/`forward`: single `qkv` weight `(3d, d)` (init by drawing the three 0.02 normals in the same generator order into slices — preserves your init contract exactly), one linear, split post-RoPE.
**Expected:** 3 launches → 1 ×4 layers fwd (+bwd), better SGEMM efficiency at these skinny shapes; ~1.02–1.05×.
**Risk:** 768-K vs three 256-K GEMM kernels may differ in tile choice → ulps vs oracle per head slice.
**Gate:** q/k/v projections bitwise-hopeful, rtol 1e-5 allowed; verify init bitwise-equal at same `seed_init`.

### 8 — Contingency: `torch.compile` the `Block` trunk only (never the scan), if graph capture proves fragile
**Change:** wrap `Block.forward` (or the full trunk minus controller) with `torch.compile`, Inductor pinned: `fx_graph_cache=True`, deterministic config, autotuning OFF, cache dir checked into the run env. Explicitly exclude `OscillatorController` (512 unrolled iterations → pathological graph size).
**Expected:** fuses LN/residual/GELU/gate chains; ~1.2–1.4× on the trunk; stack it under #1's manual graphs rather than `reduce-overhead`.
**Risk:** Moderate — Inductor reduction orders differ from eager (1e-5 gate required), and cross-process kernel-cache state must be pinned to keep run-to-run bitwise; highest process-risk item, hence last.
**Gate:** trunk outputs + full grads on a fixed batch at rtol 1e-5; 64-step loss trajectory; double-run bitwise metric diff.

---

## Top 3

1. **Whole-step CUDA graphs** — the systemic fix; ~6–8× on m1/m1b, ~1.5× on baselines, enabler for the rest of the fleet plan.
2. **Table-driven LTI scan** — removes the *only* non-graphable-shaped pathology (25k→1k launches), ~2× eager and makes #1's capture small, fast, and cheap to replay.
3. **Two concurrent runs per GPU** — ~1.6–1.9× fleet-wide for ~zero code and zero numeric risk, gated by a bitwise solo-vs-paired metrics diff.

## Not recommended (specific to your constraints)
- Flash/mem-efficient SDPA backends: their backward paths are nondeterministic/blocked under `use_deterministic_algorithms(True)`; you're on the math path on purpose — keep it, just cache its masks (#5).
- TF32 anywhere (including Inductor defaults) — explicitly verify `torch.backends.cuda.matmul.allow_tf32 is False` inside compiled/graph paths.
- Triton/`associative_scan` custom kernels: autotune selection can drift across processes → breaks your run-to-run bitwise contract.
- FFT-based convolutions for the scan: cuFFT-planner and fp32 transform rounding add 1e-5-gate risk for no win over the 9.7-GFLOP `bmm`.

Implementation order: #5/#6 (bitwise, 1 day), then #4→#1 (graphs), then #2 (scan; also shrinks the capture), then #3/#7/#8 as polish. Expect the m1-class runs to land at roughly **2.5–3.5 steps/s effective fleet throughput** versus 0.40 today.
---
## Report C: Claude Opus (max) — key empirical findings (summarized by the orchestrator; measurements taken on this machine during the live pilot)

- Dispatch counts measured: b0_local 4,886 aten dispatches per fwd+bwd; m1 62,426 — the two 256-iteration Python scan loops add ~57.5k dispatches at ~23 us each; the step is CPU-dispatch-bound.
- CUDA-graph capture of m1 fwd+bwd DEMONSTRATED bitwise-identical to eager (loss and every parameter gradient; replay-vs-replay bitwise too). Gotcha solved: set_override_stale_capture_stream(True), free loss refs pre-capture. Keep AdamW outside the graph.
- Receptive-field truncation: transformer cone is L*(w-1)+1 = 253 tokens; loss reads one position/row => ~87% of transformer work provably dead for banded variants. Verified bitwise-invariant outside the cone; truncated forward matches at 1.19e-6 rel. NOT applicable to b0_full/b4. Eval keeps the full path.
- TF32 verified OFF (matmul precision "highest", allow_tf32 False; numeric probe 5.9e-7). SDPA already uses fused CUTLASS fp32 kernels (sm80 binaries on sm_121 — no native sm_121 cubins in torch 2.13).
- Chunked SSD-form scan (Mamba-2 style, chunk 64; repeated-squaring M^C; einsum drive; causal per-mode matmul) removes the residual device-side tiny-kernel floor; needs the rtol 1e-5 gate.
- Co-tenancy: zero numerics risk (contexts time-slice; kernel-internal reduction order co-tenancy-independent); gate with a bitwise solo-vs-paired metrics diff; value shrinks once the step is GPU-bound.
- foreach AdamW: deterministic but NOT assumed bitwise-identical to the single-tensor path — a real numerics shift, free only while no evidence runs exist; ledger it.
- REJECTED: FlexAttention (open fp32->TF32 regression, pytorch#161022; Triton determinism unguaranteed; ptxas flaky on sm_121a); torch.compile deferred (determinism gaps #113707/#174386, autotune nondeterminism, compile-time blowup on unrolled graphs) — revisit only if still launch-bound after the chunked scan.
- Live pilot measured 0.447 steps/s at step ~3.6k; training process at 100% CPU (dispatch-bound confirmed).
