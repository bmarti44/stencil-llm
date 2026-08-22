#!/usr/bin/env bash
# Amendment commit gate (v1.19): the ONLY sanctioned way to land amend(vX.Y).
# Verifies, before committing, that the working tree carries: (1) a PLAN.md
# index line for vX.Y, (2) a plan/AMENDMENTS.md entry for vX.Y, (3) a
# plan/LEDGER.md topmost STATE line mentioning the next command, updated this
# session (contains today's date). Closes the orchestrator's recurring
# forgot-the-log slip class (v1.12, v1.18) mechanically.
# Usage: bash tools/amend.sh vX.Y "commit summary"
set -euo pipefail
V="$1"; MSG="$2"
ROOT="$(git rev-parse --show-toplevel)"
fail=0
grep -q "^- $V " "$ROOT/PLAN.md" || { echo "FAIL: PLAN.md index line for $V missing"; fail=1; }
grep -q "^- $V," "$ROOT/plan/AMENDMENTS.md" || { echo "FAIL: plan/AMENDMENTS.md entry for $V missing"; fail=1; }
TODAY="$(date -u +%Y-%m-%d)"
head -n 12 "$ROOT/plan/LEDGER.md" | grep -q "STATE:" || { echo "FAIL: no STATE line near top of plan/LEDGER.md"; fail=1; }
awk '/^- /{print; exit}' <(grep -A0 "^- " "$ROOT/plan/LEDGER.md") | grep -q "$TODAY" || { echo "FAIL: topmost ledger entry is not dated today ($TODAY) — refresh STATE before amending"; fail=1; }
[ "$fail" = "0" ] || exit 1
git -C "$ROOT" add -A
git -C "$ROOT" commit -m "amend($V): $MSG

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
