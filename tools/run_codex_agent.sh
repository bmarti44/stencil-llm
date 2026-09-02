#!/usr/bin/env bash
# Launch a long-running codex coding agent on a single topic.
#
# Usage:
#   bash tools/run_codex_agent.sh <agent-name> [<timeout-sec>]
#
# Reads tools/codex-agents/<agent-name>.md as the agent's brief. Codex runs
# with sandbox bypass (the host blocks unprivileged user namespaces, so
# bubblewrap fails) and gpt-5.6-sol at medium reasoning effort (override via
# CODEX_MODEL / CODEX_EFFORT + OVERRIDE_REASON). Log: results/logs/codex-agent-<name>.log.
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
    if [ -z "$tid" ]; then
        tid="MISSING-SESSION-EVENT"
        if [ "${FINAL_EC:-1}" = "0" ]; then FINAL_EC=9; fi
    fi
    python3 - "$ROOT/WORKLOG.md" "$(date -u +%Y-%m-%d)" "$AGENT" \
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
trap 'FINAL_EC=$?; rm -f "${POST_OUT:-}"; rm -rf "${PRIVATE_DIR:-}"; if ! provenance; then echo "ERROR: provenance append failed" >&2; exit 8; fi; exit ${FINAL_EC}' EXIT

mkdir -p "$ROOT/results/logs"
LOG="$ROOT/results/logs/codex-agent-${AGENT}.log"
# Overrides require a ledgered reason (PROTOCOL brief contract).
if { [ -n "${CODEX_MODEL:-}" ] || [ -n "${CODEX_EFFORT:-}" ]; } && [ -z "${OVERRIDE_REASON:-}" ]; then
    echo "ERROR: CODEX_MODEL/CODEX_EFFORT override without OVERRIDE_REASON" >&2
    exit 2
fi
# Pre-launch dirty-state manifest (v1.22 final): the scope scan must judge
# only CODER-authored changes. Orchestrator state dirty before launch (e.g.
# the required write-ahead ledger entry) is baseline, not violation.
# Enforcement inputs are snapshotted into a wrapper-private dir BEFORE the
# coder runs: the post-run verdict never consults coder-writable files
# (round-25 self-authentication bypass — deleting the allowlist or replacing
# the helper no longer disables the scan; such edits also appear in the
# changed set and face the snapshot allowlist like any other path).
# Enforcement state lives in PARENT MEMORY across the coder run (round-26:
# same-uid /tmp files are child-writable; shell variables are not). The
# allowlist and verifier CONTENT are captured pre-launch; the baseline file's
# digest is held in memory and verified post-run before use.
PRIVATE_DIR="$(mktemp -d)"
ALLOW_CONTENT="$(cat "$ALLOW")"
VERIFIER_CONTENT="$(cat "$ROOT/tools/_coder_scope.py")"
PRE_MANIFEST="$PRIVATE_DIR/pre.json"
printf '%s' "$VERIFIER_CONTENT" > "$PRIVATE_DIR/_coder_scope.py"
python3 "$PRIVATE_DIR/_coder_scope.py" pre "$PRE_MANIFEST" || { echo "ERROR: scope baseline snapshot failed" >&2; exit 10; }
PRE_DIGEST="$(sha256sum "$PRE_MANIFEST" | cut -d' ' -f1)"

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
if true; then
    viol=0
    # Post-run: re-materialize policy and verifier FROM PARENT MEMORY and
    # verify the baseline digest — child tampering with any /tmp file is
    # detected or overwritten before a single judgment is made.
    if [ "$(sha256sum "$PRE_MANIFEST" | cut -d' ' -f1)" != "$PRE_DIGEST" ]; then
        echo "SCOPE VIOLATION: baseline manifest tampered during the coder run" >&2
        FINAL_EC=7; exit 7
    fi
    printf '%s' "$VERIFIER_CONTENT" > "$PRIVATE_DIR/_coder_scope.py"
    printf '%s\n' "$ALLOW_CONTENT" > "$PRIVATE_DIR/allow"
    POST_OUT="$(mktemp)"
    python3 "$PRIVATE_DIR/_coder_scope.py" post "$PRE_MANIFEST" > "$POST_OUT" || { echo "ERROR: scope comparison failed" >&2; rm -f "$POST_OUT"; exit 10; }
    while IFS= read -r -d '' path; do
        [ -z "$path" ] && continue
        [ "$ROOT/$path" = "$LOG" ] && continue
        ok=0
        while IFS= read -r pat; do
            [ -z "$pat" ] && continue
            case "$path" in $pat) ok=1; break ;; esac
        done < "$PRIVATE_DIR/allow"
        if [ "$ok" = "0" ]; then
            echo "SCOPE VIOLATION: $path not covered by ${AGENT}.allow" >&2
            viol=1
        fi
    done < "$POST_OUT"
    rm -f "$POST_OUT"
    if [ "$viol" = "1" ]; then FINAL_EC=7; exit 7; fi
fi
# Provenance auto-append (v1.21, corrected same version after review replay
# showed the earlier placement tripped the wrapper's own scope check): runs
# AFTER the allowlist scan, inserts newest-first under the ### Ledger header,
# records the codex session id from the --json log, and the override reason.
exit $ec
