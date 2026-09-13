**REJECT for launch. The scorer can award false session successes, and permitted first replies can remove every governing rule from request 2. Resolve the findings before the timing pilot.**

Reviewed main at `441d64e2`. I did not read `data/bench/` or run GPU work. The manifest and both pool hashes reproduce. Because the sandbox prohibits temporary-file writes, I verified executable counterexamples using the unchanged authored test functions with an in-memory module loader; I did not rerun the subprocess-based 241-test suite.

**1. Harness correctness**

**F1 — Critical: request-2 packing can discard every rule and the first reply.** Packing follows oldest-message eviction and preserves system/final messages, but its qualification uses only the short gold reply. I appended harmless comments to checkpoint-1 gold, producing valid replies of 1,402–1,405 tokens—below the registered cap. In S01, S05, S09, S13, S17, S21, S25, S29, S33, S37, S41 and S45, request 2 retained only message indices `[0,19,20]`: system, event and final request. Neither governing prefix rule nor the first reply survived. The harness checks prompt length but never checks rule survival. This makes compliance partly depend on an arm’s verbosity under conditions the registration explicitly excludes. [Packing](/home/bmarti44/stencil-llm/src/stencil/a_screen.py:155), [gold-only qualification](/home/bmarti44/stencil-llm/tests/test_a_screen.py:110), [runtime check](/home/bmarti44/stencil-llm/scripts/a_screen_run.py:107).

**Fix:** Remove redundant file copies from request-2 rendering, qualify against the full permitted reply length, and enforce required-message survival before generation.

**F2 — High: the historical first request is rewritten retrospectively.** `session_messages(..., checkpoint=2, files=files1)` renders request 1 using `files1`, although the actual first request showed `files0`. Thus the model sees its completed first edit already present in the request that supposedly preceded that edit. Both smoke records exhibit this: request 2 contains three copies of the first method—rewritten historical snapshot, assistant reply and current-file rendering. This changes precedent exposure and consumes packing capacity. [Historical request construction](/home/bmarti44/stencil-llm/src/stencil/a_screen.py:143), [caller](/home/bmarti44/stencil-llm/scripts/a_screen_run.py:185).

**Fix:** Preserve the exact original request-1 message and append the actual reply, event and current-state request.

**F3 — High: per-request persistence and resumption are not implemented as registered.** Request 1 is held in `recs` until request 2 finishes. An interruption during request 2 loses the completed first request; restarting generates it again. A partially written JSON line also makes resumption crash. Completion detection trusts any request-2 record with the same session ID, without checking arm or adapter identity. [Resume](/home/bmarti44/stencil-llm/scripts/a_screen_run.py:90), [delayed write](/home/bmarti44/stencil-llm/scripts/a_screen_run.py:223).

**Fix:** Persist each completed request durably, resume checkpoint 2 from its saved first reply/repository, and validate run identity and unique record keys.

**F4 — High: EOS and deadline handling can misclassify generations.** The harness replaces the shipping generation EOS list `[151645,151643]` with `model.config.eos_token_id`, effectively `[151645]`. Emitting `<|endoftext|>` therefore need not stop generation; decoding hides it while generation continues. Separately, an EOS received after 300 seconds is accepted because `timed_out` requires `not ended`. `max_time` is a stopping criterion checked during generation, not a hard deadline. [EOS construction](/home/bmarti44/stencil-llm/scripts/a_screen_run.py:84), [terminal classification](/home/bmarti44/stencil-llm/scripts/a_screen_run.py:124), [shipping EOS configuration](/home/bmarti44/stencil-llm/deploy/stencil_focus/build/hub-4b/generation_config.json:4).

**Fix:** Preserve all configured terminal tokens and count elapsed-deadline violations as failures even when the final token is EOS.

**F5 — High: the registered deterministic execution settings are absent.** Both entrypoints seed Torch, but neither imports the module that sets the cuBLAS workspace and enables deterministic algorithms. Greedy decoding and a seed do not establish the protocol’s bitwise guarantee. [Harness](/home/bmarti44/stencil-llm/scripts/a_screen_run.py:70), [trainer](/home/bmarti44/stencil-llm/scripts/a_screen_train.py:98), [required settings](/home/bmarti44/stencil-llm/src/stencil/determinism.py:14).

**Fix:** Activate the shared determinism settings before importing Torch in both entrypoints.

The other basic paths are sound: token counting and inference tokenize the same rendered prompt; my recount matched all four smoke records. `off` loads no adapter, and `sft`/`cf` use the same PEFT loading and generation path. Applied outputs run four independent suites. Detected truncation, timeout and extraction failures force both outcomes false. However, fenced invalid Python is labelled `"applied"` and fails through test imports, rather than receiving a parse-failure terminal reason. [Scoring](/home/bmarti44/stencil-llm/src/stencil/a_screen.py:179), [application](/home/bmarti44/stencil-llm/src/stencil/a_screen.py:200).

**2. Trainer correctness**

I found no sign, masking or sequence-boundary bug in the loss:

- The shifted-logit slice includes exactly the completion tokens, including `<|im_end|>`. CE divides their negative log-probability sum by completion length.
- DPO uses **sequence sums**, with the correct chosen-minus-rejected, policy-minus-reference sign, β = 0.1 and outer weight 0.1.
- Reference scoring occurs before `get_peft_model`; no adapter exists during reference evaluation.
- Every chosen and rejected sequence checked—2,304 total—satisfied `prompt_ids + completion_ids == tokenize(prompt + completion + "<|im_end|>")`. Maximum sequence length reproduced as 3,217.
- FP32 trainable LoRA parameters under bf16 autocast are coherent. Input gradients are enabled for checkpointing through the frozen trunk.
- Eight microsteps are accumulated before clipping/updating. Partial accumulation is discarded before final saving.

These paths are implemented at [tokenization](/home/bmarti44/stencil-llm/scripts/a_screen_train.py:47), [log-probabilities/reference](/home/bmarti44/stencil-llm/scripts/a_screen_train.py:122), [PEFT/checkpointing](/home/bmarti44/stencil-llm/scripts/a_screen_train.py:148), and [loss/update](/home/bmarti44/stencil-llm/scripts/a_screen_train.py:207).

SFT and CF receive the same positive sequence/order construction. CF additionally scores rejected completions and pays reference cost; fewer CF exposures within equal time are explicitly registered.

**F6 — Medium: training telemetry does not report the claimed quantities accurately.** `reference_seconds` includes imports, example preparation, loading and adapter setup—and is populated for SFT too. `sequence_tokens_seen` counts only chosen sequences, omitting CF rejected and reference sequences. No final loss is saved unless it happens to appear in the ten-step history; the smoke’s history is empty. [Log construction](/home/bmarti44/stencil-llm/scripts/a_screen_train.py:167), [token/loss accounting](/home/bmarti44/stencil-llm/scripts/a_screen_train.py:218), [smoke](/home/bmarti44/stencil-llm/results/a-screen/smoke/cf-adapter/train-log.json:12).

**Fix:** Record separate preparation/reference/training/save times, chosen/rejected/reference token totals, discarded accumulation and the final completed-update loss.

Allocation enforcement and resumable training remain defective; see item 6 below.

**3. Pool validity and contract coverage**

I inspected repository code, requests, governing statements, events, gold construction and tests for these twelve slots:

| Target | Stable | Replacement | Scope | Reinstatement |
|---|---|---|---|---|
| Naming | S01 | S02 | S07 | S12 |
| Validation | S17 | S22 | S23 | S28 |
| Missing record | S33 | S38 | S43 | S44 |

**F7 — Critical: checkpoint 2 does not enforce all still-applicable contracts.** The following altered checkpoint-2 gold programs passed **every checkpoint-2 suite**. With an unchanged successful checkpoint 1, the harness awards `J=True`.

| Slot | Contract-breaking change accepted | Evidence |
|---|---|---|
| S01 | Rename existing `scale_recipe` to `recipe_scale` under the stable verb-first rule | [Either-spelling regression](/home/bmarti44/stencil-llm/src/stencil/a_screen_pool/s01.py:222) |
| S02 | Rename `close_ticket` to `ticket_close`, despite explicit preservation of existing names | [Regression](/home/bmarti44/stencil-llm/src/stencil/a_screen_pool/s02.py:218), [event](/home/bmarti44/stencil-llm/src/stencil/a_screen_pool/s02.py:481) |
| S12 | Rename `room_book` and remove its refusal warning | [Regression](/home/bmarti44/stencil-llm/src/stencil/a_screen_pool/s12.py:299), [support tests](/home/bmarti44/stencil-llm/src/stencil/a_screen_pool/s12.py:338) |
| S28 | Add forbidden storage validation to the grandfathered first operation | [Regression](/home/bmarti44/stencil-llm/src/stencil/a_screen_pool/s28.py:343) |
| S33 | Change `record_mark` on an unknown ID from returning None to raising KeyError | [Regression](/home/bmarti44/stencil-llm/src/stencil/a_screen_pool/s33.py:215) |
| S44 | Change `claim_item` from KeyError to None and remove its reclaim warning | [Regression](/home/bmarti44/stencil-llm/src/stencil/a_screen_pool/s44.py:262), [support tests](/home/bmarti44/stencil-llm/src/stencil/a_screen_pool/s44.py:300) |

TRAIN is worse in this respect: deleting the entire first live operation from `T-nam-ret-rep-00` still passes every checkpoint-2 suite. Both requests’ regression suites protect only the original operation. [Generator](/home/bmarti44/stencil-llm/src/stencil/a_train_pool.py:951).

**Fix:** At checkpoint 2, retain functional, naming, validation, missing-record and supporting checks for every protected earlier operation under its applicable/grandfathered state.

**F8 — High: some contract statements contradict their gold or protected behavior.** S33 requires every public method to return an Enrolment and explicitly forbids bare values, while its regression requires `count() == 1`. S01 and S02 have the same broad return-type wording while preserving integer counts. [S33 wording](/home/bmarti44/stencil-llm/src/stencil/a_screen_pool/s33.py:408), [regression](/home/bmarti44/stencil-llm/src/stencil/a_screen_pool/s33.py:92), [S01 wording](/home/bmarti44/stencil-llm/src/stencil/a_screen_pool/s01.py:425).

TRAIN also lacks explicit grandfathering where it deliberately preserves conflicting precedent. For example, `T-val-ret-sta-00` says module-level helpers **never validate**, but preserves `_apply_schedule` with validation in both gold completions. The initial target statement is global; its tests examine only the newly requested operation. [Statement](/home/bmarti44/stencil-llm/src/stencil/a_train_pool.py:730), [precedent construction](/home/bmarti44/stencil-llm/src/stencil/a_train_pool.py:937), [gold preservation](/home/bmarti44/stencil-llm/src/stencil/a_train_pool.py:968).

**Fix:** Explicitly identify the governed operations and grandfathered exceptions in the contract text, then test that exact scope.

**F9 — High: TRAIN’s family checks accept prohibited behavior.** Two verified examples:

- `T-mis-ret-sta-02`: clearing the entire store before returning None on an unknown ID passes all four suites. The contract test checks only that the unknown ID remains absent.
- `T-nam-log-sta-08`: emitting INFO on every active-record operation passes all four suites, although the statement requires no active-record log. The test rejects only WARNING-or-higher records.

[Missing-record checker](/home/bmarti44/stencil-llm/src/stencil/a_train_pool.py:604), [logging checker](/home/bmarti44/stencil-llm/src/stencil/a_train_pool.py:677), [logging wording](/home/bmarti44/stencil-llm/src/stencil/a_train_pool.py:772).

**Fix:** Compare the complete affected state before/after missing-ID calls and assert zero records at every captured level on silent paths.

**F10 — Medium: the construction-disjointness claim exceeds the evidence.** I found no non-exempt public-name overlap between TRAIN and SCREEN, including gold definitions. Wording overlaps found were predominantly ordinary boilerplate; I found no evidence that SCREEN responses were fitted. But TRAIN’s frozen-record/dictionary-store/replace/store/return construction substantially overlaps S01, S02, S33 and S44. The freeze checker verifies names and paths, not solution constructions or wording. It cannot establish that this is transfer beyond the shared construction. [TRAIN construction](/home/bmarti44/stencil-llm/src/stencil/a_train_pool.py:303), [update construction](/home/bmarti44/stencil-llm/src/stencil/a_train_pool.py:394), [S02 solution](/home/bmarti44/stencil-llm/src/stencil/a_screen_pool/s02.py:265), [freeze checks](/home/bmarti44/stencil-llm/scripts/a_screen_freeze.py:75).

**Fix:** Resolve the construction overlap within the existing pools before fitting and make the freeze’s disjointness claim match what was actually verified.

The family meanings themselves largely align: public versus lower-layer validation, naming order, and missing-ID behavior remain the trained targets. Different class/function arrangements in SCREEN provide some transfer, but do not cure these coverage defects.

**4. Counterfactual pairs**

The state selection in `pairs_from_session` is correct:

| Lifecycle | Event variant chooses | Irrelevant variant chooses |
|---|---|---|
| Stable | Unchanged state | Unchanged state |
| Replacement | New state | Pre-event state |
| Scope | Exception state for request 2 | Pre-event state |
| Reinstatement | Reinstated state | Interim state |

Request-2 gold preserves checkpoint-1 gold under checkpoint 1’s state. I checked all **1,152 pairs**: chosen and rejected pass their own authored functional, regression, contract and support suites; every rejected completion fails the chosen-state target suite; no chosen/rejected strings are identical. These conclusions are subject to F7–F9’s checker holes. [Pair extraction](/home/bmarti44/stencil-llm/src/stencil/a_screen.py:244).

`precedent_state` is actually passed into the existing code generator; the 8/8 balance per cell is real. However, the first live gold operation always follows checkpoint 1’s rule, so changing sessions still contain that stale precedent at checkpoint 2. Describe the counterbalance as applying to the **original operation**, not all code visible in the training prompt. [Counterbalance](/home/bmarti44/stencil-llm/src/stencil/a_train_pool.py:918), [first-operation construction](/home/bmarti44/stencil-llm/src/stencil/a_train_pool.py:968).

**5. Statistics and gates**

`mcnemar_exact` is two-sided and exact. I checked every possible discordant-count combination for N ≤ 48 against the binomial test. The Clopper–Pearson solver also matches the corresponding beta quantiles.

**F11 — High: the reported union-bound interval is narrower than registered.** `paired()` passes `alpha=0.05` for each component, producing two 95% intervals. Registration requires two **97.5%** intervals. The implemented union-bound argument guarantees only at least 90% simultaneous coverage, not 95%. With zero discordance at N=48, the displayed difference interval is approximately ±7.40 points; the registered calculation gives ±8.72 points. [Implementation](/home/bmarti44/stencil-llm/scripts/a_screen_summary.py:65), [registration](/home/bmarti44/stencil-llm/results/a-screen/REGISTRATION-A-SCREEN.md:122).

**Fix:** Use `alpha=0.025` for each component interval.

For a valid, complete manifest-matched dataset, gates 1–5 implement the registered inequalities correctly. [Gate implementation](/home/bmarti44/stencil-llm/scripts/a_screen_summary.py:124).

**F12 — Medium: summary validation and request-level diagnostics are incomplete.** Loading discards request-1 records, silently overwrites duplicate request-2 records and trusts stored outcomes. Consequently, “mean s/request,” truncations, timeouts and parse failures describe **request 2 only**. Completeness checks the intersection’s size, not the exact manifest and two unique records per arm/session. [Loading](/home/bmarti44/stencil-llm/scripts/a_screen_summary.py:19), [diagnostics](/home/bmarti44/stencil-llm/scripts/a_screen_summary.py:94), [completeness](/home/bmarti44/stencil-llm/scripts/a_screen_summary.py:158).

**Fix:** Validate both checkpoint records against the manifest, recompute session outcomes, and aggregate request diagnostics over both checkpoints.

**6. Compute against §8**

The arithmetic fits **conditionally**:

| Component | GPU-resident hours |
|---|---:|
| Two fixed training allocations, including CF reference scoring | 8.0 |
| Evaluation: 288 × 15 seconds | 1.2 |
| Evaluation allowance after 1.5 factor | 1.8 |
| Pilot: 4 × 3 × 2 requests at 15 seconds | 0.1 |
| Total using inflated evaluation allowance | **9.9** |

The estimated 25-minute reference pass belongs inside CF’s four hours; adding it again double-counts it. Remaining accounting includes evaluation/pilot loading, scoring while the model remains resident, packing, checkpoint writes, chunk reloads, smoke work charged to this program, and any interrupted work.

**F13 — High: the ceiling and required chunks are not enforceable with these scripts.** Evaluation has no reservation or cumulative-budget stop. The reservation wrapper records an ETA but imposes no deadline. Training supports neither optimizer/RNG/data-order/reference-cache resumption nor cumulative allocation across chunks; restarting starts fresh. Reference scoring has no budget check. The training loop can cross its deadline and then save—the 180-second smoke recorded 186.58 seconds. [Evaluation loop](/home/bmarti44/stencil-llm/scripts/a_screen_run.py:142), [training reference loop](/home/bmarti44/stencil-llm/scripts/a_screen_train.py:135), [training stop/save](/home/bmarti44/stencil-llm/scripts/a_screen_train.py:203), [reservation wrapper](/home/bmarti44/stencil-llm/tools/gpu_reserve.sh:55), [smoke duration](/home/bmarti44/stencil-llm/results/a-screen/smoke/cf-adapter/train-log.json:19).

**Fix:** Implement cumulative budget accounting and resumable ≤50-minute chunks, with complete training state and conservative stop-starting guards.

**F14 — Medium: the documented pilot is not the registered longest-prompt pilot.** Its example selects S02/S05/S09/S13. Their gold-path maximum packed prompts are 2,364/2,530/2,410/2,470 tokens; S04 and S29 reach 2,558, with other slots also longer. Gold completions reach 630 tokens in S18, so S02’s 200–300-token smoke does not establish workload-wide generation cost. [Pilot instruction](/home/bmarti44/stencil-llm/scripts/a_screen_run.py:15), [registered pilot](/home/bmarti44/stencil-llm/results/a-screen/REGISTRATION-A-SCREEN.md:132).

**Fix:** Select the four longest qualifying sessions after the rendering repair and apply 1.5 to their measured request times.

**7. Other interpretability issues**

**F15 — Medium: frozen identity is not bound to training or run records.** Both entrypoints regenerate pools from current code without comparing content against the freeze. Request records omit adapter/trunk/tokenizer/scorer identities. The TRAIN builder even writes its output when `problems` is nonempty and does not exit unsuccessfully. Repairs followed by accidental reuse of old records could therefore produce an apparently complete mixed-version result. [Training data loading](/home/bmarti44/stencil-llm/scripts/a_screen_train.py:53), [screen loading](/home/bmarti44/stencil-llm/src/stencil/a_screen_pool/__init__.py:32), [TRAIN freeze output](/home/bmarti44/stencil-llm/scripts/a_train_build.py:143).

**Fix:** Verify frozen content before use, bind immutable implementation/model/adapter identities to records, and make failed pool validation stop the build.

The immediate blocker is measurement validity: the current implementation can report successful preservation after breaking the earlier contract. Correcting the DPO arithmetic—which is already sound—would not address that defect.
