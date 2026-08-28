SCORE: 77

## Findings

1. **critical — Register-shaped benchmark (resolved).** B3k remains the correct exact, state-budget-matched comparator.

2. **critical — Gold-answer leakage (resolved).** Four-token query blocks and separate targets preserve the fix.

3. **critical — Reinsertion incumbent fairness (resolved).** Both reinsertion policies remain verdict-bearing on the shared core.

4. **critical — Adequacy handling (resolved).** B3 is now descriptive and exempt. All genuinely competitive rivals must be adequate, and their failures cannot manufacture V1.

5. **high — Verdict reliability (partially resolved; open).** The existential B3k/B4/B2 parity clause, strict margin boundaries, aggregation rule, and token-only cost scope now make V1–V3 logically coherent. However, the Round 4 summary claims a 40% min-seed tail floor that does not appear in the operative decision procedure. V1 still uses only the three-seed mean and can hide catastrophic held-out failure in one seed. Add the promised requirement explicitly—for example, every OSC seed must achieve at least 40% tail accuracy on both held-out families—alongside the mean ≥50% rule.

6. **high — Primary oscillator selection (resolved).** Exact validation ties deterministically select M1.

7. **high — Schedule construction (partially resolved; open).** The common 3848-token core, complete query blocks, bounded rejection, and direct gap sampling repair the major construction defects. Periodic expansion remains contradictory: there are 31 final-coordinate multiples of 128 from 128 through 3968, but the policy inserts only 30 blocks while claiming insertion before every crossed multiple. Following the stated algorithm produces 31 blocks and needs no trailing filler; following the stated count leaves the final interval unrefreshed and is not literally reinsert-128. Freeze one convention and test exact insertion positions.

8. **high — Stale-error metric (resolved).** Error-conditioned observation and null now use the same wrong-answer population, with explicit NA behavior.

9. **high — Fixed training shapes (partially resolved; open).** The frozen schedule says training always uses 12 updates and varies only gap bounds, but the later Training section still says 24 updates through step 8k. The latter would change CUDA-graph shapes and directly contradict the registered fix. Remove it or harmonize it to 12. Also, “16 update events” corresponds to 32 cue-range token positions because each `[USLOT][CUE]` pair contributes two retained tokens; specify the fixed `cue_positions` width—or a new structured event representation—plus policy-specific reinsertion padding so the existing B4/CUDA consumers are unambiguous.

10. **medium — Compaction realism (partially resolved; open).** The benchmark remains honestly limited to dynamic instruction tracking under local-attention loss, not actual summary compaction. Preserve that scope in the headline verdict.

11. **medium — Pilot budgeting (resolved).** Four pilots and retained hashes remain consistent.

12. **high — Token-role separation (resolved).** Update and query roles remain distinct; implementation must exclude 60–63 from Task D distractors.

13. **critical — Shared tail support (resolved).** Every contender now receives one identical latent core, so schedule IDs, true-update distances, and paired bins are genuinely shared.

## Alignment verdict

Almost, but not yet implementation-ready. V5 now provides a credible, paired, leakage-resistant benchmark with strong reinsertion and exact-register competitors. The remaining high-severity issues are concrete specification contradictions: missing seed robustness, inconsistent periodic-refresh arithmetic, and conflicting curriculum/update-count shapes. Once corrected, executing the plan would answer a well-scoped toy version of Brian’s question: whether an oscillator provides accuracy or reinsertion-token benefit for dynamic long-horizon instruction tracking under local-attention loss. It would not establish benefit under real summary compaction.

## Unverified surfaces

Task D remains unimplemented. Exact refresh positions, fixed cue tensor widths, curriculum-wide CUDA shapes, min-seed verdict enforcement, reserved-token sampling, shared-core identity, sealed final evaluation, metric arithmetic, and the 2–3-day runtime projection still require implementation tests and pilot evidence.