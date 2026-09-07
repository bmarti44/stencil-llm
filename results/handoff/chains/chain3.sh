#!/usr/bin/env bash
# Chain 3: waits for chain 2 (CHAIN_DONE), then runs check 40f (release via bias + masking).
set -u
S=/tmp/claude-1000/-home-bmarti44-stencil-llm/a88136df-3902-46b9-a661-86e0dc1bb53f/scratchpad
cd /home/bmarti44/stencil-llm || exit 2
until grep -q CHAIN_DONE "$S/chain.log" 2>/dev/null; do sleep 60; done
for task in check43b check40f; do
  echo "[$(date +%T)] START $task" >> "$S/chain.log"
  cat "$S/post-reboot-common.md" "$S/$task-brief.md" > "$S/$task-full.md"
  codex exec --sandbox danger-full-access -m gpt-6-astra -c model_reasoning_effort="high" - < "$S/$task-full.md" > "$S/$task.log" 2>&1
  echo "[$(date +%T)] END $task exit=$? last=$(git log --oneline -1 | cut -c1-70)" >> "$S/chain.log"
done
echo "CHAIN3_DONE" >> "$S/chain.log"
