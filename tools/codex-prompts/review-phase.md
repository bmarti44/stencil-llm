# Review topic: a phase's work product (generic per-phase rubric)

The wrapper's phase label names which PLAN.md phase you are reviewing (e.g. `phase0` = Phase 0). Read PLAN.md in full — the phase's spec, its gate, Appendix C, and Section 2b — then adversarially review everything the phase produced: source under src/ and scripts/, tests under tests/, configs, Makefile targets, and generated artifacts under results/.

Evaluate, in order of importance:

1. Gate honesty: do the phase's tests actually test what the PLAN registers (exact tolerances, fixtures, seeds, conventions)? Could any test pass vacuously (None gradients, empty loops, skipped asserts, fixtures regenerated from the code under test)?
2. Spec fidelity: does the implementation match every registered number and convention (mask semantics, alignment contract, seed derivation, shapes, initializations)? Recompute; do not trust comments.
3. Determinism: does the work respect the Section 3 contract (single seeded generators, no hidden nondeterminism, run_id/env recording)?
4. TDD evidence: were tests written and failing before implementation (check git history)?
5. Scope: anything implemented beyond the PLAN's registered scope, or invented where the PLAN is silent without a ledger entry?

Cite file paths and line numbers. Findings use the standard severity scale; high/critical findings block the gate.
