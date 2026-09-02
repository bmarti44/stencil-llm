# Research synthesis — how to make the wave mechanism improve benchmark scores (2026-09-02)

Sources (all web-verified runs): results/research-fable.md (24 sources opened), results/research-sol-web.md
(40+ primary sources), results/research-kimi-web.md (61 tool calls, 25 sources). Knowledge-only baselines
(research-sol.md, research-kimi.md) were used only to check for contradictions. Orchestrator cross-check:
the seven arXiv ids that two or more reviewers rely on all resolve to the claimed papers
(2311.02262 PASTA; 2505.12025 SpotLight; 2603.06745 DIRECTER; 2503.23306 Focus Directions;
2510.00231 Pitfalls of KV Cache Compression; 2605.18053 Protection Is (Nearly) All You Need;
2505.15347 FlowKV).

## What the literature says about what we built (three-way consensus)
1. **Our deficit-gated wave is SpotLight's idea in a stronger, riskier form.** SpotLight adds log(tau/psi)
   (lands below target); ours applies the exact logit correction (lands on target) and repeats it across
   layers 20–27 on all heads. SpotLight's and PASTA's own figures show all-head / single-layer steering
   frequently below baseline. (fable, sol; kimi agrees on mechanism.)
2. **Single-turn IFEval gains at 1–3B are sub-point to a few points even for the best method.** DIRECTER
   moves Llama-3.2-1B 61.3→61.6 and Qwen2.5-3B 63.9→67.1; SpotLight at its official psi=0.3 loses 13.8 pts.
   Our +0.39 is in band; a +2.0 single-turn floor at 1.7B was never supported. (fable, sol.)
3. **The effect lives in multi-turn / aged constraints.** SpotLight halves the cross-turn drop on MT-IFEval
   (18.2%→9.3%); Qwen3-1.7B official Multi-IF is 44.7 (non-thinking). (fable; kimi's Multi-IF numbers agree.)
4. **Availability beats amplification.** Pitfalls (ACL 2026) shows eviction is instruction-biased and fair
   per-instruction eviction restores adherence; Protection reports 10% boundary protection recovers 69–90% of
   ceiling; FlowKV/MemDecay recover large multi-turn losses by preserving state. Our 62% recovery from plain
   pinning is in band. (all three.)
5. **Why ours degenerates:** rigid state-dependent mass floor on incomparable heads, re-applied through eight
   layers, inflates attention to low-information span tokens (natural repetition attends there) and
   self-reinforces autoregressively (InstABoost Thm 3.3; "Repetitions are not all alike"; DITTO). (sol, fable,
   kimi.)
6. **Repetition penalty is a confound**, not a fix: it changes the base arm and interacts with IFEval
   keyword/frequency verifiers. Legitimate: intervention gating, fluency-constrained hyperparameter
   selection, truncation scored as failure (already registered in ROUND 7). (all three.)

## Ranked redesigns (merged; each reviewer's rank in brackets)
R1. **Trust-region (plausibility-gated) wave on pinned KV** [fable 1, sol 1, kimi implicit in R1(v)].
    Keep ledger selection + KV pinning. Replace the exact mass floor with a candidate perturbation
    (fractional odds, hard delta-psi cap, preselected layer/head group), compare steered vs raw next-token
    distributions (JS divergence, candidate top-1 raw prob >= 0.5 x raw top-1, entropy delta, rank change);
    outside the region halve the dose / drop the most sensitive layer pair (nested backoff over 20–21,
    22–23, 24–25, 26–27); emit raw if nothing is safe. Base arm untouched (not a decoder confound).
    Literature anchor: DIRECTER Llama-3.1-8B IFEval 73.5→78.8 and rescue of PASTA/SpotLight from below
    baseline. Gate: Multi-IF late turns, clustered LB(neural−pin-only) > 0, truncation excess <= +2,
    press-survival rate >= 5% (else the mechanism is operationally baseline).
R2. **Head-selective wave across all layers, bounded dose** [fable 2, sol 3, kimi 1].
    Causal scan on a dev slice for K≈8–16 "contextual" heads (Focus Directions: top-20 heads at tau=0.1
    EM 0.59→0.916; 600 or random heads fall below baseline); mid/all layers, not 20–27 only; alpha on a
    log grid 0.005–0.05 in logit units; relative reweighting with a per-head cap at the 95th percentile of
    the head's natural span mass. Cheap pre-check (~1 GPU-h): do such heads exist in Qwen3-1.7B? If not,
    R2 is dead before spending.
R3. **Retention-only mechanism as the null control and product** [fable 3, sol 2, kimi 2].
    Ledger keeps only its selection job; delivery = guaranteed KV residency of active constraints, stale
    ones evicted, plus (ablation arm) a fixed-template one-line constraint echo per user turn. Cannot
    degenerate. Gate: recover >= 85% of the eviction gap (now 62%) with zero added truncation; then
    Multi-IF turn-3 vs pin-only. This is the decision variable: if R3 already closes the gap, positive
    dose has nothing left to explain.
R4 (kimi only, lowest priority). A single 1-D adherence steering vector, deficit-gated (ITI-style).
    Highest variance; only after R3 disambiguates selection-failure vs compliance-failure.

## Falsification of "waves select" for this trunk (sol's operational form, endorsed by all)
Treat the actionable claim — extra causal contribution of the correct active instruction representation,
within a predeclared output-divergence budget, improves late-turn verifiable constraint satisfaction by
>= 2 pts without > 1 pt more truncation/looping — as falsified if ALL hold: (1) oracle-span head-selective
wave UCB < +2; (2) trust-region wave finds no safe nonzero dose or shifts attention without score gain;
(3) mediation fails (span mass rises, satisfaction does not; shuffled spans do as well); (4) pinning alone
recovers what any positive dose adds. The surviving result is then semantic memory routing (retention),
not attention amplification.

## What to run first (merged order)
0. Truncation hygiene on the Multi-IF base (ROUND 7 gate; consider max_new ↑ symmetric across arms) —
   a 10% truncated floor contaminates every downstream estimate. [kimi 5, fable F1]
1. **R3 retention arms** (pin-only vs pin+echo vs base) on the aged-constraint eviction suite, then
   Multi-IF late turns. ~half a week, no training. Decision variable for everything else.
2. **R2 head pre-check** (~1 GPU-h): causal head scan on a dev slice; output top-K list + natural-mass caps.
3. **R1 gate battery** (CPU/teacher-forced first: raw vs exact vs fractional lambda in {.1,.25,.5},
   delta-psi caps {.01,.02}, four layer pairs, held-out head groups; bitwise-base at beta=1), then a
   128-conversation non-confirmatory pilot with the stop rules above; freeze one config.
4. **One sealed Multi-IF confirmation** (909, ROUND 7 validity, Holm across arms): pin-only/Wave-Memory vs
   equal-budget base; Wave-TR vs matched no-positive-dose control. Publish every press/rejection counter.
   If neither crosses its gate, stop the amplification line for this trunk.
Budget: ~30 GPU-h for step 4 (the E2 futility stop freed it), ~3 GPU-days for the R2 scan.

## Disagreements and how they were resolved
- Order of R1 vs R3: fable/sol lead with the trust-region wave, kimi with retention. Resolved toward
  kimi's order because R3 is cheapest, cannot degenerate, and its outcome is a precondition for
  interpreting R1 (availability vs amplification).
- Layer placement: fable/sol keep late layers with backoff; kimi moves to mid layers. Resolved: R2's
  causal scan decides empirically; R1 backoff includes dropping the late pairs.
- Kimi flags PASTA's exact dose/head config and +22% headline as UNVERIFIED; do not cite them in a
  preregistration until checked against the paper body.
