# Automatic reminders from original sources: research decision

2026-09-08. Audience: Stencil's next experiment and implementation decision.
Root synthesis with an independent Astra xhigh research lane. Research only:
no model execution, data acquisition, training, candidate selection on evaluation
outputs, or changes to the ineligible source-interpreter trial.

**Prepare one small, fresh executable comparison of automatic original-source
reminders. Do not build a memory framework or claim that retrieval already
works.** The plausible benefit is bringing relevant evidence near the work
request without rewriting its meaning. The closest coding evidence cautions
that automatic retrieval can add cost without improving success.

The existing trained interpreter does not advance. This proposal is a distinct
prospective test of source selection and re-exposure, leaving interpretation to
the coding worker. It neither repairs that trial nor reuses its cases, labels,
responses or adapter. Automatic usefulness can matter without beating manual
prose; a perfect intermediate rule list is not a prerequisite. Larger untouched
coding evidence remains necessary before claiming the project goal.

## Evidence that changes the decision

**Executable coding provides the strongest caution.** SWE-ContextBench v3 tests
99 related coding tasks under five context settings. Reported resolution is
26.26% without retrieved context, 26.26% with autonomous full-trajectory access,
27.27% with oracle trajectories, 22.22% with autonomous summaries and 34.34%
with oracle summaries. Autonomous full-context cost rises from $0.79 to $0.98.
The oracle-summary mean is 6.66 minutes/$0.85 versus baseline 6.37/$0.79.
Thus the abstract's broader efficiency language cannot be applied uniformly.
Trajectories average 25,633.7 tokens versus 217.1 for summaries, so representation
and volume are not matched. The paper describes excluding non-applicable patches
from remaining evaluation; these are its reported percentages, not reconstructed
denominators. Prior experience quality is unfiltered, some related issues share
fixes, and comprehensive human test/solvability validation is absent. This
supports measuring automatic selection and cost directly. It does not test
short reminders from the current instruction history.
[Zhu et al., 6 May 2026, §§3.3–3.4, A.4–5](https://arxiv.org/html/2602.08316v3).

**Original evidence can recover detail lost by summarization.** ReadAgent uses
generated gists to choose original document pages automatically, then answers
with both. On QuALITY's 230 documents/2,086 questions, the revised paper reports
PaLM 2-L accuracy of 77.52% for gist-only, 85.83% for full text, 86.16% for
automatic 1–2-page lookup and 87.17% for sequential 1–6-page lookup. These are
three-run means. The GPT-3.5 appendix supplies counterevidence: full text 73.30%
exceeds parallel lookup 69.65% and sequential lookup 72.10% in one run. This is
reading comprehension, not coding or evolving authority. Generated gists remain
in context, so the intervention is not pure original-source replay. Root first
read v1, then independently verified v3; the numbers here use v3 consistently.
[Lee et al., ICML 2024; v3, 22 July 2024, Tables 1/7](https://arxiv.org/html/2402.09727v3).

**Chronological original rounds are a defensible representation, not a semantic
guarantee.** LongMemEval generally finds that replacing original conversational
rounds with facts/summaries loses QA performance, with multi-session reasoning
an explicit exception. Its automatic pipeline sorts retrieved items by timestamp;
round/session retrieval keys keep user-side text, and indexing uses model-generated
facts with a 1.5B dense retriever. Original-round GPT-4o top-10 QA improves from
67.0% to 72.0% when fact text augments the index keys; recall rises from 69.2%
to 78.4%. The 8B reader deteriorates beyond roughly 3,000 retrieved tokens;
this cannot set our local allowance. The 500-question study measures memory QA,
including updates, rather than coding, adoption or permission authority. Neither
chronological order nor role preservation has an isolated causal result here.
[Wu et al., ICLR 2025; v2, 4 March 2025, §§5.1–5.5](https://arxiv.org/html/2410.10813v2).

**Repetition is adjacent support.** Prompt Repetition reports 47 wins/zero losses
among 70 model/task combinations under its McNemar p<0.1 convention when
reasoning is disabled, versus five wins/one loss/22 ties with step-by-step
encouragement. These are QA/math/retrieval tasks; long requests sometimes increase
latency. No automatic source selection or executable coding is tested.
[Leviathan et al., Google Research, 17 December 2025](https://arxiv.org/html/2512.14982v1).
VerIFY's Reinstruct repeats a known instruction after detected noncompliance;
that known rule/detector is an additional assumption. Its 28 verifiable
instructions and four models do not establish arbitrary-rule identification or
code quality. The authors also exclude system-prompt evaluation.
[Robinette et al., EACL 2026, §§6.1/8](https://aclanthology.org/2026.findings-eacl.254.pdf).

**Evaluate maintained behavior through executable tests.** EvoCode-Bench uses
persistent projects and cumulative behavioral checks that retain active
requirements while replacing superseded assertions. Its MT@4 and isolated SR
scores differ in attempts, workspace origin and task-versus-round weighting;
their gap is not a causal forgetting estimate. It has no source-replay
intervention. We adopt only the evaluation principle: check both the new work
and requirements that remain active, without dictating an implementation.
[Shen et al., 22 May 2026, §§3–4 and Appendix B](https://arxiv.org/html/2605.24110v1).

Declarative Attention is outside this quick implementation. Its text-controlled
attention masks reduce attended tokens but reduce average accuracy on the
headline models; small-model transfer is poor and speed estimates use a B200
roofline model. Fixed-context repository QA is not executable coding. It does
not justify new kernels, model downloads or reopening prior steering recipes.
[Language Models Can Control Their Own Attention, September 2026, §§4–5/8](https://arxiv.org/html/2609.02737v1).

## Minimal prospective mechanism and test

Use one fixed selector with existing local assets to output original message
IDs only. Copy complete selected messages deterministically, in original order,
with original role and source identity carried as evidence metadata. Present
them as historical evidence, never as newly issued higher-priority commands.
Retain the coding worker's complete authentic history. Select afresh for each
request; there is no generated persistent rule state to update or repair.

This is an engineering inference, not a literature-established recipe. Whole
messages can include obsolete clauses or omit another message needed to resolve
an exception. Copying preserves bytes, not applicability. The worker must still
interpret evidence. Avoid extractive string/regex admission rules, a new encoder,
learned index, critic tree, mutable registry or custom attention engine.

Prepare three paired arms on independently Kimi-authored executable projects:
ordinary full history; full history plus automatic source reminders; and full
history plus deterministic recent-source reminders under the same evidence
budget rule. The third arm tests whether model-based selection earns its cost.
Do not select a new candidate retrospectively from the control's results.

Keep the worker, code interface, output allowance, feedback and persistent
workspace policy fixed across arms. Hidden behavioral tests should cover newly
requested behavior, still-active requirements, and retirement of obsolete
behavior. Independent source/test review and passing reference implementations
must establish that those checks actually follow the task. No exact generated
focus target or perfect-selector gate is needed for this utility question.

Use projects as independent units; report per-project trajectories, joint
correctness/adherence, regressions, and full selector-plus-worker time/tokens.
Count failed or invalid work explicitly. No gold workspace resets, silent
sample reduction, label repair after exposure, or repeated prompt/cap variants.
Measure human intervention, rather than assuming that automatic execution proves
zero intervention.

The next preparation must specify the exact model/mode, message-budget policy,
selector-error behavior, workload, absolute usefulness threshold and stopping
rule **before any fresh test outputs**. Reuse existing consumers where possible.
One separately scoped technical measurement must establish actual local cost;
then freeze a one-GPU-hour-or-less quick screen including cleanup, with startup
and call limits subordinate to the whole deadline. No new GPU launch is
authorized by this research report alone. If no fixed affordable setup is
available, reject this proposal without launching a matrix.

An improvement in a small screen permits only preparation of a larger untouched
validation. That later proof must assess useful automatic focus against ordinary
history and useful manual reminders, with executable outcomes and measured costs.
Representation superiority and perfect intermediate extraction are unnecessary.

## Remaining gaps and stopping reason

| Question | Evidence | Next decisive action |
| --- | --- | --- |
| Does source lookup preserve useful detail? | Supported in adjacent QA; model-dependent | Verify local reader/selector behavior prospectively |
| Does automatic retrieval improve coding? | Mixed; nearest raw-history result is neutral and costlier | Compare fresh executable outcomes and total cost |
| Does replay preserve temporal authority? | Byte/order provenance only; no general semantic proof | Include evolving requirements and test their behavior |
| Is this affordable on existing hardware? | Unknown for the new fixed interface | Small measured technical qualification before a screen |
| Is the overall goal met? | No | Larger untouched, independently reviewed coding validation |

The linked paragraphs form the claim-to-source ledger: titles, dates, exact
versions, methods and limitations are stated where used. All sources were
accessed on 2026-09-08. Root independently checked consequential agent claims
against the primary papers, including the ReadAgent version difference and
negative results. Broader memory discovery stopped because it cannot close the
local utility/authority gaps; those require an experiment. No benchmark dataset
was acquired or used. Incidental examples returned within paper pages are
excluded from future data authoring, fitting and testing.

Repository Markdown is the available internal engineering deliverable. Structural
and link-target review is applicable; no rendered PDF or visual review is claimed.
