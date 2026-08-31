codex
HIGH — not yet cleared.

[BENCH-WAVE-PLAN.md](/home/bmarti44/stencil-llm/BENCH-WAVE-PLAN.md:235) leaves the “exact-conditional fallback” undefined. For paired risk-difference non-inferiority with a nonzero margin, ordinary conditional McNemar/binomial inference is not valid: conditioning on discordant pairs does not eliminate the nuisance parameter as it does under the zero-difference null.

Fix either by:

- failing closed if Tango iteration does not converge; or
- freezing a named, implemented, fixture-tested exact-unconditional paired-risk-difference method.

The `0.5` parity tolerance and Tango primary rule are otherwise coherent.
