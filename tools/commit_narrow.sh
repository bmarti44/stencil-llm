#!/usr/bin/env bash
# Narrow commit helper (v1.22 final): sanctioned path for NON-governed
# commits. Governed paths move solely through tools/amend.sh. Rather than
# parsing pathspec magic (an arms race lost twice in review), this asks git
# to RESOLVE each argument and judges the resolved file set — every magic
# form (:(top), :(literal), :(glob), :/, directories, ..) is covered by
# construction because git's own resolution is the authority.
# Usage: bash tools/commit_narrow.sh "message" pathspec [pathspec...]
set -euo pipefail
MSG="$1"; shift
ROOT="$(git rev-parse --show-toplevel)"
exec 9>"$ROOT/.review.lock"; flock -w 600 9
# Refuse pre-existing staged content: the final commit is index-wide, so the
# index must start empty (round-19 bypass: staged governed changes rode along).
if [ -n "$(git -C "$ROOT" diff --cached --name-only)" ]; then
    echo "FAIL: the index already has staged content — unstage it first (git reset)"; exit 1
fi
RESOLVED="$(cd "$ROOT" && git ls-files --cached --others --modified --exclude-standard -- "$@" | sort -u)"
[ -n "$RESOLVED" ] || { echo "FAIL: the given pathspecs resolve to no files"; exit 1; }
while IFS= read -r p; do
    case "$p" in
        PLAN.md|plan/PROTOCOL.md|plan/AMENDMENTS.md|plan/LEDGER.md|AGENTS.md|CLAUDE.md|README.md|tools/*)
            echo "FAIL: pathspec resolves to governed file '$p' — use tools/amend.sh"; exit 1 ;;
    esac
done <<< "$RESOLVED"
# Stage exactly the resolved literal files (no magic reaches git add).
(cd "$ROOT" && printf '%s\n' "$RESOLVED" | while IFS= read -r p; do git add -- ":(literal)$p"; done)
git -C "$ROOT" commit -m "$MSG

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
