# FOCUS-3 gate v4 — one-round review of the CPU pre-gate stop (fable, 2026-09-06)

Scope: commit `a8b7e2bf` (v4 INELIGIBLE-ADMISSION after freeze `c72a4d3d`). Read:
v4 RESULTS.md, calibration.json, independent-audit.json, setup-admission/summary.json
and the 96 setup records, `src/stencil/focus3.py`, `src/stencil/relation_operating_point.py`,
`scripts/train_relations.py`, `data/classifier/LABELS-RELATIONS.md`, the fit/enrich jsonl
inputs, `data/classifier/relations/astra-enrich-2.jsonl`, `heldout2-records.jsonl`, and my
v3 review. CPU only. The bge classifier was NOT reloaded: every probability below is read
from the committed records or recomputed from the committed DEV logits
(`calibration/gpu-seed0-dev.npz`, sha `cc9fc611…`, 576 rows: 259 none / 106 supersedes /
72 cancels / 70 completes / 69 reinstates, 0 overflow). Nothing was fit, tuned or
selected; the sweeps below are descriptive. No sealed benchmark file was opened.
Caveat: I tried to rebuild the DEV row list through the trainer's `split_development` to
characterise individual DEV rows; the rebuilt split has identical label counts but a
different digest, so no row-level DEV wording is cited here.

## Verdict in one paragraph

The stop behaved as registered and the parity work from v3 is confirmed by the records
(all 12 gold pairs now score on training-vocabulary values; recorded probabilities match
the runtime audit). The four switched-task standing rules were **not** blocked by the
admission head (P(rule) .958–.977, all >= .95) and not by segmentation (each rule is its own
span). Two were blocked by the registered none-pair guard alone; two were blocked one step
earlier because the classifier proposed `supersedes` (.95/.94) against the *previous*
task's rule and the runtime's scope check turns a wrong-task positive into "skip this span"
instead of "this pair is none". The guard as registered (DEV gold-none **90th** percentile)
is a cutoff that only 10% of gold-none pairs can pass by construction, so requiring every
pair on a span to pass it is a near-certain veto whenever any live row exists; the v3
recommendation was the opposite quantile (a positive-miss bound). The supersedes
threshold .94 is the correct output of the registered rule, but the rule's objective
(none-FP <= 5% per class on a hard-negative-heavy DEV) is not the objective the gate needs
now; lowering it is a legitimate registered change but buys only 1 of the 4 transition
misses (.727), and the remaining three are genuine phrasing limits of the frozen model.
The enrichment file is not clean as it stands (3 verbatim bank sentences with bank task
names, one target sentence reused 90 times, a bank-mirroring domain). Separately, the
setup records show 19 unauthorized applications (18 `reinstates` on plain
continuation/return sentences, P .54–.97) in 8/16 episodes; these were outside the stop
criteria but would fail the v3 gate readings (false retirement/unauthorized update <= 2/64)
on their own, so a v5 that fixes only transitions and admission would still burn the GPU
budget.

## 1. Why the four switched-task standing rules were not admitted

Per-span evidence from `setup-admission/records/setup_3_0{0..3}_C_2.json` (the register
holds the global tag rule and the previous task's ordering rule when the new task's rule
arrives):

| episode | span | P(rule) admission | pair vs global tag rule: P(none)/P(sup) | pair vs task-A ordering rule: P(none)/P(sup) | proposed positive? | blocking cause |
|---|---|---:|---:|---:|---|---|
| setup_3_00 | "Going forward, keep every payload for task S3n0B in descending order." | .9773 | .116 / .870 | .808 / .020 (reinst .158) | no | none guard (both pairs < .9712) |
| setup_3_01 | "Each time you handle a payload for task S3n1B, sort it in descending order." | .9607 | .511 / .471 | .351 / .630 | no (sup .630 < .94) | none guard |
| setup_3_02 | "Use descending order for all payloads in task S3n2B from now on." | .9582 | .057 / .930 | .034 / **.9525** | **yes**, supersedes vs task S3n2A | wrong-task positive -> scope check `continue`, admission never evaluated |
| setup_3_03 | "From now on, for task S3n3B keep the payload sorted in descending order." | .9772 | .049 / .936 | .044 / **.9418** | **yes**, supersedes vs task S3n3A | same as above |

So: admission threshold .95 on P(rule) — **passed 4/4**. Segmentation — not a factor
(the rule sentence is one span; the "Switch to/Work on task" sentence and the sort request
are separate spans). None guard at .9712 — **blocks 4/4** (max P(none) on these 8 pairs is
.808; median .086). Additionally, in 2/4 the positive list is non-empty (wrong-task
supersedes >= .94), and `Runtime.update` hits `if scope is None or not overlaps(old.scope,
scope): continue` (focus3.py ~l.341), which skips the whole span; the admission branch is
never reached for that span.

Three separate defects, in order of weight:

1. **The guard quantile is inverted relative to its purpose.** calibration.json: 26/259
   DEV gold-none rows meet the cutoff — i.e. the registered rule admits a gold-none pair
   10% of the time. On held-out-2 it is 8/151; on the setup bank 0/189. The v3 note
   asked for "the lowest cutoff with at most 5% positive-miss on DEV gold-positive rows",
   which is the *positive* distribution's high quantile (DEV positives: 95th pct of
   P(none) = .2046, 90th = .0434). On DEV a cutoff of .5 passes 217/259 gold-none and
   5/317 positives; .2046 passes 227/259 and 16/317. The 5%-positive-violation check that
   was registered (0/317 positives >= .9712) is vacuously satisfied by any high cutoff and
   does not constrain the choice.
2. **The classifier reads a new task's ordering rule as superseding the sibling task's
   rule.** P(supersedes) .63–.95 on all four task-A pairs. LABELS-RELATIONS.md line 20
   defines mismatched tasks as `none`, and the fit pool has ~134 wrong-task none rows,
   but those use distinct natural task names ("billing service" vs "gateway"); the bank
   uses names differing in the final letter (S3n2A / S3n2B), and no fit row has
   near-identical names. This is a distribution gap of the bank's own making, not a
   label-spec violation. Note it also means that with *any* none guard these two spans
   still fail unless the runtime handles wrong-task positives.
3. **Runtime handling of a wrong-task positive.** A positive against a non-overlapping
   scope is by spec `none`; the runtime should drop that pair (or, cleaner, not pair a
   task-scoped span with rows of a different task at all, since `scope_of(span)` is
   already computed) and then evaluate admission on the remaining pairs. The current
   `continue` converts a spec-defined none into a silent non-admission.

## 2. Is supersedes = .94 the right runtime operating point?

The .94 is the exact output of `relation_operating_point.select` (grid .50–.98, allowance
floor(.05*259)=12): supersedes none-FP is 25 at .50 and first drops to <= 12 at .94 (11).
The other three classes already satisfy the cap at .50 (FP 6/7/2 <= 12). DEV
sweep from the committed logits (per-class recall on its own support; none-FP over 259
gold-none rows):

| policy | correct-positive recall (317) | total none-FP | supersedes R / FP | cancels R / FP | completes R / FP | reinstates R / FP |
|---|---:|---:|---|---|---|---|
| registered .94/.5/.5/.5 | .921 | 26 (10.0%) | .79 / 11 | .99 / 6 | .99 / 7 | .99 / 2 |
| per-class, none-FP <= 10% (allow 25) -> .5/.5/.5/.5 | .972 | 40 (15.4%) | .94 / 25 | .99 / 6 | .99 / 7 | .99 / 2 |
| supersedes .90, others .5 | .934 | 29 (11.2%) | .83 / 14 | same | same | same |
| supersedes .80 | .946 | 33 (12.7%) | .87 / 18 | | | |
| supersedes .72 | .953 | 37 (14.3%) | .89 / 22 | | | |
| supersedes .70 | .956 | 37 (14.3%) | .90 / 22 | | | |
| plain argmax | .972 | 41 (15.8%) | .94 / 26 | .99 / 6 | .99 / 7 | .99 / 2 |
| argmax with margin >= .2 | .962 | 38 (14.7%) | .92 / 24 | .99 / 6 | .99 / 7 | .99 / 1 |
| argmax with margin >= .5 | .943 | 34 (13.1%) | .89 / 21 | .97 / 5 | .97 / 7 | .97 / 1 |

Readings:
- Every alternative buys supersedes recall almost entirely at the cost of
  supersedes-vs-none FP; the other three classes are unaffected. The supersedes/none
  axis is where this model is structurally weakest (25 of the 41 argmax none-FPs go to
  supersedes; DEV nones are hard-negative-heavy by spec, LABELS line 56).
- On the v4 setup itself, lowering supersedes to .70–.72 recovers exactly one miss
  (S0n2A "switch the standing order", .727) and leaves the .702 miss at the margin; it
  would also have turned setup_3_02/3_03's wrong-task pairs (.95/.94) and setup_3_00's
  tag-rule pair (.870) into positives more often, so it *must* be paired with the
  wrong-task handling in section 1.
- Held-out-2 (read-only, 68 supersedes / 151 none; reported as a check, not used for
  selection): .94 -> 59/68, FP 2/151; .90 -> 64/68, 2/151; .80 -> 66/68, 3/151;
  .70 -> 66/68, 4/151; .50 -> 67/68, 7/151. Held-out nones are less adversarial than
  DEV nones, so DEV FP rates are the conservative bound.
- The "none-FP <= 10% per class" rule as literally registered would pick .50 for
  supersedes (FP 25 <= allowance 25, a boundary hit) — that is effectively plain argmax
  with total DEV none-FP 15.4%. If the intent is "recall matters more now", say that as a
  rule: e.g. per-class none-FP <= 8% (allowance 20) gives supersedes .76 (FP 20, recall
  93/106 = .88); <= 7% (18) gives .78 (FP 18, recall .88); <= 6% (15) gives .90 (FP 14,
  recall .83). Any of these is a registrable alternative; each should be recorded with
  its DEV table before the bank is rescored.
- Margin policies are dominated by per-class thresholds here (same FP for lower
  recall), so I would not register a margin rule.

Recommendation: keep the per-class family, register the relaxed cap (8% is the smallest
step that moves the supersedes cutoff below the two observed misses' neighbourhood only
if you accept .76; .727 needs <= 9% -> .72 with FP 22), and register it *together* with
the wrong-task pair exclusion, because the FP mass that the cap is buying is exactly the
kind the bank's sibling-task pairs produce.

## 3. The three phrasing misses

Frozen probabilities under the v4 rendering (independent-audit.json):
"Replace the sorting rule for task S0n1A: always use ascending order." supersedes .702;
"The sorting rule for task S1n2A no longer applies." cancels .016;
"That concludes task S2n3A." completes .034.

Are they in-distribution for LABELS-RELATIONS.md? Yes on the label definitions: explicit
replacement of the same key in the same task (l.23), explicit withdrawal without
replacement (l.26), explicit closure of the whole named task (l.29). They are not
excluded by any hard-case rule (not a sub-unit, not quoted, not a task switch). The fit
pool coverage of the idioms (kimi + astra + opus inputs, 6,028 rows):
"no longer" 18 rows (8 cancels, 8 none, 1 supersedes, 1 completes); "conclud*" 4 rows
(3 completes); "replace" 13 rows (3 supersedes, 9 none); "switch the" 49 rows (41
supersedes); "standing" 5 rows (all none). So "no longer applies" and "that concludes"
are thin and label-ambiguous in the pool, and "standing" appears only as a none cue —
which is consistent with the .727 on "switch the standing order". These are legitimate
limits of the frozen classifier, not rendering or runtime bugs.

Is `astra-enrich-2.jsonl` a clean fix? As committed, **no**, on three counts:
1. It contains the three bank sentences verbatim, with the bank's task identifiers
   (S1n2A, S2n3A, S0n1A) and the bank's exact target rule text. Fitting on them is
   fitting on the evaluation bank; they must be deleted, not just flagged.
2. The 90 paraphrases all share one target sentence ("Always sort payloads in ascending
   order for task Cedar.") and one domain (`synthetic-sorting`), i.e. one scenario per
   label rendered 30 ways. That is idiom enrichment of the gate's own domain and rule
   shape, not of the label. Under the 2026-09-03 rule (no probe/benchmark specifics in
   generation prompts) the honest version is: hand-write the *idioms* — "X no longer
   applies", "that concludes X", "replace the X rule: …", "switch the standing X" — across
   diverse domains and rule keys through the classifier data process, without the bank
   in view, and cap sort-order rows to the pool's existing domain share.
3. Even the clean version changes what the gate measures. The gate bank is a development
   bank, so enrichment does not contaminate held-out-2 (I verified zero overlap of the 93
   messages with heldout2-records) — but after enrichment a v5 gate pass no longer
   demonstrates that the classifier generalises to unseen phrasings; it demonstrates that
   the runtime works when the classifier has seen the idioms. That is acceptable for a
   development gate if the reading says so in its data-lineage line and the claim is
   narrowed accordingly ("gate phrasings' idioms were in the fit pool from v5 on").
   A later independent-author gate bank is the only way to get the stronger claim back.

## 4. The v5 plan

"Refit with enrichment + re-chosen thresholds on DEV, then rerun setup stop and gate" is
the right shape but is not minimal-and-honest as stated, for two reasons.

(a) It does not touch the two runtime defects that are independent of the classifier and
    that the v4 records make visible: the inverted none guard and wrong-task positive
    handling (section 1). A refit alone will not admit switched-task rules: the clean-guard
    fix is a one-line quantile change and the wrong-task exclusion is a pairing/filter
    change, both registrable now and testable on the existing v4 records (a replay with
    the frozen model would show the expected 4/4 admissions without any GPU).
(b) It does not address the 19 unauthorized applications. 18 are `reinstates` fired on
    "Continue task X;" / "Work on task X;" / "Return to task X;" / "Reply exactly calm."
    against retired rows (P .54–.97, 10 of 18 >= .90), 3 of them cross-task
    (S2n0B continuation reinstating S2n0A's completed rule). LABELS l.32/42 make
    continuation and task return `none`. This is a classifier error the fit pool should
    address (continuation-after-retirement hard negatives, which exist for live targets but
    apparently not for retired ones), and a runtime guard is also defensible by spec:
    `reinstates` requires an explicit restoring instruction, so the runtime may refuse
    reinstatement from a span that has no rule-like content (admission P(rule) < .95 on
    that span is a registrable proxy; every one of the 18 spans is a bare continuation).
    The 19th is a cancels (.60) on the quoted inert line in setup_3_00; quoted-inert
    negatives exist in the pool (LABELS l.22) and this one is marginal at .50.
    Without (b), the gate's own readings (false retirement <= 2/64, no contradictory
    recaps) fail in 8/16 setup-shaped episodes before any generation happens.

Minimal honest v5, in order:
1. Register (in the v5 pre-written reading, before any refit or rescoring):
   - none guard = the *positive*-side rule: cutoff = max P(none) among DEV gold-positive
     rows at the 95th percentile (currently .2046) or a fixed .5, with the DEV pass rates
     for gold-none and positives recorded; drop the 90th/95th none-quantile rule.
   - pairs are formed only with rows whose scope overlaps `scope_of(span)` (global rows
     always; task rows only for the same task); a positive against any other row is
     impossible by spec and is not scored. Record that this changes the pair count.
   - `reinstates` applies only from a span whose admission P(rule) >= .95 (or, if you
     prefer no new coupling, only when the same span is not a bare task-switch/continuation
     sentence per `selected_task`), with the rule stated before rescoring.
   - operating-point rule change: per-class none-FP cap value (5% -> 8/9/10%) chosen and
     justified once; the DEV table from section 2 attached; held-out-2 numbers quoted as a
     check only.
   - stop criteria for the setup replay: existing 36/36 admissions and >= 11/12
     transitions, plus **unauthorized applications == 0 across all 96 records** (the v4
     stop measured 19 and did not count them).
2. Replay v4's frozen model on the setup bank with the registered runtime changes (CPU,
   minutes). Expected from the records: admissions 36/36 (the four spans have no
   overlapping-scope positive and P(rule) >= .95), transitions 8/12 (9/12 if the
   supersedes cap moves below .727), reinstates 0. If that replay does not meet the
   admission and zero-false-application criteria, the plan's classifier assumptions are
   wrong and the refit is premature.
3. Data: delete the three verbatim rows from astra-enrich-2; rebuild the enrichment as
   idiom-diverse, multi-domain rows through the classifier data process (kimi authoring,
   sol/Opus review), including continuation-after-retirement and sibling-named-task none
   rows; write the data-lineage line (fit-on = pool + idiom enrichment authored without
   the bank; calibrated-on = fresh scenario-disjoint DEV; evaluated-on = development gate
   bank v4 wordings whose idioms are now represented in fit; held-out-2 untouched and no
   longer needed for this claim).
4. Refit (GPU), calibrate thresholds under the registered cap on the new DEV, freeze
   hashes, run the setup stop, then the 64-episode gate under the unchanged v3 readings.
5. State the narrowed claim in the v5 reading: a pass shows runtime + classifier agreement
   on a development bank whose idioms were enriched into fit, not generalisation to novel
   phrasings.

## Evidence pointers

- Switched-task spans: `results/quick-checks/focus3-gate/v4/setup-admission/records/setup_3_0{0,1,2,3}_C_2.json` (`trace.admissions[*].probabilities[1]`, `trace.pairs[*].probabilities`).
- Guard and scope `continue`: `src/stencil/focus3.py` `NONE_PAIR_THRESHOLD` (l.22), `Runtime.update` (l.341 scope check, l.374–382 `confident_none`/`accept`).
- Threshold rule: `src/stencil/relation_operating_point.py` (`RULE`, `select`); `data/classifier/model/relations/thresholds.json`.
- DEV logits: `data/classifier/model/relations/calibration/gpu-seed0-dev.npz`; calibration record `results/quick-checks/focus3-gate/v4/calibration.json`.
- False applications: `results/quick-checks/focus3-gate/v4/independent-audit.json` `false_application_details`; probabilities in the corresponding `setup_*_C_{1,3,4,5}.json` records.
- Enrichment: `data/classifier/relations/astra-enrich-2.jsonl` (93 rows, 3 verbatim bank sentences, single target sentence for the other 90).
- Fit-pool idiom counts: `data/classifier/relations/{kimi-relations,astra-enrich,opus-enrich}.jsonl`.
