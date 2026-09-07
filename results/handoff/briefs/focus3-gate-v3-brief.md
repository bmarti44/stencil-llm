# FOCUS-3 gate v3 for gpt-6-astra: spec-conformant bank + pre-gate admission stop, then rerun (2026-09-06)

Source: results/focus3-gate-review-fable.md (v2 FAIL root cause: the bank phrased its standing ordering rule as a one-off
imperative "For task X, sort the payload in asc order." — which data/classifier/LABELS.md defines as NONE (one-off work
request); the admission head scored it P(rule) 0.01-0.05 in 64/64, correctly per spec; threshold fixes refuted; setup C
traces already showed 0/16 admissions before the gate launched — a pre-gate stop was missing). Orchestrator ruling
(NEW registration, no fitting): (1) CPU first: score the v2 template sentence and 8 spec-conformant paraphrases with
training-faithful context encoding ("user:" prefix, preceding sentences) — record the P(rule) table; fix the runtime
context encoding to match training (fable item 3) if it differs. (2) Re-author the bank's standing rules in
spec-conformant STANDING phrasing, varied across episodes (e.g. "From now on, for the inventory task keep the payload
sorted ascending.", "Always sort ascending for this task.", "For this task the payload must be in ascending order
until I say otherwise."), with cancellations/completions/overrides/switches phrased naturally (also varied); keep the
64/16 split, families, seeds 30311 (setup) / 30312 (gate), checkers, default-row renderer, no masking. (3) PRE-GATE
STOP: setup C must admit every gold standing rule (16/16) and retire every gold cancellation/completion in setup;
otherwise stop INELIGIBLE-ADMISSION before the gate. (4) Run the 64-episode gate (C/O/N/T) with the v2 readings
unchanged (register agreement >= 48/64 and >= 12/16 per family; C within 4/64 of O on stale executions and final
success; false retirements <= 2/64; breakage <= 2/64; C beats T). Cap 3 GPU-h. GPU: check 40h may hold it
(results/quick-checks/check40h/RUNNING.flag) — wait; write your own flag. Outputs under
results/quick-checks/focus3-gate/v3/ (RESULTS.md with pre-written reading, summary, records, register traces incl.
admission probabilities per span); README item + WORKLOG entry; commit with explicit pathspecs (git add -f); no push.
Foreground only; never terminate or signal any process; never read the sealed IFEval input file or the sealed BFCL
cohort contents; nothing fit or trained.
