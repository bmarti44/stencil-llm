"""Relaxed round-tracking validator for review files.

Per operator directive (2026-05-10): codex may reuse / update prior
round entries; for a single review, codex just needs to track its
progress for each round — where it was and what it added/updated/
changed.

This module replaces the strict append-only validator with a softer
contract:

  1. Candidate must contain a `### Round $ROUND_HINT — DATE` header.
  2. The new round block must record progress against prior:
     - a `Score: N / 100 (delta vs prior round: +/-X)` line, OR a
       `(first review)` qualifier when no prior round exists.
     - either an `Addressed since prior round:` bullet list OR an
       explicit `(initial review)` marker.
     - a `New or remaining:` bullet list.
  3. Candidate must contain a top-of-file `**Score:** N / 100`
     frontmatter line (parseable by check_review_scores.py).

CLI: exit 0 when the candidate satisfies the contract, 1 otherwise.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def _parse_round_block(text: str, round_number: int) -> str | None:
    """Return the `### Round N` block text, or None if absent."""
    pattern = re.compile(
        rf"^### Round {round_number}\b.*?(?=^### Round \d+|^## |\Z)",
        re.MULTILINE | re.DOTALL,
    )
    m = pattern.search(text)
    return m.group(0) if m else None


def _has_score_frontmatter(text: str) -> bool:
    return bool(re.search(r"^\*\*Score:\*\*\s*\d+\s*/\s*100", text, re.MULTILINE))


def _round_records_progress(block: str, *, has_prior: bool) -> tuple[bool, list[str]]:
    findings: list[str] = []
    # Score line.
    score_line = re.search(r"-\s*Score:\s*\d+\s*/\s*100", block)
    if not score_line:
        findings.append("new round block missing `- Score: N / 100` line")
    if has_prior:
        delta_line = re.search(
            r"delta\s+vs\s+prior\s+round\s*:\s*[+\-]?\d", block, re.IGNORECASE,
        )
        first_review_line = re.search(r"first\s+review", block, re.IGNORECASE)
        if not (delta_line or first_review_line):
            findings.append(
                "new round block missing `(delta vs prior round: +/-X)` "
                "qualifier; required when prior rounds exist"
            )
        addressed = re.search(
            r"^\s*-\s*Addressed since prior round\s*:", block, re.MULTILINE,
        )
        initial_marker = re.search(r"\(initial review\)", block, re.IGNORECASE)
        if not (addressed or initial_marker):
            findings.append(
                "new round block missing `- Addressed since prior round:` bullet "
                "or `(initial review)` marker"
            )
    remaining = re.search(r"^\s*-\s*New or remaining\s*:", block, re.MULTILINE)
    if not remaining:
        findings.append("new round block missing `- New or remaining:` bullet")
    return (len(findings) == 0, findings)


def validate(prior_text: str, candidate_text: str, *, round_number: int) -> dict:
    findings: list[str] = []
    block = _parse_round_block(candidate_text, round_number)
    if block is None:
        # Compute outside the f-string so Python 3.10 doesn't choke on the
        # backslash in the regex pattern inside the f-string expression.
        observed_rounds = re.findall(r"^### Round (\d+)", candidate_text, re.MULTILINE)
        findings.append(
            f"candidate has no `### Round {round_number}` block (got rounds "
            f"{observed_rounds})"
        )
        return {"passed": False, "findings": findings}
    if not _has_score_frontmatter(candidate_text):
        findings.append(
            "candidate missing top-of-file `**Score:** N / 100` frontmatter"
        )
    # Append-only round history: every prior `### Round N` block must still be
    # present in the candidate (content may be annotated with "(updated DATE:)"
    # markers, but a round heading may never disappear).
    prior_rounds = set(re.findall(r"^### Round (\d+)", prior_text or "", re.MULTILINE))
    cand_rounds = set(re.findall(r"^### Round (\d+)", candidate_text, re.MULTILINE))
    missing = sorted(prior_rounds - cand_rounds, key=int)
    if missing:
        findings.append(
            f"candidate deleted prior round block(s) {missing}; round history is append-only"
        )
    has_prior = bool(prior_rounds)
    ok, prog_findings = _round_records_progress(block, has_prior=has_prior)
    findings.extend(prog_findings)
    return {"passed": len(findings) == 0, "findings": findings}


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--prior", type=Path, required=True)
    p.add_argument("--candidate", type=Path, required=True)
    p.add_argument("--round", type=int, required=True)
    args = p.parse_args(argv)

    try:
        prior_text = args.prior.read_text(encoding="utf-8") if args.prior.exists() else ""
        candidate_text = args.candidate.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"ERROR: cannot read input: {exc}", file=sys.stderr)
        return 2

    rep = validate(prior_text, candidate_text, round_number=args.round)
    if rep["passed"]:
        print(f"OK: candidate satisfies round-{args.round} tracking contract")
        return 0
    print("FAIL: candidate violates round-tracking contract:", file=sys.stderr)
    for f in rep["findings"]:
        print(f"  - {f}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
