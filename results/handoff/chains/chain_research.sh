#!/usr/bin/env bash
S=/tmp/claude-1000/-home-bmarti44-stencil-llm/a88136df-3902-46b9-a661-86e0dc1bb53f/scratchpad
cd /home/bmarti44/stencil-llm
while ! grep -q PILOT5_DONE $S/chain_pilot5.log; do sleep 300; done
for n in 48 49 50; do
  while ls results/quick-checks/*/RUNNING.flag results/larger-test/RUNNING.flag >/dev/null 2>&1; do sleep 300; done
  echo "RESEARCH_${n}_START $(date)"
  cat $S/post-reboot-common.md $S/check$n-real.md > $S/check$n-full.md
  codex exec --sandbox danger-full-access -m gpt-6-astra -C /home/bmarti44/stencil-llm "$(cat $S/check$n-full.md)" > $S/check$n.log 2>&1
  echo "RESEARCH_${n}_DONE $(date)"
done
echo "CHAIN_RESEARCH_DONE $(date)"
