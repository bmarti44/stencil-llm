# ruff: noqa: E501
"""CONTRACT v3 generator unit tests."""
from stencil.t2_sessions import generate_t2, prompt_at


def test_deterministic():
    a, b = generate_t2(1, 20), generate_t2(1, 20)
    assert [t.text for t in a.turns] == [t.text for t in b.turns]
    assert [o.opportunity_id for o in a.opportunities] == [o.opportunity_id for o in b.opportunities]


def test_opportunity_cells_match_history():
    for seed in range(20):
        s = generate_t2(seed, 40)
        for o in s.opportunities:
            if o.moment_class == "comment":
                continue
            led = s.ledger_at[o.turn]
            sup = s.superseded_at[o.turn]
            if o.cell == "active":
                assert o.obligation_id in led and o.expected == led[o.obligation_id]
            elif o.cell == "stale_only":
                assert o.obligation_id not in led and sup[o.obligation_id]
                assert o.superseded == sup[o.obligation_id]
            elif o.cell in ("cleared", "absent"):
                assert o.obligation_id not in led


def test_counterfactual_coverage():
    cells = {"absent": 0, "cleared": 0, "stale_only": 0}
    for seed in range(48):
        s = generate_t2(seed, 20)
        for o in s.opportunities:
            if o.cell in cells:
                cells[o.cell] += 1
    assert all(v >= 48 for v in cells.values()), cells


def test_ledger_survives_compaction():
    s = generate_t2(3, 40)
    late = [w for w in s.work_turns if w > s.compaction_turns[0]]
    assert late, "no post-compaction work turn"
    for w in late:
        p = prompt_at(s, w)
        assert p.startswith("Current coding standards (authoritative):")
        assert s.turns[0].text not in p


def test_held_out_only_in_val_final():
    dev = generate_t2(7, 40, split="dev")
    val = generate_t2(7, 40, split="val")
    assert not dev.held_out
    assert val.held_out.get("comment")
    assert any(o.moment_class == "comment" for o in val.opportunities)
