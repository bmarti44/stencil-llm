# Quick checks (2026-09-02, orchestrator, GPU idle, ~40 min total) — sharpening the odds before the G0 pilot

All on the 20 H1' sessions (data/b3 mt-train-300 dev probe; NOT a gate benchmark), reference = the FULL arm's own
greedy output, same eviction plumbing as the registered probe (scripts/ledger_kv_probe.py) and the pilot (scripts/g0_oracle.py).

1. Leave-one-out loss oracle (oracle_check.py, oracle_check_loo.log): evict one span's KV columns, teacher-force the
   model's own 96-token continuation. Known constraint spans vs exact-column controls: AUROC 0.494 (mean delta),
   0.48-0.52 on every per-token readout (max, sum-positive, top-3, top-1 flips). NO SIGNAL. Cause: prior compliant
   assistant turns make each constraint sentence redundant (sol G0R-4 non-additivity, seen live).
2. Keep-one-in oracle (oracle_check_keepin.py, oracle_check_keepin.log): evict the whole range except one span.
   Gap all-evicted minus full = 2-4 nats/token; single spans recover up to 1.2. Constraint vs control AUROC 0.518
   (mean), 0.63 (top-3), 0.60 (top-1 flips back). WEAK: the "controls" are the task sentences the model also needs to
   reproduce its own continuation, and a 96-token prefix cannot see late-acting constraints. The loss oracle measures
   need-to-reproduce-content, not adherence to standing constraints.
3. BM25 query-time retrieval, CPU (in WORKLOG): constraint-token coverage at the finder's budget 0.37 vs random 0.13,
   recency 0.02. Lexical retrieval with the current turn as query misses delayed constraints.
4. ROLE RULE on checker outcomes (role_rule_check.py, role_rule.log): pin ALL prior user turns (no finder), evict the
   rest, score exactly as H1'. Aged constraints passed / 56:
   full 44 | evicted 14 | finder-pinned (H1') 37 | finder control 18 | ROLE 41 | role exact-column control 26.
   Recovery (41-14)/(44-14) = 0.90. Safety: role truncated 1, degenerate 1 (full: 1 / 2). Budget: role pins mean 89
   columns = 20% of evictable (finder: 47). Per session vs finder +4/-1/=15; vs full +3/-5/=12.
   A parameter-free rule with no selector recovers 90% of the eviction gap on this probe.

5. RB — ROLE RULE AT THE FINDER'S BUDGET (role_budget_check.py, role_budget.log; the control kimi/sol/fable all
   required): pin prior user turns oldest-first, clipped to the H1' finder pin count per session, exact-column null.
   RB 29/56 (control 22) vs finder 37 (control 18). Kimi's pre-registered rule: RB <= 37 -> the role rule's +4 over
   the finder was BUDGET. At equal cost, which columns are kept matters: selectivity beats role.
   (fable: the keep-in "weak signal" is a span-length artefact — within-length AUROC 0.46 — report as no signal.)

6. READ-TIME RETRIEVAL BY THE MODEL'S OWN ATTENTION (attn_retrieval_check.py, attn_retrieval.log): rank archived
   sentence spans by the attention the query position (last prompt token, layers 20-27, mean over heads, per column)
   pays them; pin the top spans at the finder's budget. Constraint coverage 0.19 (per-column) / 0.26 (mass) vs BM25
   0.37, random 0.13. Outcomes: ATTN 16/56, its exact-column control 24, finder 37, evicted 14. FAILS: the query
   position attends to recent/topical content, not to standing instructions (delayed need, measured at read time).

7. THE MODEL AS ITS OWN SELECTOR (self_extract_check.py, self_extract.log): before answering, the same frozen 1.7B is
   asked to quote every earlier instruction that still applies; quotes are matched back to source sentences
   (Jaccard >= 0.5), then pinned + echoed via the H1' mechanism. Coverage of the oracle constraints 0.52 (7/20
   sessions >= 0.8), 37 extra spans. Outcomes: SELF pinned 31, SELF pinned_echo 37, exact-column control 25 —
   vs finder 37 / 48, full 44, evicted 14, role-at-budget 29, attention 16. Generic and training-free, and the best
   parameter-free selector so far, but the 1.7B extractor is the bottleneck (coverage 0.52 vs finder 0.97).
   Next quick check: the 4B trunk as extractor (same fixed prompt; no prompt tuning on this selection set).

8. 4B AS EXTRACTOR (self_extract4b_check.py, self_extract4b.log): same read-time whole-history extraction prompt,
   Qwen3-4B extracts, 1.7B runs the arms. Coverage 0.58 (9/20 >= 0.8), extras 36. SELF pinned 33, pinned_echo 30,
   control 23. Extractor size barely moves whole-history recall; extras make the echo harmful. Next: WRITE-TIME
   per-turn extraction (each prior user turn alone, short input) — the "save what matters as it arrives" form.

9. WRITE-TIME PER-TURN EXTRACTION, 4B (self_extract_turn_check.py, self_extract_turn.log): each prior user turn
   shown alone; asked to quote the sentences that are instructions to keep following. Scored coverage 0.64, extras 44,
   SELF pinned 30 / echo 31 / control 23. CAVEAT found on inspection: the extractor quoted every true constraint in
   the inspected sessions; the misses were the matcher's (sentence splitter breaks on "P.P.S.", Jaccard < 0.5 on the
   fragments). The "extras" are the task sentence and the reminder sentence. Rerun with a direct substring matcher =
   check 10 (self_extract_turn2_check.py).

11. EMBEDDING-SIMILARITY RETRIEVAL (embed_check.py; Brian's question "store an embedding of all messages, embed the
   next message, retrieve the most similar"): bge-small-en-v1.5 (cached), cosine similarity of the current message to
   each prior sentence, top spans at the finder's budget. Constraint-token coverage 0.41 (0.43 with an
   instruction-flavoured query prefix), 0-1 of 20 sessions >= 0.8 — vs BM25 0.37, attention 0.19-0.26, random 0.13.
   Semantic similarity finds what the new message is ABOUT; standing rules are not about the message that needs them.

10. WRITE-TIME PER-TURN EXTRACTION, 4B, FIXED MATCHER (self_extract_turn2_check.py, self_extract_turn2.log): quotes
   located by direct normalized-substring match in the prior history (fallback Jaccard). Coverage 0.87 (16/20 >= 0.8),
   extras 41. Outcomes / 56: SELF pinned 36 (finder 37), SELF pinned_echo 43 (finder_echo 48, full 44), exact-column
   control 22, evicted 14. A GENERIC, TRAINING-FREE selector (the frozen 4B asked, one message at a time as it arrives,
   which sentences are instructions to keep following) matches the taxonomy finder on pins and reaches the
   full-context ceiling with echo. Remaining gap to finder_echo (48) is precision: 41 extra spans dilute the echo.
   Lineage: prompt fixed before the run; no tuning on this selection set; b3 remains a selection set for the CHOICE.

12. CHECK 10 BUDGET-MATCHED (self_extract_turnB_check.py; required by fable F1 / sol QC10#3): the extractor's spans
   clipped to the finder's per-session pin count, most recent first. Coverage falls to 0.51 (2/20 >= 0.8), extras
   23; SELF pinned 25, pinned_echo 27, control 19 — vs finder 37 / 48. At EQUAL budget the extractor loses: its
   extras (task sentences, reminders) consume the budget and crowd out constraints. Recall is high (check 10),
   precision is the gap, and at a fixed budget precision decides. This is the case for the trained generic
   classifier (precision) over prompting alone.

13. INTERIM GENERIC CLASSIFIER AS SELECTOR (train_classifier.py, clf_score_sessions.py, clf_probe_check.py,
   clf_probe.log, clf_interim_metrics.json): linear head on bge-small sentence embeddings + role, trained on the first
   18 kimi-k3 batches (2,507 hand-written rows, NO review, NO b3/benchmark data; train acc 0.89, hard 0.86).
   Threshold 0.5 on P(rule)+P(fact) over sentences of prior user turns. Coverage 0.94 (17/20 >= 0.8). Outcomes / 56:
   CLF pinned 37 (= finder 37), CLF pinned_echo 47 (finder 48, full 44), exact-column control (post-clamp) 22; safety
   echo arm truncated 1 / degenerate 2 (full 1 / 2). Budget: 57 cols vs finder 47 (1.23x; 1/20 sessions at or under).
   Budget-matched by probability rank: 27 / 34 / control 20 — the probabilities are not yet discriminative: it selects
   93/120 candidate sentences incl. the one-off task sentences. Precision on imperative one-off tasks is the gap the
   reviewed/enriched data must close. Note: the classifier never saw b3; this is a transfer result for the selector,
   while b3 remains the selection set for the mechanism choice.

14. CLASSIFIER, 9,863 kimi rows (unreviewed), same linear head (clf_probe2.log): train acc 0.876 ("none" recall
   0.79). Coverage 0.91; CLF pinned 35, pinned_echo 39, control 22; budget-matched 27 / 29 / 20. More data with a
   linear head did NOT help (47 -> 39 with echo; n=56, noisy). The limit is head capacity / precision on one-off
   tasks, not volume. Next: reviewed + enriched data (sol, Opus) and a nonlinear head or encoder fine-tune.

15. CLASSIFIER, MLP head, 14,391 rows incl. partial sol/Opus enrichment (clf_probe3.log): held-out (author-disjoint,
   never trained on) acc 0.84 (Opus set 0.89, sol set 0.78; "none" recall 0.72). Probe: coverage 0.66; CLF pinned 34,
   pinned_echo 39, control 22; budget-matched 28 / 34 / 20 (precision up from check 14: 29 -> 34 with echo).
   Diagnosis of the misses (clf_scores vs true spans): (a) the postscript rule was cut at "P." by my sentence
   splitter — the same bug that hit the extractor; splitter rewritten (quotes + abbreviations) and unit-checked;
   (b) "Now add a brief closing section..." is a one-off task the probe counts as a constraint because the old finder
   kept it — the classifier's "none" is correct per LABELS.md; the coverage metric conflates the two;
   (c) "begin with the exact title <<...>>" scores 0.23 because taxonomy phrasings were (rightly) removed from
   training; generic formatting rules in plain language belong in the enrichment. The reminder sentence scores 0.96
   (it is rule-like) and is dropped by the echo clamp.

16. CLASSIFIER, MLP head, all reviewed data (15,258 rows after sol/Opus patches: 530 drops, 98 relabels; 438
   author-disjoint held-out rows, acc 0.79, "none" recall 0.61), FIXED sentence splitter (clf_probe4.log):
   coverage 0.89 (17/20). CLF pinned 38 (finder 37), pinned_echo 44 (= full 44; finder_echo 48), exact-column
   control 16; BUDGET-MATCHED 29 / 37 / 19 (echo: 29 -> 34 -> 37 across checks 14-16). Held-out threshold sweep
   (heldout_sweep.py): thr 0.5 keep-precision 0.76 / recall 0.97; thr 0.65 ~0.83 / 0.95; thr 0.8 0.89 / 0.78.
   A thr-0.65 probe is queued (check 17).
