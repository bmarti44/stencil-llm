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
    # asymmetric cells (catch a sign inversion): candidate DROPS on 10% -> not NI at a 2-point margin
    harm = non_inferiority_summary([True] * 200, [False] * 20 + [True] * 180, margin_points=2.0)
    assert harm["n10"] == 20 and harm["n01"] == 0 and harm["drop_points"] == 10.0
    assert harm["upper_bound_points"] > 10.0 and harm["non_inferior"] is False
    # candidate IMPROVES on 10% -> bound below zero, non-inferior
    gain = non_inferiority_summary([False] * 20 + [True] * 180, [True] * 200, margin_points=2.0)
    assert gain["n10"] == 0 and gain["n01"] == 20 and gain["drop_points"] == -10.0
    assert gain["upper_bound_points"] < 0.0 and gain["non_inferior"] is True
    assert harm["upper_bound_points"] != -gain["upper_bound_points"]  # Tango is not symmetric
    with pytest.raises(ValueError):
        paired_drop_table([True], [True, False])


# ---- sol's verification (results/ledger-verify-sol.md, finding 3): the runner's
# segmenter path and the conversation-769 crash.

CONV_769_TURN1 = (
    "Create a slogan for my company and wrap your entire response with double quotation marks. "
    "My company's name is Color Paper. We produce paper towls. We focus on producing eye-catching, "
    "colorful paper towls. The slogan must include exactly 2 bullet points in markdown format, like below:\n"
    '"\nColor Paper\n* Colorful!\n* Eye-catching!\n"'
)


def test_segment_char_spans_survives_standalone_quote_lines():
    """The fallback segmenter re-attached a closing-quote fragment by string
    concatenation and then could not find the joined sentence in its own text
    (RuntimeError on conversation 769). Spans are computed, never re-searched."""
    from stencil.ledger import segment_char_spans, segment_sentences
    spans = segment_char_spans(CONV_769_TURN1)
    assert spans and all(0 <= a < b <= len(CONV_769_TURN1) for a, b in spans)
    assert all(b0 <= a1 for (_, b0), (a1, _) in zip(spans, spans[1:], strict=False))  # ordered, disjoint
    assert [CONV_769_TURN1[a:b] for a, b in spans] == segment_sentences(CONV_769_TURN1)
    assert CONV_769_TURN1[spans[0][0]:spans[0][1]].startswith("Create a slogan")
    # a quote-only line EXTENDS the previous sentence's span (the newline is kept, so the text is findable)
    assert segment_char_spans('He said "go." Then left.\n"\nquoted line\n"') == [(0, 13), (14, 26), (27, 40)]
    assert segment_sentences('He said "go." Then left.\n"\nquoted line\n"') == ['He said "go."', 'Then left.\n"', 'quoted line\n"']


def test_build_ledger_accepts_resolved_salience_object_and_uses_its_segmenter(tok):
    """A bare callable resolves to the FALLBACK segmenter (sol's finding 3);
    the runner must pass the resolved Salience so split_sentences is used."""
    salience = pytest.importorskip("stencil.salience")
    from stencil.e2_multiif import build_replay_context
    from stencil.ledger import (
        Salience,
        build_ledger,
        resolve_salience,
        segment_char_spans,
    )
    sal = resolve_salience()
    assert isinstance(sal, Salience) and sal.segment is salience.split_sentences
    assert resolve_salience(sal.classify).segment is segment_char_spans  # the bug sol found
    context = build_replay_context([CONV_769_TURN1, "Add one more line."], ["x"], turn=2, positive_control=False)
    entries = build_ledger(tok, context, salience=sal)
    assert entries and all(e.provenance == "salience" for e in entries)
    seen = []

    def spy(text):
        seen.append(text)
        return salience.split_sentences(text)
    build_ledger(tok, context, salience=Salience(sal.classify, spy, "salience"))
    assert seen == [CONV_769_TURN1, "Add one more line."]  # the object's segmenter was used, per user turn


def test_instruction_origins_are_positional_over_cumulative_id_lists():
    from stencil.ledger import instruction_origins
    lists = {1: ["a", "b"], 2: ["a", "b", "c"], 3: ["a", "b", "c", "a"]}
    got = instruction_origins(lists, current_turn=3)
    assert [(o["index"], o["id"], o["origin_turn"], o["aged"]) for o in got] == [
        (0, "a", 1, True), (1, "b", 1, True), (2, "c", 2, True), (3, "a", 3, False)]
    assert [o["origin_turn"] for o in instruction_origins(lists, current_turn=2)] == [1, 1, 2]
    with pytest.raises(ValueError):
        instruction_origins({1: ["a"], 2: ["b", "a"]}, current_turn=2)  # not cumulative


def test_link_entries_records_instruction_ids_per_entry(tok):
    from stencil.ledger import build_ledger, instruction_origins, link_entries
    context = three_turn_context()
    entries = build_ledger(tok, context, salience=stub_salience)
    lists = {1: ["keywords:existence"], 2: ["keywords:existence", "punctuation:no_comma"],
             3: ["keywords:existence", "punctuation:no_comma", "startend:quotation"]}
    origins = instruction_origins(lists, current_turn=3)
    granularity = link_entries(entries, tok, context, origins)
    assert granularity == "origin_turn"  # Multi-IF carries no "Constraint:" markers
    assert [e.instruction_ids for e in entries] == [["keywords:existence"], ["punctuation:no_comma"], ["startend:quotation"]]
    assert entries[0].to_record()["instruction_ids"] == ["keywords:existence"]
    assert [o["entry_indices"] for o in origins] == [[0], [1], [2]]


def test_link_entries_uses_constraint_span_records_when_markers_exist(tok):
    from stencil.e2 import constraint_span_records
    from stencil.e2_multiif import build_replay_context
    from stencil.ledger import build_ledger, instruction_origins, link_entries
    p1 = "Write about rain. Constraint: include the keyword lantern. Constraint: do not use commas."
    context = build_replay_context([p1, "Shorter please."], ["ok"], turn=2, positive_control=False)
    assert len(constraint_span_records(tok, context)) == 2
    entries = build_ledger(tok, context, salience=lambda s: s.startswith("Constraint:"))
    assert [e.text for e in entries] == ["Constraint: include the keyword lantern.", "Constraint: do not use commas."]
    origins = instruction_origins({1: ["keywords:existence", "punctuation:no_comma"],
                                   2: ["keywords:existence", "punctuation:no_comma"]}, current_turn=2)
    assert link_entries(entries, tok, context, origins) == "constraint_span"
    assert [e.instruction_ids for e in entries] == [["keywords:existence"], ["punctuation:no_comma"]]
    assert [o["entry_indices"] for o in origins] == [[0], [1]]


def test_matched_nonledger_control_is_width_and_position_matched():
    from stencil.ledger import matched_nonledger_control
    user_turns = [(2, 30), (40, 60)]
    ledger = [(5, 10), (20, 25), (45, 50)]
    control, tiers = matched_nonledger_control(total_len=70, selected=[(5, 10), (45, 50)],
                                               ledger_spans=ledger, user_turns=user_turns)
    assert [b - a for a, b in control] == [5, 5]                       # width matched
    for (a, b) in control:
        assert any(ta <= a and b <= tb for ta, tb in user_turns)       # inside a user turn
        assert all(b <= la or a >= lb for la, lb in ledger)            # disjoint from EVERY entry
    assert control[0] == (10, 15) and control[1] == (40, 45)           # nearest window (tie -> earlier start)
    assert tiers == ["same_turn", "same_turn"]
    assert control[0][1] <= control[1][0]                              # controls disjoint from each other
    # a fully-instruction turn falls back to another user turn, then to anywhere, disclosed
    control, tiers = matched_nonledger_control(total_len=70, selected=[(40, 60)], ledger_spans=[(40, 60)],
                                               user_turns=[(2, 30), (40, 60)])
    assert control == [(10, 30)] and tiers == ["other_user_turn"]
    control, tiers = matched_nonledger_control(total_len=100, selected=[(2, 30)], ledger_spans=[(2, 30), (40, 60)],
                                               user_turns=[(2, 30), (40, 60)])
    assert tiers == ["outside_user_turns"] and control == [(60, 88)]
    # impossible window: NEVER raises (sol round 2: conversation 145 turn 2 crashed the arm);
    # the span gets tier "none" and a None control, the others are still constructed
    control, tiers = matched_nonledger_control(total_len=12, selected=[(0, 10)], ledger_spans=[(0, 10)], user_turns=[(0, 10)])
    assert control == [None] and tiers == ["none"]
    control, tiers = matched_nonledger_control(total_len=44, selected=[(0, 34), (34, 38)], ledger_spans=[(0, 34), (34, 38)],
                                               user_turns=[(0, 38)])
    assert tiers == ["none", "outside_user_turns"] and control == [None, (38, 42)]


DATA_PATH = ROOT / "data" / "bench" / "multiif_en.jsonl"
BASE_DIR = ROOT / "results" / "qwen" / "b4-multiif-base"


@pytest.mark.skipif(not (TOK_PATH.exists() and DATA_PATH.exists() and (BASE_DIR / "conv-145.json").exists()),
                    reason="tokenizer/data/base records not present")
def test_conversation_145_turn_2_control_is_incomplete_not_a_crash(tok):
    """sol round 2 (results/ledger-reverify-sol.md, HIGH): conversation 145 turn 2 has aged
    entries of widths 34 and 19; the longest non-ledger run is 31 tokens, so the 34-wide
    control is impossible in EITHER selection order.  The context is built exactly the
    runner's way (recorded base responses as history), no model."""
    import importlib.util
    import itertools
    import json

    from stencil.e2 import user_turn_span_records
    from stencil.ledger import build_ledger, matched_nonledger_control, resolve_salience
    spec = importlib.util.spec_from_file_location("ledger_eval_145", ROOT / "scripts" / "ledger_eval.py")
    ev = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ev)
    rows = [json.loads(line) for line in DATA_PATH.read_text().splitlines()]
    base = json.loads((BASE_DIR / "conv-145.json").read_text())
    sal = resolve_salience()
    ev.assert_real_segmenter(sal)
    context = ev.turn_context(rows[145], base, 2)
    P = len(tok.encode(context).ids)
    entries = build_ledger(tok, context, salience=sal)
    aged = [e for e in entries if e.turn_introduced < 2]
    assert sorted(e.span[1] - e.span[0] for e in aged) == [19, 34]
    user_turns = [tuple(r["span"]) for r in user_turn_span_records(tok, context)]
    ledger = [e.span for e in entries]
    for order in itertools.permutations(aged):
        control, tiers = matched_nonledger_control(total_len=P, selected=[e.span for e in order],
                                                   ledger_spans=ledger, user_turns=user_turns)
        assert len(control) == len(tiers) == 2
        assert tiers[[e.span[1] - e.span[0] for e in order].index(34)] == "none"
        assert tiers.count("none") == 1
        for sp, (sa, sb), tier in zip(control, [e.span for e in order], tiers, strict=True):
            if tier == "none":
                assert sp is None
                continue
            a, b = sp
            assert b - a == sb - sa and 0 <= a < b <= P
            assert all(b <= la or a >= lb for la, lb in ledger)


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
    from stencil.bench import EOS, TMPL, generate_cached
    from stencil.ledger import generate_sustained
    from stencil.qwen3 import KVCache
    m, tok, _ = gpu_setup
    context = TMPL.format(p=PROMPTS[0])
    # independent base generator: plain KV-cached greedy, NO hook argument at all
    ids = tok.encode(context).ids
    cache, base_ids = KVCache(), []
    with torch.no_grad():
        logits = m(torch.tensor([ids], device="cuda"), cache=cache)
        nxt = int(logits[0, -1].argmax())
        while nxt not in EOS and len(base_ids) < 40:
            base_ids.append(nxt)
            logits = m(torch.tensor([[nxt]], device="cuda"), cache=cache)
            nxt = int(logits[0, -1].argmax())
    calls = {"n": 0}

    def select_fn(q):
        calls["n"] += 1
        assert q.shape == (2048,)
        return []
    got = generate_sustained(m, tok, context, select_fn=select_fn, max_new=40)
    assert calls["n"] == 1, "the selection callback must run exactly once, at prefill"
    assert list(got.ids) == base_ids, "token IDs must be identical, not merely the decoded text"
    assert got.n_generated == len(base_ids) and got.prompt_tokens == len(ids)
    assert got.text == generate_cached(m, tok, PROMPTS[0], max_new=40)[0]
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
