#!/usr/bin/env bash
# Launch a long-running codex coding agent on a single topic.
#
# Usage:
#   bash tools/run_codex_agent.sh <agent-name> [<timeout-sec>]
#
# Reads tools/codex-agents/<agent-name>.md as the agent's brief. Codex runs
# with sandbox bypass (the host blocks unprivileged user namespaces, so
# bubblewrap fails) and gpt-5.6-sol at medium reasoning effort (override via
# CODEX_MODEL / CODEX_EFFORT). Streams output to /tmp/codex-agent-<name>.log.
#
# The agent is expected to:
#   1. Read the brief.
#   2. Make repository edits via apply_patch.
#   3. Run pytest to verify.
#   4. Re-run the relevant review wrapper to confirm score ≥ 90.

set -uo pipefail

if [ $# -lt 1 ] || [ $# -gt 2 ]; then
    echo "Usage: $0 <agent-name> [<timeout-sec>]" >&2
    exit 2
fi

AGENT="$1"
TIMEOUT="${2:-3600}"   # 1 hour default; agents typically need 10–30 min

ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$ROOT"

BRIEF="$ROOT/tools/codex-agents/${AGENT}.md"
if [ ! -f "$BRIEF" ]; then
    echo "ERROR: brief not found: $BRIEF" >&2
    exit 2
fi

LOG="/tmp/codex-agent-${AGENT}.log"
echo "[$(date -u +%H:%M:%S)] codex agent ${AGENT} starting (timeout ${TIMEOUT}s)" >&2

cat "$BRIEF" | timeout "$TIMEOUT" \
    codex exec \
        --skip-git-repo-check \
        --dangerously-bypass-approvals-and-sandbox \
        --model "${CODEX_MODEL:-gpt-5.6-sol}" \
        -c "model_reasoning_effort=\"${CODEX_EFFORT:-medium}\"" \
        -C "$ROOT" \
        - \
    > "$LOG" 2>&1

ec=$?
echo "[$(date -u +%H:%M:%S)] codex agent ${AGENT} exited with $ec; log: $LOG" >&2
exit $ec
