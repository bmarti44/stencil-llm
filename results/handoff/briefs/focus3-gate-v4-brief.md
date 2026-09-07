# FOCUS-3 gate v4 for gpt-6-astra: runtime value parity + registered constants, then the gate (2026-09-06)

Source: results/focus3-gate-v3-review-fable.md (rendering CODE identical to the trainer; the runtime feeds out-of-
vocabulary VALUES: status "active" vs training "live"; scope "task"/"user-global" vs "task:<name>"/"global"; metadata
with version/task_id/opaque key vs {"key": <semantic>}; prev_user = whole previous message vs one ~49-char sentence on
3.7% of rows; message = sentence + sort request (242-279 chars) vs training median 78 -> offline rescoring: runtime
0/12 gold transitions; with faithful values + message = the sentence 9/12 (supersedes/cancels/completes 3/4 each);
residual 3 misses are phrasings ("no longer applies", "That concludes task X", "Replace the sorting rule") -> route to
the TRAINING POOL, never edit the bank; frozen-constant defects: the P(none) >= 0.98 none-pair admission guard is
unreachable (0/151 held-out gold-none rows reach it; median .927) and blocks switched-task standing rules; target
selection positive[0] retires the wrong row when a span fires on the global tag rule first).
Orchestrator rulings (registered BEFORE running; no fitting): (1) Runtime.update feeds training-vocabulary values:
status {live, superseded, cancelled, completed}, scope "global" | "task:<semantic task name>", metadata {"key":
<semantic key>} only; prev_user = the single preceding user SENTENCE or None; the pair message = the candidate
sentence's own message rendered as prose only (strip the JSON sort request/payload block) — register these exact
choices; (2) none-pair guard: replace 0.98 with a DEV-calibrated quantile (the 90th percentile of P(none) on DEV
gold-none rows; compute and record; if it admits > 5% of DEV positive rows as none-pairs, use the 95th); (3) target
selection: among candidate targets with the same kind, the highest-probability positive; (4) CPU PARITY UNIT TEST:
assert every runtime pair's values are in the trainer vocabulary and render_pair(runtime) == render_pair(normalize_row(
same row)) on fixtures; (5) the pre-gate stop reports per-label transition recall and none-pair P(none) quantiles on
setup; requires every gold transition applied to the gold source row (allow <= 1 miss of 12 given the three known
phrasing misses are NOT in setup... if setup contains them, report but do not edit); (6) send the three missed
phrasings + 30 hand-written paraphrases of each to data/classifier/relations/astra-enrich-2.jsonl for a LATER refit
(not used now). Then run the gate (C/O/N/T, 64 episodes, seeds 30321 setup / 30322 gate, readings unchanged from v3).
Cap 3 GPU-h. GPU: check 40i may hold it (results/quick-checks/check40i/RUNNING.flag) — wait; write your flag; never
signal. Outputs under results/quick-checks/focus3-gate/v4/; README item + WORKLOG; commit with explicit pathspecs
(git add -f); no push. Foreground only; never terminate or signal any process; never read the sealed IFEval input
file or the sealed BFCL cohort contents; nothing fit or trained.
