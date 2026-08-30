#!/bin/bash
# T2b registered rerun after the import-side-effect fix (2026-08-30).
set -u
R=/home/bmarti44/stencil-llm
L=$R/results/logs
S=$L/t2b-r2-status.txt
: > "$S"
cd "$R"
run_step() {
  name=$1; shift
  echo "START $name $(date -Is)" >> "$S"
  if env "$@" > "$L/$name.log" 2>&1; then
    echo "OK $name $(date -Is)" >> "$S"
  else
    echo "FAIL $name $(date -Is)" >> "$S"
    exit 1
  fi
}
run_step t2b-train-r2 T2B=1 uv run python "$R/scripts/t2_train_selector.py"
run_step t2b-recal-r2 T2B=1 uv run python "$R/scripts/t2_recalibrate.py"
run_step t2b-shakeout-r2 T2B=1 uv run python "$R/scripts/t2_shakeout.py"
run_step t2b-val-r2 T2B=1 VAL=1 uv run python "$R/scripts/t2_shakeout.py"
echo "CHAIN DONE $(date -Is)" >> "$S"
