# Check 16 review — fable (independent, CPU-only), 2026-09-03

Scope: README items 13-16 (clf_probe4_{rows.json,log,metrics.json}, train_classifier.py, clf_score_sessions.py,
clf_probe_check.py, heldout_sweep.py), data/classifier/ (train, patches, held-out), the H1' records. Everything
below was recomputed with CPU scripts in the scratchpad (c16_totals.py, c16_data.py, c16_lineage.py,
c16_lineage2.py, c16_ablate.py, c16_seeds.py; logs alongside). The Qwen tokenizer was used to decode spans; the
bge-small encoder and the MLP head were run on CPU. No GPU process was launched, nothing under data/bench/ was read,
nothing was signalled. Note on timing: while this review ran, the orchestrator committed 1ea860d (check-16
correction after sol's review), 7445b70 (fable-validation set), and 759df7f (check 18), and RETRAINED
data/classifier/model/clf.pt (23:03). Findings below are independent of those; where they overlap with sol's I say
so, and F1 (seed instability) is new and changes the reading of checks 14-18.

## 1. Totals, columns, coverage, safety — recomputed from the rows

| quantity | README | recomputed |
|---|---|---|
| full / evicted / finder / finder_echo | 44 / 14 / 37 / 48 | 44 / 14 / 37 / 48 (h1p block == H1' session records, all 20) |
| CLF pinned / pinned_echo / control | 38 / 44 / 16 | 38 / 44 / 16 |
| CLFB ("budget-matched") pinned / echo / control | 29 / 37 / 19 | 29 / 37 / 19 |
| n aged | 56 | 56 |
| coverage | 0.89, 17/20 >= 0.8 | 0.890, 17/20 (recomputed from `selected` spans vs `keep`, exact) |
| candidates / selected | 116 / 74 | 116 / 74 (0.638) |
| CLF cols mean vs finder | 42 vs 47, ratio 0.91 | 42.3 vs 46.6, ratio 0.908 (sums 846 vs 932); 17/20 sessions at or under the finder |
| control columns == pinned columns (post-clamp) | claimed | asserted true for all 20 sessions and both arms |

Paired per session (win/lose/tie): CLF_pinned vs finder +2/-1/=17; CLF_echo vs finder_echo +1/-4/=15; CLF_echo vs
full +4/-4/=12; CLF_pinned vs its control +14/-0/=6 (sign test p ~ 6e-5). So: the selector beats its position-matched
null decisively; every CLF-vs-finder difference (38 vs 37, 44 vs 48) is inside session noise.

Classifier scores: I re-derived all 116 sentence probabilities from the (then-current) clf.pt on CPU — max abs diff
5e-7 against the scores file the probe consumed — and the held-out metrics (acc 0.7945, "none" recall 0.608) and the
sweep (thr 0.5: 0.763/0.965; 0.65: 0.827/0.930; 0.8: 0.885/0.778) reproduce. train_sha reproduces from the raw
files + patches (15,913 raw -> 530 dropped, 98 relabelled incl. 42 role fixes -> 15,258 after dedupe).

### F2 (MEDIUM) — "0 truncated / 0 degenerate" is true of the echo arm, not of the arm the sentence names
The budget note attaches the exact-zero to "the unclipped CLF arm ... pinned 38". CLF_pinned has 1 truncated / 1
degenerate (s18, aged_pass 2/3); CLF_pinned_echo is 0/0; CLF_control 2/2; CLFB_echo 1/1. For reference the finder's
pinned arm is 0/0, pinned_echo 0/1, full 1/2. Within the H1' safety rule (<= 2/20), but the sentence must be
re-scoped. (Same as sol MEDIUM 3.)

### F3 (MEDIUM) — the "budget-matched" arm is not budget-matched; it is a ~0.67x-budget arm
CLFB columns equal the finder budget in 0/20 sessions: mean 31.25 vs 46.6 (sum 625 vs 932). Mechanism: the reminder
sentence "Every earlier constraint from this conversation still applies..." scores 0.985 in all 20 sessions (it is
rule-shaped), ranks FIRST in the probability order, consumes ~14 columns per prior turn of the clip budget, and is
then removed by the echo clamp (echo_context cuts at that sentence) — for both CLFB arms, since the clamp precedes
all arms. In sessions where the selection is already under budget the clip is a no-op, so CLFB also inherits every
miss. 29/37 is therefore a below-budget bound, not an equal-cost comparison; the README's "conservative bound" is
right in direction, the label is wrong. Fix: clip AFTER the clamp (or exclude the reminder before ranking) and clip
to the deduplicated column count. In deployment there is no reminder sentence, so this is a probe artefact — but it
is the artefact that makes the budget-matched numbers (checks 13-18) uninterpretable as equal-cost.

### F4 (LOW) — coverage counts a task sentence as a constraint
"Now add a brief closing section for the same newsletter piece." sits inside the finder's keep spans in 7 sessions;
the classifier scores it 0.499 (correctly "none" per LABELS.md, and one thousandth under the threshold). Max
attainable coverage for a correct classifier is < 1 on those sessions; README 15(b) already notes this. The other
sub-threshold constraint is the `<<title>>` clause (0.37-0.56 across sessions).

## 2. Lineage — nearest-neighbour check, done

Method: decode the 63 keep spans of the 20 H1' sessions (38 unique constraint sentences) with the Qwen tokenizer;
embed them and all 15,258 training rows with bge-small-en-v1.5 (CPU); list the 100 training rows nearest to any
probe constraint sentence (c16_nn100.json, full list in c16_lineage.log). Lexical cross-check: normalized 5-gram
overlap and literal fingerprints.

Result: NO item-level copy or paraphrase of a b3 constraint sentence in training. Max cosine 0.830; 0 rows >= 0.85;
6 rows >= 0.80; median 0.58. Zero training rows share a normalized 5-gram with any probe constraint sentence.
Fingerprints: "P.P.S"/postscript 0, "<<" 0, "exact title" 0, "bracketed placeholder" 0, "at least N sentences" 0,
"exactly N bullet" 0, "Every earlier constraint" 0, "Constraint:" 0; 'tallow' 1 (a fantasy character name, chance).
Held-out rows: max 0.73 to any probe sentence. The 100 nearest are all family-level analogues, e.g. #1 "Never start
a sentence with 'I' in your replies." (0.830 ~ "never use the words 'harbor' or 'signal'..."), #4 "Whenever you
draft a report comment, keep it under 100 words." (0.815 ~ "keep the reply under 90 words in total."), #6 "Use five
bullets for summaries unless I ask otherwise." (0.801 ~ "format the reply as exactly 5 bullet points..."). I count
~15 of the 100 as constraint-family analogues (forbidden words, length caps, bullet counts, casing); the rest are
generic style rules and one-off edits. Sol's "~12 analogues" agrees.

### F5 (HIGH, confirms sol HIGH 1 independently) — 4 enrichment rows paraphrase the probe's TASK sentences
Nearest training rows to the probe's one-off task sentences (c16_lineage2.log): #1 sol-enrich "Write a short account
of the council vote for tomorrow's neighborhood newsletter." (0.826 to "Write a short account of pressing apples for
cider for a neighborhood newsletter."), #3 opus-enrich "Write a short account of the fundraiser for this month's
newsletter.", and the two "Now add a closing section that {thanks the volunteers | explains what residents can do
next}." rows. The vector is the enrichment brief (scratchpad classifier-data-review-brief.md), which quoted check
13's b3 failures verbatim as the first-priority hard negatives. So the training set was shaped by b3 feedback; "never
saw b3" is false by paraphrase for these 4 rows, and by design for the enrichment priorities. Effect size: an
ablation that removes the 4 rows (c16_ablate.py run B) leaves the task-sentence scores unchanged (0.263 -> 0.271
etc.) and the held-out metrics identical — the rows are not what drives task rejection (the kimi bulk already has
hundreds of "Make it shorter."-type one-offs; the top-100 nearest to task sentences are 93% kimi rows). The
lineage violation is real but its leverage on the number is small; the b3-feedback loop as a whole (checks 13-18 = 6
looks) is the issue, and the README correction (1ea860d) now says so.

### F6 (MEDIUM, = sol HIGH 2) — "author-disjoint" held-out was author-shared
opus-enrich (434, train) and opus-heldout (238, val) have the same author; likewise sol. True author-disjoint
estimates from my refits (same trainer path, seed 0, bs128 features): without opus-enrich, opus-heldout 0.828 ->
0.819; without sol-enrich, sol-heldout 0.780 -> 0.760; kimi-only training gives 0.788 overall. The author effect is
small next to the style effect that check 18 later measured on fable-validation (0.67). Consistent.

## 3. Fairness of the finder comparison — confirmed with two caveats
- Threshold: `THR = float(os.environ.get("CLF_THR", "0.5"))` is in clf_probe_check.py at its first commit
  (602bd1d, 21:06, check 13); clf_probe.log prints thr=0.5. Fixed before any probe run. Thr 0.65 (check 17) came
  from the held-out sweep — but the decision to sweep came after seeing b3 precision, and 0.65 was then rejected on
  b3 (README 17): that is threshold selection on the selection set. Fine for a selection set; must be frozen before
  Multi-IF.
- Control: computed after the clamp from the surviving keep, position-matched, column count == pinned (verified).
- Columns: CLF's lower cost (0.91x) is partly lower coverage: in s12 and s15 CLF pins 18-19 columns vs 48-49 because
  it rejects the title clause and the closing-section sentence (coverage 0.38/0.39). Cheaper and worse there.
- The arms/harness are byte-identical to check 13's (results copies == scratchpad copies).

## 4. F1 (HIGH, NEW) — the check-16 head is a single lucky seed; the result does not survive seed or 1e-7 numerics

Replicating train_classifier.py exactly (bs=64 embeddings, `torch.manual_seed(0)`, MLP, LBFGS lr 0.3 / 400
iterations, dropout 0.2 active inside the LBFGS closure) reproduces check 16 to the digit: held-out 0.7945, sweep
0.763/0.965 @0.5 and 0.827/0.930 @0.65, probe selection 52/61 constraint sentences and 2/35 task sentences, coverage
0.890 (17/20). Then, same data, same code (c16_seeds.log, c16_ablate.log):

| head | held-out acc | probe constraints selected @0.5 | coverage @0.5 | @0.65 |
|---|---|---|---|---|
| seed 0, bs64 features (= check 16) | 0.7945 | 52/61 | 0.890 (17/20) | 0.652 (7/20) = check 17 exactly |
| seed 0, bs128 features (max |dE| = 2e-7) | 0.8059 | 34/61 | 0.582 (4/20) | — |
| seed 1 | 0.8014 | 34/61 | 0.582 (4/20) | 0.309 (0/20) |
| seed 2 | 0.8059 | 34/61 | 0.582 (4/20) | 0.309 (0/20) |
| seed 0, dropout off during LBFGS | 0.8219 | 34/61 | 0.582 (4/20) | 0.394 (0/20) |
| clf.pt retrained by the orchestrator at 23:03 (check 18 data) | 0.8037 | 35/61 | 0.596 (5/20) | 0.362 |

Held-out accuracy barely moves (0.79-0.82) while the probe coverage swings 0.89 <-> 0.58 — every alternative head lands
on ~34/61, the check-16 head is the outlier. The mechanism is the trainer: dropout resampled on every closure call
makes the LBFGS objective stochastic, so the line search wanders and the optimum reached depends on seed and on
float noise; with dropout off the run is deterministic but still sits at 34/61. Consequences: (a) the check-16
headline 38 / 44 is one draw of a training-seed distribution whose typical member gives ~check-17/18 numbers (31/37,
29/36) — the 14-16 -> 17-18 "differences" are seed noise, not data effects; (b) README 18's "unstable at n=56" is
right but mis-attributes the instability: the evaluation is the same 116 sentences, the TRAINING is unstable;
(c) any future comparison (fine-tune vs frozen, policy A vs B) needs >= 3 seeds and a seed-registered head, else
it measures the seed. Also: the check-16 clf.pt no longer exists on disk (overwritten at 23:03, never committed;
data/classifier/model/ is untracked) — it can be regenerated only by the bs=64/seed-0 path above.

Ablations under this caveat (all seed 0, bs128 features, so comparable to the 0.582 baseline, not to check 16):
minus the 4 b3-paraphrase rows 0.596; minus opus-enrich 0.596; minus sol-enrich 0.523; kimi-only 0.634; sol's 309
taxonomy-family drops RESTORED 0.596, with per-type mean scores moving only +0.01 to +0.09 ("keep under N words"
0.54 -> 0.63, "at least N sentences" 0.37 -> 0.45, "exactly N bullets" 0.31 -> 0.37; title/postscript unchanged
~0.40/0.46). So kimi's "restore the 344 rows" and README 17's "the lever is plain-language formatting coverage"
are not supported by the data: restoration barely moves the formatting types, and check 18 (282 restored) got the
typical-seed result, as predicted. The frozen-embedding head simply does not place the title/postscript/bullet
clauses above 0.5, whichever rows are present.

## 5. The taxonomy-drop dispute (item 4)

Facts: sol's patch drops 495 keys (311 with a taxonomy/benchmark reason by my count of reasons; sol reports 344, the
difference is wording), 272 of them labelled `rule`; Opus dropped 11 exact/tautological phrasings. After sol's purge
plain-language formatting rules still survive in train (my surface scan: "keep it under 100 words" 1, "no bullet"
family ~30, section/heading ~90, casing 2, forbidden-word family dozens) — the purge was neither complete nor
completable, because "keep replies short", "no bullets ever", "never say 'delve'" are ordinary user rules.

Ruling: item-level disjointness with deliberate, DECLARED type overlap (Opus's policy) is right for a generic
classifier, with two conditions. Leakage risks stated honestly:
- Opus policy risk: Multi-IF is IFEval-typed, so a classifier trained on the same constraint TYPES is in-distribution
  by type on Multi-IF; its Multi-IF number cannot be read as generalization to unseen rule types. It is not
  benchmark contamination (no items, kwargs, or benchmark text; the NN audit above is the evidence), but it is
  "trained on the benchmark's taxonomy" and the card must say so.
- Sol policy risk: the classifier is made blind to a legitimate rule class, Multi-IF then underestimates a deployed
  selector, the purge is inconsistent (survivors above), and the "not even by paraphrase of the taxonomy" claim
  would be unverifiable in any case (kimi-k3 and the reviewers know IFEval from pretraining; the generation prompt
  even names the benchmarks).
Conditions: (1) cap the share of any IFEval-typed family in training and report the per-family counts; (2) the
zero-shot/transfer claim rests on the no-contact family (constraint types absent from training, blinded authors)
and on BFCL (non-formatting), never on Multi-IF alone. Model card must state: authors and prompts of every row
source with dates; the two enrichment briefs and the 4 b3-paraphrase rows; that b3 was used as the selection set
for threshold, head and data policy across checks 13-18 (six looks); the per-family taxonomy counts; the
author-shared held-out and the author-disjoint validation set with their accuracies; the training seed and its
measured sensitivity (F1); the NN-audit numbers (max cosine 0.83, 0 shared 5-grams).

## 6. What must be registered before Multi-IF 909 / BFCL (item 5)
1. Artifacts, sealed with hashes: the exact clf.pt (committed with `git add -f`), train file list + patch files + train
   sha, trainer command with seed(s), the scores file the probe consumed (results/quick-checks/clf_scores.json is
   STALE — it is check 13's 120-sentence old-splitter file, not check 16's 116-sentence file, which lives only in
   the scratchpad), splitter version, finder/harness/evaluator versions.
2. Seeds: train >= 3 seeds; register the selection rule for the deployed head (e.g., median held-out on the
   author-disjoint validation set) BEFORE looking at any benchmark; report the seed spread.
3. Threshold: one value, chosen on the author-disjoint validation set by a stated objective, frozen; no post-hoc
   sweep on benchmark outcomes.
4. Arms: full, evicted, CLF pinned, CLF pinned_echo, position-matched control (post-clamp, equal deduplicated
   columns), and a budget-matched finder or role-rule comparator with the clip applied AFTER the clamp; primary
   metric named in advance (aged pass / 909, per-turn); paired sign test with the 20-session noise in mind.
5. Safety: truncated/degenerate counts per arm with the H1' kill rule; report per arm, not per "the CLF arm".
6. Lineage statement as in section 5, plus a rerun of this NN audit against Multi-IF's and BFCL's instruction texts
   by a reader that is allowed to touch data/bench/ (I was not), before the benchmark run.
7. Budget: report deduplicated pinned columns per session for every arm; state the cost ratio with its per-session
   range, not only the mean.

## Verdict

Arithmetic, columns, coverage, control construction and the fixed 0.5 threshold: confirmed. The claim as briefed is
REFUTED on three counts: (i) "never saw b3 or any paraphrase" — false: enrichment was written against b3's failures
and contains 4 paraphrases of its task sentences (leverage small, loop real); (ii) "0 truncated / 0 degenerate"
is true only of the echo arm; "budget-matched" is a 0.67x-budget arm; (iii) NEW and decisive: the head that produced
38 / 44 is a seed-0 draw — seeds 1-2, a 2e-7 feature perturbation, dropout-off, and the retrained checkpoint all give
~34/61 constraint selection and coverage ~0.58, i.e. check-17/18-level outcomes. Check 16 is a development result
on a selection set at one seed; nothing in checks 13-18 separates data policy from seed noise.

VERDICT: REFUTED (as a lineage-clean, reproducible selector result); the corrected reading in README 1ea860d/18
("development results on a selection set; none is a transfer claim") is CONFIRMED-WITH-QUALIFICATIONS, the main
qualification being F1: register seeds and the head-selection rule before the fine-tune (check 19) is compared to
anything.
