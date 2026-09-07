# Independent updater code review — Astra

Reviewer: `gpt-6-astra`, xhigh, native session `/root/updater_accuracy_review`,
2026-09-07. Author-disjoint from Sol's implementation. The current explicit
user instruction selects Astra xhigh in place of the historical Opus rule;
this is a user-directed reviewer substitution, not an availability fallback.

Scope: the isolated DEV one-call updater/compiler and its targeted tests.
Threat model: trusted but fallible model/host, including malformed model JSON.
This review does not cover production authentication, the unfinished driver,
semantic scoring, generalization, or a GPU run. Read AGENTS.md, archived
PLAN/PROTOCOL, current ledger STATE, DEV-UPDATER-CHECK.md, USER-CORRECTION.md,
and UPDATER-CONTRACT.md. Only this review file was written; no code edits,
commits, network/model calls, held-out reads, or frozen-result changes.

## Round 1

Score: 84/100

Decision: changes required before prompt freeze/model calls. One open high and
one open medium finding. The core compiler is small and its ordinary rejection
paths work; the missing model-facing wire contract is the launch blocker.

Reviewed SHA256:

- `src/stencil/focus/maintenance_updater.py`:
  `19c07be092a9d0e40f238b690d41fec805d2df5b17fb886a8d1a338d91808514`
- `tests/test_focus_maintenance_updater.py`:
  `dbc61073affd11568c2ae4a69a7e7ebdd752bf44cda73bc3d28dfac6fd8fb2b6`

### updater-code-review-astra#1 — High: the cold prompt omits the strict operation schema

(Resolved 2026-09-07, Round 2: exact prompt schema and transition instructions
verified against the actual compiler; original finding retained below.)

Location: `maintenance_updater.py:156–181`, versus compiler requirements at
`262–288`, `303–341`, and `register.py:43–56,147–157,328–387`.

The first call starts with empty state, so the model has no example from which
to discover the required wire format. `response_schema.operations` is just a
prose string. The prompt names `scope`, `kind`, and `evidence_span` without
defining the scope object's mandatory `task_handle`/`request_kinds` fields,
the allowed request-kind or entry-kind vocabularies, or the span's two-integer
array shape. It does not explicitly show `action` among each action object's
required fields. The add-field instruction also calls a field “literal value”
without supplying a complete object schema. Reasonable semantic responses
such as `scope:"global"`, `kind:"constraint"`, or
`evidence_span:{"start":0,"end":24}` are deterministically rejected. Each was
reproduced through `execute` using an otherwise valid synthetic add.

The prompt also leaves important legal transition semantics in hidden Python:
task-local shadowing uses the same key plus a narrower **add**, supersedes
must preserve target scope, versions increment per key across its scopes,
and reinstating a retired version while a replacement remains live requires
retiring that replacement first. In a one-response/no-retry experiment, the
model cannot discover these constraints through feedback before its mistakes
enter the trajectory. This confounds maintenance interpretation with guessing
an unpublished API, even though the host correctly rejects the proposals.

Required correction: publish a complete gold-free operation schema in the
frozen prompt, with field types, required/forbidden fields by action, enum
values, null/global and empty-request-array meanings, span bounds, new-key
references, and concise lifecycle rules. Include the applicable size caps.
Add a CPU contract test on an empty register showing that the supplied schema
actually describes accepted operations and shadow/restore sequences through
the consumer. No gold keys, labels, or DEV-specific answer examples are needed.

### updater-code-review-astra#2 — Medium: escaped Unicode values bypass the rejection receipt

(Resolved 2026-09-07, Round 2: Unicode validation and protected candidate hashing
verified with both original triggers and a valid transaction prefix.)

Location: `maintenance_updater.py:283–288,428–444`.

A JSON string containing an escaped lone surrogate is accepted by `json.loads`
and `_literal`. An otherwise valid add with `value="\ud800"` or
`text="\ud800"` therefore creates a candidate register. Post-state hashing at
line 443 encodes that string as UTF-8 and raises `UnicodeEncodeError` outside
the proposal exception boundary. `execute` returns no `UpdateResult`, loses
the promised rejection receipt, and can abort the scheduled DEV trajectory.
The original immutable register remains unchanged; this is a receipt/failure
containment defect, not partial application. The narrow Unicode trigger is
why this is medium rather than high severity.

Minimal CPU reproduction, using either field:

```python
state = Register(task_handles={"A"})
source = Message("m1", "user", "Use Python.")
base = build_prompt(state, source).base_state_sha256
operation = {
    "action": "add", "key": {"new": "language"},
    "scope": {"task_handle": None, "request_kinds": ["code_answer"]},
    "kind": "language", "value": "\ud800", "text": "Use Python.",
    "evidence_span": [0, len(source.text)],
}
raw = json.dumps({"base_state_sha256": base, "operations": [operation]})
execute(state, source, lambda _: raw)  # raises UnicodeEncodeError
```

Correction: validate serializable Unicode strings and/or include candidate
post-state serialization/hash generation in the atomic rejection boundary.
Retain the raw response, original register, unchanged hashes, empty accepted
operations, and an error receipt. Cover both value and text through `execute`;
include a mixed valid/invalid transaction to preserve the atomicity guarantee.

### Verification and positive evidence

- Independently ran `CUDA_VISIBLE_DEVICES='' uv run --no-sync pytest -q
  tests/test_focus_maintenance_updater.py tests/test_focus_maintenance_bank.py`:
  **23 passed**. Scoped ruff and diff checks are clean.
- Existing tests exercise exact targets, mixed-transaction failure, stale
  hashes, host key allocation, tool/assistant authority denial, completion
  exclusion, Unicode offset bounds, and decoder exceptions through `execute`.
- Additional synthetic consumer probes reject undeclared handles, boolean
  span offsets, duplicate request kinds, and the unpublished wire-format
  alternatives listed in #1, with unchanged state and retained raw responses.
- A synthetic `Message.entries`/`adopted` poison does not change prompt bytes.
  The updater imports no bank/gold source and only serializes natural envelope
  fields plus the supplied register. No hidden expected-operation interface
  was found. Pending proposals independently change the base hash.
- Full version/retirement state is shown; non-user direct messages still call
  the decoder once and cannot mutate state; completion is excluded. These are
  transport/transaction guarantees, not evidence of semantic correctness.
- A 4,000-level JSON nesting probe within the response cap returned a normal
  rejection in this runtime. No unsupported recursion-failure claim is made.

The two fixes above are bounded prompt/receipt changes. This review requests
no production migration, new architecture, scorer expansion, or extra model
calls. Freeze the corrected hashes and recipe only after re-verification.

## Round 2 — 2026-09-07

Score: 94/100

Decision: accepted for the isolated DEV updater/compiler scope. Findings #1
and #2 are resolved; no open high/critical findings or new findings. This
acceptance does not review the separate driver or authorize a model launch.
Round 1's score, original findings, and evidence are preserved above.

Re-reviewed SHA256:

- `src/stencil/focus/maintenance_updater.py`:
  `151b114351de2d062adac0327acb37cdce568460473d18cd99e4cc8f02af0594`
- `tests/test_focus_maintenance_updater.py`:
  `05c27291ca53fa8ac0b31e96fc120e3e47ae33ead63b57a16a82865938596fc4`

For #1, the empty-state prompt now supplies closed per-action JSON objects,
mandatory action/target fields, opaque and new-key reference forms, scoped
handle values, kind enums, source-dependent integer span bounds, literal
types, size limits, and explicit global/task shadowing and ordered
cancel/reinstatement instructions. The declared scope restriction is
`request_kinds: []` or the current request kind; the compiler enforces that
same restriction. Thus acceptance is for this DEV recipe, not arbitrary
updates spanning other request kinds. The schema exposes no expected keys,
gold values, or author explanations.

The new empty-state test checks all four action shapes and sends a conforming
add through `execute`. I additionally exercised a single synthetic sequence
of global add, task-local add, task-local supersedes, cancellation of the
replacement, and reinstatement of the earlier local version. Required-field
sets were checked against the actual prompt variants. All five operations
were accepted; versions were 1–4; task A resolved to restored Rust while task B
retained global Python. This verifies the newly documented ordering and
scope semantics through the consumer rather than only checking prompt words.

For #2, `_literal` now validates strict UTF-8 scalar text and candidate
post-state hashing is within the proposal rejection boundary. I reran both
escaped-surrogate triggers after a valid add prefix. Each returned the raw
response, original register identity, equal pre/post hashes, empty accepted
operations, and a useful rejection reason. No exception escaped. Empty text,
which the updated schema permits alongside null, is accepted consistently.

Independent validation: the updater and bank targeted suites now total
**26 passed**; scoped ruff is clean. The separately reported integrated
30-test result includes driver tests outside this review, so it is not
represented here as independently reviewed driver evidence. No additional
model calls or code changes were made by this reviewer.
