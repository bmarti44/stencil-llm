#!/usr/bin/env python3
"""Run a kimi-k3 (ollama cloud) cross-model review for one topic.

Mirrors run_codex_review.sh in shape but calls the ollama REST API with the
whole (small) repo inlined as context — kimi has no tool access. Writes to
docs/reviews/{phase}/{topic}-kimi.md, enforces the same append-only round
history (tools/review_round_tracking.py) and severity-aware score gate
(tools/check_review_scores.py), and serializes under the same .review.lock
as the sol wrappers so their drift checks never see it mid-flight.

A candidate failing the round-tracking contract is saved to the sidecar
<topic>-kimi.rejected.md (never to the canonical path) for diagnosis.

Role per PLAN.md Section 2b: kimi is the cross-model second reviewer and
deadlock tie-breaker. Its findings are advisory — confirmed ones are fed
into the sol reviewer-of-record's next round for adjudication.

Usage:
    python3 tools/run_kimi_review.py <phase> <topic> <threshold>

Env overrides:
    OLLAMA_HOST       default http://127.0.0.1:11434
    KIMI_MODEL        default kimi-k3:cloud
    KIMI_TIMEOUT_SEC  default 1800
    KIMI_CONTEXT_MAX  default 400000 (bytes of repo context)
"""
from __future__ import annotations

import fcntl
import json
import re
import os
import subprocess
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

SLUG_RE = re.compile(r"^[a-z0-9-]+$")
# Tracked text files inlined as review context, in priority order.
# Priority order matters: the context cap truncates from the END, so the
# governing docs, code, and gate artifacts come first and bulky review
# history last (v1.14).
CONTEXT_GLOBS = [
    "PLAN.md", "README.md", "AGENTS.md", ".gitignore", "Makefile", "pyproject.toml",
    "results/*.md", "docs/retros/*.md",
    "src/**/*.py", "tests/**/*.py", "scripts/*.py", "configs/*.json",
    "tools/*.sh", "tools/*.py", "tools/codex-prompts/*.md",
    "docs/reviews/**/*.md",
]


def find_root() -> Path:
    out = subprocess.check_output(
        ["git", "rev-parse", "--show-toplevel"], text=True, timeout=10
    ).strip()
    return Path(out)


def build_context(root: Path, review_file: Path, max_bytes: int) -> str:
    parts, total = [], 0
    seen = set()
    for pattern in CONTEXT_GLOBS:
        for p in sorted(root.glob(pattern)):
            if not p.is_file() or p in seen or p == review_file or p.name.endswith(".rejected.md"):
                continue
            seen.add(p)
            try:
                text = p.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            rel = p.relative_to(root)
            block = f"\n\n===== FILE: {rel} =====\n{text}"
            if total + len(block) > max_bytes:
                parts.append(f"\n\n===== TRUNCATED: context cap reached before {rel} =====")
                return "".join(parts)
            parts.append(block)
            total += len(block)
    return "".join(parts)


def call_ollama(host: str, model: str, prompt: str, timeout_sec: int) -> str:
    body = {"model": model, "prompt": prompt, "stream": False, "think": True}
    req = urllib.request.Request(
        f"{host}/api/generate",
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
        parsed = json.loads(resp.read())
    text = parsed.get("response", "")
    if not text:
        raise RuntimeError(f"kimi returned empty response; keys={list(parsed.keys())}")
    return text.strip()


def main() -> int:
    if len(sys.argv) != 4:
        print(f"Usage: {sys.argv[0]} <phase> <topic> <threshold>", file=sys.stderr)
        return 2
    phase, topic, threshold_s = sys.argv[1], sys.argv[2], sys.argv[3]
    for label, v in (("phase", phase), ("topic", topic)):
        if not SLUG_RE.fullmatch(v):
            print(f"ERROR: invalid {label}: must match [a-z0-9-]+", file=sys.stderr)
            return 2
    threshold = int(threshold_s)
    floor = 75 if "retro" in topic else 90
    if threshold < floor:
        print(f"ERROR: threshold {threshold} below registered floor {floor} for topic {topic}", file=sys.stderr)
        return 2
    if not 0 <= threshold <= 100:
        print("ERROR: threshold must be 0-100", file=sys.stderr)
        return 2

    root = find_root()
    sys.path.insert(0, str(root / "tools"))
    import check_review_scores  # noqa: E402
    import review_round_tracking  # noqa: E402

    host = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434")
    model = os.environ.get("KIMI_MODEL", "kimi-k3:cloud")
    timeout_sec = int(os.environ.get("KIMI_TIMEOUT_SEC", "1800"))
    ctx_max = int(os.environ.get("KIMI_CONTEXT_MAX", "400000"))

    review_file = root / "docs" / "reviews" / phase / f"{topic}-kimi.md"
    prompt_file = root / "tools" / "codex-prompts" / f"review-{topic}.md"
    # Coverage backstop (PLAN 2b, v1.15): kimi ALWAYS reviews phase-style
    # topics through the generic lens, regardless of bespoke sol fragments.
    if topic.startswith("phase") or topic in ("tradeoff", "report"):
        prompt_file = root / "tools" / "codex-prompts" / "review-phase.md"
    header = root / "tools" / "codex-prompts" / "_common-header.md"
    for f in (prompt_file, header):
        if not f.exists():
            print(f"ERROR: missing {f}", file=sys.stderr)
            return 2
    review_file.parent.mkdir(parents=True, exist_ok=True)

    # Same serialization as the sol wrappers: never overlap with a codex run
    # whose drift checker would flag this file appearing mid-flight.
    lock_fh = open(root / ".review.lock", "w")
    fcntl.flock(lock_fh, fcntl.LOCK_EX)

    prior = review_file.read_text(encoding="utf-8") if review_file.exists() else ""
    rounds = [int(m) for m in re.findall(r"^### Round (\d+)", prior, re.MULTILINE)]
    round_n = (max(rounds) + 1) if rounds else 1
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    churn = ("" if round_n == 1 else
        "0. ANTI-CHURN (binding, PLAN 2b): this is round %d of YOUR review — re-verify "
        "your existing findings against the current files first; add new findings ONLY "
        "for regressions introduced by fixes or clear in-scope misses from your round 1. "
        "Do not expand scope.\n" % round_n)
    parts = [
        churn,
        "# KIMI CROSS-MODEL REVIEWER — IMPORTANT (overrides conflicting text below)\n\n"
        "1. You have NO TOOL ACCESS. The only repository content you can see is the "
        "REPOSITORY CONTEXT block below. If something you need is not visible, score "
        "what you can verify and add a finding naming the unverified surface — do not "
        "guess and do not score 0 for invisibility.\n"
        "2. Your only output is the entire updated review markdown, starting with the "
        f"`# {topic.title()} Review (kimi) — {phase}` header line and ending with the "
        "Evidence section. No preamble, no code fences around the document.\n"
        "3. ROUND CONTRACT, mechanically enforced — violations are rejected: never "
        "delete a prior finding; a prior Critical/High finding keeps its number and "
        "is closed only by marking its first line with (resolved DATE: how) or "
        "(refuted DATE: why). Your new round block MUST contain the three bullets "
        "`- Score:` (with delta), `- Addressed since prior round:`, and "
        "`- New or remaining:`. Preserve every prior round block.\n"
        "4. You are the SECOND, independent reviewer; a sol (codex) review of the same "
        "material may appear in the context. Do not defer to it: your value is finding "
        "what it missed and disputing what it got wrong. Explicitly list any sol "
        "findings you believe are wrong, with reasons.\n"
        f"5. Round number: Round {round_n}. Threshold: {threshold} / 100. "
        f"Reviewer model: kimi/{model}. Date: {today}.\n\n---\n\n",
        header.read_text(encoding="utf-8"),
        "\n\n---\n\n## TOPIC RUBRIC\n\n",
        prompt_file.read_text(encoding="utf-8"),
        "\n\n---\n\n## REPOSITORY CONTEXT (the only source of truth you can see)\n",
        build_context(root, review_file, ctx_max),
    ]
    if prior:
        parts.append("\n\n---\n\n## PRIOR ROUND CONTENT (preserve every prior round verbatim)\n\n" + prior)
    parts.append("\n\n---\n\n# YOUR RESPONSE STARTS NOW\nBegin with the markdown header line.\n")
    prompt = "".join(parts)

    print(f"[{datetime.now(timezone.utc):%H:%M:%S}] kimi review starting: "
          f"{phase}/{topic} -> {review_file} ({len(prompt)} prompt bytes)", file=sys.stderr)
    candidate = call_ollama(host, model, prompt, timeout_sec)
    # Strip a single wrapping code fence if the model added one anyway.
    m = re.fullmatch(r"```(?:markdown)?\n(.*)\n```", candidate, re.DOTALL)
    if m:
        candidate = m.group(1)

    rep = review_round_tracking.validate(prior, candidate, round_number=round_n)
    if not rep["passed"]:
        rej = review_file.with_suffix(".rejected.md")
        rej.write_text(candidate, encoding="utf-8")
        print(f"ERROR: kimi candidate violates round-tracking contract "
              f"(saved to {rej}):", file=sys.stderr)
        for f in rep["findings"]:
            print(f"  - {f}", file=sys.stderr)
        return 4
    review_file.write_text(candidate, encoding="utf-8")
    print(f"[{datetime.now(timezone.utc):%H:%M:%S}] kimi review finished: {phase}/{topic}", file=sys.stderr)
    return check_review_scores.main(["--file", str(review_file), "--min", str(threshold)])


if __name__ == "__main__":
    raise SystemExit(main())
