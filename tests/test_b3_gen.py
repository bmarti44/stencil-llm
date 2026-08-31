# ruff: noqa: E501
"""B3 generator acceptance (v3.1 materialization): every canonical
response passes ALL its constraints via the VENDORED checkers, every
mutation fails its target, the generator is deterministic, all train
families are covered and no held-out family appears, and the v3.1
leak firewall (a)(b)(c) holds mechanically against the 541."""
import json
import re
from pathlib import Path

from stencil.b3_gen import (
    CONSTRAINTS,
    TOPICS,
    combo_ok,
    compat_matrix,
    generate,
    verify_rows,
)

ROOT = Path(__file__).resolve().parent.parent
N_SAMPLE = 300  # review-scale sample; the full 2000 freeze run reuses the same code path


def _sample():
    return generate(seed=0, n_prompts=N_SAMPLE)


def test_deterministic():
    a, b = generate(0, 40), generate(0, 40)
    assert a == b
    assert generate(1, 40) != a


def test_all_canonicals_pass_and_mutations_fail():
    ok, failures = verify_rows(_sample())
    assert not failures, failures[:10]
    assert ok == N_SAMPLE


def test_family_coverage():
    rows = _sample()
    fams = {CONSTRAINTS[k]["family"] for r in rows for k in r["combo"]}
    assert fams == {"change_case", "keywords", "length", "detectable_format",
                    "detectable_content", "combination"}
    held = {"punctuation", "startend", "language"}
    iids = {i for r in rows for i in r["instruction_id_list"]}
    assert not any(i.split(":")[0] in held for i in iids)


def test_combos_respect_matrix():
    m = compat_matrix()
    for r in _sample():
        assert combo_ok(r["combo"], m), r["combo"]
    assert not combo_ok(["caps", "lower"], m)
    assert not combo_ok(["json_fmt", "title"], m)


def _norm(s):
    return re.sub(r"[^a-z0-9 ]", " ", s.lower())


def test_leak_firewall():
    rows541 = [json.loads(line) for line in open(ROOT / "data" / "bench" / "ifeval_input_data.jsonl")]
    gen = _sample()
    # (a) per-instruction-id kwargs tuples disjoint
    # (a) applies to PARAMETERIZED constraints; parameterless ones (caps,
    # lower, json, title, two_responses) have identical empty kwargs by
    # construction and rely on firewalls (b) phrasing + (c) topics.
    for r in gen:
        for i, k in zip(r["instruction_id_list"], r["kwargs"]):
            if not k:
                continue
            for r5 in rows541:
                for i5, k5 in zip(r5["instruction_id_list"], r5["kwargs"]):
                    if i5 == i:
                        k5n = {kk: vv for kk, vv in k5.items() if vv is not None}
                        assert k5n != k, (i, k)
    # (b) instruction phrasings never substring-overlap with 541 prompts
    norm541 = [_norm(r["prompt"]) for r in rows541]
    for key, c in CONSTRAINTS.items():
        import random as _r
        phrase = _norm(c["phrase"](c["sample"](_r.Random(0))))
        head = " ".join(phrase.split()[:6])
        assert not any(head in p for p in norm541), key
    # (c) topics disjoint from 541 prompts
    for t in TOPICS:
        tn = _norm(t)
        assert not any(tn in p for p in norm541), t


def test_compat_matrix_committed_matches_code():
    committed = json.loads((ROOT / "data" / "b3" / "compat-matrix.json").read_text())
    assert committed == compat_matrix()


def test_every_declared_pair_is_reachable():
    """checkpoint-ii round-2 sol FINDING-2: declared-but-unreachable pairs
    (insertion-order storage vs sorted lookup) must be impossible."""
    m = compat_matrix()
    for a, b in m["allowed_pairs"]:
        assert combo_ok(sorted([a, b]), m), (a, b)
    # and the committed matrix contains only canonically-ordered pairs
    for a, b in m["allowed_pairs"]:
        assert [a, b] == sorted([a, b])


def test_dev_stream_disjoint_from_train():
    train = {json.loads(line)["prompt"] for line in open(ROOT / "data" / "b3" / "train-2000.jsonl")}
    dev = [json.loads(line) for line in open(ROOT / "data" / "b3" / "dev-200.jsonl")]
    assert len(dev) == 200
    assert not any(r["prompt"] in train for r in dev)


def test_constraint_spans():
    from tokenizers import Tokenizer

    from stencil.b3_gen import constraint_spans
    tok = Tokenizer.from_file(str(ROOT / "models" / "qwen3-1.7b-hf" / "tokenizer.json"))
    rows = [json.loads(line) for line in open(ROOT / "data" / "b3" / "train-2000.jsonl")][:100]
    for r in rows:
        spans = constraint_spans(r, tok)
        enc = tok.encode(r["prompt"])
        assert set(spans) == set(r["combo"])
        for key, (a, b) in spans.items():
            assert 0 <= a < b <= len(enc.ids)
            # the span's decoded text contains the phrase's anchor word
            seg = tok.decode(enc.ids[a:b])
            assert "Constraint" in seg or "constraint" in seg, (key, seg[:60])
