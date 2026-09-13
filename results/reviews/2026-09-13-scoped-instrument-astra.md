**REPAIR. The reported defeat counts are real, but the soundness PASS is not earned.** I reproduced ordinary wrong implementations receiving all four passes, two wrong resolvers passing all 16 blocks, and an incomplete run receiving `RESCUED`. These are CPU repairs to the existing instrument. GPU use remains paused.

The prior review’s findings stand. I read no `data/bench/` and launched no GPU work. Filesystem permissions prevented direct writing; this is the review text for the calling workflow to capture. I reproduced the gate with package construction held in memory: zero reported problems, matching artifact digests, and the reported defeat counts. Under that substitution, **69 targeted tests passed; five filesystem/subprocess pipeline tests were deselected**. I also exercised the scorer in a separate CPU process with the same in-memory construction substitution. This does not constitute an unmodified reproduction of all 74 tests.

**1. High — Two plainly wrong resolvers pass 16/16; the added rivals do not close the construction question.**

These are general mistakes, not policies memorizing block IDs:

| Wrong policy | Reproduced result | Repair an existing block |
|---|---:|---|
| Resolve everything correctly except that reinstatement always restores the **first policy ever stated at that scope**, ignoring which version was referenced | **16/16 blocks pass** | In **R1**, place an earlier DEFAULT policy before the raise policy, and explicitly restore the second policy after its replacement. Correct restoration then yields raise; the shortcut yields DEFAULT. |
| Resolve policies correctly but treat **every logging obligation as package-wide**, ignoring its scope | **16/16 blocks pass** | In **R3**, make the obligation’s source explicitly compat-scoped and use compat/core applicability cases. The global-obligation shortcut must then fail the core case. |

I verified both proposed contrasts in memory: each defeats its respective shortcut while retaining different required values across the paired cases. R2 already tests preservation of a narrower rule across global reinstatement.

Every current reinstatement references the first policy at its scope. The only scoped obligation is in R3, whose two cases both fall inside its scope. Worse, its source text says “Every public function in the package,” while its hidden metadata says `compat`. [Development blocks](/home/bmarti44/stencil-llm/src/stencil/scoped_dev_blocks.py:246)

The two registered rivals are useful checks. Their 4/16 and 2/16 defeats do not establish restoration-reference resolution or obligation scoping. Nor does requiring each rival to *survive somewhere* establish soundness: a correct fixture could legitimately defeat a wrong policy everywhere. Delete that requirement; independently authored valid implementations provide the positive control. [Gate](/home/bmarti44/stencil-llm/scripts/scoped_gate.py:134)

There is also shared machinery behind the positive result: `gold_candidate()` and `evaluate()` both obtain their expected policy from `resolve()`. The oracle observes generated code behavior, but its requirement is not independent of the resolver. The statement that it never consults the history is false. Freeze explicit expected policy/support tuples for the existing cases, checked against their public wording, rather than treating agreement between these two calls as independent validation. [Oracle](/home/bmarti44/stencil-llm/src/stencil/scoped_blocks.py:414), [Gold generator](/home/bmarti44/stencil-llm/src/stencil/scoped_blocks.py:490)

**2. High — The executable oracle accepts materially wrong behavior.**

All three implementations below received:

`functional=True, contract=True, preservation=True, obligation=True`.

For **C4, compat bulk**, this passes:

```python
def gather_rates(table, keys):
    if any(k not in table for k in keys):
        return [None]
    return [table[k] for k in keys]
```

For `["beta", "gamma", "alpha"]`, it returns `[None]`, losing both present entries and their positions. The required result is `[22, None, 11]`. The functional suite tests only an all-present batch; the contract tests only a singleton missing batch. Furthermore, `observe()` examines only the first element of a nonempty list, discarding its remaining contents and length. [Observation](/home/bmarti44/stencil-llm/src/stencil/scoped_blocks.py:389), [Functional checks](/home/bmarti44/stencil-llm/src/stencil/scoped_blocks.py:432)

For **S1, compat lookup**, this passes:

```python
def fetch_rate(table, key):
    global lookup_price
    lookup_price = lambda table, key: None
    return table.get(key)
```

After invocation, the existing `lookup_price(table, "alpha")` returns `None` instead of `11`. Preservation checks existing functions’ **missing-entry classifications and logging membership**, not their present-entry behavior. [Preservation](/home/bmarti44/stencil-llm/src/stencil/scoped_blocks.py:446)

For **R1, core lookup**, this passes:

```python
def fetch_rate(table, key):
    if key not in table:
        raise MissingEntry(key)
    answer = table[key]
    note("fetch_rate")
    return answer
```

A missing-key invocation produces no audit entry. A successful invocation logs after accessing the table. Both violate the source’s requirement that logging occur first. The obligation suite calls only a present-key example and checks membership in `CALLS`; it never establishes ordering or logging on failure. [Obligation check](/home/bmarti44/stencil-llm/src/stencil/scoped_blocks.py:460)

Additional boundary errors:

- `raise MissingEntry("different-key")` passes the contract requiring `MissingEntry(key)`.
- A tuple-returning bulk implementation produces the correct ordered entries but fails `observe()`, although neither the request nor the semantics specifies a list return type. The functional suite itself accepts that tuple by converting it to a list.

Repair the existing suites with complete mixed-batch observations, exception payload checks, present and missing behavior for preserved functions, and logging checks on successful and exceptional paths. Specify the output container contract publicly.

Preserving `block.precedent` is **the correct target under the stipulated prospective semantics**. Replacing that target with the currently resolved policy would incorrectly demand retroactive changes. The defect is the narrow observation of that precedent.

Finally, “first statement” is a syntactic requirement that this behavioral oracle cannot generally establish. Prefer an observable requirement such as logging before table access, including failed lookups, and test that ordering with an instrumented mapping.

**3. High — The model does not receive the complete contract the hidden oracle enforces.**

The actual generation path bypasses `arm_payload()` and constructs its own prompt containing only the target module. Consequently, **C4/core never receives the package docstring establishing DEFAULT as the baseline**. It sees entering code that raises, a cancelled None policy, and a request to follow documentation that is absent. Even the oracle reminder merely says that the documented default applies. [Prompt construction](/home/bmarti44/stencil-llm/src/stencil/scoped_blocks.py:809), [Package baseline](/home/bmarti44/stencil-llm/src/stencil/scoped_blocks.py:174)

This is missing task information, not an instruction-resolution failure.

There are further public/hidden mismatches:

- Histories repeatedly name `compat.py`, while the actual requested file is `compat/__init__.py`.
- R3’s package-wide obligation text carries compat-only metadata.
- G1 and G2 announce a change “for the whole package” while the hidden semantics retain an operation-specific exception.
- The prospective default and precedence convention are defined in `SEMANTICS.md`, which the model is explicitly not given. Natural-language instructions do not uniquely imply those conventions. [Semantics](/home/bmarti44/stencil-llm/results/scoped/SEMANTICS.md:9), [Global revisions](/home/bmarti44/stencil-llm/src/stencil/scoped_dev_blocks.py:106)

Repair the shared public prompt with the package baseline and concise governing conventions; use actual paths and align source wording with metadata. Do this equally for both conditions. These are task specifications, not gold labels.

The existing payload checks found no direct event-label leakage, but they validate a serializer the runner does not consume. Test the actual generation input.

**4. High — “Thinking disabled” is registered but not implemented.**

The runner tokenizes the raw text directly and passes it to `model.generate()`. It never applies the chat template, establishes an assistant generation boundary, or disables thinking. Greedy decoding does not perform those operations. [Generation path](/home/bmarti44/stencil-llm/scripts/scoped_rescue.py:135)

The shipped tokenizer template explicitly implements `enable_thinking=False` by adding the assistant prefix and empty thinking block. I rendered that template on CPU; neither appears in the current prompt. This agrees with the [official Qwen instructions](https://qwen.readthedocs.io/en/v3.0/getting_started/quickstart.html).

Thus a failure could reflect raw continuation formatting or consumption of the 160-token allowance by reasoning. The current stub tests cannot detect this because their replies are supplied independently of the prompt.

Apply the existing tokenizer’s non-thinking chat template in both conditions, count the actual resulting input tokens, and test that exact path on CPU. Keep the registered trunk and greedy decoding.

**5. High — Incomplete, incompatible, and timed-out records can acquire an efficacy reading.**

Through the actual `summarize()` consumer, I supplied a plausible **48-record prefix**: the first 12 blocks completed in both conditions, with oracle successes and off failures. Four blocks had no records. It printed:

> `READING: RESCUED -- raise direction 1 from 28% to about 40%`

Missing cases are converted into failures before applying the efficacy thresholds. This violates both the registration’s INCOMPLETE rule and the owner’s requirement that positive claims use the full registered N. [Summary](/home/bmarti44/stencil-llm/scripts/scoped_rescue.py:212), [Owner rule](/home/bmarti44/stencil-llm/plan/BACK-ON-TRACK-PLAN.md:244)

Related defects affect the same consumer:

- Resume identifies completed work only by block/case/condition. Records contain no stub marker or run identity binding them to model, fixture, prompt builder, scorer and generation settings.
- Duplicate keys silently overwrite earlier observations in the summary.
- `timed_out=True` does not prevent `ok=True` from counting as success.
- A scorer timeout raises `TimeoutExpired` out of `score()`; it aborts before the generation record is saved. Resuming can regenerate the same item.
- A crash during JSONL append can leave a partial line that prevents resume. “Atomically per generation” overstates the implementation. [Resume and records](/home/bmarti44/stencil-llm/scripts/scoped_rescue.py:115), [Scorer invocation](/home/bmarti44/stencil-llm/scripts/scoped_rescue.py:71)

Require the exact 64 unique compatible records before any efficacy reading. Distinguish stub records, enforce registered timeout handling, preserve the generation receipt when scoring fails, and reject incompatible resumes. An incomplete dataset must stop at `INCOMPLETE`.

**6. High — The registered pilot and spending ceiling are prose, not enforced behavior.**

There is no pilot mode, selection of the four longest cases, projection calculation, or refusal above 0.5 GPU-hours. The supplied command starts the ordinary run immediately.

The command reserves **30 minutes** but gives the runner **45 minutes**. The runner’s default budget is unlimited. Its timer starts after model loading, resets on resume, and allows a generation to start whenever the current elapsed time remains below the limit, without reserving time for generation and scoring. The reservation wrapper records an ETA; it does not enforce a deadline. [Registration](/home/bmarti44/stencil-llm/results/scoped/RESCUE-REGISTRATION.md:85), [Runner budget](/home/bmarti44/stencil-llm/scripts/scoped_rescue.py:165), [Reservation wrapper](/home/bmarti44/stencil-llm/tools/gpu_reserve.sh:55)

Implement the already registered pilot and spending check in the existing runner. Use one cumulative accounting definition across pilot, evaluation and resumes, and align the reservation with it. No GPU execution is authorized by this review.

The **0.2–0.3-hour estimate is plausible, but not measured**:

| Total generation allowance, including the 1.5 factor | Required mean seconds/generation |
|---|---:|
| 0.2 hours | 7.50 |
| 0.3 hours | 11.25 |
| 0.5 hours | 18.75 |

These figures exclude loading and other resident overhead. The maximum output is `64 × 160 = 10,240` tokens. Using only the prior review’s measured workload ratio, `36,551 / 3,516.49 = 10.39` output tokens/second, gives:

| Mean generated tokens | Projected generation hours with 1.5 factor |
|---|---:|
| 64 | 0.164 |
| 100 | 0.257 |
| 160 | 0.410 |

That ratio came from a different workload and is not a calibrated prediction here.

A 4B bf16 trunk is roughly 8 GB of weights. At the GB10’s specified 273 GB/s bandwidth, a simplified full-weight streaming calculation gives about 29 ms/token before other costs. This is a hardware sanity check, not attainable application throughput. It neither disproves the estimate nor establishes it. [NVIDIA hardware specification](https://docs.nvidia.com/dgx/dgx-spark/hardware.html)

The already registered pilot must measure actual output lengths, EOS/cap/timeout frequency, generation time, loading and scoring overhead, total resident time, memory peak and concurrent load. Include the eight pilot generations in the accounting; state whether they are retained or repeated. Longest prompts alone do not guarantee the longest outputs.

**7. Medium — The reminder is an answer key for applicability, and that is acceptable only within the diagnostic claim.**

Quoting the **winning** statement under “Instruction in force for this edit” provides privileged selection information. In this three-value task, that often supplies nearly the entire behavioral decision. Reinstatement reminders additionally resolve the historical reference.

Calling it “source text” does not remove that privilege. The banned-substring test establishes only that certain code spellings are absent. [Reminder renderer](/home/bmarti44/stencil-llm/src/stencil/scoped_blocks.py:769), [Reminder test](/home/bmarti44/stencil-llm/tests/test_scoped_rescue.py:66)

This is nevertheless consistent with the intended diagnostic: can the model implement a task when correct applicability is supplied? It becomes uninterpretable only if presented as evidence that the automatic compiler can identify that instruction, or that compilation beats ordinary source memory.

Delete the registration’s assertion that rescue cannot be attributed to length because the text is duplicated. Duplication changes length, repetition, position and salience; the privileged header changes authority. The present comparison does not separate those mechanisms. No extra arm is needed—narrow the attribution. [Registered limitation](/home/bmarti44/stencil-llm/results/scoped/RESCUE-REGISTRATION.md:71)

Likewise, failure of this particular cue is not a mathematical demonstration that no compiler can help. The prior review explicitly rejected that upper-bound interpretation. A negative result can justify the registered spending stop without proving impossibility. [Registration’s stronger claim](/home/bmarti44/stencil-llm/results/scoped/RESCUE-REGISTRATION.md:7)

**8. Medium — The semantics are defensible stipulations, but their limits and one support-rendering defect need recording.**

Non-reviving cancellation, explicit restoration, independent policy/obligation state, and a distinguishing DEFAULT baseline are coherent choices. They are not universal interpretations of conversational instruction changes. A coding user can reasonably intend “cancel that change” as an undo. State the chosen protocol publicly.

Several details need correction:

- “Reinstatement is the ONLY way an earlier value returns” is false literally: a new `set` can repeat that value, and cancellation can expose an enclosing live rule with it. Distinguish restoration of a superseded **statement** from recurrence of a **value**.
- The resolver’s `clears` operation is absent from the frozen semantics. It clears exact named path scopes, not their descendants.
- Path depth outranks operation specificity by stipulation. That tie-free ordering is internally consistent for these hierarchical scopes; it is not a general rule of instruction interpretation.
- Every development block has at most one distinct obligation support. The fixture tests independence from policy changes, not survival after one of multiple supports is withdrawn.

There is also an executable defect in `resolve_events()`: it finds live obligation **names**, then returns every historical obligation event with those names. I supplied package-wide and compat-only supports for `note`, then released the package-wide support. The compat reminder still included both sources, including the released package-wide statement. Filter by surviving, applicable supports rather than name alone. [State reducer](/home/bmarti44/stencil-llm/src/stencil/scoped_blocks.py:109), [Support selection](/home/bmarti44/stencil-llm/src/stencil/scoped_blocks.py:784)

This does not currently change a recorded development outcome, because the necessary multiple-support case is absent. Repair the existing helper; do not claim that behavior was validated by the present blocks.

**9. Medium — Register the remaining limits before the result exists.**

The write-up should say explicitly:

- These are independent, single-function additions with fresh entering repositories, not continuing coding sessions. There is no accumulated edit state, tool-feedback loop, context turnover or automatic extraction.
- The append-only extraction interface preserves existing source structurally. Preservation failures can still occur through runtime side effects, but this is a much narrower maintenance task than general code editing.
- All 16 blocks share one rate-table package and a small implementation vocabulary. They are 16 authored contrasts, not 16 independent repository samples.
- Direct/revised/irrelevant variants exist, but the registered runner uses only revised histories. It does not estimate the advertised economics contrast.
- A separate scorer process supplies crash separation and a timeout, not a filesystem or information-access sandbox. The claim that model output uses the repository’s existing sandboxed path is inaccurate.
- A correct multiline function signature can be damaged by the line-based extractor. I reproduced a valid function passing directly, then failing after extraction reduced it to `def fetch_rate(`. Use syntax-aware extraction or explicitly narrow the accepted response grammar. [Extractor](/home/bmarti44/stencil-llm/scripts/scoped_rescue.py:53)

**Low — Correct the descriptive arithmetic and decision wording.** Using the shipped tokenizer JSON, I reproduced the stated token extrema and reminder increments. The off median was **214.5**, and histories contain **2–6 messages**, not 3–7. Gold functions occupy only **13–40 tokens**; actual model output lengths remain unknown.

The thresholds are investment rules, not significance tests: six wins and one loss gives exact two-sided paired sign-test **p=0.125**; six wins and no losses gives **p=0.03125**. Report uncertainty without translating `RESCUED` into proof. Give ceiling outcomes a consistent explanation: successful baseline performance establishes little reminder headroom, not inability to implement the task. The current summary prints both explanations.

**My artifact-success forecast remains 28%, unchanged.** The CPU work supplies no model-efficacy evidence that warrants raising it. The defects invalidate this instrument’s current PASS, but they are local repairs rather than evidence against the proposed mechanism. A sound construction gate was already assumed in the prior forecast; achieving it alone does not earn 40%.

Repair the existing blocks, public prompts, behavioral checks and runner. Retain the same 16 blocks, two conditions and trunk; add no model, benchmark or review stage. Open high findings block acceptance irrespective of the direction’s forecast clearing 25%.

VERDICT — REPAIR — 28% artifact-success forecast — The current PASS does not justify GPU spending; repair the existing CPU instrument and runner while the owner’s GPU pause remains in force.
