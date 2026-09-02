# Brief: isolation-fixes-2 — close the two residuals from results/isolation-round7-verify2-sol.md

## Objective
Read results/isolation-round7-verify2-sol.md fully (sections "1. HIGH ... OPEN" and "4. MEDIUM ... OPEN",
including every residual probe string sol lists) and close exactly those residuals:
1. HIGH — tests/kill_pattern_scanner.py: (a) resolve import aliases (`from os import kill as k`,
   `import os as o`, `from signal import pthread_kill`, `from subprocess import Popen as P` etc.) by
   tracking name bindings per module before scanning calls; (b) restore non-Python scanning: every
   *.sh / *.bash / shell heredoc inside Python strings under scripts/ src/ tools/ (excluding archive/)
   is scanned for pkill|killall|kill at command position with a pid not derived from `$!`/`$$`; add RED
   fixtures for the aliased multiline watchdog and a shell watchdog, plus a legit `kill $!` cleanup that
   must pass. Use sol's exact zero-hit example as the first RED fixture.
2. MEDIUM — tools/hooks/pretool_guard.py: tokenize wrapper options properly (`sudo -u x`, `sudo -n`,
   `env -i X=1`, `xargs -I{} -n1`, `command -p`, `nice -n 5`, `timeout 5`) before locating the process
   name; parse `kill -n <sig>` and `kill -<sig>` so signal numbers are never pids; add a decision-table
   case for every residual string sol lists (deny when the pid is not owned, allow when owned).
Do not touch anything else; keep all existing tests green.

## Allowlist
See isolation-fixes-2.allow.

## Tests first (TDD, rule 1)
RED first for every item. Run ONLY: `set -o pipefail; uv run pytest -q tests/test_no_kill_patterns.py tests/test_pretool_guard.py`.
DO NOT run the full suite.

## GPU policy
GPU is BUSY (registered H1 run). CPU only; no model process; foreground only; never terminate or signal
any process.

## Acceptance
Targeted tests green (new RED fixtures now GREEN); ruff clean on touched files; no edits outside the
allowlist; commit your work yourself before finishing.

## Ledger handoff
Append to WORKLOG.md: files touched, RED->GREEN evidence per residual, and any of sol's listed probes you
could not make deny/allow correctly, with the reason.
