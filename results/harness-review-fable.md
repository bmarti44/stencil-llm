# Harness review — Multi-IF real-eviction harness + preflight (fable, 2026-09-03)

Scope: brief `harness-review-brief.md`; code at HEAD f36c230 (harness unchanged since 8018113: `git diff 8018113 HEAD -- scripts/multiif_evict.py src/stencil tests/test_multiif_evict.py` is empty; sha256 of
`scripts/multiif_evict.py` = cacd49c1…e197, `src/stencil/ledger.py` = 506335ab…c2d7, `src/stencil/selector_v2.py` = 491fe62e…8fd3,
`src/stencil/stats.py` = 2484b07d…7b2f — all equal to the values in BOTH `multiif-evict-preflight/meta.json` and
`multiif-evict-909/meta.json`). Everything below was done on CPU with the HF `tokenizers` file and the JSON records only;
no model, no classifier, no GPU, no process touched; the sealed `data/bench/ifeval_input_data.jsonl` was not opened.
Recompute scripts: scratchpad `recompute.py`, `inspect_records.py` (not committed).

Headline: **no harness bug that warrants stopping the 909 run.** The 909 run (pid 54507, `uv run python
scripts/multiif_evict.py --out multiif-evict-909`, started 03:56) is bitwise-reproducing the preflight: conv-000..003 of the 909
dir have identical context ids, identical history generations and identical generated ids in all six arms vs the preflight
records (greedy determinism confirmed on real records, not just claimed).

## 1. Eviction is REAL — verified

| claim | evidence | status |
|---|---|---|
| protected prefix = system prompt + 4 sink columns | `context_layout` L144-169: `protected_end = max(4, tokens(system_end))`; Multi-IF rows carry no system prompt (0/909 non-user prompt roles), so every preflight record has `protected_prefix == [0,4]` (20/20). Columns 0-2 are `<|im_start|>`,`user`,`\n`; column 3 is the first content token of turn 1 | correct as registered ("first 4 columns") |
| evictable range = everything else before the current user turn | L149 `current_marker = rfind("<|im_start|>user\n", 0, turns[-1][0])`, L162 `eviction_end = tokens(context[:current_marker])`. Recomputed for 20/20 records by rebuilding the context from the data row + recorded history texts: `context_token_ids`, `protected_prefix`, `evict_range` all identical; the prefix-encode count equals the offset-based count (`#tokens with offset.end <= current_marker`) in 20/20; `decode(ids[hi:hi+4])` starts with `<|im_start|>user` in 20/20 | correct; no BPE boundary drift (boundaries sit on special tokens) |
| `KVCache.evict` called with keep = pinned spans | `run_arm` L347 `cache.evict(*evict_range, keep=keep)`; `qwen3.py:70-85` drops `[drop_start, drop_end)` from every layer except kept sub-ranges via `index_select`; `cache.length` is NOT reduced, and `Qwen3.forward` (qwen3.py:314, 343) takes the RoPE offset from `cache.length`, so surviving columns keep their original RoPE and new tokens continue absolute positions (`position_policy: no_reindex_positions_continue` is what the code does) | real |
| identical context ids across arms | `arm_inputs` L774-781: five arms take `layout["context_token_ids"]`; only `clf_pinned_echo` takes `echo_ids`, which equal the base ids on `[0, hi)` in 20/20 (`eids[:hi]==ids[:hi]`) and share the opener tail; `echo_layout["evict_range"] == layout["evict_range"]` is asserted at L767 | as registered (echo is the one registered deviation, inside the final user turn) |
| column counts instrumented per arm | `run_arm` returns `pinned_cols`, `cache_cols_before`, `cache_cols_after_eviction`, `evicted_cols` (L379-382). Recomputed for 20 records x 6 arms: full `(n, n, 0)`; evicted `(n, n-(hi-lo), 0)`; clf_pinned / clf_control / role_pinned `(n, n-(hi-lo)+npin, npin)`; echo `(ne, ne-(hi-lo)+npin, npin)` — 120/120 match; L812-815 assert clf/control/role equality | correct |
| control is exact-column and built after the clamp | `clamp_and_match_control` L257-269 clamps to `[lo,hi)` first, then `matched_control_spans` L231-254 picks, for every pinned column, the nearest free column (tie → the later one), disjoint from pinned. Identical algorithm to the check-22 probe (`ledger_kv_probe.py:340-361`). Rebuilt from the records' `selected_spans`: `classifier_spans` and `control_spans` identical in 20/20; pinned∩control = ∅, both ⊆ [lo,hi), equal cardinality in 20/20 | correct |
| role_pinned clipped to classifier count by recency | `role_pinned_spans` L272-288: all prior-USER content columns inside `[lo,hi)`, `sorted(set)[-budget:]`, hard error if short. Rebuilt: `role_spans` identical in 20/20; role columns ⊆ prior-user-turn token columns in 20/20; |role| = |pinned| = |control| | correct |

Finding E1 (medium, disclosure — NOT a stop): **eviction is post-prefill.** `run_arm` L343 prefills the whole context (including the
current user turn and the assistant opener) with full attention, evicts at L347, and takes the FIRST generated token from the
pre-eviction prefill logits (L357). Consequences: (i) the K/V of the current-turn columns at every layer were computed while
attending to the history that is then evicted, so those surviving columns carry a compressed trace of it; (ii) the first
response token is chosen with full context in every arm. This is the same ordering as the check-22 probe
(`ledger_kv_probe.py:367-392`), so the lineage is consistent and the registered text ("Eviction = everything else before the
current user turn", "on identical context ids") is satisfied literally; but the write-up must not describe the evicted arm as
"the model never saw the history" — it saw it during prefill. The effect is common to all five eviction arms, so C1/C2 are
unaffected in expectation; C3's `full − evicted` gap is the gap of THIS eviction model. A between-turn eviction (prefill
history, evict, then feed the current turn) would be the stricter comparator for a follow-up, not a restart.

Finding E2 (low): `_token_span` L172-178 keeps only tokens with `end <= char_end`, so when the tokenizer merges a sentence's final
"." with the following newline (token `.\n`), the terminal token is left out of the span. Preflight: 2/73 candidates (ci 9 and
ci 10, span [37,68], the identical "exactly 3 bullet points … first point." sentence; decode ends `…first point`, next token
`.\n`). One column under-pinned; the control/role counts are matched to the post-clamp count so no arm asymmetry. Fix after the
run (e.g. include a token if `start < char_end` and `end > char_start`), or disclose.

Finding E3 (low, by design): with no system prompt, the 4 protected sink columns include column 3, the first content token of
the turn-1 user prompt; the clamp correspondingly removed one column from turn-1 first-sentence selections in ci 8/13/14
(unclamped 67/32/31 → pinned 66/31/30). That token survives anyway as a sink; consistent with "first 4 columns in every arm".

## 2. Selector path — verified

- Candidates = sentences of PRIOR user turns only: `select_prior_user_sentences` L191 `user_turns(context)[:-1]`; 0/73 preflight
  candidates come from the current turn; `turn` field < `last_turn` in 73/73.
- Splitter: `split_sentences` L67-121 is a reformatting of `results/quick-checks/clf_score_sessions.py:split_sentences`
  (diffed: identical control flow, identical filters — the unified diff is renames/line breaks only). Re-splitting the rebuilt
  contexts reproduces the 73 candidate texts exactly (20/20 records); sentence edges are whitespace-stripped (L195-198), the
  same `.strip()` the dev-probe scorer applied (`clf_score_sessions_ft.py:31`).
- Scored WITHOUT context, role "user": L210 `scorer(texts, role="user", contexts=[""]*len)`; `ClassifierScorer.__call__`
  (`selector_v2.py:29-69`) builds the pair `("(no context)", "[user] text")`, `truncation="only_first"`, `max_length=192` — the
  exact construction of the FINAL training script (`finetune_classifier.py:85`) and of the dev-probe scorer
  (`clf_score_sessions_ft.py:21`); head = Dropout+Linear(hidden+roles → 3), keep = P(rule)+P(fact). One classifier call per
  conversation (test `test_selector_scores_three_sentences_once_without_context` passes; `seconds.selector` sums to 1.2 s over 20).
- Threshold 0.5: L217 `score >= threshold`, default 0.5, never overridden (`evaluate_conversation` L757 passes no threshold);
  `selected_spans == [c for c in candidates if c.score >= 0.5]` in 20/20 records; meta `threshold: 0.5`.
- Artifact: `build_meta` hashes the whole `data/classifier/model/ft` tree; the five registered hashes (head.pt 191b3372…,
  model.safetensors 22328135…, tokenizer.json 56827b4e…, config d4b2c4e7…, tokenizer_config c9c2e0ff…) equal LEDGER-PLAN.md
  L603 and `results/quick-checks/ft_final2_s0_sha256.txt` byte-for-byte; the meta additionally hashes `metrics.json` (not in the
  registered list — informational). The 909 meta is identical to the preflight meta except `slice.limit` (20 → null).
- Nothing else selects: the pinned set is exactly the thresholded classifier set (verified above); the `role_pinned` arm uses
  only the classifier's COUNT; the control uses only the pinned columns' positions.

## 3. Scoring — verified

- Checkers: `_score` L658-675 → `vendor/ifeval/utils.process_results` (the same vendored module `ledger_eval.py` and
  `e2_multiif.score_turn` use; there is no second ifeval copy under `vendor/`); `langdetect.DetectorFactory.seed = 0`;
  `random.seed(sha256(f"{key}:{turn}")[:8])` = `e2_multiif.seed_of` exactly.
- Aged definition: `aged = all_scores[:len(turn_{t-1} ids)]` (L681-687). This equals `ledger.instruction_origins`'s
  positional definition (origin turn < current turn) given cumulative lists — recomputed: 0/909 rows are non-cumulative,
  so the two definitions coincide on every row. Differences from `ledger_eval.py` (disclosed, not bugs): ledger_eval's primary
  further restricts to "insertable family AND linked entry"; Leg B registers ALL aged constraints — the harness does that.
- Per-turn semantics: turns 1..T-1 are generated by the base trunk with full context (`_generate_history`, no eviction), the
  arms differ only at the last turn, and only the last turn is scored (all-final n = 73 = Σ|turn_T ids|, aged n = 53 =
  Σ|turn_{T-1} ids| over the 20 rows — recomputed from the data). 13/909 conversations have only two turns; the harness scores
  them at turn 2 with turn-1 constraints as aged (WORKLOG documents this reading). Registered text says "checked at turn 3";
  low, disclose (2-turn rows = 1.4 % of clusters).
- Contrasts: `_cluster_values` = per-conversation aged pass % (100-point scale); C1 = echo − control, C2 = clf − role,
  C3 = echo − evicted − 0.5(full − evicted), all per cluster (L524-552); `_contrast` uses `stats.clustered_lower_bound`
  (t bound minus the 100/k continuity flip, k=20 → 5.0 points) and `_one_sided_cluster_p` subtracts the same 100/k from the
  mean before the t statistic, so `p < 0.05 ⇔ lower_bound > 0` (C3: LB −0.039 ↔ p 0.0505, consistent). Holm L479-493 is a
  correct step-down (`alpha/(m−rank)` with the monotone `passed_so_far`). Independent recompute (stats.py + own t-test):
  C1 +17.083 / LB −3.083 / p 0.0922; C2 +1.250 / LB −12.880 / p 0.7569; C3 +18.125 / LB −0.039 / p 0.0505 — all equal to
  summary.json, and `summarize_records(records)` re-derived from the 20 files is `==` to summary.json.
- Safety integer clause L569-579: timeouts 0; truncated ≤ full+1; degenerate ≤ full; invalid ≤ full — as registered.
  Preflight counts recomputed: full 0/0/0/0; evicted 2/2; clf_pinned 3/3; echo 1 truncated / 2 degenerate; control 2/2;
  role 2/2 (the 11 events listed by ci in my inspection: ci 7 has all five eviction arms hit 512 tokens on a 101-column
  evictable range). Two remarks (low, science not harness): degenerate ⊇ truncated by definition (L377), so
  "degenerate ≤ full" dominates "truncated ≤ full+1" and the +1 allowance can never bite; and `registered_contrasts_pass`
  (L594) ANDs a GLOBAL `safety_intact`, stricter than the registered per-arm wording ("any arm breaching safety fails ITS
  contrasts") — final adjudication should apply the per-arm rule from `safety.checks`.
- Degenerate = truncated OR rep4 > 0.5 (probe convention); `truncated = n_generated >= 512` also counts a complete
  512-token answer (low, symmetric across arms). `detect_quoting` tokenizes the echo standalone (boundary tokens may differ
  in context) — reported-only metric; the one preflight hit (ci 11, echo arm) is a genuine near-verbatim restatement.

## 4. Leakage — verified

- The harness reads `data/bench/multiif_en.jsonl` only to build prompts and to score (`_turn_doc`); the sealed IFEval file is
  not referenced anywhere in `multiif_evict.py`; no code path writes under `data/classifier` (the scorer is load-only; the
  module has no fit/threshold-search; `metrics.json` hash in meta proves the directory is byte-stable between the two runs).
- Nothing tuned on the preflight: `git show --stat f36c230` touches only `LEDGER-PLAN.md` and `results/quick-checks/README.md`.
  AMENDMENT 1 changed exactly one thing: the preflight-gate cap 12 → 24 GPU-h (a wall-clock/budget rule, not an
  arm/threshold/artifact/contrast parameter); the cohort was not cut. The 909 meta (arms, threshold, role, context policy,
  classifier/model/tokenizer/harness/ledger/selector/stats hashes, generation settings) is identical to the preflight meta.
- Preflight-influence surface: the only remaining coupling is `main` L893-898, which still hard-codes the 12 GPU-h gate for the
  field `full_run_allowed_by_preflight` (the 909 summary will print `false` — cosmetic, see F5). The 909 run does not resume
  from the preflight directory (different `--out`; the meta `slice` differs so `_check_or_write_meta` would refuse), so it
  re-generates conversations 0-19 (~29 min); the four already re-done are bitwise identical to the preflight.

## 5. Preflight arithmetic — recomputed from the 20 records

Arm totals (aged pass / 53, all-final pass / 73): full 30 / 46; evicted 18 / 32; clf_pinned 31 / 48; clf_pinned_echo 33 / 49;
clf_control 22 / 37; role_pinned 29 / 48 — identical to summary.json, WORKLOG and AMENDMENT 1.
Seconds: Σ total = 1747.527 s (history 570.1 + selector 1.2 + arms 1176.2; per-conversation 4.4-174.1 s); mean 87.376 s/conv;
projection 87.376 × 909 / 3600 = **22.063 GPU-h** (> 12, ≤ 24). Pin counts mean 37.75 (15-66), evictable 94-1088, echo tokens
added 24-78 — matching the WORKLOG handoff. Timing extrapolation caveat (low): the 20-row slice is the first 20 rows, not a
random sample; 896/909 rows have three turns, so the mix is representative of turn count, but the 909's mean could drift if
later rows have longer prompts — the 24 GPU-h cap has ~9 % headroom.

## Findings register

| id | sev | finding | action |
|---|---|---|---|
| E1 | medium | eviction is post-prefill: current-turn columns and the first generated token are computed with full attention over the history (same as the check-22 probe) | disclose in the Leg B write-up; between-turn eviction as a follow-up comparator; no restart |
| E2 | low | `_token_span` drops a sentence-final token merged as `.\n` (2/73 preflight candidates, one column each) | fix after the run; counts remain matched across arms |
| F5 | low | `full_run_allowed_by_preflight` still gated at 12.0 (L897) after AMENDMENT 1 (24) | cosmetic; do not edit the harness while the run is live — any edit changes `harness_sha256` and `_check_or_write_meta` would refuse resume |
| S1 | low | 2-turn conversations (13/909) scored at turn 2 with turn-1 constraints as aged; registered wording says turn 3 | disclose; conservative reading already in WORKLOG |
| S2 | low | safety clause: `truncated ≤ full+1` is dominated by `degenerate ≤ full`; harness gate is global, registered rule is per-arm | adjudicate per arm from `safety.checks`; registered-design remark |
| S3 | low | `truncated` counts exact-512 complete answers; quoting detector tokenizes the echo standalone | disclose |
| O1 | info | 909 run re-generates rows 0-19 (~29 GPU-min) instead of reusing preflight records; bitwise identical so far | none (it doubles as a determinism check) |
| O2 | info | meta hashes `metrics.json` which is absent from `ft_final2_s0_sha256.txt`; the five registered hashes match | none |

Tests: `tests/test_multiif_evict.py` 6/6 pass on CPU (1.05 s).

## VERDICT: SOUND-WITH-FIXES

None of the fixes requires stopping the 909 run: E2 (one-token under-pin in ~3 % of sentences, count-matched) and F5 (a
label) are post-run patches; E1 is a disclosure about the eviction model shared with the registered probe lineage. Do NOT edit
`scripts/multiif_evict.py` while the run is live (meta hash check). The preflight totals, timing, projection, contrasts,
Holm ordering and safety counts recompute exactly; eviction, control matching, role clipping and the selector path are
implemented as registered.
