#!/usr/bin/env bash
S=/tmp/claude-1000/-home-bmarti44-stencil-llm/a88136df-3902-46b9-a661-86e0dc1bb53f/scratchpad
cd /home/bmarti44/stencil-llm
while ! grep -q CHAIN48_DONE $S/chain48.log; do sleep 300; done
while ls results/quick-checks/*/RUNNING.flag results/larger-test/RUNNING.flag >/dev/null 2>&1; do sleep 300; done
echo "CHAIN49_START $(date)"
cat $S/post-reboot-common.md $S/check49-brief.md > $S/check49-full.md
codex exec --sandbox danger-full-access -m gpt-6-astra -C /home/bmarti44/stencil-llm "$(cat $S/check49-full.md)" > $S/check49.log 2>&1
echo "CHAIN49_DONE $(date)"
