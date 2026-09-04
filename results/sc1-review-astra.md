**SC1 draft registration review — astra — 2026-09-04**

The proposed comparison addresses G1: its sole primary outcome is executable final-task success, and its rule receives an input-derived budget instead of the classifier's realized dose. The binary estimand, one-sided McNemar formula, 13-net-win engineering threshold, and conservative interval are mathematically coherent under IID sampling from a fixed authoring distribution. The draft is not ready to bind: authoring, policy execution, checker validity, and freeze boundaries still admit materially different experiments. I found five high and four medium findings; no critical finding.

Review scope: the requested documents were read in order, followed by relevant implementation source. Computation was foreground, standard-library Python on CPU. No model was instantiated, no GPU process was launched, no process was signalled, and neither sealed IFEval inputs nor sealed BFCL cohort contents were read. Only this review file was written. The playbook's process/STATE documents are now under archive/plan/; I read those without changing the ledger.

Reviewed HEAD: 705b746398c908549f96e85bae32bc99af9479e7. SHA256 of LEDGER-PLAN.md: dca60baf319e0a4f95a25fe61ed5dd4a00e71b9925b72ef11925f1d7eed10aca. SHA256 of data/sc1/AUTHOR-CONTRACT.md: 283f857288a73371a235ae47afe7cb0368d043f20b534935c7b25d3bff0b6cdb.

**F1 — HIGH — The freeze permits design changes after seeing the episode bank and setup outcomes.**

Evidence: LEDGER-PLAN.md:907-910 makes registration binding only after episode hashes, then allows a dated amendment any time before the final run. LEDGER-PLAN.md:883-885 says failed setup requires new sources, but does not close the general amendment permission. The design source explicitly freezes reader settings before setup measurement (results/astra-research-blockers.md:119).

An implementer can inspect the final episodes, adjust segmentation or framing, hash them, observe setup competence/headroom, and amend thresholds before step (5). No final outcome need be viewed. This defeats the prospective interpretation while satisfying the literal freeze clause. Separate scientific-design freeze, executable-artifact freeze, and episode freeze. Passing or failing setup must not reopen scientific choices. Replacement R1 below closes this.

**F2 — HIGH — “Frozen authoring mixture” and independent sampling are not actually specified.**

Evidence: LEDGER-PLAN.md:863-866 lists four authors without allocation probabilities, versions, prompts, or session boundaries; LEDGER-PLAN.md:886-891 assumes an episode population suitable for exact inference. data/sc1/AUTHOR-CONTRACT.md:12-23 supplies marginal probabilities but does not explicitly require independent factor draws; :7-8 requires semantic distinctness without a source record; :39-45 lacks author/session/source-family provenance. The design source explicitly requires independent crossed factors and warns against fixed strata masquerading as an IID mixture (results/astra-research-blockers.md:108-109,193).

For example, perfectly correlating style with origin satisfies both stated 50:50 marginals. Giving each author a fixed block, or creating eight variants of each of 32 source stories, does not establish the registered IID-mixture sampling model. Unique entity strings are not source independence. “Separate authors' pool” also leaves open whether setup uses a different author population, weakening its competence/headroom relevance.

Freeze the author mixture, versions/settings, independent factor sampler, seeds, and source/session records. Shared grammar, executor, and checker primitives are acceptable; shared instantiated story/dependency graphs are not independent semantic sources. Semantic review and normalized source fingerprints can enforce an operational no-siblings rule under the repo's trusted-but-fallible threat model; they cannot prove statistical independence. Report that assumption explicitly. Do not silently count discovered siblings as independent or change the unit after results. Replacement R2 makes the sampling and audit contract reviewable.

**F3 — HIGH — The standalone author contract does not enforce the promised information boundary.**

Evidence: LEDGER-PLAN.md:864-865 promises contract-only authors and no diagnostics or selector knowledge. But data/sc1/AUTHOR-CONTRACT.md:5-8 only prohibits consulting/imitating benchmarks and reusing names, IDs, values, or phrasings from repository data/results. It does not prohibit conceptual use of probe failures, selector-derived guidance, prior session context, or reviewer feedback carrying those facts. results/astra-research-blockers.md:102,106 and results/astra-program-review.md:68 require this broader boundary. Historical development influence is documented in LEDGER-PLAN.md:555-568,633-634.

A previously informed session can invent entirely new prose while targeting known selector failures. This reviewer session, having read the design diagnostics and C2 result, must not subsequently act as a blinded author. Reusing the same model name in a fresh isolated context is a different matter. Repository access, retrieval, and feedback channels need an input allowlist and a retained authoring transcript; changing names alone is insufficient.

The defensible claim is new evaluation episodes authored without task-time benchmark/probe contact, evaluating a development-informed frozen selector. Neither the classifier's historical influence nor an author's model pretraining is erased. R3 supplies both the private lineage statement and the author-facing prohibition without sending policy diagnostics to authors.

**F4 — HIGH — Admission, segmentation, and echo are underspecified, and the existing helpers implement different policies.**

Evidence: LEDGER-PLAN.md:861-862 says threshold 0.5 and segmentation unchanged; :877-881 says rank candidates, admit whole spans, skip oversize spans, and echo chronologically within E. It does not explicitly say filter before ranking, define candidates straddling the recent boundary, resolve scorer ties for clf, or choose whole-entry skip versus stopping versus clipping at E. “Same admission” could also be misread as using clf's threshold-filtered candidate list for rule.

Concrete reuse hazards:

- src/stencil/bfcl.py:245-262 splits tool text by lines and sentences, and then chunks BOTH user and tool pieces into at most 128 local tokenizer tokens. “User sentences + 128-token tool chunks” does not fully describe that behavior. LEG B instead used unchunked user sentences (LEDGER-PLAN.md:572-573).
- src/stencil/bfcl.py:309-317 scores with empty context and applies the threshold. Rule needs the unscored candidate universe, not this selected output or a scorer-dependent extraction path.
- src/stencil/bfcl.py:344-379 has no 256-column ceiling and BREAKS at the first nonfitting span. It does not implement SC1's skip-and-continue admission.
- src/stencil/bfcl.py:382-393 renders role labels but no turn labels and imposes no echo cap.
- src/stencil/bfcl.py:689-727 derives recency quotas from classifier quantities and calls a helper that truncates a final span (src/stencil/bfcl.py:434-458).
- scripts/multiif_evict.py:271-287 chooses raw user columns under a supplied classifier budget; its caller supplies that realized count at :821-830.

A selected span whose echoed text itself consumes 256 tokens leaves no room for positive framing overhead under E=256. For two nominal 128-token chunks, typically only one complete labelled chunk fits; exact counts depend on tokenization after rendering. Keeping the chronological prefix can omit the latest correction and preserve a stale instruction; selection in ranking order followed by chronological presentation is a different algorithm. Both can fit the current words.

Use an unscored common candidate builder, pin down the threshold and source-coordinate rules, and register the echo selection order separately from presentation order. R4 recommends the literal chronological scan, whole-entry skip-and-continue interpretation, retaining pins even when their echo cannot fit. It deliberately preserves the proposed capped package comparison; it does not retrofit dose matching.

**F5 — HIGH — Negative mutations alone do not establish executable, attainable, non-vacuous success.**

Evidence: data/sc1/AUTHOR-CONTRACT.md:13-16 allows up to 40 lines and a one-call state task, :28-36 requires nonempty work and six rejected mutations, and :39-43 leaves checker/reference representations abstract. LEDGER-PLAN.md:871-872 caps generation at 256 tokens; :905-906 requires checker/mutation validation but no explicit positive reference execution through the consumer.

A reject-all checker rejects every mutation. It would eventually fail setup, but could falsely terminate a useful experiment as lacking competence. A checker that checks only one expected field may pass a reference and six handpicked negatives while ignoring another obligation or arbitrary collateral edits. A correct 40-line artifact or function call can exceed 256 tokenizer tokens and be impossible to emit under the registered budget. The stated contract does not require a bounded, serializable reference witness.

“Cancelled action executed” is not inherently applicable to a continuing episode, and “old-ID substitution” needs a meaningful old ID. Forcing every story to contain all six phenomena changes the intended scope mixture; accepting duplicate, malformed, or semantically unchanged mutations makes the coverage claim hollow.

R5 requires a passing bounded reference, real execution from fresh state, complete-state checking, obligation coverage, and six distinct applicable negatives. Preserve the named attack classes where meaningful, with predeclared obligation-linked substitutes. The identical checker runner must consume reference, mutations, and model outputs.

**F6 — MEDIUM — The budget is defensible as a fixed stress setting, but its interpretation and provenance controls need tightening.**

Evidence: LEDGER-PLAN.md:873-881; data/sc1/AUTHOR-CONTRACT.md:11,17-29,41-43. C is undefined with respect to the protected recent suffix. With 4,096-8,192 history tokens and 1,024 protected, the natural C is 3,072-7,168. Then B is always 256: only 8.33%-3.57% of removable history, not a working 25% allocation. The fractional branch is dormant on compliant episodes, not a broken adoption gate.

Equal pin/echo ceilings are a reasonable deployment comparison and correctly allow different realized usage. They do not make information doses equal or prove the chosen ceilings optimal. A user-first rule can fill B entirely with user spans and never reach useful tool facts. Long tool chunks and label overhead can amplify that effect; many short classifier spans can instead pay more echo-label overhead. The direction is empirical. These are structural properties of the frozen packages, not automatically unfair advantages. Do not rebalance lengths or force tool admissions after seeing selections.

The age/origin labels also need to refer to the actual decisive evidence after overrides, not merely the first mention. A supposedly OLD item can be restated in a recent assistant message or baked into a tool schema; omitting the final-query literal alone does not prevent this. “TOOL-origin fact” must not silently mean a tool has authority to override a user instruction. A common recent suffix can also carry indirect information through its already-prefilled KV; this experiment does not prove erased information is wholly absent.

R6 defines private evidence annotations and input separation. The supported claim remains success of these two retention-plus-echo packages at this one pressure setting on scripted histories, not pure KV recovery, general scope resolution, or free-running agent success.

**F7 — MEDIUM — Operational adoption counts have multiple implementable meanings.**

Evidence: LEDGER-PLAN.md:893-900. “Clf-only invalid/truncated/repetitive episodes (vs rule) <=2” could mean a union at episode level, three separate allowances, or a difference of aggregate counts. “Attributable to clf only” could require subjective attribution or merely a paired state-corruption flag. “Normalized 4-token block repeated >=8 times” omits the normalization, tokenization, overlap, and consecutiveness definitions. The source instead specifies consecutive repetition and an episode-level union (results/astra-research-blockers.md:143).

For example, three invalid-clf/valid-rule episodes and three reverse episodes have zero net excess but three clf-only failures. Those are different adoption decisions. A valid output completed exactly at token 256 is not truncated under the draft's definition, whereas scripts/multiif_evict.py:383 flags every output hitting the cap as truncated. Its invalid/repetition definitions at :290-301 are also not SC1's.

R7 supplies Boolean formulas and a concrete repeat detector. Paired zero additional corruption is a reachable engineering gate, not a population safety guarantee. If both arms corrupt the same cases, this particular incremental gate passes; that must not be described as zero corruption.

**F8 — MEDIUM — The source's cost guard disappeared, and the global cap lacks a complete-run decision path.**

Evidence: results/astra-research-blockers.md:143 requires mean total latency <=1.25 times rule latency, all selector/echo overhead, and deferral when the projection exceeds 8 GPU-h. LEDGER-PLAN.md:901 makes selector latency descriptive and :905 only states a global 8 GPU-h cap. Thus a very slow CPU classifier can be adopted while consuming little additional GPU time. Matching KV/token ceilings is not matching end-to-end resource ceilings.

The draft also needs an explicit outcome if the cap is reached before 256 pairs. It must not select rule under the “otherwise” clause, calculate a partial-cohort p-value, shrink N, or reinterpret runtime exhaustion as 100 unattempted model failures. R8 restores the proposed latency guard, defines measured costs and projections, and gives incomplete studies a separate NOT RUN/INCOMPLETE status. A different cost tradeoff could be registered prospectively, but silently dropping the source's guard is not an equivalent design.

**F9 — MEDIUM — The author-hour estimate is arithmetic, not evidence that bespoke episode/checker production fits it.**

Evidence: LEDGER-PLAN.md:863,905-906; data/sc1/AUTHOR-CONTRACT.md:11,31-36; results/astra-research-blockers.md:137. The source assumption does reproduce the draft estimate: 288 times 6-10 minutes plus 12-16 shared hours = 40.8-64 hours. But the batch contains 1,179,648-2,359,296 history tokens, 288 references, and 1,728 adversarial mutations. The ENTIRE 12-16-hour shared allowance is only 2.5-3.33 minutes per episode before paying for common machinery.

That is optimistic for 288 bespoke stories and checkers with independent semantic review. It is plausible only if most rendering, reference construction, checker execution, and mutation production are already automated and human/agent review is tightly scoped. As an illustrative sensitivity, adding 8-12 minutes of separate review per item yields 79.2-121.6 hours with the same authoring/machinery assumptions. This is a planning scenario, not a measured estimate.

The cheapest credible reduction is a small original scenario language with shared executable semantics, while still creating 288 distinct source specifications. Generate literal values, record order, filler, expected-state witnesses, and mechanical mutations from pinned seeds. Review each compact causal specification and its rendered obligations, rather than manually constructing a new checker and thousands of filler tokens each time. Thirty-two stories with eight renamed variants do not buy N=256 independent sources. R9 turns the estimate into a measured, prospective work plan.

**Recomputed inference, power, and feasibility**

For IID paired binary observations let p_b=P(clf-only success), p_c=P(rule-only success), q=p_b+p_c, and delta=p_b-p_c. Conditional on m discordances, B is Binomial(m,p_b/q). Under delta<=0 this success probability is at most 1/2, so the registered upper tail is a valid one-sided test. Ties stay in the 256-case effect denominator. The paired-binary parameterization agrees with the [author-maintained exact2x2 documentation](https://search.r-project.org/CRAN/refmans/exact2x2/html/mcnemarExactDP.html).

The interval is also correct: each two-sided 97.5% Clopper-Pearson interval misses its own discordant probability with probability at most .025; the union bound gives simultaneous coverage at least .95 without assuming b and c independent. Subtract opposite endpoints. Use b/N and c/N, not b/m and c/m. This conservative interval need not exclude zero when McNemar rejects; it is descriptive, not another adoption gate.

The test and adoption thresholds are reachable. b=13,c=0 gives p=1/8192 and a 5.078125-point gain. b=32,c=19 gives p=0.045957274908 and the same gain. Four discordances all favoring clf give p=.0625; five give .03125 but fail the 13-net-win engineering threshold. With no discordances, p=1. No statistical gate is mathematically vacuous or impossible.

I enumerated every possible discordance count and every conditional winner count on CPU, using exact integer comparisons for the rejection region. With m discordances, rejection occurs exactly when 20 times the upper-tail binomial coefficient sum is at most 2^m. Alternative probabilities were accumulated in floating point; there was no Monte Carlo simulation or asymptotic approximation.

| N | True gain | Discordance q | Exact-test rejection probability | Rejection AND at least 13 net wins |
|---|---:|---:|---:|---:|
| 256 | 5 points | .10 | .782221774671 | .519149347311 |
| 256 | 5 points | .20 | .508574554797 | .497249202424 |
| 256 | 10 points | .20 | .973556236712 | .969538336722 |
| 256 | 0 points | .20 | .037834740070 | .035785076608 |

Thus the draft's rounded 78%, 51%, and 97% are correct. The adoption probabilities are upper bounds before failure, corruption, and cost gates; unconditional study adoption also requires passing setup. At a true gain exactly on the five-point engineering boundary, high superiority-test power does not imply high adoption probability. The first row demonstrates the distinction particularly clearly.

Minimal reproducible CPU calculation, runnable from standard input without loading repository modules or writing artifacts:

~~~python
from math import comb, fsum

N = 256
critical = {}
for m in range(N + 1):
    tail = 0
    critical[m] = m + 1
    for b in range(m, -1, -1):
        tail += comb(m, b)
        if 20 * tail <= 2**m:
            critical[m] = b

def power(q, delta):
    theta = (q + delta) / (2 * q)
    test_terms, adopt_terms = [], []
    for m in range(N + 1):
        pm = comb(N, m) * q**m * (1-q)**(N-m)
        def upper(k):
            return fsum(comb(m, b) * theta**b * (1-theta)**(m-b)
                        for b in range(k, m + 1))
        test_terms.append(pm * upper(critical[m]))
        # 2*b-m >= 13; ceil((m+13)/2) = (m+14)//2.
        adopt_terms.append(pm * upper(max(critical[m], (m+14)//2)))
    return fsum(test_terms), fsum(adopt_terms)

print(power(.20, .05))
# (approximately 0.508574554797, 0.497249202424)
~~~

The method is consistent with the [exact2x2 power documentation](https://search.r-project.org/CRAN/refmans/exact2x2/html/powerPaired2x2.html); the numbers above are my independent calculation.

The setup thresholds are jointly reachable and are appropriate engineering competence/headroom checks, not population guarantees. For example, full=24/32 and evicted=16/32 passes. They do not show headroom in every role/scope cell, prove the pins help, or validate every checker; those are different requirements. Keep setup separate and do not turn its subgroups into unregistered gates.

On the interpretation with two setup arms, there are 64 setup outputs plus 512 final outputs = 576. Eight GPU-hours allows an average of 50 seconds per output INCLUDING prefill and all charged GPU overhead, before any additional model smoke work. If additional arms are run on setup, count them explicitly. The C2 cost at LEDGER-PLAN.md:810 is from a different trunk/workload/arm schedule and does not validate this projection. I did not measure new model timing during this review.

**Minimum harness coder brief**

The coder should implement a small SC1 module and command with a strict SC1 input allowlist, CPU-only acceptance tests, and a model-free dry-run mode. The brief needs the following concrete contracts.

1. **Renderer and record schema.** Pin trunk/checkpoint/config/tokenizer/chat-template versions, non-thinking opener, EOS IDs, numeric mode, generation cap, and per-attempt deadline. Render only allowlisted public fields; preserve semantic message indices and original user/tool roles even if the native template serializes tool responses inside another wrapper. Make prefix, history, final-query, echo, and generation coordinates explicit. References, checker code/specification, mutations, factor labels, seeds, author identity, private evidence annotations, and oracle final state never enter model/selector inputs. Define whether initial_state is the state immediately before the final call; validate scripted tool responses against a coherent state trace. No benchmark renderer defaults or example loading.

2. **Eviction core reuse with a strict split.** Reuse the behavior of src/stencil/qwen3.py:70-85,88-139: prefill the common history; evict only the old history while preserving prefix, recent suffix and that arm's pins; then prefill the final query plus its echo. Retain original RoPE positions and the absolute position counter. Both arms and setup-full share the two-stage schedule. Use renderer-supplied indices, not decode/rfind/re-encode inference from scripts/multiif_evict.py:343-349. Echo insertion must be after eviction, with unchanged source-history token IDs. Rebuild or deep-clone fresh cache state per arm and record cache widths in every layer. Do not inherit BFCL's K=8192 pressure trigger: SC1 calls for pre-query eviction in every compliant episode.

3. **Independent selectors and bounded echo.** Extract the pure candidate builder from the semantics at src/stencil/bfcl.py:196-302 without instantiating a classifier for rule. Implement R4 rather than calling the existing budget, quota-match, or recency helpers unchanged. Record candidates, rank, admission/skip reasons, unique pin coordinates, rendered echo source coverage, scorer truncation count, and actual resources. Rule must execute when the scorer/model path is unavailable. Preserve role quoting without exposing active/relevant/scope annotations. Wire explicit counters to every amplification/steering intervention path; a constant-zero metadata field is not evidence that none occurred.

4. **Original in-memory executor and checker runner.** Specify one strict JSON/tool-call or artifact grammar, extra-text policy, exactly-one-call validation, duplicate-key handling, types, nonexistent IDs, and allowed operations. Execute only finite declared operations against a deep copy of the episode's pre-decision state. No eval of generated code, external services, filesystem tasks, or BFCL environments. src/stencil/bfcl.py:1127-1163 calls the vendored BFCL executor/checker and is not SC1's executor. Parse/validate before mutation; compare complete resulting state and all protected objects against the registered obligations. Store action results, state differences and individual invariant failures as well as binary pass.

5. **Non-vacuity and attainable outputs.** Run each positive witness and six distinct negatives through the production path with fresh state each time; verify the witness token length, missing/extra objects, wrong target, unchanged state, and protected-state modifications. Mutation coverage comes from meaningful obligations, not six syntactically broken strings. Reviewers assess the task against the specification independently of the compiler; otherwise a shared compiler bug can make both reference and checker agree incorrectly. Have a policy-independent test of hidden-field isolation through the actual renderer.

6. **Freeze, record persistence, and resume.** Produce a manifest hashing code/dependencies, all model/tokenizer/selector files, configuration, source specs, generated episode bytes, setup/final assignment, parser/executor/checker and mutation fixtures, authoring prompts/transcripts, seeds and execution order. Record the manifest ID in every arm attempt. Persist each finished arm atomically before starting another, then assemble the paired episode record; pair-only persistence would rerun a completed first arm after a crash. Resume rejects any manifest mismatch or changed completed output. Use an attempt journal to distinguish a completed failed generation from a genuinely interrupted missing attempt. Hashes detect drift, not absence of training contamination.

7. **Analysis and runtime consumer.** Require exactly the 256 registered IDs with both arms and no duplicates before confirmatory analysis. Compute the exact one-sided tail, CP interval, R7 flags and R8 cost decision from those records; no old Holm, case-mean, complement-control, or headroom-recovery result can choose the selector. Keep NOT RUN, INCOMPLETE, INVALID, complete/no-adoption, and complete/adoption states distinct. Report all four paired success cells, marginal success, b/c, delta, interval, p, every gate, actual source-factor counts, and subgroup/resource descriptions.

8. **Targeted CPU acceptance.** The brief should name a new SC1-only test module, for example tests/test_sc1.py, executed with CUDA hidden and bytecode writes disabled. Test the actual command/consumer path with fake scorer and fake cache/trunk objects, not just duplicated formulas. Cover threshold .5, score ties, an oversize candidate followed by a fitting candidate, boundary spans, chronological echo overflow, scorer-independent rule, hidden-field isolation, event ordering and positions, positive/negative checkers, b=c=0, four/five-discordance tails, b=13/c=0 adoption, union failure counts, and interrupted-second-arm resume preserving first-arm bytes. The event test at tests/test_multiif_evict.py:283-330 is a useful pattern. Do not run the whole existing BFCL test module: it includes cohort-reading tests (tests/test_bfcl.py:52). No GPU/model process is part of this CPU implementation acceptance.

**Exact proposed replacement text**

These are prospective changes to DRAFT v1, not assertions that they are already registered or implemented. R4 chooses the LEG A chunking implementation and an explicit chronological echo algorithm; R8 restores the design source's proposed 1.25 latency guard. Those choices should be accepted before authoring, not inferred by the coder from outcomes.

**R1 — Replace LEDGER-PLAN.md:907-910 with:**

> Freeze sequence: (1) review and freeze the scientific registration and sanitized author contract before any setup or final episode is authored. This freezes the authoring distribution, policies, budgets, renderer semantics, decoding, endpoint, sample size, statistical and operational gates, failure handling, and cost rules. (2) Build the harness and pass CPU-only consumer tests on eight disposable synthetic smoke episodes; record the implementation/configuration manifest before production authoring. Smoke episodes are never reused. (3) Author and independently validate the 32 setup and 256 final episodes without policy/model feedback; hash all source records, episodes, references, checkers, mutations and split assignments. (4) Run the frozen setup gate and cost projection. (5) If both permit execution, run the fixed final cohort once. (6) Record the outcome against the frozen manifest.
>
> No scientific or executable choice may be changed using production episode content, setup model outputs, or final outputs. A dated amendment alone does not authorize such a change. Editorial corrections may clarify the record without changing executable behavior or decisions. A substantive redesign, including one motivated by failed setup, is a newly named registration using new setup and final sources. A discovered implementation defect stops the affected run; record it as INVALID rather than excluding pairs or silently rerunning under changed code.

**R2 — Replace the episode-mixture statement at LEDGER-PLAN.md:863-866, before the lineage qualification in R3, with:**

> Episodes: 256 final and 32 setup, each from a separate original semantic source. Before authoring, freeze an author manifest giving the exact versions, settings and neutral prompts for kimi-k3, fable, gpt-6-astra and Opus. Draw the author independently for each episode with probability 1/4 per author. Independently draw style (editing/tool-work, 1/2 each), decisive-fact origin (user/tool, 1/2 each), decisive-evidence age (old/recent, 1/2 each), and governing-instruction scope (continuing/overridden/cancelled-or-completed/switched, 1/4 each). Use master seed 20260904 with separate recorded streams for these assignments, authoring randomness and generated literals. Do not impose fixed quotas, rebalance realized factors, or substitute authors after inspecting their episodes or any policy output.
>
> Each authoring request uses a fresh isolated session and produces one new semantic source from its assigned factors. Setup uses an independent source pool under the same authoring law; no setup/final source, event graph, or instantiated task is shared. Retain source_id, author/version, prompt/session provenance, seed, compact source specification, entity relationships, required obligations, and scope/event dependencies in the private manifest. Review semantic siblings using these specifications and fingerprints normalized for names, IDs and literal values. A renamed, reordered or numerically perturbed version of an existing source is a sibling, even if its rendered text differs. Shared executor/checker primitives and general construction grammar are allowed; siblings cannot count as new independent episodes.
>
> Freeze validation/rejection criteria before production authoring, retain the candidate/rejection record, and permit only source-validity repairs without selector or trunk feedback. If 288 valid distinct sources cannot be produced under the frozen procedure, defer the study rather than change its mixture. Report realized author/factor counts and the provenance audit. Exact inference is conditional on the stated independent-sampling model; uniqueness checks do not by themselves prove it. Source dependence discovered after freeze invalidates that confirmatory interpretation and cannot be repaired by dropping or relabelling pairs after outcomes.

Replace data/sc1/AUTHOR-CONTRACT.md:12,17-23 with:

> The commissioning sampler independently assigns style (editing/tool-work, 1/2 each), decisive-fact origin (user/tool, 1/2 each), decisive-evidence age (old/recent, 1/2 each), and governing-instruction scope (continuing/overridden/cancelled-or-completed/switched, 1/4 each). Use the assigned factors; do not choose different factors to suit a story. These are sampling probabilities, not fixed quotas. A tool-returned fact is data; governing authority and subsequent user updates remain distinct from that fact's source. OLD means the decisive evidence lies wholly before the most recent 1,024 rendered history tokens; RECENT means it lies wholly within them. For overrides, annotate the evidence that determines the currently valid value or instruction, not merely the original mention.
>
> EDITING produces a bounded JSON patch or small text artifact; TOOL-WORK produces exactly one function call into an isolated in-memory database. CONTINUING means the instruction still applies. OVERRIDDEN means a later user update governs. CANCELLED-OR-COMPLETED means the earlier action must no longer be performed. SWITCHED means a persistent instruction remains applicable after moving to another task and returning. Every episode still requires an affirmative, nonempty final task result.

Replace data/sc1/AUTHOR-CONTRACT.md:44-45 with:

> Setup episodes use a separate source pool under the same frozen authoring distribution as final episodes. They share no semantic source, instantiated task, story or entities with final episodes. Shared generic task primitives do not make episodes siblings; reusing the same causal task blueprint with changed names, values or wording does. Record a private compact source specification and provenance so an independent reviewer can assess this distinction.

**R3 — Append to the SC1 lineage block at LEDGER-PLAN.md:861-867:**

> Fit-on: the previously frozen, development-informed selector corpus; no new fitting. Its historical probe and benchmark-family influence remains disclosed in the LEG B/LEG A lineage. Evaluated-on: new SC1 source episodes and references, excluded from fitting, threshold selection, prompt selection and policy revision. “Benchmark-free authoring” means no task-time benchmark/probe/repository-example contact during this commissioning process; it does not assert absence of benchmark material from author/trunk pretraining or erase the selector's development history. Authors receive only the sanitized contract, independently assigned factors/seeds, and original task/API specifications. They never receive this registration, its design-source reviews, benchmark outcomes, probe diagnostics, policy identities/rankings, or selector-derived feedback. Freeze and retain their complete input provenance. An informed review/development session cannot be reused as a blinded author session.

Replace data/sc1/AUTHOR-CONTRACT.md:3-8 with:

> Write original fictional, self-contained conversations requiring earlier information to complete a final task. Use only this contract, the supplied factor/seed assignment and original task/API specification. Do not browse, retrieve or consult benchmarks, repository data/results, experiment reviews, probe diagnostics, memory-policy code or outputs, or prior session notes. Do not use remembered task-specific diagnostics from earlier work on this project, even if you would change every name, value and phrase. If your current session has such information, disclose that before authoring and use a fresh isolated session.
>
> Do not imitate or paraphrase public benchmark items or templates. Names, IDs, values and incidental phrasing must be original or procedurally generated. Do not use a common instantiated story to create multiple episodes by renaming entities or varying numbers. Submit a compact semantic source specification with each episode. Reviewer feedback may address contract compliance, source independence and checker correctness only; it must contain no memory-policy scores, preferences or performance information.

**R4 — Replace LEDGER-PLAN.md:873-881 with:**

> Common source representation: let P be the rendered token boundary immediately after the protected system/tools prefix, and H the boundary immediately before the final user message, both supplied by the frozen renderer. The history length is H-P. Let R=max(P,H-1024), C=R-P, and B=min(256,floor(C/4)). Evict [P,R) before prefill of the final query or echo; retain [0,P) and [R,H) in both arms. C is computed from the common source history before selection, and counts all removable history columns, not only candidate columns. Every compliant episode undergoes this eviction; no BFCL pressure-trigger condition applies.
>
> Candidate segmentation for SC1 is the LEG A source segmentation implemented at src/stencil/bfcl.py:196-302 at the reviewed revision: prior user text is sentence-split; prior tool text is split into nonempty lines and then sentences; each resulting user or tool piece is chunked consecutively at 128 local Qwen tokenizer tokens. The frozen splitter's filtering and control-token exclusions apply identically to both arms. Build candidates without calling a scorer. Include only complete candidate spans whose mapped source-token interval is wholly inside [P,R); do not clip boundary-spanning candidates or select protected recent text. Record boundary and control-token exclusions. Do not expose the final request or private episode metadata to either selector.
>
> clf: score each candidate with the frozen classifier, its original role and empty context; preserve the registered encoder truncation rule and count its truncations. Retain only scores >=0.5, then rank by descending score, descending message index, and ascending source start offset within a message. rule: rank the entire unscored candidate universe with all user candidates before all tool candidates, descending message index and descending source start offset within each role. Source end offset breaks any remaining tie; identical source records are deduplicated. Rule reads no classifier scores, filtered membership, quotas, counts or echo quantities and runs without loading the classifier.
>
> Each arm scans its own ranking once. Admit a candidate's complete source span only if the union of admitted source columns would remain <=B. Otherwise skip it and continue; never stop the scan at the first oversize span, split a candidate, or borrow quantities from the other arm. B is a ceiling, so underfill is allowed.
>
> Echo: independently sort that arm's admitted spans by ascending source position. Scan them chronologically, appending a complete entry only when the entire serialized echo would remain <=E=256 trunk-tokenizer tokens; skip a nonfitting entry and continue. Retain a pin even if its echo entry cannot fit. Empty selection produces no echo header. The exact header is “Earlier context restated verbatim:” followed by a newline; entries use “- ROLE turn MESSAGE_INDEX: JSON_QUOTED_TEXT”, separated by newlines, with the original role and zero-based message index. Quote both user and tool content as data. Count all header, labels, quoting, separators and echo-insertion framing in E; also assert that the token-count increase in the rendered final message is <=E. Do not pad, truncate text, echo an unpinned candidate, or match another arm's dose.
>
> Both arms share tokenizer, renderer, prefix, protected recent suffix, output grammar, generation limits and prefill/position policy. Scope resolution, digesting, attention amplification and residual steering are OFF. Instrument the actual intervention entry points and require their counters to be zero. Report pin/echo resources actually used, including echo omissions by source and role.

**R5 — Replace data/sc1/AUTHOR-CONTRACT.md:31-37 with:**

> Supply the exact expected artifact or complete final state, a concrete valid reference output, and an executable checker specification enumerating every obligation and invariant. The reference, including its required output/tool-call framing, must fit within 256 tokens under the frozen trunk tokenizer; the 40-line ceiling is additional, not a substitute. For tool-work, the reference is exactly one allowed call executed from a fresh copy of the supplied pre-decision state. One pass requires complete valid output, every obligation, and every protected-state invariant. Missing or extra objects, wrong/stale values, unauthorized edits and unfinished output fail. Unchanged initial state, no-op output, empty output and generic answers must fail.
>
> Before freeze an independent reviewer runs the reference and all mutations through the identical parser, executor and checker runner used for model outputs, resetting state before every run. The reference must PASS. At least six distinct, task-applicable mutations must FAIL and name the obligation each violates. Include old-ID substitution, cancelled action, wrong entity, wrong scope, empty output and collateral edit wherever meaningful. Where one is not meaningful for this episode, record its non-applicability and substitute a different registered attack on an actual obligation: missing required field/object, wrong exact value, forbidden extra output, or incomplete artifact/call. Do not add artificial cancellation/override events merely to fill mutation categories. Do not count identical negatives, unchanged references, or six parser errors as semantic coverage.
>
> Independently review the mapping from narrative to obligations; a generated reference agreeing with a generated checker is insufficient. Include type-valid wrong-target/state mutations, and exercise every protected invariant with a violating state; add tests beyond six when needed for obligation coverage. Record reference/mutation outcomes and reviewer identity before freeze. References, checkers, mutations and review annotations are private scoring inputs and never appear in model, selector or echo inputs.

**R6 — Append to the author contract's episode-shape and record-format clauses:**

> Measure the 4,096-8,192-token history bound after frozen chat rendering, including history role delimiters and excluding the system/tools prefix, final user request, echo and generated output. Record private source coordinates for the decisive fact, applicable instruction and every update/cancellation/completion event needed to resolve it. An OLD dependency must not be restated or semantically supplied in the protected recent suffix, system/tools prefix, or final request. A RECENT dependency must be wholly in the recent suffix. The private checker reviewer verifies these annotations without running or consulting either selector. For cancelled/completed scope, the final task still requires a separate affirmative result and must not be satisfied by doing nothing.
>
> Tool schemas describe general operations and may not hard-code episode-specific answers or required target values. All scripted tool responses must be consistent with the supplied private state trace. initial_state denotes the complete database state immediately before the final call, after all scripted events. The model sees only the public transcript and general tool schemas, not a hidden database snapshot or oracle final state. The renderer uses only system, tools, turns and final_request; all provenance, factor labels, references, checkers, mutations, initial_state and evidence annotations are private unless a particular fact already appears explicitly in a scripted public turn.

Append to the budget/reporting clause in LEDGER-PLAN.md:

> With compliant history lengths, C is 3,072-7,168 and the cap fixes B at 256. This is a comparison at one registered pressure/echo setting; it is not evidence that a 25% allocation or E=256 is optimal. Report selected-span lengths, pin/echo use by role, and echo omission rates without conditioning adoption on those diagnostics. The outcome estimates these frozen retention-plus-echo packages on scripted histories. It does not isolate pure KV retention, prove absence of indirect information in surviving KV, establish free-running agent benefit, or generalize beyond the registered authoring distribution.

**R7 — Replace LEDGER-PLAN.md:893-900 with:**

> Adoption is evaluated only for a VALID, COMPLETE study with all 256 paired outcomes. Keep clf only if the exact one-sided McNemar p<=0.05, b-c>=13, and every registered operational/cost limit passes. The 13-net-win threshold is an engineering requirement on the estimate, not a test that the population advantage exceeds five points. Otherwise choose rule by simplicity and report “no worthwhile learned advantage demonstrated”; do not claim equivalence or population safety.
>
> For episode i and arm a record invalid I_ia, truncated T_ia and repetitive R_ia separately. Invalid means failure of the frozen output parser/schema. Truncated means reaching 256 generated tokens without a complete valid output; a complete valid output ending exactly at the limit is not truncated. For repetition detection only, Unicode-NFKC normalize, casefold and collapse whitespace to single spaces; tokenize with the frozen trunk tokenizer without added special tokens. Repetitive means that some contiguous four-token block occurs eight consecutive nonoverlapping times, starting at any token offset. Define F_ia=I_ia OR T_ia OR R_ia. Require sum_i 1[F_i,clf AND NOT F_i,rule]<=2, not a difference of marginal counts and not three separate allowances.
>
> Define K_ia as a checker-detected change to any protected object/field or other state invariant outside the episode's permitted edits. Require sum_i 1[K_i,clf AND NOT K_i,rule]=0. This is a paired observed-count rule; no subjective causal attribution is required. Report both arms' total K counts and their joint table, since common corruption is not zero corruption.
>
> Binary success requires the frozen parser/schema, all task obligations and all state invariants. Generation failures, malformed or incomplete output, and attempts that fail to produce a complete valid result within the per-attempt token/action/time budgets score zero with their causes retained. A complete valid result produced exactly at the token or action limit is within budget. Repetition is separately recorded and enters the operational gate even if a task checker accepts the output. Infrastructure interruption means an external interruption or resource loss that prevents an attempt from completing, documented in the attempt journal; it does not include completed bad outputs or ordinary generation-budget failures. Resume only a genuinely missing interrupted attempt from identical frozen inputs/state, preserving every completed arm's bytes and prior failed attempts. A manifest mismatch or unresolved harness defect invalidates the study; no episode may be dropped.

**R8 — Replace the cost cap in LEDGER-PLAN.md:905 and amend the latency reporting at :901 with:**

> Cost cap: 8 single-GPU allocated wall-hours for all study model execution, including setup, final arms, any model smoke work, interruptions and resumed work. Measure authoring effort, CPU selector work, peak host/device memory and allocated GPU time separately. Freeze the deployment configuration and per-attempt wall-clock limit before setup. On setup, measure the full and evicted arms and the complete CPU selector/echo paths; estimate the two final arms including prefill, up to 256 generated tokens, and all selection/rendering overhead. Record the explicit number of setup/model-smoke outputs and the projection formula. If measured setup cost plus projected remaining execution exceeds 8 GPU-hours, record NOT RUN for the final study and defer without shrinking N or changing scientific settings.
>
> For engineering adoption require mean standalone end-to-end latency of clf <=1.25 times that of rule over the 256 final episodes. Measure the same boundaries for both arms, including candidate extraction, selection, echo rendering, prefill and generation; do not exclude CPU classifier work or give one arm an uncharged shared cache. Use independently seeded arm execution order per episode, frozen before model outputs, and record that order. Record latency and allocated runtime even for failures. The measurement definition and treatment of external interruptions are frozen in the manifest.
>
> If the global cap or an infrastructure failure prevents completion of all 256 pairs, report INCOMPLETE with elapsed cost and completed counts; do not run confirmatory/adoption analysis on a partial cohort or score never-attempted cases as model failures. A failed setup is NOT RUN, and a defective harness is INVALID. Neither is the complete-study finding “no worthwhile learned advantage demonstrated.”

**R9 — Replace the authoring estimate at LEDGER-PLAN.md:905-906 and expand the power statement at :903-904 with:**

> Authoring estimate: 40.8-64 hours is conditional on 6-10 minutes per original source plus 12-16 shared machinery/review hours. It is not a measured budget for 288 bespoke executable checkers. Use the eight disposable smoke sources to time source construction, rendering, positive-reference verification, six-mutation verification and independent semantic review separately. Publish the resulting projection before production commissioning; if unaffordable, defer or preregister a different study before production sources or model outcomes exist.
>
> Prefer an original declarative scenario language with shared deterministic rendering, finite in-memory operations, complete-state checkers and mutation operators. Each episode still needs a distinct source specification and independent obligation review; reusing an instantiated story with new literals does not increase the independent-source count. Freeze the language/compiler and task primitives before production authoring. Procedurally generate literals, irrelevant content and witnesses from recorded seeds without benchmark templates or policy feedback.
>
> At N=256, exact one-sided McNemar rejection probabilities for a true five-point gain are 78.222% at discordance q=.10 and 50.857% at q=.20; a true ten-point gain at q=.20 gives 97.356%. Requiring both rejection and at least 13 net wins reduces those probabilities to 51.915%, 49.725% and 96.954%, respectively, before setup and operational/cost gates. These are calculations under assumed discordance, not empirical estimates or a claim that SC1 has 80% power for engineering adoption at a five-point true effect.

**VERDICT: SOUND-WITH-FIXES.** The scientific comparison and paired-binary analysis are sound in principle. Resolve F1-F5 before registration/authoring, and freeze explicit resolutions of F6-F9 in the coder brief and registration. A positive result would establish a useful advantage for the frozen learned package over this independently budgeted rule on the registered authored mixture; it would not establish universal learned-selection benefit.
