# Relation classifier task ledger

2026-09-06 — STATE: CHECK44C COMPLETE / NO-GO. Seed0 C2 and frozen C2+B
heldout3 overlap247/385=64.16%<85%; quoted2/36=5.56%>3%; payload0/57,
non-user0/34. SETUP36/36 admits but10/96 false turns>2;4 request-template
admits,3/4 supersedes. Token-run ceiling100%, B adds0. Explicit entry stays
first ship; no runtime swap/gatev9. Freeze fd43ff8f; GPU88.546/3600s;
783 records/1398 DEV records audited, no pending inference. Audit-only
JSON tuple/list repair preserves frozen runner and all science-function ASTs.


2026-09-06 — STATE: CHECK44B COMPLETE / NO-GO. Seed0 C overlap151/207=72.95%
<85%; negative FP0/97 payload,0/57 quoted,0/30 non-user; SETUP2/96 false turns,
0/96 request-template admits. No runtime swap or gatev9 authorization; explicit
first-ship structured entry, C assistive only. All requested artifacts and final
reports land in the completion commit; no further inference pending.

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

2026-09-06 — STATE: V8 CPU INELIGIBLE; STOP-LOSS APPLIED, AUDIT/ESCALATION NEXT.
Single CPU replay36/36admissions,11/12transitions,12unauthorized in12records:
11admit (8payload requests/3inert quotes),1same-task polluted-row completion;
0reinstatements. V7 unauthorized19→12; no safety pass.96records/16traces saved.
No trunk/O setup/gate/C' execution, corrective replay, tuning or next iteration.
User's final-iteration stop closes the gate for Brian escalation; only saved-data
audits and requested reporting/artifact commits remain. GPU269.749111s;
CPU16.508058s. No signals/background/bench/sealed reads/push.

2026-09-06 — STATE: V8 STEP D COMPLETE / INELIGIBLE; FINAL ITERATION STOPPED.
All authorized fitting/evaluation/replay work completed; CPU36/36admissions,
11/12transitions,12unauthorized (8payload/3quote admissions +1same-task complete),
0reinstatements/overflow. Required zero-unauthorized bar fails; no GPU gate or
further iteration. Escalation for Brian is in v8/ESCALATION.md with full evidence.
Both saved-data audits pass:96records,16traces,59actions,50new rows,12status
changes,214pairs,184admission spans,zero unexplained mutations. Observer-only
repairs and initial logs preserved; frozen recipe/models verified unchanged.
122targeted tests pass/1existing xfail; final import check3pass/1same xfail; lint
and diff clean. Models/source/data counts and unchanged v7 results verified in
validation.json.269.749111GPU seconds,16.508058CPU replay seconds; own flag absent.
All requested outputs, raw records, reports and metadata are force-staged for
this explicit-path final commit; safetensors local/hash-bound per registration.
No pending launch, inference, tuning or repair; Brian escalation is the next
program decision. No signals, termination, background jobs, bench/sealed reads,
external messages or push. Post-commit membership/byte verification follows.

2026-09-06 — STATE: FOCUS-3 V8 DIAGNOSTIC WRITE-AHEAD.
Direct user authorizes ONE five-arm seed30322 diagnostic despite12unauthorized
v8 CPU actions, no eligibility/PASS/FAIL claim. Archived PROTOCOL read; no wrapper
holds .review.lock. diag/RESULTS.md registers exact disclaimer before inference.
Fit/train/tune NONE; frozen relation-v2/ft-v3 seed0 and v8 runtime unchanged;
evaluate committed development bank only, no bench/sealed reads. Implement
isolated runner with same g.run_episode consumer, v3 descriptive readings and
per-false-admission conditional render-removal probes. Fresh7200s GPU cap;
post-O resource-only64/48 decision; foreground, own flag, never signal, no push.

2026-09-06 — STATE: FOCUS-3 DIAGNOSTIC FROZEN; O SETUP NEXT.
Isolated runner uses unchanged v8.classifier and g.run_episode; adds only
observation/readings and post-gate current-row removal probes.27targeted tests
pass/1existing xfail; lint clean. Sources, trunk and both seed0 checkpoint hashes
frozen; inherited trunk verified against original gate freeze. No GPU inference
yet. Next foreground command: .venv/bin/python -u -m scripts.focus3_gate_diag
--mode run, raw log diag/run.log. O16 competence descriptive; then resource-only
64/48 selection before gate. No new fitting or benchmark access.

2026-09-06 — STATE: FOCUS-3 DIAGNOSTIC O SETUP COMPLETE; FULL64 RUNNING.
O16/16 final success, descriptive only.182.916521s elapsed; slowest O9.843532s.
Registered projection64=4924.217873s (gate3937.412888s +392probe allowance
803.888465s +elapsed), below7170s.48projection3738.892535s not selected.
selection.json written before gate inference; full64 seed30322 x5arms launched.
Prior v8 eligibility unchanged. Foreground session, diag/RUNNING.flag owned;
no process signals, no new fitting, no benchmark/sealed reads, no push.

2026-09-06 — STATE: CHECK44 ADMISSION QUICK TEST WRITE-AHEAD.
Direct user authorizes frozen1.7B extractor vs ft-v3 message-wise head, optional
Kimi detector if1500rows at arm construction; fresh24Astra DEV, held-out338Fable
one look after recipe freeze. Fit-on A/B=none; demo/timing-on=fresh Astra only;
evaluated-on=reserved Fable admission, no bench/sealed reads. Archived governing
protocol/PLAN and current STATE read; no wrapper lock. User quick bar supersedes
memo800-message deeper gate: overlap recall>=.85, payload/quote FPR<=.03 each,
non-user false admissions0; failure cuts unattended first-ship admission.
Implement isolated script/validator, preserve raw JSON, source offsets, all
rejections; B head and unchanged register consumer reported separately because
its task binding is specialized. A keys NEW/opaque; do not claim semantic slug
accuracy. GPU diagnostic flag active; CPU preparation only, then foreground
exclusive flag and5400s cooperative cap, never signal any process; no push.

2026-09-06 — STATE: DIAGNOSTIC OVERRIDE FAMILY CHECKPOINT; RUN CONTINUES.
All480 override records (16episodes x5arms x6turns) complete, checkpointing
immutable records/traces while cancellation runs. Override C exact6/16,
final12/16, stale4/16, false retirement4/16, false admissions6actions;
C' exact7/16, final13/16, stale3/16; O/T final16/16 and stale0/16.
These are descriptive family readings; causal current-render probes pending.
No threshold/runtime change, no full-gate decision. All96 new setup candidate
traces exactly equal committed v8 CPU traces (setup-runtime-parity.json).

2026-09-06 — STATE: CHECK44 RECIPE FROZEN, CPU TIMING NEXT; HELD-OUT UNOPENED.
24original Astra DEV/six fixed demos; CPU grammar and actual v8 consumer smoke
pass; provenance/matching/binomial-bound selftests pass. C eligibility checked
at arm construction:870Kimi rows<1500, skipped and frozen before any evaluation.
A uses NEW/opaque keys, evidence validator, strict JSON; B head plus unchanged
register-consumer diagnostic. CPU timing fp32/4threads/24DEV/1800s boundary cap
runs while diagnostic holds GPU; no CPU outcome selects prompt. GPU A bf16
onepass remains5400s cap, resource-only projection before source held-out read.
No package-wide monkeypatch: direct LMFE tokenizer adapter passes both empty
and rule JSON paths; legal merged string-ending tokens can be overrestricted
by LMFE, recorded in cpu-smoke.json. Frozen recipe is committed before inference.

2026-09-06 — STATE: DIAGNOSTIC CANCELLATION CHECKPOINT; HALF GATE COMPLETE.
All480 cancellation records complete; first32episodes/960gate records now
finished. C/C' cancel exact11/16, final14/16, stale2/16, false retirement1/16,
contradictory1/16, breakage0; each6unauthorized admissions. O final16/16,
stale1/16; T final0/16, stale16/16; N final0/16, stale14/16, breakage1/16.
No outcome selection or repair. Completion-and-move-on family now running;
conditional rendering probes remain after allfive arms. Descriptive only.

2026-09-06 — STATE: DIAGNOSTIC COMPLETION CHECKPOINT; THREE FAMILIES COMPLETE.
All480 completion-and-move-on records complete; first48episodes/1440gate
records finished. C/C' exact10/16, final15/16, stale1/16, false retirement0,
contradictory2/16, breakage0; each8false admissions +2unauthorized completions.
O final15/16, stale1/16; N/T final0/16, stale16/16. Final switch-and-return
family running. No scientific/runtime change; conditional probes still pending.

2026-09-06 — STATE: CHECK44 CPU TIMING CAPPED; WAITING FOR DIAGNOSTIC GPU.
Frozen fp32/four-thread CPU timing reached1800s boundary cap:20complete DEV
messages plus21st partial raw output, preserved; no prompt/recipe selection.
CPU timing is INCOMPLETE/COST, not a semantic result. All sampled prompts exceed
1024tokens; that CPU ship-latency stratum is unmeasured. Required GPU24DEV and
338Fable one-shot evaluation remain unrun; source held-out unopened. Commit
CPU records/timing/log now, then foreground waiter for all GPU flags to clear.
No signals, no background process, no fitting, no push; C remains frozen skipped.

2026-09-06 — STATE: DIAGNOSTIC ALL64 FIVE ARMS COMPLETE; 220 PROBES RUNNING.
All1920gate records/320traces saved. Pooled C exact38/64, final57/64, stale7/64,
false retirement8/64, false admission21/64episodes (25actions:20payload/5quotes),
contradictory5/64, breakage0. C' exact32/64, final58/64, stale6/64, false
retirement14/64, same25false admissions and5contradictory;7extra unauthorized
supersedes plus2unauthorized completions vs C's2unauthorized completions.
O final63/64, stale2/64; T final31/64, stale32/64; N final29/64, stale33/64,
breakage1/64. C-minus-O final=-6, stale=+5; C-minus-T final=+26, stale=-25.
Switch-and-return C/C'/O/N final16/16, T15/16; candidate exact11/16 vs4/16.
These are descriptive readings, no gate label. Exactly110exposed row-turns per
candidate arm (220total) now probed using fixed original histories. Snapshot
full main-arm records and summary before probes finish; no rerun or fitting.

2026-09-06 — STATE: CHECK44 GPU ALLOCATED; FROZEN24DEV RUNNING.
Diagnostic released its flag naturally; no other compute process at allocation.
Own check44 flag acquired, pid754171, run-start receipt precedes model loading.
Recipe hashes verified unchanged; first GPU DEV outputs0.25–4.88s. No prompt
revision or fitting; source held-out remains gated on completed24DEV and frozen
elapsed+1.25*338*slowest projection.5400s GPU cap; foreground only, never signal.

2026-09-06 — STATE: DIAGNOSTIC GPU COMPLETE; SAVED-RECORD AUDITS VERIFIED.
Foreground process exited naturally:4099.336234s (68.322271min/1.1387056GPU-h),
peakTorch8956313600bytes; all1920gate +96setup +220probe generations complete.
Ownflag removed. Eacharm25false rows(20payload/5quote),110exposures,11semantic/
text/token changes,9score changes,7rows with semantic effect. Success removal
changes5false->true and3true->false; stale1false->true/4true->false; no tag or
breakage changes. Later-turn exposures9/85semanticchanges vs2/25on admission
turn. Quote probes0/10changes; payload11/100 in each arm. These are conditional
current-render effects preserving original history, not total de-admission cost.
Runtime audit replays1920records, recomputes metrics/probe scores and verifies
frozen hashes. Independent calculation verifies2236prompt/output sequences,
3389rawsoftmax vectors, O/N/T rendering, trace identity and resource choice.
No inference in either audit; both complete without correction. All96setup
candidate traces exactly match committed v8 CPU traces. Reporting/final commit
next; no further inference or model changes, no signals or push.

2026-09-06 — STATE: FOCUS-3 DIAGNOSTIC COMPLETE; FINAL ARTIFACT COMMIT.
All requested five-arm and per-admission readings are reported in diag/RESULTS.md;
README item and WORKLOG complete.220probes,1920gate/96setup records,320gate/
16setup traces;50arm-specific false-admission cases fully documented. No missing
work, no gate label, no pending inference.4099.336234/7200GPU seconds, ownflag
absent;27targeted tests/1existing xfail, both saved-data audits and lint verified.
Force-stage only named diagnostic/report paths; manifest binds every diagnostic
leaf except itself. Post-commit HEAD-blob and tracked-membership verification
follows. Prior results and unrelated files preserved; never signalled, no push.

2026-09-06 — STATE: CHECK44 HEADER-ONLY REPAIR; ZERO HELD-OUT PREDICTIONS.
Initial loader counted339JSON objects instead of338messages: author summary
header is the extra object.24GPU DEV complete, conservative projection3264.883s;
preflight INVALID count assertion,83.269454GPU seconds, zero held-out predictions.
Original script/receipt/DEV/log/summary preserved in check44/preflight-v1. Inspect
header/schema only; no message wording/outcome guides repair. New loader skips
exactly one summary header; synthetic consumer tests and existing selftests/lint
pass. Guarded resume reuses DEV, same weights/prompt/schema/GO, carries prior83.27s
into5400s budget. Source bytes reopened for metadata diagnosis, disclosed; still
one prediction pass. Repair receipt committed pre-prediction; C still skipped.

2026-09-06 — STATE: CHECK44 ONE HELD-OUT PREDICTION PASS RUNNING.
Header repair39731964 committed before inference; same338messages and all gold
span offsets validate. Resume uses saved24DEV with unchanged prompt/schema/
weights/thresholds/GO; total GPU charge includes failed preflight83.269454s.
Evaluation-start and resume-start receipts saved before first prediction; source
bank snapshot preserved. No held-out-driven fit, threshold/prompt revision or
repeat prediction. Foreground ownflag only; no signals or push.

2026-09-06 — STATE: CHECK44 COMPLETE, OPERATIONAL NO-GO; DECODER-LIMITED.
338 messages/218 gold spans predicted once; A overlap6/218(2.75%), precision6/16;
payload8/102,quote0/52,non-user0/12. B head175/218(80.28%),precision175/178;
payload2/102,quote1/52; unchanged unbound runtime writes0. C skipped at original
870-row eligibility. Explicit structured rule entry for first ship; no deeper bank.
289A provenance rejections dominate:275/314 text fields have apostrophe/comma/
space suffix. Model-free audit reproduces exclusion of legal merged closing
JSON token; valid JSON did not preserve evidence. Semantic model comparison is
confounded, not proof of underlying LLM inability. No decoder/output rescue.
Original recipe242140fb; header-only repair39731964 before held-out predictions,
reused24DEV and charged83.269454s failed preflight. TotalGPU1084.248915s<5400;
CPUtiming1801.005s boundary stop,20complete+1partial, no <=1024-token support.
338record scores/validators, prompt hashes/tokens, raw output decoding, source/
package hashes and100/200 checkpoints audited; scope/key limits disclosed.
Own flag absent; no fitting, benchmark/sealed reads, signals, background launches
or push. Final explicit-path artifact/README/WORKLOG commit and membership check
next; no further inference, threshold/prompt selection or bank authoring.

2026-09-06 — STATE: CHECK44B REGISTERING, heldout-2 unopened/uncommitted.
User's new GPU/foreground/no-signals brief supersedes prior task CPU limits;
archive protocol is historical. No .review.lock or other Stencil flag/process.
Fit-on = patched Kimi admission + Opus admission enrichment; DEV = 2/20 whole
source domains, Random(0), same split all seeds; evaluated-on = new Fable-2 once.
No scenario IDs: whole-domain grouping conservatively retains all matched pairs
and source batches together. Patch drop removes rules, not negative examples,
consistent with audited counts. Seed0 designated; seeds1/2 DEV stability only.
Frozen splitter, 512-token full-message/candidate pairs, overflow abstention;
GO/threshold/resource rules prewritten in check44b/README.md. No benchmark reads.
2026-09-06 — CHECK44B PRE-FIT VALIDATION: six focused tests + scoped lint PASS;
real CPU base-model smoke verifies pair encoding, overflow abstention and role
veto. Corpus 3103 messages/1493 spans; fit2794/dev309 (9.958% messages),
DEV183 gold-empty messages allow at most3 false admits. Frozen splitter overlap
ceiling fit1281/1346=95.17%, DEV141/147=95.92%; no splitter changes.

2026-09-06 — CHECK44B GPU PILOT: {"updates": 10, "seconds": 1.4120142249958008, "updates_per_second": 7.0820816270669935, "peak_allocated_GiB": 2.2502660751342773, "projected_total_seconds": 498.2467971894104, "cap_seconds": 3600}.
Continue matrix only if within cap.

2026-09-06 — STATE: CHECK44B ALL MODELS FROZEN, heldout-2 unopened.
GPU allocation 212.346/3600s; three complete seeds, own flag removed.
DEV overlap recall seed0 135/147, seeds1/2 138/147; each 3/183 negative FP.
Thresholds .9883976740722434/.9768228882950498/.956549283252651, seed0 designated.
All DEV scores/thresholds replayed from saved records; no extra inference.
Next: commit model-freeze and metadata, poll Fable-2 commit every five minutes.

2026-09-06 — STATE: CHECK40G CPU READY; foreground one-load GPU run next.
User's explicit quick-check40g brief/addition governs; prior protocol/PLAN archived.
Data lineage: fit/train none; profile committed40e competence replies + fresh
SQL/Go synthetic competence; evaluate reused40e TS16 (disclosed), disjoint new
SQL/Go32 and Go release24. No benchmark/sealed inputs read. Frozen prewritten
reading includes literal20/32 generality bars; TS16 diagnostics cannot establish
GENERALIZES. JS control<6/8 => INVALID immediate stop. Go Python16/16,
Go>=14/16 competence; SET>=20/32 <=2 absolute breaks triggers exact40i Z/Zc/S/OFF.
Go official tarball installed under $HOME, SHA256 verified; gofmt/go vet CPU PASS.
288 canonical checker cases, negative cases, dispatch consumer and decision tests
PASS. No flags or other GPU users observed; never signal. Cap3600s including load,
profiles/checkers/cleanup; fixed counts, cooperative deadline; no wrapper edits.
Next: .venv/bin/python /home/bmarti44/stencil-llm/scripts/focus_check40g.py run

2026-09-06 — CHECK44B FINAL AUDIT: Fable-2 commit2b3cfc74 discovered by the
third five-minute poll, after model-freeze bab43b0d. Evaluated once:330 new
held-out +96 SETUP messages, C and B on CPU/four threads. Frozen recipe/weights
unchanged. Exact/overlap/macro/family CP/CPU latency recorded; all426 records and
852 predictions independently recounted without model calls. Frozen splitter
ceiling176/207=85.02%, C adds25 misses; no rescue. GPU212.346/3600s, six focused
tests+CPU smoke pass. All tracked artifact hashes verified at completion; local
safetensors ignored. No signals, benchmark/sealed reads, background job or push.
Final lock check: .review.lock belongs to foreground focus_check40g.py GPU
run, not a review/coder wrapper; source inspection shows no workspace restorer.
No process/lock touched; check44b completion commit uses explicit own pathspecs.

2026-09-06 — STATE: CHECK40G COMPLETE AS INVALID; no further GPU work authorized by its failed gate.
Frozen JS alpha3 in40e harness: JS3/8, Python5/8, broken0; <6/8 stops TS/SQL/Go
and conditional release. No new competence or profiling ran. Overall generality
beyond Python/JS unknown. Exact40e input tokens and independent40c scorer8/8;
all48-layer dispatch/bias hashes verified, zero consumer mismatches. CPU Go
installation/gofmt/go vet passed. Allocation396.984/3600s,8 generations/219tokens;
foreground raw exit0, own flag removed, no signals/sealed reads/fit/train/push.
Artifacts, five-line index and six-line WORKLOG audited; explicit-pathspec final commit follows.

2026-09-06 — STATE: CHECK40J REGISTERING, no GPU work yet.
User's quick-test-first brief governs; PLAN/PROTOCOL archived, current STATE read.
Fit-on nothing; evaluate16 fresh targets with96 fresh OFF history tasks, seed401006.
Literal requested Live rules sentence prepended; focus3.render uses JSON instead,
so copy placement only and disclose format discrepancy. No stronger cue invented.
Inherited40i CPU mask checks, executable controls, prompt parity and40g tensor hash
PASS. R1/R2/R3 and224 generations frozen before inference;2700s one-load cap.
Next commit recipe, then foreground .venv/bin/python scripts/focus_check40j.py run;
respect flags/review lock, never signal or push. No edits to untracked composition.

2026-09-06 — STATE: CHECK40J COMPLETE R1, no further GPU work.
Recipe3dddc28e before224 generations; literal rendered cue discrepancy prewritten.
P1 OFF/bias-only JS0/16, text-only/text+bias16/16; P2 every arm16/16, no breaks.
All96 retained OFF history answers executable Python; exact shared prefixes16/16.
Combined-vs-text wins0/losses0/ties16; conservative descriptive95% gain±23.96pp.
Rendering-only primary; actuator out of default shipping. Small screen, no enlargement.
827.221/2700GPU-seconds,6439 output tokens; natural exit0 and ownflag removed.
CPU inherited mask/scorer/prompt tests PASS; SciPy1.18.1 installed during load before
first generation after reporting smoke found it absent; synthetic reading bounds PASS.
All224 saved scores/tokens/cache/mask/bias records and17 recipe git blobs audited.
Report/index/WORKLOG ready; commit explicit paths, verify tracked artifact hashes;
no signals, fitting, benchmark reads, retries, unrelated-file edits or push.

2026-09-06 — STATE: CHECK44C CPU AUDIT / PRE-REGISTRATION, before fitting or
heldout-3 read. User check44c brief governs foreground direct implementation.
Fit-on=patched kimi admission + Opus enrich + Astra-audited kimi admission2;
evaluated-on=fresh heldout3 once after freeze; heldout2 secondary second look;
SETUP development-only. Audit122 changed/5 dropped. No scenario IDs: registered
whole domain/source-batch grouping to approximate10% DEV across>=6 domains;
within-batch integrity, cross-batch semantic relatives remain review limitation.
Seed0 C2+B primary; C2 alone secondary; fixed GO bars in check44c/README.md.

2026-09-06 — CHECK44C pilot: {"updates": 10, "seconds": 1.2594217840014608, "updates_per_second": 7.94015168471026, "projected_gpu_seconds": 269.6193079393735, "peak_GiB": 1.4938702583312988, "per_seed_timeout_seconds": 199.49241058583138}.

2026-09-06 — STATE: RELATIONS V3 PREPARATION, held-out-3 unopened.
Data lineage: fit-on = exact v2 patched Kimi relations/transitions + four enrich sets
(including disclosed 90 evaluation-derived Astra2 relatives) + Opus-patched,
offset-corrected Kimi overrides; calibrated-on = scenario-disjoint DEV only;
evaluated-on = fresh Fable held-out-3 once after committed freeze, held-out-2
secondary historical re-look, FOCUS-3 v2 SETUP diagnostic. No data/bench access.
Override audit indices 178,186,291,415,417,877,945 are fit-only (excluded from DEV);
source+zero-based-index identities, repeated messages grouped. Seed0 preselected;
seeds1/2 stability, exact v2 numerical recipe/C policy; 1800s GPU allocation cap.
Archived protocol applies as context; direct user task authorizes narrow refit.
No wrapper lock held; no signals, background launch or push. Next: prepare/freeze recipe.

2026-09-06 — STATE: RELATIONS V3 ALL CHECKPOINTS FROZEN, before heldout3 read.
Three full seeds /759 updates each; GPU264.772/1800s, own flag removed naturally.
Model/DEV/policy/evaluator hashes bind next commit; README prose explicitly mutable.
Next: one seed0 heldout3 inference, historical heldout2 secondary look, exact-v2 CPU runtime diagnostic; no fitting or selection afterward.

2026-09-06 — STATE: RELATIONS V3 COMPLETE / NO-GO. Heldout3 accuracy87.05%, supersedes recall73.26%; accuracy 0.870536 < .94; supersedes recall < .90; none F1 below v2 heldout2 minus .03; supersedes F1 below v2 heldout2 minus .03; completes F1 below v2 heldout2 minus .03. Secondary heldout295.24%; runtime11/12, 1 regressions. All records/hash/CP/runtime audits pass, GPU264.77/1800s; no inference pending. Explicit-path local completion commit; no push.

2026-09-06 — check40k WRITE-AHEAD: user-authorized fresh programming competence check. Archived PLAN/PROTOCOL and current STATE read; no wrapper lock active. Fit-on nothing; calibrate-on eight fresh DEV tasks; evaluate 32 disjoint authored tasks once, never benchmark data. 40 tasks/160 hidden Node tests authored and reference-validated. Fixed 40j alpha3 JS tensor, four paired arms, 768-token cap, one load/2700s. Exact sign arithmetic and R3-before-R2 overlap interpretation registered in README before GPU work. Explicit recipe commit before inference; DEV freeze commit before evaluation; no signals/push.

2026-09-06 — check40k COMPLETE / R3 HARM. DEV5/8 without revision;32 evaluation tasks once,128 generations. Text-only16/32, bias7/32, shuffled11/32; wins2/losses11/ties19,−28.125pp, conservative95%CI[−55.123,+6.226]pp, exact two-sided p=.022461. All11 losses valid unbroken JS; no default-on, actuator remains off/opt-in.136 records/160 tests, strict-return sensitivity unchanged, tokens/biases/freeze CPU-audited;1520.526/2700GPU-s, one load, flag removed, no signals/push. Final scoped local commit includes report/index/WORKLOG and forced-added artifacts.

2026-09-06 — check40l WRITE-AHEAD (gpt-6-astra): archived PLAN/PROTOCOL and STATE read; no wrapper active. User competence-only quick screen governs; ARM A cut per fable40k, R2 unreachable. Fit-on24 DEV replies (8 priorDEV+16 authored fresh;96 reference-validated hidden tests), evaluated-on same32 check40k tasks, second look disclosed, no selection. Unchanged harness hashes permit baseline reuse. Equal-reply centred logits, own non-EOS teacher-forced positions, per-layer norms1/3 and2/3 of40k; fixed larger-dose shuffle. >=6 pass/fail each else ineligible, no DEV revisions. Conservative R3 interpretation: both tested competence doses net harm>=3 (40k bar), scoped claim only; R1 first. CPU scorer/profile/reading checks and Ruff pass; one-load2700s foreground run after scoped recipe commit; no signals/push.

2026-09-06 — STATE: CHECK40L COMPLETE / R4. DEV15pass/9fail eligible; same32 second look,120 new generations, reused40k baseline. Success text/low/high/shuffle[16, 14, 13, 15]; 1/3 1/3/28; 2/3 3/6/23; shuffle 1/2/29. R2 unreachable, ARM A cut. INCONCLUSIVE. Neither competence dose meets the registered R1 reopening criterion, and harm does not persist at both tested competence doses under the frozen R3 bar. Keep the line parked; no enlargement or shipping change. CPU saved-record/profile audit passed;GPU1345.206/2700s; flag removed, no signals/push. Explicit-path completion commit next, no further GPU work.

2026-09-06 — composition-pilot WRITE-AHEAD: user-authorized Day 5 DEV GPU pilot, <=5400 GPU-held seconds, one load, no signals/push.
Archived protocol/current STATE read; no wrapper owns .review.lock. Fable r2 closes H1–H4; bank fix 35c546f4 re-froze fixtures.
Fit/train none; development-on authored DEV only, gold events for explicit R; no evaluation episode or data/bench access.
First repair N1 against last parsable snapshots (attempted and executed scoring), DEV regression, hash-only fixture re-freeze.
Freeze four-episode fallback before GPU with both shapes; measure batch4 versus sequential through package dispatch; actuator OFF.
2026-09-06 — composition-pilot CPU FREEZE: N1 DEV regression red->green;46 targeted tests pass,1 expected xfail;448 actual-HF-dispatch stub calls pass, including threaded batch4.
All committed DEV were16 rounds; user-required long shape authored for DEV06/07 (32, distinct reinstatement26); fallback00/01/06/07,then02/03/04/05 frozen before outcomes.
DEV manifests/accounting re-frozen; evaluation manifest hashes and prior accounting preserved without constructing/opening evaluation episodes. CPU total13.637h includes enlarged DEV.
Prewritten readings, source/runtime hashes and all16 trunk-shard SHA256s frozen in composition-pilot/recipe.json. Next: foreground scripts/composition_pilot.py --mode run, one load,5400s inclusive.
2026-09-06 — composition-pilot STATE: INELIGIBLE / INCOMPLETE, GPU work finished; no evaluation launch authorized by this result.
5385.346/5400 GPU-held seconds including322.758 load/cleanup, one load; RUNNING.flag removed, exit0, no signals. DEV00 sequential RNTO64 calls; batch64 diagnostic calls, last T deadline-interrupted at343 tokens.
Batch N/T differ all16 rounds (first mismatch round0); R/O match16/16. Frozen full comparison consumed remaining budget; no later episode/32-round GPU shape fit. No history/sample rescue.
Sequential nested20.794h>12, full4x64=37.180h; interrupted batch occupied-lane proxy>=49.583/78.381h, not a qualified full batch cost. All128 tool envelopes rejected; no edits or prior executed traits; main trunc10/64.
R first10 bodies in band; observed prompt max11050+512 fits, not a long-shape certificate. Language0/0 by design; style/format/process0/5,0/4,0/6 each; mask trigger not met.
CPU audit reproduces128 scores/executions/hashes/live views and256 hidden hashes;11 means explicitly partial. Exact R golden consumer replay passes;47 targeted tests+1 expected xfail, lint/diff checked.
Post-run edits affect only reporting/audit/golden test; inference bank/renderer/decoder/custom-entry match d1fb0660 recipe. No evaluation episode/bench reads or push. Final commit closes this bounded pilot; no further inference.

2026-09-06 — STATE: CHECK45 COMPLETE / R4 INSUFFICIENT DATA. User's eligibility stop governs; archived PLAN/PROTOCOL context read (root PLAN and plan/PROTOCOL absent), current STATE read; no wrapper lock held.
Pilot README explicitly INELIGIBLE/INCOMPLETE: stop before labels/hidden states/fitting. Source reports128 calls from DEV00, also below150; >=25 violation gate not assessed.
Planned fit-on DEV pilot only; evaluated-on held-out DEV episodes by fold. Actual input pilot README only; no benchmark/evaluation-bank reads, model/GPU, signals or push.
CPU gate script emits source/script hashes, zero-fold records and empty weight manifest. No metrics or meter; R1–R3 not evaluated. Scoped result/index/WORKLOG/script commit closes task.

2026-09-06 — STATE: DAY5B CPU AMENDMENT REGISTERED BEFORE CODE.
User's explicit Day5b scope governs; protocol/PLAN are archived. Exactly two
strict-JSON tolerances and grouped_mm gate registered in composition-pilot README.
No fitting; frozen DEV00 CPU recovery and authored DEV-only re-pilot. Conservative
projection carries prior pilot spend; O proxy R disclosed if unrun. No signals,
bench reads, batch4 or push; 7200s one-load GPU cap; explicit-path commits.

2026-09-06 — DAY5B CPU RECOVERY:95/128 execute190 tools; all final lanes fail
integration (missing append separators) and obligations; style95/95 violations.
N dropped verbose contains4 unscoped delivery claims; diagnostic preserved,
not a third parser tolerance. Renderer16 original-input prompts match exactly.
Scope deviation: broad test_focus_slab selection instantiated synthetic eval
witness cases on CPU; no bench read or model inference, no scientific use of
those results. Detected mid-run; no signal sent. Dedicated tests/GPU DEV-only.

2026-09-06 — STATE: DAY5B GPU PARITY LAUNCH, freeze a3fd8613.
Dedicated17 tests pass; CPU48 real-HF stub calls succeed and arm-cost sum matches.
Broad CPU witness suite still finishing, excluded from scientific decisions.
Command: /home/bmarti44/stencil-llm/.venv/bin/python -m stencil.focus.pilot2
--out /home/bmarti44/stencil-llm/results/quick-checks/composition-pilot-2
Log: same directory/run.log; own PID registered by runner; flag/lock held until
normal/cooperative exit. One load7200s; STOP unless all64 parity with<=1 divergence.

2026-09-06 — STATE: DAY5B COMPLETE / RE-PILOT INCOMPLETE, PARITY STOP.
Freezea3fd8613 grouped_mm compares64/64;4 divergences (R/N/T/O round0 at
191/72/0/191), all60 later outputs identical. No amended re-pilot authorized
past failed<=1 gate; no extra load/backend. GPU1362.257/7200s incl323.293load;
16.813tok/s; diagnostic old-interface16-round projection14.391h>12, actual
re-pilot projection unavailable.128 hidden arrays hash/shape/nonzero audited,
10 partial means; flag removed, normal exit, no signals/push.
CPU recovery95responses/190tools; final lanes0/8.56 final guardedDEV tests pass.
Broad CPU synthetic-eval test deviation recorded; subsequent guard blocked a
legacy eval-freeze subcheck before construction (55pass/1guard rejection).
Metadata-only fixture repair used prior generated hash receipt, preserving
all episode/hidden/turn hashes; system adds49tokens, DEV consumer verified.
Frozen GPU golden/inference sources unchanged; local explicit-path final commit.

2026-09-06 — vllm-qual WRITE-AHEAD (astra): user-amended determinism/speed gate; three64-case DEV00 passes, B8 diagnostic; no fitting/eval/bench. README registration and frozen source hashes prewritten. Archived protocol is historical; current user quick-check scope governs.45GPU-minute cap; at most two memory remedies; own container cleanup only.

2026-09-06 — vllm-qual COMPLETE (astra): amended gate QUALIFIED via C4;64/64 triple-pass identity, HF5/64 disclosed;18.709/18.733B1 decode,39.912C4 aggregate;12.558h/7.845h frozen16-round projections. C8 partial9/64, no credit;201 completed+55 unsubmitted records audited;2555.495/2700GPU-s; own containers/flag removed, no push. Full-run long/controller/HF-hidden validation remains unrun; see results/quick-checks/vllm-qual/README.md.
