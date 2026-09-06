"""CPU contracts for the public register/renderer and gate consumer."""

import json

from stencil import focus3 as f


def probs(label, confidence=1.0):
    p = [0.0] * 5
    p[f.LABELS.index(label)] = confidence
    p[0] += 1 - confidence
    return p


class Scripted:
    def __init__(self, label="none", confidence=1.0):
        self.label, self.confidence = label, confidence

    def relations(self, pairs):
        return [
            dict(probabilities=probs(self.label, self.confidence), overflow=False)
            for _ in pairs
        ]

    def admission(self, spans, previous):
        return [dict(probabilities=[0.0, 1.0, 0.0], overflow=False) for _ in spans]


def test_precedence_preserves_global_outside_task_and_return():
    r = f.Register()
    a = r.add("For all tasks, sort ascending.", "sort", "*", "sort", 0, 0)
    b = r.add("For task Cedar, sort descending.", "sort", "Cedar", "sort", 1, 0)
    assert r.live("Cedar", "sort") == [b]
    assert r.live("Maple", "sort") == [a]
    assert r.live("Cedar", "sort") == [b]
    r.retire(b.id, "cancelled")
    assert r.live("Cedar", "sort") == [a]


def test_threshold_and_invalid_fail_safe_none():
    assert f.decision(probs("supersedes", 0.939)) == "none"
    assert f.decision(probs("supersedes", 0.94)) == "supersedes"
    assert f.decision([float("nan")] * 5) == "none"
    r = f.Runtime(Scripted())
    r.update("For task Cedar, sort the payload in ascending order.", 0)
    before = r.register.snapshot()
    r.classifier = Scripted("cancels", 0.49)
    r.update("Cancel the sorting rule for task Cedar.", 1)
    assert r.register.snapshot() == before
    for role in ("tool", "assistant"):
        r.classifier = Scripted("cancels")
        r.update("Cancel the sorting rule for task Cedar.", 2, role=role)
        assert r.register.snapshot() == before


def test_renderer_inside_current_user_and_kind_placement():
    r = f.Register()
    r.add("Sort ascending.", "order", "Cedar", "sort", 0, 0)
    r.add("Keep tag equal to 8.", "tag", "*", "sort", 0, 20)
    rows = r.live("Cedar", "sort")
    rendered = f.render("Payload: [3,1,2]", rows)
    assert rendered.endswith("Current user request:\nPayload: [3,1,2]")
    assert len(json.loads(rendered.splitlines()[1])) == 2
    assert not r.live("Cedar", "prose")
    assert f.render("Say hello.", []) == "Say hello."


def test_scripted_oracle_classifier_parity_and_hard_none():
    c = f.Runtime(Scripted())
    o = f.Oracle()
    text = "For task Cedar, sort the payload in ascending order."
    c.update(text, 0)
    o.update(
        text,
        0,
        [
            {
                "label": "admit",
                "span": text,
                "key": "order",
                "scope": "Cedar",
                "kind": "sort",
            }
        ],
    )
    replacement = "For task Cedar, sort the payload in descending order."
    c.classifier = Scripted("supersedes")
    c.update(replacement, 1)
    o.update(
        replacement,
        1,
        [
            {
                "label": "supersedes",
                "span": replacement,
                "target": "0:0",
                "scope": "Cedar",
                "kind": "sort",
            }
        ],
    )
    assert f.live_set(c.register.live("Cedar", "sort")) == f.live_set(
        o.register.live("Cedar", "sort")
    )
    c.classifier = Scripted("none")
    c.update('Suppose someone said "cancel that"; this is hypothetical.', 2)
    assert f.live_set(c.register.live("Cedar", "sort")) == f.live_set(
        o.register.live("Cedar", "sort")
    )


def test_endpoint_discriminators_breakage_and_agreement():
    turn = dict(
        kind="sort",
        payload=[3, 1, 2],
        direction="descending",
        stale=["ascending"],
        tag=7,
        post_change=True,
    )
    s = f.score(turn, '{"answer":[1,2,3],"tag":7}', [1, 2], 151645)
    assert s["stale"] and not s["success"] and not s["broken"]
    assert f.score(turn, "{}", [1], None)["broken"]
    s = f.score(turn, '{"answer":[3,2,1],"tag":7}', [1], 151645)
    assert s["success"] and not s["stale"]
    row = f.Rule("0:0", "x", "key", "A", "sort", 1, "live", 0, 0)
    assert f.agreement([row], [row], {"0:0": "order"}) == {
        "exact": True,
        "false_retirement": False,
        "contradictory": False,
    }
    assert f.agreement([], [row], {"0:0": "order"})["false_retirement"]
    duplicate = f.Rule("1:0", "y", "other", "A", "sort", 1, "live", 1, 0)
    assert f.agreement([row, duplicate], [row], {"0:0": "order", "1:0": "order"})[
        "contradictory"
    ]


def test_overflow_abstains_and_explicit_single_reply_never_persists():
    r = f.Runtime(Scripted())
    r.update("Work on task Cedar.", 0)
    before = r.register.snapshot()
    trace = r.update("One. Two. Three. Four. Five.", 1)
    assert trace["overflow"] and r.register.snapshot() == before
    r.update("For this reply only, sort descending.", 2)
    assert r.register.snapshot() == before


def test_confident_none_can_admit_beside_live_is_disclosed():
    r = f.Runtime(Scripted())
    r.update("For task Cedar, sort the payload in ascending order.", 0)
    trace = r.update("Cancel the sorting rule for task Cedar.", 1)
    assert len(r.register.rows) == 2
    assert trace["admitted_beside_live"] == 1
    assert all(row.status == "live" for row in r.register.rows)


def test_explicit_scope_and_request_kind_are_parsed_without_gold():
    assert f.selected_task('A quote: "Work on task Maple."', "Cedar") == "Cedar"
    assert f.scope_of("Task Cedar is complete.", "Maple") == "Cedar"
    assert f.selected_task("Return to task Cedar; do the work.", "Maple") == "Cedar"
    assert f.request_kind("Sort request for task Cedar: payload [1,2].") == "sort"
    assert f.request_kind("Reply exactly idle.") == "prose"


def test_gate_consumer_requires_overall_and_each_family_agreement():
    import copy

    from scripts.focus3_gate import FAMILIES

    episodes, records = [], []
    for family in FAMILIES:
        for i in range(16):
            eid = f"{family}_{i}"
            episodes.append(dict(id=eid, family=family))
            for arm in ("C", "O", "N", "T"):
                records.append(
                    dict(
                        episode=eid,
                        arm=arm,
                        turn=dict(kind="sort", post_change=True),
                        score=dict(stale=arm == "T", success=True, broken=False),
                        agreement=dict(
                            exact=arm != "C" or i < 12,
                            false_retirement=False,
                            contradictory=False,
                        ),
                    )
                )
    summary = f.summarize(episodes, records, 64)
    assert summary["verdict"] == "PASS"
    assert summary["counts"]["pooled"]["C"]["exact"] == 48
    assert summary["counts"]["pooled"]["N"]["false_retirement"] is None
    bad = copy.deepcopy(records)
    next(r for r in bad if r["arm"] == "C")["agreement"]["exact"] = False
    assert f.summarize(episodes, bad, 64)["verdict"] == "FAIL"
    for r in bad:
        if r["arm"] == "C":
            r["agreement"]["exact"] = True
            r["agreement"]["contradictory"] = True
    assert not f.summarize(episodes, bad, 64)["terms"]["no_contradiction"]


def test_writer_runs_complete_pairs_and_keeps_bad_answers(tmp_path, monkeypatch):
    from scripts import focus3_gate as gate
    from stencil import focus2

    monkeypatch.setattr(gate, "OUT", tmp_path)

    class FakeTrunk:
        tok = focus2.load_tokenizer(f.ROOT / "models/qwen3-4b-hf/tokenizer.json")

        def answer(self, history, text):
            assert len(history) == len(calls)
            calls.append(text)
            return dict(
                text="{}",
                output_ids=[1],
                eos=151645,
                prompt_ids=[1],
                pair_ids=[2],
                output_start=1,
                seconds=0.0,
            )

    calls = []
    ep = dict(
        id="smoke",
        family="cancel",
        gold_keys={},
        turns=[
            dict(
                text="Work on task Cedar. Reply exactly idle.",
                events=[],
                kind="prose",
                task="Cedar",
                post_change=i > 1,
                hard_none=i == 1,
            )
            for i in range(6)
        ],
    )
    records = gate.run_episode(ep, "N", FakeTrunk(), Scripted(), "gate")
    assert len(records) == len(calls) == 6
    assert len(list((tmp_path / "gate/records").glob("*.json"))) == 6
    assert len(json.loads((tmp_path / "gate/traces/smoke_N.json").read_text())) == 6
    assert all(r["generation"]["text"] == "{}" for r in records)
    assert all(not r["provenance"]["mask_used"] for r in records)
