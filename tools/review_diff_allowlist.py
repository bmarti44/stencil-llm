#!/usr/bin/env python3
"""Validate review-wrapper git diffs against a single allowed file.

The wrapper intentionally lets the reviewer update one canonical markdown
file. Anything else appearing after the run is treated as sandbox bypass or
tool misuse and rejected.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path


def _run_git(repo: Path, args: list[str]) -> list[str]:
    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    )
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def _repo_root(repo: str | None) -> Path:
    if repo:
        return Path(repo).resolve()
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    )
    return Path(result.stdout.strip()).resolve()


def _changed_paths(repo: Path) -> set[str]:
    # Required contract: the post-run check is based on
    # `git diff --name-only HEAD`. Include untracked files as well so a
    # bypass cannot create a side file that plain git diff would omit.
    tracked = _run_git(repo, ["diff", "--name-only", "HEAD", "--"])
    untracked = _run_git(repo, ["ls-files", "--others", "--exclude-standard"])
    return set(tracked) | set(untracked)


def _sha256_path(path: Path) -> str | None:
    if not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _snapshot(repo: Path) -> dict:
    changed = sorted(_changed_paths(repo))
    return {
        "changed_paths": changed,
        "blob_sha256": {
            path: _sha256_path(repo / path)
            for path in changed
        },
    }


def _read_baseline(path: Path | None) -> dict:
    if path is None:
        return {"changed_paths": [], "blob_sha256": {}}
    if not path.exists():
        raise ValueError(f"baseline file does not exist: {path}")
    text = path.read_text(encoding="utf-8")
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        # Backward-compatible reader for the prior newline path-set format.
        changed = [line.strip() for line in text.splitlines() if line.strip()]
        return {"changed_paths": changed, "blob_sha256": {}}
    if not isinstance(data, dict):
        raise ValueError(f"baseline JSON must be an object: {path}")
    changed_paths = data.get("changed_paths", [])
    blob_sha256 = data.get("blob_sha256", {})
    if not isinstance(changed_paths, list) or not all(isinstance(p, str) for p in changed_paths):
        raise ValueError("baseline changed_paths must be a list of strings")
    if not isinstance(blob_sha256, dict) or not all(
        isinstance(k, str) and (isinstance(v, str) or v is None)
        for k, v in blob_sha256.items()
    ):
        raise ValueError("baseline blob_sha256 must map paths to sha256 strings/null")
    return {
        "changed_paths": changed_paths,
        "blob_sha256": blob_sha256,
    }


def _allowed_relpath(repo: Path, allowed: str) -> str:
    allowed_path = Path(allowed)
    if not allowed_path.is_absolute():
        allowed_path = repo / allowed_path
    resolved = allowed_path.resolve()
    try:
        rel = resolved.relative_to(repo)
    except ValueError as exc:
        raise ValueError(f"allowed path must resolve inside repo: {allowed}") from exc
    return rel.as_posix()


def validate(repo: Path, allowed: str, baseline: Path | None = None) -> list[str]:
    current = _changed_paths(repo)
    before_snapshot = _read_baseline(baseline)
    before = set(before_snapshot["changed_paths"])
    before_sha = before_snapshot["blob_sha256"]
    allowed_rel = _allowed_relpath(repo, allowed)
    findings = [
        f"new dirty path not allowed: {path}"
        for path in sorted(current - before)
        if path != allowed_rel
    ]
    for path in sorted(current & before):
        if path == allowed_rel or path not in before_sha:
            continue
        current_sha = _sha256_path(repo / path)
        if current_sha != before_sha[path]:
            findings.append(f"pre-dirty content modified: {path}")
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", help="Repository root (default: git rev-parse)")
    parser.add_argument("--snapshot", action="store_true", help="Print current changed path set")
    parser.add_argument("--baseline", type=Path, help="Path set captured before the review run")
    parser.add_argument("--allowed", help="Only allowed changed path after the baseline")
    args = parser.parse_args(argv)

    repo = _repo_root(args.repo)
    if args.snapshot:
        print(json.dumps(_snapshot(repo), sort_keys=True))
        return 0

    if not args.allowed:
        parser.error("--allowed is required unless --snapshot is set")

    try:
        unexpected = validate(repo, args.allowed, args.baseline)
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        print(f"ERROR: review diff allowlist validation failed: {exc}", file=sys.stderr)
        return 2

    if unexpected:
        print("ERROR: review wrapper changed paths outside the canonical review file:", file=sys.stderr)
        for finding in unexpected:
            print(f"  {finding}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
