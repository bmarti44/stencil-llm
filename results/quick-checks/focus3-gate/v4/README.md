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
