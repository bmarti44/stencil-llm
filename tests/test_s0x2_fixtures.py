# ruff: noqa: E501
"""T1 prereg R2: interference="s0x2" — red-first.

s0x plus a task-structural moment suffix on EVERY work turn's task text:
"Include a one-line docstring and type-annotate both arguments." The
suffix must not create pressable candidate spans (matches no
CAND_PATTERN) and everything s0x guarantees still holds.
"""
from stencil.t2_select import candidate_spans
from stencil.t2_sessions import SENT, generate_t2, prompt_at

SUFFIX = "Include a one-line docstring and type-annotate both arguments."


def test_s0x2_suffix_on_every_work_turn():
    s = generate_t2(4, 20, "dev", interference="s0x2")
    for wt in s.work_turns:
        assert SUFFIX in s.turns[wt].text, wt
    # non-work turns unaffected
    for i, t in enumerate(s.turns):
        if i not in s.work_turns:
            assert SUFFIX not in t.text


def test_s0x2_suffix_creates_no_candidates():
    class Enc:
        def __init__(self, t):
            self.offsets = [(i, i + 1) for i in range(len(t))]
    assert candidate_spans(SUFFIX, Enc(SUFFIX)) == []


def test_s0x2_keeps_s0x_guarantees():
    for seed in range(6):
        s = generate_t2(seed, 20, "dev", interference="s0x2")
        info = s.held_out["s0x"]
        wt = s.work_turns[-1]
        assert info["work_turn"] == wt
        assert info["type"] not in s.ledger_at[wt]
        assert SENT[info["type"]].format(v=info["value"]) in prompt_at(s, wt, "dev")


def test_s0x2_deterministic_and_distinct_from_s0x():
    a = generate_t2(7, 20, "dev", interference="s0x2")
    b = generate_t2(7, 20, "dev", interference="s0x2")
    assert [t.text for t in a.turns] == [t.text for t in b.turns]
    c = generate_t2(7, 20, "dev", interference="s0x")
    # same structure, differing only by the suffix on work turns
    assert len(a.turns) == len(c.turns)
    diffs = [i for i in range(len(a.turns)) if a.turns[i].text != c.turns[i].text]
    assert set(diffs) == set(a.work_turns)
