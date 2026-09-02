# ruff: noqa: E501
"""Additive PRE-SOFTMAX attention bias over KEY COLUMNS for HF Qwen3.

Interface (abstract over attention columns, not prompt spans):

    ColumnBias.rows(layer, q_len, n_keys, device) -> fp32 [q_len, n_keys] | None

``n_keys`` is whatever the layer's CURRENT K/V length is (prompt so far,
plus, in a later ledger version, pinned columns appended to the cache);
the bias is simply added to the [q_len, n_keys] score matrix of that
layer before softmax. The current provider (``StepBias``) puts ``dose``
on each selected column group's columns of the LAST query row only —
exactly the research path's ``uniform_span_bias`` summed over groups.

How it is injected (transformers 4.51.0): Qwen3Attention.forward looks
up ``ALL_ATTENTION_FUNCTIONS[config._attn_implementation]`` at call
time. Inside ``wave_attention(model, bias)`` the "sdpa" entry is
temporarily replaced by ``_wave_sdpa``, which

  * with NO bias for (layer, step) calls the stock ``sdpa_attention_forward``
    with the identical arguments -> bitwise the plain transformers path
    (the model config stays "sdpa", so HF's causal-mask construction is
    also unchanged);
  * with a bias computes attention the way the research trunk does:
    fp32 scores (q.float() @ k.float()^T * scale), -inf causal mask,
    + bias, fp32 softmax, fp32 @ v.float(), cast back. The bias is added
    exactly (fp32), never rounded through a bf16 mask.

Why not a 4D float attention_mask: HF would cast it to the model dtype
(bf16) and route it through the SDPA kernel, so neither the bias nor the
no-bias case would be exact. Why not a registered custom interface name:
with a non-"sdpa" name HF builds an explicit 4D mask for every layer and
the no-bias path would no longer be the plain sdpa call.
"""
from __future__ import annotations

from collections.abc import Sequence
from contextlib import contextmanager
from typing import Protocol

import torch
from transformers.integrations.sdpa_attention import repeat_kv, sdpa_attention_forward
from transformers.modeling_utils import ALL_ATTENTION_FUNCTIONS

WAVE_LAYERS: tuple[int, ...] = tuple(range(20, 28))


class ColumnBias(Protocol):
    def rows(self, layer: int, q_len: int, n_keys: int, device) -> torch.Tensor | None: ...


class StepBias:
    """Sustained uniform bias: ``dose`` on every column of every group, on
    the last query row, at ``layers``. Groups are summed (overlap doubles),
    mirroring the research generator. ``groups`` may be replaced between
    steps (the ledger selects once at prefill and then keeps them)."""

    def __init__(self, dose: float, layers: Sequence[int] = WAVE_LAYERS):
        self.dose = float(dose)
        self.layers = frozenset(int(x) for x in layers)
        self.groups: list[tuple[int, ...]] = []
        self.applied_steps = 0
        self._last_forward_id: int | None = None

    def rows(self, layer, q_len, n_keys, device):
        if layer not in self.layers or not self.groups or self.dose == 0.0:
            return None
        out = torch.zeros(q_len, n_keys, dtype=torch.float32, device=device)
        for cols in self.groups:
            idx = torch.as_tensor(cols, dtype=torch.long, device=device)
            if int(idx.max()) >= n_keys:
                raise ValueError("bias column outside the layer's current key axis")
            out[-1, idx] += self.dose
        return out


_STATE: dict = {"bias": None, "forward_token": 0}


def _wave_sdpa(module, query, key, value, attention_mask, dropout=0.0, scaling=None, is_causal=None, **kwargs):
    bias: ColumnBias | None = _STATE["bias"]
    q_len, n_keys = query.shape[2], key.shape[2]
    rows = None if bias is None else bias.rows(getattr(module, "layer_idx", -1), q_len, n_keys, query.device)
    if rows is None:
        return sdpa_attention_forward(module, query, key, value, attention_mask, dropout=dropout,
                                      scaling=scaling, is_causal=is_causal, **kwargs)
    if query.shape[0] != 1:
        raise ValueError("stencil_wave bias supports batch size 1")
    k = repeat_kv(key, module.num_key_value_groups)
    v = repeat_kv(value, module.num_key_value_groups)
    scale = scaling if scaling is not None else query.shape[-1] ** -0.5
    att = (query.float() @ k.float().transpose(2, 3)) * scale
    if attention_mask is not None:
        att = att + attention_mask[:, :, :, :n_keys].float()
    elif q_len > 1:
        past = n_keys - q_len
        att = att + torch.triu(torch.full((q_len, n_keys), float("-inf"), device=query.device), diagonal=1 + past)
    att = att + rows[None, None]
    out = (torch.softmax(att, dim=-1) @ v.float()).to(query.dtype)
    if isinstance(bias, StepBias):
        tok = _STATE["forward_token"]
        if bias._last_forward_id != tok:
            bias._last_forward_id = tok
            bias.applied_steps += 1
    return out.transpose(1, 2).contiguous(), None


@contextmanager
def wave_attention(model, bias: ColumnBias | None):
    """Scope inside which the model's sdpa attention consults ``bias``."""
    impl = model.config._attn_implementation
    if impl != "sdpa":
        raise RuntimeError(f"stencil_wave needs attn_implementation='sdpa' (got {impl!r})")
    prev = _STATE["bias"]
    prev_local = ALL_ATTENTION_FUNCTIONS._local_mapping.get("sdpa")
    _STATE["bias"] = bias
    ALL_ATTENTION_FUNCTIONS["sdpa"] = _wave_sdpa
    try:
        yield
    finally:
        _STATE["bias"] = prev
        if prev_local is None:
            del ALL_ATTENTION_FUNCTIONS["sdpa"]  # drops the local override; the stock function is back
        else:
            ALL_ATTENTION_FUNCTIONS["sdpa"] = prev_local


def mark_forward():
    """Called once per model forward (by the layer-20 pre-hook) so StepBias
    can count biased STEPS rather than biased layers."""
    _STATE["forward_token"] += 1
