#!/usr/bin/env bash
S=/tmp/claude-1000/-home-bmarti44-stencil-llm/a88136df-3902-46b9-a661-86e0dc1bb53f/scratchpad
cd /home/bmarti44/stencil-llm
while ! grep -q DAY5_DONE $S/chain_day5.log; do sleep 300; done
echo "CHAIN45_START $(date)"
codex exec --sandbox danger-full-access -m gpt-6-astra -C /home/bmarti44/stencil-llm "$(cat $S/check45-brief.md)" > $S/check45.log 2>&1
echo "CHAIN45_DONE $(date)"
