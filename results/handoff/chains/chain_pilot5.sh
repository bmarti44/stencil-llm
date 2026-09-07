#!/usr/bin/env bash
S=/tmp/claude-1000/-home-bmarti44-stencil-llm/a88136df-3902-46b9-a661-86e0dc1bb53f/scratchpad
cd /home/bmarti44/stencil-llm
while [ ! -f $S/pilot5.GO ]; do sleep 120; done
while ls results/quick-checks/*/RUNNING.flag results/larger-test/RUNNING.flag >/dev/null 2>&1; do sleep 300; done
echo "PILOT5_START $(date)"
cat $S/post-reboot-common.md $S/pilot5-brief.md > $S/pilot5-full.md
codex exec --sandbox danger-full-access -m gpt-6-astra -C /home/bmarti44/stencil-llm "$(cat $S/pilot5-full.md)" > $S/pilot5.log 2>&1
echo "PILOT5_DONE $(date)"
