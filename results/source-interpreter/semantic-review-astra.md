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

**2. High — Author 02 loses source restrictions in its later targets.** (resolved in Round 4, 2026-09-08)

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

**3. High — Author 04's final target drops the active shorthand definitions.** (resolved in Round 4, 2026-09-08)

Query 2/msg-40, obligation 14, permits the six code tokens but no longer states
which alteration each token denotes. msg-21 specifies HM/hem, TI/take-in,
LO/let-out, SA/strap-adjust, CS/closure-swap and SR/seam-repair. Query 1 preserves
all six mappings; nothing retires them before query 2. Restore those meanings in
the final target while retaining the October 5–8 permission window, full names
outside it, and the stronger full-name requirement for EMERGENCY entries.
The missing mappings are substantive instructions for using the permission,
not a demand to match one particular target wording.

**4. High — Author 05 omits the adopted level-payload interface from all targets.** (resolved in Round 4, 2026-09-08)

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

**5. High — Author 05 narrows permission or strengthens obligation modality.** (resolved in Round 4, 2026-09-08)

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
explicit coding discussion as requested.** (deferred with reviewer concurrence in Round 4, 2026-09-08)

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

## Round 4 — 2026-09-08 — corrected-target delta and scope qualification

Score: 96/100

Decision: **qualified source/label acceptance; zero open high/critical
findings.** Findings #2–#5 are resolved, #1 remains resolved, and medium #6
remains an explicitly deferred dataset limitation with reviewer concurrence.
No new findings or additional correction cycle.

The accepted packet consists of the unchanged original authors 00, 01 and 03
from Round 3, plus these corrected full documents under
`semantic/correction-01/author-NN/authored.json`:

| Author | Corrected query indices | Accepted corrected-document SHA256 |
| --- | --- | --- |
| 02 | 1, 2 | `32d097cd35797a407b2c4f16f4413194cadefbe8660efd5dc10b497db1087019` |
| 04 | 2 | `471703e2d13c54a3fe868d20f26ab00b418822bf7c038014a29d1ff5aaac15aa` |
| 05 | 0, 1, 2 | `a02d8909a259568986a9eec3f837b4ee12fabbcf7783002afaf6cfd88e7c6d9c` |

The correction plan was frozen at `e962c5ac`, SHA256
`e799abbdffac2732dc1c02e0192748e1db14f063e7ae06fd1912a18bb1b75f46`.
All three request bytes match that commit and manifest, quote their relevant
Round 3 findings verbatim, and embed the complete corresponding original JSON
object without changes. No root- or reviewer-authored replacement target was
supplied. The returned corrections are archived at `2167571d`.

Root reported exact session 22398 terminal with exit 0. Independently read
terminal CORRECTED_UNREVIEWED job receipt SHA256
`a27f7f931e5977fc42bc4ddaf93bd550900feb944dfa9a8146d4a5725ece8159`;
owned PID 176629 is absent. All three immutable-source guards pass. Independent
standard-library comparisons reproduce the guards: every original document file
is unchanged; corrected documents preserve all source messages, metadata,
query IDs and order; exactly six allowed target objects differ and the other
twelve targets across the packet remain identical. Each corrected object equals
the parsed raw Kimi response, and every request/response/response-text/document
hash reconciles. Guard objects also agree with the terminal job record. Root's
separate reconciliation SHA256
`a6627dcf7bd045c837d190f889aace3653aa530795d7c7e447d84760f7ffc0fe`
agrees with these checks and correctly labels itself provenance-only.

The one correction batch cost 278.22715863899793 seconds with at most two
overlapping recorded requests. Returned service counts total 17,734 prompt plus
23,463 completion tokens, 41,197 combined. Original authoring plus correction
therefore totals 1,047.4646359980106 seconds and 138,408 reported service tokens;
review and orchestration costs are additional. No target-model or tokenizer
measurement is inferred from these service counts.

### Verified closures

- **#2 resolved:** radio query 1 now retains the two-source playlist restriction,
  the replacement timing/display precedence, and the narrow comments permission.
  Query 2 retains the same baseline restriction and explicitly limits archive
  aliases to Crate Digger's Assembly, excluding the two earlier queues and airing
  times. Other target items and the source remain unchanged.
- **#3 resolved:** the costume document's final target restores all six code/name
  mappings from msg-21. The October 5–8 window, full names outside it, and the
  unchanged stronger EMERGENCY naming condition remain intact. Only that
  obligation changed in the final target.
- **#4 resolved:** every sensor target now includes the adopted `ts`, `liters`,
  `pct`, `raw_mm`, `rssi` level interface and retained publication, grounded in
  m08/m09 and m11. Later targets preserve the existing separately grounded
  heavy-inflow and frost additions rather than replacing the base interface.
- **#5 resolved:** sensor queries 1 and 2 restore filtering/timing discretion
  with the later restrictions, including the smoothing floor, threshold
  sign-off and frost cadence. Query 1 now expressly treats plain text as
  permitted, while retaining the Sunday delivery and CSV obligations. Query 2's
  later conditional HTML permission remains unchanged. No material regression
  was found in the changed targets.

### Qualification and interpretation retained

I concur with the prospective #6 disposition in `semantic/PREPARATION.md`.
The frozen qualification SHA256 is
`623e9b8737adc6f4def880adc0d591a23421a3c5446be92da8ad755875798a2f`,
verified against its `e962c5ac` Git blob. The current file, SHA256
`fd2d6bb80daa108497d4739bb1bd1792fd0ee5865ac003e52cecd038e1403d5c`,
preserves that entire text and adds only a post-terminal execution/cost record.
This is an intact historical launch binding, not a requirement that the live
report never acquire an explicitly identified execution appendix.

The accepted bank is **five fictional coding/firmware conversations plus one
operational-documentation conversation**, retaining all six families, eighteen
checkpoints and thirty-six planned calls. All settings, candidates, thresholds,
inferential rules and cost bounds remain unchanged. The eventual primary
measurement is limited to this mixed authored packet. Acceptance does not turn
author 04 into a coding example or supply code correctness, manual-prose parity,
or adequate larger coding evidence.

The existing interpretation of supported current-task restatements remains:
they are optional when they merely repeat the current programming request;
their omission alone is not a standing-focus defect. Historical interface
conventions, applicability, permissions and exceptions remain required. No
exact-wording criterion or new scoring rule is introduced by this qualification.

This closes the single permitted label-correction stage. CPU preparation and
implementation qualification may use exactly the accepted packet above, under
their existing scope. This review performed no tokenizer/model/GPU operation,
code edit, test suite or scorer invocation and grants no inference launch by
itself. Source/label acceptance is not evidence of helper performance or the
broader project's success.

## Round 5 — 2026-09-08 — stable implementation review

Score: 86/100

Decision: **changes required; two open high findings, zero critical.** New
findings #7 and #8 block implementation acceptance. New #9 is medium. Findings
#1–#5 remain resolved; #6 remains deferred with the Round 4 mixed-packet
qualification. Source/label acceptance and the single completed correction
batch are unchanged.

Reviewed the stable Sol implementation through
`50ed563e2457924239f0d52a8f718773addf2aba`, including initial `81dd4252`, with
the accepted canonical copies committed separately at `284d53ca`. Exact bytes:

| Artifact | SHA256 |
| --- | --- |
| `scripts/source_interpreter_semantic.py` | `2e34c7d78f2fec1bc256aaf5e07c432a7722f8c297556686156eb13829b0d154` |
| `tests/test_source_interpreter_semantic.py` | `db53b6c9064ed793896ee45bb0c17f809a3495ccf4557235ef9c58baeebfaf7d` |
| `SEMANTIC-CODE-BRIEF.md` | `2d80b13932434c053eaeb17169e0fdac4f126f47ed0525b6787c6e5a7a738222` |
| Accepted `SEMANTIC.md` | `d892196fc32ed1e670152dc5904a50bac854d78dda82222f4da95e4c6b2826e5` |
| This review through Round 4, before this appendix | `ab90cf6f282961b16521ce4a6f3648f9fd74ee713a1e394d92feec414996c859` |

### Findings

**7. High — The actual original base assets are not verified against their
recorded bytes before model loading.** (resolved in Round 6, 2026-09-08)

Evidence: `qualify_static` (lines 185–240) binds the `base-assets.json` receipt,
but never checks the thirteen actual files described by that receipt.
`run_child` verifies adapter files at line 1242 and loads `MODEL_PATH` at
lines 1263–1271. Its later `capture_parameter_state` and
`validate_frozen_originals` establish that whatever original tensors were loaded
remain unchanged within the job. They do not connect those tensors to the
previously verified original base files. The loaded tokenizer-state comparison
also does not identify the model weight shards. The existing FIT consumer's
`validate_artifacts(verify_base_files=True)` explicitly performs the missing
file checks; the semantic consumer does not call that path or an equivalent.

Consequently ordinary accidental replacement or corruption of a local base
asset, including a same-size change, is not rejected by this identity check.
The resulting comparison could still be marked complete while its claimed
original-base lineage is unverified. This is a required scientific identity
check, not a hostile filesystem-race requirement.

Required correction: in the explicit execution path, verify the required
original assets against the frozen receipt's exact sizes and SHA256 values
before loading the model, retain the evidence, and satisfy the brief's
before/after file-identity check alongside the existing in-memory invariance
check. Account for this work within the existing startup/whole-job bounds.
Keep static/dry qualification free of actual weight reads. A small reused or
local helper is sufficient; do not load labels or unrelated FIT artifacts to
obtain this check. Exercise the actual verification consumer with a synthetic
same-size altered asset and confirm rejection before model loading.

**8. High — Final per-call record publication can exceed the call deadline
and still pass complete-execution validation.** (resolved in Round 6, 2026-09-08;
new interrupted-confirmation regression recorded separately as medium #10)

Evidence: `run_inference_schedule` checks the root stage publication against
the hard deadline at lines 925–940, then builds and durably writes
`call-NN.json` at line 966. It does not check elapsed time after this final
per-call write. `validate_complete_calls` (lines 774–810) checks the returned
nested receipt and its earlier stop facts, but has no confirmation that the
final semantic call record itself was published within the deadline.

I reproduced this through the actual schedule, existing synthetic model/tokenizer
fixtures, actual FIT single-call consumer, and actual complete-call validator.
With a one-second injected call clock, delaying the final RETURNED write for
`call-00.json` to time 1.01 produced:

- first call hard deadline: 1.0;
- first final call record published: 1.01;
- schedule result: COMPLETE, 36 returned calls;
- `validate_complete_calls`: accepted all 36 calls.

Only the in-process clock/writer and synthetic fixtures were substituted;
this created no real model calls or packet preparation. The existing root stage
correctly remains COMPLETION_PENDING while that write occurs. That watchdog
is useful, but its polling can miss a short deadline overrun followed by the
next INTENT, so it does not repair the demonstrated acceptance path. A final
call can similarly finish its publication late while still leaving time in the
whole-job allowance.

Required correction: include final semantic call-record publication in the
actual per-call completion protocol and require its timely confirmation in the
complete-result consumer. An overrun or unavailable final confirmation must
stop further calls and block both eligibility flags, while retaining any known
raw bytes, IDs, counts and timings. Use the existing pending-stage/watchdog and
bounded publication machinery; no new timing framework or extra model call is
needed. Add a negative regression through the real schedule and complete-result
consumer for this publication delay, including the final scheduled call.

**9. Medium — Loaded adapter payload identity is checked only against its own
initial state, not against the frozen serialized payloads.** (resolved in
Round 6, 2026-09-08)

Evidence: `_verify_adapter_files` correctly checks both archived parts and the
standard adapter file's exact hash, and `PeftModel.from_pretrained` loads the
specified local adapter. These provide meaningful provenance. After loading,
lines 1283–1294 check only 144 tensors, 2,949,120 elements and FP32 dtype. The
later `compare_adapter_states(state, after_state)` verifies within-job equality
with that initial loaded state. No comparison establishes that all loaded
keys, shapes and tensor values equal the verified serialized adapter payloads.

This is narrower than #7: the adapter source bytes are actually verified, and
there is no evidence that the native PEFT loader loaded a wrong adapter. The
remaining gap is in the brief's requested complete loaded-payload identity
verification. A matching count/dtype plus self-comparison does not itself
measure that identity.

Correction: inside the already authorized model-loading path, compare the
loaded adapter state against the exact verified serialized state, including
keys, shapes, dtypes and tensor values or hashes, and retain that result before
the first generation. A small mismatch regression at that actual comparison
boundary is sufficient. Do not add another adapter candidate, run or generic
serialization framework.

### Verified behavior and limits

Independent targeted verification: `tests/test_source_interpreter_semantic.py`
passed **8 tests in 8.97 seconds**. Ruff check and format check passed, and
`git diff --check` was clean for the reviewed implementation. The targeted suite
covers direct absolute invocation from `/tmp` with PYTHONPATH unset, default
dry mode and artifact-only qualification, import without heavy modules,
synthetic preparation, fixed 36-call order, native FIT generation plumbing,
ordinary returned cap/invalid continuation, technical-stop accounting,
incomplete-result rejection, and owned-child timeout/cleanup behavior. No full
suite was run.

The target-free generation manifest is produced from an explicit row whitelist;
reference text and target token IDs are written separately. The actual child
reads the generation manifest and does not reopen source documents or the
reference manifest. Unique row directories prevent the FIT consumer's fixed
mode filenames from overwriting earlier pairs. The actual FIT call consumer
uses the fixed native generation settings, checks active adapter state, clears
cache, records complete IDs and decoded bytes, and uses one model trunk across
the fixed alternating modes. Returning malformed or capped output remains an
observed return; technical incompleteness leaves later calls unattempted and
blocks the normal complete path, subject to the publication defect above.

The two root-identified pre-handoff corrections are verified. If nested raw
output exists but final call publication is unavailable, `partial_call_records`
retains known output provenance, ID count, byte count and timing without
promoting the call to RETURNED or confirming its deadline. The targeted
regression passes through this actual recovery consumer. Preparation's canonical
review binding is resolved only through the recorded `preparation_git_head`
Git blob; other bindings retain current-byte validation. In an additional
synthetic actual-consumer check, an appended live review was accepted with the
correct historical bytes, incorrect historical review bytes were rejected, and
changed current implementation bytes were rejected. The current launch review
remains a separate required freeze binding.

The observer contract exposes startup 660 seconds, per-generation 300 seconds,
whole publication/exit 3600 seconds, and a final 15-second cleanup reserve.
The owned-child supervisor monitors pending stage deadlines and records unknown
partial results and cleanup failures honestly. The independent outer observer
is still required to establish final supervisor publication, process exit and
owned-group absence; this code audit is not the later frozen-launch audit.

No source/target reauthoring, actual packet tokenization, original/adapter weight
read, model/GPU call, scorer, old-bank access, network operation, code edit or
commit was performed by this reviewer. Fix #7/#8 before implementation
acceptance; preserve the accepted data and registered settings. The small
identity correction for #9 can accompany them without changing the experiment.
Actual CPU preparation, its preview audit and final launch freeze remain future
steps. This review grants no model execution authority or performance claim.

## Round 6 — 2026-09-08 — identity and publication correction delta

Score: 94/100

Decision: **qualified implementation acceptance; zero open high/critical
findings.** Findings #7–#9 are resolved. A new medium #10 records incorrect
partial evidence after an interrupted confirmation; it is deferred with the
specific reporting restriction and reviewer concurrence below. Findings #1–#5
remain resolved and #6 remains deferred under the
explicit five-coding/firmware plus one operational-documentation qualification.
The review threshold is met, but this is neither model-launch acceptance nor
evidence that the helper performs well.

Reviewed stable Sol commit `1327643ec4edcafdcf85a279870da13d6db66dc9` against
the Round 5 bytes, under `SEMANTIC-FIX-BRIEF.md` SHA256
`69588e4b9010d3897055c550d4b1528f10159dad1c811bd9aa17f60ed1189974`.
The implementation and test hashes independently match the handoff:

| Artifact | SHA256 |
| --- | --- |
| `scripts/source_interpreter_semantic.py` | `3c6b5d71dc0e33542cbd188bff6b939cf40185d086bf8f65671c18652f409348` |
| `tests/test_source_interpreter_semantic.py` | `10a95f304fd22ac3a894e0baa27d8ee18b1afed7cfd2041d8cafa2414143029d` |
| Canonical review before this round | `c62300ff211bb2aabac0d9b134b9f839990412617e27192ab38aedef98afe70f` |

### Verified closures

- **#7 resolved:** `verify_current_base_assets` reads every entry in the frozen
  asset receipt, checks current size and SHA256, requires the historical-original
  flag, and reconciles file count and total bytes. The actual child calls it
  before ML imports/model loading and after generation, retaining both receipts
  in files and the final result. The existing frozen-receipt binding and
  in-memory original-tensor invariance remain in place. Startup/whole supervision
  still covers this work. Static qualification does not call the weight-reading
  helper. The synthetic same-size altered-file regression rejects the mismatch
  through the actual verification helper.
- **#8 resolved for the original normal-execution defect:** the final semantic
  call record is now COMPLETION_PENDING and is published before a unique
  hash-bound completion confirmation. The schedule checks publication after
  both the call record and confirmation writes, stops on a late write, and
  retains the active watchdog until the next stage. Actual schedule/FIT-call
  regressions delay ordinal 0 and ordinal 35 call records past their deadlines:
  both stop immediately, keep known raw output as UNAVAILABLE, and fail complete
  validation. A delayed confirmation also stops. Deleting the final confirmation
  from an otherwise complete synthetic schedule makes the final call UNAVAILABLE
  and complete validation reject it. The former path that normally returned
  COMPLETE and advanced after a late final call-record write is closed.
- **#9 resolved:** after native PEFT loading, the actual child reads the already
  hash-verified standard safetensors payload into CPU state and compares it with
  the loaded adapter via `compare_adapter_states`. Keys, shapes, dtypes and
  exact tensor byte hashes must agree before the first generation. The retained
  receipt includes per-tensor evidence; the existing 144-tensor/2,949,120-element
  checks and exact before/after invariance remain. A same-shape, same-dtype,
  different-value CPU tensor fails the actual comparison boundary; matching
  values pass. This review did not read the real serialized adapter.

### New regression introduced by the publication correction

**10. Medium — Interrupted confirmation publication can promote provisional
evidence to a timely RETURNED call in partial records.** (deferred in Round 6,
2026-09-08, with the reporting restriction and reviewer concurrence below)

Evidence: `_publish_call_completion` writes COMPLETE with
`completion_records_within_deadline=true` before its last publication clock
check (lines 835–850). A later check normally detects an overrun and writes
DEADLINE, as the new passing regressions demonstrate. If publication or its
following history append raises after the provisional bytes exist, or the child
is stopped there, that downgrade cannot occur. `_confirmed_call_status` then
accepts the provisional confirmation without evidence that execution passed the
last clock check. The root stage is still COMPLETION_PENDING.

Independent synthetic reproduction used the actual schedule, actual FIT
single-call consumer and existing fake model/tokenizer primitives. The final
`call-35-completion.json` confirmation containing the observed-time fields was
written, the injected clock advanced to 1.01 against a 1.0 deadline, and the
writer raised OSError before returning. The schedule propagated that error.
Nevertheless, `partial_call_records` reported all 36 calls RETURNED, with the
last call's `completion_publication_confirmed` and `within_deadline_confirmed`
both true; `validate_complete_calls` accepted all 36. Root independently
reproduced the same result. No real packet or model call was involved.

Severity is medium because the actual child exception or watchdog termination
still forces an incomplete execution, and the supervisor keeps both inference
and advancement eligibility false. This is not the Round 5 normal complete-run
bypass. The remaining harm is false certainty in partial timing/completion
evidence and acceptance by the standalone complete-call validator.

Bounded correction: use existing execution progress beyond the pending call
(the next INTENT or existing post-generation-validation transition), or
equivalent existing supervision evidence, to distinguish a confirmation whose
final check returned from one interrupted while publication was pending. Keep
the interrupted active call UNAVAILABLE, retaining its known output, counts and
timing. Add the demonstrated late-write-then-interruption case through the real
partial/complete consumers. Another chain of self-confirming receipt writes is
unnecessary. No new model call, source change, timing allowance or framework is
requested.

Disposition: I read and concur with the concrete deferral in
`semantic/PREPARATION.md`, section “Bounded disposition of
interrupted-confirmation residual,” committed at `9d426217`. For an interrupted
or INCOMPLETE run, root will treat the active pending call's completion/deadline
as UNKNOWN unless existing later-INTENT or post-generation evidence establishes
advancement beyond it. Provisional RETURNED/timely flags are not authoritative
for that call. Preserve every original receipt and all known raw output/cost
facts; do not repair evidence, infer unknown outcomes, run primary inference or
advance from an incomplete screen. A COMPLETE claim requires successful actual
child, supervisor and outer observation, never the standalone call validator
alone. This restriction addresses the remaining scientific consequence without
claiming to fix the code defect or changing a threshold. Given the verified
whole-run failure behavior, deferring this medium defect for this one-shot
screen passes the burden test; another implementation cycle is not required.

### Verification and scope

Independent targeted suite: **13 passed in 14.89 seconds**. This includes the
five newly passing cases (first/final publication are separate parameter cases)
plus the previous target-separation, ordinary capped-return continuation,
native-generation plumbing, owned-child timeout/cleanup, partial raw-output
recovery and direct `/tmp` invocation checks. Ruff check, format check and
delta whitespace check passed. The additional interrupted-confirmation
reproduction is the failing behavior documented as #10, not a passing test.

The optional `semantic/ASSESSMENT.md` conformity read found no new metric or
changed threshold. It preserves independent blinded source-authoritative
judgments, optional immediate-task restatement, unknown unattempted work,
unsalvaged invalid output, preserved original votes, whole-screen ineligibility
for post-look reference defects, six-conversation sign inference, and the
separate 12/18 plus one-per-family practical screen. I did not open the private
response map or any model response. The mixed-packet limitation remains explicit.

No actual withheld source/target read, packet tokenization, original/adapter
weight read, model/GPU execution, network access, full suite, frozen-helper
modification, code edit or commit was performed. Only this canonical review is
written. Actual CPU preparation and its audit remain later steps; any subsequent
bounded correction needs its own stable delta verification. This round makes no
semantic-performance or larger coding-utility claim.

## Round 7 — 2026-09-08 — actual CPU preparation audit

Score: 96/100

Decision: **actual prepared packet accepted; zero open high/critical findings
and no new findings.** Previous closures remain intact. Medium #6 remains the
explicit mixed-packet limitation; medium #10 remains deferred with its
interrupted-call reporting restriction. This accepts the exact preparation
artifacts for root's final launch freeze, not an inference result or the broader
coding-utility goal.

The actual preparation was frozen at
`820cf276448f90e8414dd911c7c33b5231d6d905` and archived at `40986a5c`.
Independently read the actual job/stdout/stderr/root-check records, latest
PREPARATION addendum, canonical accepted inputs, all six accepted documents,
both prepared manifests, and the relevant native tokenizer/template consumer.
Exact artifact bindings:

| Artifact | Bytes | SHA256 |
| --- | ---: | --- |
| `semantic/accepted-inputs.json` | 2856 | `fe2c1356f1f2abb5a6b70f83c638008c240e8bff4c8824e5064cd82c8ac2e8f7` |
| `semantic/prepared/generation-manifest.json` | 562048 | `7f29793be4407c7db47eecf133a2efb696356c081e49044f2a430d296b6d47e3` |
| `semantic/prepared/reference-manifest.json` | 279755 | `9293858334b7cbcb1f6af5377f490ab8b9fe07260d7e041afa9b79b55d2aea5b` |
| `semantic/preparation-job.json` | 1204 | `62b5136e5f15de24eb8ae1fb8d0866d75519bb23c86687818839933cf3315bdd` |
| `semantic/preparation-root-check.json` | 3905 | `14465a3c49c47635cdf49628a47f2df4b6c9f76fcb17b00308efd4ce1a3ace13` |

### Actual data and encoding checks

Independent read-only validation passed through the actual
`validate_generation_manifest` consumer and checked accepted-input/corpus
identity. All six canonical document files equal their accepted `284d53ca`
Git blobs byte-for-byte. Every input receipt matches its document's current
size, SHA256, withheld conversation/family identity and successful parse status.
Exactly eighteen rows remain, three queries per family, with each final query
at its document's final message. The sole empty reference remains author 00,
query index 1. No source, target, row, ordering or applicability label changed.

For every row, I independently selected the accepted messages through the query
ID, serialized that exact prefix and current task handle into the frozen
system/user prompt, and applied the local native chat template with
`add_generation_prompt=True` and `enable_thinking=False`. Direct native template
tokenization and separate encoding of the rendered template with
`add_special_tokens=False` both exactly equal the stored prefix token IDs.
Decoding reproduces the full rendered prefix. Visible source IDs, query IDs,
task handles, row identity, source-prefix hash and prefix-ID hash all reconcile.
No future message or reference target enters the constructed generation prompt.

Every separate reference is exactly the canonical serialization of its accepted
target, with identical native token IDs, decoded text and text hash. Each adds
one EOS 151645, and no target token before that EOS is a reserved control ID.
Reference identity, target/full lengths and query correspondence agree with
generation rows. The generation manifest's exact schema contains source/prefix
material and metadata, while target text and target IDs remain in the separate
reference manifest. The already reviewed inference child consumes only the
generation manifest.

The freshly loaded CPU tokenizer state equals the recorded state, including
backend/template hashes, token vocabulary, added/control-token properties and
EOS/PAD values. All six tokenizer/config asset hashes match the verified
original asset receipt. This checked tokenizer assets only, not model weights.
The manifest's interpreter/virtual-environment paths and installed package
versions pass the actual environment validator. Generation settings remain
identical to the fixed FIT generation settings, including greedy decoding,
2048 new-token allowance and EOS/PAD 151645/151643. The fixed alternating order
still schedules exactly eighteen base and eighteen adapter calls.

Recomputed length ranges are prefix **315–4059** and reference including EOS
**7–1005**. The largest prefix plus the unchanged 2048 output allowance is
**6107**, below **32768**. All eighteen individual rows match root's reported
length table. These reference lengths are descriptive and neither guarantee
that generated answers fit the cap nor justify changing it.

### Provenance, cost and launch interface

Every preparation binding matches the exact recorded preparation Git snapshot.
In particular, the review binding resolves to Round 6 SHA256
`ec917ecc069a70e8a84f52b8853c96ae8beef0708e0113bb172aa488f988e0e8`
at that snapshot. Current non-review bindings also pass the real generation
consumer. Appending this Round 7 review does not require regenerating either
manifest or changing accepted inputs: the historical preparation review remains
fixed, and the current launch review is bound separately.

The actual command used the canonical absolute `--prepare` paths from `/tmp`
with PYTHONPATH unset. The terminal receipt records exit 0 and owner/child PIDs
189230/189232; both are absent. Exact stdout/stderr byte/hash receipts match,
stderr is empty, and stdout reports PASS, six documents, eighteen rows,
thirty-six scheduled calls, no model loaded and no GPU use. Monotonic endpoint
subtraction independently reproduces the recorded outer preparation cost
**3.645484035 seconds**. The inspected execution branch loads only the tokenizer
and prepares manifests; no generation branch is invoked.

The independent read-only encoding/provenance audit took **3.026325929 seconds**
after audit imports, separately from the actual preparation's outer interval.
It did not call `prepare_packet`/`--prepare` again or write any prepared artifact.
This is verification cost, not a second preparation run or model measurement.

Also checked draft launch plan SHA256
`2cbdb5d54c8bd3ae90ac0969dacf2f59814b93fee7c5a0eef6cb7625f159b57e`
against its `32c9d0bf` Git blob. The command points to the exact generation
manifest and fresh run-01 path; settings/order match the actual manifest.
The required outer observer retains startup 660 seconds and whole publication/
exit 3600 seconds; the bound implementation retains generation 300 seconds
and the final 15-second cleanup reserve. All 26 nonprivate binding contents
reconcile. The private response map was excluded from reading/hash verification;
its inert advertised binding was visible in the plan, but its contents were not
opened. The draft explicitly carries #6/#10 reporting qualifications and
remains marked nonexecuting pending this audit. Root's final freeze must bind
the current completed review and any acceptance-only report addendum while
preserving code, data, prepared manifests, settings and limits.

The preparation report accurately distinguishes authoring cost, actual CPU
preparation, and still-unmeasured model performance. No original/adapter weight
read, model/GPU operation, generation, network access, old-bank/FIT-target
access, private-map access, full suite, code edit or commit was performed in
this audit. Only this canonical review is written. The accepted packet remains
a qualified fresh instruction-reading screen; larger executable coding utility
is still unproven.

## Round 8 — 2026-09-08 — actual execution and evidence audit

Score: 96/100

Decision: **execution accepted; zero open high/critical findings and no new
findings.** All 36 registered calls completed within the actual supervised
bounds with the required evidence. This establishes execution eligibility for
the separate semantic assessment; it does not establish semantic correctness,
learning improvement, practical advancement or coding utility. Prior closures
and deferred qualifications #6/#10 remain unchanged.

The single model job is terminal: exact session 16331, exit 0, frozen launch
commit `2d016c8d94d20559e943bb067a7c9d7b7f1f75b8`, archived at
`123a7dea522fa5327d5ec8d29f942ae39ab89ecd`. No restart or additional model
call was made for this audit. Reviewed exact artifact hashes:

| Artifact | SHA256 |
| --- | --- |
| `semantic/RESULTS.md`, execution-only version | `a1f8d58122a212e151a936b41b6dfa4d2ba666370c62f886fdc8637353e821a7` |
| `semantic/execution-root-check.json` | `35b94bf843d4fdf76edfcf7444255d87b2ed61958c3549e66851baa9212db01e` |
| `semantic/execution-archive.json` | `10db1293155adf2c924cbbfd06a8bb1a1c907b3f34e316fce5c0fb79b8f44e77` |
| `semantic/observer-run-01.json` | `f0e1605a3ceb8f16a93ab8375645debc27b052a76a65fe14977234ba3e019c45` |
| `semantic/run-01/result.json` | `6ab37b6994497e5e0b4a73eaf961587c57370a17bfafd9f1196696b470a1a5e6` |
| `semantic/run-01/lifecycle.json` | `7357fe3a2bfea2d2795a6f3146ba3ed7164a182746e49e52c2ed1ee58743b808` |

### Actual invocation, lineage and byte evidence

The actual generation-manifest and complete-call consumers pass. The derived
36 call records agree exactly across the child result, supervisor lifecycle
and outer observer's captured lifecycle. Fixed order, conversation/query
identity and eighteen calls per mode match the frozen generation manifest.
Every raw output preserves its exact prepared prefix followed by the recorded
generated IDs. These are the source-only prefix IDs accepted in Round 7;
their manifest and all accepted source/reference bindings remain unchanged.
No target or label was supplied to generation, and the child command reads only
the generation manifest. The frozen consumer runs native `model.generate`
under inference mode using a causal model loaded once, with no training path.

All 36 receipts record fresh cache and no supplied past-key-values. Each records
the same original trunk object identity. Every call's 72 adapter-layer records
show the required mode: disabled for base, enabled with only the named semantic
adapter for the trained arm. Explicit generation/config/forward/control
arguments match their frozen values. Native resolved configurations are equal
across calls except for the prefix-dependent maximum total length, which is
always prefix length plus 2048. The effective settings are greedy, one beam,
one returned sequence, EOS 151645, PAD 151643 and the fixed cap. Inherited
sampling defaults are recorded separately and do not override those settings.
The child stderr's inactive `top_k` warning is consistent with the recorded
greedy configuration; the remainder is weight-loading progress, with no error
or traceback. Child stdout is empty and the outer job log agrees with the
terminal observer status, PID, exit code and elapsed time.

Using only the local CPU tokenizer, I independently decoded all 36 payload-ID
sequences without special-token removal or cleanup. Every decoded string,
UTF-8 byte count, base64 payload and SHA256 matches the raw receipt. Generated
counts, terminal EOS, cap facts and complete-output concatenation reconcile.
The actual structural validator reproduces each recorded structural result
against its visible source IDs. No semantic judgment was made from an answer's
content, and no invalid prefix was salvaged.

The archive contains exactly 197 run files and three accompanying records,
200 files totaling 3,347,585 bytes. Every archived file matches its inventory
size/hash and its exact `123a7dea` Git blob, and every run file is represented.
All are below the archive size limit. The launch plan matches SHA256
`7fc43957aec44fa469eb2a7f679d19eb22d41c04a36f101ff5f916533b6a7767`.
I independently reconciled all 26 nonprivate launch bindings against current
bytes and the frozen launch commit. The private response-map binding was
intentionally excluded from my reads; root's 27-binding check and the actual
outer launch consumer cover it. The map itself remains unopened by this reviewer.

### Original and trained state identity

The 398 nonempty original-parameter endpoint hash entries agree exactly before
and after generation, representing 4,022,468,096 original parameters. The
recorded unchanged identity/bytes and absent-gradient checks pass through the
bound actual consumer. Both 13-file original-asset receipts match the frozen
inventory's exact names, sizes, hashes and total bytes, and agree with their
separately retained before-load/after-generation files. This audit checked the
recorded base-file evidence; it did not reread the original model weight shards.

For the small final adapter I independently read the permitted serialized
checkpoint and both archived parts on CPU. Their exact sizes and hashes match
the frozen candidate. Parsing the safetensors header and raw payload offsets
reconciles all 144 keys, shapes, FP32 dtypes and tensor byte hashes with the
loaded-versus-serialized receipt. Payload ranges cover the serialized data
exactly, totaling 2,949,120 parameters. That receipt is identical to the one
embedded in the actual result; before/after file verification and exact
in-memory adapter-state comparison are also recorded as passing. No model was
loaded to perform these independent byte checks.

### Deadlines, completion and costs

All root call confirmations and nested generation completion stages are timely.
For every call, I additionally checked a subsequent root generation INTENT, or
the final post-generation-validation INTENT, occurring after its confirmation
and before that call's 300-second deadline. The maximum interval from a call's
start through this later transition is **120.630158095 seconds**. This provides
positive execution-advancement evidence for every confirmation, so the deferred
interrupted-publication defect #10 is not used to infer completion here. The
stored call files remain their original COMPLETION_PENDING records; confirmed
RETURNED status is derived from the complete normal execution evidence.

Outer first-generation observation occurred at **75.898010935 seconds**, within
the 660-second startup bound. The successful child exit and cleanup precede
the supervisor's working deadline. The outer observer then establishes final
supervisor publication/exit and owned-group absence within 3600 seconds.
Independent endpoint subtraction reproduces **1651.235740360 seconds** for the
inner supervisor and **1651.404385013 seconds** for the outer interval. No
timeout, technical-error receipt, failure file or remaining run flag exists.
Observer 191765, supervisor 191766 and child 192119 are absent, and independent
`/proc` inspection finds no process remaining in owned group 191766.

Recomputed structural and cost results match the execution report:

| Measurement | Base | Adapter |
| --- | ---: | ---: |
| Returned calls | 18 | 18 |
| Structurally complete | 14 | 12 |
| Capped returns | 1 | 6 |
| Terminal-EOS returns | 17 | 12 |
| Generated tokens | 8851 | 18082 |
| Sum of measured generation-call seconds | 499.459512878 | 1040.675853677 |
| Longest measured generation-call seconds | 120.495669269 | 118.598697457 |

The call-time sums describe the measured native generation intervals; outer
elapsed time also includes loading, verification, publication and cleanup.
Recorded peak Torch allocation is 9,013,965,824 bytes and peak reservation is
9,741,271,040 bytes on GB10 unified memory, matching the report's qualified
allocator accounting. These are not independent dedicated-device memory pools.
Root's reconciliation cost remains a separate reported 0.048363473 seconds.
This independent CPU byte/consumer/decode audit took 2.518727527 seconds after
imports; it is additional verification cost, not model execution time.

The report correctly leaves semantic votes, inference and the practical screen
undetermined. The trained arm's twelve structurally complete outputs supply
only an upper bound of twelve semantic successes; structural validity cannot
establish the required source-grounded correctness. The packet remains five
coding/firmware families plus one operational-documentation family. Separate
blinded Astra/Kimi assessment and any source-grounded adjudication remain
necessary; no reference repair, tuning, retry or reduced bank is implied.

Only this canonical review was written. No model/GPU execution, training,
generation, re-preparation, new data, network operation, old-bank/FIT-target
access, private-map access, unchanged full suite, code edit or commit was
performed. Execution acceptance supplies no broader coding-utility proof.

## Round 9 — 2026-09-08 — final reporting and registered stop

Score: 96/100

Decision: **final report and stop disposition accepted; zero open
high/critical reporting findings. The semantic screen is INELIGIBLE.** The
reference defect remains in the archived bank. This review does not repair it,
reclassify the bank as valid, score a reduced bank, or authorize advancement.
Prior implementation/execution closures and the #6/#10 qualifications remain
preserved. The present candidate stops without a primary inference or practical
screen score; larger coding utility and the project goal remain unproven.

Reviewed the stable terminal adjudication/report at `5c644a66`, the frozen
original judgments at `a951212e`, the final record check, relevant actual source
evidence, and the new README Project status paragraph. During this round root
prepended a current-status banner to RESULTS and labeled the earlier narrative
as historical. I verified that the entire preceding `5c644a66` report remains
byte-for-byte intact below that banner. This removes the misleading entry-point
impression that judging is still pending, without altering the historical record.
Exact reviewed hashes:

| Artifact | SHA256 |
| --- | --- |
| `semantic/RESULTS.md`, with current-status banner | `f7e5ecae2adba9c7a93f070a4ab330bd11d4af9c7475b5aa09988be35f97692c` |
| Original `semantic/assessment-astra.json` | `4cd37fcac61634e1ac73e1b3b930c26b28b99b09945c5426e21b31e47d434f06` |
| Separate `semantic/assessment-astra-adjudication.json` | `d71b14dea823516ff2e26b8c139b164ab7e0c46e61db34fa455fd55ed556ce50` |
| `semantic/assessment-final-check.json` | `a35a9d4e984f7965a9a75c9d4380b27642da25c31e41b38ec3aeb610800862dd` |
| `semantic/judgment-archive.json` | `615ba69beb7cc19130656ebaf279849b827a88e6ea59de5380b973c66f432145` |
| `semantic/kimi-assessment/judgment-job.json` | `c30c5863d784163f32e631f07c003e072e970e02da0e54df50304a53ad66c59e` |
| `README.md` | `c441e9f10de45035d294f1db2e9f5f6c031d9e4fc178123bfb4193fc07705162` |

### Escaped reference defect and eligibility

I independently read the complete radio source and accepted final-query target.
The source is clear: m13 permits the public comments inbox for Midday
substitution-announcement confirmation, prohibits quoting commenter names, and
requires ignoring an entire comment that mentions donor status. The subsequent
m15/m17 changes concern ambiguity and thank-you treatment; neither retires that
permission. At m19, reconciliation explicitly revisits the two prior queues
under current rules. The Midday-scoped permission therefore remains relevant to
that queue, without extending to the new weekend show.

The final reference instead says the archive is the only additional permitted
source and confines both earlier queues to standard legitimate sources. Those
clauses exclude the surviving Midday permission. This is a material scope and
completeness error, not a requirement to copy the reference's wording or a new
interpretation invented to repair model performance.

**This error escaped this reviewer's earlier source/label acceptance.** The
Round 4 acceptance failed to detect the final reference's exclusion and cannot
support an eligible semantic inference now. The earlier reports and specific
correction closures remain historical evidence; they do not override the
source or the discovered defect. Code, preparation and execution checks may
remain correct while the reference bank is invalid for the registered claim.

The final adjudicator's INELIGIBLE decision and root's stop follow the accepted
SEMANTIC eligibility rule. The whole screen is disqualified; neither primary
sign inference nor the 12/18 plus one-per-family practical screen is computed.
No reference edit, checkpoint exclusion, repaired-label evaluation, reduced-bank
score, model retry or control promotion is used. Valid execution and descriptive
structural/cost observations remain reportable. This is not a null finding
about whether training can work, nor evidence of equivalence or coding benefit.

### Original judgments, separate adjudication and costs

All 31 Kimi archive files are tracked and match their inventory sizes/hashes and
exact `a951212e` Git blobs. Astra's original 36-record file matches its frozen
hash and historical bytes. For each of Kimi's six responses I reconciled the
request, raw response, response-text and parsed-original hashes. Plain JSON
parsing, or removal of exactly one recorded outer JSON Markdown fence, produces
the preserved original object with no semantic or enum edits. Each request
contains its frozen blinded packet; no retry or extra judgment request occurred.

Kimi returned all 36 response records, but the original
`a471514d1ca0d52c94acb97b` stale/reinstatement field literally contains
`PRESENT_CHECKED_ABSENT`, outside the registered enum. It remains unchanged and
UNKNOWN as an original judgment. The terminal delivery status is correctly
JUDGMENT_DELIVERY_INCOMPLETE, with session 68274 exit 2 and owned PID 195862
absent. Terminal assessment work does not mean every original vote is valid.

Monotonic endpoint subtraction reproduces Kimi's **719.241566905 seconds**.
The six raw service receipts total **116,456 prompt plus 114,371 generated
service tokens**, **230,827** combined; reconstructed request intervals have
maximum concurrency two. These are service-reported judgment tokens and the
batch's outer interval, not target-model generation cost or total reviewer and
orchestration cost. The earlier measured execution costs remain separately
preserved and unchanged.

Without reading the private response map, independent multiset comparisons
match all 36 blinded packets to the exact frozen source prefixes, reference
objects, returned answer text and structural facts. All 72 original structural
judgments and cited-source visibility checks reconcile. The single invalid
Kimi enum is the sole category-schema exception and remains explicitly exposed.
These are identity/structure checks, not a replacement semantic scorer.

All thirteen disputed IDs occur exactly once in the separate adjudication file.
Its recorded original field values match the immutable Astra/Kimi originals;
its final fields match the stated dispositions, with valid category enums and
cited IDs visible in the corresponding source prefix. It changes no original
record. Three disputed answers originally marked FAIL by both judges receive
separate PASS adjudications. Reading their complete returned answers confirms
the stated methodological basis: explicit retirement, replacement or suspension
qualifies earlier quoted clauses. Considering that complete wording is allowed
by the frozen semantic rubric; requiring an additional historical label on each
old clause would introduce a stricter format rule. These separate descriptive
adjudications are not a repaired-bank score or a practical-gate result.

The disclosed firmware ambiguity is also accurately reported: source m17 says
to leave frost-watch only above 4 degrees Celsius, whereas the answer's
“4 degrees Celsius hysteresis” does not uniquely specify that release boundary.
The adjudication retains the ambiguity and FAIL for that answer. Its separate
source judgment of the invalid Kimi field does not normalize or supply a valid
original Kimi vote. No further answer or label adjudication was performed by
this closing audit, and no aggregate semantic arm score was computed.

### Reporting closure

RESULTS now leads with the final INELIGIBLE status and clearly distinguishes
the intact historical execution report from terminal addenda. README accurately
says the 36-response comparison completed but an expected-answer defect prevents
advancement or a training-benefit claim. Both preserve the larger coding goal
as unproven and state that no successor model trial has launched. This audit
does not assess or endorse the separate source-evidence research hypothesis.

The generation and reference manifest hashes remain the exact Round 7 values.
All original votes, disputed-vote records, source evidence and separate final
adjudications are retained. The final check explicitly records no primary test,
practical score, reference repair or model rerun. There is no remaining
reporting correction or protocol cycle required for this stopped screen.

Only this canonical review was written. Work was read-only CPU/metadata/source
inspection: no code or label edit, model/weight/GPU operation, generation,
re-preparation, rescoring, old-bank/benchmark access, private-map access,
network operation, repeated test suite or commit. The bank remains invalid;
acceptance here is acceptance of truthful reporting and the registered stop.
