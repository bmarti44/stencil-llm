# Brief: isolation-fixes — close sol's four acceptance fixes on a133a35 / 462ec76

## Objective
Implement exactly the "Acceptance fixes, in order" from results/isolation-round7-verify-sol.md (read the
whole report first; cite its line numbers in your handoff):
1. HIGH — tests/test_no_kill_patterns.py: replace the line-local watchdog check with an AST-based scan over
   scripts/ src/ tools/ (excluding archive/): flag any function or module that BOTH (a) calls
   os.kill / os.killpg / signal.pthread_kill / subprocess.*.terminate|kill / psutil.*.terminate|kill /
   invokes a shell containing pkill|killall|kill, AND (b) targets a pid not derived from its own
   subprocess.Popen/os.fork return value (heuristic: any pid literal, any pid parsed from ps/nvidia-smi
   output, any loop over pids). Add a RED fixture module under tests/fixtures/ with a normal multiline
   watchdog (poll → sleep → terminate other pid) that MUST be caught, and a legitimate self-cleanup
   (Popen(...).terminate()) that MUST pass.
2. MEDIUM — results/qwen/ledger-eval/summary.json is an old-gate artifact: add a CPU-only
   `--resummarize <outdir>` mode to scripts/ledger_eval.py that rebuilds summary.json from the committed
   per-conversation records under the ROUND 7 gate, writing separate provenance fields
   (generation_runner_sha256 preserved from the original; summarizer_sha256 = current file) and the
   new t_base / t_arm / excess fields. Run it on results/qwen/ledger-eval/ and commit the regenerated
   summary (force-add). Test: a synthetic record dir round-trips and the validity keys match the gate.
3. MEDIUM — sealed 0444 reproducibility: add tools/setup_sealed.sh (chmod 0444 + hash check against
   pins-manifest sealed_sha256) and make tests/test_sealed_guard.py validate hash FIRST and report the
   mode as a separate, clearly-labelled assertion with the setup command in its failure message.
4. MEDIUM — tools/hooks/pretool_guard.py: handle `command kill`, `builtin kill`, `\kill`, and numeric
   signals (`kill -9 123`, `kill -s TERM 123`, `kill -SIGTERM 123`) so the signal number is never read as
   a pid; add tests for each; add a module docstring section "Boundary" stating that variable splitting,
   eval, base64 and similar indirection are outside a textual guard's assurance (defense in depth only).
Do not touch anything else. Keep all existing tests green.

## Allowlist
See isolation-fixes.allow.

## Tests first (TDD, rule 1)
RED first for every item. Run ONLY targeted tests:
`set -o pipefail; uv run pytest -q tests/test_no_kill_patterns.py tests/test_pretool_guard.py tests/test_sealed_guard.py tests/test_ledger_eval.py`
DO NOT run the full suite (it exceeds the wrapper timeout).

## GPU policy
The GPU is BUSY (registered H1 run, scripts/ledger_kv_probe.py, do not touch). CPU only for this brief;
do not launch any model process. Foreground only. Never terminate or signal any process.

## Acceptance
Targeted tests green; ruff clean on touched files; the regenerated summary committed; no edits outside
the allowlist; commit your work yourself before finishing.

## Ledger handoff
Append to WORKLOG.md: files touched, RED->GREEN evidence per item, the re-summarized 113 validity verdict
under ROUND 7 (which arms pass the truncation excess cap), and anything sol's fix list asked for that you
could not do, with the reason.
