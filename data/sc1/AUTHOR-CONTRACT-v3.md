# SC1 authoring contract — original delayed-use episodes (v2 with Amendment 1, 2026-09-04)

Data lineage: write new fictional sources for evaluation only. No episode, reference, checker, author response,
or setup result may be used for fitting, training, tuning, prompt selection, or policy revision. The 32 setup
episodes and 256 final episodes have separate sources and seeds under the same authoring distribution.

## Information boundary and session provenance

Write original, self-contained conversations requiring earlier information to complete a final task. Each source
is written in a fresh isolated session with no prior conversation, project memory, repository access, browsing,
retrieval, or tools. The complete input allowlist is this contract, the commissioning factor/seed assignment, and
the frozen original task/API and structured-specification grammar. These materials contain no worked benchmark
examples. A model family may be reused; an informed review, development, or prior authoring session may not.

Do not consult, paraphrase, imitate, or conceptually adapt any public benchmark or dataset, repository example,
experiment review, probe diagnostic, policy code/output, or prior project notes. Invent fictional entities and
incidental wording; generate names, 6–12-character identifiers and exact values from the assigned literal seed.
Do not use remembered task-specific project diagnostics even with every name changed. If your session contains
such information, disclose it and produce no source; commissioning must start a fresh isolated session.

Retain the complete authoring transcript, including every system/developer/user input, response and revision,
with session/request ID, exact model/provider/version, generation settings, input hashes, contract hash, seed
assignment, and an attestation of empty prior context and disabled external access. Attest per episode that no
benchmark item or derivative was consulted or imitated. Feedback may address contract compliance, source
distinctness, narrative-to-obligation correctness and checker validity only. It must contain no policy identity,
ranking, performance, preference, benchmark outcome, or diagnostic. Every revision and rejection is retained.
These controls establish task-time isolation; they make no claim about an author model's pretraining contents.

## Commissioning and independent factors

The commissioning sampler, not the author, assigns every factor independently: author family (kimi-k3, fable,
gpt-6-astra, Opus; probability 1/4 each); style (editing/tool-work; 1/2 each); decisive-fact origin (user/tool;
1/2 each); decisive-evidence age (old/recent; 3/4 and 1/4); governing-instruction scope (continuing, overridden,
cancelled-or-completed, switched; 1/4 each). Setup and final use the same exact frozen author versions, settings,
neutral prompts and probabilities, with distinct sessions and episodes. Assignment probabilities are not quotas.
Do not balance realized counts, correlate draws, swap authors, relabel age, or select factors to suit a story.

Sampler convention: master seed 20260904; derive each independent draw from SHA-256 of the UTF-8 string
`SC1-v2|20260904|POOL|INDEX|STREAM|ATTEMPT`, with POOL = smoke/setup/final, zero-based INDEX,
STREAM = author/style/origin/age/scope/authoring/literals/filler/order, and ATTEMPT initially 0. Use the first
two most-significant bits for the four equiprobable author/scope categories; the first bit for the two equal
style/origin categories; age is recent only for bit-pair 11. Categories follow the order listed above.
Record the complete digest and all realized assignments; separate streams supply model/literal/filler seeds
using the frozen compiler/provider mapping. Assignment streams always use ATTEMPT=0. A source-validity repair
increments the content attempt streams only, keeping the assigned author and factors. This is deterministic
pseudorandom sampling intended to implement the registered independent draws, not a proof of independence.

Each assigned slot permits at most three content attempts, with contract-only feedback and the same assignments.
An invalid source cannot be replaced by an easier factor cell. If a slot remains invalid, defer the whole study;
do not drop it or alter the mixture. Retain attempted and rejected sources, reasons and reviewer decisions.
Report realized counts by author, style, origin, age, scope and crossed cells, separately for setup and final.

## Episode shape and evidence

- Produce 12–24 scripted messages with user, assistant and tool roles, followed by one final user request.
  History length is 4,096–8,192 frozen trunk-tokenizer tokens after chat rendering, including history role
  delimiters and excluding the system/tools prefix, final request, echo and generated output.
- EDITING returns a bounded JSON patch or small text artifact of at most 40 lines. TOOL-WORK returns exactly
  one allowed function call against an isolated in-memory record store. Both require affirmative, nonempty work.
- Record the decisive fact, applicable instruction and every necessary override/cancellation/completion/switch
  event, with private turn/character pointers and renderer-computed token intervals. Origin describes the decisive
  fact's source, not governing authority: a tool result supplies data and never silently overrides a user rule.
- OLD means the decisive dependency lies wholly before the most recent 1,024 rendered history tokens. None of
  the information indispensable to resolving that dependency may be restated or semantically supplied in the
  recent suffix, system/tools prefix or final request, including by an assistant paraphrase. RECENT means the
  complete decisive dependency lies wholly within the suffix. For overrides, locate the currently governing
  update, not just the superseded first mention. The frozen renderer measures age before acceptance; a mismatch
  requires source-validity repair under the original assignment, never automatic relabelling.
- CONTINUING still applies; OVERRIDDEN is governed by the later user update; CANCELLED-OR-COMPLETED forbids
  performing the obsolete action but still requires a separate affirmative final result; SWITCHED moves to
  another task and returns while a persistent user instruction remains applicable.
- Supply 4–8 distinct distractor facts and benign transient chatter, mixing roles, age and durable-looking
  wording. Relevance must not be revealed by a special marker, role or position alone. Tool responses use
  the canonical state-return boundary below when state-bearing; incidental non-state prose
  and non-state JSON may surround a valid return. No policy-specific formatting guidance is allowed.
- The final request omits the tested earlier literal/rule. Neither it nor the system/tools prefix may contain
  any indispensable reference literal; private validation also checks semantic paraphrases. Generic schema
  keys and syntax are not answer literals. General tool schemas must not hard-code a target or answer value.
- All scripted events and tool returns must be consistent with a private state trace. `initial_state` is the
  complete state immediately before the final decision, after scripted events; it is never shown as an oracle
  snapshot. Only facts explicitly present in public turns are available to the evaluated model.

## Structured source specification and expansion

Author one compact original causal specification per episode (roughly 300–800 tokens is a planning target, not
a completeness limit). Shared grammar, executor/checker primitives and disclosed irrelevant filler are allowed;
shared instantiated stories are not. A frozen deterministic expander renders the long conversation, verifies that authored facts
already satisfy the assigned age, samples literals/filler from their streams and generates reference witnesses;
executable checkers and mutations are code-generated from this single specification. It must not invent a new decisive
rule or reuse a small scenario template bank as purportedly independent sources. The grammar, expander, original
tool families and filler pool are frozen before production authoring; no model-outcome feedback enters them.

Each episode record contains these fields (all but the four public renderer fields are private):

| Field | Required content |
|---|---|
| `schema_version`, `id`, `source_id`, `pool`, `index` | v2 schema, unique source identity, smoke/setup/final split and sampled slot. |
| `assignments`, `seeds`, `attempt` | Author and all independent factor draws; master/stream digests, content seeds and attempt history. |
| `provenance` | Exact author version/settings, prompt/contract hashes, session IDs, retained transcript/input hashes, isolation and originality attestations. |
| `domain`, `task`, `scenario_gist` | Domain tag, final-task one-liner and one-line causal story summary for cross-source review. |
| `entities`, `source_graph` | Fictional typed entities/relations; individually authored setting, task, governing rules, events and dependency edges. |
| `instruction_trajectory`, `decisive_facts` | Scope events, authority, active/superseded/cancelled values, original and rendered evidence coordinates. |
| `distractors`, `filler_manifest` | 4–8 original distractors; sampled filler IDs/seeds and shared-pool version, kept separate from decisive content. |
| `task_spec`, `initial_state`, `state_trace` | Output kind/schema, permitted operations and edits, full pre-decision state and consistent scripted event trace. |
| `obligations` | Stable obligation IDs, narrative evidence, required/forbidden outputs and target values, executable predicates. |
| `protected_set` | Explicit nonempty protected records/fields for tool-work; protected artifact fields/lines or forbidden extra keys/lines/content for editing; expected values/absence and invariant IDs. |
| `expected_artifact`, `expected_state`, `reference` | Complete oracle artifact/state and a serialized attainable reference output (unused style-specific fields explicitly null). |
| `checker`, `mutation_plan`, `mutations` | Generated executable predicates; six named attack slots with applicability/substitution and obligation IDs; additional coverage cases and their concrete outputs/state probes. |
| `system`, `tools`, `turns`, `final_request` | The ONLY public renderer inputs; `turns` contains ordered `{role,text}` messages and `tools` general schemas or null. |
| `layout_audit` | Rendered history/reference lengths, decisive-evidence intervals, assigned versus verified age, answer-leakage checks. |
| `source_fingerprint`, `distinctness_review` | Normalized structural fingerprint, pairwise semantic/collision checks, candidate/rejection trail and reviewer identity/sign-off. |
| `validation` | Reference and negative verdicts/causes, obligation/invariant coverage, reviewer constructs, compiler/runner versions and hashes. |

## Source independence audit

No sibling stories: changing names, identifiers, values, ordering or wording does not create a new semantic source
when the task, setting, governing-rule skeleton and instantiated event/dependency graph are shared. Each fresh
session writes one source only. Setup is a separate pool of EPISODES from the same author mixture; setup and final
share no story, entity, identifier, instantiated task or causal source. Generic domains/tool families may recur.

Record a normalized source fingerprint: serialize the semantic graph and scope/dependency trajectory as canonical
JSON; alpha-rename entity IDs by structural role, replace proper names and literal values with typed placeholders,
sort unordered collections, retain causal order and equality/inequality relationships, and SHA-256 the result.
The exact normalization/canonicalization algorithm is frozen with the compiler. Equal fingerprints require sibling
rejection; different fingerprints do not establish independence. Independently review all 288 `scenario_gist`s and
source specifications pairwise, with signed decisions on suspected siblings. Check proper-name and identifier
collisions across pools; regenerate colliding literals without changing the scenario or factors.

Record history 8-gram Jaccard overlap (Unicode NFKC, casefold, whitespace tokenization), excluding the system/tools
prefix and separately accounting for disclosed shared filler. Values >=0.05 flag pairs for semantic review, not
automatic source independence or rejection. Record author/domain counts without capping them. Generic primitives
and filler do not by themselves make siblings; a shared task+setting+rule graph does. Validity repair is allowed
only before episode freeze without policy/trunk feedback. After freeze, discovered source dependence invalidates
the independent-source interpretation; no pair may be dropped, relabelled or replaced after outcomes.

## Reference, executable checker and negative coverage

Generate executable declarative checks from the source spec: `state_equals`, `protected_unchanged`, `json_equals`,
`required_lines`, `forbidden_substrings`, `max_lines`, plus explicit obligation/invariant IDs. Compare parsed JSON
structurally (key order and whitespace irrelevant, numeric values equal across equivalent number spelling,
booleans type-distinct from numbers, strings exact). Require one bare JSON value/call for JSON/call tasks, with
no markdown fences or commentary; text tasks return raw text. Reject duplicate keys, non-finite numbers, unknown
fields, extra output and malformed framing. For text, normalize CRLF/CR to LF, strip trailing horizontal whitespace on
each line and collapse consecutive empty lines; apply the same normalization to the oracle and compare the
complete artifact plus all declared predicates. Freeze parser/framing details with the compiler before production.

The concrete reference, including required output/function-call framing, must fit within 256 tokens under the
frozen generation tokenizer and the additional 40-line ceiling where applicable. Tool-work executes exactly one
permitted call from a fresh copy of `initial_state`; validate syntax and types before applying any changes. Check
the COMPLETE resulting state, including non-target objects, creations/deletions and every protected invariant.
JSON patches are applied to a fresh base artifact and checked against the complete expected artifact; text outputs
are checked completely. One PASS requires a complete valid output and every obligation/invariant. A reject-all
checker, no-op, unchanged initial state, empty output, generic safe answer or unfinished output cannot pass.

Before freeze an independent reviewer runs the reference and all negatives through the SAME parser, executor
and checker runner that will consume model outputs, resetting state each time. Reference must PASS. The six
required attack slots are old-ID substitution, cancelled action executed, wrong entity, wrong scope, empty output,
and collateral edit. Each must yield a DISTINCT, APPLICABLE negative and name the actual obligation it violates.
For an inapplicable named class, predeclare its reason and a different obligation-linked substitute before running
validation: missing required field/object, wrong exact value, forbidden extra output, or incomplete artifact/call.
Use the first applicable unused substitute in that order; if six distinct negatives still cannot be constructed,
reject the source. Do not manufacture a cancellation/override merely to satisfy an attack label.

All six negatives must FAIL; identical outputs, unchanged references and a collection of parser errors are not
coverage. Include type-valid wrong-target/wrong-state cases. Exercise every obligation and protected invariant with
a targeted violating output, or a complete-state probe when that violation is unreachable through the allowed
API; those probes use the same final-state checker and do not replace the six executable output negatives.
Add negatives beyond six when needed for full obligation coverage. Check unchanged initial state/no-op explicitly.

The reviewer independently checks narrative-to-obligation correctness; agreement between a generated witness and
generated checker alone is insufficient. Per episode, add a reviewer-constructed generic safe response with no
episode-specific content that must FAIL; for OLD episodes add a best-effort recency-only response using just the
public prefix, last 1,024 history tokens and final request that must FAIL. These additional constructs never replace
the six negatives. Reviewers use no tested policy or trunk outputs. Record all verdicts, causes, evidence/coverage
links and sign-offs before hashing. References, checks, mutations, factors, evidence annotations, provenance and
hidden states never enter model, policy or echo inputs.

## Operational source and transport requirements (2026-09-04)

The provider seed is the unsigned integer from the first eight hexadecimal digits of the current content
attempt's authoring-stream SHA-256 digest. Retain it for every attempt, apply it exactly when the frozen
provider supports seeds, and otherwise record non-application. Use the same frozen version/settings.

The supported transport supplies no system/developer inputs. If the provider necessarily supplies any such
input, expose it for contract/grammar reconciliation before registration; never omit it from a transcript.
Retain a cumulative JSON transcript with session_id, provider, version, settings, input, response (the exact
source object), and messages containing the exact alternating user-input/assistant-source pairs from attempt
zero through the current attempt. Repairs resume only that source's original isolated session, at most twice.
The operator retains every request, transcript and decision and a hash-linked attempt_history with attempt,
previous entry hash, prior rejection feedback, reconstructed request_hash, transcript_path/hash, source_hash,
decision, reason and reviewer (rejections require both reason and reviewer). Only the commissioned *.input.json
is delivered as author input; the separate operator envelope and private repair-history files are not inputs.

Every decisive fact and scope event must be necessary, linked to an obligation, and have a unique verbatim
public evidence span. Scope authority is in an actual user turn. Continuing requires instruction; overridden
requires superseded then update; cancelled-or-completed requires obsolete then cancellation or completion;
switched requires switch then return. The complete necessary dependency determines age.

Every state-bearing public JSON block must be exactly the canonical {call,return} envelope on its own line in
its chronological tool trace turn, with return equal to finite-executor replay. No additional state-bearing
block is allowed. Complete multiline and nested values are checked. Duplicate object names in any public JSON
block are invalid, including overwritten nested members; they cannot be incidental prose. Non-state JSON and
incidental plain prose may surround a valid envelope but may not supply untraced state. State-like non-JSON
prose remains an independent semantic-review responsibility.

Use the frozen 512-sentence filler pool without replacement. All authored bases and all expanded history turn
texts must fit 600 tokenizer tokens each; rendered chat delimiters count separately in history. Designate
mixed user/assistant/tool non-evidence, non-trace turns. Designated turns times 600 must exceed 4608 minus
rendered base history, allowing existing text and whole-sentence packing (typically at least eight turns).
Expansion is round-robin to at least 4608 rendered history tokens, checked after each batch. The compiler
reports capacity and a lower bound on turns needed, and validates candidate pressure before accepting a source.
Never designate the newest eligible old user turn for filler or place any pool sentence anywhere in its text,
including its authored base. This is the latest user turn with any complete source piece in the removable old
range after rendering; a turn crossing the recent boundary can still qualify. Repair placement failures under
the original assignments without moving causal evidence. The relevance rule above remains binding, including
recognizable filler; these geometry checks do not establish semantic compliance.

Typed answer inventories must cover every payload/target literal and its necessary evidence/obligation links.
Fingerprint normalization jointly preserves literal equality classes and unordered graph permutations; groups
above eight entries or more than 40320 joint variants are rejected. Independent pair signatures bind both
source IDs/hashes and reviewer session; source/render hashes bind each semantic review. Within-pool literal
reuse is a review flag and cross-pool entity/identifier collisions are rejected. Flags do not prove independence.

JSON numbers have exact finite values with booleans distinct; integral decimals satisfy integer schemas.
Supported spellings contain at most 1024 lexical coefficient digits, including every leading/trailing zero
before/after the decimal point, excluding sign, decimal point and exponent digits. The stored Decimal exponent
has absolute value at most 4096; exact canonical serialization must satisfy the same limits. Unsupported
spellings/construction failures are ordinary schema-invalid outputs; representability depends on spelling too.
Wrong-number negatives negate nonzero values exactly without context rounding and replace zero with one.

Text tasks require permitted_paths: [] and nonempty zero-based editable_lines. After the production text
normalization, only replacements at those indices are permitted. Original initial_state fixes the line count
and all protected lines; the reference and expected artifact must preserve that baseline. Insertion/deletion
or protected-line changes violate permitted_edits even if the parsed output is otherwise schema-invalid.
Text old_id_work, obsolete_work and cancelled_work fields contain raw complete artifacts. Compare normalized
reference and witness at ordered line indices. A value reused from another index still changes that line;
reordering or repeated-value replacement is not set equality. Require a distinct normalized artifact and every
changed witness line in the linked event's public evidence, the applicable scope, schema validity and a failed
linked obligation. Do not mark applicable attacks inapplicable to bypass validation. Text wrong-entity witnesses
specify line, target_id, replacement_id, evidence_id, output and obligation_ids: exactly one normalized line
replaces the unique target ID with a different declared entity ID, both in the linked public evidence; the
artifact must be schema-valid and violate its linked obligation. Six distinct negatives and full coverage remain
required.
