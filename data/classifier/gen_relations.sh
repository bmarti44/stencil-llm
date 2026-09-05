#!/usr/bin/env bash
# kimi-k3 relation pass (FOCUS-3): hand-written pairwise relation data, one fresh session per call.
# Usage: bash data/classifier/gen_relations.sh <out.jsonl> [rows-per-call=40] [calls-per-domain=6]
set -u
OUT="${1:?out.jsonl}"; N="${2:-40}"; CALLS="${3:-6}"
DOMAINS=(coding writing data-analysis planning customer-support research devops legal-drafting spreadsheets email
         game-design recipes travel education finance healthcare-admin marketing translation qa-testing scheduling)
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
for d in "${DOMAINS[@]}"; do
  for i in $(seq 1 "$CALLS"); do
    seed=$(( 50000 + $(printf '%s' "$d" | cksum | cut -d' ' -f1) % 900 * 10 + i ))
    python3 "$ROOT/data/classifier/kimi_gen_relations.py" "$d" "$N" "$seed" "$OUT" || echo "FAILED $d $seed"
  done
done
echo "GEN_RELATIONS_DONE $(wc -l < "$OUT") rows"
