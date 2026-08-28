# Brief: phase3-perf2 — perf sweep remainder (items 5-6) + after-timing

## Objective

Complete the phase3-perf plan (read tools/codex-agents/phase3-perf.md and your predecessor's stop-point: items 1-3 landed green; item 4 is CLOSED by orchestrator ruling — C=256 retained, the registered tolerance is a frozen contract and is not weakened; do NOT revisit the chunked scan).

5. **Co-tenancy** (`scripts/run_matrix.py`): `--jobs N` bounded process pool (default 1); DONE-marker semantics unchanged. Test: pool of 2 fake fast cells (tmp dirs) both complete with DONE markers; a third queued cell runs after a slot frees.
6. **Cheap cleanups**: RoPE cos/sin cached as buffers (bitwise-identical — assert on logits); AdamW `foreach=True` (numerics shift permitted pre-evidence; note prominently in handoff).

Then the AFTER timing probe: 20 timed steps at batch 8, seq 2052, for b0_local and m1, with items 1-3+6 active (graph path on, truncation on for banded variants); report beside the predecessor's before-figures (b0_local 0.10982, m1 0.31883 s/step).

## Tests first (TDD, rule 1 — per-test red)

Both items' tests red first. Run only your own/touched tests.

## Allowlist

See phase3-perf2.allow. Do not touch PLAN.md, plan/, tools/, AGENTS.md, README.md, tests/fixtures/*.

## Acceptance

New tests green, ruff clean, before/after timing table. Full suite + gate-2 + pilot are the orchestrator's.

## Ledger handoff

Do not edit the ledger. End with: files changed, red/green pairs, the timing table, the foreach numerics note, residual choices (v1.10).
