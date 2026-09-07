#!/usr/bin/env bash
S=/tmp/claude-1000/-home-bmarti44-stencil-llm/a88136df-3902-46b9-a661-86e0dc1bb53f/scratchpad
cd /home/bmarti44/stencil-llm
while [ ! -f results/slab2-review-fable-r2.md ]; do sleep 120; done
echo "ADOPTION_START $(date)"
codex exec --sandbox danger-full-access -m gpt-6-astra -C /home/bmarti44/stencil-llm "$(cat $S/adoption-brief.md)" > $S/adoption.log 2>&1
echo "ADOPTION_DONE $(date)"
