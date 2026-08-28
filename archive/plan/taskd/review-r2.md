SCORE: 51

## Findings

1. **critical — Task D remains register-shaped (partially resolved; open).** Four independently updated slots materially improve the task and defeat the existing single B3 latch. However, the sufficient statistic is still exactly a four-slot keyed register. Omitting a matched four-slot latch makes B3 deliberately under-capacity and leaves the obvious exact non-oscillatory solution untested. Add a keyed four-slot register—preferably within the same 128-state budget—or an oscillator win cannot be attributed to its substrate.

2. **critical — Gold-answer leakage (resolved).** Separate targets, PAD placeholders, and the explicit prohibition against answer tokens appearing in later inputs remove the teacher-forcing channel. The planned fixture and leakage assertions adequately bind this at plan level.

3. **critical — Reinsertion incumbent fairness (partially resolved; open).** Refreshing all slots every 128 tokens repairs the original 512-versus-252 strawman, and pre-query reinsertion is a valuable upper bound. But pre-query reinsertion is also a plausible real-world incumbent and may inject fewer tokens than periodic refresh—16 query blocks versus roughly 32 periodic blocks—yet it is excluded from the verdict. All reinsertion methods already rely on generator-known active state, so calling one “oracle” does not justify ignoring it. Benefit must be assessed against the best accuracy–cost reinsertion policy.

4. **critical — Adequacy filtering (resolved).** Initial seeds always enter the primary results, retries are separate, and adoption failure blocks rather than enables a positive claim. This closes the selection-bias defect.

5. **high — Decision table remains contradictory and cost-blind (open).** BENEFIT and NO SUBSTRATE BENEFIT can both hold: if B3 exceeds M1 by 0.5 points everywhere, M1 is still “within 1 point” for rule 1 while B3 dominates within rule 2’s tolerance. No precedence resolves this. The verdict also records cost without using it, so it can call an expensive one-point accuracy gain a benefit while rejecting equal accuracy with substantially lower token overhead. Define disjoint ordered outcomes on an explicit accuracy–compute/token Pareto rule.

6. **high — Oscillator-family adjudication is asymmetric (partially resolved; open).** Adding M1b and B2 closes the contender omission, but only M1 can receive BENEFIT. A decisive M1b advantage would be forced to MIXED despite demonstrating oscillator-family benefit. The adequacy prose also says either M1 or M1b failure blocks benefit, while the decision table checks only M1 adequacy. Register symmetric per-variant decisions or a non-post-hoc family aggregation with multiplicity handling.

7. **high — Holdout sealing is fixed, but schedule construction remains under-specified (partially resolved; open).** The validation/final split and fleet freeze are strong. Load-bearing generation details remain deferred: numeric family-specific update counts, fitting sampled gaps into exactly 4096 tokens, query sampling without duplicates, collision priority, query-slot sampling, resampling no-op “updates,” and whether reinsertion shifts or replaces base tokens. “Draw order registered in the brief” is too late—the accepted scientific plan must freeze it. Paired comparisons also require a shared latent schedule identifier unaffected by reinsertion.

8. **high — Metrics are improved but not yet comparison-safe (partially resolved; open).** Fixed bins and first-crossing survival resolve the gameable half-life. Remaining ambiguities include whether “updates absorbed” means global or queried-slot updates, the precise unconditional stale-error null, and data-dependent upward merging that can produce different bins across contenders or no legal upward bin. Comparisons require canonical shared bins, explicit NA behavior, and numerator/denominator counts.

9. **high — Ragged decision shapes (resolved).** Fixed 4096-token sequences and exactly 16 decisions provide static tensor shapes compatible with batching and CUDA graphs, assuming finding 7’s insertion semantics preserve those counts.

10. **medium — Compaction realism (partially resolved; open).** The plan now honestly scopes the experiment to local-attention persistence, which fixes the overclaim. It still does not test actual summary compaction, summary/update conflicts, or lossy retained state. Therefore even a valid result answers only a toy proxy for Brian’s broader compaction setting; that limitation must constrain the headline, not merely appear as a caveat.

11. **medium — Pilot budgeting and deterministic evidence (resolved).** Piloting M1, B4, and reinsertion covers the materially different cost classes and defers the fleet projection to measurements. Record comparison hashes before discarding the scratch rerun so the bitwise claim remains auditable.

12. **high — Token-role reuse corrupts B3 and B4 semantics (new; open).** The current model treats every token in 1..32 as a cue. Because slot markers 29..32 also appear inside queries, B3 will overwrite its latch with the queried slot marker at every query, rather than behave as the intended single-rule latch. B4 will globally retain query slot markers as though they were instructions. Task D needs explicit role masks—or distinct update/query marker tokens—so only actual instruction-update tokens drive B3 and B4 retention.

13. **critical — The primary benefit contrast has no common tail support (new; open).** Distance is defined since the latest true update or reinsertion. Reinsert-128 therefore has no observations beyond 252 tokens, yet BENEFIT requires M1 to beat it specifically at distances greater than 252 using paired sequences. That comparison is undefined, not merely difficult. Use a shared axis such as distance since the last true update for cross-contender decisions, while reporting contender-specific information age separately.

## Alignment verdict

Not yet. V2 is substantially closer: it introduces simultaneous instruction state, removes answer leakage, preserves all seeds, seals the final holdout, and adds strong recurrent and reinsertion contenders. But the omitted four-slot latch, undefined primary tail comparison, overlapping verdicts, asymmetric M1/M1b treatment, and broken B3/B4 token masks still prevent execution from answering whether the oscillator provides a real benefit. After those are fixed, the benchmark could answer a scoped toy-scale local-attention version of Brian’s question; it still would not directly test real summary compaction.

## Unverified surfaces

No Task D implementation, fixture, configs, fleet-freeze mechanism, or metric artifact exists yet. Consequently, separate-target plumbing, schedule pairing, insertion length semantics, role masks, sealed-offset enforcement, bin counts, stale-null arithmetic, bitwise reproduction, and 4096-token runtime remain unverified.