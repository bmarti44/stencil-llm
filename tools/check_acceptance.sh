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
# Human-acceptance override (Adjudication 3): a committed ACCEPTED-BY-HUMAN
# file lists topics accepted by ruling; they skip the 90-bar (H/C still checked).
OVERRIDE="$DIR/ACCEPTED-BY-HUMAN"
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
        if [ -f "$OVERRIDE" ] && grep -qx "$base" "$OVERRIDE"; then
            # Human acceptance is total for the listed topic: score AND open
            # findings are superseded by the ruling recorded in
            # plan/tiebreaks/<phase>.md (Adjudication 3 semantics).
            echo "ACCEPTED-BY-HUMAN  $f"
        else
            python3 "$ROOT/tools/check_review_scores.py" --file "$f" --min 90 || fail=1
        fi
    elif grep -q '^\*\*Reviewer model:\*\* kimi/' "$f"; then
        kimi=$((kimi+1))
    else
        echo "FAIL: unexpected artifact in review dir: $f (registered layout violation)"
        fail=1
    fi
done
[ "$sol" -ge 1 ] || { echo "FAIL: no sol review exists for $PHASE"; fail=1; }
[ "$kimi" -ge 1 ] || { echo "FAIL: no kimi cross-review for $PHASE"; fail=1; }
# v1.27: binary gate artifacts require a prose description sidecar at
# results/<slug>-description.md (batch-5 presentation contract, formalized).
ART="$DIR/artifacts.txt"
if [ -f "$ART" ]; then
    while IFS= read -r a; do
        a="$(echo "$a" | tr -d ' ')"
        [ -z "$a" ] && continue
        # Binary = exists and fails grep's text heuristic (-I); text files and
        # absent artifacts (reported PRESENT/ABSENT elsewhere) are exempt.
        if [ -f "$ROOT/$a" ] && ! grep -qI . "$ROOT/$a" 2>/dev/null; then
            slug="$(basename "$a" | tr '._' '--')"
            SIDE="$ROOT/results/${slug}-description.md"
            if [ ! -f "$SIDE" ]; then
                echo "FAIL: binary artifact $a has no results/${slug}-description.md sidecar"; fail=1
            else
                # v1.27 (round-33 #24): the sidecar must record the artifact's
                # CURRENT sha256 — a stale description is a presentation failure.
                CUR="$(sha256sum "$ROOT/$a" | cut -c1-64)"
                if ! grep -q "$CUR" "$SIDE"; then
                    echo "FAIL: sidecar results/${slug}-description.md does not contain the artifact's current sha256 ($CUR) — stale description"; fail=1
                fi
            fi
        fi
    done < "$ART"
fi
# v1.25: governed status-row check (README-row flip missed in two consecutive
# phases; PLAN rule 5). For phaseN acceptance the README row must have left
# "not started" — the launch should have flipped it to in progress.
if [[ "$PHASE" =~ ^phase([0-9]+)$ ]]; then
    ROW="$(grep -E "^\| Phase ${BASH_REMATCH[1]} \|" "$ROOT/README.md" || true)"
    if [ -z "$ROW" ]; then
        echo "FAIL: README.md has no status row for Phase ${BASH_REMATCH[1]}"; fail=1
    elif printf '%s' "$ROW" | grep -q "not started"; then
        echo "FAIL: README.md Phase ${BASH_REMATCH[1]} row still says 'not started' at acceptance (rule 5: launch flips it to in progress)"; fail=1
    fi
fi
exit $fail
