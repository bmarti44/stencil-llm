"""Real consumer tests; DEV only."""

from types import SimpleNamespace

import torch
from transformers import Qwen3MoeConfig, Qwen3MoeForCausalLM

from stencil.focus.retained_decode import RetainedDecoder
from stencil.focus.slab import bank, paired_context_gate


class Tokenizer:
    pad_token_id = 0

    def decode(self, ids, **kwargs):
        return repr(ids)


def test_dev_shapes_and_gate():
    dev = bank()
    assert [len(e.turns) for e in dev] == [16] * 6 + [32] * 2
    assert {e.domain for i, e in enumerate(dev) if i in (0, 1, 6, 7)} == {
        e.domain for e in dev
    }
    assert paired_context_gate(dict.fromkeys("RNTO", 32768 - 512))
    assert not paired_context_gate(dict(R=32768 - 511, N=1, T=1, O=1))


def test_retained_batch_padding_and_hidden_against_sequential():
    torch.manual_seed(12)
    torch.set_num_threads(2)
    config = Qwen3MoeConfig(
        vocab_size=32,
        hidden_size=16,
        intermediate_size=16,
        moe_intermediate_size=8,
        num_hidden_layers=2,
        num_attention_heads=2,
        num_key_value_heads=1,
        head_dim=8,
        num_experts=2,
        num_experts_per_tok=1,
        eos_token_id=31,
        pad_token_id=0,
    )
    config._attn_implementation = "sdpa"
    model = Qwen3MoeForCausalLM(config).eval()
    model.generation_config.eos_token_id = []  # cap forces uncached last-token path
    prompts = [(1, 2, 3), (1, 4), (2, 3, 5, 6), (7, 8, 9)]
    sequential = []
    for prompt in prompts:
        decoder = RetainedDecoder(model, Tokenizer(), layers=(1, 2), cap=4)
        first, m1 = decoder([SimpleNamespace(prompt_ids=prompt)])
        second_prompt = prompt + first[0].output_ids + (10, 11)
        second, m2 = decoder([SimpleNamespace(prompt_ids=second_prompt)])
        assert m2[0]["prefill_tokens"] == 3  # last body token + appended two
        assert m1[0]["prompt_hidden"].shape == (2, 16)
        assert m1[0]["generated_forward_tokens"] == 3
        assert not m1[0]["hidden_complete"]
        sequential.append((first[0], second[0], m1[0], m2[0]))
        decoder.close()
    batch = RetainedDecoder(model, Tokenizer(), lanes=4, layers=(1, 2), cap=4)
    first, m1 = batch([SimpleNamespace(prompt_ids=p) for p in prompts])
    second, m2 = batch(
        [
            SimpleNamespace(prompt_ids=p + x.output_ids + (10, 11))
            for p, x in zip(prompts, first, strict=True)
        ]
    )
    for i, (s1, s2, h1, h2) in enumerate(sequential):
        assert (
            s1.output_ids == first[i].output_ids
            and s2.output_ids == second[i].output_ids
        )
        torch.testing.assert_close(
            torch.from_numpy(m1[i]["prompt_hidden"]),
            torch.from_numpy(h1["prompt_hidden"]),
            atol=1e-3,
            rtol=1e-3,
        )
        torch.testing.assert_close(
            torch.from_numpy(m2[i]["generated_mean"]),
            torch.from_numpy(h2["generated_mean"]),
            atol=1e-3,
            rtol=1e-3,
        )
    batch.close()


def test_frozen_gpu_renderer_replay():
    """Hold original system/feedback fixed across the Day5b parser amendment."""
    from stencil.focus.pilot2 import renderer_check

    assert renderer_check()["passed"]
