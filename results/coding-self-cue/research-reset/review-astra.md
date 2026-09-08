# Research-reset synthesis — Astra accuracy and decision review

Reviewer: explicitly configured `gpt-6-astra`, xhigh, `/root/astra_research_reset`, 2026-09-08; requested substitution for the historical Opus default. Parent authored the synthesis. This reviewer contributed one preceding research lane but did not author or edit the synthesis; this is an author-disjoint prose/source review, not a blinded replication of the research. Only this review file is writable. No implementation, training, data generation, model calls or experiment is authorized or performed. Maximum two review rounds for this documentation unit; preserve numbered findings.

## Round 1

**Score: 95/100. ACCEPTED for research accuracy and the preparation decision. Zero open high/critical findings.** Reviewed `report-source.md` SHA-256 **`8a2dbe4d55f73f455049a57c57bd10e98f746e9f231bb0408eb60e4dd7b37a81`**. One low provenance item remains below. The parent plans to add concrete reuse paths after the implementation inventory; that final delta requires a bounded second-round binding, not another literature search or experimental review.

1. **LOW — inventory-completion attribution is not yet substantiated in this snapshot (open).** The closing paragraph says Sol supplied a read-only feasibility inventory, while the review brief says the parent is still awaiting it. This does not affect the scientific decision. Once the inventory is delivered, cite or accurately summarize its concrete paths; otherwise describe it as pending. Do not imply that existing training assets have been audited clean merely because reusable infrastructure exists.

### Evidence checked

The archived screen claim agrees with commit `27dc06b8`, the original receipts and this reviewer's final integrity audit: C 2/24, M 12/24, H 10/24; zero complete trajectories in every arm; four capacity failures, complete accounting and technically incomplete evidence. The synthesis does not turn this into a fully completed semantic null, blame one unproved cause, or reopen a parked recipe.

Spot-checked the primary sources supporting the new decision:

- [SWE-agent v3](https://arxiv.org/html/2405.15793v3), Table 3: the reported edit/lint/no-edit ablation values agree. The prose correctly treats this as interface evidence on that workload, not a local causal result or a near-perfect performance prediction.
- [Is Self-Repair a Silver Bullet?](https://arxiv.org/abs/2306.09896), 2 February 2024 revision, supports the cost and feedback qualifications. [Try Again, Don't Look Back](https://arxiv.org/html/2607.26117v1) uses matched retry counts and differential benchmark feedback; the synthesis correctly denies permission to expose the new private scorer.
- [Building to the Test](https://arxiv.org/html/2606.28430v1) supports the narrow 18-run finding and dependency/no-op audit lesson. The synthesis does not claim general prevalence or import the paper's stronger causal language.
- [VerIH v5](https://arxiv.org/html/2511.04694v5), section 6.4 and Appendix C: the corrected multi-turn numbers and reported training hardware/time agree. The synthesis explicitly corrects my earlier overly broad claim about missing multi-turn evaluation. Missing transfer is narrowed to the scoped coding lifecycle and proposed local supervised method.
- [Prose2Policy](https://arxiv.org/html/2603.15799v1), sections 6–7: accepted/compiled/positive-test denominators agree; correlated test generation is appropriately treated as a limit. [AgentGuardUtil](https://arxiv.org/html/2608.23282v1), section 3: reliability/cost figures and uncovered-rule limitation agree, without implying a complete semantic guarantee.

The source ledger distinguishes author-reported results from local replication, dates the checked versions, states disconfirming evidence, and uses method/results evidence without acquiring benchmark task banks for reuse.

### Decision and arithmetic

The proposed M-only screen tests a missing prerequisite: whether the coding environment and worker can deliver useful dependent code with competent reminders. It makes no automatic-selection claim. Four projects with three requests each yield 12 work items; at most three model-call/edit attempts each yields 36 calls. The shorter trajectories are expressly a competence prerequisite, not a replacement for longer focus evaluation.

The proposed public/private separation is operationally meaningful: public-only repair and stopping, fixed attempt limits, actual accumulated artifacts, no gold resets, no private scorer observations, final private scoring, and independent direct-source/dependency review. A parser or compile failure can consume a registered repair attempt without erasing the failure. Successful final code and full accounting are required; human intervention or an unresolved final technical failure cannot be counted as success.

Independently recomputed the observed whole-HTTP rate as `26922 / 1178.774697 = 22.83897005` tokens/second. The stated illustrative projection is `36 × 1024 / rate + 600 + 120 + 60 = 2394.0832936` seconds; the 2,700-second margin is `305.9167064`. Both rounded claims are correct. The 120-second execution allowance and new-loop transfer are assumptions requiring prospective sizing, as the report says. Neither output headroom nor a local training budget is falsely claimed established.

The conditional interpreter remains one learned mechanism with small complete-current-prose output and source references. Source-ID validation is explicitly separated from semantic correctness/completeness. The report requires new fit conversations, whole-conversation separation, semantic label review, an unchanged-base comparison and cost qualification; it does not assume old data/adapters are clean or that cheap SFT reproduces verifier-reward training.

Stop-loss and progression are clear: failure parks the worker/environment point, with no easier bank, prompt rescue or additional calls on spent cases. A competent M result admits interpreter preparation, not automatic benefit. Subsequent comparisons keep worker/tools/feedback/budgets matched and require fresh larger whole-project evidence, an absolute usefulness bar and a declared loss margin against M. Nonsignificance and preauthored reminder costs are not misrepresented as parity or human-time savings. This is a preparation decision only, with implementation/data/resource review and registration still required before a launch.

## Round 2 — final settled synthesis

**Score: 96/100. ACCEPTED. Zero open findings; zero open high/critical findings.** Final synthesis SHA-256: **`2366f03e82823949c33242926eed54e18996c046595bd6260cd657dabf5cce5f`**. This is the final review round for this documentation unit.

1. **LOW — inventory-completion attribution (resolved).** Parent confirms Sol delivered the inventory; the report now includes concrete linked reuse paths and their limitations. All four local Markdown links resolve. Read-only inspection confirms `scripts/coding_self_cue_run.py` accepts only system/user/assistant roles, so the report accurately says native tool transport needs an extension. `scripts/focus_check49.py` contains a causal-language-model LoRA training primitive; its existence is not represented as a qualified interpreter, clean adapter, clean fit bank or demonstrated cheap training recipe. The failed historical scientific control remains a reason to require new qualification, not a primitive-reuse prohibition.

The delta also makes citations per obligation explicit, distinguishes the report's three-action/36-call proposal from the inventory's illustrative two-action sketch, and states that the frozen experiment files must be preserved. A new public/private validator, targeted tests and launcher mode are future preparation requirements, not claims that the existing harness already implements the proposed experiment. The last paragraph now accurately distinguishes worker inference from research activity.

The original source checks, corrected VerIH reading, arithmetic, gate order, limits on generalization and no-rescue stop rules remain intact. No additional broad research, fixture replay or model execution was needed for this final delta. Acceptance supports the stated next CPU-only specification/sizing work; it does not authorize an experiment or training launch and does not assert that a useful operating point already exists.
