# ruff: noqa: E501
"""E2 synthetic multi-turn session generator — red/green TDD.

Sessions mirror Multi-IF's SHAPE: turn 1 = task + constraints; turns
2-3 add constraints while ALL earlier ones still bind (cumulative
lists, like Multi-IF's turn_N columns). Own topics/phrasings/values;
leak-firewalled against Multi-IF; no canonicals needed (harvest rolls
the model's own generations)."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_session_shape_and_cumulative_binding():
    from stencil.b3_gen_mt import generate_sessions
    sessions = generate_sessions(seed=0, n_sessions=20, split="train")
    assert len(sessions) == 20
    for s in sessions:
        assert len(s["turns"]) == 3
        prev_ids = []
        for t in s["turns"]:
            assert t["prompt"].strip()
            # cumulative: this turn's list starts with all prior ids
            assert t["instruction_id_list"][: len(prev_ids)] == prev_ids
            assert len(t["instruction_id_list"]) > len(prev_ids)
            assert len(t["instruction_id_list"]) == len(t["kwargs"])
            prev_ids = t["instruction_id_list"]
        # every cumulative combo is jointly satisfiable per the v4.3 matrix
        from stencil.b3_gen43 import combo_ok
        assert combo_ok(sorted(s["turns"][-1]["combo"]))


def test_deterministic_and_split_topics():
    from stencil.b3_gen43 import DEV_TOPICS, TRAIN_TOPICS
    from stencil.b3_gen_mt import generate_sessions
    a = generate_sessions(seed=0, n_sessions=10, split="train")
    b = generate_sessions(seed=0, n_sessions=10, split="train")
    assert a == b
    assert generate_sessions(seed=1, n_sessions=10, split="train") != a
    for s in a:
        assert s["topic"] in set(TRAIN_TOPICS)
    for s in generate_sessions(seed=2, n_sessions=10, split="dev"):
        assert s["topic"] in set(DEV_TOPICS)


def test_turn1_is_task_later_turns_are_followups():
    from stencil.b3_gen_mt import generate_sessions
    s = generate_sessions(seed=0, n_sessions=5, split="train")[0]
    assert "Constraint:" in s["turns"][0]["prompt"]
    for t in s["turns"][1:]:
        # follow-up turns state the new constraints and the still-binding rule
        assert "Constraint:" in t["prompt"]
        assert "still apply" in t["prompt"] or "still applies" in t["prompt"]


def test_constraints_verifiable_by_vendored_checkers():
    import random
    import sys
    sys.path.insert(0, str(ROOT / "vendor"))
    import langdetect
    langdetect.DetectorFactory.seed = 0
    from ifeval import instructions_registry

    from stencil.b3_gen_mt import generate_sessions
    for s in generate_sessions(seed=0, n_sessions=10, split="train"):
        t = s["turns"][-1]
        random.seed(0)
        for iid, kw in zip(t["instruction_id_list"], t["kwargs"]):
            inst = instructions_registry.INSTRUCTION_DICT[iid](iid)
            inst.build_description(**{k: v for k, v in kw.items() if v})  # must not raise
            assert isinstance(inst.check_following("A plain sample response."), bool)


def _norm(s):
    return re.sub(r"[^a-z0-9 ]", " ", s.lower())


def test_leak_firewall_vs_multiif():
    from stencil.b3_gen_mt import generate_sessions
    mif = [json.loads(line) for line in open(ROOT / "data" / "bench" / "multiif_en.jsonl")]
    mif_prompts = [_norm(json.loads(r[f"turn_{t}_prompt"])["content"])
                   for r in mif for t in (1, 2, 3) if r[f"turn_{t}_prompt"]]
    sessions = generate_sessions(seed=0, n_sessions=30, split="train")
    for s in sessions:
        for t in s["turns"]:
            head = " ".join(_norm(t["prompt"]).split()[:8])
            assert not any(head in p for p in mif_prompts)
    # parameterized kwargs disjoint from Multi-IF's (same rule as the 541)
    mif_kw = set()
    for r in mif:
        for t in (1, 2, 3):
            if not r[f"turn_{t}_instruction_id_list"]:
                continue
            ids = json.loads(r[f"turn_{t}_instruction_id_list"])
            kws = [json.loads(k) for k in json.loads(r[f"turn_{t}_kwargs"])]
            for i, k in zip(ids, kws):
                kn = {a: b for a, b in k.items() if b is not None and a != "postscript_marker"}
                if kn:
                    mif_kw.add((i, json.dumps(kn, sort_keys=True)))
    for s in sessions:
        t = s["turns"][-1]
        for i, k in zip(t["instruction_id_list"], t["kwargs"]):
            kn = {a: b for a, b in k.items() if b and a != "postscript_marker"}
            if kn:
                assert (i, json.dumps(kn, sort_keys=True)) not in mif_kw, (i, kn)
