import hashlib
import json
import os
import subprocess
from pathlib import Path

import pytest

from stencil.config import git_identity, load_config, run_id
from stencil.train import run

CONFIG_PATH = Path(__file__).parents[1] / "configs" / "test_tiny.json"


def _git(repo: Path, *args: str) -> bytes:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        check=True,
        stdout=subprocess.PIPE,
    ).stdout


@pytest.fixture
def git_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "--initial-branch=main")
    _git(repo, "config", "user.name", "Stencil Tests")
    _git(repo, "config", "user.email", "stencil@example.invalid")
    (repo / ".gitignore").write_text("results/\n", encoding="utf-8")
    (repo / "tracked.txt").write_text("committed\n", encoding="utf-8")
    _git(repo, "add", ".gitignore", "tracked.txt")
    _git(repo, "commit", "-m", "fixture")
    return repo


def test_git_identity_frames_diff_files_and_untracked_symlinks(
    git_repo: Path,
) -> None:
    (git_repo / "tracked.txt").write_text("modified\n", encoding="utf-8")
    (git_repo / "plain.bin").write_bytes(b"plain\x00bytes")
    os.symlink("plain.bin", git_repo / "link")
    os.symlink("missing-target", git_repo / "dangling")

    expected_diff = _git(
        git_repo,
        "diff",
        "--binary",
        "--full-index",
        "--no-textconv",
        "--no-ext-diff",
        "HEAD",
    )
    payloads = {
        b"dangling": b"L\x00" + b"14\x00missing-target",
        b"link": b"L\x00" + b"9\x00plain.bin",
        b"plain.bin": b"plain\x00bytes",
    }
    record = b"".join(
        path + b"\x00" + str(len(payload)).encode("ascii") + b"\x00" + payload
        for path, payload in sorted(payloads.items())
    )

    identity = git_identity(git_repo)

    assert identity.git_sha == _git(git_repo, "rev-parse", "HEAD").decode().strip()
    assert identity.git_diff_sha256 == hashlib.sha256(expected_diff).hexdigest()
    assert identity.untracked_sha256 == hashlib.sha256(record).hexdigest()
    assert identity.dirty


def test_run_enforces_artifact_and_git_state_policy(git_repo: Path) -> None:
    config = load_config(CONFIG_PATH)

    clean_run = run(config, repo=git_repo)
    assert {path.name for path in clean_run.iterdir()} == {
        "config.json",
        "env.json",
        "metrics.jsonl",
        "DONE",
    }
    metrics = (
        clean_run.joinpath("metrics.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    )
    assert len(metrics) == 200
    assert [json.loads(row)["step"] for row in metrics] == list(range(200))
    env = json.loads(clean_run.joinpath("env.json").read_text(encoding="utf-8"))
    assert env["dirty"] is False

    with pytest.raises(FileExistsError, match="already exists"):
        run(config, repo=git_repo)

    marker = clean_run / "stale"
    marker.touch()
    replaced = run(config, repo=git_repo, force=True)
    assert replaced == clean_run
    assert not marker.exists()
    assert len(replaced.joinpath("metrics.jsonl").read_text().splitlines()) == 200

    (git_repo / "tracked.txt").write_text("dirty state one\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="requires --allow-dirty"):
        run(config, repo=git_repo)

    dirty_run = run(config, repo=git_repo, allow_dirty=True)
    dirty_env = json.loads(dirty_run.joinpath("env.json").read_text(encoding="utf-8"))
    assert dirty_env["dirty"] is True

    (git_repo / "tracked.txt").write_text("dirty state two\n", encoding="utf-8")
    new_identity = git_identity(git_repo)
    conflicting = git_repo / "results" / run_id(config, new_identity)
    conflicting.mkdir()
    conflicting.joinpath("env.json").write_text(
        json.dumps(dirty_env), encoding="utf-8"
    )
    with pytest.raises(RuntimeError, match="different git state"):
        run(config, repo=git_repo, force=True, allow_dirty=True)

    assert env["CUBLAS_WORKSPACE_CONFIG"] == ":4096:8"
