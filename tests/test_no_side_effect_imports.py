# ruff: noqa: E501
"""Regression guard for the 2026-08-30 closing-review CRITICAL: importing
scripts/t2_train_selector.py for a helper executed its top-level training code,
overwriting the recalibrated selector checkpoint before every shakeout.

Any script another script imports must keep training/eval work out of module
top level: no top-level loops, and no top-level torch.save / file writes.
"""
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
IMPORTED_SCRIPTS = ["scripts/t2_train_selector.py"]


def test_imported_scripts_have_no_top_level_work():
    for rel in IMPORTED_SCRIPTS:
        tree = ast.parse((ROOT / rel).read_text())
        for node in tree.body:
            assert not isinstance(node, (ast.For, ast.While)), f"{rel}: top-level loop {ast.dump(node)[:80]}"
            for call in ast.walk(node) if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) else []:
                if isinstance(call, ast.Call):
                    name = ast.unparse(call.func)
                    assert name not in ("torch.save", "open"), f"{rel}: top-level {name}() call"


def test_shakeout_does_not_import_training_script():
    src = (ROOT / "scripts" / "t2_shakeout.py").read_text()
    assert "t2_train_selector" not in src
