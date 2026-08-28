# Spec Review — plan

**Score:** 92 / 100
**Verdict:** PASS (≥90)
**Reviewer model:** codex/gpt-5.6-sol
**Date:** 2026-08-22

## Round log

### Round 10 — 2026-08-22 (codex/gpt-5.6-sol)
- Score: 92 / 100 (delta vs prior round: +3)
- Addressed since prior round:
  - Commit `505ca63` fully registers the formerly open G2 and G4 cases: Phase 2 now fixes the invariant/decay windows, nonzero damping-equivalence fixture, JAX/scan tolerances and shapes, gate batch, and gradient sample set; Phase 4 now fixes the remaining LBFGS, standardization, counterfactual-pair, sham, and channel-order semantics (`PLAN.md:375-382`, `PLAN.md:427-429`).
  - The same commit completes the run-ID byte serialization and repairs both wrapper-restoration paths for clean tracked files and unauthorized new files (`PLAN.md:154`, `PLAN.md:346`; `tools/run_codex_review.sh:321-342`, `tools/run_codex_review.sh:395-431`).
  - The v1.12/v1.13 amendment entries restore Appendix C's declared provenance chain, and rejected Kimi candidates are now excluded from later review context and retrospective metrics (`PLAN.md:8-10`, `PLAN.md:497`; `tools/run_kimi_review.py:41-46`, `tools/run_kimi_review.py:58-64`; `tools/agent_metrics.py:88-90`).
- New or remaining:
  - No High or Critical finding remains open; the plan clears the 90-point acceptance threshold on internal consistency and testability.
  - Phase 6 remains deliberately frozen as a non-runnable sketch, while H4 retention/aggregation, the review-before-commit exception, rejected Kimi sidecar creation, title binding, schema/RNG details, B1 initialization, and smaller task/reporting issues remain.
  - v1.13 exposes several minor reproducibility/editorial gaps: PyTorch is not version-pinned, one Phase 2 cell scope remains shorthand, stale wrapper comments contradict the repaired restoration code, and README still says only green transitions update status although PLAN now requires every state change.

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

13. **High (resolved 2026-08-22: v1.13 fixes every threshold-relevant Phase 4 semantic) — Phase 4 now fixes stream order, but its pass/fail implementations remain non-unique.** The probe now fixes `max_eval=625`, `tolerance_change=1e-9`, zero-variance handling, and the finite-sample class policy; patching constructs an exact cue-only counterfactual and defines sham equality as per-answer-position argmax equality; shuffling fixes `index=layer*n_heads+head` with ascending axes (`PLAN.md:427-429`). These rules leave one G4 adjudication for a fixed implementation. The repository-wide PyTorch-version gap is retained separately as finding 52.

15. **Medium — Phase 6 is safely blocked but still has neither an executable config nor retained gate evidence.** (updated 2026-08-22: current v1.13 citations.) Phase 6 remains an explicit “sized sketch” pending amendment; Appendix A covers only Phases 0-5 and omits the widened variant, G6.3 does not enumerate which toy-only proofs port, and ignored raw runs have no named committed scale report (`PLAN.md:441-457`, `PLAN.md:465-483`; `.gitignore:220-225`).

16. **Medium (resolved 2026-08-22: TDD is scoped to code-bearing phases) — The universal TDD rule disagreed with the run/artifact phases.** (updated 2026-08-22: current v1.12 citations.) Rule 1 scopes test-first work to code-bearing phases, and the Makefile contract consistently has gates 0-4 and 6 but no gate 5 (`PLAN.md:78`, `PLAN.md:164-166`).

17. **High (resolved 2026-08-22: v1.13 registers the complete outer and inner byte serialization) — `--force` is aligned, but run identity still excludes untracked dirty state and leaves its byte contract undefined.** Section 3 now requires lowercase ASCII hex for every digest, a 40-character lowercase ASCII Git SHA, literal `git diff HEAD` bytes for the tracked inner hash, the already framed untracked record, a fixed four-part outer order with no separators, and the corresponding inner digests in `env.json` (`PLAN.md:154`). Phase 0 delegates to that sole formula (`PLAN.md:346`), so the previous raw-versus-hex ambiguity is gone.

18. **Medium — Review-history, resume prompting, identity grammar, and amendment sequencing still disagree.** (updated 2026-08-22: v1.13 leaves only amendment sequencing.) PLAN, the common header, and the wrapper agree on annotated history, slash-form IDs, and pre-prompt SID loading (`PLAN.md:104-105`; `tools/codex-prompts/_common-header.md:14-24`; `tools/run_codex_review.sh:180-214`). The governing rule still says an amendment review “must be accepted BEFORE the amendment commit lands” (`PLAN.md:118`), while v1.13 was committed before this Round 10 review and the ledger explicitly “declined” that sequencing for the initial loop (`PLAN.md:130`). The older ledger interpretation says ongoing rounds themselves satisfy review and pre-commit sequencing starts only after acceptance (`PLAN.md:136`), but that exception never entered the governing rule.

22. **High (resolved 2026-08-22: the base transformer is sufficiently pinned for implementation and counting) — The base transformer was not specified precisely enough to reproduce.** (updated 2026-08-22: current v1.12 citations.) Section 5.1 fixes activation, norms, epsilon, biases, tying, RoPE, dropout, and seeded initialization (`PLAN.md:205-222`). B1's narrower initialization gap remains finding 42.

23. **Medium (resolved 2026-08-22: every control-output definition uses the full final-cell state) — Section 5.3 contradicted the fixed control-output shape.** (updated 2026-08-22: current v1.12 citations.) The tensor table and gate section both use `c_t=[y_2;z_2]` in `R^128` (`PLAN.md:246`, `PLAN.md:265-272`).

24. **High (resolved 2026-08-22: one explicit sole-authority procedure now determines every G3 outcome) — v1.9 adds an order but still leaves multiple contradictory G3 outcomes.** (updated 2026-08-22: v1.13 also aligns the subordinate Appendix D grammar.) Phase 3 explicitly supersedes prior phrasing, evaluates stability and necessity before selecting the primary, compares G3.4 to that primary, and emits one ordered-union state or red (`PLAN.md:411-421`). Appendix D now contributes the same named qualification tokens instead of standalone `green-with-*` states (`PLAN.md:519-527`).

25. **High (resolved 2026-08-22: every registered G3/G4 row names its aggregation) — G3 and G4 thresholds omitted seed aggregation.** (updated 2026-08-22: current v1.12 citations.) Appendix C specifies aggregation per row and Phase 4 requires all three checkpoints to pass (`PLAN.md:496-508`, `PLAN.md:422`, `PLAN.md:430`).

26. **High (resolved 2026-08-22: trained stability is a mandatory evidence condition through Phase 6) — Learned oscillator stability was checked but not gated.** (updated 2026-08-22: current v1.12 citations.) The reusable assertion and validity row cover G3/G4/G6, Phase 5 separately requires it, and the sole G3 authority makes unresolved failure red (`PLAN.md:373`, `PLAN.md:411`, `PLAN.md:434`, `PLAN.md:498`).

27. **High (resolved 2026-08-22: claim qualification follows statistical detection, not the practical margin) — H4 bands permitted routing without correcting the strict-separation claim.** (updated 2026-08-22: current v1.12 citations.) H4 and Appendix C require any per-seed detection to qualify the claim (`PLAN.md:57`, `PLAN.md:506`). Finding 40 tracks the evidence record and strong-band consequence.

28. **Low (resolved 2026-08-22: read-only status was clean before this canonical edit) — A sibling canonical review is dirty outside this review's write scope.** (updated 2026-08-22: Round 9 also began from a clean worktree.) No sibling or other outside-path drift was present before this canonical edit; this review wrote only its Round 9 block in `docs/reviews/plan/spec.md:10` and current findings/recommendations below it.

29. **Medium (resolved 2026-08-22: the treatment delta is counted across both cells) — The parameter paragraph miscounted the M1/M1b difference.** (updated 2026-08-22: current v1.12 citation.) Section 5.5 names the 128-parameter two-cell delta, matching 30,992 minus 30,864 (`PLAN.md:289`).

30. **High (resolved 2026-08-22: v1.13 instantiates every previously missing load-bearing case and predicate) — v1.9's generic non-vacuity rule does not instantiate the mandatory Phase 2 proofs or make their tolerances feasible.** Test 2 now fixes the oscillator and B2 initial states, horizons, windows, trend statistic, and bounds; test 3 fixes nonzero input/state streams and a nonzero-output precondition; tests 4-5 fix `rtol`/`atol`, seed, shape, and dtype; test 6 fixes the Task A batch; and tests 7-8 fix models, seeds, cells, sequence counts, positions, and gradient predicates (`PLAN.md:375-382`). Together with the per-case count and graph-connectivity rule (`PLAN.md:385`), mandatory G2 no longer depends on an author choosing an easy proof case. Finding 53 records the remaining non-blocking cell-scope shorthand in test 3.

31. **Medium (resolved 2026-08-22: the H2 heuristic gives its literal estimator) — H2's uncertainty condition was not exact.** (updated 2026-08-22: current v1.12 citation.) H2 defines the sample-variance estimator and confines it to M1b-minus-M1 (`PLAN.md:55`).

32. **Medium (resolved 2026-08-22: Phase 6 distinguishes exact lag from the conservative bound) — Phase 6 mislabeled `L*w` as the receptive field.** (updated 2026-08-22: current v1.12 citations.) Phase 6 gives exact lag 3060, labels 3072 conservative, and places `N=6144` beyond both, consistent with Section 1 (`PLAN.md:66`, `PLAN.md:444`).

33. **Medium (resolved 2026-08-22: the stale-error plot uses a history-conditioned comparator) — Task B had no valid stale-rule null.** (updated 2026-08-22: current v1.12 citation.) Task B registers the exact per-sequence history-conditioned comparator (`PLAN.md:316`).

34. **Medium (resolved 2026-08-22: v1.13 restores the complete amendment-log provenance chain) — Appendix C's provenance remains false through v1.9.** The log now includes both v1.12—explicitly identified as retroactive after the recorded protocol slip—and v1.13 (`PLAN.md:8-10`), while Appendix C continues to name that log as the sole authority (`PLAN.md:497`). Every current pre-Phase-0 threshold amendment is represented.

35. **High (resolved 2026-08-22: Kimi now uses the same generic topic fallback as Codex) — Mandatory Kimi Phase 5/7 reviews could not start.** (updated 2026-08-22: current v1.12 citations.) Kimi maps phase topics, tradeoff, and report to the generic rubric, matching Section 2b (`PLAN.md:105`, `PLAN.md:110`; `tools/run_kimi_review.py:122-130`).

36. **High (resolved 2026-08-22: v1.12 expressly permits the registered fp64 isolated-cell numerics run) — The global dtype contract made Phase 2 tests mutually inconsistent.** Section 3 now distinguishes model-level tests 6-8, which execute fp32, from cell-numerics tests 1-2, which may execute the isolated cell fp64 where registered and compare against fp32 (`PLAN.md:150`). Phase 2 test 1 is exactly such a registered fp64 case with a separate fp32 consistency bound (`PLAN.md:371`). Both requirements can now be satisfied.

37. **High (resolved 2026-08-22: the first answer of each independent sequence is a valid Bernoulli trial) — H4's binomial test had no valid trial.** (updated 2026-08-22: current v1.12 citations.) H4 selects the first answer from 10,000 independent sequences under `p=1/16`; its first exact `p<0.001` cutoff remains 702 successes (`PLAN.md:57`, `PLAN.md:326`, `PLAN.md:333`). Finding 40 covers retention and consequence defects.

38. **Medium — Kimi still violates the canonical-review-only policy and contaminates its own context/metrics with rejected siblings.** (updated 2026-08-22: v1.13 fixes contamination but retains prohibited sidecar creation.) Kimi now excludes `*.rejected.md` from prompt context and retrospective metrics (`tools/run_kimi_review.py:41-46`, `tools/run_kimi_review.py:58-64`; `tools/agent_metrics.py:88-90`). It still writes `<topic>-kimi.rejected.md` on validation failure (`tools/run_kimi_review.py:189-194`), and three such tracked siblings remain despite PLAN's canonical-only rule and named review layout (`PLAN.md:109`, `PLAN.md:188-189`).

39. **Medium — README was not updated for either material H4 amendment.** (updated 2026-08-22: v1.13 still leaves README unchanged.) PLAN requires same-commit mapping updates (`PLAN.md:200`). H4 uses a first-answer exact test for existence and mean accuracy only for magnitude (`PLAN.md:59`, `PLAN.md:509`), but README says the “bands ... measure any content routing” and associates low score with no evidence (`README.md:38`).

40. **Medium — H4's valid first-answer decision has no fixed evidence field, and its strong consequence can average away a seed-level falsification.** (updated 2026-08-22: current v1.13 citations.) The fixed JSON lacks first-answer successes and p-value, so the registered existence test cannot be reconstructed from the named record (`PLAN.md:336`). Appendix C detects per seed but bands the mean: seed accuracies `[60,5,5]` detect routing yet average 23.3 and evade the `>=50` capacity-probe/full-withdrawal consequence despite one strongly routing checkpoint (`PLAN.md:509`). Phase 4 inherits that trigger (`PLAN.md:430`).

41. **Low — The trained-checkpoint exact-zero-gradient regression has no gate owner.** (updated 2026-08-22: current v1.13 citations.) Phase 2 requires a post-Phase-3 rerun on trained B0-local/B1 checkpoints, but G3 and Appendix C own only performance and stability; all registered gates can be green if the rerun is skipped (`PLAN.md:381`, `PLAN.md:402-421`, `PLAN.md:501`).

42. **Medium — B1's initialization is not registered and need not start near the identity behavior used for recurrent variants.** (updated 2026-08-22: current v1.13 citations.) B1 is a bias-free sigmoid gate with no initialization in its variant row, whereas recurrent gates initialize near multiplier one (`PLAN.md:271-275`, `PLAN.md:283`). Appendix G delegates the missing initialization detail to an unpinned repository (`PLAN.md:554`).

43. **Low — Section 5.2's generic input sentence conflicts with its own fixed cell-2 input.** (updated 2026-08-22: current v1.13 citations.) The continuous system calls `u_t` a 256-dimensional token embedding “per cell,” while the tensor table makes cell 2 consume a 64-dimensional GLU output through `B_2:64x64` (`PLAN.md:227-249`).

44. **Low — Task B silently pools attention-reachable and recurrence-only delays.** (updated 2026-08-22: current v1.13 citations.) Delay is uniform 32..256 and cue-to-decision lag is delay+2; against exact field 252, delays 32..250 are attention-reachable and 251..256 recurrence-only, but reports pool only by switch count and stale error (`PLAN.md:223`, `PLAN.md:316-319`).

45. **Medium — The new residual-determinism rule is not a specification oracle.** (updated 2026-08-22: v1.13 closes the former G2/G4 examples but not the rule's structural gap.) “Lowest-index / lexicographic / first-in-stream” cannot order an unenumerated semantic alternative or continuous fixture (`PLAN.md:387`). It yields reproducibility only after a coder invents an option set, contrary to “Do not invent scope” (`PLAN.md:86`). The distractor test still leaves its held distractor vector unspecified, and the Latin test says “each dataset seed tested” without fixing the seed/config set (`PLAN.md:361-362`).

46. **High (resolved 2026-08-22: acceptance now fails when zero sol files were checked) — The new acceptance command can pass a phase with no sol review.** tools/check_acceptance.sh now increments an explicit sol-file count, excludes Kimi/rejected/tie-break files, and sets failure when the count is zero (tools/check_acceptance.sh:7-15). A Kimi-only directory can no longer exit successfully. The script still checks Kimi presence rather than topic freshness, but that narrower advisory-cadence issue does not preserve the High bypass.

47. **High (resolved 2026-08-22: both wrapper exits now restore tracked drift and delete unauthorized new files) — Review-wrapper failure containment still leaves unauthorized repository mutations in place.** The failure path restores preexisting dirty snapshots, checks out clean tracked mutations, and removes all other new files except the canonical review and machine-local logs/session state (`tools/run_codex_review.sh:321-342`). The post-run path applies the same tracked/untracked handling to every noncanonical path (`tools/run_codex_review.sh:395-431`). This mechanically enforces PLAN's canonical-only containment rule (`PLAN.md:109`). Stale comments around the repaired post-run branch are finding 50.

48. **Medium — The new finding-title validator does not bind a title to its finding number.** (updated 2026-08-22: unchanged in v1.13.) The validator extracts prior titles by number but searches each title's first 40 characters anywhere in the candidate, not in that numbered finding; swapping titles between findings or copying the phrase into Evidence passes (`tools/review_round_tracking.py:116-142`). The advertised number-bound identity/title immutability is therefore not mechanically enforced as stated (`PLAN.md:104-105`).

49. **Medium — The strict config and RNG inventories retain smaller contradictions after the API fix.** (updated 2026-08-22: unchanged in v1.13.) The global registered stream list omits `fixtures:init`, `fixtures:a`, `fixtures:b`, `fixtures:glu`, and `fixtures:input`, all required later (`PLAN.md:150`, `PLAN.md:374-379`). `seed_train` and stream `train` have no named stochastic consumer with dropout disabled; Task B fixes `k=8` but Appendix A accepts `task_k` as an unconstrained active field (`PLAN.md:150-151`, `PLAN.md:316`, `PLAN.md:468-483`). Equivalent runs can carry inert seeds and a strict loader can accept a Task-B config contradicting its task spec.

50. **Low — The repaired containment branch is documented as doing the opposite of its code.** The post-run comments say sibling reviews are never restored and unsnapshotted files are not touched (`tools/run_codex_review.sh:399-407`, `tools/run_codex_review.sh:422-427`), but the executable branch now restores every preexisting dirty file, checks out every newly dirty tracked file, and deletes every new untracked file outside the canonical/log/session allowlist (`tools/run_codex_review.sh:408-420`). The code correctly follows serialization and PLAN's containment contract; the stale comments are actively misleading for the next maintainer (`PLAN.md:109`).

51. **Low — README's status-update trigger contradicts the v1.13 gate-state rule.** PLAN now says “Every gate-state CHANGE — including to red or a qualified state” updates the README row (`PLAN.md:84`), while README still says only “Every green gate flips its row” (`README.md:58`). PLAN wins by its governed-artifact rule (`PLAN.md:200`), but the explanatory file misstates when red/in-progress transitions must be recorded.

52. **Medium — The PyTorch environment is not pinned even though G2/G4 outcomes depend on it.** The repository plan names a future `pyproject.toml` with `torch` but no version or lock-file requirement, and the stack says only “Plain PyTorch” (`PLAN.md:169`, `PLAN.md:193`). `env.json` records whichever Torch version happened to run (`PLAN.md:154`), while the JAX oracle uniquely pins its numerical dependency (`PLAN.md:378`). A Phase 0 coder must invent the Torch/NumPy versions, and the same clean config/Git state can receive the same run ID under a different installed Torch even though LBFGS and floating-point behavior can differ.

53. **Low — The zero-damping equivalence fixture still leaves its cell scope implicit.** Test 3 says to instantiate “the unified cell” and fixes a length-512 input stream, but the registered controller has two uses of that cell with different input maps—`B_1:64x256` and `B_2:64x64`—and the test does not say one or both, nor name the batch/input-feature shape (`PLAN.md:249`, `PLAN.md:377`). The shared implementation and nonzero precondition make the intended equivalence credible, so this no longer sustains the former High, but an exact coding agent still chooses the exercised shape.

## Recommendations

1. Add first-answer successes and exact p-values to the fixed result record and make the strong H4 consequence trigger per strong seed, or explicitly scope the scientific claim to mean behavior (`PLAN.md:59`, `PLAN.md:336`, `PLAN.md:430`, `PLAN.md:509`).
2. In the Phase 6 freeze amendment, extend Appendix A, enumerate the scaled proof-test subset, and retain a committed scale-evidence report outside ignored run directories (`PLAN.md:441-457`, `PLAN.md:465-483`; `.gitignore:220-225`).
3. Pin Torch and NumPy in the Phase 0 environment contract (prefer a committed `uv.lock`) and decide whether dependency identity belongs in `run_id`, rather than merely recording the installed Torch version after execution (`PLAN.md:154`, `PLAN.md:169`, `PLAN.md:193`, `PLAN.md:378`).
4. Reconcile the initial plan loop with the review-before-amendment-commit rule in governing prose, and bind each prior High/Critical title to its original finding number in the validator (`PLAN.md:105`, `PLAN.md:107`, `PLAN.md:118`, `PLAN.md:130-136`; `tools/review_round_tracking.py:116-142`).
5. Stop writing rejected Kimi candidates under `docs/reviews`; the new context/metric filters are correct but do not cure the canonical-output policy violation (`PLAN.md:109`, `PLAN.md:188-189`; `tools/run_kimi_review.py:58-64`, `tools/run_kimi_review.py:189-194`; `tools/agent_metrics.py:88-90`).
6. Update README's H4 mapping and status-transition sentence, and assign the trained-checkpoint gradient rerun to G3 (`PLAN.md:59`, `PLAN.md:84`, `PLAN.md:200`, `PLAN.md:336`, `PLAN.md:381`, `PLAN.md:509`; `README.md:38`, `README.md:58`).
7. Pin Task B `task_k=8` in validation, add every fixture stream to the canonical inventory, and define or remove the inert training RNG (`PLAN.md:150-151`, `PLAN.md:316`, `PLAN.md:374-379`, `PLAN.md:468-483`).
8. Register B1 initialization, correct the cell-2 input sentence, state whether the zero-damping equivalence test covers one or both controller cells, and stratify Task B's secondary curves by attention reachability (`PLAN.md:223`, `PLAN.md:231-249`, `PLAN.md:272-283`, `PLAN.md:316-319`, `PLAN.md:377`, `PLAN.md:554`).
9. Replace the obsolete containment comments with the actual serialized-restoration policy (`PLAN.md:109`; `tools/run_codex_review.sh:399-427`).
10. Register the held distractor fixture and exact Latin-property seed/config set instead of relying on the residual-default rule to order options the spec never enumerates (`PLAN.md:86`, `PLAN.md:361-362`, `PLAN.md:385-387`).

## Evidence consulted

- `PLAN.md:1-557`, read in full, including Section 2b, the complete amendment log and ledger, Sections 3-6, Phases 0-7, and Appendices A-G.
- `README.md:1-66`, read in full and checked against H4, governed artifacts, and stage/status language.
- The prior `docs/reviews/plan/spec.md` Round 1-9 history and every stable finding identity; `docs/reviews/plan/tiebreaks.md:1-49` was rechecked to ensure v1.13 did not alter the earlier fixture/tie-break closure basis.
- Commit `505ca63` inspected with read-only `git show`, `git diff e7034af..505ca63`, and `git log`; each v1.13 spec/tooling claim was checked against operative text and control flow rather than accepted from its amendment summary.
- `.gitignore:1-230`, `tools/check_acceptance.sh:1-16`, `tools/check_review_scores.py:1-111`, `tools/review_round_tracking.py:1-174`, `tools/run_codex_review.sh:1-438`, `tools/run_kimi_review.py:1-204`, `tools/agent_metrics.py:1-132`, and `tools/codex-prompts/_common-header.md:1-53`, checked against Section 2b, acceptance, containment, history, context, and retention.
- Repository inventory from `rg --files`: no implementation, config, fixture, Makefile, result run, or replayable gate exists; three tracked `*-kimi.rejected.md` sibling reviews remain.
- Vocabulary/run arithmetic replay: PAD + 32 cues/keys + QRY + 16 operands/values + 14 distractors = 64; `P=32` exhausts the key range; gates are `4x4=16`; Phase 3 has 66 Task A plus 30 Task M runs = 96, within “roughly 90 to 100.”
- Receptive-field replay: toy maximal lag `4*(64-1)=252` and scaled lag `12*(256-1)=3060`; Task A lags 514/2050 and Phase 6 `N=6144` remain unreachable; Task B delays 251..256 cross the toy boundary.
- Parameter replay: base `3,180,800`; additions M1 `30,864`, M1b `30,992`, B2 `34,960`, B1 `4,096`; B0 `d_ff=1032` and all others `1024` yield a 0.960% spread.
- Numerical/discretization replay: the recurrence remains symplectic Euler with implicit damping and preserves the stated undamped modified invariant; the corrected damping envelope is attainable. The v1.13 invariant/decay thresholds and fp64/fp32 split are arithmetically compatible, and every previously open mandatory proof now has a non-vacuous registered case.
- Phase 4 replay: the finite IID class claim is corrected, LBFGS's material arguments are fixed, donor/recipient sequences now differ only at the cue before the answer, sham equality is executable, and `layer*n_heads+head` enumerates all 16 channels exactly once.
- Run-identity replay: canonical JSON, 40-byte ASCII Git SHA, and two fixed 64-byte lowercase-hex inner digests give one unambiguous outer preimage; the framed untracked record distinguishes paths and content partitions.
- Read-only tooling audit: both failure and post-run paths now restore clean tracked changes and remove noncanonical new files; stale opposite comments remain. Rejected Kimi files are excluded from context/metrics but are still created; title validation remains content-global rather than number-bound.
- Read-only `git status --short` was clean before this canonical edit; no outside-path drift was observed.
- No implementation gate could be replayed because the repository remains at the specification-only stage.
