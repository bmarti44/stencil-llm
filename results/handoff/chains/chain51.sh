#!/usr/bin/env bash
S=/tmp/claude-1000/-home-bmarti44-stencil-llm/a88136df-3902-46b9-a661-86e0dc1bb53f/scratchpad
cd /home/bmarti44/stencil-llm
while ! grep -q PILOT6_DONE $S/chain_pilot6.log; do sleep 300; done
while ls results/quick-checks/*/RUNNING.flag results/larger-test/RUNNING.flag >/dev/null 2>&1; do sleep 120; done
echo "CHECK51_START $(date)"
cat $S/post-reboot-common.md $S/check51-brief.md > $S/check51-full.md
codex exec --sandbox danger-full-access -m gpt-6-astra -C /home/bmarti44/stencil-llm "$(cat $S/check51-full.md)" > $S/check51.log 2>&1
echo "CHECK51_DONE $(date)"
