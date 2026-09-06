# Check 40l accuracy review (fable, one round, 2026-09-06)

Scope: results/quick-checks/check40l/* at commit 85595392, scripts/focus_check40l.py,
context check40k and results/check40k-review-fable.md. CPU only; Node v22.22.2
re-scoring; no model launch; nothing under data/bench read. Working scripts kept in
the session scratchpad, not the repo.

## Verdict

(1) R4 INCONCLUSIVE is correctly applied and every number reproduces.
(2) The claim boundary must be narrower than the R3 sentence: 40l did not test a
"correct" bias. The dev-derived direction has no out-of-sample competence validity
even on its own 24 DEV replies and is mostly a reply-length direction (section 3).
(3) CLOSE the router-bias line operationally, with the narrowed claim in section 5;
do not adopt "does not improve ... magnitude harms" as a universal.

## 1. Verification from records (all PASS)

| Item | Method | Result |
|---|---|---|
| Harness audit | `./.venv/bin/python scripts/focus_check40l.py audit` | PASS; paired.json/audit.json rewritten byte-identically (git status clean) |
| Baseline reuse | 40l/baseline-records.jsonl vs 40k records (phase eval, arm text-only) | 32/32 identical apart from the added `source` field; every path in the 40k freeze `scripts/` set has an unchanged sha in HEAD; `git diff aa1fa772 HEAD` on all 23 frozen files is empty; runtime.json keys asserted equal in-run; kernel relative_error 0.0 |
| DEV reproduction | 8 prior DEV tasks: 40k record vs 40l record | 8/8 identical input token ids, generated token ids and text; same pass/fail |
| Hidden tests | Independent script re-ran the committed NODE harness twice on all 152 records (24 DEV + 96 eval + 32 baseline) via `base.extract_code` | 0/152 mismatches vs stored `score.tests`; 0 nondeterministic; recount 16 / 14 / 13 / 15; per-test totals of 128: text 98, comp-1/3 91, comp-2/3 92, shuffled 99 |
| DEV bank | dev-tasks.json | 24 ids, disjoint from the 32 eval ids; all >= 4 tests; no Date/random in prompts; references pass 96/96 (audit); the 16 new `l*` prompts are shorter (219 chars mean vs 355 for the old 8, 342 eval) but pass rate is 5/8 in both halves |
| Profile | Re-read all 24 profiles/*.pt (bf16 [48,n,128]); float64 across-expert centring; token mean per reply; pass mean minus fail mean | reply_means and passed equal the stored tensors; direction equal to 3.3e-16 (stored path re-centres once more, a no-op); rows sum to 5.6e-15; per-layer direction norms 0.41-1.98 |
| Norm matching | Per-layer norms vs 40g alpha-3 tensor | max relative deviation 1.7e-8 at 1/3 and 2/3; Frobenius 5.2199 / 10.4397 / 10.4397 vs target 15.6596; bf16 cast in the harness changes the Frobenius norm by 7e-5 |
| Shuffled control | seed 401207, 48 x randperm(128) | Regenerated bit-identically; 48 valid permutations, 0 rows unchanged, 44 fixed points of 6144; `gather` reproduces the shuffled tensor; cos(high, shuffled) = -0.02 |
| Freeze order | git log; run.log | aa1fa772 11:04:12 registers script/banks/refs/reading (stage=recipe); README at that commit == prewritten-reading.md; 74086c43 11:13:39 holds exactly 24 DEV records + profile + stage=profile-frozen; run.log line 26 is that commit and the first eval record (n=25) follows at line 60; 85595392 11:28:30 completes. Final README = results + prewritten text verbatim |
| Arm rotation | eval record 24+3k.. carries ARMS[k%3:]+ARMS[:k%3] with task k | 32/32; success by slot comp-1/3 5,4,5; comp-2/3 7,4,2; shuffled 4,6,5 (no position effect) |
| Arithmetic | scipy binomtest + beta quantiles; Bonferroni union of two 97.5% CP intervals (j.cp(., n, 0.025)) | one-sided p .9375 / .91015625 / .875; two-sided .625 / .5078125 / 1; difference CIs [-27.342,+16.825], [-37.421,+21.207], [-23.031,+17.814] pp; rate CIs match README |
| Reading | qualifies(): R1 needs w-l>=5, l<=2, p<=.05 (none); R3 needs l-w>=3 on both doses (1/3 gives 2) | R4 is the only consistent reading; the conservative-reading choice (R1 before R3) was fixed prewritten |
| Budget | summary.json | 1345.2 s of 2700; RUNNING.flag absent |

## 2. What the perturbations did

- Discordant tasks: comp-1/3 win noteLinks; losses dashTokens, quietSpans, softWrap.
  comp-2/3 wins noteLinks, nestDepths, runInventory; losses quietSpans, foldParcel,
  serialNext, softWrap, rowRotations, rebaseClock. Shuffled win nestDepths; losses
  quietSpans, patchRows.
- Losses are ordinary logic slips, not the exotic-JS drift of 40k: `[prefix, suffix] =
  match` dropping match[0] (serialNext), `new Date(...)` for a modular clock
  (rebaseClock), a spurious empty-word branch (softWrap). Style markers are flat across
  arms (generators 0/0/0/0, rest params 2/2/2/2, arrows 6/8/8/7); fence label is
  `javascript` on 32/32/31/32. The competence direction is essentially orthogonal to the
  JS tensor: cosine 0.065 global, per-layer -0.14..0.35.
- Fragility, not direction: across the seven perturbed or unperturbed arms of 40k+40l,
  19 of 32 tasks are discordant somewhere; quietSpans fails under all six perturbations,
  and 5 of the 6 comp-2/3 losses were also 40k bias-arm losses. The same-norm shuffled
  arm sits at 15/32. At Frobenius 10.4 the outcome is dominated by "which marginal task
  tips", not by direction.
- Output length: comp arms are ~5% shorter (4415/4414 vs 4630 tokens; shorter on 14 and
  17 of 32 tasks vs 8 and 7 longer); shuffled is neutral (4613; 10 vs 11). This is the
  direction's main measurable effect (next section).

## 3. Is the dev-derived direction a fair proxy for a "correct" bias? No.

Quantified on the 24 DEV replies that define it:

- Length confound. Passing replies average 109 tokens, failing 150. The direction's
  cosine with the short-minus-long direction (median split of the same 24 reply means)
  is 0.84; corr(reply length, projection on the direction) is -0.64 in-sample and -0.69
  leave-one-out. Most of what "competence" encodes here is "short reply".
- No out-of-sample validity. Leave-one-out projection separates pass from fail with
  AUC 0.67 and sign-threshold accuracy 62.5%, which is exactly the 15/24 base rate.
  In-sample it separates (58.3 vs -18.5) because the direction was fitted to those
  labels. 9 failing replies over 48x128 dims cannot estimate a competence direction.
- Pooling sensitivity: the equal-reply direction has cosine only 0.89 with the
  token-weighted (40b-style) alternative, so the estimate is itself unstable.
- Task confound: the old-8 minus new-16 direction has cosine 0.55 with the competence
  direction, although both halves pass at 5/8; the DEV bank mixes two authored styles.
- Magnitude: the comp-2/3 per-expert RMS is 0.06-0.28 per layer against a centred
  router-logit spread of ~1.4 (per-layer 0.9-2.5). The bias moves only near-tied
  routing decisions; that is where a random direction (shuffled) also lands.

So 40l tested a noisy, length-aligned, unvalidated direction. Its null result says
nothing about a bias that is actually correct; the prewritten text says as much, and
the R3 sentence, had it fired, would have over-claimed.

What a "correct" bias could even be on a token-local router: a constant additive vector
per layer, applied at every position, shifts expert choice only where the trained
router's top-k margin is smaller than the bias contrast. It cannot condition on the
token. Its best case is a global re-weighting that corrects a systematic routing
miscalibration for this task family. The only evidence that such a miscalibration
exists would be a direction that predicts pass/fail out of sample; the one we built
does not (AUC 0.67, accuracy = base rate). A genuinely oracle bias would have to be
fitted against hundreds of held-out authored tasks (never benchmarks), and its
admissible norm is bounded above by the window where random same-norm directions are
harmless (roughly <= 10.4 here; a random direction at 15.7 trends -5 net in 40k). That
is a fitting program, not a quick test, and its expected payoff is small: at n=32 the
paired CI half-width is ~24 pp, and the model's own rendered rule already reaches the
text-only level that every perturbation only nudges.

## 4. Totality of evidence on the router-bias line

| Check | Direction / norm | Competence outcome vs text-only |
|---|---|---|
| 40j (n=16) | JS alpha 3 (15.66) | 0 wins / 0 losses / 16 ties; rendering suffices |
| 40k (n=32) | JS alpha 3 | 16 -> 7, 2 wins / 11 losses, two-sided p = .022; exotic-JS drift |
| 40k shuffled | random, norm 15.66 | 16 -> 11, 1 / 6, p = .125 (trend) |
| 40l 1/3 | dev competence, 5.22 | 16 -> 14, 1 / 3, n.s. |
| 40l 2/3 | dev competence, 10.44 | 16 -> 13, 3 / 6, n.s. |
| 40l shuffled | random, 10.44 | 16 -> 15, 1 / 2, n.s. |
| 43b | concept-routing recipe, norms 6.8/10.2 | PRODUCT 0/8 at both norms while 63-78% of decode routes changed |

No tested constant router bias improved task competence; the one significant result is
harm from the certified JS direction at alpha 3; every other contrast is a null with wide
intervals. 43b adds that large route changes do not induce the target concept.

## 5. Claim boundary and decision

Do not write "router-logit bias does not improve task competence beyond a rendered
rule on this trunk; magnitude harms" as stated. Supportable wording:

**On Qwen3-30B-A3B bf16 with the check40 hooks, no tested constant router-logit bias
improved hidden-test task success over the rendered JavaScript rule: JS alpha-3 tensor
(40j n=16 all ties; 40k 16 -> 7 of 32, p = .022, harm), a 24-reply dev-derived
competence direction at 1/3 and 2/3 of that norm (16 -> 14 and 13, n.s.), and random
same-norm directions (16 -> 11 and 15, n.s.). Magnitude harm is demonstrated only for
the alpha-3 JS direction; the same-norm random trend is not significant. Whether a
correctly estimated competence bias exists is untested: the dev direction has no
out-of-sample validity (LOO AUC 0.67, accuracy at base rate) and is 0.84-cosine
aligned with reply length.**

Close vs park: CLOSE. The distinction that matters is not "closed as proven
impossible" but "closed because no cheap test remains". Under the quick-test rule the
remaining hypothesis (an oracle bias) has no positive evidence, no estimator with
out-of-sample validity, a narrow admissible norm window, and would need a multi-hundred
task fitting program to test. Parking implies a pending quick test; there is none.
Record the oracle question as open-and-unfunded in the ledger with the section-3
numbers so a future reopening starts from the confounds, not from another 32-task
screen.

## 6. Nits (no severity)

- "Own positions" profiling captures the router logits produced while consuming each
  generated token, i.e. the routing that produced the next token, not the token itself.
  Registered and consistent; just not "the routing that emitted the passing token".
- The README's "harm below the pre-written bar" is a magnitude statement; the
  prewritten text already says non-significance is not harmlessness. Keep both.
- Two competence contrasts plus the 40k second look on the same 32 tasks: the exact
  p-values are unadjusted and the README says so; fine for an exploratory screen.
- 44 of 6144 permutation entries are fixed points (expected 48); harmless.
