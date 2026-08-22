import hashlib
from dataclasses import replace
from pathlib import Path

import torch

from stencil.config import canonical_json, load_config
from stencil.train import first_batch, initialize_model

CONFIG_PATH = Path(__file__).parents[1] / "configs" / "test_tiny.json"
KNOWN_CANONICAL_SHA256 = (
    "0d3dca5cdef44c0cd2d025eed57a39b476c4975913d96266f4992fc53fdc3d61"
)


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
    assert hashlib.sha256(canonical_json(left)).hexdigest() == KNOWN_CANONICAL_SHA256


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
