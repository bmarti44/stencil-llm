# Focus synthesis review — kimi-k3 (2026-09-05)

# Accuracy review — gpt-6-astra synthesis of checks 31–36

**Reviewer scope/disclaimer (what I could not check):** I have no shell and did not recompute anything from raw records. I relied on the pasted queue items 31–36 and fable's CPU audits of 34 (bookkeeping verified) and 35 (bookkeeping verified). **No accuracy review of check 33 or check 36 was pasted, and the synthesis's Sources list reviews for 31/32/34/35 only** — so the decisive check-36 numbers are attested in the queue item but not, from my material, independently audited. I also could not verify: which check-36 arms R2/R3/R4 actually are (the synthesis asserts R2 = downstream recompute, R3 = full text rebuild, R4 = release+recompute; the pasted item gives counts but not arm identities); the "not bitwise-identical caches" parenthetical; the descriptor "averaged four-column suffix packets"; check 31 probe accuracies; the referent of "pin+echo"; power of the 256-episode design; realism of the GPU-hour estimates; adequacy of SC1 primitives.

## (1) Is the one-paragraph finding supported by the numbers?

Mostly yes. Verified against the pasted record:

- Check 36 old-position SWITCH 2/32 (R2, R3), identical R2/R3 outputs, text bar 27/32 (check 35 TEXT), release+recompute 17/32 → BACK 14/32 exact, 5/32 strict (R4) — **all match** the queue item.
- Check 35 copies 25–28/32 after eviction (fable: S2 25, S5 26, S3 27/28, S4 27/26), 32/32 TEXT-clear impositions (fable F5), "some sorting returned" (residual impositions 3–6/32), intact-A control 27 → 17 after second deletion (queue S4; fable F4 writes "28 → 17" once, but 27 matches the queue's 27/32 SWITCH count — synthesis used the queue number, fine).
- Check 34: K-only and V-only 0/64, layers ≥12 sufficing (58/57) — match.
- The ordering claim (current instruction > own demonstrations > old-position standing instruction) is directly supported by check 34's 60/64 current-cue-after-three-turns result and checks 35/36's failure-at-old-position pattern, and it is **properly scoped** ("role/wording were not isolated from position, attention not measured").

**Finding (low): "despite readable task identity" overgeneralizes check 32.** Per fable's check-32 review (quoted in the queue), the packets encoded "instruction present," *not which* instruction — i.e., check 32's failure was arguably absent identity, not control-despite-identity. The qualifier holds cleanly for check 33 (fit separates 128 pairs/layer) and is unverifiable for check 31's probes from my paste. Not load-bearing, but factually imprecise as written.

**Finding (low): "supplied SET and behavioral HOLD without reapplication" omits the retained-arm asymmetry.** HOLD was 32/32 (ascending) but 23/32 (descending), with retained joint only 3/32 and 5/32. The paragraph does separately say "reliable combined control remains unproved," which covers the joint weakness, but the HOLD clause reads rosier than the data.

**Not checkable, not counted against:** "not bitwise-identical caches" and the R-arm identity mapping (see reviewer scope). If check 36's README says otherwise, this upgrades.

## (2) Novelty honesty

No findings. This is the strongest part of the synthesis. Folklore (recency, restatement, few-shot imitation) is explicitly conceded; the claimed novelty is correctly framed as "measured in this record, not literature priority"; and the one over-claimable slogan — "eviction beats text at CLEAR" — is pre-emptively restricted to the exact reminder tested, with fable's F5 objection (history editing/re-prefill, explicit cancellation, explicit default request were not beaten) converted into required arms of the larger test. The Miller/oscillator disclaimer and the "other representations remain possible" hedge match the evidence. Honest throughout.

## (3) The larger test

**Design logic — sound.** The five-arm structure cleanly tests joint necessity (both vs placement-only tests eviction's added value; both vs eviction-only tests placement's; both vs text-restate tests the strongest folklore alternative). All of fable's demanded stronger alternatives are present: text-restate covers explicit cancellation + explicit default, and the eviction arms in the main comparison *are* text-history editing re-prefilled through the same renderer, which also removes the stale-K/V and malformed-turn explanations. The joint all-five endpoint (with CLEAR and the second neutral request inside it) directly addresses the registered quick-check failure (no arm passed two-request CLEAR). Text-restate's every-request restatement is **deliberately competitor-generous** (it intervenes at every scored request while other arms act only at changes), so a pass is more convincing, not less. Safety gates are real (zero newly broken vs text-restate, collateral fact/unchanged-constraint checks, strict schema), and the 0/256 → 1.16% bound is computed correctly and honestly stated as not-proof. Multi-IF lineage hygiene (evaluation-only, frozen hash-ordered slice, oracle change ID from public instructions only, sealed IFEval/BFCL untouched, native turn-3 checkers, "synthetic alone is scoped") is exemplary. The native-cue adaptation ("placement" = current recap rather than relocation) is disclosed and justified.

**Ways it could pass without answering the governing question — analyzed:**

1. **(Finding: low–medium) Marginal-eviction whisker.** The ≥5-point practical gate applies only to the text-restate contrast; both vs placement-only and both vs eviction-only need only be "positive/significant." With n=256, an exact McNemar can reach significance on roughly 10 net discordant episodes (~4 points of joint-endpoint difference). So eviction could pass as a statistically real but practically marginal add-on and still headline "placement+eviction controls what governs." Mitigated by the required paired 95% intervals and per-checkpoint reporting; a one-word pre-commitment fixes it.
2. **Floor/stringency — not a spurious-pass route.** The all-five endpoint is punishing (check 35/36 joints were ≤17/32 for the best analog); it risks an underpowered null, not a false positive. Acceptable; failure-to-pass is itself informative under the pre-registered interpretations.
3. **Oracle scope map** means the claim earned is "with oracle-managed placement+eviction" — disclosed in-line ("tests control, not autonomous detection"). Closed by scoping, and Multi-IF cannot inflate the main claim because it is downstream-gated and evaluation-only.

**Repair pre-check — sound, two small notes.** Pre-selecting placeholder replacement with a stop-don't-promote gate is good anti-cherry-picking, and the gate incorporates the two-request rule that every quick-check arm failed. **(Low)** n=32 gives coarse resolution on "no additional broken episodes," and the ≥26/32 both-neutral bar sits adjacent to one observed c2 value (S2 25/32): a genuinely repaired delete that behaves like S2 could false-stop the study — safe direction, but worth a sentence acknowledging it.

**Process finding (low, conditional):** Under the queue's own rule ("one accuracy review of the RESULT from raw records before the next item"), the decisive check-36 numbers should be confirmed independently reviewed before the CPU freeze; only the 31/32/34/35 reviews are cited. If check36-review exists, this is moot.

**Budget:** 0.5/4/5.5 GPU-h estimates with a hard 12-hour cap and feasibility pilots are consistent with the culture; I could not verify realism from the material.

## (4) Cuts

Sound and internally consistent. Q5's stated precondition ("only after Q2 or Q4 supplies a reliable actuator") is not met — and check 34's actuator is the text prompt's cache by construction (fable F1), so a learned controller over it has no advantage to learn toward. Q6's closure test is reasonably deferred given the synthesis explicitly scopes attention-level mechanism as unmeasured; the synthesis even pre-commits to calling a placement/text tie "prompting," so the cut doesn't smuggle in a mechanism claim. 1.7B (10/32 descending; bar unreachable by construction), cross-model fleets, and SC1 revival are scope cuts; retaining SC1 primitives while leaving its banks alone is coherent. "Cut claims that every transplant route is impossible" matches the paragraph's own hedge. No findings.

---

## VERDICT: **SOUND-WITH-FIXES**

The finding paragraph tracks the numbers with two low-grade imprecisions; novelty handling is exemplary; the test design is the right next step under Brian's rule and closes every pass-without-answering route except a small magnitude gate on the eviction contrasts; cuts are justified. Nothing requires redesign. Fixes are text-level.

### Exact replacement text

**Fix 1 — replace:**
> Checks 31–33 found no useful compact transplantable task state: extracted vectors, averaged four-column suffix K/V packets, and sustained or one-shot coordinate replacement failed to supply control despite readable task identity.

**with:**
> Checks 31–33 found no useful compact transplantable task state: extracted vectors, four-column suffix K/V packets, and sustained or one-shot coordinate replacement all failed to supply control. Where readability was directly measured it was not the bottleneck — check 33's fit separated the task pair at every layer yet induced nothing — but check 32's packets encoded "instruction present" rather than which instruction, so the common failure was zero usable induction, not control despite readable identity. These recipes are closed; other distributed, nonlinear or learned representations remain possible. Checks 32/33 also missed their text-competence eligibility bars.
> *(and delete the now-duplicated "These recipes are closed... eligibility bars." sentences later in the paragraph)*

**Fix 2 — replace:**
> Check 34's actual instruction-cue K/V columns supplied SET and behavioral HOLD without reapplication;

**with:**
> Check 34's actual instruction-cue K/V columns supplied SET (59/60 of 64) and, in the retained arm, behavioral HOLD without reapplication (32/32 ascending, 23/32 descending; retained joint multi-step control only 3/32 and 5/32);

**Fix 3 — replace:**
> Require all three positive/significant and >=5 percentage points over text-restate.

**with:**
> Require all three contrasts positive/significant and >=5 percentage points. A significant but <5-point edge over placement-only or eviction-only is reported as marginal added control and does not carry the headline claim; statistical evidence and practical magnitude are separate gates for every contrast, not only text-restate.

**Fix 4 — append to the Sources line:**
> Checks 33 and 36 accuracy reviews are not cited here; check 36 is the decisive input, so its independent review must be confirmed complete before the CPU freeze.

**Fix 5 (editorial, optional) — replace:**
> invalid/empty/truncated/repetitive outputs are failures, never release.

**with:**
> invalid/empty/truncated/repetitive outputs are failures and no later request can recover the episode.