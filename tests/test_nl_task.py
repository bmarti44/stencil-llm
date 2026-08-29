# ruff: noqa: E501
"""Verifications 6-8 for the NL task (GPT2-PLAN.md), TDD-first."""
from pathlib import Path

import pytest
import torch

from stencil.determinism import named_generator
from stencil.nl_task import (
    ANSWER_WORDS,
    BPE,
    DEMO_PAIRS,
    SLOT_WORDS,
    generate,
)

TOK = Path(__file__).resolve().parent.parent / "models" / "tokenizer"
needs_tok = pytest.mark.skipif(not (TOK / "vocab.json").exists(), reason="run convert_gpt2.py")


@needs_tok
def test_vocab_single_token() -> None:
    """V8: every pool word must round-trip as exactly one token with leading space."""
    bpe = BPE()
    offenders = [
        w
        for w in SLOT_WORDS + ANSWER_WORDS + [w for p in DEMO_PAIRS for w in p]
        if len(bpe.encode(" " + w)) != 1
    ]
    assert offenders == [], f"multi-token pool words: {offenders}"
    assert len(set(ANSWER_WORDS)) == 16 and len(set(SLOT_WORDS)) == 4


@needs_tok
def test_known_encoding_parity() -> None:
    """Our BPE matches the reference encoding captured at conversion time."""
    bpe = BPE()
    assert bpe.encode("The capital of France is") == [464, 3139, 286, 4881, 318]
    assert bpe.encode('New rule: reply to "cat" with "dog".')[:3] == bpe.encode("New rule:")[:3]


@needs_tok
def test_generation_deterministic_and_shaped() -> None:
    a, b = generate(5), generate(5)
    assert a.tokens == b.tokens and a.targets == b.targets
    assert len(a.tokens) == 1024
    assert 1 <= len(a.query_positions) <= 4
    c = generate(6)
    assert c.tokens != a.tokens


@needs_tok
def test_answer_never_in_input() -> None:
    """V-leakage: the answer token never follows the '->' in the input."""
    bpe = BPE()
    nl = bpe.encode("\n")[0]
    checked = 0
    for seed in range(8):
        s = generate(seed, bpe=bpe)
        for p in s.query_positions:
            assert s.targets[p] >= 0
            if p + 1 < len(s.tokens):
                assert s.tokens[p + 1] in (nl,), "answer written into input"
                assert s.tokens[p + 1] != s.targets[p]
            checked += 1
    assert checked >= 24


@needs_tok
def test_fixture_hand_derived_first_rule() -> None:
    """V6: independently replay seed 0's first draws per the spec and assert
    the generator's opening rule statement token-for-token."""
    bpe = BPE()
    g_c = named_generator(0, "cues")
    a0 = int(torch.randint(0, 16, (1,), generator=g_c))
    expected_answer = ANSWER_WORDS[a0]
    expected = bpe.encode(f'New rule: reply to "cat" with "{expected_answer}". ')
    s = generate(0, bpe=bpe)
    assert s.tokens[: len(expected)] == expected
    assert s.rule_statement_pos[0] == 0


@needs_tok
def test_distances_span_the_receptive_field() -> None:
    """The benchmark only means something if some queries sit beyond 756."""
    beyond = within = 0
    for seed in range(8):
        s = generate(seed)
        for p, slot in zip(s.query_positions, s.query_slots, strict=True):
            d = p - s.rule_statement_pos[slot]
            assert d > 0
            if d > 756:
                beyond += 1
            else:
                within += 1
    assert beyond >= 8, f"too few beyond-window queries ({beyond})"
    assert within >= 1, "no within-reach control queries at all"


@needs_tok
def test_demo_answers_supervised() -> None:
    """Iteration 2: the demo worked examples carry loss (format supervision).
    Exactly two extra target positions beyond the queries; each is a demo
    answer and IS written into the input (it is a worked example)."""
    bpe = BPE()
    demo_ids = {bpe.encode(" " + a)[0] for _, a in DEMO_PAIRS}
    for seed in range(4):
        s = generate(seed, bpe=bpe)
        extra = [
            p for p, t in enumerate(s.targets)
            if t >= 0 and p not in s.query_positions
        ]
        assert len(extra) == 2, f"expected 2 demo targets, got {len(extra)}"
        for p in extra:
            assert s.targets[p] in demo_ids
            assert s.tokens[p + 1] == s.targets[p], "demo answer must be written"


@needs_tok
def test_near_family_in_window() -> None:
    """Iteration 2 curriculum: 'near' places every rule close to its query."""
    for seed in range(4):
        s = generate(seed, family="near")
        assert len(s.tokens) == 1024
        assert 1 <= len(s.query_positions) <= 4
        for p, slot in zip(s.query_positions, s.query_slots, strict=True):
            d = p - s.rule_statement_pos[slot]
            assert 0 < d <= 250, f"near-family distance {d} not near"
    a, b = generate(3, family="near"), generate(3, family="near")
    assert a.tokens == b.tokens and a.targets == b.targets


@needs_tok
def test_batch_mixed_families() -> None:
    """Iteration 3 replay: batch() accepts per-item families."""
    from stencil.nl_task import batch
    toks, tgts, seqs = batch([11, 12, 13, 14], family=["near", "train", "near", "train"])
    assert toks.shape[0] == 4
    for idx in (0, 2):
        s = seqs[idx]
        for p, slot in zip(s.query_positions, s.query_slots, strict=True):
            assert p - s.rule_statement_pos[slot] <= 250
    long_ds = [
        p - seqs[1].rule_statement_pos[slot]
        for p, slot in zip(seqs[1].query_positions, seqs[1].query_slots, strict=True)
    ]
    assert max(long_ds) > 250


@needs_tok
def test_rule_events_recorded() -> None:
    """v6: every slot rule/update statement records (last_pos, slot, answer)
    for capture supervision; positions sit inside a recorded span."""
    for seed in (0, 3):
        for fam in ("train", "near"):
            s = generate(seed, family=fam)
            assert len(s.rule_events) >= 4
            for pos, slot, ans in s.rule_events:
                assert 0 <= slot < 4
                assert ans in ANSWER_WORDS
                assert any(lo <= pos < hi for lo, hi in s.rule_spans)


@needs_tok
def test_derived_family() -> None:
    """Experiment C: derived rules state a CLUE, never the answer word. The
    wire must store a conclusion, not a copy."""
    from stencil.nl_task import generate
    bpe = BPE()
    for seed in (0, 5):
        for fam in ("derived", "near_derived"):
            s = generate(seed, family=fam, bpe=bpe)
            assert len(s.tokens) == 1024
            assert 1 <= len(s.query_positions) <= 4
            for p, _slot, ans in zip(s.query_positions, s.query_slots, s.active_answer, strict=True):
                ans_id = bpe.encode(" " + ans)[0]
                assert s.targets[p] == ans_id
                # the answer token must appear NOWHERE in any statement span
                for lo, hi in s.rule_spans:
                    assert ans_id not in s.tokens[lo:hi], f"answer '{ans}' leaked into statement"
            if fam == "near_derived":
                for p, slot in zip(s.query_positions, s.query_slots, strict=True):
                    assert 0 < p - s.rule_statement_pos[slot] <= 250
    a, b = generate(3, family="derived"), generate(3, family="derived")
    assert a.tokens == b.tokens
