# Sol xhigh verification of the ledger build (commit 747be31), 2026-09-01

## Findings

1. **CRITICAL — `primary_claim_valid` can certify a no-op or incomplete experiment.**

   The validator only requires automatic provenance, Tango NI, and a hard-coded neural cost of zero ([ledger_eval.py:125](/home/bmarti44/stencil-llm/scripts/ledger_eval.py:125)). It does not require:

   - a complete 113-conversation run;
   - a nonempty or active ledger;
   - text-ledger improvement over base;
   - neural-ledger improvement over base;
   - registered `top_k`, dose, `max_new`, or deadline;
   - acceptable timeouts/truncations.

   I constructed a valid-shaped record with an empty ledger and 200 identical text/neural outcomes. `summarize()` returned `primary_claim_valid=true`, with a 1.335-point upper bound. It also returned true for a favorable four-cell partial record. This is enabled by `is_automatic([]) == True` ([ledger.py:132](/home/bmarti44/stencil-llm/src/stencil/ledger.py:132)) and the absence of a completeness gate.

   This directly refutes the new plan statement that an under-inclusive ledger makes a positive conservative ([LEDGER-PLAN.md:125](/home/bmarti44/stencil-llm/LEDGER-PLAN.md:125)). Missing entries weaken both text and neural arms, reduce discordance, and can make NI easier. They do not “only weaken the neural arm.”

2. **CRITICAL — the registered confidence statement uses the wrong cells and ignores clustering.**

   The Tango sign, point scale, strict `<2.0`, and one-sided 95% implementation are correct under independent paired cells. I reproduced the reported all-concordant `n=4` bound: **40.3479 points**.

   The runner, however, applies it to every cumulative current-turn instruction ([ledger_eval.py:101](/home/bmarti44/stencil-llm/scripts/ledger_eval.py:101), [ledger_eval.py:274](/home/bmarti44/stencil-llm/scripts/ledger_eval.py:274)), although the treatment contains aged entries only ([ledger_eval.py:234](/home/bmarti44/stencil-llm/scripts/ledger_eval.py:234)).

   On the diagnostic cohort:

   - 130 insertable observations are pooled;
   - only 85 are aged and therefore eligible;
   - 45/130 are fresh constraints absent from the aged ledger;
   - those 85 observations occur in only 43 conversations;
   - cumulative constraints are scored again on later turns.

   Tango’s nominal interval treats these correlated and repeated outcomes as independent. Its 95% coverage therefore does not apply. Use a preregistered conversation-clustered NI bound, with the estimand defined explicitly.

   The diagnostic slice is also too small to certify Brian’s literal “tie is a win”: an all-concordant bound is 2.039 points at `n=130` and 3.085 at the eligible `n=85`, both above the 2-point margin. It is a falsification screen, not a confirmatory NI test.

   Multiplicity does not affect the single registered primary. The secondary McNemar p-values are unadjusted and must remain exploratory; if text-vs-base, neural-vs-base, or specificity become gates, add a hierarchical or multiplicity-controlled procedure.

3. **HIGH — the actual runner uses an untested sentence segmenter and crashes near the end.**

   The runner passes `sal.classify` as a bare callable ([ledger_eval.py:231](/home/bmarti44/stencil-llm/scripts/ledger_eval.py:231)). That makes `resolve_salience()` substitute `ledger.segment_char_spans` instead of `salience.split_sentences` ([ledger.py:104](/home/bmarti44/stencil-llm/src/stencil/ledger.py:104)).

   A CPU preflight over all 221 diagnostic turns found:

   - fatal `RuntimeError("sentence not found in its own text")` on conversation 769, turns 2 and 3;
   - conversation 769 is number 98 of 113 diagnostic conversations;
   - 76 of the remaining 219 turns produced different entries from the intended real-salience path.

   Common divergence: `i.e. <<title>>.` becomes two ledger fragments. The fatal case contains standalone quoted example lines.

   The integration test calls `build_ledger()` without the explicit callable and therefore exercises the good path ([test_ledger.py:81](/home/bmarti44/stencil-llm/tests/test_ledger.py:81)), not the runner path.

4. **HIGH — the specificity arm is not a non-ledger control, and scored outcomes are not linked to selected entries.**

   The control excludes only `neural.spans`, then biases their entire complement ([ledger_eval.py:258](/home/bmarti44/stencil-llm/scripts/ledger_eval.py:258)). That complement contains:

   - unselected aged ledger entries;
   - current-turn ledger entries;
   - other instruction tokens;
   - all ordinary and special tokens.

   It is a diffuse-complement control, not “matched bias mass on non-ledger tokens.” Distributing a small dose over the whole complement is also not mechanistically equivalent to applying dose 3.0 to equal-width control spans because attention softmax is nonlinear.

   The summary compares specificity only with base, not directly with neural ([ledger_eval.py:124](/home/bmarti44/stencil-llm/scripts/ledger_eval.py:124)). Entries also carry no instruction-ID linkage, so one cannot determine whether the selected ledger entry corresponds to the insertable constraint being credited.

5. **MEDIUM — marker-free is verified; benchmark-agnostic and fully blind are not.**

   Verified:

   - no feature name or feature regex contains `"constraint"`;
   - B3’s marker is stripped before training and testing;
   - refitting reproduces the committed weights;
   - claimed F1 values reproduce: 0.9817/0.9817 LOCO, 0.854 seed-0, 0.825 blind.

   But the classifier is trained on Multi-IF turn-2/3 sentences and recorded Multi-IF responses ([salience.py:391](/home/bmarti44/stencil-llm/src/stencil/salience.py:391)), while its feature design was informed by the seed-0 Multi-IF sample. This establishes same-benchmark generalization, not benchmark independence.

   The blind sample is not wholly unseen: `"Include the words \"intern\" and \"grow\"."` occurs exactly in the default training set. Removing it leaves F1 0.821, so the threshold still passes, but the stated “never saw” claim is false.

   Labels also apply the declared rule inconsistently:

   - “Be angry about it.” = 1, but “Give me an angry recommendation.” = 0.
   - “Be chatty while explaining.” = 1, but the polite-to-moms manner request = 0.
   - “It should include the topic of not studying.” = 1 despite topic-only examples being 0.
   - German translation = 0 despite language being named as a positive category.

   These inconsistencies mostly do not appear designed to inflate F1, but the labels need independent adjudication as the newly amended plan now requires.

6. **MEDIUM — several headline tests are vacuous or weaker than their claim.**

   - Neural cost zero is tested as `context_tokens_added(context, context) == 0` ([test_ledger.py:194](/home/bmarti44/stencil-llm/tests/test_ledger.py:194)); the runner then records zero as a literal ([ledger_eval.py:254](/home/bmarti44/stencil-llm/scripts/ledger_eval.py:254)). The current code really does pass the unchanged context, but the test and artifact would not detect drift.
   - The “bitwise” empty-ledger test compares decoded text and token count, not token IDs or logits, and does not assert that the selection callback ran ([test_ledger.py:230](/home/bmarti44/stencil-llm/tests/test_ledger.py:230)).
   - The NI test uses only a balanced `n10=n01` case and asserts the implementation’s own comparison, so it cannot catch a sign inversion ([test_ledger.py:198](/home/bmarti44/stencil-llm/tests/test_ledger.py:198)).
   - There are no tests for `ledger_eval.summarize()` or the end-to-end runner consumer path.

   Code inspection does support the empty-ledger behavioral guarantee: the callback runs during prefill, returns no spans, the hook returns `None`, and later steps run without a hook. It is not trivially bypassed—but “bitwise” remains unmeasured.

7. **MEDIUM — resume provenance and configuration freezing are incomplete.**

   Metadata hashes `salience.py` but not `salience_weights.json`, and omits several behavior-affecting dependencies: tokenizer, `qwen3.py`, `ctrb.py`, `e2.py`, `e2_multiif.py`, `stats.py`, and the verifier tree. A resumed run can therefore mix implementations without failing provenance.

## Design rulings

- **Aged entries only:** Defensible for a forgetting/retention diagnostic. The primary must then contain aged constraints only.
- **Select once at prefill, sustain throughout:** Defensible as one narrow frozen policy, but it is not the existing per-step controller unchanged. It can miss obligations that become relevant later, so a negative does not refute the broader ledger architecture.
- **`top_k=2`:** Not justified yet. With the intended segmenter, 69/221 turns have more than two aged entries and 102 entries are discarded. Freeze it as exploratory or preregister evidence for it before treating results as confirmatory.
- **Dose 3.0:** Reasonable from prior actuator evidence, but here it is applied from token one to every selected span; two selections double total biased mass. Report this distinction and do not tune it after viewing outcomes.
- **`FIXABLE_FAMILIES`:** Defensible as a frozen effect slice, provided only aged, ledger-linked constraints enter the primary and excluded-family harms remain visible.

## What must change before launch

1. Fix the runner’s salience/segmenter path and add a CPU preflight over all 113 conversations.
2. Amend the endpoint before observing more outcomes: complete cohort only, aged eligible constraints only, conversation-clustered NI.
3. Add non-vacuity requirements for text-vs-base and neural-vs-base; otherwise “matching text” can mean matching a useless no-op.
4. Build a true position/width-matched non-ledger control and report neural-vs-specificity directly.
5. Reject partial, nondefault, timed-out, truncated, heuristic, or provenance-mixed runs as primary-valid.
6. Independently adjudicate the labels and assert both hand samples are disjoint from training.

Test status: 35 tests collect; locally **30 passed and 5 GPU tests skipped** because CUDA is unavailable. The existing nine Tango tests passed, and all 221 stored diagnostic base scores recomputed identically.

Finally, the repository moved during this review: the reviewed implementation is commit `747be31`; current `HEAD` advanced to `ad498f3`, and the worktree currently has an externally modified `src/stencil/qwen3.py` plus untracked `tests/test_kv_pin.py`. The six reviewed implementation/test files did not change, but do not launch from the currently moving dirty tree.
