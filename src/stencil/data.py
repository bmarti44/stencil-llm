"""Deterministic synthetic-task generators."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import torch

from stencil import determinism
from stencil.config import Config

PAD_TOKEN = 0
CUE_START = 1
CUE_STOP = 33
QUERY_TOKEN = 33
OPERAND_START = 34
OPERAND_STOP = 50
DISTRACTOR_START = 50
DISTRACTOR_STOP = 64

VOCAB_RANGES = {
    "pad": {PAD_TOKEN},
    "cues_keys": set(range(CUE_START, CUE_STOP)),
    "query": {QUERY_TOKEN},
    "operands_values_answers": set(range(OPERAND_START, OPERAND_STOP)),
    "distractors": set(range(DISTRACTOR_START, DISTRACTOR_STOP)),
}

Example = tuple[torch.Tensor, torch.Tensor, dict[str, Any]]


def _latin_square(generator: torch.Generator) -> list[list[int]]:
    sigma = torch.randperm(16, generator=generator).tolist()
    tau = torch.randperm(16, generator=generator).tolist()
    pi = torch.randperm(16, generator=generator).tolist()
    return [[pi[(sigma[i] + tau[j]) % 16] for j in range(16)] for i in range(16)]


def rule_table(config: Config) -> list[list[int]]:
    """Build the task's fixed Latin-rectangle rule table from seed_rules only."""
    _validate_rule_count(config.task_k)
    assert config.task_k is not None
    generator = determinism.named_generator(config.seed_rules, "rules")
    rows = _latin_square(generator)
    if config.task_k > 16:
        rows += _latin_square(generator)
    return rows[: config.task_k]


def cue_blind_bayes(config: Config) -> float:
    """Return the exact cue-blind Bayes accuracy of the configured rules."""
    _validate_rule_count(config.task_k)
    assert config.task_k is not None
    return 1 / config.task_k if config.task_k <= 16 else 1 / 16


def _validate_rule_count(task_k: int | None) -> None:
    if task_k is None or not (1 <= task_k <= 16 or task_k == 32):
        raise ValueError("task_k must be in [1, 16] or equal to 32")


def receptive_field(config: Config) -> int:
    """Return the true maximum sliding-window attention lag."""
    if config.n_layers < 1 or config.window < 1:
        raise ValueError("n_layers and window must be positive")
    return config.n_layers * (config.window - 1)


def generate(config: Config) -> Iterator[Example]:
    """Yield an infinite deterministic example stream for the configured task."""
    if config.task == "a":
        yield from task_a(config)
        return
    if config.task == "b":
        yield from task_b(config)
        return
    if config.task == "m":
        yield from task_m(config)
        return
    raise ValueError(f"no generator for task {config.task!r}")


def make_task_a_example(
    config: Config,
    cue_index: int,
    operand_index: int,
    distractor_draws: list[int],
) -> Example:
    """Construct Task A from explicit draws, for deterministic proof fixtures."""
    if config.task_N is None or config.task_k is None:
        raise ValueError("Task A requires task_N and task_k")
    if not 0 <= cue_index < config.task_k:
        raise ValueError("cue_index is outside the configured rules")
    if not 0 <= operand_index < 16:
        raise ValueError("operand_index must be in [0, 16)")
    if len(distractor_draws) != config.task_N or any(
        not 0 <= draw < 14 for draw in distractor_draws
    ):
        raise ValueError("distractor draws must contain task_N values in [0, 14)")
    return _make_task_a_example(
        config, rule_table(config), cue_index, operand_index, distractor_draws
    )


def _make_task_a_example(
    config: Config,
    rules: list[list[int]],
    cue_index: int,
    operand_index: int,
    distractor_draws: list[int],
) -> Example:
    answer = rules[cue_index][operand_index]
    token_values = (
        [CUE_START + cue_index]
        + [DISTRACTOR_START + draw for draw in distractor_draws]
        + [QUERY_TOKEN, OPERAND_START + operand_index, OPERAND_START + answer]
    )
    mask = [False] * len(token_values)
    mask[-2] = True
    metadata = {
        "cue_index": cue_index,
        "operand_index": operand_index,
        "distractor_draws": list(distractor_draws),
        "answer_index": answer,
    }
    return (
        torch.tensor(token_values, dtype=torch.long),
        torch.tensor(mask, dtype=torch.bool),
        metadata,
    )


def task_a(config: Config) -> Iterator[Example]:
    """Yield the configured Task A stream."""
    if config.task_N is None or config.task_k is None:
        raise ValueError("Task A requires task_N and task_k")
    if config.task_N < 0:
        raise ValueError("Task A requires a non-negative delay")
    cue_distance = config.task_N + 2
    if config.task_N in {512, 2048} and cue_distance <= receptive_field(config):
        raise AssertionError(
            "registered unreachable Task A placement is within the receptive field"
        )
    rules = rule_table(config)
    cues = determinism.named_generator(config.seed_data, "cues")
    operands = determinism.named_generator(config.seed_data, "operands")
    distractors = determinism.named_generator(config.seed_data, "distractors")
    while True:
        cue = int(torch.randint(0, config.task_k, (1,), generator=cues))
        operand = int(torch.randint(0, 16, (1,), generator=operands))
        draws = [
            int(torch.randint(0, 14, (1,), generator=distractors))
            for _ in range(config.task_N)
        ]
        yield _make_task_a_example(config, rules, cue, operand, draws)


def make_task_b_example(
    config: Config,
    cue_indices: list[int],
    operand_indices: list[int],
    distractor_draws: list[list[int]],
) -> Example:
    """Construct Task B segments and most-recent-cue labels from explicit draws."""
    if config.task_k != 8 or config.task_R is None:
        raise ValueError("Task B requires k=8 and R")
    if not (
        len(cue_indices)
        == len(operand_indices)
        == len(distractor_draws)
        == config.task_R
    ):
        raise ValueError("Task B explicit draws must contain exactly R segments")
    if any(not 0 <= cue < 8 for cue in cue_indices):
        raise ValueError("Task B cue indices must be in [0, 8)")
    if any(
        left == right
        for left, right in zip(cue_indices, cue_indices[1:], strict=False)
    ):
        raise ValueError("consecutive Task B cues must differ")
    if any(not 0 <= operand < 16 for operand in operand_indices):
        raise ValueError("Task B operand indices must be in [0, 16)")
    if any(any(not 0 <= draw < 14 for draw in draws) for draws in distractor_draws):
        raise ValueError("Task B distractor draws must be in [0, 14)")
    if config.task_delay_min is not None and config.task_delay_max is not None:
        if any(
            not config.task_delay_min <= len(draws) <= config.task_delay_max
            for draws in distractor_draws
        ):
            raise ValueError("Task B delay lengths must respect the configured bounds")

    rules = rule_table(config)
    token_values: list[int] = []
    mask: list[bool] = []
    for cue, operand, draws in zip(
        cue_indices, operand_indices, distractor_draws, strict=True
    ):
        segment = (
            [CUE_START + cue]
            + [DISTRACTOR_START + draw for draw in draws]
            + [
                QUERY_TOKEN,
                OPERAND_START + operand,
                OPERAND_START + rules[cue][operand],
            ]
        )
        segment_mask = [False] * len(segment)
        segment_mask[-2] = True
        token_values.extend(segment)
        mask.extend(segment_mask)
    metadata = {
        "cue_indices": list(cue_indices),
        "active_rule_indices": list(cue_indices),
        "operand_indices": list(operand_indices),
        "delay_lengths": [len(draws) for draws in distractor_draws],
        "distractor_draws": [list(draws) for draws in distractor_draws],
    }
    return (
        torch.tensor(token_values, dtype=torch.long),
        torch.tensor(mask, dtype=torch.bool),
        metadata,
    )


def task_b(config: Config) -> Iterator[Example]:
    """Yield the configured Task B stream."""
    if (
        config.task_k != 8
        or config.task_R is None
        or config.task_delay_min is None
        or config.task_delay_max is None
    ):
        raise ValueError("Task B requires k=8, R, and delay bounds")
    if config.task_R < 1 or not 0 <= config.task_delay_min <= config.task_delay_max:
        raise ValueError("invalid Task B segment or delay settings")
    cues = determinism.named_generator(config.seed_data, "cues")
    operands = determinism.named_generator(config.seed_data, "operands")
    distractors = determinism.named_generator(config.seed_data, "distractors")
    delays = determinism.named_generator(config.seed_data, "delays")
    while True:
        cue_indices: list[int] = []
        operand_indices: list[int] = []
        all_distractors: list[list[int]] = []
        previous_cue: int | None = None
        for _ in range(config.task_R):
            cue = int(torch.randint(0, 8, (1,), generator=cues))
            while cue == previous_cue:
                cue = int(torch.randint(0, 8, (1,), generator=cues))
            operand = int(torch.randint(0, 16, (1,), generator=operands))
            delay = int(
                torch.randint(
                    config.task_delay_min,
                    config.task_delay_max + 1,
                    (1,),
                    generator=delays,
                )
            )
            draws = [
                int(torch.randint(0, 14, (1,), generator=distractors))
                for _ in range(delay)
            ]
            cue_indices.append(cue)
            operand_indices.append(operand)
            all_distractors.append(draws)
            previous_cue = cue
        yield make_task_b_example(
            config, cue_indices, operand_indices, all_distractors
        )


def task_m(config: Config) -> Iterator[Example]:
    """Yield the configured Task M stream."""
    if config.task_P is None or config.task_queries is None:
        raise ValueError("Task M requires P and task_queries")
    if not 1 <= config.task_queries <= config.task_P <= 32:
        raise ValueError("Task M requires 1 <= task_queries <= P <= 32")
    if config.task_placement not in {"in_window", "beyond_window"}:
        raise ValueError("Task M requires a registered placement")
    keys_stream = determinism.named_generator(config.seed_data, "keys")
    values_stream = determinism.named_generator(config.seed_data, "values")
    queries_stream = determinism.named_generator(config.seed_data, "queries")
    distractors_stream = determinism.named_generator(config.seed_data, "distractors")
    gap_length = 0
    if config.task_placement == "beyond_window":
        gap_length = receptive_field(config) + 64
    while True:
        keys = torch.randperm(32, generator=keys_stream).tolist()[: config.task_P]
        values = [
            int(torch.randint(0, 16, (1,), generator=values_stream))
            for _ in range(config.task_P)
        ]
        queries = torch.randperm(config.task_P, generator=queries_stream).tolist()[
            : config.task_queries
        ]
        token_values: list[int] = []
        for key, value in zip(keys, values, strict=True):
            token_values.extend([CUE_START + key, OPERAND_START + value])
        gap_draws = [
            int(torch.randint(0, 14, (1,), generator=distractors_stream))
            for _ in range(gap_length)
        ]
        token_values.extend(DISTRACTOR_START + draw for draw in gap_draws)
        token_values.append(QUERY_TOKEN)
        mask = [False] * (
            2 * config.task_P + gap_length + 1 + 2 * config.task_queries
        )
        for query_index, pair_position in enumerate(queries):
            token_values.extend(
                [
                    CUE_START + keys[pair_position],
                    OPERAND_START + values[pair_position],
                ]
            )
            decision_position = (
                2 * config.task_P + gap_length + 1 + 2 * query_index
            )
            mask[decision_position] = True
        metadata = {
            "key_indices": keys,
            "value_indices": values,
            "query_pair_positions": queries,
        }
        if config.task_placement == "beyond_window":
            metadata.update({"gap_length": gap_length, "gap_draws": gap_draws})
            value_positions = range(1, 2 * config.task_P, 2)
            decision_positions = range(
                2 * config.task_P + gap_length + 1,
                len(token_values),
                2,
            )
            minimum_distance = min(
                decision - value
                for decision in decision_positions
                for value in value_positions
            )
            if minimum_distance <= receptive_field(config):
                raise AssertionError(
                    "Task M pair value is within the configured receptive field"
                )
        yield (
            torch.tensor(token_values, dtype=torch.long),
            torch.tensor(mask, dtype=torch.bool),
            metadata,
        )
