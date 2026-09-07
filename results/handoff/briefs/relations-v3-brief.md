# Relations refit v3 for gpt-6-astra: SUPERSEDES recall via the audited override-idiom pass (2026-09-06)

Source: results/relations-classifier-report.md (v2 refit: held-out-2 96.1% once; runtime 11/12 transitions; the
runtime's weak spot is supersedes recall on override idioms). New data: data/classifier/relations/kimi-overrides.jsonl
(1,234 rows) audited by Opus — apply data/classifier/review/overrides-opus-patch.jsonl and read
data/classifier/review/overrides-opus-audit.md (systematic errors: target_span end wrong on 1,031 rows and start on 53
— recompute offsets mechanically from target_span.text against message and drop rows whose text is not verbatim;
1,117 rows use the whole message as the span; new_rule_spans shapes vary — normalise; ids absent — assign
scenario ids by source+index; the audit's flagged paraphrase families are development-only: keep them OUT of DEV
calibration).
Task:
- Fit-on = the v2 fit corpus (kimi-relations + transitions + enrich sets with their merged patches, exactly as v2) +
  the patched, offset-corrected kimi-overrides. Same recipe/hyperparameters as relations-v2 (cite its README); seeds
  0/1/2; scenario-disjoint DEV; GPU minutes only (verify idle; RUNNING.flag; never signal). Write the data-lineage
  line first.
- Calibrate thresholds on DEV only (as v2). Register checkpoint hashes, policy and evaluator in a commit BEFORE any
  held-out look.
- EVALUATE ONCE on data/classifier/heldout/fable-relations-heldout-3.jsonl (fresh; poll for the committed file; never
  fit or select on it). Report accuracy, per-label P/R/F1, confusion matrix, supersedes recall with Clopper-Pearson
  bounds, and — secondary, disclosed second look — held-out-2 for regression. Also rerun the FOCUS-3 runtime
  transition diagnostic (the 12-transition set used for v2) with v3 swapped in; report the count and any regressions.
- Pre-written reading: GO = held-out-3 supersedes recall >= 90% with overall accuracy >= 94% and no per-label F1
  below v2's held-out-2 value by more than 3 points -> register relations-v3 as the runtime relation model (manifest
  hashes; safetensors out of git). Else NO-GO with the failing number; v2 stays.
Cap 30 GPU-minutes. Outputs: model under data/classifier/model/relations-v3/ (README with hashes, DEV records,
heldout3-records.jsonl); dated section in results/relations-classifier-report.md; WORKLOG entry (<= 6 lines). Commit
with explicit pathspecs; no push. Foreground only; never terminate or signal any process; never read anything under
data/bench.
