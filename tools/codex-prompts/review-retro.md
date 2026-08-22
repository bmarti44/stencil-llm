# Review topic: a phase retrospective (honesty audit)

Read the retrospective named by the wrapper context (plan/retros/<phase>.md), the phase's review files under plan/reviews/, results/agent_metrics.json, the plan/LEDGER.md entries for the phase, and AGENTS.md.

One rubric question governs: does the retro assign blame where the evidence points? Specifically:

1. Does it blame process or tooling for failures the evidence attributes to agent mistakes (or vice versa)?
2. Does every claimed "went well" trace to a metric or artifact, and every "went poorly" to a concrete finding, rerun, or budget overrun?
3. Did every optimization land as a diff (AGENTS.md entry, tools/ change, or ledgered deferral with reason), or is any of it advice with no mechanism?
4. Are the computed metrics (first-round score, rounds-to-acceptance, findings-per-round) quoted accurately from agent_metrics.json, and are escaped defects and lesson recurrences counted honestly?
5. Is anything material missing that the review history shows happened?

Threshold for retros is 75. Findings use the standard severity scale.
