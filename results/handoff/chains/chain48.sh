#!/usr/bin/env bash
S=/tmp/claude-1000/-home-bmarti44-stencil-llm/a88136df-3902-46b9-a661-86e0dc1bb53f/scratchpad
cd /home/bmarti44/stencil-llm
while ! grep -q GEN_PASS3_DONE $S/gen_pass3.log; do sleep 300; done
while ! git ls-files --error-unmatch data/classifier/heldout/fable-relations-heldout-4.jsonl >/dev/null 2>&1; do sleep 300; done
while ! grep -q CHAIN47_DONE $S/chain47.log; do sleep 300; done
while ls results/quick-checks/*/RUNNING.flag results/larger-test/RUNNING.flag >/dev/null 2>&1; do sleep 300; done
echo "CHAIN48_START $(date)"
cat $S/post-reboot-common.md $S/check48-brief.md > $S/check48-full.md
codex exec --sandbox danger-full-access -m gpt-6-astra -C /home/bmarti44/stencil-llm "$(cat $S/check48-full.md)" > $S/check48.log 2>&1
echo "CHAIN48_DONE $(date)"
