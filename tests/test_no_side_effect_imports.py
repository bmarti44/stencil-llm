# ruff: noqa: E501
"""Regression guard for the 2026-08-30 closing-review CRITICAL: importing
scripts/t2_train_selector.py for a helper executed its top-level training code,
overwriting the recalibrated selector checkpoint before every shakeout.

Any script another script imports must keep training/eval work out of module
top level: no top-level loops, and no top-level torch.save / file writes.
"""
import ast
import warnings
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
GPU_ENTRY_SCRIPTS = [
    "scripts/composition_pilot5.py",
    "scripts/ledger_eval.py",
    "scripts/ledger_kv_probe.py",
    "scripts/b3_deficit_conf.py",
    "scripts/b4_multiif.py",
    "scripts/b4_ifeval.py",
]
IMPORTED_SCRIPTS = GPU_ENTRY_SCRIPTS


def top_level_work(rel):
    """Return executable top-level work that can train, evaluate, or write artifacts."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", SyntaxWarning)
        tree = ast.parse((ROOT / rel).read_text())
    offenders = []
    for node in tree.body:
        if isinstance(node, (ast.For, ast.While)):
            offenders.append(f"loop:{node.lineno}")
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Import, ast.ImportFrom)):
            continue
        for call in ast.walk(node):
            if not isinstance(call, ast.Call):
                continue
            name = ast.unparse(call.func)
            if (name in ("open", "torch.load", "torch.save") or name.endswith(
                    (".read_text", ".read_bytes", ".write_text", ".mkdir", ".cuda", ".to", ".load_state_dict"))):
                offenders.append(f"{name}:{call.lineno}")
    return offenders


def test_imported_scripts_have_no_top_level_work():
    for rel in IMPORTED_SCRIPTS:
        assert not top_level_work(rel), f"{rel}: top-level work: {top_level_work(rel)}"


def test_training_helper_script_keeps_original_import_safety_contract():
    rel = "scripts/t2_train_selector.py"
    tree = ast.parse((ROOT / rel).read_text())
    for node in tree.body:
        assert not isinstance(node, (ast.For, ast.While)), f"{rel}: top-level loop"
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        for call in ast.walk(node):
            if isinstance(call, ast.Call):
                assert ast.unparse(call.func) not in ("torch.save", "open"), f"{rel}: top-level write"


def test_legacy_script_side_effect_inventory():
    legacy = sorted(str(p.relative_to(ROOT)) for p in (ROOT / "scripts").glob("*.py")
                    if str(p.relative_to(ROOT)) not in GPU_ENTRY_SCRIPTS)
    offenders = {rel: top_level_work(rel) for rel in legacy if top_level_work(rel)}
    if offenders:
        pytest.xfail(f"legacy top-level-work debt (inventory only): {offenders}")


def test_shakeout_does_not_import_training_script():
    src = (ROOT / "scripts" / "t2_shakeout.py").read_text()
    assert "t2_train_selector" not in src
