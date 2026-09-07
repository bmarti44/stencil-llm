#!/usr/bin/env bash
set -u
S=/tmp/claude-1000/-home-bmarti44-stencil-llm/a88136df-3902-46b9-a661-86e0dc1bb53f/scratchpad
cd /home/bmarti44/stencil-llm || exit 2
for task in check40h; do
  echo "[$(date +%T)] START $task" >> "$S/chain.log"
  cat "$S/post-reboot-common.md" "$S/$task-brief.md" > "$S/$task-full.md"
  codex exec --sandbox danger-full-access -m gpt-6-astra -c model_reasoning_effort="high" - < "$S/$task-full.md" > "$S/$task.log" 2>&1
  echo "[$(date +%T)] END $task exit=$? last=$(git log --oneline -1 | cut -c1-70)" >> "$S/chain.log"
done
echo "CHAIN4_DONE" >> "$S/chain.log"
