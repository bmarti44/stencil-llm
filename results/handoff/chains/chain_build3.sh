#!/usr/bin/env bash
S=/tmp/claude-1000/-home-bmarti44-stencil-llm/a88136df-3902-46b9-a661-86e0dc1bb53f/scratchpad
cd /home/bmarti44/stencil-llm
while ! grep -q BUILD2_DONE $S/chain_build2.log; do sleep 120; done
echo "BUILD3_START $(date)"
codex exec --sandbox danger-full-access -m gpt-6-astra -C /home/bmarti44/stencil-llm "$(cat $S/build-day3-brief.md)" > $S/build-day3.log 2>&1
echo "BUILD3_DONE $(date)"
