"""Check43b selection boundary and teacher-forcing alignment regressions."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import focus_check43b as check  # noqa: E402


def setup_rows(product=6, shuffled=1, malformed=1, plus=6):
    rows = []
    for i in range(8):
        for arm in check.ARMS[:4]:
            rows.append(
                dict(
                    task_id=str(i),
                    phase="setup",
                    dose=3,
                    arm=arm,
                    score=dict(
                        SUM=arm == "plus" and i < plus,
                        PRODUCT=(arm == "minus" and i < product)
                        or (arm == "shuffle-minus" and i < shuffled),
                        malformed=arm == "minus" and i >= 8 - malformed,
                    ),
                )
            )
    return rows


def test_frozen_selection_boundaries():
    assert check.cell_summary(setup_rows(), 3)["safe"]
    assert not check.cell_summary(setup_rows(product=5), 3)["concept_selected"]
    assert not check.cell_summary(setup_rows(shuffled=2), 3)["concept_selected"]
    assert not check.cell_summary(setup_rows(malformed=2), 3)["concept_selected"]
    result = check.cell_summary(setup_rows(plus=5), 3)
    assert result["concept_selected"] and not result["safe"]


def test_identity_is_not_first_pair_divergence():
    class Tokenizer:
        def decode(self, tokens):
            return "".join(tokens)

    a = ["def f(x):", "\n    ", "a", " = ", "0", "\n"]
    b = ["def f(x):", "\n    ", "acc", " = ", "1", "\n"]
    assert check.profile_positions(a, b, Tokenizer()) == 4


def test_safe_requires_same_prompt_address_pair():
    rows = setup_rows(product=6, plus=6)
    for r in rows:
        if r["arm"] == "plus":
            r["score"]["SUM"] = int(r["task_id"]) >= 2
    result = check.cell_summary(rows, 3)
    assert result["concept_selected"] and result["paired"] == 4 and not result["safe"]
