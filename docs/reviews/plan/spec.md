# Spec Review — plan

**Score:** 89 / 100
**Verdict:** CONDITIONAL PASS (75–89)
**Reviewer model:** codex/gpt-5.6-sol
**Date:** 2026-08-22

## Round log

### Round 9 — 2026-08-22 (codex/gpt-5.6-sol)
- Score: 89 / 100 (delta vs prior round: +2)
- Addressed since prior round:
  - Commit `e7034af` resolves the reopened dtype contradiction: Section 3 now expressly permits the registered fp64 isolated-cell numerics cases while keeping model-level proof tests fp32, matching Phase 2 test 1 (`PLAN.md:150`, `PLAN.md:371`).
  - The same commit fixes one Phase 4 optimizer degree of freedom by registering LBFGS `line_search_fn="strong_wolfe"`, and it defines the aggregate plan-acceptance command and threshold (`PLAN.md:105`, `PLAN.md:424`).
  - Appendix C no longer carries the stale hard-coded “last amended v1.7” label (`PLAN.md:494`), although the replacement's sole provenance authority does not record v1.12 and therefore remains incomplete.
- New or remaining:
  - Four High findings remain open: G4 still depends on unspecified data/intervention semantics, G2 still contains author-selected proof cases and predicates, run-ID serialization still has multiple compliant byte encodings, and the review wrapper still leaves unauthorized clean-tracked and review-sidecar mutations in place.
  - Phase 6 remains deliberately non-executable, and H4's retained evidence/consequence aggregation, Kimi rejected sidecars, title binding, README mapping, schema/RNG details, and smaller architecture/testability contradictions remain open.
  - The amendment log omits v1.12 even after Appendix C made that log the “sole provenance authority,” and the pre-acceptance ledger exception still conflicts with the unqualified review-before-amendment-commit rule.

### Round 8 — 2026-08-22 (codex/gpt-5.6-sol)
- Score: 87 / 100 (delta vs prior round: +2)
- Addressed since prior round:
  - Commit `a2f8a67` closes the fixture hold and materially tightens run identity: Task A/Task M now have fixed counts, seeds, RNG calls, and pre-authoring protocols; the copy config is materially complete; and untracked identity records include paths and framing (`PLAN.md:150`, `PLAN.md:304-306`, `PLAN.md:341-342`, `PLAN.md:361`).
  - The acceptance script now fails when it checks zero sol reviews, the probe fixes bias and initialization, and commit `9b2eb7d` completes the SID-definition reorder so resumed reviews receive the intended prompt without the intervening `set -u` crash (`PLAN.md:423`; `tools/check_acceptance.sh:7-15`; `tools/run_codex_review.sh:180-214`).
  - The common header now matches slash-form reviewer IDs and the annotated-history contract (`tools/codex-prompts/_common-header.md:14-24`, `tools/codex-prompts/_common-header.md:48-53`).
- New or remaining:
  - v1.11 regresses the proof-test dtype contract: Section 3 requires proof cells/models to execute fp32 while Phase 2 now requires the same oscillator cell to execute fp64.
  - Mandatory Phase 2 tests beyond the newly repaired closed-form case and threshold-relevant Phase 4 tests still omit cases, tolerance semantics, or construction details; G2/G4 therefore remain author-defined at material boundaries.
  - The run-ID record framing is fixed, but the outer concatenation still does not say whether nested SHA values are raw digests or hex text, so G0 has more than one compliant run ID.
  - Review-wrapper containment still leaves clean tracked mutations and unauthorized `docs/reviews/` sidecars in place despite reporting hard failure.
  - H4 evidence/consequences, Phase 6 evidence/configuration, Kimi rejected sidecars, Appendix C provenance, README, and smaller schema/architecture inconsistencies remain open.

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

1. **Critical (resolved 2026-08-22: verified constructive column balance, uniform independent sampling, and cell-specific nulls) — Task A's cue-blind ceiling was invalid.** (updated 2026-08-22: current v1.12 citations.) Task A's cyclic construction, fixed permutation calls, and uniform independent cue/operand sampling imply the exact `1/k` or `1/16` cue-blind optimum; Appendix C's 14.5%/8.25% bars follow (`PLAN.md:305-309`, `PLAN.md:499`).

2. **Critical (resolved 2026-08-22: explicit next-token indexing prevents answer leakage) — Answer-token alignment was unspecified.** (updated 2026-08-22: current v1.12 citation.) The causal contract fixes `logits[p]` predicting `tokens[p+1]`, places the loss mask on the preceding answer-decision position, and gives a correct miniature (`PLAN.md:297`).

3. **Critical (resolved 2026-08-22: the determinant-consistent envelope passes an independent replay) — The amended damping fixture had the wrong exponent.** (updated 2026-08-22: current v1.12 citation.) Phase 2 uses the attainable envelope `(1+G)^(-10000)`, approximately 0.29 at the registered M1b initialization; the independent recurrence replay remains inside its interval (`PLAN.md:372`).

4. **High (resolved 2026-08-22: verified complete two-cell shapes and dataflow) — Controller dimensions and stacked-cell plumbing were undefined.** (updated 2026-08-22: current v1.12 citations.) The tensor table fixes `B_1` as 64x256, two 64-pair states, the 64x64 GLU/cell-2 input, and `c_t=[y_2;z_2]` in `R^128` (`PLAN.md:246-259`). Finding 43 retains one stale generic sentence.

5. **High (resolved 2026-08-22: only M1/M1b are a controlled dissipation comparison) — H2 falsely treated B2 as differing only in energy handling.** (updated 2026-08-22: current v1.12 citations.) H2 restricts its adjudicated contrast to M1b versus M1 and labels B2 structurally uncontrolled; Section 5.4 agrees (`PLAN.md:55`, `PLAN.md:280-285`).

6. **High (resolved 2026-08-22: B0 assembly and a deterministic auditable matching algorithm are registered) — Parameter matching was self-authored and B0's assembly contradicted its count.** (updated 2026-08-22: current v1.12 citations.) B0 has no controller and the deterministic widening rule yields B0 `d_ff=1032`, all other variants 1024, and a 0.960% spread under the registered no-bias architecture (`PLAN.md:285-289`).

7. **High (resolved 2026-08-22: generators are now config-only and the inactive oscillator block is coherent) — The loader contradiction is fixed, but the config/generator randomness API still has competing authorities.** (updated 2026-08-22: current v1.12 citations.) Generators are config-only, evaluation derives from those config seeds, and inactive oscillator fields are consistently null (`PLAN.md:295`, `PLAN.md:331-333`, `PLAN.md:462-480`). The smaller stream/schema inventory defects remain finding 49.

8. **High (resolved 2026-08-22: Task B and Task M sampling/diagnostic mechanics are materially complete) — Task B and Task M generators were underspecified.** (updated 2026-08-22: current v1.12 citations.) Task B fixes its cue, rule, operand, delay, and stale-error semantics; Task M fixes 32 keys, 16 values, eight queries, placements, and the 1/16 null; Appendix B has exactly the required ranges (`PLAN.md:311-329`, `PLAN.md:482-490`).

9. **High (resolved 2026-08-22: v1.11 registers both miniature fixture protocols and the full copy harness) — Phase 0/1 exact fixtures still require choices absent from the governing construction; the tie-break's factual premise is false.** (updated 2026-08-22: current v1.12 citations.) v1.11 fixes Task A at four sequences with exact seeds and draw order, fixes Task M at P=4/two queries/four sequences with exact streams and calls, and gives the copy harness its architecture, data, targets, optimizer, steps, batch, precision, and seeds (`PLAN.md:307`, `PLAN.md:342`, `PLAN.md:355`, `PLAN.md:362`). Together with the mandatory fixture-before-generator and reviewer hand-replay contract, those fixtures are independently derived enough to close this High finding (`PLAN.md:365`; `docs/reviews/plan/tiebreaks.md:3-4`). Residual coverage choices in the property tests are tracked under finding 45.

10. **High (resolved 2026-08-22: fixed architecture shapes plus registered B/GLU streams complete the pinned external-oracle cases) — Naming two JAX streams does not determine the oracle cases; the tie-break omits unresolved parameters.** (updated 2026-08-22: current v1.12 citations.) Phase 2 fixes commits, JAX version, state dimension, A/G, length, dtype, seeds, inputs, and B/GLU distributions; Section 5.2 fixes their shapes and zero states (`PLAN.md:246`, `PLAN.md:375`). Finding 30 separately covers comparison semantics.

11. **Critical (resolved 2026-08-22: the true boundary is registered and independently verified) — The positive reachability test contradicted the fixed mask and made G2 impossible.** (updated 2026-08-22: current v1.12 citations.) The mask yields `L*(w-1)`, hence toy lag 252, and test 8 uses that reachable boundary; Task A lags 514 and 2050 remain beyond it (`PLAN.md:66`, `PLAN.md:220`, `PLAN.md:309`, `PLAN.md:379`).

12. **High (resolved 2026-08-22: Task B shares seed_rules across train and evaluation) — Task B could resample its rule table at evaluation.** (updated 2026-08-22: current v1.12 citations.) Task B uses `seed_rules`, while evaluation offsets only `seed_data` (`PLAN.md:313`, `PLAN.md:333`).

13. **High — Phase 4 now fixes stream order, but its pass/fail implementations remain non-unique.** (updated 2026-08-22: v1.12 registers `strong_wolfe`; the remaining semantic choices are unchanged.) LBFGS still omits `max_eval` and `tolerance_change`; zero-variance standardization is undefined; and the claim that a finite IID 10,000-cue sample is “balanced by construction” is false (`PLAN.md:424`). Patch pairs must be identical except for cue yet be “drawn sequentially” from an ordinary eval stream, without a registered base/counterfactual construction; the sham predicate does not choose bitwise logits, toleranced logits, or argmax equality (`PLAN.md:425`). Fisher-Yates still lacks the fixed flattening order mapping indices 0..15 to `(layer, head)` channels (`PLAN.md:426`). These choices can change G4 against its frozen bars (`PLAN.md:507`).

15. **Medium — Phase 6 is safely blocked but still has neither an executable config nor retained gate evidence.** (updated 2026-08-22: current v1.12 citations.) Phase 6 remains an explicit “sized sketch” pending amendment; Appendix A covers only Phases 0-5 and omits the widened variant, G6.3 does not enumerate which toy-only proofs port, and ignored raw runs have no named committed scale report (`PLAN.md:440-452`, `PLAN.md:462-480`; `.gitignore:220-225`).

16. **Medium (resolved 2026-08-22: TDD is scoped to code-bearing phases) — The universal TDD rule disagreed with the run/artifact phases.** (updated 2026-08-22: current v1.12 citations.) Rule 1 scopes test-first work to code-bearing phases, and the Makefile contract consistently has gates 0-4 and 6 but no gate 5 (`PLAN.md:78`, `PLAN.md:164-166`).

17. **High — `--force` is aligned, but run identity still excludes untracked dirty state and leaves its byte contract undefined.** (updated 2026-08-22: v1.12 does not change the remaining serialization defect.) Section 3 frames untracked records as UTF-8 path, NUL, decimal length, NUL, and content, and Phase 0 delegates to that formula (`PLAN.md:151`, `PLAN.md:343`). But canonical JSON bytes are concatenated with `git_sha` and two nested SHA-256 results without stating whether those results are raw 32-byte digests or ASCII hex, how `git_sha` is encoded, or the exact bytes produced for the tracked diff. Both common conventions satisfy the prose and produce different IDs; `env.json`'s “both identity hashes” inherits the ambiguity (`PLAN.md:151`). The collision class is fixed, but the exact run identity and G0 known-answer oracle are not.

18. **Medium — Review-history, resume prompting, identity grammar, and amendment sequencing still disagree.** (updated 2026-08-22: only amendment sequencing remains.) PLAN, the common header, and the wrapper agree on annotated history, slash-form IDs, and pre-prompt SID loading (`PLAN.md:102`; `tools/codex-prompts/_common-header.md:14-24`; `tools/run_codex_review.sh:180-214`). The remaining contradiction is sequencing: the governing rule says an amendment review “must be accepted BEFORE the amendment commit lands,” while the ledger records v1.12 as already applied before this Round 9 review (`PLAN.md:116`, `PLAN.md:128`). The new plan-acceptance sentence says only that “further plan changes” follow the amendment path after acceptance, whereas the unqualified rule and amendment log already call the current pre-acceptance changes amendments; the ledger-only exception remains the sole explicit reinterpretation (`PLAN.md:105`, `PLAN.md:128-133`).

22. **High (resolved 2026-08-22: the base transformer is sufficiently pinned for implementation and counting) — The base transformer was not specified precisely enough to reproduce.** (updated 2026-08-22: current v1.12 citations.) Section 5.1 fixes activation, norms, epsilon, biases, tying, RoPE, dropout, and seeded initialization (`PLAN.md:205-222`). B1's narrower initialization gap remains finding 42.

23. **Medium (resolved 2026-08-22: every control-output definition uses the full final-cell state) — Section 5.3 contradicted the fixed control-output shape.** (updated 2026-08-22: current v1.12 citations.) The tensor table and gate section both use `c_t=[y_2;z_2]` in `R^128` (`PLAN.md:246`, `PLAN.md:265-272`).

24. **High (resolved 2026-08-22: one explicit sole-authority procedure now determines every G3 outcome) — v1.9 adds an order but still leaves multiple contradictory G3 outcomes.** (updated 2026-08-22: current v1.12 citations.) Phase 3 explicitly supersedes prior phrasing, evaluates stability and necessity before selecting the primary, compares G3.4 to that primary, and emits one ordered-union state or red (`PLAN.md:408-418`). Stale Appendix C/D prose remains editorially inconsistent (`PLAN.md:503`, `PLAN.md:516-523`), but cannot override that block.

25. **High (resolved 2026-08-22: every registered G3/G4 row names its aggregation) — G3 and G4 thresholds omitted seed aggregation.** (updated 2026-08-22: current v1.12 citations.) Appendix C specifies aggregation per row and Phase 4 requires all three checkpoints to pass (`PLAN.md:496-508`, `PLAN.md:422`, `PLAN.md:430`).

26. **High (resolved 2026-08-22: trained stability is a mandatory evidence condition through Phase 6) — Learned oscillator stability was checked but not gated.** (updated 2026-08-22: current v1.12 citations.) The reusable assertion and validity row cover G3/G4/G6, Phase 5 separately requires it, and the sole G3 authority makes unresolved failure red (`PLAN.md:373`, `PLAN.md:411`, `PLAN.md:434`, `PLAN.md:498`).

27. **High (resolved 2026-08-22: claim qualification follows statistical detection, not the practical margin) — H4 bands permitted routing without correcting the strict-separation claim.** (updated 2026-08-22: current v1.12 citations.) H4 and Appendix C require any per-seed detection to qualify the claim (`PLAN.md:57`, `PLAN.md:506`). Finding 40 tracks the evidence record and strong-band consequence.

28. **Low (resolved 2026-08-22: read-only status was clean before this canonical edit) — A sibling canonical review is dirty outside this review's write scope.** (updated 2026-08-22: Round 9 also began from a clean worktree.) No sibling or other outside-path drift was present before this canonical edit; this review wrote only its Round 9 block in `docs/reviews/plan/spec.md:10` and current findings/recommendations below it.

29. **Medium (resolved 2026-08-22: the treatment delta is counted across both cells) — The parameter paragraph miscounted the M1/M1b difference.** (updated 2026-08-22: current v1.12 citation.) Section 5.5 names the 128-parameter two-cell delta, matching 30,992 minus 30,864 (`PLAN.md:289`).

30. **High — v1.9's generic non-vacuity rule does not instantiate the mandatory Phase 2 proofs or make their tolerances feasible.** (updated 2026-08-22: v1.12 fixes the dtype conflict but none of these cases.) Test 2 omits the undamped window size, trend estimator/tolerance, and an exact B2 state fixture (`PLAN.md:372`). Test 3 has no nonzero input/state, so bitwise equality can pass on a zero trajectory; test 4 and the optional scan test still say only “within 1e-5” despite test 1's declaration that every Phase 2 tolerance has explicit `rtol`/`atol`, and the scan case omits seed, shape, and dtype (`PLAN.md:371`, `PLAN.md:374-376`). Gate identity omits tokens/shape, and the gradient tests omit sample counts or fixture IDs (`PLAN.md:377-379`). The case-count rule proves only that author-selected cases ran (`PLAN.md:382`). Mandatory G2 proof strength and some pass/fail predicates remain implementation-defined.

31. **Medium (resolved 2026-08-22: the H2 heuristic gives its literal estimator) — H2's uncertainty condition was not exact.** (updated 2026-08-22: current v1.12 citation.) H2 defines the sample-variance estimator and confines it to M1b-minus-M1 (`PLAN.md:55`).

32. **Medium (resolved 2026-08-22: Phase 6 distinguishes exact lag from the conservative bound) — Phase 6 mislabeled `L*w` as the receptive field.** (updated 2026-08-22: current v1.12 citations.) Phase 6 gives exact lag 3060, labels 3072 conservative, and places `N=6144` beyond both, consistent with Section 1 (`PLAN.md:66`, `PLAN.md:444`).

33. **Medium (resolved 2026-08-22: the stale-error plot uses a history-conditioned comparator) — Task B had no valid stale-rule null.** (updated 2026-08-22: current v1.12 citation.) Task B registers the exact per-sequence history-conditioned comparator (`PLAN.md:316`).

34. **Medium — Appendix C's provenance remains false through v1.9.** (updated 2026-08-22: v1.12 removes the stale version label but makes an incomplete log the sole authority.) Appendix C now says “the amendment log is the sole provenance authority” (`PLAN.md:494`), but that log ends at v1.11 and contains no v1.12 entry even though v1.12 changed the proof dtype contract, Phase 4 optimizer, acceptance definition, and this provenance rule itself (`PLAN.md:7-9`, `PLAN.md:105`, `PLAN.md:150`, `PLAN.md:424`). Phase 0 has not begun, so preregistration timing is honest; the declared audit trail is not complete.

35. **High (resolved 2026-08-22: Kimi now uses the same generic topic fallback as Codex) — Mandatory Kimi Phase 5/7 reviews could not start.** (updated 2026-08-22: current v1.12 citations.) Kimi maps phase topics, tradeoff, and report to the generic rubric, matching Section 2b (`PLAN.md:105`, `PLAN.md:110`; `tools/run_kimi_review.py:122-130`).

36. **High (resolved 2026-08-22: v1.12 expressly permits the registered fp64 isolated-cell numerics run) — The global dtype contract made Phase 2 tests mutually inconsistent.** Section 3 now distinguishes model-level tests 6-8, which execute fp32, from cell-numerics tests 1-2, which may execute the isolated cell fp64 where registered and compare against fp32 (`PLAN.md:150`). Phase 2 test 1 is exactly such a registered fp64 case with a separate fp32 consistency bound (`PLAN.md:371`). Both requirements can now be satisfied.

37. **High (resolved 2026-08-22: the first answer of each independent sequence is a valid Bernoulli trial) — H4's binomial test had no valid trial.** (updated 2026-08-22: current v1.12 citations.) H4 selects the first answer from 10,000 independent sequences under `p=1/16`; its first exact `p<0.001` cutoff remains 702 successes (`PLAN.md:57`, `PLAN.md:326`, `PLAN.md:333`). Finding 40 covers retention and consequence defects.

38. **Medium — Kimi still violates the canonical-review-only policy and contaminates its own context/metrics with rejected siblings.** (updated 2026-08-22: unchanged in v1.12.) PLAN permits only canonical review output, but Kimi writes `topic-kimi.rejected.md`; the repository tracks process, science, and spec rejected files, and the recursive context/metrics globs ingest them as reviews (`PLAN.md:107`, `PLAN.md:186-187`; `tools/run_kimi_review.py:40-46`, `tools/run_kimi_review.py:183-188`; `tools/agent_metrics.py:88-104`).

39. **Medium — README was not updated for either material H4 amendment.** (updated 2026-08-22: v1.12 still leaves README unchanged.) PLAN requires same-commit mapping updates (`PLAN.md:197`). H4 uses a first-answer exact test for existence and mean accuracy only for magnitude (`PLAN.md:57`, `PLAN.md:506`), but README says the “bands ... measure any content routing” and associates low score with no evidence (`README.md:38`).

40. **Medium — H4's valid first-answer decision has no fixed evidence field, and its strong consequence can average away a seed-level falsification.** (updated 2026-08-22: current v1.12 citations.) The fixed JSON lacks first-answer successes and p-value, so the registered existence test cannot be reconstructed from the named record (`PLAN.md:333`). Appendix C detects per seed but bands the mean: seed accuracies `[60,5,5]` detect routing yet average 23.3 and evade the `>=50` capacity-probe/full-withdrawal consequence despite one strongly routing checkpoint (`PLAN.md:506`). Phase 4 inherits that trigger (`PLAN.md:427`).

41. **Low — The trained-checkpoint exact-zero-gradient regression has no gate owner.** (updated 2026-08-22: current v1.12 citations.) Phase 2 requires a post-Phase-3 rerun on trained B0-local/B1 checkpoints, but G3 and Appendix C own only performance and stability; all registered gates can be green if the rerun is skipped (`PLAN.md:378`, `PLAN.md:399-418`, `PLAN.md:498`).

42. **Medium — B1's initialization is not registered and need not start near the identity behavior used for recurrent variants.** (updated 2026-08-22: current v1.12 citations.) B1 is a bias-free sigmoid gate with no initialization in its variant row, whereas recurrent gates initialize near multiplier one; Appendix G delegates the missing detail to an unpinned repository (`PLAN.md:272`, `PLAN.md:280`, `PLAN.md:551`).

43. **Low — Section 5.2's generic input sentence conflicts with its own fixed cell-2 input.** (updated 2026-08-22: current v1.12 citations.) The continuous system calls `u_t` a 256-dimensional token embedding “per cell,” while the tensor table makes cell 2 consume a 64-dimensional GLU output through `B_2:64x64` (`PLAN.md:228-232`, `PLAN.md:246`).

44. **Low — Task B silently pools attention-reachable and recurrence-only delays.** (updated 2026-08-22: current v1.12 citations.) Delay is uniform 32..256 and cue-to-decision lag is delay+2; against exact field 252, delays 32..250 are attention-reachable and 251..256 recurrence-only, but reports pool only by switch count and stale error (`PLAN.md:220`, `PLAN.md:313-316`).

45. **Medium — The new residual-determinism rule is not a specification oracle.** (updated 2026-08-22: v1.12 fixes the LBFGS line-search example only.) “Lowest-index / lexicographic / first-in-stream” still cannot order unenumerated semantic alternatives such as logits versus argmax sham equality, invariant trend estimators, tolerance pairs, or continuous fixtures (`PLAN.md:384`). It yields reproducibility only after a coder invents an option set, contrary to “Do not invent scope” (`PLAN.md:84`). Findings 13 and 30 remain concrete consequences; the unspecified held fixture/seeds for distractor and Latin property tests are smaller G1 examples (`PLAN.md:358-359`).

46. **High (resolved 2026-08-22: acceptance now fails when zero sol files were checked) — The new acceptance command can pass a phase with no sol review.** tools/check_acceptance.sh now increments an explicit sol-file count, excludes Kimi/rejected/tie-break files, and sets failure when the count is zero (tools/check_acceptance.sh:7-15). A Kimi-only directory can no longer exit successfully. The script still checks Kimi presence rather than topic freshness, but that narrower advisory-cadence issue does not preserve the High bypass.

47. **High — Review-wrapper failure containment still leaves unauthorized repository mutations in place.** (updated 2026-08-22: unchanged in v1.12.) On failure, a clean tracked file modified by Codex was absent from the pre-run dirty snapshot; because it is tracked, the new deletion branch does nothing and the mutation remains (`tools/run_codex_review.sh:161-175`, `tools/run_codex_review.sh:321-340`). Newly created files under `docs/reviews` are explicitly spared, including unauthorized siblings (`tools/run_codex_review.sh:327-336`). The success-path restorer likewise restores only preexisting dirty files and intentionally leaves unsnapshotted drift before exiting 5 (`tools/run_codex_review.sh:386-429`). This contradicts PLAN's canonical-only and hard-containment guarantees (`PLAN.md:107`).

48. **Medium — The new finding-title validator does not bind a title to its finding number.** (updated 2026-08-22: unchanged in v1.12.) The validator extracts prior titles by number but searches each title's first 40 characters anywhere in the candidate, not in that numbered finding; swapping titles between findings or copying the phrase into Evidence passes (`tools/review_round_tracking.py:116-142`). The advertised title immutability is therefore not mechanically enforced as stated (`PLAN.md:102`).

49. **Medium — The strict config and RNG inventories retain smaller contradictions after the API fix.** (updated 2026-08-22: unchanged in v1.12.) The global registered stream list omits `fixtures:init`, `fixtures:a`, `fixtures:b`, `fixtures:glu`, and `fixtures:input`, all required later (`PLAN.md:147`, `PLAN.md:371`, `PLAN.md:375`). `seed_train` and stream `train` have no named stochastic consumer with dropout disabled; Task B fixes `k=8` but Appendix A accepts `task_k` as an unconstrained active field (`PLAN.md:147-148`, `PLAN.md:313`, `PLAN.md:465-480`). Equivalent runs can carry inert seeds and a strict loader can accept a Task-B config contradicting its task spec.

## Recommendations

1. Finish every remaining Phase 2 case: define the invariant windows/trend statistics, a nonzero B2/zero-damping fixture, explicit JAX/scan `rtol`/`atol` pairs and shapes, gate inputs, and gradient sample counts (`PLAN.md:372-382`).
2. Complete Phase 4's LBFGS and zero-variance settings, register an exact base/counterfactual pair constructor and sham equality predicate, and fix the channel flattening order (`PLAN.md:422-426`).
3. Specify run-ID serialization completely: raw versus hex nested hashes, Git-SHA encoding, exact tracked-diff bytes, and corresponding `env.json` fields; add one full dirty-state known-answer test (`PLAN.md:151`, `PLAN.md:343`).
4. Make review containment restore clean tracked files and remove unauthorized new files, including noncanonical `docs/reviews` sidecars, on failure and post-run drift exits (`PLAN.md:107`; `tools/run_codex_review.sh:161-175`, `tools/run_codex_review.sh:321-340`, `tools/run_codex_review.sh:386-429`).
5. Add first-answer successes and exact p-values to the fixed result record and make the strong H4 consequence trigger per strong seed, or explicitly scope the scientific claim to mean behavior (`PLAN.md:57`, `PLAN.md:333`, `PLAN.md:427`, `PLAN.md:506`).
6. In the Phase 6 freeze amendment, extend Appendix A, enumerate the scaled proof-test subset, and retain a committed scale-evidence report outside ignored run directories (`PLAN.md:440-452`, `PLAN.md:462-480`; `.gitignore:220-225`).
7. Add a v1.12 amendment-log entry, update README's H4 mapping, and assign the trained-checkpoint gradient rerun to G3 (`PLAN.md:7-9`, `PLAN.md:197`, `PLAN.md:378`, `PLAN.md:494-506`; `README.md:38`).
8. Bind each prior High/Critical title to its original number in the Findings section and reconcile the initial plan loop with the review-before-amendment-commit rule in governing prose (`PLAN.md:102`, `PLAN.md:105`, `PLAN.md:116`; `tools/review_round_tracking.py:116-142`).
9. Move rejected Kimi candidates outside `docs/reviews` and exclude them from review context and metrics (`PLAN.md:107`, `PLAN.md:186-187`; `tools/run_kimi_review.py:40-46`, `tools/run_kimi_review.py:183-188`; `tools/agent_metrics.py:88-104`).
10. Pin Task B `task_k=8` in validation, add every fixture stream to the canonical inventory, define or remove the inert training RNG, register B1 initialization, correct the cell-2 input sentence, and stratify Task B by reachability (`PLAN.md:147-148`, `PLAN.md:228-246`, `PLAN.md:272-280`, `PLAN.md:313-316`, `PLAN.md:465-480`).

## Evidence consulted

- `PLAN.md:1-554`, read in full, including Section 2b, the complete ledger, Sections 3-6, Phases 0-7, and Appendices A-G.
- `README.md:1-66`, read in full and checked against H4, governed artifacts, and stage/status language.
- The prior `docs/reviews/plan/spec.md` Round 1-8 history and every stable finding identity; `docs/reviews/plan/tiebreaks.md:1-49` was checked, including the human adjudication, which applies only to process findings 1, 2, 4, and 9.
- Commit `e7034af` inspected with read-only `git show`/diff/log; its dtype, optimizer, plan-acceptance, provenance, and ledger claims were checked against operative text rather than accepted from the summary. Commit `9b2eb7d` remained the last tooling change.
- `.gitignore:1-230`, `tools/check_acceptance.sh:1-16`, `tools/check_review_scores.py:1-111`, `tools/review_round_tracking.py:1-174`, `tools/run_codex_review.sh:1-432`, `tools/run_kimi_review.py:1-198`, `tools/agent_metrics.py:1-131`, and `tools/codex-prompts/_common-header.md:1-53`, checked against Section 2b, acceptance, containment, history, context, and retention.
- Repository inventory from `rg --files`: no implementation, config, fixture, Makefile, result run, or replayable gate exists; three tracked `*-kimi.rejected.md` sibling reviews remain.
- Vocabulary/run arithmetic replay: PAD + 32 cues/keys + QRY + 16 operands/values + 14 distractors = 64; `P=32` exhausts the key range; gates are `4x4=16`; Phase 3 has 66 Task A plus 30 Task M runs = 96, within “roughly 90 to 100.”
- Receptive-field replay: toy maximal lag `4*(64-1)=252` and scaled lag `12*(256-1)=3060`; Task A lags 514/2050 and Phase 6 `N=6144` remain unreachable; Task B delays 251..256 cross the toy boundary.
- Parameter replay: base `3,180,800`; additions M1 `30,864`, M1b `30,992`, B2 `34,960`, B1 `4,096`; B0 `d_ff=1032` and all others `1024` yield a 0.960% spread.
- Numerical/discretization replay: the recurrence remains symplectic Euler with implicit damping and preserves the stated undamped modified invariant; the corrected damping envelope is attainable. The v1.12 global dtype split now agrees with Phase 2's registered fp64/fp32 closed-form cases.
- Read-only tooling audit: a Kimi-only phase fails acceptance; wrapper restoration still has no source for clean tracked mutations and exempts unauthorized `docs/reviews` additions; the run-ID outer byte serialization remains multiply interpretable; title validation remains content-global rather than number-bound.
- Read-only `git status --short` was clean before this canonical edit; no outside-path drift was observed.
- No implementation gate could be replayed because the repository remains at the specification-only stage.
