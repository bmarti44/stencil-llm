#!/usr/bin/env bash
S=/tmp/claude-1000/-home-bmarti44-stencil-llm/a88136df-3902-46b9-a661-86e0dc1bb53f/scratchpad
cd /home/bmarti44/stencil-llm
while [ -d /proc/$(cat $S/docker-pull.pid) ]; do sleep 120; done
grep -q -i "error\|denied\|not found" $S/docker-pull.log && { echo "PULL_FAILED"; exit 1; }
while [ -d /proc/$(cat $S/pilot2.pid) ] || ls results/quick-checks/*/RUNNING.flag >/dev/null 2>&1; do sleep 300; done
echo "VLLM_QUAL_START $(date)"
cat $S/post-reboot-common.md $S/vllm-qual-brief.md > $S/vllm-qual-full.md
codex exec --sandbox danger-full-access -m gpt-6-astra -C /home/bmarti44/stencil-llm "$(cat $S/vllm-qual-full.md)" > $S/vllm-qual.log 2>&1
echo "VLLM_QUAL_DONE $(date)"
