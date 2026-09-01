"""Frozen E2 sustained-policy and ablation contracts."""

import torch


class _Encoding:
    def __init__(self, text):
        self.ids = [ord(c) % 31 + 1 for c in text]


class _Tokenizer:
    def encode(self, text):
        return _Encoding(text)

    def decode(self, ids):
        return "".join(chr(65 + int(i) % 26) for i in ids)


class _Trunk(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.anchor = torch.nn.Parameter(torch.zeros(()), requires_grad=False)

    def forward(self, tokens, *, cache=None, capture_hidden=None,
                bias_hook=None, attn_probe=None, **_kwargs):
        t = tokens.shape[1]
        past = cache.length if cache is not None else 0
        pos = torch.arange(past, past + t, device=tokens.device).float()
        h20 = torch.stack((torch.ones_like(pos), (pos % 5) / 5), dim=-1)[None]
        field = bias_hook[1](h20) if bias_hook is not None else None
        focused = field is not None and float(field[20][-1].sum()) > 0
        logits = torch.zeros(1, t, 16, device=tokens.device)
        logits[..., 1] = 2.0
        if focused:
            logits[..., 2] = 3.0
        if attn_probe is not None:
            masks, sink = attn_probe
            vals = [float(row.sum()) / max(1, row.numel()) for row in masks]
            for layer in range(20, 28):
                sink[layer] = vals
        if cache is not None:
            cache.length = past + t
        return (logits, h20) if capture_hidden is not None else logits


class _Controller(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.W_q = torch.nn.Identity()
        self.W_k = torch.nn.Identity()


def _setup():
    context = "abcdefghijABCDEFGHIJ"
    spans = [
        {"span": (2, 5), "origin_turn": 1, "is_aged": True},
        {"span": (10, 14), "origin_turn": 2, "is_aged": False},
    ]
    return _Trunk(), _Tokenizer(), _Controller(), context, spans


def test_e2_silent_policy_is_native_and_has_no_events():
    from stencil.ctrb import HazardGate
    from stencil.e2_policy import generate_e2_policy

    model, tok, ctrl, context, spans = _setup()
    native = generate_e2_policy(model, tok, context, ctrl, spans,
                                mode="native", max_new=18, raw_context=True)
    silent = generate_e2_policy(model, tok, context, ctrl, spans,
                                mode="ctrb", gate=HazardGate.constant(0),
                                threshold=0.5, max_new=18, raw_context=True)
    assert silent.token_ids == native.token_ids
    assert silent.text == native.text
    assert not silent.interventions


def test_e2_ctrb_has_one_sustained_onset_and_all_live_spans():
    from stencil.ctrb import HazardGate
    from stencil.e2_policy import generate_e2_policy

    model, tok, ctrl, context, spans = _setup()
    result = generate_e2_policy(model, tok, context, ctrl, spans,
                                mode="ctrb", gate=HazardGate.constant(1),
                                threshold=0.5, max_new=20, raw_context=True)
    onsets = [x for x in result.interventions if x["kind"] == "onset"]
    assert len(onsets) == 1
    assert onsets[0]["start"] == 6  # five-step delta history, then t+1
    assert onsets[0]["target_origins"] == [1, 2]
    assert result.biased_tokens == result.n_generated - onsets[0]["start"]
    assert result.token_ids[:6] == (1,) * 6
    assert set(result.token_ids[6:]) == {2}


def test_e2_fixed_oldest_and_periodic_ablations_bind():
    from stencil.ctrb import HazardGate
    from stencil.e2_policy import generate_e2_policy

    model, tok, ctrl, context, spans = _setup()
    fixed = generate_e2_policy(model, tok, context, ctrl, spans,
                               mode="fixed_oldest", gate=HazardGate.constant(1),
                               threshold=0.5, max_new=15, raw_context=True)
    onset = next(x for x in fixed.interventions if x["kind"] == "onset")
    assert onset["target_origins"] == [1]
    periodic = generate_e2_policy(model, tok, context, ctrl, spans,
                                  mode="periodic", periodic_onset=3,
                                  max_new=15, raw_context=True)
    ponset = next(x for x in periodic.interventions if x["kind"] == "onset")
    assert ponset["start"] == 3
    assert periodic.token_ids[:3] == (1, 1, 1)
    assert set(periodic.token_ids[3:]) == {2}
