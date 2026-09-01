# ruff: noqa: E501
"""Obligation-state gate (R3b) — red/green TDD.

The registered 6 model-state features carried no held-out signal
(AUC 0.46-0.54). Obligation state does (0.70-0.76). This gate is
DETERMINISTIC — no training — and fires only when:
  (1) an OUTSTANDING constraint is of a FIXABLE family,
  (2) NO live word-cap constraint (the harm engine: 25 of 57 breaks),
  (3) the response is past a registered fraction of expected length.
Fixability and the word-cap exclusion are frozen from the 564-moment
harvest (WORKLOG 2026-09-01).
"""
import pytest


def test_fixable_and_forbidden_families_are_frozen():
    from stencil.obligation_gate import FIXABLE_FAMILIES, VETO_INSTRUCTION_IDS
    # measured fix rates: postscript 100%, placeholders 53%, kw_exist 41%
    assert FIXABLE_FAMILIES == frozenset({
        "detectable_content:postscript",
        "detectable_content:number_placeholders",
        "keywords:existence",
        "keywords:frequency",
        "detectable_format:number_bullet_lists",
    })
    # word caps break 27% of passing cells; never fire alongside one
    assert "length_constraints:number_words" in VETO_INSTRUCTION_IDS


def test_veto_only_applies_to_upper_bound_word_limits():
    from stencil.obligation_gate import is_veto
    assert is_veto("length_constraints:number_words", {"relation": "less than", "num_words": 90})
    assert not is_veto("length_constraints:number_words", {"relation": "at least", "num_words": 45})
    assert not is_veto("keywords:existence", {"keywords": ["a", "b"]})


def test_gate_fires_only_when_all_three_conditions_hold():
    from stencil.obligation_gate import should_fire
    fixable = [("keywords:existence", {"keywords": ["lantern", "gravel"]})]
    cap = [("length_constraints:number_words", {"relation": "less than", "num_words": 90})]
    # (1) outstanding fixable + (2) no cap + (3) past position -> FIRE
    assert should_fire(outstanding=fixable, live=fixable, position=0.6).fire
    # (3) too early -> no fire
    assert not should_fire(outstanding=fixable, live=fixable, position=0.2).fire
    # (2) live word cap anywhere -> veto even if outstanding+late
    assert not should_fire(outstanding=fixable, live=fixable + cap, position=0.9).fire
    # (1) nothing outstanding -> no fire
    assert not should_fire(outstanding=[], live=fixable, position=0.9).fire
    # outstanding but UNFIXABLE family -> no fire
    unfix = [("detectable_format:title", {})]
    assert not should_fire(outstanding=unfix, live=unfix, position=0.9).fire


def test_reason_is_recorded_for_every_decision():
    from stencil.obligation_gate import should_fire
    cap = [("length_constraints:number_words", {"relation": "less than", "num_words": 90})]
    d = should_fire(outstanding=cap, live=cap, position=0.9)
    assert d.reason == "veto_word_cap" and not d.fire
    d2 = should_fire(outstanding=[], live=[], position=0.9)
    assert d2.reason == "no_outstanding_fixable"
    fixable = [("keywords:existence", {"keywords": ["x", "y"]})]
    d3 = should_fire(outstanding=fixable, live=fixable, position=0.1)
    assert d3.reason == "too_early"
    d4 = should_fire(outstanding=fixable, live=fixable, position=0.7)
    assert d4.fire and d4.reason == "fire"


def test_outstanding_uses_the_vendored_checkers_on_partial_text():
    """NON-VACUOUS: a partial response missing a required keyword must be
    reported outstanding, and reported satisfied once the keyword appears."""
    from stencil.obligation_gate import outstanding_constraints
    row = {"key": 7,
           "instruction_id_list": ["keywords:existence", "detectable_content:postscript"],
           "kwargs": [{"keywords": ["lantern", "gravel"]}, {"postscript_marker": "P.P.S"}]}
    partial = "The work began early and the path was cleared before noon."
    out = [iid for iid, _ in outstanding_constraints(row, partial)]
    assert "keywords:existence" in out and "detectable_content:postscript" in out
    done = partial + " A lantern and some gravel were used. P.P.S. bring rope."
    out2 = [iid for iid, _ in outstanding_constraints(row, done)]
    assert out2 == []


def test_position_proxy_is_oracle_free():
    """position must be computable WITHOUT knowing the final length."""
    from stencil.obligation_gate import position_proxy
    assert position_proxy(tokens_so_far=50, expected_total=100) == pytest.approx(0.5)
    # unknown expectation falls back to a registered default, never to an oracle
    p = position_proxy(tokens_so_far=50, expected_total=None)
    assert 0.0 <= p <= 1.0


# --- consumer path (GPU) ---------------------------------------------------

import torch  # noqa: E402

gpu = pytest.mark.skipif(not torch.cuda.is_available(), reason="needs GPU")


@pytest.fixture(scope="module")
def setup():
    from pathlib import Path

    from tokenizers import Tokenizer

    from stencil.qwen3 import Qwen3
    root = Path(__file__).resolve().parent.parent
    tok = Tokenizer.from_file(str(root / "models" / "qwen3-1.7b-hf" / "tokenizer.json"))
    m = Qwen3()
    m.load_state_dict(torch.load(root / "models" / "qwen3-1.7b.pt", map_location="cpu"), strict=True)
    return m.to(torch.bfloat16).cuda().eval(), tok


ROW = {"key": 3,
       "instruction_id_list": ["keywords:existence"],
       "kwargs": [{"keywords": ["lantern", "gravel"]}]}
PROMPT = ("Write two short sentences about a garden path. "
          "Constraint: make sure both of the words 'lantern' and 'gravel' appear somewhere in your reply.")


@gpu
def test_generate_gated_never_fires_is_bitwise_base(setup):
    """A gate that never fires must leave the model bitwise untouched."""
    from stencil.bench import generate_cached
    from stencil.obligation_gate import generate_gated
    m, tok = setup
    base = generate_cached(m, tok, PROMPT, max_new=40)
    got = generate_gated(m, tok, PROMPT, ROW, max_new=40, position_floor=2.0)  # unreachable floor
    assert got.text == base[0] and got.n_generated == base[1]
    assert not got.fired
    assert all(d["reason"] != "fire" for d in got.decisions)


@gpu
def test_generate_gated_fires_and_records_decisions(setup):
    """Uses a constraint the base model does NOT satisfy spontaneously
    (a postscript marker), so the gate has something outstanding to act
    on — otherwise a non-firing gate is correct behaviour, not a bug."""
    from stencil.obligation_gate import generate_gated
    m, tok = setup
    row = {"key": 11,
           "instruction_id_list": ["detectable_content:postscript"],
           "kwargs": [{"postscript_marker": "P.P.S"}]}
    prompt = ("Write two short sentences about a garden path. "
              "Constraint: finish with a postscript that starts with P.P.S")
    got = generate_gated(m, tok, prompt, row, max_new=60, position_floor=0.0)
    assert got.fired and any(d["reason"] == "fire" for d in got.decisions)
    assert len(got.decisions) > 0
    a = generate_gated(m, tok, prompt, row, max_new=60, position_floor=0.0)
    assert (a.text, a.fired) == (got.text, got.fired)  # deterministic


@gpu
def test_word_cap_veto_blocks_firing_end_to_end(setup):
    """The single highest-value rule: never fire alongside a live cap."""
    from stencil.obligation_gate import generate_gated
    m, tok = setup
    row = {"key": 4,
           "instruction_id_list": ["keywords:existence", "length_constraints:number_words"],
           "kwargs": [{"keywords": ["lantern", "gravel"]},
                      {"relation": "less than", "num_words": 90}]}
    prompt = PROMPT + " Constraint: keep the reply under 90 words in total."
    got = generate_gated(m, tok, prompt, row, max_new=60, position_floor=0.0)
    assert not got.fired
    assert any(d["reason"] == "veto_word_cap" for d in got.decisions)


def test_position_floor_parameter_is_honored_not_shadowed():
    """Regression: generate_gated accepted position_floor but should_fire
    used the module constant, so the parameter was dead."""
    from stencil.obligation_gate import POSITION_FLOOR, should_fire
    fixable = [("keywords:existence", {"keywords": ["a", "b"]})]
    pos = POSITION_FLOOR / 2
    assert not should_fire(outstanding=fixable, live=fixable, position=pos).fire
    assert should_fire(outstanding=fixable, live=fixable, position=pos,
                       position_floor=0.0).fire
