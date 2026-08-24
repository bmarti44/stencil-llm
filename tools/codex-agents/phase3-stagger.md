# Brief: phase3-stagger — stagger concurrent run launches (livelock mitigation)

## Objective

One matrix run (b0_full N=2048 k=32 s1) livelocked at step ~128 with 107% CPU when its slot launched SIMULTANEOUSLY with another heavy run — both in CUDA-graph capture at the same moment. The identical config completed normally when relaunched while neighbors were mid-training (not mid-capture). Working diagnosis: concurrent-capture race. Read scripts/run_matrix.py's pool launcher.

- Add a launch stagger to the `--jobs` pool: after starting any child, wait `--stagger` seconds (default 120) before starting the next, so no two runs are in their capture window together. Waiting applies only to LAUNCHES; running children are unaffected.
- Add a progress watchdog: if a child's run-dir metrics.jsonl fails to GROW (file size) for `--stall-timeout` seconds (default 1200), kill that child and record `STALLED` in the matrix log; the standard interrupted-restart semantics retry it later (do not retry immediately — put it at the back of the queue).
- Tests (tmp dirs, fake fast cells): stagger delays second launch by the configured amount (use a tiny value in tests); watchdog kills a fake child that stops writing and requeues it at the back; normal children unaffected.

## Tests first (TDD, rule 1)

Both features' tests red first. Only your own tests; no GPU work (the matrix owns the GPU).

## Allowlist

phase3-stagger.allow. Do not touch PLAN.md, plan/, tools/, AGENTS.md, README.md, src/stencil/* (this is a launcher-only change), tests/fixtures/*.

## Acceptance

New tests green, ruff clean. NOTE: the live matrix process already has the old code loaded — the orchestrator applies your change at the next natural matrix restart, not by killing the pool.

## Ledger handoff

Do not edit the ledger. End with: files changed, red/green pairs, residual choices (v1.10).
