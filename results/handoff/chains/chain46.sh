#!/usr/bin/env bash
S=/tmp/claude-1000/-home-bmarti44-stencil-llm/a88136df-3902-46b9-a661-86e0dc1bb53f/scratchpad
cd /home/bmarti44/stencil-llm
while [ -d /proc/$(cat $S/pilot4.pid) ]; do sleep 300; done
while ls results/quick-checks/*/RUNNING.flag results/larger-test/RUNNING.flag >/dev/null 2>&1; do sleep 300; done
echo "CHAIN46_START $(date)"
cat $S/post-reboot-common.md $S/check46-brief.md > $S/check46-full.md
codex exec --sandbox danger-full-access -m gpt-6-astra -C /home/bmarti44/stencil-llm "$(cat $S/check46-full.md)" > $S/check46.log 2>&1
echo "CHAIN46_DONE $(date)"
