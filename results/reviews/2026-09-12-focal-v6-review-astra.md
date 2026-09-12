**V6 qualifies no arm for continuation. But its headline ranking is misleading: the pilot uses a different score from the existing query-required score, and that difference reverses two mean comparisons.** The indentation repair worked on the observed failures. It did not establish a fair placement comparison or produce a functionally sound winning candidate.

I read the requested code, records, earlier reviews, ledger entries, and commit changes. I did not read `data/bench/`, run a language model, or modify files. All 15 stored v6 scores reproduce through the vendored checker. The six detector tests passed; the nine runtime test bodies also passed using the package’s local tokenizer through a lightweight adapter. The normal Transformers fixture could not initialize because this read-only environment prevents its temporary-cache setup.

**1. Bugs**

The severities below distinguish observed v6 defects from latent defects demonstrated with small CPU fixtures.

**B1 — High: the pilot scores unrequested structure and omits the existing required-structure penalty.**

[`score()`](/home/bmarti44/stencil-llm/scripts/focal_quicklook.py:48) averages every `history_regex` check, replacing every absent-object `None` with zero. It does not use the query’s required families or require the requested structure. That is different from [`fraction_required()`](/home/bmarti44/stencil-llm/src/stencil/memorycode.py:380).

This affects **every item and arm**, and materially changes the reading:

- **314-49 requests a function.** `before_compact` supplies a class containing a method, receives 10/22, and beats the header arm’s 8/22. Under the existing required score, the missing function makes `before_compact` zero; the header arm gets 8/11 and `user_phased` gets 10/11.
- **186-14 requests a class.** Three function-side checks unnecessarily depress every score.
- **184-14 requests a function.** `before_compact` earns 3/9 entirely from class/method conventions despite producing no checker-recognized function. Every arm gets zero on the existing required score.

Sources: [item definitions](/home/bmarti44/stencil-llm/results/memorycode-long/items.json:484), [314-49 before output](/home/bmarti44/stencil-llm/results/focal/quicklook-v6.json:397), [184-14 before output](/home/bmarti44/stencil-llm/results/focal/quicklook-v6.json:5390).

An all-register score can be reported descriptively. It cannot be presented as the existing required-rule measure. My earlier recommendation to preserve that measure was not implemented.

**B2 — High: detector and checker disagree about nested functions inside methods.**

The detector treats a function nested inside a method as a **function**, because it uses the nearest enclosing definition. The checker keeps `current_class` active throughout traversal and treats that same nested function as a **method**. See [detector scope](/home/bmarti44/stencil-llm/src/stencil/focal.py:153) and [checker traversal](/home/bmarti44/stencil-llm/vendor/memorycode/code/extract_objects.py:118).

This occurs in **184-14, `user_phased`**. The runtime delivers function rules to nested `validate`; the checker includes `validate` among methods. Consequently:

- Function checks find no functions.
- Method naming checks include the nonconforming helper.
- Method docstring and try checks fail because the helper lacks those features, despite their presence on the outer method.

The [events and output](/home/bmarti44/stencil-llm/results/focal/quicklook-v6.json:6592) show the disagreement directly. This changes the explanation of its 1/9 score. It does not make the output fully compliant.

**B3 — High: the vendored checker measures substantially less than the convention wording suggests.**

These are actual checker behaviors, not speculation:

| Checker defect or limitation | V6 consequence |
|---|---|
| `ImportFrom` is ignored. | **314-49 `user_phased`** receives zero for importing `gzip` despite generating `from gzip import compress, decompress`. Whether that statement satisfies the intended convention needs an explicit definition. |
| Decorators are checked by terminal name, without validating their source module, availability, application, or additional invalid decorators. | All focal arms on **186-14** receive decorator credit for unbound `retry`. **314-49 `user_phased`** receives decorator credit despite an undefined self-decorator. |
| Regex checks inspect only `obj[0]`. | Only the first argument of each function and first extracted attribute of each constructor are checked. CPU fixtures with a compliant first name and noncompliant second name pass. No demonstrated v6 score change from this particular defect. |
| An annotation check means at least one collected annotation per function/method. | It does not establish complete annotations; positional-only, keyword-only and variadic arguments are not collected. |
| Try/assert and constructor-attribute extraction examine direct body statements only; annotated attributes are omitted. | Nested constructs can be missed. The typed `self.songs` assignments in **186-14** produce empty attribute lists, although that item has no attribute check. |
| `AsyncFunctionDef` lacks equivalent handling. | Latent for this pilot; ordinary async functions escape function scoring. |
| Comments are found by `#.*`, including inside strings. | Latent false credit; a string containing `"# not a comment"` passes the comment-presence check. |

Sources: [score quantifiers](/home/bmarti44/stencil-llm/vendor/memorycode/code/evaluate_model_output.py:30), [annotation/body/attribute extraction](/home/bmarti44/stencil-llm/vendor/memorycode/code/extract_objects.py:49), [import/comment extraction](/home/bmarti44/stencil-llm/vendor/memorycode/code/extract_objects.py:167).

The comment pair branch also compares against a nested list of comments incorrectly; this is latent because v6 uses a Boolean comment check.

These limitations are partly inherited, but focal delivery changes syntax and structure, so their errors need not cancel between arms.

**B4 — High: special-method protection is still incomplete.**

Two separate defects remain:

- For decorated units, the runtime tests identifier completeness using the **decorator line** and the existence of any following newline. It can act before the method name is complete. A tokenizer-backed fixture containing decorated `__init__` fires ordinary method rules when its name is only `"__"`.
- The runtime excludes names that both start and end with `__`; the checker excludes ordinary method checks for **every name starting with `__`**, including `__private`.

Sources: [dunder predicate](/home/bmarti44/stencil-llm/src/stencil/focal_runtime.py:105), [completeness test](/home/bmarti44/stencil-llm/src/stencil/focal_runtime.py:329), [checker exclusion](/home/bmarti44/stencil-llm/vendor/memorycode/code/extract_objects.py:132).

The first defect explains prematurely recorded names such as `"roman"` and `"is"` in v6 decorated-function events. **No v6 constructor rename is demonstrated**; the damaging special-method case remains latent.

**B5 — High: the lexer still admits false triggers and misses valid units.**

CPU witnesses reproduce all of the following:

- `s = "("` suppresses a subsequent real function because brackets inside strings affect depth.
- `f(  # )` lets a subsequent keyword argument look like an assignment because brackets inside comments affect depth.
- Triple-quote state does not retain the opening delimiter. A `'''` inside a `"""` string exposes a fake function.
- `"""don't"""` can leave the scanner incorrectly inside a string.
- Fence-looking lines inside triple-quoted strings reset lexical state and expose fake code.
- A bare-code string containing `` ``` `` makes auto-detection switch to fenced mode and miss real code.
- Multiline function signatures do not produce body events.
- One-line function bodies, annotation-only assignments, tuple assignments, and additional statements on a line lack the advertised coverage.
- Indentation counts characters and re-feeds spaces; tabs are not preserved correctly.

Sources: [lexical helpers](/home/bmarti44/stencil-llm/src/stencil/focal.py:120), [scanner](/home/bmarti44/stencil-llm/src/stencil/focal.py:160), [body detection](/home/bmarti44/stencil-llm/src/stencil/focal.py:244).

**I did not establish these lexical edge cases as causes of the v6 outcome.** They invalidate broad coverage and safe-insertion claims. Complete-output replay does not qualify these incremental cases.

**B6 — High for coverage: some rule packets are silently undeliverable.**

Three demonstrated cases:

- An `any`-only rule set never fires: those rules only accompany another nonempty packet.
- With `phased=False`, attribute rules are never delivered. They belong to `init/body`, but unphased packet selection accepts only headers, while constructor headers are skipped.
- When a method’s first body statement is a nested function, delivering the method-body cue can make the rollback floor prevent the nested function’s header cue. A tokenizer-backed fixture delivers only the body packet.

Sources: [packet selection](/home/bmarti44/stencil-llm/src/stencil/focal_runtime.py:175), [trigger selection](/home/bmarti44/stencil-llm/src/stencil/focal_runtime.py:299), [rollback floor](/home/bmarti44/stencil-llm/src/stencil/focal_runtime.py:361).

These are latent in the supplied v6 trajectories. The unphased attribute defect concerns **314-49’s header arm**, although that trajectory never produces a constructor anyway.

Separately, `deliver="first"` is intentionally **once per kind/phase**, not every governed unit. It must not inherit the proposal’s “every unit” guarantee.

**B7 — High: re-feed can still preserve an incompatible syntactic choice.**

The decorator-positive fix does not cover the general problem:

- An existing `@` is always re-fed, including when a rule prohibits decorators.
- An import trigger beginning with `from` re-feeds `from`, although the checker credits only `import` statements.
- Rules specifying decorator dependencies can arrive after the relevant import opportunity, with an `@` prefix preventing an import before that decorator.

Source: [keyword selection and re-feed](/home/bmarti44/stencil-llm/src/stencil/focal_runtime.py:370).

The import issue occurs in **314-49’s focal arms**. Missing decorator bindings occur in **186-14’s three focal arms** and **314-49’s comment arms**. These are material functional defects, even when the convention checker awards points.

The new indentation routine fixes the observed extra space. Its test assumes continuation along a fixed target tokenization; it does not prove that a changed model continuation will use that segmentation.

**B8 — Medium: user-channel token provenance and rollback events are wrong.**

Each user-channel rebuild replaces the entire retained answer prefix with one `"keep"` piece. Earlier model-selected tokens disappear from `generated_ids`, although they remain in `text`. The event’s rollback count is then computed after that replacement, so it includes retained tokens.

Source: [user rebuild and event recording](/home/bmarti44/stencil-llm/src/stencil/focal_runtime.py:425).

| `user_phased` item | Retained model selections: `steps − discarded − EOS` | Reported `n_generated` | Sum of event rollback counts | Actual `discarded_tokens` |
|---|---:|---:|---:|---:|
| 314-49 | 555 | 403 | 163 | 11 |
| 186-14 | 164 | 117 | 57 | 10 |
| 184-14 | 300 | 83 | 235 | 18 |

`refed_tokens` also omits the bulk of repeated prompt/prefix processing. **The text and its score are not lost. The output-token and work-accounting interpretation is wrong.** Wall-clock `seconds` still measures the elapsed generation call.

**B9 — High: the total-context limit is checked incorrectly and too late.**

The loop counts `pending` twice because those tokens are already in `pieces`. It also appends forced comment tokens before checking their size, and user-channel rebuilding performs the expanded prefill before checking the new context.

Sources: [loop guard](/home/bmarti44/stencil-llm/src/stencil/focal_runtime.py:231), [comment insertion](/home/bmarti44/stencil-llm/src/stencil/focal_runtime.py:401), [user prefill](/home/bmarti44/stencil-llm/src/stencil/focal_runtime.py:425).

With a 20-token limit, CPU fixtures produced:

- Plain output stopping at 19 total tokens.
- Comment-channel result containing 78 total tokens.
- User-channel prefill processing 43 total tokens.

**This did not determine v6:** no record reports context exhaustion, and the capped 314-49 phased trajectory totals only **3,462 tokens**, including forced tokens. Its problem is repetition exhausting the selection cap.

**B10 — High as an experimental control: periodic delivery is still not matched.**

The periodic branch:

- Sends the entire remaining rule set, not the same phased packets.
- Ignores `deliver="first"` and can send every rule three times.
- Ignores `channel="user"` and inserts comments anyway.
- Uses generated code-line counts, so placement and delivery count depend on the arm’s trajectory.
- Depends on token boundaries ending exactly at a newline.
- Does not prevent accidental alignment; it only records adjacency afterward.
- Inherits the scanner defects and has no equivalent rollback/re-feed operation.

Source: [periodic branch](/home/bmarti44/stencil-llm/src/stencil/focal_runtime.py:257).

A CPU fixture with `policy="periodic", deliver="first", channel="user"` produced **three comment insertions and no user reminders**.

**No periodic arm exists in v6**, so this does not change its arithmetic. Neither v6 nor the older periodic results establish an alignment advantage.

**B11 — Medium: echo counting is a prefix detector, not an imitation measure.**

[`count_echoes()`](/home/bmarti44/stencil-llm/src/stencil/focal.py:310) counts only three literal prefixes, without distinguishing code, strings, or prose.

Examples it misses:

- **184-14, both comment arms:** `# and the '@trace_method' decorator to all methods.` invents and extends a convention, while `echoed_lines=0`.
- **314-49, `user_phased`:** several generated comments restate naming and decorator requirements, while `echoed_lines=0`.

Sources: [184-14 header text](/home/bmarti44/stencil-llm/results/focal/quicklook-v6.json:6101), [314-49 user text](/home/bmarti44/stencil-llm/results/focal/quicklook-v6.json:3048).

The reported 67 prefix matches in **314-49 `focal_phased_compact`** are real. Its “60 repeated-line runs” are overlapping six-line windows, not 60 independent loops. The code correctly leaves generated echoes in the scored output.

**B12 — Medium: parse and failure measurement miss important failures.**

[`parse_status()`](/home/bmarti44/stencil-llm/scripts/focal_quicklook.py:69):

- Marks an empty code block as parsing successfully.
- Detects only six identical successive nonblank lines, missing alternating or larger repeated blocks.
- Uses the first extracted code block; later broken blocks are ignored.
- Cannot establish compilability, dependency resolution, task correctness, or preservation of the requested interface.

The scorer also catches every exception and silently turns it into zero. That conflates checker failure with model failure. I encountered no such exception when reproducing v6.

These defects affect the **interpretation of every arm’s status**. The missed functional failures are observed in v6; the empty/multiple-block cases are latent.

**B13 — Medium: the summariser implements an underspecified and weakened gate.**

[`failures()`](/home/bmarti44/stencil-llm/scripts/focal_quicklook_summary.py:16) adds failure categories rather than counting failed outputs. Thus its **+3** for the phased arm means **one additional failed output with three flags**, not three additional failed outputs. Summing categories can also trade fewer flags on one item against newly failing other items.

Further problems:

- `context_exceeded` and timeouts do not enter the gate.
- Missing parse information defaults to success.
- Missing arm records are dropped; `wins >= 2` is accepted without requiring three complete, unique item pairs.
- Any noncontrol arm can qualify; no prespecified candidate is enforced.
- The original requirement of **no new functional breakage** disappeared.

Sources: [comparison logic](/home/bmarti44/stencil-llm/scripts/focal_quicklook_summary.py:49), [original gate](/home/bmarti44/stencil-llm/results/reviews/2026-09-12-focal-rootcause-astra.md:215).

**None changes v6’s gate failure.** The omitted functionality condition makes its practical assessment too lenient.

**B14 — Medium: the artifact writer does not preserve the promised audit trail or write each arm immediately.**

Records are written only after all five arms finish, by overwriting the JSON. A crash can lose completed arms or leave a partial file. The artifact omits exact prompts/history boundaries, complete output token sequence with provenance, forced-token IDs, per-check outcomes, runtime/configuration hashes, and timeout status.

Sources: [record schema](/home/bmarti44/stencil-llm/scripts/focal_quicklook.py:177), [write location](/home/bmarti44/stencil-llm/scripts/focal_quicklook.py:295).

The base identity check only records a Boolean; it does not stop on failure. The unused `text_for_score` parameter is a low-severity interface defect, though every current call supplies the same text.

**V6 is complete**, so no completed arm was lost here. Exact reconstruction and qualification claims remain weaker than the records suggest.

**B15 — Medium: active-runtime qualification is missing, and Stage 0 does not supply it.**

I found no demonstrated off-by-one error in `HFBackend.crop`; its drop-and-refeed convention is internally consistent. But plain-loop identity does not test active cache cropping against recomputing the same edited token prefix.

The scripted backend follows a fixed target and removes cue lines. It cannot establish how an actual model responds to the edited prefix.

Moreover, [`focal_stage0.py`](/home/bmarti44/stencil-llm/scripts/focal_stage0.py:96) calls the detector on complete outputs, not successive generation prefixes. Its AST reference also disagrees with the vendored checker about nested methods. The new body events are absent from its reference units and would be counted as false fires. The old Stage 0 result does not qualify the current runtime.

Two repairs do check out: **the frozen-history construction no longer re-fits history separately for reminder arms**, and **v6’s recorded cue spans are disjoint, cover the inserted cue lines, and strip correctly**. I found no v6 score corruption from span stripping.

**2. Validity**

**No: v6 is a delivery-policy debugging comparison, not a fair isolation of placement.**

The common history is a real improvement. The pilot builds the base prompt once and inserts additional text into that same string, avoiding the earlier extra-history-eviction confound. But the following differences remain:

- **Wrongly described control location.** `before_compact` is appended **after the request**, before the assistant opening. It is a before-generation control, not the advertised before-request control. See [suffix construction](/home/bmarti44/stencil-llm/scripts/focal_quicklook.py:157).
- **Different delivered information.** The reminder sees all 22/9/9 rules. Comment arms deliver only **11/6/4** rules on the respective items. `user_phased` delivers **11/6/9**. Rules for absent structures never arrive, and before-generation rules can change which structures are planned.
- **Different wording, grouping and channel.** The reminder adds “Conventions still in force” and uses prose packets. Comment arms use `# For this …`; the header arm merges body rules into header packets.
- **Different computational intervention.** Focal arms discard selections and force continuation prefixes. The user arm rewrites the instruction prompt and recomputes the retained answer under it. That is more than moving identical tokens within an otherwise identical sequence.
- **Unmatched token exposure.** Base prompts have 1,792 tokens. Before prompts have **2,139/1,916/1,928**. Phased comment insertions add **142/75/57** tokens; final user prompts have **1,945/1,877/1,922**. Reporting these differences does not match them.
- **Oracle scope only.** Both treatment and reminder derive rules from the same oracle, which is reasonable for isolating delivery. It tests neither classifier admission nor lifecycle maintenance. The source is [label-derived live instructions](/home/bmarti44/stencil-llm/src/stencil/memorycode.py:192).
- **Selected, exposed items.** These three were explicitly chosen after earlier trajectories were inspected. The overload item was intentionally deferred. That is acceptable debugging, but does not support a population effect or novelty claim.
- **No interaction measurement.** There are no matched, predeclared unit positions, no valid periodic comparator, and no independent manipulation of irrelevant-rule load.
- **Budget interpretation differs.** The 1,536 cap now bounds total selections, including discarded selections and EOS. It is an equal selection-work cap, not an equal retained-output allowance.

The before arm’s tendency to build a class for a function request illustrates the central confound: global rule exposure changes task planning before focal delivery gets its first opportunity.

**3. Reading**

Using the summariser exactly as written:

| Arm | 314-49 | 186-14 | 184-14 | Mean | Difference from before | Wins | Gate |
|---|---:|---:|---:|---:|---:|---:|---|
| `base` | .136 | .222 | .000 | .120 | — | — | — |
| `before_compact` | .455 | .667 | .333 | .485 | — | — | — |
| `focal_header_compact` | .364 | .556 | .111 | .343 | −14.1 points | 0/3 | Fail |
| `focal_phased_compact` | .000 | .556 | .111 | .222 | −26.3 points | 0/3 | Fail |
| `user_phased` | .455 | .667 | .111 | .411 | −7.4 points | 0/3 | Fail |

Source: [v6 log](/home/bmarti44/stencil-llm/results/focal/quicklook-v6.log:9). The phased arm adds one failed output, producing the summariser’s three additional failure flags.

Re-scoring the **same outputs**, without regeneration, through the existing query-required measure gives:

| Arm | 314-49 | 186-14 | 184-14 | Mean difference from before |
|---|---:|---:|---:|---:|
| `before_compact` | .000 | 1.000 | .000 | — |
| `focal_header_compact` | .727 | .833 | .000 | **+18.7 points** |
| `focal_phased_compact` | .000 | .833 | .000 | −5.6 points |
| `user_phased` | .909 | 1.000 | .000 | **+30.3 points** |

That is a diagnostic re-score, not a replacement registration. **No candidate wins two items under this measure either.**

V6 shows:

- The observed indentation defect was real and repairable.
- Local delivery can elicit naming, decorator and body features.
- Phased comments can still initiate severe repetition.
- User-channel delivery avoids that particular loop in these records.
- No candidate meets the written continuation gate.

It does **not** show that focal placement generally reduces required-rule compliance, that the user arm is equivalent to the reminder, that the proposed interaction is absent, or that high convention scores imply working code.

I agree with a demanding practical gate before spending the remaining cohort. I do **not** agree with this gate’s current measurement implementation or with treating it as a scientific decision rule for D. Restore the intended score, functional condition, complete-pair requirement and explicit failure definitions. Keep practical magnitude separate from statistical evidence.

**4. Direction**

**My decision is: stop this configuration; do not advance it to a registered screen now.**

The decisive reason is **the absence of a qualifying, functionally sound candidate**, not the misleading negative all-check means. Correcting the score still produces only one winning item. The user arm’s strongest apparent success contains both an undefined decorator and an incorrect algorithm.

This is consistent with the earlier reviews: D’s interaction remains unproven rather than disproved, while the bounded cue-only configuration has reached its practical stop. “Not disproved” was never evidence that this implementation deserved continued development.

If D is later pursued as a modified scientific screen, these are the minimum requirements—not another wording-search cycle:

- **Runtime:** resolve detector/checker scope; repair lexical and multiline boundaries, special methods, packet collisions and undeliverable packets; preserve dependency and decorator opportunities; enforce context limits before insertion/prefill; retain complete token provenance; qualify active cache continuation.
- **Arms:** freeze one candidate and the precise control location; use common history and explicitly matched rule content, packet rendering, copy counts and budgets for the alignment comparison; repair the already-proposed nonaligned control. Keep the user-channel policy distinct from inline comment placement.
- **Registration:** define query-required structures and units before generation; freeze scorer semantics and count missing required units as failures; make the selected interaction necessary for scientific success; report functionality and cost; specify complete-pair, timeout, context and stopping rules. Keep oracle-delivery claims separate from live-register claims and label the remaining cohort’s exposure accurately.

The current v6 gate does not authorize that screen.

**5. Other observations**

The most consequential missed fact is **functional failure behind the best user-channel score**.

In **314-49 `user_phased`**, the function decorates itself with `@a_roman_numeral_to_integer_chx_b` before that name is defined. Even isolating its body and removing decorators for diagnosis, it returns:

| Input | Correct | Base body | User-phased body |
|---|---:|---:|---:|
| `"I"` | 1 | 1 | **0** |
| `"IV"` | 4 | 4 | **−1** |
| `"VI"` | 6 | 6 | **1** |

This is observed algorithmic damage, independent of the scorer dispute. [Generated text](/home/bmarti44/stencil-llm/results/focal/quicklook-v6.json:3048).

There are further concrete failures:

- **314-49’s comment arms** import nonexistent `typing` names such as `FinalStr` and `FinalDict`; the phased arm also invents `@a_chx`. [Header output](/home/bmarti44/stencil-llm/results/focal/quicklook-v6.json:977).
- **186-14’s three focal arms** use `@retry` without importing or defining it; the reminder arm supplies its import. [Phased output](/home/bmarti44/stencil-llm/results/focal/quicklook-v6.json:4361), [user output](/home/bmarti44/stencil-llm/results/focal/quicklook-v6.json:4701).
- **184-14’s comment arms** invent a `trace_method` requirement that was never supplied. Their zero echo counts obscure that behavior.
- The claim that phased delivery presents a small local load is inaccurate for **314-49**: its function-header packet still contains seven rules.
- The implementation has only header/body phases. The earlier recommendation to distinguish docstring opportunity from executable-body requirements was not fully implemented.
- V3–v6 are successive development observations under changing runtime, prompt, scoring cleanup and budget conditions. They are not independent replications that can be pooled as evidence against D.

The saved artifacts are valuable because they expose these distinctions. Their current summaries compress away precisely the distinctions needed to decide whether the mechanism is useful.
