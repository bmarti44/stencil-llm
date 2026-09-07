#!/usr/bin/env bash
S=/tmp/claude-1000/-home-bmarti44-stencil-llm/a88136df-3902-46b9-a661-86e0dc1bb53f/scratchpad
cd /home/bmarti44/stencil-llm
while ! grep -q GEN_ADMISSION2_DONE $S/gen_admission2.log; do sleep 300; done
while ! git ls-files --error-unmatch data/classifier/heldout/fable-admission-heldout-3.jsonl >/dev/null 2>&1; do sleep 300; done
while [ -d /proc/$(cat $S/check40j.pid) ] || ls results/quick-checks/*/RUNNING.flag >/dev/null 2>&1; do sleep 300; done
echo "CHAIN44C_START $(date)"
cat $S/post-reboot-common.md $S/check44c-brief.md > $S/check44c-full.md
codex exec --sandbox danger-full-access -m gpt-6-astra -C /home/bmarti44/stencil-llm "$(cat $S/check44c-full.md)" > $S/check44c.log 2>&1
echo "CHAIN44C_DONE $(date)"
