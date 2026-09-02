# H1′ review — kimi-k3 (2026-09-02)

# H1′ cross-model review — kimi-k3 (2026-09-02)

Artifact: `results/qwen/ledger-kv-probe-h1p/` (`summary.json` schema 3, commit cd73dad). Seat: CPU-only cross-model review — I have the brief, the registered ladder text, and `summary.json`; I do **not** have the 20 session files or repo code. Every arithmetic claim below is recomputed from `summary.json`; code-level assertions are listed as a verification checklist (F6) for the repo-seated reviewer. Suggested report path: `results/h1p-review-kimi.md`.

**BLUF:** All arithmetic verifies. Literal application of the registered H1′ rules yields **ADVANCE-RETENTION**, safety intact — in fact every arm is at or below `full` on every safety event, so the H1 breach mode did not recur. Verdict: **CONFIRMED-WITH-QUALIFICATIONS**.

---

## 1. Recomputation and arithmetic (brief item 1)

**Pass counts and rates** — all exact:

| arm | checks | rate recomputed | reported |
|---|---|---|---|
| full | 44/56 = 0.785714 | ✓ | 0.785714 |
| evicted | 14/56 = 0.250000 | ✓ | 0.250000 |
| pinned | 37/56 = 0.660714 | ✓ | 0.660714 |
| pinned_control | 18/56 = 0.321429 | ✓ | 0.321429 |
| echo_only | 37/56 = 0.660714 | ✓ | 0.660714 |
| pinned_echo | 48/56 = 0.857143 | ✓ | 0.857143 |
| full_echo | 46/56 = 0.821429 | ✓ | 0.821429 |

**Gap and contrasts** — all exact: gap = 44−14 = 30 (`$.gap_full_minus_evicted_passes` ✓, rate 30/56 = 0.53571 ✓). pinned−evicted = 23 (23/30 = 0.7667 ✓); echo_only−evicted = 23 (0.7667 ✓); pinned_echo−echo_only = 11 (11/30 = 0.3667 ✓); pinned−pinned_control = 19 (19/30 = 0.6333 ✓); full_echo−full = 2 (2/30 = 0.0667 ✓).

**Safety table** — I recomputed every `vs_full` cell (event_count − full's count) for all 7 arms × 4 metrics: all 28 cells correct, and every `safe` flag follows. Notably **all vs_full values ≤ 0**: the H1′ run would have passed even the retired H1-era zero-tolerance clause.

**Quoting-excluded rates** — internally consistent with item-level exclusion over quoting-flagged sessions: echo_only 0.625 ↔ 25/40 (6 quoting sessions ≈16 checks: 56=16+40, 37=12+25); pinned_echo 0.833333 ↔ 30/36 (56=20+36, 48=18+30); full_echo 0.871795 ↔ **exactly 34/39** (56=17+39, 46=12+34). Quoting-session check averages (2.67–2.86) match the 2.8 checks/session corpus mean. No convention stated in the file; flag the missing definition, not the numbers.

**Automatic selection** — per-session coverage sums to 19.3333/20 = 0.96667 ✓ (18×1.0 + 2×2/3); extras sum to 7 ✓.

**Bootstrap** (`$.paired_bootstrap_pinned_minus_control`): mean 0.34167 over 20 sessions implies Σ dᵢ/nᵢ = 6.833 — achievable only with mixed session sizes (an all-3-check cohort would give 19/60 = 0.3167), internally consistent with 56 checks / 20 sessions. CI [0.1667, 0.5083] excludes 0. Plausible; resampling not verifiable from this seat.

**Zero arithmetic errors found.**

## 2. Target-blindness and the 0.967 question (brief item 2)

Meta asserts `mark_isolation`: all arm contexts and salience inputs have literal `Constraint:` markers removed; marked text retained only for reported coverage. Provenance pins `salience2.py` and weights hashes; `focus: auto`, `salience_backend: linguistic` (verify this equals the registered DEFAULT_BACKEND — F6a).

On the numbers, the finder re-found the oracle spans (18 sessions 3-of-N, two sessions 2-of-3) plus 7 extras. **This does not disqualify automaticity.** The registration gates the *information path* (no arm or finder reads marks), and explicitly makes coverage "reported, not gated: it is the automatic-vs-oracle bridge." Coverage 0.967 means the finder validated against the oracle on this distribution — which is exactly what a bridge metric is for.

The genuine limitation: mt-train constraints are explicit directive sentences, unusually findable after stripping. H1′ therefore provides **weak evidence of finder generalization** to implicit/agentic targets. That evidence gap is precisely what publish-gate precondition (2) (BFCL V3 MT sealed cohort) exists to fill; H1′ must not be cited as demonstrating generalization.

Leak paths I cannot check from this seat (F6): eviction ranges, pinned_control exact-column matching, span-window ends (the registered dangling-" Constraint" bleed fix), and echo renderer inputs must all derive from auto spans only.

## 3. Decision rules applied literally (brief item 3)

Registered H1′ rule → **ADVANCE-RETENTION iff** pinned > pinned_control AND pinned_echo > echo_only AND pinned_echo recovers ≥ 0.85 of the in-job gap AND safety intact:

1. pinned 37 > pinned_control 18 — **TRUE** (+19; bootstrap LB 0.167).
2. pinned_echo 48 > echo_only 37 — **TRUE** (+11).
3. Recovery = (48−14)/30 = **1.1333 ≥ 0.85 — TRUE** (see F1 on >1.0).
4. Integer-count safety — **TRUE**: timeouts 0 in all arms; truncations max 1 ≤ full+1 = 2; degenerate max 2 ≤ full = 2 (ties allowed by "≤"); invalid max 1 ≤ full = 1.

The RE-INJECTION-ONLY branch fails its own first clause (echo_only recovery 23/30 = 0.767 < 0.85), so no ambiguity between branches. **Registered outcome: ADVANCE-RETENTION.** The orchestrator's WORKLOG reading ("all four conditions hold; not acted on pending review") is accurate and contains no over-claim.

**H1 vs H1′:** same 20 sessions (corpus hash matches H1; "Same 20 sessions" registered), **but mark-stripping changed the base task** — histories were regenerated from unmarked prompts (`history_decode: raw_context_greedy` + `mark_isolation`). full 44 vs 41 (+3) and evicted 14 vs 15 (−1) are small, plausible consequences of removing the "Constraint:" scaffolding (slightly less salience under eviction widens the gap 26→30; slightly less clutter helps full). Every arm moved (pinned 33→37, echo 36→37, control 20→18). H1↔H1′ cell comparisons are **descriptive, not inferential** (F4). The substantive pattern replicated both rounds: echo alone recovers ~0.77–0.81 of the gap; pinned+echo >1.0; pinned > control.

## 4. full_echo − full = +2 (brief item 4)

+2/56 checks (+3.6 pts) is within session-level noise for n=20 clustered sessions (~1–2 sessions flipping). Two readings: (i) it explains the pinned_echo > full anomaly — recency contributes +2 even at full residency, and pinned_echo − full_echo is only +2 more; (ii) its direction independently matches the registered 113-slice text_ledger result (+2.8 pts pooled, p=0.012), so a small real recency benefit in the non-evicted regime is plausible. **Product reading: re-injection is neutral-to-slightly-positive when nothing is evicted; the value case remains the eviction regime.** Do not headline "pinned_echo beats full KV" (F1).

## 5. Quoting / echo-leak (brief item 5)

Quoting rates (sessions): echo_only 6/20, pinned_echo 7/20, full_echo 6/20; all non-echo arms 0.0 as required (no echo text present). Implied per-check splits (§1):

| arm | quoting sessions pass | non-quoting pass | raw → excluded |
|---|---|---|---|
| echo_only | 12/16 = 0.750 | 25/40 = 0.625 | 0.661 → 0.625 |
| pinned_echo | 18/20 = 0.900 | 30/36 = 0.833 | 0.857 → 0.833 |
| full_echo | 12/17 = 0.706 | 34/39 = 0.872 | 0.821 → **0.872** |

In the eviction-regime arms, quoting co-occurs with passing (quoted fragments can satisfy required literals), inflating raw rates by ~2 checks. In full_echo the sign **flips** — parroting co-occurs with *failure* when the content is already resident. The decision is robust under exclusion: pinned_echo − echo_only stays ≈ +11.7 check-equivalents; pinned_echo recovery stays 1.089 ≥ 0.85. **But** a 30–35% session parroting rate is a product-quality liability for publish-gate claims (F2): on 909/BFCL, report quoting-excluded alongside primary.

## 6. Next-rung ranking (brief item 6)

1. **(c) Minimal CPU preflight, hours-scale, no GPU:** salience2 coverage audit on the Multi-IF 909 text_ledger inputs (finder spans vs checker-critical literals/keywords — the linguistic backend needs no model) plus a few-slice dev-set checker-plumbing smoke. This is the binding uncertainty H1′ leaves open (coverage 0.967 on explicit-directive constraints does not bound coverage on IFEval-style instructions), and it de-risks the 30 GPU-h spend against an uninterpretable finder-driven null. This is a preflight *within* the registered 909 step, not a new rung.
2. **(a) 909 Multi-IF text_ledger confirmation under ROUND 7** — the registered next step upon ADVANCE; proceed once (c) shows non-degenerate coverage; report raw and quoting-excluded rates.
3. **(b) BFCL V3 MT sealed cohort** — wait for the harness; run its preflights first (S2 ≥ 8k, random-span control, orchestrator-hands-off). It is the actual publish gate.

Explicitly **not** next: any H3 wave pilot (killed at H1; ladder forbids it as next on ADVANCE). Reminder: the H1′ registration requires fable/sol/kimi pass before any next rung — this is one of three.

## 7. Findings registry

- **F1 (LOW)** — Recovery 1.133 > 1.0 (pinned_echo 48 > full 44). Criterion satisfied literally; >1.0 is noise + redundancy (full_echo +2 explains most), replicated from H1 (1.19). Forbid "beats full residency" framing. Evidence: `$.arms`, `$.contrasts`.
- **F2 (MEDIUM)** — Quoting confound: 30–35% of echo sessions parrot ≥8 echoed tokens; quoting co-occurs with passing under eviction (0.75–0.90) but with *failure* in full_echo (0.706 vs 0.872). Decision robust under exclusion (+11.7; recovery 1.089). Product liability for the publish gate. Evidence: partitions in §5 from `$.echo_only/$.pinned_echo/$.full_echo`.
- **F3 (MEDIUM)** — Automaticity scope: real as registered (marks stripped; coverage report-only) but finder re-found oracle-style explicit constraints; generalization unproven and reserved to the BFCL gate. Evidence: `$.automatic_selection`, `$.mark_isolation`.
- **F4 (LOW)** — Base-task shift vs H1 (mark-stripped history regeneration); gap 26→30; cross-round cell comparisons descriptive only.
- **F5 (LOW)** — Definition drift: `degenerate_def: "truncated or rep4>0.5"` vs registered "rep4 > 0.5". Stricter, passes either way; fix string/provenance before publish docs.
- **F6 (LOW, blocking-if-wrong)** — Code-verification checklist (repo seat): (a) linguistic == DEFAULT_BACKEND; (b) marks stripped before history generation for *all* arms incl. full; (c) eviction ranges and pinned_control matching from auto spans only; (d) dangling-" Constraint" bleed fix landed; (e) oracle text used only for coverage. Any failure in (b)–(e) voids this verdict.
- **F7 (INFO)** — full_echo − full = +2: within noise; direction matches prior +2.8-pt text_ledger result; non-evicted product regime neutral-to-positive.
- **F8 (INFO)** — Factorial coherence: echo's marginal value declines with residency (+23/+11/+2); echo_only = pinned = 37 (H1: 36 vs 33); no anomaly. Quoting-excluded definition absent from summary — add to meta.

## 8. Verdict

**CONFIRMED-WITH-QUALIFICATIONS.** Under the registered H1′ rules applied literally with the integer-count safety clause, the outcome is **ADVANCE-RETENTION**: pinned 37 > pinned_control 18; pinned_echo 48 > echo_only 37; recovery 34/30 = 1.133 ≥ 0.85; safety intact (all arms ≤ full on every safety event — stricter than the amended clause requires, and the H1 truncation breach did not recur). All summary.json arithmetic verifies with zero errors. Qualifications: recovery >1.0 is criterion-satisfying noise, not superiority over full residency; echo-arm parroting (30–35% of sessions) inflates raw echo rates ~2 checks and must be co-reported (quoting-excluded) in confirmation runs; coverage 0.967 validates the finder only against oracle-style explicit constraints — true automatic generalization remains the job of the registered publish-gate benchmark; H1/H1′ number comparisons are descriptive (mark-stripping changed the base task). F6 items (b)–(e) must be verified in code at cd73dad by the repo-seated reviewer before the ADVANCE is banked.

**Ranked next step:** (1) CPU-only finder-coverage + checker preflight on Multi-IF 909 inputs; then (2) the registered 909 Multi-IF text_ledger confirmation (~30 GPU-h, ROUND 7, raw + quoting-excluded reporting); then (3) BFCL V3 MT sealed-cohort preflights once the harness exists. Pending fable and sol concurrence per the registration.