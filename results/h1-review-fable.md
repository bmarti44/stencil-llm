# H1 (FOCUS LADDER v1) artifact review — fable, empirical verifier, PROVENANCE level

Date: 2026-09-02. Scope: results/qwen/ledger-kv-probe-h1/ (meta.json, summary.json, session-000..019.json),
scripts/ledger_kv_probe.py @ HEAD (sha256 fddd7d14… == meta.provenance["ledger_kv_probe.py"] == `git show 9c7e1ac`),
registered text LEDGER-PLAN.md:342-370 (FOCUS LADDER v1 / H1), orchestrator reading WORKLOG.md (last entry, ~17:20).
Method: every number below was recomputed on CPU from the 20 session records with my own code
(scratchpad recompute_h1.py: own tokenizer decode, own "Constraint:" span extractor, own echo renderer, own
IFEval scorer call, own rep4/truncation/degeneracy/quoting, own contrasts and bootstrap). No GPU or model process
was launched, no process was signalled, no repo file other than this report was written.

## 0. Recompute result: NO MISMATCH

| check | result |
|---|---|
| 20 sessions x 9 arms = 180 arm-records; all 9 arms present in every record; meta.max_new 512; summary head == meta | OK |
| `text == tok.decode(generated_token_ids)` | 180/180 |
| score vectors re-scored with vendored IFEval (random.seed(key), key = corpus key*10+T) | 180/180 identical |
| aged_pass == sum(scores[:n_aged]); n_aged == len(turn T-1 instruction list); cumulative-order assumption | 20/20 holds |
| truncated == (n >= 512); rep4 recomputed; degenerate == truncated or rep4>0.5 | 180/180 |
| context re-tokenised from history_token_ids + last prompt + OPENER == context_token_ids; evict_range | 20/20 |
| keep spans == my own "Constraint:" extractor's aged spans | 20/20 |
| echo: my render (header + "- span") inserted before final `<|im_end|>` == echo_context_token_ids; sha256 == echo_text_sha256; echo_tokens_added; eviction text identical under echo; no chat-control tokens | 20/20 |
| quoting flag (8 consecutive tokens of the echo text in the response) | 180/180 |
| per-arm aggregates (pass, n, rate, trunc, timeout, mean_rep4, degenerate, quoting_rate, quoting-excluded rate) | 9/9 arms exact |
| gap 26; contrasts +18/+21/+10/+13; recovered fractions 0.692/0.808/0.385/0.500; pinned_echo 31/26 = 1.192 | exact |
| best wave = d3.0 (rate 0.679), wave_killed True, 0.885 | exact |
| paired bootstrap pinned − control (seed 0, 2000): mean 0.2375, CI [0.0708, 0.3958] | exact |

Per arm (recomputed): full 41/56, evicted 15/56, pinned 33/56 (trunc 2), pinned_control 20/56, echo_only 36/56,
pinned_echo 46/56 (trunc 1), wave d0.5/1.0/3.0 = 31/36/38, truncations 2/3/11, degenerate sessions 2/4/12.
Quoting rate 8/20 = 0.40 in both echo arms; quoting-excluded 20/33 = 0.606 (echo_only), 27/33 = 0.818 (pinned_echo).
All 9 arms ran in one job (single meta, single provenance block, per-session records carry all 9 arms), max_new 512.

Additional paired statistics (session-unit bootstrap seed 0; exact two-sided sign test on discordant constraints):

| contrast | mean/session | 95% CI | sessions +/−/0 | fix/break | sign p |
|---|---|---|---|---|---|
| pinned − evicted | +0.329 | [+0.183, +0.467] | 13/1/6 | 20/2 | 0.0001 |
| echo_only − evicted | +0.379 | [+0.250, +0.504] | 14/0/6 | 21/0 | <0.0001 |
| pinned_echo − echo_only | +0.171 | [+0.062, +0.287] | 9/1/10 | 13/3 | 0.021 |
| pinned − pinned_control | +0.237 | [+0.071, +0.396] | 11/2/7 | 19/6 | 0.015 |
| pinned_echo − pinned | +0.221 | [+0.121, +0.333] | 10/0/10 | 14/1 | 0.001 |
| pinned_echo − full | +0.079 | [−0.017, +0.183] | 6/2/12 | 10/5 | 0.30 |
| echo_only − full | −0.092 | [−0.192, +0.000] | 2/7/11 | 6/11 | 0.33 |
| wave d0.5 − pinned | −0.042 | [−0.117, +0.033] | 1/3/16 | 1/3 | 0.63 |
| wave d1.0 − pinned | +0.058 | [+0.000, +0.125] | 3/0/17 | 3/0 | 0.25 |

## 1. Findings (graded)

### F1 — HIGH: the registered safety clause is NOT met literally; ADVANCE-RETENTION cannot be claimed as written
LEDGER-PLAN.md:356-357 registers "truncation excess over `full` <= +2 pts". Recomputed: full 0/20 truncations;
pinned_echo 1/20 (session 16) = +5.0 pts; pinned 2/20 = +10 pts; wave d0.5/1.0/3.0 = +10/+15/+55 pts. Timeouts 0
(OK), degenerate sessions pinned_echo 1 <= full 2 (OK). The WORKLOG entry reports "Safety: timeouts 0; pinned_echo
trunc 1, degenerate 1 (<= full's 2)" and never applies the truncation-excess clause. Decision rule 1 requires
"with safety intact"; rule 2 (RE-INJECTION-ONLY) requires echo_only >= 0.85 (it is 0.81); rule 3 is "every other
outcome" → the LITERAL registered outcome is FAIL / DO NOT ADVANCE.
Mitigation (post hoc, must be recorded as such): at n = 20 the clause has 5-pt granularity, i.e. it is a
zero-truncation rule, which no pinned arm satisfied (and which `full` itself would fail in a harness where the
history is degenerate, see F3). The single pinned_echo truncation is session 16, where `full` is ALSO degenerate
(15 tokens of "* * *", rep4 0.67) — the same failure mode, run to the cap. Under the ROUND 7 convention
(truncated scored as fail) the reading is unchanged: pinned_echo 45 vs echo_only 36, pinned 30 vs control 20,
recovery (45−15)/26 = 1.15. So the SUBSTANTIVE reading survives; the REGISTERED reading does not. The honest
label is "ADVANCE-RETENTION conditional on an amendment of the truncation clause (count-based, e.g. <= full + 1 at
n = 20, or measured at n >= 50)", registered before the next rung, not silently.

### F2 — MEDIUM: "pinned_echo above the full ceiling (1.19)" is over-claimed
pinned_echo − full: 10 fixes / 5 breaks, sign p = 0.30, session-paired CI [−0.017, +0.183]. It is
indistinguishable from `full`, not above it. Two non-leak explanations account for the +5: (i) `full` is not a
ceiling — it has no re-injection (recency) and its history is greedy 1.7B output that is itself degenerate in
sessions 16 and 17 (second assistant history turn = 19 tokens of "* * *"; `full` then emits 15/19 tokens and
scores 1/3 in each). Excluding those two sessions: full 39/50, pinned_echo 42/50, echo_only 32/50, evicted 13/50.
(ii) Session 17 alone contributes full 1 vs pinned_echo 3. Recommend the WORKLOG wording "1.19 — above the full
ceiling" be replaced by "recovers the whole in-job gap; not distinguishable from full (p = 0.30)".

### F3 — MEDIUM: the "quoting" metric does not measure echo parroting; the quoting-excluded rate is a composition artefact
All 16 quoting flags (8 sessions x 2 echo arms) match 8-grams that are the LITERAL strings the constraints
demand: postscript lines ("P.P.S. Do not forget next week's plan", s00/s02/s18) and exact titles
("<<Cataloguing River Pebbles, Briefly>>", s08/s10/s12/s14/s15). Every quoting session has a postscript or
title constraint in its aged set; no non-literal session quotes. Zero responses in any arm contain "Constraint",
the ledger header "Earlier user instructions restated verbatim", or the reminder sentence (one wave d3.0 response
contains "still applies" — that arm has no echo). So there is no evidence of the echo leaking into the response
beyond required literals, and no evidence that the verifier rewards anything the echo places in the prompt
(the checkers see only the response). Quoting vs non-quoting pass: echo_only 16/23 = 0.696 vs 20/33 = 0.606;
pinned_echo 19/23 = 0.826 vs 27/33 = 0.818. The echo_only difference is constraint-type composition (title 6/6,
postscript 3/4 in echo_only), not leakage. Consequence: "pass_rate_quoting_excluded" systematically drops the
literal-type constraints and should not be read as a de-leaked rate; the registered definition (>= 8 echoed
tokens) needs a carve-out for literals required by the constraint (or report quoting per constraint type).

### F4 — MEDIUM: the registered rule text cites a secondary descriptive number as "the 113-slice text_ledger result"
LEDGER-PLAN.md:368 "+2.8 pts pooled, p=0.012" is results/qwen/ledger-eval/summary.json
`secondary_all_constraints_descriptive.text_vs_base` (all 650 constraint outcomes incl. non-aged; n01 38 / n10 20;
McNemar labelled `_exploratory`). The registered eligible-only (aged, linked) text-vs-base is n01 5 / n10 1 on
n = 85 (+4.7 pts, exploratory p = 0.109); conversation-clustered lower bound −3.1 (text_vs_base_all_eligible_clustered),
i.e. not significant at the registered unit. Any RE-INJECTION-ONLY reading that leans on "+2.8, p = 0.012" should say
"descriptive, all-outcome, exploratory".

### F5 — LOW/MEDIUM: the "verbatim" echo spans bleed
The span extractor's token window (a < end and b > start) includes the leading-space " Constraint" token of the
NEXT clause and, for the last clause of a turn, the reminder sentence "Every earlier constraint from this
conversation still applies to this reply as well." Rendered echo lines therefore read
"-  Constraint: use the word 'tallow' no fewer than 2 times. Constraint" (s00; 4 entries = 109 tokens). Same
bleed is in the pinned KV columns (pinned_cols 89 for 4 short clauses). Harmless for H1's internal contrasts
(all arms share the marks) but it is not "byte-for-byte the aged spans", and it inflates the token/column cost
of both re-injection and residency. Fix the window (b <= end) before the automatic-selection replication.

### F6 — LOW: exact-column control confirmed (Q5)
All 20 sessions: |control columns| == |pinned columns| (dedup, clipped to evict_range), disjoint, inside the
eviction range; arm records pinned_cols identical for pinned / pinned_control / all wave arms; no control span
contains "Constraint" text. Note the control is the nearest-neighbour columns, i.e. adjacent prompt/answer text:
it BEATS pinned on style constraints (english_capital 3/5 vs 0/5, bullet lists 2/4 vs 0/4) while pinned wins
on content constraints (placeholders 7/7 vs 0/7, postscript 4/4 vs 0/4, frequency 3 vs 0). The specificity
claim holds overall (+13, p = 0.015) but style-format adherence rides on neighbouring assistant text, not on the
constraint clause.

### F7 — LOW: wave rule applied correctly; the "d0.5 safe" wording is loose
Best dose by (rate, −degenerate) = d3.0 (38/56) with 12/20 degenerate → killed. d1.0 36 > 33 with 4/20 → killed.
d0.5: 2/20 degenerate (not > 2, so passes the wave rule; equals full's 2 for the degenerate clause) but 31 < 33
(1 fix / 3 breaks) — and it still fails the +2-pt truncation clause (2/20 truncations, +10 pts). d1.0 − pinned is
3 fixes / 0 breaks (p = 0.25) — not evidence either way. 15 of d3.0's 38 passes come from truncated responses
(keyword/frequency constraints satisfied by repetition); under truncated-as-fail d3.0 falls to 23 < pinned 30.
The orchestrator's "no dose beats plain pinning without exceeding 2/20" is exactly right.

### F8 — LOW: degenerate history is a harness limitation, not a bug
History turns are greedy base decodes (max_new 512). Sessions 16/17 have a 19-token degenerate second history
turn; this depresses `full` and `pinned` (s16 pinned and pinned_echo run the "* * *" loop to the cap; echo_only
does not). Two of 20 sessions with contaminated history is enough to move the full/pinned_echo comparison
(F2) and to produce the only pinned_echo safety event (F1). A replication should either screen history
degeneracy (drop sessions whose history turns are degenerate, registered in advance) or report it per session.

## 2. Answers to the brief

1. Recompute: every summary number reproduces exactly; 180/180 score vectors replay; six H1 arms + three dose
   arms in one job at max_new 512; artifact tracked (22 files, commit daccd3e).
2. pinned_echo > full is not a red flag for leakage (F3) but it is not a real "above ceiling" either (F2):
   p = 0.30, and `full` is depressed by degenerate history in s16/s17. Quoting responses do not pass more in
   pinned_echo (0.826 vs 0.818); in echo_only they do (0.696 vs 0.606) purely because they are the literal-type
   constraints.
3. Target-blind: NO. The echo (and the pins) use the harness's "Constraint:" marks — oracle focus, with span
   bleed (F5). What H1 shows: GIVEN the right spans, text re-injection recovers 0.81 of an eviction-induced gap
   (21/0 fix/break) and KV residency adds +10 passes on top (13/3, p = 0.02; CI [+0.06, +0.29] per session);
   residency alone recovers 0.69 and is specific (+13 vs matched columns). What H1 does NOT show: (a) that
   automatic salience selection finds those spans (the 113-slice's `eligible_coverage` 0.953 with top_k 2 is the
   only automatic-selection evidence, on a different regime); (b) any gain in the NON-evicted regime — H1 has no
   `full + echo` arm, and pinned_echo vs full is null (F2); the 113 slice, which IS that regime, gives eligible
   n01 5 / n10 1 (p 0.11, clustered LB −3.1) and only the all-outcome descriptive +2.8/p 0.012 (F4). So H1 is
   evidence about availability + recency under eviction with oracle marks, not about the product setting.
4. Literal rules: pinned 33 > control 20 ✓; pinned_echo 46 > echo_only 36 ✓; recovery 1.19 ≥ 0.85 ✓; safety:
   timeouts 0 ✓, degenerate 1 ≤ 2 ✓, truncation excess +5 pts > +2 ✗ → literal outcome FAIL (F1). The
   orchestrator's reading is right on every clause it evaluated and wrong by omission on the one it skipped.
   Wave: KILLED at best dose (12/20), d1.0 killed (4/20), d0.5 not killed but 31 < 33 — reading exactly right (F7).
5. Exact-column control: confirmed 20/20 (F6).
6. Next rung: see §4.

## 3. Verdict on the H1 reading
CONFIRMED-WITH-QUALIFICATIONS. The numbers are exact and the mechanism reading (selection + availability + recency;
amplification not creditable) is supported by paired statistics. But (i) the registered ADVANCE-RETENTION cannot
be claimed literally because the +2-pt truncation clause is violated by pinned_echo (+5 pts) — the decision
requires a recorded amendment, not a silent pass; (ii) "above the full ceiling" must be withdrawn (p = 0.30,
degenerate-history confound); (iii) the quoting-excluded rates are not a de-leaking control; (iv) the result is
oracle-focus under artificial eviction and says nothing yet about automatic selection or the non-evicted regime;
(v) the registered rule text's "+2.8, p=0.012" is a descriptive all-outcome number.

## 4. Ranked next rung ("adequate proof before scaling", "do not over-engineer")
1. (a) Automatic-selection replication of H1 on the same harness — BEST. Cheapest test of the only unproven
   link (selection). Minimal spec: salience-selected spans replace the marks in pinned / echo_only / pinned_echo;
   keep full / evicted / marked-pinned_echo as anchors; add ONE arm `full_echo` (no eviction + echo) so the
   product regime is measured in-job; fix the span window (F5); raise to 40–60 sessions so the truncation clause
   has 2-pt resolution, and pre-register history-degeneracy screening (F8) and a literal carve-out for quoting
   (F3). Drop all wave doses (killed). ~2–3 GPU-h. Success = pinned_echo(auto) recovers ≥ 0.85 of gap AND
   ≥ 0.85 x pinned_echo(marked), safety by the amended clause.
2. (b) 909 Multi-IF text_ledger confirmation under ROUND 7 — second. It is the right "larger implementation"
   for re-injection, but it does not test KV residency (H1's actual novelty, +10 passes) and its eligible-outcome
   signal on the 113 slice is weak (5/1). Run it after (a) confirms automatic selection, so that the confirmation
   arm can be the automatic pinned_echo rather than text_ledger alone; otherwise it only confirms the product
   that (F4) already labels as descriptive.
3. (c) H3 trust-region wave pilot — LAST / not now. Its registered precondition (H1 ADVANCE-RETENTION) is not
   literally met; every dose that gains passes degenerates (F7), d1.0's 3/0 is not evidence; 15 of d3.0's passes
   are truncation artefacts. Building a rejection policy on top of an amplification signal that has never been
   creditable at this harness is over-engineering.
