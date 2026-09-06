# FOCUS-3 gate v3 — one-round diagnosis of the CPU pre-gate stop (fable, 2026-09-06)

Scope: commit `3e8f8f14` (INELIGIBLE-ADMISSION). Read: v3 RESULTS.md, audits,
all 96 setup records, `src/stencil/focus3.py`, `scripts/train_relations.py`,
`data/classifier/model/relations/*` (thresholds, manifest, heldout2-records),
`data/classifier/LABELS-RELATIONS.md`, and the training jsonl field values.
CPU only; the relations bge-small encoder + head were loaded once to rescore
the 12 gold-positive setup pairs (and, for one diagnostic sweep, all 240 setup
pairs). No repo edits besides this file; no sealed benchmark file opened;
nothing fit, tuned or selected. Scratch scripts live in the session scratchpad.

## Verdict in one paragraph

The relation misses are **not** a bug in the rendering *code*: `focus3.pair_input`
and `train_relations.render_pair` produce byte-identical strings (asserted on all
12 pairs; recorded probabilities reproduce through the trainer's encoder path).
The bug is in the **field values the runtime feeds into that renderer**: status
`active` (training vocabulary: `live`), scope `task` / `user-global` (training:
`task:<name>` / `global`), a `[metadata]` block with `version` and `task_id`
(training: `{"key": ...}` only), an opaque key `new:0:90` (training: semantic
keys), and a `[prev_user]` that is the whole previous message (training: 3.7 %
of rows, one short sentence). On top of that the bank's messages are ~3x longer
than any training message because every sentence is followed by the sort request.
Restoring the training vocabulary alone moves supersedes from P 0.02–0.12 to
0.07–0.92; also dropping `prev_user` gives 5/12 at the frozen thresholds; also
scoring the sentence alone as the message gives 9/12 (supersedes 3/4, cancels
3/4, completes 3/4). Three misses remain that are phrasing, not rendering.
Two further frozen-constant defects would still block v4 even with perfect
rendering: the `P(none) >= 0.98` none-pair guard is unreachable (0/151 gold-none
held-out-2 rows and 0/228 setup none pairs under any rendering reach it), and the
`positive[0]` target choice retires the wrong row when a span fires on two targets.

## 1. Runtime vs trainer rendering, field by field

Renderer text is identical in both code paths:
`[target] <status> <scope> <text> [metadata] {json}` ||
`[message] <role>: <message> [span] <span> [prev_user] <prev>`.
What differs is every value slot (training distribution from the four manifest
input files, 6,028 pair rows; held-out-2, 357 rows):

| slot | training / held-out-2 values | runtime v3 value (`Runtime.update`) |
|---|---|---|
| status | `live` 4992, `cancelled` 567, `completed` 272, `superseded` 197 | `active` for live (never seen in training); retired statuses passed through |
| scope | `task:<name>` 3625, `global` 2362, `reply` 41 | `task` (no name) / `user-global` (never seen) |
| metadata | `{"key": <semantic>}` on 6028/6028; no `version`, no `task_id` | `{"key": "new:0:90", "task_id": "S0n0A", "version": 1}` |
| prev_user | present on 400/10724 rows (3.7 %), one sentence, median 49 chars, max 102 | always the whole previous message, 283–311 chars, containing a hard-none decoy quote and a JSON sort request |
| message | median 78 chars, p90 103, max 193; span == message on 49 % | 242–279 chars: instruction sentence + "Sort request for task ...; reply as compact JSON ..." |
| pair length | held-out-2: no overflow, short | 129–309 tokens (median 254) |

Example, gold `cancels` (setup_1_00_C_2), runtime segment A actually scored:
`[target] active task For task S1n0A, always sort the payload in ascending order. [metadata] {"key": "new:0:90", "task_id": "S1n0A", "version": 1}`
vs. the nearest training-shaped form:
`[target] live task:S1n0A For task S1n0A, always sort the payload in ascending order. [metadata] {"key": "sort-order"}`.

The target rule text and the candidate span are correct: every gold pair's
`old_rule.text` is the admitted sentence and `target_span.text` is the gold
event span (sentence splitter output), so span/target selection is not the
problem.

## 2. Offline rescoring of the 12 gold-positive pairs (trainer encoder path, CPU)

Decision = frozen thresholds (.94/.50/.50/.50, argmax). Variants are cumulative
V1 -> V5; V6/V7 isolate one factor from the runtime form.

| pair (gold) | V0 runtime as-is | V1 status/scope fixed | V3 +key-only meta (semantic) | V4 +no prev_user | V5 +message = span | V6 runtime, no prev only | V7 runtime, span-msg only |
|---|---|---|---|---|---|---|---|
| 0_00 supersedes | .068 none | .736 | .907 | **.957 S** | **.970 S** | .210 | .090 |
| 0_01 supersedes | .022 none | .073 | .355 | .292 | .888 (<.94) | .030 | .022 |
| 0_02 supersedes | .033 none | .250 | .674 | .823 | **.947 S** | .055 | .024 |
| 0_03 supersedes | .121 none | .879 | .919 | **.955 S** | **.969 S** | .294 | .129 |
| 1_00 cancels | .033 none | .084 | .025 | **.685 C** | **.976 C** | .249 | .193 (reinst .737) |
| 1_01 cancels | .080 reinstates(.593) | **.651 C** | .194 | **.960 C** | **.976 C** | **.545 C** | .447 |
| 1_02 cancels | .006 none | .005 | .006 | .009 | .038 | .010 | .011 (reinst .501) |
| 1_03 cancels | .017 none | .044 | .012 | **.749 C** | **.971 C** | .247 | .069 (reinst .728) |
| 2_00 completes | .025 none | .014 | .011 | .424 | **.975 Cm** | .078 | **.523 Cm** |
| 2_01 completes | .019 none | .011 | .008 | .157 | **.976 Cm** | .028 | .127 |
| 2_02 completes | .017 none | .012 | .008 | .161 | **.974 Cm** | .034 | .381 |
| 2_03 completes | .013 none | .008 | .008 | .008 | .150 | .011 | .029 |
| correct / 12 | 0 | 1 | 0 | 5 | 9 | 1 | 1 |

Readings:
- V0 reproduces the recorded probabilities exactly, so the encoder/head path in
  `FrozenClassifier.infer` equals the trainer's (`evaluate_frozen`); no
  tokenizer/role/head discrepancy.
- Status/scope vocabulary is the largest single lever for `supersedes`
  (0.07 -> 0.74/0.88 on two pairs from one change). Metadata shape and key
  semantics matter less (V1 -> V2 -> V3 moves a few points either way).
- `prev_user` as a whole message is the largest lever for `cancels`; the runtime
  `reinstates` proposals (0.45–0.59 on cancel pairs) come from that context,
  which quotes a decoy instruction sentence.
- Message length is the decisive lever for `completes`: with the sort request
  appended, completes never exceeds 0.42 even with everything else fixed; with
  the sentence alone it is 0.97 on 3/4 (the held-out-2 completes rows that
  scored 100 % are single 1–2 sentence messages, e.g. "The aging log for the
  winter batch is closed out, all wheels are sold.").
- Three misses survive the best rendering and are phrasing outside the fit
  distribution, not rendering: "The sorting rule for task S1n2A no longer
  applies." (cancels .038), "That concludes task S2n3A." (completes .150),
  "Replace the sorting rule for task S0n1A: always use ascending order."
  (supersedes .888 under a .94 cutoff).

## 3. Two frozen-constant defects independent of rendering

1. **The `P(none) >= 0.98` none-pair guard is unreachable.** It is required for
   any admission when a live row exists (`confident_none` in `Runtime.update`).
   On held-out-2 the frozen scorer's gold-none rows have median P(none) 0.927 and
   0/151 reach 0.98; on setup, 0/228 gold-none pairs reach it under the runtime
   rendering and 0/228 under either faithful rendering. Consequence: after the
   first two admissions no standing rule can ever be admitted — the four
   switched-task ordering rules (P(rule) .955–.977) were blocked by this alone
   ("new task's standing rule on switch 0/4"). This value was never calibrated
   (thresholds.json calibrates only the four positive classes); the 0.98 appears
   to be inherited from the historical `predict()` floor.
2. **`positive[0]` target choice.** Under the faithful span-only rendering three
   cancel spans and two override spans also fire on the *global tag* rule
   (e.g. "Drop the ordering requirement for task S1n1A." -> cancels 0.967 against
   "keep tag equal to 35"). The register orders the tag row first, so with two
   positives the runtime would cancel the tag rule and leave the ordering rule
   live — a false retirement. The classifier does not honour the key field;
   the runtime must (choose the highest-probability target, or restrict to
   same-kind rows via `kind_of`).
   Also observed: a switched-task standing rule scored supersedes 0.954 against
   the *previous* task's rule (wrong-task, spec says none); the scope check
   correctly refuses it but then the span is never admitted (positive non-empty).

## 4. Did the pre-gate stop behave correctly?

Yes. The frozen stop required every gold cancellation/completion (8) to retire
its actual source row and every replacement/new-task admission to apply; it
observed 0/8 and 0/8 and stopped before any GPU claim (0/10800 s), retained all
96 records with probabilities and model inputs, and the independent audit
reproduced probabilities from logits. The stop did what it was registered to do.
What it did not do: it reported event counts, not a transition-recall table, so
the diagnosis above required re-deriving the pair confusion from the records;
and it had no rendering-parity check, which is why an out-of-vocabulary status
string reached the sealed run. The v2->v3 fix concentrated on admission
(segment A of the ft head) and never verified the relation inputs.

## 5. What v4 must change (registration items)

1. **Vocabulary parity in `Runtime.update`** (`src/stencil/focus3.py` ~l.239):
   `status=rule.status` (register already uses live/cancelled/completed/superseded);
   `scope="global" if rule.scope == "*" else f"task:{rule.scope}"`; metadata
   `{"key": ...}` only (drop `version`, `task_id`); use a descriptive key
   (`kind_of` -> e.g. `sort-order` / `tag`) rather than `new:<turn>:<start>`.
2. **`prev_user`**: pass `None`, or at most the single last previous user
   sentence; never the whole previous message. Register this choice before the
   run; both readings above are reported so the choice is not score-selected.
3. **Message field**: register whether the relation `message` is the full
   message or the classified sentence. The full-message form is the spec's
   ("include the whole new message") but the v3 bank glues a 150-char sort
   request to every sentence, which is outside the fit distribution and is the
   single cause of all four completes misses. Prefer: message = the user
   message with the sort-request sentence removed (prose part only), which is
   spec-conformant and bank-independent; report the span-only form beside it.
4. **CPU parity unit test** (tests/test_focus3_gate_v3.py): build one register
   with a live global rule and a live task rule, run `Runtime.update` with a
   stub classifier that captures `pair_input` rows, and assert (a)
   `pair_input(row) == train_relations.render_pair(train_relations.normalize_row(row))`
   and (b) every `old_rule.status`/`scope` value is in the set observed in the
   training jsonl (`live|cancelled|completed|superseded`, `global|task:<name>`),
   metadata keys == {"key"}, and `prev_user` length <= one sentence. Assert on
   values, not on the renderer function.
5. **Stop that reports transition recall**: the setup stop must print and save,
   per label, gold count / proposed / applied, plus the none-pair confusion and
   the P(none) quantiles on gold-none pairs and on gold-admit spans. Keep the
   existing eligibility rule; add the table so a miss is diagnosable in-run.
6. **Replace the 0.98 none-pair guard** with a registered, DEV-calibrated
   constant (same rule family as thresholds.json: the lowest cutoff with at most
   5 % positive-miss on DEV gold-positive rows) or with "no positive proposed
   on any pair for this span" (which is what the rows already guarantee).
   Record it in the v4 pre-written reading; do not pick it after seeing setup.
7. **Target selection with multiple positives**: apply to the highest-probability
   target among same-kind rows; retire nothing when two different-kind rows tie.
   Add a unit test with the tag+ordering register above.
8. **Bank phrasing**: do not edit the three missed phrasings after seeing scores
   (that is outcome-based selection on the evaluation bank). Either accept them
   as classifier misses in the v4 reading or add fresh cancellation/completion
   phrasings to the *training* pool through the classifier data process before
   any retrain; write the data-lineage line either way.

## 6. Evidence pointers

- Records: `results/quick-checks/focus3-gate/v3/setup-admission/records/setup_{0,1,2}_0{0..3}_C_2.json` (the 12 gold pairs; `trace.pairs[*].model_input` shows the exact strings).
- Rendering code: `src/stencil/focus3.py` `Runtime.update` (status/scope mapping, `prev_user=self.previous`), `pair_input`; `scripts/train_relations.py` `render_pair`, `normalize_row`.
- Guard: `src/stencil/focus3.py` `confident_none = all(p["probabilities"][0] >= 0.98 ...)`.
- Training vocabulary: manifest `data_audit.input_sha256` files under `data/classifier/relations/` and `data/classifier/review/relations-merged-patch.jsonl`; held-out-2 probabilities `data/classifier/model/relations/heldout2-records.jsonl`.
