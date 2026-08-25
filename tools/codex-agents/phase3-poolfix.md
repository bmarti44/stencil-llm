# Brief: phase3-poolfix — one failing cell must never kill the matrix pool

## Objective

The concurrent pool in `scripts/run_matrix.py` died silently after ~8 hours: a child exceeded the per-run `--timeout` and was terminated, `_subprocess_launcher` raised `CalledProcessError`/`RuntimeError`, and `handle_result` catches ONLY `StalledRun` — so the exception propagated out of the `while queue or in_flight` loop, `ThreadPoolExecutor.__exit__` blocked in `shutdown(wait=True)`, and the pool ran one lonely child to completion while launching nothing for 2+ hours. Zero diagnostics reached the log. Read `execute_pending`, `handle_result`, `_subprocess_launcher`, `_watch_process`.

Fixes:

1. **No single cell may kill the pool.** In BOTH the `jobs == 1` and concurrent paths, catch `BaseException`-minus-`KeyboardInterrupt`/`SystemExit` (i.e. `except Exception`) around each cell's result, not just `StalledRun`. On failure: `print(f"FAILED {cell.key}: {exc!r}", flush=True)` and requeue at the back. Add a per-cell attempt counter with a cap (`--max-attempts`, default 3); a cell that exhausts its attempts is recorded in a `failed` list, logged as `GIVING UP {cell.key} after N attempts`, and the pool CONTINUES with remaining cells.
2. **Report at the end.** `execute_pending` returns `{"skipped", "launched", "failed": [cell keys]}`; the CLI prints a final summary line naming every failed cell (or `all cells completed`). A non-empty failed list sets a nonzero process exit code, but only AFTER every other cell has been attempted.
3. **Timeout diagnostics.** When `_watch_process` terminates a child for exceeding the total `timeout`, raise a distinct `RunTimeout` exception carrying the cell key, elapsed seconds, and last observed step, so the log line says which limit fired. `StalledRun` keeps its existing meaning (metrics stopped growing).
4. Keep the existing stagger and stall-watchdog behavior unchanged.

## Tests first (TDD, rule 1 — per-test red)

Using fake/fast child launchers in tmp dirs: (a) a child that always fails is retried up to the cap, then reported in `failed`, while a healthy sibling cell still completes; (b) a timeout-terminated child logs `RunTimeout` with its cell key and is retried; (c) the pool never exits early with cells still pending; (d) the final summary lists failures and the exit code is nonzero only after all cells were attempted. Run only your own/touched tests — no GPU work.

## Allowlist

phase3-poolfix.allow. Do not touch PLAN.md, plan/, tools/, AGENTS.md, README.md, src/stencil/*, tests/fixtures/*.

## Acceptance

Your new tests plus the existing `tests/test_run_matrix.py` suite green, ruff clean. No GPU work, no training launches — the orchestrator relaunches the matrix after this lands.

## Ledger handoff

Do not edit the ledger. End with: files changed, red/green pairs, the exact exception-handling contract you implemented, residual choices (v1.10).
