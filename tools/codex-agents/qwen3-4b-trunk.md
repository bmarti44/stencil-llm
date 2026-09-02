# Brief: qwen3-4b-trunk — generalize the hand-rolled trunk to Qwen3-4B without changing 1.7B behaviour

## Objective
Brian (2026-09-02): use a larger model for the agentic stage if it does not slow the program. Make the trunk
model-agnostic across Qwen3 dense sizes so Qwen3-4B runs through the SAME code path (bias hooks, deficit
gate, KVCache.evict/pin, attn_probe) with bitwise-unchanged 1.7B results.
1. src/stencil/qwen3.py: replace the class-constant `Qwen3Config` with an instance-based config
   (`Qwen3Config.from_hf(path_to_config_json)` → n_layer, n_head, n_kv_head, head_dim, d_model, d_ff, vocab,
   rope_theta, rms_eps, n_ctx, tie_word_embeddings). `Qwen3(cfg)` and `KVCache(cfg)` take the config; keep a
   module-level default `QWEN3_1_7B = Qwen3Config.from_hf(ROOT/"models/qwen3-1.7b-hf/config.json")` so every
   existing call site (`Qwen3()`, `KVCache()`) keeps working unchanged. Untied lm_head must be supported
   (Qwen3-4B ties embeddings; Qwen3-8B does not) — read `tie_word_embeddings` and load `lm_head.weight` when
   present. Update the 4 external `Qwen3Config.*` references.
2. scripts/convert_qwen3.py: `--hf-dir` and `--out` flags (defaults = current 1.7B paths). Conversion for
   Qwen3-4B → models/qwen3-4b.pt from models/qwen3-4b-hf (the orchestrator is downloading it; if the directory
   is absent when you get there, implement + test with a tiny synthetic config and say so).
3. Parity: extend the existing 32-prompt parity capture (tests/fixtures/qwen3_parity.pt, scripts/b0_score_parity.py
   or the test that owns it) so a `--model` selects the fixture; capture a Qwen3-4B fixture ONLY if the GPU is
   idle (see policy); the 1.7B fixture must remain byte-identical (assert its sha256 before and after).
4. Tests (CPU): config parsing for 1.7B and 4B config.json (values above; 4B: 36 layers, d_model 2560, 32/8 heads,
   head_dim 128, d_ff 9728, vocab 151936); a 2-layer synthetic-config forward on CPU proves shapes/GQA repeat
   and that an (h,t,T) attn_bias broadcasts per head; KVCache.evict with a non-default n_layer.
Do not change any numerics for 1.7B: run tests/test_qwen3_parity* (or the owning test) as the regression gate.

## Allowlist
See qwen3-4b-trunk.allow.

## Tests first (TDD, rule 1)
RED first. Run ONLY: `set -o pipefail; uv run pytest -q tests/test_qwen3*.py tests/test_kv_pin.py tests/test_deficit_gate.py tests/test_ctrb.py -k "not gpu"`
plus whichever CPU test owns the parity fixture. DO NOT run the full suite.

## GPU policy
Another registered job may hold the GPU (H1′). Before ANY GPU call run
`nvidia-smi --query-compute-apps=pid --format=csv,noheader`; if non-empty, skip GPU steps (parity capture for
4B, GPU pin test) and say so in the handoff — they will be run by the orchestrator. Foreground only; never
terminate or signal any process. `.review.lock` is held by your own wrapper: do not wait on it; commit your
allowlisted files directly when done.

## Acceptance
Targeted tests green; 1.7B parity fixture sha unchanged; ruff clean on touched files; `Qwen3()` with no args
still loads models/qwen3-1.7b.pt strict=True; no edits outside the allowlist; commit before finishing.

## Ledger handoff
Append to WORKLOG.md: files touched, RED->GREEN evidence, the 1.7B fixture sha before/after, whether the 4B
conversion/parity ran (with nvidia-smi evidence) or was deferred, and the measured tokens/s if any GPU step ran.
