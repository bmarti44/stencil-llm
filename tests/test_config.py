import hashlib
import json
from dataclasses import replace
from pathlib import Path

import pytest
import torch

from stencil.config import (
    GitIdentity,
    canonical_json,
    config_hash,
    load_config,
    run_id,
)
from stencil.train import first_batch, initialize_model

CONFIG_PATH = Path(__file__).parents[1] / "configs" / "test_tiny.json"
KNOWN_CANONICAL_SHA256 = (
    "0d3dca5cdef44c0cd2d025eed57a39b476c4975913d96266f4992fc53fdc3d61"
)


def _raw_config(**overrides: object) -> dict[str, object]:
    raw = json.loads(CONFIG_PATH.read_text())
    raw.update(overrides)
    return raw


def _write_config(tmp_path: Path, raw: dict[str, object]) -> Path:
    path = tmp_path / "config.json"
    path.write_text(json.dumps(raw), encoding="utf-8")
    return path


def _task_config(task: str, **overrides: object) -> dict[str, object]:
    raw = _raw_config(
        task=task,
        task_N=None,
        task_k=None,
        task_R=None,
        task_delay_min=None,
        task_delay_max=None,
        task_P=None,
        task_queries=None,
        task_placement=None,
    )
    raw.update(overrides)
    return raw


def _state_dict_bytes(model: torch.nn.Module) -> bytes:
    return b"".join(
        tensor.detach().cpu().contiguous().numpy().tobytes()
        for tensor in model.state_dict().values()
    )


def test_config_hash_stable() -> None:
    left = {"b": 2, "a": 1.5}
    right = {"a": 1.5, "b": 2}
    expected = b'{"a":1.5,"b":2}'

    assert canonical_json(left) == expected
    assert canonical_json(right) == expected
    assert config_hash(left) == KNOWN_CANONICAL_SHA256
    assert config_hash(right) == KNOWN_CANONICAL_SHA256


def test_load_config_rejects_unknown_fields(tmp_path: Path) -> None:
    path = _write_config(tmp_path, _raw_config(unknown_field=1))
    with pytest.raises(ValueError, match="unknown config fields"):
        load_config(path)


@pytest.mark.parametrize(
    ("variant", "damping_learnable"),
    [("m1", True), ("m1b", False)],
)
def test_load_config_rejects_inconsistent_damping(
    tmp_path: Path, variant: str, damping_learnable: bool
) -> None:
    raw = _raw_config(
        variant=variant,
        osc_pairs=8,
        osc_cells=1,
        period_min=8.0,
        period_max=128.0,
        damping_learnable=damping_learnable,
    )
    path = _write_config(tmp_path, raw)
    with pytest.raises(ValueError, match="damping_learnable is inconsistent"):
        load_config(path)


def test_load_config_rejects_oscillator_fields_for_non_oscillatory(
    tmp_path: Path,
) -> None:
    path = _write_config(tmp_path, _raw_config(osc_pairs=8))
    with pytest.raises(ValueError, match="oscillator fields must be null"):
        load_config(path)


@pytest.mark.parametrize(
    "raw",
    [
        _task_config("a", task_k=8),
        _task_config("a", task_N=128, task_k=8, task_R=2),
        _task_config("b", task_k=8, task_delay_min=32, task_delay_max=256),
        _task_config(
            "b",
            task_k=8,
            task_R=2,
            task_delay_min=32,
            task_delay_max=256,
            task_N=128,
        ),
        _task_config("m", task_queries=8, task_placement="in_window"),
        _task_config(
            "m", task_P=32, task_queries=8, task_placement="in_window", task_k=8
        ),
        _task_config("copy", task_N=128),
    ],
)
def test_load_config_rejects_invalid_per_task_field_matrix(
    tmp_path: Path, raw: dict[str, object]
) -> None:
    path = _write_config(tmp_path, raw)
    with pytest.raises(ValueError, match="task fields"):
        load_config(path)


def test_load_config_period_max_covers_twice_longest_delay(tmp_path: Path) -> None:
    raw = _task_config(
        "a",
        variant="m1",
        osc_pairs=8,
        osc_cells=1,
        period_min=8.0,
        period_max=255.0,
        damping_learnable=False,
        task_N=128,
        task_k=8,
    )
    with pytest.raises(ValueError, match="twice the longest task delay"):
        load_config(_write_config(tmp_path, raw))

    raw["period_max"] = 256.0
    assert load_config(_write_config(tmp_path, raw)).period_max == 256.0


def test_load_config_rejects_invalid_task_placement(tmp_path: Path) -> None:
    raw = _task_config(
        "m", task_P=32, task_queries=8, task_placement="somewhere"
    )
    with pytest.raises(ValueError, match="invalid task_placement"):
        load_config(_write_config(tmp_path, raw))


def test_run_id_uses_registered_four_term_preimage() -> None:
    config = {"z": 3, "a": 1.5}
    identity = GitIdentity(
        git_sha="0123456789abcdef0123456789abcdef01234567",
        git_diff_sha256="a" * 64,
        untracked_sha256="b" * 64,
        dirty=True,
    )
    preimage = (
        b'{"a":1.5,"z":3}'
        + b"0123456789abcdef0123456789abcdef01234567"
        + b"a" * 64
        + b"b" * 64
    )
    expected = hashlib.sha256(preimage).hexdigest()[:12]

    assert run_id(config, identity) == expected


def test_seed_isolation() -> None:
    config = load_config(CONFIG_PATH)

    data_changed = replace(config, seed_data=config.seed_data + 1)
    assert _state_dict_bytes(initialize_model(config)) == _state_dict_bytes(
        initialize_model(data_changed)
    )
    assert not torch.equal(first_batch(config), first_batch(data_changed))

    init_changed = replace(config, seed_init=config.seed_init + 1)
    assert _state_dict_bytes(initialize_model(config)) != _state_dict_bytes(
        initialize_model(init_changed)
    )
    assert torch.equal(first_batch(config), first_batch(init_changed))
