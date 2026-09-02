"""Hard invariant: the sealed IFEval set (data/bench/ifeval_input_data.jsonl,
single-use) may be referenced ONLY by the registered sealed runner and the
vendor/parity tests. A salience builder trained on it on 2026-09-01 (caught
by the orchestrator, refit ordered); this test makes the invariant
mechanical."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ALLOWED = {
    "scripts/b4_ifeval.py",           # the registered sealed runner
    "scripts/b0_score_parity.py",     # scorer parity (no model)
    "tests/test_b3_gen.py",
    "tests/test_ifeval_vendor.py",
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
