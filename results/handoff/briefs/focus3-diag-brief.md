# FOCUS-3 DIAGNOSTIC gate run for gpt-6-astra (2026-09-06): run the five arms with the v8 runtime as-is; no PASS claim

The v8 CPU replay is INELIGIBLE (12 unauthorized actions, all from the admission head: 8 one-shot payload requests + 3
inert quotes admitted; 1 completion retiring a wrongly admitted same-task row). The orchestrator authorizes ONE
diagnostic GPU run of the 64-episode gate (seed 30322 bank, unopened) with the v8 runtime (relation model v2, admission
head ft-v3, all v8 rules) to measure the END-TO-END COST of those false admissions: arms C (primary), C' (alt), O
(oracle), N (none), T (naive restate-all). Register in results/quick-checks/focus3-gate/diag/RESULTS.md BEFORE running:
"DIAGNOSTIC — the registered eligibility stop was not met; readings are reported but no PASS/FAIL label is assigned;
this run informs the admission-detector redesign only." Report everything the v3 readings define (register-exact
agreement per family, stale executions, final success, false retirements incl. false ADMISSIONS as their own row,
breakage, unauthorized actions per family, C vs O and C vs T contrasts descriptively) plus, per false admission, what
it did to downstream answers (did rendering a spurious rule change behaviour? how often?). Cap 2 GPU-h (project after
O setup; scale to 48 episodes if needed and record). GPU idle; RUNNING.flag; never signal. Outputs under
results/quick-checks/focus3-gate/diag/; README item; WORKLOG; commit with explicit pathspecs (git add -f); no push.
Foreground only; never terminate or signal any process; never read the sealed IFEval input file or anything under
data/bench; nothing fit or trained.
