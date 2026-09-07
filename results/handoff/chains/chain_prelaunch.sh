#!/usr/bin/env bash
S=/tmp/claude-1000/-home-bmarti44-stencil-llm/a88136df-3902-46b9-a661-86e0dc1bb53f/scratchpad
cd /home/bmarti44/stencil-llm
while ! grep -q ADOPTION_DONE $S/chain_adoption.log; do sleep 120; done
echo "DRIVERFIX_START $(date)"
codex exec --sandbox danger-full-access -m gpt-6-astra -C /home/bmarti44/stencil-llm "$(cat $S/driverfix-brief.md)" > $S/driverfix.log 2>&1
echo "DRIVERFIX_DONE $(date)"
touch $S/pilot5.GO
echo "PILOT5_ARMED $(date)"
