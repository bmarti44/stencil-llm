# ruff: noqa: E501
"""Focus cache for the Qwen rung (QWEN-PLAN P1).

Structured writes (the runtime supplies obligation spans + slot ids — the
focus.set API shape), so no learned gates at this phase. Writer pools frozen
blocks 0-19 contextual states over the span; reader attends over slots from
block-20 states and feeds zero-init additive injections into blocks 24-27.
State is an explicit object carried across chunks; the evidence chunk can be
deleted entirely (provable unreachability by deletion).
"""
from __future__ import annotations

from dataclasses import dataclass, field

import torch
from torch import nn

from .qwen3 import Qwen3, Qwen3Config, _rope

INJ_LAYERS = (24, 25, 26, 27)
WRITE_LAYER = 20  # hidden states feeding the writer / reader
D_KEY = 64
D_VAL = 1024  # 4 x 256 flattened
D_CODE = 512


@dataclass
class QwenCacheState:
    slots: dict[int, tuple[torch.Tensor, torch.Tensor]] = field(default_factory=dict)  # id -> (key, value)

    def detached(self) -> QwenCacheState:
        return QwenCacheState(
            slots={i: (k.detach().clone(), v.detach().clone()) for i, (k, v) in self.slots.items()}
        )


class QwenFocusCache(nn.Module):
    def __init__(self, *, seed: int = 0) -> None:
        super().__init__()
        c = Qwen3Config
        g = torch.Generator().manual_seed(seed)
        self.key_mlp = nn.Sequential(nn.Linear(c.d_model, 256), nn.GELU(), nn.Linear(256, 4 * D_KEY))
        self.val_mlp = nn.Sequential(nn.Linear(c.d_model, 1024), nn.GELU(), nn.Linear(1024, D_VAL))
        self.query = nn.Linear(c.d_model, D_KEY)
        self.code_proj = nn.Linear(D_VAL // 4, D_CODE)
        self.inj = nn.ModuleList(nn.Linear(D_CODE, c.d_model, bias=False) for _ in INJ_LAYERS)
        for lin in [m for m in self.key_mlp if isinstance(m, nn.Linear)] + [m for m in self.val_mlp if isinstance(m, nn.Linear)] + [self.query, self.code_proj]:
            nn.init.normal_(lin.weight, std=0.02, generator=g)
            nn.init.zeros_(lin.bias)
        for lin in self.inj:
            nn.init.zeros_(lin.weight)  # bitwise inert until trained

    def write(
        self,
        h: torch.Tensor,                      # (1, t, d) block-WRITE_LAYER states of the evidence chunk
        events: list[tuple],   # (span_lo, span_hi, slot_id[, kind]) kind in set/update/clear
        state: QwenCacheState | None = None,
    ) -> QwenCacheState:
        state = state or QwenCacheState()
        for ev in events:
            lo, hi, slot = ev[0], ev[1], ev[2]
            kind = ev[3] if len(ev) > 3 else "set"
            if kind == "clear":
                state.slots.pop(slot, None)
                continue
            enc = h[0, lo:hi].float().mean(dim=0)
            state.slots[slot] = (self.key_mlp(enc), self.val_mlp(enc))
        return state

    def read_inj(self, h: torch.Tensor, state: QwenCacheState) -> dict[int, torch.Tensor]:
        """h: (1, t, d) block-WRITE_LAYER states of the current chunk ->
        per-layer additive injections."""
        if not state.slots:
            return {}
        ids = sorted(state.slots)
        # 4 sub-entries per slot: position-varying queries can walk through a
        # value's sub-vectors, letting a static write drive a token SEQUENCE.
        K = torch.cat([state.slots[i][0].view(4, D_KEY) for i in ids])      # (4n, D_KEY)
        V = torch.cat([state.slots[i][1].view(4, D_VAL // 4) for i in ids])  # (4n, 256)
        q = self.query(h.float())                                            # (1, t, D_KEY)
        att = torch.softmax(q @ K.T / (D_KEY ** 0.5), dim=-1)
        code = self.code_proj(att @ V)                                       # (1, t, D_CODE)
        return {L: self.inj[j](code).to(h.dtype) for j, L in enumerate(INJ_LAYERS)}


class QwenWithCache(nn.Module):
    """Two-pass graft: (1) write from an evidence chunk, (2) read while
    generating on a later chunk with the evidence deleted."""

    def __init__(self, trunk: Qwen3, cache: QwenFocusCache) -> None:
        super().__init__()
        self.trunk = trunk
        self.cache = cache

    def hidden(self, tokens: torch.Tensor) -> torch.Tensor:
        with torch.no_grad():
            return self.trunk(tokens, return_hidden=WRITE_LAYER)

    def write_chunk(
        self, tokens: torch.Tensor, events: list[tuple[int, int, int]],
        state: QwenCacheState | None = None,
    ) -> QwenCacheState:
        return self.cache.write(self.hidden(tokens), events, state)

    def read_logits(
        self, tokens: torch.Tensor, state: QwenCacheState, *, zero_code: bool = False,
    ) -> torch.Tensor:
        c = Qwen3Config
        h = self.hidden(tokens)
        inj = {} if zero_code else self.cache.read_inj(h, state)
        x = h.detach()
        cos, sin = _rope(tokens.shape[1], tokens.device)
        for i in range(WRITE_LAYER, c.n_layer):
            x = self.trunk.layers[i](x, cos, sin, inj.get(i))
        x = self.trunk.norm(x)
        return x.float() @ self.trunk.embed_tokens.weight.float().T
