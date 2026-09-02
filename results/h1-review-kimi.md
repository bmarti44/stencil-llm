# H1 review — kimi-k3 (2026-09-02)

# H1 Artifact Review — kimi-k3 (cross-model)

**Artifact:** `results/qwen/ledger-kv-probe-h1/summary.json` (schema 3) against registered FOCUS LADDER v1 / H1.
**Method constraint:** I have no shell and was not given the 20 session files or meta.json. Everything below is therefore (i) exact internal-consistency recomputation from summary.json, and (ii) literal application of the registered rules. Where a brief item requires session-level data (score vectors, column equality, one-job provenance), I say so and do not pretend to have verified it. Nothing in summary.json contradicts the orchestrator's claims; several things cannot be confirmed from it.

---

## 1. Arithmetic verification (brief item 1)

All recomputed by hand from the JSON counts. `n = 56` aged slices, 20 sessions.

| Quantity | Stated | Recomputed | OK |
|---|---|---|---|
| full rate | 0.7321428571 | 41/56 = 0.7321428571 | ✓ |
| evicted rate | 0.2678571429 | 15/56 = 0.2678571429 | ✓ |
| pinned rate | 0.5892857143 | 33/56 | ✓ |
| pinned_control rate | 0.3571428571 | 20/56 | ✓ |
| echo_only rate | 0.6428571429 | 36/56 | ✓ |
| pinned_echo rate | 0.8214285714 | 46/56 | ✓ |
| wave d0.5 / d1.0 / d3.0 | 0.5536 / 0.6429 / 0.6786 | 31/36/38 per 56 | ✓ |
| gap (passes) | 26 | 41 − 15 = 26 | ✓ |
| gap (rate) | 0.46428571428571425 | float(41/56) − float(15/56) | ✓ (float-path, not 26/56 literal) |
| pinned − evicted | +18, frac 0.6923077 | 33 − 15; 18/26 = 0.69230769 | ✓ |
| echo_only − evicted | +21, frac 0.8076923 | 21/26 | ✓ |
| pinned_echo − echo_only | +10, frac 0.3846154 | 10/26 | ✓ |
| pinned − pinned_control | +13, frac 0.5 | 13/26 | ✓ |
| wave best dose | d3.0 | max(31,36,38) = 38 | ✓ |
| wave best-dose recovery | 0.8846154 | (38−15)/26 = 23/26 | ✓ |
| wave_killed | true | degenerate 12 > 2 at best dose | ✓ |
| degenerate ≥ trunc per arm | holds | e.g. d3.0: 12 ≥ 11, extras from rep4 | ✓ |
| degenerate = trunc + rep4 cases | consistent | mean_rep4 monotone in dose: 0.182/0.213/0.568 | ✓ |
| bootstrap pinned − control | mean 0.2375, 95% CI [0.0708, 0.3958] | pooled 13/56 = 0.2321; session-mean 0.2375 plausible with unequal slices/session; CI excludes 0 | ✓ |

**Not verifiable here:** per-slice score vectors, per-session rep4/truncation decomposition, quoting flags, recovery curves, meta.json job structure. Nine arms and `max_new: 512` are consistent with the registered one-job requirement (single corpus hash, single position policy, uniform deadline); one-job provenance itself is asserted, not demonstrated, in what I was given.

**Finding F7 (informational):** two 1-ulp float artifacts — `gap_full_minus_evicted` is the float difference of rates rather than 26/56, and top-level `recovered_frac_pinned` (0.6923076923076924) differs by 1 ulp from the contrasts entry (0.6923076923076923). Both recompute exactly under their computation paths. No action.

---

## 2. pinned_echo > full (46 > 41) — red flag analysis (brief item 2)

The quoting-excluded denominators can be backed out exactly: `pass_rate_quoting_excluded` = 20/33 = 0.606060… (echo_only) and 27/33 = 0.818181… (pinned_echo). That implies **23 quoting responses in each echo arm** (56 − 33), and:

| Arm | Quoting responses pass | Non-quoting pass | Δ |
|---|---|---|---|
| echo_only | 16/23 = 69.6% | 20/33 = 60.6% | +9.0 pts |
| pinned_echo | 19/23 = 82.6% | 27/33 = 81.8% | +0.8 pts |

Three conclusions:

1. **The anomaly is not a quoting artifact.** Excluding quoting responses moves pinned_echo 0.821 → 0.818, and the headline contrast *strengthens*: raw pinned_echo − echo_only = 10/56 = 0.179; quoting-excluded = 0.818 − 0.606 = 0.212. The "quoting responses get verifier credit" effect is real but confined to echo_only (+9 pts), where literal reproduction is the only recency channel; in the winning arm, quoting and non-quoting responses pass at the same rate.
2. **The "echo leaks the constraint into a rewarded position" hypothesis is common-mode.** The echo text is byte-for-byte identical in echo_only and pinned_echo; any leak exists in both and is differenced out of the +10 contrast. What differs is KV residency, and it adds 10 passes on top of re-injection.
3. **Over-recovery is coherent, not suspicious.** full has availability without recency (constraints aged far back); pinned has availability without recency by construction (`position_policy: no_reindex_positions_continue` — pinned KV keeps aged positions); pinned_echo has both. pinned (33) < pinned_echo (46) and pinned_echo > full (46 > 41) is exactly the recency-on-top-of-availability signature the factorial was designed to detect. Recovery = 31/26 = 1.19 ≥ 0.85.

**Finding F5 (low):** the registered 0.85-gap criterion is silent on recovery > 1, so it is trivially satisfied by an arm exceeding full. Not a violation; note for the next registration that "recovers ≥ 0.85 of gap" should perhaps read "recovers ≥ 0.85 of gap, where recovery > 1 is reported explicitly."
**Finding F4 (low):** quoting inflates verifier passes by ~9 pts *within echo_only only*; headline contrasts survive exclusion. Keep the quoting-excluded metric as the primary citation for the echo arms.

---

## 3. The oracle-focus label (brief item 3)

The echo is rendered byte-for-byte from the harness's marked "Constraint:" spans, so the **selection set is oracle-derived in every arm that touches focus** — the echo arm does not deserve "target-blind," and the registered "marked/oracle focus" label is the correct one. The only weaker sense in which the echo is target-agnostic is that it carries all aged constraints rather than the specific slice's target; membership, though, came from the marks.

Precisely, H1 shows — **under oracle-marked focus, on 20 sessions / 56 aged slices**: (i) availability without recency recovers +18 (+0.692 of gap); (ii) text re-injection without residency recovers +21 (+0.808); (iii) residency adds +10 on top of re-injection (quoting-excluded: ≈ +7 passes on the common 33-response subset, 0.212 in rate); (iv) the effect is column-specific (+13 over exact-column control, bootstrap CI excludes 0).

H1 **does not show** anything about the automatic case: salience2 never selected anything in these arms (its presence in provenance hashes is infrastructural, not operational). The external evidence for the automatic case remains the 113-slice text_ledger result (+2.8 pts pooled, p = 0.012) — a *text re-injection* result at small effect. H1's echo_only (+21) is the oracle-marked analogue and must not be cited as confirmation of the automatic selection path. If WORKLOG's ADVANCE-RETENTION entry does not carry the "marked/oracle focus" label forward, that is an over-claim by omission; the label is part of the registered reading.

---

## 4. Literal application of the decision rules (brief item 4)

**ADVANCE-RETENTION conditions:**
- pinned 33 > pinned_control 20 ✓ (CI [0.071, 0.396], excludes 0)
- pinned_echo 46 > echo_only 36 ✓
- pinned_echo recovery 31/26 = 1.192 ≥ 0.85 ✓
- Safety: timeouts 0 everywhere ✓; degenerate sessions not above full (pinned 2 = full 2; pinned_echo 1; echo_only 1) ✓; **truncation excess — see F1 below.**

RE-INJECTION-ONLY is correctly not triggered (echo_only recovers 0.808 < 0.85, and pinned_echo > echo_only). The FAIL parenthetical — recovery in [pinned, 0.85·gap) — does not apply since recovery is 1.19. The orchestrator selected the correct branch.

**Finding F1 (medium):** the safety clause "truncation excess over `full` ≤ +2 pts" is unit-ambiguous, and the ADVANCE reading silently adopts the lenient one. Count reading: pinned has 2 trunc events vs full 0 → +2 ≤ +2, passes at the boundary. Slice-rate reading: 2/56 = +3.6 pts > +2 → fails, and a strictly literal "pts" reading would flip ADVANCE-RETENTION to FAIL. Session-rate reading (2/20 = +10 pts) fails harder. The rulebook mixes units elsewhere (timeouts in %, degeneracy in session counts), so this is a registration defect, not an artifact defect. The substantive effect is two marginal truncations in one arm with degenerate-sessions equal to full, so I do not change the verdict over it — but the WORKLOG entry should state the adopted reading, and the ladder text should pin the unit.

**Wave rule:** kill rule fired correctly (best dose d3.0, degenerate 12/20 > 2). The orchestrator's stronger phrasing — "fails at every gaining dose" — is accurate: the gaining doses are d1.0 (36 > pinned 33; degenerate 4/20 > 2) and d3.0 (38 > 33; 12/20 > 2); d0.5 sits exactly at the 2/20 boundary and is **non-gaining** (31 < 33), so it is not a counterexample. Note the trap the rule was built for: best-dose wave recovery is 0.8846 ≥ 0.85, i.e., without the degeneracy kill, amplification would have looked creditable. The rule worked as designed.

**Finding F6 (low):** nine arms ran where six were registered; the wave arms are exploratory riders (added at 9c7e1ac) sharing sessions and the in-job gap, so the factorial contrasts are uncontaminated — but the wave numbers must stay out of the H1 outcome sentence. H3 preconditions (frozen rejection policy, CPU formula tests) do not exist; this probe is not and cannot be an H3 pilot.

---

## 5. Exact-column control (brief item 5)

**Finding F2 (medium — verification gap, not a defect):** column equality between pinned and pinned_control per session (the v3 assertion) cannot be confirmed from summary.json, and I have no session access. The statistical side is sound (+13/56; paired session-level bootstrap [0.0708, 0.3958], n = 20, seed 0, 2000 resamples), and `aged_n: 56` matches across arms. But "specificity" as a claim is only as good as the harness property, and the ADVANCE-RETENTION rule's first condition rests on it. Since the registered text calls this an assertion, the cheapest fix is for the session JSONs to carry a one-line `control_columns_equal: true` per session so any future reviewer (shell-less or not) can verify from the artifact alone. I found **no evidence of violation**; I am marking what I could not check.

---

## 6. Findings summary

| # | Grade | Summary |
|---|---|---|
| F1 | **medium** | Truncation-safety clause unit ambiguous ("+2 pts"); ADVANCE holds only on the count reading, at the boundary (pinned 2 vs full 0) |
| F2 | **medium** | Exact-column control equality unverifiable from summary.json by this reviewer; statistics consistent; no counter-evidence |
| F3 | **low** | `quoting_rate: 0.4` is not k/56; backed-out quoting count is 23/56 = 0.4107 in *both* echo arms (identical denominators 33 elsewhere) → field is session-level (8/20?) or rounded; schema should name the denominator |
| F4 | **low** | Quoting inflates echo_only passes +9 pts (69.6% vs 60.6%), pinned_echo +0.8 pts; contrasts strengthen after exclusion |
| F5 | **low** | Recovery > 1 (1.19) not anticipated by the registered criterion; report explicitly next time |
| F6 | **low** | Unregistered wave arms rode the H1 job; contrasts uncontaminated; wave correctly killed; keep wave out of the outcome text |
| F7 | informational | 1-ulp float-path duplicates in gap/recovered_frac fields |

No arithmetic errors found. No critical or high findings.

---

## Verdict

**CONFIRMED-WITH-QUALIFICATIONS.** The orchestrator's ADVANCE-RETENTION reading is arithmetically correct and the right branch of the registered rules; "wave fails the 2/20 rule at every gaining dose" is verified word-for-word. Qualifications: (1) the truncation-safety clause passes only under the count reading, at the boundary — state it (F1); (2) the result is **marked/oracle focus** and the automatic-selection claim remains unproven — the label must travel with the result (§3); (3) column equality of the control is unverified in this review (F2); (4) wave numbers are exploratory and excluded from the outcome. None of these overturn the reading.

## Ranked next rung

1. **(a) Automatic-selection replication of H1 (H1′)** — same 20 sessions, same six factorial arms, salience-selected spans in place of oracle marks, contrasts and thresholds re-registered identically before viewing outcomes. It closes the *one* gap H1 is explicitly registered as leaving open, at ~1 GPU-h with machinery already in the tree (salience2 hashes are in provenance). Best on both criteria: adequate proof *and* minimal engineering.
2. **(b) 909 Multi-IF confirmation restricted to text_ledger (re-injection), ROUND 7** — the legitimate first scale-up, but only after (a), and scoped to the text channel where independent automatic-case evidence already exists (+2.8 pts, p = 0.012). Scaling the KV-retention claim on oracle-marked evidence alone would build the larger run on exactly the confound H1 was designed to isolate.
3. **(c) H3 trust-region wave pilot** — do not run. The wave was killed at every gaining dose on this very corpus (12/20 degenerate at the best dose), H3 is unregistered, and none of its preconditions (frozen rejection policy, CPU formula tests, disjoint confirmation cohort) exist. Running it now is over-engineering against a registered kill.