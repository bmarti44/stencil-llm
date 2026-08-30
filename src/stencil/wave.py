# ruff: noqa: E501
"""Internal-wave controller — FROZEN (INTERNAL-WAVE-PLAN v3.1 + W0.05
selection A2, 2026-08-30).

e_ti = 8 * cos(q_t, k'_i); q = W_q h20, k' = W_k K, both F.normalized;
b_t = g_t * softmax(e_t) / max(softmax(e_t))   (peak-normalized A2:
per-token cap g_t); g_t = beta_max * sigmoid(w_g h20_t); init: W_q/W_k
default, w_g weight ZERO bias -2.0 (g_0 = 0.1192 * beta_max).
264,321 parameters. Differentiable through the trunk's pre-softmax
attn_bias path.
"""
import torch
import torch.nn.functional as F


class WaveController(torch.nn.Module):
    def __init__(self, beta_max: float = 2.0):
        super().__init__()
        self.beta_max = beta_max
        self.W_q = torch.nn.Linear(2048, 64)
        self.W_k = torch.nn.Linear(2048, 64)
        self.w_g = torch.nn.Linear(2048, 1)
        torch.nn.init.zeros_(self.w_g.weight)
        torch.nn.init.constant_(self.w_g.bias, -2.0)

    def gain(self, h20):
        return self.beta_max * torch.sigmoid(self.w_g(h20)).squeeze(-1)

    def field(self, H, K):
        """H [T, 2048] generation states, K [P, 2048] prompt features
        -> peak-normalized bias field [T, P]."""
        q = F.normalize(self.W_q(H), dim=-1)
        k = F.normalize(self.W_k(K), dim=-1)
        e = 8.0 * (q @ k.T)
        sm = F.softmax(e, dim=-1)
        sm = sm / sm.max(dim=-1, keepdim=True).values
        return self.gain(H)[:, None] * sm

    def forward(self, h20, K):
        return self.field(h20[None], K)[0]
