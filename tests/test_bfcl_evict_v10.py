"""CPU regressions for BFCL harness-v9 review findings."""

from __future__ import annotations

import json
from copy import deepcopy

import pytest


def _meta_and_records(tmp_path):
    from scripts import bfcl_mt
    from tests.test_bfcl_evict_v9 import _certificate_meta

    meta = bfcl_mt.bind_run_identity(
        _certificate_meta("dev", {"dev-1:case": "e" * 64})
    )
    record = {
        "case_id": "dev-1",
        "run_identity_sha256": meta["run_identity_sha256"],
        "arms": {"base": {}, "full": {}},
    }
    output = tmp_path / "preflight"
    (output / "records").mkdir(parents=True)
    bfcl_mt.atomic_json(output / "meta.json", meta)
    bfcl_mt.atomic_json(output / "records" / "dev-1.json", record)
    return meta, [record], output


def test_v9_1_certificate_binds_frozen_meta_verified_bytes_records_and_gates(
    monkeypatch, tmp_path
):
    from scripts import bfcl_mt
    from tests.test_bfcl_evict_v9 import _gates

    meta, records, output = _meta_and_records(tmp_path)
    fresh = {
        key: value
        for key, value in meta.items()
        if key not in {"preflight_certificate_sha256", "run_identity_sha256"}
    }
    monkeypatch.setattr(bfcl_mt, "artifact_meta", lambda _args: deepcopy(fresh))

    payload = bfcl_mt.issue_preflight_certificate(
        object(), output, meta, records, _gates(), sealed_arms=["base", "full"]
    )
    evidence = payload["preflight_evidence"]
    assert evidence["run_identity_sha256"] == meta["run_identity_sha256"]
    assert evidence["meta_sha256"] == bfcl_mt.sha256(output / "meta.json")
    assert evidence["dev_verified_bytes"] == meta["frozen_hashes"]["verified_bytes"]
    assert evidence["records_sha256"] == {
        "dev-1.json": bfcl_mt.sha256(output / "records" / "dev-1.json")
    }
    assert evidence["preflight_arms"] == ["base", "full"]
    assert payload["trunk"] == "1.7b"
    assert payload["arms"] == ["base", "full"]
    assert payload["gates"] == _gates()


@pytest.mark.parametrize("drift", ["dev_record", "harness"])
def test_v9_1_producer_rejects_post_run_artifact_drift(
    monkeypatch, tmp_path, drift
):
    from scripts import bfcl_mt
    from tests.test_bfcl_evict_v9 import _gates

    meta, records, output = _meta_and_records(tmp_path)
    fresh = {
        key: deepcopy(value)
        for key, value in meta.items()
        if key not in {"preflight_certificate_sha256", "run_identity_sha256"}
    }
    if drift == "dev_record":
        fresh["frozen_hashes"]["verified_bytes"]["records"]["dev-1:case"] = (
            "0" * 64
        )
    else:
        fresh["frozen_hashes"]["harness_files"]["scripts/bfcl_mt.py"] = "0" * 64
    monkeypatch.setattr(bfcl_mt, "artifact_meta", lambda _args: fresh)

    with pytest.raises(RuntimeError, match="ARTIFACT_DRIFT"):
        bfcl_mt.issue_preflight_certificate(
            object(), output, meta, records, _gates(), sealed_arms=["base", "full"]
        )
    report = json.loads((output / "preflight.json").read_text())
    assert report["status"] == "INCONCLUSIVE"
    assert report["failure_state"] == "ARTIFACT_DRIFT"
    assert "certificate" not in report


@pytest.mark.parametrize("altered", ["meta", "record", "failed_gate"])
def test_v9_1_consumer_rejects_altered_or_failed_preflight(
    monkeypatch, tmp_path, altered
):
    from scripts import bfcl_mt
    from tests.test_bfcl_evict_v9 import _certificate_meta, _gates

    meta, records, output = _meta_and_records(tmp_path)
    fresh = {
        key: value
        for key, value in meta.items()
        if key not in {"preflight_certificate_sha256", "run_identity_sha256"}
    }
    monkeypatch.setattr(bfcl_mt, "artifact_meta", lambda _args: deepcopy(fresh))
    payload = bfcl_mt.issue_preflight_certificate(
        object(), output, meta, records, _gates(), sealed_arms=["base", "full"]
    )
    bfcl_mt.atomic_json(
        output / "preflight.json",
        {
            "status": "PASSED",
            "certificate": payload,
            "certificate_sha256": bfcl_mt._canonical_sha256(payload),
        },
    )
    if altered == "meta":
        (output / "meta.json").write_text("{}")
    elif altered == "record":
        (output / "records" / "dev-1.json").write_text("{}")
    else:
        report = json.loads((output / "preflight.json").read_text())
        report["certificate"]["gates"]["cost"] = False
        report["certificate_sha256"] = bfcl_mt._canonical_sha256(
            report["certificate"]
        )
        bfcl_mt.atomic_json(output / "preflight.json", report)

    sealed = _certificate_meta("sealed", {"sealed-1:case": "f" * 64})
    with pytest.raises(RuntimeError, match="preflight certificate"):
        bfcl_mt.validate_preflight_certificate(output / "preflight.json", sealed)


@pytest.mark.parametrize("arm", ["base", "full"])
def test_v9_2_reference_safety_breach_prevents_supported_primary_claim(arm):
    from stencil.bfcl import summarize_records
    from tests.test_bfcl_evict_v3 import _record

    records = [_record(str(index)) for index in range(6)]
    records[0]["arms"][arm]["turns"][0]["timeout"] = True
    summary = summarize_records(records)

    assert summary["contrasts"]["a3_half_gap_recovery"]["status"] == "uninformative"
    assert summary["leg_status"] == "INCONCLUSIVE"
    assert summary["outcome"]["label"] == "INCONCLUSIVE"
    assert summary["primary_claim"]["status"] == "INCONCLUSIVE"
    assert arm in summary["primary_claim"]["reason"]
    assert not summary["registered_contrasts_pass"]


def test_v9_2_reference_method_breach_prevents_supported_primary_claim():
    from stencil.bfcl import summarize_records
    from tests.test_bfcl_evict_v3 import _record

    records = [_record(str(index)) for index in range(6)]
    records[0]["arms"]["base"]["turns"][0]["eviction"]["match_impossible"] = True
    summary = summarize_records(records)

    assert summary["primary_claim"]["status"] == "INCONCLUSIVE"
    assert summary["primary_claim"]["reason"] == (
        "A3 integrity breach: base comparator method"
    )
    assert not summary["registered_contrasts_pass"]


@pytest.mark.parametrize("a3_reason", ["no_headroom", "post_exclusion_k"])
def test_v9_2_safe_measurement_uninformative_still_supports_a1_only(a3_reason):
    from stencil.bfcl import primary_claim_status

    result = primary_claim_status(
        global_k=6,
        a1_informative=True,
        treatment_safety=True,
        a1_passed=True,
        a3_eligible=False,
        a3_passed=False,
        a3_safety_intact=True,
        a3_safety_reason=None,
        a3_uninformative_reason=a3_reason,
    )
    assert result["status"] == "SUPPORTED_A1_ONLY"
    assert a3_reason.replace("_", " ") in result["reason"]
