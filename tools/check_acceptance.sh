#!/usr/bin/env bash
# Gate acceptance check (PLAN.md 2b checklist item b/c): thresholds hardcoded —
# 90 for sol reviews, kimi advisory presence verified. Not parameterizable.
set -euo pipefail
PHASE="$1"
ROOT="$(git rev-parse --show-toplevel)"
fail=0
count=0
for f in "$ROOT"/docs/reviews/"$PHASE"/*.md; do
    case "$f" in *-kimi.md|*.rejected.md|*tiebreaks*) continue ;; esac
    count=$((count+1))
    python3 "$ROOT/tools/check_review_scores.py" --file "$f" --min 90 || fail=1
done
if [ "$count" = "0" ]; then echo "FAIL: no sol review exists for $PHASE"; fail=1; fi
ls "$ROOT"/docs/reviews/"$PHASE"/*-kimi.md >/dev/null 2>&1 || { echo "FAIL: no kimi cross-review for $PHASE"; fail=1; }
exit $fail
