import json

from scripts.make_report import _load_evaluations, render_summary


def _family(name: str, accuracy: float, overhead: int) -> dict:
    bins = []
    for label, denominator in (("[0,64]", 250), ("(512,1024]", 210)):
        bins.append(
            {
                "label": label,
                "numerator": round(accuracy * denominator),
                "denominator": denominator,
                "accuracy": accuracy,
            }
        )
    return {
        "family": name,
        "sequence_weighted_exact_match": {
            "numerator": accuracy * 10_000,
            "denominator": 10_000,
            "accuracy": accuracy,
        },
        "decision_axis_bins": bins,
        "accuracy_by_global_update_count": [
            {"updates": 4, "numerator": 90, "denominator": 100, "accuracy": 0.9}
        ],
        "first_crossing_survival": 512,
        "stale_slot_preference": {
            "n_wrong_answers": 10,
            "n_stale_matches": 3,
            "observed": 0.3,
            "null": 0.2,
            "excess": 0.1,
        },
        "tail_over_512": {"numerator": 105, "denominator": 210, "accuracy": 0.5},
        "injected_token_overhead": {
            "per_sequence": overhead,
            "total": overhead * 10_000,
        },
    }


def test_task_d_report_renders_curves_adoption_cost_and_inputs_without_verdict() -> (
    None
):
    evaluation = {
        "cell": "task_d",
        "variant": "m1",
        "contender": "m1",
        "seed": 0,
        "split": "validation",
        "n_sequences": 10_000,
        "n_answers": 160_000,
        "families": {
            name: _family(name, 0.96 if name == "id-control" else 0.55, 0)
            for name in ("id-control", "drought", "burst")
        },
        "cost": {"train_wall_seconds": 12.5, "eval_wall_seconds": 3.0},
    }

    report = render_summary([evaluation])

    assert "## Task D" in report
    assert "### Adoption reliability" in report
    assert "PASS" in report
    assert "### Cost axis" in report
    assert "injected tokens / sequence" in report
    assert "### id-control validation curves" in report
    assert "distance bin" in report
    assert "global updates" in report
    assert "### Decision-table inputs" in report
    assert "tail >512" in report
    assert "verdict:" not in report.lower()


def test_task_d_report_loader_consumes_merged_eval_json(tmp_path) -> None:
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    (run_dir / "DONE").touch()
    split = {
        "cell": "task_d",
        "variant": "m1",
        "contender": "m1",
        "seed": 0,
        "split": "validation",
        "n_sequences": 10_000,
        "n_answers": 160_000,
        "families": {
            name: _family(name, 0.96, 0) for name in ("id-control", "drought", "burst")
        },
    }
    document = {
        key: split[key]
        for key in (
            "cell",
            "variant",
            "contender",
            "seed",
            "n_sequences",
            "n_answers",
        )
    }
    document["splits"] = {"validation": split}
    (run_dir / "eval.json").write_text(json.dumps(document), encoding="utf-8")

    loaded = _load_evaluations(tmp_path)

    assert loaded == [split]
    assert "## Task D" in render_summary(loaded)
