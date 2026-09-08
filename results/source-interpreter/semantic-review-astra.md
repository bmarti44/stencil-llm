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

## Round 3 — 2026-09-08 — authored sources and reference targets

Score: 82/100

Decision: **reference targets require correction before acceptance.** Open
findings: four high (#2–#5), one medium (#6), zero critical. Finding #1 remains
resolved. The new findings concern newly available authored data, not expansion
of the accepted specification review. All six conversations and all 18 targets
have now been read against their exact source prefixes; this is a complete
packet review, not an interim judgment based on the first returned authors.

### Provenance and reviewed packet

The accepted specification remains SHA256
`d892196fc32ed1e670152dc5904a50bac854d78dda82222f4da95e4c6b2826e5`.
Authoring was frozen at `96a99d8c`, with plan SHA256
`86497ce8aebe70db493b5fe8e50e4e28397b57e6d0a3bec5706745a7bc144f9c`.
The six request hashes still match that plan. The completed originals are
archived at `8c28c1d5`.

| Author | Messages | Query message IDs, in order | Authored JSON SHA256 |
| --- | ---: | --- | --- |
| 00 | 12 | m01, m08, m12 | `a49317e828b796973ac35058006b37786ea9182ab51394f78a552ba58f4f0f5e` |
| 01 | 10 | m1, m6, m10 | `898c7da5d44b2b7dd7e5b95e778a0a986f33769f7ba4379b2028334f33fd2468` |
| 02 | 19 | m03, m13, m19 | `d427ea8e72c5922fb6839a3e3d2cab87caf2a1955aada5be342cf4b80973b4dc` |
| 03 | 19 | m01, m10, m19 | `0868058f816feb45af035b8ccead8c4f417d03772d98efe60fa27d3896b89f20` |
| 04 | 40 | msg-11, msg-26, msg-40 | `e1f8352e34ed214970826cd6f3227f5a40940f2152b7912a776171873127d857` |
| 05 | 37 | m11, m25, m37 | `9a9f23c366a5d4d46ee45a466ff057f4e820d192234a6dfadc96d81c7f264c55` |

Every authored document exactly equals the parsed JSON object in its raw Kimi
response; request, response, response-text and authored-file hashes reconcile
with all six completed receipts. The requested alias is `kimi-k3:cloud`; the
raw responses identify their model as `kimi-k3`. All six report HTTP 200,
`done=true`, `done_reason=stop`, and AUTHORED_UNREVIEWED status. No semantic
postprocessing is present in those object comparisons.

Root reported authoritative exec session 55846 terminal with exit 0. The job
receipt is terminal AUTHORED_UNREVIEWED, SHA256
`4ab0530c90cd350148d9c72d15fe9124cce49a5f38f0efd13fc3890de30170d1`,
and owned PID 171095 is absent. Recorded request intervals overlap at most twice,
consistent with the frozen concurrency. Whole authoring cost is
769.2374773590127 seconds. Kimi reports 4,589 prompt and 92,622 completion tokens,
97,211 combined; these are returned service counts, not locally tokenized target
lengths. Root's actual generic structural-consumer receipt, SHA256
`95e7aa1eb5f83c945d867d7b9648294c539bac0eda4042cb7b90bb34240390aa`,
records PASS_STRUCTURE_PROVENANCE_ONLY in 0.022665808 seconds. It explicitly
does not claim semantic acceptance. This review independently checked the raw
bindings without invoking a tokenizer, model, scorer or implementation tests.

### New findings

All query and obligation indices below are **zero-based** and refer to the
unchanged originals in `semantic/author-NN/authored.json`. Corrections must be
authored by Kimi from the frozen sources; the reviewer specifies defects and
scope, not replacement gold prose.

**2. High — Author 02 loses source restrictions in its later targets.**

- Queries 1/m13 and 2/m19, obligation 0: m01 restricts legitimate playlist sources
  to the published on-air page and automation CSV exports. m09 replaces source
  **precedence**, preserving the other baseline rules. Both targets retain
  primary-for-times/display wording and individual private-source bans but omit
  the general exclusivity. A primary source is not the same as the only allowed
  source. Restore the surviving restriction, while retaining the later narrow
  comments/archive permissions and their conditions. Cite the actual originating
  and modifying user messages as needed; no verbatim phrase is required.
- Query 2/m19, obligations 0 and 4: m19 permits archive use for artist aliases
  **for this show**, Crate Digger's Assembly. The same request also reconciles two
  earlier queues. The targets instead describe a task-level archive permission,
  losing the show boundary and potentially extending it to those earlier shows.
  Preserve the named-show restriction as well as the alias-only/no-airing-times
  limits.

These are target omissions with clear source support. Neither requires a source
edit, a new task, or a different interpretation of the earlier task-handle-bound
Subterranean Frequencies exception.

**3. High — Author 04's final target drops the active shorthand definitions.**

Query 2/msg-40, obligation 14, permits the six code tokens but no longer states
which alteration each token denotes. msg-21 specifies HM/hem, TI/take-in,
LO/let-out, SA/strap-adjust, CS/closure-swap and SR/seam-repair. Query 1 preserves
all six mappings; nothing retires them before query 2. Restore those meanings in
the final target while retaining the October 5–8 permission window, full names
outside it, and the stronger full-name requirement for EMERGENCY entries.
The missing mappings are substantive instructions for using the permission,
not a demand to match one particular target wording.

**4. High — Author 05 omits the adopted level-payload interface from all targets.**

Queries 0/m11, 1/m25 and 2/m37: m08 proposes the level payload fields `ts`,
`liters`, `pct`, `raw_mm` and `rssi`; m09 explicitly accepts that payload.
Retained publication is also expressly required in m11. No later message retires
this interface or retention convention. None of the three targets states the
complete adopted field set or retained publication, although the later targets
do carry the additional heavy-inflow and frost fields. Preserve the adopted
base interface and retention in each target, alongside the stage-appropriate
later additions. This is a persistent interface convention, not a requirement
to repeat the current programming algorithm or the assistant's unadopted
implementation choices.

**5. High — Author 05 narrows permission or strengthens obligation modality.**

- Queries 1/m25 and 2/m37: m05 permits tuning filtering **and timing** details.
  m19 refines smoothing discretion with a three-reading floor and repeats the
  alert-threshold approval requirement; it does not revoke all other tuning
  discretion. The targets preserve only smoothing-window permission. Restore
  the surviving general permission with the later specific limits intact,
  including the frost-watch rule, window floor, and threshold sign-off. Do not
  introduce an unrestricted permission that overrides those later directions.
- Query 1/m25, obligation 8: m23 says a plain-text body "is fine". The target's
  categorical delivery "with a plain-text body" turns an acceptable format into
  a requirement. Preserve the permissive modality; Sunday 18:00 delivery and
  the CSV attachment remain required. Query 2's later conditional HTML
  permission from m33 is already represented and must remain intact.

**6. Medium — Author 04 is an operational-documentation conversation, not an
explicit coding discussion as requested.**

The source asks for a written wardrobe protocol, then revisions to versions 2
and 3, and consults an alteration-log store. It never establishes a software
implementation, repository, programming interface or coding task. Calling all
six conversations fictional coding discussions would overstate the authored
packet's match to the accepted specification/request. This is distinct from
requiring executed projects: the other five documents contain explicit software
or firmware work despite also being fictional.

Severity is medium because the document still directly exercises standing
instruction interpretation, has the assigned costume-tracking domain, and
provides valid retirement/reinstatement evidence once #3 is corrected. It does
not compromise paired measurement or require removing a difficult case. Honest
**qualified** acceptance is possible if root prospectively records this
deviation and describes the retained bank as five coding/firmware conversations
plus one operational-documentation conversation, with the same six families,
18 checkpoints, 36 calls, thresholds and cost bounds. The resulting primary
measurement concerns that mixed authored packet; it cannot be presented as six
coding conversations or downstream coding evidence. This is a proposed explicit
qualification, not a silent relaxation or authorization to rewrite/resample the
source. Record its disposition before target-model access.

### Coverage and semantic interpretation

The packet has six distinct scenario realizations, two documents per registered
message band, three ordered queries per document and every final query at the
final message. Only author 00/query 1 has an empty target. Its three project-wide
rules and TideCast carve-out are explicitly retired before the separate overlap
sweep; no retired rule should be resurrected to fill that target. All other
17 checkpoints have substantive standing instructions. Every family contains
meaningful instruction changes across its checkpoints.

Source-grounded features inspected include the ferry retirement/reinstatement
and replacement journal; SeedLedger's approval exception, suspended timing
permission and frost-buffer restriction; radio source precedence, adoption and
task scope; gravel-lens's inert tool suggestions, file/git permissions, adopted
spectral features, changing confidence threshold and scoped naming/rounding;
the wardrobe snapshot retirement/backfill, rental exceptions, shorthand and
post-opening rules; and the tank's changing alert policy, frost hysteresis,
report-only units, buffering and demo-mode exceptions. The confirmed omissions
above are the needed corrections; sources need no semantic rewrite to fix them.

Several targets also restate the current requested task, most visibly all three
author 01 targets. Under the already accepted rule that the current programming
algorithm need not be repeated, these are optional supported restatements, not
additional mandatory standing-focus items. Their absence from a candidate
response cannot be scored as an omission merely because they occur in the
reference. No correction is needed solely to remove them. This applies without
weakening genuine historical standing conventions, permissions or interfaces.

Read scoped clauses and their exceptions together; equivalent grouping is
allowed. Preserve later author 04 no-rewrite/superseding-entry requirements
when interpreting historical corrections or snapshot backfill, rather than
inferring permission to rewrite from the older backfill direction. No source
ambiguity was found that requires rewriting or replacing these conversations.
No old source bank was consulted; the freshness evidence is the frozen
example-free requests, separate authored realizations and preserved provenance,
not a claim of worldwide uniqueness or an empirical proof of independence.

### One bounded correction batch

The complete target-only correction scope is:

| Author | Query indices allowed | Findings |
| --- | --- | --- |
| 02 | 1, 2 | #2 |
| 04 | 2 | #3 |
| 05 | 0, 1, 2 | #4, #5 |

Only Kimi may author those corrections. Keep every message, role, source ID,
task handle, document/family identity, split, query order and nonlisted target
unchanged; preserve all original requests/responses/documents and the complete
correction request/response evidence. Do not simplify other targets, tune for
the output cap, or add a second correction cycle. Return the corrected targets
and the explicit #6 disposition to this same reviewer session for a narrow
verification. This review accepts neither the current defective labels nor a
GPU launch, and does not reopen the training recipe or broader coding claim.
