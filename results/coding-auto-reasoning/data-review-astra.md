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
