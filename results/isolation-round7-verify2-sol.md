# Isolation / ROUND 7 / KV probe v3 verification 2 (sol, xhigh)

**Target:** `001c854883dfeb27309005aa6be9edd4821e9652` (`fix: close round 7 isolation findings`), parent `8beaeb365dcf644fe9e8170dbbfaab4692010c62`.

**Verdict: REJECT.** Fixes 2 and 3 are closed. Fix 1 remains open at HIGH because an ordinary imported `os.kill` alias gives a zero-hit multiline watchdog, and the replacement gate also dropped all non-Python scanning. Fix 4 remains open at MEDIUM because the prior required option-bearing `sudo`/`env`/`xargs` forms still bypass the guard and Bash's `kill -n <number>` form still treats the signal number as a target PID.

## Scope and method

- Read the target diff, the prior report, the archived governing protocol, the test fixtures, and the committed 113-record artifact. The pre-existing dirty `WORKLOG.md` and untracked `tools/codex-agents/isolation-and-gates.gpu` were not touched or used as evidence.
- CPU only, foreground only, with `CUDA_VISIBLE_DEVICES=''` on the combined test run. I launched no model or GPU process, queried no live GPU state, sent no signal, and terminated no process. Guard probes were strings passed to `decision()` and were never executed.
- The only repository file written by this verification is this report. Fresh-checkout and re-summarization reproductions used temporary directories outside the repository.

## 1. HIGH — watchdog-pattern scanner: OPEN

### What now works

The new scanner is genuinely AST-based. It recognizes direct process methods and Python/shell termination APIs at `tests/kill_pattern_scanner.py:105-145`, finds unsafe calls per function at `:148-169`, and propagates danger through named helper calls at `:170-182`. Locally created `subprocess.Popen` objects and `os.fork` PIDs are classified as owned at `:48-85`.

The committed fixture produced exactly these positive hits:

```text
tests/fixtures/watchdog_patterns.py:16:watchdog_other_pid
tests/fixtures/watchdog_patterns.py:25:kill_literal_pid
tests/fixtures/watchdog_patterns.py:32:kill_pid_parsed_from_nvidia_smi
```

Thus the multiline/direct shell case, literal PID, and PID parsed from `nvidia-smi` are caught. `cleanup_own_child` (`tests/fixtures/watchdog_patterns.py:19-21`) and `cleanup_forked_child` (`:35-37`) produced no hits, as required by `test_multiline_watchdog_fixture_is_caught_but_own_child_cleanup_passes` at `tests/test_no_kill_patterns.py:33-40`. The existing cross-function owned-child chain is explicitly allowlisted by path and scope at `tests/test_no_kill_patterns.py:7-13`.

The focused test `test_no_kill_or_cross_process_watchdog_patterns` also passes. Manual trials establish that call propagation works even though the committed synthetic fixture does not itself test a delegated helper:

| Trial | Watchdog shape | Scanner result |
|---:|---|---|
| 1 | helper calls `os.kill(pid, ...)`; watchdog calls helper | hits helper and watchdog |
| 2 | helper calls `proc.terminate()`; watchdog calls helper | hits helper and watchdog |
| 3 | `from os import kill`; multiline watchdog calls `kill(pid, SIGTERM)` | **no hits** |

The third trial was:

```python
from os import kill
from signal import SIGTERM

def watchdog(pid):
    while alive(pid):
        kill(pid, SIGTERM)
```

`scan_python_path()` returned `[]`. This is not encoded, dynamic, or `eval`-based indirection; it is an ordinary import style. The cause is exact: `_unsafe_termination()` recognizes only the dotted names `os.kill`, `os.killpg`, and `signal.pthread_kill`, while its generic `kill` handling requires an `ast.Attribute` (`tests/kill_pattern_scanner.py:128-145`). It does not resolve `ImportFrom` aliases represented as `ast.Name` calls.

There is also a regression in coverage: the gate now traverses only `*.py` (`tests/test_no_kill_patterns.py:23-27`). Its parent scanned `.py`, `.sh`, `.json`, `.toml`, `.yaml`, and `.yml` (`001c854^:tests/test_no_kill_patterns.py:7,19-25`). A literal `pkill`, `killall`, or `kill -...` added to a shell launcher is therefore invisible to the replacement gate.

**Exact residual:** resolve ordinary imported termination aliases (at minimum `from os import kill`/`killpg`) and restore a non-Python textual backstop for shell/config launch surfaces. Add a positive committed cross-helper watchdog case so call propagation cannot regress vacuously. Until then, the original HIGH mechanical-backstop finding is not closed.

## 2. MEDIUM — CPU re-summarization and ROUND 7 artifact: CLOSED

`--resummarize` is registered at `scripts/ledger_eval.py:116-133`; `resummarize()` loads `meta.json` and all `conv-*.json` records, preserves generation provenance, stamps current summarizer provenance, reuses `summarize()`, writes `t_base` / `t_arm` / `excess`, and atomically replaces the summary at `scripts/ledger_eval.py:608-653`. The CLI branches into it before the GPU assertion or any model imports at `:656-666`. This is protected by:

- `test_resummarize_round_trips_records_with_round7_gate` (`tests/test_ledger_eval.py:907-934`)
- `test_resummarize_cli_is_cpu_only` (`tests/test_ledger_eval.py:937-947`)

Separate provenance is present in `results/qwen/ledger-eval/summary.json:56-57`:

- `generation_runner_sha256 = eedecc7300e63feed91840186ee6bed5ee37e85a0d2eb045845cf19339fbfb90`, equal to `meta.json`'s original `provenance["ledger_eval.py"]`.
- `summarizer_sha256 = 433818707b3d20f41590a23b9e0de50277bf0c75a7929c3a82ed7bb87f067496`, independently equal to the SHA-256 of the target `scripts/ledger_eval.py`.

The explicit ROUND 7 fields are committed at `results/qwen/ledger-eval/summary.json:398-407`. Independent counting directly over the 113 `conv-*.json` records gives 221 late turns and zero timeouts in every arm:

| arm | truncated | `t` | excess over base | ROUND 7 result |
|---|---:|---:|---:|---|
| base | 19/221 | 0.0859728506787330 (0.0860) | reference | reference; no absolute truncation cap |
| text_ledger | 21/221 | 0.0950226244343891 (0.0950) | 0.0090497737556561 | **PASS** |
| neural_ledger | 24/221 | 0.1085972850678733 (0.1086) | 0.0226244343891403 | **FAIL** |
| specificity | 20/221 | 0.0904977375565611 (0.0905) | 0.0045248868778281 | **PASS** |

These values exactly equal the committed `t_base`, `t_arm`, and `excess`. The artifact correctly records text/specificity `true`, neural `false`, and aggregate truncation validity `false` at `summary.json:369-374`. The 2-point rule is implemented unchanged at `scripts/ledger_eval.py:460-465,490-504`.

As an end-to-end CPU check, running the exact CLI on a temporary copy of the committed record directory regenerated a byte-identical `summary.json`; both files had SHA-256 `2d16bb87b461bcab6ab916b53befed23c0fdb98bdd65d64b3d1165747b704c35`.

## 3. MEDIUM — sealed hash/mode setup: CLOSED

`tools/setup_sealed.sh:4-13` resolves the repository paths, reads `sealed_sha256`, computes the actual SHA-256, and exits on mismatch. Only after that branch does it describe the same-UID limitation and run `chmod 0444` (`:15-17`). The script is tracked executable (`100755`).

The tests now separate the claims:

- `test_sealed_ifeval_hash_matches_manifest` uses `_assert_sealed_hash_matches_manifest` at `tests/test_sealed_guard.py:33-41`.
- `test_sealed_ifeval_mode_is_read_only_after_hash_validation` first calls the hash assertion, then checks mode, with the exact failure instruction `run tools/setup_sealed.sh after checkout` at `:44-49`.
- `test_setup_sealed_verifies_hash_before_chmod` checks source ordering at `:52-56`.

Independent hash recomputation gives `67ffeee0fcb87c317c5b08a2de85557b4a7e96ada6178aa645b4954fe4b53d49`, exactly matching `pins-manifest.json`.

Fresh-tree reproduction from `git archive 001c854`:

1. The Git entry is ordinary mode `100644`; with this environment's umask it materialized writable as `0664`.
2. Before setup, the mode test failed as expected and printed `sealed mode mismatch: run tools/setup_sealed.sh after checkout`.
3. `tools/setup_sealed.sh` reported `sealed hash verified; mode set to 0444` and the resulting mode was `0444`.
4. The three focused hash/mode/setup-order tests then passed (`3 passed`).

The mode is therefore reproducible after a fresh checkout through the documented command, without conflating it with hash integrity or claiming it is a security boundary.

## 4. MEDIUM — PreToolUse process parsing and boundary: OPEN

### What now works

The module docstring has the explicit `Boundary` section at `tools/hooks/pretool_guard.py:2-10`. It names variable splitting, `eval`, base64 payloads, command substitution, nested shells, and the defense-in-depth limitation. `test_textual_guard_boundary_is_explicit` enforces the key wording at `tests/test_pretool_guard.py:83-87`.

The parser now uses `shlex` and recognizes `builtin`, `command`, `exec`, `sudo`, `env`, and `xargs` as wrappers at `tools/hooks/pretool_guard.py:70-96`. The new decision-table rows at `tests/test_pretool_guard.py:55-63` pass for:

- `command kill 123`, `builtin kill 123`, and `\kill 123`: denied when unowned and allowed when PID 123 is owned.
- `kill -9 123`, `kill -s TERM 123`, and `kill -SIGTERM 123`: allowed when PID 123 is owned, without treating the registered signal spellings as PIDs.

The five earlier probes now produce:

| earlier probe | result now | assessment |
|---|---|---|
| variable-built sealed path | allowed | disclosed boundary |
| `command kill 123` | denied | fixed |
| variable-built Python command with simulated busy GPU | allowed | disclosed boundary |
| split `nohup` spelling under `STENCIL_SUBAGENT=1` | allowed | disclosed boundary |
| `kill -9 123`, owned set `{123}` | allowed | fixed |

### Residual from the prior required fix

The prior report explicitly required recognition of **option-bearing** `sudo`/`env`/`xargs` command positions. The implementation skips wrapper and option tokens but does not consume option operands (`tools/hooks/pretool_guard.py:77-95`). Decision-only probes returned `None` (allowed) for all three unowned termination commands:

```text
sudo -u root kill 123
env -u NAME kill 123
printf 123 | xargs -n 1 kill
```

The numeric-signal parser also recognizes `-s`/`--signal` specially but otherwise skips only the option token (`tools/hooks/pretool_guard.py:97-113`). Bash's valid numeric form `kill -n 9 123`, with owned set `{123}`, was denied because `9` was still parsed as an unowned target PID.

**Exact residual:** consume option arguments while locating the command behind `sudo`, `env`, and `xargs`, and handle `kill -n <signum>` the same way as `kill -s <sigspec>`/`--signal <sigspec>`. Add these four rows to the decision table. The named new cases and documentation close part of the finding, but the prior option-bearing requirement and numeric-signal class are not fully closed.

## Prior science checks and regression evidence

- **ROUND 7 gate unchanged:** the target diff does not alter `summarize()`; it only adds argument parsing, `resummarize()`, and the intentional CPU branch. The registered math remains at `scripts/ledger_eval.py:460-465,490-504,543-552`. The four original ROUND 7 fixtures remain at `tests/test_ledger_eval.py:245-283`; the target only appends the two re-summarization tests.
- **GPU ownership assertion unchanged for generation:** `src/stencil/determinism.py` and `tests/test_determinism_gpu_guard.py` have byte-identical Git blobs in parent and target (`a5a1b211...` and `65c12de5...`). `scripts/b3_deficit_conf.py`, `scripts/b4_multiif.py`, and `scripts/b4_ifeval.py` are also byte-identical. The normal `ledger_eval` path still asserts ownership before runtime/model imports at `scripts/ledger_eval.py:662-666`; only the explicitly CPU-only re-summary path bypasses it.
- **KV probe v3 preparation unchanged:** `scripts/ledger_kv_probe.py` and `tests/test_ledger_kv_probe.py` are byte-identical in parent and target (`d8bc4f5b...` and `6bea8d934...`). The registered doses/max-new and arms remain at `scripts/ledger_kv_probe.py:34-57`; provenance at `:75-105`; exact disjoint control-column checks at `:168-188,236-267,416-445`; recorded token IDs at `:228-264,446-454`; paired bootstrap at `:280-305,467`; and best-dose `> 2` kill rule at `:462-467`.
- **Import/fixture guard unchanged:** `tests/test_no_side_effect_imports.py` is byte-identical (`314c38f3...`) and its registered legacy xfail remains the sole xfail.

CPU-only combined command:

```text
CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 uv run pytest -q -p no:cacheprovider \
  tests/test_ledger_eval.py tests/test_determinism_gpu_guard.py \
  tests/test_pretool_guard.py tests/test_no_kill_patterns.py \
  tests/test_sealed_guard.py tests/test_no_side_effect_imports.py \
  tests/test_ledger_kv_probe.py
```

Result: **119 passed, 1 xfailed, 1 warning in 9.60s**. The xfail is the registered legacy import inventory; the warning is the pre-existing invalid escape warning in `scripts/b2_gsm8k.py`. Ruff over every changed Python file passed, and `bash -n tools/setup_sealed.sh` passed.

## Final verdict

**REJECT.** Fix 1 is **OPEN (HIGH)** and fix 4 is **OPEN (MEDIUM)** with the exact residuals above. Fixes 2 and 3 are **CLOSED**. The prior ROUND 7 science, GPU assertion, fixtures, and KV-probe-v3 preparation remain intact.
