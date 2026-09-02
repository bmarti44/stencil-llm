# ruff: noqa: E501
"""LEDGER component B (LEDGER-PLAN.md) — red/green TDD, no vacuous tests.

Every span assertion decodes the tokens back to text and compares against
the instruction sentence; every selection assertion checks object identity
against the input list; the harm guarantee is bitwise against the
independent base generator (modelled on
tests/test_obligation_gate.py::test_generate_gated_never_fires_is_bitwise_base).
"""
import sys
from pathlib import Path

import pytest
import torch

ROOT = Path(__file__).resolve().parent.parent
TOK_PATH = ROOT / "models" / "qwen3-1.7b-hf" / "tokenizer.json"
gpu = pytest.mark.skipif(not torch.cuda.is_available(), reason="needs GPU")


@pytest.fixture(scope="module")
def tok():
    if not TOK_PATH.exists():
        pytest.skip("tokenizer not present")
    from tokenizers import Tokenizer
    return Tokenizer.from_file(str(TOK_PATH))


# A 3-turn Multi-IF-shaped conversation: narrative mixed with instructions.
PROMPTS = [
    "Write a short note about rain. It fell all night on the tin roof. "
    "Your response should include the keywords lantern and gravel.",
    "Now make it about snow instead. Do not use any commas in your response.",
    "Rewrite it once more as a poem. Wrap your entire response in double quotation marks.",
]
RESPONSES = ["Rain drummed the roof; a lantern swung over the gravel.", "Snow fell softly on the roof"]
INSTRUCTIONS = {
    "Your response should include the keywords lantern and gravel.": 1,
    "Do not use any commas in your response.": 2,
    "Wrap your entire response in double quotation marks.": 3,
}


def stub_salience(sentence: str) -> bool:
    return sentence in INSTRUCTIONS


def three_turn_context():
    from stencil.e2_multiif import build_replay_context
    return build_replay_context(PROMPTS, RESPONSES, turn=3, positive_control=False)


def test_segment_sentences_splits_on_terminators_and_newlines():
    from stencil.ledger import segment_sentences
    got = segment_sentences('First one. Second "quoted." Third!\nFourth line? fifth')
    assert got == ["First one.", 'Second "quoted."', "Third!", "Fourth line?", "fifth"]
    assert segment_sentences("") == []


def test_build_ledger_three_turn_fixture_spans_decode_to_instruction(tok):
    from stencil.e2 import user_turn_span_records
    from stencil.ledger import build_ledger
    context = three_turn_context()
    entries = build_ledger(tok, context, salience=stub_salience)
    assert [e.text for e in entries] == list(INSTRUCTIONS)
    assert [e.turn_introduced for e in entries] == [1, 2, 3]
    assert all(e.status == "unknown" and e.key is None and e.provenance == "salience" for e in entries)
    ids = tok.encode(context).ids
    turns = {r["origin_turn"]: r["span"] for r in user_turn_span_records(tok, context)}
    for e in entries:
        a, b = e.span
        assert 0 <= a < b <= len(ids)
        decoded = tok.decode(ids[a:b])
        assert decoded.strip() == e.text, decoded
        for bleed in ("<|im_end|>", "<|im_start|>", "assistant", "user\n"):
            assert bleed not in decoded
        ta, tb = turns[e.turn_introduced]
        assert ta <= a and b <= tb  # inside the enclosing user message


def test_build_ledger_with_real_salience_module_admits_only_instructions(tok):
    """Integration with the REAL component A: no stub, no explicit classifier."""
    pytest.importorskip("stencil.salience")
    from stencil.ledger import build_ledger, is_automatic, resolve_salience
    sal = resolve_salience()
    assert sal.provenance == "salience" and sal.note == "", sal.note
    context = three_turn_context()
    entries = build_ledger(tok, context)
    assert [e.text for e in entries] == list(INSTRUCTIONS)
    assert [e.turn_introduced for e in entries] == [1, 2, 3]
    assert is_automatic(entries) and {e.provenance for e in entries} == {"salience"}
    ids = tok.encode(context).ids
    for e in entries:
        a, b = e.span
        assert tok.decode(ids[a:b]).strip() == e.text


def test_build_ledger_falls_back_to_labelled_heuristic_when_salience_missing(tok, monkeypatch):
    from stencil.ledger import build_ledger, is_automatic, resolve_salience
    monkeypatch.setitem(sys.modules, "stencil.salience", None)  # import raises ImportError
    sal = resolve_salience()
    assert sal.provenance == "heuristic" and "unavailable" in sal.note
    entries = build_ledger(tok, three_turn_context())
    assert entries, "heuristic must still find the instruction sentences"
    assert {e.provenance for e in entries} == {"heuristic"}
    assert not is_automatic(entries)
    assert "Your response should include the keywords lantern and gravel." in [e.text for e in entries]
    assert "It fell all night on the tin roof." not in [e.text for e in entries]
    # and an entry from the salience path counts as automatic
    entries_auto = build_ledger(tok, three_turn_context(), salience=stub_salience)
    assert is_automatic(entries_auto) and entries_auto


def test_untrained_real_salience_model_falls_back_labelled(tok, monkeypatch):
    """An all-zero model would admit EVERY sentence (sigmoid(0) >= 0.5): the
    over-inclusive ledger that killed the raw-span version. Never trust it."""
    salience = pytest.importorskip("stencil.salience")
    import numpy as np

    from stencil.ledger import build_ledger, is_automatic, resolve_salience
    zero = salience.Model(np.zeros_like(salience.DEFAULT_MODEL.w), 0.0, list(salience.DEFAULT_MODEL.feature_names))
    assert not salience.is_trained(zero)
    monkeypatch.setattr(salience, "DEFAULT_MODEL", zero)
    assert not salience.is_trained()
    sal = resolve_salience()
    assert sal.provenance == "heuristic" and "untrained" in sal.note
    entries = build_ledger(tok, three_turn_context())
    assert entries and {e.provenance for e in entries} == {"heuristic"} and not is_automatic(entries)
    assert "It fell all night on the tin roof." not in [e.text for e in entries]


def test_real_salience_segmenter_keeps_abbreviation_sentence_whole(tok):
    salience = pytest.importorskip("stencil.salience")
    from stencil.e2_multiif import build_replay_context
    from stencil.ledger import build_ledger, resolve_salience
    assert resolve_salience().segment is salience.split_sentences
    whole = "The result must contain a title wrapped in double angular brackets, i.e. <<title>>."
    context = build_replay_context(["Write a poem about dawn. " + whole + " Keep it short."], [], turn=1, positive_control=False)
    entries = build_ledger(tok, context)
    assert [e.text for e in entries] == [whole]  # not split at "i.e."
    ids = tok.encode(context).ids
    a, b = entries[0].span
    assert tok.decode(ids[a:b]).strip() == whole and entries[0].turn_introduced == 1


def test_select_returns_top_k_entries_ranked_by_controller_score():
    import torch.nn.functional as F

    from stencil.ledger import Entry, select
    from stencil.wave import WaveController
    torch.manual_seed(0)
    ctrl = WaveController(beta_max=1.0).eval()
    keys = torch.randn(4, 2048)
    entries = [Entry(f"e{i}", (10 * i, 10 * i + 5), keys[i], 1) for i in range(4)]
    query = torch.randn(2048)
    with torch.no_grad():
        q = F.normalize(ctrl.W_q(query[None]), dim=-1)
        k = F.normalize(ctrl.W_k(keys), dim=-1)
        expect = (q @ k.T)[0].tolist()
    order = sorted(range(4), key=lambda i: (-expect[i], i))
    got = select(entries, query, ctrl, top_k=2)
    assert len(got) == 2 and all(isinstance(e, Entry) for e in got)
    assert [entries.index(e) for e in got] == order[:2]  # identity, not indices into another list
    assert got[0] is entries[order[0]]
    assert [e.text for e in select(entries, query, ctrl, top_k=9)] == [entries[i].text for i in order]
    assert select([], query, ctrl) == []
    with pytest.raises(ValueError):
        select([Entry("x", (0, 1), None, 1)], query, ctrl)


def test_render_text_ledger_round_trips_entry_texts():
    from stencil.ledger import Entry, parse_text_ledger, render_text_ledger
    entries = [Entry(t, (0, 1), None, n) for t, n in INSTRUCTIONS.items()]
    text = render_text_ledger(entries)
    assert parse_text_ledger(text) == list(INSTRUCTIONS)
    for t in INSTRUCTIONS:
        assert t in text
    assert render_text_ledger([]) == ""


def test_text_ledger_context_adds_tokens_and_neural_context_adds_zero(tok):
    from stencil.e2_multiif import OPENER
    from stencil.ledger import build_ledger, context_tokens_added, text_ledger_context
    context = three_turn_context()
    entries = build_ledger(tok, context, salience=stub_salience)
    aged = [e for e in entries if e.turn_introduced < 3]
    text_ctx = text_ledger_context(context, aged)
    assert text_ctx.endswith("<|im_end|>\n" + OPENER)  # inserted before the assistant turn
    assert text_ctx.startswith(context[: context.rfind("<|im_end|>")])
    for e in aged:
        assert text_ctx.count(e.text) == 2  # original + re-appended verbatim
    added = context_tokens_added(tok, context, text_ctx)
    assert added >= sum(len(tok.encode(e.text).ids) for e in aged) > 0
    assert context_tokens_added(tok, context, context) == 0  # the neural arm's whole claim
    assert text_ledger_context(context, []) == context


def test_paired_drop_table_and_non_inferiority_points():
    from stencil.ledger import non_inferiority_summary, paired_drop_table
    # reference right/candidate wrong = drop (n10); converse = n01
    ref = [True, True, False, True, False, True]
    cand = [True, False, True, True, False, True]
    assert paired_drop_table(ref, cand) == {"n10": 1, "n01": 1, "n": 6}
    s = non_inferiority_summary(ref * 20, cand * 20, margin_points=2.0)
    assert s["n"] == 120 and s["n10"] == 20 and s["n01"] == 20
    assert s["drop_points"] == 0.0 and s["upper_bound_points"] > 0
    assert s["non_inferior"] == (s["upper_bound_points"] < 2.0)
    with pytest.raises(ValueError):
        paired_drop_table([True], [True, False])


@pytest.fixture(scope="module")
def gpu_setup():
    if not torch.cuda.is_available():
        pytest.skip("needs GPU")
    from tokenizers import Tokenizer

    from stencil.qwen3 import Qwen3
    from stencil.wave import WaveController
    tok = Tokenizer.from_file(str(TOK_PATH))
    m = Qwen3()
    m.load_state_dict(torch.load(ROOT / "models" / "qwen3-1.7b.pt", map_location="cpu"), strict=True)
    m = m.to(torch.bfloat16).cuda().eval()
    ctrl = WaveController(beta_max=1.0).cuda()
    ctrl.load_state_dict(torch.load(ROOT / "results" / "qwen" / "b3-ce-s0.pt", map_location="cpu"))
    return m, tok, ctrl.eval()


@gpu
def test_empty_ledger_neural_arm_is_bitwise_base(gpu_setup):
    """The harm guarantee: no entries -> no hook -> bitwise the base generator."""
    from stencil.bench import TMPL, generate_cached
    from stencil.ledger import generate_sustained
    m, tok, _ = gpu_setup
    base = generate_cached(m, tok, PROMPTS[0], max_new=40)
    got = generate_sustained(m, tok, TMPL.format(p=PROMPTS[0]), select_fn=lambda q: [], max_new=40)
    assert got.text == base[0] and got.n_generated == base[1]
    assert got.spans == () and got.biased_tokens == 0


@gpu
def test_build_ledger_keys_are_pooled_h20_and_select_runs_on_gpu(gpu_setup):
    from stencil.ledger import build_ledger, generate_sustained, select
    m, tok, ctrl = gpu_setup
    context = three_turn_context()
    entries = build_ledger(tok, context, model=m, salience=stub_salience)
    ids = torch.tensor([tok.encode(context).ids], device="cuda")
    with torch.no_grad():
        _, h20 = m(ids, capture_hidden=20)
    for e in entries:
        a, b = e.span
        assert e.key.shape == (2048,)
        assert torch.equal(e.key, h20[0, a:b].float().mean(0))
    chosen = {}
    res = generate_sustained(
        m, tok, context,
        select_fn=lambda q: [e.span for e in chosen.setdefault("sel", select(entries, q, ctrl, top_k=1))],
        max_new=20)
    assert len(chosen["sel"]) == 1 and chosen["sel"][0] in entries
    assert res.spans == (chosen["sel"][0].span,) and res.biased_tokens == res.n_generated
