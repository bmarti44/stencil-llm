"""Opt-in DEV-only execution for CPU harness amendment work."""

import sys
from pathlib import Path

import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--focus-dev-only",
        action="store_true",
        help="Skip SLAB evaluation construction before accessing episode content.",
    )


def pytest_configure(config):
    if not config.getoption("--focus-dev-only"):
        return
    from stencil.focus import slab

    original = slab.generate_episode

    def dev_only(family="dev", *args, **kwargs):
        if family != "dev":
            pytest.skip("CPU fix scope: evaluation construction prohibited")
        return original(family, *args, **kwargs)

    slab.generate_episode = dev_only

    def deny_bench(event, args):
        if event == "open" and isinstance(args[0], (str, bytes)):
            path = str(
                Path(
                    args[0].decode() if isinstance(args[0], bytes) else args[0]
                ).resolve()
            )
            if "/data/bench/" in path or path.endswith("/data/bench"):
                raise AssertionError("CPU fix scope: benchmark access prohibited")

    sys.addaudithook(deny_bench)
