# ruff: noqa: E501
"""Minimal Qwen3-1.7B in the stencil harness (QWEN-PLAN P0).

Owns the forward pass for the same reasons gpt2.py did: bitwise determinism,
probe access at every layer, inert-graft tests, and provable-unreachability
constructions (here via chunk deletion rather than windowing). Config values
from models/qwen3-1.7b-hf/config.json (pinned revision). Norms and softmax in
fp32, matmuls in bf16, mirroring the reference implementation closely enough
for the registered parity tolerance; our own outputs are then frozen bitwise.
"""
from __future__ import annotations

import math

import torch
import torch.nn.functional as F
from torch import nn


class Qwen3Config:
    n_layer = 28
    n_head = 16
    n_kv_head = 8
    head_dim = 128
    d_model = 2048
    d_ff = 6144
    vocab = 151936
    rope_theta = 1_000_000.0
    rms_eps = 1e-6
    n_ctx = 40960


class KVCache:
    """Per-layer post-RoPE K / V cache (BENCH-WAVE B0; kept pre-GQA-repeat
    for memory). Grown by Qwen3.forward when passed via `cache=`."""

    def __init__(self) -> None:
        self.k: list[torch.Tensor | None] = [None] * Qwen3Config.n_layer
        self.v: list[torch.Tensor | None] = [None] * Qwen3Config.n_layer
        self.length = 0

    def evict(self, drop_start: int, drop_end: int, keep=()) -> dict[int, int]:
        """LEDGER-KV: remove columns [drop_start, drop_end) from every layer
        EXCEPT the kept sub-ranges (pinned ledger entries), which survive
        with their original RoPE. `length` is NOT reduced: new tokens keep
        their original absolute positions (no re-indexing). Returns the
        old->new column index map for every surviving column."""
        assert 0 <= drop_start <= drop_end <= self.k[0].shape[2]
        survive = []
        for old in range(self.k[0].shape[2]):
            if not (drop_start <= old < drop_end) or any(s <= old < e for s, e in keep):
                survive.append(old)
        idx = torch.tensor(survive, device=self.k[0].device)
        for L in range(Qwen3Config.n_layer):
            self.k[L] = self.k[L].index_select(2, idx).contiguous()
            self.v[L] = self.v[L].index_select(2, idx).contiguous()
        return {old: new for new, old in enumerate(survive)}


class RMSNorm(nn.Module):
    def __init__(self, dim: int, eps: float = Qwen3Config.rms_eps) -> None:
        super().__init__()
        self.weight = nn.Parameter(torch.ones(dim))
        self.eps = eps

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        dt = x.dtype
        x = x.float()
        x = x * torch.rsqrt(x.pow(2).mean(-1, keepdim=True) + self.eps)
        return (x * self.weight.float()).to(dt)


def _rope(t: int, device: torch.device, offset: int = 0) -> tuple[torch.Tensor, torch.Tensor]:
    c = Qwen3Config
    inv = 1.0 / (c.rope_theta ** (torch.arange(0, c.head_dim, 2, device=device).float() / c.head_dim))
    pos = torch.arange(offset, offset + t, device=device).float()
    freqs = torch.outer(pos, inv)
    emb = torch.cat((freqs, freqs), dim=-1)
    return emb.cos(), emb.sin()


def _rotate_half(x: torch.Tensor) -> torch.Tensor:
    half = x.shape[-1] // 2
    return torch.cat((-x[..., half:], x[..., :half]), dim=-1)


def _apply_rope(q: torch.Tensor, k: torch.Tensor, cos: torch.Tensor, sin: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
    cos = cos[None, None, :, :]
    sin = sin[None, None, :, :]
    qf, kf = q.float(), k.float()
    q2 = qf * cos + _rotate_half(qf) * sin
    k2 = kf * cos + _rotate_half(kf) * sin
    return q2.to(q.dtype), k2.to(k.dtype)


class _Block(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        c = Qwen3Config
        qd = c.n_head * c.head_dim
        kd = c.n_kv_head * c.head_dim
        self.input_layernorm = RMSNorm(c.d_model)
        self.q_proj = nn.Linear(c.d_model, qd, bias=False)
        self.k_proj = nn.Linear(c.d_model, kd, bias=False)
        self.v_proj = nn.Linear(c.d_model, kd, bias=False)
        self.o_proj = nn.Linear(qd, c.d_model, bias=False)
        self.q_norm = RMSNorm(c.head_dim)
        self.k_norm = RMSNorm(c.head_dim)
        self.post_attention_layernorm = RMSNorm(c.d_model)
        self.gate_proj = nn.Linear(c.d_model, c.d_ff, bias=False)
        self.up_proj = nn.Linear(c.d_model, c.d_ff, bias=False)
        self.down_proj = nn.Linear(c.d_ff, c.d_model, bias=False)

    def forward(
        self,
        x: torch.Tensor,
        cos: torch.Tensor,
        sin: torch.Tensor,
        inj: torch.Tensor | None = None,
        attn_bias: torch.Tensor | None = None,  # (t, T_total) fp32, pre-softmax
        cache: "KVCache | None" = None,
        layer_idx: int = -1,
        deficit_gate: tuple | None = None,  # (span_mask[T_total] bool, tau, b_max)
        attn_probe: tuple | None = None,  # (span_mask[T_total] bool, sink dict) -> sink[layer] = last-row mean span mass
    ) -> torch.Tensor:
        c = Qwen3Config
        b, t, _ = x.shape
        h = self.input_layernorm(x)
        q = self.q_proj(h).view(b, t, c.n_head, c.head_dim).transpose(1, 2)
        k = self.k_proj(h).view(b, t, c.n_kv_head, c.head_dim).transpose(1, 2)
        v = self.v_proj(h).view(b, t, c.n_kv_head, c.head_dim).transpose(1, 2)
        q = self.q_norm(q)
        k = self.k_norm(k)
        q, k = _apply_rope(q, k, cos, sin)
        past = 0
        if cache is not None:
            if cache.k[layer_idx] is not None:
                past = cache.k[layer_idx].shape[2]
                k = torch.cat([cache.k[layer_idx], k], dim=2)
                v = torch.cat([cache.v[layer_idx], v], dim=2)
            cache.k[layer_idx] = k
            cache.v[layer_idx] = v
        rep = c.n_head // c.n_kv_head
        k = k.repeat_interleave(rep, dim=1)
        v = v.repeat_interleave(rep, dim=1)
        att = (q.float() @ k.float().transpose(-2, -1)) / (c.head_dim ** 0.5)
        T_total = past + t
        mask = torch.triu(torch.full((t, T_total), float("-inf"), device=x.device), diagonal=1 + past)
        att = att + mask
        if attn_bias is not None:
            att = att + attn_bias.float()
        if deficit_gate is not None:
            # v4.5 deficit-triggered gating (registered): measure the natural
            # post-softmax mass psi on the governing span per head/row; bias
            # ONLY where psi < tau, by the exact odds correction
            # min(b_max, logit(tau) - logit(psi)); zero deficit -> bitwise
            # identical attention.
            span_mask, tau, b_max = deficit_gate
            p0 = F.softmax(att, dim=-1)
            psi = p0[..., span_mask].sum(-1).clamp(1e-6, 1 - 1e-6)  # (b, h, t)
            need = psi < tau
            if bool(need.any()):
                logit_t = math.log(tau / (1 - tau))
                b_amt = (logit_t - torch.log(psi / (1 - psi))).clamp(max=b_max)
                b_amt = torch.where(need, b_amt, torch.zeros_like(b_amt))
                att = att + b_amt[..., None] * span_mask.float()[None, None, None, :]
        if attn_probe is not None:
            pm, sink = attn_probe
            probs = F.softmax(att, dim=-1)
            if pm.ndim == 1:
                sink[layer_idx] = float(probs[0, :, -1, :][:, pm].sum(-1).mean())
            elif pm.ndim == 2:
                # CTRB needs the natural attention mass for whichever prompt
                # span its frozen q/k readout selects.  Probe every declared
                # span in the same forward so selection cannot introduce a
                # second-forward semantic mismatch.  The legacy 1-D contract
                # above remains bit-for-bit unchanged.
                last = probs[0, :, -1, :]
                sink[layer_idx] = [
                    float(last[:, row].sum(-1).mean()) for row in pm
                ]
            else:
                raise ValueError("attn_probe mask must be [T] or [S,T]")
        out = (F.softmax(att, dim=-1) @ v.float()).to(x.dtype)
        out = out.transpose(1, 2).reshape(b, t, c.n_head * c.head_dim)
        x = x + self.o_proj(out)
        if inj is not None:
            x = x + inj
        h = self.post_attention_layernorm(x)
        x = x + self.down_proj(F.silu(self.gate_proj(h)) * self.up_proj(h))
        return x


class Qwen3(nn.Module):
    """Plain trunk. The focus-cache graft arrives in P1 as a separate module
    so the trunk stays hash-checkable in isolation."""

    def __init__(self) -> None:
        super().__init__()
        c = Qwen3Config
        self.embed_tokens = nn.Embedding(c.vocab, c.d_model)
        self.layers = nn.ModuleList(_Block() for _ in range(c.n_layer))
        self.norm = RMSNorm(c.d_model)
        # lm_head tied to embed_tokens.

    def forward(
        self,
        tokens: torch.Tensor,
        *,
        inj: dict[int, torch.Tensor] | None = None,
        attn_bias: dict[int, torch.Tensor] | None = None,
        return_hidden: int | None = None,
        cache: "KVCache | None" = None,
        capture_hidden: int | None = None,
        bias_hook=None,  # (layer, fn): at layer-input, attn_bias = fn(x)
        deficit_hook=None,  # (layer, fn): at layer-input, gates = fn(x); dict[layer] -> (span_mask, tau, b_max)
        attn_probe=None,  # (span_mask, sink): record last-row span attention mass at layers 20-27
    ) -> torch.Tensor:
        x = self.embed_tokens(tokens)
        offset = cache.length if cache is not None else 0
        cos, sin = _rope(tokens.shape[1], tokens.device, offset)
        captured = None
        deficit_gates = None
        if return_hidden is not None and cache is not None:
            raise ValueError(
                "return_hidden early-returns before cache.length updates and "
                "before layers >= i append k/v — it would corrupt the cache; "
                "use capture_hidden with cache instead")
        for i, block in enumerate(self.layers):
            if return_hidden is not None and i == return_hidden:
                return x
            if capture_hidden is not None and i == capture_hidden:
                captured = x
            if bias_hook is not None and i == bias_hook[0]:
                attn_bias = bias_hook[1](x)
            if deficit_hook is not None and i == deficit_hook[0]:
                deficit_gates = deficit_hook[1](x)
            x = block(
                x, cos, sin,
                None if inj is None else inj.get(i),
                None if attn_bias is None else attn_bias.get(i),
                cache=cache, layer_idx=i,
                deficit_gate=(deficit_gates.get(i) if deficit_hook is not None and i >= deficit_hook[0] and deficit_gates else None),
                attn_probe=(attn_probe if attn_probe is not None and i >= 20 else None),
            )
        if cache is not None:
            cache.length = offset + tokens.shape[1]
        x = self.norm(x)
        logits = x.float() @ self.embed_tokens.weight.float().T
        if capture_hidden is not None:
            return logits, captured
        return logits
