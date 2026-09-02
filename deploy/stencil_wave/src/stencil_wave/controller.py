"""The frozen WaveController (INTERNAL-WAVE-PLAN v3.1, selection A2).

264,321 parameters: W_q / W_k 2048->64 (the selector), w_g 2048->1 (the
gain head; loaded for completeness, unused by the ledger's selection).
Weights are the research checkpoint results/qwen/b3-ce-s0.pt converted
bitwise to ``weights/controller.safetensors``.
"""
from __future__ import annotations

from pathlib import Path

import torch
import torch.nn.functional as F

CONTROLLER_PATH = Path(__file__).with_name("weights") / "controller.safetensors"
N_PARAMS = 264_321


class WaveController(torch.nn.Module):
    def __init__(self, beta_max: float = 1.0):
        super().__init__()
        self.beta_max = beta_max
        self.W_q = torch.nn.Linear(2048, 64)
        self.W_k = torch.nn.Linear(2048, 64)
        self.w_g = torch.nn.Linear(2048, 1)

    def gain(self, h20):
        return self.beta_max * torch.sigmoid(self.w_g(h20)).squeeze(-1)

    def scores(self, query_h20: torch.Tensor, keys: torch.Tensor) -> torch.Tensor:
        """cos(W_q q, W_k k) for one query [2048] against keys [N, 2048]."""
        q = F.normalize(self.W_q(query_h20.float().reshape(1, -1)), dim=-1)
        k = F.normalize(self.W_k(keys.float()), dim=-1)
        return (q @ k.T)[0]

    @classmethod
    def load(cls, path: Path | str = CONTROLLER_PATH, device=None) -> WaveController:
        from safetensors.torch import load_file

        ctrl = cls()
        ctrl.load_state_dict(load_file(str(path)), strict=True)
        n = sum(p.numel() for p in ctrl.parameters())
        if n != N_PARAMS:
            raise RuntimeError(f"controller has {n} parameters, expected {N_PARAMS}")
        return ctrl.to(device).eval() if device is not None else ctrl.eval()
