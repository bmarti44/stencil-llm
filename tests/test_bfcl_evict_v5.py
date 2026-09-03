"""CPU contracts closing the BFCL harness-v4 review findings."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/bench/bfcl_v3_mt"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_v4_1_dev_loader_reads_only_registered_dev_offsets(monkeypatch):
    """No read made by the dev loader may overlap a sealed case/answer row."""
    from scripts import bfcl_mt

    index = json.loads((DATA / "offsets.json").read_text())
    sealed_ranges = {
        (row["file"], row["offset"], row["offset"] + row["length"])
        for case_id in index["cohorts"]["sealed"]
        for row in index["records"][case_id].values()
    }
    original_open = Path.open
    touched: list[tuple[str, int, int]] = []

    class Tracked:
        def __init__(self, handle, relative):
            self.handle = handle
            self.relative = relative

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return self.handle.__exit__(*args)

        def seek(self, offset, whence=0):
            return self.handle.seek(offset, whence)

        def read(self, size=-1):
            start = self.handle.tell()
            value = self.handle.read(size)
            touched.append((self.relative, start, start + len(value)))
            return value

        def __iter__(self):
            raise AssertionError("indexed BFCL files must never be scanned")

    def tracked_open(path, *args, **kwargs):
        handle = original_open(path, *args, **kwargs)
        try:
            relative = str(path.relative_to(ROOT))
        except ValueError:
            return handle
        if relative.endswith(".jsonl") and "bfcl_v3_mt" in relative:
            return Tracked(handle, relative)
        return handle

    monkeypatch.setattr(Path, "open", tracked_open)
    rows = bfcl_mt.load_cases("dev")
    assert [row[1]["id"] for row in rows] == index["cohorts"]["dev"]
    assert len(rows) == 32
    assert touched
    for file_name, start, end in touched:
        assert not any(
            file_name == sealed_file and start < sealed_end and end > sealed_start
            for sealed_file, sealed_start, sealed_end in sealed_ranges
        )


def test_v4_1_index_preserves_all_frozen_bfcl_files_and_is_manifest_pinned():
    index_path = DATA / "offsets.json"
    index = json.loads(index_path.read_text())
    manifest = json.loads((ROOT / "data/bench/pins-manifest.json").read_text())
    bfcl_pin = manifest["pins"]["ShishirPatil/gorilla BFCL V3 multi-turn"]
    assert bfcl_pin["offsets_sha256"] == _sha256(index_path)
    for relative, digest in index["source_files_sha256"].items():
        assert _sha256(ROOT / relative) == digest
        assert bfcl_pin["files_sha256"][relative] == digest


def test_v4_2_preflight_arm_cut_is_rejected_and_sealed_requires_certificate(
    monkeypatch,
):
    from scripts.bfcl_mt import parse_args

    with pytest.raises(SystemExit):
        parse_args(["preflight", "--arm-cut"])
    monkeypatch.setenv("STENCIL_SEALED_RUN", "1")
    with pytest.raises(SystemExit):
        parse_args(["run", "--split", "sealed"])
    with pytest.raises(SystemExit):
        parse_args(
            [
                "run",
                "--split",
                "sealed",
                "--preflight-certificate",
                "missing.json",
                "--limit",
                "1",
            ]
        )


def test_v4_2_certificate_rejects_mismatch_and_failure(tmp_path):
    from scripts.bfcl_mt import certificate_payload, validate_preflight_certificate

    meta = {
        "trunk": "1.7b",
        "arms": ["base", "full"],
        "max_new": 512,
        "deadline": 300.0,
        "k": 8192,
        "frozen_hashes": {"harness_manifest": "abc"},
    }
    payload = certificate_payload(
        meta,
        {
            "competence": True,
            "determinism": True,
            "feasibility": True,
            "invariants": True,
            "cost": True,
        },
    )
    digest = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    path = tmp_path / "preflight.json"
    path.write_text(
        json.dumps(
            {"status": "PASSED", "certificate": payload, "certificate_sha256": digest}
        )
    )
    assert validate_preflight_certificate(path, meta) == digest
    with pytest.raises(RuntimeError, match="certificate"):
        validate_preflight_certificate(path, {**meta, "trunk": "4b"})
    path.write_text(json.dumps({"status": "INCONCLUSIVE"}))
    with pytest.raises(RuntimeError, match="passing preflight"):
        validate_preflight_certificate(path, meta)


@pytest.mark.parametrize(
    ("kwargs", "expected"),
    [
        ({"global_k": 5}, "INCONCLUSIVE"),
        ({"a1_informative": False}, "INCONCLUSIVE"),
        ({"treatment_safety": False}, "UNSUPPORTED"),
        ({"a3_eligible": False, "a1_passed": True}, "SUPPORTED_A1_ONLY"),
        ({"a3_eligible": False, "a1_passed": False}, "UNSUPPORTED"),
        ({"a3_eligible": True, "a1_passed": True, "a3_passed": True}, "SUPPORTED"),
        ({"a3_eligible": True, "a1_passed": True, "a3_passed": False}, "UNSUPPORTED"),
        ({"a3_eligible": True, "a1_passed": False, "a3_passed": True}, "UNSUPPORTED"),
    ],
)
def test_v4_3_primary_claim_status_complete_ordering(kwargs, expected):
    from stencil.bfcl import primary_claim_status

    defaults = dict(
        global_k=6,
        a1_informative=True,
        treatment_safety=True,
        a1_passed=True,
        a3_eligible=True,
        a3_passed=True,
    )
    assert primary_claim_status(**(defaults | kwargs))["status"] == expected


def test_v4_3_summary_splits_a2_a3_a4_and_does_not_gate_primary_on_a2():
    from stencil.bfcl import summarize_records
    from tests.test_bfcl_evict_v3 import _record

    records = [_record(str(index)) for index in range(6)]
    for record in records:
        record["arms"]["recency_pinned"]["turns"][0]["pass"] = True
    summary = summarize_records(records)
    assert summary["primary_claim"]["status"] == "SUPPORTED"
    assert summary["a2_claim"]["passed"] is False
    assert summary["a2_claim"]["non_rejection_wording"] == (
        "no learned-ranking advantage detected"
    )
    assert {"headroom_gate_passed", "k", "status", "eligible"} <= set(summary["a3"])
    assert "passed" in summary["a4_echo_minus_tool_swap"]


def test_v4_4_truncated_repetition_and_unmatched_markers_are_invalid():
    from scripts.bfcl_mt import _degenerate
    from stencil.bfcl import parse_tool_calls

    assert _degenerate([1, 2, 3, 4] * 20, truncated=True) is False
    assert _degenerate([1, 2, 3, 4] * 20, truncated=False) is True
    assert parse_tool_calls("<tool_call>{broken}</tool_call>")[0].valid is False
    assert parse_tool_calls('<tool_call>{"name":"x","arguments":{}}')[0].valid is False
    assert parse_tool_calls("</tool_call>")[0].valid is False


def test_v4_4_repeated_call_set_includes_ground_truth_and_echoed_calls():
    from scripts.bfcl_mt import canonical_repeated_call_set

    tools = [{"name": "lookup"}]
    history = [["lookup(q='old')"]]
    entries = [
        {
            "role": "tool",
            "text": '<tool_call>{"arguments":{"q":"echo"},"name":"lookup"}</tool_call>',
        }
    ]
    assert canonical_repeated_call_set(history, tools, entries) == {
        '{"arguments":{"q":"old"},"name":"lookup"}',
        '{"arguments":{"q":"echo"},"name":"lookup"}',
    }


def test_v4_5_manifest_covers_all_executing_modules_and_records_bind_identity():
    from scripts.bfcl_mt import harness_manifest
    from stencil.bfcl import assert_case_record_schema
    from tests.test_bfcl_evict_v3 import _record

    manifest = harness_manifest()
    required = {
        "scripts/bfcl_mt.py",
        "src/stencil/bfcl.py",
        "src/stencil/selector_v2.py",
        "src/stencil/ledger.py",
        "src/stencil/stats.py",
        "src/stencil/qwen3.py",
        "src/stencil/qwen_cache.py",
        "chat_template:render_prompt",
    }
    assert required <= set(manifest["files"])
    assert any(name.endswith("multi_turn_checker.py") for name in manifest["files"])
    record = _record("case")
    record["run_identity_sha256"] = "a" * 64
    assert_case_record_schema(
        record, expected_arms=list(record["arms"]), run_identity_sha256="a" * 64
    )
    with pytest.raises(ValueError, match="run identity"):
        assert_case_record_schema(
            record, expected_arms=list(record["arms"]), run_identity_sha256="b" * 64
        )


def test_v4_5_meta_stores_individual_data_model_and_harness_hashes():
    from scripts.bfcl_mt import artifact_meta

    args = type(
        "Args",
        (),
        {
            "split": "dev",
            "mode": "teacher",
            "trunk": "1.7b",
            "max_new": 512,
            "deadline": 300.0,
            "limit": None,
            "arm_cut": False,
        },
    )()
    frozen = artifact_meta(args)["frozen_hashes"]
    assert {"harness_files", "bfcl_files", "trunk_config", "offsets"} <= set(frozen)
    assert all(len(digest) == 64 for digest in frozen["harness_files"].values())


def test_v4_5_summary_requires_exact_ordered_cohort_and_digest():
    from stencil.bfcl import summarize_records
    from tests.test_bfcl_evict_v3 import _record

    records = [_record(str(index)) for index in range(6)]
    for record in records:
        record["run_identity_sha256"] = "c" * 64
    expected = [str(index) for index in range(6)]
    summarize_records(records, expected_case_ids=expected, run_identity_sha256="c" * 64)
    with pytest.raises(ValueError, match="cohort"):
        summarize_records(
            records[::-1], expected_case_ids=expected, run_identity_sha256="c" * 64
        )
    with pytest.raises(ValueError, match="run identity"):
        summarize_records(
            records, expected_case_ids=expected, run_identity_sha256="d" * 64
        )


def test_v4_6_invariants_report_named_numerators_and_candidate_source():
    from scripts.bfcl_mt import assert_dev_invariants
    from tests.test_bfcl_evict_v3 import _record

    records = [_record("one")]
    for arm in records[0]["arms"].values():
        eviction = arm["turns"][0]["eviction"]
        eviction.update(
            current_turn_prefilled_before_eviction=False,
            protected_prefix_survived=True,
            pinned_columns_by_role={"user": 3, "tool": 0},
            echo_token_delta=0,
            match_impossible=False,
            control_role_shortfall=False,
            role_column_deltas={"user": 0, "tool": 0},
        )
        eviction["columns_after"] = (
            eviction["columns_before"]
            - eviction["evictable_size"]
            + eviction["pinned_columns"]
        )
        arm["selector"]["turns"] = [
            {"candidate_message_indices": [0], "current_user_message_index": 1}
        ]
    report = assert_dev_invariants(records)
    assert set(report["families"]) == {
        "protected_prefix",
        "current_turn_absent",
        "cache_equation",
        "candidate_source",
        "comparator_columns",
        "comparator_echo",
    }
    assert all(set(row) == {"passed", "n"} for row in report["families"].values())
    assert report["passed_fraction"] == 1.0


def test_v4_7_tool_swap_preserves_treatment_rank_order():
    from stencil.bfcl import tool_swap_plan
    from tests.test_bfcl_evict_v4 import _candidate

    selected_tool = {
        **_candidate("tool", "selected", 10, 2, 2),
        "pinned_columns": [10, 11],
    }
    selected_user = {**_candidate("user", "user", 0, 2, 3), "pinned_columns": [0, 1]}
    replacement = _candidate("tool", "replacement", 20, 2, 2)
    result = tool_swap_plan(
        [selected_tool, selected_user, replacement],
        [selected_tool, selected_user],
        (0, 30),
        seed=20260903,
    )
    assert [row["text"] for row in result["entries"]] == ["replacement", "user"]


def test_v4_7_role_arm_uses_all_prior_user_columns_without_candidates(qwen_tok):
    from scripts.bfcl_mt import render_prompt
    from stencil.bfcl import context_layout, prior_user_spans

    messages = [
        {"role": "user", "content": "x"},
        {"role": "assistant", "content": "ok"},
        {"role": "user", "content": "now"},
    ]
    context = render_prompt(messages, [])
    layout = context_layout(qwen_tok, context, messages, current_message_index=2)
    spans = prior_user_spans(qwen_tok, context, messages, 2, layout["evict_range"])
    assert sum(end - start for start, end in spans) > 0


@pytest.fixture(scope="module")
def qwen_tok():
    from tokenizers import Tokenizer

    return Tokenizer.from_file("models/qwen3-1.7b-hf/tokenizer.json")


def test_v4_7_report_includes_echo_only_outcomes_and_registered_dose_fields():
    from stencil.bfcl import summarize_records
    from tests.test_bfcl_evict_v3 import _record

    records = [_record(str(index)) for index in range(6)]
    records[0]["arms"]["base"]["turns"][0]["eviction"]["evicted"] = False
    summary = summarize_records(records)
    assert "arms" in summary["reported"]["non_evicting_turns"]
    assert all(
        "effect_vs_base_points" in row
        for row in summary["reported"]["non_evicting_turns"]["arms"].values()
    )
    required = {
        "scorer_truncated_candidates",
        "echo_dropped_control_tokens",
        "pin_overflow_dropped_columns",
        "role_column_deltas",
        "budget_used",
        "echo_token_deltas",
        "position_overflow",
    }
    for arm in summary["categories"]["long_context"]["arms"].values():
        assert required <= set(arm)
