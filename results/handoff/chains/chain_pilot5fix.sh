#!/usr/bin/env bash
S=/tmp/claude-1000/-home-bmarti44-stencil-llm/a88136df-3902-46b9-a661-86e0dc1bb53f/scratchpad
cd /home/bmarti44/stencil-llm
echo "PILOT5FIX_START $(date)"
cat $S/post-reboot-common.md $S/pilot5fix-brief.md > $S/pilot5fix-full.md
codex exec --sandbox danger-full-access -m gpt-6-astra -C /home/bmarti44/stencil-llm "$(cat $S/pilot5fix-full.md)" > $S/pilot5fix.log 2>&1
echo "PILOT5FIX_DONE $(date)"
