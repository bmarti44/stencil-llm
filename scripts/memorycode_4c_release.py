"""Exp 4C release consumer: the ONLY path that pushes the evaluated artifact.

Requires, bound to one package fingerprint (REGISTRATION-4C.md; review finding 9):
1. ``summary-4c.json`` with ``statistical_gates_passed`` and technical completeness;
2. an accepted result audit (``results/memorycode-long/audit-4c.json`` naming the
   summary digest, verdict ACCEPT);
3. ``verification-4c.json`` passed, fingerprint-bound to the qualification.

``--stage`` copies the evaluated hub build into an immutable staging directory with
the card as README.md and rehashes it (must equal the qualification fingerprint);
``--push`` rehashes the staging inventory again immediately before uploading,
uploads that directory, records the HF commit and verifies the remote inference-file
hashes against the release manifest. Never reassembles the package.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import shutil
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "memorycode-long"

_spec = importlib.util.spec_from_file_location(
    "memorycode_package_run", ROOT / "scripts" / "memorycode_package_run.py"
)
runner = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(runner)
screen = runner.screen
UPSTREAM_REVISION = "1cfa9a7208912126459214e8b04321603b3df60c"


def _sha(p: Path) -> str:
    return screen._sha256(p)


def git_blob_sha1(p: Path) -> str:
    data = p.read_bytes()
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


def gates(
    summary_path: Path, audit_path: Path, verification_path: Path, qual_path: Path
):
    """Every release gate; an empty problem list authorizes staging/pushing."""
    problems = []
    docs = {}
    named = (
        ("summary", summary_path),
        ("audit", audit_path),
        ("verification", verification_path),
        ("qualification", qual_path),
    )
    for name, p in named:
        if not p.exists():
            problems.append(f"{name} missing: {p}")
        else:
            docs[name] = json.loads(p.read_text())
    if problems:
        return problems, docs
    s, a, v, q = (
        docs["summary"],
        docs["audit"],
        docs["verification"],
        docs["qualification"],
    )
    pkg = q["manifest"]["package_sha256"]
    if not s["reading"].get("statistical_gates_passed") or not s["status"].get(
        "technical_ok"
    ):
        problems.append("summary: statistical gates not passed")
    if s.get("qualification_sha256") != _sha(qual_path):
        problems.append("summary: bound to another qualification")
    if a.get("verdict") != "ACCEPT":
        problems.append("audit: not ACCEPT")
    if a.get("summary_sha256") != _sha(summary_path):
        problems.append("audit: bound to another summary")
    if a.get("package_sha256") != pkg:
        problems.append("audit: bound to another package")
    if not v.get("passed") or not v.get("fingerprint_bound"):
        problems.append("verification: not passed")
    if v.get("package_sha256") != pkg or v.get("qualification_sha256") != _sha(
        qual_path
    ):
        problems.append("verification: bound to another package/qualification")
    return problems, docs


def stage(hub: Path, staged: Path, card: Path, expected_fingerprint: str) -> dict:
    if staged.exists():
        raise SystemExit(f"{staged} exists; staging is immutable")
    shutil.copytree(
        hub, staged, ignore=shutil.ignore_patterns("__pycache__", "README.md")
    )
    shutil.copy2(card, staged / "README.md")
    files = runner.package_files(staged)
    fp = runner.package_fingerprint(files)
    if fp != expected_fingerprint:
        shutil.rmtree(staged)
        raise SystemExit(f"staged fingerprint {fp} != evaluated {expected_fingerprint}")
    return files


def inventory_of(staged: Path) -> dict:
    return {
        p.relative_to(staged).as_posix(): {
            "sha256": _sha(p),
            "git_blob_sha1": git_blob_sha1(p),
            "bytes": p.stat().st_size,
        }
        for p in sorted(staged.rglob("*"))
        if p.is_file() and "__pycache__" not in p.parts
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--hub", default=str(ROOT / "deploy/stencil_focus/build/hub-4b")
    )
    parser.add_argument(
        "--staged", default=str(ROOT / "deploy/stencil_focus/build/release-4c")
    )
    parser.add_argument(
        "--card", default=str(ROOT / "deploy/stencil_focus/MODEL_CARD-4b.md")
    )
    parser.add_argument(
        "--records", default=str(OUT / "screen_long_4c-4b-package-role_evicted")
    )
    parser.add_argument("--qualification", default=str(OUT / "qualification-4c.json"))
    parser.add_argument("--audit", default=str(OUT / "audit-4c.json"))
    parser.add_argument("--verification", default=str(OUT / "verification-4c.json"))
    parser.add_argument("--repo", default="bmarti44/stencil-focus-qwen3-4b")
    parser.add_argument("--stage", action="store_true")
    parser.add_argument("--push", action="store_true")
    args = parser.parse_args(argv)
    summary_path = Path(args.records) / "summary-4c.json"
    qual_path = Path(args.qualification)
    if args.stage:
        # staging needs the statistical gate + audit; verification runs on the staging
        problems, docs = gates(
            summary_path, Path(args.audit), Path(args.verification), qual_path
        )
        problems = [p for p in problems if not p.startswith("verification")]
        if problems:
            raise SystemExit("release refused: " + "; ".join(problems))
        expected = docs["qualification"]["manifest"]["package_sha256"]
        files = stage(Path(args.hub), Path(args.staged), Path(args.card), expected)
        print(f"staged {len(files)} inference files at {args.staged}")
        return 0
    problems, docs = gates(
        summary_path, Path(args.audit), Path(args.verification), qual_path
    )
    if problems:
        raise SystemExit("release refused: " + "; ".join(problems))
    staged = Path(args.staged)
    if docs["verification"].get("staged_dir") != str(staged):
        raise SystemExit("verification ran on a different staged directory")
    files = runner.package_files(staged)  # rehash immediately before pushing
    fp = runner.package_fingerprint(files)
    expected = docs["qualification"]["manifest"]["package_sha256"]
    if fp != expected:
        raise SystemExit(f"staged bytes changed since verification: {fp} != {expected}")
    inventory = inventory_of(staged)
    manifest = {
        "registration": "results/memorycode-long/REGISTRATION-4C.md",
        "repo": args.repo,
        "package_sha256": fp,
        "package_files": files,
        "upload_inventory": inventory,
        "upstream_revision": UPSTREAM_REVISION,
        "digests": {
            "qualification": _sha(qual_path),
            "items_4c": _sha(OUT / "items-4c.json"),
            "summary": _sha(summary_path),
            "audit": _sha(Path(args.audit)),
            "verification": _sha(Path(args.verification)),
            "records": {
                p.name: _sha(p) for p in sorted(Path(args.records).glob("item-*.json"))
            },
        },
        "environment": docs["qualification"]["manifest"]["environment"],
        "decoding": docs["qualification"]["manifest"]["decoding"],
        "eos_token_ids": docs["qualification"]["manifest"]["eos_token_ids"],
        "reading": docs["summary"]["reading"],
        "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    if not args.push:
        print(json.dumps({"would_push": args.repo, "files": len(inventory), "sha": fp}))
        return 0
    from huggingface_hub import HfApi

    api = HfApi()
    api.create_repo(args.repo, repo_type="model", exist_ok=True)
    info = api.upload_folder(
        folder_path=str(staged),
        repo_id=args.repo,
        repo_type="model",
        commit_message="Exp 4C PROVEN, SCOPED release (REGISTRATION-4C.md)",
        ignore_patterns=["__pycache__/*"],
    )
    manifest["hf_commit"] = getattr(info, "oid", None) or str(info)
    remote = api.get_paths_info(
        args.repo,
        list(files),
        repo_type="model",
        expand=True,
        revision=manifest["hf_commit"],
    )
    checks = {}
    for entry in remote:
        name = entry.path
        lfs = getattr(entry, "lfs", None)
        if lfs is not None and getattr(lfs, "sha256", None):
            checks[name] = lfs.sha256 == files[name]
        else:
            checks[name] = (
                getattr(entry, "blob_id", None) == inventory[name]["git_blob_sha1"]
            )
    manifest["remote_hash_checks"] = checks
    manifest["remote_verified"] = len(checks) == len(files) and all(checks.values())
    screen._write_atomic(OUT / "release-manifest-4c.json", manifest)
    print(
        json.dumps(
            {
                "pushed": args.repo,
                "commit": manifest["hf_commit"],
                "ok": manifest["remote_verified"],
            }
        )
    )
    return 0 if manifest["remote_verified"] else 1


if __name__ == "__main__":
    sys.exit(main())
