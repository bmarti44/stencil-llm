"""Admission experiment contracts, without any held-out reads or model calls."""

import ast
import json
from pathlib import Path

import pytest

from scripts import focus_check44b as c
from stencil.admission import accepts, candidates, pairing


def row(text="Always be brief.", role="user", positive=True):
    return dict(
        message=text,
        role=role,
        standing_rules=[
            dict(text=text, start=0, end=len(text), key="brief", scope="global")
        ]
        if positive
        else [],
    )


def test_audited_patch_and_scenario_partition():
    rows = c.corpus()
    assert len(rows) == 3103
    assert sum(len(r["standing_rules"]) for r in rows) == 1493
    fit, dev = c.partition(rows)
    assert {r["domain"] for r in fit}.isdisjoint(r["domain"] for r in dev)
    assert len({r["domain"] for r in dev}) == 2
    assert {r["source"] for r in fit if r["source"].startswith("kimi")}.isdisjoint(
        r["source"] for r in dev if r["source"].startswith("kimi")
    )
    assert not {c.identity(r["message"]) for r in fit} & {
        c.identity(r["message"]) for r in dev
    }


def test_pairing_whole_message_and_role_overflow_guards():
    r = row("The memo says be brief. Use that from now on.")
    spans = candidates(r)
    assert len(spans) == 2
    assert pairing(r, spans[1]) == ("[user] " + r["message"], "Use that from now on.")
    assert len(accepts(r, spans, [None, 0.8], 0.8)) == 1
    assert accepts(dict(r, role="tool"), spans, [1.0, 1.0], 0.8) == []


def test_calibration_message_denominator_ties_and_abstention():
    records = []
    for i in range(50):
        r = row("First. Second.", positive=False)
        records.append(
            dict(
                input=r,
                C=dict(spans=candidates(r), probabilities=[0.9 if i < 2 else 0.1, 0.8]),
            )
        )
    pos = row()
    records.append(dict(input=pos, C=dict(spans=candidates(pos), probabilities=[0.95])))
    result = c.calibrate(records)
    assert result["threshold"] == 0.95 and result["false_admissions"] == 0
    assert result["negative_messages"] == 50 and result["maximum_allowed"] == 1
    records[-1]["C"]["probabilities"] = [1.0]
    for r in records[:-1]:
        r["C"]["probabilities"] = [1.0, 1.0]
    assert c.calibrate(records)["threshold"] > 1.0


def test_bank_loader_consumes_summary_without_fixed_old_bank_size():
    raw = "\n".join(json.dumps(r) for r in ({"summary": {"rows": 1}}, row()))
    rows, header = c.read_bank(raw.encode())
    assert len(rows) == header["rows"] == 1
    with pytest.raises(AssertionError):
        c.read_bank(raw.replace('"rows": 1', '"rows": 2').encode())


def test_setup_gold_includes_superseding_rule_and_unmatched_positive_turn():
    rows = c.setup_rows()
    assert len(rows) == 96
    assert len(rows[2]["standing_rules"]) == 1
    assert "From now on" in rows[2]["standing_rules"][0]["text"]
    r = rows[0]
    pred = list(r["standing_rules"])
    start = r["message"].index("Sort request for task ")
    pred.append(dict(start=start, end=len(r["message"]), text=r["message"][start:]))
    records = [dict(input=r, C=dict(accepted=pred, seconds=0.1))]
    result = c.setup_summary(records, "C")
    assert result["false_admission_turns"]["errors"] == 1
    assert result["request_template_false_admissions"]["errors"] == 1


def test_imports_are_inert():
    for path in (Path(c.__file__), c.ROOT / "src/stencil/admission.py"):
        tree = ast.parse(path.read_text())
        assert not any(isinstance(n, (ast.For, ast.While, ast.With)) for n in tree.body)
