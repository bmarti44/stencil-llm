# ruff: noqa: E501
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
from stencil.a_screen_pool import available_slots
from stencil.a_screen_pool import load as load_screen
from stencil.a_train_pool import make_session, train_sessions

HUB = Path("deploy/stencil_focus/build/hub-4b")

SLOTS = available_slots()
# every 48th generated TRAIN session (12 of 576); scripts/a_train_build.py checks all
TRAIN_KEYS = [
    (s.target_family, s.support_family, s.lifecycle, int(s.id.rsplit("-", 1)[1]))
    for s in train_sessions()[::48]
]


def load(slot):
    if isinstance(slot, tuple):
        s = make_session(*slot)
        s.validate()
        return s
    return load_screen(slot)


def _pairs():
    out = [pytest.param(slot, id=slot) for slot in SLOTS]
    out += [
        pytest.param(k, id=f"T-{k[0][:3]}-{k[1][:3]}-{k[2][:3]}-{k[3]}")
        for k in TRAIN_KEYS
    ]
    return out


@pytest.fixture(scope="module")
def tok():
    try:
        from transformers import AutoTokenizer
    except Exception:  # pragma: no cover
        pytest.skip("transformers unavailable")
    if not HUB.exists():
        pytest.skip("shipping tokenizer not present")
    return AutoTokenizer.from_pretrained(str(HUB), trust_remote_code=True)


@pytest.fixture(scope="module")
def counter(tok):
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
def test_packing_keeps_rule_turns_and_compacts(slot, counter, tok):
    s = load(slot)
    files0 = dict(s.files)
    m1 = A.session_messages(s, 1, files0)
    kept1, idx1 = A.pack(m1, counter)
    assert counter(kept1) <= A.PROMPT_BUDGET
    surv1 = A.surviving_prefix_turns(idx1)
    assert set(s.rule_turns) <= surv1, (slot, 1, sorted(surv1))
    assert len(surv1) < 16, (slot, "no compaction before request 1")
    f1 = A.gold_files(s, 1)
    # gold reply: rule turns survive, more compaction than at request 1
    m2 = A.session_messages(s, 2, files0, A.gold_reply(s, 1), f1)
    kept2, idx2 = A.pack(m2, counter, drop_first=A.drop_first_order(2))
    assert counter(kept2) <= A.PROMPT_BUDGET
    surv2 = A.surviving_prefix_turns(idx2)
    assert set(s.rule_turns) <= surv2, (slot, 2, sorted(surv2))
    dropped1 = set(range(len(m1))) - set(idx1)
    dropped2 = set(range(len(m2))) - set(idx2)
    assert len(dropped2) > len(dropped1), (slot, "no further compaction at request 2")
    assert 17 in dropped2, (slot, "superseded request not evicted first")
    assert A.required_indices(s, 2) <= set(idx2), (slot, "required message dropped")
    # the event message and the live request are always present
    assert idx2[-1] == len(m2) - 1 and (len(m2) - 2) in idx2
    # the request-1 message renders the files as that request saw them (Astra F2)
    assert m2[17]["content"] == A.render_request_message(s.requests[0], files0)
    # Astra F1: a reply at the permitted maximum length must still leave every rule
    # turn, the lifecycle event and the live request in the window
    long_reply = A.synthetic_reply(tok, A.MAX_NEW_TOKENS, s.requests[0], s.state_at[0])
    n_reply = len(tok(long_reply, add_special_tokens=False)["input_ids"])
    assert n_reply >= A.MAX_NEW_TOKENS
    files1_long, reason = A.apply_reply(files0, s.requests[0], long_reply)
    assert reason == "applied"
    m3 = A.session_messages(s, 2, files0, long_reply, files1_long)
    kept3, idx3 = A.pack(m3, counter, drop_first=A.drop_first_order(2))
    assert counter(kept3) <= A.PROMPT_BUDGET
    assert A.required_indices(s, 2) <= set(idx3), (
        slot,
        "max-length reply evicts required messages",
        sorted(A.surviving_prefix_turns(idx3)),
    )
    # the live request carries the current content of the changed file
    assert files1_long[s.requests[0].target].strip() in m3[-1]["content"]
    # a reply that was not applied leaves the repository as request 1 showed it
    m4 = A.session_messages(s, 2, files0, "no code here", files0)
    assert "unchanged from the earlier request" in m4[-1]["content"]


@pytest.mark.parametrize("slot", _pairs())
def test_protected_suite_guards_the_first_operation(slot):
    """Astra F7: the checkpoint-2 PROTECTED suite re-runs request 1's functional,
    contract (state at checkpoint 1) and support tests; the request-1 target reverted
    to its ORIGINAL content (first operation removed) must fail it."""
    s = load(slot)
    f2 = A.gold_files(s, 2)
    r1 = s.requests[0]
    # (a) the first operation rolled back: the protected suite must fail
    reverted = {**f2, r1.target: s.files[r1.target]}
    res = A.score_checkpoint(s, 2, reverted)
    assert not res["protected"], (
        slot,
        "first operation removed but protected suite passed",
    )
    # (b) a pre-existing public method renamed: api_preserved must fail (Astra F7)
    before = sorted(
        n.split(".")[-1] for n in A.public_api(s.files[r1.target]) if "." in n
    )
    if before:
        victim = before[0]
        renamed = f2[r1.target].replace(f"def {victim}(", f"def {victim}_renamed(", 1)
        assert renamed != f2[r1.target]
        res2 = A.score_checkpoint(s, 2, {**f2, r1.target: renamed})
        assert not res2["api_preserved"], (
            slot,
            "rename of an existing method accepted",
        )
        assert not res2["all"], (slot, "renamed existing method still scored J")


def test_pack_never_drops_system_or_final():
    msgs = [{"role": "system", "content": "s"}] + [
        {"role": "user", "content": "x" * 50} for _ in range(5)
    ]
    kept, idx = A.pack(msgs, lambda m: sum(len(x["content"]) for x in m), budget=120)
    assert idx[0] == 0 and idx[-1] == 5 and len(kept) == 3
