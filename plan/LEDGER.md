# Relation classifier task ledger

2026-09-05 — STATE: RECONCILING, before any fitting or held-out read. User's
CPU-only, foreground-only task governs this work. Prior PLAN/PROTOCOL/LEDGER
were moved to archive/; read archived protocol and latest STATE for context.
No wrapper holds .review.lock. WORKLOG.md and unrelated working files untouched.
Data lineage: fit-on = kimi + astra/opus enrichment after merged patch;
calibrated-on = scenario-disjoint 10% development split; evaluated-on = reserved
author-disjoint fable held-out, once for seed 0 after all recipes freeze.
No benchmark or sealed inputs read. Seed 0 is designated in advance; seeds 1/2
are development stability checks, never checkpoint selection. Trainer needs
row-indexed field patch support and separate fit/evaluation modes. A cooperative
CPU-time budget will stop fitting at a batch boundary, without signals. Any
recipe reduction will be recorded before the held-out evaluation.

2026-09-05 — STATE: RECONCILIATION COMPLETE, CPU PILOT NEXT. Kimi retains 5265
rows after 121 union drops; 227 disagreements include implicit original-label
retention by a reviewer who supplied no patch. Decisions and reasons are in
data/classifier/review/relations-disagreements.md and the merged summary.
Unindexed Opus duplicate drops resolve to later matching source rows, requiring
matching original labels; Astra indices are asserted exactly. Additional 60
Astra enrichment inactive-target supersedes labels receive the same none + new
span rule, preserving inputs. V3 resolves narrower global bare suspensions to
none, hedged proposals to none, task completion + global admission separately.
Targeted validation: 28 passed, 1 expected failure; ruff clean. No held-out read.
Pilot command (foreground, no signals): CUDA_VISIBLE_DEVICES='' uv run --no-sync
python scripts/train_relations.py --cpu-smoke --seed 0 --device cpu
--cpu-threads 4 --patch data/classifier/review/relations-merged-patch.jsonl
--enrich data/classifier/relations/astra-enrich.jsonl
data/classifier/relations/opus-enrich.jsonl --output /tmp/relations-cpu-pilot-20260905.
Pilot artifacts carry CPU/wall time; maximum 200 development-source rows, one
epoch, no held-out access. Full seed recipes remain three epochs, with
cooperative fitting stop at 72 CPU-minutes and 18 CPU-minutes reserved for
calibration/save within the user's 90 CPU-minute per-seed cap.

2026-09-05 — STATE: SEED 0 CPU FIT LAUNCH. Pilot completed: 6 updates, 1.263
CPU-minutes, 0.306 wall-minutes (180 fit / 20 dev); zero overflow. Conservative
linear projection for three epochs: 109.2 CPU-minutes / 26.5 wall-minutes per
seed, exceeding the 90 CPU-minute cap. Before any full-run or held-out outcome,
reduce ALL seeds to TWO epochs, retaining 512-token abstention and other
hyperparameters. Projection: 72.8 CPU-minutes / 17.7 wall-minutes per seed,
218.4 CPU-minutes / 53.0 wall-minutes total; cooperative 72-minute fitting cap
still applies. This is resource-based, not score-based selection. Effective
corpus after 143 dedup removals: 5764 pairs (none 2592, supersedes 1060,
cancels 723, completes 704, reinstates 685); every split is 5188 fit / 576 dev.
Run each seed in order 0,1,2, foreground:
CUDA_VISIBLE_DEVICES='' uv run --no-sync python /home/bmarti44/stencil-llm/scripts/train_relations.py --dev-only --seed SEED --epochs 2 --device cpu --cpu-threads 4 --patch /home/bmarti44/stencil-llm/data/classifier/review/relations-merged-patch.jsonl --enrich /home/bmarti44/stencil-llm/data/classifier/relations/astra-enrich.jsonl /home/bmarti44/stencil-llm/data/classifier/relations/opus-enrich.jsonl --output OUTPUT
OUTPUT seed 0 = data/classifier/model/relations; seeds 1/2 =
data/classifier/model/relations-seed1 and relations-seed2. Logs are
results/logs/relations-seedN.log; raw exit status preserved with pipefail.
Seed 0 remains preselected regardless of development stability scores.

2026-09-05 — STATE: SEED 0 FROZEN; SEED 1 FITTING, HELD-OUT UNOPENED. Seed 0
stopped cooperatively after 311/326 planned updates (one complete epoch plus a
partial second): total 73.364 CPU-minutes / 16.282 wall-minutes, within cap.
Dev argmax accuracy 496/576 = 86.11%; all .98 thresholds, operational accuracy
259/576 = 44.97%, zero non-none predictions and 0/259 none-FP. This is abstention,
not useful transition recall. No threshold/recipe rescue or seed selection.
Seed 1 launched with the prewritten command and same cap/recipe; foreground log
results/logs/relations-seed1.log. Evaluation repeat/nonzero-seed guards tested:
28 trainer tests pass; no held-out access in tests. Mechanical audit independently
asserted Astra span text preservation, all patch preimages, exact offsets and
string admission spans. Seed 0 process observed CUDA_VISIBLE_DEVICES empty and
peak resident memory about 3.49 GiB. Partial-epoch printed loss divides by the
whole eligible population; do not use that diagnostic as a processed-row mean.

2026-09-05 — STATE: SEED 1 FROZEN; SEED 2 FITTING, HELD-OUT UNOPENED. Seed 1:
312/326 updates, 73.588 CPU-minutes / 16.254 wall-minutes; dev argmax 504/576
= 87.50%, operational 259/576 = 44.97%, 0/259 none-FP, zero positive predictions.
All four thresholds remain .98. Seed 2 launched with the identical prewritten
recipe; foreground log results/logs/relations-seed2.log. No data, weights or
thresholds changed in response to dev outcomes. After seed 2 freezes, evaluate
the predesignated frozen seed 0 once using --evaluate-only; then finalize report,
metadata/stability summaries, validation and an explicit-pathspec local commit.

2026-09-05 — STATE: ALL SEEDS FROZEN; FINAL HELD-OUT EVALUATION LAUNCH. Seed 2:
312/326 updates, 73.489 CPU-minutes / 16.320 wall-minutes; dev argmax 512/576
= 88.89%, operational 259/576 = 44.97%, zero non-none predictions and 0/259
none-FP. All seeds' artifact hashes verified and evaluation counters are zero.
31 targeted tests pass, one expected failure; lint/whitespace checks pass.
Merged patch and disagreement table reproduce exactly without file writes.
No recipe/data/threshold adjustment from scores. Seed 0 remains predesignated.
ONE foreground final evaluation command:
CUDA_VISIBLE_DEVICES='' uv run --no-sync python /home/bmarti44/stencil-llm/scripts/train_relations.py --evaluate-only --seed 0 --device cpu --cpu-threads 4 --patch /home/bmarti44/stencil-llm/data/classifier/review/relations-merged-patch.jsonl --enrich /home/bmarti44/stencil-llm/data/classifier/relations/astra-enrich.jsonl /home/bmarti44/stencil-llm/data/classifier/relations/opus-enrich.jsonl --output /home/bmarti44/stencil-llm/data/classifier/model/relations
Log: results/logs/relations-heldout.log. The trainer marks evaluation started
before opening Fable; repeated evaluation is refused. Score frozen labels as
provided; never return held-out results to fitting, calibration or selection.

2026-09-05 — STATE: EVALUATION PREFLIGHT ABORTED BEFORE INFERENCE. Exact failure:
assert_heldout_disjoint rejected one shared message token, “Undo that.”; no
shared declared scenario/relative IDs and zero shared old-rule/message pair
fingerprints. The held-out target is plant naming; development targets differ.
This is common utterance text, not a shared authored scenario. No held-out
logits, predictions or scores exist. Inspection was identity-only after all
three checkpoints froze; no labels/scores informed fitting or selection.
Preserve the fitting source in a local commit, then repair only evaluation
identity validation: require disjoint authors, declared families/relatives and
pair fingerprints; record message-only collisions rather than conflating
independently authored targets. Resume this unscored evaluation through an
explicit preflight-resume receipt, retaining the evaluation counter of one and
recording two preflight attempts. No data row, split, weight or threshold changes.

2026-09-05 — STATE: FINAL EVALUATION COMPLETE; REPORT/METADATA READY TO COMMIT.
A second preflight aborted before inference: two coarse old-rule/message keys
had different prior-user contexts and thus different full model inputs. Fixed
evaluation-only dedup to use render_pair; all 594 pairs retained with original
labels. Training functions verified AST-identical to commit 10c2d39. One metadata
header excluded separately (595 JSONL records / 594 pair rows / 0 admission-only).
Both aborted preflights and source hashes remain in manifest receipts. The third
preflight succeeded: exactly ONE inference pass, evaluation counter 1, inference
counter 1, 1.163 CPU-minutes. Seed 0 held-out argmax 482/594 = 81.14%; registered
.98 operating accuracy 255/594 = 42.93%, zero positive predictions/recall,
0/255 none-FP, 0/234 hard-negative FP, zero overflow. Argmax none-FP 84/255.
No held-out scores informed training, calibration, checkpoint selection or repairs;
all repairs preceded the first inference and affected identity preflight only.
Report is 50 lines and says NOT READY for the register; the 64-episode gate and
admission are untested. Metadata includes all dev stability measurements, source,
data/checkpoint hashes, effective label/scope/admission counts and full metrics.
Final local commit will include metadata/report/evaluation repair with explicit
pathspecs; safetensors and raw predictions remain local, WORKLOG.md untouched,
no push. Fitting source/data/spec/reconciliation already committed in 10c2d39.

2026-09-05 — STATE: CPU RELATION TASK COMPLETE IN THIS COMMIT; REGISTER NOT READY.
Final verification: 33 targeted tests pass, one expected failure; lint and diff
checks green. Verified every seed-0 artifact/input hash, both stability checkpoint
hashes, preserved fitting source via 10c2d39, current evaluation source hash,
per-seed CPU budgets, 594-row confusion total, and report length (50 lines).
One held-out inference after two documented unscored preflight failures; no
post-score changes to data/model/thresholds. This commit lands final metadata,
report and evaluation-only guard fixes. Next: no further run authorized by this
task; any future development must preserve the already-used held-out boundary.
