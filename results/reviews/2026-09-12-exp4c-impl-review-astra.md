**Verdict: BLOCK.** Reviewed through commit `1281e28d77dac07d1dcd3227d13aba390c638e6f`, including its timeout correction. Several paths can admit invalid evidence or exceed the registered budget.

I wrote no files, ran no models, used no GPU, and read nothing under `data/bench/`. Twelve selected tests passed with filesystem-writing features disabled. Additional in-memory probes reproduced the defects below; the full suites were not run.

1. **High — the recorded EOS set differs from the package’s effective EOS set.**

   [runner:125](/home/bmarti44/stencil-llm/scripts/memorycode_package_run.py:125) unions model-config and generation-config EOS IDs. The assembled package actually defaults generation to **model.config.eos_token_id**, at [package:75](/home/bmarti44/stencil-llm/deploy/stencil_focus/build/hub-4b/modeling_stencil_focus.py:75).

   For the current files, those are respectively `{151645}` and `{151645, 151643}`. Qualification passes the larger set to plain generation at [qualification:147](/home/bmarti44/stencil-llm/scripts/memorycode_4c_qualify.py:147).

   Consequently, `151643` can appear inside package output and enter scored text/repetition counts, while plain generation stops there. If it occurs at the package’s output limit, the runner removes it and incorrectly reports EOS instead of cap.

   **Required change:** preserve unchanged package behavior: normalize its effective config EOS to `[151645]`, and use that exact setting for recording, terminal stripping, plain comparison and replay. Include it in fingerprint equality. Strip only a terminal **effective** EOS.

   With that correction, the scored-ID cap convention is consistent with the inherited research scorer: a terminal EOS in raw position 512 leaves 511 scored IDs and is an EOS completion; 512 non-EOS IDs are capped.

   The question’s short-stop hole **is fixed in the reviewed commit**: [runner:154](/home/bmarti44/stencil-llm/scripts/memorycode_package_run.py:154) classifies short, non-EOS output as timeout even at 299.9 seconds. Keep that rule, record a distinguishing reason such as `max_time_stop` versus `wall_deadline_exceeded`, and retain zero primary/strict credit plus the timeout failure flag.

2. **High — qualification neither preserves sufficient evidence nor releases models sequentially.**

   At [qualification:60](/home/bmarti44/stencil-llm/scripts/memorycode_4c_qualify.py:60), `_free(model)` deletes only its local parameter. The caller retains `model` during the plain load, and retains `plain` during the package reload.

   At [qualification:175](/home/bmarti44/stencil-llm/scripts/memorycode_4c_qualify.py:175), the report is written only after all calls. An interruption loses completed qualification outputs and permits starting qualification again because the final file does not exist. The report also discards prompt bytes/IDs, stores only plain-match booleans, omits plain raw outputs/timings, and checks replay prompt text without separately comparing token IDs.

   **Required change:** delete caller-owned references before each subsequent load, then collect/empty cache. Persist each prescribed call atomically, with immutable call identity, prompt bytes/IDs, raw output, EOS, termination and timing. Save plain and replay outputs, and compute explicit prompt-byte, prompt-ID and raw-output comparisons. Derive the generation count from receipts.

   The intended count is correct: \(8+12+16+8=44\), with \(4+12=16\) package-off outputs. Resume only unfinished prescribed work under the same qualification identity; never replace a completed timing call or recompute `t_max` from a fresh run.

3. **High — the allocation limits are not enforced by the actual launch paths.**

   [qualification:68](/home/bmarti44/stencil-llm/scripts/memorycode_4c_qualify.py:68) accepts no worker-budget argument and never enforces its cumulative qualification limit. The actual [qualification wrapper:8](/home/bmarti44/stencil-llm/tools/exp4c_qualify_launch.sh:8) requests **40 GB**, not the registered 32 GB, and supplies no worker budget.

   `gpu_reserve.sh` records a reservation and waits; it does not terminate at its ETA. Moreover, `max_time` finishes the current generation pass after the allowance expires; it is not a hard process watchdog. [Transformers documentation](https://huggingface.co/docs/transformers/main/en/main_classes/text_generation)

   Evaluation checks its ceiling only before an item at [runner:272](/home/bmarti44/stencil-llm/scripts/memorycode_package_run.py:272), then can start both arms with insufficient remaining allowance. Its initial slice check also precedes model loading and prompt preparation.

   **Required change:** implement the registered owned-process watchdog; check remaining slice and cumulative allowances immediately before each call, including time for terminal persistence. Record and enforce:

   - qualification resident time, including interrupted attempts, ≤3,600 seconds;
   - evaluation generation spending ≤\(3t_{\max}N\);
   - cumulative evaluation loading/other resident overhead ≤2,700 seconds;
   - release verification resident time ≤900 seconds.

   The summarizer should consume durable process/slice start/end or watchdog receipts for these limits. Terminal generation records alone cannot reconstruct loading overhead or interrupted qualification spending. The final release gate must consume verification receipts. Missing accounting cannot establish budget compliance.

   The actual wrappers also need failure propagation. [Evaluation wrapper:11](/home/bmarti44/stencil-llm/tools/exp4c_eval_launch.sh:11) can lose the Python qualification-check failure through `read ... <<< "$(…)"`; [line 38](/home/bmarti44/stencil-llm/tools/exp4c_eval_launch.sh:38) logs runner failure and continues launching slices. Capture and check each status explicitly; terminal configuration/qualification failures must stop execution.

4. **High — a completed generation can disappear from both spending and resume protection.**

   [runner:338](/home/bmarti44/stencil-llm/scripts/memorycode_package_run.py:338) writes an attempt `"end"` **before** scoring and saving the terminal record at [line 397](/home/bmarti44/stencil-llm/scripts/memorycode_package_run.py:397).

   If the process dies between those operations, `_generation_seconds` finds no output, while [interrupted_seconds:205](/home/bmarti44/stencil-llm/scripts/memorycode_package_run.py:205) removes the ended attempt. My synthetic completed 40-second attempt with no terminal record was charged **zero** interrupted seconds. Resume then regenerates that arm.

   **Required change:** assign unique attempt IDs and durably save raw terminal output immediately after generation. Link attempts and scored records, accounting for every completed attempt exactly once even if scoring/persistence later fails. Resume scoring from saved raw output.

   Open attempts require watchdog-measured spending or a defensible conservative bound. Clamping elapsed time to 300 seconds is not conservative when a call can overrun that duration.

5. **High — the timing-derived freeze is not enforced end to end.**

   [items:96](/home/bmarti44/stencil-llm/scripts/memorycode_4c_items.py:96) accepts `--freeze N` without qualification or timing evidence. `--qualification` is merely stored as a string. Candidate reconstruction does not assert the registered candidate count or either registered hash before rewriting the candidate file.

   [summary:320](/home/bmarti44/stencil-llm/scripts/memorycode_4c_summarize.py:320) trusts the frozen `n` and preferentially trusts its `t_max`; it does not recompute them from the prescribed qualification calls or verify that the selected definitions are exactly the candidate prefix. [Runner:237](/home/bmarti44/stencil-llm/scripts/memorycode_package_run.py:237) does not check qualification before generation.

   **Required change:** make freeze consume the completed qualification receipts. Verify its fingerprint, prescribed timing-call identities, eligibility and qualification hash; recompute `t_max` and `N`; verify both registered hashes; require `len(items)==N` and the exact candidate prefix. Store the qualification digest in the frozen manifest. Recheck this chain in the runner and summary. Reject inconsistent overrides.

   The committed candidate artifact itself checks out: **196 unique dialogues, 68 reserve items**, both registered hashes reproduced, and the first 128 match the original definitions—including the additional `families` and `history_prompt_tokens` fields.

   Candidate-index alternation is correct. However, unrestricted `--ids`/`--arms` launches can change global execution order; the 4C consumer should select the next missing work in the frozen schedule itself.

6. **High — resume can silently relabel an old arm with a new environment.**

   [fingerprint_matches:105](/home/bmarti44/stencil-llm/scripts/memorycode_package_run.py:105) treats **every** missing/`None` environment field as compatible, not just a temporarily unresolved attention backend. An empty environment matched the populated test manifest in my probe.

   At [runner:259](/home/bmarti44/stencil-llm/scripts/memorycode_package_run.py:259), a partial record is checked before loading resolves attention. After loading, it is not rechecked; [line 320](/home/bmarti44/stencil-llm/scripts/memorycode_package_run.py:320) replaces its manifest. An old arm can therefore acquire the new arm’s environment identity.

   **Required change:** permit a provisional comparison only for deciding whether to load. Before generating or modifying a record, resolve and strictly compare the complete frozen fingerprint against qualification and existing arms. Missing required fields must fail. Preserve each arm’s generation-time identity.

   Freeze effective generation settings, EOS, dtype, device/GPU identity, deterministic-algorithm settings, cuBLAS workspace, TF32/matmul precision, and enabled SDPA kernels. Record relevant dependency versions such as `tokenizers`; record analysis dependency versions separately. The attention implementation name alone does not identify the resolved SDPA kernel.

   Current top-level config, generation-config and tokenizer files are covered by `package_files`; it skips subdirectories. Either enforce the flat inference-file layout or hash inference dependencies recursively with explicit documentation/cache exclusions.

7. **High — record validity is too weak to support confirmation.**

   [summary:87](/home/bmarti44/stencil-llm/scripts/memorycode_4c_summarize.py:87) checks field presence without verifying their consistency. My probe accepted contradictory raw/scored IDs, a score of `3.0`, negative elapsed time and a failure dictionary containing none of the required categories.

   More seriously, **NaN scores produced `technical_ok=True` and “STATISTICAL GATES PASSED.”** NaN endpoints make the rejection comparisons false, reaching [reading:277](/home/bmarti44/stencil-llm/scripts/memorycode_4c_summarize.py:277).

   [summary:158](/home/bmarti44/stencil-llm/scripts/memorycode_4c_summarize.py:158) also omits `extra` from completeness. A complete 128-pair cohort plus an extra valid record passed. Malformed JSON currently crashes the driver instead of appearing in its missingness/invalidity report.

   **Required change:** validate finite bounded scores and finite nonnegative spending; actual booleans/categories; raw-to-scored EOS transformation; token counts; termination/timeout/cap consistency; prompt hashes/counts/allocation; item/query/index identity; and strict-score consistency. Recompute scores and failures from saved outputs with the frozen checker. Require finite valid interval endpoints before any positive decision.

   Reject extra records, unknown arms, duplicate identities, malformed files and mismatched filenames. Derive descriptive subsets from frozen item metadata, not unchecked record metadata.

8. **High — floating-point rounding bypasses the zero-variance fallback.**

   At [paired_t:47](/home/bmarti44/stencil-llm/scripts/memorycode_4c_summarize.py:47), the mean of identical floating-point values can differ slightly from each value, making the subsequently calculated SD nonzero.

   Reproduced through `analyze`: **134 identical differences of 0.12** yielded SD approximately \(1.393\times10^{-17}\), interval `[0.12, 0.12]`, p=0 and statistical success. The registered result is the Hoeffding interval **[−0.114644204, 0.354644204]**, with p-bound **0.762118808**: NOT PROVEN.

   **Required change:** detect exactly constant input values before variance calculation, using equality to the first value; take the fallback directly. Use stable summation for the remaining calculation. Do not substitute an arbitrary near-zero threshold.

9. **High — publication is described conditionally, but the push consumer does not enforce it.**

   The summary correctly avoids declaring PROVEN. However, [push_to_hub:85](/home/bmarti44/stencil-llm/deploy/stencil_focus/scripts/push_to_hub.py:85) reassembles the package, overwriting configuration and remote code, then [line 96](/home/bmarti44/stencil-llm/deploy/stencil_focus/scripts/push_to_hub.py:96) uploads without checking statistical success, accepted audit, verification or evaluated hashes.

   **Required change:** add the 4C release consumer before launch. It must require all three gates, bound to the same frozen package/results identities, and upload an immutable evaluated staging directory. Rehash the upload inventory immediately before pushing; documentation changes alone may be excluded from the inference fingerprint.

   The clean-environment check should demonstrate that the staged package loads through the documented public API with pinned dependencies and a clean remote-code cache, independently of research-repo imports. Use a prospectively fixed existing qualification long session—`359-99`, both flag states is sufficient—and reproduce its prompt bytes, prompt IDs, effective generation configuration and raw outputs including EOS. Verify scored-ID/text reconstruction too. Complete this within the registered verification allowance; no new efficacy evaluation or research-runtime parity stage is needed.

   The release manifest should bind the per-file inference hashes, aggregate fingerprint, upstream revision, qualification/frozen-items/records/summary/audit/verification digests, environment, decoding settings and complete upload inventory. The card should carry the registered scoped wording, measured results, disclosures and reproduction settings. Record the resulting HF commit and verify its inference-file hashes against that manifest.

10. **Medium — provenance is incomplete, and the registration silently shortened the binding records requirement.**

   The runner saves prompt text losslessly, prompt hashes/counts, raw/scored IDs, text, scores, failure categories, timing, reminder text/counts and package identities. A full frozen-items digest can identify an individual item when combined with a validated item ID; a separate per-item digest is not inherently necessary.

   It does **not** save checker hashes or reminder source offsets. A repository Git SHA does not replace an enforced checker fingerprint. Missing checker identity matters directly to score reproducibility and mixed-version resume; add hashes for the scoring wrapper and vendored checker dependencies to the frozen scoring identity.

   [Registration:138](/home/bmarti44/stencil-llm/results/memorycode-long/REGISTRATION-4C.md:138) substituted “reminder text and sentence counts” for the binding decision’s “reminder/source offsets.” Restore that requirement and record source-message/thread character spans, the eviction boundary, and a source-content digest. This can be runner-side instrumentation using the existing session spans; it need not change prompting. Repeated identical sentences make text/counts alone insufficient to identify provenance.

The statistical formulas otherwise match the registration. The paired t quantile is \(t_{.975,N-1}\), with two-sided \(2\,\mathrm{sf}(|t|)\); the implemented Hoeffding expressions are correct when their branch is reached. The Clopper–Pearson fallback uses separate 97.5% intervals and subtracts **on-only lower − off-only upper**, and **on-only upper − off-only lower**, in the correct direction. McNemar and sign tests use exact two-sided binomial conventions, with p=1 for no discordances. Bootstrap input is lexicographically sorted, and indices 250 and 9749 are the registered order statistics 251 and 9750.

For zero discordant failures, each discordance probability has upper bound
\[
U=1-0.0125^{1/N},
\]
so the paired interval is \([-U,U]\).

| Failure configuration | Mean difference | Registered 95% interval, percentage points | Guard |
|---|---:|---:|---|
| N=196, zero discordances | 0 | [−2.210920697, +2.210920697] | Pass |
| N=128, zero discordances | 0 | [−3.365521009, +3.365521009] | Pass |
| N=196, one on-only, zero off-only | +0.510204082 points | [−0.496022475, +1.516430638] | Pass |

For the last row, \(s_H=1/14\), \(SE=1/196\), \(t=1\), \(t_{.975,195}=1.972204051\), and two-sided paired-t p=**0.318549791**. Exact McNemar p=1. All three intervals satisfy the registered equivalence flag; none demonstrates an increase.

For valid finite inputs, the reading order is correctly **technical → efficacy → guard**, and failure evidence is calculated independently. The defects above concern what reaches that decision function and its handling of invalid numerics.

The sample-size arithmetic is also correct:

| \(t_{\max}\), seconds | N | Evaluation ceiling, seconds |
|---:|---:|---:|
| 47.641592214 | 196 | 28,013.256221832 |
| 50 | 192 | 28,800 |
| 60 | 160 | 28,800 |
| 75 | 128 | 28,800 |
| 76 | 126 — ineligible | No evaluation |

Full N=196 requires \(t_{\max}\le48.979591837\) seconds; eligibility requires \(t_{\max}\le75\). The component allowances sum to **36,000 seconds = 10 hours**.

No score enters the normal sample-size formula or candidate-index alternation. Outcome-dependent latitude nevertheless remains through unbound freeze arguments, lost completed attempts, arbitrary arm/item launches and repeated qualification after interruption. Also, [summary:175](/home/bmarti44/stencil-llm/scripts/memorycode_4c_summarize.py:175) computes efficacy on partial records, and the driver overwrites summaries. Add a finalization check: incomplete ongoing runs expose operational completeness/cost only; a terminal incomplete report may describe available outcomes. Ordinary progress logs should omit compliance scores.

**Minimum edits before qualification launch:** fix findings 1–9; add the required provenance from finding 10; and add focused consumer tests for EOS divergence, qualification persistence/model release, post-generation interruption, budget exhaustion, frozen-N mismatch, partial-record backend changes, extras/NaN/malformed records, constant differences, and refusal to publish changed or unverified bytes. Replace the tautological assertion at [test:130](/home/bmarti44/stencil-llm/tests/test_memorycode_4c.py:130). Close these findings in this same review record; no new scientific revision or general review stage is required.

---

## Closure record (orchestrator, 2026-09-12, before the qualification launch)

Each finding is closed (resolved) in the commit that follows this review; prior text above is
unchanged. Tests: `tests/test_memorycode_4c.py` (16 consumer tests).

1. (resolved) Effective EOS = `model.config.eos_token_id` only (`eos_ids`), normalized `[151645]`;
   recorded in `decoding.eos_token_id` and `eos_token_ids`, both inside `FINGERPRINT_KEYS`; only
   a terminal effective EOS is stripped; plain comparison and replay use the receipt's list;
   `timeout_reason` distinguishes `max_time_stop` from `wall_deadline_exceeded`. Test
   `test_effective_eos_is_the_config_value_not_the_generation_config_union`.
2. (resolved) Qualification rewritten around 44 immutable per-call receipts
   (`qualification-4c/calls/NN-stage-id-arm.json`, written atomically right after each call, with
   prompt bytes/ids, raw output, EOS, termination, timing, manifest and the session messages);
   resume only unfinished prescribed calls under a persisted identity; models released
   sequentially (`release_model` + caller drops references); explicit prompt-byte, prompt-id and
   raw comparisons; report derived from receipts. Tests
   `test_qualification_prescribes_44_calls_and_reports_from_receipts`,
   `test_release_model_drops_references`.
3. (resolved) `ProcessReceipt` heartbeat receipts + watchdog thread (resident limit, cumulative
   overhead ≤ 2,700 s, per-call deadline + 60 s grace) end the owned process; allowances checked
   immediately before each call incl. a persistence margin; qualification resident ≤ 3,600 s
   enforced from receipts; wrappers declare 32 GB, capture every status and stop on failure.
   Tests `test_process_receipt_watchdog_detects_limit_violations`,
   `test_incomplete_on_missing_invalid_duplicate_extra_malformed_or_budget`.
4. (resolved) Unique attempt ids; raw output persisted durably before the `end` row; accounting
   from the attempt log (every ended attempt once, open attempts bounded by the process
   heartbeat, missing receipt → unbounded → INCOMPLETE); resume scores from the saved raw
   output. Test `test_completed_attempt_without_record_is_charged_and_open_attempts_are_bounded`.
5. (resolved) `--freeze` removed; freezing consumes the qualification report only (eligibility,
   eight prescribed timing identities, recomputed t_max and N, registered hashes, exact
   candidate prefix, qualification digest and package fingerprint stored); `verify_frozen`
   rechecked by the runner, the wrapper and the summary; `--ids`/`--arms` removed (the runner
   selects the next missing work in the frozen schedule). Test
   `test_freeze_chain_verifies_and_rejects_frozen_n_mismatch`.
6. (resolved) Strict fingerprint equality over all keys incl. a complete environment
   (framework and tokenizer versions, GPU, dtype, device, attention backend, determinism,
   cuBLAS workspace, TF32/matmul precision, SDPA kernels) and checker hashes; provisional
   leniency only for load-resolved fields and only to decide whether to load; per-arm
   manifests never replaced; recursive package hashing with documented exclusions. Test
   `test_fingerprint_is_strict_after_load_and_only_provisionally_lenient`.
7. (resolved) Record validation checks consistency (finite bounded scores, finite non-negative
   timing, boolean categories, raw→scored EOS transform, termination/timeout/cap agreement,
   prompt hash/count/allocation, item identity from the frozen manifest, strict agreement,
   provenance), re-scores text with the frozen checker and re-decodes ids; extras, unknown
   arms, duplicates, malformed files and misnamed files block; finite endpoints required for
   any positive decision. Tests `test_record_consistency_is_checked_not_just_presence`,
   `test_nan_scores_never_pass`, `test_records_are_rescored_with_the_frozen_checker_and_decoded_text_checked`.
8. (resolved) Exactly-constant differences detected by equality before any variance arithmetic;
   `math.fsum` elsewhere; reproduces the registered [−0.114644204, 0.354644204], p 0.762118808.
   Test `test_paired_t_and_hoeffding_fallback_on_exactly_constant_differences`.
9. (resolved) `scripts/memorycode_4c_release.py` is the only push path: statistical gate +
   accepted audit + passed verification, all bound to one package fingerprint and the same
   summary/qualification digests; immutable staging; rehash immediately before upload; release
   manifest with per-file hashes, upstream revision, digests, environment, decoding, inventory,
   HF commit and remote hash verification. `scripts/memorycode_4c_verify.py` builds a fresh
   pinned venv with an empty remote-code cache and replays 359-99 both flag states from the
   qualification receipts through the public API within `timeout 900`. Test
   `test_release_refuses_unverified_or_changed_bytes`.
10. (resolved) Checker hashes in the fingerprint; `reminder_sources` per focus arm (kept-sentence
    character spans with message index, eviction boundary, thread digest); registration wording
    restored to reminder/source offsets; progress logs carry no compliance scores; the summary
    is written once under `--terminal`, otherwise only completeness/cost (`progress-4c.json`).
    The tautological test assertion is replaced by explicit expectations.
