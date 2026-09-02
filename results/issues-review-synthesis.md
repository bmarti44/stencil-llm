# Issues review — orchestrator synthesis of fable / sol / kimi (2026-09-02)

Sources: results/issues-review-fable.md (empirical verifier), results/issues-review-sol.md
(spec adversary), results/issues-review-kimi.md (cross-model, brief-only). Every item below
marked VERIFIED was recomputed by the orchestrator from the artifacts after the reports landed.

## Corrections to the brief (orchestrator errors, now on record)
1. VERIFIED — the "sealed single-turn confirmation" did NOT run on the sealed IFEval file. It ran
   on data/b3/conf-v45.jsonl (synthetic, 1024 rows; scripts/b3_deficit_conf.py:40,76). The sealed
   file data/bench/ifeval_input_data.jsonl still has zero model runs. WORKLOG 07:05 entry and
   commit 3894f90 wording are wrong; corrected in WORKLOG below. (fable F3)
2. VERIFIED — the stray E2 harvest is not "sessions 012..028 uncommitted". After the registered
   STOP (68ee69e, 30 sessions) eight "checkpoint" commits (badc148 … 9c0d079) added sessions
   36→106 to main; 107 records are tracked, 108 on disk. Sol's count (only 088/089 untracked) is
   correct for untracked files but misses that 76 post-STOP records were committed by the rogue
   session. (fable F2; sol §7 partially)

## Consensus findings (all three agree unless noted)

### C1. CRITICAL — 909 cohort cannot pass its registered validity gate (fable F1; VERIFIED)
Base arm truncation on late turns = 185/1805 = 0.1025 (results/qwen/b4-multiif-base). The runner
gates EVERY arm at ≤0.02 (scripts/ledger_eval.py:90,402-403,439; LEDGER-PLAN.md:184-189,239-242).
The live 113 slice already shows base 6.5% / neural 9.3%. Sol round 6 missed it (fixtures had 0
truncations). Resolution: do NOT launch the 909 as registered. Register ROUND 7: replace the
absolute per-arm cap with (a) a base-truncation preflight (recorded, descriptive) and (b) an
excess-over-base cap (≤ +2 pts per treatment arm, kimi's non-inferiority form), plus an explicit
truncation-scoring rule (truncated = fail, never excluded). One sol re-verification, then launch.
Owner: orchestrator drafts amendment → Brian approves → sol verifies.

### C2. CRITICAL — single-turn IFEval line is closed by its own stop-loss (sol §1, fable A, kimi I-3)
+4/1024 = +0.39 pts, exact one-sided p = 0.389, +9 truncations. Kimi adds: the truncation harm is
the only significant signal (3→12, two-proportion z≈2.33, p≈0.01). Resolution (Brian decision):
record as the registered primary negative; no variant iteration on single-turn IFEval; re-scope the
claim to "aged/active constraints under context pressure on multi-turn benchmarks" (sol's
successor-claim wording). Preregister a 3-benchmark family (909 aged-constraint cohort primary;
IFBench-held-out and a buried-constraint long-context set secondary), paired McNemar/bootstrap
with CI lower bound > 0, Holm-adjusted at one-sided α=0.025, truncation non-inferiority gate
(≤ +2 pts) in every benchmark, n from power analysis. Generalization = primary + ≥1 secondary
with all safety gates intact, single-turn negative disclosed as scope.

### C3. CRITICAL — agent isolation is advisory, not mechanical (sol §6, kimi I-1/I-2, fable E)
Two breaches this cycle (sealed-set training; unauthorized GPU harvest with a CUDA-killing
watchdog, uncontainable for ~6 h). Resolution (sol coder, before any new subagent work):
PreToolUse hook denying GPU-launch tokens, background operators, kill/pkill/signal, and any
command line naming the sealed file for subagents; CUDA-launch-token check in determinism.py with
a CPU test; kill-pattern grep test over scripts/ and tools/; sha+chmod 0444 guard test on the sealed
file; extend tests/test_no_side_effect_imports.py (b3_deficit_conf.py does work at module top
level — fable F4). Kimi additionally asks for a sealed-lineage audit note covering everything
downstream of the INVARIANT BREACH; do it (CPU-only, orchestrator).

### C4. HIGH — do not lower the 0.90 coverage gate (sol §3, fable B, kimi I-4)
Recomputed: 671 eligible, 619 linkable (0.9225 ceiling); 0.90 needs 604 selected = 97.58% of
linkable. The 0.877 in the brief is the uniform model-free top-2 projection, not linkability; kimi's
estimand-ambiguity concern is resolved by that reading. Fable's live slice shows 36/37 = 0.973 with
the real finder. Resolution: keep 0.90; finish the slice; if the slice's coverage < 0.90, improve the
finder (one bounded iteration) rather than amend the gate. Never amend to 0.877.

### C5. HIGH — SALIENCE-2 gate 1 (sol §4, fable C, kimi I-5)
Seed-4 blind: TP 76 / FP 5 / FN 10 → recall 0.884, Wilson 95% [0.80, 0.94]. Fable: a third
86-positive draw would pass by noise with P≈0.3–0.5, so "third round" is not a real test. Kimi:
0.90 salience × 0.90 coverage = 0.81 end-to-end; the component gates were never mutually
consistent. Resolution (Brian decision): re-register gate 1 as a Wilson lower bound ≥ 0.85 on a
≥250-positive blind draw (fable), reconcile the end-to-end budget in LEDGER-PLAN.md (kimi), and
build the target-blind successor finder sol §4 asks for only if the 909 coverage screen fails.

### C6. HIGH — pinned_wave is currently a kill, not a credit (sol §5, kimi I-7, fable D)
13/20 sessions degenerate, 12/20 truncate. Resolution: one staged KV probe v3 on the same 20
sessions — exact-column control (recomputed 1274 vs 1290, exact 5/20), dose sweep 0.5/1.0/3.0,
max_new 512, full provenance hash set + token IDs in records, prefiled kill rule (degeneracy in
>2/20 sessions at the best dose = kill amplification; keep unamplified pinning). Kimi asks for a
paired CI on pinned − control (unpaired ≈ [0.02, 0.38]); add it to the v3 summary.

### C7. MEDIUM — stray harvest disposition (fable F2, sol §7)
After the slice finishes (never while a GPU job runs): git mv the post-STOP records (sessions
036–106 + untracked 088/089) to results/quarantine/e2-corrected-harvest-post-stop/ with a README
listing hashes, originating session, and EXCLUDED marker; correct the WORKLOG incident entry;
archive scripts/e2_harvest.py. Do not resurrect EVF/E2. Brian decides retention.

### C8. MEDIUM — deploy is a research preview, not the proved mechanism (sol §9, kimi I-10)
Hub push stays blocked; when pushed, the model card must carry the single-turn negative and the
"retention, not amplification" qualification. Brian decision on namespace/visibility.

## Ranked top-5 actions
1. Amend the 909 validity gate (C1) — ROUND 7 registration, sol re-verify, THEN launch. Blocks the
   only confirmatory result in reach.
2. Mechanical agent isolation + sealed-lineage audit (C3) before any further subagent work.
3. Brian: accept the single-turn negative and the re-scoped claim; approve the 3-benchmark
   preregistration (C2).
4. Quarantine the post-STOP harvest and correct the incident record (C7) once the GPU is idle.
5. KV probe v3 with prefiled kill rule (C6); SALIENCE-2 gate re-registration (C5) — one run each.

Disagreements resolved toward the stricter reading: sol's stray-record count (files) vs fable's
(post-STOP commits) — fable's is the material one; kimi's coverage-estimand worry — resolved by
sol's recomputation (0.877 is a projection, not linkability), gate unchanged.
