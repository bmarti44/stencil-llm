#!/usr/bin/env python3
"""Runnable tie-break mode (PLAN.md 2b, v1.14).

Usage: python3 tools/run_tiebreak.py <prompt-file> <output-file>

Appends, in order: the full prompt verbatim (committed evidence), then the
arbiter's raw response, to <output-file>. The caller commits the prompt
BEFORE running (tie-break auditability rule); this tool re-appends it so the
output file is self-contained even if invoked directly.
"""
import json, sys, urllib.request, os
from datetime import datetime, timezone

def main():
    if len(sys.argv) != 3:
        print(__doc__, file=sys.stderr); return 2
    import subprocess
    dirty = subprocess.run(["git", "status", "--porcelain", "--", sys.argv[1]],
                           capture_output=True, text=True).stdout.strip()
    if dirty:
        print(f"ERROR: {sys.argv[1]} is not committed clean; commit the prompt "
              "BEFORE running the tie-break (auditability rule)", file=sys.stderr)
        return 3
    prompt = open(sys.argv[1], encoding="utf-8").read()
    body = {"model": os.environ.get("KIMI_MODEL", "kimi-k3:cloud"),
            "prompt": prompt, "stream": False, "think": True}
    req = urllib.request.Request(
        os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434") + "/api/generate",
        data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=1800) as r:
        out = json.loads(r.read())["response"].strip()
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    with open(sys.argv[2], "a", encoding="utf-8") as f:
        f.write(f"\n\n# Tie-break — {stamp} ({body['model']})\n\n## Prompt (verbatim)\n\n"
                f"```\n{prompt}\n```\n\n## Raw verdict\n\n{out}\n")
    print(out)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
