"""Score ONE model-produced function against the hidden oracle, in a subprocess.

The gate in scripts/scoped_gate.py runs trusted renderer output in process.  This
scorer runs MODEL output, which is untrusted, so it is a separate process the
caller kills on a timeout.

Reads one JSON object on stdin: {"block": "S1", "case": 0, "source": "def ..."}
Writes one JSON object on stdout: {"scores": {...}, "ok": bool, "error": str}

    echo '{"block":"S1","case":0,"source":"..."}' \\
        | uv run python scripts/scoped_score_one.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


def main() -> int:
    from stencil.scoped_blocks import (
        Candidate,
        append_function,
        entering_project,
        evaluate,
    )
    from stencil.scoped_dev_blocks import BLOCKS

    spec = json.loads(sys.stdin.read())
    block = next(b for b in BLOCKS if b.id == spec["block"])
    case = block.cases[int(spec["case"])]
    project = entering_project(block)
    try:
        candidate = Candidate(
            append_function(project, case.path, spec["source"]), "model")
        scores = evaluate(block, case, candidate)
        out = {"scores": scores, "ok": all(scores.values()), "error": ""}
    except Exception as exc:  # noqa: BLE001 - a crash is a failed case, not a crash here
        out = {"scores": {}, "ok": False, "error": f"{type(exc).__name__}: {exc}"}
    print(json.dumps(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
