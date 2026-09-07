#!/usr/bin/env bash
S=/tmp/claude-1000/-home-bmarti44-stencil-llm/a88136df-3902-46b9-a661-86e0dc1bb53f/scratchpad
cd /home/bmarti44/stencil-llm
while ls results/quick-checks/*/RUNNING.flag results/larger-test/RUNNING.flag >/dev/null 2>&1; do sleep 120; done
echo "LARGER2_START $(date)"
cat $S/post-reboot-common.md $S/larger-test-v2-brief.md > $S/larger-test-v2-full.md
codex exec --sandbox danger-full-access -m gpt-6-astra -C /home/bmarti44/stencil-llm "$(cat $S/larger-test-v2-full.md)" > $S/larger-test-v2.log 2>&1
echo "LARGER2_DONE $(date)"
