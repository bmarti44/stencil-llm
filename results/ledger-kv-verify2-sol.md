# LEDGER-KV probe v2 — adversarial verification (sol)

Date: 2026-09-02  
Artifact: `results/qwen/ledger-kv-probe-v2/`  
Registered authority: `LEDGER-PLAN.md`, sections **LEDGER-KV**, **KV PROBE VERIFICATION**, and **FIX ROUND 2**

## Bottom line

The saved arithmetic and the central unamplified-pinning effect are reproducible. All 20 expected session files are present, every record has exactly the five registered arms, all 100 stored score vectors replay against the current vendored checkers, and every number in `summary.json` recomputes exactly from the session records.

Two claims require qualification:

1. `pinned_wave` has **13/20 degenerate sessions**, not 13/56. Twelve of the 20 sessions truncate. Its 36/56 adherence rate and 0.808 recovery fraction are valid raw arithmetic but are not creditable under the registered requirement that recovery occur without degeneracy (`LEDGER-PLAN.md:153-160`).
2. `pinned_control` fixes the v1 one-span defect—every session has 2–4 control spans with the same nominal per-span widths—but it is not exactly matched in actual surviving attention columns. Overlapping ledger spans are deduplicated while control spans are disjoint, giving pinned 1,274 columns versus control 1,290; only 5/20 sessions are exactly column-matched.

No summary-field mismatch was found.

## Scope and method

- Parsed `meta.json`, `summary.json`, and exactly `session-000.json` through `session-019.json`; there were no missing or extra session records.
- Recomputed each arm's `aged_pass`, `aged_n`, rate, truncation count, timeout count, mean stored `rep4`, and degeneracy from the session records. Degeneracy was independently derived as `truncated or rep4 > 0.5`, not trusted from the stored boolean.
- Recomputed the gap and both recovery fractions from the arm totals.
- Replayed all 100 `(20 sessions × 5 arms)` response texts through `score_row_constraints` using the corresponding frozen corpus rows. All score vectors matched. The scorer and per-row seed are at `src/stencil/causal_moments.py:193-206`; the runner's scoring/slicing is at `scripts/ledger_kv_probe.py:173-185`.
- Verified that every final-turn instruction list begins with the previous turn's full instruction list and that its length equals each record's `n_aged`; this makes the `scores[:n_aged]` slice correct in all 20 sessions.
- Recomputed all metadata SHA-256 fields against the current working tree at clean HEAD `3d036661dad3dd13bf40ed97a520a260e01d1bea`.
- Used no model inference in this verification. The checker replay and JSON arithmetic were CPU-only.

## Complete summary recomputation

`degenerate` below is a count of sessions out of 20, because degeneracy is an output/session property. Every value is exactly equal to `summary.json:22-65` before display rounding.

| arm | aged_pass | aged_n | rate | trunc | timeout | mean_rep4 | degenerate sessions | match |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| full | 41 | 56 | 0.7321428571 | 5 | 0 | 0.1019188257 | 7/20 | exact |
| evicted | 15 | 56 | 0.2678571429 | 1 | 0 | 0.0423837223 | 2/20 | exact |
| pinned | 31 | 56 | 0.5535714286 | 4 | 0 | 0.1299298469 | 4/20 | exact |
| pinned_control | 20 | 56 | 0.3571428571 | 1 | 0 | 0.0945041832 | 2/20 | exact |
| pinned_wave | 36 | 56 | 0.6428571429 | 12 | 0 | 0.5327133781 | 13/20 | exact |

Derived values, all exact matches to `summary.json:67-69` and to the formulas at `scripts/ledger_kv_probe.py:202-205`:

- `gap_full_minus_evicted = (41 - 15) / 56 = 26/56 = 0.46428571428571425`.
- `recovered_frac_pinned = (31 - 15) / (41 - 15) = 16/26 = 0.6153846153846155`.
- `recovered_frac_pinned_wave = (36 - 15) / (41 - 15) = 21/26 = 0.8076923076923079`.

All per-arm stored `aged_pass` values also equal the sum of the first `n_aged` booleans, all stored `aged_n` values equal the record-level `n_aged`, and every stored `degenerate` boolean equals the independently applied registered rule.

## Registered-contract checks

### 1. Exact five-arm set — confirmed

The amendment registers `pinned_control` as the fifth arm at `LEDGER-PLAN.md:230-235`. The runner freezes exactly `("full", "evicted", "pinned", "pinned_control", "pinned_wave")` at `scripts/ledger_kv_probe.py:29`; `meta.json:8-14` contains that exact ordered list. Every one of the 20 record-level `arms` mappings has exactly the same ordered keys. No extra or missing arm was found.

The module docstring at `scripts/ledger_kv_probe.py:8-14` still describes only four arms, but executable behavior and artifacts contain all five. This is a low-severity documentation omission, not a data defect.

### 2. No chat-template double-wrap — confirmed from the hashed runner

The corrected history path constructs one raw Qwen chat context plus `OPENER`, tokenizes that context directly, and calls `run_arm` (`scripts/ledger_kv_probe.py:150-157`). It does not call `generate_cached`, whose template wrapper caused v1. The final context uses the same raw construction at `scripts/ledger_kv_probe.py:158-162`. Metadata records `history_decode = "raw_context_greedy"` at `meta.json:20`, and the runner hash in metadata exactly matches this source.

Qualification: session records do not persist the generated history/context text or token IDs, so this check rests on the matching runner provenance rather than a direct history replay from the artifacts.

### 3. `DEGENERATE_REP4 = 0.5` — definition confirmed; requested denominator refuted

The plan registers `truncated or rep4>0.5` at `LEDGER-PLAN.md:224-234`. The runner defines `DEGENERATE_REP4 = 0.5` at `scripts/ledger_kv_probe.py:30`, applies strict `>` at `scripts/ledger_kv_probe.py:68-69`, and embeds the same rule in metadata at `meta.json:19`.

For `pinned_wave`:

- Mean of the 20 stored repetition fractions is exactly **0.5327133780891873**.
- Degenerate sessions are `{2, 3, 4, 5, 7, 9, 11, 12, 13, 16, 17, 18, 19}`: **13/20**.
- Twelve are truncated; session 17 is the additional non-truncated degeneration with `rep4 = 0.696969696969697` (`session-017.json:113-121`).
- Those 13 sessions contain 36 of the 56 aged constraint observations. Thus neither **13/56** nor a putative constraint-level interpretation is correct; it is 13/20 degenerate outputs, or 36/56 constraints exposed to a degenerate output.
- The mean `rep4` also reproduces from re-tokenizing the saved `pinned_wave` response texts. No generated model process was used.

The vivid failure mode is visible directly in, for example, session 5: `n=320`, `truncated=true`, `rep4=0.892744...`, `degenerate=true` (`session-005.json:113-121`).

### 4. `pinned_control` construction — multi-span fix confirmed; exact mass matching not confirmed

Every session has `len(control_keep) == len(keep)`, with counts 2–4; there is no n=1 session. Corresponding control and ledger spans have identical nominal widths, all control spans lie within `evict_range`, and all are disjoint from the ledger spans and from one another. This confirms the intended v1 correction in `LEDGER-PLAN.md:230-235` and the construction at `scripts/ledger_kv_probe.py:46-65`.

Actual attention-column mass differs because `run_arm` converts pinned positions to a set (`scripts/ledger_kv_probe.py:85-87`). Ledger constraint spans overlap by tokenizer boundary tokens, whereas the control constructor forces its spans to be disjoint:

- Nominal widths across all sessions: ledger 1,290; control 1,290.
- Unique surviving columns: ledger 1,274; control 1,290.
- Exact actual-column matches: 5/20 sessions (1, 2, 3, 4, 14).
- The other 15 sessions give control 1–2 extra columns; total imbalance is 16/1,274 = 1.26% relative to pinned.
- Session 0 demonstrates the mechanism: ledger spans overlap at `[17,34)`/`[33,46)` and `[135,159)`/`[158,195)` (`session-000.json:10-26`), giving 89 unique pinned columns, while the same nominal control widths are disjoint and give 91 (`session-000.json:87-112`). Session 5 similarly gives 61 versus 62 (`session-005.json:77-101`).

Therefore “same nominal widths, multi-span, near-position control” is accurate. “Mass-matched per session” is not literally accurate at the attention-column level that LEDGER-KV is intended to manipulate.

### 5. RoPE positions after eviction — confirmed, with no re-indexing distortion

`KVCache.evict` removes physical K/V columns but deliberately does not reduce `cache.length` (`src/stencil/qwen3.py:42-57`). `Qwen3.forward` obtains the next RoPE offset from that unchanged logical length (`src/stencil/qwen3.py:219-221`) and advances it by the newly processed logical tokens (`src/stencil/qwen3.py:246-247`). Pinned keys remain the original post-RoPE tensors (`src/stencil/qwen3.py:33-47`). Thus:

- surviving old keys keep their original absolute phases;
- post-eviction queries and newly appended keys continue at the original full-context positions;
- deletion changes which columns exist, but it does not re-index their RoPE positions.

The v1 re-indexing concern is therefore absent in this implementation. The v2 contexts span only 339–814 tokens, so this does not test the plan's motivating position-5,000/turn-200 regime (`LEDGER-PLAN.md:148-151`). That is a scope qualification, not an implementation mismatch.

### 6. Determinism and provenance — present pins match; metadata coverage is incomplete

All hashes present in `meta.json:3-7` match the current bytes exactly:

| field | recomputed SHA-256 | match |
|---|---|---|
| corpus | `28cdb6975c81adf472600ae13856ada21223e8aba9425b0ad5af9df5f223d540` | yes |
| model | `13bfabb5592c7b35383a56471fba1c74c771f57587322e60faaabb96268b2829` | yes |
| runner | `3202661479a58fb7673d3f2e4cd64737a3d82ec48fc5fc84a9681c4d727fce98` | yes |
| qwen3 | `5122ec09d96ed6c1e4231cdeb5efbf5e35ff927beed440560f74881d374de616` | yes |

The runner imports `stencil.determinism` before its own Torch import (`scripts/ledger_kv_probe.py:24-26,107-117`). The determinism module sets `CUBLAS_WORKSPACE_CONFIG=:4096:8` before importing Torch and enables deterministic algorithms (`src/stencil/determinism.py:8-16`). Generation is greedy, and the constraint scorer resets Python randomness per row (`src/stencil/causal_moments.py:193-205`). The current tree was clean during verification.

However, the probe metadata does not hash the tokenizer, `determinism.py`, `bench.py` (EOS and biased layers), `causal_moments.py` (scoring), `e2.py` (constraint spans), or the vendored IFEval verifier tree, even though all affect results. `FIX ROUND 2` expressly identifies `bench.py` and `determinism.py` among required provenance dependencies (`LEDGER-PLAN.md:236-247`), and the shared comprehensive pin helper shows the expected tokenizer/bench/qwen/wave/vendor pattern at `src/stencil/bench.py:143-166`. The probe's resume check compares only its incomplete metadata dictionary (`scripts/ledger_kv_probe.py:128-138`) and skips existing session files without record-level revalidation (`scripts/ledger_kv_probe.py:145-148`).

This does not produce a current-tree hash mismatch—the four recorded hashes all match, the tree is clean, and the artifacts are tracked together—but it prevents `meta.json` alone from proving all execution and scoring dependencies. Severity is medium because it weakens fail-closed provenance without changing the verified current arithmetic.

### 7. Specificity and wave credit

#### `pinned - pinned_control = +0.196`

The pooled point estimate is exact:

`31/56 - 20/56 = 11/56 = +0.1964285714`.

The per-session evidence is not driven by a single large session:

- pinned better / tied / worse: **10 / 7 / 3 sessions**;
- unweighted mean per-session rate difference: **+0.2000**;
- approximate conversation-clustered t interval: **[+0.031, +0.369]**;
- paired constraint cells: pinned-only 15, control-only 4, both-pass 16, both-fail 21 (an unclustered exact two-sided discordance diagnostic is 0.0192, not a registered confirmatory test).

So `+0.196` is a fair **descriptive paired rate difference**, and the session counts are directionally consistent with content specificity. It is not a clean exact-mass specificity estimate because actual column matching fails in 15/20 sessions. The correct claim is “+19.6 points over a same-nominal-width, slightly control-heavier non-constraint pin control.” The small imbalance may be conservative or adverse; extra irrelevant K/V columns need not have a monotone effect, so direction should not be assumed.

#### `pinned_wave`

The raw values are arithmetically real: 36/56, +21/56 versus evicted, and +5/56 versus pinned. Per session, wave is better/tied/worse than pinned in 8/9/3 sessions. But **13/20 wave outputs are degenerate and 12/20 truncate**, compared with 4/20 degenerate and 4/20 truncated for pinned. Among wave-degenerate sessions the raw score is 20/36; among the seven nondegenerate sessions it is 16/20, but post-hoc deletion of degenerate sessions is not a valid rescue because degeneration is treatment-induced.

Accordingly, the wave rate is reportable only as a raw diagnostic. It is not creditable toward the registered feasibility gate, cannot establish that amplification recovers more of the gap, and should not be used for a design decision except as evidence that dose-3 amplification is unsafe in this setup.

## Findings by severity

1. **HIGH — wave degeneracy is denominator-misstated and defeats gate credit.** The reproducible count is 13/20 sessions (36/56 constraint observations exposed), not 13/56; 12/20 truncate. This directly conflicts with the gate's “without degeneracy” condition (`LEDGER-PLAN.md:153-160`; `summary.json:58-65`). The wave's raw rate is not gate evidence.
2. **MEDIUM — `pinned_control` is not exactly attention-column-mass matched.** Multi-span and nominal-width matching are fixed, but overlapping ledger spans versus disjoint controls yield 1,274 versus 1,290 actual columns and exact matching in only 5/20 sessions (`scripts/ledger_kv_probe.py:46-65,85-87`; `session-000.json:10-44,87-112`). The +0.196 specificity label must carry this qualification.
3. **MEDIUM — metadata provenance is incomplete despite all recorded hashes matching.** Determinism, tokenizer, biased-layer/EOS definitions, span extraction, scoring, and verifier code are not hashed, contrary to the dependency-hardening principle recorded in `FIX ROUND 2` (`LEDGER-PLAN.md:236-247`; `meta.json:3-7`; `scripts/ledger_kv_probe.py:128-138`).
4. **LOW — the exact raw history and generated token IDs are absent from session records.** The matching runner proves the corrected history path, and the saved text reproduces all wave `rep4` values, but the artifacts are not independently sufficient to inspect history scaffolding or reproduce token-level repetition measurements in every arm without relying on current tokenizer/source provenance.
5. **LOW — the runner docstring omits the fifth arm.** Executable `ARMS`, metadata, and all records are correct (`scripts/ledger_kv_probe.py:8-14,29`).

No critical finding was found. No stored summary value differs from its recomputation.

Verdict: **CONFIRMED-WITH-QUALIFICATIONS** — the single most important qualification is that `pinned_wave` is degenerate in **13/20 sessions with 12/20 truncations**, so its 36/56 rate and 0.808 recovery fraction are raw diagnostics, not creditable feasibility evidence.
