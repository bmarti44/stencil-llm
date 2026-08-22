"""Parse `**Score:** N / 100` from a review markdown file.

The current score is the first match (top of file); round-log entries are
preserved verbatim below it. Exit code 0 if score >= threshold, 1 otherwise.

Usage:
    python3 tools/check_review_scores.py --file docs/reviews/plan/science.md --min 90
    python3 tools/check_review_scores.py --files "docs/reviews/plan/*.md" --min 90
"""
from __future__ import annotations

import argparse
import glob
import re
import sys
from pathlib import Path

SCORE_RE = re.compile(r"^\*\*Score:\*\*\s*(\d{1,3})\s*/\s*100\s*$", re.MULTILINE)
# An open high/critical finding: numbered entry in ## Findings whose first line
# declares severity Critical or High and carries no (resolved ...) / (refuted ...)
# closure marker authored by a reviewer round.
OPEN_HC_RE = re.compile(r"^\d+\.\s+\*\*(?:Critical|High)\b(?![^\n]*\((?:resolved|refuted))", re.MULTILINE | re.IGNORECASE)


def open_high_critical(path: Path) -> list[str]:
    """Return first-lines of open High/Critical findings in the ## Findings section."""
    text = path.read_text(encoding="utf-8")
    m = re.search(r"^## Findings\s*$(.*?)(?=^## |\Z)", text, re.MULTILINE | re.DOTALL)
    if not m:
        # A review with no Findings section is malformed, not clean: treat as
        # one synthetic blocker so deleting the section cannot yield a PASS.
        return ["<missing '## Findings' section — malformed review>"]
    return [ln.strip()[:120] for ln in m.group(1).splitlines() if OPEN_HC_RE.match(ln.strip())]


def parse_score(path: Path) -> int | None:
    """Return the current score (first match) from a review file, or None if absent."""
    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8")
    m = SCORE_RE.search(text)
    if not m:
        return None
    return int(m.group(1))


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint for tools/check_review_scores.py. Returns process exit code."""
    p = argparse.ArgumentParser(description=__doc__)
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--file", type=Path, help="Single review file path")
    g.add_argument("--files", type=str, help="Glob pattern for multiple review files")
    p.add_argument("--min", dest="threshold", type=int, default=90, help="Minimum score required (inclusive)")
    p.add_argument("--quiet", action="store_true", help="Only print failing files")
    args = p.parse_args(argv)

    if args.file:
        paths = [args.file]
    else:
        paths = [Path(s) for s in sorted(glob.glob(args.files))]

    if not paths:
        print(f"No files matched", file=sys.stderr)
        return 2

    failed = 0
    for path in paths:
        score = parse_score(path)
        if score is None:
            print(f"FAIL  {path}: no Score: line found", file=sys.stderr)
            failed += 1
            continue
        open_hc = open_high_critical(path)
        if score < args.threshold:
            print(f"FAIL  {path}: {score}/100 (need >={args.threshold})")
            failed += 1
        elif open_hc:
            print(f"FAIL  {path}: {score}/100 but {len(open_hc)} open high/critical finding(s):")
            for ln in open_hc:
                print(f"        {ln}")
            failed += 1
        elif not args.quiet:
            print(f"PASS  {path}: {score}/100, no open high/critical findings")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
