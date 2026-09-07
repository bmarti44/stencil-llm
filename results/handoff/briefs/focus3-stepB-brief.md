# FOCUS-3 step B for gpt-6-astra: clean refit with the transition + quoted-negative enrichment, then gate v6 (2026-09-06)

Inputs: results/quick-checks/focus3-gate/v5/RESULTS.md (step A: admissions 33/36, transitions 8/12, 2 unauthorized
from quoted text); data/classifier/relations/kimi-transitions.jsonl (1,466) + data/classifier/review/transitions-opus-
patch.jsonl (3 relabels, 2 drops; systemic: target_span.end wrong on 1,206, start wrong on 70, whole-message spans on
1,191, new_rule_spans mixed types, missing id/scenario_id, one invalid status) + data/classifier/relations/opus-enrich-2.
jsonl (291: 150 quoted/reported hard negatives, 61 switched-task admissions, 80 low-confidence pair rows) + the
earlier corpus/patches/enrich (relations-merged-patch, astra-enrich-2 with the 3 verbatim bank rows already deleted);
trainer scripts/train_relations.py; runtime src/stencil/focus3.py with the v5 step-A fixes.
RULINGS (register in results/quick-checks/focus3-gate/v6/RESULTS.md pre-written section BEFORE fitting):
 (1) Loader: mechanical span repair (start = message.find(text); end = start + len(text); rows whose span text is not
     verbatim in the message are DROPPED and counted), normalize new_rule_spans to strings, backfill id/scenario_id
     (scenario-level split: rows sharing scenario_id never straddle fit/dev), invalid status -> drop. Apply both patch
     files. Report final counts per label and source.
 (2) Refit seeds 0/1/2, 3 epochs, GPU (idle now; write results/quick-checks/focus3-gate/v6/RUNNING.flag; never signal;
     Brian's llama-server is gone; ignore nothing else). Same recipe/base encoder as 952079b8.
 (3) Thresholds on DEV only: per-class none-FP cap 5% (primary, as registered before) AND a registered alternative
     policy with supersedes at none-FP cap 10% (arm C'); admission = "no positive proposal >= its threshold on any
     overlapping pair" (positive-proposal bound; the P(none) >= .5 rule is retired); admission P(rule) >= .95 unchanged.
 (4) Held-out-2: evaluate seed 0 ONCE MORE as a disclosed SECOND LOOK (diagnostic, not a claim); report the delta.
 (5) CPU pre-gate replay on the v5 setup bank (seed 30321) with the new model: required 36/36 admissions, >= 11/12
     transitions, 0 unauthorized applications, per-label recall table; else INELIGIBLE and stop.
 (6) Gate v6: 64 episodes (seed 30322 bank from v4/v5, unopened) x arms C (primary thresholds), C' (alt), O, N, T;
     readings unchanged (C register-exact >= 48/64 and >= 12/16 per family; C within 4/64 of O on stale executions and
     final success; false retirements <= 2/64; breakage <= 2/64; stale C < T; zero contradictory recaps); C' reported
     with the same readings as a secondary. Cap 3 GPU-h; project after O setup.
Outputs under results/quick-checks/focus3-gate/v6/ (RESULTS.md pre-written + outcome, summary, records, traces,
calibration, data counts); model metadata under data/classifier/model/relations-v2/ (safetensors out of git); update
results/relations-classifier-report.md with a dated "v2 refit" section; README item + WORKLOG; commit with explicit
pathspecs (git add -f for results); no push. Foreground only; never terminate or signal any process; never read the
sealed IFEval input file or anything under data/bench.
