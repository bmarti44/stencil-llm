import json
from dataclasses import replace
from pathlib import Path

import pytest
import torch

from stencil.config import load_config
from stencil.data import make_task_d_example, task_d, task_d_curriculum_bounds
from stencil.determinism import named_generator
from stencil.model import StencilTransformer
from stencil.oscillator import CueLatch, KeyedCueLatch
from stencil.train import next_examples

ROOT = Path(__file__).parents[1]
BASE = load_config(ROOT / "configs/test_tiny.json")


def _d_config(**overrides):
    values = dict(
        task="d",
        task_k=8,
        context_len=4096,
        task_d_slots=4,
        task_d_core_len=3848,
        task_d_updates=12,
        task_d_queries=16,
        task_d_family="train",
        task_d_reinsert="none",
        task_d_gap_min=64,
        task_d_gap_max=320,
        task_d_burst_start_min=64,
        task_d_burst_start_max=512,
        task_d_burst_intra_min=8,
        task_d_burst_intra_max=32,
        task_d_burst_inter_min=640,
        task_d_burst_inter_max=1200,
        task_d_curriculum_start=8000,
        task_d_curriculum_end=12000,
        task_d_curriculum_gap_min=32,
        task_d_curriculum_gap_max=128,
        task_d_schedule_offset=0,
        task_d_sequence_index=0,
    )
    values.update(overrides)
    return replace(BASE, **values)


def test_task_d_miniature_exact() -> None:
    fixture = json.loads((ROOT / "tests/fixtures/task_d_miniature.json").read_text())
    config = _d_config(
        task_d_slots=2,
        task_d_core_len=256,
        context_len=256,
        task_d_updates=3,
        task_d_queries=4,
        task_d_gap_min=16,
        task_d_gap_max=48,
        task_d_reinsert="miniature-64",
    )
    tokens, mask, metadata = next(task_d(config))

    assert tokens.tolist() == fixture["tokens"]
    assert metadata["targets"].tolist() == fixture["targets"]
    assert metadata["updates"] == fixture["updates"]
    assert metadata["queries"] == fixture["queries"]
    assert metadata["noop_update_indices"] == fixture["noop_update_indices"]
    assert metadata["reinsert64_tokens"] == fixture["reinsert64_tokens"]
    assert metadata["seed_data"] == fixture["seed_data"] == 0
    assert torch.nonzero(mask).flatten().tolist() == sorted(
        q["start"] + 2 for q in fixture["queries"]
    )


def test_task_d_no_answer_in_input() -> None:
    tokens, mask, metadata = next(task_d(_d_config()))
    positions = torch.nonzero(mask).flatten()
    targets = metadata["targets"]
    assert positions.numel() == 16
    assert torch.all(tokens[positions] != targets[positions])
    assert torch.all(tokens[positions + 1] == 0)
    assert all(
        q["answer"] not in tokens[q["start"] : q["start"] + 4].tolist()
        for q in metadata["queries"]
    )


def test_task_d_batch_uses_separate_targets_and_fixed_events() -> None:
    batch = next_examples(task_d(_d_config()), 2)
    rows = torch.arange(2)[:, None]
    assert batch.targets.shape == (2, 16)
    expected = torch.stack(
        [
            details["targets"][positions]
            for details, positions in zip(
                batch.metadata, batch.decision_positions, strict=True
            )
        ]
    )
    assert torch.equal(batch.targets, expected)
    assert torch.all(batch.targets != batch.tokens[rows, batch.decision_positions])
    assert torch.all(batch.tokens[rows, batch.decision_positions + 1] == 0)
    assert batch.cue_positions.shape == batch.cue_valid.shape == (2, 32)
    assert torch.all(batch.cue_valid)


@pytest.mark.parametrize(
    "family,updates", [("train", 12), ("drought", 3), ("burst", 8)]
)
@pytest.mark.parametrize("policy", ["none", "every-128", "prequery"])
def test_task_d_fixed_shapes(family: str, updates: int, policy: str) -> None:
    family_bounds = (
        {"task_d_gap_min": 768, "task_d_gap_max": 1280} if family == "drought" else {}
    )
    tokens, mask, metadata = next(
        task_d(
            _d_config(
                task_d_family=family,
                task_d_updates=updates,
                task_d_reinsert=policy,
                **family_bounds,
            )
        )
    )
    assert tokens.shape == mask.shape == (4096,)
    assert int(mask.sum()) == 16
    assert metadata["targets"].shape == (4096,)
    assert metadata["cue_positions"].shape == (32,)
    assert metadata["cue_valid"].shape == (32,)
    assert metadata["cue_valid"].dtype == torch.bool
    assert int(metadata["cue_valid"].sum()) == 2 * (4 + updates)
    assert len(metadata["queries"]) == 16


def test_task_d_reinsert_positions() -> None:
    _, _, periodic = next(task_d(_d_config(task_d_reinsert="every-128")))
    starts = periodic["refresh_block_starts"]
    assert starts == [multiple - 8 for multiple in range(128, 3969, 128)]
    assert len(starts) == 31
    for start in starts:
        assert periodic["core_position_by_final"][start + 8] is not None

    tokens, _, prequery = next(task_d(_d_config(task_d_reinsert="prequery")))
    assert len(prequery["refresh_block_starts"]) == 16
    assert {start + 8 for start in prequery["refresh_block_starts"]} == {
        query["final_start"] for query in prequery["queries"]
    }
    for start in prequery["refresh_block_starts"]:
        assert tokens[start : start + 8].tolist()[::2] == [29, 30, 31, 32]

    periodic_tokens, _, split = next(
        task_d(_d_config(task_d_reinsert="every-128", task_d_sequence_index=4))
    )
    split_queries = [
        query
        for query in split["queries"]
        if query["final_positions"]
        != list(range(query["final_start"], query["final_start"] + 4))
    ]
    assert split_queries
    for query in split["queries"]:
        positions = query["final_positions"]
        assert [int(periodic_tokens[position]) for position in positions] == [
            33,
            59 + query["slot"],
            34 + query["x"],
            0,
        ]
        assert query["final_decision_position"] == positions[2]
        assert query["final_pad_position"] == positions[3]


def test_task_d_common_core_across_policies_and_sequence_index() -> None:
    def core(policy: str, sequence_index: int) -> tuple[list[int], dict]:
        tokens, _, metadata = next(
            task_d(
                _d_config(
                    task_d_reinsert=policy,
                    task_d_sequence_index=sequence_index,
                )
            )
        )
        values = [
            int(tokens[final])
            for final, core_position in enumerate(metadata["core_position_by_final"])
            if core_position is not None
        ][:3848]
        return values, metadata

    for sequence_index in (0, 1):
        none_core, none = core("none", sequence_index)
        periodic_core, periodic = core("every-128", sequence_index)
        prequery_core, prequery = core("prequery", sequence_index)
        assert none_core == periodic_core == prequery_core
        assert none["updates"] == periodic["updates"] == prequery["updates"]
        assert (
            [q["start"] for q in none["queries"]]
            == [q["start"] for q in periodic["queries"]]
            == [q["start"] for q in prequery["queries"]]
        )
        assert none["schedule_id"] == ("train", 0, sequence_index)


def test_task_d_curriculum_changes_only_gap_bounds() -> None:
    config = _d_config()
    assert task_d_curriculum_bounds(config, 0) == (32, 128)
    assert task_d_curriculum_bounds(config, 8000) == (32, 128)
    assert task_d_curriculum_bounds(config, 10000) == (48, 224)
    assert task_d_curriculum_bounds(config, 12000) == (64, 320)
    assert task_d_curriculum_bounds(config, 30000) == (64, 320)
    assert config.task_d_updates == 12


def test_task_d_gap_redraw_fallback_is_counted() -> None:
    config = _d_config(
        task_d_core_len=500,
        context_len=500,
        task_d_updates=3,
        task_d_gap_min=150,
        task_d_gap_max=150,
    )
    _, _, metadata = next(task_d(config))
    assert metadata["gap_redraws"] == 64
    assert metadata["gap_fallbacks"] == 1
    assert metadata["gaps"] == [150, 150, 58]


def test_task_d_registered_family_gap_construction() -> None:
    _, _, drought = next(
        task_d(
            _d_config(
                task_d_family="drought",
                task_d_updates=3,
                task_d_gap_min=768,
                task_d_gap_max=1280,
            )
        )
    )
    assert len(drought["gaps"]) == 3
    assert all(768 <= gap <= 1280 for gap in drought["gaps"])

    _, _, burst = next(
        task_d(_d_config(task_d_family="burst", task_d_updates=8))
    )
    assert len(burst["gaps"]) == 8
    assert 64 <= burst["gaps"][0] <= 512
    assert all(640 <= burst["gaps"][index] <= 1200 for index in (3, 6))
    assert all(
        8 <= burst["gaps"][index] <= 32 for index in (1, 2, 4, 5, 7)
    )


def test_task_d_active_rule_resolution() -> None:
    config = _d_config(
        task_d_slots=2,
        task_d_core_len=64,
        context_len=64,
        task_d_updates=0,
        task_d_queries=1,
    )
    _, _, metadata = make_task_d_example(
        config,
        updates=[(0, 1, 2), (2, 2, 3), (10, 1, 5), (20, 2, 3)],
        queries=[(6, 1, 0), (15, 1, 1), (25, 2, 2)],
    )
    assert [q["active_rule"] for q in metadata["queries"]] == [2, 5, 3]
    assert metadata["noop_update_indices"] == [1]
    assert metadata["queries"][1]["active_rule"] == 5


def test_b3k_slot_isolation() -> None:
    latch = KeyedCueLatch(
        8, slots=4, register_dim=2, generator=torch.Generator().manual_seed(0)
    )
    embeddings = torch.randn(1, 7, 8, generator=torch.Generator().manual_seed(1))
    tokens = torch.tensor([[29, 4, 60, 7, 30, 2, 61]])
    state = latch(embeddings, tokens).reshape(1, 7, 4, 2)
    assert torch.count_nonzero(state[0, 0]) == 0
    assert torch.count_nonzero(state[0, 1, 0]) > 0
    assert torch.count_nonzero(state[0, 1, 1:]) == 0
    assert torch.equal(
        state[0, 1], state[0, 3]
    )  # QSLOT + cue-like neighbor is not an update
    assert torch.equal(state[0, 5, 0], state[0, 3, 0])
    assert torch.count_nonzero(state[0, 5, 1]) > 0
    assert torch.count_nonzero(state[0, 5, 2:]) == 0


def test_b3k_gate_identity_bitwise() -> None:
    config = _d_config(variant="b3k", d_model=64, n_layers=2, n_heads=2, d_ff=256)
    base = replace(config, variant="b0_local")
    tokens = torch.stack([next(task_d(config))[0] for _ in range(2)])
    with torch.no_grad():
        actual = StencilTransformer(config)(tokens, gate_identity=True)
        expected = StencilTransformer(base)(tokens)
    assert torch.count_nonzero(actual) > 0
    assert torch.equal(actual, expected)


def test_b3_b4_role_masks() -> None:
    tokens = torch.tensor([[1, 60, 61, 32, 63, 50]])
    role_mask = (tokens >= 1) & (tokens <= 32)
    assert role_mask.tolist() == [[True, False, False, True, False, False]]
    embeddings = torch.randn(1, 6, 4)
    single = CueLatch(4, 4, generator=named_generator(0, "role-mask:b3"))
    state = single(embeddings, role_mask)
    assert torch.equal(state[:, 0], state[:, 1])
    assert torch.equal(state[:, 1], state[:, 2])
    assert not torch.equal(state[:, 2], state[:, 3])

    b4 = StencilTransformer(replace(_d_config(variant="b4"), window=1))
    positions, valid = b4.blocks[0].attention._banded_layout(
        tokens.shape[1], role_mask, torch.device("cpu")
    )
    assert positions[0, -1][valid[0, -1]].tolist() == [0, 3, 5]

    latch = KeyedCueLatch(
        4, slots=4, register_dim=1, generator=torch.Generator().manual_seed(0)
    )
    keyed_state = latch(embeddings, tokens)
    assert torch.count_nonzero(keyed_state) == 0  # no [USLOT][CUE] pair


@pytest.mark.parametrize(
    "field,value,match",
    [
        ("task_d_slots", 3, "slots"),
        ("task_k", 7, "k=8"),
        ("task_d_core_len", 3849, "core"),
        ("task_d_queries", 15, "queries"),
        ("task_d_updates", 13, "updates"),
        ("task_d_family", "unknown", "family"),
        ("task_d_reinsert", "sometimes", "reinsert"),
        ("task_d_gap_min", 321, "gap"),
        ("task_d_burst_inter_max", 1199, "burst"),
        ("task_d_curriculum_start", 12001, "curriculum"),
        ("task_d_curriculum_gap_min", 33, "curriculum"),
        ("task_d_schedule_offset", -1, "schedule"),
        ("task_d_sequence_index", -1, "sequence"),
        ("eval_seed_offset", 0, "eval seed"),
        ("context_len", 4095, "core/context"),
    ],
)
def test_task_d_config_negative_cases(
    tmp_path: Path, field: str, value: object, match: str
) -> None:
    raw = _d_config().as_dict()
    raw[field] = value
    path = tmp_path / "bad.json"
    path.write_text(json.dumps(raw))
    with pytest.raises(ValueError, match=match):
        load_config(path)


@pytest.mark.parametrize(
    "family,updates,gap_min,gap_max",
    [
        ("train", 12, 64, 320),
        ("id-control", 12, 64, 320),
        ("drought", 3, 768, 1280),
        ("burst", 8, 64, 320),
    ],
)
@pytest.mark.parametrize("policy", ["none", "every-128", "prequery"])
def test_task_d_config_accepts_registered_fullscale_cells(
    tmp_path: Path,
    family: str,
    updates: int,
    gap_min: int,
    gap_max: int,
    policy: str,
) -> None:
    raw = _d_config(
        variant="b3k",
        task_d_family=family,
        task_d_updates=updates,
        task_d_gap_min=gap_min,
        task_d_gap_max=gap_max,
        task_d_reinsert=policy,
    ).as_dict()
    path = tmp_path / f"{family}-{policy}.json"
    path.write_text(json.dumps(raw))
    config = load_config(path)
    assert config.task_d_validation_offset == config.eval_seed_offset
    assert config.task_d_final_offset == config.eval_seed_offset * 2 + 1
