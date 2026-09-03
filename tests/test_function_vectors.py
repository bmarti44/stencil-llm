"""CPU-only deterministic tests for residual-stream function vectors."""

from __future__ import annotations

import torch


def _tiny_model():
    from stencil.qwen3 import Qwen3, Qwen3Config

    cfg = Qwen3Config(
        n_layer=3,
        n_head=2,
        n_kv_head=1,
        head_dim=4,
        d_model=8,
        d_ff=12,
        vocab=17,
        rope_theta=10_000.0,
        rms_eps=1e-6,
        n_ctx=16,
        tie_word_embeddings=True,
    )
    return Qwen3(cfg).eval()


def test_pair_construction_removes_only_the_selected_constraint_sentence():
    from stencil.function_vectors import build_minimal_pairs

    rows = [
        {
            "key": 7,
            "prompt": (
                "Write a note. Constraint: write the whole reply in lowercase "
                "letters only. Constraint: use the word 'hinge' no fewer than 2 "
                "times."
            ),
            "combo": ["lower", "kw_freq"],
        }
    ]
    pairs = build_minimal_pairs(rows, ["lower", "kw_freq"], n_per_type=1)
    assert set(pairs) == {"lower", "kw_freq"}
    lower = pairs["lower"][0]
    assert lower["with_prompt"] == rows[0]["prompt"]
    assert "lowercase letters only" in lower["constraint_sentence"]
    assert "lowercase letters only" not in lower["without_prompt"]
    assert "use the word 'hinge'" in lower["without_prompt"]
    assert lower["source_key"] == 7


def test_pair_construction_enforces_n_per_type():
    import pytest

    from stencil.function_vectors import build_minimal_pairs

    with pytest.raises(ValueError, match="lower.*2"):
        build_minimal_pairs(
            [
                {
                    "key": 0,
                    "prompt": "Do it. Constraint: reply in lowercase.",
                    "combo": ["lower"],
                }
            ],
            ["lower"],
            n_per_type=2,
        )


def test_real_train_v43_supplies_16_disjoint_pairs_for_every_probe_type():
    import json
    from pathlib import Path

    from stencil.function_vectors import build_minimal_pairs

    rows = [
        json.loads(line)
        for line in Path("data/b3/train-v43.jsonl").read_text().splitlines()
    ]
    types = (
        "bullets",
        "caps",
        "kw_exist",
        "kw_forbid",
        "kw_freq",
        "lower",
        "n_sent",
        "n_words_max",
        "placeholders",
        "postscript",
        "title",
    )
    pairs = build_minimal_pairs(rows, types, n_per_type=16)
    assert {key: len(value) for key, value in pairs.items()} == {
        key: 16 for key in types
    }
    assert all(
        pair["constraint_sentence"] not in pair["without_prompt"]
        for type_pairs in pairs.values()
        for pair in type_pairs
    )


def test_function_vector_is_mean_with_minus_mean_without():
    from stencil.function_vectors import mean_difference

    with_states = [torch.tensor([3.0, 7.0]), torch.tensor([5.0, 9.0])]
    without_states = [torch.tensor([1.0, 2.0]), torch.tensor([2.0, 4.0])]
    result = mean_difference(with_states, without_states)
    assert torch.equal(result, torch.tensor([2.5, 5.0]))


def test_residual_hook_injects_only_registered_layer_and_positions():
    from stencil.function_vectors import make_residual_hook

    events = []
    vector = torch.tensor([1.0, -2.0])
    hook = make_residual_hook(
        vector,
        alpha=2.0,
        layer=1,
        generated_position=3,
        clear_after=64,
        event_sink=events,
    )
    x = torch.zeros(1, 1, 2)
    assert torch.equal(hook[1](x), torch.tensor([[[2.0, -4.0]]]))
    assert events == [{"layer": 1, "generated_position": 3}]


def test_prompt_prefill_injection_changes_only_the_final_token_position():
    from stencil.function_vectors import make_residual_hook

    hook = make_residual_hook(
        torch.tensor([1.0, -2.0]),
        alpha=2.0,
        layer=1,
        generated_position=0,
    )
    hidden = torch.zeros(1, 3, 2)
    changed = hook[1](hidden)
    assert torch.count_nonzero(changed[:, :-1]) == 0
    assert torch.equal(changed[:, -1], torch.tensor([[2.0, -4.0]]))


def test_alpha_zero_and_zero_vector_are_bitwise_identity():
    from stencil.function_vectors import make_residual_hook

    model = _tiny_model()
    tokens = torch.tensor([[1, 2, 3]])
    with torch.no_grad():
        baseline = model(tokens)
        alpha_zero = model(
            tokens,
            residual_hook=make_residual_hook(
                torch.ones(8), alpha=0.0, layer=1, generated_position=0
            ),
        )
        vector_zero = model(
            tokens,
            residual_hook=make_residual_hook(
                torch.zeros(8), alpha=2.0, layer=1, generated_position=0
            ),
        )
    assert torch.equal(alpha_zero, baseline)
    assert torch.equal(vector_zero, baseline)


def test_nonzero_injection_reaches_only_the_registered_layer():
    from stencil.function_vectors import make_residual_hook

    model = _tiny_model()
    seen = []
    original = make_residual_hook(
        torch.ones(8),
        alpha=1.0,
        layer=1,
        generated_position=0,
        event_sink=seen,
    )
    with torch.no_grad():
        model(torch.tensor([[1, 2]]), residual_hook=original)
    assert seen == [{"layer": 1, "generated_position": 0}]


def test_multiple_hidden_layers_are_captured_at_the_final_prompt_token():
    model = _tiny_model()
    with torch.no_grad():
        logits, captured = model(torch.tensor([[1, 2]]), capture_hidden=(0, 2))
    assert logits.shape == (1, 2, 17)
    assert set(captured) == {0, 2}
    assert captured[0][0, -1].shape == (8,)


def test_generation_injects_current_prompt_then_clears_at_position_one():
    from torch import nn

    from stencil.function_vectors import generate_injected
    from stencil.qwen3 import Qwen3Config

    events = []

    class Tokenizer:
        def decode(self, _ids, skip_special_tokens=False):
            del skip_special_tokens
            return "answer"

    class StubTrunk(nn.Module):
        def __init__(self):
            super().__init__()
            self.anchor = nn.Parameter(torch.zeros(()))
            self.cfg = Qwen3Config(
                1, 1, 1, 2, 2, 2, 151_646, 10_000.0, 1e-6, 16, True
            )

        def forward(self, tokens, *, cache, residual_hook=None):
            values = tokens[0].tolist()
            events.append((values, None if residual_hook is None else residual_hook[0]))
            hidden = torch.zeros(1, len(values), 2)
            if residual_hook is not None:
                hidden = residual_hook[1](hidden)
            prior_sum = 0.0 if cache.k[0] is None else float(cache.k[0].sum())
            fresh = hidden[:, None]
            cache.k[0] = (
                fresh if cache.k[0] is None else torch.cat([cache.k[0], fresh], 2)
            )
            cache.v[0] = cache.k[0].clone()
            cache.length += len(values)
            logits = torch.zeros(1, len(values), self.cfg.vocab)
            if values == [60, 50] and residual_hook is not None:
                predicted = 7
            elif values == [7] and prior_sum > 0:
                predicted = 8
            else:
                predicted = 151_645
            logits[0, -1, predicted] = 1.0
            return logits

    result = generate_injected(
        StubTrunk(),
        Tokenizer(),
        [10, 11, 12, 13, 60, 50],
        evict_range=(1, 4),
        vector=torch.ones(2),
        alpha=1.0,
        layer=0,
        clear_after=1,
        max_new=2,
        deadline_s=5.0,
    )
    assert events == [
        ([10, 11, 12, 13], None),
        ([60, 50], 0),
        ([10, 11, 12, 13], None),
        ([60, 50], None),
        ([7], None),
    ]
    assert result["generated_token_ids"] == [7]
    assert result["cache_rebuilt_at"] == 1


def test_clearing_schedule_is_active_for_64_positions_then_bitwise_inert():
    from stencil.function_vectors import make_residual_hook

    model = _tiny_model()
    tokens = torch.tensor([[1]])
    vector = torch.ones(8)
    with torch.no_grad():
        baseline = model(tokens)
        at_63 = model(
            tokens,
            residual_hook=make_residual_hook(
                vector,
                alpha=1.0,
                layer=1,
                generated_position=63,
                clear_after=64,
            ),
        )
        at_64 = model(
            tokens,
            residual_hook=make_residual_hook(
                vector,
                alpha=1.0,
                layer=1,
                generated_position=64,
                clear_after=64,
            ),
        )
    assert not torch.equal(at_63, baseline)
    assert torch.equal(at_64, baseline)


def test_summary_contract_preregisters_reading_and_unknown_counts():
    from stencil.function_vectors import function_vector_summary

    rows = [
        {
            "arms": {
                "evicted": {"scores": [False, True]},
                "fv_inject": {"scores": [True, True]},
                "fv_inject_echo": {"scores": [True, False]},
            },
            "unknown_vector_constraints": 1,
        }
    ]
    summary = function_vector_summary(
        rows,
        totals={"evicted": 10, "fv_inject": 30, "fv_inject_echo": 47},
        killed={"fv_inject": False, "fv_inject_echo": False, "fv_clear": False},
    )
    assert summary["preregistered_reading"] == {
        "helps": "fv_inject >= 30/56; paired wins > losses vs evicted; not killed",
        "strong": "fv_inject_echo > 46/56; paired wins > losses; not killed",
        "harmful": "killed or fv_inject < evicted + 5",
    }
    assert summary["unknown_vector_constraints"] == 1
    assert summary["paired_fv_inject_vs_evicted"] == {"wins": 1, "losses": 0}
    assert summary["reading"] == {"helps": True, "strong": False, "harmful": False}
