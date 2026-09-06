# FOCUS-3 gate v4 — pre-written reading (2026-09-06)

User-authorized repair; fit/train NONE. Frozen ft and seed0 relations models
unchanged, historical admission lineage caveats retained. Calibration-on: ONLY
committed GPU seed0 DEV logits, original scenario-disjoint576-row split.
Evaluation-on: unchanged v3 templates, fresh lists30321 setup/30322 gate (16/64).
These are reused development wordings, not independent-author or new scenarios.
The three known misses ARE in setup and gate; report without editing the bank.
Enrichment3 originals +90 handwritten relatives is evaluation-derived development
material for a LATER refit ONLY, excluded from current calibration/inference.
No sealed IFEval/BFCL inputs, fitting, background launches, signals or push.

RUNTIME VALUES, registered before calibration or setup: status passes through
live/superseded/cancelled/completed; scope global or task:<visible semantic name>;
metadata {"key": semantic sort-order/tag/instruction}, no opaque key/version/task_id.
Relation message = entire prose prefix before Sort request/payload block, keeping
all prose sentences; no pairs for payload-only sentences. Original exact span
start/end offsets remain. prev_user = last sentence of previous user's prose
prefix or None (not earlier sentences in this message). Admission classifier
still gets its original spans and up-to-three preceding prefixed sentences.
Pair rendering is checked against trainer normalize_row/render_pair on fixtures.
Positive label thresholds .94/.50/.50/.50 and admission .95 unchanged.
None guard = linear90th percentile DEV gold-none P(none); if >5% DEV positives
meet >=cutoff, use linear95th. If95th still violates5%, stop, never retune.
Chosen cutoff and denominators recorded in calibration.json before setup.
Same-kind positive target with highest proposed-label probability wins; stable
source-order ties. Broad task closure considers all kinds and retains atomic
whole-task completion. Existing scope/status guards and no-positive admission
requirement retained. No new key/scope outcome rescue.

PRE-GATE CPU STOP: all36 gold admissions (initial order16, tag16, switched task4)
and >=11/12 gold transitions, applied to correct source row with exact source
retirement/replacement state; no overflow; all96 setup records required.
Report per-label gold/proposed/applied and recall, gold-none pair confusion and
P(none) quantiles, plus none-pair probabilities on gold-admit spans. Report known
phrasing membership, never exclude it. Failure INELIGIBLE-ADMISSION, zero GPU/gate.
If eligible: O competence>=15/16 with unchanged v2 cues and C preflight recheck.
Then exactly64 C/O/N/T episodes, no48 fallback or outcome-based retries.

V3 gate readings unchanged: C exact>=48/64 and>=12/16 per family; absolute C/O
stale distance<=4/64 and final success distance<=4/64; C false retirement<=2/64
(including missing admissions), broken<=2/64; stale C<T; no contradictory recaps.
All1536 gate records required. N descriptive. No masking; same greedy cap64,
trunk, renderer/defaults, checkers, raw records/history and endpoint semantics.

Fresh10800 GPU-held seconds includes load/setup/classification/generation.
After O setup, elapsed+1.25*slowest_episode*64*4 must be<=10770s or INCOMPLETE.
Wait for all quick-check RUNNING.flags and other compute jobs to clear; Brian's
permanent llama-server pid2705 is exempt and untouched. Atomically claim own
v4/RUNNING.flag under review lock; remove own flag on natural exit only.
Foreground, cooperative cap, never terminate or signal a process.
All sources/model/bank/reading/calibration hashes committed before setup scores.
Same-run records/traces/diagnostics, summary, audit and outcome retained.

## Outcome — INELIGIBLE-ADMISSION; GPU gate not run

Freeze `c72a4d3d` preceded the single CPU setup replay. All 16 episodes / 96
turn records completed. Runtime values and rendered pairs passed the CPU trainer
parity checks. The registered stop failed: **8/12 transitions** applied to the
correct source rows (required >=11/12), and **32/36 admissions** succeeded
(required 36/36). Initial ordering and global tags each admitted 16/16; switched
task rules admitted 0/4. No bank edits, outcome-based repairs, retries or refit.

| Gold transition | Gold pairs | Correct proposals | Applied to gold source | Recall |
|---|---:|---:|---:|---:|
| supersedes | 4 | 2 | 2 | 50% |
| cancels | 4 | 3 | 3 | 75% |
| completes | 4 | 3 | 3 | 75% |
| reinstates | 0 | 0 | 0 | unsupported |

All three known phrasings are present and missed. The fourth transition miss is
“For task S0n2A, switch the standing order from descending to ascending.”
P(supersedes)=0.7268192443, below the unchanged .94 cutoff. The three known misses
have P(gold)=.7022823938/.0155701830/.0335639569 for replacement/cancellation/
completion, respectively. These values use the registered **full prose message
and one previous-user prose sentence**, so they are not the review's span-only,
no-prev-user 9/12 diagnostic. See [all gold transition probabilities](independent-audit.json).

## Registered DEV calibration and setup none pairs

The committed GPU seed0 DEV file has 576 rows (259 none, 317 positive).
Its SHA256 is `cc9fc6112107e9309447a5235842df818ba438d47b5587dabe6563766587985c`.
The registered linear 90th percentile is **0.9711621345086118**: 26/259 DEV none
rows and 0/317 DEV positives meet >=cutoff. The 95th fallback was unnecessary
(.97256607268076; 13/259 none, 0/317 positives). This calibrated only the runtime
admission guard; frozen encoder/head, positive thresholds and admission .95 did
not change. [Complete calibration and split binding](calibration.json).

| Setup gold-none P(none) | Value |
|---|---:|
| minimum | 0.0122871529 |
| median | 0.9539164324 |
| p90 | 0.9665213910 |
| p95 | 0.9673825335 |
| p98 | 0.9684618542 |
| maximum | 0.9699236177 |

There are 201 scored relation pairs: 12 gold positives and 189 gold-none pairs.
**0/189 setup gold-none pairs reach the DEV cutoff.** All eight pairs on the
four gold switched-task admission spans also fail it (median .0862694756,
maximum .8076887648). Two of those spans additionally propose wrong-task
supersedes, which the existing scope check refuses; they remain unadmitted.
The lower registered constant therefore did not resolve switched-task admission
on this setup. Initial simultaneous admissions had no existing candidate targets.
Full quantiles, including p10, are in [setup diagnostics](setup-admission/summary.json).

| Gold-none decision | none | positive |
|---|---:|---:|
| proposed | 162 | 27 |
| applied | 170 | 19 |

The 19 unauthorized applications across eight episodes are **18 reinstates and
one cancellation**. The cancellation follows a quoted, explicitly inert setup
line. Reinstates occur on continuation, return and plain prose requests after
retirement; three are on the prose-only request. Thus event-time recall alone
does not establish that the retired state stays correct. Saved full source
messages still feed the inherited scope parser; the appended request's word
“conversation” permits a global scope reading on some continuation spans.
This is visible in `setup_2_00_C_3`: a rule from task S2n0A is reinstated while
the request names S2n0B. These are recorded failure diagnostics, with no
post-outcome scope or classifier repair. [Exact false-application records](independent-audit.json).

## Artifacts, validation and resource use

[Runtime replay audit](audit.json) PASS: all 96 records / 16 traces, 201 pair
inputs, source state, raw-logit softmax probabilities, every runtime value and
trainer-normalized rendering, admission context, DEV calibration and frozen
hashes reproduce. [Independent saved-record audit](independent-audit.json) PASS:
gold labels derived from bank events and exact source/new-row status counts
match the registered summary; no new model inference. The raw recount script
was authored after outcomes solely for verification; the runtime replay audit
was frozen before setup. Its source is [audit_raw.py](audit_raw.py).

32 applicable CPU tests pass; one legacy import-inventory xfail. Ruff and
whitespace checks pass. No sealed-byte hash tests or sealed inputs were read.
Enrichment contains the exact 3 observed originals plus 30 individually
handwritten paraphrases each (93 valid rows, 3 linked scenario families), all
marked evaluation-derived and reserved for later refit. They are absent from
the frozen model's fit/calibration inputs and cannot support independent future
held-out claims. File: `data/classifier/relations/astra-enrich-2.jsonl`.

CPU setup replay loop: 19.307595 seconds of wall time after classifier loading
(the historical field is named cpu_seconds; this is not process CPU time).
**GPU use 0/10800 seconds; generated responses 0; gate records 0.** Check40i
retained its own GPU job/flag; this CPU-only stop required no GPU claim or flag.
Brian's pid2705 and all other processes were untouched. The 64-episode v4
C/O/N/T gate and its endpoints remain unmeasured under the mechanical stop.
This completes the authorized v4 experiment at its registered stop.
