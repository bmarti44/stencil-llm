#!/usr/bin/env bash
S=/tmp/claude-1000/-home-bmarti44-stencil-llm/a88136df-3902-46b9-a661-86e0dc1bb53f/scratchpad
cd /home/bmarti44/stencil-llm
while [ ! -f $S/larger-test.GO ]; do sleep 120; done
while ls results/quick-checks/*/RUNNING.flag >/dev/null 2>&1; do sleep 300; done
echo "LARGER_START $(date)"
cat $S/post-reboot-common.md $S/larger-test-brief.md > $S/larger-test-full.md
codex exec --sandbox danger-full-access -m gpt-6-astra -C /home/bmarti44/stencil-llm "$(cat $S/larger-test-full.md)" > $S/larger-test.log 2>&1
echo "LARGER_DONE $(date)"
