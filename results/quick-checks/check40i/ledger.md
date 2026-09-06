# Check40i operational ledger

2026-09-06 — PRE-INFERENCE freeze bb42c4e6: seed40080/24, Z primary, fixed20/2
thresholds and two paired release conditions, BACK controls<=4; no fitting.
Native HF CPU checks and writer->audit fixture672/480 PASS. Foreground launch
at06:27:06 UTC; resource receipt shows no compute blockers or Stencil flags,
115.06GiB available. Own pid1921303 recorded in RUNNING.flag; no signals.
Command: /home/bmarti44/stencil-llm/.venv/bin/python -u /home/bmarti44/stencil-llm/scripts/focus_check40i.py --mode run
Log: console.log, raw foreground exit preserved; cap1800s incl load/cleanup.
Other task writes in shared plan/LEDGER.md observed after our freeze; subsequent
check40i progress uses this task-local ledger to avoid committing its work.

MIDPOINT: first12 complete episodes snapshotted and CPU-audited336 records/
240 generations. All token/history/bias/mask/position scores and frozen hashes
PASS. Z SWITCH/CLEAR12 Python, BACK11 JS +1 Python, paired CLEAR11; controls
BACK JS0, no breaks. Frozen denominator24 and INCOMPLETE label preserved.
Direct runner continues unchanged; checkpoint explicitly committed while no
review/coder wrapper runs. Report CPU dummy fixture also PASS.

COMPLETE / CLOSED-RELEASE: natural foreground exit0, charged1319.300596/1800s,
flag removed. All24 episodes/672 records/480 generations/14152 tokens retained.
Z SWITCH24 Python/BACK23 JS/CLEAR24 Python, paired SWITCH24/CLEAR23; episode2
BACK/HOLD_AFTER_BACK remains Python. Controls Zc/S BACK JS0; OFF allPython.
Broken0 every step/arm, fences480/480 actual, missing parentheses/bare/echo/OK0.
Full CPU audit and independent raw-count/paired/Python-parse recount PASS;
all48 raw router layers and grouped_mm OFF equality PASS; frozen hashes match.
Five-line index and six-line WORKLOG entry complete. Explicit-path final local
commit includes force-added results; no push/signals/sealed reads/fit or rerun.
