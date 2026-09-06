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
