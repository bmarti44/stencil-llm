#!/bin/bash
set -u
R=/home/bmarti44/stencil-llm
S=$R/results/logs/w1-train-status.txt
: > "$S"
for O in ce proxy; do
  echo "START $O $(date -Is)" >> "$S"
  if OBJ=$O uv run python "$R/scripts/w1_train.py" > "$R/results/logs/w1-train-$O.log" 2>&1; then
    echo "OK $O $(date -Is)" >> "$S"
  else
    echo "FAIL $O $(date -Is)" >> "$S"; exit 1
  fi
done
echo "DONE $(date -Is)" >> "$S"
