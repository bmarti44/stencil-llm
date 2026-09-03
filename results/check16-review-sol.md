# Quick check 16 review — generic classifier as selector (2026-09-03)

## Scope and method

I reviewed the requested quick-check artifacts, the classifier data and review patches, the 20 H1' session records,
and relevant git history. I did not read any file under an evaluation-benchmark directory. The only model execution
was the permitted `BAAI/bge-small-en-v1.5` encoder and classifier head on CPU; no Qwen generation or GPU process was
launched.

I independently summed the row JSON, reconciled every inherited H1' result and finder budget to its source session,
reconstructed the post-patch training set, rescored the probe sentences with the current CPU classifier checkpoint,
and ranked all 15,258 post-patch training rows against the 56 true aged b3 `Constraint:` clauses by maximum cosine
similarity of normalized bge-small CLS embeddings. The similarity screen used target sentence text (with role prefix),
not the finder-selected spans; this avoids admitting the finder's task-sentence false positives into the requested
constraint sample.

## Findings

### HIGH 1 — The “never saw b3” and transfer claims are false

Check 13 and its b3 results were committed at `602bd1d` (21:06). The later training enrichment was explicitly written
in response to that result:

- The Opus review says its “first priority” was “the measured gap (quick-checks item 13).” Its enrichment, committed
  at `82c9b7b` (21:51), includes “Now add a closing section that thanks the volunteers,” a close paraphrase of b3's
  “Now add a brief closing section for the same newsletter piece,” plus the paired standing newsletter rule.
- `sol-enrich.jsonl`, committed at `788668b` (22:10), starts with the same b3-specific newsletter/task contrast and
  includes “Now add a closing section that explains what residents can do next.”
- Check 15's own diagnosis quotes the b3 task sentence and says enrichment is the remedy. Thus the development
  pipeline used the probe not just to choose a mechanism, but to shape that mechanism's training examples.

This does not erase the measured check-16 outputs; b3 is a development/selection set, so they remain legitimate
development measurements. It does erase the characterization of check 16 as transfer by a classifier that “never
saw b3.” The classifier should be described as **developed on b3 feedback** and check 16 as a selected-on-probe
result.

The required nearest-neighbour audit gives a more nuanced result. Among the 100 closest training targets to the 56
true b3 constraint clauses, I found no exact copy and no reuse of b3's nonce words, titles, placeholders, or postscript
text. I did find at least 12 clear constraint-family analogues, including 100-word caps versus b3's 90/110-word caps,
five-bullet summaries versus exactly five bullets, named forbidden words, upper/lower-case rules, and maximum sentence
counts versus b3's minimum sentence counts. These are not evidence of copying a particular row; they are taxonomy-level
overlap. They contradict the stronger “not even by paraphrase of the instruction taxonomy” language in `LABELS.md`.

### HIGH 2 — The 438-row held-out set is not author-disjoint from training

The file split is real and the trainer does not glob `heldout/`. There is also zero normalized exact-text overlap
between the reconstructed training and held-out sets. But the full training set contains 434 `opus-enrich` rows and
421 `sol-enrich` rows, while the held-out set contains 238 `opus-heldout` rows and 200 `sol-heldout` rows. The same two
authors wrote both sides. The review reports use the narrower formulation “author-disjoint from kimi,” which is not
author-disjoint from the full training set used by check 16.

Therefore the 0.7945 accuracy and 0.6077 `none` recall are confirmed as metrics on a path-disjoint, exact-text-disjoint
split, but not on an author-disjoint transfer set. Using this split to select a threshold risks selecting for Sol/Opus
wording and contrast-pair style. A threshold-validation set written by authors/models that supplied no training rows is
needed for the claimed boundary.

### MEDIUM 3 — The exact-zero safety claim is scoped to the wrong arm

The row-level safety counts are:

| arm | truncated sessions | degenerate sessions |
|---|---:|---:|
| `CLF_pinned` | 1 (session 18) | 1 (session 18) |
| `CLF_pinned_echo` | 0 | 0 |
| `CLF_control` | 2 (11, 15) | 2 (11, 15) |
| `CLFB_pinned` | 0 | 0 |
| `CLFB_pinned_echo` | 1 (19) | 1 (19) |
| `CLFB_control` | 1 (15) | 1 (15) |

Thus 0/0 is true only for the unclipped pinned+echo arm (and clipped pinned), not for the unclipped pinned result whose
38/56 score the budget note uses, nor for the full set of reported outputs. `CLF_pinned` is still no worse than the
H1' full-context baseline (1 truncation, 2 degenerate sessions), but the exact-zero wording must be arm-qualified.

### MEDIUM 4 — The check-16 classifier-to-score artifact chain is not sealed

The tracked `results/quick-checks/clf_scores.json` is byte-identical to the file committed with check 13's 2.5k-row
linear classifier (`sha256 85be4b...`) and does not contain the probabilities in check-16 rows. The matching MLP
checkpoint is currently untracked (`data/classifier/model/clf.pt`, `sha256 4963ec...`). A fresh CPU score with that
checkpoint and the fixed splitter reproduced all 74 selected spans and rounded probabilities in check 16 with zero
session mismatches, and its `metrics.json` is byte-identical to `clf_probe4_metrics.json`. This is good present-state
cross-validation, but a clean checkout cannot reconstruct the check from tracked artifacts alone.

Also, `train_sha` hashes only sorted target text. It does not bind labels, roles, contexts, sources, review patches, or
the encoder revision. Those fields can change the model without changing the recorded hash. This must be replaced by a
canonical full-row/manifest hash before confirmatory evaluation.

### MEDIUM 5 — Threshold 0.5 is stable, but pre-check-13 fixation is not independently registered

The check-13 log confirms execution at 0.5, and git blame shows the unchanged default
`CLF_THR=0.5` originated in the check-13 commit. The parent commit contains no threshold registration. Therefore the
available history supports “0.5 was used from check 13 onward and was not changed after later probe results,” but it
cannot independently confirm that 0.5 was immutably fixed before the first check-13 probe was inspected.

The held-out sweep supports 0.5 at precision/recall 0.763/0.965 and 0.8 at 0.885/0.778. The script does not test 0.65.
An exact CPU recomputation at 0.65 gives 239 TP, 50 FP, 18 FN, 131 TN: precision **0.827**, recall **0.930**, not the
README's approximately 0.83/0.95. More importantly, that selection set has the author-overlap described above.

### LOW 6 — Patch bookkeeping calls role fixes “relabels”

The final size of 15,258 is reproducible: 15,913 valid raw rows, 530 physical rows dropped, then 125 rows removed by
the trainer's `(text, label, role)` deduplication. The trainer's “98 relabelled” counter consists of 28 label changes
and 70 role changes. The headline size is correct, but “98 relabels” and “15,258 rows after 530 drops” omit these two
distinctions.

## Numerical and comparison verification

All inherited H1' full/evicted/finder/finder-echo values and finder column budgets in the four classifier row files
match the original 20 session records exactly.

| check | coverage mean (sessions >= 0.8) | CLF pin / echo / control | clipped pin / echo / control | CLF cols / finder cols |
|---|---:|---:|---:|---:|
| 13 | 0.940 (17/20) | 37 / 47 / 22 | 27 / 34 / 20 | 1,144 / 932 = 1.227x |
| 14 | 0.906 (15/20) | 35 / 39 / 22 | 27 / 29 / 20 | 988 / 932 = 1.060x |
| 15 | 0.659 (6/20) | 34 / 39 / 22 | 28 / 34 / 20 | 726 / 932 = 0.779x |
| 16 | 0.890 (17/20) | 38 / 44 / 16 | 29 / 37 / 19 | 846 / 932 = 0.9077x |

For check 16 specifically:

- Denominator: 56 aged constraints; full 44, evicted 14, finder pinned 37, finder pinned+echo 48.
- The claimed 38/44/16 and clipped 29/37/19 all recompute exactly from rows.
- The unclipped classifier selects 74 of 116 candidate sentences. Mean unique pinned columns are 42.3 versus 46.6
  for the finder, accurately rounded to 42 versus 47 and 0.91x. It is at or below the finder in 17/20 sessions.
- `matched_control_spans` is called after echo-feasibility clamping and constructs the same number of deduplicated
  surviving columns. Every row's recorded control `pinned_cols` equals its corresponding CLF count. The deterministic
  nearest-position control and common `run_arm` path make the pinned comparison fair on column mass.
- “Budget-matched” is an at-most-budget clip, not an exact cost match: the clipped arm retains only 625 columns total,
  0.671x the finder's 932, because it does not fill unused budget when selected mass is insufficient and can lose more
  mass during clamping. Calling 29/37 a conservative bound is fair; calling it an equal-budget estimate would not be.

The numerical results and the main 0.91x column comparison are therefore confirmed. The lineage, author-disjointness,
safety, and sealing qualifications are not cosmetic: two are direct contradictions of central claim language.

## Taxonomy-drop ruling

For a **generic** rule/fact/none classifier intended to recognize ordinary formatting preferences, Opus's narrower
policy is the right primary policy: remove exact benchmark items and distinctive near-item templates, but retain
ordinary concepts such as concise replies, bullets, headings, casing, and sentence limits. Sol's 344-key policy removes
large parts of the target construct itself. Since Multi-IF tests formatting rules, broad concept deletion creates an
artificial distribution hole and makes the model less generic. It is suitable only as a separately frozen
taxonomy-scrubbed sensitivity arm, not as the sole production dataset.

Neither policy licenses a zero-leakage claim here:

- **Narrow-policy risk:** the data generators/reviewers knew the named benchmark families, and same-taxonomy examples
  can amount to benchmark-aware category adaptation even without item text. It has higher taxonomy-level leakage risk.
- **Broad-policy risk:** it lowers that risk but cannot eliminate it—the final corpus still contains clear word-count,
  sentence-count, bullet-count, forbidden-word, and casing analogues, including context rows not exhaustively removed.
  It also sacrifices construct validity and invites later leakage if missing categories are restored after observing
  benchmark failures.

The model card must therefore say: benchmark **item/text** disjointness is the intended policy, not taxonomy
disjointness; the generator prompts named public benchmark families as exclusions; Sol removed 344 broad taxonomy or
benchmark-like keys while Opus removed 11 distinctive near phrasings; generic formatting-rule analogues remain; no
evaluation-directory read was found in the code path and the authors attest to none, but semantic no-contact is not
provable from the artifacts; b3 feedback directly shaped enrichment; and the current held-out authors also supplied
training rows. A truly no-contact claim belongs to the separately registered family produced by blinded authors/models.

## Required registration before Multi-IF 909 and BFCL

1. **Freeze identity and lineage.** Commit and hash the exact checkpoint, canonical full training/held-out rows
   (including labels, roles, context and source), patches, generator prompts, encoder model revision, tokenizer,
   splitter, training command/seeds, classifier code, finder code, harness, evaluator and benchmark versions. Record a
   contact log and the exact fit-on/evaluated-on disjointness statement. State the b3 development contact and the chosen
   taxonomy policy. No changes after first access to Multi-IF/BFCL responses.
2. **Freeze threshold and selection rule.** Choose one threshold by a stated objective on a genuinely author-disjoint,
   benchmark-disjoint validation set; freeze it before evaluation. Specify `P(rule)+P(fact)`, role coverage, sentence
   splitting, overlap merging, probability ties, clamping and partial-span behavior. Do not choose between 0.5/0.65
   from b3 or target-benchmark results.
3. **Freeze arms and primary contrasts.** At minimum: full context; evicted/no-memory; finder pinned; finder
   pinned+echo; classifier pinned; classifier pinned+echo; post-clamp exact-column classifier control; and an
   exact-cost pin+echo control if echo is confirmatory. Designate one primary arm/contrast and endpoint per benchmark;
   treat the remainder as secondary or apply a predeclared multiplicity hierarchy.
4. **Freeze controls.** Controls must exclude selected columns, be constructed after every feasibility clamp, match
   unique column count per item exactly with deterministic tie-breaking/seed, and use the same eviction and generation
   path. An echo control must additionally match echoed token count, placement and rendering so semantic content—not
   extra context length—is the changing factor.
5. **Freeze budgets.** Use the same predeclared exact per-item column budget (or a fixed budget grid with a declared
   area-under-cost endpoint) for finder and classifier. State whether echo tokens count separately and how an arm fills
   budget when it selects too little. Do not label an at-most cap such as current CLFB as exact budget matching.
6. **Freeze scoring and safety.** Define the paired experimental unit, all 909 Multi-IF items and exact BFCL slice,
   prompt/order/seeds, maximum output, deadlines, invalid-output handling and missing-data rule. Register primary task
   metrics plus truncation, timeout, invalid tool/schema output, repetition/degeneracy, and echo-quoting rates with
   denominators. Register non-inferiority limits versus full/evicted, a scaled stopping rule, and count every invalid or
   timed-out output as a failure; no rescue reruns.
7. **Freeze reporting.** Report raw paired rows, per-arm cost, exact safety counts, confidence intervals, all exclusions,
   and both aggregate and relevant BFCL/Multi-IF strata. Preserve a separately preregistered no-contact family for any
   zero-shot/generalization claim.

The efficacy arithmetic is sound, but the composite claim includes a false b3 no-contact assertion, a false
author-disjoint assertion, and an overbroad exact-zero safety assertion. Those defects change what the result means.

VERDICT: REFUTED
