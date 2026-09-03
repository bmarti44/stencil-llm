# Check 19-22 verification — fable (2026-09-03)

Brief: scratchpad/check22-review-brief.md. Read-only; CPU only; no process touched. Independent of the other
reviewer's report (results/check22-review-kimi.md was not opened). Everything below was recomputed from the rows,
logs, model artifacts and data files; the nearest-neighbour check was run for real (bge-small-en-v1.5 on CPU,
CUDA_VISIBLE_DEVICES empty; script kept at scratchpad/fable_nn_check.py, outputs scratchpad/fable_nn_out.txt).

Note on the environment during the review: at 01:10-01:12 the FINAL chain's `clf_probe_check.py` (GPU, seed 0 of the
identical-data run, scratchpad/clf_probe9_s0.log) was running, and `data/classifier/model/ft/` had already been
overwritten by that chain's training at 01:09:48 — i.e. AFTER the check-22 commit (01:07:34). See F6.

## 1. Recomputed totals (per seed, from the per-session log lines and the rows files)

Per-session lines summed (clf_probe8_s{0,1,2}.log; rows files exist for seeds 0 and 2, seed 1's were overwritten by
the chain as the README says). Every TOTALS line in the logs matches the sum of its own per-session lines.

| seed | held-out acc (ep3) | fable-val | none prec | CLF pinned | CLF pin+echo | CLF ctrl | CLFB pinned | CLFB pin+echo | CLFB ctrl | CLF cols | CLFB cols |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 0.9001 | 0.851 | 0.946 | 33 | 46 | 17 | 33 | 45 | 17 | 803 | 793 |
| 1 | 0.8976 | 0.879 | 0.958 | 33 | 45 | 17 | 27 | 35 | 17 | 803 | 677 |
| 2 | 0.9001 | 0.857 | 0.958 | 33 | 44 | 17 | 33 | 40 | 18 | 803 | 775 |
| mean | 0.899 | 0.862 | | 33.0 | 45.0 | 17.0 | 31.0 | 40.0 | 17.3 | 40.15/session | |

Reference arms (H1' records, recomputed): n_aged 56; full 44 (1 truncated / 2 degenerate); evicted 14 (0/1);
finder pinned 37 (0/0); finder pinned_echo 48 (0/1); finder pinned_control 18 (1/2); finder columns 932
(46.6/session). Claimed "0.86x the finder's columns": 803/932 = 0.862. Confirmed. Coverage 0.859 (13/20 sessions
>= 0.8) on all three seeds. Confirmed. "held-out 0.90 each": 0.900 / 0.898 / 0.900; "fable 0.85-0.88": 0.851-0.879.
Confirmed (seed 1 rounds to 0.90).

Safety per arm (rows files; degenerate = truncated or rep4 > 0.5):

| arm | seed 0 trunc/degen | seed 2 trunc/degen | full |
|---|---|---|---|
| CLF_pinned | 0 / 0 | 0 / 0 | 1 / 2 |
| CLF_pinned_echo | 0 / 1 | 0 / 2 | |
| CLF_control | 2 / 2 | 2 / 2 | |
| CLFB_pinned | 0 / 0 | 0 / 0 | |
| CLFB_pinned_echo | 0 / 0 | 0 / 1 | |
| CLFB_control | 2 / 2 | 1 / 1 | |

Check 21's "pinned 0/0; echo 0/2 (full 1/2)" for seed 2 is confirmed. The control arms (2 truncated vs full's 1) sit
exactly at the draft registration's `truncated <= full + 1` line; the echo arms satisfy `degenerate <= full`.

Two things the totals do NOT say, which matter for the "stable across seeds" reading (F2):

- The selected span sets are IDENTICAL across seeds: 20/20 sessions have the same `selected` spans in the seed-0 and
  seed-2 rows files (72 spans from 116 candidates; the lowest selected probability is 0.994 for seed 0 and 0.875 for
  seed 2), and seed 1's log shows the same per-session column counts (803 total) and coverages. The pinned arm is
  greedy on identical context ids with identical keep spans, so 33/33/33 is ONE deterministic measurement repeated,
  not three estimates. The 46/45/44 spread in the echo arm comes solely from the echo ORDER (`aged_all` is sorted by
  each seed's probabilities), which is an honest +-1 noise floor for that arm.
- The budget-matched arm (CLFB: top spans by probability clipped to the finder's column count, plus its own control),
  which the README calls "the conservative bound" in checks 16-18, is not reported for check 22 at all. It is the
  only arm where seeds actually differ, and they differ a lot: pinned 33 / 27 / 33, pin+echo 45 / 35 / 40,
  columns 793 / 677 / 775. Ranking by probability is seed-unstable even though the threshold set is not.

## 2. The v1 -> v2 spec change and what it makes b3

Timeline from git and file mtimes (all 2026-09-02/03, local):

- 23:24 check 19 committed; its diagnosis names the four probe misses ("finish with this exact postscript line",
  "begin with the exact title <<...>>", "exactly 5 bullet points", "in lowercase letters only").
- 23:24-23:25 LABELS.md v2 written and committed ("after quick check 19"); gen_scope.sh / kimi_gen_scope.py /
  kimi_relabel_scope.py written 23:24-23:25.
- 23:26-23:44 kimi-scope pass generated (4,954 rows, 40 domains). 23:45 relabel pass (469-line unreviewed patch).
- 23:55 Opus approvals (95), 00:00 sol approvals (131), 00:01 final patch = intersection (59).
- 00:06 seed-1 training starts; 00:26 seed 2; ~00:46 seed 0 (rerun); 01:07 check 22 committed.

Precisely what this makes b3 (data/b3/mt-train-300.jsonl, the 20 H1' sessions): it is the SELECTION set for the
mechanism (checks 10-18), the SELECTION set for the classifier design (checks 13-18: enrichment written in response
to check 13's misses; the item-level taxonomy policy chosen after check 16), AND, from check 19 on, the
SPEC-DEVELOPMENT set: the label definition itself (the third scope) was written to cover the specific constraint
types the probe showed as misses, and the generation and relabel prompts carry exemplars taken from those misses
(next section). No claim on b3 is therefore a transfer claim, and — new with v2 — the label semantics are no longer
independent of the probe either. The README's own wording ("development result on the selection set, not
transfer") is correct as far as it goes; it should add "spec developed against the probe".

Is the v2 definition generic or probe-shaped? Both sides, with the scope rows:

- Generic (defensible): the third scope is a real phenomenon of multi-turn work, not an IFEval artefact. The scope
  pass instantiates it across 40 domains with sentences that have nothing to do with the probe — "Start the
  return-instructions email with the RMA number on its own line" (rule, no scope words), "Hold the tone neutral, no
  exclamation marks, in all drafts for this deal" (rule), "Mark the SLO breach as red if it exceeds 30 minutes"
  (rule), versus "For this reply only, include step numbers" (none), "Now extend the gift guide with budget picks"
  (none, continuation), "This one time, skip the formal salutation" (none). Opus's review record (results/
  scope-v2-review-opus.md) draws the boundary with domain-neutral criteria (HOW vs WHAT, whole deliverable vs
  sub-unit, maintainable property vs completed operation). Held-out accuracy on fable's author-disjoint set went UP
  under v2 (0.87 -> 0.85-0.88, flat) rather than down, so v2 did not buy the probe at the cost of the generic task.
- Probe-shaped (also defensible): (a) the trigger was four probe misses, and the amendment was made and committed
  within one minute of check 19, with no non-probe evidence that the v1 labels were wrong; (b) the operative clause
  "when scope is unstated, a constraint on how the work must be written is TASK-scoped (rule)" is exactly the reading
  that makes IFEval-style single-turn formatting constraints ("in lowercase letters only", "exactly 5 bullet
  points") into rules — which is what the probe needs and what a system-prompt-persona or customer-support session
  may not need; (c) the exemplars in both the spec and the kimi prompt are probe-derived (below), so the scope pass
  is dense in the probe's constraint families: 126 word-count caps (14 of them "90 words"), 93 bullet-point rows,
  21 angle-bracket-title rows, 17 forbidden-word rows, 34 "exactly N" rows in 4,954 — versus 0 angle-bracket and
  0 "90 words" rows in the 15,913 earlier rows; (d) reviewer agreement on the new boundary is poor (Opus 95 vs sol
  131 approvals, intersection 59, Jaccard 0.35; sol's 26 "missed" additions include explicitly single-reply
  sentences — "Keep it under fifty words for this speech only", "Use bullet points in each email this time", "For
  this scene only, play him as warm and grandfatherly" — which scope (3) says are none). A boundary two careful
  reviewers place this differently is not yet a generic notion; it is a working definition tuned until the probe
  misses went away.

My reading: the concept is generic, the calibration of its ambiguous edge is probe-shaped, and the exemplar vocabulary
is probe-derived. That is acceptable for a development result and must be stated as such wherever the selector is
described (see F3 for the claim wording).

## 3. Lineage

3a. Nearest-neighbour check, scope pass (4,954 rows) vs the 38 unique probe keep-span sentences (decoded from
results/qwen/ledger-kv-probe-h1p/session-*.json with the Qwen tokenizer: 63 keep spans, 38 unique; one of the 38 is
the continuation "Now add a brief closing section for the same newsletter piece.", which is a finder keep span, not
a constraint). Embedding = bge-small CLS, L2-normalised, cosine; lexical = difflib ratio.

- Max cosine over the 38: min 0.662, median 0.749, mean 0.767, max 0.921; 11 of 38 >= 0.80, 7 >= 0.85, 1 >= 0.90.
  Lexical max ratio: median 0.55, max 0.79. For calibration, probe-to-probe nearest-neighbour cosine (sentences of
  the same family with different fillers) has median 0.895 — none of the training neighbours reaches that.
- No copies and no item-level paraphrases: no scope row shares the probe's filler words, numbers (other than "90"),
  titles, placeholders, or the sentence frames "no fewer than N times", "make sure both of the words", "include
  exactly these four bracketed placeholders", "finish with this exact postscript line", "begin with the exact
  title <<...>>". Those frames have zero lexical hits in all 20,867 training rows and the 801 held-out rows.
- The closest pairs are family-level analogues (top-1 for each probe sentence is in scratchpad/fable_nn_out.txt):
  "keep the reply under 90 words in total." -> "Keep it under 90 words." (cos 0.921, twice in the scope pass;
  teaching-assistant-grading:15, financial-planning-chat:32) and "Keep the summary under 90 words." (0.898);
  "keep the reply under 110 words in total." -> "Just this once, keep the reply under 100 words." (0.890, none);
  "respond using only capital letters throughout." / "in lowercase letters only" -> "From now on, respond only in
  lowercase letters." (0.893 / 0.868); "write at least 11 full sentences." -> "Keep sentences short. Eight words
  max." (0.853); "Now add a brief closing section for the same newsletter piece." -> "Now add a closing section to
  the letter." (0.874, none). Everything else is <= 0.83.
- Same check on the earlier training rows (kimi + kimi-ctx + enrich, 15,913): max 0.885, 2 >= 0.85, 0 >= 0.90 —
  the scope pass is measurably closer to the probe than the earlier data, as expected from (c) above.

3b. The paraphrase flags, and where they come from. The "90 words" and "angle-bracket title" analogues are not
kimi's invention: LABELS.md v2 and the kimi_gen_scope.py prompt list "keep it under 90 words", "begin with a title in
angle brackets" / "begin with the title <<...>>", "no bullet points", "end with a P.S." as the canonical task-scoped
examples, and kimi_relabel_scope.py's prompt repeats them. Those four exemplars are the four constraint types of the
probe misses in check 19, with the probe's own number (90) kept. Before the scope pass there were 0 "90 words" rows
and 0 angle-bracket rows in training; after it there are 14 and 21. This is the mechanism by which probe knowledge
entered training: not by copying rows but by choosing the spec's exemplar vocabulary from the probe and handing it to
the generator. It is taxonomy-level (the README's item-level disjointness policy, check 16 correction (c), permits
it), but it is a step beyond "constraint-family analogues exist by design", because the families were selected AFTER
seeing which ones the classifier missed on the evaluation set.

Irony worth recording: the exemplar "end with a P.S." produced exactly one training row (a none: "Extend the welcome
email with a P.S. about the referral bonus"), and the three postscript sentences remain the classifier's only true
misses on the probe for all three seeds (P(keep) 0.01-0.06; the fourth sub-0.5 sentence is the continuation, scored
0.00, correctly). 34/38 pass at 0.5 for every seed. So the pinned deficit vs the finder (33 vs 37) is the postscript
family, and it is the family the spec change did NOT manage to teach.

3c. The relabel pipeline (kimi proposes -> Opus and sol approve independently -> intersection). Ways probe knowledge
could enter: (i) the kimi relabel prompt (same probe-derived exemplars as above) — it only chooses among EXISTING
rows written under v1 before check 19, so it can re-label but not import probe text; (ii) the reviewers: Opus's record
states the criteria and 20 rejections and adds nothing; sol added 26 rows, none from the probe; (iii) held-out
leakage: the relabel pass ran over heldout/* too and proposed 26 held-out rows (fable-validation 14, opus-heldout 11,
sol 1); Opus approved none, sol approved 5, the intersection contains 0 — so the reported held-out numbers are on
unchanged v1 labels (which slightly penalises a v2 model; fine, conservative). Final patch: 59 rows, all
`new_label: rule`, no drops, sources kimi-k3-ctx 39 / kimi-k3 19 / sol-enrich 1; no probe family patterns in it
(0 word caps, 0 titles, 0 P.S., 1 bullet-point row). I find no path by which a probe sentence or paraphrase entered
a training row through the relabel pipeline. The exemplar path in 3b is the only import, and it is via the spec.

3d. Evaluation-benchmark lineage: the trainer never reads data/bench (asserted in its docstring; the glob list is
kimi, kimi-ctx, kimi-scope, *-enrich, heldout, review/*-patch.jsonl — verified by reading the code). I did not open
data/bench. The scope prompt tells kimi not to copy IFEval/Multi-IF/BFCL/tau-bench; that is an instruction, not a
check — the item-level check against Multi-IF/BFCL sentences is still owed before the post-development leg and is
not in this review's scope.

## 4. Seed 0's training set vs seeds 1-2 — the README's premise is wrong

README check 22: "seed 0 rerun after the 59-row reviewed relabel patch landed, so its training set differs slightly
from seeds 1-2". Evidence that all three seeds trained on the SAME data, patch included:

- The trainer picks up patches with `glob(review/*-patch.jsonl)`; `scope-v2-final-patch.jsonl` matches that
  pattern (the unreviewed file `scope-v2-patch.unreviewed.jsonl` does not). The final patch was written at
  00:01:03 (mtime; commit 00:01:21). The seed-1 trainer started at 00:06:42 (birth time of scratchpad/ft_v2_s1.log;
  its model saved 00:09:10) and seed 2 at 00:26:12 (saved 00:28:40). Seed 0's log (birth 23:51:34, i.e. a first
  attempt before the list-context fix at 23:52:55) was rewritten ~00:46-00:48:45. Every training run that produced a
  check-21/22 model started after the patch existed on disk.
- `train 20385` cannot discriminate: the patch is relabel-only (no drops) and I reproduce 20385 both with and without
  it (see F5 for how I reproduce it at all).
- Behavioural check on CPU: P(rule)+P(fact) >= 0.5 on the 59 patch rows is 44/59 (mean 0.74) for the `ft` model,
  47/59 (0.77) for ft-seed1 and 46/59 (0.76) for ft-seed2, against 21-30/377 (mean 0.07-0.09) on the 377 rows kimi
  proposed and the reviewers rejected (which stayed none). With training loss 0.08 after three epochs, seeds 1-2
  would not score 80% of rows they had been trained to call none this high while scoring their rejected siblings
  at 8%. All three models learned the patch.

Consequences: the three-seed agreement in check 22 IS an identical-data result already; the "FINAL identical-data
run" is a replication, not a correction. The README/ledger sentence must be corrected. The replication is still
worth finishing for one reason — the check-22 seed-0 artifact no longer exists on disk (F6) — and it must show:
(i) `train 20385` under a pinned patch order (F5); (ii) seed 0 held-out metrics identical to ft_v2_s0.log (the
FINAL seed 0 already reproduces the ep3 dict to all printed digits; data/classifier/model/ft/metrics.json ==
log line, verified); (iii) the same 72 selected spans (803 columns, coverage 0.859) for each seed; (iv) pinned
33/33/33 exactly (deterministic given (iii)), echo within the 44-46 band; (v) sha256 of encoder/model.safetensors
and head.pt per seed recorded in WORKLOG before any Multi-IF arm. If (iii) fails for any seed, the stability claim
was never about seeds and the selection is sensitive to something unrecorded.

## 5. What must be registered verbatim before the post-development evaluation

The draft at scratchpad/selector-v2-registration.md already covers most of this (arms incl. role_pinned at equal
columns, exact-column control post-clamp, protected prefix, greedy/512/300 s, three Holm contrasts, ROUND-7 safety
clause, preflight 20 -> 909 only if <= 12 GPU-h, outcome rules, seed 0 only). Items it must state verbatim and does
not yet, or states wrongly:

1. Selector artifact: `data/classifier/model/ft/encoder/model.safetensors` sha256 and `head.pt` sha256 of the FINAL
   seed-0 run, written into WORKLOG and the harness meta BEFORE the first Multi-IF arm, plus the trainer's git blob
   hash and the exact patch-file precedence (F5). Today's values: encoder 56f73260...3e61, head da31f2a0...e251 —
   these are the FINAL run's, not check 22's.
2. Data lineage sentence, corrected: "Training rows are hand-written and item-disjoint from every benchmark and from
   the b3 probe (nearest-neighbour audit: no copies, max cosine 0.92 for 'keep it under 90 words'). The label spec
   (v2) and the scope-pass generation prompt were developed against the b3 probe after check 19, and their exemplar
   constraint types ('keep it under 90 words', 'begin with a title in angle brackets', 'no bullet points', 'end with a
   P.S.') were chosen from the probe's misses; constraint-type overlap with IFEval is therefore deliberate and
   probe-directed." The draft's model-card line "no benchmark item or paraphrase entered training" should be
   narrowed to "no benchmark or probe item entered training; family-level paraphrases of the probe's constraint
   types were introduced by the spec's exemplars".
3. Threshold 0.5, no-context scoring, role "user", the registered sentence splitter (clf_score_sessions.py's
   split_sentences/user_turns, by hash), and the budget rule: unclipped set (all spans >= 0.5) is the primary arm;
   the budget-matched clip is reported alongside with its per-seed instability disclosed (33/27/33 on the probe).
4. Control: exact-column matched control drawn from the same role pool (prior user turns) AFTER the echo clamp, as in
   clf_probe_check.py; state that the control's truncation count on the probe sat at full+1.
5. Eviction: the draft's harness (scripts/multiif_evict.py) does not exist yet; the registration must name the
   harness file and its hash once written and must assert, with an instrumented column count per arm, that the
   evicted/pinned arms actually drop columns — scripts/ledger_eval.py's text_ledger runner has no eviction code path
   at all (0 occurrences of "evict"; it re-appends ledger text to a full context) and cannot serve.
6. Claim wording for the probe result, fixed now: "On the development probe (20 sessions, 56 aged constraints), the
   fine-tuned selector at threshold 0.5 selects the same 72 spans for all three seeds (0.86x the taxonomy finder's
   columns); pinned 33 (finder 37), pinned+echo 44-46 (finder 48, full context 44), exact-column control 17,
   evicted 14. The pinned number is a single deterministic measurement; the echo spread is order noise." Not:
   "three seeds agree within +-1".
7. Stop rule: any change to the classifier data, spec or threshold after the first Multi-IF arm voids the leg
   (the draft says this for outcomes; say it for inputs too).

## Findings

- F1 (MEDIUM) README check 22 / ledger: "seed 0's training set differs slightly from seeds 1-2" is false — all
  three seeds trained with the 59-row final patch (glob match + timestamps + model behaviour, Section 4). The
  identical-data replication was launched on a wrong premise; correct the record before registration.
- F2 (MEDIUM) "Three seeds agree within +-1" overstates: the selected span sets are identical across seeds, so the
  pinned arm is one measurement and the echo spread is echo-order noise. The stability that IS shown — the threshold
  set does not move across seeds — is the useful fact; say that instead. The budget-matched arm, where seeds do
  differ (27-33 / 35-45), is omitted from check 22.
- F3 (HIGH, claim wording, not numbers) Lineage: no probe item or item-level paraphrase is in any training row
  (nearest-neighbour + frame search), but the v2 spec's and the generation/relabel prompts' exemplars were chosen
  from the probe's check-19 misses and carry the probe's number ("90 words") and formats ("title in angle
  brackets"); the scope pass is 2x denser in those families than the earlier data and is measurably closer to the
  probe (max cos 0.921 vs 0.885). The registration's "benchmark-disjoint ... no paraphrase" wording must be narrowed
  as in Section 5 item 2. Blocking for the claim text, not for the development result.
- F4 (MEDIUM) The v2 boundary is under-determined at the reply/artifact edge: Opus/sol approvals overlap at Jaccard
  0.35, sol approved explicitly single-reply sentences as rule (removed only by the intersection). Record the
  intersection rule and the two review files as part of the spec; add the agreement figure to LABELS.md.
- F5 (LOW) The trainer's patch precedence depends on os.listdir order: 28 (source,text) keys appear in both
  sol-patch and opus-patch; with listdir order (sol, opus, final) 19 sol drops are overridden by opus entries and
  train = 20385 (reproduces the logs); with sorted order train = 20369. Pin the order (sorted, or explicit list)
  and re-state train_n in the registration.
- F6 (LOW) `data/classifier/model/ft/` was overwritten at 01:09:48 by the FINAL chain, after the check-22 commit, so
  the check-22 seed-0 weights are gone; their held-out metrics are reproduced digit-for-digit by the FINAL seed 0,
  which is strong evidence of bitwise reproduction but not a hash. Record the FINAL hashes and treat them as the
  registered artifact.
- F7 (LOW) "38 unique true constraint sentences" (check 19) includes one finder keep span that is a continuation
  ("Now add a brief closing section ..."); it is correctly scored 0.00 and drags coverage's denominator. The only
  genuine misses, all seeds, are the three "finish with this exact postscript line" sentences.
- F8 (INFO) Arithmetic confirmed: per-seed totals, means (33.0 / 45.0 / 17), 0.862 column ratio, coverage 0.859,
  held-out 0.900/0.898/0.900, fable 0.851-0.879, none precision 0.946-0.958, seed-2 safety 0/0 and 0/2 vs full 1/2.

## VERDICT: CONFIRMED-WITH-QUALIFICATIONS

The numbers in checks 19-22 reproduce exactly from the artifacts, the selector is benchmark- and probe-disjoint at
the item level, and the no-context 0.5-threshold selection is genuinely seed-stable. The qualifications are about
what those numbers mean and how they are worded: the three seeds were trained on identical data (README wrong), the
pinned "agreement" is one measurement, the budget-matched arm is unstable and unreported, and the v2 spec plus its
generation exemplars were developed against the probe with probe-derived vocabulary — so the result is a
development result on a selection-and-spec-development set, and the registration's disjointness sentence must say
so before Multi-IF or BFCL is run.
