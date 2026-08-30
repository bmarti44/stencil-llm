#!/bin/bash
set -u
R=/home/bmarti44/stencil-llm
S=$R/results/logs/t1-collect-status.txt
: > "$S"
for B in train calib; do
  echo "START $B $(date -Is)" >> "$S"
  if BLOCK=$B uv run python "$R/scripts/t1_collect.py" > "$R/results/logs/t1-collect-$B.log" 2>&1; then
    echo "OK $B $(date -Is)" >> "$S"
  else
    echo "FAIL $B $(date -Is)" >> "$S"; exit 1
  fi
done
echo "DONE $(date -Is)" >> "$S"
