# ruff: noqa: E501
"""W3a generator mode interference="s0c" — red-first.

s0 scheduling + CLEAN prefix rendering: every prefix sentence anywhere
(user_set/update, distractors, s0 notes, ledger, stale matching) uses
SENT_UNSEEN_FMT; the trained prefix template appears NOWHERE for ANY
pool value. Scope: prefix only."""
from stencil.qwen_task import CODE_PREFIXES
from stencil.t2_sessions import SENT, SENT_UNSEEN_FMT, generate_t2, prompt_at


def all_prompts(s):
    return [prompt_at(s, wt, "dev") for wt in s.work_turns]


def test_zero_trained_prefix_occurrences_all_values():
    for seed in range(13_700_000, 13_700_012):
        s = generate_t2(seed, 20, "dev", interference="s0c")
        for p in all_prompts(s):
            for v in CODE_PREFIXES:
                assert SENT["prefix"].format(v=v) not in p, (seed, v)


def test_unseen_format_present_when_prefix_active():
    found = False
    for seed in range(13_700_000, 13_700_008):
        s = generate_t2(seed, 20, "dev", interference="s0c")
        for wt in s.work_turns:
            led = s.ledger_at[wt]
            if "prefix" in led:
                p = prompt_at(s, wt, "dev")
                assert SENT_UNSEEN_FMT["prefix"].format(v=led["prefix"]) in p, (seed, wt)
                found = True
    assert found


def test_s0_notes_still_scheduled():
    s = generate_t2(13_700_003, 20, "dev", interference="s0c")
    note_turns = [t for t in s.turns if t.text.startswith("Note: ")]
    assert len(note_turns) >= 2 * len(s.work_turns) - 2  # two per work (minus early-ledger-empty fallbacks)


def test_doc_hint_unchanged():
    s = generate_t2(13_700_004, 20, "dev", interference="s0c")
    joined = " ".join(t.text for t in s.turns)
    # doc/hint still use trained formats (scope: prefix only)
    assert ("docstring must begin" in joined) or ("type-hinted as" in joined)


def test_stale_classification_consistent():
    """cells must be computed with the SAME renderer (a superseded prefix
    whose unseen-format sentence is visible must classify stale_only)."""
    for seed in range(13_700_000, 13_700_020):
        s = generate_t2(seed, 20, "dev", interference="s0c")
        for o in s.opportunities:
            if o.obligation_id != "prefix" or o.cell != "stale_only":
                continue
            p = prompt_at(s, o.turn, "dev")
            assert any(SENT_UNSEEN_FMT["prefix"].format(v=v) in p for v in o.superseded), (seed, o.turn)


def test_s0_bit_identical_regression():
    a = generate_t2(9, 20, "dev", interference="s0")
    b = generate_t2(9, 20, "dev", interference="s0")
    assert [t.text for t in a.turns] == [t.text for t in b.turns]
