import importlib.util
import json
from dataclasses import replace
from pathlib import Path

import torch

from stencil import determinism
from stencil.config import load_config
from stencil.data import (
    VOCAB_RANGES,
    _sample_task_a_example,
    cue_blind_bayes,
    generate,
    make_task_b_example,
    receptive_field,
    rule_table,
    task_a,
    task_b,
)

ROOT = Path(__file__).parents[1]
BASE_CONFIG = load_config(ROOT / "configs" / "test_tiny.json")


def _config(task: str, **overrides):
    task_fields = {
        "task_N": None,
        "task_k": None,
        "task_R": None,
        "task_delay_min": None,
        "task_delay_max": None,
        "task_P": None,
        "task_queries": None,
        "task_placement": None,
    }
    task_fields.update(overrides)
    return replace(BASE_CONFIG, task=task, **task_fields)


def test_task_a_exact_output() -> None:
    fixture = json.loads(
        (ROOT / "tests/fixtures/task_a_k2_n8_seed0.json").read_text()
    )
    config = _config("a", task_N=fixture["N"], task_k=fixture["k"])
    stream = generate(config)
    actual = []
    for _ in fixture["sequences"]:
        tokens, loss_mask, metadata = next(stream)
        actual.append(
            {
                "tokens": tokens.tolist(),
                "loss_mask": loss_mask.tolist(),
                "metadata": metadata,
            }
        )

    assert rule_table(config) == fixture["rule_table_first_k_rows"]
    assert actual == fixture["sequences"]


def test_rules_are_permutations() -> None:
    expected = list(range(16))
    cases = 0
    for k in (2, 8, 16, 32):
        rules = rule_table(_config("a", task_N=8, task_k=k))
        assert len(rules) == k
        for rule in rules:
            assert sorted(rule) == expected
            cases += 1
    assert cases == 58


def test_vocab_ranges_disjoint() -> None:
    expected = {
        "pad": {0},
        "cues_keys": set(range(1, 33)),
        "query": {33},
        "operands_values_answers": set(range(34, 50)),
        "distractors": set(range(50, 64)),
    }
    assert VOCAB_RANGES == expected
    names = list(VOCAB_RANGES)
    comparisons = 0
    for left_index, left in enumerate(names):
        for right in names[left_index + 1 :]:
            assert VOCAB_RANGES[left].isdisjoint(VOCAB_RANGES[right])
            comparisons += 1
    assert comparisons == 10
    assert set().union(*VOCAB_RANGES.values()) == set(range(64))


def test_distractor_rule_independence() -> None:
    config = _config("a", task_N=8, task_k=8)
    fixed_distractors = [3, 1, 4, 1, 5, 9, 2, 6]
    cues = determinism.named_generator(config.seed_data, "cues")
    operands = determinism.named_generator(config.seed_data, "operands")
    distractors = determinism.named_generator(config.seed_data, "distractors")
    rules = rule_table(config)
    counts = [0] * config.task_k
    sample_count = 10_000
    for _ in range(sample_count):
        tokens, _, metadata = _sample_task_a_example(
            config,
            rules,
            cues,
            operands,
            distractors,
            distractor_draws=fixed_distractors,
        )
        assert metadata["distractor_draws"] == fixed_distractors
        assert tokens[1 : 1 + config.task_N].tolist() == [
            50 + draw for draw in fixed_distractors
        ]
        counts[metadata["cue_index"]] += 1

    expected = sample_count / config.task_k
    sigma = (sample_count * (1 / config.task_k) * (1 - 1 / config.task_k)) ** 0.5
    assert sum(counts) == sample_count
    assert all(abs(count - expected) <= 5 * sigma for count in counts)


def test_task_a_registered_grid_uses_independent_production_streams() -> None:
    config = _config("a", task_N=128, task_k=8)
    tokens, loss_mask, metadata = next(task_a(config))
    cues = determinism.named_generator(config.seed_data, "cues")
    operands = determinism.named_generator(config.seed_data, "operands")
    distractors = determinism.named_generator(config.seed_data, "distractors")
    expected_cue = int(torch.randint(0, config.task_k, (1,), generator=cues))
    expected_operand = int(torch.randint(0, 16, (1,), generator=operands))
    expected_distractors = [
        int(torch.randint(0, 14, (1,), generator=distractors))
        for _ in range(config.task_N)
    ]

    assert metadata["cue_index"] == expected_cue
    assert metadata["operand_index"] == expected_operand
    assert metadata["distractor_draws"] == expected_distractors
    assert tokens[0].item() == 1 + expected_cue
    assert tokens[1 : config.task_N + 1].tolist() == [
        50 + draw for draw in expected_distractors
    ]
    assert torch.nonzero(loss_mask).flatten().tolist() == [config.task_N + 2]


def test_rules_latin_rectangle() -> None:
    cases = 0
    for seed_rules in (0, 1, 2):
        for k in (2, 8, 16, 32):
            config = replace(
                _config("a", task_N=8, task_k=k), seed_rules=seed_rules
            )
            rules = rule_table(config)
            for row in rules:
                assert sorted(row) == list(range(16))
            for operand in range(16):
                outputs = [row[operand] for row in rules]
                if k <= 16:
                    assert len(set(outputs)) == k
                else:
                    assert [outputs.count(answer) for answer in range(16)] == [2] * 16
                cases += 1
            assert cue_blind_bayes(config) == (1 / k if k <= 16 else 1 / 16)
    assert cases == 3 * 4 * 16


def test_loss_mask_positions() -> None:
    configs_and_expected = [
        (_config("a", task_N=8, task_k=2), lambda config: [config.task_N + 2]),
        (
            _config(
                "b",
                task_k=8,
                task_R=3,
                task_delay_min=2,
                task_delay_max=2,
            ),
            lambda config: [4, 10, 16],
        ),
        (
            _config("m", task_P=4, task_queries=2, task_placement="in_window"),
            lambda config: [2 * config.task_P + 1, 2 * config.task_P + 3],
        ),
    ]
    cases = 0
    for config, expected_positions in configs_and_expected:
        tokens, loss_mask, _ = next(generate(config))
        actual = torch.nonzero(loss_mask, as_tuple=False).flatten().tolist()
        expected = expected_positions(config)
        assert actual == expected
        assert loss_mask.numel() == tokens.numel()
        assert all(position + 1 < tokens.numel() for position in actual)
        cases += 1
    assert cases == 3


def test_task_b_active_rule_tracking() -> None:
    config = _config(
        "b",
        task_k=8,
        task_R=4,
        task_delay_min=1,
        task_delay_max=3,
    )
    cues = [1, 3, 1, 7]
    operands = [0, 5, 9, 15]
    distractors = [[0], [1, 2], [3, 4, 5], [6]]
    tokens, loss_mask, metadata = make_task_b_example(
        config, cues, operands, distractors
    )
    rules = rule_table(config)

    observed_active = None
    decision_index = 0
    cue_tokens_seen = 0
    for position, token in enumerate(tokens.tolist()):
        if 1 <= token <= 8:
            observed_active = token - 1
            cue_tokens_seen += 1
        if loss_mask[position]:
            assert observed_active == cues[decision_index]
            assert metadata["active_rule_indices"][decision_index] == observed_active
            assert tokens[position + 1].item() == (
                34 + rules[observed_active][operands[decision_index]]
            )
            decision_index += 1
    assert cue_tokens_seen == config.task_R
    assert decision_index == config.task_R


def test_task_b_exact_output() -> None:
    fixture = json.loads(
        (ROOT / "tests/fixtures/task_b_r2_k8_seed0.json").read_text()
    )
    config = _config(
        "b",
        task_k=fixture["k"],
        task_R=fixture["R"],
        task_delay_min=fixture["delay_min"],
        task_delay_max=fixture["delay_max"],
    )
    stream = task_b(config)
    cue_draws = determinism.named_generator(config.seed_data, "cues")
    rules = rule_table(config)
    actual_sequences = []
    redraw_cases = 0
    for _expected in fixture["sequences"]:
        tokens, loss_mask, metadata = next(stream)
        actual_segments = []
        previous_cue = None
        for cue, operand, delay in zip(
            metadata["cue_indices"],
            metadata["operand_indices"],
            metadata["delay_lengths"],
            strict=True,
        ):
            drawn_cue = int(torch.randint(0, config.task_k, (1,), generator=cue_draws))
            redraws = 0
            while drawn_cue == previous_cue:
                drawn_cue = int(
                    torch.randint(0, config.task_k, (1,), generator=cue_draws)
                )
                redraws += 1
            assert cue == drawn_cue
            actual_segments.append(
                {
                    "cue_index": cue,
                    "operand_index": operand,
                    "delay": delay,
                    "cue_redraws": redraws,
                    "answer_index": rules[cue][operand],
                }
            )
            previous_cue = cue
            redraw_cases += redraws
        actual_sequences.append(
            {
                "tokens": tokens.tolist(),
                "loss_mask": loss_mask.tolist(),
                "segments": actual_segments,
            }
        )

    assert actual_sequences == fixture["sequences"]
    assert redraw_cases == 1


def test_task_m_bindings() -> None:
    fixture = json.loads(
        (ROOT / "tests/fixtures/task_m_p4_q2_seed0.json").read_text()
    )
    config = _config(
        "m",
        task_P=fixture["P"],
        task_queries=fixture["n_queries"],
        task_placement="in_window",
    )
    stream = generate(config)
    actual = []
    query_count = 0
    for _expected in fixture["sequences"]:
        tokens, loss_mask, metadata = next(stream)
        actual.append(
            {
                "tokens": tokens.tolist(),
                "loss_mask": loss_mask.tolist(),
                "metadata": metadata,
            }
        )
        keys = metadata["key_indices"]
        values = metadata["value_indices"]
        queries = metadata["query_pair_positions"]
        assert len(keys) == len(set(keys)) == config.task_P
        assert len(queries) == len(set(queries)) == config.task_queries
        for decision_position, pair_position in zip(
            torch.nonzero(loss_mask).flatten().tolist(), queries, strict=True
        ):
            assert tokens[decision_position].item() == 1 + keys[pair_position]
            assert tokens[decision_position + 1].item() == 34 + values[pair_position]
            query_count += 1
    assert len(actual) == 4
    assert query_count == 8
    assert actual == fixture["sequences"]


def test_task_m_gap_exceeds_receptive_field() -> None:
    config = _config(
        "m", task_P=32, task_queries=8, task_placement="beyond_window"
    )
    tokens, loss_mask, metadata = next(generate(config))
    field = receptive_field(config)
    assert field == config.n_layers * (config.window - 1)
    assert metadata["gap_length"] == field + 64
    assert len(metadata["gap_draws"]) == field + 64
    gap_start = 2 * config.task_P
    gap_stop = gap_start + metadata["gap_length"]
    assert tokens[gap_start:gap_stop].numel() == field + 64
    assert all(50 <= token < 64 for token in tokens[gap_start:gap_stop].tolist())

    value_positions = list(range(1, 2 * config.task_P, 2))
    decision_positions = torch.nonzero(loss_mask).flatten().tolist()
    distances = [
        decision - value
        for decision in decision_positions
        for value in value_positions
    ]
    assert len(decision_positions) == config.task_queries
    assert len(distances) == config.task_P * config.task_queries
    assert min(distances) > field


def test_data_samples_have_three_samples_per_task_and_placement() -> None:
    script_path = ROOT / "scripts/make_data_samples.py"
    spec = importlib.util.spec_from_file_location("make_data_samples", script_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    rendered = module.render_document()
    module.validate_document(rendered)
    assert rendered.count("## Task A ") == 1
    assert rendered.count("## Task B ") == 1
    assert rendered.count("## Task M ") == 2
    assert rendered.count("### Sample ") == 12
