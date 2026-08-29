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
V_TOK = 12    # max stored value tokens (per-token transcript path)
D_TOK = 128   # per-token projection width
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
        self.pool_q = nn.Parameter(torch.empty(4, D_KEY))     # four-query span pooling
        self.pool_k = nn.Linear(c.d_model, D_KEY)
        self.key_mlp = nn.Sequential(nn.Linear(c.d_model, 256), nn.GELU(), nn.Linear(256, 4 * D_KEY))
        self.val_mean = nn.Sequential(nn.Linear(c.d_model, 1024), nn.GELU(), nn.Linear(1024, D_VAL))
        self.val_tok = nn.Linear(c.d_model, D_TOK)   # per-token value transcript
        self.tok_code = nn.Linear(D_TOK, D_CODE)     # transcript -> code contribution
        self.step_q = nn.Linear(c.d_model, V_TOK)    # which transcript position to read
        self.val_mlp = nn.Sequential(nn.Linear(c.d_model, 1024), nn.GELU(), nn.Linear(1024, D_VAL // 4))
        self.query = nn.Linear(c.d_model, D_KEY)
        self.code_proj = nn.Linear(D_VAL // 4, D_CODE)
        self.inj = nn.ModuleList(nn.Linear(D_CODE, c.d_model, bias=False) for _ in INJ_LAYERS)
        for lin in [m for m in self.key_mlp if isinstance(m, nn.Linear)] + [m for m in self.val_mlp if isinstance(m, nn.Linear)] + [m for m in self.val_mean if isinstance(m, nn.Linear)] + [self.query, self.code_proj, self.pool_k]:
            nn.init.normal_(lin.weight, std=0.02, generator=g)
            nn.init.zeros_(lin.bias)
        nn.init.normal_(self.pool_q, std=1.0, generator=g)  # strong distinct queries: break view symmetry from step 0
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
            span = h[0, lo:hi].float()                       # (s, d)
            att = torch.softmax(self.pool_q @ self.pool_k(span).T / (D_KEY ** 0.5), dim=-1)
            pooled = att @ span                              # (4, d) four views of the span
            # mean path (fast, coarse) + pooled per-view path (precise)
            val = self.val_mean(span.mean(dim=0)) + self.val_mlp(pooled).reshape(-1)
            # per-token transcript of the VALUE tokens (focus.set knows its
            # value argument): identity-preserving by construction.
            transcript = torch.zeros(V_TOK, D_TOK, device=h.device)
            if len(ev) > 5 and ev[4] is not None:
                vlo, vhi = ev[4], min(ev[5], ev[4] + V_TOK)
                transcript[: vhi - vlo] = self.val_tok(h[0, vlo:vhi].float())
            key = self.key_mlp(span.mean(dim=0))             # addressing from the whole note
            state.slots[slot] = (key, torch.cat([val, transcript.reshape(-1)]))
        return state

    def read_inj(self, h: torch.Tensor, state: QwenCacheState) -> dict[int, torch.Tensor]:
        """h: (1, t, d) block-WRITE_LAYER states of the current chunk ->
        per-layer additive injections."""
        if not state.slots:
            return {}
        ids = sorted(state.slots)
        # summary part: 4 sub-entries per slot; transcript part: per-token.
        K = torch.cat([state.slots[i][0].view(4, D_KEY) for i in ids])      # (4n, D_KEY)
        V = torch.cat([state.slots[i][1][:D_VAL].view(4, D_VAL // 4) for i in ids])  # (4n, 256)
        T_ = torch.stack([state.slots[i][1][D_VAL:].view(V_TOK, D_TOK) for i in ids])  # (n, V_TOK, D_TOK)
        q = self.query(h.float())                                            # (1, t, D_KEY)
        att = torch.softmax(q @ K.T / (D_KEY ** 0.5), dim=-1)               # (1, t, 4n)
        code = self.code_proj(att @ V)                                       # (1, t, D_CODE)
        # slot-level attention (sum over each slot's 4 sub-entries) selects
        # which transcript to read; step_q selects the position within it.
        slot_att = att.view(1, -1, len(ids), 4).sum(-1)                      # (1, t, n)
        step_att = torch.softmax(self.step_q(h.float()), dim=-1)             # (1, t, V_TOK)
        chosen = torch.einsum("btn,nvd->btvd", slot_att, T_)                 # (1, t, V_TOK, D_TOK)
        tok_read = torch.einsum("btv,btvd->btd", step_att, chosen)           # (1, t, D_TOK)
        code = code + self.tok_code(tok_read)
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
