#!/usr/bin/env bash
# Chain 2: waits for check 40d (chain 1) to finish, stops chain 1 before it starts 40e, then runs
# 41c -> 40e -> 42 -> relations-calib sequentially. Only touches processes this session launched.
set -u
S=/tmp/claude-1000/-home-bmarti44-stencil-llm/a88136df-3902-46b9-a661-86e0dc1bb53f/scratchpad
cd /home/bmarti44/stencil-llm || exit 2
C1=$(cat "$S/chain.pid")
until grep -q "END check40d" "$S/chain.log" 2>/dev/null; do
  [ -d /proc/$C1 ] || break
  sleep 30
done
# stop chain 1 and any codex child it may have started for 40e
if [ -d /proc/$C1 ]; then
  for k in $(pgrep -P "$C1"); do kill -TERM "$k" 2>/dev/null; done
  kill -TERM "$C1" 2>/dev/null
  sleep 5
fi
echo "[$(date +%T)] chain1 stopped after 40d; chain2 begins" >> "$S/chain.log"
for task in check43 check40e check42 relations-calib; do
  echo "[$(date +%T)] START $task" >> "$S/chain.log"
  cat "$S/post-reboot-common.md" "$S/$task-brief.md" > "$S/$task-full.md"
  codex exec --sandbox danger-full-access -m gpt-6-astra -c model_reasoning_effort="high" - < "$S/$task-full.md" > "$S/$task.log" 2>&1
  echo "[$(date +%T)] END $task exit=$? last=$(git log --oneline -1 | cut -c1-70)" >> "$S/chain.log"
done
echo "CHAIN_DONE" >> "$S/chain.log"
