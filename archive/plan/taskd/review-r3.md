SCORE: 67

## Findings

1. **critical — Register-shaped benchmark (resolved).** B3k supplies the requested exact four-slot keyed register within the same 128-dimensional state budget. This makes substrate attribution honest for this task: tying or losing to B3k correctly means oscillation added no benefit over the simpler sufficient statistic. Broader external validity remains under finding 10.

2. **critical — Gold-answer leakage (resolved).** Separate targets, PAD placeholders, and explicit no-answer-in-input tests remain sufficient.

3. **critical — Reinsertion incumbent fairness (resolved).** Both periodic and pre-query reinsertion are now verdict-bearing incumbents, periodic refresh is within the receptive field, token overhead is recorded, and comparisons use a shared true-update axis.

4. **critical — Adequacy handling (partially resolved; reopened).** Initial results and retries remain properly separated, but only OSC adoption failure forbids V1. V1 could therefore be manufactured by an undertrained B3k, B4, B2, or reinsertion run. Every verdict-bearing rival must satisfy a predeclared adequacy requirement, or any rival adoption failure must force MIXED rather than count as evidence for OSC.

5. **high — Decision procedure remains non-disjoint and incompletely cost-aware (open).** V1 and V2 overlap at the one-point boundaries. For example, V1 permits a rival to beat OSC by exactly one point “everywhere else,” while V2 triggers when a rival beats OSC by at least one point anywhere in the tail. Likewise, OSC beating a rival by exactly one point in one family while tying elsewhere satisfies both V1 and V2’s all-within-one tie condition. Checking V1 first makes the output deterministic but can select BENEFIT where V2’s negative condition also holds. Use non-overlapping strict boundaries. Also freeze whether comparisons use seed means, every paired seed, or pooled sequences; “all seeds” is not an aggregation rule. Finally, zero injected tokens is not zero cost—the oscillator pays controller compute and memory—so either incorporate measured runtime/memory into the Pareto rule or explicitly limit “benefit” to token overhead.

6. **high — Oscillator-family adjudication (resolved).** Validation-sealed selection between M1 and M1b allows either oscillator variant to become the single final-test subject without final-holdout selection. Add a deterministic validation aggregation and tie-break under finding 5, but the original M1-only defect is closed.

7. **high — Frozen schedule is internally inconsistent (open).** Scaling cumulative gaps to a fixed interval destroys the registered gap distributions: 12 train gaps span 768–6144 tokens and three drought gaps span 3072–6144, while the usable interval is about 4024. Rescaling therefore moves gaps outside their stated uniform bounds. The generic gap algorithm also does not fully specify burst’s 3/3/2 cluster construction. Additional contradictions remain:

   - Initial rules have no registered draw order.
   - The no-op note compares a target-slot draw to the slot’s current rule; it belongs to the subsequent rule draw.
   - Sampling query start positions without replacement does not prevent multi-token query blocks from overlapping one another.
   - Inserting roughly 256 periodic or 128 pre-query tokens cannot generally be undone by trimming only the 64-token trailing reserve, especially when queries may occur near the end.
   - Insertions shift true updates and queries in actual token coordinates, so their measured distances are not reinsertion-invariant without a separately defined base-timeline axis.

   Construct schedules directly within fixed legal regions—without rescaling—and define exact block placement, insertion displacement, and base-versus-model token coordinates.

8. **high — Metrics are substantially improved but still incomplete (partially resolved; open).** Canonical bins, shared-support NA handling, counts, global-update semantics, and first-crossing survival close most of the original defect. Two load-bearing pieces remain: define whether decision-axis distance is measured on the latent base timeline or each contender’s actual post-insertion tokens, and register the stale-error null formula in this plan rather than deferring it to a later brief. First-crossing behavior when an intermediate bin is NA also needs an explicit rule.

9. **high — Ragged decision shapes (resolved).** Fixed sequence and query counts remain compatible with static batching, subject to correcting schedule placement under finding 7.

10. **medium — Compaction realism (partially resolved; open).** The local-attention-only scope is honest and consistently repeated. The benchmark still cannot answer Brian’s summary-compaction setting directly, so the final headline must say “toy local-attention persistence under dynamic slot updates,” not general long-horizon or real-world compaction benefit.

11. **medium — Pilot budgeting (partially resolved; reopened).** The implementation calls for four pilot cost classes—M1, B3k, B4, and reinsert-128—but Verification says three. Make the count and acceptance requirement consistent, and retain comparison hashes before discarding scratch reruns.

12. **high — B3/B4 token-role collision (resolved).** Distinct query markers 60–63 prevent queries from touching cue-triggered latch and retention paths, and the role-separation test binds the intended behavior. Implementation must also remove 60–63 from Task D’s distractor sampler because they currently belong to that range.

13. **critical — Empty reinsertion tail comparison (resolved).** Cross-contender decisions now use distance since the last true update, while reinsertion-aware information age is descriptive. This restores common tail support, subject to fixing base-versus-post-insertion coordinates under findings 7–8.

## Alignment verdict

Not yet, but v3 is materially closer. It now has the right attribution-bearing keyed register, both oscillator variants, strong reinsertion incumbents, answer-leakage protection, and a shared holdout comparison axis. Executing it unchanged would still not yield a trustworthy verdict because the schedule laws cannot be implemented as written, rival undertraining can create V1, and V1/V2 overlap at their registered boundaries. Fixing those issues would make it capable of answering a carefully scoped toy-scale version of Brian’s question; actual summary compaction would remain outside the evidence.

## Unverified surfaces

Task D, B3k, separate-target training, role masks, schedule construction, reinsertion placement, fleet sealing, metric formulas, and the report consumer remain unimplemented. No fixture or pilot yet verifies that 60–63 are excluded from distractors, all event blocks fit exactly within 4096 tokens, paired schedule IDs survive insertion, final evaluation runs once, or the projected 2–3-day fleet cost is realistic.