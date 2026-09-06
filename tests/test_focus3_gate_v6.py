"""Mechanical repairs and actual admission/calibration consumers for v6."""

import copy

import numpy as np
import pytest

from scripts import focus3_gate_v6 as v6
from scripts import train_relations as tr
from stencil import focus3 as f
from stencil import relation_operating_point as op
from tests.test_focus3_gate_v5 import Classifier


def row():
    return dict(
        old_rule=dict(text="Always sort ascending.", scope="task:Cedar", status="live"),
        message="Repeat. Repeat.",
        target_span=dict(text="Repeat.", start=999, end=1),
        role="user",
        label="none",
        source="kimi:fixture",
        source_file="fixture.jsonl",
        source_row=1,
        new_rule_spans=[dict(text="Repeat.")],
    )


def test_mechanical_repair_and_explicit_drops():
    good = row()
    variants = []
    for field in ["status", "target", "new"]:
        r = row()
        if field == "status":
            r["old_rule"]["status"] = "systematic"
        elif field == "target":
            r["target_span"]["text"] = "repeat."
        else:
            r["new_rule_spans"] = ["Fabricated."]
        variants.append(r)
    repaired, audit = tr.repair_v2([good] + variants)
    assert len(repaired) == 1 and len(audit["drops"]) == 3
    assert repaired[0]["target_span"] == dict(start=0, end=7, text="Repeat.")
    assert repaired[0]["new_rule_spans"] == ["Repeat."]
    assert repaired[0]["id"] and repaired[0]["scenario_id"]
    assert good == row()


def test_status_minimal_pair_survives_full_input_dedup_and_groups():
    a = row()
    b = copy.deepcopy(a)
    b["old_rule"]["status"] = "cancelled"
    b["label"] = "reinstates"
    b["source_row"] = 2
    repaired, _ = tr.repair_v2([a, b])
    rows = [tr.normalize_row(r) for r in repaired]
    kept, drops = tr.deduplicate(rows, full_input=True)
    assert len(kept) == 2 and not drops
    assert len(tr.group_rows(kept)) == 1
    conflict = copy.deepcopy(kept[0])
    conflict["label"] = "cancels"
    kept, drops = tr.deduplicate([*kept, conflict], full_input=True)
    assert len(kept) == 1 and len(drops) == 2


@pytest.mark.parametrize("score,accepted", [(0.799999, True), (0.80, False)])
def test_positive_proposal_bound_exact_cutoff_consumer(score, accepted):
    clf = Classifier(pnone=1 - score)
    clf.thresholds = dict(supersedes=0.80, cancels=0.5, completes=0.5, reinstates=0.5)
    clf.admission_bound = "positive_proposal"
    rt = f.Runtime(clf)
    old = rt.register.add("Keep tag equal to 7.", "tag", "*", "sort", 0, 0)
    # Inapplicable supersedes still vetoes admission: bound precedes status guard.
    old.status = "cancelled"
    trace = rt.update("Always sort ascending for task Cedar.", 1)
    assert len(trace["pairs"]) == 1
    assert trace["admissions"][0]["accepted"] is accepted
    assert len(rt.register.rows) == 1 + accepted


def test_blocked_reinstates_proposal_also_blocks_admission():
    clf = Classifier(label="reinstates")
    clf.admission_bound = "positive_proposal"
    rt = f.Runtime(clf)
    rt.register.add("Keep tag equal to 7.", "tag", "*", "sort", 0, 0)
    trace = rt.update("Always sort ascending for task Cedar.", 1)
    assert trace["pairs"][0]["proposed"] == "reinstates"
    assert not trace["admissions"][0]["accepted"] and not trace["applied"]


def test_calibration_caps_and_consumer_parity():
    p = np.tile([0.96, 0.01, 0.01, 0.01, 0.01], (40, 1))
    p[0] = [0.39, 0.60, 0.003, 0.003, 0.004]
    p[1] = [0.39, 0.60, 0.003, 0.003, 0.004]
    p[2] = [0.19, 0.80, 0.003, 0.003, 0.004]
    p[3] = [0.19, 0.80, 0.003, 0.003, 0.004]
    p[4] = [0.09, 0.90, 0.003, 0.003, 0.004]
    positives = np.full((4, 5), 0.01)
    positives[np.arange(4), np.arange(1, 5)] = 0.96
    probs = np.concatenate([p, positives])
    labels = np.array([0] * 40 + [1, 2, 3, 4])
    overflow = np.zeros(44, dtype=bool)
    result = v6.calibrate(dict(logits=np.log(probs), labels=labels, overflow=overflow))
    c, alt = [result["arms"][a]["policy"] for a in ["C", "C'"]]
    assert c["thresholds"]["supersedes"] == 0.81
    assert alt["thresholds"]["supersedes"] == 0.61
    for policy in [c, alt]:
        pp, _, _ = op.inputs(np.log(probs), labels, overflow)
        predicted = op.predict(pp, policy, overflow)
        assert [f.decision(row, False, policy["thresholds"]) for row in pp] == [
            op.LABELS[i] for i in predicted
        ]
    assert result["arms"]["C"]["dev"]["none_fp_count"] == 1
    assert result["arms"]["C'"]["dev"]["none_fp_count"] == 3


def test_ineligible_gate_fails_before_claim_or_trunk(tmp_path, monkeypatch):
    monkeypatch.setattr(v6, "OUT", tmp_path)
    monkeypatch.setattr(v6, "verify_freeze", lambda: {})
    (tmp_path / "summary.json").write_text('{"eligible": false}')
    with pytest.raises(AssertionError, match="gate prohibited"):
        v6.run()


def test_cpu_replay_writer_and_repeat_guard(tmp_path, monkeypatch):
    import json

    class Fake:
        admission_bound = "positive_proposal"
        thresholds = f.THRESHOLDS

        def prediction(self, model_input, n):
            logits = np.array([8.0] + [0.0] * (n - 1))
            return dict(
                logits=logits.tolist(),
                probabilities=(
                    np.exp(logits - logits.max()) / np.exp(logits - logits.max()).sum()
                ).tolist(),
                model_input=list(model_input),
                overflow=False,
            )

        def relations(self, pairs):
            return [self.prediction(f.pair_input(p), 5) for p in pairs]

        def admission(self, spans, previous):
            return [self.prediction(p, 3) for p in f.admission_inputs(spans, previous)]

    monkeypatch.setattr(v6, "OUT", tmp_path)
    monkeypatch.setattr(v6, "verify_freeze", lambda: {})
    monkeypatch.setattr(v6, "classifier", Fake)
    monkeypatch.setenv("CUDA_VISIBLE_DEVICES", "")
    for name, value in [
        ("second-look.json", {}),
        ("freeze.json", {}),
        ("fit-summary.json", dict(gpu_held_seconds=1)),
    ]:
        (tmp_path / name).write_text(json.dumps(value))
    v6.replay()
    summary = json.loads((tmp_path / "summary.json").read_text())
    assert summary["verdict"] == "INELIGIBLE"
    assert len(list((tmp_path / "records").glob("*.json"))) == 96
    assert len(list((tmp_path / "traces").glob("*.json"))) == 16
    with pytest.raises(FileExistsError):
        v6.replay()


def test_secondary_arm_uses_runtime_and_its_own_policy(tmp_path, monkeypatch):
    from scripts import focus3_gate as gate
    from stencil import focus2
    from tests.test_focus3_gate import Scripted

    monkeypatch.setattr(gate, "OUT", tmp_path)

    class Trunk:
        tok = focus2.load_tokenizer(f.ROOT / "models/qwen3-4b-hf/tokenizer.json")

        def answer(self, history, text):
            return dict(
                text="idle",
                output_ids=[1],
                eos=151645,
                prompt_ids=[1],
                pair_ids=[2],
                output_start=1,
                seconds=0.0,
            )

    clf = Scripted("supersedes", 0.7)
    clf.thresholds = dict(supersedes=0.6, cancels=0.5, completes=0.5, reinstates=0.5)
    clf.admission_bound = "positive_proposal"
    ep = dict(
        id="secondary",
        family="override",
        gold_keys={},
        turns=[
            dict(
                text=text,
                events=[],
                kind="prose",
                task="Cedar",
                post_change=i > 0,
                hard_none=False,
            )
            for i, text in enumerate(
                [
                    "Work on task Cedar. Always sort ascending.",
                    "Always sort descending for task Cedar.",
                ]
            )
        ],
    )
    records = gate.run_episode(ep, "C'", Trunk(), clf, "gate")
    assert records[1]["trace"]["applied"][0]["label"] == "supersedes"
    assert records[1]["selected_task"] == "Cedar"
    assert records[1]["trace"]["after"][-1]["status"] == "live"
    assert records[1]["arm"] == "C'"
