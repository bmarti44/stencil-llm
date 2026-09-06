# FOCUS-3 v6 / relations v2 refit — pre-written registration (2026-09-06)

User-authorized step B supersedes the v5 stop. Fit-on: patched original Kimi,
Astra/Opus enrichment, reviewed Kimi transitions, Opus enrich-2, and 90 retained
Astra enrich-2 relatives (three verbatim bank rows already deleted). Those 90
are evaluation-derived development material; this setup/gate is a development
runtime agreement check, not unseen-idiom generalization. Calibration-on:
seed-specific scenario-disjoint DEV only. Evaluate-on: held-out-2 SECOND LOOK
(diagnostic, never a claim or selection signal), then reused setup30321;
gate30322 remains unexecuted unless eligible. No data/bench or sealed inputs.
Frozen admission branch is unchanged, including its historical lineage caveats.

## Rulings frozen before fitting

1. Apply relations-merged-patch and transitions-opus-patch to exact preimages.
   Mechanical repair: start=message.find(span text), end=start+len(text).
   Drop/count nonverbatim target/admission span text and invalid status (allowed:
   live/superseded/cancelled/completed). Normalize new_rule_spans to strings.
   Backfill id from source file + original row number and scenario_id from
   normalized message identity; preserve existing IDs and declared relatives.
   Identical messages and declared scenario/relative connected components never
   straddle fit/dev. Preserve whole-message candidate text: no speculative
   reauthoring/sentence splitting. Retain status-only minimal pairs by deduping
   full rendered model input; exclude contradictory labels for identical inputs.
   Report repairs/drops and final counts per label, author, and source file.
2. Seeds0/1/2, three full epochs, GPU, same base BAAI/bge-small-en-v1.5 revision
   5c38ec7c405ec4b44b94cc5a9bb96e735b38267a and recipe as952079b8:
   AdamW3e-5, batch32, weight_decay.01, warmup.06, clip1, dropout.1,
   CLS+role, class weights recomputed on fit, max512/overflow abstention,
   deterministic final-epoch checkpoint only. Seed0 always ships; no selection.
   Model metadata at data/classifier/model/relations-v2/seedN; weights out of git.
   Foreground only, atomically claim v6/RUNNING.flag under review lock, wait for
   every other quick-check flag and any GPU compute process; ignore no PID.
   Never terminate/signal. Preserve all earlier committed artifacts; no push.
3. DEV thresholds: lowest feasible .50:.01:.98 per positive class with empirical
   gold-none FP cap5%, else disable at1.01. No margin substitution: the explicit
   per-class cap is binding. C' differs only in supersedes cap10%, independently
   calibrated on the same DEV. Positive argmax/threshold >= consumer unchanged.
   Report correct-positive recall/usefulness>=.60 descriptively, not seed select.
   Admission requires NO positive proposal meeting its threshold on ANY
   overlapping pair, before status/kind/reinstates applicability filtering;
   overflow blocks. P(none)>=.50 is retired for v6. Admission P(rule)>=.95 stays.
   No new quoted-text veto or admission training.
4. After all three models and both policies freeze, evaluate seed0 on the
   committed357-pair held-out-2 exactly once more. Durable second-look receipt
   precedes read; raw per-pair logits/predictions written in the inference run.
   Report primary/secondary and delta from952079b8's first look. No post-score
   recipe, threshold, data or runtime tuning.
5. ONE CPU pre-gate replay: exact v5 setup30321 bank, all96 records/16 traces.
   Required36/36 admissions, >=11/12 correct-source transitions, zero unauthorized
   applications, no overflow. Per-label recall table (reinstates N/A if no gold).
   Retain v5 >=3/4 represented-label floor (implied by >=11/12). Else INELIGIBLE
   and stop: no trunk loading, O setup, gate or additional corrective replay.
6. If eligible, O setup16 requires>=15 final successes; project after setup.
   Gate exactly64 episodes seed30322, arms C,C',O,N,T, same greedy64-token trunk,
   renderer/checkers/history and no masking. C register-exact>=48/64 and>=12/16
   each family; absolute stale/final-success C/O distance<=4/64; false retirements
   <=2/64; breakage<=2/64; stale C<T; zero contradictory recaps. Same readings
   separately for secondary C'. No arm substitution or48 fallback. Cap10800
   GPU-held seconds, conservatively including this refit's GPU time; projection
   = spent + 1.25*slowest O setup episode*64*5, require<=10770. Cooperative
   deadline checks only; incomplete budget run reported INCOMPLETE.

Outputs: registration, data counts/split receipts, calibration, frozen model
metadata, second-look records/metrics/delta, CPU records/traces/summary/audit;
O/gate records only if eligible. Append outcome here, dated v2 refit report,
README item and WORKLOG; force-add results, commit explicit paths, no push.
