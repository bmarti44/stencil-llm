"""CPU fixtures for the prospective relation trainer; no evaluation inputs."""

import copy
import json

import numpy as np
import pytest

from scripts import train_relations as tr


def row(message="Use square bullets instead.", label="supersedes", **extra):
    result = {
        "old_rule": "Use round bullets",
        "message": message,
        "source": "kimi:fixture",
        "scope": "global",
        "status": "live",
        "role": "user",
        "label": label,
        "target_span": {"start": 0, "end": len(message), "text": message},
        "hard": False,
    }
    result.update(extra)
    return result


def write_rows(path, rows):
    path.write_text("".join(json.dumps(r) + "\n" for r in rows))
    return path


def test_patch_exact_match_relabel_drop_and_merge(tmp_path):
    a, b = row(), row("Withdraw the bullet rule.", "cancels")
    other_source = row(source="opus:fixture")
    patch = {k: a[k] for k in ("source", "message", "old_rule")}
    patch.update(old_label="supersedes", new_label="none", drop=False, why="audit")
    drop = {k: b[k] for k in ("source", "message", "old_rule")}
    drop.update(old_label="cancels", new_label="cancels", drop=True, why="audit")
    fixed, audit = tr.apply_patches([a, b, other_source], [patch, drop])
    assert [r["label"] for r in fixed] == ["none", "supersedes"]
    assert a["label"] == "supersedes"  # no mutation
    assert audit["dropped"] == 1 and audit["relabeled"] == 1
    base = write_rows(tmp_path / "base.jsonl", [a, b])
    patches = write_rows(tmp_path / "patch.jsonl", [patch, drop])
    enrich = write_rows(tmp_path / "enrich.jsonl", [row("Continue writing.", "none")])
    rows, receipt = tr.load_training([base], [patches], [enrich])
    assert len(rows) == 2 and {r["label"] for r in rows} == {"none"}
    assert len(receipt["input_sha256"]) == 3


def test_patch_conflicts_stale_and_unmatched_refused():
    a = row()
    p = {k: a[k] for k in ("source", "message", "old_rule")}
    p.update(old_label="supersedes", new_label="none", drop=False)
    for patches in (
        [dict(p, old_label="cancels")],
        [dict(p, source="unknown")],
        [p, dict(p, new_label="cancels")],
    ):
        with pytest.raises(ValueError):
            tr.apply_patches([a], patches)


def test_semantic_dedup_ignores_case_source_and_drops_all_label_conflicts():
    a = tr.normalize_row(row())
    b = tr.normalize_row(
        row(
            message="USE SQUARE BULLETS INSTEAD.",
            old_rule="USE ROUND BULLETS",
            source="opus:fixture",
        )
    )
    assert len(tr.deduplicate([a, b])[0]) == 1
    b["label"] = "none"
    kept, decisions = tr.deduplicate([a, b])
    assert kept == []
    assert len(decisions) == 2
    assert all("conflicting" in d["reason"] for d in decisions)


@pytest.mark.parametrize("marker", ["IFEval", "Multi-IF", "BFCL", "tau-bench", "S2/B3"])
def test_benchmark_markers_refused_even_in_context_or_dropped_rows(tmp_path, marker):
    bad = row(prev_user=f"Instructions from {marker}")
    path = write_rows(tmp_path / "bad.jsonl", [bad])
    with pytest.raises(ValueError, match="benchmark"):
        tr.load_training([path], [], [])


def test_reserved_author_and_heldout_paths_refused_for_fit(tmp_path):
    path = write_rows(tmp_path / "rows.jsonl", [row(author="fable")])
    with pytest.raises(ValueError, match="author"):
        tr.load_training([path], [], [])
    with pytest.raises(ValueError, match="evaluation"):
        tr.read_jsonl(tmp_path / "heldout" / "missing.jsonl")


def test_rendering_pair_and_optional_context_and_span_integrity():
    r = tr.normalize_row(row(prev_user="We are formatting a list."))
    a, b = tr.render_pair(r)
    assert a == "[target] live global Use round bullets"
    assert b == (
        "[message] user: Use square bullets instead. "
        "[span] Use square bullets instead. "
        "[prev_user] We are formatting a list."
    )
    nested = copy.deepcopy(r)
    nested["old_rule"].update(task_id="list", key="bullets", version=2)
    assert "list" in tr.render_pair(nested)[0]
    bad = row(target_span={"start": 0, "end": 3, "text": "invented"})
    with pytest.raises(ValueError, match="span"):
        tr.normalize_row(bad)
    # Legacy authored offsets are inaccurate; unique verbatim quotes can be located.
    fixed = tr.normalize_row(
        row(target_span={"start": 0, "end": 3, "text": "Use square bullets instead."})
    )
    assert fixed["target_span"]["end"] == len(fixed["message"])
    assert fixed["span_offsets_repaired"]


class TinyTokenizer:
    def __call__(self, a, b, **kwargs):
        assert kwargs["truncation"] is False
        return {
            "input_ids": list(range(len((a + b).split()) + 3)),
            "attention_mask": [1] * (len((a + b).split()) + 3),
        }


def test_overflow_abstains_without_silent_truncation():
    rows = [tr.normalize_row(row()), tr.normalize_row(row("long " * 100))]
    encoded, overflow = tr.encode_rows(rows, TinyTokenizer(), max_length=32)
    assert encoded[0] is not None and encoded[1] is None
    assert overflow.tolist() == [False, True]
    logits = np.array([[0, 12, 0, 0, 0], [0, 12, 0, 0, 0]], dtype=float)
    assert tr.predict(
        logits, dict.fromkeys(tr.LABELS[1:], 0.98), overflow
    ).tolist() == [1, 0]


def test_thresholds_enforce_empirical_none_cap_with_ties():
    logits = np.zeros((105, 5))
    logits[:3, 1] = 10  # three tied false positives exceed 2/100 budget
    logits[100:, 1] = 12
    labels = np.array([0] * 100 + [1] * 5)
    thresholds = tr.calibrate_thresholds(logits, labels)
    predictions = tr.predict(logits, thresholds)
    assert np.count_nonzero(predictions[:100]) <= 2
    assert (predictions[100:] == 1).all()
    assert all(v >= 0.98 for v in thresholds.values())
    assert thresholds["cancels"] > 1  # no development support disables the class
    no_none = tr.calibrate_thresholds(logits[100:], labels[100:])
    assert (tr.predict(logits, no_none) == 0).all()


def test_invalid_logits_and_disabled_saturated_class_fail_safe():
    logits = np.array([[0, 10000, 0, 0, 0], [np.nan, 2, 0, 0, 0]])
    disabled = dict.fromkeys(tr.LABELS[1:], tr.DISABLED_THRESHOLD)
    assert tr.predict(logits, disabled).tolist() == [0, 0]
    with pytest.raises(ValueError):
        tr.calibrate_thresholds(logits, np.array([0, 1]))


def test_group_split_preserves_scenarios_messages_and_relatives():
    rows = [
        tr.normalize_row(row(f"Message {i}.", "none", scenario_id=f"s{i // 2}"))
        for i in range(40)
    ]
    rows[10]["parent_id"] = "relative"
    rows[20]["id"] = "relative"
    fit, dev = tr.split_development(rows, seed=7)
    assert fit and dev
    assert {r["scenario_id"] for r in fit}.isdisjoint(r["scenario_id"] for r in dev)
    assert {r["author"] for r in dev} <= {r["author"] for r in fit}
    assert (rows[10] in dev) == (rows[20] in dev)
    assert tr.split_development(rows, seed=7) == (fit, dev)


def test_metrics_none_fp_and_hard_negative_denominators():
    rows = [
        tr.normalize_row(row("a", "none", hard=True)),
        tr.normalize_row(row("b", "none")),
        tr.normalize_row(row("c", "supersedes", hard=True)),
    ]
    report = tr.evaluation_report(rows, np.array([1, 0, 1]), np.zeros(3, dtype=bool))
    assert report["none_fp"]["numerator"] == 1
    assert report["none_fp"]["denominator"] == 2
    assert report["hard_negatives"]["none_fp"]["rate"] == 1
    assert report["per_class"]["supersedes"]["precision"] == 0.5


def test_admission_separate_and_heldout_disjointness():
    admission = row(old_rule=None, label=None, message_new_rule=True)
    assert tr.normalize_row(admission) is None
    fit = [tr.normalize_row(row())]
    held = [tr.normalize_row(row(author="fable"))]
    with pytest.raises(ValueError, match="overlap"):
        tr.assert_heldout_disjoint(fit, held)


def test_import_safe_and_cpu_defaults():
    from tests.test_no_side_effect_imports import top_level_work

    assert not top_level_work("scripts/train_relations.py")
    args = tr.parse_args([])
    assert args.device == "cpu" and args.seed == 9054301
    assert args.base_revision == "5c38ec7c405ec4b44b94cc5a9bb96e735b38267a"


def test_patch_summary_is_receipted_without_becoming_a_patch(tmp_path):
    data = write_rows(tmp_path / "data.jsonl", [row()])
    patches = write_rows(
        tmp_path / "patch.jsonl",
        [{"summary": {"audit": "IFEval markers checked without opening inputs"}}],
    )
    rows, audit = tr.load_training([data], [patches], [])
    assert len(rows) == 1
    assert len(audit["review_summaries"]) == 1


def test_nested_patch_key_requires_exact_rule_version():
    original = row(
        old_rule={
            "text": "Use round bullets",
            "version": 1,
            "scope": "global",
            "status": "live",
        }
    )
    patch = {k: copy.deepcopy(original[k]) for k in ("source", "message", "old_rule")}
    patch.update(old_label="supersedes", new_label="none", drop=False)
    other = copy.deepcopy(original)
    other["old_rule"]["version"] = 2
    result, _ = tr.apply_patches([original, other], [patch])
    assert [r["label"] for r in result] == ["none", "supersedes"]


def test_explicit_development_and_spec_illustration_never_fit():
    rows = [tr.normalize_row(row(f"Unique message {i}.")) for i in range(40)]
    a, b = tr.DEVELOPMENT_ILLUSTRATIONS[0]
    illustration = tr.normalize_row(row(b, "none", old_rule=a))
    explicit = tr.normalize_row(row("Development only.", split="development"))
    rows.extend([illustration, explicit])
    fit, dev = tr.split_development(rows)
    assert illustration in dev and explicit in dev
    assert all(not r["development_only"] for r in fit)


def test_conflicting_heldout_labels_stop_scoring():
    a, b = tr.normalize_row(row()), tr.normalize_row(row(label="none"))
    with pytest.raises(ValueError, match="conflicting held-out"):
        tr.deduplicate([a, b], reject_conflicts=True)


@pytest.mark.parametrize("smoke", [True, False])
def test_cpu_pipeline_freezes_before_heldout_and_smoke_never_reads_it(
    tmp_path, monkeypatch, smoke
):
    """Exercise the training consumer using tiny stand-ins, no model download."""
    from types import SimpleNamespace

    import torch
    import transformers
    from safetensors.torch import save_file

    modes = []

    class Encoder(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.config = SimpleNamespace(hidden_size=4)
            self.embedding = torch.nn.Embedding(64, 4)

        def forward(self, input_ids, attention_mask):
            modes.append(self.training)
            return SimpleNamespace(last_hidden_state=self.embedding(input_ids))

        def save_pretrained(self, path):
            assert not self.training
            path.mkdir(parents=True)
            save_file(self.state_dict(), str(path / "model.safetensors"))

    class Tokenizer(TinyTokenizer):
        def pad(self, items, **kwargs):
            length = max(len(item["input_ids"]) for item in items)
            return {
                key: torch.tensor(
                    [item[key] + [0] * (length - len(item[key])) for item in items]
                )
                for key in items[0]
            }

        def save_pretrained(self, path):
            (path / "tokenizer.json").write_text("{}")

    def base_only(name, **kwargs):
        assert name == tr.BASE_MODEL and kwargs["revision"] == tr.BASE_REVISION
        return Encoder()

    monkeypatch.setattr(transformers.AutoModel, "from_pretrained", base_only)
    monkeypatch.setattr(
        transformers.AutoTokenizer, "from_pretrained", lambda *a, **kw: Tokenizer()
    )
    data = write_rows(
        tmp_path / "training.jsonl",
        [row(f"Fixture {i}.", tr.LABELS[i % 5]) for i in range(200)],
    )
    patch = write_rows(tmp_path / "patch.jsonl", [])
    enrich = write_rows(tmp_path / "enrich.jsonl", [])
    heldout = write_rows(
        tmp_path / "fable.jsonl",
        [
            row(f"Held-out fixture {i}.", tr.LABELS[i % 5], author="fable")
            for i in range(20)
        ],
    )
    original_read = tr.read_jsonl
    heldout_reads = []

    def guarded_read(path, **kwargs):
        if kwargs.get("evaluation"):
            assert not smoke and path == heldout
            frozen = json.loads((output / "manifest.json").read_text())
            assert frozen["state"] == "checkpoint_and_thresholds_frozen"
            for name, sha in frozen["artifact_sha256"].items():
                assert (
                    tr.hashlib.sha256((output / name).read_bytes()).hexdigest() == sha
                )
            heldout_reads.append(path)
        else:
            assert path in (data, patch, enrich)
        return original_read(path, **kwargs)

    monkeypatch.setattr(tr, "read_jsonl", guarded_read)
    output = tmp_path / "output"
    args = tr.parse_args(
        [
            *(["--cpu-smoke"] if smoke else []),
            "--epochs",
            "1",
            "--heldout",
            str(heldout),
            "--train",
            str(data),
            "--patch",
            str(patch),
            "--enrich",
            str(enrich),
            "--output",
            str(output),
        ]
    )
    tr.train(args)
    manifest = json.loads((output / "manifest.json").read_text())
    assert manifest["state"] == ("cpu_smoke_complete" if smoke else "complete")
    assert manifest["recipe"]["device"] == "cpu"
    assert manifest["split"]["fit"]["n"] == 180
    assert manifest["split"]["development"]["n"] == 20
    assert set(modes) == {True, False} and modes[-1] is False
    assert ("heldout" in json.loads((output / "metrics.json").read_text())) == (
        not smoke
    )
    assert len(heldout_reads) == (0 if smoke else 1)
    assert "head.safetensors" in manifest["artifact_sha256"]
    for name, expected in manifest["artifact_sha256"].items():
        assert tr.hashlib.sha256((output / name).read_bytes()).hexdigest() == expected
    with pytest.raises(ValueError, match="output already exists"):
        tr.train(args)
