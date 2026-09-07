#!/usr/bin/env bash
S=/tmp/claude-1000/-home-bmarti44-stencil-llm/a88136df-3902-46b9-a661-86e0dc1bb53f/scratchpad
cd /home/bmarti44/stencil-llm
while [ ! -f results/check40k-review-fable.md ]; do sleep 120; done
while ls results/quick-checks/*/RUNNING.flag >/dev/null 2>&1; do sleep 300; done
echo "CHAIN40L_START $(date)"
cat $S/post-reboot-common.md $S/check40l-brief.md > $S/check40l-full.md
codex exec --sandbox danger-full-access -m gpt-6-astra -C /home/bmarti44/stencil-llm "$(cat $S/check40l-full.md)" > $S/check40l.log 2>&1
echo "CHAIN40L_DONE $(date)"
