# Proposed SC1 Stage 1 clauses — 2026-09-04

PROPOSALS ONLY. These clauses are not a registration, amendment, or authorization
for production authoring/model execution. The orchestrator must reconcile and
append accepted wording as a dated amendment to LEDGER-PLAN.md before Stage 1/2
acceptance. Governing SC1 DRAFT v2 and AUTHOR-CONTRACT v2 are unchanged.

Data lineage: fit-on = the previously frozen selector development corpus; no new
fitting. Evaluated-on = newly commissioned, disjoint setup/final sources under the
registered law; these CPU smoke fixtures and their recorded responses are never
production sources or fitting data. No policy/model outcome informed these repairs.

## Registration identity and snapshot (astra ambiguity 2; fable N3/N6)

Proposed clause: Stage 1 is a JSON object with `status: "REGISTERED"`, a unique
`study_id`, absolute `execution_root`, `trunk: "4b"`,
`science_snapshot_path: "data/sc1/registration-snapshot.md"`, `science_hash`
(SHA-256 of that file), `deployment`, and `authors`. At freeze the snapshot is the
exact byte concatenation of the governing SC1 DRAFT v2 section and the v2 author
contract, with no inserted text. Its two source parts and boundary are recorded
in the handoff. Subsequent live-ledger editorial entries do not change that file.
Any substantive accepted amendment requires prospective reconciliation of this
candidate and re-freeze before authoring; this candidate does not enact these
proposals. The executable and production manifests bind the same snapshot bytes.

`deployment` must equal the executable manifest block: bfloat16,
hf_compatible, temperature 0, greedy true, max_new_tokens 256, deadline 300,
eos_ids [151645,151643], nonthinking_opener as frozen, one resident initialization
per invocation/no warmup, max_prefix 2048, max_query 1024, position_guard 40960.
Stage 2 hashes the actual 4B checkpoint, tokenizer, configs, executable code,
dependencies, parser, grammar and filler bytes.

`authors` has exactly kimi-k3, fable, gpt-6-astra and Opus keys. Each value includes
`provider`, `immutable_version`, `settings` (temperature, top_p, reasoning_effort,
max_output_tokens, seed_support), exact `neutral_template`, `contract_hash` and
`grammar_hash`. The first unsigned 32 SHA-256 bits map provider seeds; the mapped
seed is retained whether or not the frozen provider supports applying it. Apply
it exactly when supported; do not silently substitute versions/settings.

One study has one absolute execution root; relocation is refused. A durable
per-checkout registry at `.git/sc1-studies` binds study and source-fingerprint
ownership; new registrations require new production sources. This is a local
trusted-operator guard, not a global cross-checkout uniqueness service. Each stage
binding publishes an immutable `registration-audit.<stage>.json` with the study
ID digest, registry location/hash, complete entry (including manifest IDs) and
source-owner file hashes, and appends those bytes to WORKLOG.md. The receipt
captures the registry at that binding, not an assertion that mutable registry
bytes never change when another stage is bound. Review that audit before launch.

All determinism/setup/final consumers and analysis (which may recover journals or
publish pairs) acquire a nonblocking exclusive execution-root lock before opening
mutable journals/meters or constructing a backend, and retain ownership through
final durable publication. A second owner is refused immediately; no waiting,
unlinking the lock inode, or process signalling. Root binding alone is insufficient.

## Source geometry, pressure and disclosure (astra R8/ambiguity 1; fable N1/N2)

Proposed clause: Freeze FILLER_VERSION SC1-incidental-v2, the 512-item
subject/verb/place sentence pool and its manifest hash. Sample without replacement
within each episode using the filler seed. Expand designated non-evidence,
non-trace turns round-robin, covering user/assistant/tool roles. Every authored
base and every final rendered history turn is at most 600 tokenizer tokens in
its text (chat delimiters are counted in rendered history, not that text cap).
Designated turns × 600 must exceed 4608 minus rendered base history, with room
for existing base text and whole-sentence packing; typically at least eight turns
are needed. The expander reports base tokens, usable capacity and a lower bound
on total turns needed. The history minimum is checked after each round-robin
batch, so 4608 is a minimum target, not an exact length; smoke observations are
approximately 4620–4699. Full acceptance still requires history 4096–8192,
U >= 2B and at least one actual budget skip. No causal evidence is moved or
relabelled to fit. Grammar capacities/complexity limits apply before source freeze.

Disclose the induced population: the current smoke design's disclosed filler
occupies over 90% of candidate columns. Most retained rule pieces come from the
newest old user filler turn. OLD retention is therefore strongly determined by
author turn ordering; this setting may chiefly compare rejection of formulaic
filler against user-first recency. This is not a measured classifier advantage
or a general claim about realistic histories. Production authors remain blind.

Report per episode candidate_columns, real_candidate_columns, B, budget skips,
echo omissions, role/position geometry and per-arm pin composition (pieces and
columns from designated filler turns versus other turns). Here "real" means
non-designated-turn provenance, not semantic necessity; original base prose in a
filler turn counts with that turn. The smoke README carries the concrete
role/position/wording audit and measurements. Independent Stage 1/2 acceptance
must reconcile these observed cues with the contract's no-position-only-relevance
requirement before production; this proposal does not waive that requirement.

## Evidence, public tools and finite source grammar (astra ambiguities 3/5)

Proposed clause: Every decisive fact and trajectory entry is a necessary,
obligation-linked dependency with a unique verbatim public evidence span. Every
trajectory event has user authority in an actual user turn and the assigned
scope. Continuing requires instruction; overridden requires superseded then
update; cancelled-or-completed requires obsolete then cancellation or completion;
switched requires switch then return. The full necessary dependency determines
age. Unsupported structures require repair within the original assignment.

State-bearing public JSON, including complete multiline/nested blocks, must be
exactly one canonical `{call,return}` envelope on its own line in the chronological
trace's tool turn. The return must equal finite-executor replay. No extra public
state block is allowed beside it. Incidental plain prose and non-state JSON are
allowed around the envelope; they may not purport to supply an untraced state.
This serialization boundary prospectively narrows the contract's general
"realistic JSON or plain text" language and must be reconciled before authoring.
Typed answer inventories cover every payload/target literal and its necessary
evidence/obligation links. Independent reviews bind source and public-render hashes.

Fingerprints jointly alpha-normalize entities/literal equality classes and
unordered graph permutations. Reject unordered groups above eight entries or
more than 40,320 joint variants before source acceptance. Pair signatures bind
both source IDs/hashes and an independent reviewer session. Source-content hashes
exclude provenance/review to avoid circularity; complete provenance is separately
manifest-bound. Within-pool entity/identifier reuse is a Stage 3 review flag
(fable N8); cross-pool collisions are rejected. Flags do not certify independence.

## Numeric and text checker law (astra R1/R4/R7; ambiguity 4)

Proposed clause: JSON numerics use exact finite Decimal values, at most 1024
coefficient digits and an absolute stored decimal exponent at most 4096; canonical
serialization must also remain within those limits. Unsupported representation or
exponent construction is an ordinary parser/schema-invalid output, retained and
scored once, not a harness exception or retry. Integral decimals satisfy integer
schemas; booleans are distinct. Wrong-number negatives negate nonzero values
exactly (without Decimal context rounding), or replace zero with one.

Text tasks have `permitted_paths: []` and explicit nonempty zero-based
`editable_lines`. After the production newline/trailing-whitespace/blank-run
normalization, only replacements at those indices are permitted. The original
`initial_state` fixes the line count and every noneditable line. Both reference
and expected artifact must preserve that baseline before freeze; matching an
inconsistent oracle cannot waive permissions. `permitted_edits` is the reserved
implicit invariant. Insertion/deletion or a protected-line change is corruption,
including otherwise schema-invalid parsed text. Wrong values wholly inside an
editable line can fail the task without causing corruption.

Text old-ID/obsolete/cancelled witnesses store raw full artifacts in
`old_id_work`, `obsolete_work`, or `cancelled_work` of linked public trajectory
entries. Compare with the production text normalization, never JSON parsing or
JSON string quoting. Require changed normalized lines to occur in that event's
public evidence, distinct from the reference, and the applicable assigned scope.
A text wrong-entity witness includes `line`, `target_id`, `replacement_id`,
`evidence_id`, `output`, and `obligation_ids`: exactly one normalized line replaces
one occurrence of the target ID with a different declared entity ID; both IDs
must occur in the linked public evidence. It must remain schema-valid and violate
its linked obligation. No truly applicable attack may be relabelled inapplicable
to bypass unsupported validation. Six distinct negatives and full invariant
coverage remain required.

## Author transport and attempt history (astra ambiguity 6; fable N7)

Proposed clause: A fresh isolated session writes one source; up to two repairs
resume only that same source's session. No session is reused for another source.
Each cumulative transcript JSON contains `session_id`, `provider`, `version`,
`settings`, `input`, `response` (the exact source object), and `messages` (the exact
alternating user-input/assistant-source pairs for attempts 0 through the current
attempt). No unrecorded prior context is allowed. This transport profile supplies
no system/developer inputs; a provider that necessarily supplies any such input
must expose it for prospective contract/schema reconciliation before registration,
not silently drop it in conversion. CPU tests do not establish provider isolation.

`attempt_history` entries contain zero-based `attempt`, `previous` (prior complete
entry hash, null initially), `feedback` (prior rejection reason, null initially),
`request_hash` (canonical hash of the commissioning_request function envelope),
`transcript_path`, `transcript_hash`, `source_hash`, `decision`, `reason`, and
`reviewer`. Accepted entries may omit reason/reviewer; rejections require both.
Retain all requests, responses, inputs, feedback and decisions; reject missing
attempts or a chain above three. Provenance binds session, exact settings,
prompt/input hashes, provider, transcript and isolation/originality attestations.

Only `*.input.json` is delivered to an author. Its canonical input hash and file
SHA-256 are retained in `*.request.json`; that separate operator envelope holds
private order/setup-order streams and retained prior attempts. Do not send the
operator envelope or repair history files to an author. Exact transport-message
history is validated independently of the private envelope's file packaging.

## Determinism, abandoned work, failure records and cost (astra R5/R6; fable N5/N9)

Proposed clause: Use the two lexically first frozen smoke IDs in two fresh
processes, with both arms in each process: exactly eight retained observations.
Each cell binds deployment, frozen episode/input, initialization, token IDs and
immutable arm/output hashes; the certificate binds two closed, charged allocation
intervals. Every cell must complete generation without timeout/generation failure
and contain nonempty generated token IDs. Task success is not required; a
nonempty deterministic malformed answer can qualify. Cross-process token/input
equality is required separately for each source/arm cell.

No replacement of an incomplete/failed determinism schedule or selective extra
outputs is permitted under the study ID. The prerequisite is deferred/failed;
retained artifacts and the abandoned allocation are preserved. If a new study_id
and execution_root are prospectively registered, abandoned GPU seconds are
reported separately in WORKLOG.md and the new registration's cost disclosure,
with predecessor study IDs, allocation hashes, loss evidence and total cumulative
SC1 effort. The old study's charged intervals remain in its ledger; a fresh ledger
is not a claim that abandoned work was free. No automatic re-registration or cost
reset is authorized by this proposal. The orchestrator must expressly accept this
separate-reporting disposition or instead register a carry-over mechanism before
any restart. Within one study every interrupted/resumed interval counts in its
8-hour cap, including determinism and initialization.

Caught journal-write failures require reconciliation of actual durable bytes
before another append. Retain recovery proof before a separating newline; atomically
prepared outputs already represent completed work and are published on recovery,
never regenerated. Recovery failures propagate with the original durable evidence
intact. Completed bad outputs/timeouts are scored once. Host/device/resource loss
requires external evidence for genuinely missing work; unresolved harness defects
invalidate the study, never cause selective reruns.

R detects periods 1, 2 and 4 using the registered four-token algorithm, not all
possible loops. QwenBackend returns timeout or raises exceptions; GenerationFailure
is currently reachable only from fixtures. RuntimeError messages mentioning
cuda/nccl/device/out of memory are provisionally classified as infrastructure,
including possible harness bugs; operator evidence/judgment is mandatory before
resuming missing work. `analysis.json` includes this failure-taxonomy disclosure.
Only actual attention-amplification and residual-steering entry points have
measured zero counters; scope/digest execution paths are absent, not measured zeros.

The cost projection retains the maximum measured future initialization reserve
and adds maximum measured per-arm persistence overhead to the forecast, besides
the registered prefill/token/CPU/check terms. It uses only remaining arm attempts,
never lowers retained maxima, and reserves the 300-second ceiling before launch.
These conservative extensions to the printed formula require prospective adoption.
Actual Qwen determinism and GPU timing remain unperformed, separately authorized
prerequisites; these CPU artifacts cannot certify either.
