# Check 40b review — fable (one round, accuracy)

Reviewed at commit dbbe9fb7. CPU only; no model launch; no repo edits other than
this file. Sealed inputs under data/bench and BFCL cohorts were not read.

## What I verified from raw artifacts

1. **Parsers re-run.** `base.score` re-executed on all 224 `records.jsonl` texts
   (Python `ast` + `node --check`, node v22.22.2): 0 mismatches against the saved
   scores. Arm totals (correct 26 JS / 6 broken / 25 task-pass; swapped 0 JS /
   29 Py / 3 broken; shuffled 0 JS / 32 Py / 0 broken; OFF 0 JS / 32 Py; text-cue
   32 JS) reproduce. Top-8 overlap recomputed from `profile-statistics.json`:
   mean 0.8073, min 0.5, max 1.0, 48 layers, gate not tripped.
2. **No language cue in recipient prompts.** Input token ids are identical across
   correct/swapped/shuffled/OFF for 32/32 screen tasks and across the four grid
   cells for 8/8 setup tasks. System prompt is language-neutral ("code block
   defining the requested function"). No prompt outside competence/text-cue
   contains python/javascript/js/node/dart/brace/script. Text-cue differs from OFF
   by exactly three inserted tokens `[13, 5443, 12914]` (" Use JavaScript.").
3. **Bias construction and control.** Read `profiles.pt`/`frozen-biases.pt` with
   a numpy-only unpickler. `normal == profiles - mean(profiles,0)` exactly;
   `correct == 4*normal[JS]`, `swapped == 4*normal[Py]`, `shuffled == 4*shuffled[JS]`
   exactly (so correct = 2*(JS-Py), swapped = -correct). Shuffled is a within-layer
   permutation of the same values (verified per layer), per-layer norms equal to
   the correct bias, cosine with correct -0.15..0.23 (mean 0.02): a fair
   matched-norm random-direction control. No normalization or fitting anywhere.
   Profiles: 16 tasks/language, 375 JS and 343 Py generated-token positions,
   token-weighted means; capture slice is the generated tokens' own positions.
   Grid selection rule reproduces (alpha 4 JS: 7 JS/1 broken beats alpha 1: 0/0);
   selection used the 8 grid tasks only, screen empty at freeze
   (`screen_records_at_freeze: 0`). Freeze hashes for both scripts, banks and the
   pre-written reading match the working tree at dbbe9fb7.
4. **Hook semantics (the main thing I chased).** The `.venv` transformers 5.16.1
   that ran the job (WORKLOG launch line; `runtime.json` transformers_version)
   has `Qwen3MoeTopKRouter.forward` return `(router_logits, router_scores,
   router_indices)` with raw logits in slot 0 (softmax goes to a separate
   `router_probs`). The hook adds `bias[layer]` to slot 0 for every row of the
   call (so all prefill positions and every decode step, since `h.bias` is set
   before the prefill forward and cleared only after generation), then
   recomputes `softmax(float32) -> topk(8) -> normalize -> cast`, which is
   exactly the model's own router arithmetic; the consumer takes slots 1 and 2.
   OFF returns the untouched output object (`verify_kernel` asserts identity
   and full-model logit equality with hooks removed vs installed). Note: a stale
   transformers 5.2.0 under `~/.local` returns softmax probabilities in slot 0;
   had the run used it, the bias would have been added to probabilities and the
   re-softmax would have flattened the top-8 weights. It did not. The profile
   means (range -13.3..-2.6, per-layer mean ~ -ln 128, sum exp ~1.0-1.4) are
   consistent with raw logits, not probabilities.
5. **Bias magnitude in context.** Router logits are natively near log-prob scale,
   so alpha-4 bias elements are interpretable in nats: max |elem| 3.72, mean
   0.16, per-layer L2 norm 1.25-6.35 (largest at layers 41, 45, 29, 17). On the
   mean profiles the alpha-4 JS bias replaces 1-6 of the top-8 experts per layer
   (129 replacements over 48 layers on the Python profile, ~2.7/layer). This is
   a moderate, not saturating, perturbation.
6. **Semantic correctness.** I evaluated the returned arithmetic expression of
   every generation against the task expression: 221/224 exact, including all
   32 correct-arm replies (the 4 Dart-style and 2 `->` replies return the right
   expression) and all grid/competence replies. The only 3 semantic failures are
   the 3 swapped-arm Python replies that drop the final `)` before the closing
   fence. Competence is preserved under bias; only surface language moves.
7. **Where the flip happens.** First three generated token ids in the correct arm:
   "```javascript\n" 25/32, "```dart\n" 4/32, bare `solve_screen_N = ` 3/32 (two
   `-> ` replies plus the one parser-valid bare arrow). OFF/swapped/shuffled are
   "```python\n" 32/32; text-cue "```javascript\n" 32/32. The language decision
   is made at the fence-label token, before any Python-specific syntax could be
   generated, so the 26/32 is not a "Python syntax degrades, braces are the
   fallback" artifact.
8. **Cost.** 744.53 s charged = 0.2068 GPU-h, of which 314.04 s load; summed
   generation time 411.4 s for 6,194 tokens = 15.05 tok/s, consistent with
   check40's 16 tok/s conservative figure and the 2,190 s projection. No cap
   overrun, no screen halving.

## Findings

- **F1 (low, disclosure).** README calls the profiles "raw router logits" and
  the hook "router-logit bias" — correct for the executed venv, but the repo
  contains a second transformers (5.2.0, `~/.local`) with the opposite slot-0
  contract. Nothing enforces which one a future rerun imports. Suggest the
  script assert `output[0]` is not a probability vector (e.g. row-sum != 1 or a
  negative element) in `verify_kernel`, or pin the interpreter path.
- **F2 (medium, interpretation).** Correct-arm breakage is task-family
  clustered: 5 of the 6 breaks are in the `screen_2` family `((a-b)-(c+d))`
  (5/10 vs 1/22 elsewhere; hypergeometric P(>=5 of 6 land in a 10-task family)
  = 0.006). The swapped-arm breaks are all in `screen_1` (3/11, P = 0.03). So
  "6/32 broken" is not a homogeneous rate; the dose that is clean on two
  families over-drives on the third. The README reports 6/32 literally, which
  is correct, but the family dependence is material for the next dose choice
  and is not mentioned.
- **F3 (low, interpretation).** The "broken" replies are all C-family
  curly-brace/typed neighbours of JavaScript (Dart `int f() {}`, Java/Kotlin-
  style `() -> expr` lambda), never Python or anything else. Combined with
  26/32 JS at the mode, the direction is best described as "JavaScript-modal
  within a C-family brace region", not a JS-exclusive address. The README's
  "not a claim that Dart-style outputs are invalid in every language" is an
  honest hedge but understates this: the neighbours are informative about what
  the router direction encodes (fence label + brace/typed syntax).
- **F4 (low).** The grid alpha-4 JS cell's task-check 4/8 comes from 3 bare
  `name = () => expr` assignments that the inherited checker rejects (parser
  valid, semantically right). Same limitation hits screen task 26. The checker
  is inherited and frozen, so this is reporting-only, but "coarse task pass"
  under-counts JS by ~1-3 for arrow forms.
- **F5 (info).** Bias is also applied over all prompt positions (prefill).
  Disclosed. It leaves open whether the flip comes from perturbing the reading
  of the request versus steering generation; a decode-only or prefix-only arm
  would separate these (see (c)).
- No finding on cue leakage, control fairness, OFF fidelity, profile statistic,
  selection hygiene, freeze integrity, or cost arithmetic. The audit script's
  claims reproduce.

## Answers

**(a) Is the language flip real and specific?** Yes, real and direction-
specific on this synthetic bank. Same token-identical prompts give Python 32/32
under OFF, matched-norm shuffled and the swapped direction; the JS direction
gives 26/32 parser-valid JavaScript plus 6 C-family neighbours, all 32
semantically correct, decided at the fence-label token. Specificity is to a
brace/C-family region with JS as the mode (F3), and the clean dose window is
narrow and family-dependent (F2). It is a single-shot, single-seed, greedy,
n=32 observation on arithmetic one-liners; MARGINAL is the right label.

**(b) Versus check 41's null.** Check41 (Qwen3-4B dense, MLP neuron gain
scaling, k in {200,500,1000}, gains 0.5-2, retained-history episodes) gave SET
0/64 in every biased arm with text-cue 64/64. Mechanistic differences: (i) the
router bias acts on the model's own discrete decision variable — it swaps whole
expert FFNs (roughly 1-6 of 8 per layer here) rather than rescaling individual
neurons' activations inside a fixed FFN, which the residual stream and later
layers can absorb; (ii) the direction is a mean-difference in the router's own
logit coordinates measured at generated positions, whereas check41's neuron set
was chosen by frequency statistics and then perturbed multiplicatively; (iii)
30B-A3B with 128 experts x 48 layers offers a routing degree of freedom that a
4B dense model lacks; (iv) check40b is single-shot fresh-KV SET only, no
HOLD/SWITCH/CLEAR, so it has not yet met the harder part of check41's design.
The contrast supports "actuate the routing decision, not the activation
magnitude" but does not by itself show neuron scaling could not work at other
doses.

**(c) Single cheapest next test.** Same 32 screen tasks, same frozen JS
direction, three arms at 64-token cap: alpha 2, alpha 3, and alpha 4 applied
only to the first 3 generated tokens (through the fence label) then OFF. 96
generations, ~30 tokens each at 15 tok/s is ~3.5 min decode + load; under 12
GPU-min total. It directly addresses the failed bar (does a dose exist with
JS >= 20 and broken <= 2, and is the family-2 breakage dose-limited) and F5
(is the router bias needed only at the decision point, in which case sustained
bias is what breaks syntax). Pre-write: POSSIBLE-equivalent if any single arm
hits JS >= 20, broken <= 2 with the same OFF/shuffled baselines already in hand.

**(d) Reasons to doubt.** The flip is confirmed, but: alpha 1 gave 0/8 and
alpha 4 gave 7/8 with breakage, so the working window was found in one shot on
8 setup tasks and may be narrow; breakage is family-clustered (F2), so a
different task mix could report anything from 1/32 to 5/32 at the same alpha;
the direction encodes surface-form tokens (fence label, `function`, braces)
learned from 64-token cued replies, so it may not transfer to prompts whose
default language is not Python or to non-language skills; n=32, one seed,
greedy; the coarse checker under-counts arrow forms (F4); and nothing here
tests HOLD/SWITCH/CLEAR or retained history, which is where check41 also
failed. The README's own scope statement ("not a reliable general skill
controller, persistent state, benchmark result, or semantic-correctness claim")
is accurate; I would add "the semantics happen to be fully preserved (32/32)"
as a positive fact the README leaves implicit.

Verdict on the report: accurate as written; MARGINAL stands; findings F1-F5 are
low/medium disclosure items, none blocking.
