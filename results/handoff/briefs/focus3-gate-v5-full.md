# POST-REBOOT NOTE (2026-09-05, power outage at ~18:27; machine up since 18:27)
The previous codex sessions died mid-task; the scratchpad was wiped. Artifacts committed in git are the only state.
GPU: a llama-server owned by Brian (pid 2705, Qwen3.8-27B Q4, ~16 GB) now runs permanently on the GPU. It is NOT a
Stencil job: treat the GPU as available for Stencil when no OTHER compute process (a .venv python) is present; never
touch pid 2705. Memory budget: 128 GB total minus the llama-server; Qwen3-30B-A3B bf16 (~61 GB) still fits. Coordinate
with other Stencil GPU checks via results/quick-checks/<check>/RUNNING.flag files (write yours while running, delete
after; wait if another Stencil flag exists). Never signal any process. All committed prior results stand; re-read the
relevant README/records rather than redoing completed work. Commit with explicit pathspecs; no push.
# FOCUS-3 gate v5 for gpt-6-astra — step A (CPU): runtime fixes + registered constants + CPU replay of the FROZEN v4 model (2026-09-06)

Source: results/focus3-gate-v4-review-fable.md (items 1-10). Do NOT refit yet. Orchestrator rulings (register in the v5
RESULTS pre-written section before running anything):
 (1) none-pair admission guard = POSITIVE-side bound: a pair is "confident none" iff P(none) >= 0.5 (DEV: passes
     217/259 gold-none, blocks 5/317 positives; record the DEV table); the gold-none 90th-percentile guard is retired.
 (2) scope-overlap pairing: spans are paired only with rules whose scope overlaps the current task (global or same
     task); wrong-task pairs are never scored; a positive proposal against a non-overlapping rule is dropped (never
     `continue` past the span's admission).
 (3) reinstates only from rule-bearing spans (a span must itself pass admission P(rule) >= .95 or name a retired rule
     verbatim); "Continue/Work on/Return to task X" spans are task switches, not reinstatements.
 (4) per-class thresholds unchanged (.94/.50/.50/.50) for this replay; record the DEV sweep table (fable item 4) and
     register the alternative (.80 supersedes: recall .87, none-FP 12.7%) as a SEPARATE arm C' in the gate, not a swap.
 (5) setup stop adds "unauthorized applications == 0/96" and per-label transition recall >= 3/4 per label with the
     three known phrasing misses reported (they will still miss until refit).
 (6) DELETE the 3 verbatim bank sentences from data/classifier/relations/astra-enrich-2.jsonl (record which); the
     multi-domain kimi transition pass (data/classifier/relations/kimi-transitions.jsonl, being generated) is the
     clean enrichment for the later refit; do not touch it now.
 (7) CPU PARITY tests extended: guard side, scope pairing, reinstates rule, unauthorized-application counter.
Then: CPU replay of the 16 setup episodes with the FROZEN v4 model (expected 36/36 admissions, 8-9/12 transitions,
0 unauthorized applications); write results/quick-checks/focus3-gate/v5/RESULTS.md (pre-written section + replay
outcome) and STOP there (step B = refit + gate follows after the enrichment review). Commit code/tests/results (git add
-f) + README item + WORKLOG with explicit pathspecs; no push. CPU only; never launch any GPU/model process; never
terminate or signal any process; never read the sealed IFEval input file or anything under data/bench.
