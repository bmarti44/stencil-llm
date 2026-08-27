SCORE: 86

## Findings

1. **critical — Register-shaped benchmark (resolved).** The four-slot state and matched 128-dimensional keyed-latch comparator make oscillator-specific benefit falsifiable.

2. **critical — Gold-answer leakage (resolved).** Separate targets and fixed input placeholders eliminate answer-derived recovery.

3. **critical — Reinsertion incumbent fairness (resolved).** Both exact periodic reinsertion and pre-query reinsertion are verdict-bearing, with explicit token costs.

4. **critical — Adequacy filtering (resolved).** Initial seeds remain reported; inadequate rivals cannot manufacture either positive or negative evidence, and the intentionally under-capacity B3 is descriptive only.

5. **high — V1 still lacks the promised seed-robust tail floor (partially resolved; open).** The operative V1 rule still says only “OSC tail accuracy ≥50%.” It never imposes the 40% minimum for every seed claimed in the Round 5 summary. Moreover, “tail accuracy” is undefined across two families and potentially several bins. Thus a strong mean could still hide a Phase-3-style catastrophic seed. Define the aggregation and add the minimum-seed requirement directly to V1; review-history prose does not amend the decision rule.

6. **high — Oscillator selection and recurrent controls (resolved).** M1/M1b selection is validation-sealed with a deterministic tie-break, and B2 plus B3k provide attribution-bearing non-oscillatory controls.

7. **high — Holdout schedule construction (resolved).** The common 3,848-token core, fixed draw law, bounded rejection, exact four-token query blocks, and 31-refresh arithmetic now form a coherent, paired schedule design.

8. **high — Gameable or misleading diagnostics (resolved).** Shared-support bins, invariant true-update distance, NA behavior, first-crossing survival, and the error-conditioned stale preference statistic are sufficiently specified.

9. **high — Ragged/CUDA-incompatible shapes (resolved).** Training now consistently uses 12 updates, while the registered 16-event/32-position tensor and validity mask provide fixed consumer shapes.

10. **medium — Compaction realism (partially resolved; open).** The plan correctly limits its claim to persistence beyond local attention. It does not test survival through actual lossy summary compaction, so any conclusion must retain that qualification.

11. **medium — Scope and pilot budgeting (resolved).** Four relevant cost classes are piloted before the 24-run fleet, with timing, memory, deterministic hashes, and a launch decision based on measured cost.

12. **high — Query/update token-role collision (resolved).** Distinct query-slot tokens prevent queries from mutating latch or retained-cue state.

13. **critical — Reinsertion-invariant comparison support (resolved).** Every contender now receives the same latent core and comparisons use core-coordinate schedules and distances, eliminating contender-dependent tail support.

## Alignment verdict

V6 is nearly sufficient to answer Brian’s question at toy scale for dynamic instruction tracking beyond local attention, with strong reinsertion and non-oscillatory controls. It is not ready for an honest positive verdict because the operative success rule can still average away catastrophic oscillator seeds and leaves tail aggregation ambiguous. Put the promised per-seed floor and exact family/bin aggregation into V1; after that, the plan would be decision-capable within its explicitly limited local-attention—not real summary-compaction—scope.

## Unverified surfaces

No Task D implementation or results were available to verify. Implementation review must confirm common-core identity across contenders, exact refresh placement, fixed event tensors and masks, exclusion of reserved query tokens from distractors, target/logit alignment, sealed-final enforcement, metric arithmetic, and literal enforcement of the corrected V1 rule.