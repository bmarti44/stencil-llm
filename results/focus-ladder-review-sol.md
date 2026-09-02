# Focus ladder review — sol (spec adversary)

Date: 2026-09-02  
Reviewed snapshot: `3a1dd35`; `scripts/ledger_kv_probe.py` SHA-256 `80d0e997c7a8984df2434f588f210510de82537c24a79df1276038a261249e46`  
Method: CPU-only source/artifact inspection and arithmetic. No model or GPU process was launched.

## Verdict

**NOT LAUNCHABLE AS WRITTEN.** H1 is a useful, small factorial experiment after several exact fixes. H2's gate is mathematically expected to pass under the global null and its teacher-forced target is undefined by the corpus. H3 does not run on the same causal regime as either existing harness, its rejection/backoff policy is incomplete, and a 128-example development pilot followed by an inclusive “sealed 909” reuses development outcomes in confirmation. The final falsifier therefore does not support its stated causal conclusion.

Recommended disposition: repair and run H1; delete H2 as a gate (or retain it only as a non-gating ranker after defining valid reference continuations); reduce H3 to CPU formula/cache tests plus one frozen-config cache-probe pilot. Register a separate, disjoint Multi-IF confirmation only after that pilot passes. The fixed 909 is estimated at about 30 GPU-hours in `results/research-synthesis.md`, so it cannot honestly be an under-one-day rung on the current estimate.

## Arithmetic and gate audit

### H1

The pinned 0.615 figure is correct for `results/qwen/ledger-kv-probe-v2`:

| arm | aged passes | truncations | degenerate sessions |
|---|---:|---:|---:|
| full | 41/56 | 5/20 | 7/20 |
| evicted | 15/56 | 1/20 | 2/20 |
| pinned | 31/56 | 4/20 | 4/20 |
| pinned_control | 20/56 | 1/20 | 2/20 |
| pinned_wave (raw, non-creditable) | 36/56 | 12/20 | 13/20 |

Thus the eviction gap is `41 - 15 = 26` passes and pinned recovery is `(31 - 15)/(41 - 15) = 16/26 = 0.6153846`.

- The 0.85 H1 gate requires at least `ceil(15 + 0.85*26) = 38/56` for pinned_echo. `37/56` recovers `22/26 = 0.8462` and fails; `38/56` recovers `23/26 = 0.8846` and passes.
- The “pinned + 0.05 of gap” stop boundary is `31 + 1.3`. With integer outcomes, pinned_echo at 31 or 32 stops; 33–37 misses the success gate but does not trigger the written stop. That intermediate result needs an explicit `H1 fail / do not advance` reading.
- The artifact used `max_new=320`; the current probe defaults to 512 (`scripts/ledger_kv_probe.py:50`). The historical 0.615, five truncations in full, and four in pinned cannot be mixed with a new 512-token run. Freeze 320 or rerun every arm and recompute the gap.
- The repo definition is `truncated OR rep4 > 0.5` (`scripts/ledger_kv_probe.py:34,138`), not the ladder's `rep4 >= 0.5`.
- The proposed absolute `degenerate <= 2/20` is not inherited from retention: it is stricter than full (7/20) and pinned (4/20). Compare pinned_echo to pinned on the same run; minimally require no excess degeneration and truncation no higher than full.
- The v2 five-arm run took about 20 minutes by artifact timestamps. A six-arm H1 at the same 320-token cap is plausibly below one hour, but the repo protocol still requires one timed pilot cell before projection.

### H2

Qwen3-1.7B has 28 layers and 16 query heads (`src/stencil/qwen3.py:21-24`), hence **448** `(layer, head)` candidates.

- With 448 unadjusted two-sided 95% intervals, the one-sided positive false-positive probability is approximately 0.025 per head. Under a global null, the expected count of positive “significant” heads is `448*0.025 = 11.2`, and `P(X >= 8) = 0.8724`. If “95% CI” is interpreted one-sided, the false-pass probability is approximately 0.9999. The `>=8` gate is therefore non-diagnostic.
- The 20 sessions contain 56 aged constraints but only 20 independent conversation/session clusters. Tokens and constraints must not be bootstrapped as independent units.
- The stored full continuations contain 4,206 tokens (mean 210.3/session), but only 7/20 full-arm responses pass every aged constraint. The corpus supplies verifier metadata, not canonical gold continuations. Its 56 constraints cover 11 families, including forbidden words, maximum length, case, sentence count, and bullet count; many have no local “aged-constraint answer tokens.” The proposed log-probability outcome is undefined, and treating native/full output as gold would reward noncompliant behavior in 13/20 sessions.
- A `(16,t,T)` bias does broadcast over the batch dimension of the `(b,16,t,T)` attention tensor at `src/stencil/qwen3.py:150-151`; per-head steering itself needs no trunk change. Natural-mass measurement does: the current `attn_probe` records the last row averaged over heads and is only attached at layers 20–27 (`src/stencil/qwen3.py:167-181,244`). It cannot provide the requested per-head, all-layer distribution.
- “Fixed delta-psi 0.02” must define an exact logit operation. For raw span mass `psi`, an absolute target `psi' = psi + .02` requires `b = logit(psi') - logit(psi)`. This is not uniformly small: at `psi=.01`, `b≈1.12` (about 3.06x span odds), and it diverges as `psi` approaches zero. A natural-mass ceiling alone does not bound that low-mass case; freeze a `b_max` or a minimum `psi` as well.
- A naive scan is 20*448 = 8,960 intervened full-sequence forwards plus raw passes. `results/research-synthesis.md` calls the pre-check about one GPU-hour but budgets the R2 scan at about three GPU-days. No measured pilot supports the smaller number. The hand-written trunk also performs fp32 attention without a fused attention path. Do not launch the full matrix on the one-hour claim.

### H3 and ROUND 7

The grid has six nominal candidates (`3 lambdas * 2 delta caps`), before adaptive retries. The existing runner and proposed mechanism do not align:

- `scripts/ledger_kv_probe.py` evicts history and pins KV, but uses the synthetic, explicitly marked 20-session corpus and only the final turn.
- `scripts/ledger_eval.py` runs 113/909 Multi-IF with full replayed history. Its `text_ledger` arm already re-appends aged entry text, but none of its arms evicts or pins KV. Pinning has no availability role there.
- The current 113 slice is now observed: 113 conversations, 221 late turns, 85 eligible cells in 43 clusters, coverage 80/85 = 0.9412. Its current neural arm fails its registered screen (credited neural-minus-base clustered lower bound -9.63 points; text-minus-neural upper bound 13.19 points). It is development evidence, not an untouched source for a new configuration followed by an inclusive sealed 909.

ROUND 7 replaces the impossible absolute truncation gate with treatment-minus-base <= 0.02 and retains an absolute timeout cap <= 0.02. The frozen base has 185/1805 = 0.102493 truncation. On the same 1,805-turn denominator, a treatment may have at most 221 truncations (`36/1805` excess passes; `37/1805` fails), and at most 36 timeouts. Truncated responses are scored as-is and never excluded. H3's “truncation excess <= +2” must say **percentage points per late turn**, and it omits the timeout gate.

The existing confirmatory gate also requires the registered cohort/config, real salience, coverage >=0.90, both clustered text-vs-base non-vacuity gates, credited neural-vs-base superiority, activity on every credited turn, and provenance. A new head set, dose law, pinned cache, and pinned_echo comparator do not run “under ROUND 7” merely by retaining its truncation rule; they require a new registered arm/estimand and re-verification.

## Severity-graded findings

### CRITICAL 1 — H2's `>=8 significant heads` gate self-passes under the null

The uncorrected 448-way scan expects 11.2 positive false discoveries and has about an 87% chance of producing at least eight. Ranking and testing on the same 20 sessions adds winner's curse. This gate cannot establish that contextual heads exist.

**Required correction:** either remove H2 as a hypothesis gate, or split discovery and validation by session, freeze a head set on discovery, and perform one session-clustered held-out test of the set-level intervention. Do not test 448 individual bootstrap intervals. Holm/max-T correction is valid but likely underpowered at 20 clusters and adds machinery without helping the decision.

### HIGH 2 — H2 has no valid teacher-forced target and delta-psi is not a small fixed dose

There are no gold continuations or general token-to-constraint alignments. Native/full outputs are not gold, and negative/global constraints cannot be represented by a few target tokens. A +0.02 absolute mass change can require a very large logit offset on a naturally low-mass head.

**Required correction:** before any scan, define a held-out set of verifier-passing reference continuations and a session-level normalized outcome (for example mean continuation log-probability, explicitly acknowledged as a proxy), plus the exact `psi -> b` formula, a natural-mass ceiling, and `b_max`. If building valid references is more work than the H3 pilot, skip H2 and use the preregistered layer-pair fallback; an invalid pre-check is worse than no pre-check.

### HIGH 3 — H1's success event does not identify retention

The primary gate is on pinned_echo, a joint KV-retention plus textual-repetition treatment. It can pass entirely because echo_only works. Conversely, the absolute degeneracy gate would reject the already observed full and pinned baselines. Dropping pinned_control also loses the best evidence that semantic retention, rather than generic surviving columns, matters.

**Required correction:** retain the exact-column `pinned_control`, and read the factorial contrasts: `pinned - evicted`, `echo_only - evicted`, and `pinned_echo - echo_only`. Call retention a mechanism only if pinning adds value over echo_only and beats pinned_control. A pinned_echo-only pass supports “making the text available,” not specifically KV memory routing.

### HIGH 4 — H3's Multi-IF pilot and confirmation are not defined on a pinned-KV causal regime

The 20-session probe has eviction/pinning; the 113/909 runner has neither. Porting H3 into the latter requires an explicit compaction/eviction boundary, exact pinned columns, a matched evicted baseline, and a decision on whether the current user echo survives. Without that policy, “TR versus pinned_echo” is not an executable same-difference comparison.

Further, a 128-conversation pilot drawn from the 909 and then included in the sealed 909 leaks configuration selection into confirmation. The already observed 113 cannot be treated as pristine confirmation data.

**Required correction:** use the synthetic 20-session cache harness to freeze the H3 policy, or identify and hash a development cohort disjoint from the 909. If development uses a subset of the 909, confirmation must use only the held-out remainder and the governing sample-size registration must change before outcomes are viewed.

### HIGH 5 — The DIRECTER-style rejection policy is incomplete and unsafe to implement literally

“JS <= dev budget; else halve dose / drop a layer pair / emit raw” leaves the JS calibration, retry sequence, layer-drop order, maximum retries, and H2-head grouping unspecified. The lambda grid is not a halving chain (`.5 -> .25 -> .125`, not `.1`). `press-survival` has no denominator. Most importantly, `Qwen3.forward` mutates `KVCache` in place (`src/stencil/qwen3.py:134-141,246-247`): raw and candidate passes cannot sequentially share one cache. The accepted distribution must carry the corresponding accepted KV state forward.

**Required correction:** freeze:

1. `p=raw`, `q=candidate`, `yq=argmax(q)`; accept iff `p[yq] >= .5*max(p)` and `JS(p,q) <= J_max`.
2. A development-only rule for `J_max`, including JS log base and float precision.
3. A finite candidate/backoff list and fixed layer-pair removal order, terminating in raw.
4. Cache cloning before raw/candidate passes and committing only the chosen branch's cache.
5. Counters for eligible steps, proposed nonzero presses, accepted nonzero presses, each rejection reason, backoff depth, raw fallbacks, and actual mass change. Survival is `accepted_nonzero/proposed_nonzero`; a zero cap does not count as a press.

### HIGH 6 — H3's pilot gate and final falsifier overclaim

“late-turn adherence LB > pinned_echo” is dimensionally ambiguous. It must be the one-sided conversation-clustered lower bound of the paired difference `H3 - pinned_echo`, on the same conversations. Applying that inferential gate after choosing the best of six configurations on the same 128 examples is anti-conservative and likely too strict for a pilot expected to find a 1–3 point effect.

The final logic `H2 stop AND H3 stop AND H1 pass => availability, not amplitude` does not follow: H2 can stop from an invalid/underpowered proxy; H3 can stop from an over-tight trust budget; and H1 can pass due entirely to echo_only. It also drops the synthesis's mediation and shuffled-span conditions.

**Required correction:** the pilot is for safety/futility and freezing, not confirmation: require no safety regression, survival >=5%, verified positive mass change, and a positive point estimate (or an efficacy UCB still compatible with the target). Reserve `LB(H3-pinned_echo)>0` for a disjoint confirmation. Conclude “amplitude not useful for this trunk” only after a safe accepted dose raises correct-span mass, its efficacy UCB excludes the practical target, shuffled spans do no better, and pin-specific H1 contrasts pass.

### MEDIUM 7 — Echo scoring is clean, but the proposed renderer and target-blind wording are not

The verifier does **not** see the appended echo. In the synthetic probe, `score_row_constraints(row, response)` receives verifier IDs/kwargs and the assistant response only (`src/stencil/causal_moments.py:193-206`). In Multi-IF, `score_turn` receives the original current prompt and response, not the modified `text_ctx` (`src/stencil/e2_multiif.py:27-38`). There is no direct prompt-scoring leakage.

Echoing input constraint text also does not itself violate target blindness: the model sees no answer target or verifier. But the current KV probe obtains focus spans by parsing explicit `Constraint:` markers (`scripts/ledger_kv_probe.py:301-303`; `src/stencil/e2.py:50-82`). It is an oracle/marked-focus mechanism probe and cannot establish the plan's automatic, marker-free target-blind product claim.

The new singular template is unnecessary and underspecified for multiple spans. It adds a terminal period to text that may contain exact postscript/title punctuation, does not define ordering/deduplication/delimiters, and introduces another cross-rung wording difference. `src/stencil/ledger.py:337-359` already supplies a tested insertion inside the final user message:

`Earlier user instructions restated verbatim:` followed by one bullet per exact entry.

**Required correction:** reuse that renderer byte-for-byte in both H1 and H3; freeze ledger order and deduplication; assert the echo is inserted before the final user `<|im_end|>`; reject embedded chat-control tokens; record added token count. Label the 20-session result “marked/oracle focus,” not automatic target-blind selection.

### MEDIUM 8 — Safety gates omit the observed failure modes

H3 carries truncation but drops repetition/loop and invalid-output safety, despite pinned_wave's 13/20 degeneration being the reason amplification was killed. It also omits ROUND 7 timeouts and the rescope's stale-constraint adoption condition. Multi-IF's cumulative constraints do not supply deletion/supersession cases, so stale adoption is not measurable there.

**Required correction:** carry `rep4 > .5 OR truncation` (or separately report both), invalid output, absolute timeout <=2%, and truncation excess <=2 points. Treat stale adoption as a separate non-vacuous safety set; do not report it as passed on a corpus with no stale rules.

### MEDIUM 9 — The “under a day” requirement conflicts with the registered confirmation

H1 is comfortably small. H2 has no measured one-hour projection and the synthesis itself says about three GPU-days. H3's 909 confirmation is budgeted at about 30 GPU-hours. Shrinking the fixed 909 after development would sacrifice the existing registration and power.

**Required correction:** make every *iteration* under a day, not the terminal confirmation. Split H3 into an under-day pilot rung and a separate H4 confirmation. Keep the 909 only if its registered evidentiary value is worth the >1-day runtime; otherwise amend the claim and sample size before any H3 outcome is observed.

## Minimal runnable ladder

### H1 — one small factorial run

- Freeze `20 sessions`, the same 56 aged constraints, `max_new=320`, deadline 300 seconds, greedy decode, and repo rule `rep4 > .5`.
- Arms: `full | evicted | pinned_control | pinned | echo_only | pinned_echo`.
- Reuse the existing text-ledger renderer. Keep generation/scoring metadata separate; record echo token count and generated token IDs.
- Success: same-run recovery >=0.85 (historical endpoints imply pinned_echo >=38/56), pinned_echo truncation <= full, pinned_echo degeneration <= pinned, pinned > pinned_control, and a positive pin contribution `pinned_echo - echo_only`. Report paired repair/regression counts by session.
- Stop: pinned_echo <=32/56 under historical endpoints means echo adds <=5% of the gap; 33–37 is an explicit H1 fail/partial result and does not advance the “H1 pass” branch.

This is a sub-hour run at the prior measured pace and can be read from one six-row table plus three paired contrasts.

### H2 — cut the invalid gate

Preferred fast path: skip H2 and use the already specified layer-pair fallback in H3. Do not interpret the skip as evidence that contextual heads do not exist.

If a ranker is still wanted, limit it to a predeclared 128 late-layer coordinates (layers 20–27), use session-split discovery/validation with valid compliant references, rank on discovery, and test the frozen top-eight **joint intervention once** on validation. Pilot one candidate/session first and project wall time. This is engineering selection, not a 448-hypothesis discovery claim.

### H3 — two under-day stages, then a separate confirmation

1. **CPU formula/cache tests:** exact zero-dose identity; only named heads change; delta-psi and `b_max` hold; JS/probability rejection is deterministic; raw fallback is bitwise raw; raw/candidate caches do not double-append; chosen cache matches chosen logits.
2. **One frozen-config cache pilot:** choose the six-grid winner teacher-forced on development only, then generate exactly one TR configuration on the 20-session eviction harness against pinned and pinned_echo. Gate safety, >=5% accepted-nonzero survival, verified mass movement, and positive paired point estimate. No lower-bound claim on this tuning set.
3. **H4, not an under-day rung:** only after stage 2 passes, register a cache-pressure Multi-IF runner, a development set disjoint from confirmation, the full DIRECTER backoff policy, ROUND 7 safety, loop/invalid/stale safety, and the paired clustered estimand. Then run one frozen confirmation. Do not call an inclusive 909 sealed after tuning on 113/128 of it.

## Final verdict

**REJECT LADDER v0; ACCEPT H1 AFTER THE SPECIFIED CUTS.** H2 should not gate H3 in its present form. H3 requires a new registered causal harness and disjoint confirmation design. Until those changes land, a joint H2/H3 stop cannot falsify attention amplitude, and an H1 pinned_echo pass cannot establish memory routing.
