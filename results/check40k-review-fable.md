# Check 40k accuracy review (fable, one round, 2026-09-06)

Scope: results/quick-checks/check40k/* at commit c0db8623, scripts/focus_check40k.py.
CPU only; Node v22.22.2 re-scoring; no model launch; nothing under data/bench read.

## Verdict

R3 HARM is correctly applied and every number in the README reproduces. The
regression is real, is not a scoring artifact, and is not truncation or broken
output. The claim boundary should be narrowed in one direction (specificity) and
sharpened in another (mechanism). Park the actuator line; do not spend the
30 GPU-min dose screen (reasoning in section 5).

## 1. Verification from records (all PASS)

| Item | Method | Result |
|---|---|---|
| Hidden tests deterministic | Independent script re-ran the committed NODE harness on all 136 records, twice each, via `base.extract_code` | 0/136 mismatches vs stored `score.tests`; 0 nondeterministic; recount text 16 / bias 7 / shuffled 11 / OFF 7 |
| Hidden tests fair | Read all 13 discordant task specs against their 4 tests; scanned prompts for Date/random; reference passes 160/160; no task fails only on the `__proto__` case; `no_mutation` triggers only on the two prompts that say "mutat" and the failing replies there really mutate | Specs are terse but fully determine the tested behaviour; no test contradicts its prompt |
| Bias hash = 40j | `digest_bias` recomputed on check40g/js-control-bias.pt | bda3d63e...cb2, identical to check40j/freeze.json; file sha 5776dfab... identical in both freezes |
| Shuffled control | Each of 48 rows is a valid permutation of 0..127; regenerated from seed 401107 bit-identically; `gather` reproduces shuffled-bias.pt; per-layer sorted values equal; 0 rows unchanged | Multiset exactly preserved. Per-layer float32 norms differ by <= 4.8e-7 (reduction order only; equal in float64). README's "exactly preserves ... norm" is true in exact arithmetic; nit only |
| Arm rotation | For eval task k, record ids 8+4k..11+4k carry arms ARMS[k%4:]+ARMS[:k%4] and task id k | 32/32 correct; success by rotation slot shows no position effect (text-only 3,4,5,4; bias 2,1,2,2) |
| Freeze order | git: 28869719 (10:13:40) holds tasks/refs/perm/shuffled/script and a stage=recipe freeze; run.log first DEV record at elapsed 393 s after a 382 s load; 4942594d (10:21:31) holds exactly 8 DEV records and stage=evaluation-frozen; eval records begin after that commit in run.log; `git diff 28869719 HEAD` on every recipe file is empty | Recipe committed before inference; eval opened once after the DEV freeze |
| DEV-only calibration | dev-summary-0 = 5/8 on round 0; no calibration-needed/control files; DEV task ids disjoint from the 32 eval ids; prewritten-reading.md is byte-identical to the pre-result README section (diff shows only the appended results) | No evaluation feedback |
| Arithmetic | scipy/comb recompute | two-sided p 0.0224609375, one-sided 0.998291015625, CI [-55.123, +6.226] pp; shuffled p 0.125, CI [-38.900, +12.169]; rate CIs match |

## 2. What the 11 biased regressions actually are

Per-test totals (of 128): text-only 98, shuffled 87, bias 56, OFF 51. Bias replies
switch the fence label to `js` on 26/32 (text-only and shuffled: `javascript` 32/32),
the same presentation shift 40j recorded. None of the 11 losses is truncated or
flagged; all are valid JS. Grouped by the error the biased reply makes:

| Class | Tasks | What happened (bias arm) | Text-only on same task |
|---|---|---|---|
| Calling-convention corruption | weightedSeat, cappedWalk, rowRotations | `function weightedSeat(...weights)` + `arguments[...]`; `cappedWalk(balance,[low,high],deltas)` destructures a number (TypeError x4); `const [len] = row` | Ordinary positional signatures, all correct |
| Generator instead of function | peakShelves, palletNames | `function*` with `yield`; returns a generator object, serialised as `{}`, 0/4 | Plain function, 4/4 (shuffled reply is byte-identical to text-only on peakShelves) |
| Minified/obfuscated style with wrong logic | serialNext, rangeBadges | Single-letter names (`e,t,n,r`), nested IIFE, `+t[2]` overflow on the 20-digit case, wrong run detection | Readable code, 4/4 |
| Wrong algorithm | dashTokens, foldParcel | Regex one-liner `split(/-(?=-)/)`; string `.reverse()` TypeError plus unescaping bug | Explicit scanner, 4/4 |
| Off-by-one / spec edge | quietSpans, patchRows | `prev = mark+1` without `max` (negative mark -> interval [-1,0]); `Object.assign` mutates the input row and mis-orders re-created ids | `Math.max(prev, mark+1)`; Map copy, 4/4 |

Seven of the eleven (rows 1-3) carry a signature that never appears in the
text-only or shuffled arms: exotic JavaScript surface constructs (rest parameters,
destructuring, generators, minifier-style naming, regex one-liners). This is the
JS direction over-expressing "JavaScript-ness" at the expense of reading the spec,
not a general loss of reasoning. The two wins (cancelMarks, runInventory) are
ordinary logic fixes with no such markers and look like noise.

## 3. Shuffled arm: dose harm vs JS-specific harm

Shuffled loses 6 / wins 1 (net -5, p = 0.125, not significant at n=32) and drops
11 hidden tests; bias drops 42. Five of the six shuffled losses are also bias
losses (dashTokens, quietSpans, foldParcel, patchRows, rowRotations) and on
quietSpans the two perturbed arms produce the identical off-by-one. So:

- There is a nonspecific dose-harm component: a random same-norm router
  perturbation (Frobenius 15.66, per-layer 0.94-4.76 on all 128 experts of all
  48 layers) knocks out roughly the marginal tasks. That component is a trend,
  not a result, at this n.
- The JS-specific component is the additional six losses (rows 1-3 above), all
  with exotic-JS markers, none shared with shuffled. Direction matters beyond norm.
- Dose-response inside 40k: none; alpha is fixed. The only graded signal is the
  per-test ladder text 98 > shuffled 87 > bias 56, which orders perturbations by
  "how JS-aligned", not by dose. Cross-check history: 40c's language dose curve
  (alpha 2: 25/32 JS, alpha 3: 32/32, alpha 4: 26/32 with 6 broken) was measured
  on the toy screen with no competence endpoint, and 40d showed the committed
  alpha-2 tensor (check40c/selected-bias.pt, exactly bias/1.5) induces JS on only
  6/32 of a fresh bank. So a lower dose is not "uncertified": alpha 2 is committed
  and is already known to be a weak actuator on its own.

## 4. Claim boundary

"Actuator harms task competence at the certified dose" is defensible but should
read: **at alpha 3, adding the frozen JS router bias on top of the rendered rule
reduced hidden-test task success 16 -> 7 of 32 (exact sign p = .022); the harm
is expressed as drift toward exotic JavaScript constructs and spec misreading;
a same-norm shuffled bias also trends downward (16 -> 11, n.s.), so the split
between JS-specific and nonspecific dose harm is not established.** Note also
that text+bias equals OFF on JS-task success (7/32 each, 4 discordant each way):
with the bias on, the model does no better than with no rule at all. Keep the
existing limits (this model, tensor, schedule, authored family; conservative CI
includes zero; not population harm).

## 5. Is the alpha 1 / 1.5 / 2 screen worth it?

No. Brian's question is whether bias-on-top-of-text makes the model better at
the task. The prior for "yes" at a lower dose is low on three independent lines:
40j found zero additivity at n=16 (all ties), 40k finds harm at alpha 3 and a
downward trend even for a random direction, and alpha 2 alone barely induces
language on a fresh bank (40d). Lowering the dose shrinks the perturbation, so
the expected outcome of the screen is more ties, i.e. R2 "no benefit" - the
decision 40j already registered. A screen whose likely readings are "no benefit"
or "smaller harm" cannot change the shipping decision, and at n=32 it cannot
demonstrate harmlessness either (paired CI half-width ~24 pp). Under the
quick-test rule the hypothesis does not rank: park the actuator line. The one
scientific residue worth a line in the ledger, not a GPU run, is the mechanism
note in section 2 (JS direction => exotic-JS style drift), which is the first
concrete description of what the router direction does beyond the fence label.

## 6. Nits (no severity)

- README "exactly preserves ... norm": float32 per-layer norms differ by <=4.8e-7
  from reduction order; multiset is exact. Wording fine, but "multiset (and
  therefore norm)" is the precise statement.
- `no_mutation = "mutat" in prompt` is a substring switch; it happens to select
  exactly the two intended tasks here but would silently include any future
  prompt mentioning "mutation" descriptively.
- The R3-before-R2 ordering was fixed prewritten and was needed here (2-11 also
  satisfies literal R2); good that it was recorded before outcomes.
