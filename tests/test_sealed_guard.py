"""Hard invariant: the sealed IFEval set (data/bench/ifeval_input_data.jsonl,
single-use) may be referenced ONLY by the registered sealed runner and the
vendor/parity tests. A salience builder trained on it on 2026-09-01 (caught
by the orchestrator, refit ordered); this test makes the invariant
mechanical."""
import hashlib
import json
import stat
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ALLOWED = {
    "scripts/b4_ifeval.py",           # the registered sealed runner
    "scripts/b0_score_parity.py",     # scorer parity (no model)
    "tests/test_b3_gen.py",
    "tests/test_ifeval_vendor.py",
    "tests/test_pretool_guard.py",    # guard decision-table fixture only
    "tests/test_sealed_guard.py",
}


def test_sealed_ifeval_referenced_only_by_allowlist():
    hits = []
    for sub in ("src", "scripts", "tests", "deploy"):
        for p in (ROOT / sub).rglob("*.py"):
            if "ifeval_input_data" in p.read_text(errors="ignore"):
                rel = str(p.relative_to(ROOT))
                if rel not in ALLOWED:
                    hits.append(rel)
    assert not hits, f"sealed IFEval referenced outside the allowlist: {hits}"


def _assert_sealed_hash_matches_manifest():
    sealed = ROOT / "data" / "bench" / "ifeval_input_data.jsonl"
    manifest = json.loads((ROOT / "data" / "bench" / "pins-manifest.json").read_text())
    actual = hashlib.sha256(sealed.read_bytes()).hexdigest()
    assert actual == manifest["sealed_sha256"], "sealed hash mismatch"


def test_sealed_ifeval_hash_matches_manifest():
    _assert_sealed_hash_matches_manifest()


def test_sealed_ifeval_mode_is_read_only_after_hash_validation():
    _assert_sealed_hash_matches_manifest()
    sealed = ROOT / "data" / "bench" / "ifeval_input_data.jsonl"
    assert stat.S_IMODE(sealed.stat().st_mode) == 0o444, (
        "sealed mode mismatch: run tools/setup_sealed.sh after checkout"
    )


def test_setup_sealed_verifies_hash_before_chmod():
    setup = ROOT / "tools" / "setup_sealed.sh"
    source = setup.read_text()
    assert "pins-manifest.json" in source and "sealed_sha256" in source
    assert source.index("sha256sum") < source.index("chmod 0444")
