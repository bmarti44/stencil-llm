codex
NOT CLEARED. One CRITICAL semantic mismatch and two HIGH one-shot hazards must be fixed before certification.

## CRITICAL — certification bypasses the registered ledger-span guard

[g0_certify.py](/home/bmarti44/stencil-llm/scripts/g0_certify.py:82) defines “live” by value:

```python
has_live = any(cands[i][1] == live_val for i in typed)
chosen_live = cands[j][1] == live_val
```

Then [line 96](/home/bmarti44/stencil-llm/scripts/g0_certify.py:96) applies the chosen candidate whenever the predicted type exists in the ledger:

```python
if ty in spans:
    # applies cands[j]'s span
```

That is not the registered runner guard. [run_policy_session](/home/bmarti44/stencil-llm/src/stencil/t2_runner.py:225) applies only when the chosen span itself lies inside an authoritative ledger span.

The distractor generators do prevent deliberately conflicting notes from equaling the active value. But prompts also contain historical `user_set`/`user_update` sentences repeating the current ledger value. All 323 active trace events contained multiple same-value candidates. Trace cosine happened to choose the first—the authoritative ledger occurrence—323/323, but block A is not entitled to that assumption.

Current consequences:

- A same-value historical span can be counted as correct.
- It can be applied even though the real runner would reject it as out-of-ledger.
- That altered generation can change later timing events, feedback and assertion coverage.
- A resulting certificate would not certify the named runner-composed policy.

Fix by defining authoritative status from span containment, not value:

```python
chosen_span = cands[j][2]
authoritative = any(
    start <= chosen_span[0] and chosen_span[1] <= end
    for start, end in spans.values()
)

if float(cos[j]) > THR:
    if not authoritative:
        reasons.append(...)
    else:
        # apply chosen_span
```

Prefer running through `run_policy_session`, or extract one shared guard helper used by both paths. Add a test with two same-type, same-value candidates—one ledger, one historical—and force selection of the historical span. It must count as a pre-guard false selection and must not be applied.

## HIGH — s0x non-vacuity can be satisfied at the wrong work

[g0_certify.py](/home/bmarti44/stencil-llm/scripts/g0_certify.py:84) sets `assertion_met` at any work in the session. The registered fixture is specifically the injected hazard at the targeted final work. An earlier incidental inactive-type event can therefore satisfy the assertion even if the injected fixture never produces a timing fire.

Record `target_work` in `held_out["s0x"]`, then require all of:

```python
wt == target_work
ty == target
target not in sess.ledger_at[wt]
any(cands[i][1] == target_value for i in typed)
no authoritative same-type candidate
```

The generator insertion itself is otherwise sound: clear → injected note → two S0 notes → final work, with no update capable of reactivating the target. Work/turn indices are built after insertion, so the historical index-desynchronization bug is not repeated.

## HIGH — the sealed job is not fail-closed

[g0_certify.py](/home/bmarti44/stencil-llm/scripts/g0_certify.py:36) permits arbitrary `BLOCK` and `N`, defaults silently to A, loads a mutable unverified checkpoint, and overwrites any existing result. A smoke invocation with `N=1`, rerun after a crash, or wrong block value can consume sealed seeds outside the registered job.

Before execution:

- Hard-code this job to exactly block A and `N=160`, or require and strictly validate a frozen manifest.
- Assert no result or `.started` marker already exists.
- Atomically create a start manifest before the first seed; write the result through partial-file + rename.
- Hash-check and record the exact artifacts. Current hashes are:
  - selector: `e9922d703cbcf1a4f2cc127dab134ce44f679871df72949c9c8833047f08104f`
  - Qwen weights: `13bfabb5592c7b35383a56471fba1c74c771f57587322e60faaabb96268b2829`
  - tokenizer: `aeb13307a71acd8fe81861d94ad54ab689df773318809eed3cbe794b4492dae4`
- Move model loading under `main()` and add CPU tests for the pure failure/assertion logic.
- Perform any end-to-end smoke only on registered trace/development seeds.

The normalized cosine computation, type restriction, `>` threshold semantics, and first-index tie handling match `press_families.evaluate_event`. The corrected `nextafter` matrix, singleton abstention, counterfeit construction, and AUPRC-all implementation are sound. The 21 relevant CPU tests pass.

Process disclosure: while auditing the requested generator invariants, I instantiated block-A `s0x` sessions but did not run Qwen, timing/address heads, or observe policy scores/outcomes. Under the literal “fixture block untouched outside its sealed collection job” rule, that is still a metadata-level touch. The conservative playbook reading is to administratively void A and amend the named policy onto a fresh reserve block before any model execution.
