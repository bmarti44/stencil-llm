# Brief: qwen3-4b-parity — diagnose and fix the Qwen3-4B trunk parity failure

## Objective
`uv run python scripts/convert_qwen3.py --model 4b` converts (398 tensors → models/qwen3-4b.pt) but parity capture
fails at scripts/convert_qwen3.py:165 with `top-1 disagreement for 'New rule: reply to "cat" with "dog". cat ->\nVariation 0:'`
(log: the orchestrator's scratchpad; reproduce it yourself). 4B config: 36 layers, hidden 2560, 32/8 heads, head_dim 128,
d_ff 9728, tie_word_embeddings True, rope_theta 1e6, rms_eps 1e-6. The 1.7B path must stay bitwise (fixture sha
005ba9424195cef19ac88924742cfa32c287890f1dad1a60a7575677769e6242).
1. Write a layer-by-layer comparison tool (scripts/qwen3_parity_debug.py, CPU or GPU): run HF Qwen3ForCausalLM and our
   trunk on the failing prompt with output_hidden_states, report the first layer where max |Δ| exceeds bf16 noise, and
   the per-block sub-step (post-attn vs post-MLP) via hooks. Suspects, in order: (a) lm_head weight source when
   tie_word_embeddings is True/False (4B ties; check the converter does not load a stale/absent lm_head); (b) the
   q_norm/k_norm per-head RMSNorm eps/dtype; (c) head_dim vs hidden/n_head assumptions anywhere (2560/32 = 80 ≠ 128 —
   Qwen3-4B's head_dim is 128 with q_proj out = 4096, NOT hidden_size); (d) rope inv_freq using head_dim; (e) MLP
   intermediate size; (f) the converter's tensor name mapping for 36 layers.
2. Fix the root cause in the smallest diff; add a CPU test on a synthetic config with head_dim ≠ hidden/n_head that
   exercises the projection shapes and the tied/untied lm_head path.
3. Re-run parity for 4B on the GPU (it is idle; check with nvidia-smi first — if a job appears, wait by re-checking,
   never by polling a lock) and record tokens/s for a 512-token greedy generation as the throughput number Brian asked
   about. Do not touch the 1.7B fixture; assert its sha before and after.

## Allowlist
See qwen3-4b-parity.allow.

## Tests first (TDD, rule 1)
RED first for the shape/tied-head test. Run ONLY: `set -o pipefail; uv run pytest -q tests/test_qwen3_config.py tests/test_qwen3_convert.py tests/test_qwen3.py -k "not gpu"` plus the new test. DO NOT run the full suite.

## GPU policy
GPU may be used for the debug comparison and the parity capture when `nvidia-smi --query-compute-apps=pid --format=csv,noheader` is empty. Foreground only; never terminate or signal any process. `.review.lock` is held by your own wrapper: never wait on it; commit your allowlisted files when done.

## Acceptance
`convert_qwen3.py --model 4b` completes with the parity fixture saved (tests/fixtures/qwen3-4b_parity.pt, all 32 prompts top-1 agree, max |Δlogit| reported); targeted tests green; 1.7B fixture sha unchanged; ruff clean; commit before finishing.

## Ledger handoff
Append to WORKLOG.md: root cause (file:line), the layer-by-layer evidence, parity numbers, 4B tokens/s, fixture shas.
