#!/usr/bin/env bash
set -u
OUT=/home/bmarti44/stencil-llm/data/classifier/relations/kimi-admission-2.jsonl
for d in coding writing data-analysis planning customer-support research devops spreadsheets email scheduling qa-testing marketing legal-drafting finance education; do
  for i in 1 2 3; do
    seed=$(( 90000 + $(printf '%s' "$d" | cksum | cut -d' ' -f1) % 900 * 10 + i ))
    python3 /home/bmarti44/stencil-llm/data/classifier/kimi_gen_admission.py "$d" 35 "$seed" "$OUT" || echo "FAILED $d $seed"
  done
done
echo "GEN_ADMISSION2_DONE $(wc -l < "$OUT") rows"
