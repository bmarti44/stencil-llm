# fable review — evict-before-query fix (commit 5c743f1; docs b273da8), 2026-09-03

Scope: CPU-only code trace of `src/stencil/qwen3.py:88-131` (`prefill_with_eviction`), `scripts/multiif_evict.py:322-401`,
`scripts/ledger_kv_probe.py:60-70,112-127,166-173,385-419`, `scripts/clf_probe_check.py`, and the tests. No GPU or model
process was launched; the sealed IFEval file was not read. Verification performed: (a) `CUDA_VISIBLE_DEVICES="" pytest
tests/test_multiif_evict.py tests/test_ledger_kv_probe.py tests/test_no_side_effect_imports.py` -> 37 passed, 1 skipped
(the GPU bitwise test, "CUDA unavailable"), 1 xfailed; (b) a scratch CPU script using a 2-layer random-weight
`Qwen3Config` (fp32, real Qwen3 tokenizer, real `KVCache`/`prefill_with_eviction`/`context_layout`/
`tokenized_eviction_range`/`current_turn_start`/`multiif_evict.run_arm`) — results quoted below.

Note on the environment: PID 54538 (`scripts/multiif_evict.py --out multiif-evict-909`) started 03:56, i.e. BEFORE
commit 5c743f1 (04:14). It is the invalid post-prefill run (its `meta.json` has no `eviction_timing`; 46 records +
meta at review time) that WORKLOG says is to be stopped on Brian's approval. Untouched by this review. The corrected
harness cannot resume into that directory (meta mismatch), and its default output directory differs, so there is no
collision hazard; but the queued GPU bitwise test will keep skipping until the GPU has no compute PIDs.

## Answers to the brief

**(1) Current-turn ids (and echo text) absent from the cache when `KVCache.evict` runs — every arm.** Yes.
The pre-query path runs `model(tokens[:, :history_end])`, then asserts `cache.length == history_end` AND
`cache.k[0].shape[2] == history_end` (`qwen3.py:118-122`) — with a fresh `KVCache` this proves exactly the first
`history_end` ids are cached at eviction time. `multiif_evict.run_arm` builds a fresh cache per arm (`:338`) and
derives `history_end` from the last `<|im_start|>user\n` in `tokenizer.decode(ids)` (`:347-351`), so for
`clf_pinned_echo` (ids = `echo_layout["context_token_ids"]`) the echo, which `text_ledger_context` places inside the
final user turn before its `<|im_end|>` (`src/stencil/ledger.py:350-359`), is at index >= `history_end` and is
prefilled only after eviction. The evict range for the echo arm is asserted identical to the base one
(`multiif_evict.py:785`). Probe: `run_arm` uses `history_end = evict_range[1]` for every last-turn arm including
`full`/`full_echo` (evict_range is passed for all arms; only the helper's `evict_range` argument is nulled for the
full arms, `ledger_kv_probe.py:395-407`); the probe's `echo_context` also inserts via `text_ledger_context`, and the
main loop asserts the evicted text is identical across base/echo ids (`:659-660`). CPU check on the test context and
its echo variant: `context_layout` evict end = probe `tok_last` = run_arm `history_end` = `current_turn_start` = 49
for both; token before the boundary decodes to `'<|im_end|>\n'`, token at the boundary to `'<|im_start|>'`;
decode/encode round trip exact. The stub-trunk test (`tests/test_multiif_evict.py:180-227`) mechanically asserts the
call order prefill(history) -> evict -> prefill(current) with the current ids unseen at eviction.

**(2) Position continuity.** Correct. `Qwen3.forward` takes `offset = cache.length` (`qwen3.py:360`) and sets
`cache.length = offset + t` (`:389`); `KVCache.evict` never touches `length` (`:71-85`) and the helper asserts it
(`:125-128`). So history gets positions `0..history_end-1`, the current turn `history_end..N-1`, generation `N..` —
exactly the one-shot positions. The attention mask uses `past = cache.k[layer].shape[2]` (surviving columns) with
`triu(diagonal=1+past)` over `(t, past+t)` (`:245-258`), so every current-turn row sees all surviving/pinned columns
plus its causal current-turn prefix. CPU check: two-stage evicted+keep prefill vs history-prefill/evict/token-by-token
decode of the current turn agree to 4-6e-6 (fp32 reduction-order noise), same index_map, same final `length`
(66/78) and same column count (29/41); `pinned_cols` semantics unchanged (pins are within `evict_range`, so no pin can
fall in the now-absent current-turn part of `index_map`).

**(3) Full-arm two-stage vs one-shot.** Mathematically identical: same token ids, same positions, same causal
visibility, same weights; only the matmul batching (M dimension) differs. CPU fp32 tiny model: `torch.equal` on the
last-row logits is True (max diff 0.0) for base and echo contexts. On the GPU (bf16 matmuls, fp32 attention math;
the 1.7B config takes the non-SDPA path since `n_head*head_dim == d_model`, `qwen3.py:202`), cuBLAS may pick
different kernels/split-K for different M, so bitwise equality is likely but not guaranteed. The queued test
`test_full_two_stage_prefill_logits_bitwise_equal_one_shot` must show `torch.equal(two_stage[:, -1], one_shot[:, -1])`
on the real bf16 model. If it fails, report the max |diff| and whether the argmax agrees; a sub-ulp bf16 difference
would NOT invalidate the harness (all six arms and the history turns now share the same two-stage schedule, so the
within-run contrasts are confound-free, which is what sol's EVICT-1 asked for), but the word "bitwise" in WORKLOG
would then have to be narrowed to "argmax-identical / within tolerance" per the AGENTS.md rule.

**(4) Protected prefix, evictable range, keep/control spans, column counts.** Unchanged in meaning. `context_layout`
and `tokenized_eviction_range` are untouched; the eviction still acts on the columns `ids[0:history_end]`, which
are the same physical columns the one-shot cache held at those indices. `pinned_cols` is computed from the same
`index_map` restricted to keep spans; `cache_cols_before = len(ids)` and `cache_cols_after_eviction =
history_columns_after + (len(ids) - history_end)` equal the old post-prefill measurements for every last-turn arm
(verified arithmetically and on CPU: 49 -> 12 history columns + 17/29 current tokens). Probe `cache_cols` remains the
post-generation measurement. The probe's protected prefix (first-user content) vs the harness's (system prompt + 4)
differ as before — pre-existing, not part of this fix.

**(5) Meta timing flag and resume refusal.** Harness meta hard-codes `"eviction_timing": "pre-query"`
(`multiif_evict.py:656`); `_check_or_write_meta` compares the whole dict (`:661-666`), so an old directory (no key,
old harness hash) refuses to resume — covered by `test_meta_records_prequery_and_rejects_other_timing`. Probe: the
`--eviction-timing` flag (default pre-query, legacy `post-prefill`) flows into `build_meta` and `run_arm`
(`ledger_kv_probe.py:69,123,615,700`), and the exact-meta check at `:623-628` refuses old directories the same way.
The helper's `post-prefill` branch reproduces the old ordering exactly (`qwen3.py:110-115`). Flags/defaults tested.

**(6) Boundary choice.** Registered: "Eviction = everything else before the current user turn" (LEDGER-PLAN.md:583)
and "Protected prefix = system prompt + first 4 columns". History ending immediately before the final
`<|im_start|>user\n` — so including the prior assistant `<|im_end|>\n` — is the registered semantics, and it is the
same endpoint the pre-fix `evict_range[1]` already used, so no coordinate in any record changes meaning.

## Findings

### FIX-1 — LOW — `run_arm` column arithmetic is wrong on the `history_end == 0` path (not persisted)
`prefill_with_eviction` returns `(columns, columns)` — the FULL column count twice — when `history_end == 0`
(`qwen3.py:104-109`), but `multiif_evict.run_arm:373` treats the second value as history-only columns and adds the
current-turn length. CPU run on a first-turn context of 15 ids: `cache_cols_before 15, cache_cols_after_eviction 30,
evicted_cols -15`. This path is only reached by `_generate_history` for turn 1, which copies only text/ids/n/timeouts
(`:741-749`), so no record carries the wrong numbers. Fix: return `(0, 0)` from the empty-history branch (its
docstring should say the two counts are history columns), or measure `int(cache.k[0].shape[2])` in `run_arm` after
the helper returns (that is also the "claim what you measure" form for the last-turn arms).

### FIX-2 — LOW — no assertion that `history_end == evict_range[1]` in `multiif_evict.run_arm`
The split is re-derived by decode/re-encode (`:347-351`) while the evict range comes from `context_layout` on the
original string. They agree (CPU check above, and the round trip is exact for this tokenizer), but if they ever
diverged the failure mode is asymmetric: `history_end < evict_range[1]` trips `KVCache.evict`'s bounds assert,
`history_end > evict_range[1]` silently leaves un-evicted history columns. One line — `if evict_range is not None and
evict_range[1] != history_end: raise AssertionError` — makes it fail-closed both ways. (The probe already uses
`evict_range[1]` directly, so it is not affected.)

### FIX-3 — LOW — probe meta `schema` still 3 after adding `eviction_timing`
`ledger_kv_probe.build_meta` gained a key but keeps `"schema": 3` (`:117`). Harmless for resume (exact-dict
compare) but any downstream reader keyed on schema cannot distinguish pre-/post-fix directories except by the key's
absence. Bump to 4 or document.

### FIX-4 — INFO — the GPU bitwise test lives in the unit suite and loads the full 1.7B model
`tests/test_multiif_evict.py:229-274` is skip-guarded by `nvidia-smi` compute-PID emptiness (and CUDA availability),
so it is safe under the current run, but it silently skips whenever anything holds the GPU; the sealed claim in
WORKLOG must cite an actual non-skipped pass. `clf_probe_check.py` is import-safe (work under `main()`; the
side-effect inventory test passes with it present).

## VERDICT: SOUND-WITH-FIXES
The ordering defect (EVICT-1) is fixed for every arm in both harness and probe: eviction provably precedes any
current-turn/echo prefill, positions and masks are the one-shot ones, the coordinate system is unchanged, and the
timing is recorded and enforced on resume. The three fixes above are low-severity hygiene (a non-persisted arithmetic
slip, a missing fail-closed assertion, a schema number); none changes generated outputs. The remaining open item is
evidence, not code: the GPU bitwise test must actually run (non-skipped) once PID 54538 is gone, and the WORKLOG
wording adjusted to whatever it measures.
