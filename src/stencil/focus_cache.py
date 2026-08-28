# ruff: noqa: E501
"""Focus cache: event-gated keyed memory for the current task (GPT2-PLAN era v8).

Design per results/gpt2-goal-review.md (sol) with the fable-review fixes:
- contextual writer over blocks 0-7 hidden states (not static embeddings);
- salience (span membership) and commit (statement end) are HARD, DETACHED
  binary gates in the forward pass, trained only by their direct BCE teachers
  (the v7 lesson: downstream gradients through the gate are poison);
- a commit performs a HARD write: same-key overwrite, else allocate; filler
  causes exactly zero state change (no soft decay anywhere);
- values are NOT RMS-normalized (the fable lesson: a 2%-scale signal is a
  silent killer); the read is query-conditioned soft attention over slots and
  feeds the validated blocks-8-11 additive injection;
- the cache state is an explicit input/output so it can be carried across
  context chunks (compaction verification).
"""
from __future__ import annotations

from dataclasses import dataclass, field

import torch
import torch.nn.functional as F
from torch import nn


@dataclass
class CacheState:
    """Per-sequence slot store keyed by explicit slot id (R1 fix: ids allow
    teacher-forced addressing during training). Tensors are graph-connected
    during training; call detached() before carrying across chunks."""

    slots: dict[int, tuple[torch.Tensor, torch.Tensor]] = field(default_factory=dict)

    @property
    def keys(self) -> list[torch.Tensor]:
        return [self.slots[i][0] for i in sorted(self.slots)]

    @property
    def vals(self) -> list[torch.Tensor]:
        return [self.slots[i][1] for i in sorted(self.slots)]

    def detached(self) -> CacheState:
        return CacheState(
            slots={
                i: (k.detach().clone(), v.detach().clone())
                for i, (k, v) in self.slots.items()
            }
        )


class FocusCache(nn.Module):
    MATCH_THRESHOLD = 0.7

    def __init__(
        self,
        d_model: int = 768,
        n_slots: int = 8,
        d_key: int = 32,
        d_val: int = 128,
        *,
        generator: torch.Generator,
    ) -> None:
        super().__init__()
        self.n_slots = n_slots
        self.d_key = d_key
        self.d_val = d_val
        self.writer = nn.Linear(d_model, 256)
        self.key_mlp = nn.Sequential(nn.Linear(256, 64), nn.GELU(), nn.Linear(64, d_key))
        self.val_mlp = nn.Sequential(nn.Linear(256, 256), nn.GELU(), nn.Linear(256, d_val))
        self.query = nn.Linear(d_model, d_key)
        self.salience = nn.Linear(d_model, 1)
        self.commit = nn.Linear(d_model, 1)
        linears = [self.writer, self.query]
        linears += [m for m in self.key_mlp if isinstance(m, nn.Linear)]
        linears += [m for m in self.val_mlp if isinstance(m, nn.Linear)]
        for lin in linears:
            nn.init.normal_(lin.weight, std=0.02, generator=generator)
            nn.init.zeros_(lin.bias)
        for gate in (self.salience, self.commit):
            # Zero weight + negative bias: EXACTLY closed at init regardless
            # of hidden-state scale (contextual states have RMS ~50-150, so a
            # random weight would leak). BCE supervision opens them.
            nn.init.zeros_(gate.weight)
            nn.init.constant_(gate.bias, -3.0)

    def forward(
        self,
        h: torch.Tensor,  # (b, t, d_model) contextual states from blocks 0-7
        *,
        states: list[CacheState] | None = None,
        sal_override: torch.Tensor | None = None,     # (b, t) bool, teacher/tests
        commit_override: torch.Tensor | None = None,  # (b, t) bool, teacher/tests
        slot_override: torch.Tensor | None = None,    # (b, t) long, -1 = learned
    ) -> tuple[torch.Tensor, list[CacheState], dict]:
        b, t, _ = h.shape
        sal_logits = self.salience(h).squeeze(-1)
        commit_logits = self.commit(h).squeeze(-1)
        # Hard, detached gates: forward is exactly binary; the gates learn
        # only from their direct BCE supervision.
        sal = (
            sal_override
            if sal_override is not None
            else (torch.sigmoid(sal_logits) > 0.5).detach()
        )
        com = (
            commit_override
            if commit_override is not None
            else (torch.sigmoid(commit_logits) > 0.5).detach()
        )
        w = self.writer(h)  # (b, t, 256)
        states = [CacheState() for _ in range(b)] if states is None else states
        code = h.new_zeros(b, t, self.d_val)
        commit_records: list[tuple[int, int, torch.Tensor, torch.Tensor, int]] = []  # (batch, pos, val, key, slot_id)
        for i in range(b):
            st = states[i]
            # Writes: replay commits left to right, snapshotting the state at
            # each boundary so reads use the state as of each segment start.
            boundaries: list[int] = []
            snapshots: list[CacheState] = [CacheState(slots=dict(st.slots))]
            prev = -1
            for p in [int(x) for x in torch.nonzero(com[i]).flatten()]:
                span = [q for q in range(prev + 1, p + 1) if bool(sal[i, q])]
                prev = p
                if not span:
                    continue
                enc = w[i, span].mean(dim=0)
                key = self.key_mlp(enc)
                val = self.val_mlp(enc)
                if slot_override is not None and int(slot_override[i, p]) >= 0:
                    slot = int(slot_override[i, p])  # teacher-forced addressing
                else:
                    slot = self._address(st, key)
                st.slots[slot] = (key, val)
                boundaries.append(p)
                snapshots.append(CacheState(slots=dict(st.slots)))
                commit_records.append((i, p, val, key, slot))
            # Piecewise reads: a commit at p becomes readable from p+1 on.
            starts = [0] + [p + 1 for p in boundaries]
            ends = [*[p + 1 for p in boundaries], t]
            for seg_idx, (s0, s1) in enumerate(zip(starts, ends, strict=True)):
                if s0 >= s1:
                    continue
                snap = snapshots[seg_idx]
                if not snap.slots:
                    continue
                K = torch.stack(snap.keys)          # (n, d_key)
                V = torch.stack(snap.vals)          # (n, d_val)
                q = self.query(h[i, s0:s1])         # (s, d_key)
                att = F.softmax(q @ K.T / (self.d_key ** 0.5), dim=-1)
                code[i, s0:s1] = att @ V
        return code, states, {
            "sal_logits": sal_logits,
            "commit_logits": commit_logits,
            "commits": commit_records,
        }

    def _address(self, st: CacheState, key: torch.Tensor) -> int:
        """Same-key overwrite above MATCH_THRESHOLD cosine, else allocate
        (lowest-id replacement when full). Hard, deterministic. The key-margin
        loss (train_cache) shapes key_mlp so this matches the taught slots."""
        ids = sorted(st.slots)
        if ids:
            K = torch.stack([st.slots[i][0].detach() for i in ids])
            sims = F.cosine_similarity(K, key.detach().unsqueeze(0), dim=-1)
            best = int(sims.argmax())
            if float(sims[best]) > self.MATCH_THRESHOLD:
                return ids[best]
        if len(ids) >= self.n_slots:
            return ids[0]
        return (max(ids) + 1) if ids else 0
