#!/usr/bin/env bash
# Run a codex review for one topic, updating the canonical review file in place.
#
# Usage:
#   bash tools/run_codex_review.sh <phase> <topic> <threshold>
#
# Args:
#   phase      e.g. phase-a1, phase-b, phase-c
#   topic      e.g. security, determinism, contract, corpus, code-quality, test-inventory, sft-quality
#   threshold  minimum acceptable score (e.g. 90)
#
# Reads the existing review file at plan/reviews/{phase}/{topic}.md (if any)
# so the prompt can reference prior round logs. Invokes codex with the prompt
# fragment from tools/codex-prompts/review-{topic}.md plus the common header.
# Codex is instructed (via the prompt) to update the same file path in place
# with a new "## Round K" log entry at top.
#
# Env overrides:
#   CODEX_BIN   path to codex binary (default: codex on PATH)
#   CODEX_MODEL model id (default: gpt-5)
#   REVIEW_DIR  directory for review files (default: plan/reviews)
#   PROMPTS_DIR directory of prompt fragments (default: tools/codex-prompts)
#   CODEX_TIMEOUT_SEC timeout in seconds (default: 1800)

set -euo pipefail

if [ $# -ne 3 ]; then
    echo "Usage: $0 <phase> <topic> <threshold>" >&2
    exit 2
fi

PHASE="$1"
TOPIC="$2"
THRESHOLD="$3"

CODEX_BIN="${CODEX_BIN:-codex}"
# Default codex model: gpt-5.6-sol ("sol"). Reviews run at xhigh reasoning effort.
# Override via CODEX_MODEL=o3 (etc.) for explicit selection. Setting to empty
# string ("") uses the codex CLI's compiled-in default.
CODEX_MODEL="${CODEX_MODEL-gpt-5.6-sol}"
REVIEW_DIR="${REVIEW_DIR:-plan/reviews}"
PROMPTS_DIR="${PROMPTS_DIR:-tools/codex-prompts}"
CODEX_TIMEOUT_SEC="${CODEX_TIMEOUT_SEC:-3600}"
LOG_DIR_DEFAULT="results/logs"
CODEX_EFFORT="${CODEX_EFFORT:-xhigh}"

ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$ROOT"

# Serialize wrappers per-repo: the post-run drift restorer copies pre-codex
# snapshots back over dirty files, which clobbers concurrent edits. One
# reviewer/coder wrapper at a time (Stencil PLAN.md Section 2b).
exec 9>"$ROOT/.review.lock"
if ! flock -w 7200 9; then
    echo "ERROR: could not acquire $ROOT/.review.lock within 2h" >&2
    exit 6
fi

validate_slug() {
    local label="$1"
    local value="$2"
    if [[ ! "$value" =~ ^[a-z0-9-]+$ ]]; then
        echo "ERROR: invalid $label: must match [a-z0-9-]+ and contain no '/', '..', or NUL" >&2
        exit 2
    fi
}

resolve_safe_dir() {
    local label="$1"
    local raw="$2"
    local allowed_rel="$3"
    local candidate
    local resolved
    local allowed

    if [ -z "$raw" ]; then
        echo "ERROR: invalid $label: path must not be empty" >&2
        exit 2
    fi
    IFS='/' read -r -a parts <<< "$raw"
    for part in "${parts[@]}"; do
        if [ "$part" = ".." ]; then
            echo "ERROR: invalid $label: path must not contain '..'" >&2
            exit 2
        fi
    done
    if [[ "$raw" = /* ]]; then
        candidate="$raw"
    else
        candidate="$ROOT/$raw"
    fi
    resolved="$(realpath -m "$candidate")"
    allowed="$(realpath -m "$ROOT/$allowed_rel")"
    case "$resolved" in
        "$allowed"|"$allowed"/*)
            printf '%s\n' "$resolved"
            ;;
        *)
            echo "ERROR: invalid $label: path must resolve under $allowed_rel" >&2
            exit 2
            ;;
    esac
}

MIN_T=90; case "$TOPIC" in retro*|*-retro) MIN_T=75 ;; esac
if [ "$THRESHOLD" -lt "$MIN_T" ] 2>/dev/null; then
    echo "ERROR: threshold $THRESHOLD below the registered floor $MIN_T for topic $TOPIC" >&2
    exit 2
fi
validate_slug "phase" "$PHASE"
validate_slug "topic" "$TOPIC"
REVIEW_DIR="$(resolve_safe_dir "REVIEW_DIR" "$REVIEW_DIR" "plan/reviews")"
PROMPTS_DIR="$(resolve_safe_dir "PROMPTS_DIR" "$PROMPTS_DIR" "tools/codex-prompts")"

# Canonical layout (docs/plans Phase 0 reorg): per-phase subdirs under
# plan/reviews. Codex/kimi scripts previously wrote dash-form
# `${REVIEW_DIR}/${PHASE}-${TOPIC}.md` while the canonical files live at
# `${REVIEW_DIR}/${PHASE}/${TOPIC}.md` — the silent path mismatch caused
# every codex round to "succeed" (exit 0) without materialising a review
# file, wasting GPU time. Fixed 2026-05-15.
REVIEW_FILE="${REVIEW_DIR}/${PHASE}/${TOPIC}.md"
TOPICS_MANIFEST="${REVIEW_DIR}/${PHASE}/topics.txt"
if [ -f "$TOPICS_MANIFEST" ] && ! grep -Eq "^${TOPIC}( kimi)?$" "$TOPICS_MANIFEST"; then
    echo "ERROR: topic '$TOPIC' is not in $TOPICS_MANIFEST (register it in the write-ahead entry first)" >&2
    exit 2
fi
PROMPT_FILE="${PROMPTS_DIR}/review-${TOPIC}.md"
# Routing fallback (PLAN 2b cadence): phase-style topics without a specific
# fragment use the generic per-phase rubric.
if [ ! -f "$PROMPT_FILE" ]; then
    case "$TOPIC" in
        phase*|tradeoff|report) PROMPT_FILE="${PROMPTS_DIR}/review-phase.md" ;;
    esac
fi
COMMON_HEADER="${PROMPTS_DIR}/_common-header.md"

if [ ! -f "$PROMPT_FILE" ]; then
    echo "ERROR: prompt fragment not found: $PROMPT_FILE" >&2
    exit 2
fi
if [ ! -f "$COMMON_HEADER" ]; then
    echo "ERROR: common header not found: $COMMON_HEADER" >&2
    exit 2
fi

mkdir -p "$(dirname "$REVIEW_FILE")"

# Build the full prompt: common header + topic prompt + canonical-file path + previous content
PROMPT_FILE_ABS="$(realpath "$PROMPT_FILE")"
COMMON_HEADER_ABS="$(realpath "$COMMON_HEADER")"
REVIEW_FILE_ABS="$(realpath -m "$REVIEW_FILE")"

PRIOR_BLOCK=""
PRIOR_SNAPSHOT=""
if [ -f "$REVIEW_FILE" ]; then
    PRIOR_BLOCK=$'\n\n## PRIOR ROUND CONTENT (verbatim — preserve in your round log)\n\n'"$(cat "$REVIEW_FILE")"
    # Phase 8 security #2: snapshot the prior file so we can verify the
    # model returned an append-only candidate (no prior round removed
    # or modified).
    PRIOR_SNAPSHOT="$(mktemp)"
    cp "$REVIEW_FILE" "$PRIOR_SNAPSHOT"
fi
REVIEW_DIFF_BASELINE="$(mktemp)"
python3 "$ROOT/tools/review_diff_allowlist.py" --repo "$ROOT" --snapshot > "$REVIEW_DIFF_BASELINE"

# Defensive: codex with --dangerously-bypass-approvals-and-sandbox can
# shell out to `git checkout/restore/reset` and revert files outside
# the canonical review path. Snapshot every dirty file's CONTENT (not
# just sha) so we can restore them after codex finishes.
WRAPPER_PRE_DIR="$(mktemp -d)"
while IFS= read -r path; do
    [ -z "$path" ] && continue
    if [ -f "$ROOT/$path" ]; then
        mkdir -p "$WRAPPER_PRE_DIR/$(dirname "$path")"
        cp "$ROOT/$path" "$WRAPPER_PRE_DIR/$path"
    fi
done < <(cd "$ROOT" && {
    git diff --name-only HEAD --
    git ls-files --others --exclude-standard
} | sort -u)

ROUND_HINT=$(awk '/^### Round [0-9]+/{n=$3; gsub(/[^0-9]/,"",n); if(n+0>m)m=n} END{print (m?m+1:1)}' "$REVIEW_FILE" 2>/dev/null || echo 1)
TODAY=$(date -u +%Y-%m-%d)

LOG_DIR="$ROOT/${LOG_DIR_DEFAULT}"
mkdir -p "$LOG_DIR"
CODEX_LOG="$LOG_DIR/codex-${PHASE}-${TOPIC}.log"
SESSION_DIR="$ROOT/plan/reviews/.sessions"
mkdir -p "$SESSION_DIR"
SESSION_FILE="$SESSION_DIR/${PHASE}-${TOPIC}"
SID=""
if [ -f "$SESSION_FILE" ]; then
    SID="$(head -c 64 "$SESSION_FILE" | tr -cd 'a-f0-9-')"
fi
RESUME_NOTE=""
if [ -n "${SID:-}" ]; then
    RECENT_GIT="$(cd "$ROOT" && git log --oneline -8 2>/dev/null)"
    RESUME_NOTE=$'\n## RESUMED REVIEW SESSION\n\nYou are the same reviewer who wrote the prior rounds of this review; your session context is intact. The repository has changed since your last round. Recent commits:\n\n'"$RECENT_GIT"$'\n\nRe-read the changed files, re-verify each of YOUR open findings against the current state, and mark genuinely fixed/refuted ones with (resolved DATE: how) / (refuted DATE: why) markers per the closure protocol. Anti-churn rule: add new findings ONLY for regressions introduced by the fixes or clear in-scope misses from your original review; do not expand scope round-over-round.\n'
fi
PROMPT=$(cat <<EOF
$(cat "$COMMON_HEADER_ABS")
$RESUME_NOTE

---

$(cat "$PROMPT_FILE_ABS")

---

## Wrapper-supplied context

- **Canonical review file path** (write your output here, replacing the file's contents):
  $REVIEW_FILE_ABS
- **Phase label**: $PHASE
- **Topic**: $TOPIC
- **Threshold**: $THRESHOLD / 100
- **Round number to use in the log entry**: Round $ROUND_HINT
- **Date**: $TODAY
- **Reviewer model**: codex/${CODEX_MODEL:-default}

## STRICT FILE WRITE POLICY (MANDATORY)

You MUST ONLY write to the canonical review file path listed above. Do NOT:
  * Modify, delete, or git-checkout / git-restore / git-reset / git-stash ANY other file in the repository — including other review files, source files, tests, or configs. Other reviewer agents may be writing in parallel; reverting their work corrupts the round.
  * Run shell commands that mutate files outside the canonical review path. Reading files (cat, head, less) and read-only git commands (git log, git diff, git show, git blame) are fine. Apply-patch / write-tool calls MUST target only the canonical review file.
  * Touch any file under src/, tests/, scripts/, configs/, results/, tools/, or PLAN.md / README.md — these are read-only inputs to your review.

If you observe drift in files outside your canonical review, REPORT IT in your findings. Do not attempt to "clean it up" — that's the wrapper's job.

## Round-tracking format

This file accumulates rounds over time. Your job for THIS round is to track progress against prior rounds:

- Add a new \`### Round $ROUND_HINT — $TODAY (codex/${CODEX_MODEL:-default})\` block at the TOP of the \`## Round log\`. Below it, list:
  - \`- Score: N / 100 (delta vs prior round: +/-X)\`
  - \`- Addressed since prior round:\` — concrete commits / file:line citations of what changed
  - \`- New or remaining:\` — what is still outstanding
- You MAY update prior round entries (e.g., correct a citation, mark a finding as fixed) — but flag any such edit explicitly with a parenthetical "(updated $TODAY: ...)".
- Update the top-of-file frontmatter (Score, Verdict, Reviewer model, Date) to reflect THIS round.
- The \`## Findings\` section reflects the CURRENT state — keep findings that are still open, drop / mark-resolved ones the latest commits closed, add new ones.
- The \`## Recommendations\` section reflects the CURRENT state similarly.

After your review is complete, write the entire updated review markdown to the canonical path above. Use shell write tools to overwrite the file. Do not produce any other output.
$PRIOR_BLOCK
EOF
)

echo "[$(date -u +%H:%M:%S)] codex review starting: $PHASE/$TOPIC -> $REVIEW_FILE" >&2

# Build codex args; only pass --model if CODEX_MODEL is explicitly set.
# Codex's bubblewrap sandbox needs unprivileged user namespaces; on hosts
# where they're disabled (some DGX configs, CI runners), operators may set
# CODEX_BYPASS_SANDBOX=1 explicitly. The default is sandboxed workspace-write.
CODEX_ARGS=(exec --skip-git-repo-check -C "$ROOT" --json -c "model_reasoning_effort=\"$CODEX_EFFORT\"")
if [ "${CODEX_BYPASS_SANDBOX:-0}" == "1" ]; then
    CODEX_ARGS+=(--dangerously-bypass-approvals-and-sandbox)
else
    CODEX_ARGS+=(--sandbox workspace-write)
fi
if [ -n "$CODEX_MODEL" ]; then
    CODEX_ARGS+=(--model "$CODEX_MODEL")
fi
# Review-session continuity (PLAN.md 2b): one review = one reviewer session
# across all its rounds. Round 1 records the codex thread id; later rounds
# resume it so the reviewer keeps its original context instead of
# re-litigating from scratch. New review (new phase/topic) = new session.
if [ -n "$SID" ]; then
    CODEX_ARGS+=(resume "$SID")
fi
CODEX_ARGS+=(-)

# Phase 0 security finding #7: invoke codex with a narrowed env so
# caller secrets (OPENAI_API_KEY, ANTHROPIC_API_KEY, AWS_*, etc.)
# don't leak into the codex CLI. Only PATH, HOME, locale vars, and
# CODEX_/OPENAI_API_KEY (which the codex CLI requires for auth) are
# forwarded. The CLEAN_CODEX_ENV block below uses `env -i` to start
# from a blank environment and re-injects the explicit allowlist.
# DISTIALLATION_REVIEW_ENV is the documented escape-hatch knob if a
# downstream operator needs to broaden the env (set as a prefix).
CLEAN_CODEX_ENV=(
    env -i
    "PATH=$PATH"
    "HOME=$HOME"
    "LANG=${LANG:-C.UTF-8}"
    "LC_ALL=${LC_ALL:-C.UTF-8}"
    "TERM=${TERM:-xterm}"
    "TZ=${TZ:-UTC}"
)
# Codex CLI authenticates via OPENAI_API_KEY; forward only that one
# auth token so the wrapper can run.
if [ -n "${OPENAI_API_KEY:-}" ]; then
    CLEAN_CODEX_ENV+=("OPENAI_API_KEY=$OPENAI_API_KEY")
fi
# Forward CODEX_-namespaced knobs (the wrapper's own config).
for var in $(env | awk -F= '/^CODEX_/{print $1}'); do
    CLEAN_CODEX_ENV+=("$var=${!var}")
done

# Invoke codex non-interactively with the narrowed env.
echo "$PROMPT" | timeout "$CODEX_TIMEOUT_SEC" \
    "${CLEAN_CODEX_ENV[@]}" \
    "$CODEX_BIN" "${CODEX_ARGS[@]}" \
    >"$CODEX_LOG" 2>&1 || {
        ec=$?
        # Session-continuity fallback (PLAN.md 2b): if this was a resume attempt,
        # drop the stored session and retry once with a fresh session.
        if [ -n "${SID:-}" ]; then
            echo "WARN: resume of session $SID failed (exit $ec); retrying with fresh session" >&2
            rm -f "$SESSION_FILE"
            FRESH_ARGS=()
            skip_next=0
            for a in "${CODEX_ARGS[@]}"; do
                if [ "$skip_next" = "1" ]; then skip_next=0; continue; fi
                if [ "$a" = "resume" ]; then skip_next=1; continue; fi
                FRESH_ARGS+=("$a")
            done
            if echo "$PROMPT" | timeout "$CODEX_TIMEOUT_SEC" \
                "${CLEAN_CODEX_ENV[@]}" \
                "$CODEX_BIN" "${FRESH_ARGS[@]}" \
                >"$CODEX_LOG" 2>&1; then
                ec=0
            else
                ec=$?
            fi
        fi
        if [ "$ec" != "0" ]; then
        echo "ERROR: codex exec failed with exit $ec; see $CODEX_LOG" >&2
        # v1.10: restore pre-codex dirty content on the failure path too —
        # previously a failed run exited with unrestored drift. v1.11: also
        # delete files the failed run newly created (not in the snapshot),
        # sparing the canonical review file and logs.
        REVIEW_REL="$(realpath --relative-to="$ROOT" "$REVIEW_FILE_ABS" 2>/dev/null || echo __none__)"
        while IFS= read -r path; do
            [ -z "$path" ] && continue
            [ "$path" = "$REVIEW_REL" ] && continue
            case "$path" in results/logs/*|plan/reviews/.sessions/*) continue ;; esac
            if [ -f "$WRAPPER_PRE_DIR/$path" ]; then
                cp "$WRAPPER_PRE_DIR/$path" "$ROOT/$path"
            elif git -C "$ROOT" ls-files --error-unmatch "$path" >/dev/null 2>&1; then
                git -C "$ROOT" checkout -- "$path"
            else
                rm -f "$ROOT/$path"
            fi
        done < <(cd "$ROOT" && { git diff --name-only HEAD --; git ls-files --others --exclude-standard; } | sort -u)
        rm -f "$REVIEW_DIFF_BASELINE"
        rm -rf "$WRAPPER_PRE_DIR"
        exit "$ec"
        fi
    }

TID="$(grep -m1 '"type":"thread.started"' "$CODEX_LOG" 2>/dev/null | sed 's/.*"thread_id":"\([a-f0-9-]*\)".*/\1/')"
if [ -n "$TID" ]; then
    printf '%s\n' "$TID" > "$SESSION_FILE"
fi
echo "[$(date -u +%H:%M:%S)] codex review finished: $PHASE/$TOPIC (session ${TID:-unknown})" >&2

# Verify the file was written and check the score.
if [ ! -f "$REVIEW_FILE" ]; then
    echo "ERROR: codex did not produce $REVIEW_FILE" >&2
    rm -f "$REVIEW_DIFF_BASELINE"
    rm -rf "$WRAPPER_PRE_DIR"
    exit 3
fi

# Phase 2 R5+: relaxed contract per operator directive (2026-05-10).
# Codex tracks progress across rounds and may update prior round
# entries (with explicit "(updated DATE: ...)" markers) as findings
# resolve. We no longer enforce strict byte-identity on prior rounds.
# We DO require that the candidate contain a `### Round $ROUND_HINT`
# block AND the new round records progress against the prior round
# (delta line + addressed/remaining bullets).
if [ -n "$PRIOR_SNAPSHOT" ] && [ -f "$PRIOR_SNAPSHOT" ]; then
    if ! python3 "$ROOT/tools/review_round_tracking.py" \
            --prior "$PRIOR_SNAPSHOT" \
            --candidate "$REVIEW_FILE" \
            --round "$ROUND_HINT"; then
        echo "ERROR: review wrapper rejecting candidate (round-tracking violation); restoring prior $REVIEW_FILE" >&2
        cp "$PRIOR_SNAPSHOT" "$REVIEW_FILE"
        rm -f "$PRIOR_SNAPSHOT"
        rm -f "$REVIEW_DIFF_BASELINE"
        rm -rf "$WRAPPER_PRE_DIR"
        exit 4
    fi
    rm -f "$PRIOR_SNAPSHOT"
fi

DIFF_VIOLATIONS="$(python3 "$ROOT/tools/review_diff_allowlist.py" \
    --repo "$ROOT" \
    --baseline "$REVIEW_DIFF_BASELINE" \
    --allowed "$REVIEW_FILE_ABS" 2>&1 || true)"
rm -f "$REVIEW_DIFF_BASELINE"

# Restore any file codex modified outside the canonical review path.
# Per docs/plans/current-roadmap.md operator directive (2026-05-10):
# codex must NOT mutate files outside its canonical review; the wrapper
# silently restores any drift so parallel reviewers don't corrupt each
# other's outputs and source files survive review rounds untouched.
RESTORED=0
REVIEW_FILE_REL="$(realpath --relative-to="$ROOT" "$REVIEW_FILE_ABS" 2>/dev/null || echo "")"
while IFS= read -r path; do
    [ -z "$path" ] && continue
    [ "$path" = "$REVIEW_FILE_REL" ] && continue
    full="$ROOT/$path"
    # Never restore OTHER reviewers' canonical review files. Parallel
    # reviewer wrappers write their own Round-N entries to sibling
    # plan/reviews/<phase>/<topic>.md (slash-form per Phase 0 reorg)
    # OR plan/reviews/<phase>-<topic>.md (legacy dash-form) paths;
    # restoring those here from this wrapper's pre-codex snapshot
    # reverts their in-flight work. The original glob was
    # `plan/reviews/*.md` which only matched the flat-layout dash-form;
    # code-auditor round 4 #1 caught that nested slash-form sibling
    # reviews were not exempted. Match both layouts:
    case "$path" in results/logs/*|plan/reviews/.sessions/*) continue ;; esac
    if [ -f "$WRAPPER_PRE_DIR/$path" ]; then
        # Was dirty before codex ran — restore the captured pre-codex content.
        cp "$WRAPPER_PRE_DIR/$path" "$full"
        RESTORED=$((RESTORED + 1))
    elif git -C "$ROOT" ls-files --error-unmatch "$path" >/dev/null 2>&1; then
        # Tracked and clean pre-run: codex modified it — revert (v1.13; the
        # sibling-review exemption is obsolete under lock serialization).
        git -C "$ROOT" checkout -- "$path"
        RESTORED=$((RESTORED + 1))
    else
        rm -f "$full"
        RESTORED=$((RESTORED + 1))
    fi
    # If the file was NOT in the wrapper's pre-codex snapshot, do NOT
    # touch it: parallel reviewer wrappers may legitimately be writing
    # their own canonical review files at the same time. Restoring
    # those via `git checkout HEAD` would revert their in-flight Round
    # entries. The diff allowlist still flags this drift so the
    # operator can inspect it post-hoc.
done < <(cd "$ROOT" && {
    git diff --name-only HEAD --
    git ls-files --others --exclude-standard
} | sort -u)

rm -rf "$WRAPPER_PRE_DIR"
if [ -n "$DIFF_VIOLATIONS" ]; then
    echo "[$(date -u +%H:%M:%S)] $PHASE/$TOPIC restored $RESTORED file(s); UNCONTAINED drift detected:" >&2
    echo "$DIFF_VIOLATIONS" >&2
    exit 5
fi

python3 "$ROOT/tools/check_review_scores.py" --file "$REVIEW_FILE" --min "$THRESHOLD"
