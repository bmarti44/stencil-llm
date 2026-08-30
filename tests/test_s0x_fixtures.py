# ruff: noqa: E501
"""G0 fixture-generator extension (interference="s0x") — red-first.

Registered spec (PRESS-PLAN G0 amendments): each fixture session carries
one deterministic inactive TARGET type with an S0-style format-identical
same-type non-live note inside the surviving window of the final work
turn, outside the authoritative ledger. Target type balanced across
prefix/doc/hint by seed; intended cell alternates cleared/stale_only.
Truly-absent-with-note is not constructible under the base plan (every
type gets set) — disclosed in the plan; cells here are cleared/stale.
"""
from stencil.t2_sessions import SENT, generate_t2, prompt_at


def _last_work(s):
    return s.work_turns[-1]


def test_s0x_deterministic_and_targets_balanced():
    a = generate_t2(5, 20, "dev", interference="s0x")
    b = generate_t2(5, 20, "dev", interference="s0x")
    assert a.held_out["s0x"] == b.held_out["s0x"]
    assert [t.text for t in a.turns] == [t.text for t in b.turns]
    types = {generate_t2(s, 20, "dev", interference="s0x").held_out["s0x"]["type"] for s in range(3)}
    assert types == {"prefix", "doc", "hint"}


def test_s0x_target_inactive_with_visible_note():
    for seed in range(12):
        s = generate_t2(seed, 20, "dev", interference="s0x")
        info = s.held_out["s0x"]
        ty, v = info["type"], info["value"]
        wt = _last_work(s)
        # inactive at the targeted work turn
        assert ty not in s.ledger_at[wt], (seed, ty)
        # the injected note's exact sentence is in the surviving window
        assert SENT[ty].format(v=v) in prompt_at(s, wt, "dev"), (seed, ty, v)
        # and it is NOT the authoritative ledger (which has no live entry of ty)
        led_line = "Current coding standards (authoritative):"
        prompt = prompt_at(s, wt, "dev")
        led_block = prompt.split("\n\n")[0]
        assert led_block.startswith(led_line) and SENT[ty].format(v=v) not in led_block


def test_s0x_cell_is_cleared_or_stale():
    cells = set()
    for seed in range(12):
        s = generate_t2(seed, 20, "dev", interference="s0x")
        ty = s.held_out["s0x"]["type"]
        wt = _last_work(s)
        cell = next(o.cell for o in s.opportunities if o.turn == wt and o.obligation_id == ty)
        assert cell in ("cleared", "stale_only"), (seed, ty, cell)
        cells.add(cell)
    assert cells == {"cleared", "stale_only"}  # both intents realized across 12 seeds


def test_s0x_note_value_is_non_live_everywhere():
    for seed in range(8):
        s = generate_t2(seed, 20, "dev", interference="s0x")
        info = s.held_out["s0x"]
        wt = _last_work(s)
        assert s.ledger_at[wt].get(info["type"]) != info["value"]


def test_s0_sessions_unchanged_by_extension_code():
    """The s0 distribution must be bit-identical to before (dev/val stay on
    the unextended generator)."""
    s = generate_t2(3, 20, "dev", interference="s0")
    assert "s0x" not in s.held_out
    texts = [t.text for t in s.turns]
    s2 = generate_t2(3, 20, "dev", interference="s0")
    assert texts == [t.text for t in s2.turns]
