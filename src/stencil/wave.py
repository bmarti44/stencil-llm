# ruff: noqa: E501
"""Internal-wave controller (INTERNAL-WAVE-PLAN W0 skeleton).

Emits a nonnegative, bounded attention-bias row over prompt positions:
b = g * softmax(q K'^T / 8), q = W_q h20, K' = W_k K,
g = beta_max * sigmoid(w_g . h20). Fully differentiable through the
frozen trunk's pre-softmax attn_bias path. Architecture parameters
(notably beta_max) are frozen at the checkpoint-i review.
"""
import torch
import torch.nn.functional as F


class WaveController(torch.nn.Module):
    def __init__(self, beta_max: float = 4.0):
        super().__init__()
        self.beta_max = beta_max
        self.W_q = torch.nn.Linear(2048, 64)
        self.W_k = torch.nn.Linear(2048, 64)
        self.w_g = torch.nn.Linear(2048, 1)

    def field(self, H, K):
        """H [T, 2048] generation states, K [P, 2048] prompt features
        -> bias field [T, P]."""
        q = self.W_q(H)                      # [T, 64]
        k = self.W_k(K)                      # [P, 64]
        attn = F.softmax(q @ k.T / 8.0, dim=-1)
        g = self.beta_max * torch.sigmoid(self.w_g(H)).squeeze(-1)  # [T]
        return g[:, None] * attn

    def forward(self, h20, K):
        """Single-row convenience: h20 [2048] -> bias row [P]."""
        return self.field(h20[None], K)[0]
