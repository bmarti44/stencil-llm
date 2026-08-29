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


def _rope(t: int, device: torch.device) -> tuple[torch.Tensor, torch.Tensor]:
    c = Qwen3Config
    inv = 1.0 / (c.rope_theta ** (torch.arange(0, c.head_dim, 2, device=device).float() / c.head_dim))
    pos = torch.arange(t, device=device).float()
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
        rep = c.n_head // c.n_kv_head
        k = k.repeat_interleave(rep, dim=1)
        v = v.repeat_interleave(rep, dim=1)
        att = (q.float() @ k.float().transpose(-2, -1)) / (c.head_dim ** 0.5)
        mask = torch.triu(torch.full((t, t), float("-inf"), device=x.device), diagonal=1)
        att = att + mask
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
        return_hidden: int | None = None,
    ) -> torch.Tensor:
        x = self.embed_tokens(tokens)
        cos, sin = _rope(tokens.shape[1], tokens.device)
        for i, block in enumerate(self.layers):
            if return_hidden is not None and i == return_hidden:
                return x
            x = block(x, cos, sin, None if inj is None else inj.get(i))
        x = self.norm(x)
        return x.float() @ self.embed_tokens.weight.float().T
