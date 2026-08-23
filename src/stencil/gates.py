"""Headwise gate projection and post-attention application."""

from __future__ import annotations

import torch


def apply_headwise_gate(heads: torch.Tensor, gates: torch.Tensor) -> torch.Tensor:
    """Apply one scalar gate per batch, token, and attention head."""
    return heads * gates.transpose(1, 2).unsqueeze(-1)


def project_b1_gate(normalized: torch.Tensor, weight: torch.Tensor) -> torch.Tensor:
    """Project B1's post-norm layer input to bias-free headwise gates."""
    return torch.sigmoid(torch.einsum("btd,hd->bth", normalized, weight))


def project_control_gate(
    control: torch.Tensor,
    weight: torch.Tensor,
    bias: torch.Tensor,
) -> torch.Tensor:
    """RMS-normalize recurrent control and project it to headwise gates."""
    control_rms = torch.sqrt(control.square().mean(dim=-1, keepdim=True) + 1e-8)
    normalized_control = control / control_rms
    return 2 * torch.sigmoid(
        torch.einsum("btc,hc->bth", normalized_control, weight) + bias
    )
