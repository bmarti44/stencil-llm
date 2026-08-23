"""Oscillator and decay control pathways plus their sequential proof helpers."""

from __future__ import annotations

import math

import torch
from torch import nn
from torch.nn import functional as F

from stencil.config import Config


def _inverse_softplus(value: torch.Tensor) -> torch.Tensor:
    return value + torch.log(-torch.expm1(-value))


def discrete_invariant(
    y: torch.Tensor,
    z: torch.Tensor,
    a: torch.Tensor,
    dt: float = 1.0,
) -> torch.Tensor:
    """Return symplectic Euler's exactly conserved modified energy.

    Substitution of ``z' = z-dt*A*y`` and ``y' = y+dt*z'`` into this
    quadratic cancels every term, giving H_d' = H_d when forcing and damping
    are zero: H_d = z^2 + A*y^2 - dt*A*y*z.
    """
    return z.square() + a * y.square() - dt * a * y * z


class OscillatorCell(nn.Module):
    """Sequential unified conservative/implicitly damped oscillator cell."""

    def __init__(
        self,
        input_dim: int,
        pairs: int,
        period_min: float,
        period_max: float,
        damping_learnable: bool,
        *,
        generator: torch.Generator,
        dtype: torch.dtype = torch.float32,
        dt: float = 1.0,
    ) -> None:
        super().__init__()
        if input_dim < 1 or pairs < 1:
            raise ValueError("input_dim and pairs must be positive")
        if not 0 < period_min <= period_max:
            raise ValueError("period bounds must satisfy 0 < min <= max")
        self.input_dim = input_dim
        self.pairs = pairs
        self.dt = dt
        self.damping_learnable = damping_learnable
        periods = torch.logspace(
            math.log10(period_min),
            math.log10(period_max),
            pairs,
            dtype=dtype,
        )
        a = (2 * math.pi / periods).square()
        self.a_raw = nn.Parameter(_inverse_softplus(a))
        if damping_learnable:
            self.g_raw = nn.Parameter(torch.full((pairs,), -9.0, dtype=dtype))
        else:
            self.register_buffer("g_zero", torch.zeros(pairs, dtype=dtype))
        self.B = nn.Parameter(torch.empty(pairs, input_dim, dtype=dtype))
        nn.init.normal_(self.B, mean=0.0, std=0.02, generator=generator)

    @property
    def A(self) -> torch.Tensor:
        return F.softplus(self.a_raw)

    def damping(self, *, zero_damping: bool = False) -> torch.Tensor:
        if zero_damping:
            if not self.damping_learnable:
                raise ValueError("zero_damping is only valid for learnable damping")
            return torch.zeros_like(self.g_raw)
        if self.damping_learnable:
            return F.softplus(self.g_raw)
        return self.g_zero

    def forward(
        self,
        inputs: torch.Tensor,
        *,
        initial: tuple[torch.Tensor, torch.Tensor] | None = None,
        zero_damping: bool = False,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        if inputs.ndim != 3 or inputs.shape[-1] != self.input_dim:
            raise ValueError("inputs must have shape (batch, length, input_dim)")
        batch = inputs.shape[0]
        if initial is None:
            y = inputs.new_zeros(batch, self.pairs)
            z = inputs.new_zeros(batch, self.pairs)
        else:
            y, z = initial
            if y.ndim == 1:
                y = y.expand(batch, -1)
            if z.ndim == 1:
                z = z.expand(batch, -1)
            if y.shape != (batch, self.pairs) or z.shape != (batch, self.pairs):
                raise ValueError(
                    "initial states must have shape (pairs,) or (batch,pairs)"
                )
        a = self.A
        g = self.damping(zero_damping=zero_damping)
        denominator = 1 + self.dt * g
        ys: list[torch.Tensor] = []
        zs: list[torch.Tensor] = []
        forcing = F.linear(inputs, self.B)
        for position in range(inputs.shape[1]):
            # The homogeneous 2x2 map has determinant 1/(1+dt*G).  In the
            # stable complex-modal regime |lambda|^2 equals that determinant,
            # so modal quadratic energy decays exactly as (1+dt*G)^(-n), not
            # with a doubled exponent.
            z = (z + self.dt * (-a * y + forcing[:, position])) / denominator
            y = y + self.dt * z
            ys.append(y)
            zs.append(z)
        return torch.stack(ys, dim=1), torch.stack(zs, dim=1)


class DecayCell(nn.Module):
    """Sequential first-order diagonal decay controller used by B2."""

    def __init__(
        self,
        input_dim: int,
        state_dim: int,
        *,
        generator: torch.Generator,
        dtype: torch.dtype = torch.float32,
    ) -> None:
        super().__init__()
        self.input_dim = input_dim
        self.state_dim = state_dim
        raw = math.log(0.999 / 0.001)
        self.raw = nn.Parameter(torch.full((state_dim,), raw, dtype=dtype))
        self.B = nn.Parameter(torch.empty(state_dim, input_dim, dtype=dtype))
        nn.init.normal_(self.B, mean=0.0, std=0.02, generator=generator)

    @property
    def decay(self) -> torch.Tensor:
        return torch.sigmoid(self.raw)

    def forward(
        self, inputs: torch.Tensor, *, initial: torch.Tensor | None = None
    ) -> torch.Tensor:
        if inputs.ndim != 3 or inputs.shape[-1] != self.input_dim:
            raise ValueError("inputs must have shape (batch, length, input_dim)")
        batch = inputs.shape[0]
        state = inputs.new_zeros(batch, self.state_dim) if initial is None else initial
        if state.ndim == 1:
            state = state.expand(batch, -1)
        if state.shape != (batch, self.state_dim):
            raise ValueError("initial state has the wrong shape")
        forcing = F.linear(inputs, self.B)
        states: list[torch.Tensor] = []
        for position in range(inputs.shape[1]):
            state = self.decay * state + forcing[:, position]
            states.append(state)
        return torch.stack(states, dim=1)


class OscillatorController(nn.Module):
    def __init__(self, config: Config, generator: torch.Generator) -> None:
        super().__init__()
        if config.osc_pairs is None or config.osc_cells != 2:
            raise ValueError("oscillator variants require exactly two configured cells")
        if config.period_min is None or config.period_max is None:
            raise ValueError("oscillator period bounds are required")
        learnable = config.variant == "m1b"
        self.cells = nn.ModuleList(
            [
                OscillatorCell(
                    config.d_model,
                    config.osc_pairs,
                    config.period_min,
                    config.period_max,
                    learnable,
                    generator=generator,
                ),
                OscillatorCell(
                    config.osc_pairs,
                    config.osc_pairs,
                    config.period_min,
                    config.period_max,
                    learnable,
                    generator=generator,
                ),
            ]
        )
        self.W_a = nn.Parameter(torch.empty(config.osc_pairs, config.osc_pairs))
        self.W_b = nn.Parameter(torch.empty(config.osc_pairs, config.osc_pairs))
        nn.init.normal_(self.W_a, mean=0.0, std=0.02, generator=generator)
        nn.init.normal_(self.W_b, mean=0.0, std=0.02, generator=generator)

    def forward(self, embeddings: torch.Tensor) -> torch.Tensor:
        y1, _ = self.cells[0](embeddings)
        glu = F.linear(y1, self.W_a) * torch.sigmoid(F.linear(y1, self.W_b))
        y2, z2 = self.cells[1](glu)
        return torch.cat((y2, z2), dim=-1)


def assert_stable(module: nn.Module) -> None:
    cells = [child for child in module.modules() if isinstance(child, OscillatorCell)]
    if not cells:
        raise ValueError("stability check requires at least one oscillator")
    for cell in cells:
        if not torch.all(cell.dt * torch.sqrt(cell.A) < 2):
            raise ValueError("oscillator stability bound violated")
