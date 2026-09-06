# Check 43 accuracy review (fable, one round)

Scope: commit e7c1680b, `results/quick-checks/check43/` (README, profiles.pt,
profiles/*.pt, grid.json, summary.json, audit-details.json, records.jsonl,
banks.json, unhooked-replay.json), `scripts/focus_check43.py`, design source
`results/neuron-granularity-research-astra.md` items 3-6. CPU only; no model
launch; no sealed benchmark file read. All numbers below recomputed from the
raw artifacts.

## Verdict in one line

The FAIL / NO SAFE SET reading is correct as a measurement, the checker and
statistic are sound, but the null is a **dose-scale artifact**, not evidence
that routing does not carry the operation: the SUM/PRODUCT direction is 7.2x
smaller than the 40b/40c language direction, the un-normalized alpha grid
never reached the dose range where 40c flipped language, and a sign flip of
the bias changed the generated tokens on 1 of 24 prompt pairs.

## What was verified

1. **Profile statistic.** `focus_check43.py` lines ~1350-1390: positions =
   the four tokens immediately before the user turn's `<|im_end|>`
   (`stop-4 .. stop-1`); per-donor `.pt` files record `positions=[127..130]`
   and `neutral_token_ids=[279,4583,729,13]` (" the complete function.") for
   all 32 donors, `count=4`; per-example mean = sums/4; operation mean =
   mean over 16 examples (equal weight per example, as designed). `b =
   (mean_SUM - mean_PRODUCT)/2`, expert-wise centered, zeroed outside layers
   7-34. Recomputed Frobenius norm 0.7224128 matches the README.
2. **Bias application.** Every grid record carries a `bias_sha256` that
   differs by sign and by alpha (f24c/e432, 24c5/fcff, 30a6/fb39), and
   `audit-details.json` reports all bias hashes verified and zero consumer
   mismatches. Changed top-8 sets are confined to layers 7-34. Per-layer
   changed-route fraction (recomputed from `dispatch` in records) in the band:
   alpha 1 ~5% of layer-token observations (14-17% at layers 7-9, 4-8% at
   layers 20-34); alpha 2 ~10%; alpha 3 ~14% (37-44% at layers 7-9, 15-23%
   deeper). Mixture-weight L1 change per token in the band is 0.01-0.04
   (alpha 1) to 0.04-0.12 (alpha 3): the flipped routes are marginal 8th/9th
   swaps carrying little mixture weight.
3. **Magnitude versus the 40b/40c language direction.**
   - Unit direction (alpha = 1) Frobenius: check43 0.722 (band only) vs
     40b/40c 5.22 (all 48 layers; 40b frozen alpha-4 bias 20.88, 40c
     selected alpha-2 bias 10.44). Ratio 7.2x. Same `/2` convention in both
     (40b uses "language mean minus two-language mean"), so this is a real
     magnitude gap, not a convention artifact.
   - Restricted to layers 7-34: 40c alpha-2 band norm 6.81 vs check43
     alpha-3 2.17 (3.1x smaller); vs 40c alpha-3 (the 32/32 JS cell) 4.7x
     smaller. Per-layer 40c-unit/43-unit norm ratio ranges 5.4x to 23.7x.
   - Largest per-expert logit shift at alpha 3: 0.29 (layer 8), band mean of
     per-layer maxima 0.11, versus 0.52 for the 40c selected bias. Router
     logit spread across experts at these positions is ~0.7 (std), so alpha-3
     shifts are roughly 0.15 std.
   - The astra design fixed alpha = {1,2,3} in absolute units with no
     norm-matching to the prior actuator (grep for norm/scale/match in the
     design finds none). So the grid was calibrated to nothing.
   - A second, structural reason for the gap: 40b/40c pooled router logits
     over **generated code tokens** (where the language is manifest in every
     token); check43 pooled over four **neutral prompt tokens** where the
     operation is only latent. Different statistic, different scale.
4. **Direction reliability (is b signal or noise?).** From the 32 per-donor
   means, 16 paired SUM-minus-PRODUCT differences: mean-diff norm per band
   layer 0.18-0.46 versus per-example diff norm 0.34-0.52 and between-task
   std within one operation 0.03 (per expert); 25-92 of 128 experts per band
   layer have |t| > 3 (16 pairs). Leave-one-out cosine between a held-out
   pair's centered diff and the direction from the other 15 is positive on
   16/16 folds in every band layer (mean 0.89 at layer 7 falling to ~0.45 at
   layers 30-34; minimum 0.05). The direction is real and consistent; the
   null is not from a noisy profile.
5. **OFF default and the informative sign.** No neutral-prompt OFF generation
   exists in the records (the OFF/shuffle/text controls were scheduled after
   dose selection and were skipped). The "OFF equals unhooked" parity is the
   text-SUM pilot replayed with hooks closed (58 identical tokens,
   `unhooked-replay.json`), not a neutral OFF run. The default operation is
   inferred: at alpha 1 the + and - arms produced identical token sequences
   on 8/8 prompts (23/24 pairs across all doses; the one alpha-3 difference
   is a loop-bound rewrite, both SUM), all 48 grid outputs contain `acc = 0`
   and none contain `*=`. So the neutral prompt defaults to SUM and only the
   -b (PRODUCT) sign was informative. The README should say the OFF default
   is inferred, not measured.
6. **Checker.** Independent native-Python execution of all 81 recorded code
   strings on the recorded inputs with the script's family semantics
   (`whole`, `prefix=[:hi]`, `suffix=[lo:]`, `slice=[lo:hi]`) reproduces the
   recorded SUM/PRODUCT verdicts 81/81. Each setup task has 32-38 of 43
   inputs on which SUM and PRODUCT differ. The 1/8 "other" output
   (setup-Python-7) is a genuine off-by-one (`min(7, len)` for hi=6),
   identical across all six arms, so it is a model competence quirk, not a
   bias effect.
7. **Partial PRODUCT effect.** None observable: no `*=`, no `acc = 1`, no
   token-sequence divergence attributable to sign. Records store dispatch
   counts only (no router logits, no next-token logits), so a sub-threshold
   shift toward PRODUCT-cued experts cannot be checked from the artifacts.
   This is a gap in the instrumentation, not a finding either way.
8. **Where the operation is decided.** In the 16 donor pairs, SUM and
   PRODUCT generations first diverge at generated index 21 on 15/16 (18 on
   one): that is the identity literal token `0` (id 15) vs `1` (id 16) after
   `acc = `, not the operator token. The operator (`+=` / `*=`) comes later
   and is already conditioned on the identity choice. Any follow-up profiling
   at generated positions should target the identity-literal position (and
   the tokens leading to it), with the operator as a secondary position.

## Answers to the three questions

(a) **Is the null real?** Yes, as stated in the README's narrow scope: with
this direction, this band, and doses 1-3, nothing moved. The measurement is
clean (checker verified, bias applied, routes changed, no truncation).

(b) **Artifact or evidence?** Artifact of dose scale, with a statistic-choice
contributor. Alpha 3 delivered ~0.11 logits of per-expert shift and 14%
marginal top-8 swaps; 40c needed ~0.5 logits and its alpha-3 cell to get
32/32. Both signs of the bias yielding byte-identical outputs on 23/24 pairs
is the signature of a perturbation below the model's decision threshold, not
of a decision made elsewhere. The positions are defensible (the direction is
reliable there), but they are also where the operation is weakest; the
generated identity-literal position is where it is decided. Nothing here
supports "routing does not carry the operation".

(c) **Cheapest follow-up.** One GPU run, roughly 12 minutes (6.5 min load,
~1 min teacher-forced profiling, ~3 min for 48 generations): teacher-force
the 32 existing donor outputs (already in records.jsonl), capture router
logits at all generated non-EOS tokens (the 40c statistic) and separately at
the identity-literal position; build b the same way; **norm-match** the dose
to the 40c band (scale the band Frobenius to ~6.8, i.e. about 9x the current
unit b for the prompt-tail direction, or grid alpha over the generated-token
direction at 40c's {2,3}); keep the paired-success rule but add the 40c
breakage gate (malformed <= 1/8 per sign) instead of zero. Run -b only if
budget is tight (the +b sign is redundant given the SUM default). If that
run also gives 0/8 PRODUCT with any breakage, close concept-level routing at
this actuator; do not close it on check 43.

## Minor README corrections

- "OFF equals the unhooked consumer" is verified for the text-SUM pilot
  only; no neutral OFF generation was made. State the SUM default as
  inferred from the alpha-1 sign-identity.
- Add the magnitude context: unit-direction norm 0.72 vs 5.22 for the
  language direction; alpha-3 band norm 2.17 vs 40c alpha-2 band norm 6.81.
  Without it the table reads as a decisive null.
- "The actuator did change routing" should carry the mixture-weight L1 per
  token (0.01-0.12) so readers see the changes were marginal swaps.

**Correction (astra full review, 2026-09-05)**: (F4) This grid did not induce PRODUCT. Its smaller perturbation leaves under-dosing as an untested explanation; concept control remains open. No neutral OFF operation was measured in check43: the saved OFF replay is a text-SUM pilot. Equal global norms do not establish equal decision-site sensitivity or show that a larger dose would work.
