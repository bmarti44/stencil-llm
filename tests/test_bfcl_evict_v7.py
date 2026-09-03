"""CPU regressions closing BFCL-V6-1 through BFCL-V6-6."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/bench/bfcl_v3_mt"


def _candidate(role, text, start, width, turn, *, message_index=None):
    return {
        "role": role,
        "text": text,
        "span": [start, start + width],
        "turn": turn,
        "message_index": turn if message_index is None else message_index,
        "score": 0.1,
    }


def _selected(role, text, start, width, turn):
    return {
        **_candidate(role, text, start, width, turn),
        "score": 0.9,
        "pinned_columns": list(range(start, start + width)),
    }


def test_v6_1_control_visits_every_target_before_supplementing():
    from stencil.bfcl import build_matched_control

    user = _selected("user", "selected-user", 0, 2, 5)
    tool = _selected("tool", "selected-tool", 2, 2, 4)
    rows = [
        user,
        tool,
        _candidate("user", "wide-user", 10, 4, 5),
        _candidate("tool", "tool-match", 20, 2, 4),
    ]
    result = build_matched_control(rows, [user, tool], (0, 30), seed=20260903)
    assert result["match_impossible"] is False
    assert [row["target_role"] for row in result["matches"][:2]] == ["user", "tool"]
    assert result["role_counts"] == {"user": 2, "tool": 2}


def test_v6_1_tool_swap_replaces_every_selected_tool_chunk():
    from stencil.bfcl import tool_swap_plan

    first = _selected("tool", "first", 0, 2, 5)
    second = _selected("tool", "second", 2, 2, 4)
    rows = [
        first,
        second,
        _candidate("tool", "wide", 10, 4, 5),
        _candidate("tool", "second-match", 20, 2, 4),
    ]
    result = tool_swap_plan(rows, [first, second], (0, 30), seed=20260903)
    assert result["match_impossible"] is False
    assert [row["target_role"] for row in result["matches"][:2]] == ["tool", "tool"]
    assert len(result["entries"]) == 2
    assert all(result["entries"])
    assert sum(len(row["pinned_columns"]) for row in result["entries"]) == 4


def test_v6_1_failed_clamp_is_never_reported_usable(monkeypatch):
    import stencil.bfcl as bfcl

    selected = _selected("user", "selected", 0, 3, 2)
    available = _candidate("user", "available", 10, 3, 2)
    original = bfcl.clamp_candidate_rows

    def incomplete(*args, **kwargs):
        result = original(*args, **kwargs)
        result["entries"] = []
        result["pins"] = []
        result["role_counts"] = {"user": 0, "tool": 0}
        result["match_impossible"] = True
        return result

    monkeypatch.setattr(bfcl, "clamp_candidate_rows", incomplete)
    result = bfcl.build_matched_control(
        [selected, available], [selected], (0, 20), seed=20260903
    )
    assert result["match_impossible"] is True


def test_v6_2_indexed_row_hash_rejects_same_id_byte_mutation(tmp_path):
    from scripts.bfcl_mt import _read_indexed_row

    original = b'{"id":"case-1","value":1}\n'
    changed = b'{"id":"case-1","value":2}\n'
    path = tmp_path / "cases.jsonl"
    path.write_bytes(changed)
    entry = {
        "file": path.name,
        "offset": 0,
        "length": len(changed),
        "category": "base",
        "sha256": hashlib.sha256(original).hexdigest(),
    }
    with pytest.raises(RuntimeError, match="record hash mismatch"):
        _read_indexed_row(tmp_path, entry, "case-1")


def test_v6_2_function_document_hash_is_verified_from_loaded_bytes(tmp_path):
    from scripts.bfcl_mt import _load_verified_json

    path = tmp_path / "doc.json"
    original = b'[{"name":"lookup"}]\n'
    path.write_bytes(b'[{"name":"changed"}]\n')
    expected = hashlib.sha256(original).hexdigest()
    with pytest.raises(RuntimeError, match="hash mismatch"):
        _load_verified_json(path, expected)


def test_v6_2_certificate_lists_actual_verified_case_answer_and_runtime_bytes():
    from scripts.bfcl_mt import artifact_meta

    args = type(
        "Args",
        (),
        {
            "split": "dev",
            "mode": "teacher",
            "trunk": "1.7b",
            "max_new": 1,
            "deadline": 1.0,
            "limit": 1,
            "arm_cut": False,
        },
    )()
    verified = artifact_meta(args)["frozen_hashes"]["verified_bytes"]
    assert len(verified["records"]) == 2
    assert all(len(value) == 64 for value in verified["records"].values())
    assert verified["offsets"] == hashlib.sha256(
        (DATA / "offsets.json").read_bytes()
    ).hexdigest()
    assert len(verified["function_docs"]) == 8
    assert verified["checker"]
    assert len(verified["template"]) == 64


def test_v6_3_echo_overflow_rejected_by_schema_and_summary():
    from stencil.bfcl import assert_case_record_schema, summarize_records
    from tests.test_bfcl_evict_v3 import _record

    records = [_record(str(index)) for index in range(6)]
    bad = records[0]["arms"]["clf_control"]["turns"][0]["eviction"]
    bad.update(echo_token_delta=17, match_impossible=False)
    with pytest.raises(ValueError, match="echo token delta"):
        assert_case_record_schema(records[0])
    with pytest.raises(ValueError, match="echo token delta"):
        summarize_records(records)


def test_v6_4_repeated_call_uses_execution_normalization():
    from scripts.bfcl_mt import canonical_repeated_call_set, repeated_call_event
    from stencil.bfcl import canonical_call

    prior = canonical_repeated_call_set(
        [["lookup(q='x')"]],
        [{"name": "lookup", "parameters": {"properties": {"q": {}}}}],
        [],
    )
    assert canonical_call({"name": "API.lookup", "arguments": {"q": "x"}}) in prior
    current = {
        canonical_call({"name": "lookup", "arguments": {"q": "x"}})
    }
    generated = canonical_call({"name": "API.lookup", "arguments": {"q": "x"}})
    assert generated in prior
    assert repeated_call_event(
        {"name": "API.lookup", "arguments": {"q": "x"}}, prior, set()
    )
    assert not repeated_call_event(
        {"name": "API.lookup", "arguments": {"q": "x"}}, prior, current
    )


def test_v6_5_manifest_covers_dry_runtime_import_closure():
    from scripts import bfcl_mt

    manifest = bfcl_mt.harness_manifest()["files"]
    repo_modules = {}
    for name, module in tuple(sys.modules.items()):
        raw = getattr(module, "__file__", None)
        if not raw:
            continue
        path = Path(raw).resolve()
        if path.suffix == ".py" and path.is_relative_to(ROOT) and (
            name == "scripts.bfcl_mt"
            or name.startswith("stencil")
            or name.startswith("bfcl_eval")
        ):
            repo_modules[name] = str(path.relative_to(ROOT))
    assert "src/stencil/bench.py" not in manifest
    assert set(repo_modules.values()) <= set(manifest)
    assert "src/stencil/__init__.py" in manifest
    assert "vendor/bfcl_eval/__init__.py" in manifest


@pytest.mark.parametrize(
    ("phase", "expected_final_n"),
    [("initial_prompt", 5), ("within_generation", 6), ("tool_step", 6)],
)
def test_v6_6_full_overflow_phase_controls_final_reporting(phase, expected_final_n):
    from stencil.bfcl import summarize_records
    from tests.test_bfcl_evict_v3 import _record

    records = [_record(str(index)) for index in range(6)]
    full_turn = records[0]["arms"]["full"]["turns"][0]
    full_turn.update(
        {
            "pass": False,
            "truncated": True,
            "position_overflow": True,
            "overflow_phase": phase,
        }
    )
    records[0]["arms"]["full"].update(final_pass=False, position_overflow=True)
    summary = summarize_records(records)
    full = summary["categories"]["long_context"]["arms"]["full"]
    assert full["final_pass"]["n"] == expected_final_n
    assert full["position_overflow_phases"][phase] == 1


def test_v6_6_pressure_fact_keeps_pre_generation_overflow_primary():
    from stencil.bfcl import summarize_records
    from tests.test_bfcl_evict_v3 import _record

    records = [_record(str(index)) for index in range(6)]
    for record in records:
        record["turn_facts"] = [
            {"turn": 1, "pressure_triggered": True, "pin_overflow_total": False}
        ]
    base_turn = records[0]["arms"]["base"]["turns"][0]
    base_turn["eviction"]["evicted"] = False
    base_turn.update(
        {
            "pass": False,
            "truncated": True,
            "position_overflow": True,
            "overflow_phase": "initial_prompt",
        }
    )
    summary = summarize_records(records)
    assert summary["primary"]["turns"] == 6
    assert summary["safety"]["counts"]["base"]["truncated"] == 1


def test_v6_2_offset_index_has_hash_for_every_authorized_record():
    index = json.loads((DATA / "offsets.json").read_text())
    assert index["schema"] >= 2
    assert all(
        len(entry["sha256"]) == 64
        for record in index["records"].values()
        for entry in record.values()
    )
