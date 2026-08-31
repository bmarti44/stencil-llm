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


from stencil.bench import make_wave_bias_fn  # noqa: E402


def test_consumer_path_trained_wave_through_cache(setup):
    """checkpoint-ii FINDING-5 (sol, round 2): the ACTUAL trained
    WaveController (sealed w0-ce.pt) through cached generation must
    (a) produce a finite NONZERO field, (b) change the logits vs a
    zero-field run on the same prefix, (c) repeat deterministically.
    Re-run at pre-B4 with the trained BENCHMARK wave before sealing."""
    from pathlib import Path

    from stencil.bench import TMPL, WAVE_LAYERS, generate_cached
    from stencil.wave import WaveController
    root = Path(__file__).resolve().parent.parent
    m, tok = setup
    ctrl = WaveController().cuda()
    ctrl.load_state_dict(torch.load(root / "results" / "qwen" / "w0-ce.pt", map_location="cpu"))
    ctrl = ctrl.eval()

    # (a)+(b): first-token logits differ between wave field and zero field
    ids = tok.encode(TMPL.format(p=SMOKE)).ids
    P = len(ids)
    toks = torch.tensor([ids], device="cuda")
    with torch.no_grad():
        h20 = m(toks, return_hidden=20)
        field = ctrl(h20[0, P - 1:P].float(), h20[0, :P].float())
        assert torch.isfinite(field).all()
        assert float(field.abs().max()) > 0, "trained controller emits a zero field"
        b = torch.zeros(P, P, device="cuda")
        b[-1, :P] = field[0]
        lw = m(toks, attn_bias={L: b for L in WAVE_LAYERS})[0, -1]
        l0 = m(toks)[0, -1]
    assert float((lw - l0).abs().max()) > 0, "wave field does not reach the logits"

    # (c): full cached generation with the registered adapter, twice
    state = {}
    a = generate_cached(m, tok, SMOKE, bias_fn=make_wave_bias_fn(ctrl, state), max_new=48)
    state2 = {}
    b2 = generate_cached(m, tok, SMOKE, bias_fn=make_wave_bias_fn(ctrl, state2), max_new=48)
    assert a == b2
    assert a[1] > 0
    assert float(state["prefill_field"].abs().max()) > 0


def test_return_hidden_with_cache_raises(setup):
    m, tok = setup
    from stencil.qwen3 import KVCache
    with pytest.raises(ValueError, match="corrupt"):
        m(torch.tensor([[1, 2, 3]], device="cuda"), cache=KVCache(), return_hidden=20)
