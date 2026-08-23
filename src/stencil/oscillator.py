"""Oscillator and decay control pathways plus their sequential proof helpers."""

from __future__ import annotations

import math
from collections.abc import Callable

import torch
from torch import nn
from torch.nn import functional as F

from stencil.config import Config

_SCAN_BLOCK_SIZE = 256


def _configure_inductor_for_determinism() -> None:
    """Pin every Inductor tuning switch used by the compiled scan path."""
    torch._inductor.config.deterministic = True
    torch._inductor.config.max_autotune = False
    torch._inductor.config.coordinate_descent_tuning = False


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


def _interleave_scan_parts(
    first: torch.Tensor,
    odd: torch.Tensor,
    even: torch.Tensor,
    length: int,
) -> torch.Tensor:
    """Interleave recursive scan results along dimension one."""
    if length % 2:
        tail = torch.stack((odd, even), dim=2).flatten(1, 2)
    else:
        paired = torch.stack((odd[:, :-1], even), dim=2).flatten(1, 2)
        tail = torch.cat((paired, odd[:, -1:]), dim=1)
    return torch.cat((first[:, :1], tail), dim=1)


def _scan_affine_2x2(
    transform: tuple[torch.Tensor, ...],
) -> tuple[torch.Tensor, ...]:
    """Inclusive fixed-tree scan of per-mode two-dimensional affine maps."""
    length = transform[0].shape[1]
    if length < 2:
        return transform

    left = tuple(value[:, 0:-1:2] for value in transform)
    right = tuple(value[:, 1::2] for value in transform)
    l00, l01, l10, l11, ld0, ld1 = left
    r00, r01, r10, r11, rd0, rd1 = right
    reduced = _scan_affine_2x2(
        (
            r00 * l00 + r01 * l10,
            r00 * l01 + r01 * l11,
            r10 * l00 + r11 * l10,
            r10 * l01 + r11 * l11,
            r00 * ld0 + r01 * ld1 + rd0,
            r10 * ld0 + r11 * ld1 + rd1,
        )
    )

    even_source = tuple(value[:, 2::2] for value in transform)
    prefix = reduced if length % 2 else tuple(value[:, :-1] for value in reduced)
    l00, l01, l10, l11, ld0, ld1 = prefix
    r00, r01, r10, r11, rd0, rd1 = even_source
    even = (
        r00 * l00 + r01 * l10,
        r00 * l01 + r01 * l11,
        r10 * l00 + r11 * l10,
        r10 * l01 + r11 * l11,
        r00 * ld0 + r01 * ld1 + rd0,
        r10 * ld0 + r11 * ld1 + rd1,
    )
    return tuple(
        _interleave_scan_parts(original, odd, paired, length)
        for original, odd, paired in zip(transform, reduced, even, strict=True)
    )


def _scan_affine_scalar(
    multiplier: torch.Tensor, drive: torch.Tensor
) -> tuple[torch.Tensor, torch.Tensor]:
    """Inclusive fixed-tree scan of scalar affine maps per state channel."""
    length = drive.shape[1]
    if length < 2:
        return multiplier, drive

    left_multiplier = multiplier[:, 0:-1:2]
    right_multiplier = multiplier[:, 1::2]
    left_drive = drive[:, 0:-1:2]
    right_drive = drive[:, 1::2]
    odd_multiplier, odd_drive = _scan_affine_scalar(
        right_multiplier * left_multiplier,
        right_multiplier * left_drive + right_drive,
    )

    even_multiplier = multiplier[:, 2::2]
    even_drive = drive[:, 2::2]
    prefix_multiplier = (
        odd_multiplier if length % 2 else odd_multiplier[:, :-1]
    )
    prefix_drive = odd_drive if length % 2 else odd_drive[:, :-1]
    paired_multiplier = even_multiplier * prefix_multiplier
    paired_drive = even_multiplier * prefix_drive + even_drive
    return (
        _interleave_scan_parts(
            multiplier, odd_multiplier, paired_multiplier, length
        ),
        _interleave_scan_parts(drive, odd_drive, paired_drive, length),
    )


class OscillatorCell(nn.Module):
    """Unified conservative/implicitly damped oscillator cell."""

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
        use_compiled_scan: bool = False,
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
        self._use_scan = True
        self._use_compiled_scan = use_compiled_scan
        self._compiled_scan: Callable[..., tuple[torch.Tensor, torch.Tensor]] | None = (
            None
        )
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

    def _forward_sequential(
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

    def _forward_scan(
        self,
        inputs: torch.Tensor,
        *,
        initial: tuple[torch.Tensor, torch.Tensor] | None = None,
        zero_damping: bool = False,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        if inputs.ndim != 3 or inputs.shape[-1] != self.input_dim:
            raise ValueError("inputs must have shape (batch, length, input_dim)")
        batch, length, _ = inputs.shape
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
        forcing = F.linear(inputs, self.B)
        block_size = _SCAN_BLOCK_SIZE
        block_count = (length + block_size - 1) // block_size
        padded_length = block_count * block_size
        if padded_length != length:
            forcing = F.pad(forcing, (0, 0, 0, padded_length - length))
        forcing = forcing.reshape(batch, block_count, block_size, self.pairs)

        shape = (1, block_count, self.pairs)
        one = torch.ones(shape, dtype=inputs.dtype, device=inputs.device)
        zero = torch.zeros(shape, dtype=inputs.dtype, device=inputs.device)
        m00, m01, m10, m11 = one, zero, zero, one
        d0 = inputs.new_zeros(batch, block_count, self.pairs)
        d1 = inputs.new_zeros(batch, block_count, self.pairs)
        for position in range(block_size):
            next_m10 = (m10 + self.dt * (-a * m00)) / denominator
            next_m11 = (m11 + self.dt * (-a * m01)) / denominator
            m00 = m00 + self.dt * next_m10
            m01 = m01 + self.dt * next_m11
            m10, m11 = next_m10, next_m11
            next_d1 = (
                d1 + self.dt * (-a * d0 + forcing[:, :, position])
            ) / denominator
            d0 = d0 + self.dt * next_d1
            d1 = next_d1

        p00, p01, p10, p11, pd0, pd1 = _scan_affine_2x2(
            (m00, m01, m10, m11, d0, d1)
        )
        end_y = p00 * y[:, None] + p01 * z[:, None] + pd0
        end_z = p10 * y[:, None] + p11 * z[:, None] + pd1
        block_y = torch.cat((y[:, None], end_y[:, :-1]), dim=1)
        block_z = torch.cat((z[:, None], end_z[:, :-1]), dim=1)

        ys: list[torch.Tensor] = []
        zs: list[torch.Tensor] = []
        for position in range(block_size):
            block_z = (
                block_z
                + self.dt * (-a * block_y + forcing[:, :, position])
            ) / denominator
            block_y = block_y + self.dt * block_z
            ys.append(block_y)
            zs.append(block_z)
        all_y = torch.stack(ys, dim=2).flatten(1, 2)
        all_z = torch.stack(zs, dim=2).flatten(1, 2)
        return all_y[:, :length], all_z[:, :length]

    def forward(
        self,
        inputs: torch.Tensor,
        *,
        initial: tuple[torch.Tensor, torch.Tensor] | None = None,
        zero_damping: bool = False,
        use_scan: bool | None = None,
        use_compiled_scan: bool | None = None,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        if use_scan is None:
            use_scan = self._use_scan
        if use_compiled_scan is None:
            use_compiled_scan = self._use_compiled_scan
        if not use_scan:
            implementation = self._forward_sequential
        elif use_compiled_scan:
            if self._compiled_scan is None:
                _configure_inductor_for_determinism()
                self._compiled_scan = torch.compile(
                    self._forward_scan,
                    fullgraph=True,
                    dynamic=False,
                )
            implementation = self._compiled_scan
        else:
            implementation = self._forward_scan
        return implementation(
            inputs, initial=initial, zero_damping=zero_damping
        )


class DecayCell(nn.Module):
    """First-order diagonal decay controller used by B2."""

    def __init__(
        self,
        input_dim: int,
        state_dim: int,
        *,
        generator: torch.Generator,
        dtype: torch.dtype = torch.float32,
        use_compiled_scan: bool = False,
    ) -> None:
        super().__init__()
        self.input_dim = input_dim
        self.state_dim = state_dim
        self._use_scan = True
        self._use_compiled_scan = use_compiled_scan
        self._compiled_scan: Callable[..., torch.Tensor] | None = None
        raw = math.log(0.999 / 0.001)
        self.raw = nn.Parameter(torch.full((state_dim,), raw, dtype=dtype))
        self.B = nn.Parameter(torch.empty(state_dim, input_dim, dtype=dtype))
        nn.init.normal_(self.B, mean=0.0, std=0.02, generator=generator)

    @property
    def decay(self) -> torch.Tensor:
        return torch.sigmoid(self.raw)

    def _forward_sequential(
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

    def _forward_scan(
        self, inputs: torch.Tensor, *, initial: torch.Tensor | None = None
    ) -> torch.Tensor:
        if inputs.ndim != 3 or inputs.shape[-1] != self.input_dim:
            raise ValueError("inputs must have shape (batch, length, input_dim)")
        batch, length, _ = inputs.shape
        state = inputs.new_zeros(batch, self.state_dim) if initial is None else initial
        if state.ndim == 1:
            state = state.expand(batch, -1)
        if state.shape != (batch, self.state_dim):
            raise ValueError("initial state has the wrong shape")
        forcing = F.linear(inputs, self.B)
        block_size = _SCAN_BLOCK_SIZE
        block_count = (length + block_size - 1) // block_size
        padded_length = block_count * block_size
        if padded_length != length:
            forcing = F.pad(forcing, (0, 0, 0, padded_length - length))
        forcing = forcing.reshape(batch, block_count, block_size, self.state_dim)

        multiplier = torch.ones(
            (1, block_count, self.state_dim),
            dtype=inputs.dtype,
            device=inputs.device,
        )
        drive = inputs.new_zeros(batch, block_count, self.state_dim)
        for position in range(block_size):
            multiplier = self.decay * multiplier
            drive = self.decay * drive + forcing[:, :, position]
        prefix_multiplier, prefix_drive = _scan_affine_scalar(multiplier, drive)
        end_state = prefix_multiplier * state[:, None] + prefix_drive
        block_state = torch.cat((state[:, None], end_state[:, :-1]), dim=1)

        states: list[torch.Tensor] = []
        for position in range(block_size):
            block_state = (
                self.decay * block_state + forcing[:, :, position]
            )
            states.append(block_state)
        return torch.stack(states, dim=2).flatten(1, 2)[:, :length]

    def forward(
        self,
        inputs: torch.Tensor,
        *,
        initial: torch.Tensor | None = None,
        use_scan: bool | None = None,
        use_compiled_scan: bool | None = None,
    ) -> torch.Tensor:
        if use_scan is None:
            use_scan = self._use_scan
        if use_compiled_scan is None:
            use_compiled_scan = self._use_compiled_scan
        if not use_scan:
            implementation = self._forward_sequential
        elif use_compiled_scan:
            if self._compiled_scan is None:
                _configure_inductor_for_determinism()
                self._compiled_scan = torch.compile(
                    self._forward_scan,
                    fullgraph=True,
                    dynamic=False,
                )
            implementation = self._compiled_scan
        else:
            implementation = self._forward_scan
        return implementation(inputs, initial=initial)


class CueLatch(nn.Module):
    """Event-driven register that replaces its state only at cue positions."""

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
        self.W_e = nn.Parameter(torch.empty(state_dim, input_dim, dtype=dtype))
        nn.init.normal_(self.W_e, mean=0.0, std=0.02, generator=generator)

    def forward(
        self, embeddings: torch.Tensor, cue_mask: torch.Tensor
    ) -> torch.Tensor:
        if embeddings.ndim != 3 or embeddings.shape[-1] != self.input_dim:
            raise ValueError("embeddings must have shape (batch, length, input_dim)")
        if cue_mask.shape != embeddings.shape[:2] or cue_mask.dtype != torch.bool:
            raise ValueError("cue_mask must be boolean with shape (batch, length)")
        candidates = F.linear(embeddings, self.W_e)
        positions = torch.arange(embeddings.shape[1], device=embeddings.device)
        cue_indices = torch.where(cue_mask, positions[None], -1)
        latest_cue = torch.cummax(cue_indices, dim=1).values
        gather_index = latest_cue.clamp_min(0)[..., None].expand(
            -1, -1, self.state_dim
        )
        latched = torch.gather(candidates, dim=1, index=gather_index)
        return torch.where(latest_cue[..., None] >= 0, latched, 0.0)


class OscillatorController(nn.Module):
    def __init__(
        self,
        config: Config,
        generator: torch.Generator,
        *,
        use_compiled_scan: bool = False,
    ) -> None:
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
                    use_compiled_scan=use_compiled_scan,
                ),
                OscillatorCell(
                    config.osc_pairs,
                    config.osc_pairs,
                    config.period_min,
                    config.period_max,
                    learnable,
                    generator=generator,
                    use_compiled_scan=use_compiled_scan,
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
