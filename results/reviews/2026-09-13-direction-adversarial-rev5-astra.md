**E3 does not meet all of the owner’s criteria. I reject “good chance of working” for the full artifact.** My estimates are **10–25% that the specified screen reads CONTINUE**, and **5–15% that pursuing E3 under its stopping rules produces a published wrapper with a credible joint-success advantage over itself unmodified on long coding sessions**.

Those are judgment ranges, not statistical estimates from E3 experiments. “DISPROVED” below means rejecting the proposal’s claim to satisfy a criterion; it does not mean proving that every implementation must fail.

The research cutoff is **12 September 2026**, the current session date. I reviewed the September 12/13 repository records, including the September 13 proposal. I did not access `data/bench/`.

**The novelty claim survives only in a narrow form. Several closer predecessors were missing from the proposal and my previous assessment.**

| Source and identifier | Exactly what it already covers | What remains different in E3 |
|---|---|---|
| **LLMCrit**, ACL Findings 2024, **2024.findings-acl.472** | Extracts criteria from guidelines, including the Google Python Style Guide, and constructs synthetic demonstrations conditioned on which criteria should be satisfied or violated. Uses model generation, existing human texts, and manual refinement. This directly covers **style-guide-conditioned demonstration synthesis**. | Its downstream task is generating feedback on code, rather than generating functionally correct code. It does not use E3’s frozen executable templates or changing-session lifecycle. [Paper](https://arxiv.org/html/2403.01069v1) |
| **ContextIF**, ICLR 2026, **OpenReview IuscGSmfEf** | A trained context generator produces constraint summaries and analogous demonstrations for a frozen target model. This directly covers **manufacturing constraint-conditioned demonstrations to improve an unchanged model’s instruction following**. | It sees the current query and uses a learned generator. E3 generates earlier, without the query, using deterministic templates. [Official paper](https://proceedings.iclr.cc/paper_files/paper/2026/file/4d4aeebde3d074d5e8d77e9d2194e55e-Paper-Conference.pdf) |
| **ChatGPT Prompt Patterns for Improving Code Quality…**, **arXiv:2303.07839**, §4.5 | Explicitly describes **Few-shot Code Example Generation**: generate code examples that capture APIs, specifications, and design decisions for use in subsequent prompts. It covers synthetic code demonstrations as reusable memory. | Model-generated examples rather than dependency-checked template instantiation. No controlled evidence for E3’s transfer claim. [Author manuscript](https://www.cs.wm.edu/~dcschmidt/PDF/prompt-patterns-book-chapter.pdf) |
| **LLMs Learn Better In-Context from Rules than from Examples**, **arXiv:2609.03213**, September 2026 | Implements task rules and programmatically generates valid demonstrations; compares rules, examples, and their combination. This covers **executable rules → synthetic in-context examples**, including a direct redundancy comparison. | Games, arithmetic, and linguistic tasks rather than changing Python conventions. Not a token-matched study of this 4B wrapper. [Paper](https://arxiv.org/html/2609.03213v1) |
| **Self-ICL**, **2023.emnlp-main.968**; **Synthetic Prompting**, **PMLR 202:shao23a** | Manufacturing demonstrations when an adequate demonstration pool is unavailable; generating questions and reasoning demonstrations, including executable reasoning representations. | Neither establishes E3’s frozen family compiler, current dependency validity, or cross-algorithm convention transfer. [Self-ICL](https://aclanthology.org/2023.emnlp-main.968/), [Synthetic Prompting](https://proceedings.mlr.press/v202/shao23a/shao23a.pdf) |
| **Automatic Generation of Problems and Explanations for an Intelligent Algebra Tutor**, AIED 2019, **DOI:10.1007/978-3-030-23204-7_32** | Uses an explicit domain model of production rules to generate problems and explanations, including worked examples. **Rule-to-worked-example generation is established instructional technology.** | Human algebra learning, not coding-model prompting or session-rule updates. [Publisher record](https://link.springer.com/chapter/10.1007/978-3-030-23204-7_32) |
| **ASG: Automatic Generation of Analogous Problems…**, **CEUR Vol.1815, paper11** | Generates analogous subtraction problems under constraints, targeted to a diagnosed misconception. Covers **controlled example synthesis that preserves relevant structure while changing surface content**. | Uses information about the learner’s current problem and misconception. E3 deliberately excludes analogous target information. [Paper](https://ceur-ws.org/Vol-1815/paper11.pdf) |
| **Show and Tell**, **arXiv:2511.13972** | Combines prose style instructions with compact code examples across a two-turn coding task. | Its demonstration contains operations directly relevant to the requested CSV program. That is weaker support for an algorithm-free template than the proposal implies. [Paper and complete prompts](https://arxiv.org/html/2511.13972v1) |
| **Cursor Rules**, current product documentation | Repository-scoped rules, concrete examples, and referenced boilerplate templates are already product features. Examples include service and component templates. This covers **repository conventions delivered alongside reusable code exemplars**. | Documentation does not establish automatic recompilation of verified executable demonstrations whenever a convention changes, or measured superiority of that policy. [Official documentation](https://cursor.com/docs/rules) |
| **LintCFG: Still Manual? Automated Linter Configuration via DSL-Based LLM Compilation of Coding Standards**, **arXiv:2602.07783** | Compiles natural-language coding standards through a structured representation into operational tooling. It covers **style-guide compilation**, not demonstration synthesis. | Produces linter configuration rather than an example for a generator to imitate. Calling it an exact E3 predecessor would be inaccurate. [Paper](https://arxiv.org/html/2602.07783v1) |

These sources remove broad novelty claims about synthesizing examples, conditioning them on conventions, compiling rules into examples, and pairing repository rules with code templates.

I did **not** find a source establishing the exact remaining comparison:

> Under changing conventions, does a frozen, task-independent executable example improve functional transfer over complete prose and a defensible session-example policy, at matched resources?

That is an unclosed empirical question. It is not evidence that the combination is technically substantial.

Recompilation after a change is ordinary maintenance of a derived artifact. Parameter substitution into a code template is ordinary generation. **The potential contribution is the transfer effect of deliberately removing irrelevant algorithm content while retaining the convention’s operational structure.** If that effect disappears under fair controls, little remains beyond automated prompt authoring.

I retain the correction made in [round 2](/home/bmarti44/stencil-llm/results/reviews/2026-09-12-direction-adversarial-rev2-astra.md): familiar ingredients do not automatically invalidate a useful recombination. [Round 1](/home/bmarti44/stencil-llm/results/reviews/2026-09-12-direction-adversarial-astra.md) applied that objection too broadly. But neither [round 3’s rejection of D](/home/bmarti44/stencil-llm/results/reviews/2026-09-12-direction-adversarial-rev3-astra.md) nor [round 4’s provisional suggestion of E3](/home/bmarti44/stencil-llm/results/reviews/2026-09-13-direction-adversarial-rev4-astra.md) supplies positive E3 evidence.

**“Provenance” is meaningful as a construction policy, but the claimed causal interpretation is wrong.**

The argument **for** E3 is real. A current-rule compiler can provide an example when no suitable session example exists. It can remove an irrelevant algorithm, control size, expose an import–decorator relationship, and cheaply regenerate after a change. These choices predict differences in freshness, interference, availability, and construction cost.

The argument **against** the framing is decisive: given identical model state and delivered tokens, an example’s unobserved origin cannot change the model’s output distribution. A hand-written example and a byte-identical compiled example induce the same prompting intervention. Automation can improve reliability or cost; it does not create an additional learning mechanism.

Furthermore, E3’s arms change several things simultaneously:

- Current versus previous-rule compatibility.
- Trivial versus substantive algorithm content.
- Example length and complexity.
- Possibly dependency information.
- Representativeness of the next task.

Calling this bundle “provenance” does not isolate those differences. Section 4’s statement that the session-example arm attributes the effect to provenance is unsupported.

Human pedagogical research supports the narrower construction-policy argument. Shafto, Goodman, and Griffiths show that example selection and assumptions about a teacher’s selection process influence learning. That concerns information available to the learner, not an invisible manufacturing history. [**DOI:10.1016/j.cogpsych.2013.12.004**](https://shaftolab.com/assets/papers/shaftogg14.pdf)

**My decision:** the policy is not necessarily a meaningless permutation. The claim that the screen identifies a provenance effect is disproved. E3 is automated, constrained few-shot prompting with a potentially useful example-selection hypothesis.

**The strongest mechanism objection is that an executable witness is not a transfer guarantee.**

Let \(d\) be the demonstration, \(R\) the conventions, and \(G(q,d)\) the generated answer to a different request. Verifying

\[
R(d)
\]

does not establish

\[
R(G(q,d)) \land \operatorname{Tests}_q(G(q,d)).
\]

E3 checks the source artifact. The owner needs correctness of the generated target.

A trivial example can show where an import belongs and how a decorator is spelled. It may avoid making the model reconstruct those relationships from prose. That is a plausible computational benefit even when the example adds no new facts.

But a real algorithm introduces the interactions that the trivial body removed: signatures, keyword-only calls, recursion, exceptions, asynchronous execution, return types, decorator order, and stateful library behavior. Showing a decorator around `return 0` does not teach how its semantics interact with those cases.

“Trivial” also does not mean assumption-free. `return None`, `pass`, a broad exception handler, a synchronous signature, and a particular function arity are all concrete choices. A model can copy them. A compiler eliminates old-task algorithm copying by substituting a different source of potentially inappropriate behavior.

The external evidence cuts both ways:

- **Positive evidence exists, but is not specific enough.** ContextIF reports improved instruction following with generated context. Its reported general coding result changes from 62.20 to 63.30, while the context-generation system includes learned selection and constraint summarization. Those results do not identify the benefit of one frozen, target-independent template over complete prose. [ContextIF, Appendix Table 8](https://proceedings.iclr.cc/paper_files/paper/2026/file/4d4aeebde3d074d5e8d77e9d2194e55e-Paper-Conference.pdf)
- **Direct redundancy evidence is unfavorable.** The September 2026 rules-versus-examples study finds that combined prompting generally tracks rules alone, without consistent significant additive benefits. It also reports settings where smaller base models benefit more, particularly on easier tasks. This is evidence against a general additive-benefit assumption, not proof of equivalence or a measured result for Qwen3-4B. [**arXiv:2609.03213**](https://arxiv.org/html/2609.03213v1)
- **Style demonstrations can distract.** LLMCrit’s criteria-plus-demonstrations condition does not reliably outperform criteria alone. The authors report cases where models discuss the demonstration instead of the current input, particularly with lengthy demonstrations. That is feedback generation, so it supports an interference concern rather than an E3 failure-rate estimate. [**2024.findings-acl.472**, results and analysis](https://arxiv.org/html/2403.01069v1)
- **Code adaptation remains a separate difficulty.** AdaptEval studies adapting existing code to new requirements and documents substantial failures despite having a source snippet. Correct source code does not remove the adaptation problem. [**arXiv:2601.04540**](https://arxiv.org/html/2601.04540v1)

The human-learning analogy is also weaker than “minimal example lowers load, therefore transfer improves.”

Paas and van Merriënboer found benefits from worked examples, especially varied examples, in geometrical problem solving for machine programming. That supports worked examples under particular instructional conditions. It does not compare E3 with a complete, explicit prose specification supplied to a pretrained transformer. [**DOI:10.1037/0022-0663.86.1.122**](https://ris.utwente.nl/ws/files/288323661/Paas1994variability.pdf)

A particularly relevant **2026** study compared lower- and higher-interactivity methods for fraction multiplication. The reported advantage included practice and simple post-test problems. Crucially, the lower-interactivity instruction still taught an actual solution procedure. E3 removes the target algorithm instead of merely presenting its reasoning more efficiently. [Ngu, Phan, and Usop, **DOI:10.1002/acp.70169**](https://onlinelibrary.wiley.com/doi/10.1002/acp.70169)

Analogical-learning research finds benefits from explicitly comparing examples to extract relational structure. E3 supplies a minimal example but does not establish that the model extracts the intended invariant. [Gentner, Loewenstein, and Thompson, **DOI:10.1037/0022-0663.95.2.393**](https://groups.psych.northwestern.edu/gentner/papers/GentnerLoewensteinThompson03.pdf)

Engineering-design experiments also demonstrate fixation on supplied examples. They make inappropriate copying a credible concern, but cannot quantify its probability in a 4B language model. [Jansson and Smith, **DOI:10.1016/0142-694X(91)90003-F**](https://cs.uwaterloo.ca/~jianzhao/cs449-649/files/design-fixation-jansson91.pdf)

**The repository supports concern about functional integration, not a confident prediction that templates will fix it.**

In [quicklook-v6.json](/home/bmarti44/stencil-llm/results/focal/quicklook-v6.json), the model can visibly follow convention cues while producing unusable code. The Roman-numeral output in `314-49`, for example, includes imports and several decorators but also decorates the function with its own not-yet-defined name. Its arithmetic body is independently wrong. Correcting the dependency presentation could fix one failure while leaving joint success unchanged.

Other inspected outputs show unbound `@retry` and extensive cue imitation. These are evidence of dependency and imitation problems. **They are not observations of E3 template-body copying**, because E3 has not been run.

The stronger package-path evidence is [RESULTS-4C.md](/home/bmarti44/stencil-llm/results/memorycode-long/RESULTS-4C.md):

- Mean required-convention compliance: **8.45% → 10.49%**, a **2.05-point** increase; primary 95% interval **−0.07 to +4.16 points**.
- Strict compliance: **0/139 → 1/139**.
- Output failures: **60/139 → 61/139**.
- **119/278 outputs** reached the 512-token cap.

This is unfavorable evidence for the existing wrapper’s demonstrated capability. It is **not an upper bound on E3**: the intervention differs, the output cap matters, and this result did not measure executable functional success.

The [September 12/13 ledger](/home/bmarti44/stencil-llm/plan/LEDGER.md) also records register overflow on **138/144 LONG items** and the change to the evicted-sentence reminder policy. The focal classifier’s **123/123 gold-typing** result does not establish live admission, scope resolution, supersession, or dependency tracking.

The central missing quantity is the number of tasks where the model already produces a functionally correct answer and misses only conventions that E3 can rescue. Improving convention recognition on already broken algorithms does not improve the primary outcome.

**My probability ranges assume a fair implementation, rather than an easy way to trigger the gate.**

| Event | Judgment range | Main reasons |
|---|---:|---|
| The §3 screen reads **CONTINUE** | **10–25%** | Requires at least an 18.75-point observed joint-success advantage over both controls; complete prose may leave little headroom; transfer and functional-harm requirements are demanding. |
| E3 yields the owner’s published wrapper artifact under the stated stopping policy | **5–15%** | Must additionally survive oracle-to-live integration, realistic session state, rule interactions, package behavior, and comparison with the actual unmodified package. |

The task distribution and delivered prompts are not yet specified enough to support a calibrated forecast. If prose omits facts available to the compiler, or authored tasks closely fit the templates, the literal CONTINUE probability could be substantially higher. That would weaken the interpretation.

My round-4 estimate was **30–50% for a useful small-screen result**, not for this subsequently specified conjunction of gates. I also missed closer literature. That earlier estimate deserves revision, not protection because I proposed E3.

For scale, I recomputed the gate probabilities. At \(N=32\), against one comparator:

- With true win/loss probabilities **0.10/0.00**, the probability of at least six net wins is **9.4%**.
- With **0.15/0.05**, also a true ten-point advantage, it is **17.3%**.
- With **0.25/0.05**, a true twenty-point advantage, it is **62.0%**.

These are illustrations, not estimates of E3’s win/loss probabilities. The two comparisons share treatment outputs and cannot be multiplied as independent events.

If the harm condition means zero E3-only functional failures, even a **2%** per-task probability of such a failure leaves only a **52.4%** chance of observing none in 32 tasks. The screen can reject a useful intervention while still being incapable of establishing a low harm rate.

**Section 3 is capable of stopping E3, but it is not presently a fair test of all its claims.**

Its strongest features are joint success, counting missing units as failures, frozen templates, common histories, and the explicit prohibition on treating CONTINUE as confirmation. Those are substantive protections.

The material confounds and omissions are:

| Issue | Why it matters |
|---|---|
| **“Best available” versus previous-version example** | The claim names the best available session example; the arm selects the latest example satisfying the previous rule version. Those are different policies. |
| **Staleness is bundled with source** | A previous-version example may be obsolete, or may still satisfy the new rule. Neither case is established merely by its timestamp. A win against an obsolete example does not identify a compilation advantage. |
| **Selective inclusion of rule-change histories** | Every task contains the circumstance intended to favor E3. This can support a conditional claim, but gives no estimate of its frequency or value across ordinary long sessions. |
| **Unequal dependency facts** | The compiler explicitly receives actual dependencies. The proposal does not explicitly require the prose comparator to contain the same facts. |
| **Information versus representation** | If the example adds an import path, API requirement, or ordering fact absent from prose, the result can be explained by additional information. |
| **Token matching is unspecified** | Fixed history, unchanged prose, added demonstrations, and identical token counts require an explicit allocation policy. Padding, paraphrasing, or truncation are interventions themselves. |
| **Token equality does not match repetition or placement** | Code formatting, repeated identifiers, order, role, distance from the request, and emphasis can differ at identical token counts. |
| **The session example carries more nuisance content** | Algorithm complexity, length, signatures, and incidental conventions change alongside origin. |
| **Template/task co-design** | Preventing the compiler from seeing tests does not prevent the template author from knowing the task designs. “Evaluated-on only” does not by itself establish independence. |
| **Task independence needs substantive enforcement** | The prohibition on counting shared template clusters is appropriate. Renamed or cosmetically varied tasks cannot supply independent evidence of broad transfer. |
| **Supported-family selection** | Undefined support and exclusion rules permit difficult cases or compilation failures to disappear from the denominator. |
| **Per-rule validity versus joint validity** | Individually valid demonstrations can conflict when several current conventions are rendered together. |
| **Meaning of executable** | Importing a file or defining a decorated function may never exercise its behavior. An uncalled example can pass while its important assumptions remain untested. |
| **Test strength and independence** | Weak tests can accept copied trivial bodies. Tests must exercise the delivered code, including relevant decorators and interfaces, rather than a normalized substitute. |
| **Convention scoring** | All required units, nesting, imports, aliases, scope, and asynchronous forms need consistent treatment. A superficial match can reward broken code. |
| **Copying attribution** | Shared syntax is often intended. A copied-looking fragment is not automatically inappropriate, and a functional failure is not automatically caused by copying. |
| **Family comparison** | “Dependency-bearing” and “local” are not clean categories: naming can affect callers, and `try` changes behavior. Baseline difficulty and ceiling effects can masquerade as the predicted interaction. |
| **Mechanism prediction is not operationalized** | The gate requires aggregate gains; it does not establish a larger dependency-family effect or reduced inappropriate copying. “Confined to local families” lacks an exact decision definition. |
| **Harm wording** | “No treatment-only functional failures beyond base’s” is ambiguous between zero harmful discordances and no net excess failure. These yield different decisions. |
| **Sampling and execution policy** | Decoding, seeds, retries, timeouts, construction failures, and missing records need fixed treatment. Otherwise the binary outcome is not reproducible. |
| **Oracle-to-live gap** | A separate register-error table does not measure how those errors interact with compilation and generation. |
| **Session realism** | A frozen history followed by one completion does not exercise accumulated edits, broken callers, changing files, or repeated wrapper decisions. |
| **Cost scope** | Template authoring, dependency maintenance, execution checks, and amortization are part of the system’s cost, even if admission-time generation uses no model. |

**The session-example comparator is a straw man for “best available ordinary few-shot practice” whenever it deliberately supplies an invalidated example.** It remains useful as a stress condition. The `rules` arm prevents winning solely by defeating that condition, provided its dependency information is complete. `base` is the necessary artifact comparator.

Two defects in the decision rule are particularly concrete.

First, **six net wins is not a significance threshold**:

| E3 wins / losses | Net wins | Exact two-sided McNemar \(p\) |
|---:|---:|---:|
| 6 / 0 | 6 | 0.03125 |
| 7 / 1 | 6 | 0.07031 |
| 9 / 3 | 6 | 0.14600 |
| 13 / 7 | 6 | 0.26318 |

The proposal may legitimately use a practical development gate instead of a significance gate. But naming McNemar and an interval does not make them decision requirements. Even the 6/0 case has approximately **−6.6 to +38.9 percentage points** under the conservative paired interval constructed from simultaneous binomial bounds.

Second, **CONTINUE does not require beating `base` on joint success**. Consider this possible result:

| Arm | Functional tests passed | Joint successes |
|---|---:|---:|
| `base` | 32 | 20 |
| `rules` | 32 | 12 |
| `rules+session_example` | 32 | 12 |
| `rules+compiled` | 32 | 18 |

With nested success sets, E3 wins six and loses zero against both named comparators, causes no functional failures, and can have its gains in dependency-bearing cases. It passes the gate while losing to the unmodified package.

That is a direct counterexample to treating CONTINUE as support for the owner’s artifact comparison.

A CONTINUE would therefore be uninterpretable **as evidence for the advertised mechanism or artifact** if it depended on unequal dependency facts, obsolete-example punishment, template-matched tasks, weak tests, denominator exclusions, or failure to outperform `base`. It would still be an observation about those exact prompts.

**My verdict per owner criterion is:**

| Criterion | Verdict | Decisive reason |
|---|---|---|
| **Novel recombination** | **NOT DISPROVED, narrowly** | No exact match found for the lifecycle-plus-transfer comparison. Most of the mechanism is already covered by closer prior work. |
| **Useful** | **NOT DISPROVED** | Cheap, current exemplars could reduce convention-instantiation errors and maintenance cost. |
| **Not a meaningless permutation** | **NOT DISPROVED for the construction policy** | Removing irrelevant algorithm content while retaining operational relationships is a real hypothesis. The claimed isolation of “provenance” is disproved. |
| **Significant difference** | **NOT DISPROVED as a possible outcome** | A substantial joint-success gain at matched resources would matter. Merely substituting names and imports into familiar examples would not establish that difference. |
| **Good chance of producing the owner’s artifact** | **DISPROVED as a research-selection judgment** | Favorable evidence does not bridge task-independent examples to functional transfer, or oracle rules to live long-session improvement. Closer comparative evidence is mixed or unfavorable, and the repository has not demonstrated the necessary functional headroom. |

The owner has not supplied a numerical definition of “good chance.” The probability ranges are more precise than that phrase. At the ranges above, I would not describe the artifact as having a good chance.

**Has narrowing reached triviality? Almost at the implementation level, but not completely at the hypothesis level.**

E3 is more falsifiable than an unspecified “better memory” direction: it fixes the example source, timing, allowed information, and exclusions. That prevents complete retreat into vagueness.

But its technical implementation is now essentially a maintained library of parameterized examples. The remaining substantive question is whether that particular simplification improves transfer. Calling an untested comparison “the gap” cannot establish significance.

The local-family kill rule also confuses research distinctiveness with practical value. A reliable, cheap improvement in common local conventions could be useful. Conversely, a gain on a few elaborate decorator cases could be technically interesting and commercially irrelevant. The category label does not decide significance.

**On another reachable direction: my judgment is that no presently specified direction supported by these assets earns a defensible “good chance” for the full artifact.**

That is not a claim that all possible wrappers around a 4B model are incapable of improvement. The assets are general enough that such a universal impossibility claim would be indefensible.

It means I cannot name a replacement with the requested rigor using the evidence currently available. Deterministic normalization, validation, and repair are plausible engineering approaches, but they do not automatically preserve behavior across the supported conventions, repair the live register, or supply a novel recombination. Renaming one of them E4 and attaching another optimistic probability would repeat the problem.

The owner should conclude that **the current direction search has not met the requirement**. The existing package’s documented negative result remains the established outcome. E3 is a speculative experiment, not a research-supported route to the promised artifact.

Three further points deserve attention:

- **The rule compiler needs a language it can actually understand.** A sentence classifier is not a semantic compiler. Closed family schemas make compilation feasible but limit coverage. Accepting unrestricted prose transfers the difficult interpretation problem into an underspecified component.
- **Current output and current session state are different targets.** Correctly applying a new naming or interface rule to the next completion can break older callers. The wrapper’s inability to edit historical code is a material limitation for long coding sessions.
- **Adversarial survival is an asymmetric stopping condition.** A modestly specified empirical proposal can remain impossible to disprove conclusively while having a poor chance of success. Four reviews are not four experiments, and successive renaming does not create new evidence. The owner’s goal remains unmet.
