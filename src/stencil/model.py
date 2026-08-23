"""Shared base transformer and Phase 2 model-variant assembly."""

from __future__ import annotations

from collections import OrderedDict

import torch
from torch import nn
from torch.nn import functional as F

from stencil.config import Config
from stencil.determinism import named_generator
from stencil.gates import apply_headwise_gate, project_b1_gate, project_control_gate
from stencil.oscillator import DecayCell, OscillatorController


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
            heads = apply_headwise_gate(heads, gates)
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
        pathway_generator = named_generator(config.seed_init, "pathway")
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
                    gates = project_b1_gate(
                        normalized, self.b1_weight[layer_index]
                    )
            elif self.gate_weight is not None:
                if gate_identity:
                    gates = x.new_ones(x.shape[0], x.shape[1], self.config.n_heads)
                else:
                    assert control is not None and self.gate_bias is not None
                    gates = project_control_gate(
                        control,
                        self.gate_weight[layer_index],
                        self.gate_bias[layer_index],
                    )
            x = x + block.attention(normalized, gates)
            x = x + block.down(F.gelu(block.up(block.mlp_norm(x))))
        return self.lm_head(self.final_norm(x))


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
