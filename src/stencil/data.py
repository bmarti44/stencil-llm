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
    if config.task == "d":
        yield from task_d(config)
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


def _sample_task_a_example(
    config: Config,
    rules: list[list[int]],
    cues: torch.Generator,
    operands: torch.Generator,
    distractors: torch.Generator,
    *,
    distractor_draws: list[int] | None = None,
) -> Example:
    """Sample one Task A example from its independent production streams."""
    if config.task_N is None or config.task_k is None:
        raise ValueError("Task A requires task_N and task_k")
    cue = int(torch.randint(0, config.task_k, (1,), generator=cues))
    operand = int(torch.randint(0, 16, (1,), generator=operands))
    draws = (
        [
            int(torch.randint(0, 14, (1,), generator=distractors))
            for _ in range(config.task_N)
        ]
        if distractor_draws is None
        else list(distractor_draws)
    )
    return _make_task_a_example(config, rules, cue, operand, draws)


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
        yield _sample_task_a_example(
            config, rules, cues, operands, distractors
        )


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


def task_d_curriculum_bounds(config: Config, step: int) -> tuple[int, int]:
    """Interpolate Task D training gap bounds, leaving update count fixed."""
    required = (
        config.task_d_curriculum_start,
        config.task_d_curriculum_end,
        config.task_d_curriculum_gap_min,
        config.task_d_curriculum_gap_max,
        config.task_d_gap_min,
        config.task_d_gap_max,
    )
    if any(value is None for value in required) or step < 0:
        raise ValueError("Task D curriculum requires complete non-negative bounds")
    start, end, initial_lo, initial_hi, final_lo, final_hi = required
    assert all(isinstance(value, int) for value in required)
    if step <= start:
        return initial_lo, initial_hi
    if step >= end:
        return final_lo, final_hi
    elapsed = step - start
    duration = end - start
    return (
        initial_lo + (final_lo - initial_lo) * elapsed // duration,
        initial_hi + (final_hi - initial_hi) * elapsed // duration,
    )


def _task_d_gap_vector(config: Config, delays: torch.Generator) -> list[int]:
    assert config.task_d_updates is not None
    family = config.task_d_family
    if family == "burst":
        bounds = []
        for index in range(config.task_d_updates):
            if index == 0:
                bounds.append(
                    (config.task_d_burst_start_min, config.task_d_burst_start_max)
                )
            elif index in {3, 6}:
                bounds.append(
                    (config.task_d_burst_inter_min, config.task_d_burst_inter_max)
                )
            else:
                bounds.append(
                    (config.task_d_burst_intra_min, config.task_d_burst_intra_max)
                )
    else:
        bounds = [
            (config.task_d_gap_min, config.task_d_gap_max)
        ] * config.task_d_updates
    if any(lo is None or hi is None for lo, hi in bounds):
        raise ValueError("Task D gap bounds are incomplete")
    return [int(torch.randint(lo, hi + 1, (1,), generator=delays)) for lo, hi in bounds]


def _task_d_update_starts(slots: int, gaps: list[int]) -> list[int]:
    previous_end = 2 * slots
    starts = []
    for gap in gaps:
        start = previous_end + gap
        starts.append(start)
        previous_end = start + 2
    return starts


def _task_d_active(updates: list[list[int]], core_position: int) -> dict[int, int]:
    active: dict[int, int] = {}
    for start, slot, rule in updates:
        if start < core_position:
            active[slot] = rule
    return active


def _task_d_refresh(
    updates: list[list[int]], core_position: int, slots: int
) -> list[int]:
    active = _task_d_active(updates, core_position)
    if len(active) != slots:
        raise AssertionError(
            "Task D refresh occurred before all slots were initialized"
        )
    result = []
    for slot in range(1, slots + 1):
        result.extend((28 + slot, active[slot]))
    return result


def _task_d_expand(
    config: Config,
    core_tokens: list[int],
    core_targets: list[int],
    updates: list[list[int]],
    queries: list[dict[str, Any]],
) -> tuple[list[int], list[int], list[int | None], list[int]]:
    assert config.task_d_slots is not None
    policy = config.task_d_reinsert
    out: list[int] = []
    targets: list[int] = []
    core_by_final: list[int | None] = []
    refresh_starts: list[int] = []
    query_starts = {query["start"] for query in queries}

    if policy == "every-128":
        multiples = iter(range(128, 3969, 128))
        next_multiple = next(multiples, None)
        for core_position, (token, target) in enumerate(
            zip(core_tokens, core_targets, strict=True)
        ):
            if next_multiple is not None and len(out) == next_multiple - 8:
                refresh_starts.append(len(out))
                refresh = _task_d_refresh(updates, core_position, config.task_d_slots)
                out.extend(refresh)
                targets.extend([-1] * 8)
                core_by_final.extend([None] * 8)
                next_multiple = next(multiples, None)
            out.append(token)
            targets.append(target)
            core_by_final.append(core_position)
        if next_multiple is not None:
            raise AssertionError("Task D periodic expansion missed a refresh boundary")
    elif policy == "prequery":
        for core_position, (token, target) in enumerate(
            zip(core_tokens, core_targets, strict=True)
        ):
            if core_position in query_starts:
                refresh_starts.append(len(out))
                refresh = _task_d_refresh(updates, core_position, config.task_d_slots)
                out.extend(refresh)
                targets.extend([-1] * 8)
                core_by_final.extend([None] * 8)
            out.append(token)
            targets.append(target)
            core_by_final.append(core_position)
    elif policy in {"none", "miniature-64"}:
        out = list(core_tokens)
        targets = list(core_targets)
        core_by_final = list(range(len(core_tokens)))
    else:
        raise ValueError(f"invalid Task D reinsert policy: {policy}")

    final_length = 4096 if len(core_tokens) == 3848 else len(out)
    while len(out) < final_length:
        out.append(DISTRACTOR_START)
        targets.append(-1)
        core_by_final.append(None)
    if len(out) != final_length:
        raise AssertionError("Task D expansion has the wrong final length")
    return out, targets, core_by_final, refresh_starts


def _task_d_miniature_reinsert(
    tokens: list[int], updates: list[list[int]], slots: int
) -> list[int]:
    """Reproduce the binding hand fixture's registered miniature-64 expansion."""
    out: list[int] = []
    final_position = 0
    for core_position, token in enumerate(tokens):
        if final_position and final_position % 64 == 0:
            refresh = _task_d_refresh(updates, core_position, slots)
            out.extend(refresh)
            final_position += len(refresh)
        out.append(token)
        final_position += 1
    return out


def _assemble_task_d(
    config: Config,
    rules: list[list[int]],
    updates: list[list[int]],
    query_draws: list[tuple[int, int, int]],
    distractors: torch.Generator,
    *,
    gaps: list[int] | None = None,
    noop_update_indices: list[int] | None = None,
    redraw_count: int = 0,
    fallback_count: int = 0,
    seed_data: int | None = None,
    sequence_index: int | None = None,
) -> Example:
    assert config.task_d_core_len is not None and config.task_d_slots is not None
    core_tokens: list[int | None] = [None] * config.task_d_core_len
    for start, slot, rule in updates:
        if not 0 <= start < config.task_d_core_len - 1:
            raise ValueError("Task D update is outside the core")
        if core_tokens[start] is not None or core_tokens[start + 1] is not None:
            raise ValueError("Task D updates overlap")
        core_tokens[start], core_tokens[start + 1] = 28 + slot, rule
    core_targets = [-1] * config.task_d_core_len
    query_metadata: list[dict[str, Any]] = []
    for start, slot, operand in query_draws:
        if not 0 <= start < config.task_d_core_len - 3:
            raise ValueError("Task D query is outside the core")
        if any(
            core_tokens[position] is not None for position in range(start, start + 4)
        ):
            raise ValueError("Task D query overlaps another event")
        active = _task_d_active(updates, start)
        if slot not in active:
            raise ValueError("Task D query precedes its slot initialization")
        rule = active[slot]
        answer = OPERAND_START + rules[rule - 1][operand]
        core_tokens[start : start + 4] = [
            QUERY_TOKEN,
            59 + slot,
            OPERAND_START + operand,
            PAD_TOKEN,
        ]
        core_targets[start + 2] = answer
        query_metadata.append(
            {
                "start": start,
                "slot": slot,
                "x": operand,
                "active_rule": rule,
                "answer": answer,
            }
        )
    for position, token in enumerate(core_tokens):
        if token is None:
            core_tokens[position] = 50 + int(
                torch.randint(0, 10, (1,), generator=distractors)
            )
    concrete_core = [int(token) for token in core_tokens]
    tokens, targets, core_by_final, refresh_starts = _task_d_expand(
        config, concrete_core, core_targets, updates, query_metadata
    )
    final_by_core = {
        core: final for final, core in enumerate(core_by_final) if core is not None
    }
    for query in query_metadata:
        if len(tokens) != len(concrete_core):
            query["final_start"] = final_by_core[query["start"]]
            query["final_positions"] = [
                final_by_core[query["start"] + offset] for offset in range(4)
            ]
            query["final_decision_position"] = final_by_core[query["start"] + 2]
            query["final_pad_position"] = final_by_core[query["start"] + 3]
    event_positions = [
        final_by_core[position]
        for update in updates
        for position in update[:1]
        for position in (position, position + 1)
    ]
    if len(event_positions) > 32:
        raise AssertionError("Task D event tensor exceeds its fixed width")
    cue_positions = torch.zeros(32, dtype=torch.long)
    cue_valid = torch.zeros(32, dtype=torch.bool)
    cue_positions[: len(event_positions)] = torch.tensor(event_positions)
    cue_valid[: len(event_positions)] = True
    target_tensor = torch.tensor(targets, dtype=torch.long)
    metadata: dict[str, Any] = {
        "targets": target_tensor,
        "updates": updates,
        "queries": query_metadata,
        "noop_update_indices": list(noop_update_indices or []),
        "gaps": list(gaps or []),
        "gap_redraws": redraw_count,
        "gap_fallbacks": fallback_count,
        "cue_positions": cue_positions,
        "cue_valid": cue_valid,
        "refresh_block_starts": refresh_starts,
        "core_position_by_final": core_by_final,
        "schedule_id": (
            config.task_d_family,
            config.task_d_schedule_offset,
            sequence_index,
        ),
    }
    if seed_data is not None:
        metadata["seed_data"] = seed_data
    if config.task_d_reinsert == "miniature-64":
        metadata["reinsert64_tokens"] = _task_d_miniature_reinsert(
            concrete_core, updates, config.task_d_slots
        )
    return (
        torch.tensor(tokens, dtype=torch.long),
        target_tensor >= 0,
        metadata,
    )


def make_task_d_example(
    config: Config,
    *,
    updates: list[tuple[int, int, int]],
    queries: list[tuple[int, int, int]],
) -> Example:
    """Construct Task D from explicit core-coordinate events for proof tests."""
    normalized = [list(update) for update in updates]
    initial_count = config.task_d_slots or 0
    noops: list[int] = []
    active: dict[int, int] = {}
    for event_index, (_, slot, rule) in enumerate(normalized):
        if event_index >= initial_count and active.get(slot) == rule:
            noops.append(event_index - initial_count)
        active[slot] = rule
    return _assemble_task_d(
        config,
        rule_table(config),
        normalized,
        queries,
        determinism.named_generator(config.seed_data, "distractors"),
        noop_update_indices=noops,
    )


def task_d(config: Config) -> Iterator[Example]:
    """Yield the frozen Task D common-core schedule and policy expansion."""
    required = (
        config.task_d_slots,
        config.task_d_core_len,
        config.task_d_updates,
        config.task_d_queries,
    )
    if any(value is None for value in required) or config.task_k != 8:
        raise ValueError("Task D requires slots, core length, updates, Q, and k=8")
    assert config.task_d_slots is not None
    assert config.task_d_updates is not None
    assert config.task_d_queries is not None
    assert config.task_d_core_len is not None
    stream_seed = config.seed_data + (config.task_d_schedule_offset or 0)
    cues = determinism.named_generator(stream_seed, "cues")
    delays = determinism.named_generator(stream_seed, "delays")
    operands = determinism.named_generator(stream_seed, "operands")
    distractors = determinism.named_generator(stream_seed, "distractors")
    rules = rule_table(config)
    requested_sequence_index = config.task_d_sequence_index or 0
    sequence_index = 0
    while True:
        updates: list[list[int]] = []
        active: dict[int, int] = {}
        for slot in range(1, config.task_d_slots + 1):
            rule = int(torch.randint(1, 9, (1,), generator=cues))
            updates.append([2 * (slot - 1), slot, rule])
            active[slot] = rule

        gaps: list[int] = []
        fallback_count = 0
        redraw_count = 0
        for attempt in range(64):
            gaps = _task_d_gap_vector(config, delays)
            starts = _task_d_update_starts(config.task_d_slots, gaps)
            if (
                starts[-1] + 2 + config.task_d_queries * 4
                <= config.task_d_core_len - 64
            ):
                redraw_count = attempt
                break
        else:
            redraw_count = 64
            starts = _task_d_update_starts(config.task_d_slots, gaps)
            excess = (
                starts[-1]
                + 2
                + config.task_d_queries * 4
                - (config.task_d_core_len - 64)
            )
            gaps[-1] = max(0, gaps[-1] - excess)
            starts = _task_d_update_starts(config.task_d_slots, gaps)
            if starts[-1] + 2 + config.task_d_queries * 4 > config.task_d_core_len - 64:
                raise ValueError("Task D final-gap fallback cannot fit the core")
            fallback_count = 1

        update_slots = [
            int(torch.randint(1, config.task_d_slots + 1, (1,), generator=cues))
            for _ in range(config.task_d_updates)
        ]
        update_rules = [
            int(torch.randint(1, 9, (1,), generator=cues))
            for _ in range(config.task_d_updates)
        ]
        noops: list[int] = []
        for index, (start, slot, rule) in enumerate(
            zip(starts, update_slots, update_rules, strict=True)
        ):
            if active[slot] == rule:
                noops.append(index)
            active[slot] = rule
            updates.append([start, slot, rule])

        blocked: set[int] = set()
        for start, _, _ in updates:
            blocked.update(range(start - 2, start + 4))
        query_starts: list[int] = []
        initial_end = 2 * config.task_d_slots
        for _ in range(config.task_d_queries):
            valid = [
                start
                for start in range(initial_end, config.task_d_core_len - 4)
                if all(start + offset not in blocked for offset in range(4))
            ]
            if not valid:
                raise AssertionError("Task D has no valid query start")
            draw = int(torch.randint(0, len(valid), (1,), generator=operands))
            start = valid[draw]
            query_starts.append(start)
            blocked.update(range(start - 2, start + 6))
        query_slots = [
            int(torch.randint(1, config.task_d_slots + 1, (1,), generator=cues))
            for _ in range(config.task_d_queries)
        ]
        query_operands = [
            int(torch.randint(0, 16, (1,), generator=operands))
            for _ in range(config.task_d_queries)
        ]
        example = _assemble_task_d(
            config,
            rules,
            updates,
            list(zip(query_starts, query_slots, query_operands, strict=True)),
            distractors,
            gaps=gaps,
            noop_update_indices=noops,
            redraw_count=redraw_count,
            fallback_count=fallback_count,
            seed_data=stream_seed,
            sequence_index=sequence_index,
        )
        if sequence_index >= requested_sequence_index:
            yield example
        sequence_index += 1
