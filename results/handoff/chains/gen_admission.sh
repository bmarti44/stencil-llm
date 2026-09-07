#!/usr/bin/env bash
set -u
OUT=/home/bmarti44/stencil-llm/data/classifier/relations/kimi-admission.jsonl
for d in coding writing data-analysis planning customer-support research devops legal-drafting spreadsheets email game-design recipes travel education finance healthcare-admin marketing translation qa-testing scheduling; do
  for i in 1 2 3 4; do
    seed=$(( 70000 + $(printf '%s' "$d" | cksum | cut -d' ' -f1) % 900 * 10 + i ))
    python3 /home/bmarti44/stencil-llm/data/classifier/kimi_gen_admission.py "$d" 35 "$seed" "$OUT" || echo "FAILED $d $seed"
  done
done
echo "GEN_ADMISSION_DONE $(wc -l < "$OUT") rows"
