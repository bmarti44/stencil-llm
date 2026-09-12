"""Exp 4C release verification, orchestrator (REGISTRATION-4C.md; review finding 9).

Builds a FRESH virtual environment with the qualification's pinned dependency
versions (uv, no system site packages), an empty remote-code cache, and runs
``memorycode_4c_verify_clean.py`` inside it under ``timeout 900`` (the registered
verification allowance) against the staged release directory and the prospectively
fixed qualification receipts (SETUP 359-99, both flag states). Binds the result to the
qualification's package fingerprint; writes
results/memorycode-long/verification-4c.json.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "memorycode-long"
PINNED = ("torch", "transformers", "tokenizers")
EXTRA = {"accelerate": "1.14.0", "safetensors": "0.8.0", "numpy": "2.5.2"}
RECEIPTS = ("00-timing-359-99-base.json", "01-timing-359-99-focus.json")
ALLOWANCE = 900


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--staged", default=str(ROOT / "deploy/stencil_focus/build/release-4c")
    )
    parser.add_argument("--qualification", default=str(OUT / "qualification-4c.json"))
    parser.add_argument("--out", default=str(OUT / "verification-4c.json"))
    parser.add_argument("--venv", default=None, help="fresh venv dir (default: temp)")
    args = parser.parse_args(argv)
    if Path(args.out).exists():
        raise SystemExit(
            f"{args.out} exists; verification runs once per staged package"
        )
    qual = json.loads(Path(args.qualification).read_text())
    env = qual["manifest"]["environment"]
    pins = [f"{p}=={env[p].split('+')[0]}" for p in PINNED]
    pins += [f"{k}=={v}" for k, v in EXTRA.items()]
    venv = Path(args.venv or tempfile.mkdtemp(prefix="stencil-verify-"))
    py = venv / "bin" / "python"
    subprocess.run(["uv", "venv", "--python", env["python"], str(venv)], check=True)
    subprocess.run(["uv", "pip", "install", "--python", str(py), *pins], check=True)
    modules_cache = Path(tempfile.mkdtemp(prefix="stencil-verify-modules-"))
    receipts = [str(OUT / "qualification-4c" / "calls" / r) for r in RECEIPTS]
    clean_env = {
        "PATH": os.environ.get("PATH", ""),
        "HOME": os.environ.get("HOME", ""),
        "HF_MODULES_CACHE": str(modules_cache),
        "HF_HUB_OFFLINE": "1",
        "PYTHONNOUSERSITE": "1",
    }
    started = time.monotonic()
    proc = subprocess.run(
        [
            "timeout",
            str(ALLOWANCE),
            str(py),
            str(ROOT / "scripts/memorycode_4c_verify_clean.py"),
            args.staged,
            args.out + ".clean.json",
            *receipts,
        ],
        env=clean_env,
        cwd=str(venv),
        capture_output=True,
        text=True,
    )
    wall = time.monotonic() - started
    clean_path = Path(args.out + ".clean.json")
    clean = json.loads(clean_path.read_text()) if clean_path.exists() else None
    expected = qual["manifest"]["package_sha256"]
    bound = bool(clean) and clean["package_sha256"] == expected
    passed = proc.returncode == 0 and bool(clean) and clean["passed"] and bound
    passed = passed and wall <= ALLOWANCE
    report = {
        "registration": "results/memorycode-long/REGISTRATION-4C.md",
        "staged_dir": args.staged,
        "qualification_sha256": hashlib.sha256(
            Path(args.qualification).read_bytes()
        ).hexdigest(),
        "package_sha256": expected,
        "fingerprint_bound": bound,
        "clean_environment": {"pins": pins, "venv": str(venv)},
        "process_returncode": proc.returncode,
        "wall_seconds": wall,
        "allowance_seconds": ALLOWANCE,
        "stdout_tail": proc.stdout[-2000:],
        "stderr_tail": proc.stderr[-2000:],
        "clean_report": clean,
        "passed": passed,
        "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    Path(args.out).write_text(json.dumps(report, indent=1))
    print(json.dumps({"passed": passed, "wall_seconds": wall, "rc": proc.returncode}))
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
