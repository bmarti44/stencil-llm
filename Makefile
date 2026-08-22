.PHONY: verify gate-0

verify:
	uv run python scripts/verify_determinism.py

gate-0:
	uv run pytest -q \
		tests/test_determinism.py::test_determinism_two_runs_bitwise \
		tests/test_config.py::test_config_hash_stable \
		tests/test_config.py::test_seed_isolation
	uv run ruff check .
