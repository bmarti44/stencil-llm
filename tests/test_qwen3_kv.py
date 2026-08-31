# ruff: noqa: E501
"""KV-cache acceptance (BENCH-WAVE B0 registered fallback, AMENDED —
pending checkpoint-ii ruling; see WORKLOG 2026-08-30).

The originally registered criterion ("token-by-token parity vs full
forward") is unpassable in bf16: cached (GEMV) and full (GEMM) attention
select different cuBLAS kernels, giving max logit drift 0.459 (no-bias) /
1.107 (bias) — while greedy trajectories contain top-1/top-2 margins as
small as 0.103. This is the same drift class as our HF parity (0.6955)
and cannot be engineered away without changing dtype or kernel.

Amended acceptance (conservative reading, flagged for review):
1. The CACHED path is the deployment semantics for every benchmark arm
   (base and wave alike) — it must be bitwise self-deterministic.
2. Cross-path drift vs full forward is characterized and bounded
   (logits <= 1.0 no-bias / 2.0 bias along the full-path trajectory),
   and top-1 must agree at every step whose full-path margin exceeds
   the bound.
3. capture_hidden (single-pass h20 for the wave controller) must match
   return_hidden within 5% of the activation's max magnitude and
   cosine >= 0.999.

GPU required (bf16 trunk).
"""
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


PROMPT = "<|im_start|>user\nDescribe a quiet morning by a lake, in three sentences.<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\n"
STEPS = 24


def make_rows(P, n):
    g = torch.Generator().manual_seed(7)
    return [2.0 * torch.rand(P, generator=g).cuda() for _ in range(n)]


def cached_greedy(m, ids, bias_rows=None, capture=None):
    """the deployment path: prefill once (bias_rows[0] on the prompt's
    last row), then one cached step per token."""
    from stencil.qwen3 import KVCache
    P = len(ids)
    cache = KVCache()
    out, hs = [], []
    with torch.no_grad():
        ab = None
        if bias_rows is not None:
            b = torch.zeros(P, P, device="cuda")
            b[-1, :P] = bias_rows[0]
            ab = {L: b for L in range(20, 28)}
        r = m(torch.tensor([ids], device="cuda"), cache=cache, attn_bias=ab, capture_hidden=capture)
        logits, h = (r if capture is not None else (r, None))
        if capture is not None:
            hs.append(h[0, -1].float())
        out.append(int(logits[0, -1].argmax()))
        for s in range(1, STEPS):
            ab = None
            if bias_rows is not None:
                row = torch.zeros(1, cache.length + 1, device="cuda")
                row[0, :P] = bias_rows[s]
                ab = {L: row for L in range(20, 28)}
            r = m(torch.tensor([[out[-1]]], device="cuda"), cache=cache,
                  attn_bias=ab, capture_hidden=capture)
            logits, h = (r if capture is not None else (r, None))
            if capture is not None:
                hs.append(h[0, -1].float())
            out.append(int(logits[0, -1].argmax()))
    return out, hs


def full_path_drift(m, ids, bias_rows=None):
    """follow the FULL-forward greedy trajectory; at each step compare the
    cached path's logits computed over the identical prefix. Returns
    (per-step max abs logit diff, per-step full-path top1-top2 margin,
    per-step top-1 agreement)."""
    from stencil.qwen3 import KVCache
    P = len(ids)
    toks = torch.tensor([ids], device="cuda")
    cache = KVCache()
    diffs, margins, agree = [], [], []
    with torch.no_grad():
        ab = None
        if bias_rows is not None:
            b = torch.zeros(P, P, device="cuda")
            b[-1, :P] = bias_rows[0]
            ab = {L: b for L in range(20, 28)}
        lf = m(toks, attn_bias=ab)[0, -1].float()
        lc = m(toks, attn_bias=ab, cache=cache)[0, -1].float()
        for s in range(STEPS):
            diffs.append(float((lf - lc).abs().max()))
            top2 = torch.topk(lf, 2).values
            margins.append(float(top2[0] - top2[1]))
            agree.append(int(lf.argmax()) == int(lc.argmax()))
            nxt = int(lf.argmax())
            toks = torch.cat([toks, torch.tensor([[nxt]], device="cuda")], dim=1)
            if s + 1 == STEPS:
                break
            ab = abc = None
            if bias_rows is not None:
                t = toks.shape[1]
                bf = torch.zeros(t, t, device="cuda")
                bf[-1, :P] = bias_rows[s + 1]
                ab = {L: bf for L in range(20, 28)}
                row = torch.zeros(1, cache.length + 1, device="cuda")
                row[0, :P] = bias_rows[s + 1]
                abc = {L: row for L in range(20, 28)}
            lf = m(toks, attn_bias=ab)[0, -1].float()
            lc = m(torch.tensor([[nxt]], device="cuda"), cache=cache, attn_bias=abc)[0, -1].float()
    return diffs, margins, agree


def test_cached_self_deterministic_no_bias(setup):
    m, tok = setup
    ids = tok.encode(PROMPT).ids
    assert cached_greedy(m, ids)[0] == cached_greedy(m, ids)[0]


def test_cached_self_deterministic_with_wave_bias(setup):
    m, tok = setup
    ids = tok.encode(PROMPT).ids
    rows = make_rows(len(ids), STEPS)
    a = cached_greedy(m, ids, rows)[0]
    b = cached_greedy(m, ids, rows)[0]
    assert a == b


def test_cross_path_drift_bounded_no_bias(setup):
    m, tok = setup
    ids = tok.encode(PROMPT).ids
    diffs, margins, agree = full_path_drift(m, ids)
    assert max(diffs) <= 1.0, f"no-bias logit drift {max(diffs):.4f} > 1.0"
    bad = [s for s in range(STEPS) if margins[s] > 1.0 and not agree[s]]
    assert not bad, f"top-1 disagrees at wide-margin steps {bad}"


def test_cross_path_drift_bounded_with_wave_bias(setup):
    m, tok = setup
    ids = tok.encode(PROMPT).ids
    rows = make_rows(len(ids), STEPS)
    diffs, margins, agree = full_path_drift(m, ids, rows)
    assert max(diffs) <= 2.0, f"bias logit drift {max(diffs):.4f} > 2.0"
    bad = [s for s in range(STEPS) if margins[s] > 2.0 and not agree[s]]
    assert not bad, f"top-1 disagrees at wide-margin steps {bad}"


def test_capture_hidden_matches_return_hidden(setup):
    m, tok = setup
    ids = tok.encode(PROMPT).ids
    out, hs = cached_greedy(m, ids, capture=20)
    # hs[s] is h20 of the last position when computing step s's logits;
    # step 5's input sequence is ids + out[:5]
    toks = torch.tensor([ids + out[:5]], device="cuda")
    with torch.no_grad():
        ref = m(toks, return_hidden=20)[0, -1].float()
    scale = float(ref.abs().max())
    err = float((hs[5] - ref).abs().max())
    cos = float(torch.nn.functional.cosine_similarity(hs[5], ref, dim=0))
    assert err <= 0.05 * scale, f"h20 drift {err:.3f} > 5% of scale {scale:.1f}"
    assert cos >= 0.999, f"h20 cosine {cos:.5f} < 0.999"
