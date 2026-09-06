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
