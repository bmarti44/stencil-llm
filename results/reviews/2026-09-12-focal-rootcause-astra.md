**These pilots do not yet justify declaring focal delivery futile.** They mix a real repetition failure with delivery defects, scope errors, and an unmatched periodic control. The most consequential remaining problem is that keyword re-feed can close the very syntactic opportunity the reminder needs.

I inspected the code, four v2 records, and three completed v3 records. I ran only model-free checks; no files were written, models run, or `data/bench/` read.

**1. A — The best-supported diagnosis is self-reinforcement seeded by the intervention format, with greedy decoding sustaining it.**

The records distinguish several mechanisms:

- **The repeated prefix is a plausible initiator.** Repeating `# Convention: always …` supplies an easily extended pattern, including opportunities to invent additional conventions.
- **The problem persists beyond the insertion boundary.** On v3 314-49, `oracle_focal_first` generates **111 identical** `# Convention: always include a try block` lines. Its reported `echoed_lines=0` means none exactly matched a supplied rule—not that imitation disappeared.
- **Comments are not necessary for degeneration.** On 352-99, `oracle_before` repeats `self.chx = "chx"` **116 times**.
- **Neither model size nor position is independently identified.** These runs do not vary model size, and they confound placement with formatting, repetition, and retained history.

This matches the experimentally documented self-reinforcement effect: repeating a sentence can increase its probability of recurring under maximization-based decoding. That supports the mechanism, though it does not prove which intervention token initiated these particular loops. [Xu et al., NeurIPS 2022](https://arxiv.org/abs/2206.02369)

Qwen’s model card recommends sampling for non-thinking mode and explicitly warns about greedy repetition in thinking mode. Your package supplies an empty, closed thinking block, so the thinking-mode warning is relevant background, not a direct diagnosis of this runtime. [Qwen3-4B model card](https://huggingface.co/Qwen/Qwen3-4B), [package opener](/home/bmarti44/stencil-llm/deploy/stencil_focus/build/hub-4b/focus_session.py:17)

**Recommended change:** Keep greedy fixed and remove repeated rule-list scaffolding; treat subsequent imitation as a measured failure, not something output cleanup repairs.

**2. A — A compact, locally phrased comment is the best first format change; none of the papers establishes a guaranteed cure.**

| Option | Concrete assessment |
|---|---|
| **Single-line cue** | Best inexpensive first change. It removes repeated line prefixes, but nine semicolon-separated instructions remain nine obligations. |
| **Docstring-like string** | Poor first choice. It introduces string-boundary hazards and can become the function’s actual docstring, displacing task documentation or affecting scoring. |
| **Instruction versus statement** | Prefer a concrete instruction tied to the next operation: “For this function, …”. Merely replacing “Convention” with “Apply here” is a weaker change. |
| **First versus second person** | Low priority. Original Thinking Intervention found small narrative differences on its tested reasoning model; that does not establish a preferred voice for code comments. |
| **Terminator** | End with a complete sentence and newline. A textual “end reminder” marker is not a hard boundary; another comment line may simply extend the pattern. |
| **No-repeat n-gram constraints** | They retain determinism but change the shipped decoding policy. Applying them equally permits a separate fair comparison, not a claim about unchanged greedy decoding. They can also forbid legitimate repeated decorators, identifiers, and code structures. |

The stronger literature lesson is **fit the intervention to its surrounding representation and limit repeated disruption**:

- The Thinking Intervention follow-up found naturalized intervention styles better than vanilla text, and repeated interventions often worse than a single intervention. [Findings EMNLP 2025, §§6.3–6.4](https://aclanthology.org/2025.findings-emnlp.209/)
- SafeRemind crafts text resembling the model’s reasoning and uses **at most one injection** in its main implementation. Its results concern thinking traces, not Python comments. [SafeRemind, Appendix B.7](https://arxiv.org/html/2601.03662v1)
- Hydra places specific checker feedback in a comment immediately before repair continuation. This establishes that comments can be useful—not that repeated generic convention lists are effective. [Hydra, §4](https://arxiv.org/html/2605.15238v1)
- Answer Engineering scores compatible candidate edits under the preceding prefix. Its lesson is contextual compatibility, not a universally effective phrase. It also reports repetition and instability under dense corrections. Candidate probing adds computation and selection beyond this reminder-only mechanism. [Answer Engineering, §§5.2, 6.10](https://arxiv.org/html/2606.21121v1)

**Recommended change:** Use one complete, operation-specific comment per delivery phase, preserving the rule meanings; defer decoding penalties and phrase-search machinery.

**3. A — A user-turn intervention is a worthwhile diagnostic, but requires a separate conversation representation.**

A properly framed user reminder removes the cue from the assistant’s code and presents it through an instruction-trained interface. That makes it a strong comparator for testing whether the assistant-code channel is the problem. I found no direct evidence that it outperforms comments in this exact setting.

Appending the proposed role delimiters to the current `pieces` stream is insufficient:

- A new assistant turn normally starts a new response; it does not automatically resume an unfinished code block.
- The new assistant opening must preserve the package’s non-thinking behavior.
- Generated code must be assembled separately from conversation scaffolding. Otherwise role labels and reminder text enter the detector or final output.
- Earlier cues remain in context. A role boundary does not erase self-imitation.
- Forced role delimiters must remain distinct from model-generated EOS.

An alternative is rebuilding the prompt with the reminder on its instruction side and the retained assistant prefix afterward. That avoids pretending an interrupted turn naturally resumes, but invalidates more cached computation.

**Recommended change:** Implement user-turn delivery as an explicitly separate diagnostic arm with a code-output projection and verified continuation framing.

**4. B/C — Deliver by decision point, not merely by enclosing unit type.**

The current taxonomy collapses names, decorators, arguments, annotations, docstrings, and body requirements into `function` or `method`. [Family mapping](/home/bmarti44/stencil-llm/src/stencil/focal.py:40)

The literature supports reducing simultaneous integration demands, but **does not establish a universal cap of three rules**. Human prospective-memory experiments show that high maintenance load can eliminate a focal-cue advantage. The stacking paper supports grouping and semantic rewriting; its reordering-only control supplied little benefit. [Maintenance-load experiment](https://pubmed.ncbi.nlm.nih.gov/28600628/), [Instruction Stacking Collapse, §5](https://arxiv.org/html/2608.02639v1)

Use these delivery points:

| Rule | Last useful delivery point |
|---|---|
| Decorators | Before the first decorator, or before an undecorated header |
| Function/class name | Before its identifier |
| Arguments and annotations | Before the relevant signature tokens |
| Docstring | Before the first body statement |
| `assert` / `try` | After any docstring, before executable body statements |
| Attribute naming | Before the governed attribute assignment |
| Required imports | Before import construction, with decorator dependencies handled explicitly |

**Do not put every body rule after the docstring:** the docstring requirement must arrive before its opportunity passes.

Compile compatible naming requirements into one operational contract—for example, prefix `a_`, containment `chx`, and suffix `_b`—while preserving all three checks. This reduces integration work without silently dropping obligations.

Prioritizing violations is sensible only when violations are observable. An incomplete name is not yet a suffix violation; a body that has not ended is not yet missing its required `try`. Detecting a completed violation and rolling back is a **repair policy**, which should be identified separately from prospective delivery. Checklist practice likewise distinguishes prompting action from verifying completed state. [Degani and Wiener, NASA checklist report](https://www.interruptions.net/literature/Degani-Checklist.pdf)

**Recommended change:** Split delivery into decorator, signature, docstring, and executable-body phases; cap intervention burden without discarding undelivered rules silently.

**5. C/D — High: unconditional keyword re-feed blocks decorator insertion on undecorated units.**

At [focal_runtime.py:245](/home/bmarti44/stencil-llm/src/stencil/focal_runtime.py:245), the runtime recovers the original keyword and later forces it into the continuation.

After forcing:

```python
# cue requesting @retry
def
```

the model cannot prepend a decorator to that header through ordinary continuation. The same problem applies to `class`. Re-feeding an already generated `@` preserves decorator opportunities; re-feeding `def` does not.

The v3 186-14 records show the predicted symptom: method interventions re-feed `def `, and both focal arms lose `retry` compliance despite receiving that rule. This is consistent evidence, not a clean causal ablation. [v3 records](/home/bmarti44/stencil-llm/results/focal/quicklook.json:783)

The trailing-space fix addresses tokenization behavior; **it does not fix this semantic restriction**.

**Recommended change:** Re-feed `def` or `class` only after decorator decisions are complete, or when no applicable decorator rule exists.

**6. B/D — High: method delivery consumes its first opportunity on `__init__` and can destroy constructor semantics.**

The detector classifies every class-contained `def` as a method. It triggers before learning the complete name. [focal.py:93](/home/bmarti44/stencil-llm/src/stencil/focal.py:93), [classification](/home/bmarti44/stencil-llm/src/stencil/focal.py:157)

The checker instead treats `__init__` specially for attributes and excludes other double-underscore methods from ordinary method checks. [extract_objects.py:132](/home/bmarti44/stencil-llm/vendor/memorycode/code/extract_objects.py:132)

Consequences:

- `deliver="first"` can spend all ordinary method rules on a constructor that is outside their checker scope.
- Naming instructions can transform `__init__` into an ordinary method. **v3 186-14 actually produces `def  x__init__(...)`.**
- Renaming changes checker membership while breaking initialization behavior.
- Attribute rules delivered indiscriminately at method headers miss their actual assignment opportunities.

**Recommended change:** Buffer enough of the identifier to classify special methods before rollback; preserve constructor names and route attribute rules separately.

**7. D — The rollback remainder is stripped incorrectly, but it is a latent bug rather than an established cause of these Qwen failures.**

At [focal_runtime.py:242](/home/bmarti44/stencil-llm/src/stencil/focal_runtime.py:242), `remainder + block` is encoded together and marked entirely `"ins"`.

`remainder` contains preserved pre-boundary output. It should survive scoring.

A model-free tokenizer fixture reproduced:

```text
Intended retained code: pass\nx=1\n
After cue stripping:   passx=1\n
```

However, inspection of this package’s tokenizer vocabulary found **no tokens containing bytes after a newline within the same token**. Thus the demonstrated newline-crossing case is not evidence that this defect caused the ASCII pilot failures.

The general fix is still warranted because the implementation explicitly supports a remainder and currently assigns it the wrong provenance.

I found **no demonstrated off-by-one defect in `HFBackend.crop`**: dropping one additional cached token and re-feeding it is consistent with its pending-token convention. Active-path numerical parity remains unqualified; baseline identity does not test it. [crop implementation](/home/bmarti44/stencil-llm/src/stencil/focal_runtime.py:366)

**Recommended change:** Preserve the remainder as retained output, strip only the cue, and qualify active cache reuse against the identical edited token prefix.

**8. D — The periodic string fix is incomplete, and the detector is not a Python lexer.**

Model-free witnesses expose remaining failures:

- `x = "'''"\ndef f(): ...` causes the triple-quote counter to suppress the real function.
- A comment containing `"""` incorrectly puts `code_line_count` into string state.
- Fence-looking text inside a triple-quoted string can cause `unit_starts` to expose a fake function.
- A position after `x = 1 + \` is reported eligible for periodic insertion, although inserting a comment there breaks explicit line continuation.

These follow from quote counting and fence processing before adequate lexical classification. [unit scanner](/home/bmarti44/stencil-llm/src/stencil/focal.py:128), [periodic scanner](/home/bmarti44/stencil-llm/src/stencil/focal.py:203)

Parenthesis depth is also absent, so multiline keyword arguments can resemble assignment units. Before the first fence appears, prose is treated as bare Python; encountering a later fence retroactively changes that interpretation.

**Recommended change:** Share a prefix-tolerant lexical scanner that tracks strings, escapes, comments, continuation state, brackets, and established code regions.

**9. D — Delivery bookkeeping and the periodic arm do not support the advertised matching claims.**

The first-kind cooldown correction is present. Remaining distinctions matter:

- A delivery event means **an insertion attempt**, not that the intended unit was subsequently produced.
- For assignments, re-feed is empty. If the model writes intervening comments, the regenerated assignment moves to another offset and can receive another delivery.
- `every` remains bounded by cooldown and `max_per_rule=3`; it is not coverage of every unit.
- Periodic delivery ignores those per-rule counts and repeatedly inserts the complete register. [periodic branch](/home/bmarti44/stencil-llm/src/stencil/focal_runtime.py:185), [delivery bookkeeping](/home/bmarti44/stencil-llm/src/stencil/focal_runtime.py:228)

The actual imbalance is enormous: v2 352-99 uses **8,230 periodic inserted tokens versus 182 focal**, and 314-49 uses **9,152 versus 158** for focal-first. Periodic failure therefore cannot identify an alignment advantage.

**Recommended change:** Track attempted, skipped, and completed delivery opportunities separately; match rule identities and copy counts before calling periodic a placement control.

**10. D — Scoring obscures both failure mechanisms and apparent successes.**

Three corrections are necessary:

- **Do not delete model-authored echoes from the primary output.** `strip_echoes` changes the generated artifact before scoring. Its exact-match count also misses paraphrased imitation, including the 111-line loop. The new default `Apply here` renderer additionally disagrees with the script’s hard-coded `Convention` echo set. [strip_echoes](/home/bmarti44/stencil-llm/src/stencil/focal.py:224), [consumer](/home/bmarti44/stencil-llm/scripts/focal_quicklook.py:181)
- **Separate parse failure from individual-rule failure.** Every capped output in the supplied records lacks a closed code fence and fails the current extraction/parsing path. Its all-zero score does not establish that no individual obligation was attempted or satisfied in the partial program. [checker extraction](/home/bmarti44/stencil-llm/vendor/memorycode/code/evaluate_model_output.py:11)
- **Convention scores do not establish executable correctness.** The v2 186-14 focal-every output scores `.667` but uses `@retry` without importing it. The v3 constructor rename is another concrete functional failure.

One factual correction: the saved 314-49 before output contains **11 decorators**, not 13. Some are class/method-directed decorators placed on a function, demonstrating scope confusion alongside its higher score.

The script also omits inserted spans, token IDs, re-fed-token counts, and explicit runtime-version metadata from saved arm records. [record writer](/home/bmarti44/stencil-llm/scripts/focal_quicklook.py:193)

**Recommended change:** Score output with only forced cue spans removed; retain echoes, report failure categories separately, and save enough provenance to reconstruct the scored artifact.

**11. D — Token limits currently undercount work and exceed the proposed context contract.**

Rollback resets `n_gen` to retained generated tokens, and re-fed keywords are counted separately. Consequently, `max_new_tokens` does not bound total autoregressive selections. [focal_runtime.py:263](/home/bmarti44/stencil-llm/src/stencil/focal_runtime.py:263)

There is also no enforced total-context budget. Recorded before prompts contain **3,584 tokens**; adding a 1,200-token response already permits **4,784**, before focal insertions. This exceeds the proposal’s 4,096-token contract, although it is below Qwen’s native context capacity.

Finally, constructing `oracle_before` by inserting the reminder into the request causes `_fit` to retain less history. Thus before and focal are not merely different placements of the same information. [prompt fitting](/home/bmarti44/stencil-llm/deploy/stencil_focus/build/hub-4b/focus_session.py:124)

**Recommended change:** Freeze common retained history, enforce total context, and record monotonic generated-work counts separately from retained, discarded, inserted, and re-fed tokens.

**12. E — Run one bounded delivery-format pilot after these repairs.**

Use **314-49, 186-14, and 184-14**, all already exposed, with these five arms:

| Arm | Purpose |
|---|---|
| `base` | Plain shipped greedy decoding |
| `before_compact` | Same compact rule packets, supplied once before generation |
| `focal_header_compact` | Compact cues at current unit boundaries, with decorator-safe continuation |
| `focal_phased_compact` | Same rule content distributed across decorator/signature/docstring/body opportunities |
| `user_phased` | Same phased packets through a correctly framed user-turn intervention |

That is **15 generations**, each with a **1,536-token model-generation cap**. Freeze common history with a base prompt budget of at most **1,792 tokens**, reserve **768 tokens for forced intervention/scaffolding**, and enforce the 4,096-token total. Disclose that this is a shortened-context debugging pilot, not a replication of the original SETUP-LONG condition.

Before generation, require model-free checks for the identified failures and active-cache qualification at an actual intervention boundary. Save each arm immediately.

Report:

- Existing fixed-denominator compliance;
- Per-unit naming, decorator, and body compliance;
- Parse/cap/loop outcomes;
- Constructor preservation, unresolved decorator names, and simple task-function checks;
- Actual delivered rule counts and all token costs.

**Why postpone 352-99?** It should remain a later overload stress case, not decide whether basic delivery works. Its focal loop begins after a five-rule class packet and four-rule variable packet; saying “51 rules overwhelmed one function” does not describe those trajectories. Its register also contains **19 function rules and 17 method rules**, beyond the stated 9–14 range.

**Practical continuation gate:** advance only if a prespecified phased candidate beats `before_compact` by at least **10 percentage points in mean compliance**, wins on at least **two of three items**, and has no net increase in parse/cap/loop failures or new functional breakage. Otherwise stop this cue-only configuration on greedy Qwen3-4B after the repaired pilot. If runtime qualification fails, the experiment is invalid and the instrument needs repair.

That is a development decision, **not statistical disproof of D**. Three exposed items cannot establish general futility or the proposed interaction.

**Recommended change:** Run this single disclosed diagnostic, then make the practical stop/continue decision without opening another wording-search loop.

**Ranked fixes to apply first**

1. **Restore syntactic opportunity:** decorator-safe continuation and special-method scope.
2. **Repair measurement:** preserve model output, distinguish parse failure, save complete provenance.
3. **Enforce common history and honest token budgets.**
4. **Replace repeated convention lists with compact, operation-specific cues.**
5. **Split signature, docstring, and body delivery; harden lexical boundaries.**
6. **Run the bounded five-arm pilot, including the user-turn diagnostic.**
