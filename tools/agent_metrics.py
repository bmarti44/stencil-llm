#!/usr/bin/env python3
"""Compute agent-performance metrics from review history and git log.

"Are agents getting better at working in this repo?" is answered with
numbers computed from artifacts the agents being measured cannot edit:
review round logs are reviewer-authored (append-only, validated), and gate
commits are in git history. Nothing here is self-reported.

Emits results/agent_metrics.json and a markdown table on stdout (pasted
into each phase retro). Registered metrics (PLAN.md Section 2b):

  first_round_score    per topic: score of round 1 — do agents produce
                       better first drafts over time?
  rounds_to_accept     rounds until score >= threshold with zero open
                       high/critical (None if not yet accepted)
  findings_by_round    counts per severity per round — do high/criticals
                       trend to zero faster in later phases?
  open_high_critical   current open count per topic (must be 0 at accept)

Escaped defects and lesson recurrence are qualitative tags counted in the
retro by grepping reviews for `[escape:` and matching AGENTS.md lessons;
budget projection error comes from ledger entries. This tool only computes
what is mechanically parseable.

Usage: python3 tools/agent_metrics.py [--threshold 90]
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

SEVERITIES = ("critical", "high", "medium", "low")
ROUND_RE = re.compile(r"^### Round (\d+) — (\S+)", re.MULTILINE)
ROUND_SCORE_RE = re.compile(r"-\s*Score:\s*(\d+)\s*/\s*100")
FINDING_RE = re.compile(
    r"^\d+\.\s+\*\*(Critical|High|Medium|Low)\b([^\n]*)", re.MULTILINE | re.IGNORECASE
)


def parse_review(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    rounds = []
    matches = list(ROUND_RE.finditer(text))
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else text.find("\n## ", m.end())
        block = text[m.start(): end if end != -1 else len(text)]
        sm = ROUND_SCORE_RE.search(block)
        rounds.append({
            "round": int(m.group(1)),
            "date": m.group(2),
            "score": int(sm.group(1)) if sm else None,
        })
    rounds.sort(key=lambda r: r["round"])

    fsec = re.search(r"^## Findings\s*$(.*?)(?=^## |\Z)", text, re.MULTILINE | re.DOTALL)
    counts = {s: 0 for s in SEVERITIES}
    open_hc = 0
    if fsec:
        for fm in FINDING_RE.finditer(fsec.group(1)):
            sev = fm.group(1).lower()
            counts[sev] += 1
            closed = re.match(r"\s*\((?:resolved|refuted)", fm.group(2), re.IGNORECASE)
            if sev in ("critical", "high") and not closed:
                open_hc += 1
    return {"rounds": rounds, "current_findings": counts, "open_high_critical": open_hc}


def gate_commits(root: Path) -> list[str]:
    try:
        out = subprocess.check_output(
            ["git", "-C", str(root), "log", "--pretty=%h %s"], text=True, timeout=10)
    except subprocess.SubprocessError:
        return []
    return [ln for ln in out.splitlines() if re.search(r"\bgate\(G\d\w*\):", ln)]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--threshold", type=int, default=90)
    args = ap.parse_args(argv)

    root = Path(subprocess.check_output(
        ["git", "rev-parse", "--show-toplevel"], text=True, timeout=10).strip())
    reviews = sorted((root / "docs" / "reviews").rglob("*.md"))
    report = {"threshold": args.threshold, "topics": {}, "gate_commits": gate_commits(root)}

    for path in reviews:
        rel = str(path.relative_to(root / "docs" / "reviews"))
        info = parse_review(path)
        accepted_round = None
        for r in info["rounds"]:
            # acceptance = score at threshold in that round AND, if it is the
            # latest round, zero open high/critical now (history rounds can't
            # retro-check openness, so only the latest round can accept).
            if (r["score"] is not None and r["score"] >= args.threshold
                    and r["round"] == info["rounds"][-1]["round"]
                    and info["open_high_critical"] == 0):
                accepted_round = r["round"]
        report["topics"][rel] = {
            "first_round_score": info["rounds"][0]["score"] if info["rounds"] else None,
            "latest_round": info["rounds"][-1]["round"] if info["rounds"] else 0,
            "latest_score": info["rounds"][-1]["score"] if info["rounds"] else None,
            "rounds_to_accept": accepted_round,
            "scores_by_round": {r["round"]: r["score"] for r in info["rounds"]},
            "current_findings": info["current_findings"],
            "open_high_critical": info["open_high_critical"],
        }

    out = root / "results" / "agent_metrics.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    print("| review | r1 score | latest (round) | accepted | open H/C | C/H/M/L now |")
    print("|---|---|---|---|---|---|")
    for rel, t in report["topics"].items():
        c = t["current_findings"]
        print(f"| {rel} | {t['first_round_score']} | {t['latest_score']} "
              f"(r{t['latest_round']}) | "
              f"{'r' + str(t['rounds_to_accept']) if t['rounds_to_accept'] else 'no'} | "
              f"{t['open_high_critical']} | "
              f"{c['critical']}/{c['high']}/{c['medium']}/{c['low']} |")
    print(f"\ngate commits: {len(report['gate_commits'])}; written {out.relative_to(root)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
