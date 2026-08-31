codex
NOT CLEARED. No criticals, but three HIGH findings remain.

- HIGH — W3b did not evaluate the registered eligibility population. The preregistration requires eligible opportunity IDs, but [`chosen_for_work`](/home/bmarti44/stencil-llm/scripts/w3b.py:136) retains only the first eligible moment per work. Recomputing the first three trace sessions found 22 distinct eligible opportunity IDs—30 parser-fire rows—but only 11 retained. The resulting `n=90` and +42.2-point estimate are therefore from an unregistered subset. Additionally, [non-target scoring](/home/bmarti44/stencil-llm/scripts/w3b.py:176) excludes every opportunity of the target type, incorrectly excluding the other argument for hint overrides. The overall FAIL is robust—its existing subset already has 7 losses versus the ≤2 gate—but the effect size is diagnostic, not the registered estimate.

- HIGH — W3b omitted the registered execution-cost measurement. It records only [`parse_cost`](/home/bmarti44/stencil-llm/scripts/w3b.py:181), despite the [parse/exec requirement](/home/bmarti44/stencil-llm/results/w3-prereg-draft.md:74). The WORKLOG’s “parse-safe” claim must become “zero paired parse losses observed in the implemented 90-pair subset; execution cost was not recorded.” A conforming rerun would require fresh seeds and exact opportunity-ID mapping. Given the already decisive non-target failure, burden-testing favors closing W3b as an implementation-qualified negative rather than rerunning merely to obtain a better effect estimate.

- HIGH — W3a omitted the registered full per-work paired records. The runner constructs them at [lines 124–125](/home/bmarti44/stencil-llm/scripts/w3a.py:124), but writes only aggregates and hashes at [line 163](/home/bmarti44/stencil-llm/scripts/w3a.py:163). Thus the 2/6/5/26 broken counts cannot be independently reconstructed from the sealed artifact. Recover this with a deterministic reproduction audit that emits the records and matches every regenerated full-code SHA-256 to the committed hashes; do not overwrite `w3a.json`.

Everything else checks:

- W3a: headroom `155/998=.1553`; wave closure `185/155=1.1935`; `dU=185−2×2=181`; proxy `dU=131−12=119`; reinsertion `113<.8×165=132`, hence invalid; causal margin `185>131`.
- Contamination was checked on every final `build_arm_prompt` output, for all five arms, before tokenization: zero across 371 works per arm.
- Readout FAIL is correct: `73/289=.2526`.
- McNemar is correct: discordance 38/0 gives one-sided `p=2⁻³⁸≈3.64×10⁻¹²`; JSON’s rounded `0.0` is merely lossy.
- W3a’s marker, pre-run script hashes, commit ordering, and single execution are consistent with the record.

Replace the WORKLOG’s “meaning, not surface” with:

> The frozen wave generalized to the single registered unseen prefix rendering with zero trained-template occurrences. This does not establish meaning-level invariance or generalization to arbitrary paraphrases.
