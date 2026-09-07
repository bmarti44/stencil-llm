#!/usr/bin/env bash
S=/tmp/claude-1000/-home-bmarti44-stencil-llm/a88136df-3902-46b9-a661-86e0dc1bb53f/scratchpad
cd /home/bmarti44/stencil-llm
while ! git ls-files --error-unmatch data/classifier/heldout/fable-relations-heldout-3.jsonl >/dev/null 2>&1; do sleep 300; done
while ! grep -q CHAIN44C_DONE $S/chain44c.log; do sleep 300; done
while ls results/quick-checks/*/RUNNING.flag >/dev/null 2>&1; do sleep 300; done
echo "CHAIN_REL3_START $(date)"
cat $S/post-reboot-common.md $S/relations-v3-brief.md > $S/relations-v3-full.md
codex exec --sandbox danger-full-access -m gpt-6-astra -C /home/bmarti44/stencil-llm "$(cat $S/relations-v3-full.md)" > $S/relations-v3.log 2>&1
echo "CHAIN_REL3_DONE $(date)"
