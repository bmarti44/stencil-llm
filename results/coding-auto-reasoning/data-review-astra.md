# Independent fresh DEV data review — Astra

2026-09-08. Native Astra, xhigh, explicitly selected by the user; author-disjoint.
This canonical data-review topic continues in the existing reviewer session
because a separate reviewer launch reached the thread limit. Purpose: source
authority/scope, oracle and recap fidelity, references and actual dependencies,
check integrity, negative controls, public-feedback invariance and prospective
capacity. Threat model: trusted but fallible semantic author and consumers, not
malicious same-user interference. This is data readiness, not a test of a worker
or proof of automatic usefulness. No model calls, old-case reads, replacement
semantics, data/code edits, validation bypass or authored-code execution were
performed by the reviewer. The parent owns correction requests and preflight.

## Round 1 — 68/100; both projects not accepted

Four open high findings and two open medium findings; zero critical findings.
One bounded Kimi correction should address the paths below before another
source review and normal per-document preflight. These are unaccepted fresh
authoring outputs, not permission to change or rerun an earlier experiment.

| Input | SHA-256 |
| --- | --- |
| `author-00/authored.json` | `8771f0079c6e423042a5c9606b374e124968dd289f4fd4393a53b1c54ffdd76f` |
| `author-00/preflight-initial.json` | `b63de3471f64d1d9a964653d138f131bc5345ca87a854fdd428a183bb9fb3c9c` |
| `author-01/authored.json` | `986644670e47f42b2f3ffebad54d97fb3dfc5098c4644e3f3259e1b6273d169a` |
| `author-01/preflight-initial.json` | `484a80bf9c0b61ea0592714d41ce27bfc810d15650cc55854d24a5547535db54` |
| `DATA-CONTRACT.md` | `502410a3f48b3355135e9cab1f3000fb040d3ff3fd77daf067bfaeb99e78cc5d` |
| Accepted `DESIGN.md` | `6891d83ad2f6aac7d88bbec3d88a7c6337dd9337d011a1a95c9ccb3c3f9be1dc` |

Paths above are relative to `results/coding-auto-reasoning/`. Reviewed consumers
are the unchanged `scripts/coding_competence_dev.py`,
`scripts/coding_worker_dev.py`, and the relevant `slab.py`, `slab_sandbox.py` and
`renderer.compact` boundaries. The preflight receipts bind their implementation
hashes; source inspection confirms the specific mechanics cited below.

### Finding 1 — high, open: project 00 changes existing rule identities

`author-00/private.rounds[1].oracle.effective_rules[1..3]` and the same indices
in round 2 change the text of `rule-report-errors`, `rule-keep-duplicates` and
`rule-no-sort` under their existing IDs. The unchanged validator defines identity
as `(scope, strength, text)` and rejects the first change. The parent's initial
preflight is INVALID with `rule rule-report-errors changed identity`; reference
execution did not begin. I independently compared all six changed paths.

Kimi correction: keep genuinely unchanged identities byte-consistent; represent
actual changes or exceptions with coherent lifecycle identities and source
support, updating recap, active/inactive IDs and dependent check references as
needed. Source IDs may gain relevant visible antecedents without changing an
otherwise unchanged identity. Do not merely copy earlier text where finding 2
requires a semantic correction.

### Finding 2 — high, open: project 00 promotes request-local error behavior to global authority

`private.rounds[0].oracle.effective_rules[1]` declares `rule-report-errors`
global, citing only `m04`. That message specifies `validate_batch` and its error
list; it does not establish that every later feature must return that list.
The authentic global rule in `m03` requires JSON-safe error handling, which is
not the same requirement. Grouping's unchanged error list is established later
by `m08`; summary's is established by `m11`/`m12`. The later versions of the same
oracle entry and corresponding `manual_recap` passages inherit the unsupported
global promotion. This could wrongly classify a source-faithful automatic view
as incomplete or require a reminder to overstate the user's authority.

Kimi correction paths: the three `rule-report-errors` entries, all three recaps,
and affected rule references. Respect the genuine source scope and the times at
which downstream requirements arise; do not invent an earlier global instruction
solely to justify the present labels.

The summary best-attempt instruction itself is correctly interpreted as a
`summarize-class` exception: `m09` frames the feature, and `m11`/`m12` establish
best-score counting there. It does not authorize deduplication in validation or
grouping. Preserve that interpretation while fixing the duplicate-rule identity
and its exception representation. The references currently preserve the earlier
functions and apply best-score selection inside the summary.

### Finding 3 — high, open: public full outputs reveal declared standing-rule answers

Project 01's public examples are not invariant to the declared global house
rules. Concrete paths include:

- `public.rounds[0].public_checks[0]` (`chk-r0-pub-1`) turns `" Night  Drive "`
  into `"Night Drive"`, directly teaching `r-clean-text`, and shows T01/T02,
  teaching `r-id-format`.
- The nonempty success examples in all three rounds expose the same mandatory
  identifier format. `public.rounds[2].public_checks[0]` also teaches title
  whitespace cleanup.
- `public.rounds[0].public_checks[2]`, round 1 index 2 and round 2 index 2 teach
  exact rejection strings covered by `r-err-exact` (and, in round 1, the declared
  scoped order-vocabulary rule).

Empty `rule_ids` do not remove this information from worker feedback. The
selector does not see checks, but the worker does, so the registered interface
still matters. Project 00 also puts rule-sensitive rejection/error reporting in
public examples: round 0 indices 1 and 3, and rounds 1/2 index 1. These need
reassessment under the corrected scope contract and the explicit instruction to
keep rule-sensitive rejection cases private.

Kimi correction: author valid public functionality examples whose complete
outputs are invariant to the standing distinctions being studied. Where a
declared convention necessarily appears in every useful nonempty success
example, make the natural source/rule/check design compatible with this
interface, as the data contract requires. Do not simply clear IDs, relabel an
unchanged global rule as functionality, or delete a live requirement from the
oracle. Keep meaningful dependent work and private discriminating cases.

Correction scope clarification, 2026-09-08: preserve both original algorithms,
dependency chains and meaningful scoped changes. In project 01, every nonempty
successful track result contains an identifier, so informative complete outputs
cannot be invariant to its format while that format remains a standing
distinction under study. The minimal redesign needs a genuine Kimi-authored
separation of the fixed feature contract from the reminder-sensitive standing
policies, with unchanged required feature behavior and consistent source, oracle
and checks. It cannot consist of empty/trivial public examples, missing live
rules or easier replacement projects. The current document is incompatible as
written; a green reference preflight alone would not resolve this finding.

### Finding 4 — high, open: project 01's authored key-order requirement is lost at the consumer boundary

`public.rounds[0].source_messages[0]` house rule 4 and the repeated
`r-unknown-key-first` oracle entries require the first unrecognized key in the
order supplied. `private.rounds[0].obligation_checks[1]` (`chk-r0-obl-2`) gives
`tracks`, then `zeta`, then `alpha`, and expects `unexpected key 'zeta'`.

The unchanged consumer does not preserve that authored insertion order:
`coding_worker_dev._fresh_execute` serializes cases with `renderer.compact`,
whose `json.dumps` has `sort_keys=True`; `slab._execute_cached` serializes the
sandbox request with it again. The callable receives `alpha` before `zeta`.
The parent's saved preflight reports exactly `unexpected key 'alpha'` and the
sole reference failure at that check. The reference's iteration is faithful to
the object it actually receives; the receipt is not evidence it ignored the
authored first-key rule.

Kimi correction scope: the natural unknown-key policy and its matching repeated
oracle/recap/request clauses, relevant helper/reference/control behavior if
needed, and discriminating checks. Author a deterministic requirement that this
unchanged JSON boundary can actually test. Changing only the expected value to
`alpha` would conceal the lost distinction between authored insertion order and
the order delivered to the callable. Do not change the frozen consumer or bypass
serialization to make this document pass.

### Finding 5 — medium, open: project 00's functional mutant also violates declared standing policy

`private.rounds[0].negative_controls[0].patch` (`nc-r0-functional`) inserts a
`break` after the first invalid element. For `chk-r0f-01`, this drops the later
valid Ada attempt as well as the later invalid element's report. That changes
the declared preserve-every-attempt policy in addition to processing/counting
functionality. The obligation cases happen to contain only valid entries, so
their passing would not demonstrate policy preservation.

Kimi should replace this control with one meaningful algorithmic defect that
preserves the corrected standing policy, then declare its actual private
discriminators. The contract allows incidental full-output obligation failures
from a functional defect; it does not permit the functional mutant to change
the rule policy itself. No replacement implementation is authored here.

### Finding 6 — medium, open: private combinations miss central specified distinctions

Project 00's summary checks never put the same student in different assignments,
so summing per-assignment distinct-student counts instead of counting class-wide
unique students is unchallenged. Its only best-attempt example increases from
70 to 95; taking the last attempt also passes that witness. Paths:
`private.rounds[2].functional_checks` and `obligation_checks`.

Project 01 specifies validating every entry before checking duplicates, but its
private normalization cases do not combine an earlier duplicate with a later
invalid entry. A consumer that returns the duplicate before validating the rest
is unchallenged. Path: `private.rounds[0].functional_checks`.

Kimi should add bounded, independently authored private combinations for those
specific distinctions, including a later lower resubmission and a student
appearing across assignments. Retain source-derived expectations and public/
private disjointness. This is not a request for exhaustive tests, a new test
framework or a perfect comparator. Source review remains necessary afterward.

### Other source, dependency and control evidence

Both projects have distinct target stubs and meaningful actual call chains.
Project 00 references call `normalize_submission`, then `validate_batch`, then
`group_submissions`; the summary aggregates per-student maxima without editing
earlier functions. Its visible helper rejects Boolean scores, preserves valid
numeric values and trims the specified names. Static tracing of all saved
expected outputs found no additional arithmetic/reference contradiction.

Project 01 references reuse `parse_track`/`format_clock`, then normalization,
then sequencing. Normalization validates the full list before duplicate checks;
sequencing uses stable ordering while preserving normalized IDs; the manifest
applies its longer-first artist-group change locally and preserves sequencer
ordering for duration mode. The manifest's earlier shorter-first plan is
correctly retired, and the unadopted title tie-break and rejected shuffle
suggestions are not promoted to instructions. Its function-level scoped
requirements are not automatically global ones. Optional input fields specify
conditional required behavior, rather than permission for the implementation
to choose arbitrary outputs.

The future manifest plan in round 1 must not become a current sequencer ordering
instruction. An all-active oracle inventory is not automatically a current-task
focus projection; preserve scope and dependency context when preparing or
reviewing capacity references and selector output. No current-focus completeness
claim is made from the unfiltered token counts below.

Project 00's remaining controls have intelligible single intended changes:
duplicate dropping, assignment-name lowercasing, unweighted averaging, and stale
two-decimal rounding. Execution remains pending because the document is INVALID.
For project 01 I inspected the parent's terminal preflight rather than repeating
it: **235 executions in 4.270335289 seconds, FAIL** solely at `chk-r0-obl-2` for
the reference; all six controls meet the current mechanical audit, and each
obligation control passes cumulative stable private functionality. The bad
key-order expectation also appears as an incidental control failure, so those
receipts cannot repair the reference failure or establish full semantic validity.

Check IDs are unique within each document. Static comparison found no private
symbol/input collision with any public initial or round check. Episode IDs are
distinct across documents. Counts are: project 00, five initial checks plus
round public/private-functional/private-obligation counts 4/3/2, 3/3/2, 3/3/3;
project 01, seven initial checks plus 3/6/2, 3/4/2, 3/5/2. Disjointness and case
counts do not establish public invariance or complete coverage.

### Capacity and next acceptance boundary

Local-tokenizer counts of exact compact `{"source": ...}` argument JSON are
170/105/334 for project 00 and 584/322/686 for project 01. Serializing the present
unaccepted oracle texts/source IDs into an unfiltered `obligations` list gives
189/229/311 and 248/449/677 tokens, respectively. No authored code ran for these
counts. All are below the prospective 893-token reference-argument ceiling;
corrected complete current-focus references must be reviewed and counted again.
This says nothing about future generated length, native prompt size or quality.

Preserve both original authoring outputs and preflight receipts. After Kimi's
bounded correction, use the normal unchanged validator and reference/control
preflight, then independently review the changed source and all consequences
before bank acceptance. No validation bypass, private fallback, model-output
rescue or weakening of the frozen predecessor verdicts follows from this review.

## Round 2 — 96/100; corrected two-project DEV bank accepted

2026-09-08. Same native Astra xhigh reviewer; bounded correction and consequences
review. All six prior findings are resolved below. Zero open findings, including
zero open high or critical findings. This accepts the corrected data for the
registered narrow engineering pilot; it does not authorize launch or establish
model usefulness, parity, reliability or universal source correctness.

| Corrected input | SHA-256 |
| --- | --- |
| `author-00/patch-01/patched.json` | `1a5f91d4e0fac8ee467741bbcafd581a11a40e04ddcdb384b41a49e8d54617b0` |
| Its `preflight.json` | `7214fa326552c9e7b42b0b649fd0eedef4c903b6ab382067d4cc32ccf0ca6dcf` |
| Its `parent-verification.json` | `93789e0344f10e8c2ab00714f9a829e66e227741248ac03a3b326d540e2d3ddc` |
| `author-01/patch-01/patched.json` | `9e866c8ada769e6371615d509000ff02fd3d3dc6056e64e73213183417ee1dc8` |
| Its `preflight.json` | `dc9bd29442eb7f336c56ea3354ee32e842df037455f22a96ca7b46837fd1095a` |
| Its `parent-verification.json` | `13871a35e08ff45f57b13160f1dafe5424ec3289423943e7eccb5c036285e502` |

The design and data-contract bindings from round 1 remain applicable. Original
authoring outputs and their failed preflights remain historical evidence.

I independently reconstructed all 16 and 22 replacements from the original
documents, checking each allowlisted path and exact old/new value hash, and
reproduced both patched files byte-for-byte. The saved patch lists equal the
JSON extracted from the two terminal raw Kimi responses. Their response hashes
are `fea2455b714ac673400ef8d2e01ab175147eabd97c211f08db269147e100d6fc`
and `cc32d9f2af358536e8e38fdde7e193974d501aa49c5a2115f2db443cc4fb9e25`.
Original message IDs, roles, ordering, task handles and targets are preserved;
initial checks are unchanged. I inspected the changed source/code/check content,
not just the guard claims.

### Finding closures

**Finding 1 — high, resolved 2026-09-08.** Project 00 now keeps each repeated
rule's scope, strength and text consistent. Separate function-scoped error-list
identities represent grouping and summary behavior. The original duplicate and
no-sort identities remain stable; the summary's genuine local best-attempt
exception is represented separately. Static identity comparison and the normal
preflight both pass.

**Finding 2 — high, resolved 2026-09-08.** `rule-report-errors` is now scoped to
`validate-batch` and cites `m04`. Grouping's own rule cites `m08`; summary's cites
`m11`/`m12`. Recaps explicitly distinguish those feature contracts from the
global JSON-safe error-handling direction and do not claim an earlier global
error-list mandate. Project 00's authentic conversation and all three reference
algorithms are unchanged. The summary exception does not authorize changing
validation or grouping.

**Finding 3 — high, resolved 2026-09-08.** Project 00 replaces the identified
public rejection/error-reporting cases with valid nontrivial batches and retains
rejection coverage privately. Public examples contain no resubmissions; their
student ordering already agrees with the declined alphabetical proposal, and
public averages do not distinguish one from two decimal places. Private cases
retain the duplicate, ordering and rounding distinctions. Empty error fields in
valid success objects are specified API shape, not evidence that an invalid
element was reported according to an undisclosed policy.

Project 01's source was actually redesigned, rather than merely deleting oracle
IDs. The initial user explicitly establishes one shared unknown-key policy and
assigns identifiers, success schemas and other exact behavior to each feature's
fixed API description. Normalization still requires the same T01-style IDs and
the same helper-based cleaning; manifest title cleaning is now explicitly stated
in its task. Existing informative success cases remain. The public invalid-order
case is replaced with a delegated fixed-helper rejection case. No public case
contains an unknown key, a duplicate-handling choice, or an equal ordering key
that reveals the scoped tie policy; supported valid order modes do not reveal
whether additional modes are forbidden. The meaningful standing unknown-key,
sequencer-stability, manifest retirement/replacement and closed-order constraints
remain source-supported and privately tested.

These distinctions concern the standing policies under study, not invariance
to every possible incorrect algorithm. The fixed API behavior is still required
and public checks legitimately test it. This is neither empty-case substitution
nor an easier replacement project.

**Finding 4 — high, resolved 2026-09-08.** The new source specifies the
alphabetically first unknown key, independent of authored insertion order.
The initial parser and each reference use explicit sorted-key iteration;
matching oracle/recap/request clauses and expectations change consistently.
Multi-unknown-key private witnesses cover both the top-level payload and nested
track entries, and later features retain their own witnesses. The corrected
normalization obligation control chooses the reverse sorted key, providing a
discriminating failure while preserving stable functionality. This is a genuine
deterministic policy change before exposure, not expected-value-only repair or
consumer modification. All other reference computation is unchanged.

**Finding 5 — medium, resolved 2026-09-08.** Project 00's functional control now
processes every element and preserves every valid record and error report. Its
single intended defect swaps valid/invalid counts. Named private discriminators
are updated and fail in the saved preflight. Its incidental full-output
obligation failures are consistent with the permitted functional-result overlap;
the preserve-attempt and error-reporting policies themselves are retained.

**Finding 6 — medium, resolved 2026-09-08.** New private `chk-r2f-04` in project
00 puts Ada in two assignments and correctly expects three counted scores but
two distinct class-wide students. New `chk-r2o-04` puts a score of 96 before a
later 71 for the same student and requires the best-score average of 90.0 with
the other student's 84. Project 01 adds `chk-r0-f7`: a duplicate pair precedes
an invalid third entry, and validation's track-3 error must win. These directly
address the recorded distinctions; no broad test expansion was imposed.

### Current-scope projection boundary

For these reviewed documents, the active entries with scope `global` or the
current request's task handle provide a source-correct complete standing-focus
reference, with the following explicit semantic interpretation. This conclusion
comes from reading the source and dependencies; the enum filter alone does not
prove it for arbitrary future data.

- In project 00, global attempt preservation remains the default. At the
  summary, the included task-specific best-attempt text is its explicit counting
  exception; the two are not read as conflicting absolute demands. Earlier
  validation/grouping behavior remains intact. Their separate error-list
  descriptions may be omitted from the current projection because the current
  feature's own propagation rule and required dependency supply that contract.
  The retired two-decimal rule is absent in later rounds.
- In project 01, current sequencing includes its own delegation and stable-tie
  requirement; the future manifest plan is excluded. Current manifest focus
  includes its replacement tie rule, equal-length stability, unchanged duration
  ordering, delegation, global unknown-key policy and closed order vocabulary.
  It need not restate every implementation detail of the normalizer or
  sequencer, whose actual code remains a required dependency. The retired
  shortest-first manifest rule is absent.
- The projected objects contain some accurate task-API notes as well as
  standing rules. They are not a mandatory phrase list or a requirement that
  selector prose reproduce the whole algorithm. Fixed success fields, grouping
  without an extra averages field, and other fully specified current API details
  remain in the original request. Semantic completeness must be judged against
  the accepted standing-focus domain. Optional input fields are conditional
  required API behavior, not permission to choose arbitrary outputs.

This projection supplies a valid offline capacity reference; it is not runtime
oracle input, semantic inference by code, or a guarantee the selector will
produce a complete accurate view. Keep the original source as authority and
judge actual selector omissions, additions, modality and scope independently.

### Verification and capacity

I inspected the parent's terminal normal preflights: project 00 **212 checks in
4.148007289 seconds, PASS**; project 01 **253 checks in 5.066790319 seconds,
PASS**. Both bind the exact corrected data hashes, contain no reference failure,
and validate all controls. All obligation controls preserve cumulative stable
private functionality and fail no public check. I did not repeat these 465
executions. Static checks reconfirm unique check IDs, visible source citations,
stable rule identities and no public/private symbol-input collisions.

Local token counts of compact, unescaped-Unicode, sorted-key argument JSON:

| Project | Round | Global + current focus | Reference edit |
| --- | ---: | ---: | ---: |
| 00 | 0 | 189 | 170 |
| 00 | 1 | 193 | 105 |
| 00 | 2 | 261 | 334 |
| 01 | 0 | 141 | 585 |
| 01 | 1 | 222 | 323 |
| 01 | 2 | 327 | 687 |

The largest argument leaves 334 tokens within the 1,021-token final allowance,
above the required 128. These are exact reference-serialization counts, not
native prompt counts or bounds on future generated JSON. Final preview must
bind the accepted files and settled implementation. Finite checks and this
source audit do not guarantee correctness for every possible input; no model
output exists here and no empirical workflow-success claim follows.
