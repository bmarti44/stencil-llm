#!/usr/bin/env bash
# Amendment commit gate (v1.19, hardened v1.20): the ONLY sanctioned way to
# land amend(vX.Y). Requires an ACCEPTED pre-commit amendment review of the
# working tree (score >=90, zero open high/critical, latest round names the
# version), verified history entries, and a STATE line whose next command is
# this exact amendment. Takes the repo lock so it cannot race a wrapper.
# Usage: bash tools/amend.sh vX.Y "commit summary"
set -euo pipefail
ROOT="$(git rev-parse --show-toplevel)"
# --tree-id mode: print the content identity of the full working tree
# (tracked changes + untracked non-ignored files) without touching the real
# index. The amendment reviewer runs this and quotes the id in its round
# bullet; commit mode refuses unless the ids match — the reviewed artifact
# IS the committed artifact, by content (v1.20 final, per round-4 #7).
tree_id() {
    # Read-only content identity (v1.20 final): sha256 over HEAD sha, the
    # tracked diff, and framed (path, NUL, length, NUL, content) records of
    # untracked non-ignored files in sorted path order — the same framing as
    # the registered run-identity formula (PLAN.md Section 3). No git object
    # writes: runnable in a reviewer sandbox with a read-only .git.
    # The amendment review file is excluded so the reviewer's own round write
    # does not invalidate the id it quotes.
    python3 - "$ROOT" <<'PYID'
import hashlib, subprocess, sys, os, stat
root = sys.argv[1]
EXCLUDE = {"plan/reviews/plan/amendment.md"}
h = hashlib.sha256()
head = subprocess.run(["git", "-C", root, "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
h.update(head.encode())
diff = subprocess.run(["git", "-C", root, "diff", "--binary", "--full-index", "--no-textconv", "--no-ext-diff", "HEAD", "--", ".", ":(exclude)plan/reviews/plan/amendment.md"],
                      capture_output=True, check=True).stdout
h.update(hashlib.sha256(diff).hexdigest().encode())
raw = subprocess.run(["git", "-C", root, "ls-files", "--others", "--exclude-standard", "-z"],
                     capture_output=True, check=True).stdout
paths = [p.decode("utf-8", "surrogateescape") for p in raw.split(b"\x00") if p]
for p in sorted(set(paths) - EXCLUDE):
    fp = os.path.join(root, p)
    try:
        st = os.lstat(fp)
    except OSError:
        h.update(b"GONE\x00" + p.encode("utf-8", "surrogateescape") + b"\x00")
        continue
    h.update(p.encode("utf-8", "surrogateescape")); h.update(b"\x00")
    if stat.S_ISLNK(st.st_mode):
        tgt = os.readlink(fp).encode("utf-8", "surrogateescape")
        h.update(b"L\x00" + str(len(tgt)).encode() + b"\x00" + tgt)
    elif stat.S_ISREG(st.st_mode):
        data = open(fp, "rb").read()
        x = b"X" if (st.st_mode & stat.S_IXUSR) else b"-"
        h.update(b"F" + x + b"\x00" + str(len(data)).encode() + b"\x00" + data)
    else:
        h.update(b"OTHER\x00" + oct(st.st_mode).encode() + b"\x00")
print(h.hexdigest()[:40])
PYID
}
if [ "${1:-}" = "--tree-id" ]; then tree_id; exit 0; fi
V="$1"; MSG="$2"
exec 9>"$ROOT/.review.lock"
flock -w 600 9 || { echo "FAIL: could not take repo lock"; exit 6; }
fail=0
REV="$ROOT/plan/reviews/plan/amendment.md"
[ -f "$REV" ] || { echo "FAIL: no amendment review at $REV"; exit 1; }
python3 "$ROOT/tools/check_review_scores.py" --file "$REV" --min 90 --quiet || { echo "FAIL: amendment review not accepted"; fail=1; }
# The review's LATEST round block must name this version (reviewed THIS diff,
# not a stale acceptance from an earlier amendment).
LATEST="$(awk '/^### Round /{n++} n==1{print} n==2{exit}' "$REV")"
echo "$LATEST" | grep -q "$V" || { echo "FAIL: latest amendment-review round does not mention $V"; fail=1; }
TID="$(tree_id)"
echo "$LATEST" | grep -q "$TID" || { echo "FAIL: latest review round does not quote the current tree id $TID — the reviewed tree is not this tree (post-review edits, or the reviewer never ran tools/amend.sh --tree-id)"; fail=1; }
grep -q "^- $V " "$ROOT/PLAN.md" || { echo "FAIL: PLAN.md index line for $V missing"; fail=1; }
grep -q "^- $V," "$ROOT/plan/AMENDMENTS.md" || { echo "FAIL: plan/AMENDMENTS.md entry for $V missing"; fail=1; }
TODAY="$(date -u +%Y-%m-%d)"
TOP_ENTRY="$(awk '/^- /{print; exit}' "$ROOT/plan/LEDGER.md")"
echo "$TOP_ENTRY" | grep -q "STATE:" || { echo "FAIL: topmost ledger entry carries no STATE:"; fail=1; }
echo "$TOP_ENTRY" | grep -q "$TODAY" || { echo "FAIL: topmost ledger entry not dated today"; fail=1; }
# First occurrence, non-greedy, then exact anchored prefix equality.
FIRST_NEXT="$(printf '%s' "$TOP_ENTRY" | awk -F'next command: `' 'NF>1{split($2,a,"`"); print a[1]; exit}')"
case "$FIRST_NEXT" in
    "bash tools/amend.sh $V "*|"bash tools/amend.sh $V") : ;;
    *) echo "FAIL: topmost STATE's first next command is '$FIRST_NEXT', not the exact amend.sh $V invocation"; fail=1 ;;
esac
[ "$fail" = "0" ] || exit 1
git -C "$ROOT" add -A
git -C "$ROOT" commit -m "amend($V): $MSG

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
