codex
NOT CLEARED. Two HIGH findings remain.

- HIGH — the parity tolerance is knowingly unpassable. [`max_abs_error <= 1e-3`](/home/bmarti44/stencil-llm/BENCH-WAVE-PLAN.md:206) conflicts with the recorded HF parity scale: worst error was `0.365`. Use exact token-ID equality, finite logits, all-fixture top-1 equality, and a realistic frozen bound such as `max_abs_error <= 0.5`; identity is already established by hashes.

- HIGH — ordinary exact-binomial McNemar is not a non-inferiority test with a nonzero margin. The construction at [line 213](/home/bmarti44/stencil-llm/BENCH-WAVE-PLAN.md:213) tests the zero-margin null that the two discordant directions are equally likely. It cannot test degradation margins of 0.5 or 1.0 percentage points by simply changing the interpretation. Register a valid paired-proportion non-inferiority procedure—e.g. a one-sided 95% Newcombe/Tango confidence bound for the paired accuracy difference, or an exact unconditional paired test—and pass only when the upper degradation bound is below the margin.

The single-use, five-arm/two-seed, and IFBench changes are sound.
