# CROSS-MODEL REVIEW — kimi-k3, independent second check on sol/Opus

I recomputed everything computable from the text. The arithmetic first, because it is the load-bearing question.

---

## A. The conjunction arithmetic (Q2 — the most important question)

**Setup.** Multi-IF turn *t* is scored on turn *t*'s cumulative instruction list. Strict-prompt = ALL constraints pass; inst-level = per-constraint rate. If constraints were independent with per-constraint rate *p_t* and average count *n_t*, then strict_t ≈ p_t^(n_t).

**Back out the implied constraint counts from the reported numbers:**

| turn | strict | inst | implied n = ln(strict)/ln(inst) |
|---|---|---|---|
| 1 | 0.708 | 0.769 | **1.32** |
| 2 | 0.525 | 0.752 | **2.26** |
| 3 | 0.323 | 0.694 | **3.09** |

These implied counts match Multi-IF's actual structure (turn 1 = an IFEval-derived prompt averaging ~1.3–1.5 instructions; each later turn adds ~1). Now check the forward prediction: 0.769^1.32 = 0.708; 0.752^2.26 = 0.525; 0.694^3.09 = 0.324. **The observed strict-prompt series is exactly what conjunction of the observed inst-level rates predicts.** The program's own (proper, per-conversation) independence computation agrees: prediction 0.686/0.497/0.290 vs observed 0.711/0.513/0.321 — observed sits *slightly above* independence at every turn, i.e., constraints are positively correlated and there is **no excess strict-prompt decay at all**.

**Decomposition of the −38.5pt strict drop:** holding the rate at 0.769 and letting only the count grow predicts 0.708 → 0.552 → 0.444. So ~26pts of the drop is pure count-growth arithmetic; ~12pts comes from the per-constraint rate decline. And the per-constraint decline is itself confounded (below).

**Verdict on the interpretation:** "Focus-retention failure, huge headroom" at the strict-prompt level is **not warranted — it is arithmetic**. The program already corrected this (E2 endpoint re-registration, crediting kimi CRITICAL-1) and re-staked the claim on constraint aging (0.770 → 0.719 → 0.661 for turn-1 constraints). That correction is to its credit. **But the corrected headroom is also confounded**, and nobody has run the decisive contrast:

- The aging map compares turn-1 constraints *at turn 1* (0.770) vs *at turn 3* (0.661). That mixes true aging with **turn-3-global difficulty** (longer context, own-history pollution, concurrent constraint load, harder turn-3 mix).
- Backing out the fresh turn-3 rate from the pooled 0.694 (counts 1.3/1/1, aged rates 0.661/0.747): fresh-t3 ≈ (0.694×3.3 − 1.3×0.661 − 0.747)/1 ≈ **0.684**. With counts 1.5/1/1: ≈ 0.690. Either way, **fresh constraints also drop ~8pts at turn 3**, and the *within-turn-3* fresh-vs-aged gap is only ~2pts (0.684 vs 0.661) — before mix adjustment, which could erase or reverse it.

So the registered target ("recovering aged-constraint compliance, ~5–11pts") is likely an overestimate of pure aging by a large factor. The E2 *endpoint* (replayed-history paired aged-constraint McNemar) remains a valid causal design regardless — but the *motivating number* has not survived contact with arithmetic twice now, and the within-turn fresh-vs-aged, mix-and-length-adjusted contrast is still unreported.

---

## B. Findings (graded)

### CRITICAL-1 — The E2 eval as registered cannot support the claim it would be taken to make.
Three independent defects, each sufficient alone:
1. **No effect floor.** Co-primary 1 gates on "positive paired delta, one-sided p < 0.05" over ~809 conversations × ~2–3 aged constraints ≈ **2,500–2,900 paired observations**. At that n, a **+1–2% net** discordance crosses p < 0.05 easily. The B4/IFEval discipline (+2.0pts AND p < 0.05) was dropped for the endpoint that matters most. A statistically significant, practically trivial result would be read as "WHEN solved."
2. **Clustering ignored.** Per-constraint McNemar treats constraints within a conversation as independent; they share a history and a response, so discordants are positively correlated and the exact test is **anti-conservative**. No conversation-level aggregation or cluster bootstrap is registered.
3. **No trigger/span ablation arms.** The biggest headroom concentrates in turn-1-origin constraints (0.661). A gate whose addressing **degenerates to "always boost the oldest user turn"** — or whose conflict features effectively fire at random on out-of-distribution text — would produce a positive co-primary 1 indistinguishable from a conflict-triggered mechanism. A matched-rate **periodic trigger** arm and a **fixed-span (always-oldest-turn)** arm are not registered; the learned-vs-heuristic addressing ablation died with the killed confirmation and was never re-registered for E2. The registered controls (bitwise-silent rows, truncation reports, synthetic holdout gates) do not close this channel.

If the eval runs unamended and returns a positive, the program will have its first **misleading positive** — worse for the theory than every honest negative it has banked. This blocks the eval in this program's own severity culture.

### HIGH-1 — The pivot's motivating statistic was an artifact; the corrected headroom is still confounded.
The pivot to multi-turn was *decided* on the 38pt strict-prompt decay, which is conjunction arithmetic (Section A). The corrected 5–11pt aging target confounds aging with turn-3-global difficulty and mix (my back-out: fresh-t3 ≈ 0.68, within-turn-3 aging ≈ 2pts). The replayed-history endpoint is the right design; the *expected effect size* staked on it is not currently supported by the headroom map. Required before the eval: within-turn fresh-vs-aged, per-family mix-adjusted, length/truncation-adjusted aging from the recorded base arm.

### HIGH-2 — Synthetic→real distribution shift is unmeasured before a one-shot eval.
The q/k addressing was trained on "Constraint:"-marked synthetic spans; real Multi-IF instructions are unmarked natural language. `constraint_spans_in_context` keys on the literal string "Constraint:", which real Multi-IF does not contain — so span candidacy on the eval distribution is either undefined or falls back to whole-user-turn spans, a categorically different intervention (PASTA-style turn boosting, not rule reactivation). The hazard threshold is calibrated on synthetic conflict statistics, with labels harvested under importance sampling (`--conflict-top`) and failing-row restriction — biasing the helpful base rate the threshold assumes. No pre-eval audit of firing rate per turn or span-selection distribution is registered. A null here would be uninformative and a positive ambiguous — the worst of both.

### HIGH-3 — Governance: registered stop-losses bind the agents, not the user.
The v4.5 stop-loss ("LAST single-turn rescue… failure CLOSES the line") was superseded mid-run by Brian at ~100/1024 rows — the cheapest decisive experiment in the program was never allowed to answer. The four-branch post-Multi-IF decision rule was registered, then superseded by E2 *before any Multi-IF data existed*. E0's post-mortem "NEVER: E1 as originally specced" was partially walked back into CTRB (same three failed family-holdout features + bursts ≤4 + refractory — the E1 schedule — with better labels). Every supersession is documented honestly (ABANDONED-BY-RULING is the right record), but the pattern is real: preregistration's binding force is asymmetric, and the pivot was locked in on the uncorrected arithmetic. The single-turn question now stands formally **unanswered** — not failed, not passed.

### MEDIUM-1 — "Amplitude solved / WHERE solved" overclaims.
Amplitude: the dose sweep shows x1.0 *harmful* (−4.6pts), best dose ≈ 0.25×, effect at that dose +1.5 n.s. The accurate statement is "amplitude is not the binding constraint," not "solved." WHERE: K-perm necessity is shown on synthetic dev; the learned-vs-heuristic comparison on real data never ran; on Multi-IF the addressing operates off-distribution (HIGH-2). These joints carry the E2 claim and should be stated as open.

### MEDIUM-2 — The diagnostic slice is a leak channel unless frozen against.
"key hash mod 9 == 0 (~100 conversations)" is disclosed and excluded from primary claims — good. But unless **every** gate parameter (threshold, dose, burst, refractory, span-selection rule) is frozen before *any* gated contact with Multi-IF, tuning on the 100 leaks into the 809. Register the freeze explicitly or drop the slice.

### MEDIUM-3 — The draft-confirm path steps off the registered deployment semantics.
`_native_draft_confirms` recomputes the draft with **uncached full forwards**, while the committed trajectory is KV-cached — and this program's own KV characterization recorded cross-path drift up to 1.107 logits (wave-bias) against greedy margins as low as 0.103, with an observed argmax flip. Deterministic, yes; but WHEN decisions are partially governed by a numerically different path than the one committed. Uncharacterized decision noise in the mechanism under test.

### LOW-1 — Label-harvest sampling biases (conflict-top, failing-only) shift the helpful base rate; disclose and register for the training harvest, not just the smoke.
### LOW-2 — Multiplicity language: two co-primaries + a secondary; the gate rests on co-primary 1 only. Acceptable, but state the familywise policy explicitly.
### LOW-3 — Credit where due: negative reporting is genuinely strong (B2 FAILs banked, dev-gate FAILs banked, E0 KILL banked, the 0.5 parity gate recorded as *failed*, the unauditable sweep self-flagged, ABANDONED-BY-RULING). The framing overreach ("huge headroom," "the wave's arena," "solved") is the exception, not the pattern.

---

## C. What I would do differently (registered amendments, pre-eval)

1. **Effect floor on co-primary 1**: net aged-constraint recovery ≥ +2.0pts AND p < 0.05 — mirror the B4 discipline.
2. **Cluster-aware inference**: conversation-level secondary (any/all aged constraints recovered per conversation) or cluster bootstrap by conversation, reported alongside the per-constraint test.
3. **Two ablation arms** if runtime allows, else explicit claim scoping to "the CTRB package": (a) periodic trigger at the gate's measured firing rate, no conflict features; (b) fixed-span always-oldest-user-turn bursts. A positive that does not beat both is not evidence for conflict-triggered WHEN.
4. **Within-turn fresh-vs-aged headroom report** (mix- and length-adjusted) from the recorded base arm before the 5–11pt target is quoted again.
5. **Pre-eval gate audit on synthetic holdout**: firing rate per turn, span-selection by turn origin, burst-count distribution, with registered acceptable ranges.
6. **Freeze all gate parameters before any Multi-IF contact**, diagnostic slice included — or drop the slice.
7. **A re-append positive control** (MMMT-IF-style: aged instructions restated fresh in the replayed history). No training, cheap, and it bounds what "focus/retrieval recovery" could ever deliver on this harness — calibrating any wave positive as a fraction of the addressable headroom.
8. **Formally close the single-turn question as unanswered** (or complete the abandoned confirmation if the claim is ever revived). Do not let "pivot" quietly function as "failed."

## D. The single biggest misleading-positive risk

A **floor-less, cluster-inflated, ablation-less positive**: the gate fires at some rate on real Multi-IF, bursts land on the oldest user turn often enough (or the addressing degenerates to exactly that, which is where the headroom concentrates), a +1–2% net aged-constraint recovery crosses p < 0.05 on ~2,900 correlated pairs, and the program declares the WHEN bottleneck solved on untouched Multi-IF — when a periodic or fixed-span spotlight would produce the identical signature. Nothing currently registered excludes this.

---

## Bottom-line verdict

The measurement culture — vendored verifiers with goldens, sealed one-shot runs, hash-pinned resumes, fail-closed statistics with a killed-and-replaced invalid construction, mechanical leak firewalls, two-seed external-claim requirements, and genuinely honest negative reporting — is exemplary, and the WHERE/WHEN decomposition is a faithful operationalization of the Miller framing. The science chain is directionally sound but overstated at two joints ("solved" ×2; the original "huge headroom"). The pivot was **motivated in origin** — decided on an arithmetic artifact, before the registered single-turn test completed — but is **disciplined in execution**: the replayed-history paired endpoint is the correct causal design, and the contamination rule is real.

**Conditionally defensible.** The program is on solid ground *if* CRITICAL-1 (effect floor, cluster-aware stats, trigger/span ablations or claim scoping) and HIGH-1/HIGH-2 (within-turn headroom contrast; pre-eval firing/addressing audit; parameter freeze before any Multi-IF contact) are amended before the one-shot eval. As currently registered, the eval cannot support the claim it would be taken to make — and this program's own history says the expensive failure mode is not another honest negative; it is the first positive that doesn't survive its own review loop.