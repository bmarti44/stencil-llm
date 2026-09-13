**The screen still cannot launch. It can award J = 1 after an edit deletes unrelated records, and the summary can still turn a failed gate into a pass.**

I reviewed `e80d02cd`. Both frozen pool hashes reproduce. I executed the behavioral counterexamples through in-memory imports of the authored suites and measured packing with the shipping tokenizer files and chat template. The read-only sandbox prevented rerunning the subprocess-based 301-test suite. I did not read `data/bench/` or run GPU work.

| Finding | Disposition | Reason |
|---|---|---|
| F1 | **PARTIAL** | Request 2’s target survives, but supporting source definitions still disappear. [a_screen.py:154](/home/bmarti44/stencil-llm/src/stencil/a_screen.py:154) |
| F3 | **PARTIAL** | Identity matching and duplicate checks improved. Resume deletes a valid final JSON record without a newline and skips incompatible records before appending into their file. [a_screen_run.py:263](/home/bmarti44/stencil-llm/scripts/a_screen_run.py:263) |
| F6 | **RESOLVED** | Final-update loss now uses that update’s microsteps. Updates averaging 1 and 9 report 9. [a_screen_train.py:340](/home/bmarti44/stencil-llm/scripts/a_screen_train.py:340) |
| F7 | **PARTIAL** | The previous `find` mutation fails, but destructive changes to the first operation still pass. [a_screen.py:375](/home/bmarti44/stencil-llm/src/stencil/a_screen.py:375) |
| F8 | **RESOLVED** | Both TRAIN validation statements explicitly grandfather existing operations; the amended pool hash reproduces. [a_train_pool.py:747](/home/bmarti44/stencil-llm/src/stencil/a_train_pool.py:747) |
| F12 | **PARTIAL** | J is recomputed from suites, but function-only and lifecycle annotations remain trusted inputs to gates. [a_screen_summary.py:108](/home/bmarti44/stencil-llm/scripts/a_screen_summary.py:108) |
| F13 | **PARTIAL** | Resumed accounting omits resident overhead; adapter qualification still accepts unregistered training configurations. [accounting:290](/home/bmarti44/stencil-llm/scripts/a_screen_run.py:290), [guard:159](/home/bmarti44/stencil-llm/scripts/a_screen_run.py:159) |
| F15 | **PARTIAL** | The new fingerprint does not bind weight or large tokenizer content. The identity also omits the generation deadline. [hash:55](/home/bmarti44/stencil-llm/scripts/a_screen_run.py:55), [identity:219](/home/bmarti44/stencil-llm/scripts/a_screen_run.py:219) |
| F16 | **RESOLVED** | The scorer’s function-only calculation excludes protected contracts. The summary’s separate validation defect belongs under F12. [a_screen.py:394](/home/bmarti44/stencil-llm/src/stencil/a_screen.py:394) |
| F17 | **RESOLVED** | The behavior-preserving `count = _count` implementation passes. Executable binding checks replace the rejected AST shape requirement. [a_screen.py:319](/home/bmarti44/stencil-llm/src/stencil/a_screen.py:319) |

**F1 — high: the target fix still leaves required source knowledge outside the window.**

My S03 adversarial pair uses checkpoint-1 gold padded with harmless comments to **1,535 text tokens**, leaving room for EOS, followed by the **248-token** checkpoint-2 gold.

Request 2 packs to **2,531 tokens**, retaining indices:

```text
[0, 9, 10, 11, 12, 13, 14, 15, 16, 19, 20]
```

It now contains `FineLedger`, but contains neither the `Fine` definition nor its `frozen=True` declaration. Those are in the omitted `loandesk/model.py`. Both oracle replies pass every suite, so **J = 1**. Replacing the second reply’s `replace(fine, status="waived")` with an in-place assignment produces `FrozenInstanceError` and **J = 0**. The target is visible; its relevant representation constraint is hidden. [record definition:27](/home/bmarti44/stencil-llm/src/stencil/a_screen_pool/s03.py:27), [renderer:155](/home/bmarti44/stencil-llm/src/stencil/a_screen.py:155)

**Fix:** render all current files at request 2. In my 48 maximum-reply cases, all files plus the protected messages required at most **2,372 tokens**, leaving **188 tokens** spare. This needs no new context mechanism.

**F7 — high: a session still receives J = 1 after deleting unrelated records.**

Use S01’s correct first reply, optionally padded to 1,535 tokens. In checkpoint-2 gold, replace:

```python
self._recipes[recipe_id] = scaled
```

with:

```python
self._recipes = {recipe_id: scaled}
```

The second reply is **283 tokens**. Every checkpoint-2 suite, both protected flags, `all`, and `function_only` remains **True**. With successful request 1, **J = 1**.

Create recipes A and B, then scale A: `count()` becomes **1**, and `find(B)` returns **None**. The repository is wrong. The protected tests exercise scaling with only one stored recipe. [functional fixtures:71](/home/bmarti44/stencil-llm/src/stencil/a_screen_pool/s01.py:71), [regression fixture:226](/home/bmarti44/stencil-llm/src/stencil/a_screen_pool/s01.py:226)

I also verified a **286-token** second reply replacing `recipe.with_servings(servings)` with `Recipe(recipe.recipe_id, recipe.title, servings)`. It passes everything but erases an existing tag when scaling.

**Fix:** exercise the first operation with an unrelated stored record and nondefault fields, including a tag-then-scale sequence.

These answer question 3 directly: **yes, false session successes remain**. I did not reproduce a new false rejection of a behavior-preserving class alias or inherited method. A correct final repository following a failed first checkpoint legitimately receives J = 0 under the registered two-checkpoint outcome.

**F12 — high: the validating loader still permits decision-changing false inputs.**

I executed the actual summary entrypoint against synthetic 48-session records:

- Changing only CF’s S03 lifecycle from `scope` to `replacement` changed **GATE FAILED → GATE PASSED**. The summary takes strata from CF’s records rather than the manifest.
- Leaving a failed functional suite intact while changing stored request and session `function_only` flags to True also changed **GATE FAILED → GATE PASSED**.

The first bypasses the stratum gate; the second bypasses the functional-decline gate. [function-only loading:108](/home/bmarti44/stencil-llm/scripts/a_screen_summary.py:108), [stratum selection:236](/home/bmarti44/stencil-llm/scripts/a_screen_summary.py:236)

A nonempty but incomplete identity also passes validation: required identity fields are not required, and matching identities are not checked against the current freeze. [identity check:61](/home/bmarti44/stencil-llm/scripts/a_screen_summary.py:61), [comparison:197](/home/bmarti44/stencil-llm/scripts/a_screen_summary.py:197)

**Fix:** recompute function-only from its three individual suites, derive gate strata from the frozen manifest, and require the identity fields actually used to establish comparability.

**F12 — medium: incomplete summaries still crash.** Zero completed sessions now works, but one completed stable session across all arms raises `ZeroDivisionError` when the changing-rule subset is empty. **Fix:** handle empty subsets before calling `paired`. [a_screen_summary.py:259](/home/bmarti44/stencil-llm/scripts/a_screen_summary.py:259)

**F3 — medium: resume repairs too aggressively and refuses incompatible files too late.**

Executing the resume block on a complete JSON object without its trailing newline deleted that record. An incompatible identity was skipped while its bytes remained available for subsequent appends; the resulting mixed file will be rejected by the summary.

**Fix:** preserve a valid final JSON object by adding its newline, discard only malformed trailing content, and refuse incompatible output files before generation. [a_screen_run.py:263](/home/bmarti44/stencil-llm/scripts/a_screen_run.py:263)

**F13/F15 — high: adapter and model provenance still do not establish the registered comparison.**

The exact adapter guard accepted a final CF log declaring the current pool, no limit and 14,400 budget seconds, alongside:

```text
steps=1, seconds=1, seed=99, rank=8, alpha=16,
lr=0, beta=0, dpo_weight=0, accum=1,
a different training trunk and an old trainer identity
```

It also accepted `steps=-1`; the “positive steps” check is a truthiness check. These are unchecked values, not evidence that such a run occurred. [a_screen_run.py:155](/home/bmarti44/stencil-llm/scripts/a_screen_run.py:155)

The hub fingerprint hashes JSON content only below **2,000,000 bytes**. The actual `tokenizer.json` is **11,422,654 bytes**, and `vocab.json` is **2,776,833 bytes**. Both receive size-only treatment, as do the weights. I reproduced identical fingerprints after replacing both weight bytes and large tokenizer bytes with different same-length content. Adapter configuration is also absent from the adapter-weight fingerprint. [hub hash:61](/home/bmarti44/stencil-llm/scripts/a_screen_run.py:61), [adapter hash:201](/home/bmarti44/stencil-llm/scripts/a_screen_run.py:201)

**Fix:** hash actual model/tokenizer and adapter-configuration content; check the existing training configuration and trunk identity against the registration; require positive steps; include and enforce the registered deadline.

These gaps can differ between arms without the summary detecting it.

The other changes do **not** warrant additional machinery:

- I found **no protected-test filename collisions across 48 SCREEN and 576 TRAIN sessions**, including the generated binding filename.
- Fresh suite subprocesses avoid cross-arm import-cache contamination. Binding resolution establishes existence; behavioral preservation remains the executable tests’ job.
- `pack_session` is **not** the only call path: the trainer still calls `A.pack` directly. However, all **1,152 frozen TRAIN prompts** produced identical retained indices under both paths, with no missing required messages. That is currently a cleanup, not a launch blocker. [a_screen_train.py:80](/home/bmarti44/stencil-llm/scripts/a_screen_train.py:80)
- Moving output-directory creation earlier fixes the exhausted-reference branch’s access to `out`. I found no independent failure caused by that move. [a_screen_train.py:120](/home/bmarti44/stencil-llm/scripts/a_screen_train.py:120)

**Compaction remains, but rule retention is guaranteed by the apparatus.**

Measured over all 48 SCREEN slots:

| Measurement | Minimum | Median | Maximum |
|---|---:|---:|---:|
| Unpacked request-1 tokens | 2,577 | 2,894 | 3,144 |
| Packed request-1 tokens | 2,303 | 2,433.5 | 2,551 |
| Packed request-2 tokens, gold first reply | 2,311 | 2,447 | 2,559 |
| Packed request-2 tokens, 1,535-token first reply | 2,320 | 2,478 | 2,557 |
| Retained prefix turns, request 1 | 13 | 14 | 15 |
| Retained prefix turns, gold request 2 | 13 | 14 | 15 |
| Retained prefix turns, maximum first reply | 6 | 8 | 9 |

Every slot drops prefix history before request 1. Request 1’s message and reply are evicted at request 2 in **48/48** gold and maximum-reply cases. On the gold path, only **13/48** lose additional prefix turns; 29 retain the same count and six retain more. The qualification counts all dropped messages, including the superseded request and reply. [qualification:121](/home/bmarti44/stencil-llm/tests/test_a_screen.py:121)

Adding `protect` changes **zero gold SCREEN packings** and only **S47** among my maximum-reply cases. It therefore has not broadly emptied the context of distraction. But the model never has to recover an evicted registered rule: those **2–3 rule turns are explicitly protected**. This supports the limited history-replay claim in §14.6. Token counts cannot establish that the task has become easy. [protection:218](/home/bmarti44/stencil-llm/src/stencil/a_screen.py:218)

**Compute remains conditional, and 1,296 is now the wrong subprocess count.**

The amended scorer runs **five suites at checkpoint 1 and six at checkpoint 2**. The full applied evaluation path therefore entails:

```text
48 × 3 × 11 = 1,584 suite subprocesses
```

That is **288 more** than §14.4 counts. The 12 pilot arm-sessions add **132**, making **1,716** including the pilot. Failed applications can reduce these counts. [a_screen.py:360](/home/bmarti44/stencil-llm/src/stencil/a_screen.py:360)

| Component | Estimated hours |
|---|---:|
| Two trainings, CF reference scoring included | 8.0 |
| Evaluation generations: 288 × 15 s × 1.5 | 1.8 |
| Pilot generations: 24 × 15 s | 0.1 |
| Subtotal | **9.9** |
| One permitted training rerun | 4.0 |
| Subtotal with rerun | **13.9** |
| Remaining allowance | **2.1** |

The remaining 7,560 seconds permit at most **4.41 seconds per suite invocation** across evaluation and pilot **before** allowing for evaluation/pilot loads and other uncovered resident overhead. These remain estimates pending the registered pilot. CF reference scoring must not be added again. [§14.4:351](/home/bmarti44/stencil-llm/results/a-screen/REGISTRATION-A-SCREEN.md:351)

**F13 — high: cumulative accounting still forgives consumed compute.** Saved `seconds` measures only `model.generate`. Resume sums that field, dropping prior loading, scoring, packing and interrupted unrecorded work. The guard checks at the budget boundary, without the protocol’s five-minute starting margin. Finishing both requests of an admitted session is consistent with amendment 2; I am not reopening per-request stopping. [generation timer:308](/home/bmarti44/stencil-llm/scripts/a_screen_run.py:308), [resume accounting:290](/home/bmarti44/stencil-llm/scripts/a_screen_run.py:290), [guard:359](/home/bmarti44/stencil-llm/scripts/a_screen_run.py:359)

**Fix:** persist cumulative resident wall time, include failed launches, apply the starting margin, and enforce the whole-screen ceiling using the corrected suite count.

The measured-save reserve and exhausted-reference INCOMPLETE marker are improvements. The reserve still excludes optimizer overhead from its microstep estimate, and a periodic save can consume the allowance reserved for the final save; final status is set to complete unconditionally. Account for those operations in the same budget correction. [estimate:299](/home/bmarti44/stencil-llm/scripts/a_screen_train.py:299), [periodic/final saves:350](/home/bmarti44/stencil-llm/scripts/a_screen_train.py:350)

I found no additional reason to change the arms, benchmark, outcome unit or narrowed scientific claim. The remaining obstacles are apparatus defects.

The shortest changes that would change my answer are:

1. Render all current files at request 2.
2. Add the demonstrated S01 multi-record and field-preservation checks.
3. Recompute function-only, use manifest strata, finish identity validation, and repair resume handling.
4. Bind actual model/tokenizer/adapter content and enforce registered training and decoding configuration.
5. Account for cumulative resident time, save/update overhead and **1,584 evaluation suite invocations**, then apply §8 using the registered pilot.

**DO NOT LAUNCH**
