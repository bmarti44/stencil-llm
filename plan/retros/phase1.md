# Retrospective — Phase 1 (data generators), 2026-08-22

Scope: Phase 1 launch through gate(G1) commit `465986c`. Two coder runs, one review cycle (2 rounds sol + 2 rounds kimi), zero tie-breaks, zero human interventions. Metrics from `tools/agent_metrics.py`.

## What went well — with evidence

1. **Three independent implementations agreed byte-for-byte.** The TDD-conform fixture protocol did exactly what it was registered to do: the orchestrator hand-executed Task A/M fixtures from spec text before any generator existed; the coder's data.py reproduced them exactly on first landing; the sol reviewer then reconstructed all eight sequences independently and matched. The round-1 kimi finding (Task B unpinned) extended the same protocol mid-phase: the orchestrator derived a Task B fixture from the ledgered schedule *without reading data.py*, and the generator matched it too, cue-redraw semantics included. Fabricating agreeing outputs across three blind implementations is the strongest honesty evidence this protocol can produce.
2. **Convergence again fast and identical:** sol 84→95 (r2), kimi 84→92 (r2), zero high/criticals at any point. Same scores in round 1 from both reviewers, independently.
3. **The G1 binding condition (spec#9 tie-break) was discharged honestly by both reviewers within their capabilities** — sol by full draw-level reconstruction, kimi by construction-text equality plus artifact-internal numeric checks, with its no-tool limit disclosed rather than papered over.
4. **Test-honesty findings were the round's substance** (production-path bypass, unbound gate artifact, vacuous-capable guards) — the reviewers are auditing what a green gate *means*, not just whether it is green. That is the review culture the plan needs at Phase 3.

## What went poorly — with evidence

1. **Lesson recurrence: 1.** The README status row missed its "in progress" flip for the second phase running (sol#1/kimi#1), after the phase0 retro explicitly documented the first miss. Flagging without mechanizing did not work; mechanization is now v1.25 item (d) (acceptance-time check).
2. **Escaped defect: 1** (first entry for this metric). kimi#7: the Appendix A loader-validation matrix was implemented in Phase 0 but never tested; Phase 0's review missed it, and Phase 1 made those rules load-bearing. Root cause accepted in an earlier phase, caught one phase late. The 16-case suite now guards it.
3. **The lens decision was silently skipped** (sol#4/kimi#4): PROTOCOL requires each review launch to name its adaptive lens and rationale; the launch entry recorded everything else but that. Confessed and recorded mid-phase; the write-ahead template in the v1.25 auto-write-ahead includes a lens field, which mechanizes the reminder at the same stroke.

## Optimizations

| lesson | disposition |
|---|---|
| README-row flips recur un-flipped when manual | v1.25 item (d): check_acceptance fails if the phase row still says "not started" (landed via the amendment path, not this commit) |
| Review-launch write-aheads recur incomplete | v1.25 item (a) auto-write-ahead, now with a lens field (decision made in phase0 retro correction 2; scope extended here) |
| Fixture-pinning pays for itself; unpinned residual schedules are latent identity risks | Standing practice, no diff needed: every task/schedule that later phases depend on gets an orchestrator-authored fixture before or immediately after implementation (Task B's landed mid-phase this way); Phase 2's brief lists its fixture surface explicitly |
| Loader-style "correct but unguarded" code escapes phase reviews | Phase 2 brief instruction (forward binding, discharges when it lands): every validation/assertion surface the phase introduces must name its negative-case tests in the handoff |

## Verdict against the north star

Two implementation phases, two gates, both closed in exactly two review rounds with zero high/criticals and zero human interventions — the v1.24 budget (10) has never been approached. The generator layer the entire experiment feeds on is now pinned by three-way independent agreement and gate-bound artifacts. Remaining debt is process hygiene (v1.25 bundle), not science.
