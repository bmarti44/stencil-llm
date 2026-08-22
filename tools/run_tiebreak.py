#!/usr/bin/env python3
"""Runnable tie-break mode (PLAN.md 2b, v1.14; verbatim verification v1.22).

Usage: python3 tools/run_tiebreak.py <prompt-file> <output-file> <review-file>

When <review-file> is given, every "> "-quoted line in the prompt must be an
exact line of that file — mechanically proving the arbiter record quotes the
reviewer verbatim rather than paraphrasing (the vacated batch-4 failure).

Appends, in order: the full prompt verbatim (committed evidence), then the
arbiter's raw response, to <output-file>. The caller commits the prompt
BEFORE running (tie-break auditability rule); this tool re-appends it so the
output file is self-contained even if invoked directly.
"""
import json, sys, urllib.request, os
from datetime import datetime, timezone

def main():
    if len(sys.argv) != 4:
        print(__doc__, file=sys.stderr); return 2
    import subprocess, fcntl
    root = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True,
                          text=True, check=True).stdout.strip()
    # Prompt must be a tracked, committed, in-repo file (no ignored or
    # out-of-repository paths), and we serialize on the repo lock.
    lk = open(os.path.join(root, ".review.lock"), "w"); fcntl.flock(lk, fcntl.LOCK_EX)
    rel = os.path.relpath(os.path.abspath(sys.argv[1]), root)
    if rel.startswith(".."):
        print(f"ERROR: prompt {sys.argv[1]} is outside the repository", file=sys.stderr); return 3
    tracked = subprocess.run(["git", "-C", root, "ls-files", "--error-unmatch", rel],
                             capture_output=True)
    if tracked.returncode != 0:
        print(f"ERROR: prompt {rel} is not a tracked file", file=sys.stderr); return 3
    dirty = subprocess.run(["git", "-C", root, "status", "--porcelain", "--", rel],
                           capture_output=True, text=True, check=True).stdout.strip()
    if dirty:
        print(f"ERROR: {sys.argv[1]} is not committed clean; commit the prompt "
              "BEFORE running the tie-break (auditability rule)", file=sys.stderr)
        return 3
    prompt = open(sys.argv[1], encoding="utf-8").read()
    if True:
        review_lines = set(l.strip() for l in open(sys.argv[3], encoding="utf-8").read().splitlines() if l.strip())
        quoted = [l[2:].strip() for l in prompt.splitlines()
                  if l.startswith("> ") and not l[2:].lstrip().startswith("#")]
        if not quoted or sum(len(q) for q in quoted) < 200:
            print("ERROR: at least 200 characters of non-heading verbatim '> ' quotes from the review file are required", file=sys.stderr)
            return 3
        fake = [q for q in quoted if q not in review_lines]
        if fake:
            print(f"ERROR: {len(fake)} quoted line(s) are not verbatim lines of {sys.argv[3]}; first: {fake[0][:100]}", file=sys.stderr)
            return 3
    for marker, why in ((">", "verbatim quotation blocks ('> ...')"),
                        ("Reviewer", "the reviewer's argument"),
                        ("Orchestrator", "the orchestrator's argument")):
        if marker not in prompt:
            print(f"ERROR: prompt lacks {why}; tie-breaks require the verbatim record", file=sys.stderr)
            return 3
    body = {"model": os.environ.get("KIMI_MODEL", "kimi-k3:cloud"),
            "prompt": prompt, "stream": False, "think": True}
    req = urllib.request.Request(
        os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434") + "/api/generate",
        data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=1800) as r:
        out = json.loads(r.read())["response"].strip()
    import re as _re
    verdicts = _re.findall(r"\*\*Verdict:?\*\*:?\s*(UPHOLD|REFUTE|MIDDLE)", out, _re.IGNORECASE)
    if not verdicts:
        print("ERROR: no enumerated Verdict (UPHOLD/REFUTE/MIDDLE) line found; not a ruling", file=sys.stderr)
        rej = sys.argv[2] + ".rejected"
        open(rej, "a", encoding="utf-8").write(out + "\n")
        return 4
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    with open(sys.argv[2], "a", encoding="utf-8") as f:
        f.write(f"\n\n# Tie-break — {stamp} ({body['model']})\n\n## Prompt (verbatim)\n\n"
                f"```\n{prompt}\n```\n\n## Raw verdict\n\n{out}\n")
    print(out)
    led = os.path.join(root, "plan", "LEDGER.md")
    entry = (f"- {stamp.split()[0]}, tiebreak (auto, run_tiebreak.py). Prompt {rel}, "
             f"output {sys.argv[2]}, verdicts: {', '.join(v.upper() for v in verdicts)}. "
             "Next: execute the verdicts and record them in the next orchestrator entry.\n")
    s2 = open(led).read()
    marker = "### Ledger\n\n"
    open(led, "w").write(s2.replace(marker, marker + entry, 1) if marker in s2 else s2 + entry)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
