# ruff: noqa: E501
"""Ledger construction on rendered contexts (CPU; needs only the tokenizer)."""
from __future__ import annotations

import pytest
import torch
from stencil_wave.attention import WAVE_LAYERS, StepBias
from stencil_wave.controller import N_PARAMS, WaveController
from stencil_wave.ledger import (
    Entry,
    build_ledger,
    render_text_ledger,
    select,
    user_turns,
)
from stencil_wave.model import TMPL

THREE_TURNS = (
    "<|im_start|>user\nWrite a short note about autumn. Do not use any commas in your response.<|im_end|>\n"
    "<|im_start|>assistant\nAutumn arrives with cool air and golden leaves.<|im_end|>\n"
    "<|im_start|>user\nInclude the keyword 'harvest' at least twice. Make it about winter.<|im_end|>\n"
    "<|im_start|>assistant\nWinter comes with snow and the harvest is stored. The harvest keeps us fed.<|im_end|>\n"
    "<|im_start|>user\nNow one about spring.<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\n"
)


def test_user_turns_finds_every_user_body():
    bodies = [THREE_TURNS[a:b] for a, b in user_turns(THREE_TURNS)]
    assert bodies[0].startswith("Write a short note") and bodies[-1] == "Now one about spring."
    assert len(bodies) == 3


def test_user_turns_unterminated_raises():
    with pytest.raises(ValueError):
        user_turns("<|im_start|>user\nno end")


def test_build_ledger_spans_decode_to_the_instruction(hf_tokenizer):
    enc = hf_tokenizer(THREE_TURNS, return_offsets_mapping=True)
    entries = build_ledger(enc["offset_mapping"], THREE_TURNS)
    texts = [e.text for e in entries]
    assert "Do not use any commas in your response." in texts
    assert "Include the keyword 'harvest' at least twice." in texts
    assert all(e.turn_introduced in (1, 2) for e in entries), texts  # the spring turn holds no instruction
    for e in entries:
        a, b = e.span
        decoded = hf_tokenizer.decode(enc["input_ids"][a:b])
        assert e.text in decoded or decoded.strip() in e.text, (e.text, decoded)
        assert e.columns == tuple(range(a, b))
        # never leaks past the enclosing user message
        assert "<|im_end|>" not in decoded and "assistant" not in decoded


def test_instruction_echo_in_assistant_turn_is_not_an_entry(hf_tokenizer):
    ctx = ("<|im_start|>user\nWrite about rain.<|im_end|>\n"
           "<|im_start|>assistant\nDo not use any commas in your response.<|im_end|>\n"
           "<|im_start|>user\nContinue.<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\n")
    enc = hf_tokenizer(ctx, return_offsets_mapping=True)
    assert build_ledger(enc["offset_mapping"], ctx) == []


def test_single_turn_template_matches_pinned_string(hf_tokenizer):
    p = "Answer with fewer than 40 words. What is a linked list?"
    rendered = hf_tokenizer.apply_chat_template([{"role": "user", "content": p}], tokenize=False,
                                                add_generation_prompt=True, enable_thinking=False)
    assert rendered == TMPL.format(p=p)


def test_select_ranks_by_controller_score_with_ledger_order_tiebreak():
    torch.manual_seed(0)
    ctrl = WaveController()
    assert sum(p.numel() for p in ctrl.parameters()) == N_PARAMS
    keys = [torch.randn(2048) for _ in range(4)]
    entries = [Entry(f"e{i}", (i, i + 1), 1, (i,), key=k) for i, k in enumerate(keys)]
    q = torch.randn(2048)
    chosen = select(entries, q, ctrl, top_k=2)
    scores = ctrl.scores(q, torch.stack(keys)).tolist()
    want = sorted(range(4), key=lambda i: (-scores[i], i))[:2]
    assert [entries[i] for i in want] == chosen
    assert all(e.score is not None for e in entries)
    dup = [Entry("same", (0, 1), 1, (0,), key=keys[0]), Entry("same2", (1, 2), 1, (1,), key=keys[0])]
    assert select(dup, q, ctrl, top_k=1)[0] is dup[0]


def test_packaged_controller_loads_with_registered_shapes():
    ctrl = WaveController.load()
    assert tuple(ctrl.W_q.weight.shape) == (64, 2048) and tuple(ctrl.W_k.weight.shape) == (64, 2048)
    assert sum(p.numel() for p in ctrl.parameters()) == N_PARAMS


def test_step_bias_rows_are_last_row_only_and_sum_overlaps():
    b = StepBias(3.0)
    b.groups = [(2, 3, 4), (4, 5)]
    rows = b.rows(20, 7, 12, "cpu")
    assert rows.shape == (7, 12) and rows[:-1].abs().sum() == 0
    assert rows[-1].tolist() == [0, 0, 3, 3, 6, 3, 0, 0, 0, 0, 0, 0]
    assert b.rows(19, 7, 12, "cpu") is None and b.rows(27, 1, 12, "cpu").shape == (1, 12)
    assert StepBias(0.0).rows(20, 1, 5, "cpu") is None
    assert tuple(WAVE_LAYERS) == tuple(range(20, 28))
    b.groups = [(40,)]
    with pytest.raises(ValueError):
        b.rows(20, 1, 12, "cpu")


def test_render_text_ledger_round_trip():
    entries = [Entry("Do not use commas.", (0, 1), 1, (0,)), Entry("Be brief.", (1, 2), 1, (1,))]
    text = render_text_ledger(entries)
    assert text.splitlines()[1:] == ["- Do not use commas.", "- Be brief."]
    assert render_text_ledger([]) == ""
