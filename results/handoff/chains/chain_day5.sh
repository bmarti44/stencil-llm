#!/usr/bin/env bash
S=/tmp/claude-1000/-home-bmarti44-stencil-llm/a88136df-3902-46b9-a661-86e0dc1bb53f/scratchpad
cd /home/bmarti44/stencil-llm
while [ -d /proc/$(cat $S/build-day4b.pid) ]; do sleep 120; done
while ls results/quick-checks/*/RUNNING.flag >/dev/null 2>&1 || ! grep -q CHAIN40L_DONE $S/chain40l.log; do sleep 300; done
echo "DAY5_START $(date)"
cat $S/post-reboot-common.md $S/build-day5-brief.md > $S/build-day5-full.md
codex exec --sandbox danger-full-access -m gpt-6-astra -C /home/bmarti44/stencil-llm "$(cat $S/build-day5-full.md)" > $S/build-day5.log 2>&1
echo "DAY5_DONE $(date)"
