# ruff: noqa: E501
"""Minimal GPT-2 small in the stencil harness.

Loads converted weights (scripts/convert_gpt2.py), supports windowed causal
attention and per-head gates driven by either a stateless (current-token) path
or the oscillator controller. Trunk parameters are frozen by the arms runner;
gates initialize to an exact no-op (bypass verified bitwise by tests).
"""
from __future__ import annotations

import math

import torch
import torch.nn.functional as F
from torch import nn

from .oscillator import OscillatorCell


class ExternalOscillatorController(nn.Module):
    """The library's two-cell oscillator stack for an arbitrary input width.

    Mirrors OscillatorController.forward (cell -> GLU -> cell, output
    [y2; z2]) but takes input_dim explicitly instead of the toy Config.
    """

    def __init__(
        self,
        input_dim: int,
        pairs: int,
        period_min: float,
        period_max: float,
        generator: torch.Generator,
    ) -> None:
        super().__init__()
        self.cells = nn.ModuleList(
            [
                OscillatorCell(
                    input_dim, pairs, period_min, period_max, False,
                    generator=generator,
                ),
                OscillatorCell(
                    pairs, pairs, period_min, period_max, False,
                    generator=generator,
                ),
            ]
        )
        self.W_a = nn.Parameter(torch.empty(pairs, pairs))
        self.W_b = nn.Parameter(torch.empty(pairs, pairs))
        nn.init.normal_(self.W_a, mean=0.0, std=0.02, generator=generator)
        nn.init.normal_(self.W_b, mean=0.0, std=0.02, generator=generator)

    def forward(self, embeddings: torch.Tensor) -> torch.Tensor:
        y1, _ = self.cells[0](embeddings)
        glu = F.linear(y1, self.W_a) * torch.sigmoid(F.linear(y1, self.W_b))
        y2, z2 = self.cells[1](glu)
        return torch.cat((y2, z2), dim=-1)


class GPT2Config:
    n_layer = 12
    n_head = 12
    d_model = 768
    d_ff = 3072
    vocab = 50257
    n_ctx = 1024
    ln_eps = 1e-5


class _Block(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        c = GPT2Config
        self.ln_1 = nn.LayerNorm(c.d_model, eps=c.ln_eps)
        self.attn_qkv = nn.Linear(c.d_model, 3 * c.d_model)
        self.attn_proj = nn.Linear(c.d_model, c.d_model)
        self.ln_2 = nn.LayerNorm(c.d_model, eps=c.ln_eps)
        self.mlp_fc = nn.Linear(c.d_model, c.d_ff)
        self.mlp_proj = nn.Linear(c.d_ff, c.d_model)

    def forward(
        self,
        x: torch.Tensor,
        mask: torch.Tensor,
        gates: torch.Tensor | None,
    ) -> torch.Tensor:
        c = GPT2Config
        b, t, _ = x.shape
        h = self.ln_1(x)
        q, k, v = self.attn_qkv(h).split(c.d_model, dim=2)
        shape = (b, t, c.n_head, c.d_model // c.n_head)
        q, k, v = (z.view(shape).transpose(1, 2) for z in (q, k, v))
        att = (q @ k.transpose(-2, -1)) / math.sqrt(q.shape[-1])
        att = att.masked_fill(~mask, torch.finfo(att.dtype).min)
        out = F.softmax(att, dim=-1) @ v  # (b, head, t, hd)
        if gates is not None:
            # gates: (b, t, n_head) scalar per head/position, applied to head
            # outputs BEFORE the output projection (the registered gate site).
            out = out * gates.permute(0, 2, 1).unsqueeze(-1)
        out = out.transpose(1, 2).reshape(b, t, c.d_model)
        x = x + self.attn_proj(out)
        h = self.ln_2(x)
        x = x + self.mlp_proj(F.gelu(self.mlp_fc(h), approximate="tanh"))
        return x


class GateSource(nn.Module):
    """Maps a per-position control vector to per-layer/head gates near 1.0."""

    def __init__(self, control_dim: int, generator: torch.Generator) -> None:
        super().__init__()
        c = GPT2Config
        weight = torch.empty(c.n_layer * c.n_head, control_dim)
        with torch.no_grad():
            weight.normal_(0.0, 1e-3, generator=generator)
        self.weight = nn.Parameter(weight)
        self.bias = nn.Parameter(torch.zeros(c.n_layer * c.n_head))

    def forward(self, control: torch.Tensor) -> torch.Tensor:
        # control: (b, t, control_dim), RMS-normalized by the caller.
        pre = control @ self.weight.T + self.bias
        return 2.0 * torch.sigmoid(pre)  # (b, t, layers*heads), 1.0 at init


class GatedGPT2(nn.Module):
    """GPT-2 small with windowed attention and an optional control pathway.

    arm = "vanilla" (no gates), "base" (stateless current-token gates), or
    "osc" (oscillator-driven gates). gate_bypass=True forces gates to exactly
    1.0 through a multiplicative identity path (skips the gate product), which
    must be bitwise identical to "vanilla".
    """

    def __init__(
        self,
        arm: str = "vanilla",
        *,
        window: int | None = None,
        seed_init: int = 0,
        osc_periods: tuple[float, float] = (8.0, 2048.0),
    ) -> None:
        super().__init__()
        if arm not in {"vanilla", "base", "osc"}:
            raise ValueError("arm must be vanilla, base, or osc")
        c = GPT2Config
        self.arm = arm
        self.window = window
        self.wte = nn.Embedding(c.vocab, c.d_model)
        self.wpe = nn.Embedding(c.n_ctx, c.d_model)
        self.blocks = nn.ModuleList(_Block() for _ in range(c.n_layer))
        self.ln_f = nn.LayerNorm(c.d_model, eps=c.ln_eps)
        # lm_head is tied to wte (GPT-2 convention).
        self.controller: nn.Module | None = None
        self.gate_source: GateSource | None = None
        if arm != "vanilla":
            from .determinism import named_generator

            pathway = named_generator(seed_init, "pathway")
            if arm == "osc":
                self.controller = ExternalOscillatorController(
                    c.d_model, 64, osc_periods[0], osc_periods[1], pathway
                )
                control_dim = 128
            else:
                control_dim = c.d_model  # current-token embedding, stateless
            self.gate_source = GateSource(control_dim, pathway)

    def trunk_parameters(self) -> list[nn.Parameter]:
        names = ("wte", "wpe", "blocks", "ln_f")
        return [
            p
            for n, p in self.named_parameters()
            if n.split(".")[0] in names
        ]

    def pathway_parameters(self) -> list[nn.Parameter]:
        trunk = {id(p) for p in self.trunk_parameters()}
        return [p for p in self.parameters() if id(p) not in trunk]

    def _mask(self, t: int, device: torch.device) -> torch.Tensor:
        i = torch.arange(t, device=device)
        causal = i.unsqueeze(1) >= i.unsqueeze(0)
        if self.window is not None:
            causal &= (i.unsqueeze(1) - i.unsqueeze(0)) < self.window
        return causal.unsqueeze(0).unsqueeze(0)  # (1,1,t,t)

    def control_states(self, tokens: torch.Tensor) -> torch.Tensor:
        """The wire trajectory (b, t, control_dim) for probing/transplants."""
        emb = self.wte(tokens)
        if self.arm == "osc":
            assert self.controller is not None
            return self.controller(emb)
        return emb

    def forward(
        self,
        tokens: torch.Tensor,
        *,
        gate_bypass: bool = False,
        control_override: torch.Tensor | None = None,
    ) -> torch.Tensor:
        b, t = tokens.shape
        if t > GPT2Config.n_ctx:
            raise ValueError("sequence exceeds GPT-2 position table")
        pos = torch.arange(t, device=tokens.device)
        x = self.wte(tokens) + self.wpe(pos)
        gates = None
        if self.arm != "vanilla" and not gate_bypass:
            control = (
                control_override
                if control_override is not None
                else self.control_states(tokens)
            )
            control = control * torch.rsqrt(
                control.pow(2).mean(-1, keepdim=True) + 1e-8
            )
            all_gates = self.gate_source(control)  # (b,t,L*H)
            gates = all_gates.view(b, t, GPT2Config.n_layer, GPT2Config.n_head)
        mask = self._mask(t, tokens.device)
        for index, block in enumerate(self.blocks):
            layer_gates = None if gates is None else gates[:, :, index, :]
            x = block(x, mask, layer_gates)
        x = self.ln_f(x)
        return x @ self.wte.weight.T
