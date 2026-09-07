#!/usr/bin/env bash
set -u
OUT=/home/bmarti44/stencil-llm/data/classifier/relations/kimi-overrides.jsonl
for d in coding writing data-analysis planning customer-support devops spreadsheets email scheduling qa-testing; do
  for i in 1 2 3; do
    seed=$(( 80000 + $(printf '%s' "$d" | cksum | cut -d' ' -f1) % 900 * 10 + i ))
    python3 /home/bmarti44/stencil-llm/data/classifier/kimi_gen_transitions.py "$d" 40 "$seed" "$OUT" || echo "FAILED $d $seed"
  done
done
echo "GEN_OVERRIDES_DONE $(wc -l < "$OUT") rows"
