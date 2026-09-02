# Brief: isolation-and-gates — mechanical agent isolation, ROUND 7 truncation gate, KV probe v3 prep

## Objective
Implement the code-level resolutions from results/issues-review-synthesis.md (C1, C3, C6, fable F4):
1. Mechanical agent isolation (C3):
   - `tools/hooks/pretool_guard.py` + registration snippet for `.claude/settings.json` PreToolUse (Bash):
     deny any command line that (a) names `data/bench/ifeval_input_data.jsonl` unless the invoking script
     is in the sealed allowlist of tests/test_sealed_guard.py; (b) contains kill/pkill/killall/`kill -`/
     `signal.` targeting a pid not owned by the caller's own launch; (c) launches a CUDA/GPU python
     process (`torch`, `cuda`, `uv run python scripts/*` with a model path, `nvidia-smi --gpu-reset`)
     while `nvidia-smi --query-compute-apps=pid --format=csv,noheader` is non-empty ("GPU busy" guard);
     (d) uses `nohup`/`&`/`setsid`/`disown` when the env var `STENCIL_SUBAGENT=1` is set.
     Emit a one-line JSON deny reason. Unit-test the guard's decision function on a table of ~25 command
     lines (CPU, no GPU).
   - `src/stencil/determinism.py`: add `assert_gpu_free_or_owned()` that raises unless the GPU has no
     other compute apps or `STENCIL_GPU_OWNER=<pid>` matches; call it from every GPU entry script's
     main() (scripts/ledger_eval.py, ledger_kv_probe.py, b3_deficit_conf.py, b4_multiif.py, b4_ifeval.py).
     CPU test with a monkeypatched nvidia-smi.
   - `tests/test_no_kill_patterns.py`: fail if any file under scripts/ src/ tools/ (excluding archive/)
     contains `os.kill(`, `signal.SIG`, `pkill`, `killall`, or a watchdog loop that terminates other pids.
   - `tests/test_sealed_guard.py`: extend to assert the sealed file's sha256 equals pins-manifest and its
     mode is 0444 (chmod it 0444 in the same change).
   - `tests/test_no_side_effect_imports.py`: extend to ALL scripts/*.py (currently one script); move
     scripts/b3_deficit_conf.py top-level work (lines ~87-122) under `def main()` + `if __name__` guard.
2. ROUND 7 validity gate (C1) in scripts/ledger_eval.py per LEDGER-PLAN.md "ROUND 7 AMENDMENT":
   timeouts absolute <= 2% per arm; truncation = excess-over-base <= +0.02 per treatment arm with
   t_base recorded from the base records; truncated turns scored as-is, never excluded; both reported in
   summary. Keep the constant names; add `MAX_EXCESS_TRUNCATION_OVER_BASE = 0.02`. Update
   tests/test_ledger_eval.py: a fixture where base truncates 10% and a treatment 11% PASSES; base 10%
   and treatment 13% FAILS; timeouts 3% FAILS regardless.
3. KV probe v3 prep (C6) in scripts/ledger_kv_probe.py: exact-column mass matching for pinned_control
   (match the deduplicated surviving-column count exactly per session; assert it), `--dose` list
   (default 0.5,1.0,3.0) producing arms pinned_wave_d{dose}, `--max-new` default 512, token IDs
   (history + generated) in each record, full provenance hash set (determinism.py, tokenizer.json,
   bench.py, ctrb.py, ledger_kv_probe.py, salience2 weights, vendored verifier tree), docstring lists all
   arms, and the registered kill rule in meta: `wave_kill_rule = "degenerate sessions > 2/20 at best dose"`.
   Add a paired bootstrap CI for (pinned - pinned_control) to the summary. CPU tests only for the
   control-matching function and the record schema (no model load).

## Allowlist
See isolation-and-gates.allow.

## Tests first (TDD, rule 1)
Write every test above RED before the implementation; commit order is test-then-impl within one PR.
Existing suite must stay green: `set -o pipefail; uv run pytest -q tests/`.

## GPU policy (Brian, 2026-09-02)
You MAY use the GPU to check your work ONLY when it is idle. It is BUSY at brief time (pid 2749844,
scripts/ledger_eval.py --diagnostic-only, the registered 113 slice). Before ANY GPU call run
`nvidia-smi --query-compute-apps=pid --format=csv,noheader`; if non-empty, do not launch, and use
CPU tests. Never kill, signal, or wait-loop on another process. The orchestrator will append a line
"GPU RELEASED <time>" to tools/codex-agents/isolation-and-gates.gpu when the slice finishes; you may
poll that file (read-only) instead of nvidia-smi. Allowed GPU checks when free: a 2-session
`ledger_kv_probe.py --sessions 2 --max-new 64 --out ledger-kv-probe-v3-smoke` and
`SMOKE=2 ledger_eval.py --diagnostic-only` dry runs only. No background launches.

## Acceptance
All new tests green; full suite green; `uv run ruff check`; `tools/check_acceptance.sh` unchanged in
behaviour; a smoke of the pretool guard against the 25-line table; no edits outside the allowlist.

## Ledger handoff
Append to WORKLOG.md: files touched, test counts (before/after), the RED->GREEN evidence for each new
test, whether any GPU smoke ran (with nvidia-smi evidence that it was idle), and open questions for the
sol xhigh re-verification of the ROUND 7 gate.
