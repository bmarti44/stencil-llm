# Evict-before-query fix review (sol, 2026-09-03)

Target: code commit `5c743f1`, documentation commit `b273da8`, and the accepted EVICT-1 finding in `results/harness-review-sol.md`. This was a CPU-only review: no GPU/model process was launched, no process was signalled, and the sealed IFEval input was not read.

## Findings

### EVICT-1 — formerly CRITICAL — RESOLVED

The current user turn can no longer attend to history that its arm is supposed to evict. The shared helper now executes history prefill, optional eviction, current-turn/opener prefill, then generation (`src/stencil/qwen3.py:88-131`). In the pre-query path, only `tokens[:, :history_end]` reaches the model before `cache.evict`; the helper additionally requires both the absolute cache length and physical history-column count to equal `history_end` before eviction (`:118-126`). Only after eviction does it submit `tokens[:, history_end:]` (`:129-130`). The first generated-token logits therefore come from the post-eviction current-turn/opener pass, closing both the direct first-logit leak and the surviving-current-turn-K/V leak described by EVICT-1.

No new high, critical, medium, or low finding was found in this fix.

## 1. Every arm, including echo arms

`scripts/multiif_evict.py:792-812` routes all six registered arms through the same corrected `run_arm`. `full` passes no eviction but still uses the two-stage schedule; `evicted`, `clf_pinned`, `clf_control`, and `role_pinned` evict between stages; `clf_pinned_echo` supplies the echoed IDs and the recomputed-but-equal history range. `run_arm` derives `history_end` immediately before the final `<|im_start|>user\n` and delegates the only prefill to the shared helper (`:343-362`). Thus the final user IDs, rendered echo, final user terminator, and assistant opener are all in the second slice.

The probe paths have the same property. Every registered probe arm, including `echo_only`, `pinned_echo`, and `full_echo`, reaches `prefill_with_eviction` at `scripts/ledger_kv_probe.py:385-416`; echo arms use `echo_ids` and `echo_evict_range` at `:690-701`. The copied classifier probe forwards its selected timing and echoed IDs/range through that same path (`scripts/clf_probe_check.py:134-148`). Full/full-echo skip deletion but use the same split; all deleting arms call `KVCache.evict` before any current-turn ID is submitted.

The committed stub test makes the order observable: it sees exactly history prefill -> eviction -> current prefill and asserts the current IDs have not been seen at eviction (`tests/test_multiif_evict.py:180-228`). An independent tokenizer audit over all 20 preserved preflight records found 20/20 with `evict_range[1]` equal to the final-user split, byte-identical base/echo history ID prefixes, and the preceding assistant `<|im_end|>\n` on the history side.

## 2. Absolute positions and RoPE

`KVCache.evict` deliberately does not reduce `cache.length` (`src/stencil/qwen3.py:70-85`), and the helper asserts that invariant around the deletion (`:124-128`). `Qwen3.forward` takes its RoPE offset from `cache.length` and advances it only by the number of newly submitted tokens (`:359-363`, `:388-389`). Therefore, if the history boundary is `H`, current-turn token `j` receives absolute position `H+j` even though the physical K/V cache contains fewer than `H` surviving history columns. Subsequent generated tokens start after the complete original prompt length.

A CPU tensor check independently confirmed that `_rope(S, offset=H)` is bitwise equal to the suffix `H:H+S` of `_rope(H+S, offset=0)`, while physical eviction leaves `cache.length == H`. The stub contract also observes the second prefill entering with unshortened offset 4 and ending with absolute length 6.

## 3. Full-arm equivalence and the queued GPU proof

The full arm's split is logically equivalent to one-shot causal prefill. Causality makes the history states independent of the later suffix; the suffix then sees all unchanged history K/V plus its own causal prefix. Its RoPE positions are identical by the `cache.length` argument above. Using this same two-stage schedule for `full` also removes schedule as a between-arm confound.

Bitwise identity is still an empirical GPU-kernel claim, not something the CPU review can certify. The queued test at `tests/test_multiif_evict.py:250-277` must pass `torch.equal` between the complete final-prompt vocabulary-logit vector from one-shot prefill and the vector returned by two-stage full-arm prefill on the pinned bf16 Qwen3 trunk and test context. Equality of argmax or tolerance-based closeness is insufficient. A failure must block the corrected launch and be investigated; a pass establishes the registered first-generation decision is bitwise unchanged. The test was intentionally not run in this review under the CPU-only rule.

## 4. Ranges, spans, and column accounting

The fix does not change `context_layout`, protected-prefix construction, selector spans, clamp-before-control logic, role spans, echo rendering, or the six-arm table. The protected prefix remains `[0, max(4, system_end))`, and the evictable range remains `[protected_end, final_user_marker)` (`scripts/multiif_evict.py:141-170`). Classifier, exact-count disjoint control, and role spans are still constructed before arm execution (`:232-289`, `:774-799`) and their equality assertions remain (`:830-833`). The old-to-new map is still produced by the unchanged `KVCache.evict` and is used for pinned-column accounting (`:363-370`).

The Multi-IF count fields preserve their prior prompt-level meaning. If `T=len(ids)`, `H=history_end`, and eviction deletes `D` history columns, the new code reports `cache_cols_before=T` and `cache_cols_after_eviction=(H-D)+(T-H)=T-D` (`scripts/multiif_evict.py:372-399`), exactly the old one-shot-before/delete-after totals. They are now reconstructed from asserted invariants rather than sampled from a temporally post-query cache. `pinned_cols` and `evicted_cols` are unchanged algebraically.

## 5. Timing provenance and resume refusal

The fixed harness writes `eviction_timing: pre-query` into exact meta (`scripts/multiif_evict.py:629-657`), defaults to the fresh `multiif-evict-909-prequery` directory (`:41-50`), and refuses any existing meta that differs (`:661-666`, called before model loading at `:883-893`). The CPU test demonstrates a pre-query meta cannot resume as post-prefill (`tests/test_multiif_evict.py:280-286`).

The probe exposes only the two allowed timing values, defaults to pre-query, records the selected value, and applies the same exact-meta refusal (`scripts/ledger_kv_probe.py:60-78`, `:112-139`, `:610-628`). The copied classifier probe also records and reports the selected timing (`scripts/clf_probe_check.py:25-37`, `:167-182`).

## 6. Boundary versus the registration

Yes. `LEDGER-PLAN.md:579-585` defines eviction as everything eligible before the current user turn and puts echo inside the final user turn before its `<|im_end|>`. The implemented split is immediately before the final `<|im_start|>user\n`; because generated history is serialized through the prior assistant's `<|im_end|>\n` before that marker (`scripts/multiif_evict.py:753-771`), that terminator remains in history. The final user text, inserted echo, final user close, and assistant opener are all post-eviction. The explicit boundary statement in `WORKLOG.md:2542-2544` is therefore an accurate clarification of the registered semantics, not a semantic amendment.

## Verification

- `34 passed, 1 deselected` for `tests/test_multiif_evict.py tests/test_ledger_kv_probe.py` with CUDA hidden, bytecode disabled, pytest cache disabled, and the GPU equality test deselected by name.
- Targeted Ruff passed; the commit diff passed `git diff --check`.
- Independent CPU checks passed for the tokenizer boundary, base/echo history identity, echo/opener placement, `KVCache.length`, and suffix RoPE equality. No repository file other than this review was written.

## VERDICT

**SOUND.** EVICT-1 is resolved. The corrected launch remains conditioned on the queued GPU test demonstrating exact `torch.equal` full-arm final-prompt logits; that pending execution is a validation gate, not a defect found in the code.
