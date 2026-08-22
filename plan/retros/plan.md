# Retrospective — plan phase (acceptance loop), 2026-08-22

Scope: from PLAN.md v1.0 through acceptance (v1.23, Human Adjudication 3). 27 commits, 76 sol review rounds across 4 topics plus 21 kimi rounds, 5 tie-break batches, 3 human adjudications. Metrics from `tools/agent_metrics.py` (results/agent_metrics.json).

## What went well — with evidence

1. **The adversarial loop fixed the science.** Science 38→92 (7 rounds), spec 32→92 (10). Round 1 alone caught four experiment-killing defects: the mathematically impossible chance rate (cue-blind Bayes is 1/k, not 1/16), G2 energy tests no integrator could pass, the answer-token leak (no causal shift registered), and the eval-seed bug (held-out stream silently resampled the rule tables). Any one of these would have wasted the entire Phase 3 GPU budget or produced fake results. This is the loop's rent, paid in full.
2. **Cross-model review delivered real independence.** Kimi found the B2 competence-floor hole sol missed; sided with sol against the orchestrator in batch 5; convergent scores (sol 72/68/70 vs kimi 72/66/69 in the same round) validated finding quality.
3. **Session continuity worked as designed.** Post-resume rounds re-verified their own lists instead of re-litigating; science's find-list narrowed monotonically to acceptance.
4. **The protocol policed its operators — including the orchestrator.** Reviewers caught the orchestrator: violating a human ruling twice (v1.18/v1.19 sequencing), submitting a strawman tie-break record (batch 4, vacated), five ledger-discipline slips, and one self-defeating test (`tr` validating a producer whose consumer used `read -d ''`). Every failure class ended confessed-then-mechanically-prevented (amend.sh, commit_narrow.sh, verbatim tie-break verification).

## What went poorly — with evidence

1. **The amendment-review spiral (the centerpiece).** 26 rounds on one topic; roughly the final 13 hardened a coder wrapper that had never run a coder, against a malicious-insider threat model two adjudications had already ruled unattainable. Root cause: **acceptance was reviewer-shaped, not purpose-shaped.** "90 + zero open high/critical" hands the reviewer the frontier; bounded, falsifiable content exhausts its frontier (science, spec converged), unbounded content (same-uid security) cannot. Amplifiers: session continuity drilled the invested thread deeper; each finding was individually correct and cheap-looking, so "fix" always locally beat "stop"; the orchestrator — holding the burden test that would have terminated it — chose one-more-fix ~10 consecutive times and flagged the absurdity twice without acting. Terminated only by human intervention.
2. **Governance outgrew its subject.** ~20 amendments, 3 governance tools, and 5 tie-break batches before one line of project code. Some was rent (the science fixes); a measurable fraction was meta-tooling hardening whose defect classes exist only because the tooling exists.
3. **Orchestrator error rate under batch pressure.** Every fix batch for ~6 rounds shipped at least one real defect (exponent double-count, `set -u` ordering, self-matching pkill, heredoc marker misses). Cost: multiple wasted review rounds.
4. **Escaped defects / lesson recurrence:** 2 recurrences of the forgot-the-log class before mechanization; 1 recurrence of relative-path-in-background after the AGENTS.md lesson existed. Lessons only stick when they become tooling.

## Optimizations — every one landed as a diff

| lesson | mechanism (landed) |
|---|---|
| Reviews need a purpose and threat model, or they cannot terminate | PROTOCOL v1.23: purpose-scoped rubrics; registered threat model |
| Unbounded topics need a stop-loss independent of the reviewer | PROTOCOL v1.23: tooling = 1 round + fix pass; any review at 3+ rounds with zero H/C → orchestrator decides, score advisory |
| Discipline rules recur until mechanized | amend.sh, commit_narrow.sh, trap-based provenance, verbatim tie-break verification (all in tools/) |
| Arbiter records must be verbatim, never summarized | run_tiebreak.py quote verification; PROTOCOL rule (post-batch-4) |
| Test the consumer's semantics, not the producer's output | AGENTS.md entry (this commit) |
| The orchestrator is the terminator; flagging without acting is not acting | AGENTS.md entry (this commit); the stop-loss makes it mechanical anyway |

## Verdict against the north star

The loop made the experiment plan dramatically more likely to produce a true result, then overshot into self-referential hardening at roughly 2x the effort the science fixes cost. The v1.23 stop-loss is expected to keep future phase reviews at 1–3 rounds. Phase 0 is the test: its review has a bounded subject (real code against a registered spec), which is the regime where this system demonstrably converges.
