codex
NOT VERIFIED.

### CRITICAL — Finding 3 draws an unsafe conclusion that T0.3b directly contradicts

[press-plan-report.md:45](/home/bmarti44/stencil-llm/results/press-plan-report.md:45) claims structural provenance eliminates the costly boundary and therefore press-timing policies need “no safety machinery at all.”

T0.3 tested:

- a non-authoritative span at the right moment;
- the correct authoritative span at a wrong moment.

It did not test the wrong authoritative type. T0.3b did—and provenance-safe scheduled presses had negative expected utility in every cell, with 1–4.5% broken works. Provenance removes non-authoritative-span errors; it does not prevent semantic mistargeting among authoritative entries.

Replace finding 3 with: structural provenance eliminates the specific non-authoritative risk measured by T0.3, but type/moment routing still needs a parser, checker, or validated selector.

### HIGH — Three ladder claims misstate their artifacts

At [line 20](/home/bmarti44/stencil-llm/results/press-plan-report.md:20), `k=149/160` comprises 71 false-selection sessions plus 79 assertion misses, with one overlap. The cosine policy’s actual error evidence is 71/160 false-selection sessions—still a decisive failure, `U95≈0.512`. The report currently attributes the entire 149 to discrimination.

At [line 21](/home/bmarti44/stencil-llm/results/press-plan-report.md:21), `30/48 → 1/17` does not equal a 93% reduction and mixes train-hard with calib-hard denominators. The defensible comparison is the reused calib screen: old policy `14/17` hazard-facing sessions versus trained head `1/17`, a 92.9% descriptive reduction. Disclose that this is an unsealed calibration result.

At [line 22](/home/bmarti44/stencil-llm/results/press-plan-report.md:22), nullosc does not tie every trained controller. It ties oscillator and GRU at 2 leaks, while beating EMA at 3 and static at 5. Also disclose that this ranking uses the third-used, 17-hazard-session calibration set.

### HIGH — The “proven deployable recipe” was never evaluated as a composition

[Lines 36–44](/home/bmarti44/stencil-llm/results/press-plan-report.md:36) describe structured+reactive pressing as a proven layered recipe. The artifacts test structured and reactive separately; there is no combined arm.

The structured oracle’s `+14.5` validation gain also carried 7 paired parse and 11 exec losses over 409 works, failed the registered zero-loss gate, and incurred the previously reported ~1.7% validity tax. Call these “individually supported candidate components”; composition and deployment remain untested.

### HIGH — T0.3b’s matching-moment counts are computed with incompatible units

[t0_costb.py:117](/home/bmarti44/stencil-llm/scripts/t0_costb.py:117) slices decoded characters using `step`, which is a generated-token index. Consequently, the reported `0–12/200` matching-moment counts and the “presses off-moment” explanation are not valid.

The negative expected-ΔU gate does not depend on these classifications and remains valid. Remove the class-count claim or recompute moments from token-aligned prefixes.

### HIGH — Review-round accounting is unsupported

[Lines 69–70](/home/bmarti44/stencil-llm/results/press-plan-report.md:69) claim 14 sol and 7 fable rounds. The named categories contain 16 committed sol review artifacts; WORKLOG records nine fable rounds. Remove the totals or state a reproducible counting convention.
