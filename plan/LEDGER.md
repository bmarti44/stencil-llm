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

2026-09-05 18:53 UTC — STATE: DEV OPERATING-POINT REVISION STARTED.
User authorizes revising the orchestrator development choice and GPU seeds
0/1/2 for three full epochs; this is not an archived science phase gate.
Fit-on = unchanged patched Kimi + Astra/Opus enrichment; calibrated/evaluated-on
= original seed-specific scenario-disjoint DEV only. Held-out-1 was seen once
previously and is now development history. No held-out or benchmark input opened
in this task; held-out-2 reserved for a later final check. No background launch,
signals, WORKLOG edit or push. GPU wait 18:53 UTC to 2026-09-06 00:53 UTC;
600-second polls. Initially GPU empty but check40/check41 run scripts live and
readings PENDING; check40 then acquired the review lock for its GPU run.
Initial source edits preceded noticing that lock; after detection all subsequent
calibration/source work stayed in /tmp pending release. No review/coder wrapper
was running. The protocol is archived; the user's foreground CPU-now instruction
governs this narrow development revision, with no new science-gate claim.

2026-09-05 19:01 UTC — STATE: CPU RULE FROZEN; GPU PRIORITY WAIT.
DEV split hashes and unchanged input hashes reproduce; CPU seed-0 logits were
recomputed on CPU only, no held-out access. Freeze lowest per-class threshold
on .50:.01:.98 with empirical none-FP <=.05; require correct-positive recall
>=.60, a conservative interpretation of positive coverage. Else lowest single
margin on .00:.01:.98 satisfying both requirements. If neither qualifies retain
per-class and explicitly fail usefulness. Each seed recalibrates this exact
rule on its original DEV; seed 0 always ships, without selection on scores.
CPU selected [.89,.50,.50,.50]: 283/317 correct-positive recall, 283/322 precision,
322/576 emitted/all coverage, 286/317 emitted/gold-positive coverage, 36/259
combined none-FP; per-class FP counts 12/10/9/5 (denominator 259). Qualified.
Margin .80 is the first feasible margin: 280/317 correct positives, 280/305
precision, 25/259 combined none-FP; diagnostic because primary qualifies.
The old .98 floor, not the 2% cap alone, caused abstention: DEV 2%-without-floor
thresholds [.94,.91,.87,.50] recover 229/317 positives, precision 229/246.
These are descriptive DEV measurements, no population guarantee.

2026-09-05 — check40b WRITE-AHEAD: user's minimal unregistered foreground SET pass.
Archived PROTOCOL read; no review/coder wrapper owns the lock. Fit/train-on none;
profile-on same 32 cued competence replies, choose alpha on 8 setup tasks, evaluate
32 disjoint synthetic expression statements from check40 cf8c38ae. No sealed reads.
Interpret four grid cells as two directions x two alphas; choose alpha from JS
cells by JS-valid count, then breakage. Mean raw logits, generated-token positions;
no new profile decoding. Fixed reading/projection in check40b/prewritten-reading.md.
Initial GPU empty and check41 process absent; RUNNING.flag written for check42.

2026-09-05 — check40b COMPLETE: MARGINAL, correct JS26/32 but broken6/32 >2;
OFF/shuffled Python32/32, text JS32/32. 224 records/32 teacher-forced profiles audited;
744.53/5400 GPU seconds. Lock queue fixed before outcomes; original waiter naturally
exited before model load. No training/sealed reads/signals/push. This scoped commit closes check40b.

2026-09-05 — check41b WRITE-AHEAD: direct user-authorized foreground causal-neuron check; archived protocol read. No fit/train. Gradient readout 32 synthetic tasks, select 8 setup, evaluate 32 distinct prompts; seed 41042. Fixed reading in check41b/prewritten-reading.md; no sealed reads, signals or push; 5400-second cooperative cap.

2026-09-05 — check41b PILOT: {"pilot_seconds": 2.3100071551743895, "worst_fit_or_pilot_seconds": 6.602241795975715, "mean_fit_or_pilot_seconds": 2.5802316907652174, "pilot_tokens": 44, "projected_seconds_with_optional_history": 2638.4149435981863, "peak_memory_bytes": 8519124992, "cap_seconds": 5400}; fixed design, cooperative cap, no outcome redesign.

2026-09-05 — check41b SET COMPLETE: all 36 grid cells frozen before 160 fresh SET records. Selected k=200/g=3/T=1 multiply (setup JS 4/8, broken 1/8). SET correct JS 14/32, broken 7/32 => MARGINAL; swapped/shuffled/OFF JS 0/32; text cue 32/32. Mean c shifts correct +20.5957, swapped +20.9110, shuffled +0.2237, OFF 0, text +41.8997. Correct token 1 is ` moduleId` on 23/32: registered parser-level result, not clean runnable-program evidence. Required >=12 trigger met: continue the frozen 16 retained-history episodes, no adjustments or signals.

2026-09-05 — check40c WRITE-AHEAD: frozen 40b JS direction, same 32 exploratory screen tasks; fit/train none, prior profile/setup disjoint. Four arms and reading frozen in check40c/prewritten-reading.md; CPU real-HF slot/schedule checks pass. Foreground 1800-second GPU cap, 300-second flag polls; no sealed inputs, signals or push.

2026-09-05 — check41b COMPLETE: MARGINAL; all 800 generation records and 32 per-task attribution files saved. GPU 2418.0495/5400 seconds; flag removed, no signals. Full consumer audit PASS. Seven correct JS histories persist at HOLD/SWITCH/BACK/CLEAR; text cue active-stage target success 16/16. Final report, five-line index and six-line WORKLOG ready for explicit-path local commit; no push.

2026-09-05 — check40c COMPLETE: POSSIBLE; alpha2 sustained JS25/32 broken0 frozen by prewritten order, alpha3 JS32/32 broken0. First3 JS25/broken4; first8 JS26/broken6. All 128 new/64 reference records CPU-audited; 629.2471514409408/1800 GPU seconds, no overrun. RUNNING.flag removed; no fitting/sealed reads/signals/push.

2026-09-05 — check40d WRITE-AHEAD: user-authorized unregistered foreground router history check; archived science/protocol and current ledger read. Fit/train none; reuse committed 40b competence profiles/direction; evaluate fresh synthetic screen-family expressions, disjoint from prior profile/setup/screen expressions. Alpha3 primary by explicit orchestrator override of 40c first-eligible alpha2, alpha2 secondary. Fixed reading and projection will precede outcomes. Interpret retained history as actual KV plus complete own pairs; shuffled random matched-norm at every step including CLEAR; text CLEAR uncued. No wrappers active. GPU pid2705 untouched; observed 93445 MiB server allocation and only ~20 GiB MemAvailable, so preparation proceeds on CPU pending sufficient memory. No sealed reads, signals, background launch or push.

2026-09-05 22:56 UTC — check40d FROZEN/LAUNCH: CPU real-consumer KV/schedule, raw-slot, cap-closure and verdict checks PASS; 32 episodes/992 generations, capped projection 7002.679/7200 s. README/prewritten-reading/tasks/biases/source hashed before outcomes. Memory changed externally to 115.7 GiB available, GPU process list empty, no flags; no process touched by this task. Foreground runner acquires review lock and publishes RUNNING.flag; complete user/assistant pairs and actual KV, fresh CLEAR OFF baselines, alpha3 primary/alpha2 secondary.

2026-09-05 — check40d COMPLETE: PARTIAL; SET/HOLD/BACK JS32/32 with broken0, SWITCH/CLEAR Python0/32, 32 paired CLEAR impositions. Shuffled JS0 throughout; text SWITCH Python32/32 but CLEAR JS32/32; alpha2 JS6/32 throughout. All 992 records, frozen biases, permutations, fresh tasks, retained KV histories and reading CPU-audited; 2088.0014/7200 GPU s, no overrun. Primary broken0/coarse32 each step; shuffled numeric history ambiguous and lambda history coarse-failed disclosed. RUNNING.flag removed; no signals/sealed reads/fitting/push. Scoped local commit closes the requested check.

2026-09-05 — check43 write-ahead (gpt-6-astra). STATE: CPU recipe/checker ready; next foreground scripts/focus_check43.py --mode run after scoped freeze commit.
Fit/train none; profile seed95061 Python, dose seed95062 Python, fresh evaluation seeds95063/95064 Python/JS; no benchmark/sealed reads.
Source results/neuron-granularity-research-astra.md §4 items1–11 governs this unregistered check; bounded AST fixtures/native parity and actual small-model dispatch/OFF checks pass.
Freeze 96 tokens, layers7–34, alpha1/2/3, paired6/8 setup; 392 scored generations plus one disclosed OFF instrumentation replay; reject projection >5400s.
Source arithmetic recomputed1.1885h; RUNNING.flag acquired atomically under review lock, Brian pid2705 exempt; no signals/background/push.
CPU recipe committed before load; any selected profiles/dose/setup and full final binding committed before final generation; stop gates applied without rescue.

2026-09-05 — check43 completion (gpt-6-astra). STATE: FAIL/NO SAFE SET; task complete after frozen setup stop, report/artifacts committing; no next GPU command.
Donor SUM/PRODUCT16/16 each; alpha1/2/3 each paired0/8 and malformed0; each sign SUM7/8, PRODUCT0/8, one slice-endpoint error.
Last-four-neutral-token example means, 7–34 band and shuffle recomputed exactly; consumer route/weight changes real, OFF unchanged; 81-record CPU audit PASS.
Final/JS-transfer/selected-dose controls/collateral branches not reached; no post-outcome rescue. 700.2435/5400s; 82 total generations incl. one OFF replay.
Recipe a993adbc committed before outcomes. All output artifacts force-added with explicit paths; no signals/background/termination/push; RUNNING.flag absent.

2026-09-05 — check40e WRITE-AHEAD (gpt-6-astra): user-authorized quick check; archived protocol/science and current state read; no wrapper active.
Fit/train none; profile-on 16 paired synthetic competence tasks per pair; evaluate-on 32 disjoint synthetic tasks per pair, seed40050; no sealed/benchmark reads.
Go/gofmt absent: frozen P1 Python/TypeScript fallback; P2 JSON rows/SQL. Both executable semantic checkers, OFF-first distribution, alpha3 sustained, cap64, five arms.
192 canonical CPU cases plus negative fixtures and inherited real-HF router/consumer checks pass. Frozen reading uses semantic success/breakage, matched shuffle40052, >=14/16 competence.
Full cap-based projection3351.196/3600s; measured resource-only16-task fallback uses proportional thresholds with reduced-screen disclosure. Foreground/no signals/no push; all flags coordinated; pid2705 exempt.

2026-09-05 — check40e COMPLETE (gpt-6-astra): P1 NOT; P2 INELIGIBLE. OFF P1 Python32/32 correct; P2 JSON32/32 with25/32 correct row sets.
P1 Python/TypeScript competence16/16 each, top8 overlap75.5208%; alpha3 correct/swapped/shuffled TS0/32, text32/32; broken0, paired flips0/32.
P2 JSON15/16 and SQL0/16: all16 replies use wrong table identifier `table`, intended predicates retained. Frozen competence gate stops P2 profiles/interventions; non-language flip untested, no outcome rescue.
256 generations/6546 tokens/32 teacher-forced profiles; CPU consumer/token/profile/bias audit PASS; 803.824/3600 GPU seconds; full32-task P1 screen/P2 OFF, no reduction.
Recipe6d28b09c precedes outcomes. Flag removed after cleanup; no sealed reads, fit/train, signals/background/push. Scoped report/artifacts/index/WORKLOG commit closes user task.

2026-09-06 — check42 REBOOT RECOVERY/WRITE-AHEAD (gpt-6-astra).
Fit/train none; evaluate frozen FOCUS-2d final seed9053723, other-arm outcomes seen.
All 11 freeze hashes and seven committed preparation artifacts match; reuse CPU validation.
Preserve four uncommitted interrupted records; fresh original 192 episodes, no outcome selection.
Charge prior launch-to-boot upper bound299s; combined projection12356.312/12600s.
Only scheduling/accounting updated for user server exemption and RUNNING.flag; no wrapper active.
Next scoped freeze commit, foreground run, CPU full-record audit, report/index/WORKLOG commit; no signals/sealed reads/push.

2026-09-06 — check42 FIRST CELL PRESERVED / DELAY EXCLUSION OBSERVED.
48 episodes/1008 records committed85524381 while foreground runner continues.
B at ascending/512/index0 capped DELAY1 at160 and RETRY320; frozen common-pair
exclusion applies and prewritten no-exclusion closure guard cannot pass.
Continue all frozen episodes within cap; no prompt/cap/reading adjustment.
Before inspecting task-score aggregates: also report A/C complete-pair coverage
on all planned IDs as a descriptive censoring diagnostic, because B-only delay
failures otherwise hide valid A/C records. Keep frozen common-sample verdict;
no new closure gate, selection, threshold, prompt or generation change.

2026-09-06 — check42 HALF-SAMPLE PRESERVATION: all96 ascending episodes scheduled through termination; A/C complete, B capped-delay exclusions retained. Charged6023.117/12600s. Commit prefix96; foreground descending cells continue unchanged.

2026-09-06 — check42 THREE-CELL PRESERVATION: all144 episodes scheduled through termination, unchanged36 B delay exclusions; all A/C complete. Charged8042.256/12600s. Commit prefix144; final48 descending/delay512 episodes continue in foreground, no recipe changes.

2026-09-06 — check42 FINAL-CELL MIDPOINT: 168 scheduled episodes through termination; charged9841.704/12600s. Preserve prefix168 before final24; A/C complete, B delay exclusions retained, frozen run continues unchanged.

2026-09-06 — check42 COMPLETE / FINAL AUDIT PASS; frozen MASKING NOT CLOSED.
All192 scheduled attempts; B68 twice-capped delays, common124. A/B99 vsC88,
constraint0 each; numeric gates pass but frozen no-exclusion condition fails.
Full A/C diagnostic151 vs131/192, b/c39/19, p(worse).99732257; A user/tool failures1 each.
All4471 records replayed, all1632 C trajectories match original, exact stats independently checked.
Input-only correction: selected IDs contain64 memo, not preparation prose48; IDs/bank/recipe unchanged.
Charge11631.286656/12600s incl.299s old bound; natural exit, flag absent, no signals/sealed reads/fit/push.
Final explicit-path local commit carries complete report/index/WORKLOG and forced result artifacts; no next run.

2026-09-05 post-reboot — STATE: RELATIONS GPU RETRAIN WRITE-AHEAD (gpt-6-astra).
User authorizes seeds 0/1/2, three full GPU epochs, same original seed-specific
fit/DEV splits, frozen b134f6f8 operating rule; seed 0 predetermined, no selection.
Fit-on = kimi+enrich after merged patch; calibrated-on = dev; evaluated-on =
held-out-2 exactly once after all freezes; held-out-1 = development history.
Archived protocol read; user task supersedes obsolete CPU/GPU-wait restrictions.
Frozen rule/source hashes, commit bytes and all 592 CPU curve rows reproduced.
Existing seed1/2 dirs are intact historical CPU runs (312/326 steps), not GPU
retrain checkpoints; preserve them and use results/quick-checks/relations-retrain/seedN.
No review/coder wrapper/lock owner, Stencil GPU python or RUNNING.flag observed.
Foreground launch publishes relations-retrain/RUNNING.flag under brief review-lock
acquisition, exempts Brian pid2705, and removes only its own flag on natural exit.
No signals/background, held-out reads during training, benchmark inputs, WORKLOG
edits or push. Each run must complete 489/489 steps and 3/3 epochs before freeze.

2026-09-06 UTC (2026-09-05 local) — STATE: RELATIONS THREE GPU SEEDS FROZEN.
Each finished 489/489 steps, 3/3 epochs in 49.03/49.15/49.05 wall seconds;
original per-seed input and fit/DEV split hashes reproduce exactly. All 1,776
GPU calibration curve rows recomputed; frozen rule unchanged. DEV argmax
and operational reports, per-class counts, checkpoints and logs preserved in
canonical calibration/ and metrics.json. DEV operational accuracies 91.15%,
91.84%,90.10%; all qualify. Seed0 policy .94/.50/.50/.50, 292/317 correct-positive
recall,26/259 combined none-FP (11/6/7/2 per class); never select seed by scores.
Historical CPU seed0 directory preserved locally and metadata copied into
calibration/. RUNNING.flag removed after natural completion; no signals.
37 targeted synthetic tests pass, lint clean. New one-shot evaluator uses the
actual frozen policy, durably claims before input read, pins held-out-2's git
blob, and writes per-row raw logits/metadata/predictions in the same pass.
Next: explicit-path freeze commit, then ONE foreground CPU inference via
CUDA_VISIBLE_DEVICES='' .venv/bin/python -m scripts.evaluate_relations_heldout2.
No held-out-2 input opened yet; no WORKLOG edits or benchmark/sealed inputs.

2026-09-06 — STATE: RELATIONS RETRAIN + HELD-OUT-2 COMPLETE; COMMITTING.
Freeze commit0829665c preceded the only held-out-2 open/inference (03:55 UTC).
357/357 pair records saved during that CPU pass; one excluded summary, zero
pair drops/overflow/author or declared-relative/pair/message overlap with fit+DEV.
Seed0 frozen-policy337/357=94.40%; argmax338/357=94.68%. Operational none-FP10/151,
hard-none10/107; positive precision196/206, correct-positive recall196/206;
emitted/all206/357. No outcome-based fitting, threshold changes or seed selection.
Descriptive v3 replay: bare suspensions5/6, scoped replacements15/22, hedges22/22,
closure+global-admission relation22/22; admission untested; subunit cell unsupported.
All357 raw records and independent confusion counts audited; all hashes match;
37 targeted tests and lint pass. Useful offline scorer; scope errors remain,
runtime/admission and64-episode FOCUS-3 gate untested, so no gate PASS/readiness.
Canonical metrics/thresholds/manifest and dated report updated; historical CPU
metadata/calibration preserved. Safetensors local only, flag absent, WORKLOG
unchanged; explicit-path commits only, no push/signals/benchmark/sealed reads.
No further training or held-out inference is part of this task.

2026-09-06 — STATE: FOCUS-3 GATE CPU BUILD WRITE-AHEAD (gpt-6-astra).
User brief supersedes archived design seeds/arms/masking:30301,64+16 setup,C/O/N/T,
no masking,3 GPU-h,optional48 resource-only before gate. Archived PROTOCOL read.
Fit-on: existing frozen relations kimi+astra/opus and inherited admission branch;
evaluate-on: new gpt-5.5-authored templates/fresh synthetic values, no fitting.
Admission retains disclosed development influence; no package-independence claim.
Reserved gpt-5.5 author has no relation-data context. O alone receives gold events.
Conservative reading: false retirement includes missing initial admissions;
agreement includes every task answer; absolute C/O distance<=4/64 for both endpoints.
CPU sealed guard: deselect its two hash-reading tests under explicit no-read rule.
No wrapper lock owner observed; foreground-only GPU claim requires empty compute
list and no quick-check RUNNING.flag; never signals. No push; explicit paths only.

2026-09-06 — check43b WRITE-AHEAD (gpt-6-astra). STATE: CPU READY; foreground run next after scoped recipe commit.
User-authorized unregistered check supersedes archived phase workflow; fit/train none. Profile existing32 check43 donors; select existing8 setup; evaluate fresh96063/96064 Python/JS only if safe.
Primary generated identity window d-2..d; actual identity d=21 all16 pairs (one first divergence d18 is a/acc naming). Norm grid6.805823/10.208735, both signs/stable shuffle, OFF first, same-runtime JS>=6/8 required.
CPU bounded/native fixtures and actual router consumer pass; selection/alignment/import tests6 passed/1 legacy xfail. Freeze includes reading/banks/source; setup1440s, final2700s only if safe; no sealed reads/signals/background/push.

2026-09-06 — STATE: FOCUS-3 GATE CPU READY; pre-inference freeze committing.
14 targeted tests pass,2 sealed-byte hash tests deselected by explicit no-read;
ruff clean;80 episodes/480 user requests validate,5 executable tasks+1prose each.
Independent gpt-5.5 author fixture and30301/30302 lists freeze before inference;
C task/kind selection parses visible user text only; gold keys evaluator-only.
Initial source IDs seed identical opaque C/O keys; no allocation-order artifact.
Cap64,greedy4B hf_compatible,1632 max generations initial projection9454/10800s.
Next foreground setup16 then resource-only64/48 selection and frozen gate;
claim only when compute list and all quick-check flags empty. No signals/push.

2026-09-06 — check43b COMPLETE (gpt-6-astra). STATE: CLOSE; no safe setup cell, no final/collateral run.
OFF SUM8/8; same-runtime JS8/8 validates harness. Both norms6.805823/10.208735: -b PRODUCT0/8, malformed0, shuffled-minus PRODUCT0/8; plus malformed0/1, shuffle-plus0/4.
Identity21 all32 donors/window19–21; raw profiles, all80 scores/hashes and stable matched shuffles independently reconstructed, consumer mismatches0. Tested direction changes decode routes63.01%/77.82%, mixtureL1.2023/.2951 without PRODUCT.
Recipe da131791 before outcomes; 80 generations/3963 tokens,672.881907/1440 GPU seconds; natural exit and flag absent. Operational closure of tested concept-routing recipe, not universal impossibility; explicit scoped results/index/WORKLOG commits next, no push/signals/sealed reads.

2026-09-06 — FOCUS-3 pre-inference loader repair; no outcomes existed.
Initial aa6c0e41 attempt failed before any classifier/trunk inference because
ft/head.pt wraps weights under head. Preserved freeze/start/log/summary in
initialization-failure/; charge2.570128334s carried into3h cap. Corrected wrapper
consumer with label/role/hidden assertions; actual two-branch CPU loader smoke
now passes.15 tests pass,2 sealed reads deselected,ruff clean. Reading/author/
bank byte-identical to aa6c0e41; new source freeze before any evaluation output.

2026-09-06 — STATE: FOCUS-3 GATE COMPLETE / INELIGIBLE AT SETUP; committing.
Frozen setup final8/16<15: override4,cancel0,complete/move0,switch/return4 per4;
stale8/16,broken0,tags80/80,task55/80. Mechanical stop; zero64-bank gate outputs.
C update diagnostics timed but O renders setup, so no C answer/agreement result.
96 records/16 traces retained; source/hash and independent token/history/score
replays pass.15 tests pass,2 sealed-byte hash tests deselected,ruff clean.
181.012248456/10800 charged seconds incl.2.570128334 initialization failure;
64 projection3320.879s fit. No outcome repair; failed init receipts preserved.
RESULTS.md/summary/index/WORKLOG ready; frozen reading unchanged; explicit paths
only, no push/fitting/sealed reads/signals, natural exit and own flag removed.
No next GPU command: authorized setup stop ends this frozen experiment.

2026-09-06 — STATE: FOCUS-3 V2 DEFAULT-RENDERING REPAIR WRITE-AHEAD.
User explicitly authorizes repair after setup8/16 and one setup->gate rerun.
Fit/train none; frozen relations/admission unchanged; evaluate synthetic only.
30302 was ALREADY the v1 setup seed: retain explicitly requested30302 and disclose
setup reuse; gate30301 stays byte-identical, unevaluated. Preserve v1 artifacts.
Default ordering is request-kind configuration shared by C/O, derived live output
when no applicable ordering row remains, including a fresh task after completion;
synthetic rows are not classifier inputs. N/T and plain renderer text unchanged.
check40f owns GPU/lock (direct script, not coder/reviewer wrapper); CPU scoped
repair authorized now, GPU waits for empty compute/all flags. No signals/push.

2026-09-06 — STATE: FOCUS-3 V2 CPU READY / GPU WAIT.
19 applicable tests pass;2 sealed-byte hash tests excluded;ruff/diff clean.
V1 file bytes verified against8f0c550b; bank byte-identical (setup30302 reused,
gate30301 unevaluated). Classifier/decision/renderer/episode/decoder/checker
ASTs unchanged. New default live rows and agreement audited through consumer.
Pre-inference freeze includes independent audit source; charge prior181.012s.
Next foreground scripts/focus3_gate.py --mode run when compute/flags empty;
setup15/16 required,then frozen64/48 resource decision/gate;no rescue/signals.

2026-09-06 — STATE: FOCUS-3 V2 FOREGROUND GPU LAUNCH.
Freeze27003fda precedes inference;check40f naturally finished,empty compute list
and no quick-check RUNNING.flag observed. Runner atomically claims its own flag.
Command:.venv/bin/python -u /home/bmarti44/stencil-llm/scripts/focus3_gate.py --mode run
Log:results/quick-checks/focus3-gate/console.log;pipefail preserves raw exit.

2026-09-06 — STATE: FOCUS-3 V2 SETUP PASS / FULL64 GATE RUNNING.
Setup16/16 final,4/4 every family;96 records retained,prior setup preserved.
Frozen resource rule projects3504.526747/10800s,select64 before gate output.
Foreground same process continues all C/O/N/T arms;no output-based changes.

2026-09-06 — FOCUS-3 V2 GATE QUARTER:16 override episodes/all4 arms complete;
384 gate records preserved before cancellation family. Recipe unchanged,
foreground process continues;full-cohort verdict/audit await remaining48.

2026-09-06 — FOCUS-3 V2 GATE HALF:32 override/cancel episodes/all4 arms
complete,768 gate records preserved;completion/move family now running.
No retries/exclusions/source changes;final agreement/endpoint audit pending.

2026-09-06 — FOCUS-3 V2 GATE THREE-QUARTERS:48 episodes/all4 arms complete,
1152 gate records preserved;final16 switch/return episodes underway unchanged.
Charged2321.907s incl.prior181.012;no budget pressure,retries,exclusions/signals.

2026-09-06 — STATE: FOCUS-3 V2 COMPLETE / FAIL; FINAL ARTIFACTS IN THIS COMMIT.
Setup16/16 passes;full64 gate C/O final27/61,stale27/2,C exact0/64 and false
retirements64/64;breakage0,contradictory0,C beatsT stale27<32;conjunction FAIL.
Raw admission:initial order0/64,tag64/64;no positive relation targets admitted,
48 gold change events unpaired;do not infer relation-transition recall.
Both audits PASS1632 records/272 episode-arms;19 tests,2 forbidden reads excluded.
2965.079361649/10800s incl.prior181.012;natural exit,own flag removed.
RESULTS v2/summary/README/WORKLOG ready;source/model/bank hashes match freeze.
No further run or repair authorized;explicit paths only,no fitting/sealed/signals/push.

2026-09-06 — STATE: FOCUS-3 V3 CPU WRITE-AHEAD (gpt-6-astra).
New user registration supersedes v2 stop: spec-conformant varied standing bank,
setup30311/gate30312,16/64,frozen v2 endpoints,3 new GPU-h,no48 fallback.
Fit-on = existing frozen ft and relations training (historical lineage caveats
retained); evaluated-on = fresh synthetic v3 templates/values; fit/train none.
Archive/plan/PROTOCOL.md read (root protocol archived); explicit task governs.
check40h pid807294 owns GPU/lock directly, not a review/coder wrapper; scoped
CPU work proceeds without GPU claim or process signals. Unrelated files excluded.
First freeze eight spec-authored paraphrases, score both directions plus v2 on
CPU using user-prefixed preceding sentences; use all eight, never score-select.
Repair admission context to that training contract, record every span's score.
Conservative pre-gate eligibility: all initial gold order rules16/16, every gold
standing admission/replacement (including tag and switched task), and all gold
cancellations/completions8/8 must be applied to the actual target; absence or
scope-hidden live rows do not count as retirement. Replay all16 setup episodes
on CPU before trunk load; any miss stops INELIGIBLE-ADMISSION with zero gate.
If eligible, wait for free GPU, claim own flag, setup O>=15/16 then full64 C/O/N/T.
No benchmark/sealed input reads, fitting, background launches, signals or push.

2026-09-06 — STATE: FOCUS-3 V3 FROZEN CPU READY; preflight next.
25 targeted tests pass,1 legacy inventory xfail,2 sealed hash readers deselected;
ruff/diff clean. Original v2 bank recompiles identically;80 new episodes validate.
All8 standing forms retained. Actual v2 G0n0A old wording P(rule).0260/.0263
legacy -> .4885/.3467 faithful (asc/desc); standing forms .99577-.99665 faithful.
Readable Inventory old wording .9721/.9660 shows task-name dependence, not rescue.
Freeze includes both diagnostic tables, bank, authoring, sources, tests, models,
reading and token audit. check40h naturally completed during CPU work; no signals.
Next: explicit-path freeze commit then ONE foreground CPU --mode preflight;
no trunk or gate unless all gold standing and retirement setup checks pass.

2026-09-06 — STATE: FOCUS-3 V3 COMPLETE / INELIGIBLE-ADMISSION; committing.
Freeze b6e40442 precedes only CPU setup pass;16/16 initial orders and16/16 tags
admitted, overrides0/4,new-task admissions0/4,cancellations0/4,completions0/4.
Retirement requirement0/8 mechanically stops before GPU;64 bank unevaluated.
240 pairs incl12 gold-positive with admitted targets; all applied-none, one
wrong reinstates proposal blocked on live target. New-task P(rule)>=.95 but
none-pair guard fails. No post-outcome source/bank/threshold changes or rerun.
96 records/16 traces/184 admission spans; runtime replay and independent raw
status/logit recount PASS;25 tests,1 legacy xfail,2 forbidden reads excluded.
19.306524 CPU update seconds,0/10800 GPU seconds,zero generations; no GPU claim
or flag required. check40h ended naturally; no fitting/sealed/signals/background/push.
RESULTS retains pre-written reading, summary/probe tables/records and README/
WORKLOG updated. Explicit-path force-added artifact commit is terminal for v3.

2026-09-06 — check40i WRITE-AHEAD: Z primary fresh-seed closure,40080/24.
User-authorized unregistered foreground check; archived PROTOCOL read; fit/train
none. Frozen40b JS/shuffle alpha3, profile/setup historical; new synthetic
expressions disjoint from40b/40d/40f/40h. No sealed/benchmark inputs read.
Conservative paired rule:>=20 SET+HOLD JS->SWITCH Python and>=20 BACK+HOLD JS
->CLEAR Python, in addition to literal20/2 and BACK controls<=4 thresholds.
Shared4-step Z/Zc/S prefix; all branches3-step tails; OFF full7:480 generations,
672 records; measured40h+25% projection1684.45/1800s. No lock owner/compute/flag
observed; pre-inference CPU consumer checks and explicit-path freeze next.
No wrappers/background/signals/push; Brian2705 never touched.

2026-09-06 — check40i CPU READY / PRE-INFERENCE FREEZE.
Native HF mask/position/bias tests and threshold boundaries PASS; full CPU dummy
writer->audit consumer PASS672 records/480 generations, CUDA uninitialized.
Inherited40h generator/scorer/cache/mask unchanged; only seed/arm schedule and
primary reading differ. All168 expressions disjoint incl40h; ruff/diff clean.
Next foreground scripts/focus_check40i.py --mode run, cap1800s, own flag under
review lock after resource recheck; no outcome retries/signals/sealed reads/push.

2026-09-06 — STATE: FOCUS-3 V4 CPU WRITE-AHEAD (gpt-6-astra).
User-authorized runtime-value/constant repair supersedes v3 stop; archived protocol
read for context, direct foreground task governs. No review/coder wrapper active;
check40i is a direct GPU runner, so scoped CPU work proceeds without GPU claim.
Fit/train none. Calibrate ONLY committed frozen GPU seed0 DEV predictions;
evaluate unchanged v3 wording with fresh lists30321 setup/30322 gate,16/64.
Register before calibration/inference: relation status passes through live,
superseded,cancelled,completed; scope global or task:<visible semantic task name>;
metadata key-only, semantic sort-order/tag (generic instruction otherwise).
Message is the entire current prose prefix before the Sort request/payload block,
retaining all prose sentences; payload-only spans generate no relation pairs.
prev_user is the last sentence of the previous user's prose prefix, or None;
it is not the entire previous message nor earlier sentences of this message.
Source span offsets remain original; pairs also carry exact end offsets.
Admission inputs/threshold.95 unchanged. None-pair threshold = NumPy linear90th
percentile of DEV gold-none P(none); if >5% DEV positives meet >=threshold use
linear95th. If95th still exceeds5%, report and stop ineligible, never retune.
Select highest proposed-label probability among same request-kind targets;
retain whole-task atomic completion rule and existing scope/status guards;
stable source order breaks equal-probability ties. No extra key/scope rescue.
Eligibility: all36 gold admissions plus >=11/12 correctly applied transitions
with exact gold source retirement/replacement state; no overflow;96 records.
Known three phrasings are present in inherited setup: disclose, never remove.
Gate endpoints/competence/cap unchanged (C/O/N/T,64,10800 GPU seconds); mechanical
setup failure stops GPU/gate. Brian pid2705 exempt from GPU readiness; no signals.
Enrichment: exact3 known misses +90 individually handwritten paraphrases for a
LATER refit only, explicitly evaluation-derived/development-only relatives; never
used by current classifier/calibration. This authorized exception does not make
these families eligible as independent future evaluation. No sealed inputs,
background launch or push; force-add artifacts, explicit-path commits only.

2026-09-06 — STATE: FOCUS-3 V4 CPU READY; FREEZE BEFORE SETUP.
DEV576-row committed-logit hash matches frozen manifest. Linear90th cutoff
0.9711621345086118:26/259 gold-none admitted,0/317 positives admitted;95th fallback
not selected (0.97256607268076,13/259,0/317). No weights/positive thresholds changed.
CPU parity/target/guard/stop tests PASS; actual dummy preflight writer->audit
consumer saves/replays96 records. Targeted suite31 passed/1 legacy inventory xfail,
plus new writer/audit test passed (32 total applicable);ruff/diff clean.
All3 known phrasing misses present in exact inherited authoring; only30321/30322
lists change.93-row handwritten enrichment quarantined for later refit, family
links and evaluation-derived provenance explicit; source templates not edited.
Pre-inference freeze includes source/model/DEV/bank/reading/enrichment hashes.
Next ONE foreground CPU preflight: CUDA_VISIBLE_DEVICES='' .venv/bin/python -u
-m scripts.focus3_gate_v4 --mode preflight. Log v4/preflight.log via pipefail.
If setup misses>1 transition or any of36 admissions, stop INELIGIBLE-ADMISSION;
otherwise wait for flags/other compute (pid2705 exempt), then foreground GPU run.
No sealed reads/fitting/signals/background/push; explicit-path local commit next.

2026-09-06 — STATE: FOCUS-3 V4 COMPLETE / INELIGIBLE-ADMISSION; COMMITTING.
Freeze c72a4d3d preceded one CPU setup replay. Correct-source transitions8/12
(required>=11):supersedes2/4,cancels3/4,completes3/4; all3 known phrasings retained
and missed, plus standing-order switch .726819<.94. Initial ordering16/16,
tags16/16,switched-task admissions0/4 =>32/36, so mechanical pre-gate stop.
DEV90th .9711621345086118 remains frozen; setup gold-none0/189 reach it (maximum
.969923617737972). 27 wrong positive proposals/19 applications:18 reinstates,
1 cancellation,8 episodes. Full request still feeds inherited scope parser;
conversation word can broaden continuation scope, observed wrong-task restore.
No outcome-driven repair, retune, bank edits or repeat inference.
96 records/16 traces/201 relation pairs/184 admission spans saved in same run;
frozen runtime/trainer-parity/raw-softmax replay and independent exact-source
recount both PASS.32 tests pass,1 legacy inventory xfail;ruff/diff clean.
93 evaluation-derived enrichment rows (3 originals+30 handwritten relatives each)
committed for later refit ONLY; frozen model lineage/weights unchanged.
CPU replay loop19.307595 wall seconds (historical cpu_seconds field is wall time);
GPU0/10800s,zero generations/gate records. Gate30322/64 unevaluated;check40i owns
its separate GPU job/flag;no GPU claim needed,no process touched. No sealed
reads/fitting/background/signals/push. RESULTS,README item,WORKLOG and all raw
artifacts land with explicit force-added paths; authorized v4 stop is terminal.

2026-09-06 — STATE: FOCUS-3 V5 STEP A WRITE-AHEAD. User CPU-only task governs;
archived protocol read, no wrapper lock held. Seven rulings/DEV review tables
registered in v5/RESULTS.md before tests/replay. Fit-on unchanged v4 pool;
evaluate-on committed v4 setup only. C fixed .94/.50/.50/.50; C-prime .80 later
only. Global overlap remains in none guard; report residual failures without
rescue. Delete only three verbatim enrichment rows; Kimi transitions untouched.
Implement CPU parity, replay once, audit, explicit-path commit; no GPU, sealed/
bench reads, fitting, signals, background launches or push. Stop after step A.

2026-09-06 — STATE: V5 CPU INFERENCE COMPLETE; IMPLEMENTATION CORRECTION.
First replay33/36 admissions,8/12 transitions,13 unauthorized actions. Audit PASS
for saved runtime/softmax/DEV parity but inspection found task-switch guard used
payload-concatenated admission span, violating ruling3. Preserve original run,
freeze and sources under v5/implementation-diagnostic; correct switch recognition
to relation prose prefix. Prewritten implementation-correction.md binds next
CPU saved-probability replay: exact same inputs required, no new model inference.
Expected effect limited to final-turn switches; no policy/bank/threshold change.

2026-09-06 — STATE: FOCUS-3 V5 STEP A COMPLETE / INELIGIBLE; FINAL COMMIT.
Final saved-score CPU replay33/36 admissions,8/12 transitions,2 unauthorized/96;
reinstates0. Supersedes2/4 fails per-label floor; cancels/completes3/4 each.
Three admissions still vetoed by overlapping global-tag none probabilities;
quoted inert text yields false admit+cancel. No further policy repair/refit/gate.
Single CPU inference at1780f5b9 retained as implementation-diagnostic; correction
037c7efb obeys task-switch ruling on prose prefix, recomputes only11 final-turn
states from identical stored predictions with exact input assertions.96 records,
16 traces,156 pairs,184 spans audited; independent counter/state checks PASS.
53 tests pass,1 existing xfail;ruff/diff clean.Three verbatim bank rows deleted;
90 relatives quarantined,Kimi untouched.No GPU,sealed/bench reads,signals,push.
This scoped commit lands final RESULTS,README,WORKLOG and force-added evidence.
No next command: stop at authorized step A; step B awaits enrichment review.

2026-09-06 — STATE: FOCUS-3 V6 STEP B WRITE-AHEAD, BEFORE FITTING.
User authorizes clean enriched refit0/1/2 GPU3epochs, DEV5% primary/10% supersedes
secondary, heldout2 SECOND LOOK, CPU setup then conditional gate. Archived
protocol read for context; direct user task governs, no wrappers active.
Lineage: fit patched original + reviewed transitions + opus2 +90 astra2
(evaluation-derived, never independent test); calibrate scenario-disjoint DEV;
evaluate heldout2 diagnostic then setup30321, conditional gate30322. No benches.
Rulings in v6/RESULTS.md before fitting: mechanical exact span repair/drop,
status drop, IDs/grouping, full-model-input dedup preserves status minimal pairs,
positive-proposal admission bound before applicability filters. Admission head
unchanged: relation negatives cannot directly repair false quoted admissions.
GPU/flags currently empty. No process signals/background/push; scoped commits.

2026-09-06 — STATE: V6 CPU READY / PRE-FIT FREEZE.
7749 effective pairs: none3259/supersedes1521/cancels1038/completes1024/reinstates907.
Merged+transition patches drop123/relabel225; additional mechanical drops2
nonverbatim targets+1invalid status. Repair68starts/1202ends, normalize110objects;
0full-input dedup removals, status minimal pair retained. Each6974fit/775DEV,
all scenario/message/relative links disjoint. Seed0's90Astra2 rows all DEV;
seed1/2 each30fit/60DEV under unchanged splitter, disclosed before fitting.
92 targeted tests pass,1existing xfail; consumer tests cover exact proposal
boundary, ignored-reinstates veto, C' runtime, one-shot96-record writer and
ineligible gate refusal. Source/reading/input/ft/bank hashes frozen pre-fit.
Next foreground .venv/bin/python -u -m scripts.focus3_gate_v6 --mode fit,
seeds0/1/2, no heldout/setup outcomes yet; own flag, no PID exceptions/signals.

2026-09-06 — STATE: V6 ALL THREE SEEDS FROZEN; SECOND LOOK NEXT.
Each654/654updates,3epochs,zero overflow; total GPU-held195.999037s.
Primary supersedes cutoffs .90/.82/.88; C-prime .50/.50/.60; other3 .50.
Primary DEV correct-positive414/425/418 of449; none-FP30/30/34 of326,
per-class caps verified. Seed0 remains predetermined. Natural exit, flag removed.
Next commit freezes all checkpoints/hashes/calibration; then one CPU command
CUDA_VISIBLE_DEVICES=empty .venv/bin/python -m scripts.focus3_gate_v6
--mode second-look. Durable SECOND LOOK receipt before heldout2 open, no tuning.

2026-09-06 — STATE: V6 DISCLOSED SECOND LOOK COMPLETE; CPU REPLAY NEXT.
Freeze54e09f25 preceded one new357-pair CPU inference with durable look2 receipt.
Primary343/357 accuracy,201/206 correct-positive,9/151 none-FP; vs first look
+6correct overall,+5positive,-1none-FP. Diagnostic only; no policy/model changes.
Raw357 records written in same inference pass; identities match first-look inputs.
Next ONE CPU pre-gate replay --mode replay; required36/36,>=11/12,0unauthorized.

2026-09-06 — STATE: V6 STEP B COMPLETE / INELIGIBLE; FINAL COMMIT.
CPU setup35/36 admissions,11/12 transitions: supersedes3/4,cancels4/4,completes4/4;
all three prior named misses pass, standing-order switch .570806<.90 remains.
Two unauthorized actions: quoted-sample admission(P(rule).960425), and new-task
ordering supersedes global tag key(P(supersedes).949289), missing one new-key
admission. Mechanical stop: no O setup, no trunk/gate/C-prime trajectories.
One inference pass96records/16traces/165pairs/184spans, zero overflow. Runtime,
trainer-input, softmax, full-data/split/calibration and second-look saved-logit
audit PASS. Independent saved-record audit accounts48 actions/40new rows/
11status changes, zero unexplained mutations. Legacy P(none)>=.50 diagnostic
field identified explicitly; actual bound124/153 none pairs pass no-proposal.
92 targeted tests pass,1existing xfail;lint/diff checks clean. Artifacts/report/
README/WORKLOG/model evaluation metadata ready; registration prefix and frozen
model/source hashes unchanged. User input corpora and historical models unchanged.
195.999037/10800 GPU-held seconds; own flag absent, no signals/background/sealed/
bench reads/push. Explicit-path force-added commit closes step B at required stop.

2026-09-06 — STATE: V7 STEP C REGISTERED, IMPLEMENTATION NEXT.
Archived protocol/science and current ledger read; direct user quick-check scope
applies, no wrapper active. Fit original admission lineage + source quoted NONE;
DEV sentence-group disjoint; fable-validation* diagnostic once after freeze;
never gate-bank fit, benchmark/sealed reads. Register key slug identity before
precedence, cross-key dropped also excluded from admission veto. Seed0 fixed,
3epochs/3seeds, .95 admission fixed, no relation refit/second look. v7/RESULTS.md
freezes inherited stop/readings and 10800s budget. No signals/background/push.

2026-09-06 — STATE: V7 RECIPE FROZEN, GPU REFIT NEXT.
61 targeted CPU tests pass. Original20054 rows reproduced;150Opus+61transition+
273relation messages yield582 sentence negatives; final20634rows after2dedup,
zero gate-sentence exclusions. Seeds each18571fit/2063DEV, sentence identities
cannot cross. Training tokenization preflight passes with unchanged192 recipe.
Original282 taxonomy-category drop exceptions preserved/disclosed per ft lineage.
Next foreground .venv/bin/python -u -m scripts.focus3_gate_v7 --mode fit;
3full epochs per seed, seed0 fixed, no heldout input read. No flags/compute now;
claim helper exempts only Brian2705, never signals, saves elapsed in finally.

2026-09-06 — STATE: V7 PRE-REPLAY RUNTIME CORRECTION, FIT UNCHANGED.
Consumer code audit found semantic storage keys would change cross-task version
counts, violating inherited renderer/register semantics. Retain original keys;
keep a separate provenance-ID-to-semantic-slug map. Synthetic version regression
added before any heldout/setup/gate score. Original recipe receipt retained;
new receipt changes only runtime, v7 audit consumer and tests. Seed fitting/data/
thresholds unchanged. Loader audit qualifies earlier 'reproduced' claim: pinned
six manifest admission patches yield20054, present broad historical script glob
also loads later relation patches (20069). This is ft lineage, not verified
historical row-byte reconstruction; correction receipt documents distinction.

2026-09-06 — STATE: V7 THREE ADMISSION SEEDS FROZEN; FABLE EVALUATION NEXT.
All3epochs/1743updates per seed; DEV1954/1959/1961 of2063 correct; .95 admissions
seed0 709/765rules,16/1298nonrules; seed1 733/784,12/1279; seed2 703/757,8/1306.
Seed0 unchanged designation. No heldout/setup outcomes read; GPU run exited
naturally and removed its flag. Freeze binds all checkpoint/DEV metadata hashes.
62 targeted CPU tests pass. Next one CPU evaluate on fable-validation* with
same-pass original-ft comparator, then ONE CPU setup replay and mechanical stop.

2026-09-06 — STATE: V7 FABLE PREFLIGHT ABORTED UNSCORED; RESUME NEXT.
Exactly one generic sentence collision: Thanks, that fixed it. Kimi has empty
context; Fable has preceding debugging reply. Different full paired inputs and
authors. No classifier loaded/inference made in aborted attempt. Preserve start
receipt/log and pre-evaluation freezes; evaluation-only correction requires
full-input disjointness, reports sentence collision, adds durable inference-start
repeat guard. No row/model/threshold changes. Next resume one unscored evaluation.

2026-09-06 — STATE: V7 FABLE INFERENCE COMPLETE; ONE CPU REPLAY NEXT.
One363-row pass per model after one unscored preflight. Original315/363 matches
historical metrics; ft-v2 318/363 (+0.8264pp). Fixed.95 rule admissions114→111
of124; nonrule admissions9→5 of239. Same labels/data, no tuning. Full model inputs
and authors disjoint; one generic sentence-only collision disclosed. Next replay,
required36/36admissions,>=11/12transitions,0unauthorized/overflow, else stop.

2026-09-06 — STATE: V7 STEP C COMPLETE / INELIGIBLE; FINAL COMMIT.
OneCPU replay36/36admissions,11/12transitions,19unauthorized(14admit/4reinstate/
1complete);10cross-key positives dropped, specific new-task admission repaired.
Quoted sample remains falsely admitted(.978070);10one-shot sort requests and
4inert quotes admitted,4generic requests reinstate cancelled rows,1extra false
row completed. No correction/tuning/replay after outcome; stop before trunk/O/gate.
96records/16traces/229pairs/184spans;0overflow. Saved runtime/split/DEV/Fable audit
and independent softmax/trainer/action-state accounting PASS(66actions,57newrows,
12statuschanges,0unexplained).96targeted tests pass,1existing xfail;lint/diff clean.
264.589652GPUseconds; own flag absent. All requested reports/metadata/raw records
force-added with explicit paths, safetensors excluded, no signals/bench/sealed
reads/background/push. No next GPU command; committed INELIGIBLE closes step C.

2026-09-06 — STATE: V8 STEP D REGISTERED; LAST ITERATION, IMPLEMENTATION NEXT.
Direct user scope governs archived protocol; no wrapper holds review lock.
Fit-on v7 committed corpus + hand-written request NONE/standing-rule enrichment;
DEV sentence-group disjoint; evaluate-on author-disjoint Fable once after freeze.
No bench/sealed reads. v8/RESULTS.md freezes three rulings and inherited bars.
V7 four reinstatements verified from saved traces: instruction key borrowed
sort-order target; all four pass .95 admission and .50 relation thresholds.
Extra completion is same-task inert pollution; scope-only fix cannot guarantee
its removal. No unauthorized quote veto. Stop after one failed CPU replay and
prepare escalation; no next iteration. Foreground only, never signal, no push.

2026-09-06 — STATE: V8 RECIPE FROZEN; FOREGROUND REFIT NEXT.
Hand-wrote300 unique JSONL rows:200NONE/100STANDING,10domains; no script-created
example content. Inline/escaped payloads and nearby multiline code/CSV contexts
preserve single runtime-sentence targets. Corpus20934 (v7 exact20634 +300), zero
exclusions; seed splits18841/2093,18840/2094,18841/2093. Existing282 historical
patch exceptions unchanged. Tokenizer preflight PASS;122CPU tests pass/1existing
xfail;14new lifecycle failures observed before implementation, now pass.
V8 flag preserves old consumers; completion filters scope before precedence;
reinstatement requires own admitted key and cancelled/completed status, no
embedded-text bypass, conservative cancellation veto. v7 measured264.59s for
three seeds on20634rows projects about268.44s for20934rows, GPU-minutes within
10800s cap; no new pilot/model selection. Recipe and source hashes frozen before
any fitting/heldout scores. Next .venv/bin/python -u -m scripts.focus3_gate_v8
--mode fit, foreground flag-coordinated/no signals. CPU query no compute/flags.

2026-09-06 — STATE: V8 THREE SEEDS FROZEN; ONE FABLE DIAGNOSTIC NEXT.
All three final checkpoints saved after3epochs/1767updates; seed0 fixed.
DEV correct1989/2093,1977/2094,1985/2093; rule admissions668/719,719/773,722/763;
nonrule18/1374,11/1321,16/1330. New-family NONE admissions0/21,0/20,0/18;
standing positives7/8,7/7,7/7. Small DEV family support is disclosed.
Freeze verifies all model/data hashes; fit exited naturally, own flag removed.
Next one CPU Fable inference on seed0 only; v7 ft-v2 comparator reuses committed
raw logits after exact input-row/file-hash verification. No prior heldout reads
in this v8 task, no threshold/seed selection, no new relation heldout evaluation.

2026-09-06 — STATE: V8 FABLE DIAGNOSTIC COMPLETE; ONE CPU REPLAY NEXT.
One363-row ft-v3 seed0 inference after freeze; comparison uses identical-row
committed v7 logits. Accuracy318/363 (87.6033%), unchanged fromft-v2; rule
admissions111/124 unchanged; nonrule admissions5→8/239 (+3). Existing generic
sentence collision has different context; zero full-input overlap and authors
disjoint. No extra heldout/model inference or tuning. Fit269.749111GPU seconds.
Next CPU-only setup replay:36/36,>=11/12,0unauthorized/overflow or INELIGIBLE STOP.
