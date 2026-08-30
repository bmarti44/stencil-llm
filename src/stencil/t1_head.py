# ruff: noqa: E501
"""T1 candidate-or-null head (PRESS-PLAN T1 prereg v3, frozen).

Logit layout: index 0 = NULL (linear head on h20, zero-init), 1..n =
typed candidates (cosine(q(h20), k(cand)) / T, T = softplus(t),
t init = softplus_inverse(1) so T starts at exactly 1.0). q/k warm-start
from the pinned legacy selector. Decision rule: best candidate logit
minus NULL logit, strictly positive presses; NULL wins exact ties;
candidate ties resolve to the first index.
"""
import math

import torch
import torch.nn.functional as F

T_INIT = math.log(math.exp(1.0) - 1.0)  # softplus_inverse(1) = 0.5413248546...


class T1Head(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.Wq = torch.nn.Linear(2048, 64)
        self.Wk = torch.nn.Linear(2048, 64)
        self.null_head = torch.nn.Linear(2048, 1)
        torch.nn.init.zeros_(self.null_head.weight)
        torch.nn.init.zeros_(self.null_head.bias)
        self.t = torch.nn.Parameter(torch.tensor(T_INIT))

    def warm_start(self, legacy_state: dict):
        self.Wq.load_state_dict(legacy_state["Wq"])
        self.Wk.load_state_dict(legacy_state["Wk"])

    def forward(self, h20, cand_feats):
        """h20 [2048], cand_feats [n, 2048] -> logits [n+1] (0 = NULL)."""
        T = F.softplus(self.t)
        null_logit = self.null_head(h20).squeeze(-1)
        if cand_feats is None or cand_feats.shape[0] == 0:
            return null_logit[None]
        q = F.normalize(self.Wq(h20), dim=0)
        k = F.normalize(self.Wk(cand_feats), dim=1)
        return torch.cat([null_logit[None], (q @ k.T) / T])


def decide(logits):
    """-> candidate index (0-based among candidates) or None for NULL."""
    if logits.shape[0] <= 1:
        return None
    cands = logits[1:]
    j = int(cands.argmax())  # torch argmax returns the first maximal index
    return j if float(cands[j]) - float(logits[0]) > 0 else None


def margin_loss(logits, live_idx, margin: float = 0.1):
    """Decision-aligned hinge (prereg v3). live_idx is the 0-based
    CANDIDATE index for active rows, None for inactive rows. Rows with no
    candidates carry zero loss."""
    if logits.shape[0] <= 1:
        return logits.sum() * 0.0
    null_l = logits[0]
    cands = logits[1:]
    if live_idx is not None:
        others = torch.cat([cands[:live_idx], cands[live_idx + 1:]])
        rival = torch.max(null_l, others.max()) if others.shape[0] else null_l
        return F.relu(rival + margin - cands[live_idx])
    return F.relu(cands.max() + margin - null_l)
