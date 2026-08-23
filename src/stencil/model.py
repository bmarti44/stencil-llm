"""Shared base transformer and Phase 2 model-variant assembly."""

from __future__ import annotations

from collections import OrderedDict

import torch
from torch import nn
from torch.nn import functional as F

from stencil.config import Config
from stencil.determinism import named_generator
from stencil.gates import apply_headwise_gate, project_b1_gate, project_control_gate
from stencil.oscillator import CueLatch, DecayCell, OscillatorController


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
        self._use_banded = self.window is not None
        self._banded_block_size = None if self.window is None else 8 * self.window
        self.rope_theta = config.rope_theta
        self.layer_index = layer_index
        self.q = nn.Linear(config.d_model, config.d_model, bias=False)
        self.k = nn.Linear(config.d_model, config.d_model, bias=False)
        self.v = nn.Linear(config.d_model, config.d_model, bias=False)
        self.o = nn.Linear(config.d_model, config.d_model, bias=False)
        self.register_buffer("rope_cosine", torch.empty(0), persistent=False)
        self.register_buffer("rope_sine", torch.empty(0), persistent=False)
        self._rope_cache_key: tuple[torch.device, torch.dtype] | None = None

    def _rope_cache(
        self, value: torch.Tensor, required_length: int
    ) -> tuple[torch.Tensor, torch.Tensor]:
        key = (value.device, value.dtype)
        if self._rope_cache_key != key or self.rope_cosine.shape[0] < required_length:
            frequency = self.rope_theta ** (
                -torch.arange(
                    0,
                    self.head_dim,
                    2,
                    device=value.device,
                    dtype=value.dtype,
                )
                / self.head_dim
            )
            angle = (
                torch.arange(
                    required_length,
                    device=value.device,
                    dtype=value.dtype,
                )[:, None]
                * frequency[None]
            )
            self.rope_cosine = angle.cos()
            self.rope_sine = angle.sin()
            self._rope_cache_key = key
        return self.rope_cosine, self.rope_sine

    def _rope(self, value: torch.Tensor, position_offset: int = 0) -> torch.Tensor:
        length = value.shape[2]
        end = position_offset + length
        cosine, sine = self._rope_cache(value, end)
        cosine = cosine[position_offset:end][None, None]
        sine = sine[position_offset:end][None, None]
        even, odd = value[..., 0::2], value[..., 1::2]
        return torch.stack(
            (even * cosine - odd * sine, even * sine + odd * cosine), dim=-1
        ).flatten(-2)

    def _banded_layout(
        self,
        length: int,
        cue_mask: torch.Tensor | None,
        device: torch.device,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        """Return gathered key positions and their validity mask.

        Positions within each row are ordered as old global cues followed by
        the chronological local window.  A cue already in the local window is
        excluded from the global portion, so every allowed key occurs once.
        """
        assert self.window is not None
        queries = torch.arange(length, device=device)
        local_positions = (
            queries[:, None] + torch.arange(1 - self.window, 1, device=device)[None]
        )
        local_valid = local_positions >= 0
        local_positions = local_positions.clamp_min(0)
        if cue_mask is None:
            return local_positions[None], local_valid[None]

        max_cues = int(cue_mask.sum(dim=1).max().item())
        if max_cues:
            all_positions = queries[None].expand(cue_mask.shape[0], -1)
            global_positions = torch.where(cue_mask, all_positions, length)
            global_positions = global_positions.sort(dim=1).values[:, :max_cues]
            global_positions = global_positions[:, None].expand(-1, length, -1)
            global_valid = global_positions <= queries[None, :, None] - self.window
            global_positions = global_positions.clamp_max(length - 1)
        else:
            global_positions = queries.new_empty(cue_mask.shape[0], length, 0)
            global_valid = cue_mask.new_empty(cue_mask.shape[0], length, 0)
        batch = cue_mask.shape[0]
        return (
            torch.cat(
                (global_positions, local_positions[None].expand(batch, -1, -1)),
                dim=-1,
            ),
            torch.cat(
                (global_valid, local_valid[None].expand(batch, -1, -1)),
                dim=-1,
            ),
        )

    def _forward_banded(
        self,
        q: torch.Tensor,
        k: torch.Tensor,
        v: torch.Tensor,
        cue_mask: torch.Tensor | None,
        cue_positions: torch.Tensor | None = None,
        cue_valid: torch.Tensor | None = None,
    ) -> torch.Tensor:
        """Compute exact causal-window attention in O(T * (window + cues))."""
        assert self.window is not None
        batch, _, length, _ = q.shape
        queries = torch.arange(length, device=q.device)
        global_k = None
        global_v = None
        global_positions = None
        if cue_mask is not None:
            if cue_positions is not None or cue_valid is not None:
                if cue_positions is None or cue_valid is None:
                    raise ValueError(
                        "cue positions and validity must be provided together"
                    )
                if (
                    cue_positions.shape != cue_valid.shape
                    or cue_positions.shape[0] != batch
                ):
                    raise ValueError("padded cue tensors have incompatible shapes")
                global_positions = cue_positions
            else:
                max_cues = int(cue_mask.sum(dim=1).max().item())
                all_positions = queries[None].expand(batch, -1)
                global_positions = torch.where(cue_mask, all_positions, length)
                global_positions = global_positions.sort(dim=1).values[:, :max_cues]
                cue_valid = global_positions < length
            if global_positions.shape[1]:
                gather_positions = global_positions.clamp_max(length - 1)
                gather_index = gather_positions[:, None, :, None].expand(
                    -1, self.n_heads, -1, self.head_dim
                )
                global_k = torch.gather(k, 2, gather_index)
                global_v = torch.gather(v, 2, gather_index)

        chunks: list[torch.Tensor] = []
        assert self._banded_block_size is not None
        query_block = self._banded_block_size
        for start in range(0, length, query_block):
            end = min(start + query_block, length)
            key_start = max(0, start - self.window + 1)
            query_positions = queries[start:end]
            local_positions = queries[key_start:end]
            lag = query_positions[:, None] - local_positions[None]
            local_valid = (lag >= 0) & (lag < self.window)
            block_k = k[:, :, key_start:end]
            block_v = v[:, :, key_start:end]

            if global_positions is not None:
                assert global_k is not None and global_v is not None
                global_valid = (
                    (global_positions[:, None]
                    <= query_positions[None, :, None] - self.window)
                    & cue_valid[:, None]
                )
                valid = torch.cat(
                    (
                        global_valid,
                        local_valid[None].expand(batch, -1, -1),
                    ),
                    dim=-1,
                )
                block_k = torch.cat((global_k, block_k), dim=2)
                block_v = torch.cat((global_v, block_v), dim=2)
            else:
                valid = local_valid

            chunks.append(
                F.scaled_dot_product_attention(
                    q[:, :, start:end],
                    block_k,
                    block_v,
                    attn_mask=valid[:, None] if valid.ndim == 3 else valid,
                )
            )
        return torch.cat(chunks, dim=2)

    def forward(
        self,
        x: torch.Tensor,
        gates: torch.Tensor | None,
        cue_mask: torch.Tensor | None = None,
        *,
        use_banded: bool | None = None,
        cue_positions: torch.Tensor | None = None,
        cue_valid: torch.Tensor | None = None,
        position_offset: int = 0,
    ) -> torch.Tensor:
        batch, length, _ = x.shape

        def reshape(value: torch.Tensor) -> torch.Tensor:
            return value.view(batch, length, self.n_heads, self.head_dim).transpose(
                1, 2
            )

        q = self._rope(reshape(self.q(x)), position_offset)
        k = self._rope(reshape(self.k(x)), position_offset)
        v = reshape(self.v(x))
        if cue_mask is not None and (
            cue_mask.shape != (batch, length) or cue_mask.dtype != torch.bool
        ):
            raise ValueError("cue_mask must be boolean with shape (batch, length)")
        if use_banded is None:
            use_banded = self._use_banded
        if use_banded and self.window is not None:
            heads = self._forward_banded(
                q, k, v, cue_mask, cue_positions, cue_valid
            )
        else:
            positions = torch.arange(length, device=x.device)
            lag = positions[:, None] - positions[None, :]
            mask = lag >= 0
            if self.window is not None:
                local = lag < self.window
                if cue_mask is not None:
                    if (
                        cue_mask.shape != (batch, length)
                        or cue_mask.dtype != torch.bool
                    ):
                        raise ValueError(
                            "cue_mask must be boolean with shape (batch, length)"
                        )
                    mask = mask[None, None] & (
                        local[None, None] | cue_mask[:, None, None, :]
                    )
                else:
                    mask = mask & local
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

    def forward(
        self,
        x: torch.Tensor,
        gates: torch.Tensor | None,
        cue_mask: torch.Tensor | None = None,
    ) -> torch.Tensor:
        x = x + self.attention(self.attention_norm(x), gates, cue_mask)
        x = x + self.down(F.gelu(self.up(self.mlp_norm(x))))
        return x


class StencilTransformer(nn.Module):
    """One shared decoder-only transformer assembled into all eight variants."""

    def __init__(self, config: Config, *, use_compiled_scan: bool = False) -> None:
        super().__init__()
        if config.variant not in {
            "b0_full",
            "b0_local",
            "b1",
            "b2",
            "m1",
            "m1b",
            "b3",
            "b4",
        }:
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
            self.controller = OscillatorController(
                config,
                pathway_generator,
                use_compiled_scan=use_compiled_scan,
            )
        elif config.variant == "b2":
            self.controller = DecayCell(
                config.d_model,
                128,
                generator=pathway_generator,
                use_compiled_scan=use_compiled_scan,
            )
        elif config.variant == "b3":
            self.controller = CueLatch(config.d_model, 128, generator=pathway_generator)
        if config.variant in {"m1", "m1b", "b2", "b3"}:
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
        self,
        tokens: torch.Tensor,
        *,
        gate_identity: bool = False,
        decision_positions: torch.Tensor | None = None,
        cue_positions: torch.Tensor | None = None,
        cue_valid: torch.Tensor | None = None,
        use_truncation: bool | None = None,
        truncation_start: int | None = None,
    ) -> torch.Tensor:
        return self.forward_embeddings(
            self.token_embedding(tokens),
            gate_identity=gate_identity,
            cue_mask=(tokens >= 1) & (tokens <= 32),
            decision_positions=decision_positions,
            cue_positions=cue_positions,
            cue_valid=cue_valid,
            use_truncation=use_truncation,
            truncation_start=truncation_start,
        )

    def forward_embeddings(
        self,
        embeddings: torch.Tensor,
        *,
        gate_identity: bool = False,
        cue_mask: torch.Tensor | None = None,
        decision_positions: torch.Tensor | None = None,
        cue_positions: torch.Tensor | None = None,
        cue_valid: torch.Tensor | None = None,
        use_truncation: bool | None = None,
        truncation_start: int | None = None,
    ) -> torch.Tensor:
        if gate_identity and self.config.variant in {"b0_full", "b0_local"}:
            raise ValueError("baseline has no gate to bypass")
        control = None
        if self.config.variant == "b3":
            if cue_mask is None:
                raise ValueError("b3 embedding forwards require a cue_mask")
            assert isinstance(self.controller, CueLatch)
            control = self.controller(embeddings, cue_mask)
        elif self.controller is not None:
            control = self.controller(embeddings)
        if self.config.variant == "b4" and cue_mask is None:
            raise ValueError("b4 embedding forwards require a cue_mask")
        truncatable = self.config.variant not in {"b0_full", "b4"}
        if use_truncation is None:
            use_truncation = decision_positions is not None and truncatable
        if use_truncation and not truncatable:
            raise ValueError("this variant does not permit receptive-field truncation")
        position_offset = 0
        if use_truncation:
            if decision_positions is None:
                raise ValueError("truncation requires decision positions")
            if truncation_start is None:
                if decision_positions.device.type != "cpu":
                    raise ValueError("CUDA truncation requires a CPU-computed start")
                truncation_start = max(
                    0,
                    int(decision_positions.min()) - self.receptive_field(),
                )
            if not 0 <= truncation_start < embeddings.shape[1]:
                raise ValueError("truncation start is outside the sequence")
            position_offset = truncation_start
            x = embeddings[:, truncation_start:]
            if control is not None:
                control = control[:, truncation_start:]
            if cue_mask is not None:
                cue_mask = cue_mask[:, truncation_start:]
            decision_positions = decision_positions - truncation_start
            if decision_positions.device.type == "cpu" and bool(
                torch.any(decision_positions < 0)
            ):
                raise ValueError("truncation removed a decision position")
        else:
            x = embeddings
        for layer_index, block in enumerate(self.blocks):
            normalized = block.attention_norm(x)
            gates = None
            if self.config.variant == "b1":
                if gate_identity:
                    gates = x.new_ones(x.shape[0], x.shape[1], self.config.n_heads)
                else:
                    assert self.b1_weight is not None
                    gates = project_b1_gate(normalized, self.b1_weight[layer_index])
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
            attention_cue_mask = cue_mask if self.config.variant == "b4" else None
            x = x + block.attention(
                normalized,
                gates,
                attention_cue_mask,
                cue_positions=cue_positions,
                cue_valid=cue_valid,
                position_offset=position_offset,
            )
            x = x + block.down(F.gelu(block.up(block.mlp_norm(x))))
        return self._project_logits(x, decision_positions)

    def _project_logits(
        self, hidden: torch.Tensor, decision_positions: torch.Tensor | None
    ) -> torch.Tensor:
        if decision_positions is not None:
            if (
                decision_positions.ndim != 2
                or decision_positions.shape[0] != hidden.shape[0]
                or decision_positions.dtype != torch.long
            ):
                raise ValueError(
                    "decision positions must have shape (batch, decisions)"
                )
            gather_index = decision_positions[..., None].expand(
                -1, -1, hidden.shape[-1]
            )
            hidden = torch.gather(hidden, 1, gather_index)
        return self.lm_head(self.final_norm(hidden))


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
    if config.variant == "b3":
        return base + 128 * d + gates
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
    order = ("b0_full", "b0_local", "b1", "b2", "m1", "m1b", "b3", "b4")
    fixed = {
        variant: _base_config(variant, 1024, seed_init) for variant in ("m1", "m1b")
    }
    target = _config_param_count(fixed["m1b"])
    configs: OrderedDict[str, Config] = OrderedDict()
    for variant in order:
        if variant in fixed:
            configs[variant] = fixed[variant]
            continue
        if variant == "b4":
            configs[variant] = _base_config(
                variant, configs["b0_local"].d_ff, seed_init
            )
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
