# Brief: phase3-prefetch — overlap data generation with GPU compute (human-directed)

## Objective

Hide the 0.16 s/batch CPU data-generation cost behind GPU execution (now ~25-30% of the optimized ~0.5 s step). Read `src/stencil/train.py`'s training loop and batch/collate path first.

- Double-buffered prefetch: a single background thread (`threading.Thread` or a 1-deep `queue.Queue`) generates batch N+1 while the GPU executes batch N. EXACTNESS CONTRACT: the generator draws must be IDENTICAL in value and order to the current synchronous path — the same generator objects consumed in the same sequence, only earlier in wall clock. One worker thread only (two would interleave stream consumption — forbidden). H2D copies may use a side stream with proper event synchronization into the graph-replay stream; no `pin_memory` games that change values.
- Applies to the graphed and eager paths alike; flag to disable (default on).
- New test `test_prefetch_bitwise_equals_sync`: N training steps with prefetch on vs off — losses and final parameters bitwise equal (torch.equal). Also assert the metrics.jsonl rows are identical.

## Tests first (TDD, rule 1)

The bitwise test red (flag absent) before implementing. Run only your own/touched tests plus test_train_two_runs_bitwise_short. Report a timing probe: m1 and b0_local s/step at (2048,8) batch 8, prefetch on vs off, 20 timed steps.

## Allowlist

See phase3-prefetch.allow. Do not touch PLAN.md, plan/, tools/, AGENTS.md, README.md, tests/fixtures/*.

## Acceptance

New/touched tests green, ruff clean, timing table. Full suite + pilot are the orchestrator's.

## Ledger handoff

Do not edit the ledger. End with: files changed, red/green pairs, timing table, the exactness argument (why draw order is unchanged), residual choices (v1.10).
