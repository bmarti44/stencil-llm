.PHONY: verify gate-0 gate-1 gate-2

verify:
	uv run python scripts/verify_determinism.py

gate-0:
	uv run pytest -q
	uv run ruff check .

gate-1:
	uv run pytest -q tests/test_data.py
	uv run python scripts/make_data_samples.py --check
	uv run python scripts/make_data_samples.py
	git diff --exit-code -- results/data_samples.md
	uv run ruff check .

gate-2:
	uv run pytest -q tests/test_models.py
	uv run python scripts/make_params.py --check
	uv run ruff check .
