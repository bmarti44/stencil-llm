"""Run the registered Phase 0 in-process determinism check."""

from pathlib import Path

from stencil.config import load_config
from stencil.train import train_losses


def main() -> None:
    config_path = Path(__file__).parents[1] / "configs" / "test_tiny.json"
    config = load_config(config_path)
    first = train_losses(config)
    second = train_losses(config)
    if len(first) != 200 or first != second:
        raise AssertionError("200-step loss sequences are not bitwise identical")
    if first[0] == first[-1]:
        raise AssertionError("training loss did not change from first to final step")
    print("determinism verified: two 200-step loss sequences are bitwise identical")


if __name__ == "__main__":
    main()
