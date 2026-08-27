SCORE: 54

## Findings

1. **critical — Register-shaped benchmark (resolved).** B3k remains the exact, state-budget-matched register comparator needed for honest substrate attribution.

2. **critical — Gold-answer leakage (resolved).** Separate targets and PAD placeholders remain correctly specified.

3. **critical — Reinsertion incumbent fairness (resolved).** Both periodic and pre-query policies remain inside the verdict, with token overhead explicitly scoped.

4. **critical — Adequacy handling (open; v4 regression).** V4 requires every verdict-bearing contender—including B3—to have all seeds reach 95% ID accuracy. But B3 is intentionally under-capacity and “provably insufficient,” so its expected failure makes V1 impossible by construction. Adequacy must test optimization/adoption rather than require an incapable architecture to solve Task D. Make B3 descriptive only, or exclude it from V1 adequacy while requiring adequate training for the genuinely competitive rivals. More generally, distinguish “failed to adopt a usable pathway” from substantive architectural inability.

5. **high — Verdict semantics remain incorrect despite fixed boundaries (open).** The `<1` versus `≥1` assignments repair the prior numerical overlap. However, V2’s parity clause requires every adequate rival to tie OSC everywhere. If B3k ties OSC exactly while the intentionally weak B3 loses badly, V2 does not fire and the outcome becomes MIXED—despite the exact simpler register proving no substrate benefit. Parity should require existence of one adequate zero-token stateful rival matching OSC everywhere, not parity by every rival. Reinsertion parity should remain compatible with V1 because OSC avoids its token overhead. The frozen three-seed mean is now explicit, but a positive verdict can still hide catastrophic held-out failure in one seed; given Phase 3’s known variance, require a min-seed tail floor or consistent paired-seed direction.

6. **high — Primary oscillator selection lacks a deterministic tie rule (partially resolved; reopened).** Validation-based selection now uses a defined seed-mean framework, but exact M1/M1b ties are likely on the ID control and remain unresolved. Freeze a tie-break—such as M1 on exact equality—before implementation.

7. **high — Schedule construction is improved but still inconsistent (partially resolved; open).** Direct bounded draws and rejection repair the prior rescaling defect, but:

   - “Bounded rejection” has no maximum attempts or deterministic failure rule.
   - Reinsert-128 reserves 31 refresh blocks, while only 30 multiples of 128 lie on its 3848-token base timeline; the plan must state that refresh positions are defined in final-token coordinates if that is the intended arithmetic.
   - Scheduled queries are treated as three-token blocks even though the required PAD placeholder occupies a fourth token. PAD placement and collision exclusion must cover the complete four-token event.
   - The curriculum changes update count from 24 to 12 without specifying integer interpolation and rounding.

8. **high — Stale-error metric uses an incompatible null (open).** The observed metric is described as unconditional stale errors over all queries, but `|stale outputs| / 15` is the null conditional on already being wrong and choosing uniformly among the 15 wrong answers. For an unconditional uniform answer, the null is `|stale outputs| / 16`. Alternatively, retain `/15` and define the observed metric as stale errors divided by wrong answers, or subtract `wrong_indicator × |stale outputs|/15` per query. As written, the “excess” mostly reflects overall accuracy rather than stale-rule preference.

9. **high — CUDA-graph shapes are not fixed across the curriculum (reopened).** Q=16 fixes decision tensors, but changing the update count from 24 to 12 changes the number of cue positions. The existing CUDA graph allocates `cue_positions` and `cue_valid` from the first batch and rejects later shape changes. Pad cue tensors to the registered curriculum maximum with validity masks, keep update count fixed, or disable CUDA graphs for Task D.

10. **medium — Compaction realism (partially resolved; open).** The plan remains honestly scoped to local-attention persistence, not actual summary compaction. The final headline must retain that limitation.

11. **medium — Pilot budgeting (resolved).** Four cost classes and retained comparison hashes now agree across implementation and verification.

12. **high — B3/B4 token-role collision (resolved).** Query/update markers remain separated. Task D must still exclude reserved tokens 60–63 from distractor sampling during implementation.

13. **critical — Shared tail support (reopened).** The decision axis is conceptually correct, but the “shared latent timeline” is not shared: none, periodic reinsertion, and pre-query reinsertion use base lengths 4096, 3848, and 3968. Gap rejection thresholds and query valid-start sets therefore differ by contender, so identical schedule IDs can name different updates and queries. Use one common latent core—most naturally 3848—for every contender, generate the schedule once, and add policy-specific insertions plus neutral filler to reach 4096. Only then are paired comparisons and shared bins valid.

## Alignment verdict

No. V4 improves schedule fitting, adequacy intent, boundary handling, metric registration, and pilot auditability, but executing it unchanged still cannot answer Brian’s question: V1 is impossible because the deliberately weak B3 must pass adequacy, and the supposedly paired contenders receive different latent schedules. The V2 parity quantifier can also bury the decisive result where B3k ties OSC. Fixing those issues would leave a credible toy benchmark of dynamic instruction tracking under local-attention loss, still not an evaluation of real summary compaction.

## Unverified surfaces

Task D remains unimplemented. No evidence yet verifies a common latent schedule, exact 4096-token construction, four-token query/PAD placement, bounded rejection termination, curriculum-wide static tensor shapes, corrected stale-null arithmetic, deterministic M1/M1b selection, sealed final evaluation, or the projected fleet cost.