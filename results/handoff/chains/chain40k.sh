#!/usr/bin/env bash
S=/tmp/claude-1000/-home-bmarti44-stencil-llm/a88136df-3902-46b9-a661-86e0dc1bb53f/scratchpad
cd /home/bmarti44/stencil-llm
while ! grep -q CHAIN_REL3_DONE $S/chain_rel3.log; do sleep 300; done
while ls results/quick-checks/*/RUNNING.flag >/dev/null 2>&1; do sleep 300; done
echo "CHAIN40K_START $(date)"
cat $S/post-reboot-common.md $S/check40k-brief.md > $S/check40k-full.md
codex exec --sandbox danger-full-access -m gpt-6-astra -C /home/bmarti44/stencil-llm "$(cat $S/check40k-full.md)" > $S/check40k.log 2>&1
echo "CHAIN40K_DONE $(date)"
