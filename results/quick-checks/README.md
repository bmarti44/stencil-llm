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
   BUDGET NOTE (check 16): the unclipped CLF arm pinned a mean 42 columns vs the finder's 47 (ratio 0.91; 74/116
   candidate sentences selected) with 0 truncated / 0 degenerate outputs — so "pinned 38 vs finder 37" is at slightly
   LOWER cost than the finder. The clipped budget-matched arm (29/37) discards spans by probability rank and is the
   conservative bound.

17. CHECK 16 AT THRESHOLD 0.65 (clf_probe5.log; threshold chosen from the held-out sweep, not from the probe):
   coverage 0.65 (7/20); CLF pinned 31, pinned_echo 37, control 15; clipped 28 / 35 / 18. Worse than 0.5: the
   higher bar drops true constraints the classifier is unsure about — the formatting-rule class that sol's
   taxonomy purge removed from training (kimi's check-16 review: restore those 344 rows, keep exact-phrasing drops).
   Threshold stays 0.5 (registered value); the lever is training coverage of plain-language formatting rules.

CORRECTION (sol's check-16 review, HIGH 1-2, accepted): (a) the enrichment rows were written AFTER and in response
to check 13's failure on this probe (both reviewers' briefs named the b3 task-sentence gap; Opus/sol wrote "Now add a
closing section ..." contrast pairs), so the classifier was DEVELOPED WITH b3 FEEDBACK — "never saw b3" was an
overclaim; check 16 is a development/selected-on-probe result, not transfer. (b) the 438-row held-out set is
path- and text-disjoint but NOT author-disjoint from training (sol/Opus wrote both enrich and held-out rows); the
threshold sweep therefore risks selecting for their style. Fix: a validation set written by an author who supplied
no training rows (fable), and transfer claims reserved for the post-development benchmarks and the no-contact family.
(c) Sol's nearest-neighbour audit: no copies of b3 rows, but ~12 constraint-family analogues among the 100 nearest —
taxonomy-level overlap; LABELS.md's "not even by paraphrase of the taxonomy" wording is withdrawn in favour of
item-level disjointness with deliberate type overlap (kimi + sol + Opus all concur on Opus's policy).

18. CHECK 16 RETRAINED WITH THE ITEM-LEVEL POLICY (282 taxonomy-category rows restored) + fable's author-disjoint
   validation set added to held-out (clf_probe6.log): held-out acc 0.74 overall — fable-validation 0.67 (n=363),
   opus 0.83, sol 0.77: the author-shared held-out sets overstated generalization (sol HIGH 2 confirmed
   empirically). Probe: coverage 0.60; CLF pinned 29, pinned_echo 36, control 15; clipped 26 / 35 / 18. WORSE than
   check 16 (38 / 44) after a modest data change: the frozen-embedding + MLP classifier is unstable at n=56 and its
   errors on fable's set are the one-off-imperative class ("Convert this function to TypeScript." -> rule) and
   context-as-prefix hurting (0.58 with context vs 0.74 without). Conclusion: a frozen sentence embedding cannot draw
   this boundary; the encoder must be fine-tuned with context as a sentence PAIR. Fine-tune queued (check 19).
   Checks 13-18 are development results on a selection set; none is a transfer claim.

CORRECTION (fable's check-16 review, HIGH F1): check 16's head was a single lucky seed — replicating the trainer
exactly reproduces 0.890 coverage; seeds 1-2, a 2e-7 feature perturbation, or dropout-off all give ~0.58 coverage
(check 17/18-level). Cause: dropout resampled inside the LBFGS closure (fixed). Checks 14-18 differences are seed
noise; the "restore taxonomy rows" lever is unsupported (+0.01..0.09 on formatting-type scores). Also: the clipped
budget-matched arm ran at 0.67x the finder's columns (reminder sentence consumed the clip then was clamped out), and
"0 truncated / 0 degenerate" held for the echo arm only. From check 19 on: >= 3 seeds, results reported per seed and
as the mean, head-selection rule fixed in advance (mean over seeds; no picking the best seed on the probe).

19. FINE-TUNED ENCODER (finetune_classifier.py, seed 0, 3 epochs, 111 s on GPU; finetune_seed0.log): held-out acc
   0.90 — fable-validation (author-disjoint) 0.87 (was 0.67 frozen), Opus 0.92, sol 0.94; "none" precision 0.93 /
   recall 0.87; hard 0.85. PROBE (clf_probe7.log, pair scoring with preceding sentences as context): coverage 0.17,
   CLF pinned 15 / echo 19 / control 14 — the evicted floor. Diagnosis (ft_diag.py on the 38 unique true constraint
   sentences): context prefix at scoring collapses P(keep) 0.47 -> 0.17 (scorer changed to no-context); and even
   without context only 17/38 pass — the near-zero ones are "finish with this exact postscript line", "begin with the
   exact title <<...>>", "exactly 5 bullet points", "in lowercase letters only": by LABELS.md these are reply-scoped
   formatting constraints (none), but in the probe, in Multi-IF, and in any session that keeps working on the same
   artifact, they persist while that work continues. The spec knew two scopes (this reply / forever); there is a
   third — the current task or artifact — and that is what the taxonomy finder had learned. Spec amended (LABELS.md
   v2: task-scoped constraints are rules unless explicitly one-off); kimi writes a focused "scope" batch; retrain
   x3 seeds; rescore without context. The seeds-1/2 runs already queued use the old scorer and are reported as-is.

20. FINE-TUNED ENCODER, spec v1, seeds 1-2 (queued before the v2 spec; context-prefix scorer): seed 1 held-out 0.90
   (fable 0.87) — probe coverage 0.29, CLF pinned 22 / echo 23 / control 15. Seed 2 did NOT train (crash: the scope
   pass wrote "context" as a list in some rows; fixed in the trainer) and its probe reused seed 1's scores — reported
   as invalid. Consistent with check 19: under spec v1 the fine-tuned classifier rejects task-scoped formatting
   constraints. Next (check 21): spec v2 data + scope pass, three seeds, no-context scoring, mean reported.

21. SPEC v2 (scope pass added; reviewed relabel patch NOT yet applied), fine-tuned encoder, NO-context scoring,
   seeds 1 and 2 (ft_v2_s{1,2}.log, clf_probe8_s{1,2}.log): held-out 0.90 / 0.90 (fable author-disjoint 0.88 / 0.86;
   "none" precision 0.96). Probe: seed 1 pinned 33 / echo 45 / control 17; seed 2 pinned 33 / echo 44 / control 17;
   coverage 0.86. Two seeds agree (finder 37 / 48; full 44; evicted 14). Seed 0 (rerun) and the FINAL three-seed
   run with the 59-row reviewed relabel patch follow; the reported number will be the three-seed mean.
   Check 21 budget/safety (seed 2 rows): CLF pinned a mean 40 columns vs the finder's 47 (0.86x); pinned arm 0
   truncated / 0 degenerate; echo arm 0 truncated / 2 degenerate (full: 1 / 2). Seed-1 rows were overwritten by the
   chain (per-run copies added from here on); its log totals stand.

22. SPEC v2, three seeds (seed 0 rerun after the 59-row reviewed relabel patch landed, so its training set differs
   slightly from seeds 1-2 — the FINAL run re-does all three on identical data): pinned 33 / 33 / 33 (mean 33.0);
   pinned_echo 46 / 45 / 44 (mean 45.0); control 17; coverage 0.86; held-out 0.90 each (fable author-disjoint
   0.85-0.88). vs finder 37 / 48, full 44, evicted 14. Three seeds agree within +-1 — the instability of the frozen-
   embedding checks is gone. Reading (development result on the selection set, not transfer): a generic classifier
   trained on hand-written, reviewed, benchmark-disjoint data under the three-scope spec reaches the full-context
   ceiling with pin+echo (45 vs 44) at 0.86x the finder's columns, and trails the taxonomy finder by 4 on pins and
   3 on echo.

REVIEWS of checks 19-22 (kimi CONFIRMED-WITH-QUALIFICATIONS; sol CONFIRMED-WITH-QUALIFICATIONS, HIGH 1-2 accepted):
(1) b3 shaped the spec and the kinds of training examples written after its failures — "no training row derives
from b3" is false causally; only "development result on the selection set" stands. (2) The scope pass (4,954 rows)
was NOT reviewed; "hand-written, reviewed" is narrowed to the kimi/kimi-ctx passes until the scope-pass review
(sol, Opus) lands; LABELS.md's taxonomy-disjoint sentence replaced by the item-level policy. (3) "Ceiling" ->
"full-context baseline point estimate"; 0.86x refers to pinned columns only, echo tokens excluded. (4) The FINAL
identical-data run carries a train manifest (sha, per-source counts, patch files) and per-run rows for safety.
FABLE (checks 19-22): CONFIRMED-WITH-QUALIFICATIONS. F1: all three v2 seeds already trained on identical data (the
trainer's patch glob picked up the 59-row patch before seeds 1-2 started) — the check-22 caveat is withdrawn and the
FINAL chain is a replication. F2: the selected span sets are identical across seeds (pinned 33 is one deterministic
measurement; the echo spread is echo-order noise); budget-matched arms differ by seed (pinned 33/27/33, echo
45/35/40) and are reported here. F3 (HIGH, accepted): the v2 spec and the scope-generation prompt carried exemplars
lifted from the probe's misses with their specifics (90-word cap, angle-bracket title, postscript); 38 scope rows
echoing them are dropped (review/scope-exemplar-patch.jsonl), exemplars rewritten in LABELS.md and the generator;
lineage wording narrowed. F5: patch precedence now deterministic (sorted). F7: the postscript family is the one the
spec change did not teach (all seeds miss it).

23. HELD-OUT SLICES vs the replication seed-0 model (eval_heldout_ft.py): fable-scope-validation (author-disjoint,
   scope-specific, template-varied, 292 rows) acc 0.83 (hard 0.76); fable-validation 0.85 (hard 0.75);
   opus-heldout 0.94; sol-heldout 0.94 (author-shared with enrichment — inflated, as sol predicted). The classifier
   carries the scope concept beyond the training templates at ~0.83, not at the 0.94 the shared-author sets suggest.
   Confusion: rule->fact 26, none->rule 40, none->fact 27, rule->none 21 (of 1,093).

24. REPLICATION (same data as check 22, three seeds, clf_probe9_s*.log): pinned 33 / 33 / 33; pinned_echo 46 / 45 /
   44; control 17 / 17 / 17 — identical to check 22 (fable F1 confirmed: the data were already identical). Per-run
   rows retained (clf_probe_rows_<epoch>.json). The corrected run (scope-pass reviews + exemplar drop applied)
   follows as check 25; its seed-0 artifact is the candidate registered selector.

25. FINAL (registered) run — scope-pass reviews (sol, Opus) + exemplar drop applied; 20,054 training rows; three
   seeds on identical data with a train manifest (clf_probe10_s*.log, ft_final2_s*.log, metrics in
   data/classifier/model/ft*/metrics.json): pinned 33 / 33 / 33; pinned_echo 46 / 45 / 44 (mean 45.0); control
   17 / 17 / 17; coverage 0.86; held-out 0.89 each — fable-scope-validation 0.85 / 0.85 / 0.83, fable-validation
   0.87 / 0.88 / 0.88 (author-disjoint), opus/sol held-out 0.92-0.95 (author-shared). Seed 0 artifact =
   data/classifier/model/ft (sha256 list: ft_final2_s0_sha256.txt) — the SELECTOR v2 registered for the
   post-development Multi-IF evaluation. Reading (revised 2026-09-04, astra program review): development result under the old post-prefill ordering;
   three-seed mean pin+echo 45/56 vs finder 48/56 and full 44/56, at 0.86x the finder's pinned columns, excluding
   echo cost. These point estimates do not establish parity, superiority, or equivalence. Check 27 supplies the
   corrected-ordering development measurement.

26. MULTI-IF REAL-EVICTION PREFLIGHT (scripts/multiif_evict.py, 20 conversations, results/qwen/multiif-evict-
   preflight): aged constraints / 53 — full 30, evicted 18, clf_pinned 31, clf_pinned_echo 33, clf_control 22,
   role_pinned 29. Same ordering as the dev probe on the real benchmark with real eviction; pin+echo above full.
   Contrasts not significant at n=20 (C1 p 0.09, C3 p 0.05, C2 p 0.76). 87 s/conversation -> 22 GPU-h for 909
   (cap amended to 24 GPU-h, LEG B AMENDMENT 1). Safety: full 0 degenerate on 20 -> the integer clause fails every
   other arm on 1-3 events; judged on 909.

27. CORRECTED EVICTION ORDERING (history prefill -> evict -> current-turn prefill; commit 5c743f1; sol/fable fix
   reviews SOUND) — the 20-session probe with the FINAL selector (results/qwen/ledger-kv-probe-prequery/clf-probe.json):
   full 44 | evicted 10 | clf_pinned 41 | clf_pinned_echo 46 | exact-column control 13   (post-prefill ordering:
   44 | 14 | 33 | 46 | 17). The old ordering leaked history through the current turn: clean eviction costs 4 more
   (14 -> 10) and pins matter MORE (33 -> 41): pins alone recover (41-10)/(44-10) = 0.91 of the gap; pin+echo 46
   exceeds full. Prefill diagnostic (prefill_diag.log): on the recorded diagnostic, two-stage and one-shot fp32 logits differed
   by at most ~8e-5 and agreed in top-1 predictions; bf16 logits differed more (max |d| 0.67; batch-shape noise
   floor 0.0). This is numerical agreement on that diagnostic, not bitwise identity. Every comparison arm uses the
   same two-stage schedule; the test wording is narrowed to fp32-close / bf16-top-1-equal. All checks 4-25 are now
   labelled "post-prefill ordering"; check 27 supersedes them for the mechanism claim.

28. CLASSIFIER-GATED DEFICIT WAVE (Brian's proposal; results/qwen/clf-gated-wave-prequery/clf-probe.json; corrected
   eviction ordering; tau 0.3, b_max 3.0 from the frozen calibration; fable's pre-registered reading in
   results/gated-wave-review-fable.md): clf_pinned_wave 44 (clf_pinned 41; paired 4 wins / 1 loss / 15 ties);
   clf_pinned_wave_conf 42 (confidence saturated — near-duplicate as predicted); clf_pinned_echo_wave 44
   (clf_pinned_echo 46; 2 wins / 3 losses). SAFETY: degenerate 8 / 8 / 6 of 20 vs clf_pinned 3, full 2; truncated 5
   vs 2 / 1. All three wave arms KILLED by the registered rule (degenerate > 2/20) and HARMFUL by the pre-registered
   reading (excess degeneracy over the base arm > 2). Reading: gating the boost to selected spans at deficit moments
   reduces but does not remove degeneration; the +3 on pins is bought with 4x the degeneracy; re-injection reaches 46
   with none. The tested attention-bias interventions failed the registered development criteria; this ends the
   cache-column-bias branch for now (it does not rule out all activation steering).

29. LEG B (Multi-IF 909, corrected eviction; results/qwen/multiif-evict-909-prequery-v2): full 0.652 | evicted 0.167 |
   clf_pinned 0.572 | clf_pinned_echo 0.592 | control 0.330 | role_pinned 0.605 on 2,276 aged constraints. C1 +26.8
   (LB +24.7), C3 +18.5 (LB +16.7) pass; C2 −3.5 fails (role rule > classifier at equal columns). Safety: one invalid
   output in each pinned arm vs 0 for full -> registered clause breached -> REGISTERED VERDICT: not supported;
   substance disclosed. See LEDGER-PLAN "LEG B OUTCOME".

30. FUNCTION-VECTOR FOCUS (Brian: "turn up the focus on the weights"; results/qwen/fv-vectors/{vectors.pt,grid.json,
   report.json}, results/qwen/function-vector-focus/clf-probe.json; corrected eviction; vectors = mean residual
   difference with/without each of 11 constraint types from 352 dev-corpus pairs; grid chose alpha 2.0 at layer 12
   as the strongest non-degenerate cell on 4 dev conversations; pre-registered reading fixed before the run):
   fv_inject 14 (evicted 10, clf_pinned 41; paired vs evicted 5 wins / 1 loss / 14 ties; vs clf_pinned 1 / 17 / 2);
   fv_inject_echo 35 (clf_pinned_echo 46; 1 / 7 / 12); fv_clear 13. Safety: truncated 14-15 of 20 (full 1,
   clf_pinned 2) — the injected vector drives generation to the 512-token limit; degenerate 1 (not killed by the
   4-gram rule). Pre-registered reading: HARMFUL (fv_inject < evicted + 5; truncation breach). Reading: switching on
   the instruction's circuit through a residual-stream direction recovers almost nothing of what forgetting costs,
   and added on top of re-injection it subtracts 11 points; one grid point only (alpha 2.0 / layer 12), chosen for
   non-degeneracy, not tuned on the probe. Revised closure (astra program review, 2026-09-04): the selected sustained residual-vector intervention scored
   14/56 without pins and 35/56 with pin+echo, with 14/20 and 15/20 truncations; clearing at 64 tokens scored 13/56
   with 2/20 truncations. Type metadata selected these activation vectors. These outcomes justify ending this
   engineering branch for now; they do not rule out all activation steering or test Miller's biological mechanism.
   Note: residual-vector steering changes activations, not weights. Re-injection stands.

31. UNREGISTERED FOCUS-1 feasibility (Brian approved 2026-09-05; seed 31031; focus1-probe/README.md):
   1.7B cue asc/desc 0/32, 0/32; 4B 27/32, 30/32. Held cue-absent copy: 12/16 and 16/16.
   Both trunks: every sustained steering direction 0/16 exact; prompt-only directions also 0/16 -> INFEASIBLE.
   4B is the better competence baseline; no useful steering cell. Complete in 5.33 / 9.73 GPU-min, respectively.
   Probe-only disjoint synthetic fit/eval lists; no registered FOCUS-1 selection. JSON/schema correction disclosed.

32. Q4 OPERAND-FREE KV PACKET transplant (seed 32040; check32-kv/README.md): **INELIGIBLE on both trunks**.
   Full six-arm matrices completed: text-cue joint 4B 29/64, 1.7B 6/64 (bar 48/64); correct joint and HOLD 0/64 each.
   Correct SET/SWITCH/BACK 0/64 each; CLEAR copy 64/64, impositions 0/64; upper-layer diagnostic induced no task.
   Restored columns bitwise equal; downstream residuals and replay-control discrepancies reported; 73.74 GPU-min total.
   Q2 was declined by Brian and never run to completion; existing Q2 partial work is preserved, not a Q4 result.

33. Q3 COORDINATE REPLACEMENT (seed 33033; check33/README.md): **INELIGIBLE on both trunks and variants**.
   Correct joint and one-shot HOLD 0/64 throughout; all 32 setup cells across the two trunks induced neither task.
   Retained/fresh text joint: 4B 34/7 of 64; 1.7B 7/6 of 64 (bar 48/64); fresh contexts do not rescue eligibility.
   Fit separates 128/128 pairs at every layer; correct CLEAR impositions 0; breakage sustained/one-shot: 4B 0/0, 1.7B 2/3.
   Completed in 52.07/90 GPU-min; all 7,808 raw records audited; bf16 cast residuals and 1.7B batch differences disclosed.

34. CUE-COLUMN POSITIVE CONTROL (seed 34034; 4B only; [check34](check34/README.md)): **POSITIVE**.
   Transplant A/B 59/60 of 64, text 59/60, shuffled donors 60/60; OFF induction 0/64; breakage A/B 1/0.
   Retained A/B joint 3/5 of 32; HOLD 32/23; SWITCH 3/17; CLEAR copy 0/0 (columns restored exactly).
   Stickiness NOT SUPPORTED: fresh B / B after A / A after B = 60/60/60 of 64; gap 0 pp, conservative 95% Wilson-based CI [-14.53, 14.53] pp.
   Cache-transplant route alive; prior packets were inadequate. 21.44/45 GPU-min, 1,728 records audited; no fitting/training or benchmark access.

35. RECENT CUE ADDRESSES + ANSWER RELEASE (seed 35035; 4B; [check35](check35/README.md)): **TEXT solves SWITCH; no cache arm does; none solves CLEAR**.
   SWITCH→BACK successes: S1 3→32, S2 0→32, S3 12→18, S5 9→30, TEXT 27→29 (n=32); S4 still A 27/32, control valid.
   Restore+evict CLEAR/next impositions: S2 3/6, S3 4/1, S5 3/5 of 32; first-copy gains do not meet the two-request rule.
   Joint SET/HOLD/SWITCH/BACK/CLEAR: S5/c2 8/32, S3/c2 3/32, all others 0; SET/HOLD 29/31 of 32 throughout.
   27.52/45 GPU-min; all 1,536 records, 1,600 cache operations and 286 donors audited; no fitting, training, benchmark access or push.

36. DOWNSTREAM RECOMPUTATION (seed 36036; 4B; [check36](check36/README.md)): **PRECEDENCE_PATTERN; no SWITCH rescue**.
   SWITCH→BACK exact: R1 3→32, R2 2→32, R3 2→32, R4 17→14, R5 0→32 (n=32); R2/R3 outputs identical.
   R1/S1 and R5/S2 replicate every SWITCH/BACK output; R4 improves SWITCH but BACK strict exact is 5/32; all breakage 0.
   7.57/15 GPU-min; 320 records and 64 source-history hashes audited; reused S1 histories, no fitting/training/sealed inputs/push.

37. EVICTION REPAIR (seed 9053701; Qwen3-4B; [check37](check37/README.md)): **STOP; do not preselect placeholder**.
   Placeholder releases surviving 30/30, rebuilt 28/29 vs intact 30/30 (n=32); rebuilt release-1 loss 2 exceeds 1.
   Both modes copy 32/32 at BOTH neutral requests, but add broken episode 24 (duplicate integer); intact breaks elsewhere.
   14.72/30 GPU-min; all 1,088 records/384 edit records audited; no fitting/training/sealed inputs/signals/push; no larger test.

38. ROLE / RECENCY / PATTERN (seed 38038; 4B; [check38](check38/README.md)): **NONE of the three fixed thresholds met**.
   SWITCH B: T1/T2/T3/T4/R3=1/12/0/11/2 of 32; T3 A=31/32; ascending default T2 A=12/32.
   BACK A: 32/23/32/30/32 of 32; R3 token outputs 64/64 identical; Wilson intervals in report.
   8.02/15 GPU-min; 320 records audited; two actual source exchanges (request said three); no fitting/training/sealed inputs/signals/push.

39. EVICTION REPAIR RERUN (seed 39039; n=64; 4B; [check39](check39/README.md)): **PROCEED_PLACEHOLDER**; check37 STOP stands.
   Strict releases placeholder surviving 60/59, rebuilt 58/57; intact surviving 59/58.
   Paired b/c surviving 0/4, rebuilt 0/4; both modes' neutral gates PASS; full strict/lenient cells in report.
   16.59/30 GPU-min; 1,152 records/384 edits audited; fresh disjoint episodes, no fitting/training/sealed inputs/signals/push.

40. BRUTE-FORCE MoE SKILL ROUTING (seed 40040; Qwen3-30B-A3B; [check40](check40/README.md)): **PARTIAL / COST STOP**.
   Installed grouped_mm adopted; nonzero dispatch and exact OFF logits verified; 3x128 pilot measured 16.02 / 17.27 / 17.37 tokens/s.
   Full capped screen projects to 14.43 GPU-h; prescribed 32-episode / alpha {1,4} / all-layer reduction still 7.56 h > 4 h: STOPPED before competence/extraction.
   Memo pair ranking, shared-suffix frequency/SD profiles, retained-KV bias placement, and post-selection-token risk adopted; no skill-steering verdict or pair selection.
   14.50 GPU-min charged including preserved metadata-failure retry; 384 pilot tokens audited; no training, benchmarks, sealed reads, signals, or push.

## QUEUE (2026-09-05, Brian's quick-test-first ruling; merged from results/hypotheses-{astra,fable,kimi}.md)
Skill pair for all: ascending sort vs REVERSE input order (1.7B cannot do descending: 10/32); value-exact,
format-lenient scorer (check 31 lost 28/32 correct ascending sorts to quotes/fences). Own seeds; no benchmark data;
pass/fail reading written before running; one accuracy review of the RESULT from raw records before the next item.
- Q1 DONE = check 31 (extracted mean-difference residual steering, oracle A/B/OFF): INFEASIBLE on both trunks; vectors
  near-collinear (cosine 0.89-0.98); zero task inductions in all 18 cells x 2 trunks. Extracted-vector family closed.
- Q2 DECLINED by Brian: content-free slot address over a fixed skill menu; never run to completion.
  Existing partial work under check32/ is preserved. Item 32 now refers to Q4 below.
- Q3 DONE = check 33, coordinate replacement (astra #3), explicitly authorized by Brian after Q2 was declined.
  Both trunks/variants INELIGIBLE; correct joint and one-shot HOLD 0/64; 52.07/90 GPU-min. See item 33.
- Q4 = check 32: one-shot KV address / operand-free KV packet transplant, hold without reapplication, clear by restore
  (fable #3, astra #4). DONE: both trunks INELIGIBLE; zero correct-packet task induction; 73.74/90 GPU-min. See item 32.
- Q5 = learned address prefix / controller-in-the-loop (fable #2, astra #2, kimi H2) — only after Q2 or Q4 supplies a
  reliable actuator; <= 4 GPU-h.
- Q6 = head-gate patterns (fable #4, astra #5, kimi H5), <= 4 GPU-h, closure test.

## QUEUE UPDATE (2026-09-05, after checks 32-33)
- Q4 (check 32, KV packet) and Q3 (check 33, coordinate replacement, sustained AND one-shot) both induced NOTHING on
  either trunk (0/64 any induction; outputs copy the input); fable's check-32 review: the write channel is live, the
  packet content encodes "instruction present" not "which"; the cache-transplant hypothesis is NOT disconfirmed
  without a positive control (donor's actual cue columns). The "stickiness" reading of the text bar was mostly
  B-task (reverse) difficulty + a system-prompt precedence confound (fable).
- Skill pair from check 34 on: ascending vs DESCENDING on 4B (27/32, 30/32 competent); reverse-order made the 48/64
  text bar unreachable by construction. 1.7B secondary only.
- Q4b DONE = check 34: POSITIVE (real cue-column K/V transplant A/B 59/60 of 64; OFF 0/64); see item 34.
  The cache-transplant route is alive; the earlier final-token/four-column representations were inadequate.
  User-turn stickiness NOT SUPPORTED: B-first and B-after-three-A-turns both 60/64; no system-cue confound.

41. LANGUAGE-SPECIFIC MLP NEURON SCALING (seed 41041; Qwen3-4B; [check41](check41/README.md)): **CPU READY / WAITING**.
   Count on 32 cued tasks/language; entropy-weighted frequency differences; k={200,500,1000}, gains={0.5,1,2}, deactivate-other.
   Separate 16-task setup freezes one cell; 64 retained-history episodes x correct/swapped/shuffled/OFF/text-cue; original check40 531030a tasks/checkers.
   Fixed reading: SET/SWITCH >=40/64, broken <=4/64, shuffled non-default/CLEAR impositions <=8/64; competence >=28/32 and overlap <=50%.
   CPU consumer/decoding/checker/threshold fixtures passed; no model outcomes; foreground 600-second GPU/check40 wait, two GPU-hour cap, no signals/push.

41b. CAUSAL DECISION-TOKEN MLP NEURONS (seed 41042; Qwen3-4B; [check41b](check41b/README.md)): **MARGINAL**.
   32 gradient-readout tasks; 36 cells on 8 setup tasks; frozen k=200/g=3/T=1; 32 fresh SET tasks plus 16 retained-history episodes.
   SET valid JS: correct 14/32, swapped/shuffled/OFF 0/32, text cue 32/32; correct broken 7/32 and JS + coarse task 13/32.
   Mean delta-c: correct +20.596, swapped +20.911, shuffled +0.224, OFF 0, text +41.900; correct starts ` moduleId` on 23/32.
   Correct HOLD/BACK JS 7/16, SWITCH Python 8/16, CLEAR JS 7/16; 40.30/90 GPU-min; 800-record audit PASS; parser-level induction only.

42. EVERY-REQUEST LIVE RULE ([check42](check42/README.md)): **NOT CLOSED under frozen no-exclusion reading**; 192 scheduled, 124 common pairs.
   Common all-five A/B99 vs C88; recorded BOTH78/neither0; A/B/C constraint0. B twice caps in 68/96 delay episodes; 4,471 records audited.
   Full A/C diagnostic: 151/192 vs131/192, b/c39/19, p(worse)=.997323; constraint0 each, A user/tool fact failures1 each; no verdict override.
   B vs A all-five99 each; assistant-fact failures3 vs23/41, but 68 exclusions. Actual subset64 memo (not prose48); frozen IDs unchanged.
   Qwen3-4B, reused seed9053723 bank (prior outcomes seen), no fit/train; 193.855/210 GPU-min incl.299s recovery; flag removed, no signals/sealed reads/push.

40b. MINIMAL MoE ROUTER SET (seed 40040; Qwen3-30B-A3B; [check40b](check40b/README.md)): **MARGINAL**.
   Cued competence Python/JS 16/16 each; raw-logit profiles; alpha 4 frozen from JS grid 7/8, breakage 1/8.
   Correct valid JS 26/32, broken 6/32 (>2 limit), coarse task pass 25/32; swapped valid Python 29/32, broken 3/32.
   OFF and matched-norm shuffled Python 32/32; text-cue JS 32/32; no truncation at 64 tokens, no screen reduction.
   12.41 GPU-min; 224 generations and 32 teacher-forced profiles audited; unregistered, no fitting/sealed reads/signals/push.

41 (FINAL). LANGUAGE-SPECIFIC MLP NEURON SCALING ([check41](check41/README.md)): **NOT POSSIBLE**; all 64 episodes complete.
   Frozen k=200 deactivate-other: SET/HOLD/SWITCH/BACK = 0/0/63/0 of 64; text-cue = 64/64 at all four stages; fresh defaults Python 64/64.
   Correct broken 4/64; shuffled non-default 0/64; correct CLEAR impositions 0/64; no setup cell induced both languages, and g=2 mostly increased breakage.
   Cued competence 32/32 each; all neuron-set overlaps 0%; layer counts/grid/task checks saved; counting only on disjoint synthetic profile/setup slices.
   All 2,528 records audited; 83.86/120 GPU-min including preserved empty attempt; check40 cost-stopped before behavior; no training, benchmarks, signals or push.

40c. ROUTER DOSE / FIRST TOKENS ([check40c](check40c/README.md)): **POSSIBLE**; same exploratory 32-task bank.
   Sustained alpha2 JS25/32, broken0; alpha3 JS32/32, broken0; freeze alpha2 by prewritten first-qualifying order.
   Alpha4 first3 JS25/broken4, first8 JS26/broken6; recorded sustained JS26/broken6, OFF JS0/broken0; family/arrow counts saved.
   128 new generations +64 recorded references audited; 10.49 GPU-min incl. load; unregistered, no training/sealed reads/signals/push.

40d. ROUTER SET / HOLD / SWITCH / BACK / CLEAR ([check40d](check40d/README.md)): **PARTIAL**, both release steps fail.
   32 fresh retained-KV episodes; alpha3 primary by explicit override of 40c's first-eligible alpha2; alpha2 secondary, 64-token caps.
   Primary JS32/32 at SET/HOLD/BACK, Python0/32 at SWITCH/CLEAR; zero broken, coarse32/32 every step; CLEAR impositions32/32.
   Shuffled JS0/32 everywhere (broken1/32 each scored step); OFF Python32/32; text SWITCH Python32/32, CLEAR JS32/32; alpha2 JS6/32 throughout.
   992 generations, 34.80/120 GPU-min; all-record CPU audit PASS; family/token/fence/arrows saved; unregistered, no fitting/sealed reads/signals/push.

40e. ROUTER TRANSFER BEYOND JS ([check40e](check40e/README.md)): **P1 NOT; P2 INELIGIBLE**, non-language flipping untested.
   OFF first: P1 Python32/32 correct; P2 JSON32/32, correct rows25/32. Go absent: authorized TypeScript fallback, alpha3 sustained/cap64.
   P1 cued Python/TS16/16 each; correct/swapped/shuffled TS0/32 (broken0), text-cue TS32/32; top8 overlap75.52%; paired flips0/32.
   P2 cued JSON15/16, SQL0/16: all SQL names `table` instead of supplied `items`; competence gate stops profiles/bias arms, no repair.
   256 records/32 profiles audited; 13.40/60 GPU-min, seed40050; frozen recipe6d28b09c; no fitting/sealed reads/signals/push.

43. CONCEPT-LEVEL SUM / PRODUCT ROUTING ([check43](check43/README.md)): **FAIL / NO SAFE SET**; unregistered, no fitting/training.
   Python cued SUM/PRODUCT donors16/16 each; last-four-neutral-token example means, layers7–34; frozen alpha1/2/3 each paired0/8 (<6/8).
   Each sign/dose: SUM7/8, PRODUCT0/8, one valid slice-endpoint error, malformed0; actual expert routes/weights changed inside the band.
   Setup stop applied: no selected dose, final/JS transfer, collateral or final McNemar/Holm inference; fresh banks95063/95064 remain unevaluated.
   81 scored +1 OFF replay, 4329 total tokens, 11.67/90 GPU-min; all records/profiles/hashes audited; flag removed, no signals/sealed reads/push.

**Correction (astra full review, 2026-09-05)**: (F1–F8; item-specific replacement readings)

F1 — Checks 40c/40d: Alpha3 was selected after exploratory screen results; a fresh same-family bank yielded32/32 SET, while the originally selected alpha2 yielded6/32. No general dose robustness is established. For checks 40b/40c/40d/41b, the provenance description is “locally frozen before execution according to run receipts”. Their freeze files first entered Git with results; matching local hashes and timestamps do not independently establish pre-outcome Git commitment. Checks 41/40e/43 have pre-generation Git anchors. Some checks 34–38 have launch-copy/hash evidence; check39’s exact reading was committed before its recorded start. These are not all committed preregistrations; no fabricated chronology was found.

F2 — Check36: Rebuilding downstream K/V leaves old-slot SWITCH at2/32. Stale downstream K/V alone cannot explain failure; role, placement, turn structure and prior demonstrations remain confounded. Check38: Check38’s T1/T4 cue events and inherited filler are unanswered consecutive user turns. Role, recency, turn structure and prior demonstrations were not isolated. The 19/32 “decay” plus 10/32 “answers” comparison is not an identified additive decomposition: it compares different lists/histories across checks. The paired T2/R3 contrast does not identify the cause of the whole deficit.

F3 — FOCUS-2c/2d context: Non-BOTH arms produced 16 truncations and 3 additional placement-only tag omissions, 19 broken outputs total; BOTH produced 18 well-formed tag omissions. The current request lacked a refresh, and the system carrier and most older exemplars were absent; the preceding event cue and answer remained. The delayed CLEAR failure count is 57/128 = 44.53%, not near-deterministic; the corresponding undelayed count is 1/128.

F4 — Check43: This grid did not induce PRODUCT. Its smaller perturbation leaves under-dosing as an untested explanation; concept control remains open. No neutral OFF operation was measured in check43: the saved OFF replay is a text-SUM pilot. Equal global norms do not establish equal decision-site sensitivity or show that a larger dose would work. Check40e: The tested TS direction/dose failed on this bank. A same-harness JS control would help localize the failure; generality beyond Python→JS remains unestablished.

F5 — Check40b: All 32 contain the intended arithmetic expression;26 parse as JavaScript and6 fail the paired language checker. This is expression preservation, not32 executable correct programs. Check41b’s accepted fences/labels can hide damaged prefixes; its 14 parser successes are not 14 clean complete programs. Both signs give large positive proxy shifts, so that proxy does not validate directionality. The same seven JS histories persist through SWITCH/CLEAR; the Python defaults are not successful release of those induced histories.

F6 — Check40c: Biased prefill plus the first few biased predictions can preserve the observed language rate. These arms neither isolate decode-only causality nor establish that sustained late bias causes all breakage. Check40d: Check40d redraws independent shuffled permutations at each step, including CLEAR while correct is OFF. Instantaneous norm matching does not match temporal coherence or the release schedule; this shuffled trajectory does not establish that a stable address causes HOLD. HOLD co-occurs with sustained bias and retained biased K/V/answers; no common-history OFF-at-HOLD arm isolates maintenance by the bias.

F7 — Check31 competence: “4B is stronger but misses the cited ascending bar”. QUEUE UPDATE reverse-order eligibility: “the observed reverse-order text controls missed eligibility”. The earlier check41 CPU READY / WAITING entry is historical; see the [41 (FINAL) row](https://github.com/bmarti44/stencil-llm/blob/b5be4318a92e5c0fea336e67a1139e7ff38c1016/results/quick-checks/README.md#L385) and [completed check41 report](check41/README.md). 41 (FINAL): NOT POSSIBLE for the tested frequency selector; SET/HOLD/BACK JS0/64 and SWITCH Python63/64 versus OFF64/64. No cell met the≥10/16-per-direction setup qualification.

F8 — Q1 extracted-vector closure: Further work on the tested mean-difference recipe is stopped; other selectors remain untested. “Dense neuron control is closed” denotes the operational stop for the tested check41/41b recipes, not a universal impossibility result; other dense selectors remain untested. FOCUS-2d completed and failed both efficacy versus per-request recap and unchanged-constraint safety. Placement and masking influence behavior, but the tested combination must not be promoted. Router claim: An externally maintained routing bias selects a narrow output mode using frozen co-trained experts. Whether it selects language-independent computation or supplies reversible task control remains unproved.

43b. CALIBRATED SUM/PRODUCT ROUTING ([check43b](check43b/README.md)): **CLOSE** on this trunk under the tested recipe; unregistered, no fit/train.
   OFF measured first: SUM8/8; same-runtime frozen JS alpha3 sanity8/8. Teacher-forced32 donors, identity21/window19–21; norms6.805823/10.208735.
   −b PRODUCT0/8 both doses, malformed0; shuffled− PRODUCT0/8; +b SUM8/7 with malformed0/1, shuffled+ malformed0/4; no safe cell, final/collateral skipped.
   80 generations/3963 tokens, 11.21/24 GPU-min; all scores/profiles/biases/dispatch audited; recipe da131791 precedes outcomes; flag removed, no signals/sealed reads/push.

FOCUS-3 gate ([results v2](focus3-gate/RESULTS.md), [frozen reading](focus3-gate/README.md)): **FAIL** after the authorized default-rendering repair; setup16/16 passes15/16.
   C/O now render explicit ordering defaults on every governed request; N/T unchanged, no masking. Setup30302 reused as requested (already used in v1); fresh gate30301 unchanged.
   Full64 gate: C/O final27/61, stale27/2; N final25/stale38, T final31/stale32. C exact0/64, false retirements64/64 (includes admission misses), broken0, contradictory0.
   Admission bottleneck: initial ordering0/64, global tag64/64; no ordering relation targets, so transition recall unmeasured. Switch-back C6/16 versus O/N/T16/16; mask un-release untested.
   19 tests pass,2 forbidden sealed-byte hash tests excluded; Ruff clean. Both audits PASS on1632 records/272 episode-arms; v1 evidence preserved, freeze27003fda precedes inference.
   2965.079/10800 charged GPU seconds incl.v1; full64 projection3504.527s. RESULTS v2/summary/records/traces complete; natural exit/own flag removed, no fit/sealed reads/signals/push.

40f. ROUTER RELEASE + ANSWER MASKING ([check40f](check40f/README.md)): **RELEASE WORKS by fixed rule (R2)**; unregistered, no fit/train.
   Pre-run cost fallback24 episodes, seed40060/alpha3/cap64; R2 Python23/24 SWITCH + HOLD_AFTER_SWITCH (broken1), CLEAR24/24 (broken0).
   R1 Python0/24 SWITCH/CLEAR; R3 Python0/24, broken6 each; R4 period copies/broken24 each; T SWITCH24/24, CLEAR0/24 (broken1).
   Masking enables SWITCH in addition to routing; R2 BACK JS0/24 means CLEAR is23 Python-persistence +1 broken-to-Python, not an independent JS release.
   648 generations/864 records/14406 tokens,22.95/90 GPU-min; full CPU audit PASS; recipe e570e74c, flag removed, no signals/sealed reads/push.
