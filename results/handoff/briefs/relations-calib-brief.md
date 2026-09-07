# Task for gpt-6-astra: relation classifier — apply the frozen DEV operating-point rule, GPU retrain 3 epochs, evaluate ONCE on held-out-2 (2026-09-05)

RESUME after the power outage. State in git: results/relations-classifier-report.md (first CPU model: argmax 81%
held-out-1 / 86-89% dev; the 2% none-FP fail-safe drove thresholds to 0.98 -> coverage 0), commit b134f6f8 "Freeze
DEV-only relation operating-point rule and calibration curves" (data/classifier/model/relations/operating-point.json
+ calibration/), untracked partial retrain dirs data/classifier/model/relations-seed1/ and relations-seed2/ (may be
incomplete — verify or discard). Held-out-1 (fable-relations-heldout.jsonl) was SEEN ONCE and is now development
only; held-out-2 (data/classifier/heldout/fable-relations-heldout-2.jsonl, 357 rows, 14774ba/8ae68078) is UNTOUCHED
and reserved for exactly ONE final evaluation in this task.
Do: (1) verify the frozen operating-point rule and curves; (2) GPU retrain seeds 0/1/2 with 3 full epochs
(scripts/train_relations.py; same data/merged patch/dev split; minutes on the GPU) — the GPU hosts Brian's
llama-server (pid 2705; not ours; never touch); use the GPU when no other Stencil python process is present and write
results/quick-checks/relations-retrain/RUNNING.flag while training (delete after); (3) apply the frozen rule on the dev
split, record dev metrics for all seeds; (4) evaluate seed 0 ONCE on held-out-2: accuracy, per-class P/R, confusion,
none-FP, coverage, hard-negative slice, the v3-clause cells; (5) update data/classifier/model/relations/{metrics.json,
thresholds.json, manifest.json} (lineage line: fit-on = kimi+enrich after merged patch; calibrated-on = dev; evaluated-
on = held-out-2 once; held-out-1 = development) and append a dated "Retrain + held-out-2" section to
results/relations-classifier-report.md with a plain-language readiness paragraph for the FOCUS-3 feasibility gate.
Keep safetensors out of git. Commit the metadata, calibration files, report with explicit pathspecs; no push; do not
edit WORKLOG.md. Foreground only; never terminate or signal any process; never read the sealed IFEval input file or
anything under data/bench.
