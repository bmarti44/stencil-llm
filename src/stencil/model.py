"""Shared transformer, recurrent controllers, and Phase 2 proof helpers."""

from __future__ import annotations

import math
from collections import OrderedDict

import torch
from torch import nn
from torch.nn import functional as F

from stencil.config import Config
from stencil.determinism import named_generator


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


class Attention(nn.Module):
    def __init__(self, config: Config, layer_index: int) -> None:
        super().__init__()
        self.d_model = config.d_model
        self.n_heads = config.n_heads
        if config.d_model % config.n_heads:
            raise ValueError("d_model must be divisible by n_heads")
        self.head_dim = config.d_model // config.n_heads
        if self.head_dim % 2:
            raise ValueError("RoPE head dimension must be even")
        self.window = None if config.variant == "b0_full" else config.window
        self.rope_theta = config.rope_theta
        self.layer_index = layer_index
        self.q = nn.Linear(config.d_model, config.d_model, bias=False)
        self.k = nn.Linear(config.d_model, config.d_model, bias=False)
        self.v = nn.Linear(config.d_model, config.d_model, bias=False)
        self.o = nn.Linear(config.d_model, config.d_model, bias=False)

    def _rope(self, value: torch.Tensor) -> torch.Tensor:
        length = value.shape[2]
        frequency = self.rope_theta ** (
            -torch.arange(0, self.head_dim, 2, device=value.device, dtype=value.dtype)
            / self.head_dim
        )
        angle = (
            torch.arange(length, device=value.device, dtype=value.dtype)[:, None]
            * frequency[None]
        )
        cosine = angle.cos()[None, None]
        sine = angle.sin()[None, None]
        even, odd = value[..., 0::2], value[..., 1::2]
        return torch.stack(
            (even * cosine - odd * sine, even * sine + odd * cosine), dim=-1
        ).flatten(-2)

    def forward(self, x: torch.Tensor, gates: torch.Tensor | None) -> torch.Tensor:
        batch, length, _ = x.shape

        def reshape(value: torch.Tensor) -> torch.Tensor:
            return value.view(batch, length, self.n_heads, self.head_dim).transpose(
                1, 2
            )

        q = self._rope(reshape(self.q(x)))
        k = self._rope(reshape(self.k(x)))
        v = reshape(self.v(x))
        positions = torch.arange(length, device=x.device)
        lag = positions[:, None] - positions[None, :]
        mask = lag >= 0
        if self.window is not None:
            mask = mask & (lag < self.window)
        heads = F.scaled_dot_product_attention(q, k, v, attn_mask=mask)
        if gates is not None:
            heads = heads * gates.transpose(1, 2).unsqueeze(-1)
        merged = heads.transpose(1, 2).contiguous().view(batch, length, self.d_model)
        return self.o(merged)


class Block(nn.Module):
    def __init__(self, config: Config, layer_index: int) -> None:
        super().__init__()
        self.attention_norm = nn.LayerNorm(config.d_model, eps=1e-5)
        self.attention = Attention(config, layer_index)
        self.mlp_norm = nn.LayerNorm(config.d_model, eps=1e-5)
        self.up = nn.Linear(config.d_model, config.d_ff, bias=False)
        self.down = nn.Linear(config.d_ff, config.d_model, bias=False)

    def forward(self, x: torch.Tensor, gates: torch.Tensor | None) -> torch.Tensor:
        x = x + self.attention(self.attention_norm(x), gates)
        x = x + self.down(F.gelu(self.up(self.mlp_norm(x))))
        return x


class StencilTransformer(nn.Module):
    """One shared decoder-only transformer assembled into all six variants."""

    def __init__(self, config: Config) -> None:
        super().__init__()
        if config.variant not in {"b0_full", "b0_local", "b1", "b2", "m1", "m1b"}:
            raise ValueError("unknown model variant")
        self.config = config
        self.token_embedding = nn.Embedding(config.vocab, config.d_model)
        self.blocks = nn.ModuleList(
            [Block(config, index) for index in range(config.n_layers)]
        )
        self.final_norm = nn.LayerNorm(config.d_model, eps=1e-5)
        self.lm_head = nn.Linear(config.d_model, config.vocab, bias=False)

        generator = named_generator(config.seed_init, "init")
        self._initialize_base(generator)
        pathway_generator = torch.Generator(device="cpu")
        pathway_generator.set_state(generator.get_state())
        self.controller: nn.Module | None = None
        self.gate_weight: nn.Parameter | None = None
        self.gate_bias: nn.Parameter | None = None
        self.b1_weight: nn.Parameter | None = None
        if config.variant in {"m1", "m1b"}:
            self.controller = OscillatorController(config, pathway_generator)
        elif config.variant == "b2":
            self.controller = DecayCell(
                config.d_model, 128, generator=pathway_generator
            )
        if config.variant in {"m1", "m1b", "b2"}:
            self.gate_weight = nn.Parameter(
                torch.empty(config.n_layers, config.n_heads, 128)
            )
            self.gate_bias = nn.Parameter(torch.zeros(config.n_layers, config.n_heads))
            nn.init.normal_(
                self.gate_weight,
                mean=0.0,
                std=1e-3,
                generator=pathway_generator,
            )
        elif config.variant == "b1":
            self.b1_weight = nn.Parameter(
                torch.empty(config.n_layers, config.n_heads, config.d_model)
            )
            nn.init.normal_(
                self.b1_weight,
                mean=0.0,
                std=0.02,
                generator=pathway_generator,
            )

    def _initialize_base(self, generator: torch.Generator) -> None:
        nn.init.normal_(
            self.token_embedding.weight, mean=0.0, std=0.02, generator=generator
        )
        for block in self.blocks:
            for linear in (
                block.attention.q,
                block.attention.k,
                block.attention.v,
                block.attention.o,
                block.up,
                block.down,
            ):
                nn.init.normal_(linear.weight, mean=0.0, std=0.02, generator=generator)
            nn.init.ones_(block.attention_norm.weight)
            nn.init.zeros_(block.attention_norm.bias)
            nn.init.ones_(block.mlp_norm.weight)
            nn.init.zeros_(block.mlp_norm.bias)
        nn.init.ones_(self.final_norm.weight)
        nn.init.zeros_(self.final_norm.bias)
        nn.init.normal_(self.lm_head.weight, mean=0.0, std=0.02, generator=generator)

    def receptive_field(self) -> int:
        return self.config.n_layers * (self.config.window - 1)

    def forward(
        self, tokens: torch.Tensor, *, gate_identity: bool = False
    ) -> torch.Tensor:
        return self.forward_embeddings(
            self.token_embedding(tokens), gate_identity=gate_identity
        )

    def forward_embeddings(
        self, embeddings: torch.Tensor, *, gate_identity: bool = False
    ) -> torch.Tensor:
        if gate_identity and self.config.variant in {"b0_full", "b0_local"}:
            raise ValueError("baseline has no gate to bypass")
        control = None
        if self.controller is not None:
            control = self.controller(embeddings)
        x = embeddings
        for layer_index, block in enumerate(self.blocks):
            normalized = block.attention_norm(x)
            gates = None
            if self.config.variant == "b1":
                if gate_identity:
                    gates = x.new_ones(x.shape[0], x.shape[1], self.config.n_heads)
                else:
                    assert self.b1_weight is not None
                    gates = torch.sigmoid(
                        torch.einsum(
                            "btd,hd->bth", normalized, self.b1_weight[layer_index]
                        )
                    )
            elif self.gate_weight is not None:
                if gate_identity:
                    gates = x.new_ones(x.shape[0], x.shape[1], self.config.n_heads)
                else:
                    assert control is not None and self.gate_bias is not None
                    gates = 2 * torch.sigmoid(
                        torch.einsum(
                            "btc,hc->bth", control, self.gate_weight[layer_index]
                        )
                        + self.gate_bias[layer_index]
                    )
            x = x + block.attention(normalized, gates)
            x = x + block.down(F.gelu(block.up(block.mlp_norm(x))))
        return self.lm_head(self.final_norm(x))


def assert_stable(module: nn.Module) -> None:
    cells = [child for child in module.modules() if isinstance(child, OscillatorCell)]
    if not cells:
        raise ValueError("stability check requires at least one oscillator")
    for cell in cells:
        if not torch.all(cell.dt * torch.sqrt(cell.A) < 2):
            raise ValueError("oscillator stability bound violated")


def count_params(module: nn.Module) -> int:
    return sum(
        parameter.numel()
        for parameter in module.parameters()
        if parameter.requires_grad
    )


def _config_param_count(config: Config) -> int:
    d = config.d_model
    base = (
        2 * config.vocab * d
        + config.n_layers * (4 * d * d + 2 * d * config.d_ff + 4 * d)
        + 2 * d
    )
    gates = config.n_layers * config.n_heads * (128 + 1)
    if config.variant == "b1":
        return base + config.n_layers * config.n_heads * d
    if config.variant == "b2":
        return base + 128 * d + 128 + gates
    if config.variant in {"m1", "m1b"}:
        assert config.osc_pairs is not None
        m = config.osc_pairs
        pathway = m * d + 3 * m * m + 2 * m + gates
        if config.variant == "m1b":
            pathway += 2 * m
        return base + pathway
    return base


def _base_config(variant: str, d_ff: int, seed_init: int) -> Config:
    oscillatory = variant in {"m1", "m1b"}
    return Config(
        seed_data=0,
        seed_init=seed_init,
        seed_train=0,
        variant=variant,
        d_model=256,
        n_layers=4,
        n_heads=4,
        d_ff=d_ff,
        window=64,
        vocab=64,
        context_len=2052,
        rope_theta=10_000.0,
        osc_pairs=64 if oscillatory else None,
        osc_cells=2 if oscillatory else None,
        period_min=8.0 if oscillatory else None,
        period_max=4096.0 if oscillatory else None,
        damping_learnable=(variant == "m1b") if oscillatory else None,
        task="a",
        seed_rules=0,
        task_N=2048,
        task_k=8,
        task_R=None,
        task_delay_min=None,
        task_delay_max=None,
        task_P=None,
        task_queries=None,
        task_placement=None,
        lr=3e-4,
        lr_min=3e-5,
        warmup=500,
        steps=20_000,
        batch=64,
        clip=1.0,
        adam_beta1=0.9,
        adam_beta2=0.95,
        adam_eps=1e-8,
        weight_decay=0.1,
    )


def build_matched_configs(seed_init: int = 0) -> OrderedDict[str, Config]:
    """Choose the first d_ff multiple of eight within 1% of M1b's count."""
    order = ("b0_full", "b0_local", "b1", "b2", "m1", "m1b")
    fixed = {
        variant: _base_config(variant, 1024, seed_init) for variant in ("m1", "m1b")
    }
    target = _config_param_count(fixed["m1b"])
    configs: OrderedDict[str, Config] = OrderedDict()
    for variant in order:
        if variant in fixed:
            configs[variant] = fixed[variant]
            continue
        for width in range(8, 4097, 8):
            candidate = _base_config(variant, width, seed_init)
            count = _config_param_count(candidate)
            if abs(count - target) <= 0.01 * max(count, target):
                configs[variant] = candidate
                break
        else:
            raise RuntimeError(f"no matching d_ff found for {variant}")
    return configs
