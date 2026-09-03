"""CPU regressions for BFCL harness-v8 review findings under Amendment 5."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest


def _gates() -> dict[str, bool]:
    return {
        name: True
        for name in ("competence", "determinism", "feasibility", "invariants", "cost")
    }


def _certificate_meta(split: str, records: dict[str, str]) -> dict:
    return {
        "split": split,
        "trunk": "1.7b",
        "arms": ["base", "full"],
        "max_new": 512,
        "deadline": 300.0,
        "k": 8192,
        "budget_fraction": 0.25,
        "chunk_tokens": 128,
        "echo_cap": 1024,
        "selector_threshold": 0.5,
        "echo_header": "header",
        "control_tie_break": "stable",
        "registration_sha256": "1" * 64,
        "classifier_sha256": {"artifact": "2" * 64},
        "frozen_hashes": {
            "harness": "3" * 64,
            "harness_manifest": "3" * 64,
            "harness_files": {"scripts/bfcl_mt.py": "4" * 64},
            "selector_artifact": "5" * 64,
            "trunk_weights": "6" * 64,
            "trunk_tokenizer": "7" * 64,
            "trunk_config": "8" * 64,
            "cohorts": "9" * 64,
            "offsets": "a" * 64,
            "pins_manifest": "b" * 64,
            "chat_template": "c" * 64,
            "vendored_checker": "d" * 64,
            "bfcl_manifest": {
                "dev_records": {"dev-1:case": "e" * 64},
                "sealed_records": {"sealed-1:case": "f" * 64},
                "source_files": {"mixed.jsonl": "0" * 64},
            },
            "verified_bytes": {
                "offsets": "a" * 64,
                "pins_manifest": "b" * 64,
                "records": records,
                "source_files": (
                    {"mixed.jsonl": "0" * 64} if split == "sealed" else {}
                ),
                "cohorts": "9" * 64,
                "function_docs": {"functions.json": "1" * 64},
                "checker": {"checker.py": "2" * 64},
                "template": "c" * 64,
            },
        },
    }


def _write_certificate(path: Path, payload: dict) -> None:
    digest = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    path.write_text(
        json.dumps(
            {"status": "PASSED", "certificate": payload, "certificate_sha256": digest}
        )
    )


def test_v8_1_dev_certificate_validates_for_split_invariant_sealed_contract(tmp_path):
    from scripts.bfcl_mt import certificate_payload, validate_preflight_certificate

    dev_meta = _certificate_meta("dev", {"dev-1:case": "e" * 64})
    sealed_meta = _certificate_meta("sealed", {"sealed-1:case": "f" * 64})
    payload = certificate_payload(dev_meta, _gates())
    path = tmp_path / "preflight.json"
    _write_certificate(path, payload)

    assert payload["preflight_evidence"]["dev_verified_bytes"]["records"] == {
        "dev-1:case": "e" * 64
    }
    assert validate_preflight_certificate(path, sealed_meta) == hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def test_v8_1_common_manifest_change_rejects_certificate(tmp_path):
    from scripts.bfcl_mt import certificate_payload, validate_preflight_certificate

    dev_meta = _certificate_meta("dev", {"dev-1:case": "e" * 64})
    payload = certificate_payload(dev_meta, _gates())
    path = tmp_path / "preflight.json"
    _write_certificate(path, payload)
    changed = _certificate_meta("sealed", {"sealed-1:case": "f" * 64})
    changed["frozen_hashes"]["harness_files"]["scripts/bfcl_mt.py"] = "0" * 64

    with pytest.raises(RuntimeError, match="certificate"):
        validate_preflight_certificate(path, changed)


def test_v8_1_real_dev_certificate_validates_before_sealed_rows(
    monkeypatch, tmp_path
):
    from scripts import bfcl_mt

    def args(split: str):
        return type(
            "Args",
            (),
            {
                "split": split,
                "mode": "teacher",
                "trunk": "1.7b",
                "max_new": 512,
                "deadline": 300.0,
                "limit": None,
                "arm_cut": False,
            },
        )()

    dev_meta = bfcl_mt.artifact_meta(args("dev"))
    monkeypatch.setattr(
        bfcl_mt,
        "assert_clean_git_for_sealed",
        lambda: {"commit": "f" * 40, "dirty": False, "status": ""},
    )
    monkeypatch.setattr(
        bfcl_mt,
        "_load_cases_verified",
        lambda *a, **k: pytest.fail("pre-authorization metadata read sealed rows"),
    )
    sealed_contract = bfcl_mt.artifact_meta(args("sealed"))
    bound_meta = bfcl_mt.bind_run_identity(dev_meta)
    output = tmp_path / "real-dev-preflight"
    records_dir = output / "records"
    records_dir.mkdir(parents=True)
    bfcl_mt.atomic_json(output / "meta.json", bound_meta)
    case_ids = sorted(
        {
            key.rsplit(":", 1)[0]
            for key in dev_meta["frozen_hashes"]["verified_bytes"]["records"]
        }
    )
    records = [
        {
            "case_id": case_id,
            "run_identity_sha256": bound_meta["run_identity_sha256"],
            "arms": {arm: {} for arm in bound_meta["arms"]},
        }
        for case_id in case_ids
    ]
    for record in records:
        bfcl_mt.atomic_json(records_dir / f"{record['case_id']}.json", record)
    monkeypatch.setattr(bfcl_mt, "artifact_meta", lambda _args: dev_meta)
    payload = bfcl_mt.issue_preflight_certificate(
        args("dev"),
        output,
        bound_meta,
        records,
        _gates(),
        sealed_arms=list(bound_meta["arms"]),
    )
    path = output / "preflight.json"
    _write_certificate(path, payload)

    assert len(payload["preflight_evidence"]["dev_verified_bytes"]["records"]) == 64
    assert len(payload["preflight_evidence"]["records_sha256"]) == 32
    assert bfcl_mt.validate_preflight_certificate(path, sealed_contract)


def test_v8_1_rejected_certificate_precedes_any_sealed_loader(monkeypatch, tmp_path):
    from scripts import bfcl_mt

    args = type(
        "Args",
        (),
        {
            "split": "sealed",
            "command": "run",
            "mode": "teacher",
            "trunk": "1.7b",
            "max_new": 1,
            "deadline": 1.0,
            "limit": None,
            "out": str(tmp_path / "out"),
            "arm_cut": False,
            "preflight_certificate": tmp_path / "bad.json",
        },
    )()
    order: list[str] = []
    monkeypatch.setattr(bfcl_mt, "parse_args", lambda: args)
    monkeypatch.setattr(bfcl_mt, "assert_clean_git_for_sealed", lambda: {})
    monkeypatch.setattr(bfcl_mt.determinism, "assert_gpu_free_or_owned", lambda: None)
    monkeypatch.setattr(
        bfcl_mt, "artifact_meta", lambda *a, **k: _certificate_meta("sealed", {})
    )

    def reject(*_args, **_kwargs):
        order.append("certificate")
        raise RuntimeError("rejected certificate")

    def sealed_loader(*_args, **_kwargs):
        order.append("sealed_loader")
        pytest.fail("sealed loader ran before certificate refusal")

    monkeypatch.setattr(bfcl_mt, "validate_preflight_certificate", reject)
    monkeypatch.setattr(bfcl_mt, "_load_cases_verified", sealed_loader)
    with pytest.raises(RuntimeError, match="rejected certificate"):
        bfcl_mt.main()
    assert order == ["certificate"]


def test_v8_2_amendment_5_shortfall_total_and_other_per_role_are_fail_closed():
    from scripts.bfcl_mt import assert_dev_invariants
    from stencil.bfcl import assert_case_record_schema
    from tests.test_bfcl_evict_v8 import _v8_record

    shortfall = _v8_record()
    control = shortfall["arms"]["clf_control"]["turns"][0]["eviction"]
    control.update(
        control_role_shortfall=True,
        pinned_columns_by_role={"user": 0, "tool": 3},
        role_column_deltas={"user": -2, "tool": 2},
    )
    assert_dev_invariants([shortfall])
    assert_case_record_schema(shortfall)

    control["pinned_columns_by_role"] = {"user": 0, "tool": 2}
    with pytest.raises(AssertionError, match="comparator_columns"):
        assert_dev_invariants([shortfall])
    with pytest.raises(ValueError, match="comparator column"):
        assert_case_record_schema(shortfall)

    other = _v8_record()
    recency = other["arms"]["recency_pinned"]["turns"][0]["eviction"]
    recency.update(
        control_role_shortfall=True,
        pinned_columns_by_role={"user": 0, "tool": 3},
        role_column_deltas={"user": -2, "tool": 2},
    )
    with pytest.raises(AssertionError, match="comparator_columns"):
        assert_dev_invariants([other])
    with pytest.raises(ValueError, match="comparator column"):
        assert_case_record_schema(other)


@pytest.mark.parametrize(
    ("selected_role", "fallback_role"), [("user", "tool"), ("tool", "user")]
)
def test_v8_2_shortfall_builder_records_exact_total_role_deltas(
    selected_role, fallback_role
):
    from stencil.bfcl import build_matched_control

    selected = {
        "role": selected_role,
        "text": "selected",
        "span": [0, 3],
        "turn": 2,
        "message_index": 2,
        "score": 0.9,
        "pinned_columns": [0, 1, 2],
    }
    fallback = {
        "role": fallback_role,
        "text": "fallback",
        "span": [3, 7],
        "turn": 1,
        "message_index": 1,
        "score": 0.1,
    }
    result = build_matched_control([selected, fallback], [selected], (0, 7))
    assert result["match_impossible"] is False
    assert result["control_role_shortfall"] is True
    assert sum(result["role_counts"].values()) == 3
    assert result["role_column_deltas"][selected_role] == -3
    assert result["role_column_deltas"][fallback_role] == 3


def test_v8_3_competence_excludes_initial_na_but_counts_within_turn_failure():
    from scripts.bfcl_mt import preflight_competence

    def record(case_id: str, *, phase: str | None) -> dict:
        full_turn = {
            "pass": phase is None,
            "na": phase == "initial_prompt",
            "overflow_phase": phase,
        }
        base_turn = {"pass": True, "na": False, "overflow_phase": None}
        return {
            "case_id": case_id,
            "category": "long_context",
            "arms": {
                "base": {"final_pass": True, "turns": [base_turn]},
                "full": {"final_pass": phase is None, "turns": [full_turn]},
            },
        }

    report = preflight_competence(
        [
            record("eligible", phase=None),
            record("initial-na", phase="initial_prompt"),
            record("within-failure", phase="within_generation"),
        ],
        trunk="1.7b",
    )
    assert report["full_overall"] == {
        "passed": 1,
        "n": 2,
        "excluded_initial_prompt_na": 1,
        "floor": "at least 5 eligible cases",
    }
    assert report["full_long_cases"]["n"] == 2
    assert report["full_long_cases"]["excluded_initial_prompt_na"] == 1
    assert report["full_long_turns"]["n"] == 2
    assert report["full_long_turns"]["passed"] == 1
