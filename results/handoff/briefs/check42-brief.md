# Quick check 42 for gpt-6-astra: placement EVERY request vs text-restate on the frozen FOCUS-2d banks (2026-09-05)

RESUME: your previous session reached the CPU freeze stage (results/quick-checks/check42/ has freeze.json,
cpu-validation.json, preparation-v1-freeze.json, gpu-readiness.json) before the power outage; reuse them if their hashes
still verify, otherwise redo the CPU stage. Source: results/focus2d-review-fable.md items 5-10 and the FOCUS-2d
OUTCOME (LEDGER-PLAN.md). Finding: placement-only rendered the live rule only at change events; where it rendered it
beat the anti-imitation recap per checkpoint; the 32-vs-176 all-five gap is CADENCE. Hypothesis: a live-rule block
rendered in EVERY request, carrying every live obligation (task rule, schema, tag), matches or beats text-restate with
zero constraint harm, making the custom cache/mask unnecessary for the ship path.
Reuse the FROZEN FOCUS-2d final bank (results/qwen/focus2d/freeze, seed 9053723; same 256 episodes; disclose that
this bank's outcomes were seen for other arms) and scripts/focus2.py plumbing. Three arms, own prior answers KEPT
(no masking): (A) placement-every-request: the live task rule rendered inside EVERY request (all five checkpoints and
the delay pairs' user turns), nothing else; (B) A + the schema/tag lines repeated inside the same block; (C)
text-restate exactly as FOCUS-2d (comparator). Plus the recorded FOCUS-2d BOTH and neither arms as reference rows
(no regeneration). Scoring identical to FOCUS-2d (all-five; constraint/collateral; F6 flags). READING (fixed before
running): masking is CLOSED on this family if A or B >= C on all-five (exact McNemar not-worse, p > .05) AND
constraint failures <= C + 2; otherwise report the gap; secondary: B vs A isolates the schema-carrier effect.
Outputs: results/quick-checks/check42/{summary.json, records/, README.md (pre-written reading, tables, plain-language
conclusion for the FOCUS-3 ship design)}; item 42 in results/quick-checks/README.md (5 lines); WORKLOG entry (<= 8
lines). Commit scripts/focus_check42.py, results (git add -f), README/WORKLOG with explicit pathspecs; no push. GPU cap
3.5 h (project from FOCUS-2d's 72.9 s worst cell; scale to 192 episodes if needed, recorded before running).
Foreground only; never terminate or signal any process; never read the sealed IFEval input file or the sealed BFCL
cohort contents; nothing fit or trained.
