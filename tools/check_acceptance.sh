#!/usr/bin/env bash
# Gate acceptance check (PLAN.md 2b): exact-artifact validation (v1.16).
# Sol reviews are files in docs/reviews/<phase>/ whose frontmatter declares
# "**Reviewer model:** codex/"; kimi cross-reviews declare kimi/. Any other
# file in the directory (except *.rejected.md sidecars) is a layout violation.
# Thresholds hardcoded; not parameterizable.
set -euo pipefail
PHASE="$1"
ROOT="$(git rev-parse --show-toplevel)"
DIR="$ROOT/docs/reviews/$PHASE"
fail=0; sol=0; kimi=0
for f in "$DIR"/*.md; do
    [ -e "$f" ] || { echo "FAIL: no reviews in $DIR"; exit 1; }
    case "$f" in *.rejected.md) continue ;; esac
    if grep -q '^\*\*Reviewer model:\*\* codex/' "$f"; then
        sol=$((sol+1))
        python3 "$ROOT/tools/check_review_scores.py" --file "$f" --min 90 || fail=1
    elif grep -q '^\*\*Reviewer model:\*\* kimi/' "$f"; then
        kimi=$((kimi+1))
    else
        echo "FAIL: unexpected artifact in review dir: $f (registered layout violation)"
        fail=1
    fi
done
[ "$sol" -ge 1 ] || { echo "FAIL: no sol review exists for $PHASE"; fail=1; }
[ "$kimi" -ge 1 ] || { echo "FAIL: no kimi cross-review for $PHASE"; fail=1; }
exit $fail
