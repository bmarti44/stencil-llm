# ruff: noqa: E501
"""PRESS-PLAN H3: wrong-span non-vacuity on the real model.

A deliberately WRONG span, pressed through the H1 policy path, must be
(a) actually applied per the press log and (b) actually change the
model's next-token logits — instrumentation that cannot demonstrate its
own effect is a test bug, not a pass (exact-zero lesson)."""
import pytest
import torch

pytestmark = pytest.mark.skipif(not torch.cuda.is_available(), reason="needs GPU")


def test_wrong_span_press_changes_logits():
    from pathlib import Path

    from tokenizers import Tokenizer

    from stencil.qwen3 import Qwen3
    from stencil.t2_runner import LAYERS, run_policy_session

    root = Path(__file__).resolve().parent.parent
    tok = Tokenizer.from_file(str(root / "models" / "qwen3-1.7b-hf" / "tokenizer.json"))
    m = Qwen3()
    m.load_state_dict(torch.load(root / "models" / "qwen3-1.7b.pt", map_location="cpu"), strict=True)
    m = m.to(torch.bfloat16).cuda().eval()

    prompt = "All function names must start with 'calc_'. Write a python function.\n```python\n"
    ids = tok.encode(prompt).ids
    wrong_span = (0, 4)  # deliberately NOT the governing region we'd target

    with torch.no_grad():
        toks = torch.tensor([ids], device="cuda")
        base_logits = m(toks)[0, -1].float()
        t = toks.shape[1]
        bias = torch.zeros(t, t, device="cuda")
        bias[-1:, wrong_span[0]:wrong_span[1]] = 8.0  # large beta so the effect is unmistakable
        pressed_logits = m(toks, attn_bias={L: bias for L in LAYERS})[0, -1].float()

    diff = float((pressed_logits - base_logits).abs().max())
    assert diff > 1e-3, f"wrong-span press did not move logits (max |diff|={diff}) — instrumentation vacuous"

    # and the H1 path actually applies a wrong-but-in-ledger span per its log
    log = []
    ledger_spans = {"prefix": (0, 12)}
    policy = lambda model, tk, ptxt, text: ((0, 4), {"score": 1.0})
    run_policy_session(m, tok, prompt, ledger_spans, policy, threshold=0.5,
                       press_log=log, max_new=2)
    assert any(e["applied"] == (0, 4) for e in log)
