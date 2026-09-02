"""CPU coverage for model-agnostic Qwen3 dense configurations."""

from pathlib import Path

import pytest
import torch

from stencil.qwen3 import KVCache, Qwen3, Qwen3Config

ROOT = Path(__file__).resolve().parent.parent


def test_config_from_hf_1_7b() -> None:
    cfg = Qwen3Config.from_hf(ROOT / "models/qwen3-1.7b-hf/config.json")
    assert (
        cfg.n_layer,
        cfg.d_model,
        cfg.n_head,
        cfg.n_kv_head,
        cfg.head_dim,
        cfg.d_ff,
        cfg.vocab,
    ) == (28, 2048, 16, 8, 128, 6144, 151936)
    assert cfg.rope_theta == 1_000_000.0
    assert cfg.rms_eps == 1e-6
    assert cfg.n_ctx == 40960
    assert cfg.tie_word_embeddings is True


def test_config_from_hf_4b() -> None:
    cfg = Qwen3Config.from_hf(ROOT / "models/qwen3-4b-hf/config.json")
    assert (
        cfg.n_layer,
        cfg.d_model,
        cfg.n_head,
        cfg.n_kv_head,
        cfg.head_dim,
        cfg.d_ff,
        cfg.vocab,
    ) == (36, 2560, 32, 8, 128, 9728, 151936)
    assert cfg.tie_word_embeddings is True


def _tiny_config(*, tie_word_embeddings: bool = True) -> Qwen3Config:
    return Qwen3Config(
        n_layer=2,
        n_head=4,
        n_kv_head=2,
        head_dim=4,
        d_model=16,
        d_ff=32,
        vocab=31,
        rope_theta=10_000.0,
        rms_eps=1e-6,
        n_ctx=32,
        tie_word_embeddings=tie_word_embeddings,
    )


def test_synthetic_forward_gqa_cache_and_per_head_bias() -> None:
    cfg = _tiny_config()
    model = Qwen3(cfg).eval()
    tokens = torch.tensor([[1, 2, 3]])
    cache = KVCache(cfg)
    per_head_bias = torch.zeros(cfg.n_head, 3, 3)
    per_head_bias[0, 1:, 0] = 2.0

    with torch.no_grad():
        base = model(tokens)
        biased = model(tokens, attn_bias={0: per_head_bias}, cache=cache)

    assert base.shape == (1, 3, cfg.vocab)
    assert biased.shape == base.shape
    assert not torch.equal(base, biased)
    assert cache.k[0].shape == (1, cfg.n_kv_head, 3, cfg.head_dim)
    assert cache.v[1].shape == (1, cfg.n_kv_head, 3, cfg.head_dim)


def test_untied_lm_head_is_registered_and_used() -> None:
    cfg = _tiny_config(tie_word_embeddings=False)
    model = Qwen3(cfg).eval()
    assert model.lm_head is not None
    assert model.lm_head.weight.data_ptr() != model.embed_tokens.weight.data_ptr()
    with torch.no_grad():
        model.lm_head.weight.zero_()
        logits = model(torch.tensor([[1, 2]]))
    assert torch.count_nonzero(logits) == 0


@pytest.mark.parametrize("tie_word_embeddings", [True, False])
def test_head_dim_independent_projection_shapes_and_lm_head_dtype(
    tie_word_embeddings: bool,
) -> None:
    """Qwen3-4B has a 128-wide head although hidden_size / heads is 80."""
    cfg = Qwen3Config(
        n_layer=1,
        n_head=3,
        n_kv_head=1,
        head_dim=4,
        d_model=9,
        d_ff=13,
        vocab=17,
        rope_theta=10_000.0,
        rms_eps=1e-6,
        n_ctx=16,
        tie_word_embeddings=tie_word_embeddings,
    )
    model = Qwen3(cfg).to(torch.bfloat16).eval()
    block = model.layers[0]

    assert block.q_proj.weight.shape == (cfg.n_head * cfg.head_dim, cfg.d_model)
    assert block.k_proj.weight.shape == (cfg.n_kv_head * cfg.head_dim, cfg.d_model)
    assert block.v_proj.weight.shape == (cfg.n_kv_head * cfg.head_dim, cfg.d_model)
    assert block.o_proj.weight.shape == (cfg.d_model, cfg.n_head * cfg.head_dim)
    assert (model.lm_head is None) is tie_word_embeddings

    with torch.no_grad():
        logits = model(torch.tensor([[1, 2, 3]]))
        cache = KVCache(cfg)
        model(torch.tensor([[1, 2, 3]]), cache=cache)
        cached_logits = model(torch.tensor([[4]]), cache=cache)
    assert logits.shape == (1, 3, cfg.vocab)
    assert logits.dtype == torch.bfloat16
    assert cached_logits.shape == (1, 1, cfg.vocab)
    assert cache.k[0].shape == (1, cfg.n_kv_head, 4, cfg.head_dim)


def test_kv_cache_evict_non_default_layer_count() -> None:
    cfg = _tiny_config()
    cache = KVCache(cfg)
    for layer in range(cfg.n_layer):
        values = torch.arange(20).view(1, 1, 5, 4).repeat(1, 2, 1, 1)
        cache.k[layer] = values + 100 * layer
        cache.v[layer] = values + 200 * layer
    cache.length = 5

    index_map = cache.evict(1, 4, keep=[(2, 3)])

    assert index_map == {0: 0, 2: 1, 4: 2}
    assert len(cache.k) == len(cache.v) == cfg.n_layer
    assert all(t is not None and t.shape[2] == 3 for t in cache.k + cache.v)
    assert cache.length == 5
