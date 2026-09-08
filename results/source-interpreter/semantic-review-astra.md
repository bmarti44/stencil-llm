# Source-semantic specification review — Astra

Canonical topic: `source-semantic`. Reviewer session: native
`/root/source_semantic_review`, Astra xhigh, author-disjoint from the specification
and implementation. Current user-directed native-agent/model roles supersede the
archived wrapper and Opus roles; this is that explicit substitution, not a silent
fallback. Reviewer writes only this file and makes no commits.

Purpose: test fresh lineage, semantic measurement and inference, practical cost,
one-look handling, and efficient progress toward adequate fresh coding evidence.
Threat model: trusted-but-fallible research agents. Hostile same-UID defenses,
perfect-selector gates, representation superiority, and a new experiment
framework are outside scope. This review grants no experiment authority.

## Round 1 — 2026-09-08

Score: 88/100

Decision: changes required. Open findings: **one high, zero critical**. The
proposed small comparison is otherwise scientifically reasonable and practical
as a bounded falsification screen.

Reviewed `SEMANTIC.md` SHA256
`6a855ab40fbb638de4f1b844986b0878444d6afe86c257e5de3c15161696b4d9`,
at commit `e13c51416005fa5a2eaac04cd7c278a34487d64d`.

Read current AGENTS, `archive/plan/PROTOCOL.md`, latest appended LEDGER STATE,
accepted FIT/PREP, current FIT RESULTS, the relevant source/schema/preparation
consumer, and the existing research recommendation. FIT RESULTS was read while
its separate accuracy audit was pending; root subsequently reported that audit
accepted at 96/100 with no open high/critical findings, unchanged recorded costs
and capped trained failure. This review uses the recorded timings for prospective
arithmetic and does not duplicate that actual-run audit.

Also reviewed the six prospective Kimi requests and authoring plan SHA256
`75303a6d43e82a43250f0967823b9d6ed9e2c65d354c8996dcab7862b15b9ea7`.
All request bytes match that manifest. Their preassigned withheld identities,
domains, bands, three checkpoints, final-query boundary, and distributed semantic
coverage agree with the draft. No new source conversation, reference target, or
model response exists in the reviewed requests. No model/GPU/weight/network call,
old-bank access, or implementation edit was performed.

### Findings

**1. High — Incomplete execution is not excluded from the primary inference or
automatic continuation decision.** (resolved in Round 2, 2026-09-08)

Evidence: SEMANTIC lines 111–115 classify technical exceptions/deadlines as
INCOMPLETE; lines 127–137 score unavailable responses as failures; lines 147–166
then define the sign test and practical decision without a completion-eligibility
condition. Consequently an unattempted control can be treated as an observed
semantic loss. The known schedule makes this concrete: final row 17 runs the
adapter before the base, so a whole-job deadline can leave an adapter answer and
no corresponding base answer.

Deterministic counterexample, not experimental data: trained conversation counts
`[3,3,3,3,2,2]` and base counts `[2,2,2,2,2,1]` yield five wins, no losses, one
tie, and one-sided `p=1/32`. If the last base answer was merely unattempted and
would have succeeded, the base counts are `[2,2,2,2,2,2]`: four wins, no losses,
two ties, `p=1/16`. The missing call alone crosses the registered 0.05 boundary.
The trained 16/18 count also passes the practical bar in both versions. Printing
INCOMPLETE beside either claim does not remove the missing comparison or define
which rule controls advancement.

Required correction: register explicit eligibility before inference and the
automatic practical-screen decision. An eligible completed comparison needs all
36 scheduled calls returned with required evidence, accepted labels, and no
technical deadline/exception or unresolved unavailable/not-attempted comparison.
An incomplete or label-ineligible run may retain qualified partial descriptive
evidence and costs, but cannot claim primary learning improvement or automatically
pass this screen. Never treat an unknown control response as an observed semantic
failure in inferential counts. A normally returned capped or malformed response
remains an observed failure and does not by itself make execution incomplete.
No rerun, additional model call, new framework, or changed threshold is needed.

### Checks and interpretation

- Decimal arithmetic independently reproduces the pair cost
  `163.568515525` seconds; eighteen pairs `2944.233279450`; setup plus tail total
  `3166.124011412` seconds, or `52.7687335` minutes; and four times the estimate
  `12664.496045648` seconds. The 3600-second ceiling leaves `433.875988588`
  seconds, approximately 13.70% above the estimate. This is little contingency
  for unseen longer prefixes, but the draft discloses that uncertainty and
  registers an honest stop. No larger allowance is implied by the arithmetic.
- Six conversation units avoid treating correlated checkpoints as independent.
  Exact binomial arithmetic gives `p=1/64` for six wins, `1/32` for five wins and
  a tie, `1/16` for four wins and two ties, and `7/64` for five wins/one loss.
  Zero discordances gives 1. This is a coarse screen: nonsignificance cannot
  establish equivalence. Inferential interpretation remains conditional on
  independent conversation signs under the registered comparison and this
  narrow authored setting; six selected domains do not establish generalized
  long-session usefulness.
- Fixed adapter/base identity, matching prompts and caps, source-prefix-only
  inputs, fixed alternating call order, no cache sharing, and separate complete
  evidence are appropriate controls. The generic `validate_corpus/prepare_rows`
  path accepts withheld data, while `preview` expressly requires FIT. A bounded
  new consumer can respect that distinction; broad infrastructure is unnecessary.
- Independent source-grounded label checks and blinded dual judgments are
  appropriate for prose with multiple valid realizations. Material omissions,
  authority/scope/modality errors, unsupported additions, stale rules and bad
  supporting citations measure the intended semantics. Blinded evaluator packets
  must actually conceal arm-revealing execution order as well as explicit model
  labels; verify that implementation before exposing responses.
- The 12/18 plus at-least-one-per-family criterion is a defensible prospective
  spending rule. It permits substantial error and does not demand superiority,
  statistical significance, perfect selection, or perfect manual performance
  before proposing a separately justified fresh worker comparison. It establishes
  none of those broader properties itself.
- The blanket post-look reference-defect invalidation is more conservative than
  needed to report source-grounded observations on unaffected checkpoints. Its
  prospective use is acceptable, but INELIGIBLE must not be reported as evidence
  that no useful behavior occurred. Preserve qualified observations with all
  scheduled cases visible; do not repair gold, shrink the bank, or rescue the
  primary claim after seeing model answers.

Round 1 stops here. Resolve finding `source-semantic#1` in the specification and
return the delta to this same reviewer session. No additional general research,
semantic data authoring, implementation, or experimental evidence is required
to resolve it.

## Round 2 — 2026-09-08

Score: 96/100

Decision: **accepted; zero open high/critical findings.** Finding
`source-semantic#1` is resolved. No new findings or scope expansion.

Same reviewer session, purpose and threat model. Reviewed the narrow delta at
commit `1b940000c4728fd64df38259ada7f931955f59b0`, with SEMANTIC.md SHA256
`d892196fc32ed1e670152dc5904a50bac854d78dda82222f4da95e4c6b2826e5`.
The file bytes match that commit. Before this round's permitted closure marker
and append, the review matched its recorded Round 1 SHA256 exactly.

The new eligibility paragraph requires all 36 scheduled calls returned within
the registered bounds, complete required evidence/cost accounting, and an
eligible bank for **both** primary inference and the practical advancement
decision. INCOMPLETE and INELIGIBLE explicitly block both, including when
partial counts meet the numeric bar. Unknown or unattempted answers cannot be
counted as observed losses; a reduced primary test and partial-result advancement
are expressly prohibited. The earlier conflicting unavailable-as-failure wording
has been removed. Thus Round 1's unattempted final-base counterexample cannot
produce a qualifying sign test or screen pass under the corrected specification.

Normally returned capped/malformed answers still count as observed failures and
do not independently make execution incomplete. The correction therefore binds
decision eligibility to complete evidence without requiring perfect semantic or
structural performance. Qualified partial observations and costs remain
reportable, preserving useful evidence from an honest stopped run.

The only other specification change accurately updates the FIT audit status;
its trained capped failure remains explicit. Candidates, settings, limits,
cost estimate, bank definition, statistical test and 12/18-with-family-coverage
threshold are unchanged. Authoring-plan SHA256 is now
`ed9a0f86a80ac629ee41b35cbedf66243d664988c8dca49f7630f9955c22bda0`;
its only change is the specification binding. All six request files match their
previous committed bytes and registered hashes.

This accepts the corrected prospective specification and unchanged authoring
requests. It does not accept labels that have not yet been authored or qualify
an unimplemented generation consumer for launch. No experiment, model/data call,
network access, code edit, or test suite was performed in this delta review.
