#!/bin/bash
# Exp 4C qualification (REGISTRATION-4C.md): 44 generations through the package, once.
# Resumable: unfinished prescribed calls only; the script enforces the 3,600 s resident
# allowance from its own receipts (watchdog) and refuses once the report exists.
set -u
export STENCIL_GPU_SHARE=1
R=/home/bmarti44/stencil-llm; cd $R
LOG=${STENCIL_LOG_DIR:-$R/results/memorycode-long/logs}; mkdir -p $LOG
[ -f $R/results/memorycode-long/qualification-4c.json ] && { echo "qualification exists" >> $LOG/exp4c-qualify.log; touch $LOG/exp4c-qualify.done; exit 0; }
bash $R/tools/gpu_reserve.sh stencil-exp4c-qualify 55 32 -- $R/.venv/bin/python $R/scripts/memorycode_4c_qualify.py >> $LOG/exp4c-qualify.log 2>&1
status=$?
echo "qualify exit=$status $(date -u +%FT%TZ)" >> $LOG/exp4c-qualify.log
touch $LOG/exp4c-qualify.done
exit $status
