# ruff: noqa
"""CONTRACT v3 registered post-build pre-run hash audit."""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ARTIFACTS = [
    "src/stencil/t2_sessions.py", "src/stencil/t2_runner.py",
    "scripts/t2_train_selector.py", "scripts/t2_shakeout.py",
    "src/stencil/qwen3.py", "src/stencil/qwen_task.py",
    "results/qwen/t2-selector.pt", "models/qwen3-1.7b.pt",
    "models/qwen3-1.7b-hf/tokenizer.json", "TIMED-SELECTOR-PLAN.md",
]
out = {}
for a in ARTIFACTS:
    p = ROOT / a
    if not p.exists():
        print(f"MISSING: {a}"); sys.exit(1)
    out[a] = hashlib.sha256(p.read_bytes()).hexdigest()
(ROOT / "results" / "qwen" / "t2-hash-audit.json").write_text(json.dumps(out, indent=1))
print("hash audit written:", len(out), "artifacts")
