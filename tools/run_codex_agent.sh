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

# Serialize with reviewers/coders (PLAN.md 2b rule 7).
exec 9>"$ROOT/.review.lock"
if ! flock -w 7200 9; then
    echo "ERROR: could not acquire $ROOT/.review.lock within 2h" >&2
    exit 6
fi

# Brief contract validation (PLAN 2b, v1.14): the five required sections.
for h in "Objective" "Allowlist" "Tests first" "Acceptance" "Ledger handoff"; do
    if ! grep -qi "^#\+.*$h" "$BRIEF"; then
        echo "ERROR: brief $BRIEF missing required section: $h" >&2
        exit 2
    fi
    # Section must have non-empty body content (v1.15).
    if ! awk -v h="$h" 'BEGIN{IGNORECASE=1; insec=0}
        /^#+/{ if (insec) exit; if ($0 ~ h) insec=1; next }
        insec && NF { found=1; exit } END{ exit !found }' "$BRIEF"; then
        echo "ERROR: brief $BRIEF section \"$h\" is empty" >&2
        exit 2
    fi
done

ALLOW="$ROOT/tools/codex-agents/${AGENT}.allow"
# Mandatory per tie-break batch 2 (2026-08-22): every brief ships an allowlist.
if [ ! -f "$ALLOW" ]; then
    echo "ERROR: missing scope allowlist $ALLOW (mandatory per PLAN 2b / tie-break batch 2)" >&2
    exit 2
fi

provenance() {
    # Runs on EVERY exit path (trap): records the run whether it succeeded,
    # violated scope, or died. Strings passed as argv — never interpolated
    # into code (injection-safe). A missing session id is recorded loudly.
    local tid
    tid="$(grep -m1 '"type":"thread.started"' "$LOG" 2>/dev/null | sed 's/.*"thread_id":"\([a-f0-9-]*\)".*/\1/')"
    [ -n "$tid" ] || tid="MISSING-SESSION-EVENT"
    python3 - "$ROOT/plan/LEDGER.md" "$(date -u +%Y-%m-%d)" "$AGENT" \
        "${CODEX_MODEL:-gpt-5.6-sol}" "${CODEX_EFFORT:-medium}" "${FINAL_EC:-?}" \
        "$tid" "$LOG" "${OVERRIDE_REASON:-}" <<'PYLED'
import sys
p, date, agent, model, effort, ec, tid, log, why = sys.argv[1:10]
entry = (f"- {date}, coder (auto, run_codex_agent.sh). Brief {agent}: model {model}, "
         f"effort {effort}, exit {ec}, session {tid}, log {log}."
         + (f" Override reason: {why}." if why else "") + "\n")
s = open(p).read()
marker = "### Ledger\n\n"
open(p, "w").write(s.replace(marker, marker + entry, 1) if marker in s else s + entry)
PYLED
}
trap 'FINAL_EC=$?; provenance' EXIT

mkdir -p "$ROOT/results/logs"
LOG="$ROOT/results/logs/codex-agent-${AGENT}.log"
# Overrides require a ledgered reason (PROTOCOL brief contract).
if { [ -n "${CODEX_MODEL:-}" ] || [ -n "${CODEX_EFFORT:-}" ]; } && [ -z "${OVERRIDE_REASON:-}" ]; then
    echo "ERROR: CODEX_MODEL/CODEX_EFFORT override without OVERRIDE_REASON" >&2
    exit 2
fi
echo "[$(date -u +%H:%M:%S)] codex agent ${AGENT} starting (timeout ${TIMEOUT}s)" >&2

cat "$BRIEF" | timeout "$TIMEOUT" \
    codex exec \
        --skip-git-repo-check \
        --dangerously-bypass-approvals-and-sandbox \
        --json \
        --model "${CODEX_MODEL:-gpt-5.6-sol}" \
        -c "model_reasoning_effort=\"${CODEX_EFFORT:-medium}\"" \
        -C "$ROOT" \
        - \
    > "$LOG" 2>&1

ec=$?
echo "[$(date -u +%H:%M:%S)] codex agent ${AGENT} exited with $ec; log: $LOG" >&2
echo "--- post-run repo diff (audit against the brief's scope) ---" >&2
(cd "$ROOT" && git status --porcelain=v1) >&2
# Scope enforcement (PLAN 2b): if the brief ships an allowlist of glob
# patterns (one per line) at tools/codex-agents/<name>.allow, any dirty
# path not matching a pattern is a hard failure.
ALLOW="$ROOT/tools/codex-agents/${AGENT}.allow"
if [ -f "$ALLOW" ]; then
    viol=0
    while IFS= read -r path; do
        [ -z "$path" ] && continue
        case "$path" in plan/LEDGER.md|results/logs/*) continue ;; esac
        ok=0
        while IFS= read -r pat; do
            [ -z "$pat" ] && continue
            case "$path" in $pat) ok=1; break ;; esac
        done < "$ALLOW"
        if [ "$ok" = "0" ]; then
            echo "SCOPE VIOLATION: $path not covered by ${AGENT}.allow" >&2
            viol=1
        fi
    done < <(cd "$ROOT" && { git diff --name-only HEAD --; git ls-files --others --exclude-standard; } | sort -u)
    if [ "$viol" = "1" ]; then exit 7; fi
fi
# Provenance auto-append (v1.21, corrected same version after review replay
# showed the earlier placement tripped the wrapper's own scope check): runs
# AFTER the allowlist scan, inserts newest-first under the ### Ledger header,
# records the codex session id from the --json log, and the override reason.
exit $ec
