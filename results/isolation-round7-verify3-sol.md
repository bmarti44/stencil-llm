# Isolation / ROUND 7 / KV probe v3 verification 3 (sol, xhigh)

**Target:** current HEAD at final reconciliation, `8e2c3572d32962b3b306137aea2022f104b5bc15`. The seven scoped isolation-fixes-2 blobs are byte-identical between `9841de1` and this HEAD. Tests ran on its source-identical parent `033b3ad`; `033b3ad..8e2c357` changes only `.gitignore`.

**Verdict: REJECT.** Fix 1 remains **OPEN (HIGH)**: the registered cases now pass, but three ordinary, non-encoded forms still produce zero scanner hits (a function-local imported `os.kill` alias, a shell `kill` used as an `if` condition, and a backslash-continued shell `kill`). Fixes 2, 3, and 4 are **CLOSED**. The ROUND 7 science and GPU-ownership checks are unchanged. A concurrent, unrelated H1-prime commit advanced HEAD during this verification and extended the KV probe; its registered oracle/v3 defaults and checks remain intact, but those two files are not byte-identical to verify2, as detailed below.

## Scope and method

- Reviewed the committed HEAD versions of exactly the seven requested files plus the prior verification, fix provenance, and the already-closed science files. `git diff 9841de1..HEAD -- <seven scoped paths>` was empty, all seven Git blob IDs matched, and the scoped paths had no working-tree diff. The final HEAD advance from the tested parent touched only `.gitignore`.
- CPU only and foreground only. `CUDA_VISIBLE_DEVICES=''` and injected/mocked guard state were used. I launched no model or GPU process, queried no live GPU state, sent no signal, and terminated no process. Every process-control probe below was an inert string passed to scanner or `decision()` code and was never executed.
- The final suite ran from `/tmp/stencil-verify3-head033.2YktKt`, made by `git archive HEAD`, so unrelated working-tree changes could not enter the evidence. Read-only links supplied the gitignored local tokenizer and base preflight records; no model was loaded. `tools/setup_sealed.sh` was run only in that temporary tree.
- The only repository file written by this verification is this report.

## 1. HIGH — watchdog-pattern scanner: OPEN

### Registered fixes that work

Import bindings are canonicalized at `tests/kill_pattern_scanner.py:30-49`. The new fixture has `from os import kill`, `import os as o`, `from os import kill as k`, `from signal import pthread_kill`, and `from subprocess import Popen as P` at `tests/fixtures/watchdog_alias_patterns.py:4-17`; unsafe alias calls are at `:8-37`, while aliased owned-child cleanup is at `:40-42`. `test_import_alias_watchdogs_are_caught_but_aliased_child_cleanup_passes` (`tests/test_no_kill_patterns.py:47-61`) passes.

The exact hits were:

```text
tests/fixtures/watchdog_alias_patterns.py:10:watchdog
tests/fixtures/watchdog_alias_patterns.py:21:watchdog_module_alias
tests/fixtures/watchdog_alias_patterns.py:25:watchdog_kill_alias
tests/fixtures/watchdog_alias_patterns.py:29:watchdog_killpg_alias
tests/fixtures/watchdog_alias_patterns.py:33:watchdog_pthread_alias
tests/fixtures/watchdog_alias_patterns.py:37:watchdog_popen_alias
```

Thus the verify2 zero-hit example now returns `['earlier_zero_hit.py:6:watchdog']`:

```python
from os import kill
from signal import SIGTERM

def watchdog(pid):
    while alive(pid):
        kill(pid, SIGTERM)
```

Owned `Popen` and `fork` cleanup remains allowed through the ownership analysis at `tests/kill_pattern_scanner.py:73-115`: `cleanup_aliased_popen_child`, `cleanup_own_child`, and `cleanup_forked_child` produced no hits, as asserted by `test_import_alias_watchdogs_are_caught_but_aliased_child_cleanup_passes` and `test_multiline_watchdog_fixture_is_caught_but_own_child_cleanup_passes` (`tests/test_no_kill_patterns.py:37-61`).

Non-Python traversal is restored for `*.sh` and `*.bash` at `tests/test_no_kill_patterns.py:21-34`. Shell ownership explicitly recognizes direct `$!`/`$$` and variables assigned from them at `tests/kill_pattern_scanner.py:224-254`. The shell fixture's foreign `$1` produces `tests/fixtures/watchdog_patterns.sh:7:shell_watchdog`, while direct and derived `$!` cleanup at `:10-18` produces no hit. Python multiline shell text is scanned at `tests/kill_pattern_scanner.py:334-342`; the heredoc fixture produces `tests/fixtures/watchdog_shell_heredoc.py:5:shell_heredoc_watchdog`, while its `$!` cleanup produces no hit. `test_shell_watchdog_and_python_shell_heredoc_are_caught_but_own_pid_passes` (`tests/test_no_kill_patterns.py:64-86`) passes.

Cross-function danger propagation remains implemented at `tests/kill_pattern_scanner.py:317-332`. However, the positive committed cross-helper fixture requested in verify2 was not added: the three new fixtures contain aliases and direct shell calls only. The implementation still has no non-vacuous committed regression assertion for that propagation path.

### Three new evasions (bounded as requested)

All three returned `[]`.

1. Function-local imported alias:

   ```python
   def watchdog(pid):
       from os import kill as k
       k(pid, 15)
   ```

   Cause: `_import_bindings()` walks only `tree.body` (`tests/kill_pattern_scanner.py:30-40`), so a normal local `ImportFrom` never enters the binding map.

2. Shell command position after the `if` reserved word:

   ```bash
   watchdog() {
       if kill "$1"; then
           echo stopped
       fi
   }
   ```

   Cause: `_shell_command_index()` handles assignments and wrappers but not shell reserved words (`tests/kill_pattern_scanner.py:202-221`), so it sees `if` as the process and never reaches `kill`.

3. Backslash-continued shell command:

   ```bash
   watchdog() {
       kill \
           "$1"
   }
   ```

   Cause: `_scan_shell_text()` tokenizes each physical line independently (`tests/kill_pattern_scanner.py:257-284`); the first line is an incomplete shlex token sequence and the second has no `kill` command token.

These are ordinary Python/shell styles, not `eval`, encoding, or dynamic API construction. Because this gate is the mechanical backstop for the prior cross-process watchdog class and still admits all three, the original HIGH is not closed.

**Exact residual:** include imports inside function scopes in alias resolution; parse shell logical lines/continuations and reserved-word command positions (at minimum `if`/`while`/`until` conditions); and add the previously requested positive committed cross-helper regression fixture.

## 2. MEDIUM — CPU re-summarization and ROUND 7 artifact: CLOSED

The Fix 2 files are byte-identical between `001c854` and HEAD: `scripts/ledger_eval.py` Git blob `f2fb9b5...`, `results/qwen/ledger-eval/summary.json` `da61063...`, and `tests/test_ledger_eval.py` `5acf03c...`.

`resummarize()` still loads records, preserves generation provenance, computes with `summarize()`, writes separate summarizer provenance plus `t_base`/`t_arm`/`excess`, and atomically replaces the summary at `scripts/ledger_eval.py:608-653`. The CLI still takes that CPU-only branch before the GPU assertion/model imports at `:656-666`. The protecting tests `test_resummarize_round_trips_records_with_round7_gate` and `test_resummarize_cli_is_cpu_only` remain at `tests/test_ledger_eval.py:907-947` and passed.

The committed artifact still records separate generation and summarizer hashes at `results/qwen/ledger-eval/summary.json:56-57`; the current summarizer SHA-256 independently remains `433818707b3d20f41590a23b9e0de50277bf0c75a7929c3a82ed7bb87f067496`. The ROUND 7 values remain at `summary.json:398-407`: base `0.08597285067873303`; text excess `0.009049773755656104` (pass); neural excess `0.022624434389140274` (fail); specificity excess `0.004524886877828052` (pass). The aggregate remains false at `:369-374`, and `primary_claim_valid` remains false at `:386-396`.

## 3. MEDIUM — sealed hash/mode setup: CLOSED

The Fix 3 files are byte-identical between `001c854` and HEAD: `tools/setup_sealed.sh` Git blob `03de8b8...` and `tests/test_sealed_guard.py` `8238753...`.

The setup resolves the pinned hash and exits on mismatch at `tools/setup_sealed.sh:4-13`, then applies `0444` only at `:15-17`. The hash, mode-after-hash, and source-order tests remain separate at `tests/test_sealed_guard.py:33-56`. In the fresh HEAD archive, setup printed `sealed hash verified; mode set to 0444`; all three tests passed. Independent SHA-256 remained `67ffeee0fcb87c317c5b08a2de85557b4a7e96ada6178aa645b4954fe4b53d49`.

## 4. MEDIUM — PreToolUse wrapper/signal parsing: CLOSED

The guard now consumes wrapper options and their operands at `tools/hooks/pretool_guard.py:70-144`, parses `-n` alongside `-s`/`--signal` without reading the signal as a PID at `:154-174`, and applies the ownership decision at `:177-219`. All corresponding rows are committed in `tests/test_pretool_guard.py:64-84` and pass under `test_decision_table` (`:88-93`).

Decision-only results (`DENY` means the PID-is-not-owned reason):

| probe | unowned | owned `{123}` |
|---|---|---|
| `sudo -u x kill 123` | DENY | ALLOW |
| `sudo -n kill 123` | DENY | ALLOW |
| `env -i X=1 kill 123` | DENY | ALLOW |
| `xargs -I{} -n1 kill` | DENY | DENY |
| `command -p kill 123` | DENY | ALLOW |
| `nice -n 5 kill 123` | DENY | ALLOW |
| `timeout 5 kill 123` | DENY | ALLOW |
| `kill -n 9 123` | DENY | ALLOW |
| `kill -9 123` | DENY | ALLOW |

The standalone `xargs -I{} -n1 kill` has neither a literal target nor literal pipeline input, so denial in both ownership states is the correct fail-closed result. Its concrete literal form, `printf 123 | xargs -I{} -n1 kill {}`, is DENY unowned and ALLOW for `{123}`.

Earlier residual probes now give the required bidirectional result:

| earlier residual | unowned | owned `{123}` |
|---|---|---|
| `sudo -u root kill 123` | DENY | ALLOW |
| `env -u NAME kill 123` | DENY | ALLOW |
| `printf 123 | xargs -n 1 kill` | DENY | ALLOW |
| `kill -n 9 123` | DENY | ALLOW |

The original five-probe table also remains consistent: `command kill 123` is now denied, and owned `kill -9 123` is allowed; variable-built sealed paths, variable-built Python, and split `nohup` remain allowed as the explicitly disclosed textual boundary at `tools/hooks/pretool_guard.py:4-9`. No Fix 4 residual was found in the requested cases.

## Science and regression evidence

`git diff --exit-code 001c854..HEAD` is empty over `scripts/ledger_eval.py`, its summary and tests, sealed setup/tests, `src/stencil/determinism.py`, `tests/test_determinism_gpu_guard.py`, the three other GPU entry scripts, and `tests/test_no_side_effect_imports.py`. Representative unchanged Git blobs are `a5a1b21...` (GPU assertion), `65c12de...` (its tests), and `314c38f...` (import guard).

- ROUND 7 timeout/truncation math remains at `scripts/ledger_eval.py:460-465,490-504`; the four non-vacuous fixtures remain `test_round7_base_10pct_treatment_11pct_truncation_passes`, `test_round7_base_10pct_treatment_13pct_truncation_fails`, `test_round7_timeouts_3pct_fail_regardless_of_truncation_baseline`, and `test_round7_truncated_turns_are_scored_as_is_and_never_excluded` at `tests/test_ledger_eval.py:245-283`.
- GPU ownership remains fail-closed at `src/stencil/determinism.py:34-60`, with free/unowned/exact-owner/extra-app/query-failure coverage at `tests/test_determinism_gpu_guard.py:12-46`. These tests monkeypatch the query; this verification did not run `nvidia-smi`.
- The concurrent H1-prime commit changed `scripts/ledger_kv_probe.py` and `tests/test_ledger_kv_probe.py` to Git blobs `fe9048c...` and `069132f...`; therefore byte-identity would be false. The registered oracle/v3 path is nevertheless preserved: default `--focus oracle`, doses `0.5/1.0/3.0`, and `max_new=512` are at `scripts/ledger_kv_probe.py:44,62-72`; the exact `> 2/20` best-dose rule remains at `:46,694-702`; exact matched controls and paired bootstrap remain at `:340-358,459-484`. The original tests remain and passed (`test_dose_list_defaults_and_arm_names`, `test_control_matches_deduplicated_surviving_columns_exactly`, `test_record_schema_has_history_and_generated_token_ids`, `test_provenance_and_registered_kill_rule`, and `test_paired_bootstrap_ci_is_session_paired_and_deterministic`, `tests/test_ledger_kv_probe.py:34-181`). The delta adds H1-prime automatic-focus coverage; it does not arise from the seven isolation fixes.
- The import/fixture guard is unchanged, and its legacy inventory remains the sole registered xfail.

Final CPU-only command on the source-identical parent of final HEAD (after hash-first sealed setup in the archive):

```text
CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider \
  tests/test_ledger_eval.py tests/test_determinism_gpu_guard.py \
  tests/test_pretool_guard.py tests/test_no_kill_patterns.py \
  tests/test_sealed_guard.py tests/test_no_side_effect_imports.py \
  tests/test_ledger_kv_probe.py
```

Result: **152 passed, 1 xfailed, 1 warning in 7.06s**. The xfail is the registered legacy import inventory; the warning is the pre-existing invalid escape warning in `scripts/b2_gsm8k.py`. Ruff with `--no-cache` over all changed Python scanner/guard files and fixtures passed.

## Final verdict

**REJECT.** Fix 1 is **OPEN (HIGH)** with the exact three zero-hit forms and missing cross-helper regression fixture stated above. Fixes 2, 3, and 4 are **CLOSED**. The orchestrator should escalate the residual to the human as directed rather than begin another fix loop.
