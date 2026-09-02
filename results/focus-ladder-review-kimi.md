# Focus-ladder review — kimi-k3 (2026-09-02)

# Focus Ladder Review — kimi-k3 (cross-model, no shell)

Reviewed the ladder against the synthesis text provided (I cannot open the repo; findings that depend on code state are marked *must-verify*). Severity grades: **low / medium / high / critical**.

---

## (1) The echo arm — confounded as billed

**F1 [high] pinned_echo manipulates recency + repetition, not availability.** Appending the constraint to the current user turn un-ages it. The suite's entire value is the 56 *aged* constraints; pinned_echo converts them into fresh constraints with stale KV also resident. So a pinned_echo > pinned result cannot support H1's stated conclusion ("focus = selection + availability") — it supports "reminders work." The echo_only arm (good design, do not cut it) bounds this: pinned_echo − echo_only isolates what pinning adds on top of re-injection. But the rung title and the H3 baseline both need re-labelling, or the program gates its mechanism against a prompt-engineering intervention and calls it a memory mechanism.

**F2 [high] Verifier contamination via the quoting channel.** The echo enters the *prompt*, so response-side rule verifiers don't see it directly — but a freshly reminded model restates/paraphrases the constraint, and IFEval-style keyword/frequency checks count substrings in the response. Restating "the word X should appear…" adds occurrences of X. This is the same confound family the synthesis flags for repetition penalty (point 6), imported into H1's baseline arm. Fix: report a quoting-excluded secondary metric (drop responses reproducing ≥k consecutive echoed tokens) and per-arm quoting rates.

**F3 [high, must-verify] Target-blindness is conditional.** The frozen template ("Active constraints: …") is generic and safe — low risk in itself. But the blind claim holds only if the ledger's *active set at turn t* is computable from conversation state alone, without the benchmark answer key. If "active" is defined using which constraints are scored later, the leak is not new — echo *and pinning* both already inherit it. Require a prereg assertion + unit test: active-set computation must not import the checker. This blocks the "target-blind" claim, not the runs.

**F4 [medium] Role placement.** Injecting harness text into the *user* turn changes task semantics (the user never reminded). Decide and preregister: system/harness-role echo (product-honest) or user-role echo explicitly evaluated as a prompt-engineering product feature. Also: ledger_eval.py already has a text_ledger echo arm — unify template and scorer path, or H1 silently forks a second echo implementation.

**F5 [medium] Missing specificity control.** Add one cheap arm: wrong-content echo (a stale/irrelevant constraint from the same conversation, length-matched). If that also lifts pass rate, the gain is template/recency, not content. This mirrors the synthesis's own "shuffled spans" falsifier.

---

## (2) delta-psi 0.02 on one head — the H2 gate is statistically vacuous

**F6 [critical] The gate passes under a global null.** 28 layers × 16 heads ≈ **448 paired tests**, each "95% bootstrap CI excludes 0," no multiplicity control. Under no real effects, expected false positives = 448 × 0.05 ≈ **22**, sd ≈ 4.6. The gate needs ≥ 8. P(pass | null) ≈ 0.999. H2 as written will "discover contextual heads" whether or not any exist — it is not a gate. Fix: keep the scan for *ranking*, but gate on (a) the **joint top-16 effect** (one extra measurement: all 16 boosted together, paired test) and (b) a **shuffled-span null arm** (+0.02 to random length-matched token sets; pass iff observed top-16 joint/median effect exceeds the null's 95th percentile). Bonferroni over 448 at n=56 is hopeless (MDE ≈ 0.63σ); FDR-BH is weak at this n; rank-vs-null is the right design.

**F7 [high] n for power.** Paired design (per constraint, steered − base per-token logprob delta), n = 56: MDE ≈ (1.96 + 0.84)/√56 ≈ **0.37σ**. So n=56 detects only moderate-to-large per-item effects. For 0.2σ you need n≈200 items; for 0.1σ, n≈785. Consequences: the per-head significance gate is unfixable at n=56 (another reason for F6's redesign); the *joint* top-16 test and the null calibration are adequately powered by the same n. If per-head claims are ever wanted, expand the probe suite (~150+ constraints), not the bootstrap.

**F8 [medium] Dose-unit ambiguity.** "delta-psi 0.02" — mass or logit units? (Synthesis R2 grids alpha in *logit* units; H3 caps delta-psi in *mass* units.) If fixed logit bias, achieved mass shift varies per item — report achieved Δψ. If mass-target (solved bias, as the wave does), say so. Either way, a fixed +0.02 is a 20× boost for a head with natural span mass 0.001 and a 6% nudge for one at 0.3 — the scan conflates "heads where 0.02 is large" with "contextual heads," and contradicts R2's own 95th-pct natural-mass cap. Rank on effect per unit achieved mass, or dose per-head-capped.

**F9 [medium] 1 GPU-h is conditional.** Feasible only with unsteered prefill + KV reuse + steered scoring at answer positions: 56 items × (1 + 448) ≈ 25k short forwards ≈ <20 min. Deployment-faithful steering (bias through prefill) is ~2–4 h. Compromise: read-time scan as the screen, then prefill-time validation of the top-16 only (≈900 full forwards, ~10 min). Preregister which query positions carry the bias.

---

## (3) H3 gates vs DIRECTER-style rejection

**Structurally consistent** — candidate plausibility rule (raw prob of candidate argmax ≥ 0.5 × raw top-1), divergence budget (JS ≤ dev budget), halve-on-reject, emit-raw fallback, press-survival ≥ 5% counter. That is the DIRECTER pattern. Four gaps:

**F10 [high] Adaptive rejection creates a selected sample; H3 has no ITT accounting.** If the gate rejects precisely on hard late turns and accepts on easy ones, "late-turn adherence LB > pinned_echo" measures gate selection, not treatment. Score the steered arm intent-to-treat (emit-raw turns counted), stratify acceptance/survival by turn index, publish all counters (synthesis already demands this; make it a gate artifact, not a footnote).

**F11 [high] No degeneracy criterion in H3.** Degeneration via autoregressive self-reinforcement is *the* documented failure mode of this mechanism (synthesis point 5). A per-step JS trust region does not bound trajectory-level drift; the CPU battery is teacher-forced and cannot see it. H1's rep4 ≥ 0.5 metric must be ported into H3's pilot and battery gates — especially since the H2-failed fallback re-opens the late-layer all-head substrate that degenerated before.

**F12 [medium] Threshold inconsistencies.** Truncation excess: falsifier says >1 pt, R1/H3 gates say +2 — freeze one. Efficacy bar: the program's falsifier requires ≥ +2 pts; H3's pilot gate is any LB > 0 over pinned_echo — declare it two-stage (pilot: direction + safety; sealed 909: ≥ +2 with Holm across arms, per synthesis step 4). Magic constants: 0.5 top-1 ratio and "dev-calibrated" JS budget — freeze the calibration protocol (slice, n, quantile) before the pilot; sensitivity-check 0.5 ∈ {0.35, 0.5, 0.65} in the CPU battery only.

**F13 [medium] Missing inert-gate control.** Synthesis step 4 calls for a matched no-positive-dose control (λ=0 through the same press/reject path) to prove the gate machinery itself does nothing. Cheap, teacher-forced; add once.

---

## (4) Cuts to iterate faster

1. **Reuse, don't rerun:** full / evicted / pinned already produced 0.615 on these 20 sessions — assert checkpoint + decode-config hash and reuse; H1 becomes a two-arm run (pinned_echo, echo_only) + one added wrong-content echo.
2. **Unify the echo** with ledger_eval.py's existing text_ledger arm; one template, one scorer.
3. **H2: cut the 448-CI gate** (F6), keep identical forward passes; gate on joint top-16 + shuffled null. Same ~1 h, a gate that can actually fail.
4. **H3: cut the dose grid.** A 3×2×4 = 24-config battery duplicates what halve-on-reject already discovers; enter at one top dose on the H2-decided substrate (head set XOR layer pairs — not both) → 2–4 configs. Cut entropy-delta/rank-change from the accept rule to logged diagnostics; JS + top-1 ratio suffice.
5. **Pilot:** at n=128 clustered by conversation, an LB-vs-baseline efficacy gate for +2 pts is underpowered (SE ≈ 0.25σ; a non-confirmatory pilot cannot carry a hard efficacy gate). Demote pilot to safety/direction (survival, truncation, degeneracy, acceptance-by-turn, point-estimate direction); efficacy belongs to the sealed 909.
6. **Add the missing rung 0:** synthesis step 0 (Multi-IF truncation hygiene, symmetric max_new) is absent from the ladder; a 10% truncated base floor contaminates every downstream comparison, including the H3 confirmations.
7. **Process:** preregister each rung's one-page readout (fixed tables, CIs, counters) so "run and read in a day" survives contact with reviewers.
8. **Do not cut:** echo_only, the null arms, truncation reporting, press/reject counters.

**Precision note (affects H1 and H3 alike, [high]):** with 56 constraints nested in 20 session clusters, the paired SE on arm-difference pass rates is ~5 pts or worse. H1's stop rule ("≤ pinned + 0.05 of gap") and the 0.85-of-gap gate are point-estimate reads sitting inside that noise. Recast every H1/H3 stop and gate as a session-clustered bootstrap CI comparison.

---

## VERDICT

**Approve with mandatory revisions — do not run H2's gate as written.** The ladder's architecture is right and matches the synthesis consensus (retention null first, cheap head pre-check, trust region with real stop rules, falsifier wired), and the per-rung scope is mostly right-sized. But three defects are not cosmetic: H2's headline gate **passes with probability ≈1 under a global null** (critical — it manufactures evidence for contextual heads); H1's echo arm **confounds availability with recency/repetition** and its 56-item stop rules sit below the noise floor; H3 omits the **degeneracy gate and ITT accounting** that DIRECTER-style rejection requires. All fixes are analysis-side or single extra arms — shuffled-span null, wrong-content echo, joint top-16 test, cluster-bootstrapped gates, rep4 in H3, rung-0 truncation hygiene — adding hours, not days. Fix these and the ladder is a sound one-day-per-rung program; run it unfixed and H1's baseline, H2's existence proof, and H3's gains are all illegible.