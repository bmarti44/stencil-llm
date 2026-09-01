"""Multi-IF replay construction and registered endpoint contracts."""

import pytest


def test_diagnostic_partition_is_stable_and_near_one_ninth():
    from stencil.e2_multiif import is_diagnostic_key

    a = [is_diagnostic_key(f"key-{i}") for i in range(900)]
    b = [is_diagnostic_key(f"key-{i}") for i in range(900)]
    assert a == b
    assert 70 <= sum(a) <= 130


def test_replayed_history_uses_base_responses_and_positive_control_restates():
    from stencil.e2_multiif import build_replay_context

    prompts = ["first task", "second constraint", "third constraint"]
    base = ["base one", "base two", "base three"]
    regular = build_replay_context(prompts, base, turn=3, positive_control=False)
    assert "base one" in regular and "base two" in regular
    assert "base three" not in regular
    assert regular.count("first task") == 1
    positive = build_replay_context(prompts, base, turn=3, positive_control=True)
    assert positive.count("first task") == 2
    assert positive.count("second constraint") == 2
    assert "Earlier user instructions restated verbatim" in positive


def test_paired_endpoint_exact_counts_and_effect():
    from stencil.e2_multiif import paired_endpoint

    pairs = [(False, True)] * 7 + [(True, False)] + [(True, True)] * 2
    got = paired_endpoint(pairs)
    assert got["n"] == 10
    assert got["repairs"] == 7 and got["regressions"] == 1
    assert got["delta_points"] == pytest.approx(60.0)
    assert got["p_one_sided"] == pytest.approx(9 / 256)


def test_conversation_any_all_endpoints_respect_clusters():
    from stencil.e2_multiif import conversation_endpoints

    clusters = {
        "a": [([False, False], [True, False])],
        "b": [([True], [True])],
        "c": [([True, True], [False, True])],
    }
    got = conversation_endpoints(clusters)
    assert got["any"]["repairs"] == 1
    assert got["any"]["regressions"] == 0
    assert got["all"]["repairs"] == 0
    assert got["all"]["regressions"] == 1


def test_mix_length_adjustment_uses_common_support_only():
    from stencil.e2_multiif import adjusted_aging_gap

    cells = []
    # Two common-support strata. Raw mix differs, but within each stratum
    # fresh exceeds aged by 0.5.
    for family in ("A", "B"):
        cells += [
            {"aged": False, "pass": True, "family": family, "length_bin": 0},
            {"aged": False, "pass": True, "family": family, "length_bin": 0},
            {"aged": True, "pass": True, "family": family, "length_bin": 0},
            {"aged": True, "pass": False, "family": family, "length_bin": 0},
        ]
    cells.append({"aged": True, "pass": False, "family": "aged-only", "length_bin": 1})
    got = adjusted_aging_gap(cells)
    assert got["fresh_minus_aged_points"] == pytest.approx(50.0)
    assert got["common_support_cells"] == 8
    assert got["excluded_cells"] == 1


def test_replay_analysis_applies_effect_floor_and_beats_ablations():
    from stencil.e2_multiif import analyze_replay_records

    records = []
    for i in range(100):
        base = False
        arms = {
            "ctrb": i < 10,
            "periodic": i < 2,
            "fixed_oldest": i < 3,
            "positive_control": i < 20,
        }
        def branch(value):
            return {
                "scores": {
                    "inst_level_strict_acc": [value],
                    "prompt_level_strict_acc": value,
                },
                "n_generated": 20,
                "truncated": False,
                "timed_out": False,
                "interventions": [],
                "biased_tokens": 0,
            }
        records.append(
            {
                "ci": i,
                "key": f"k{i}",
                "diagnostic": False,
                "turns": {
                    "2": {
                        "aged_count": 1,
                        "base": branch(base),
                        "arms": {name: branch(value) for name, value in arms.items()},
                    }
                },
            }
        )
    got = analyze_replay_records(records, diagnostic=False, bootstrap_draws=200)
    assert got["gate_pass"]
    assert not got["failure_reasons"]
    assert got["arms"]["ctrb"]["aged_constraints"]["delta_points"] == 10.0
    # Make periodic equal CTRB: conflict-triggered WHEN attribution must fail.
    for record in records:
        record["turns"]["2"]["arms"]["periodic"] = record["turns"]["2"]["arms"]["ctrb"]
    bad = analyze_replay_records(records, diagnostic=False, bootstrap_draws=50)
    assert not bad["gate_pass"]
    assert any("periodic" in reason for reason in bad["failure_reasons"])
