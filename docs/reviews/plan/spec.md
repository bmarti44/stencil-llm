# Spec Review — plan

**Score:** 82 / 100
**Verdict:** CONDITIONAL PASS (75–89)
**Reviewer model:** codex/gpt-5.6-sol
**Date:** 2026-08-22

## Round log

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

1. **Critical (resolved 2026-08-22: verified constructive column balance, uniform independent sampling, and cell-specific nulls) — Task A's cue-blind ceiling was invalid.** Task A starts from the cyclic square, applies seeded row/column/symbol permutations, and makes every output column distinct for `k <= 16` or twice balanced for `k = 32` (`PLAN.md:300`). Cue and operand are uniform and mutually independent (`PLAN.md:302`). The resulting `1/k` and `1/16` optima and Appendix C's 14.5%/8.25% bars are correct (`PLAN.md:301`, `PLAN.md:489`).

2. **Critical (resolved 2026-08-22: explicit next-token indexing prevents answer leakage) — Answer-token alignment was unspecified.** The causal contract says “`logits[p]` predicts `tokens[p+1]`,” places `loss_mask[p]` on the preceding decision position, and supplies a correct miniature (`PLAN.md:292`).

3. **Critical (resolved 2026-08-22: the determinant-consistent envelope passes an independent replay) — The amended damping fixture had the wrong exponent.** Phase 2 requires `[0.8,1.2] x (1+G)^(-10000)` and identifies it as approximately 0.29 (`PLAN.md:367`). With `G=softplus(-9)`, the target is `0.2911415`; the registered replay gives `H_10000/H_0=0.29358`, inside the interval.

4. **High (resolved 2026-08-22: verified complete two-cell shapes and dataflow) — Controller dimensions and stacked-cell plumbing were undefined.** The fixed tensor table gives `B_1:64x256`, two 64-state cells, the `64x64` GLU, `B_2:64x64`, and `c_t=[y_2;z_2] in R^128` (`PLAN.md:241`). The remaining generic-input shorthand is non-blocking finding 43.

5. **High (resolved 2026-08-22: only M1/M1b are a controlled dissipation comparison) — H2 falsely treated B2 as differing only in energy handling.** H2 confines the verdict to M1b versus M1 and calls B2 structurally different (`PLAN.md:53`); Section 5.4 repeats that separation (`PLAN.md:280`).

6. **High (resolved 2026-08-22: B0 assembly and a deterministic auditable matching algorithm are registered) — Parameter matching was self-authored and B0's assembly contradicted its count.** B0 instantiates no controller (`PLAN.md:280`), while Section 5.5 fixes the widening algorithm (`PLAN.md:284`). Recomputed additions are M1 `30,864`, M1b `30,992`, B2 `34,960`, and B1 `4,096`; B0 uses `d_ff=1032`, others `1024`, for a 0.960% spread.

7. **High — The loader contradiction is fixed, but the config/generator randomness API still has competing authorities.** Appendix A now correctly makes the oscillator block, including `damping_learnable`, null for non-oscillatory variants (`PLAN.md:470`). Section 6 nevertheless declares generators pure in “`(config, seed)`” while `seed_data` and `seed_rules` are config members and the eval stream is defined from those members (`PLAN.md:290`, `PLAN.md:328`, `PLAN.md:455-466`); no precedence or equality rule exists. Section 3 registers `seed_train` and a `train` stream but no stochastic operation consumes either, and Appendix A lets Task B set `task_k` although Task B fixes `k=8` without a validation rule (`PLAN.md:142-143`, `PLAN.md:308`, `PLAN.md:461`). Exact run JSONs and disagreement behavior remain implementation choices.

8. **High (resolved 2026-08-22: Task B and Task M sampling/diagnostic mechanics are materially complete) — Task B and Task M generators were underspecified.** Task B fixes cue/rule/operand/delay semantics and the stale-error comparator (`PLAN.md:308-311`). Task M fixes 32 keys, 16 values, eight queries, placements, and the 1/16 null (`PLAN.md:313-324`); Appendix B contains exactly the required ranges (`PLAN.md:472-480`).

9. **High — Phase 0/1 exact fixtures still require choices absent from the governing construction; the tie-break's factual premise is false.** The tie-break says the construction is mechanically hand-executable (`docs/reviews/plan/tiebreaks.md:3-4`), but “draw a ... permutation” never selects `torch.randperm`, Fisher-Yates, or any other byte-level primitive, so the same registered seed yields different compliant fixtures (`PLAN.md:142`, `PLAN.md:300`, `PLAN.md:350`). Task A gives no miniature count; Task M's “exact miniature fixture at P=4” has no seed, bytes, or pre-authoring protocol; the distractor and Latin tests leave their held vector/statistic and tested seeds open (`PLAN.md:353-357`). Phase 0 still omits the copy grammar/targets and most of `configs/test_tiny.json` (`PLAN.md:337`, `PLAN.md:343`, `PLAN.md:452-470`). A later reviewer checking whichever bytes the author chose does not make those missing choices derive from PLAN, so I dispute rather than execute the requested refutation.

10. **High — Naming two JAX streams does not determine the oracle cases; the tie-break omits unresolved parameters.** The tie-break claims “no authorial discretion remains” (`docs/reviews/plan/tiebreaks.md:6-7`), but Phase 2 still does not fix the input feature dimension, fixture-side `B`, official-code parameter mapping, expected hashes, Python, or NumPy; the latter is merely recorded after generation (`PLAN.md:370`). `A` is simultaneously called log-spaced and “drawn” from `fixtures:a`, without an operation that connects the stream to the deterministic period grid, and no fixture stream is registered for `B` (`PLAN.md:142`, `PLAN.md:370`). Appendix G still says only “installs jax[cpu]” and “fixed random inputs” (`PLAN.md:540`). Different nondegenerate shapes and forcing maps remain compliant, so the executed tie-break does not validly refute this finding.

11. **Critical (resolved 2026-08-22: the true boundary is registered and independently verified) — The positive reachability test contradicted the fixed mask and made G2 impossible.** The mask gives `L*(w-1)` (`PLAN.md:64`), hence toy lag 252 (`PLAN.md:215`); test 8 uses exactly that reachable boundary (`PLAN.md:374`). Task A distances 514 and 2050 remain beyond it (`PLAN.md:304`).

12. **High (resolved 2026-08-22: Task B shares `seed_rules` across train and evaluation) — Task B could resample its rule table at evaluation.** Task B uses `seed_rules` (`PLAN.md:308`), while only `seed_data` receives the eval offset (`PLAN.md:328`).

13. **High — Phase 4 now fixes stream order, but its pass/fail implementations remain non-unique.** The single pass and dataset order are finally normative (`PLAN.md:412`). The probe still omits bias, initialization, zero-variance handling, and LBFGS `max_eval`, `tolerance_change`, and `line_search_fn`, with PyTorch unpinned (`PLAN.md:194`, `PLAN.md:414`). Patch pairs are said both to be identical except for cue and to be “drawn sequentially” from an ordinary eval stream, without specifying the base-sequence/counterfactual construction; independently drawn sequences will not have identical distractors (`PLAN.md:415`). The sham predicate does not choose bitwise logits, toleranced logits, or argmax equality, and Fisher-Yates lacks the `(layer,head)` flattening order (`PLAN.md:415-416`). These choices can move the frozen G4 bars.

15. **Medium — Phase 6 is safely blocked but still has neither an executable config nor retained gate evidence.** The freeze rule calls it “a sized sketch, not yet a runnable spec” (`PLAN.md:432`). Appendix A covers only Phases 0-5 and omits the widened variant (`PLAN.md:452-470`). “Phase 2 proof tests” does not say which toy-only JAX, six-variant parameter, B1, and Task-A cases port to the scaled pair (`PLAN.md:436`, `PLAN.md:442`). Raw runs are ignored and the retained list names no scale artifact (`PLAN.md:188-190`; `.gitignore:220-225`).

16. **Medium (resolved 2026-08-22: TDD is scoped to code-bearing phases) — The universal TDD rule disagreed with the run/artifact phases.** Rule 1 scopes test-first work (`PLAN.md:76`), and the Makefile contract consistently has gates 0-4 and 6 but no gate 5 (`PLAN.md:159-160`).

17. **High — `--force` is aligned, but run identity still excludes untracked dirty state and leaves its byte contract undefined.** Section 3 hashes `git diff HEAD` and claims dirty work “can never collide” with clean evidence (`PLAN.md:146`); that command excludes untracked files. Gate runs reject dirty trees, but an `--allow-dirty` untracked-only run still receives the clean ID and can occupy it. Phase 0 now correctly limits `--force` to the same recorded git state (`PLAN.md:341`), but neither passage defines whether “git state” includes untracked path/content, nor the encodings/delimiters for the three concatenated hash inputs (`PLAN.md:338`). The destructive overwrite conflict is fixed; the identity and collision claim are not.

18. **Medium — Review-history, resume prompting, identity grammar, and amendment sequencing still disagree.** PLAN permits dated edits to prior content (`PLAN.md:100`), while the common header says “preserve verbatim” and the wrapper permits updates (`tools/codex-prompts/_common-header.md:24`, `tools/run_codex_review.sh:217-226`). The annotated-history tie-break is coherent but does not align those texts (`docs/reviews/plan/tiebreaks.md:9-10`). `RESUME_NOTE` checks `SID` before `SID` is read, so resumed prompts omit it (`tools/run_codex_review.sh:180-184`, `tools/run_codex_review.sh:258-264`). Reviewer identity is hyphen-form in the template and slash-form in wrapper context (`tools/codex-prompts/_common-header.md:14`; `tools/run_codex_review.sh:204`). Finally, the unqualified policy requires accepted review before an amendment commit, while v1.9 again committed before this review under a ledger-only initial-loop exception (`PLAN.md:114`, `PLAN.md:126-128`).

22. **High (resolved 2026-08-22: the base transformer is sufficiently pinned for implementation and counting) — The base transformer was not specified precisely enough to reproduce.** Section 5.1 fixes its activation, norms, epsilon, biases, tying, RoPE, dropout, and initialization (`PLAN.md:200-217`). Recurrent gate initialization is literal (`PLAN.md:260-267`); B1's narrower initialization issue is finding 42.

23. **Medium (resolved 2026-08-22: every control-output definition uses the full final-cell state) — Section 5.3 contradicted the fixed control-output shape.** The fixed table and gate section use `c_t=[y_2;z_2] in R^128` (`PLAN.md:241`, `PLAN.md:260`).

24. **High — v1.9 adds an order but still leaves multiple contradictory G3 outcomes.** Rule 5 uses the meta-grammar `green[+qualifications]`, while Phase 3 uses standalone `green-with-*` forms and the compound `green-with-M1b-primary+efficiency-miss`; G3.2b-alone is said to contribute a qualification absent from the three-item list (`PLAN.md:80`, `PLAN.md:402-407`). More materially, Phase 3 and Appendix C require B0-full minus M1 for G3.4, while the composition rule switches to M1b when primary (`PLAN.md:397`, `PLAN.md:407`, `PLAN.md:493`). An unresolved stability violation is red under that rule, but Appendix D.2b still allows “kill or downgrade per the affected clause” (`PLAN.md:407`, `PLAN.md:506`). Appendix D.5 also permits “three failed attempts” despite the one-pass/one-rerun G3 rules (`PLAN.md:70`, `PLAN.md:502`, `PLAN.md:511`). A fixed evaluation order cannot choose among conflicting metrics and consequences.

25. **High (resolved 2026-08-22: every registered G3/G4 row names its aggregation) — G3 and G4 thresholds omitted seed aggregation.** Appendix C names aggregation per row (`PLAN.md:486-498`), and Phase 4 requires every checkpoint to pass (`PLAN.md:412`, `PLAN.md:420`). Finding 40 concerns an inconsistent consequence attached to those explicit rules.

26. **High (resolved 2026-08-22: trained stability is a mandatory evidence condition through Phase 6) — Learned oscillator stability was checked but not gated.** The checkpoint assertion and validity row cover G3/G4/G6 (`PLAN.md:368`, `PLAN.md:488`), and Phase 5 separately requires it (`PLAN.md:424`). Finding 24 tracks the contradictory fallback consequence.

27. **High (resolved 2026-08-22: claim qualification follows statistical detection, not the practical margin) — H4 bands permitted routing without correcting the strict-separation claim.** H4 and Appendix C require any detection to qualify the claim (`PLAN.md:55`, `PLAN.md:496`). Finding 40 tracks the remaining evidence-record and strong-band aggregation defects.

28. **Low — A sibling canonical review is dirty outside this review's write scope.** Read-only `git status --short` reports `M docs/reviews/plan/science.md`; its Round 6 begins at `docs/reviews/plan/science.md:10`. This review did not alter or restore it.

29. **Medium (resolved 2026-08-22: the treatment delta is counted across both cells) — The parameter paragraph miscounted the M1/M1b difference.** Section 5.5 names the 128-parameter, two-cell delta (`PLAN.md:284`), matching `30,992-30,864`.

30. **High — v1.9's generic non-vacuity rule does not instantiate the mandatory Phase 2 proofs or make their tolerances feasible.** Test 1 fixes periods/forcing/G/horizon but not initial state, so its zero-forcing arm may be the all-zero trajectory (`PLAN.md:366`). It also compares fp32 model execution to fp64 reference “within 1e-5” without absolute/relative semantics; at period 4096, unit forcing produces states around `4e5`, whose fp32 ulp is about `3e-2`, making an absolute `1e-5` reading impossible (`PLAN.md:145`, `PLAN.md:366`). Test 2 omits the window/trend estimator and tolerance; B2 inherits it without a state fixture (`PLAN.md:367`). The zero-damping test names no nonzero input/state, scan comparison omits seed/shape/dtype, gate identity omits tokens/shape, and gradient tests omit sample counts/fixture IDs (`PLAN.md:369-374`). “Nonempty” and “executed” do not stop these cases from being trivial or author-selected (`PLAN.md:377`).

31. **Medium (resolved 2026-08-22: the H2 heuristic gives its literal estimator) — H2's uncertainty condition was not exact.** H2 defines the sample-variance estimator and M1b-minus-M1 scope (`PLAN.md:53`).

32. **Medium (resolved 2026-08-22: Phase 6 distinguishes exact lag from the conservative bound) — Phase 6 mislabeled `L*w` as the receptive field.** It gives 3060 exact, 3072 conservative, and `N=6144` beyond both (`PLAN.md:434`), consistent with Section 1 (`PLAN.md:64`).

33. **Medium (resolved 2026-08-22: the stale-error plot uses a history-conditioned comparator) — Task B had no valid stale-rule null.** The exact per-sequence comparator is registered (`PLAN.md:311`).

34. **Low — Appendix C's provenance remains false through v1.9.** It still says “last amended v1.7” and cites only v1.4-v1.7 (`PLAN.md:484`), although v1.8/v1.9 changed H2/H4 thresholds and the trial (`PLAN.md:9-10`, `PLAN.md:53`, `PLAN.md:55`, `PLAN.md:496`). Phase 0 has not started, so timing is honest; the audit label is not.

35. **High (resolved 2026-08-22: Kimi now uses the same generic topic fallback as Codex) — Mandatory Kimi Phase 5/7 reviews could not start.** Kimi maps `phase*`, `tradeoff`, and `report` to `review-phase.md` before checking existence (`tools/run_kimi_review.py:122-130`), matching the registered cadence (`PLAN.md:103-108`).

36. **High (resolved 2026-08-22: model execution and test-side reference precision are separated) — The global dtype contract made Phase 2 tests mutually inconsistent.** Section 3 permits fp64 references/accumulation while models execute fp32 (`PLAN.md:145`). Phase 2 follows that split (`PLAN.md:366-370`); finding 30 separately covers the still-ambiguous comparison tolerance.

37. **High (resolved 2026-08-22: the first answer of each independent sequence is a valid Bernoulli trial) — H4's binomial test had no valid trial.** H4 now selects the first queried answer, `n=10,000`, null `p=1/16`, and an exact upper-tail test (`PLAN.md:55`). Task M makes first-query values uniform across independent fresh sequences (`PLAN.md:321`, `PLAN.md:328`). Recalculation gives the first `p<0.001` cutoff at 702/10,000; the statistic is mathematically executable. Its artifact and consequence are finding 40.

38. **Medium — Kimi still violates the canonical-review-only policy and contaminates its own context/metrics with rejected siblings.** PLAN permits only canonical reviewer output (`PLAN.md:105`, `PLAN.md:182-183`), but Kimi deliberately writes `<topic>-kimi.rejected.md` (`tools/run_kimi_review.py:11-12`, `tools/run_kimi_review.py:183-188`). Both rejected files are tracked; Kimi inlines every `docs/reviews/**/*.md`, and `agent_metrics.py` parses every such Markdown as a topic (`tools/run_kimi_review.py:40-46`; `tools/agent_metrics.py:88-104`). Rejected candidates therefore affect later context and retrospective metrics.

39. **Medium — README was not updated for either material H4 amendment.** PLAN requires a same-commit README mapping update for material gate changes (`PLAN.md:192`). H4 now separates a first-answer detection test from mean magnitude (`PLAN.md:55`, `PLAN.md:496`), but README still says the “pre-registered bands ... measure any content routing” and lets “a low score” stand for no evidence (`README.md:38`); neither v1.8 nor v1.9 modified README.

40. **Medium — H4's valid first-answer decision has no fixed evidence field, and its strong consequence can average away a seed-level falsification.** Section 6 fixes each cell's result record to pooled `{cell, variant, seed, n_sequences, n_answers, accuracy}` with no first-answer successes or p-value (`PLAN.md:328`), so the new statistic cannot be reconstructed from the named retained record. Appendix C detects per seed but bands mean accuracy across seeds; `[60,5,5]` detects routing yet averages 23.3, evading the `>=50` capacity probe and full withdrawal despite one checkpoint strongly routing content (`PLAN.md:496`). Phase 4 inherits the band trigger (`PLAN.md:417`). A coder must add an unregistered result field, and the categorical claim consequence disagrees with the per-seed existence unit.

41. **Low — The trained-checkpoint exact-zero-gradient regression has no gate owner.** Phase 2 says to rerun the load-bearing test after Phase 3 on trained B0-local/B1 checkpoints (`PLAN.md:373`), but G3's clauses and Appendix C validity row name only performance and stability (`PLAN.md:392-408`, `PLAN.md:488`). The post-training guard can be skipped with every gate green.

42. **Medium — B1's initialization is not registered and need not start near the identity behavior used for recurrent variants.** B1 is a bias-free `sigmoid(w·x_norm)` gate but its row gives no initialization (`PLAN.md:275`, `PLAN.md:284`). At near-zero weights it scales heads by about 0.5, whereas recurrent gates are explicitly initialized near multiplier 1 (`PLAN.md:267`). Appendix G delegates B1 initialization details to an unpinned repository (`PLAN.md:541`). This does not break the unreachable null, but it leaves fidelity and the stated M1-minus-B1 statefulness comparison implementation-dependent.

43. **Low — Section 5.2's generic input sentence conflicts with its own fixed cell-2 input.** It calls `u_t` “token embedding (256)” for the system “per cell” (`PLAN.md:223`), while the fixed table says cell 2 reads a 64-dimensional GLU output through `B_2:64x64` (`PLAN.md:241`). The explicit table makes intent inferable, but both statements cannot literally hold for cell 2.

44. **Low — Task B silently pools attention-reachable and recurrence-only delays.** Delay is uniform over 32..256 and cue-to-decision lag is delay+2 (`PLAN.md:308`); with receptive field 252 (`PLAN.md:215`), delays 32..250 are reachable and 251..256 are not. The only reports are accuracy versus switch count and stale error, with no delay stratum (`PLAN.md:310-311`). Matched sampling preserves the M1/M1b comparison, but the secondary switching curves do not identify which memory path produced their behavior.

## Recommendations

1. Define one generator API and seed source of truth; pin Task B `task_k=8` in validation and name any real consumer of `seed_train` (`PLAN.md:142-143`, `PLAN.md:290`, `PLAN.md:308`, `PLAN.md:455-470`).
2. Register the exact permutation primitive, Task A fixture count, Task M miniature seed/bytes/protocol, distractor/Latin fixtures, and the complete copy-task config/grammar before Phase 0/1 code (`PLAN.md:300`, `PLAN.md:337-357`).
3. Freeze every Phase 2 case and tolerance: nonzero initial states/inputs, absolute-plus-relative comparison rules, window/trend estimator, scan and gate fixtures, and sample counts (`PLAN.md:145`, `PLAN.md:366-377`).
4. Freeze the JAX manifest's input dimension, `B`, state, official mapping, Python/NumPy/JAXLIB versions, inputs, and expected hashes; make Appendix G reference that manifest (`PLAN.md:370`, `PLAN.md:536-540`).
5. Complete Phase 4's classifier/LBFGS settings, counterfactual pair construction, sham predicate, and channel flattening order (`PLAN.md:412-416`).
6. Use one literal G3 status grammar; make G3.4 conditional on the primary variant in Phase 3 and Appendix C; replace D.2b's discretion and reconcile D.5's attempt budget (`PLAN.md:80`, `PLAN.md:397`, `PLAN.md:402-407`, `PLAN.md:493`, `PLAN.md:506`, `PLAN.md:511`).
7. Add first-answer successes and exact p-value to the fixed result record, and trigger strong H4 consequences on any strong seed or explicitly scope the claim to mean behavior (`PLAN.md:55`, `PLAN.md:328`, `PLAN.md:417`, `PLAN.md:496`).
8. Hash untracked paths/content or forbid all dirty runs from sharing the clean namespace; define byte encodings/delimiters and the full `env.json` git-state identity (`PLAN.md:146`, `PLAN.md:338`, `PLAN.md:341`).
9. Move rejected Kimi candidates outside `docs/reviews`, exclude them from context/metrics, initialize `SID` before prompt construction, and align the header's history/identity grammar with PLAN and the wrapper (`PLAN.md:100`, `PLAN.md:105`; `tools/run_codex_review.sh:180-204`, `tools/run_codex_review.sh:258-264`; `tools/run_kimi_review.py:40-46`, `tools/run_kimi_review.py:183-188`).
10. In the Phase 6 amendment, extend Appendix A, enumerate the scaled proof subset, and name a committed scale-evidence report outside ignored run directories (`PLAN.md:432-442`, `PLAN.md:452-470`; `.gitignore:220-225`).
11. Update Appendix C provenance and README's H4 explanation to v1.9, and assign the trained-checkpoint gradient rerun to G3 (`PLAN.md:192`, `PLAN.md:373`, `PLAN.md:484`, `PLAN.md:496`; `README.md:38`).
12. Register B1 initialization, correct the cell-2 generic input sentence, and stratify Task B's secondary curves by attention reachability (`PLAN.md:223`, `PLAN.md:241`, `PLAN.md:267`, `PLAN.md:275`, `PLAN.md:308-311`).

## Evidence consulted

- `PLAN.md:1-544`, read in full, including Section 2b, the entire ledger, Sections 3-6, Phases 0-7, and Appendices A-G.
- `README.md:1-66`, read in full and checked against H4, governed artifacts, and stage/status language.
- Existing `docs/reviews/plan/spec.md`, including every finding and the verbatim Round 1-5 log blocks; `docs/reviews/plan/tiebreaks.md:1-10`, whose two spec verdict premises were independently checked and disputed above.
- Commit `e872754` inspected with read-only `git show`/`git diff`; every v1.9 claim was checked against normative text rather than the amendment summary.
- `.gitignore:220-230`, `tools/check_review_scores.py:1-111`, `tools/review_round_tracking.py:1-158`, `tools/run_codex_review.sh:1-417`, `tools/run_kimi_review.py:1-198`, `tools/agent_metrics.py:1-131`, and `tools/codex-prompts/_common-header.md:1-53`, checked against Section 2b and the layout/results policy.
- Repository inventory from `rg --files`; no implementation, configs, Makefile, fixtures, results, or replayable gate exists, while two tracked `*-kimi.rejected.md` sibling reviews do.
- Vocabulary/run replay: PAD + 32 cues/keys + QRY + 16 operands/values + 14 distractors = 64; `P=32` exhausts the key range; 16 gates are `4x4`; the Phase 3 matrix is 66 Task A plus 30 Task M runs = 96.
- Receptive-field replay: toy lag `4*(64-1)=252`, scaled lag `12*(256-1)=3060`; Task A distances 514/2050 and Phase 6 `N=6144` remain unreachable; Task B delays 251..256 cross the toy boundary.
- Parameter replay: base `3,180,800`; additions M1 `30,864`, M1b `30,992`, B2 `34,960`, B1 `4,096`; B0 `d_ff=1032` and all others `1024` give a 0.960% spread.
- Numerical replay: the recurrence is symplectic Euler with implicit damping and preserves the stated undamped invariant; the corrected damping envelope remains attainable. At period 4096 under unit forcing, fp32 state scale makes an unspecified absolute `1e-5` comparison infeasible.
- H4 replay: the first-answer statistic is Bernoulli(1/16); the exact `p<0.001` upper-tail cutoff is 702/10,000 (tail `0.0009386`, versus `0.0010734` at 701). The fixed result JSON cannot reconstruct that count, and mean banding can hide a strong seed.
- Read-only `git status --short` showed only `docs/reviews/plan/science.md` modified outside this review path before writing; its Round 6 begins at line 10. This review did not alter or restore it.
- No implementation gate could be replayed because the repository remains at the specification-only stage.
