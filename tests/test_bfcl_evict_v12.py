"""CPU regressions closing fable's BFCL harness-v10 findings."""

from __future__ import annotations

import json
from copy import deepcopy
from types import SimpleNamespace

import pytest


@pytest.mark.parametrize("arm", ["recency_pinned", "tool_swap_echo"])
def test_fv10_1_column_invariant_is_not_laundered_as_match_impossible(arm):
    from scripts.bfcl_mt import assert_dev_invariants
    from stencil.bfcl import assert_case_record_schema
    from tests.test_bfcl_evict_v8 import _v8_record

    record = _v8_record()
    eviction = record["arms"][arm]["turns"][0]["eviction"]
    eviction.update(
        pinned_columns_by_role={"user": 1, "tool": 1},
        match_impossible=False,
        invariant_violation="columns",
    )

    with pytest.raises(AssertionError, match="comparator_columns"):
        assert_dev_invariants([record])
    # The sealed-shaped record is retained and makes the contrast uninformative.
    assert_case_record_schema(record)


def test_fv10_1_echo_invariant_stops_dev_but_genuine_impossibility_does_not():
    from scripts.bfcl_mt import assert_dev_invariants
    from stencil.bfcl import assert_case_record_schema
    from tests.test_bfcl_evict_v8 import _v8_record

    record = _v8_record()
    eviction = record["arms"]["tool_swap_echo"]["turns"][0]["eviction"]
    eviction.update(
        echo_token_delta=29,
        echo_unreachable=True,
        invariant_violation="echo_delta",
        match_impossible=False,
    )
    with pytest.raises(AssertionError, match="comparator_echo"):
        assert_dev_invariants([record])
    assert_case_record_schema(record)

    eviction.update(
        echo_token_delta=0,
        echo_unreachable=False,
        invariant_violation=None,
        match_impossible=True,
    )
    assert_dev_invariants([record])
    assert_case_record_schema(record)


def test_fv10_1_preflight_refuses_certificate_on_recorded_invariant(
    monkeypatch, tmp_path
):
    from scripts import bfcl_mt
    from tests.test_bfcl_evict_v8 import _v8_record

    record = _v8_record()
    eviction = record["arms"]["recency_pinned"]["turns"][0]["eviction"]
    eviction.update(
        pinned_columns_by_role={"user": 1, "tool": 1},
        match_impossible=False,
        invariant_violation="columns",
    )
    monkeypatch.setattr(bfcl_mt, "run", lambda *args, **kwargs: [record])
    monkeypatch.setattr(
        bfcl_mt,
        "issue_preflight_certificate",
        lambda *args, **kwargs: pytest.fail("certificate issuance was reached"),
    )
    args = SimpleNamespace(out=str(tmp_path), trunk="1.7b")

    with pytest.raises(RuntimeError, match="registered preflight invariant failed"):
        bfcl_mt.preflight(args, None, None, None, meta={}, cases=[])
    report = json.loads((tmp_path / "preflight.json").read_text())
    assert report["failure_state"] == "INVARIANT_FAILURE"
    assert "comparator_columns" in report["error"]


def test_fv10_2_git_drift_is_evidence_but_harness_drift_refuses(
    monkeypatch, tmp_path
):
    from scripts import bfcl_mt
    from tests.test_bfcl_evict_v9 import _gates
    from tests.test_bfcl_evict_v10 import _meta_and_records

    meta, records, output = _meta_and_records(tmp_path)
    fresh = {
        key: deepcopy(value)
        for key, value in meta.items()
        if key not in {"preflight_certificate_sha256", "run_identity_sha256"}
    }
    fresh["git"] = {"commit": "f" * 40, "dirty": True, "status": "?? review.md"}
    monkeypatch.setattr(bfcl_mt, "artifact_meta", lambda _args: deepcopy(fresh))
    payload = bfcl_mt.issue_preflight_certificate(
        object(), output, meta, records, _gates(), sealed_arms=["base", "full"]
    )
    assert payload["preflight_evidence"]["git_at_freeze"] == meta.get("git")
    assert payload["preflight_evidence"]["git_at_issue"] == fresh["git"]

    fresh["frozen_hashes"]["harness_files"]["scripts/bfcl_mt.py"] = "0" * 64
    with pytest.raises(RuntimeError, match="ARTIFACT_DRIFT"):
        bfcl_mt.issue_preflight_certificate(
            object(), output, meta, records, _gates(), sealed_arms=["base", "full"]
        )


def test_fv10_4_teacher_final_score_excludes_na_turns():
    from scripts.bfcl_mt import _teacher_final_score

    turns = [
        {"pass": False, "na": True},
        {"pass": True, "na": False},
        {"pass": None, "na": False},
    ]
    assert _teacher_final_score(turns) == {"valid": True}
    assert _teacher_final_score([{"pass": False, "na": True}]) == {"valid": True}
