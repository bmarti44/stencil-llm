# H1′ (FOCUS LADDER v1, automatic selection) — empirical verification, fable, 2026-09-02

Scope: results/qwen/ledger-kv-probe-h1p/ (meta.json, summary.json, session-000..019.json) produced by
scripts/ledger_kv_probe.py --focus auto at cd73dad. PROVENANCE level: every number below was recomputed on CPU
from the 20 session records with my own python (vendored IFEval checkers via stencil.causal_moments.score_row_constraints,
the cd73dad helpers loaded from `git show cd73dad:scripts/ledger_kv_probe.py`, the tokenizer, and the corpus).
No GPU or model process was launched; no repo file was edited. Scripts: scratchpad recompute_h1p.py, heldout_refit.py.

Provenance hashes: ledger_kv_probe.py at cd73dad, salience2.py, salience2_weights.json and the corpus all match meta.json.

## 1. Recompute — 0 mismatches

| quantity | recomputed | summary.json |
|---|---|---|
| context_token_ids == tokenizer(decoded context); evict_range; history_token_ids | 20/20 exact | — |
| decoded context contains "Constraint:" | 0/20 | — |
| keep spans from a fresh `focus_span_records(..., focus="auto")` replay (shipped weights) | 20/20 identical | — |
| control_keep from `matched_control_spans`; equal column mass; zero overlap; spans inside evict range | 20/20 | — |
| echo_context_token_ids, echo_text_sha256, echo_tokens_added | 20/20 | — |
| n_aged (oracle records on the rebuilt marked context; == len(id_list) − marks in last prompt) | 20/20 | — |
| auto_coverage / auto_extra | 20/20 | mean 0.9667, extra 7 |
| score vectors, 7 arms × 20 sessions (140 checker calls) | 140/140 | — |
| text == decode(generated_token_ids); n; truncated; rep4; invalid_output; degenerate; quoting; cache_cols; pinned_cols | 140/140 | — |
| aged passes full/evicted/pinned/control/echo_only/pinned_echo/full_echo | 44/14/37/18/37/48/46 of 56 | same |
| trunc / degenerate / invalid per arm | 1-2-1, 0-1-1, 0-0-0, 1-2-0, 0-1-1, 0-1-0, 1-2-1 | same |
| contrasts +23 / +23 / +11 / +19 / +2; gap 30; recoveries 0.767 / 0.767 / 0.367 / 0.633 / 0.067 | same | same |
| paired bootstrap pinned−control (seed 0, 2000) | mean 0.342 [0.167, 0.508] | same |
| safety table (integer clause) | all 7 arms safe | same |

Per-session recomputed aged passes (full/evicted/pinned/control/echo_only/pinned_echo/full_echo):
s0 3/0/2/0/2/4/3 · s1 2/1/2/1/2/2/2 · s2 2/0/2/0/2/2/1 · s3 2/2/2/2/2/2/2 · s4 1/0/0/1/1/2/2 · s5 3/1/3/1/2/3/3 · s6 3/0/2/1/2/3/3 ·
s7 2/0/0/0/1/2/2 · s8 2/1/2/1/3/3/3 · s9 3/1/2/1/2/3/3 · s10 1/0/1/1/2/2/2 · s11 3/1/3/1/2/2/3 · s12 2/2/2/2/2/2/2 · s13 2/1/1/1/2/2/2 ·
s14 1/0/2/0/1/2/1 · s15 3/2/2/2/2/2/3 · s16 3/1/2/2/3/2/3 · s17 1/0/2/0/0/3/1 · s18 2/1/3/1/2/3/2 · s19 3/0/2/0/2/2/3.

Additional statistics (mine, not in the artifact). Paired constraint-level fix/break, two-sided exact sign test:
pinned vs control 22/3 (p<0.001); pinned vs evicted 23/0; echo_only vs evicted 25/2; pinned_echo vs echo_only 13/2 (p=0.007);
pinned_echo vs pinned 12/1 (p=0.003); echo_only vs pinned 9/9 (p=1.0); full_echo vs full 3/1 (p=0.63); pinned_echo vs full 10/6 (p=0.45).
Session-paired bootstrap of the per-session rate difference (95%): pinned−control +0.34 [0.17, 0.51]; pinned_echo−echo_only
+0.19 [0.07, 0.32]; pinned−evicted +0.42 [0.28, 0.55]; echo_only−evicted +0.42 [0.30, 0.53]; full_echo−full +0.03 [−0.04, 0.12];
pinned_echo−full +0.08 [−0.04, 0.21].

## 2. Findings

### F1 — none (verified): mark isolation holds in the code at cd73dad and in the artifact
- Generation contexts: `strip_constraint_marks` is applied to every prompt before turn-1..T-1 history generation and to the
  last prompt (probe_cd73dad.py:610, :623); `focus_span_records` raises if "Constraint:" is in the context in auto mode (:241);
  main asserts `strip(marked_context) == context` (:629). The 20 decoded contexts contain no "Constraint:" (my check).
- Finder input: `extract_instructions` runs per user turn on the unmarked context only (:249-251); the marked mirror is
  consumed solely by `auto_selection_metrics` (:654) and `oracle_focus_records` for `n_aged` (:651) — both are scoring-side
  (which constraints count as aged), not selection-side. Eviction range comes from `<|im_start|>user` markers (:144-154);
  the exact-column control is derived from the auto `keep` (:643); echo spans are the auto records (:635). No path from the
  oracle spans into any arm's context, pins, eviction range or control — verified by replaying the whole selection from
  the decoded contexts and matching all 20 keep sets and all 20 control sets.
- Dead code, harmless: `echo_context` still cuts at " Constraint:" (:298, :302-303); in auto mode no such string exists.
- LOW (disclosure, not a leak): the corpus reminder "Every earlier constraint from this conversation still applies to this
  reply as well." is NOT a mark and survives stripping; it is present in the turn-2 and turn-3 prompts of every arm
  (it is also in `full` and `evicted`). The base task is therefore an explicitly reminded task; the contrasts are unaffected.

### F2 — MEDIUM: coverage 0.967 is the finder re-finding its own training positives; mitigated by a held-out refit
- src/stencil/salience2.py:837 `load_b3_docs` defaults to ("train-v43", "cal-v45", "mt-train-300.jsonl") and
  `training_docs` (:1105-1113) uses that default; `main` (:1217-1229) fits the shipped `salience2_weights.json` on it. All 300
  rows of mt-train-300.jsonl carry split "train", so the 20 H1′ sessions' constraint sentences were positives in the
  finder's training set. "Automatic" in H1′ therefore means "no oracle marks at runtime", not "unseen distribution".
- Mitigation (CPU, my heldout_refit.py): refitting on the FULL default corpus reproduces the shipped weights bit-for-bit
  (max |Δw| = 0.0 — the fit is deterministic, as the module claims). Refitting WITHOUT mt-train-300.jsonl (10,746 clauses,
  5,597 positive) and replaying the selection on the 20 unmarked contexts gives IDENTICAL keep spans in 20/20 sessions,
  coverage 0.967 and 7 extras. So the selection does not depend on having trained on these sessions — it depends on the
  clause cues, which the same synthetic template family (train-v43 / cal-v45) also supplies. H1′ is in-distribution
  automatic selection, not a generalization test; that is fine for the rung as registered but must be worded that way.
- What the finder actually picked (all 20 sessions inspected): every oracle clause except the two
  "write the whole reply in lowercase letters only" (s5, s16), where it emits only " in lowercase letters only" (<50 %
  token overlap → uncovered by the metric, though the echoed fragment still carries the instruction), and four bullet
  clauses trimmed before ", each starting with '* '" (s4, s7, s16, s17 — counted as covered). All 7 "extra" spans are the
  same turn-2 framing sentence "Now add a brief closing section for the same newsletter piece." (s0, s7, s10, s12, s15, s16, s18).
  Net: the H1′ focus set ≈ oracle set − 2 half-clauses + 7 framing sentences.

### F3 — MEDIUM: "same 20 sessions" holds at the corpus level only; H1 and H1′ contexts differ in every session
- Because turn-1/2 prompts are stripped before history generation, the model's turn-1/2 responses differ: decoded H1
  context with marks removed ≠ H1′ context in 20/20 sessions; context length changes e.g. s1 486→683, s14 866→1022,
  s11 579→441 tokens. The pinned column mass also shrinks from 1,274 (H1, e2 reader incl. label/bleed tokens) to 932
  (H1′, clause-bounded) — and `pinned` still improves (33→37).
- Consequence: full 44 vs 41 and evicted 14 vs 15 are not paired comparisons on identical inputs. Per-session `full`
  deltas H1→H1′: s6 +1, s9 +1, s10 −1, s16 +2, s18 −1, s19 +1 (net +3; s16 was a degenerate `full` history in H1).
  This is noise on a re-generated base task, not a mark-stripping effect on the task's difficulty. H1′ is a replication on
  regenerated histories with an automatically bounded focus set, which is a fair (arguably stronger) reading, but the
  ledger wording "same 20 sessions" should say "same 20 corpus rows; histories regenerated from unmarked prompts".

### F4 — outcome under the registered H1′ rules, applied literally: ADVANCE-RETENTION
- pinned 37 > pinned_control 18 ✓ (fix 22 / break 3; session-paired 95 % [0.17, 0.51]).
- pinned_echo 48 > echo_only 37 ✓ (fix 13 / break 2, p = 0.007; [0.07, 0.32]).
- pinned_echo recovers (48 − 14)/30 = 1.133 ≥ 0.85 ✓. Sensitivity: dropping the degenerate-but-passing s4 pinned_echo
  output (rep4 0.79, a looped placeholder list scored 2/2) gives 46/56 → 1.07, still ≥ 0.85.
- Safety, integer clause, in-job: timeouts 0 in every arm ✓; truncation events ≤ full + 1 = 2: max 1 ✓; degenerate ≤ full
  = 2: max 2 ✓ (pinned_echo 1); invalid_output ≤ full = 1: max 1 ✓ (pinned_echo 0). All four conditions hold → ADVANCE-RETENTION.
- LOW caveats on the clause, not the result: (i) `full` itself carries 1 trunc / 2 degenerate / 1 invalid (s14 512-token
  truncation; s17 "* * *" invalid output in full/evicted/echo_only/full_echo), which gives every arm headroom under a
  "≤ full" clause; pinned_echo would still pass at trunc 0 / invalid 0, but its 1 degenerate session would fail against a
  clean `full`. (ii) The checkers reward degenerate loops (s4 pinned_echo 2/2 at rep4 0.79; s17 `full` 1/3 on "* * *" via the
  bullet counter). Register a degenerate-excluded sensitivity for the 909 rather than re-litigating here.
- Not claimable: "pinned_echo above the full ceiling" (1.13 of gap). Constraint-level fix 10 / break 6 vs full, p = 0.45;
  session-paired [−0.04, +0.21]. Same over-claim as H1; do not repeat it.

### F5 — LOW: full_echo − full = +2 is noise; nothing detectable in the non-evicted regime
Fix 3 / break 1 (p = 0.63); session-paired [−0.04, +0.12]. The quoting-excluded rates (0.872 vs 0.786) are a composition
artefact (excluding the 6 literal-type sessions removes the harder postscript/title sessions from the numerator). Reading:
recency/re-injection adds nothing measurable when the history is already resident; the product's whole effect in this
harness is recovery under eviction (echo_only +23, pinned +23, pinned_echo +34 of a 30-pass gap). This is the
"retention/re-injection, not amplification" qualification the publish gate already requires — H1′ supplies its evidence.

### F6 — LOW: quoting flags are required literals again; not an echo-leak signal
Quoting 6/20 echo_only, 7/20 pinned_echo, 6/20 full_echo. Every matched 8-token run is the literal string a constraint
requires: "P.P.S. Do not forget ..." (s0, s2, s8, s18) or an exact "<<title>>" (s8, s10, s12, s14). Every quoting session has
a postscript/title aged constraint; s15/s19 (title constraints) do not trigger only because the response's title tokenizes
differently (upper-cased in s15; "<<A" at response start in s19 vs " <<A" in the echo) — the 8-token metric is
tokenization-sensitive. Quoting vs non-quoting pass: echo_only 0.75 vs 0.63, pinned_echo 0.90 vs 0.83, full_echo 0.71 vs
0.87 — no consistent direction. The checkers see only the response; the echo lives in the prompt. Same verdict as H1 (F3
there): report quoting per constraint type or carve out required literals; "pass_rate_quoting_excluded" is not a de-leak rate.

### F7 — HIGH (for the next step, not for H1′): the shipped finder is trained on the Multi-IF 909 prompts and is weak off-distribution
- salience2.py:898-909 `load_multiif23_docs` reads data/bench/multiif_en.jsonl — 909 rows, i.e. the registered P cohort
  (LEDGER-PLAN.md:316 "Multi-IF 909 cohort") — and labels EVERY turn-2/3 clause a positive (only the HAND_CLAUSES sentences are
  excluded). A 909 text_ledger confirmation run with salience2_weights.json therefore measures an in-sample finder; its
  registered "coverage ≥ 0.90" is not an automatic-selection result until a held-out refit is used (the b3 held-out refit
  in F2 shows the fit is cheap — 1 s on CPU — and, on b3, selection-invariant; Multi-IF may not be).
- The BFCL harness handoff (WORKLOG, bfcl-harness) reports finder recall 78/100 on the pinned BFCL labels with 1/23 on user
  instruction sentences (77/77 schemas admitted automatically). Off the synthetic/Multi-IF template families the finder
  finds ~4 % of user instructions; Leg A would be blocked by the finder, not by the mechanism.

## 3. Verdict on the H1′ reading: CONFIRMED-WITH-QUALIFICATIONS
Every number in summary.json reproduces from the records (0 mismatches). The registered decision rules, applied literally
with the integer-count safety clause, give ADVANCE-RETENTION; the four registered contrasts are real (sign tests p ≤ 0.007,
session-paired lower bounds > 0). Qualifications that must travel with the result: (a) automatic = no runtime marks on an
in-distribution synthetic corpus whose finder was trained on the same template family (and on these rows; a held-out refit
reproduces the identical selection, so no memorization, but no generalization either); (b) histories were regenerated, so
H1 and H1′ are not paired and the 44-vs-41 ceiling is noise; (c) 1.13 of the gap is not "above ceiling"; (d) full_echo − full
is null; (e) quoting = required literals. The orchestrator's "all four ADVANCE-RETENTION conditions hold" is correct as written.

## 4. Ranked next step toward the PUBLISH GATE
1. (c) FIRST, CPU-only, hours, 0 GPU-h: refit the linguistic finder with Multi-IF turn-2/3 EXCLUDED (and, for the record,
   b3 excluded — F2 shows that changes nothing on H1′), hash the held-out weights, and measure 909 coverage of the aged
   FIXABLE constraints with them. If coverage ≥ 0.90, register that weight hash for the 909 run. If < 0.90, the finder —
   not retention — is the open problem and no GPU-hour should be spent on either leg until it is fixed (the BFCL 1/23
   user-instruction recall says the same thing from the other side).
2. (a) THEN the Multi-IF 909 text_ledger confirmation on 1.7B (~30 GPU-h) under ROUND 7, with the held-out finder weights,
   a degenerate-excluded sensitivity, and quoting reported per constraint type. This is the already-registered successor of
   H1′ ADVANCE-RETENTION and directly serves Leg B; it is the right first GPU spend.
3. (b) BFCL Leg A preflights only after the finder recall floor (≥ 0.80 on the 100 BFCL labels; currently 0.78 with 1/23
   user spans) is met without touching the labels — otherwise the sealed cohort would be spent on a finder failure.
