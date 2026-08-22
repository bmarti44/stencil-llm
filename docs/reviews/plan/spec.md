# Spec Review — plan

**Score:** 74 / 100
**Verdict:** FAIL (<75)
**Reviewer model:** codex/gpt-5.6-sol
**Date:** 2026-08-22

## Round log

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

1. **Critical (resolved 2026-08-22: verified constructive column balance, uniform independent sampling, and cell-specific nulls) — Task A's cue-blind ceiling was invalid.** Task A starts from the cyclic square, applies seeded row/column/symbol permutations, and makes every output column distinct for `k <= 16` or twice balanced for `k = 32` (`PLAN.md:297`). It separately states that cue and operand are uniform and mutually independent (`PLAN.md:299`). The resulting `1/k` and `1/16` Bayes optima and Appendix C's 14.5%/8.25% gates are arithmetically correct (`PLAN.md:298`, `PLAN.md:483`).

2. **Critical (resolved 2026-08-22: explicit next-token indexing prevents answer leakage) — Answer-token alignment was unspecified.** The causal contract says “`logits[p]` predicts `tokens[p+1]`,” defines `loss_mask[p]` on the preceding answer-decision position, measures cue distance to that position, and supplies a correct miniature (`PLAN.md:289`). A conforming causal model cannot read an answer embedding when predicting that answer.

3. **Critical (resolved 2026-08-22: the corrected determinant-consistent envelope passes an independent replay) — The amended damping fixture had the wrong exponent.** Phase 2 requires `[0.8,1.2] x (1+G)^(-10000)` and identifies it as approximately 0.29 (`PLAN.md:364`). With `G=softplus(-9)=0.000123402...`, the target is `0.2911415`; the registered 64-mode, seed-0 fp64 recurrence replay gives `H_10000/H_0=0.29358`, inside `[0.2329,0.3494]`.

4. **High (resolved 2026-08-22: verified complete two-cell shapes and dataflow) — Controller dimensions and stacked-cell plumbing were undefined.** Section 5.2 fixes `B_1 in R^{64x256}`, zero `y_1,z_1`, the two `64x64` GLU matrices, `B_2 in R^{64x64}`, zero `y_2,z_2`, and `c_t=[y_2;z_2] in R^128`, with no extra readout (`PLAN.md:238`). Section 5.3 agrees.

5. **High (resolved 2026-08-22: only M1/M1b are claimed as a controlled dissipation comparison) — H2 falsely treated B2 as differing only in energy handling.** H2 says M1/M1b differ in damping while B2 differs in recurrence order, depth, and nonlinearity (`PLAN.md:52`). The variant prose repeats that B2 is a deliberately different baseline (`PLAN.md:277`).

6. **High (resolved 2026-08-22: B0 assembly and a deterministic auditable matching algorithm are registered) — Parameter matching was self-authored and B0's assembly contradicted its count.** B0 has no controller or unused oscillator parameters (`PLAN.md:277`), and Section 5.5 locks M1/M1b to `d_ff=1024` while choosing the smallest multiple-of-eight width within 1% of the maximum (`PLAN.md:281`). Recomputed additions are M1 `30,864`, M1b `30,992`, B2 `34,960`, and B1 `4,096`; widths are `1032` for B0 and `1024` otherwise, with 0.960% max-to-min spread.

7. **High — The config/API fix introduces an impossible non-oscillatory damping value and leaves the generator seed duplicated.** Section 3 maps experiment seed `s` to the four config seeds (`PLAN.md:139-140`), but Section 6 still declares every generator a function of “`(config, seed)`” while `seed_data`/`seed_rules` already live in the config and define training/eval streams (`PLAN.md:287`, `PLAN.md:325`, `PLAN.md:449-460`). No precedence or disagreement rule is given. More directly, Appendix A now requires `damping_learnable` to equal `(variant == m1b)`—therefore `False` for B0/B1/B2—and in the same sentence requires it to be `null` for every non-oscillatory variant (`PLAN.md:464`). A strict loader cannot satisfy both `False` and `null`; v1.8 fixed the unused period/copy issue but replaced it with a literal type contradiction.

8. **High (resolved 2026-08-22: Task B and Task M sampling/diagnostic mechanics are materially complete) — Task B and Task M generators were underspecified.** Task B fixes `k=8`, nonrepeating consecutive cues, uniform operands, delays, active-rule semantics, collision counting, and no-error handling (`PLAN.md:305-308`). Task M fixes 32 unique keys, replacement-sampled 16-way values, eight unique queries, ordering, placements, and its exact 1/16 null (`PLAN.md:310-321`). Appendix B supplies 32 cue/key, 16 operand/value, and 14 distractor tokens (`PLAN.md:466-473`).

9. **High — Phase 0/1 exact fixtures still require their author to select missing behavior and then certify it.** Named-stream derivation is fixed (`PLAN.md:139`), but `test_task_a_exact_output` gives neither the sequence count nor literal bytes, and “draw a ... permutation” never names the exact permutation calls/draw order its promised hand execution must replay (`PLAN.md:297`, `PLAN.md:347`). `test_task_m_bindings` still requests an “exact miniature fixture at P=4” without a seed, token bytes, metadata, or an independent fixture-before-generator protocol (`PLAN.md:354`). The distractor test says to “resample the rule assignment” even though the rule table is fixed and does not identify the held distractor vector/statistic; the Latin test leaves “each dataset seed tested” to its author (`PLAN.md:300`, `PLAN.md:350-351`). Phase 0 still specifies only part of `configs/test_tiny.json` and never defines the copy grammar, targets, optimizer values, or remaining strict-schema fields (`PLAN.md:334`, `PLAN.md:340`, `PLAN.md:446-464`). These mandatory G0/G1 oracles remain self-authored.

10. **High — The JAX oracle parameters remain self-selected despite v1.8's amendment-log claim.** Phase 2 pins repository SHAs, `jax==0.4.35`, `m=64`, `A/G`, input distribution, seeds, length, and fp64 (`PLAN.md:367`), but still omits the input feature dimension, exact `B`, initial states, official-code parameter mapping, expected hashes, Python, and NumPy. It says inputs use the “registered stream scheme,” yet the registered names contain no JAX/input stream (`PLAN.md:139`, `PLAN.md:367`). Recording shapes and versions in NPZ metadata lets the generator choose them after implementation. Appendix G still only says “installs `jax[cpu]`” and “fixed random inputs” (`PLAN.md:534`). The normative test text did not implement the amendment log's claim that fixture parameters are fully drawn from registered streams, so materially different oracle files remain compliant.

11. **Critical (resolved 2026-08-22: the true boundary is registered and independently verified) — The positive reachability test contradicted the fixed mask and made G2 impossible.** The mask is `0 <= t-s <= w-1`, and `receptive_field()` returns `L*(w-1)` (`PLAN.md:63`). The toy value is `4*63=252` (`PLAN.md:212`), and test 8 puts the positive control exactly there (`PLAN.md:371`). Unreachable Task A distances 514 and 2050 remain beyond it (`PLAN.md:301`).

12. **High (resolved 2026-08-22: Task B explicitly shares `seed_rules` across train and evaluation) — Task B could resample its rule table at evaluation.** Task B builds rules from `seed_rules` and calls them shared train/eval (`PLAN.md:305`); the eval contract offsets only `seed_data` (`PLAN.md:325`).

13. **High — Phase 4's pass/fail datasets and optimizer remain non-unique; the claimed v1.8 single-pass pin is absent from the phase text.** The probe still omits classifier bias/init, zero-variance handling, and LBFGS `max_eval`, `tolerance_change`, and `line_search_fn`; PyTorch itself is unpinned (`PLAN.md:158`, `PLAN.md:408`). “Checkpoint's own eval stream” does not state the offset after G3's 10,000 examples or allocate distinct slices to probe train/test, patch, and shuffle (`PLAN.md:325`, `PLAN.md:408-410`). Tests normally recreate generators, so their listed order does not establish the amendment log's claimed shared single pass. The sham predicate still does not choose bitwise logits, toleranced logits, or argmax equality, and the `(layer,head)` flattening order is absent (`PLAN.md:409-410`). Frozen G4 outcomes can change under choices the coder must make.

15. **Medium — Phase 6 is safely blocked but still has neither an executable config nor retained gate evidence.** The freeze rule calls it “a sized sketch, not yet a runnable spec” (`PLAN.md:426`). Appendix A covers only Phases 0-5 and omits `b0_local_widened` (`PLAN.md:446-464`). “Phase 2 proof tests” does not identify which toy-specific JAX-shape, six-variant parameter, B1, and Task-A cases apply to the scaled pair (`PLAN.md:430`, `PLAN.md:436`). Raw run evidence is gitignored, while the retained-report list names no Phase 6 artifact (`PLAN.md:185-186`; `.gitignore:220-225`). The future amendment is a valid launch block, but PLAN.md is not yet a complete Phases 0-6 specification.

16. **Medium (resolved 2026-08-22: TDD is scoped to code-bearing phases) — The universal TDD rule disagreed with the run/artifact phases.** Rule 1 applies test-first to code-bearing work and gives run/artifact phases their protocol/review path (`PLAN.md:75`). The Makefile contract has gates 0-4 and 6 but no gate 5 (`PLAN.md:156-157`).

17. **High — G0 now names the right formula, but run identity still omits untracked code and `--force` still contradicts its guard.** Section 3 hashes `git diff HEAD` and claims a dirty worktree “can never collide” with clean evidence (`PLAN.md:143`); `git diff HEAD` excludes untracked files, so an untracked-only dirty tree gets the clean ID. The same paragraph refuses to delete an existing directory from a different git state, while Phase 0 still says `--force` unconditionally “deletes and recreates it” (`PLAN.md:143`, `PLAN.md:338`). The G0 formula itself is now aligned (`PLAN.md:335`), but byte encodings/delimiters and the contents of `env.json`'s “git state” remain unspecified. A dirty run can still collide with or replace distinct evidence under a compliant reading.

18. **Medium — Review-history, resume prompting, identity grammar, and amendment sequencing still disagree.** PLAN now requires dated annotations for prior-content edits (`PLAN.md:99`), but the common header still says prior rounds are preserved verbatim while the wrapper allows updates (`tools/codex-prompts/_common-header.md:24`, `tools/run_codex_review.sh:214-220`). `RESUME_NOTE` still checks `SID` before the session file is read, so resumed runs never receive the promised note (`tools/run_codex_review.sh:175-182`, `tools/run_codex_review.sh:237-258`). Reviewer identity is hyphen-form in the template and slash-form in wrapper context (`tools/codex-prompts/_common-header.md:14`; `tools/run_codex_review.sh:199`). Finally, the unqualified rule says amendments are accepted before commit (`PLAN.md:113`), but the ledger records committed v1.8 under an “initial loop” exception that exists only in that ledger interpretation, not the rule (`PLAN.md:125`).

22. **High (resolved 2026-08-22: the base transformer is sufficiently pinned for implementation and counting) — The base transformer was not specified precisely enough to reproduce.** Section 5.1 fixes GELU, pre-LN/final LayerNorm, epsilon, biases, tying, RoPE, dropout, and seeded initialization (`PLAN.md:197-214`). Gate initialization is literal (`PLAN.md:257-264`).

23. **Medium (resolved 2026-08-22: every control-output definition uses the full final-cell state) — Section 5.3 contradicted the fixed control-output shape.** Sections 5.2 and 5.3 both define `c_t=[y_2;z_2] in R^128` (`PLAN.md:238`, `PLAN.md:257-264`).

24. **High — Qualified states may now reach Phase 6, but composition conflicts with the status enum, Appendix C, and the stability branch.** Rule 5 restricts README statuses to four non-red G3 spellings and has no composite names (`PLAN.md:79`), while Phase 3 creates arbitrary unions such as `green-with-M1b-primary+efficiency-miss` without a complete suffix/order grammar (`PLAN.md:396-402`; `README.md:47-58`). The composition rule says G3.4 uses M1b when M1b is primary, but Appendix C still freezes the metric as “B0-full minus M1” (`PLAN.md:401`, `PLAN.md:487`). It also says an unresolved stability violation is red, while Appendix D.2b ends with the undefined alternative “kill or downgrade per the affected clause” (`PLAN.md:401`, `PLAN.md:500`). Phase 6 now correctly admits every registered green state (`PLAN.md:424`), but gate adjudication and status recording remain contradictory.

25. **High (resolved 2026-08-22: every registered G3/G4 row names its aggregation) — G3 and G4 thresholds omitted seed aggregation.** Appendix C gives an aggregation for every row (`PLAN.md:480-492`), and Phase 4 requires all three checkpoints to clear each bar (`PLAN.md:406`).

26. **High (resolved 2026-08-22: trained stability is a mandatory evidence condition through Phase 6) — Learned oscillator stability was checked in prose but not gated.** `test_stability_bound` covers G3/G4/G6 checkpoints (`PLAN.md:365`, `PLAN.md:482`), Phase 3 makes it a non-red precondition (`PLAN.md:396`), and v1.8 now requires every checkpoint entering the Phase 5 tradeoff document to pass as well (`PLAN.md:418`). The narrower ambiguity in the new failure branch is finding 24.

27. **High (resolved 2026-08-22: claim qualification now follows declared statistical detection, not the practical margin) — H4 bands permitted routing without correcting the strict-separation claim.** H4 and Appendix C now require any declared detection, including below 8.25%, to produce quantified leakage and at least partial-separation wording; 8.25 only grades magnitude and 50 triggers full withdrawal (`PLAN.md:54`, `PLAN.md:490`). The replacement test's invalid trial definition is a separate regression in finding 37.

28. **Low — A sibling canonical review remains dirty outside this review's write scope.** Read-only `git status --short` reports `M docs/reviews/plan/science.md`; its current Round 5 block begins at `docs/reviews/plan/science.md:10`. This review did not alter or restore it, per the wrapper policy.

29. **Medium (resolved 2026-08-22: the treatment delta is counted across both cells) — The parameter paragraph miscounted the M1/M1b difference.** Section 5.5 calls it the “128-parameter `g_raw` difference — two cells x 64” (`PLAN.md:281`), matching `30,992 - 30,864`.

30. **High — The closed-form cases improved, but several mandatory Phase 2 proofs still select their own inputs or pass vacuously.** Test 1 now fixes periods, forcing, `G`, horizon, and tolerance, but not the initial state and its zero-forcing arm can still be the all-zero trajectory (`PLAN.md:363`). The invariant test does not define the window size/trend statistic/tolerance; B2 inherits “the same windowed criterion” without an exact state/energy fixture (`PLAN.md:364`). `test_damping_zero_matches_m1_bitwise` still names no nonzero input/state (`PLAN.md:366`). Scan comparison omits seed/shape/dtype, gate identity omits tokens/shape, and the gradient tests give no sample count/fixture IDs (`PLAN.md:368-371`). Mandatory G2 proof strength still depends on easy cases chosen by its implementer.

31. **Medium (resolved 2026-08-22: the H2 heuristic gives its literal estimator) — H2's uncertainty condition was not an exact adjudication algorithm.** H2 defines `sqrt((var(M1b_seeds)+var(M1_seeds))/2)` with sample variances over three seeds and applies it only to M1b-minus-M1 (`PLAN.md:52`).

32. **Medium (resolved 2026-08-22: Phase 6 distinguishes exact lag from the conservative bound) — Phase 6 mislabeled `L*w` as the receptive field.** It gives exact field `12*255=3060`, calls 3072 conservative, and keeps `N=6144` beyond both (`PLAN.md:428`), consistent with Section 1 (`PLAN.md:63`).

33. **Medium (resolved 2026-08-22: the stale-error plot uses a history-conditioned comparator) — Task B had no valid null for its stale-rule diagnostic.** The plan requires the exact per-sequence probability for a uniform-random wrong answer, computed from rule tables/metadata (`PLAN.md:308`).

34. **Low — Appendix C's provenance regressed immediately after being corrected.** It still says thresholds were “last amended v1.7” and points only to v1.4-v1.7 (`PLAN.md:478`), but v1.8 changed H2's competence floor and replaced the H4 decision rule (`PLAN.md:9`, `PLAN.md:52`, `PLAN.md:490`). Phase 0 has not started, so preregistration timing is still honest; the stated threshold history is not.

35. **High — Codex topic routing is fixed, but mandatory Kimi Phase 5/7 reviews still cannot start.** The Codex wrapper now falls back to `review-phase.md` for `tradeoff` and `report` (`tools/run_codex_review.sh:117-124`). The Kimi wrapper still constructs only `review-${topic}.md` and exits if absent (`tools/run_kimi_review.py:118-124`); neither file exists. Section 2b requires a Kimi cross-review per phase and specifically registers those topics (`PLAN.md:102-103`, `PLAN.md:107`), so Phase 5/7 cadence is still unrunnable as specified.

36. **High (resolved 2026-08-22: model execution and test-side reference precision are now separated) — The global dtype contract made Phase 2 proof tests mutually inconsistent.** Section 3 now requires model execution in fp32 but expressly allows fp64 closed-form references and invariant accumulation (`PLAN.md:142`). Phase 2's matrix-power/JAX trajectories and invariant accumulation are therefore fp64 references compared with fp32 model execution (`PLAN.md:363-367`), and the scaled model proofs remain fp32 (`PLAN.md:430`). The exact scaled subset is still deferred under finding 15, but there is no longer a global dtype contradiction.

37. **High — H4's new “binomial test” has no valid Bernoulli trial and cannot produce the registered p-value.** H4 specifies `n=10,000 sequences`, “sequence-mean accuracy as the unit,” and a one-sided binomial test against 6.25% (`PLAN.md:54`, `PLAN.md:490`). Each Task M sequence has eight answers, so its mean is fractional in `{0,1/8,...,1}`, not a Bernoulli success. Treating “any correct” as the trial would have null probability `1-(15/16)^8 ~= 40.33%`, not 6.25%; treating all 80,000 answers as binomial contradicts the stated sequence unit and ignores the within-sequence dependence the amendment sought to handle (`PLAN.md:316`, `PLAN.md:325`). No integer success statistic, tail rule, or clustered null distribution is registered, so the claim-qualification decision remains non-executable.

38. **Medium — The Kimi wrapper and committed repository violate the canonical-review-only policy by creating rejected siblings.** PLAN says reviewers write only their canonical file and uncontained drift is a hard failure (`PLAN.md:104`); the reviewer protocol likewise says never create sibling files (`tools/codex-prompts/_common-header.md:3`, `tools/codex-prompts/_common-header.md:50`). `run_kimi_review.py` deliberately writes `<topic>-kimi.rejected.md` on validation failure (`tools/run_kimi_review.py:11-12`, `tools/run_kimi_review.py:177-182`), and both `docs/reviews/plan/spec-kimi.rejected.md` and `science-kimi.rejected.md` are now tracked although the repo layout only names canonical and `-kimi` reviews (`PLAN.md:179`).

39. **Medium — README was not updated for the material v1.8 H4 gate change.** PLAN requires material hypothesis/task/gate changes to update README in the same commit (`PLAN.md:189`). H4 now uses statistical detection independent of magnitude (`PLAN.md:54`, `PLAN.md:490`), but README still says “pre-registered bands ... measure any content routing” and implies low score means no evidence (`README.md:38`); commit `e028c90` did not modify README. Below-8.25 detection is possible under PLAN but not explained by the governed mapping.

## Recommendations

1. Remove the generator's extra `seed` argument or define its exact relationship to `seed_data`; make `damping_learnable` either boolean for every variant or nullable for non-oscillatory variants, not both (`PLAN.md:287`, `PLAN.md:325`, `PLAN.md:449-464`).
2. Register literal Task A, Task M, and copy fixtures—full configs, exact tokens, masks, metadata, permutation operations/draw order, and sample counts—before their implementations; make the distractor and Latin tests name their fixtures and seeds (`PLAN.md:297-300`, `PLAN.md:334-354`).
3. Give every Phase 2 proof a fixed nontrivial input: exact `A/G/B`, initial state, forcing, seed, shape, dtype, and expected statistic; define the invariant trend estimator and keep zero-damping/gate-bypass tests from passing on all-zero cases (`PLAN.md:363-371`).
4. Freeze the JAX manifest before generation: Python/NumPy/JAX/JAXLIB versions, input feature dimension, exact `B` and initial states, official parameter mapping, named stream, input hashes, and expected trajectory hashes; make Appendix G repeat or link that normative manifest (`PLAN.md:139`, `PLAN.md:367`, `PLAN.md:530-534`).
5. Define the probe bias, initialization, zero-variance policy, and all LBFGS settings; assign explicit nonoverlapping eval-stream offsets to the Phase 4 datasets, define sham equality, and freeze `(layer,head)` order (`PLAN.md:325`, `PLAN.md:408-410`).
6. Hash untracked-file paths and contents in `run_id`, specify concatenation encodings/delimiters and the recorded git-state fields, and qualify Phase 0's `--force` rule with the Section 3 different-state refusal (`PLAN.md:143`, `PLAN.md:335`, `PLAN.md:338`).
7. Replace H4's invalid fractional-unit binomial test with a fully registered sequence-cluster-aware test or an exact integer statistic and null distribution; state multiplicity handling for the any-seed decision (`PLAN.md:54`, `PLAN.md:316-325`, `PLAN.md:490`).
8. Define a canonical compositional G3 status grammar in Rule 5 and README, make Appendix C's G3.4 comparator conditional on the primary model, and replace Appendix D.2b's “kill or downgrade” with the single registered stability outcome (`PLAN.md:79`, `PLAN.md:401`, `PLAN.md:487`, `PLAN.md:500`; `README.md:47-58`).
9. Give the Kimi wrapper the same `tradeoff`/`report` fallback as Codex, and keep rejected candidates outside `docs/reviews/` or in a non-review diagnostic channel rather than creating sibling review files (`PLAN.md:102-107`, `PLAN.md:179`; `tools/run_codex_review.sh:117-124`; `tools/run_kimi_review.py:118-124`, `tools/run_kimi_review.py:177-182`).
10. Align the common header with the annotated-history validator, initialize/read `SID` before constructing the prompt, standardize reviewer-ID grammar, and either codify or remove the ledger-only pre-commit initial-loop exception (`PLAN.md:99`, `PLAN.md:113`, `PLAN.md:125`; `tools/codex-prompts/_common-header.md:14-24`; `tools/run_codex_review.sh:175-182`, `tools/run_codex_review.sh:237-258`).
11. In the Phase 6 freeze amendment, extend Appendix A with the widened variant/full run fields, enumerate the exact scaled proof-test subset, and require a committed scale summary outside ignored run directories (`PLAN.md:426-436`, `PLAN.md:446-464`; `.gitignore:220-225`).
12. Update Appendix C's provenance to v1.8 and revise README's H4 mapping so statistical detection below the practical band still changes the separation claim, as PLAN requires for material gate amendments (`PLAN.md:54`, `PLAN.md:189`, `PLAN.md:478`, `PLAN.md:490`; `README.md:38`).

## Evidence consulted

- `PLAN.md:1-538`, read in full, including Section 2b, the complete Work log/ledger, Sections 3-6, Phases 0-7, and Appendices A-G.
- `README.md:1-66`, read in full and cross-checked against governed claims, artifacts, gate-state vocabulary, and the H4 mapping.
- Existing `docs/reviews/plan/spec.md` and the wrapper-supplied Round 4 content, including all four prior round blocks and every stable High/Critical finding identifier; prior round log blocks were preserved verbatim.
- Commit `e028c90` inspected with read-only `git show` and `git show --stat`; the v1.8 edits were compared against each Round 4 finding rather than accepted from the amendment log.
- `.gitignore:220-230`, `tools/check_review_scores.py:1-111`, `tools/review_round_tracking.py:1-158`, `tools/run_codex_review.sh:1-412`, `tools/run_kimi_review.py:1-192`, and `tools/codex-prompts/_common-header.md:1-53`, checked against Section 2b, result retention, topic dispatch, canonical output, history, and session continuity.
- Repository inventory from `rg --files`; no `src/`, `tests/`, `scripts/`, `configs/`, `results/`, `Makefile`, `pyproject.toml`, or replayable implementation gate exists, while two tracked `*-kimi.rejected.md` sibling reviews do exist.
- Vocabulary/run arithmetic replay: 32 cue/key tokens, 16 operand/value tokens, and 14 distractors plus PAD/QRY sum to 64; `P=32` exhausts the key range; the controller has `4x4=16` gates; Phase 3 is 66 Task A plus 30 Task M runs, exactly 96 and within “roughly 90 to 100.”
- Receptive-field replay: the mask gives toy maximal lag `4*(64-1)=252` and scaled lag `12*(256-1)=3060`; Task A distances 514/2050 and Phase 6 `N=6144` remain unreachable.
- Parameter replay under the fixed no-bias architecture: base at `d_ff=1024` is `3,180,800`; additions are M1 `30,864`, M1b `30,992`, B2 `34,960`, and B1 `4,096`; matching yields B0 `d_ff=1032`, all others `1024`, with a 0.960% max-to-min spread.
- Algebraic/numerical replay: substitution verifies `H_d=z^2+A*y^2-dt*A*y*z`; the damped map determinant is `(1+G)^(-1)`; the corrected M1b target remains attainable. The written recurrence remains symplectic Euler for the conservative part with damping implicit in `z_{k+1}`, so its IMEX/symplectic description is internally correct.
- H4 replay: Task M has eight scored answers per sequence, so its sequence mean has nine possible fractional values rather than a Bernoulli support; the null probability of at least one correct answer is `1-(15/16)^8 ~= 0.40328`, not 0.0625. No registered statistic makes the stated sequence-unit binomial test valid.
- Read-only `git status --short` showed `docs/reviews/plan/science.md` modified outside this review's path before this canonical file was written; its Round 5 starts at line 10. This review did not alter or restore it.
- No gate could be replayed because the repository remains at the specification-only stage.
