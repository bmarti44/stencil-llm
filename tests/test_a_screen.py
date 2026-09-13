"""Self-checks for six-family candidate-A sessions (registration §5, §6, §10).

For every authored session: gold reaches every suite at both checkpoints; cross-state
gold fails the applicable target-contract suite at each checkpoint; the unmodified
target fails the functional suite; and, with the shipping tokenizer, the packing policy
keeps every rule turn while dropping at least one prefix turn before request 1 and at
least one more before request 2.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from stencil import a_screen as A
from stencil.a_screen_pool import available_slots, load

HUB = Path("deploy/stencil_focus/build/hub-4b")

SLOTS = available_slots()


def _pairs():
    out = []
    for slot in SLOTS:
        out.append(pytest.param(slot, id=slot))
    return out


@pytest.fixture(scope="module")
def counter():
    try:
        from transformers import AutoTokenizer
    except Exception:  # pragma: no cover
        pytest.skip("transformers unavailable")
    if not HUB.exists():
        pytest.skip("shipping tokenizer not present")
    tok = AutoTokenizer.from_pretrained(str(HUB), trust_remote_code=True)

    return A.make_counter(tok)


@pytest.mark.parametrize("slot", _pairs())
def test_gold_path_reaches_every_suite(slot):
    s = load(slot)
    f1 = A.gold_files(s, 1)
    r1 = A.score_checkpoint(s, 1, f1)
    assert r1["all"], (slot, 1, r1)
    f2 = A.gold_files(s, 2)
    r2 = A.score_checkpoint(s, 2, f2)
    assert r2["all"], (slot, 2, r2)


@pytest.mark.parametrize("slot", _pairs())
def test_cross_state_gold_fails_contract(slot):
    s = load(slot)
    for k in (1, 2):
        state = s.state_at[k - 1]
        other = s.other(state)
        files = A.gold_files(s, k, state=other)
        r = s.requests[k - 1]
        ok, _ = A.run_tests(files, r.contract_tests[state])
        assert not ok, (slot, k, "cross-state gold reached the contract suite")
        # and the cross-state gold is itself executable under its own state
        ok_f, msg = A.run_tests(files, r.functional_tests)
        assert ok_f, (slot, k, "cross-state gold not functional", msg)
        ok_c, _ = A.run_tests(files, r.contract_tests[other])
        assert ok_c, (slot, k, "cross-state gold fails its own contract suite")


@pytest.mark.parametrize("slot", _pairs())
def test_unmodified_target_fails_functional(slot):
    s = load(slot)
    ok, _ = A.run_tests(dict(s.files), s.requests[0].functional_tests)
    assert not ok, (slot, "request 1 already satisfied")
    f1 = A.gold_files(s, 1)
    ok, _ = A.run_tests(f1, s.requests[1].functional_tests)
    assert not ok, (slot, "request 2 already satisfied by checkpoint-1 gold")


@pytest.mark.parametrize("slot", _pairs())
def test_packing_keeps_rule_turns_and_compacts(slot, counter):
    s = load(slot)
    files0 = dict(s.files)
    m1 = A.session_messages(s, 1, files0)
    kept1, idx1 = A.pack(m1, counter)
    assert counter(kept1) <= A.PROMPT_BUDGET
    surv1 = A.surviving_prefix_turns(idx1)
    assert set(s.rule_turns) <= surv1, (slot, 1, sorted(surv1))
    assert len(surv1) < 16, (slot, "no compaction before request 1")
    f1 = A.gold_files(s, 1)
    m2 = A.session_messages(s, 2, f1, A.gold_reply(s, 1), {s.requests[0].target})
    kept2, idx2 = A.pack(m2, counter)
    assert counter(kept2) <= A.PROMPT_BUDGET
    surv2 = A.surviving_prefix_turns(idx2)
    assert set(s.rule_turns) <= surv2, (slot, 2, sorted(surv2))
    assert len(surv2) < len(surv1), (slot, "no further compaction before request 2")
    # the event message and both live requests are always present
    assert idx2[-1] == len(m2) - 1 and (len(m2) - 2) in idx2 and (len(m2) - 4) in idx2


def test_pack_never_drops_system_or_final():
    msgs = [{"role": "system", "content": "s"}] + [
        {"role": "user", "content": "x" * 50} for _ in range(5)
    ]
    kept, idx = A.pack(msgs, lambda m: sum(len(x["content"]) for x in m), budget=120)
    assert idx[0] == 0 and idx[-1] == 5 and len(kept) == 3
