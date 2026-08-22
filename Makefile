.PHONY: verify gate-0 gate-1

verify:
	uv run python scripts/verify_determinism.py

gate-0:
	uv run pytest -q
	uv run ruff check .

gate-1:
	uv run pytest -q tests/test_data.py
	uv run ruff check .
