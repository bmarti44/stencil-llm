# Multi-IF real-eviction harness + preflight review (sol, 2026-09-03)

Target: current tree `f36c230` (harness/preflight commit `8018113`, followed only by LEG B AMENDMENT 1), governing `LEDGER-PLAN.md:554-613`, `scripts/multiif_evict.py`, `src/stencil/selector_v2.py`, `src/stencil/ledger.py`, `src/stencil/qwen3.py`, `scripts/ledger_eval.py`, `tests/test_multiif_evict.py`, and the 20 committed preflight records. Review was CPU-only; no model/GPU process was launched, no process was signalled, and the sealed IFEval input was not read. The CPU contract test passed: `6 passed in 2.17s` with bytecode and pytest-cache writes disabled.

## Findings

### EVICT-1 — CRITICAL — eviction occurs after the final query has already attended to the supposedly evicted history

The run is not a valid real-eviction experiment and must be stopped.

The registered intervention is to evict all eligible prior-history columns before the current user turn is processed (`LEDGER-PLAN.md:579-585`). Instead, `run_arm` sends the entire context—prior history, current user turn, and assistant opener—to the model in one prefill (`scripts/multiif_evict.py:321-343`). Only after that full-context forward pass does it call `cache.evict(..., keep=keep)` (`scripts/multiif_evict.py:344-355`), and it then chooses the first generated token directly from the pre-eviction logits (`scripts/multiif_evict.py:357-365`).

This is not merely a one-token discrepancy. During that full prefill, every layer appends K/V for the current user turn and assistant opener (`src/stencil/qwen3.py:177-205`); those states were computed while the full old history was visible. `KVCache.evict` later removes old columns but preserves all columns outside the drop interval (`src/stencil/qwen3.py:70-85`), including those already-contaminated current-turn/opener states. Later generated tokens can therefore recover information about evicted history indirectly through the surviving final-query K/V. The first token has direct full-context leakage as well.

The JSON instrumentation proves that physical columns were eventually removed, but cannot establish the registered temporal intervention. For example, conversation 0 records range `[4,881)`, 930 pre-eviction columns, and 53 post-eviction columns for `evicted` (`results/qwen/multiif-evict-preflight/conv-000.json:1924`, `:1928`, `:3334-3337`). Across the 20 records, all five non-echo arms necessarily have the same first generated token because their shared full-context logits are consumed before their different evictions; direct recomputation found this in 20/20 records (and the echo arm also happened to agree in 20/20). Thus the records demonstrate “delete after query prefill,” not native eviction before the query.

The CPU tests do not exercise call order: the sole eviction test checks only token-range construction (`tests/test_multiif_evict.py:33-47`), while no test asserts that `KVCache.evict` precedes current-turn prefill or first-token selection.

Required repair: split every arm at `evict_range[1]`; prefill only the prior-history prefix, evict with the arm's keep spans, then feed the current-user/opener suffix and take first-token logits from that post-eviction suffix pass. Use the same two-stage schedule for `full` (without deletion) to avoid a one-shot-vs-cached numerical confound. Add a call-order test and record/assert prefix and suffix input identities. Preserve the invalid records, but restart into a fresh output directory because a corrected harness hash cannot resume the current records.

### PROV-1 — MEDIUM — Amendment 1's 24 GPU-hour cap is absent from harness provenance and reporting

Amendment 1 changes the sole launch parameter from 12 to 24 GPU-hours and explicitly keeps the 909 cohort (`LEDGER-PLAN.md:605-608`). The code still hard-codes `<= 12.0` when writing `full_run_allowed_by_preflight` (`scripts/multiif_evict.py:892-898`), and `build_meta` has no budget-cap or amendment field (`scripts/multiif_evict.py:612-640`). Consequently, the full-run artifact will report that its launch was disallowed even though Amendment 1 authorized it; the current full-run meta likewise contains no trace of the amendment. This does not change generated outcomes, but it makes the validity/provenance report stale. Update the constant and record the amendment identity/cap when fixing EVICT-1.

### CTRL-1 — LOW — “matched random” / “after the echo clamp” overstates the implemented control construction

The control has exact, disjoint column mass after clamping to the eviction range (`scripts/multiif_evict.py:231-269`, `:756-763`), but it is not random: each control column is the deterministic nearest available column (`scripts/multiif_evict.py:247-253`). This follows the brief's explicit `matched_control_spans` instruction, so the phrase “matched random columns” in the C1 gloss (`LEDGER-PLAN.md:587`) should be narrowed rather than retroactively changing the control.

Also, control construction occurs before echo rendering (`scripts/multiif_evict.py:759-765`), and `text_ledger_context` does not reject chat-control tokens inside entries (`src/stencil/ledger.py:337-359`); therefore the worklog's “proven echo-safe” description is not mechanically true. I found zero literal Qwen chat-control tokens in all 2,714 benchmark user prompts, so this does not alter this cohort or the preflight. A fail-closed entry check would make the claimed ordering/robustness real.

## 1. Eviction layout, arm identity, controls, and instrumentation

Subject to EVICT-1's fatal timing error, the coordinate arithmetic is correct:

- `context_layout` protects the union of the global four sink columns and a leading system turn, then ends eviction exactly before the current user marker (`scripts/multiif_evict.py:124-169`). All 20 converted preflight conversations have no system prompt, and every record has protected prefix `[0,4)`. Recomputed evictable width is mean 688.25 columns, range 94–1,088.
- `run_arm` really calls `KVCache.evict(drop_start, drop_end, keep=keep)` (`scripts/multiif_evict.py:346-355`); `KVCache.evict` retains keep spans and original absolute RoPE positions (`src/stencil/qwen3.py:70-85`, `:313-317`, `:342-343`). The defect is when that call happens, not whether it happens.
- History is generated once (`scripts/multiif_evict.py:709-739`). The five non-echo arms receive the same base `context_token_ids`; `clf_pinned_echo` necessarily receives a different ID sequence containing the registered insertion (`scripts/multiif_evict.py:765-781`). Thus “identical context ids” holds for non-echo arms and as a shared underlying history, not literally across all six arms. Both base and echo IDs are recorded (`scripts/multiif_evict.py:822-840`).
- The classifier spans are clamped before column accounting, and the control is exact-count and disjoint (`scripts/multiif_evict.py:257-269`). The role comparator takes the most recent prior-user content columns and requires exactly the classifier budget (`scripts/multiif_evict.py:272-288`). Independent checks over all 20 records found zero count/range/overlap discrepancies: classifier, control, and role pin counts match in 20/20; mean classifier mass is 37.75 columns, range 15–66.
- Per-arm `pinned_cols`, `cache_cols_before`, `cache_cols_after_eviction`, and `evicted_cols` are emitted (`scripts/multiif_evict.py:370-383`) and summarized into each conversation (`scripts/multiif_evict.py:812-840`). Independent reconstruction from the recorded ranges and spans found zero discrepancies across 120 arm records. Conversation 0 is representative: 45 columns for each classifier/echo/control/role arm (`results/qwen/multiif-evict-preflight/conv-000.json:2776-2809`) and 832 physical deletions for the classifier arm (`:3522-3525`).

## 2. Selector path

The frozen selector path matches the registration:

- The copied splitter at `scripts/multiif_evict.py:67-121` is behaviorally/textually the registered splitter in `results/quick-checks/clf_score_sessions.py:19-50`.
- Only sentences from prior user turns become candidates (`scripts/multiif_evict.py:181-209`). Scores are made in one call with `role="user"` and an empty context for every sentence (`scripts/multiif_evict.py:209-217`), and the only keep rule is `score >= 0.5` (`:217`). The threshold is not exposed as a run-time CLI choice.
- `ClassifierScorer` loads the frozen encoder/head on CPU in eval mode and returns `P(rule)+P(fact)` under `torch.no_grad()` (`src/stencil/selector_v2.py:9-27`, `:29-69`). Its pair encoding exactly matches the FINAL trainer's `(no context)` plus `[user] sentence` representation (`results/quick-checks/finetune_classifier.py:69-88`). No salience finder, response, checker result, or current-turn content selects classifier pins.
- Recomputed SHA-256 values match preflight meta (`results/qwen/multiif-evict-preflight/meta.json:19-25`) and the registration (`LEDGER-PLAN.md:603`): `head.pt` = `191b3372...e3e`, `encoder/model.safetensors` = `22328135...830`, and `encoder/tokenizer.json` = `56827b4e...bc6`; config and tokenizer-config also exactly match `results/quick-checks/ft_final2_s0_sha256.txt:1-5`. The full-run meta carries the same six classifier hashes.

## 3. Scoring, contrasts, and safety

The checker path matches `scripts/ledger_eval.py`'s consumer. `_score` builds the same vendored IFEval document and seeds checker randomness from SHA-256 of `key:turn` (`scripts/multiif_evict.py:651-675`; compare `src/stencil/e2_multiif.py:16-38`, imported by `scripts/ledger_eval.py:668-675`). Truncated text is scored as-is.

The final turn is evaluated once per conversation (`scripts/multiif_evict.py:742-795`). Aged cells are the prefix whose width equals the preceding turn's cumulative instruction list (`scripts/multiif_evict.py:678-692`), the same positional convention used by the existing Multi-IF evaluator (`src/stencil/e2_multiif.py:199-205`). I independently checked all 909 rows: every instruction list is cumulative. The cohort has 896 three-turn and 13 two-turn conversations; for the latter, “last turn” means turn 2 and the turn-1 constraints are aged. This follows the harness's registered “last turn” rule (`LEDGER-PLAN.md:579`), although `LEDGER-PLAN.md:585`'s turn-3 shorthand should not be read as excluding those 13 conversations.

Each cluster is one conversation's mean aged pass rate (`scripts/multiif_evict.py:442-449`). C1, C2, C3, and descriptive echo-minus-full are formed exactly as registered (`scripts/multiif_evict.py:524-552`). The lower bound uses `stats.clustered_lower_bound`, including the one-cluster continuity penalty, and the one-sided p-value uses the matching corrected t statistic (`scripts/multiif_evict.py:452-476`; `src/stencil/stats.py:262-292`). Holm is the correct step-down procedure over only C1–C3 (`scripts/multiif_evict.py:479-493`, `:553-559`). Independent calculation with a separate incomplete-beta Student-t implementation reproduced:

| contrast | mean points | corrected 95% LB | one-sided p | Holm cutoff | pass |
|---|---:|---:|---:|---:|---|
| C3 half-gap recovery | 18.1250 | -0.0387343 | 0.0504664 | 0.0166667 | no |
| C1 echo - control | 17.0833 | -3.0826497 | 0.0921590 | 0.0250000 | no |
| C2 classifier - role | 1.2500 | -12.8798031 | 0.7569055 | 0.0500000 | no |
| descriptive echo - full | 6.2500 | -13.0786344 | 0.4408436 | n/a | n/a |

Safety counting implements the registered integers exactly: timeout count 0; truncation count at most full+1; degenerate and invalid counts at most full (`scripts/multiif_evict.py:560-595`). “Degenerate” is truncation or repeated-4-gram fraction above 0.5 (`scripts/multiif_evict.py:291-295`, `:368-378`), matching the prior probe convention. The preflight is not safety-intact: every treatment fails at least the degenerate clause, and all but `clf_pinned_echo` also exceed the truncation allowance.

## 4. Leakage and Amendment 1

I found no evaluation-to-training path. `main` reads the fixed 909-row Multi-IF file to generate and score outputs (`scripts/multiif_evict.py:847-880`); it instantiates only the already-frozen classifier and trunk. `ClassifierScorer` is eval-only/no-grad and contains no optimizer or write path (`src/stencil/selector_v2.py:9-69`). Selection consumes only prior user sentences, not labels, checker results, responses from an arm, or current-turn constraints. The classifier artifacts hash-identically before preflight and full-run meta. The harness never imports or invokes the training script.

Amendment 1 changed exactly one configuration item after the preflight: it raised the timing authorization from 12 to 24 GPU-hours because the measured projection was 22.1, while retaining all 909 conversations (`LEDGER-PLAN.md:605-608`). It did **not** change the cohort, arm set, selector/artifacts, threshold, control, contrasts, Holm alpha, generation settings, checker, or safety rule (`LEDGER-PLAN.md:609-613`). The preflight's already-viewed outcome table was recorded descriptively; it did not alter scientific configuration. PROV-1 is the remaining reporting inconsistency.

## 5. Independent preflight arithmetic

Direct aggregation of `conv-000.json` through `conv-019.json`, without calling the harness summarizer, gives:

| arm | aged pass / 53 | all-final pass / 73 | timeout | truncation | degenerate | invalid | quote |
|---|---:|---:|---:|---:|---:|---:|---:|
| full | 30 | 46 | 0 | 0 | 0 | 0 | 0 |
| evicted | 18 | 32 | 0 | 2 | 2 | 0 | 0 |
| clf_pinned | 31 | 48 | 0 | 3 | 3 | 0 | 0 |
| clf_pinned_echo | 33 | 49 | 0 | 1 | 2 | 0 | 1 |
| clf_control | 22 | 37 | 0 | 2 | 2 | 0 | 0 |
| role_pinned | 29 | 48 | 0 | 2 | 2 | 0 | 0 |

These exactly reproduce `results/qwen/multiif-evict-preflight/summary.json:4-58` and `:135-225`. The 20 record-level total times sum to 1,747.5269425765 s, hence 87.3763471288 s/conversation. The registered projection is

`87.3763471288 * 909 / 3600 = 22.0625276500 GPU-h`,

matching `summary.json:228-231` and rounding to Amendment 1's 87.4 s/conversation and 22.1 GPU-hours.

## VERDICT

**UNSOUND.** One CRITICAL, one MEDIUM, and one LOW finding. All selector, scoring, leakage, count, statistical, and timing checks otherwise reproduce, but the central cache intervention is performed too late.

**STOP THE RUN: the final query and first generated token see the full supposedly evicted history because `KVCache.evict` is called only after whole-context prefill.**
