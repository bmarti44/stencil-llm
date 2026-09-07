#!/usr/bin/env bash
set -u
R=/home/bmarti44/stencil-llm/data/classifier
for d in woodworking beekeeping aquarium-keeping home-brewing sailing amateur-astronomy pottery knitting model-trains rock-climbing birdwatching gardening chess-club community-theatre car-restoration; do
  for i in 1 2; do
    seed=$(( 120000 + $(printf '%s' "$d" | cksum | cut -d' ' -f1) % 900 * 10 + i ))
    python3 $R/kimi_gen_admission3.py "$d" 35 "$seed" $R/relations/kimi-admission-3.jsonl || echo "FAILED adm $d $seed"
    python3 $R/kimi_gen_transitions3.py "$d" 35 "$seed" $R/relations/kimi-transitions-3.jsonl || echo "FAILED rel $d $seed"
  done
done
echo "GEN_PASS3_DONE adm=$(wc -l < $R/relations/kimi-admission-3.jsonl) rel=$(wc -l < $R/relations/kimi-transitions-3.jsonl)"
