"""CPU checks for the Exp 1 echo-only script (selection, budget, summary arithmetic)."""

import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
TOKENIZER = ROOT / "models" / "qwen3-1.7b-hf" / "tokenizer.json"


def _module():
    spec = importlib.util.spec_from_file_location(
        "multiif_echo_only", ROOT / "scripts" / "multiif_echo_only.py"
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules["multiif_echo_only"] = mod
    spec.loader.exec_module(mod)
    return mod


def _arm(aged, invalid=False):
    return {
        "scores": {"aged": aged},
        "safety": {
            "invalid": invalid,
            "degenerate": False,
            "truncated": False,
            "timed_out": False,
        },
    }


def test_import_has_no_side_effects():
    mod = _module()
    assert mod.N_SOURCES == 128 and mod.ECHO_BUDGET == 256 and mod.MARGIN == 2.0


def test_sign_test_and_bootstrap_arithmetic():
    mod = _module()
    st = mod._sign_test([1.0, 2.0, -1.0, 0.0, 3.0])
    assert st == {
        "wins": 3,
        "losses": 1,
        "discordant": 4,
        "p_two_sided": pytest.approx(0.625),
    }
    bs = mod._bootstrap([2.0, 2.0, 2.0, 2.0])
    assert bs["mean"] == 2.0 and bs["ci95"] == [2.0, 2.0]


def test_summarize_readings_and_safety_excess(tmp_path, monkeypatch):
    mod = _module()
    monkeypatch.setattr(mod, "OUT_DIR", tmp_path)
    selected = [{"source": f"s{i}", "ci": i, "key": f"k{i}"} for i in range(4)]
    (tmp_path / "selection.json").write_text(json.dumps({"selected": selected}))
    records = {}
    for i in range(4):
        records[i] = {
            "arms": {
                "full": _arm([True, True]),
                "evicted": _arm([False, False]),
                "clf_pinned": _arm([True, False]),
                "clf_pinned_echo": _arm([True, True]),
                "role_pinned": _arm([True, True]),
            }
        }
        (tmp_path / f"conv-{i:03d}.json").write_text(
            json.dumps(
                {
                    "arms": {
                        "clf_echo_only": _arm([True, False], invalid=True),
                        "role_echo_only": _arm([True, True]),
                    }
                }
            )
        )
    summary = mod.phase_summarize(records)
    assert summary["complete"] and summary["n_complete"] == 4
    d1 = summary["contrasts"]["D1_clf_pinned_echo_minus_clf_echo_only"]
    assert d1["mean"] == 50.0 and d1["sign_test"]["wins"] == 4
    assert summary["readings"]["D1"].startswith("PINS EARN THEIR PLACE")
    assert summary["readings"]["D3"].startswith("ROLE RULE DEFAULT (interval above 0)")
    assert summary["safety_excess_over_full"]["clf_echo_only"]["invalid"] == 4
    assert (tmp_path / "manifest.json").exists()


@pytest.mark.skipif(not TOKENIZER.exists(), reason="Qwen tokenizer not present")
def test_role_echo_budget_includes_header_and_is_newest_first():
    from tokenizers import Tokenizer

    from stencil.ledger import TEXT_LEDGER_HEADER

    mod = _module()
    evict = mod._evict()
    tokenizer = Tokenizer.from_file(str(TOKENIZER))
    long_sentence = "Please always " + "keep every reply extremely thorough " * 12
    candidates = [
        {
            "text": f"Sentence number {i} about turn {t}.",
            "turn": t,
            "span": [10 * i, 10 * i + 5],
        }
        for t, i in [(1, 0), (1, 1), (2, 2), (2, 3)]
    ]
    record = {
        "selector_candidates": candidates
        + [{"text": long_sentence * 4, "turn": 3, "span": [90, 95]}]
    }
    chosen, tokens = mod.role_echo_entries(evict, tokenizer, record)
    # the newest sentence alone exceeds the budget, so nothing is chosen
    assert chosen == [] and tokens == 0
    record = {"selector_candidates": candidates}
    chosen, tokens = mod.role_echo_entries(evict, tokenizer, record)
    assert [c["text"] for c in chosen] == [c["text"] for c in candidates]
    header_tokens = len(tokenizer.encode(TEXT_LEDGER_HEADER).ids)
    assert header_tokens < tokens <= mod.ECHO_BUDGET
    # tighten the budget so only the newest sentences fit, in chronological order
    mod.ECHO_BUDGET = header_tokens + 24
    chosen, tokens = mod.role_echo_entries(evict, tokenizer, record)
    assert chosen and chosen[-1]["text"] == candidates[-1]["text"]
    assert tokens <= mod.ECHO_BUDGET
