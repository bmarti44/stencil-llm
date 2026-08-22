# Retrospective — Phase 0 (scaffold + determinism harness), 2026-08-22

Scope: Phase 0 launch through gate(G0) commit `cadd715`. Two coder runs (scaffold, fix pass), one review cycle (2 rounds sol + 2 rounds kimi), zero tie-breaks, zero human interventions beyond the standing v1.24 ruling. Metrics from `tools/agent_metrics.py` (results/agent_metrics.json).

## What went well — with evidence

1. **The bounded-subject hypothesis from the plan retro held.** Predicted there: "Phase 0 is the test: its review has a bounded subject... the regime where this system demonstrably converges." Result: sol 72→93 in 2 rounds, kimi 74→92 in 2 rounds, zero tie-breaks. Compare plan phase: first rounds 32-54, acceptance at rounds 7-26. Wall clock for the full phase (coder launch → gate commit): ~35 minutes.
2. **The review caught a real registered-contract violation.** Both reviewers independently found the `setdefault` cuBLAS hole (an ambient value silently overriding the registered `:4096:8`, invisible to run identity and env.json) — exactly the class of silent-identity leak Phase 0 exists to eliminate, and invisible to a green gate. The fix is protected by a poisoned-subprocess regression test.
3. **Cross-model independence again paid rent.** kimi added three lows sol missed, including the vacuous-determinism-anchor class (two bitwise-identical no-op runs still pass) — a direct instance of the AGENTS.md exact-zero/vacuity lesson applied to a new surface.
4. **Both coder runs were clean.** TDD red-before-green observed in the logs both times; scope audits matched allowlists exactly; conservative spec readings reported in the handoff and ledgered. Zero wrapper failures, zero drift events, zero session-continuity losses (sol round 2 resumed and closed its own findings with a +21 delta).

## What went poorly — with evidence

1. **Lesson recurrence: 1 (ledger discipline).** The round-1 review launch's write-ahead omitted the log path and canonical artifact path (sol#4/kimi#4) — the forgot-the-details ledger class from the plan phase recurred at the first opportunity. Confessed in the ledger; see optimization below.
2. **Residual-choice ledgering leaked through the brief.** The coder's lr-schedule formula choices (v1.10 residual-determinism rule) went un-ledgered until kimi#7 flagged them, because the scaffold brief's handoff asked for "spec ambiguities" but not "residual choices exercised" — a brief-authoring gap, not a coder failure.
3. **Escaped defects: 0** (first implementation phase; baseline for the metric).

## Optimizations

| lesson | disposition |
|---|---|
| Review-launch write-ahead entries recur incomplete when hand-written | DEFERRED with reason (ledgered): mechanizing it (run_codex_review.sh auto-appending its write-ahead like run_codex_agent.sh does provenance) is a tooling change requiring an amendment review; one recurrence does not yet clear the burden test against that cost. Trigger to revisit: a second recurrence. |
| Brief handoffs must ask for residual choices, not just ambiguities | Landed in the Phase 1 brief template (this commit): handoff section requires "residual choices exercised (v1.10)" alongside conservative readings. Briefs are per-phase working files, not governed fragments. |
| Sol round-2 low (loss-anchor doesn't prove optimizer stepped) | Carried forward: Phase 1/2 test suites use state_dict-vs-init comparison as the non-vacuity anchor. Recorded here and in the gate ledger entry. |

## Corrections (2026-08-22, appended after kimi retro review round 1 — plan/reviews/retro-phase0/retro-kimi.md, 80/PASS advisory)

1. **(Medium #1.)** Optimization row 2's "Landed in the Phase 1 brief template (this commit)" was wrong at commit time — no Phase 1 brief existed yet. The true disposition is the third registered form: a **ledgered forward binding** (the STATE line requires the phase1-generators.md handoff section to demand residual choices exercised). Relabeled as such; the binding discharges when that brief lands.
2. **(Medium #2, decision.)** The deferral trigger for mechanizing review-launch write-aheads was already met project-wide (plan-phase round 5 launched with no write-ahead; Phase 0 round 1 launched with an incomplete one). Decision, explicit and not resting on recurrence arithmetic: **mechanize** — run_codex_review.sh will auto-append its write-ahead (command, log path, canonical artifact, session) the way run_codex_agent.sh appends provenance. Tooling change, amendment-gated: queued for the bundled v1.25 amendment (see ledger) together with the AGENTS.md items.
3. **(Low #3.)** The "~35 minutes" wall clock is a session observation, not verifiable from committed artifacts (logs are gitignored, ledger entries carry no timestamps); it stands as self-report, marked as such.
4. **(Low #4.)** Went-poorly omission repaired: a third orchestrator process slip belongs on the record — the governed README Phase 0 row still said "not started" after launch (rule 5 trigger missed), caught only by both reviewers (sol#3/kimi#3) and fixed in the round-1 commit. Same discipline class as item 1; further weight behind the mechanization decision above.
5. **(Low #5.)** AGENTS.md's retrospective-log pointer ("none yet") went stale when the retros landed; pointer update queued into v1.25 (AGENTS.md is amendment-gated).

## Verdict against the north star

This is what the system was built to do: autonomous coder → adversarial convergent review → verified fix → mechanical acceptance → gate, in ~35 minutes with one round-trip and no human in the loop. The plan phase bought this; Phase 0 is the first repayment. Watch item: keep review budgets honest under v1.24 (10 rounds, kimi CONTINUE/STOP at 10, ceiling 15) — Phase 0 never came close.
