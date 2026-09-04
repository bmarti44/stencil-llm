## SC1 AMENDMENT 1 (2026-09-04) — operational and source-validation clauses adopted for DRAFT v2

SC1 AMENDMENT 1 — 2026-09-04. This amendment prospectively adopts the operational and source-validation clauses below for SC1 DRAFT v2. It does not accept a Stage 2 artifact, authorize production authoring, or authorize model execution. Stage 2 acceptance requires the amended science snapshot, reconciled sanitized author contract/grammar, passing consumer regressions and independent disposition of the smoke cue audit. Unresolved requirements below remain freeze blockers. The v2 endpoint, N, factor distribution, policy algorithms, adoption gates and prohibition on outcome-informed revision remain unchanged except where this amendment expressly states otherwise.

Data lineage: fit-on = the previously frozen selector development corpus; no new
fitting. Evaluated-on = newly commissioned, disjoint setup/final sources under the
registered law; these CPU smoke fixtures and their recorded responses are never
production sources or fitting data. No policy/model outcome informed these repairs.
Historical selector-development influence remains disclosed in DRAFT v2 and LEG B/LEG A.

Binding orchestrator decisions (verbatim):

(a) Filler-cue disposition = astra's conservative text C: the contract's relevance rule stays binding; no exception
    for recognizable filler; Stage 2 acceptance requires the independent review of the frozen source/expansion law and
    smoke evidence, which will be performed in the NEXT review round on your output (not a separate round).
    In addition: the expander must never place formulaic filler as the newest eligible old user turn; add that as a
    source law + validator rule + test (so the smoke shortcut astra names is mechanically excluded).
(b) Abandoned-cost disposition = astra's text G (separate reporting; 8 GPU-h cap cumulative per registered study).
(c) Snapshot definition = fable's clause-1 replacement + astra's B (algorithmic: exact concatenation of the SC1 DRAFT
    v2 section, the accepted AMENDMENT 1 text, and the reconciled sanitized author contract; byte ranges and hashes
    recorded); add a `snapshot` producer mode to scripts/sc1.py (V2).
(d) Adopt astra's A, D, E, F, H and fable's precisions for clauses 3, 6, 11 verbatim.

### 1. Registration identity and snapshot

Stage 1 is a JSON object with `status: "REGISTERED"`, a unique `study_id`,
absolute `execution_root`, `trunk: "4b"`, `science_snapshot_path`, `science_hash`,
`science_parts`, `deployment`, and `authors`. `science_parts` contains the three
ordered provenance records emitted by `snapshot`; the companion
`data/sc1/registration-snapshot.json` is also manifest-bound.

`science_snapshot_path` is `data/sc1/registration-snapshot.md`; `science_hash` is its SHA-256. The snapshot is
produced mechanically at freeze time as the exact bytes of LEDGER-PLAN.md from the line beginning
`## SC1 — LEARNED vs RULE SELECTOR, BENCHMARK-FREE FROZEN-POLICY COMPARISON (DRAFT v2` through the end of that
file (which at freeze includes this amendment), immediately followed by the exact bytes of
data/sc1/AUTHOR-CONTRACT.md, with nothing inserted; the two part lengths and the file hash are recorded in the
handoff. It is regenerated, and the executable manifest re-frozen, whenever that ledger section or the contract
changes before Stage 2; after Stage 2 the snapshot is byte-frozen and later LEDGER-PLAN.md entries do not affect
any manifest or test. The Stage 1 JSON file is byte-frozen after registration; its SHA-256 (`registration_hash`)
is bound into the study identity by every consumer.

At Stage 1 freeze, science_snapshot_path is data/sc1/registration-snapshot.md and science_hash is its SHA-256. The snapshot is the exact concatenation, with no inserted bytes, of (1) the SC1 DRAFT v2 section, (2) the accepted SC1 AMENDMENT 1 text, and (3) the reconciled sanitized author contract. Record each source path, source commit, half-open byte range, byte length and SHA-256, in this order, in the Stage 1 registration. Exclude subsequent editorial ledger entries using these frozen boundaries. The executable and production manifests bind these same snapshot bytes and the corresponding author contract/grammar hashes. The eff241b snapshot predates Amendment 1 and must be replaced prospectively; regenerate and verify the executable manifest before accepting Stage 2 or authoring any production source. Snapshot tests use the recorded byte boundaries, not the entire future tail of the live ledger. Only the sanitized contract, assignments and original grammar are sent to authors; the science snapshot and reviews remain private.

The following boundary rule reconciles the mechanical initial through-EOF recipe
above with the three-part law: at this amendment's initial freeze it is the final
ledger section, so both recipes produce identical bytes. The producer locates the
exact DRAFT v2 heading and this amendment heading, uses the v2 bytes up to this
heading and the exact adopted amendment length, then appends the contract bytes.
Later editorial sections are excluded; their presence does not extend a frozen
range. `CUDA_VISIBLE_DEVICES='' uv run python scripts/sc1.py snapshot` records
half-open byte offsets, lengths, SHA-256 values and full source commits for all
three parts. Commit source ranges first; the producer verifies their committed
bytes. It inserts no separator or metadata in the Markdown snapshot. Copy its
`parts` array into Stage 1 `science_parts`; every consumer checks that array against
the executable manifest. The sidecar is provenance, not a fourth snapshot part.

`deployment` must equal the executable manifest block: bfloat16,
hf_compatible, temperature 0, greedy true, max_new_tokens 256, deadline 300,
eos_ids [151645,151643], nonthinking_opener as frozen, one resident initialization
per invocation/no warmup, max_prefix 2048, max_query 1024, position_guard 40960.
Stage 2 hashes the actual 4B checkpoint, tokenizer, configs, executable code,
dependencies, parser, grammar and filler bytes.

`authors` has exactly kimi-k3, fable, gpt-6-astra and Opus keys. Each value includes
`provider`, `immutable_version`, `settings` (temperature, top_p, reasoning_effort,
max_output_tokens, seed_support), exact `neutral_template`, `contract_hash` and
`grammar_hash`.
The provider seed is the unsigned integer represented by the first eight hexadecimal digits of the current content attempt's authoring-stream SHA-256 digest. Retain that mapped value for every attempt. Apply it exactly when the frozen provider supports seeds; otherwise record that it was not applied. Do not substitute the author version, settings or seed mapping.

### 2. Registry and audit receipt

One study has one absolute execution root; relocation is refused. A durable
per-checkout registry at `.git/sc1-studies` binds study and source-fingerprint
ownership; new registrations require new production sources. This is a local
trusted-operator guard, not a global cross-checkout uniqueness service. Each stage
binding publishes an immutable `registration-audit.<stage>.json` with the study
ID digest, registry location/hash, complete entry (including manifest IDs) and
source-owner file hashes, and appends those bytes to WORKLOG.md. The receipt
captures the registry at that binding, not an assertion that mutable registry
bytes never change when another stage is bound. Review that audit before launch.

The receipt is appended to WORKLOG.md by the consumer itself; that append is committed with the run's artifacts.
A CPU registration-binding/audit step and its review must precede model allocation.
Run production consumers only when no coder/reviewer wrapper holds `.review.lock`.

### 3. Exclusive execution-root lock

All determinism/setup/final consumers and analysis (which may recover journals or
publish pairs) acquire a nonblocking exclusive execution-root lock before opening
mutable journals/meters or constructing a backend, and retain ownership through
final durable publication. A second owner is refused immediately; no waiting,
unlinking the lock inode, or process signalling. Root binding alone is insufficient.

The lock is an advisory `flock` on `<execution_root>/.execution.lock`, valid on the executing host only; the registered absolute `execution_root` must be a local filesystem path.

### 4. Source geometry and pressure

Freeze FILLER_VERSION SC1-incidental-v2, the 512-item
subject/verb/place sentence pool and its manifest hash. Sample without replacement
within each episode using the filler seed. Expand designated non-evidence,
non-trace turns round-robin, covering user/assistant/tool roles. Every authored
base and every final rendered history turn is at most 600 tokenizer tokens in
its text (chat delimiters are counted in rendered history, not that text cap).
Designated turns × 600 must exceed 4608 minus rendered base history, with room
for existing base text and whole-sentence packing; typically at least eight turns
are needed. The expander reports base tokens, usable capacity and a lower bound
on total turns needed. The history minimum is checked after each round-robin
batch, so 4608 is a minimum target, not an exact length; eff241b smoke observations were
approximately 4620–4699; these are historical measurements, not an acceptance range. Full acceptance still requires history 4096–8192,
U >= 2B and at least one actual budget skip. No causal evidence is moved or
relabelled to fit. Grammar capacities/complexity limits apply before source freeze.

`filler_turns` are zero-based indices into authored `turns`, excluding the system
prefix. The expander must never place formulaic filler as the newest eligible old
user turn. Define that turn using the common, unscored candidate builder after
expansion: the greatest user message index with at least one complete candidate
piece inside the removable old range; a straddling turn can qualify. If such a
turn exists it must not be filler-designated and none of its text may contain a
sentence from the frozen formulaic pool, including author-supplied base text.
The expander and bank validator reject violations and report the index. They do
not move evidence, silently skip filler placements, or choose a source according
to either policy's retention. A source must be repaired under its original factors.
Retain bank-consumer negative tests for both designated expansion and undesignated
base-text insertion, plus positive checks on all eight frozen smoke sources.

### 5. Induced population and cue disposition

Disclose the induced population: the eff241b smoke design's disclosed filler
occupied over 90% of candidate columns. Most retained rule pieces came from the
newest old user filler turn. OLD retention was therefore strongly determined by
author turn ordering; this setting may chiefly compare rejection of formulaic
filler against user-first recency. This is not a measured classifier advantage
or a general claim about realistic histories. Production authors remain blind.

Report per episode candidate_columns, real_candidate_columns, B, budget skips,
echo omissions, role/position geometry and per-arm pin composition (pieces and
columns from designated filler turns versus other turns). Here "real" means
non-designated-turn provenance, not semantic necessity; original base prose in a
filler turn counts with that turn. The smoke README carries the concrete
role/position/wording audit and measurements.

The eff241b smoke audit documents a potential relevance shortcut: formulaic filler dominates old candidates and occupies the newest eligible old user turn in all eight smoke sources. These fixtures establish mechanical pressure but do not establish compliance with the author contract's prohibition on relevance revealed by marker, role or position alone. That prohibition remains binding. Stage 2 is deferred until an independent review of the frozen source/expansion law and disposable smoke evidence explicitly accepts compliance or a further prospective Stage 1 amendment specifies a narrower population and its claim limits. Any source-law or executable repair occurs before production authoring, uses no policy/model outcomes, preserves factor assignments and is followed by smoke validation and re-freeze. Neither a high U/B ratio, mixed roles nor this disclosure constitutes that acceptance. Do not select or reject a production source according to whether either tested policy retains its evidence.

The next independent review round on this output performs that source/expansion
law and smoke-evidence review; no extra intermediate review round is required.
The new placement guard mechanically excludes the documented newest-old-user
shortcut, but does not certify absence of other role, position or wording cues.
The updated smoke README reports the candidate's measurements and remaining cues.

### 6. Evidence and public tool state

Every decisive fact and trajectory entry is a necessary,
obligation-linked dependency with a unique verbatim public evidence span. Every
trajectory event has user authority in an actual user turn and the assigned
scope. Continuing requires instruction; overridden requires superseded then
update; cancelled-or-completed requires obsolete then cancellation or completion;
switched requires switch then return. The full necessary dependency determines
age. Unsupported structures require repair within the original assignment.

This amendment narrows the author contract's general realistic-JSON-or-plain-text allowance for state-bearing returns. Every state-bearing public JSON block must be exactly the canonical {call,return} envelope on its own line in its chronological tool trace turn, with a return equal to finite-executor replay; no additional state-bearing block is allowed. Inspect complete multiline and nested values without discarding overwritten object members. Duplicate object names in public JSON blocks are invalid and cannot be treated as incidental prose. Incidental plain prose and non-state JSON may surround a valid envelope but may not purport to supply untraced state. Freeze this boundary in the sanitized author grammar and require bank-consumer regressions for duplicate-wrapper and multiline state before Stage 2 acceptance.

Typed answer inventories cover every payload/target literal and its necessary
evidence/obligation links. Independent reviews bind source and public-render hashes.

Only JSON-syntax blocks are mechanically checked; state-like non-JSON prose is a Stage 3 semantic-review item.

### 7. Fingerprints and independence flags

Fingerprints jointly alpha-normalize entities/literal equality classes and
unordered graph permutations. Reject unordered groups above eight entries or
more than 40,320 joint variants before source acceptance. Pair signatures bind
both source IDs/hashes and an independent reviewer session. Source-content hashes
exclude provenance/review to avoid circularity; complete provenance is separately
manifest-bound. Within-pool entity/identifier reuse is a Stage 3 review flag
(fable N8); cross-pool collisions are rejected. Flags do not certify independence.

### 8. Exact numeric law

JSON numbers are compared by exact finite value with booleans distinct; integral decimal spellings satisfy integer schemas. Supported number spellings have at most 1024 lexical coefficient digits, counting every digit before and after the decimal point, including leading and trailing zeros, but excluding sign, decimal point and exponent digits. The stored Decimal exponent must have absolute value at most 4096, and exact canonical serialization must also satisfy the coefficient/exponent limits. Unsupported spellings or construction failures are ordinary parser/schema-invalid outputs, retained and scored once without harness invalidation or retry. Representability is a property of the spelling as well as the value. Wrong-number negatives negate nonzero values exactly without Decimal-context rounding and replace zero with one.

### 9. Text edit permissions and semantic witnesses

Text tasks have `permitted_paths: []` and explicit nonempty zero-based
`editable_lines`. After the production newline/trailing-whitespace/blank-run
normalization, only replacements at those indices are permitted. The original
`initial_state` fixes the line count and every noneditable line. Both reference
and expected artifact must preserve that baseline before freeze; matching an
inconsistent oracle cannot waive permissions. `permitted_edits` is the reserved
implicit invariant. Insertion/deletion or a protected-line change is corruption,
including otherwise schema-invalid parsed text. Wrong values wholly inside an
editable line can fail the task without causing corruption.

Text old-ID/obsolete/cancelled witnesses store raw full artifacts in old_id_work, obsolete_work or cancelled_work on linked public trajectory entries. Compare reference and witness using the production text normalization and ordered line indices, never JSON parsing or JSON string quoting. A witness line is changed when its normalized value differs from the reference at that index; a value already present at another index is still a change. Require a distinct normalized artifact and every changed witness line in the linked event's public evidence, with the applicable assigned scope, schema validity and violation of its linked obligation. A legitimate reordering or repeated-value replacement must not be rejected merely because the set of line values is unchanged. Applicable attacks may not be relabelled inapplicable to bypass this validation.

A text wrong-entity witness includes `line`, `target_id`, `replacement_id`,
`evidence_id`, `output`, and `obligation_ids`: exactly one normalized line replaces
one occurrence of the target ID with a different declared entity ID; both IDs
must occur in the linked public evidence. It must remain schema-valid and violate
its linked obligation. No truly applicable attack may be relabelled inapplicable
to bypass unsupported validation. Six distinct negatives and full invariant
coverage remain required.

### 10. Author transport and retained attempt history

A fresh isolated session writes one source; up to two repairs
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

### 11. Determinism prerequisite

Use the two lexically first frozen smoke IDs in two fresh
processes, with both arms in each process: exactly eight retained observations.
Each cell binds deployment, frozen episode/input, initialization, token IDs and
immutable arm/output hashes; the certificate binds two closed, charged allocation
intervals. Every cell must complete generation without timeout/generation failure
and contain nonempty generated token IDs. Task success is not required; a
nonempty deterministic malformed answer can qualify. Cross-process token/input
equality is required separately for each source/arm cell.

A cell whose total wall time exceeds the 300 s deadline is recorded as `timeout` even if a full token stream was produced and does not qualify.

### 12. Abandoned work and separate cost reporting

No replacement of an incomplete or failed determinism schedule, and no selective additional output, is permitted under its study ID. The prerequisite is deferred or failed, with all retained outputs, incomplete work and allocation evidence preserved. This amendment adopts separate reporting of abandoned-study cost: the eight-hour cap applies cumulatively within each registered study, including its determinism, initialization, interrupted and resumed intervals. A newly named registration requires a new execution root and new production sources under v2; it is not automatic and cannot rescue outcomes from the abandoned bank. Before any restart, record predecessor study IDs, allocation artifact hashes, external loss evidence, abandoned GPU seconds and total cumulative SC1 program effort in WORKLOG.md and the new registration's cost disclosure. Preserve each predecessor's charged ledger; do not present the new ledger as total program cost or claim that all SC1 effort fits within eight hours. No cost reset or selective restart is authorized merely by an interruption.

### 13. Failure records and conservative cost projection

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

This amendment adopts projected_seconds = spent_allocated_seconds + remaining_initialization_seconds + remaining_arm_attempts * 1.25 * (t_prefill + 256*t_token + t_cpu + t_check + t_persistence), with the v2 scaling and retained maxima. t_persistence is the maximum measured arm-persistence overhead; the future initialization reserve is at least the maximum measured invocation initialization. Keep the separate 300-second per-attempt reservation and never lower retained maxima to reopen a refused budget.

Actual Qwen determinism and GPU timing remain unperformed, separately authorized
prerequisites; these CPU artifacts cannot certify either.

<!-- END SC1 AMENDMENT 1 -->
