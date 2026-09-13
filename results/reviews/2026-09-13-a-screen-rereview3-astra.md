**The screen still cannot launch. It accepts replies that corrupt record identity or future inserts, and interrupted work still escapes the budget.**

Reviewed `69cedb54`. SCREEN `4f5d59eb87bb99f8` reproduces; all 576 TRAIN content hashes match. Containment against `52d9c31c` reports 39 changed slots and zero violations. I executed counterexamples through the unchanged scorer with authored tests imported in memory. The read-only sandbox prevented rerunning the subprocess-based 301-test suite. No GPU work or `data/bench/` access occurred.

| Finding | Disposition | Reason |
|---|---|---|
| F1 | **RESOLVED** | Every current file and required message survives all 48 capped-reply cases. [a_screen.py:140](/home/bmarti44/stencil-llm/src/stencil/a_screen.py:140) |
| F3 | **RESOLVED** | Resume preserves a complete unterminated record, discards malformed trailing content, and refuses incompatible records before generation. [a_screen_run.py:308](/home/bmarti44/stencil-llm/scripts/a_screen_run.py:308) |
| F12 | **PARTIAL** | The decision-changing aggregate and stratum defects are fixed; the new freeze check crashes on empty runs. [a_screen_summary.py:250](/home/bmarti44/stencil-llm/scripts/a_screen_summary.py:250) |
| F13 | **PARTIAL** | Recorded resident time carries forward, but time after the last record disappears. Over-budget final adapters can still qualify. [a_screen_run.py:350](/home/bmarti44/stencil-llm/scripts/a_screen_run.py:350) |
| F15 | **PARTIAL** | Evaluation fingerprints bind actual bytes. Training provenance still permits stale trainer/packing identities and binds the trunk only by pathname. [a_screen_train.py:234](/home/bmarti44/stencil-llm/scripts/a_screen_train.py:234) |
| Pool fixtures / F7 | **PARTIAL** | Both previous S01 mutations fail. New identity and counter mutations pass; a behavior-preserving private rename fails. [s01.py:211](/home/bmarti44/stencil-llm/src/stencil/a_screen_pool/s01.py:211), [s05.py:99](/home/bmarti44/stencil-llm/src/stencil/a_screen_pool/s05.py:99) |

**F1: the adversarial packing pair now works.**

My S03 first reply is gold padded inside the fence to **1,535 tokens**, reserving one token for EOS. The second reply is the **248-token** gold. Request 2 packs to **2,537 tokens**, retaining:

```text
[0, 9, 11, 13, 14, 15, 16, 19, 20]
```

Every current file is present, including `Fine` and `frozen=True`. Both checkpoints pass: **J = 1**. Changing the second reply to assign `fine.status` in place produces **J = 0**, correctly.

Across my 48 capped first replies, required messages plus files reached **2,380 tokens**, worst at S08; all packed prompts fit. The difference from §15’s 2,383 reflects different comment padding. Rule protection remains an explicit limitation of the screen’s claim, already disclosed. [packing:230](/home/bmarti44/stencil-llm/src/stencil/a_screen.py:230)

**Pool fixtures — high: changing a record’s identity still earns J = 1.**

Use S01’s **209-token** first gold reply. In second gold, change:

```python
tagged = replace(recipe, tags=recipe.tags + (tag,))
```

to:

```python
tagged = replace(recipe, recipe_id=tag, tags=recipe.tags + (tag,))
```

The second reply is **288 tokens**. All six checkpoint-2 suites pass; checkpoint 1 passes: **J = 1**.

After adding recipes A and B and tagging A with `"vegan"`:

```text
returned.recipe_id       = "vegan"
find(returned.recipe_id)  = None
find("R1").recipe_id      = "vegan"
count()                  = 2
```

The fixtures preserve tags, servings, title and neighbors but omit the updated record’s ID. The audit only enumerates **defaulted** fields, excluding `recipe_id`. [assertions:215](/home/bmarti44/stencil-llm/src/stencil/a_screen_pool/s01.py:215), [mutation fields:27](/home/bmarti44/stencil-llm/scripts/a_screen_mutate.py:27)

**Fix:** add a mutation class for changing required identity fields; assert identity preservation on both the returned record and public read-back.

**Pool fixtures — high: updates can corrupt the next insertion without failing.**

Insert `self._counter = 0` at the start of S05’s `member_renew`. With first gold, this **292-token** second reply earns **J = 1**. The public sequence is:

```text
enroll A → M1
enroll B → M2
renew M1
enroll C → M1
```

C overwrites A; count remains two. I also reproduced **J = 1** after the same insertion in S45’s `promote_lead`.

The strengthened fixtures check records already present. They do not consistently exercise creation **after** the new update. [allocator:39](/home/bmarti44/stencil-llm/src/stencil/a_screen_pool/s05.py:39), [renewal tests:265](/home/bmarti44/stencil-llm/src/stencil/a_screen_pool/s05.py:265)

**Fix:** add an allocator-reset mutation and a public create–update–create sequence asserting fresh identity and survival of earlier records.

**New fixture defect — medium: a correct implementation can receive J = 0.**

Consistently rename `self._members` to `self._records` in both S05 replies. Public behavior is unchanged. Checkpoint 1 fails only because the new fixture writes `r._members[...]`; checkpoint 2 fails its protected replay for the same reason. Both raise `AttributeError`. [s05.py:105](/home/bmarti44/stencil-llm/src/stencil/a_screen_pool/s05.py:105)

Requiring two records and preserving non-default attributes is legitimate: the request says to retain existing behavior. Requiring an undocumented private attribute name is an additional implementation constraint. Calling private seeding “weaker evidence” does not disclose that it rejects valid replies.

**Fix:** exercise renewal-count preservation through request 2’s public renew-then-freeze sequence and remove the new checkpoint-1 dependency on that private mapping.

**The five audit classes are useful, but their count overstates semantic coverage.**

All **292 generated mutants compile**; the longest fenced mutant is **630 tokens**. I found no reply-cap or syntax barrier making them impossible model outputs.

However, S47’s class-4 mutation adds `borrower=None` to a `Hold` update. `Hold` has no `borrower` field. It fails with:

```text
TypeError: Hold.__init__() got an unexpected keyword argument 'borrower'
```

That detects a wrong keyword, not erasure of an existing attribute. The generator gathers defaults across every record type without associating them with the updated type. [generator:63](/home/bmarti44/stencil-llm/scripts/a_screen_mutate.py:63), [record definitions:15](/home/bmarti44/stencil-llm/src/stencil/a_screen_pool/s47.py:15)

**Low; fix:** exclude or separately label nonexistent-field mutations when reporting preservation coverage.

The declined sixth class is **not generally observationally equivalent** to deletion: a wrong-key write can leave an extra entry, and ID/key confusion is a plausible programming error. Nevertheless, all **57 additional wrong-key writes** I executed across the 35 slots supported by my in-memory runner were detected. I found no independent sixth-class escape and would not demand extra machinery for it. Narrow §15.6’s categorical reasoning; prioritize the demonstrated identity and allocator escapes. [declined class:615](/home/bmarti44/stencil-llm/results/a-screen/REGISTRATION-A-SCREEN.md:615)

**F12 — medium: zero completed sessions now crash again.**

Three empty arm files produce `StopIteration` at:

```python
seen = next(iter(shared.values()))["pool_sha256"]
```

The `if not ids` branch comes afterward. The same problem occurs when records exist but no arm has a completed session. [a_screen_summary.py:256](/home/bmarti44/stencil-llm/scripts/a_screen_summary.py:256)

**Fix:** handle an empty `shared` collection before extracting its first identity and report INCOMPLETE.

For complete records, **the five gates remain §7’s gates**. Recomputing function-only from functional, regression and protected-function suites preserves its definition; manifest-derived lifecycle labels restore the frozen strata. The count thresholds are unchanged. [function-only:112](/home/bmarti44/stencil-llm/scripts/a_screen_summary.py:112), [gates:310](/home/bmarti44/stencil-llm/scripts/a_screen_summary.py:310)

The statistical calculations still agree: zero discordances at N=48 gives ±**0.087249**; exact McNemar gives **0.0625** for 5–0 and **0.25** for 3–0. Passing the count gates therefore remains a development decision, not evidence of statistical significance. [statistics:135](/home/bmarti44/stencil-llm/scripts/a_screen_summary.py:135)

**F13 — high: interrupted work still disappears from cumulative accounting.**

Executing the actual stamp and resume expressions:

```text
last record saved at 600 resident seconds
process dies at 900 resident seconds
resume starts with 600 seconds charged
```

The missing 300 seconds never enter another record. A launch that fails before writing its first record contributes **zero** prior spend. `resident_s` improves completed-work accounting but cannot account for interrupted work that has no record. [resume:350](/home/bmarti44/stencil-llm/scripts/a_screen_run.py:350), [stamp:417](/home/bmarti44/stencil-llm/scripts/a_screen_run.py:417)

**Fix:** retain launch-level elapsed spend, including failed/interrupted launches, independently of successful request records and charge it against the whole-screen ceiling.

**F13 — medium: the save reserve still permits over-budget completion.**

The periodic-save condition now reserves room for two estimated saves. That correction is sound. But `complete` depends only on positive steps.

I executed the actual `save(final=True)` function with a save starting at 14,390 seconds and taking 30 seconds. It wrote:

```text
seconds=14420, final=True, status="complete"
```

The adapter guard accepted it. Its runtime check imposes a lower bound only. [save status:275](/home/bmarti44/stencil-llm/scripts/a_screen_train.py:275), [runtime guard:208](/home/bmarti44/stencil-llm/scripts/a_screen_run.py:208)

Also, the microstep timestamp precedes `loss.item()`, leaving that synchronization outside the measured microstep duration. [timing:327](/home/bmarti44/stencil-llm/scripts/a_screen_train.py:327)

**Fix:** include synchronization in the measured step duration and mark/refuse an allocation that finishes beyond its registered budget.

**F15 — high: the guard still accepts an unverified training implementation.**

Executing the actual guard with the correct new recipe, pool, allocation, objective and trunk pathname still accepts:

```text
trainer_sha256 = old-code
a_screen_sha256 = old-packing
a_train_pool_sha256 = old-builder
```

Those recorded hashes are unchecked. The training identity also has no trunk-content fingerprint. Replacing weights at the same pathname between training allocations is therefore invisible to this check, even though evaluation now hashes the replacement bytes correctly. [training identity:234](/home/bmarti44/stencil-llm/scripts/a_screen_train.py:234), [guard:179](/home/bmarti44/stencil-llm/scripts/a_screen_run.py:179)

**Fix:** validate the recorded training implementation hashes and record/compare the training trunk’s byte fingerprint.

**Compute: §15.5’s arithmetic is correct; eligibility remains conditional.**

The full applied path requires **1,584 evaluation suites**, plus **132 pilot suites**. With the rerun reserve, the estimated remainder is **7,560 seconds**, or **4.41 seconds per invocation before other uncovered overhead**. Training loads, saves and CF reference scoring already charged inside the eight training hours must not be added again.

Resident time is the right pilot measurement, provided the pilot exercises the scoring work being extrapolated. Parse/application failures skip suites; their resident times cannot establish the cost of all 1,584 invocations. Charge the full scoring path within the existing pilot, include planned reloads, and apply the registered contention factor. [skipped scoring:460](/home/bmarti44/stencil-llm/scripts/a_screen_run.py:460), [compute:505](/home/bmarti44/stencil-llm/results/a-screen/REGISTRATION-A-SCREEN.md:505)

**Giving up the optional rerun reserve first is correct.** It preserves the registered arms, N and evaluation. It cannot forgive compute already consumed.

The shortest changes that would change my answer are:

1. Catch identity corruption and allocator resets with public behavioral checks.
2. Remove the new private-name constraint demonstrated by S05.
3. Handle empty summaries before identity extraction.
4. Account for interrupted launches and refuse over-budget training completion.
5. Bind adapters to the registered training implementation and actual training trunk bytes.

**DO NOT LAUNCH**
