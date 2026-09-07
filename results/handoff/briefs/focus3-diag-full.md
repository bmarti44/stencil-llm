# POST-REBOOT NOTE (2026-09-05, power outage at ~18:27; machine up since 18:27)
The previous codex sessions died mid-task; the scratchpad was wiped. Artifacts committed in git are the only state.
GPU: a llama-server owned by Brian (pid 2705, Qwen3.8-27B Q4, ~16 GB) now runs permanently on the GPU. It is NOT a
Stencil job: treat the GPU as available for Stencil when no OTHER compute process (a .venv python) is present; never
touch pid 2705. Memory budget: 128 GB total minus the llama-server; Qwen3-30B-A3B bf16 (~61 GB) still fits. Coordinate
with other Stencil GPU checks via results/quick-checks/<check>/RUNNING.flag files (write yours while running, delete
after; wait if another Stencil flag exists). Never signal any process. All committed prior results stand; re-read the
relevant README/records rather than redoing completed work. Commit with explicit pathspecs; no push.
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
