# ruff: noqa: E501
"""B0.3 runner tests: bias_hook equivalence (the mid-forward hook must
reproduce a directly-passed attn_bias bitwise), generator determinism
on a NON-IFEval smoke prompt (single-use invariant: the 541 is never
touched by a model outside the sealed job), and scoring determinism
(langdetect pin effective through the runner's own import path)."""
import pytest
import torch

pytestmark = pytest.mark.skipif(not torch.cuda.is_available(), reason="needs GPU")


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


SMOKE = "List three animals that live in forests."


def test_bias_hook_matches_direct_attn_bias(setup):
    m, tok = setup
    from stencil.bench import TMPL, WAVE_LAYERS
    ids = tok.encode(TMPL.format(p=SMOKE)).ids
    toks = torch.tensor([ids], device="cuda")
    t = len(ids)
    g = torch.Generator().manual_seed(11)
    b = (2.0 * torch.rand(t, t, generator=g)).cuda()
    with torch.no_grad():
        direct = m(toks, attn_bias={L: b for L in WAVE_LAYERS})
        hooked = m(toks, bias_hook=(20, lambda h: {L: b for L in WAVE_LAYERS}))
    assert torch.equal(direct, hooked)


def test_bias_hook_sees_layer20_input(setup):
    m, tok = setup
    from stencil.bench import TMPL
    ids = tok.encode(TMPL.format(p=SMOKE)).ids
    toks = torch.tensor([ids], device="cuda")
    seen = {}

    def grab(h):
        seen["h"] = h
        return None
    with torch.no_grad():
        ref = m(toks, return_hidden=20)
        m(toks, bias_hook=(20, grab))
    assert torch.equal(seen["h"], ref)


def test_generate_cached_deterministic_base(setup):
    m, tok = setup
    from stencil.bench import generate_cached
    a = generate_cached(m, tok, SMOKE, max_new=48)
    b = generate_cached(m, tok, SMOKE, max_new=48)
    assert a == b
    assert a[1] > 0


def test_generate_cached_wave_deterministic_and_differs(setup):
    m, tok = setup
    from stencil.bench import generate_cached

    def bias_fn(h20, P, past):
        # deterministic stand-in field over prompt positions from h20
        t = h20.shape[1]
        row = torch.zeros(t, past + t, device="cuda")
        row[:, :P] = 2.0 * torch.sigmoid(h20[0, :, :1] - 1.0)
        return row
    a = generate_cached(m, tok, SMOKE, bias_fn=bias_fn, max_new=48)
    b = generate_cached(m, tok, SMOKE, bias_fn=bias_fn, max_new=48)
    base = generate_cached(m, tok, SMOKE, max_new=48)
    assert a == b
    assert a[0] != base[0]  # the hook demonstrably reaches the logits


def test_scoring_deterministic():
    from stencil.bench import score_response
    row = {"key": 1, "prompt": "Write about rain in all lowercase.",
           "instruction_id_list": ["change_case:english_lowercase", "language:response_language"],
           "kwargs": [{}, {"language": "en"}]}
    resp = ("the rain settled over the valley this morning and the paths "
            "were quiet while the river carried small branches away.")
    a = score_response(row, resp)
    b = score_response(row, resp)
    assert a == b
    assert a["prompt_level_strict_acc"] is True


def test_aggregate_math():
    from stencil.bench import aggregate
    pp = [
        {"prompt_level_strict_acc": True, "inst_level_strict_acc": [True, True],
         "prompt_level_loose_acc": True, "inst_level_loose_acc": [True, True]},
        {"prompt_level_strict_acc": False, "inst_level_strict_acc": [True, False],
         "prompt_level_loose_acc": True, "inst_level_loose_acc": [True, True]},
    ]
    agg = aggregate(pp)
    assert agg["prompt_level_strict_acc"] == 0.5
    assert agg["inst_level_strict_acc"] == 0.75
    assert agg["prompt_level_loose_acc"] == 1.0
    assert agg["inst_level_loose_acc"] == 1.0
