**Repair the oracle diagnosis before changing trunks or estimands. I found a concrete oracle-construction bug: the observed zeros do not establish a zero competence ceiling.** My ranking for a positive **new registration** within roughly 10 GPU-hours is **h, g, a**, with a moving upward if the registered 4B qualification and timing both pass.

1. **The oracle contains current-session changes, not the cumulative live instructions.**

   The vendored generator appends newly introduced/updated instruction pairs to `instruction_template`, but separately accumulates `history_regex`. On filler sessions it appends `[-1]` while retaining those historical rules. The adapter incorrectly calls `instructions[s]` the live set and renders only those pairs. See [generate_template.py:246](/home/bmarti44/stencil-llm/vendor/memorycode/code/generate_template.py:246), [memorycode.py:58](/home/bmarti44/stencil-llm/src/stencil/memorycode.py:58), and [memorycode.py:157](/home/bmarti44/stencil-llm/src/stencil/memorycode.py:157).

   This explains the otherwise suspicious empty reminders. For example, `314-49` has historical checks but an empty oracle; its oracle and base prompt hashes are identical. That is a duplicated baseline, not a ceiling measurement. [item-314-49.json:1090](/home/bmarti44/stencil-llm/results/memorycode-long/setup_long-role_evicted/item-314-49.json:1090)

   **Repair:** replay instruction events through session `s`, retaining the latest update per pivot; verify that the reconstructed regexes equal `history_regex`. Preserve first-introduction chronology separately from last-update chronology. Add a filler-after-instruction fixture: the existing fixture incorrectly supplies cumulative pairs and therefore hides this defect. [test_memorycode.py:92](/home/bmarti44/stencil-llm/tests/test_memorycode.py:92)

   Even after this repair, a **256-token packed oracle is not an unrestricted competence ceiling** if packing drops applicable rules. A separate, explicitly diagnostic prompt containing every applicable live rule is needed to distinguish missing information from inability to apply it.

2. **The recorded floor is real, but “this trunk cannot comply” is too strong.**

   I recomputed all 188 SHORT generations and their item aggregates:

   | Arm | Strict items | Mean fraction | Unparsable generations | Capped generations |
   |---|---:|---:|---:|---:|
   | history | 0/16 | .05729 | 16/47 | 26/47 |
   | restate_all | 0/16 | .08247 | 11/47 | 19/47 |
   | auto | 0/16 | .11997 | 12/47 | 21/47 |
   | oracle | 0/16 | .05122 | 7/47 | 9/47 |

   These reproduce [setup/summary.json:24](/home/bmarti44/stencil-llm/results/memorycode-derived/setup/summary.json:24). SHORT strictness also requires **every query in an item** to pass, whereas LONG generates only the first query. One SHORT `auto` generation actually achieves strict compliance; its other query makes the item fail. [item-95-3.json:2628](/home/bmarti44/stencil-llm/results/memorycode-derived/setup/item-95-3.json:2628)

   My final LONG snapshot, **01:47 UTC September 12**, contains **12 complete triples**. Rescoring all 36 generations reproduces every saved score. All arms remain 0/12 strict. Mean fractions are base **.10147**, focus **.06925**, oracle **.07446**: paired focus-minus-base **−3.22 points**, with **0 improvements, 4 declines, 8 ties**. The declines are `189-14`, `302-49`, `313-49`, and `352-99`. This is descriptive partial-run evidence, not a terminal HARM reading.

   Thus option **b has no observed positive LONG signal to recover merely by changing the estimand**.

3. **Three additional diagnostic limits matter.**

   **Output length:** capped or unparsable completions contribute substantially to the zeros. LONG base hits the cap on 9/12 completed items. The checker returns zero on syntax errors. This supports testing a compact code-only instruction before assuming a larger trunk is necessary. It does not justify silently raising the registered cap. [evaluate_model_output.py:23](/home/bmarti44/stencil-llm/vendor/memorycode/code/evaluate_model_output.py:23)

   **Applicability:** the item cohort is frozen, but the fractional denominator is not wholly frozen. `score_generation` includes every non-`None` check, including optional object families introduced by an output. I reproduced valid SHORT outputs with different denominators across arms. A synthetic function-only answer scores 1.0; adding a convention-violating optional class changes it to .5 under the same query. This is particularly consequential for **b**. Also, each official “family score” already requires all checked objects to satisfy that rule; it is not a smooth fraction of compliant identifiers. [memorycode.py:328](/home/bmarti44/stencil-llm/src/stencil/memorycode.py:328), [evaluate_model_output.py:50](/home/bmarti44/stencil-llm/vendor/memorycode/code/evaluate_model_output.py:50)

   **Information supplied:** some focus reminders contain almost entirely conversation filler. `352-99` spends its reminder on MacBooks and Discord. Better phrasing or stronger attention cannot reconstruct absent conventions. Separately, `314-49` has **zero focus candidates**, which warrants tracing speaker parsing and eviction offsets; I cannot establish its cause from the saved record. [item-352-99.json:905](/home/bmarti44/stencil-llm/results/memorycode-long/setup_long-role_evicted/item-352-99.json:905), [item-314-49.json:616](/home/bmarti44/stencil-llm/results/memorycode-long/setup_long-role_evicted/item-314-49.json:616)

4. **The earlier positive evidence favors competent tasks with useful reminders, not attention amplification as the next rescue.**

   Recomputing Exp 1’s source records gives role echo **66.67%**, classifier echo **54.69%**, difference **+11.979 points**, signs **44/15/69**, two-sided sign-test **p=.0002037**. Crucially, **every candidate sentence fit in all 128 role reminders**. This supports restatement where the model can comply and the relevant material survives packing; it does not validate newest-first selection among thousands of candidates. [Exp 1 RESULTS.md:25](/home/bmarti44/stencil-llm/results/qwen/multiif-echo-only-128/RESULTS.md:25)

   Recomputing the FOCUS-3 diagnostic episode table gives **57/64 C, 29/64 N, 63/64 O**, a **43.75-point** C−N difference. That makes 4B credible, but the evidence concerns constrained tasks and reused development templates. [FOCUS-3 diagnostic:10](/home/bmarti44/stencil-llm/results/quick-checks/focus3-gate/diag/RESULTS.md:10), [diagnostic:75](/home/bmarti44/stencil-llm/results/quick-checks/focus3-gate/diag/RESULTS.md:75)

   The 30B episode records reproduce delivery **35 wins/0 losses**, format **25/4**, and indentation **17/15 with zero mean gain**. Larger size therefore does not eliminate outcome-specific compliance failures. Its recorded claim also excludes superiority to prose. [larger-test-v2 RESULTS.md:20](/home/bmarti44/stencil-llm/results/larger-test-v2/RESULTS.md:20), [RESULTS.md:39](/home/bmarti44/stencil-llm/results/larger-test-v2/RESULTS.md:39)

   For wave, the saved counts yield `(545−524)/1218 = +1.724 points` over reinsertion under the historical scorer. That small increment does not establish a rescue for this workload. Also, “more breakage than reinsertion” reverses the original table: its recorded paired-broken counts are **21 wave versus 30 reinsertion**. Those historical counts still require their scorer caveats. [w-seal.json:16](/home/bmarti44/stencil-llm/results/qwen/w-seal.json:16), [w-seal.json:72](/home/bmarti44/stencil-llm/results/qwen/w-seal.json:72)

5. **Ranked recommendation.**

   These probabilities are **subjective planning ranges**, not estimated power or confidence intervals. They concern a positive *new* registration within approximately 10 GPU-hours; none substitutes for the original Exp 4 claim.

   | Rank / option | Probability of PROVEN | GPU-h | Why; cost to the artifact’s claim |
   |---|---:|---|---|
   | **1 — h: fresh, narrower workload** | **45–65%** | About **8.2** at current pilot rate; potentially less for short outputs | Directly removes task-complexity and instruction-capacity floors. Claim becomes sparse-instruction, bounded coding-session retention. Do **not** select successful MemoryCode items or families. |
   | **2 — g: one compact application format** | **10–25%** | About **8.6** for the test below plus confirmation/parity | Can reduce prose, truncation, and failure to translate stated rules into code. Cannot fix missing rules. Claim covers the specific formatting/reminder bundle. |
   | **3 — a: Qwen3-4B** | **10–25%** before qualification | **Unmeasured; timing must qualify** | Best direct capacity intervention; existing 4B evidence is encouraging. Still inherits retrieval and budget failures. Renamed artifact; no claim about the 1.7B artifact. Moves above g if qualification and timing pass. |
   | **4 — e: relevance ranking** | **5–15%** | About **8.2**, plus ranking overhead | Can recover useful sentences currently displaced by filler. Generic request similarity does not establish liveness or resolve updates. Claim includes the frozen retriever. |
   | **5 — b: fractional primary** | **2–10%** | About **7.0** for confirmation/parity | Escapes the all-conventions conjunction, but current paired movement is adverse. Requires a precisely frozen denominator; proves average partial compliance only. |
   | **6 — d: model-written synopsis** | **2–10%** | **7.0 + synopsis generation**, unmeasured | May compress rules, but adds omission, invented-rule, and stale-state failures across repeated summaries. Claims a recurrent summarization system, with its extra inference cost. |
   | **7 — c: attention amplification** | **1–5%** | **Unmeasured** custom-path overhead | Might increase use of present rules; cannot supply missing ones. Adds dose risk, attention implementation, and off-switch/parity work. |
   | **8 — f: register repair** | **1–5%** | Evaluation plus unmeasured development | Needed for a useful maintainer, but admission, retirement, and overflow are separate failures. It changes the shipping policy and still cannot ensure code compliance. |

   Cost arithmetic: the four pilot records average **87.7889 seconds/generation**, maximum **97.9951**. Thus 256 primary generations cost **6.243 hours** at that mean; 32 parity generations add **.780 hours**. These are projections, not guarantees: the registered safety ceiling for SCREEN alone is **10.453 hours**. [memorycode-long pilot:7](/home/bmarti44/stencil-llm/results/timing-pilot/memorycode-long.json:7)

   For **f**, the cap checks **all stored rows**, before computing relations. Merely retiring rows may therefore leave overflow intact. [focus3.py:304](/home/bmarti44/stencil-llm/src/stencil/focus3.py:304)

6. **Yes: running the registered SCREEN unchanged remains scientifically defensible.**

   The registration explicitly says oracle comparisons gate nothing; the primary pair remains well-defined despite the oracle defect. [REGISTRATION.md:154](/home/bmarti44/stencil-llm/results/memorycode-long/REGISTRATION.md:154)

   Furthermore, even a valid 0/16 competence sample has a one-sided 95% binomial upper bound of **17.07%**. It does not establish zero population success. SHORT and LONG have different units, and correlated arm failures cannot be pooled as independent evidence.

   I recomputed the registered interval thresholds: **10 wins/0 losses**, or **29 wins/10 losses**, first give a positive lower bound at N=128. If SCREEN instead produces no discordances, its registered interval is **[−3.366, +3.366] points**, giving **NOT PROVEN**, not demonstrated mechanism uselessness.

   **My recommendation is to repair and inspect the diagnostic before spending on SCREEN, but not to invent a retrospective eligibility gate.** If the primary is left unrun, report that explicitly; SETUP cannot issue SCREEN’s terminal reading. The current data also do not justify “almost surely NOT PROVEN.”

7. **Common rules for the three quick tests.**

   First repair the oracle bookkeeping using CPU fixtures and verify coverage. Preserve existing outputs and disclose the correction. That is an instrument repair; changing reminder policy, trunk, or estimand is a new registration.

   Use **fresh authored development material**, disjoint from benchmark prompts, answers, and confirmation material. Freeze all families, prompts, packing, and stopping rules before generation. No selecting successful benchmark families under the name “derived workload.”

   The thresholds below are **resource-allocation gates**, not statistical proof: report paired intervals and two-sided tests, then require a separate untouched confirmation. Their proposed efficacy gate is a **25-point paired strict gain**, oracle qualification **75%**, and focus-only output-failure rate **≤5%**. Failure means “do not spend the remaining budget on this proposal.”

   These are alternatives, not an authorization to run three rescue cycles. Amendment 1 already consumed one policy revision; a new registration does not silently reset the program budget. [REGISTRATION.md:144](/home/bmarti44/stencil-llm/results/memorycode-long/REGISTRATION.md:144), [PROTOCOL.md:15](/home/bmarti44/stencil-llm/plan/PROTOCOL.md:15)

8. **Quick test h — qualify a sparse-instruction long coding workload.**

   **Items/N:** 16 fresh authored long sessions, four prespecified convention families with four sessions each. Use small coding requests, varied rule values and positions, and long code/conversation history. Require all evicted instruction-role sentences to fit the existing reminder budget; disclose this restriction as part of the population. Do not position rules specially at the eviction boundary.

   **Arms:** identical 1.7B artifact off; existing role-evicted focus; complete-current-rule diagnostic oracle. One final generation per session, unchanged W/E/output cap. **48 generations**.

   **Outcome/kill:** strict compliance with fixed required structure. Stop if oracle passes fewer than **12/16**, paired focus gain is below **4/16**, or focus-only failure rate exceeds **5%**. Do not salvage it by dropping a failed family.

   **Cost:** **1.17 hours** at the existing pilot mean, **1.96** under its safety multiplier. If qualified, freeze the recipe and use fresh N=128 confirmation.

9. **Quick test g — test one application instruction, not a prompt sweep.**

   **Items/N:** 16 fresh authored development sessions containing multiple simultaneous conventions and realistically verbose coding requests.

   **Arms:** base; current focus; focus with one frozen format; complete-current-rule oracle using that format. A concrete candidate is: “Return one complete fenced Python block. Apply every listed convention to every relevant object. Omit commentary.” Charge the added instruction against the reminder budget. **64 generations**.

   **Outcome/kill:** strict compliance, parse/cap failures, and paired gains. Stop if formatted oracle is below **12/16**, formatted focus gains less than **4/16** over base, fails to improve over current focus, or exceeds the **5%** focus-only failure limit. Oracle improvement without focus improvement diagnoses a remaining information-selection problem.

   **Cost:** **1.56 hours** at the pilot mean, **2.61** with its safety multiplier. This tests the actual shipping bundle; an oracle-only formatting success is insufficient.

10. **Quick test a — use the registered retry, then require LONG headroom and timing.**

   **First gate:** the already registered four-arm 4B SHORT retry, **16 items**; `history <6/16` kills this route under its existing contract. Correct the oracle interpretation, but do not replace the history gate with it. No 4B records existed when I checked. [CONTRACT.md:181](/home/bmarti44/stencil-llm/results/memorycode-derived/CONTRACT.md:181)

   **Additional items/N:** 16 fresh authored LONG development sessions, with dense simultaneous conventions and frozen queries. Arms: **4B off, 4B role-evicted focus, complete-current-rule diagnostic oracle**; 48 generations.

   **Outcome/kill:** the same **12/16 oracle**, **4/16 paired gain**, and **≤5% focus-only failure** gates. Also stop if the measured remaining confirmation-plus-parity budget does not fit. A 4B SHORT pass alone establishes neither LONG retention headroom nor affordable confirmation.

   The control must remain the **same frozen 4B artifact with its flag off**. All successful alternatives still require packaging parity; MemoryCode-style final-response evidence alone does not upgrade the claim to free-running agentic coding. [plan:100](/home/bmarti44/stencil-llm/plan/BACK-ON-TRACK-PLAN.md:100), [plan:178](/home/bmarti44/stencil-llm/plan/BACK-ON-TRACK-PLAN.md:178)

No files written, models/GPU/network used, or data/bench/ contents read.
