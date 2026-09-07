# CPU fix pass for gpt-6-astra: SLAB-2 blocking findings from fable's review (2026-09-06)

Read results/slab2-review-fable.md fully (file:line). Register the fixes as "SLAB-2 Amendment 1" in
tests/fixtures/slab2_cpu_report.md BEFORE code, then fix ALL of H1-H3, M4-M7 in src/stencil/focus/slab2.py (+ a
GPU driver):
H1 Parse BEFORE write: a syntactically broken reply never reaches disk; disk stays at last_parsable; the error
   names the file and the parse error line; repairing must not trigger wrong_family.
H2 Cap and wording: raise the reply cap to 2048 (context gate must still pass — re-run the accounting); remove the
   contradiction between per-request "Document ... boundary behavior / explanatory docstring" and the system
   prompt's one-line docstring rule (one consistent instruction; re-freeze prompts); state that 577/1024 was
   reference size, not a model measurement.
H3 Cost-gate semantics: register lane_seconds = GPU-held wall / concurrent lanes at the same max_workers as the
   registered run; the 12 GPU-h gate is evaluated on that; write the three projections (aggregate 24.7 tok/s,
   per-stream 11 tok/s, model-style x1.35) as the pre-written cost table.
M4 Witness power: schedule the delivery obligation BEFORE the format retirement in the lifecycle shapes so the
   primary substitution witness (delivery -> ready after completes) has opportunities in >= 7/8 DEV and >= 56/64
   eval episodes; keep format as an omission trait (floor-gated); regenerate manifests (same seeds), assert counts.
M5 Parser tolerance set (registered, bounded, labelled per reply): CRLF; leading/trailing prose outside the
   fence; trailing period; case-insensitive status; key-order variants; blank line before the trailer; language
   tags py/python/Python/bare; a leading <think></think> block. Anything else = breakage with a category.
M6 12-round fallback: implement n_rounds as a registered parameter (16 default; 12 fallback) so dry_run and
   paired_clauses accept it; the fallback is a pre-registered science change, applied only by the cost rule.
M7 GPU driver: scripts/composition_pilot5.py (or a mode in the existing runner) that drives slab2 through
   loop.generate_once with the vLLM decoder adapter, plumbs `truncated` into Executor.run and the records, and
   records per-lane seconds; CPU stub smoke test through the real driver path (no GPU).
Tests for each; run tests/test_focus_*.py + tests/test_no_side_effect_imports.py; commit only src/stencil/focus/
slab2.py, scripts/composition_pilot5.py, tests/**, tests/fixtures/slab2_*, WORKLOG (<= 6 lines) with explicit
pathspecs; no push; no GPU (checks 46-50 own it); never terminate or signal any process; never read anything
under data/bench or evaluation episode content. Report test counts and the new accounting/cost table.
