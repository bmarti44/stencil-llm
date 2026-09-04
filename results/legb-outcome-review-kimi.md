# LEG B outcome review — kimi-k3 (2026-09-04)

```markdown
# LEG B OUTCOME — cross-model review (kimi-k3), 2026-09-04
Target file: results/legb-outcome-review-kimi.md (CPU-only; no GPU/model processes launched; no processes
signalled; no repo edits; sealed IFEval input untouched — no shell was available to me regardless).

## 0. Scope: what this review could and could not check
Packet-only review. NOT available to me: the 909 conv-*.json records (summarized only), meta.json (harness
hash, classifier sha256s, seeds), the harness source and its registered definitions of
invalid/degenerate/truncated, echo-token counts and per-arm column counts, the control_impossible
conversations (keys only), and — critically — the invalid outputs themselves: the packet section
"invalid outputs (from records)" is an EMPTY list []. Every "recomputation" below is therefore an
internal-consistency check of summary.json, not a recount from records. Where the verdict pivots on
record-level facts, I say so.

## (1) Totals, contrasts, recovered fraction, safety — VERIFIED at summary level; NOT recountable
- [VERIFIED] Arm totals→rates recompute exactly: 1483/2276=0.651582; 379/2276=0.166520; 1302/2276=0.572056;
  1348/2276=0.592267; 747/2263=0.330093; 1377/2276=0.605009. All/all_pass rates likewise. Cohort totals
  (909 conversations; 2,276 aged; 3,185 all) match the OUTCOME header.
- [VERIFIED] Contrast point estimates are exactly recoverable from the conversation-mean rates, which
  cross-validates the contrast engine against the arm table: C2 = 0.5725156−0.6074441 = −3.4928492849284 pts
  (exact to 13 digits); C3 = echo − ½(full+evicted) = 18.472680601393474 pts (exact); C1's 26.8437 over 904
  clusters implies an echo-904 mean of 0.5957780 vs the reported 909-mean 0.5945178, i.e., the 5 excluded
  conversations average ≈0.367 echo rate — arithmetic hangs together; control aged_n 2263 = 2276−13 implies
  the 5 impossible conversations carry exactly 13 aged (18 total) constraints; consistent.
- [VERIFIED] Bound mechanics: continuity = 100/n pts (0.11062 at 904; 0.11001 at 909, exact), and
  lower_bound = t_descriptive − continuity for all four contrasts. Implied t-stats from the descriptive bounds
  (C1 ≈ 21.9, C3 ≈ 18.6, echo−full ≈ −5.1, C2 ≈ −4.9/−5.0 depending on whether p is taken on the
  continuity-shifted statistic) are consistent with the reported one-sided p's (C1/C3 → 0.0;
  C2 → 1−3.2e-7; echo−full → 1−1.1e-7). Holm ordering and cutoffs (0.05/3, 0.05/2, 0.05) correct; the two
  zero-p contrasts pass under either tie order.
- [VERIFIED] Recovered fraction: (0.5923−0.1665)/(0.6516−0.1665) = 0.8777 aggregate (0.8751 on cluster
  means) ≈ 0.88 as stated.
- [VERIFIED] Safety-clause arithmetic on summary counts: timeouts 0 everywhere; truncated ≤ 209 (=full+1,
  arms 54–208); degenerate ≤ 241 (arms 54–222); invalid = 1 > 0 = full for exactly clf_pinned,
  clf_pinned_echo, role_pinned; checks table, safety.intact=false, and registered_contrasts_pass=false all
  follow. The per-record counts behind this are NOT recountable from the packet.
- [MINOR] summary.json wart: full_run_allowed_by_preflight=false is computed against the superseded 12-GPU-h
  cap (realized 75,124 s = 20.87 h ≤ amended 24 h; 82.64 s/conv ✓). Harmless under Amendment 1 but misleading
  to a summary-only reader; "projected_full_gpu_hours" is realized, not projected, hours.

## (2) Invalid outputs and control_impossible — NOT INSPECTABLE (this review's central evidence gap)
- [GAP — must resolve] The packet's invalid-outputs section is []. Either the extraction intended for this
  review is empty (then I simply cannot inspect them), or it asserts the records contain none — which would
  flatly contradict summary.json (1/1/1 vs full 0) and the checks table. The entire registered verdict pivots
  on these three events. Required follow-up: export the three invalid records (conversation key, arm, raw
  text) and the harness's invalid predicate. I could not verify which conversations they are, what the text
  is, whether "invalid" matches the registered/harness definition (that definition is not in the Leg B
  excerpt I received), or whether all three breaches are the same underlying conversation across the three
  pinned arms (identical context ids at the last turn make that plausible; it would not change the clause
  arithmetic, but it changes interpretation: one pathological conversation vs three independent events).
- [NOTED] control_impossible: 5 keys, two sharing base id 334 (334:1:en, 334:5:en) — derived items from one
  source treated as separate clusters; likely more such pairs among 909. Conversation-level cluster
  robustness then slightly understates dependence for all contrasts — immaterial to C1 (+26.8) and C3
  (+18.5); C2 fails regardless. The *reason* exact-column matching failed for these 5 is not stated in the
  packet; the exclusion from C1 is disclosed, n=5/904 cannot move a contrast whose LB is +24.7, and no
  materiality concern arises.
- [MINOR] The control_impossible exclusion rule is not visible in the Leg B registered excerpt I received
  (contrast Leg A's explicit fail-closed rule). Disclosed in summary.json; acceptable — the OUTCOME section
  should have restated it.

## (3) Application of the registered outcome rules — CORRECT; two two-way readings examined and rejected
- [CORRECT] The safety clause is literal: "invalid <= full. Any arm breaching safety fails its contrasts
  regardless of pass counts." 1 > 0 for the three pinned arms kills C1, C2, C3 as registered (C2 also fails
  outright: −3.5 pts, p_one_sided ≈ 1). NOT SUPPORTED is the only registered-consistent verdict, and the
  refusal to change the clause retroactively is the integrity-critical call — doubly so because Amendment 1
  recorded, pre-run, that a zero-full category makes the integer clause vacuous-fail-prone ("full 0/0/0/0…
  so every other arm fails… the clause is applied to the 909 counts, unchanged"). The risk was knowingly
  registered; it cannot now be renegotiated.
- [TWO-WAY, resolved] (a) Treating a one-event breach on a vacuous zero baseline as non-failing — rejected,
  contradicts the text. (b) Invoking "C2 fails alone" as a registered consequence (role rule registered as
  the selector) — rejected as a *registered* consequence because C1/C3 also fail as registered, so "fails
  alone" is not satisfied; the orchestrator's "applies descriptively" is the calibrated reading.
- [CORRECT] Disclosure discipline: C1/C3 substance and the 0.88 recovery sit under DISCLOSED, NOT CLAIMED;
  the safety breach is stated numerically; no retroactive clause change.
- [MINOR completeness gaps]
  1. The registered "reported, not gated" descriptive clf_pinned_echo vs full (−6.2 pts, LB −8.2 — echo
     significantly BELOW full, unlike the dev probe where echo matched the full point estimate) is absent
     from the OUTCOME narrative though present in summary.json. It is the one descriptive unfavorable to the
     echo mechanism; repair in the ledger.
  2. "Echo tokens added" and "columns per arm" were registered reportables; they are not in the packet's
     summary, so I cannot confirm they were reported.
  3. The C1/C3-fail branch's forward guard ("classifier NOT iterated on Multi-IF results") and the status of
     the no-contact family (the outcome rules attach its registration to ADVANCE) are not restated; nothing
     proposed violates them, but the ledger should say both explicitly.

## (4) Quoting 153/909 — disclosed substance survives; interpretation notes
- [CONSISTENT] Quoting = 0 on every non-echo arm → the metric is measuring ledger-copy specifically ✓;
  reported-not-gated status honored ✓.
- [BOUNDED] C1 cannot be explained by copying: even the impossible extreme (all 153 quoting conversations'
  echo passes are pure artifact, control = 0 on every one) removes at most (153/904)×100 ≈ 16.9 pts of a
  +26.8-pt contrast. For C3 the same absolute worst case (max 16.8 pts) leaves the point estimate positive
  (18.5) but strictly exceeds the LB (16.7) — stated for completeness only: that extreme requires every
  quoting conversation to score 100% with full≈0, ludicrous against a 65% full rate, and copying the ledger
  does not by itself satisfy aged output-format constraints. Practical risk to both contrasts: negligible.
- [INTERPRETATION] The real effect is on the mechanism story: echo's recovery is partly
  transcription-assisted ("read the ledger back"), and echo lands 6 pts below full here (probe had echo at
  the full point estimate); quoting/ledger-derail is a plausible contributor — untestable from the packet
  (quoting × degenerate(222) cross-tab unavailable). Verdict impact: none (safety-driven); C2 impact: none
  (role_pinned, quoting 0, is still the best non-full arm at 0.605, above echo's 0.592 with zero echo tokens).

## (5) Model card and next registration
- [MODEL CARD] The registered verbatim lineage lines remain accurate. Add the outcome plainly and do not
  claim any Multi-IF retention benefit: learned selection UNDERPERFORMED the parameter-free recency-clipped
  role rule at equal columns (−3.5 pts, LB −4.8); echo-ledger recovered ~88% of the eviction gap vs matched
  random columns as disclosed substance; the registered Leg B claim is NOT SUPPORTED (one invalid output per
  pinned arm vs zero for full).
- [RE-RUN — recommendation] Do NOT re-generate: greedy decoding, frozen artifacts, identical context ids → a
  re-run reproduces near-identical text for ~21 GPU-h, and Leg A already runs under the +1 clause on BFCL.
  A verdict-flipping registration written after outcomes are known is post-hoc in spirit; the single
  laundering fact available is that invalid ≤ full+1 was registered for Leg A on 2026-09-03 — before this
  outcome, for the documented vacuity reason — so the clause was not invented to rescue Leg B. If the program
  wants the C1/C3 claim-label (mechanism validity), the defensible instrument is a RE-ADJUDICATION
  registration, not a re-run: same records with record-level hashes pinned, only the safety integers changed
  to Leg A's clause verbatim, the three invalid outputs exported for review, and an explicit statement that
  the C2 consequence is unchanged. Default: skip it — no pending decision depends on the label.
- [C2 → program] Settled and unrescuable by any safety clause: even the optimistic cluster bound is negative.
  The classifier's case now rests entirely on dialogue styles where the role prior is weak — tool traces and
  function-call turns, i.e., exactly Leg A's BFCL with its recency comparators. Role rule becomes the default
  selector for chat-style compaction. No classifier iteration from Multi-IF results (registered guard stands).

## (6) Leakage / lineage
- [OK] Ordering fix: INVALID-ORDERING run retained at 145/909; Amendment 2 registered before corrected-run
  outcomes were viewed; arms/contrasts/threshold/artifacts unchanged. Small residual: the packet does not
  state whether the partial 145/909 outcomes were viewed before Amendment 2 — the fix is correctness-only, so
  risk is low.
- [MAJOR — documentation gap] Amendment 2 names the corrected artifact results/qwen/multiif-evict-909-prequery;
  the outcome artifact is …-prequery-V2. Nothing in the packet explains the suffix (restart? re-score?
  carry-over?). Required in WORKLOG/ledger: what changed between -prequery and -v2, whether records were
  carried over or regenerated, and whether anything in -prequery was viewed before -v2 launched. Given
  "records are never deleted and are resumable," an innocent explanation is likely — but it must be on the
  record before this run is cited.
- [NOT VERIFIABLE from packet] Harness code hash vs registration; classifier artifact sha256 match
  (head.pt 191b3372…, model.safetensors 22328135…, tokenizer.json 56827b4e…) — asserted by the brief, not
  checked. Sealed-IFEval non-contact stands (untouched; nothing in the packet references it).
- [OK] Benchmark-contact framing: Multi-IF is registered as a development benchmark and the outcome reading
  does not use "zero-shot" ✓; the model-card lineage sentence remains true of this run.

VERDICT: CONFIRMED-WITH-QUALIFICATIONS
```