.PHONY: verify gate-0

verify:
	uv run python scripts/verify_determinism.py

gate-0:
	uv run pytest -q
	uv run ruff check .
