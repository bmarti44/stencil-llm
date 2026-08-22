# Review topic: a proposed amendment to PLAN.md

The orchestrator proposes an amendment to governed content (hypotheses, thresholds, architecture, protocol). Under the Autonomy policy (PLAN.md Section 2b), it takes effect only if this review accepts it with zero open high/critical findings.

Read PLAN.md in full, the amendment's diff (git log / git diff, or the draft text the wrapper context names), and the ledger entry motivating it. Adversarially evaluate:

- Legitimacy: does it comply with operating rule 3 (no threshold edits after the affected phase's first run launched)? Check the ledger for the phase's launch entry.
- Motivation: is it fixing a genuine defect or diagnosed ambiguity, or rescuing a failing result? Amendments that weaken a bar, widen a band, or relax a test after data exists are presumptively dishonest — flag as critical unless the evidence clearly predates the data.
- Consistency: does the amended text contradict any other part of PLAN.md, README.md, or the tooling?
- Completeness: does it update every dependent passage (Appendix C, phase specs, README component map) in the same change?

Score the amendment, not the whole plan. Findings use the standard severity scale.
