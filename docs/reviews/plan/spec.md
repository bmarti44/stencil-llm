# Spec Review — plan

**Score:** 85 / 100
**Verdict:** CONDITIONAL PASS (75–89)
**Reviewer model:** codex/gpt-5.6-sol
**Date:** 2026-08-22

## Round log

### Round 7 — 2026-08-22 (codex/gpt-5.6-sol)
- Score: 85 / 100 (delta vs prior round: +3)
- Addressed since prior round:
  - Commit `58ef452` removes the duplicate generator seed argument, fixes Task A's permutation primitive/order, hashes untracked content, and makes one Phase 3 block the sole G3 outcome authority (`PLAN.md:148`, `PLAN.md:292`, `PLAN.md:302`, `PLAN.md:405-415`).
  - The JAX cases now draw `B` and GLU parameters from named streams, and every Phase 2 test must document and count its registered cases; these changes close the former oracle-parameter hold but do not fill the separate proof-case/tolerance gaps (`PLAN.md:372`, `PLAN.md:379`).
  - G3 now selects the primary variant before G3.4, makes unresolved stability red, gives G3.2b-alone no invented qualification, and emits one `green[+...]` state (`PLAN.md:408-415`).
- New or remaining:
  - Task-M/copy fixtures, several mandatory Phase 2 cases/tolerances, and threshold-relevant Phase 4 semantics remain author-selected; the new residual-default rule cannot define semantic options that PLAN never enumerates.
  - The run hash still omits untracked paths and byte framing, while Phase 0 still prints the pre-v1.10 formula.
  - The new acceptance script can succeed with only a Kimi file and no sol review, and the review wrapper's claimed failure-path restoration leaves clean tracked mutations and new untracked files in place.
  - H4 evidence fields/consequences, Phase 6 evidence, README/provenance, rejected Kimi sidecars, session/history wording, B1 initialization, and several lower-severity testability issues remain open.

### Round 6 — 2026-08-22 (codex/gpt-5.6-sol)
- Score: 82 / 100 (delta vs prior round: +8)
- Addressed since prior round:
  - Commit `e872754` replaces H4's fractional pseudo-trial with the first answer from each of 10,000 independent sequences, fixes the non-oscillatory loader contradiction, and makes the Phase 0 `--force` rule honor the different-git-state refusal (`PLAN.md:55`, `PLAN.md:341`, `PLAN.md:470`).
  - The Phase 4 stream is now one explicitly ordered pass, every Phase 2 test receives a general non-vacuity obligation, Kimi gains the generic `phase*`/`tradeoff`/`report` rubric fallback, and both wrappers enforce threshold floors (`PLAN.md:377`, `PLAN.md:412`; `tools/run_codex_review.sh:105-109`; `tools/run_kimi_review.py:103-106`, `tools/run_kimi_review.py:122-130`).
  - G3 now has a fixed clause-evaluation order and Rule 5 admits compositional qualifications; these are substantive improvements even though conflicting G3.4, stability, and state-name authorities still prevent a unique outcome (`PLAN.md:80`, `PLAN.md:406-407`).
- New or remaining:
  - The executed tie-breaks for fixture and JAX completeness are not factually supported by the governing text: the exact permutation primitive, Task-M/copy fixtures, fixture `B`/input shape, and reference mapping remain unregistered.
  - Mandatory Phase 2 and Phase 4 tests still choose threshold-relevant inputs, tolerances, optimizer defaults, sham predicates, and channel order; v1.9's generic non-vacuity sentence does not instantiate those cases.
  - G3 still has contradictory M1/M1b comparators, stability consequences, branch budgets, and qualification spellings.
  - H4's new test is mathematically valid, but its first-answer statistic is absent from the fixed result record and a seed-level strong side channel can be averaged below the strong consequence.
  - Generator seed precedence, dirty/untracked run identity, Phase 6 evidence, review-session prompting, rejected Kimi sidecars, Appendix C provenance, and README remain incomplete or inconsistent.

### Round 5 — 2026-08-22 (codex/gpt-5.6-sol)
- Score: 74 / 100 (delta vs prior round: +0)
- Addressed since prior round:
  - Commit `e028c90` aligns the Phase 0 hash test with Section 3, registers concrete closed-form oscillator cases, scopes fp64 to test-side references/accumulation, and adds variant-specific oscillator-field rules (`PLAN.md:142-143`, `PLAN.md:335`, `PLAN.md:363`, `PLAN.md:464`).
  - G3 qualifications now compose, any registered green state may reach Phase 6, M1b becomes the efficiency comparator when primary, and Phase 5 evidence is subject to trained stability (`PLAN.md:401`, `PLAN.md:418`, `PLAN.md:424`).
  - The Codex review wrapper now routes `tradeoff` and `report` to the generic phase rubric, and H4 correctly separates evidence existence from practical magnitude in principle (`PLAN.md:54`, `PLAN.md:490`; `tools/run_codex_review.sh:117-124`).
- New or remaining:
  - The H4 replacement is not an executable binomial test: its declared trial is an eight-answer fractional sequence mean, not a Bernoulli outcome.
  - Composite G3 states are outside the restricted status enum, the M1b-primary efficiency comparator still contradicts Appendix C's M1-only row, and the stability branch says both red and “downgrade.”
  - Config seeds/fields, Phase 0/1 fixtures, mandatory Phase 2 cases, JAX parameters, Phase 4 optimizer/data slices, run identity, and Phase 6 evidence still require implementation choices or contain contradictions.
  - Kimi still has no generic prompt fallback and deliberately writes rejected sibling review files; the resume/history/amendment sequencing remains inconsistent.
  - Appendix C provenance and README were not updated for the v1.8 H4 amendment, and the deliberately deferred Phase 6 config remains incomplete.

### Round 4 — 2026-08-22 (codex/gpt-5.6-sol)
- Score: 74 / 100 (delta vs prior round: +6)
- Addressed since prior round:
  - Commit `bebbea8` corrects the M1b-init energy target to `(1+G)^(-10000) ~= 0.29`; the registered recurrence replay is now inside the mandatory interval (`PLAN.md:362`).
  - Experiment seeds and named streams are mapped, Task B rules now use `seed_rules`, and its stale-error reference is sequence-specific rather than the invalid cue-blind rate (`PLAN.md:137-138`, `PLAN.md:303-306`).
  - Controller-output wording, the 128-parameter M1/M1b delta, H2's estimator, Appendix C provenance, and the Phase 6 receptive-field arithmetic are internally corrected (`PLAN.md:51`, `PLAN.md:255`, `PLAN.md:279`, `PLAN.md:425`, `PLAN.md:475`).
  - Dirty tracked diffs enter run identity, numeric recurrent/rescue bars and a Task-M-qualified G3 state are registered, and Phase 4's feature scaling and pair sampling are materially tighter (`PLAN.md:141`, `PLAN.md:394-407`, `PLAN.md:493-503`).
- New or remaining:
  - G0 still names the old run-ID formula and an unconditional destructive `--force`, while the governing determinism contract uses a diff hash and conditional refusal; the new hash also omits untracked files.
  - The generator/config boundary, Phase 0/1 fixture bytes, several mandatory Phase 2 inputs/statistics, JAX parameter cases, and Phase 4 optimizer/eval slices remain implementer-selected.
  - The global fp32 proof-test rule directly contradicts the mandatory fp64 oscillator and JAX tests.
  - Two registered qualified G3 states still cannot satisfy the Phase 6 prerequisite, and the advertised Phase 5/7 review topics have no prompt files or generic fallback in either wrapper.
  - Review-history wording/session notes, retained Phase 6 evidence, and the deliberately deferred Phase 6 config/test contract remain incomplete.

### Round 3 — 2026-08-22 (codex/gpt-5.6-sol)
- Score: 68 / 100 (delta vs prior round: +12)
- Addressed since prior round:
  - Commit `e943c9f` fixes the load-bearing receptive-field boundary and positive control: the exact toy lag is now `4*(64-1)=252`, and `test_cue_reachable_when_close` uses that value (`PLAN.md:61`, `PLAN.md:207`, `PLAN.md:366`).
  - Task A now has a constructive balanced rule sampler, independent uniform cue/operand sampling, and a dedicated `seed_rules`; the general eval contract keeps rule tables fixed while offsetting only the example stream (`PLAN.md:292-295`, `PLAN.md:320`, `PLAN.md:447`).
  - Base-model choices, B0 assembly, deterministic parameter matching, copy-task admission, Task-A/Task-B `task_k` semantics, TDD scope, trained-stability gating, and per-row seed aggregation are materially specified (`PLAN.md:73`, `PLAN.md:209`, `PLAN.md:272`, `PLAN.md:276`, `PLAN.md:360`, `PLAN.md:442-457`, `PLAN.md:473-485`).
  - Phase 4 now fixes the checkpoint policy, prefix contract, principal L-BFGS settings, derangement algorithm, and conditional Task-M checkpoint set; H4 now requires claim qualification for every result above 8.25% (`PLAN.md:399-404`, `PLAN.md:483-484`).
  - Full oracle repository SHAs, additional recurrent sanity runs, Phase 5's inherited training block and budget, one run-ID formula, and gate-ineligible dirty runs were added (`PLAN.md:138`, `PLAN.md:362`, `PLAN.md:378`, `PLAN.md:411`, `PLAN.md:526`).
- New or remaining:
  - The newly registered M1b-init damping oracle uses `(1+G)^(-20000)` but labels it `~0.30`; the formula is about 0.085, while the registered recurrence produces about 0.29. Mandatory G2 is still unpassable as written.
  - The four config seed fields are not mapped to the matrix's three experimental seeds, Task B still derives rules from a “dataset seed,” and the generator's additional `seed` argument plus unspecified derived-stream scheme prevent exact reproduction.
  - Several Phase 0-2 fixtures still let their implementer select the inputs and expected behavior; the JAX cases lack exact arrays/parameters and dependency versions, and Phase 4 still lacks a reproducible intervention/evaluation sample contract.
  - The G3 state machine still invokes undefined recurrent-sanity bars, introduces a gate state absent from the governing state vocabulary, and authorizes proceeding after a mandatory sanity failure without any non-red exit state.
  - Dirty-run overwrite safety, review-history enforcement, the deliberately deferred Phase 6 contract, and several smaller arithmetic/provenance contradictions remain open.

### Round 2 — 2026-08-22 (codex/gpt-5.6-sol)
- Score: 56 / 100 (delta vs prior round: +24)
- Addressed since prior round:
  - Commit `18bca48` replaces the invalid flat Task A chance claim with a column-balanced Latin construction and cell-specific cue-blind nulls (`PLAN.md:275-276`, `PLAN.md:451`).
  - The causal next-token contract now fixes inputs, targets, masks, decision positions, and cue-distance indexing (`PLAN.md:265-278`).
  - The oscillator text now identifies symplectic Euler, states the correct modified invariant, and replaces the impossible continuous closed-form oracle with a discrete one (`PLAN.md:206-215`, `PLAN.md:340-343`).
  - Controller shapes and the two-cell dataflow are now explicit; H2 limits the controlled dissipation comparison to M1 versus M1b; Task B and Task M sampling semantics are substantially complete (`PLAN.md:49`, `PLAN.md:217-231`, `PLAN.md:282-298`).
  - Optimizer and basic evaluation settings, Phase 4 intervention details, result retention, Makefile scope, severity-aware review acceptance, authoring roles, governed README language, and repository tracking were materially improved (`PLAN.md:97-101`, `PLAN.md:138-168`, `PLAN.md:302`, `PLAN.md:354-380`; `.gitignore:220-227`; `README.md:17-42`; `tools/check_review_scores.py:18-83`).
- New or remaining:
  - G2 remains unpassable: the positive reachability test uses lag 256 although the registered mask's true four-layer bound is 252, and the damped-energy target is incompatible with the registered damping initialization.
  - The training/eval seed wording can regenerate Task A/B rule tables for evaluation despite simultaneously claiming those tables are shared.
  - Exact base-model choices, parameter-matched widths, config coverage, Latin-square generation, JAX pins, several fixtures, seed aggregation, and the Phase 4 checkpoint policy still require the coder to invent behavior and its oracle.
  - The G3 exit rule contradicts Appendix D.3b, and Appendix D requires M1b/B2 sanity runs absent from the matrix.
  - Run identity, review-history mutability, H4 claim handling, and the deliberately deferred Phase 6 specification remain inconsistent or incomplete.

### Round 1 — 2026-08-22 (codex/gpt-5.6-sol)
- Score: 32 / 100 (delta vs prior round: +0; initial round)
- Addressed since prior round:
  - None. This is the initial review and the canonical review file did not previously exist.
- New or remaining:
  - The Task A construction does not pin an unreachable baseline to 6.25% chance, so the central necessity gate is invalid as specified.
  - The stated recurrence fails its closed-form, exact-energy, and monotone-energy tests; Gate G2 cannot go green honestly.
  - Controller dimensions, controller matching, parameter counts, configuration fields, task sampling, evaluation protocols, and most test fixtures require implementation choices that the plan forbids the coder from inventing.
  - Phase 6, artifact retention, Makefile targets, and review tooling disagree with the governing text.

## Findings

1. **Critical (resolved 2026-08-22: verified constructive column balance, uniform independent sampling, and cell-specific nulls) — Task A's cue-blind ceiling was invalid.** Task A's cyclic construction and uniform independent cue/operand sampling imply the exact `1/k` or `1/16` cue-blind optimum, and Appendix C's 14.5%/8.25% bars follow (`PLAN.md:302-304`, `PLAN.md:496`).

2. **Critical (resolved 2026-08-22: explicit next-token indexing prevents answer leakage) — Answer-token alignment was unspecified.** The causal contract fixes `logits[p] -> tokens[p+1]`, the preceding decision-position mask, and a correct miniature (`PLAN.md:294`).

3. **Critical (resolved 2026-08-22: the determinant-consistent envelope passes an independent replay) — The amended damping fixture had the wrong exponent.** Phase 2 now uses `(1+G)^(-10000) ~= 0.29`; the independently replayed registered recurrence remains inside its interval (`PLAN.md:369`).

4. **High (resolved 2026-08-22: verified complete two-cell shapes and dataflow) — Controller dimensions and stacked-cell plumbing were undefined.** The tensor table fixes `B_1:64x256`, two 64-pair states, `64x64` GLU/cell-2 input, and `c_t=[y_2;z_2] in R^128` (`PLAN.md:243`). Finding 43 tracks one stale generic sentence.

5. **High (resolved 2026-08-22: only M1/M1b are a controlled dissipation comparison) — H2 falsely treated B2 as differing only in energy handling.** H2 restricts the verdict to M1b versus M1 and treats B2 descriptively as structurally different (`PLAN.md:54`, `PLAN.md:282`).

6. **High (resolved 2026-08-22: B0 assembly and a deterministic auditable matching algorithm are registered) — Parameter matching was self-authored and B0's assembly contradicted its count.** B0 has no controller, and the deterministic widening rule yields B0 `d_ff=1032`, all other variants `1024`, and a 0.960% count spread under the registered no-bias architecture (`PLAN.md:282`, `PLAN.md:286`).

7. **High (resolved 2026-08-22: generators are now config-only and the inactive oscillator block is coherent) — The loader contradiction is fixed, but the config/generator randomness API still has competing authorities.** Section 6 now says generators are pure functions of the config alone, whose seed fields also determine evaluation; the competing extra seed argument is gone (`PLAN.md:292`, `PLAN.md:330`, `PLAN.md:462-477`). The remaining unused `seed_train`/Task-B `task_k` schema issues are narrower finding 49.

8. **High (resolved 2026-08-22: Task B and Task M sampling/diagnostic mechanics are materially complete) — Task B and Task M generators were underspecified.** Task B fixes cue/rule/operand/delay semantics and its stale-error reference (`PLAN.md:310-313`). Task M fixes 32 unique keys, replacement-sampled 16-way values, eight queries, placements, and the 1/16 null (`PLAN.md:315-326`); Appendix B provides exactly 32 cue/key, 16 operand/value, and 14 distractor tokens (`PLAN.md:481-486`).

9. **High — Phase 0/1 exact fixtures still require choices absent from the governing construction; the tie-break's factual premise is false.** v1.10 correctly fixes Task A's three `torch.randperm(16)` calls and their order (`PLAN.md:302`), but the promised exact fixture still has no sequence count and its cue/operand/distractor draw calls and per-sequence draw order are not literal (`PLAN.md:304-305`, `PLAN.md:352`). Task M's P=4 exact fixture still has no seed, token bytes, metadata, or fixture-before-generator protocol; its without-replacement/random-order operations are semantic distributions rather than an RNG call sequence (`PLAN.md:323`, `PLAN.md:359`). The distractor and Latin tests leave the held vector/statistic and seeds open (`PLAN.md:355-356`). Phase 0 still omits the copy grammar, targets, variant, optimizer values, and the rest of strict `configs/test_tiny.json` (`PLAN.md:339`, `PLAN.md:345`, `PLAN.md:459-477`). A reviewer can check a chosen fixture, but PLAN still does not uniquely derive it; the tie-break's mechanical-execution premise remains false beyond the newly fixed Latin draws (`docs/reviews/plan/tiebreaks.md:3-4`).

10. **High (resolved 2026-08-22: fixed architecture shapes plus registered B/GLU streams complete the pinned external-oracle cases) — Naming two JAX streams does not determine the oracle cases; the tie-break omits unresolved parameters.** Phase 2 now fixes repository commits, JAX version, `m`, `A/G`, length, dtype, seeds, inputs, and `B`/GLU distributions and named streams (`PLAN.md:372`); Section 5.2 fixes both `B` shapes, zero states, and GLU shapes (`PLAN.md:243`). Those inputs determine committed trajectories through the pinned reference implementations, so literal expected arrays in PLAN are unnecessary. Finding 30 separately covers the ambiguous PyTorch comparison tolerance, and finding 49 notes the stale global stream-name inventory.

11. **Critical (resolved 2026-08-22: the true boundary is registered and independently verified) — The positive reachability test contradicted the fixed mask and made G2 impossible.** The mask yields `L*(w-1)`, hence toy lag 252, and test 8 uses that reachable boundary; Task A lags 514 and 2050 remain beyond it (`PLAN.md:65`, `PLAN.md:217`, `PLAN.md:306`, `PLAN.md:376`).

12. **High (resolved 2026-08-22: Task B shares `seed_rules` across train and evaluation) — Task B could resample its rule table at evaluation.** Task B uses `seed_rules`, while evaluation offsets only `seed_data` (`PLAN.md:310`, `PLAN.md:330`).

13. **High — Phase 4 now fixes stream order, but its pass/fail implementations remain non-unique.** The single pass fixes dataset order (`PLAN.md:419`), but the probe still omits bias, initialization, zero-variance handling, LBFGS `max_eval`, `tolerance_change`, and `line_search_fn`; “classes balanced by construction” is false for a finite IID 10,000-cue sample (`PLAN.md:421`). Patch pairs must be identical except for the cue while also being “drawn sequentially” from the ordinary eval stream, but no base/counterfactual construction is given, so independent draws will not share distractors and operands (`PLAN.md:422`). The sham predicate does not choose logits/tolerance/argmax equality, and Fisher-Yates has no `(layer, head)` flattening order (`PLAN.md:422-423`). These semantic choices can move the frozen G4 bars (`PLAN.md:504`); the generic fallback in finding 45 does not preregister them.

15. **Medium — Phase 6 is safely blocked but still has neither an executable config nor retained gate evidence.** It is expressly a “sized sketch” pending amendment (`PLAN.md:439`). Appendix A covers only Phases 0-5 and omits the widened variant (`PLAN.md:459-477`); G6.3 does not enumerate which toy-only JAX, six-variant count, B1, and Task-A proofs port to the scaled pair (`PLAN.md:443`, `PLAN.md:449`). Raw runs are ignored and the retained-root list names no scale report (`PLAN.md:188-191`; `.gitignore:220-225`).

16. **Medium (resolved 2026-08-22: TDD is scoped to code-bearing phases) — The universal TDD rule disagreed with the run/artifact phases.** Rule 1 scopes test-first work, and the Makefile contract consistently has gates 0-4 and 6 but no gate 5 (`PLAN.md:77`, `PLAN.md:161-162`).

17. **High — `--force` is aligned, but run identity still excludes untracked dirty state and leaves its byte contract undefined.** v1.10 hashes concatenated contents of sorted untracked files, but not their paths or framed `(path,length,content)` records; a rename is invisible and content partitions such as `ab|c` versus `a|bc` collide before hashing (`PLAN.md:148`). The outer concatenation still lacks encodings/delimiters, and “git state” in `env.json` names only git SHA/versions/hardware rather than the tracked/untracked hashes used for overwrite identity (`PLAN.md:148`). Phase 0 then restates the obsolete three-term v1.8 formula with no untracked component (`PLAN.md:340`), so `test_config_hash_stable` and Section 3 disagree. The same-state `--force` guard itself is now aligned (`PLAN.md:343`).

18. **Medium — Review-history, resume prompting, identity grammar, and amendment sequencing still disagree.** PLAN permits dated prior-content edits, while the common header says “preserve verbatim” and the wrapper permits updates (`PLAN.md:101`; `tools/codex-prompts/_common-header.md:24`; `tools/run_codex_review.sh:217-226`). `RESUME_NOTE` still checks `SID` before `SID` is loaded, so resumed prompts omit it (`tools/run_codex_review.sh:180-184`, `tools/run_codex_review.sh:258-264`). Reviewer IDs remain hyphen-form in the template and slash-form in context (`tools/codex-prompts/_common-header.md:14`; `tools/run_codex_review.sh:204`). The unqualified policy requires acceptance before an amendment commit, while v1.10 again landed before this review under the ledger-only initial-loop exception (`PLAN.md:115`, `PLAN.md:127-130`). Finding 48 covers the new title check.

22. **High (resolved 2026-08-22: the base transformer is sufficiently pinned for implementation and counting) — The base transformer was not specified precisely enough to reproduce.** Section 5.1 fixes activation, norms, epsilon, biases, tying, RoPE, dropout, and seeded initialization (`PLAN.md:202-219`). B1's narrower initialization gap is finding 42.

23. **Medium (resolved 2026-08-22: every control-output definition uses the full final-cell state) — Section 5.3 contradicted the fixed control-output shape.** The tensor table and gate section both use `c_t=[y_2;z_2] in R^128` (`PLAN.md:243`, `PLAN.md:262`).

24. **High (resolved 2026-08-22: one explicit sole-authority procedure now determines every G3 outcome) — v1.9 adds an order but still leaves multiple contradictory G3 outcomes.** Phase 3 now explicitly supersedes prior phrasing, evaluates stability and necessity before selecting the primary, compares G3.4 to that primary, gives G3.2b-alone no qualification, and emits one ordered-union `green[+...]` state or red (`PLAN.md:405-415`). Replaying the previous M1b-primary, stability, G3.2b, and combined-qualification cases now has one controlling answer. Stale Appendix C/D prose remains editorially contradictory (`PLAN.md:500`, `PLAN.md:513`, `PLAN.md:518`), but the explicit precedence rule prevents it from changing the registered outcome.

25. **High (resolved 2026-08-22: every registered G3/G4 row names its aggregation) — G3 and G4 thresholds omitted seed aggregation.** Appendix C names aggregation per row, and Phase 4 requires every checkpoint to pass (`PLAN.md:493-504`, `PLAN.md:419`, `PLAN.md:427`). Finding 40 concerns the consequence attached to one explicit aggregation.

26. **High (resolved 2026-08-22: trained stability is a mandatory evidence condition through Phase 6) — Learned oscillator stability was checked but not gated.** The reusable assertion and validity row cover G3/G4/G6, and Phase 5 separately requires it (`PLAN.md:370`, `PLAN.md:431`, `PLAN.md:495`). The v1.10 sole authority makes an unresolved failure red (`PLAN.md:408`).

27. **High (resolved 2026-08-22: claim qualification follows statistical detection, not the practical margin) — H4 bands permitted routing without correcting the strict-separation claim.** H4 and Appendix C require any per-seed detection to qualify the claim (`PLAN.md:56`, `PLAN.md:503`). Finding 40 tracks the remaining evidence-record and strong-band consequence defects.

28. **Low — A sibling canonical review is dirty outside this review's write scope.** Read-only `git status --short` reports `M docs/reviews/plan/science.md`; its Round 7 begins at `docs/reviews/plan/science.md:10`. This review did not alter or restore it.

29. **Medium (resolved 2026-08-22: the treatment delta is counted across both cells) — The parameter paragraph miscounted the M1/M1b difference.** Section 5.5 names the 128-parameter two-cell delta, matching `30,992-30,864` (`PLAN.md:286`).

30. **High — v1.9's generic non-vacuity rule does not instantiate the mandatory Phase 2 proofs or make their tolerances feasible.** Test 1 still omits its initial state, allowing the zero-forcing arm to be all zero, and “within 1e-5” does not say absolute, relative, or `atol/rtol`; period 4096 under unit forcing reaches roughly `4e5`, where fp32 ulps are about `3e-2`, so an absolute `1e-5` oracle is impossible (`PLAN.md:147`, `PLAN.md:368`). Test 2 still omits window size, trend estimator/tolerance, and an exact B2 state fixture (`PLAN.md:369`). The zero-damping test has no nonzero input/state; optional scan omits seed/shape/dtype; gate identity omits tokens/shape; gradient tests omit sample counts/fixture IDs (`PLAN.md:371-376`). Counting cases and copying their prose into docstrings proves only that author-selected cases ran; it does not supply these inputs or make them nontrivial (`PLAN.md:379`). The fallback in finding 45 can select zero and worsen vacuity.

31. **Medium (resolved 2026-08-22: the H2 heuristic gives its literal estimator) — H2's uncertainty condition was not exact.** H2 defines the sample-variance estimator and M1b-minus-M1 scope (`PLAN.md:54`).

32. **Medium (resolved 2026-08-22: Phase 6 distinguishes exact lag from the conservative bound) — Phase 6 mislabeled `L*w` as the receptive field.** It gives 3060 exact, 3072 conservative, and `N=6144` beyond both (`PLAN.md:441`), consistent with Section 1 (`PLAN.md:65`).

33. **Medium (resolved 2026-08-22: the stale-error plot uses a history-conditioned comparator) — Task B had no valid stale-rule null.** Task B registers the exact per-sequence history-conditioned comparator (`PLAN.md:313`).

34. **Low — Appendix C's provenance remains false through v1.9.** The defect persists unchanged in v1.10: Appendix C still says “last amended v1.7” and cites only v1.4-v1.7 although v1.8/v1.9 changed H2/H4 thresholds and the H4 trial (`PLAN.md:9-11`, `PLAN.md:491-503`). Phase 0 has not begun, so preregistration timing is honest; the audit label is not.

35. **High (resolved 2026-08-22: Kimi now uses the same generic topic fallback as Codex) — Mandatory Kimi Phase 5/7 reviews could not start.** Kimi maps `phase*`, `tradeoff`, and `report` to the generic rubric (`tools/run_kimi_review.py:122-130`), matching Section 2b (`PLAN.md:104`, `PLAN.md:109`).

36. **High (resolved 2026-08-22: model execution and test-side reference precision are separated) — The global dtype contract made Phase 2 tests mutually inconsistent.** Models execute fp32 while closed-form references/invariant accumulation may use fp64 (`PLAN.md:147`, `PLAN.md:368-372`). Finding 30 covers tolerance semantics.

37. **High (resolved 2026-08-22: the first answer of each independent sequence is a valid Bernoulli trial) — H4's binomial test had no valid trial.** H4 selects the first answer of 10,000 independent sequences under null `p=1/16`; the first exact upper-tail `p<0.001` cutoff is 702 successes (`PLAN.md:56`, `PLAN.md:323`, `PLAN.md:330`). Its missing artifact and consequence are finding 40.

38. **Medium — Kimi still violates the canonical-review-only policy and contaminates its own context/metrics with rejected siblings.** PLAN permits only canonical output (`PLAN.md:106`, `PLAN.md:184-185`), but Kimi writes `<topic>-kimi.rejected.md`; two such files are tracked, then included by the recursive review-context glob and parsed as metric topics (`tools/run_kimi_review.py:11-12`, `tools/run_kimi_review.py:40-46`, `tools/run_kimi_review.py:183-188`; `tools/agent_metrics.py:88-104`).

39. **Medium — README was not updated for either material H4 amendment.** PLAN requires same-commit README mapping updates (`PLAN.md:194`). H4 uses a first-answer exact test for existence and mean accuracy only for magnitude (`PLAN.md:56`, `PLAN.md:503`), but README still says the “bands ... measure any content routing” and associates low score with no evidence (`README.md:38`). v1.10 also left README untouched.

40. **Medium — H4's valid first-answer decision has no fixed evidence field, and its strong consequence can average away a seed-level falsification.** The fixed JSON has no first-answer successes or p-value, so the registered existence test cannot be reconstructed from the named result (`PLAN.md:330`). Appendix C detects per seed but applies magnitude bands to the mean: `[60,5,5]` detects routing yet averages 23.3 and evades the `>=50` capacity probe/full withdrawal despite one strongly routing checkpoint (`PLAN.md:503`). Phase 4 inherits that trigger (`PLAN.md:424`).

41. **Low — The trained-checkpoint exact-zero-gradient regression has no gate owner.** Phase 2 requires a post-Phase-3 rerun on trained B0-local/B1 checkpoints (`PLAN.md:375`), but G3 and Appendix C name only performance and stability (`PLAN.md:396-415`, `PLAN.md:495`). It can be skipped with every gate green.

42. **Medium — B1's initialization is not registered and need not start near the identity behavior used for recurrent variants.** B1 is a bias-free `sigmoid(w·x_norm)` gate with no initialization in its variant row (`PLAN.md:277`), while recurrent gates are explicitly near multiplier one (`PLAN.md:269`). Appendix G delegates fidelity/initialization to an unpinned repository branch (`PLAN.md:548`). This leaves the claimed M1-minus-B1 statefulness comparison implementation-dependent.

43. **Low — Section 5.2's generic input sentence conflicts with its own fixed cell-2 input.** The continuous system calls `u_t` a 256-dimensional token embedding “per cell” (`PLAN.md:225`), while the tensor table makes cell 2 consume the 64-dimensional GLU through `B_2:64x64` (`PLAN.md:243`). The table makes intent inferable, but the statements are not both literal.

44. **Low — Task B silently pools attention-reachable and recurrence-only delays.** Delay is uniform 32..256 and cue-to-decision lag is delay+2 (`PLAN.md:310`); against receptive field 252 (`PLAN.md:217`), delays 32..250 are reachable and 251..256 are recurrence-only. The only reports pool by switch count/stale error (`PLAN.md:312-313`), weakening the memory-path interpretation.

45. **Medium — The new residual-determinism rule is not a specification oracle.** It assigns any open choice the “lowest-index / lexicographic / first-in-stream option” and records the choice only when exercised (`PLAN.md:381`). That cannot order unenumerated semantic alternatives such as probe bias versus no bias, absolute versus relative tolerance, logits versus argmax equality, or a continuous initial state; choosing a lowest numeric state can make a proof vacuous. The rule yields reproducibility after a coder invents an option set, not pre-run testability, and directly undercuts rule 7's “Do not invent scope” (`PLAN.md:83`). Findings 9, 13, and 30 are therefore not closed by this blanket sentence.

46. **High — The new acceptance command can pass a phase with no sol review.** Section 2b says the phase's sol review is accepted only through `tools/check_acceptance.sh <phase>` (`PLAN.md:105`). The script loops over `*.md` but skips every `*-kimi.md`; if a phase directory contains only a Kimi review, the loop performs zero sol checks, the Kimi `ls` succeeds, and the script exits zero (`tools/check_acceptance.sh:7-13`). It also accepts any Kimi topic/age rather than the gate-critical review named by the cadence. This is a direct mechanical bypass of the mandatory 90-point, zero-open-High/Critical sol gate.

47. **High — Review-wrapper failure containment still leaves unauthorized repository mutations in place.** PLAN says uncontained drift is a hard failure and the wrapper's restorer protects concurrent work (`PLAN.md:106`). The new failure handler copies only files present in `WRAPPER_PRE_DIR`, which snapshots files dirty before launch; a clean tracked file modified by Codex and a newly created untracked file have no snapshot and are not restored or removed before exit (`tools/run_codex_review.sh:161-175`, `tools/run_codex_review.sh:321-333`). The successful-path restorer has the same gap and explicitly leaves unsnapshotted mutations untouched before exiting 5 (`tools/run_codex_review.sh:379-422`). Thus the v1.10 claim that failure-path drift is restored (`PLAN.md:9`) is false, and a failed reviewer can leave source/tool mutations outside its canonical file.

48. **Medium — The new finding-title validator does not bind a title to its finding number.** `_hc_titles` extracts each prior High/Critical title, but validation searches only for its first 40 characters anywhere in the entire candidate (`tools/review_round_tracking.py:116-131`). Swapping the titles/bodies of two preserved finding numbers, or copying the old title phrase into Evidence, satisfies the check. The claimed title immutability in v1.10 therefore does not close silent finding substitution (`PLAN.md:9`, `PLAN.md:101`).

49. **Medium — The strict config and RNG inventories retain smaller contradictions after the API fix.** The registered global stream-name list omits the locally required `fixtures:a`, `fixtures:b`, `fixtures:glu`, and `fixtures:input` names (`PLAN.md:144`, `PLAN.md:372`). `seed_train` and stream `train` have no named stochastic consumer with dropout disabled, while Task B fixes `k=8` but Appendix A makes `task_k` an unconstrained active field (`PLAN.md:144-145`, `PLAN.md:310`, `PLAN.md:462-477`). A strict loader can accept a Task-B config that disagrees with its task spec, and equivalent runs can carry a semantically inert seed.

## Recommendations

1. Finish the Phase 0/1 fixtures: register the complete copy config/grammar/targets, Task A fixture count and all sample draw calls, the Task M miniature seed/bytes/metadata/protocol, and literal distractor/Latin cases (`PLAN.md:302-305`, `PLAN.md:339-359`, `PLAN.md:459-477`).
2. Freeze every Phase 2 input and comparison: nonzero initial states/forcing, explicit `atol`/`rtol`, the invariant window/trend statistic, B2/scan/gate fixtures, and gradient sample counts; do not treat the residual-default rule as an oracle (`PLAN.md:368-381`).
3. Complete Phase 4's classifier bias/init/zero-variance and LBFGS settings, define paired counterfactual construction and sham equality, and register the `(layer,head)` order (`PLAN.md:419-423`).
4. Hash framed untracked `(path,length,content)` records, define all outer hash encodings/delimiters and `env.json` git-state fields, and update the Phase 0 test to the v1.10 formula (`PLAN.md:148`, `PLAN.md:340`, `PLAN.md:343`).
5. Make `check_acceptance.sh` require the registered sol file(s) explicitly and fail when none were checked; bind the required Kimi review to the phase/topic and current acceptance event (`PLAN.md:104-105`; `tools/check_acceptance.sh:7-13`).
6. Snapshot all tracked files or otherwise restore clean tracked mutations, remove reviewer-created untracked files on failure, and run containment before every wrapper exit (`PLAN.md:106`; `tools/run_codex_review.sh:161-175`, `tools/run_codex_review.sh:321-333`, `tools/run_codex_review.sh:379-422`).
7. Bind prior finding titles to the same number in the Findings section, then align the common header, SID construction, reviewer-ID grammar, and amendment sequencing with PLAN (`PLAN.md:101`, `PLAN.md:115`; `tools/review_round_tracking.py:116-131`; `tools/run_codex_review.sh:180-204`, `tools/run_codex_review.sh:258-264`).
8. Add first-answer successes and exact p-values to the fixed result record; trigger the strong H4 consequence on any strong seed or explicitly scope the claim to mean behavior (`PLAN.md:56`, `PLAN.md:330`, `PLAN.md:424`, `PLAN.md:503`).
9. Move rejected Kimi candidates outside `docs/reviews` and exclude them from context and metrics (`PLAN.md:106`, `PLAN.md:184-185`; `tools/run_kimi_review.py:40-46`, `tools/run_kimi_review.py:183-188`; `tools/agent_metrics.py:88-104`).
10. In the Phase 6 amendment, extend Appendix A, enumerate the scaled proof subset, and retain a committed scale-evidence report outside ignored run directories (`PLAN.md:439-449`, `PLAN.md:459-477`; `.gitignore:220-225`).
11. Update Appendix C provenance and README's H4 explanation through v1.10, and assign the trained-checkpoint gradient rerun to G3 (`PLAN.md:194`, `PLAN.md:375`, `PLAN.md:491-503`; `README.md:38`).
12. Register B1 initialization, correct the cell-2 input sentence, stratify Task B by reachability, pin `task_k=8`, and either define or remove the inert training RNG (`PLAN.md:144-145`, `PLAN.md:225`, `PLAN.md:243`, `PLAN.md:277`, `PLAN.md:310-313`, `PLAN.md:462-477`).

## Evidence consulted

- `PLAN.md:1-551`, read in full, including Section 2b, the full ledger, Sections 3-6, Phases 0-7, and Appendices A-G.
- `README.md:1-66`, read in full and checked against H4, governed artifacts, and status language.
- Existing `docs/reviews/plan/spec.md`, including every stable finding and the verbatim Round 1-6 log blocks; `docs/reviews/plan/tiebreaks.md:1-10`, whose fixture/JAX premises were rechecked after v1.10.
- Commit `58ef452` inspected with read-only `git show`, `git diff e872754..58ef452`, `git log`, and `git diff --check`; amendment-log claims were checked against normative text and tooling.
- `.gitignore:1-230`, `tools/check_acceptance.sh:1-13`, `tools/check_review_scores.py:1-111`, `tools/review_round_tracking.py:1-174`, `tools/run_codex_review.sh:1-425`, `tools/run_kimi_review.py:1-198`, `tools/agent_metrics.py:1-131`, and `tools/codex-prompts/_common-header.md:1-53`, checked against Section 2b, canonical output, acceptance, containment, history, and result retention.
- Repository inventory from `rg --files`; no implementation, configs, Makefile, fixtures, result runs, or replayable gate exists, while two tracked `*-kimi.rejected.md` sibling files remain.
- Vocabulary/run replay: PAD + 32 cues/keys + QRY + 16 operands/values + 14 distractors = 64; `P=32` exhausts the key range; the gate count is `4x4=16`; Phase 3 has 66 Task A plus 30 Task M runs = 96, inside “roughly 90 to 100.”
- Receptive-field replay: toy maximal lag `4*(64-1)=252`, scaled lag `12*(256-1)=3060`; Task A lags 514/2050 and Phase 6 `N=6144` remain unreachable; Task B delays 251..256 cross the toy boundary.
- Parameter replay: base `3,180,800`; additions M1 `30,864`, M1b `30,992`, B2 `34,960`, B1 `4,096`; B0 `d_ff=1032` and all others `1024` yield a 0.960% spread.
- Numerical replay: the recurrence remains symplectic Euler with implicit damping and preserves the stated undamped modified invariant; the corrected damping envelope is attainable. Period-4096 unit forcing still makes an unspecified absolute fp32 `1e-5` comparison infeasible.
- H4 replay: first-answer trials are Bernoulli(1/16), with exact `p<0.001` cutoff 702/10,000; the fixed JSON cannot reconstruct the statistic, and `[60,5,5]` demonstrates mean banding can hide a strong seed.
- Read-only acceptance/containment audit: `check_acceptance.sh`'s only-Kimi path performs no sol score check; the review wrapper snapshots only preexisting dirty files, so clean tracked and newly untracked reviewer mutations have no restoration source.
- Read-only `git status --short` showed only `docs/reviews/plan/science.md` modified outside this canonical path before writing; its Round 7 begins at line 10. This review did not alter or restore it.
- No implementation gate could be replayed because the repository remains at the specification-only stage.
