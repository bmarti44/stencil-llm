"""CPU tests of the session core: off switch, budget, eviction, isolation."""

from pathlib import Path

import pytest
from stencil_focus import Session, chat_prompt, pack_newest_first, render_reminder

TOK = Path(__file__).resolve().parents[3] / "models" / "qwen3-1.7b-hf"


@pytest.fixture(scope="module")
def tokenizer():
    if not TOK.exists():
        pytest.skip("local Qwen3 tokenizer not present")
    from transformers import AutoTokenizer

    return AutoTokenizer.from_pretrained(str(TOK))


def _fill(session, n=60):
    for i in range(n):
        session.add_message(
            "user", f"Rule number {i}: always use snake_case for item {i}."
        )
        session.add_message("assistant", f"Understood, item {i}.")


def test_off_switch_is_plain_window(tokenizer):
    on = Session(tokenizer, focus=True, window=400)
    off = Session(tokenizer, focus=False, window=400)
    _fill(on)
    _fill(off)
    p_on = on.build_prompt("Write the function.")
    p_off = off.build_prompt("Write the function.")
    assert p_off.startswith("<|im_start|>user\n") and p_off.endswith(
        chat_prompt("")[-len("<|im_start|>assistant\n<think>\n\n</think>\n\n") :]
    )
    assert "Earlier instructions still in force:" not in p_off
    assert "Earlier instructions still in force:" in p_on
    assert off.last["prompt_tokens"] <= 400
    # same complete token count (retokenisation at the cut may move it by <= 2)
    assert abs(on.last["prompt_tokens"] - off.last["prompt_tokens"]) <= 2
    assert on.last["thread_tokens_kept"] < off.last["thread_tokens_kept"]


def test_reminder_only_restates_truncated_sentences(tokenizer):
    s = Session(tokenizer, focus=True, window=400)
    _fill(s)
    s.build_prompt("Write the function.")
    kept_text = s.last["thread_text_kept"]
    for line in s.last["reminder"].splitlines()[1:]:
        assert line.startswith("- ")
        assert line[2:] not in kept_text
    assert s.last["reminder_tokens"] <= 256


def test_budget_includes_header(tokenizer):
    enc = lambda t: tokenizer(t, add_special_tokens=False)["input_ids"]  # noqa: E731
    ordered = [f"Sentence {i} is here." for i in range(100)]
    kept, used = pack_newest_first(ordered, enc, budget=40)
    assert used <= 40 and kept == ordered[-len(kept) :]
    assert len(enc(render_reminder(kept))) == used


def test_sessions_are_isolated(tokenizer):
    a = Session(tokenizer, window=400)
    b = Session(tokenizer, window=400)
    _fill(a)
    assert b.messages == [] and b.thread() == ""
    a.reset()
    assert a.messages == [] and a.last is None


def test_no_instruction_when_nothing_truncated(tokenizer):
    s = Session(tokenizer, focus=True, window=3584)
    s.add_message("user", "Use tabs.")
    s.build_prompt("Write it.")
    assert s.last["reminder"] == "" and s.last["evicted_sentences"] == 0
