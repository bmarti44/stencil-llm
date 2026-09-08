# Independent review: original-source reminder research

2026-09-08. Reviewer: Astra xhigh, maximum-effort reasoning requested.
Reviewer selection: explicitly assigned Astra for this research review, replacing
the repository's standing Opus review default. Author-disjoint from both the
research lane and root synthesis. No additional agents used.

Reviewed base commit: `c6616c4f581c177816721b97407fafd59be77450`.
Initial report SHA256: `ad7742880281d6fc46abfdeaa7ab96754a3e557e0d4f9a140457735a0268282f`.
Final reviewed report SHA256 (updated 2026-09-08 after the narrow correction):
`a7e7cb46c51734ad3600fbad78714fe2c02aa62b8a592bf9ee94b979ec7ae220`.
Scope SHA256: `2bd17a20a2682891e2dae3549757d5976eb37aef4a070a9cb3709278351c9f19`.

Purpose: assess claim/source accuracy and whether one minimal, fresh utility
comparison is worth preparing. Threat model: trusted-but-fallible science.
The ineligible trained-interpreter screen and its frozen failure are accepted
premises, not re-adjudicated. This review does not approve an experiment
specification, model configuration, qualification run, or GPU launch.

## Round 1

Score: 96/100

Decision: **Recommend preparing one small original-source reminder comparison
against ordinary history and deterministic recency.** There is sufficient
adjacent evidence to justify this bounded question, and insufficient evidence
to predict a coding win. No high or critical findings. One low source-reporting
caveat was resolved by the correction recorded below (updated 2026-09-08).
No open findings remain.

### Findings

1. **LOW — Qualify LongMemEval's exact recall gain because its tables disagree.**
   **(resolved 2026-09-08)**
   The report's lines 56–58 accurately reproduce main Table 3: GPT-4o top-10 QA
   goes from 0.670 to 0.720, and round Recall@10 from 0.692 to 0.784. Appendix
   Table 10 repeats those numbers. However, Appendix Table 9 lists Stella V5
   1.5B round Recall@10 as 0.784 for both `K = V` and `K = V + fact`. The
   discrepancy appears in both HTML and PDF text. The exact retrieval gain
   should therefore be attributed explicitly to Tables 3/10 with this caveat,
   or omitted while retaining the QA result. This limits confidence in that
   precise effect size; it does not refute the proposed preparation or establish
   which table is wrong. No reproduction or new data work is warranted here.
   [LongMemEval v2, Tables 3/9/10](https://arxiv.org/pdf/2410.10813v2).

   Closure check: the revised bytes explicitly exclude the disputed recall gain
   and attribute QA to Table 3. Only that paragraph changed.

### Consequential primary-source checks

- **SWE-ContextBench:** the five resolution figures, costs, runtimes, and
  representation lengths match v3 Table 4 and §3.3. These are Claude Sonnet 4.5
  results on the 99-task Lite comparison. The paper's patch-exclusion wording
  and reported percentages leave denominator interpretation unclear; the
  synthesis appropriately avoids reconstructing counts. Unfiltered experience,
  shared-fix relationships, and incomplete human validation are documented.
  The automatic raw-context result is neutral and costlier; oracle summaries
  are not proof that automatic selection works. The report uses this as
  counterevidence rather than borrowing the abstract's broad efficiency claim.
  [SWE-ContextBench v3, §§2.2.3/3.3 and A.4–5](https://arxiv.org/html/2602.08316v3).

- **ReadAgent:** Tables 1 and 7 confirm every quoted accuracy and the
  three-run versus one-run distinction. Relative to full text, the cited
  PaLM 2-L automatic lookup improvements are only 0.33 and 1.34 percentage
  points; GPT-3.5 loses 3.65 and 1.20 points. Gists remain part of the method,
  and these are QuALITY development-set reading results. The synthesis makes
  the relevant model and task-transfer limitations explicit; it does not
  advertise the much larger gist-only comparison as a coding effect.
  [ReadAgent v3, Tables 1/7](https://arxiv.org/html/2402.09727v3).

- **LongMemEval:** remaining representation, indexing, timestamp, and budget
  claims match §5. Chain-of-Note/JSON are additional reader ingredients; this
  remains adjacent QA evidence. Ordering and role preservation have no isolated
  causal result. (updated 2026-09-08: condensed the remaining checks.)
  [LongMemEval v2, §§5.1–5.5](https://arxiv.org/html/2410.10813v2).

- **Prompt repetition and VerIFY:** the 47/70 wins and zero losses use the
  stated McNemar threshold; the reasoning condition is five wins, one loss,
  22 ties. VerIFY's Reinstruct assumes an already identified instruction and
  detected noncompliance; its 28 instruction variants, four models, and
  user-prompt-only evaluation match the report. Neither supplies evidence of
  automatic arbitrary-source selection improving executable coding.
  [Prompt Repetition v1, §2 and A.2](https://arxiv.org/html/2512.14982v1),
  [VerIFY, §§4–6/8](https://aclanthology.org/2026.findings-eacl.254.pdf).

- **EvoCode-Bench:** cumulative tests retain active behavior and replace
  superseded assertions. The report correctly distinguishes task-averaged,
  four-attempt persistent MT@4 from round-averaged, single-attempt SR starting
  from reference-completed workspaces. Their difference cannot isolate
  forgetting. Adopting behavioral verification while declining a causal
  source-replay inference is justified.
  [EvoCode-Bench v1, §3.4 and B.3–5](https://arxiv.org/html/2605.24110v1).

- **Declarative Attention:** the headline accuracy reductions, worse small-model
  transfer, custom masking, and B200 roofline cost estimates are correctly
  characterized. They provide no basis for estimating this local replay's
  realized speed or requiring an attention-engine implementation.
  [Language Models Can Control Their Own Attention, §§4–5/8](https://arxiv.org/html/2609.02737v1).

### Why the preparation recommendation survives

The intervention is materially distinct from the frozen interpreter: its
intermediate output selects message identities, deterministic copying supplies
the original evidence, and the coding worker performs interpretation. Success
is downstream executable behavior. That removes the requirement to generate a
complete authoritative rule list, while retaining the real possibility that
selection omits a needed exception or overemphasizes obsolete text. The report
acknowledges that copying preserves text rather than applicability.

The three proposed arms answer useful, separable practical questions: whether
automatic reminders help an ordinary-history worker and whether model-based
selection earns its expense over a cheap recency rule. Equal budget policies
and complete selector-plus-worker accounting are appropriate for this utility
screen. The evidence does not require an oracle selector, a new index, fitting,
or a search across prompt variants before this question can be tested.

Exact worker/selector identities, reasoning modes, allowances, error behavior,
project count, operational gates, and stop conditions remain prospective work
explicitly deferred by the report. Their absence is not a defect in a research
decision. The eventual preparation must preserve the promised one-setting
freeze, fresh independent projects, reviewed source/test alignment, affordable
whole-run limit, and restriction of a positive small screen to preparing larger
untouched validation. No old-case repair or adapter salvage follows from this
recommendation. Useful automation need not surpass manual prose to be worth
measuring.

Only scope/report and repository governance/state metadata were read locally.
Primary web spot checks covered all seven cited papers and consequential version
dates. No implementation, tests, model calls, fitting, GPU execution, paid
services, or dataset acquisition occurred. Current withheld semantic sources,
responses, private maps, and spent project banks were not opened. Incidental
examples in paper pages are excluded from future authoring or evaluation use.
