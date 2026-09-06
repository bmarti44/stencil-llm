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

## Outcome — 2026-09-06

**INELIGIBLE.** The refit and disclosed second look completed. The single CPU
setup replay failed the required admission and unauthorized-application readings.
No O setup, trunk load or C/C'/O/N/T gate inference ran; seed 30322 remains
unevaluated. No post-outcome model, threshold, runtime or data change/replay.

| CPU setup criterion | v6 | required | v5 |
|---|---:|---:|---:|
| Initial ordering admissions | 16/16 | 16/16 | 16/16 |
| Initial tag admissions | 16/16 | 16/16 | 16/16 |
| Switched-task admissions | 3/4 | 4/4 | 1/4 |
| Total authorized admissions | **35/36** | **36/36** | 33/36 |
| Correct-source transitions | **11/12** | >=11/12 | 8/12 |
| Unauthorized applications | **2 in 2 records** | **0** | 2 |
| Records / traces | 96 / 16 | 96 / 16 | 96 / 16 |
| Overflow | 0 | 0 | 0 |

| Transition label | gold | proposed correctly | applied correctly | recall |
|---|---:|---:|---:|---:|
| supersedes | 4 | 3 | 3 | 75.00% |
| cancels | 4 | 4 | 4 | 100.00% |
| completes | 4 | 4 | 4 | 100.00% |
| reinstates | 0 | 0 | 0 | N/A (no gold support) |

All three inherited named misses now pass, without removing their setup sentences.
The remaining supersedes miss is setup_0_02: “For task S0n2A, switch the standing
order from descending to ascending.” Correct-target P(supersedes)=.570806<.90.
No secondary setup trajectory was run or substituted.

The two unauthorized applications are different failure modes:

- setup_0_01 turn 1 admits the quoted sample “Inert setup context: the sample
  "Cancel the sorting rule for task S0n1A." is not an instruction.” Admission
  P(rule)=.960425; both overlapping relation pairs propose none (.978524/.980012
  P(none)). The relation-only refit does not repair this frozen admission error.
- setup_3_02 turn 2 wrongly supersedes global tag row 0:20 with the new task B
  ordering sentence (P(supersedes)=.949289). It creates a task B version under the
  tag key, shadowing the tag there; the global row survives outside task B. The
  sentence passes admission P(rule)=.958220, but is consumed by the wrong relation
  instead of creating a new key. This is the missing 36th authorized admission.

V5's quoted cancellation is now none (P(cancels)=.007925), with admission
P(rule)=.760051, so it no longer changes the register. Zero reinstates applied.

## Corpus accounting

Raw 7,875 rows; patches drop 123 (original 121 + transitions 2), relabel 225; mechanical
loader drops another 3 (two nonverbatim target spans, one invalid status). Final
7,749 pairs, no admission-only exclusions or full-input dedup removals. Preserve
whole-message candidate text; the reported span issue is repaired mechanically,
not reauthored into new sentence/label examples. The full-input dedup avoids
conflating distinct status/context/metadata inputs: the earlier coarse dedup
removed 143 such rows; this registered change retains them.

The post-patch mechanical pass repairs 68 starts/1202 ends, normalizes 110 span
objects to strings, backfills 6,812 IDs / 6,538 scenario IDs. Additional dropped
transition source rows are 558, 626, 725 (one-based; reviewer indices 557, 625, 724).
Both exact-preimage patch files and detailed repair receipts are in data-counts.json.

| Source | none | supersedes | cancels | completes | reinstates | total |
|---|---:|---:|---:|---:|---:|---:|
| astra-enrich-2 | 0 | 30 | 30 | 30 | 0 | 90 |
| astra-enrich | 180 | 10 | 10 | 50 | 70 | 320 |
| kimi-relations | 2335 | 982 | 699 | 640 | 609 | 5265 |
| kimi-transitions | 344 | 412 | 273 | 274 | 158 | 1461 |
| opus-enrich-2 | 251 | 11 | 10 | 10 | 9 | 291 |
| opus-enrich | 149 | 76 | 16 | 20 | 61 | 322 |
| **Total** | 3259 | 1521 | 1038 | 1024 | 907 | **7749** |

Every seed has 6,974 fit / 775 DEV rows; DEV has 326 none / 449 positive rows. Scenario/message/declared-relative
connected components are disjoint. The unchanged split algorithm assigns all 90
evaluation-derived Astra2 relatives to seed 0 DEV, and 30 fit / 60 DEV for seeds 1/2.
Thus seed 0 did not fit on those 90; they do influence its DEV operating point.
No seed/split selection was performed. Backfilled scenario grouping uses exact
message identity, not proof of semantic independence for undeclared paraphrases.

## DEV calibration and resource use

Each seed completed 3 epochs / 654 updates; training algorithm AST matches 952079b8
apart from the registered loader option. Same base encoder/revision/optimizer.
Zero fit/DEV overflow. C cap 5% means<=16/326 none-FP per positive class; C'
supersedes cap 10% means<=32/326. Combined FP is not constrained to 5%/10%.

| Seed / arm | thresholds S/C/Cm/R | accuracy | correct-positive recall | positive precision | combined none-FP |
|---|---|---:|---:|---:|---:|
| 0 / C | 0.90/0.50/0.50/0.50 | 91.61% | 414/449 (92.20%) | 414/447 | 30/326 |
| 0 / C' | 0.50/0.50/0.50/0.50 | 90.71% | 424/449 (94.43%) | 424/476 | 47/326 |
| 1 / C | 0.82/0.50/0.50/0.50 | 93.03% | 425/449 (94.65%) | 425/461 | 30/326 |
| 1 / C' | 0.50/0.50/0.50/0.50 | 93.03% | 432/449 (96.21%) | 432/476 | 37/326 |
| 2 / C | 0.88/0.50/0.50/0.50 | 91.61% | 418/449 (93.10%) | 418/459 | 34/326 |
| 2 / C' | 0.60/0.50/0.50/0.50 | 90.84% | 429/449 (95.55%) | 429/490 | 51/326 |

Total GPU-held time **195.999037/10800 seconds** (3.27 minutes),
including all three refits; own flag removed on natural exit. CPU setup loop
15.204360 wall seconds; 165 relation pairs/184 admission spans.
O-setup projection is not applicable because eligibility stopped before O setup.

## Held-out-2: disclosed SECOND LOOK, diagnostic only

One additional 357-pair seed 0 CPU inference after freeze 54e09f25, durable receipt
before read; each row saved in that same pass. Author/declared-relative/pair/
message overlap checks against the refit pool are all zero (exact identities,
not semantic proof). No new held-out claim, selection, tuning or deployment
readiness follows from this repeat. Both policies scored the same saved logits.

| Policy | accuracy | correct-positive recall | positive precision | none-FP |
|---|---:|---:|---:|---:|
| 952079b8 first look | 337/357 (94.40%) | 196/206 (95.15%) | 196/206 | 10/151 |
| v2 C second look | 343/357 (96.08%) | 201/206 (97.57%) | 201/210 | 9/151 |
| v2 C' second look | 344/357 (96.36%) | 203/206 (98.54%) | 203/213 | 10/151 |

Primary delta: +6/357 correct (+1.68 percentage points), +5/206 correct positives
(+2.43 points recall), -1/151 none-FP (-.66 points). C' remains secondary; no
full C' setup/gate outcome exists.

| Held-out label | C correct / gold | C' correct / gold | C none-FP /151 | C' none-FP /151 |
|---|---:|---:|---:|---:|
| supersedes | 64/68 | 66/68 | 1 | 2 |
| cancels | 47/47 | 47/47 | 6 | 6 |
| completes | 44/45 | 44/45 | 0 | 0 |
| reinstates | 46/46 | 46/46 | 2 | 2 |

## Verification and files

92 targeted tests pass, 1 existing expected failure; lint/diff checks pass. Saved
CPU Runtime replay matches every record/trace; trainer rendering and raw softmax
parity pass. All three split receipts/calibration grids reproduce. Second-look
metrics/predictions reproduce from 357 saved logits without another input read.
Independent action/state audit accounts 48 applications , 40 new rows / 11 status
changes, zero unexplained mutations; authorized 35 admissions + 11 transitions, 2 unauthorized.

Raw summary inherits a historical diagnostic field,
`diagnostics.gold_none.guard_admitted`: it counts 120/153 pairs at the retired
P(none)>=.50 cutoff; **it is not the v6 admission decision**. The actual new
no-positive-proposal pair bound passes 124/153 gold-none pairs; 29 propose a
positive, one applies. `independent-audit.json` records this distinction.
Eligibility/admission records use the registered positive-proposal bound.

`recipe-freeze.json` binds reading/code/inputs/admission/bank; `freeze.json` binds
all three checkpoints/metadata. Recipe 44abb504, models 54e09f25, second look a627c512
precede CPU eligibility. `records/`, `traces/`, `summary.json`, `audit.json`,
`independent-audit.json`, `data-counts.json`, `calibration/`, and second-look files
carry the measurements. Seed metadata/DEV logits/tokenizers live under
`data/classifier/model/relations-v2/seed{0,1,2}`; safetensors remain local and
are hash-bound. Historical source data/models/results are unchanged. Foreground
only; no signals, benchmark/sealed reads, gate generations or push.
