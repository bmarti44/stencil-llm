#!/usr/bin/env bash
# Sequential post-reboot chain: check 40d -> 40e -> 42 -> relation classifier retrain. Each codex task gets the
# common post-reboot note prepended. Logs per task in the scratchpad. Never signals anything.
set -u
S=/tmp/claude-1000/-home-bmarti44-stencil-llm/a88136df-3902-46b9-a661-86e0dc1bb53f/scratchpad
cd /home/bmarti44/stencil-llm || exit 2
for task in check40d check41c check40e check42 relations-calib; do
  echo "[$(date +%T)] START $task" >> "$S/chain.log"
  cat "$S/post-reboot-common.md" "$S/$task-brief.md" > "$S/$task-full.md"
  codex exec --sandbox danger-full-access -m gpt-6-astra -c model_reasoning_effort="high" - < "$S/$task-full.md" > "$S/$task.log" 2>&1
  echo "[$(date +%T)] END $task exit=$? last=$(git log --oneline -1 | cut -c1-70)" >> "$S/chain.log"
done
echo "CHAIN_DONE" >> "$S/chain.log"
