#!/usr/bin/env bash
# Gate acceptance check (PLAN.md 2b): exact-artifact validation (v1.16).
# Sol reviews are files in plan/reviews/<phase>/ whose frontmatter declares
# "**Reviewer model:** codex/"; kimi cross-reviews declare kimi/. Any other
# file in the directory (except *.rejected.md sidecars) is a layout violation.
# Thresholds hardcoded; not parameterizable.
set -euo pipefail
PHASE="$1"
ROOT="$(git rev-parse --show-toplevel)"
DIR="$ROOT/plan/reviews/$PHASE"
fail=0; sol=0; kimi=0
# Topic manifest (v1.22): the write-ahead-registered sol topics for this
# phase. Acceptance requires exactly these codex reviews to exist and pass —
# "any scored codex file" no longer counts.
MANIFEST="$DIR/topics.txt"
if [ ! -f "$MANIFEST" ]; then echo "FAIL: no topic manifest $MANIFEST"; exit 1; fi
while IFS= read -r line; do
    [ -z "$line" ] && continue
    t="${line%% *}"
    [ -f "$DIR/$t.md" ] || { echo "FAIL: registered topic '$t' has no review file"; fail=1; }
    if [ "$line" != "$t" ]; then  # 'kimi' flag present
        if [ ! -f "$DIR/$t-kimi.md" ] || ! grep -q '^\*\*Reviewer model:\*\* kimi/' "$DIR/$t-kimi.md"; then
            echo "FAIL: topic '$t' requires a kimi companion review"; fail=1
        fi
    fi
done < "$MANIFEST"
for f in "$DIR"/*.md; do
    [ -e "$f" ] || { echo "FAIL: no reviews in $DIR"; exit 1; }
    case "$f" in *.rejected.md) continue ;; esac
    if grep -q '^\*\*Reviewer model:\*\* codex/' "$f"; then
        base="$(basename "$f" .md)"
        grep -Eq "^${base}( kimi)?$" "$MANIFEST" || { echo "FAIL: codex review '$base' is not in the topic manifest"; fail=1; }
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
