# Disposable SC1 harness fixtures

These eight fictional sources were written for this implementation by an informed
harness session. They are not isolated production authoring and must never be
reused for setup or final. The recorded author/factor draws exercise the sampler;
they do not claim those providers authored these fixtures. Independent semantic
review, author construction effort, and model determinism are not certified here.

CPU commands:

```
uv run pytest -q tests/test_sc1.py tests/test_eval_data_separation.py tests/test_sealed_guard.py tests/test_no_side_effect_imports.py
uv run python scripts/sc1.py validate data/sc1/smoke
uv run python scripts/sc1.py smoke
```

`smoke` validates all eight sources, writes the expanded episodes and validation
report, exports the original source/API grammar and exact power enumeration, and
writes an executable manifest. It loads a tokenizer and hashes checkpoint bytes;
it never instantiates a model. Code must be committed before manifest creation.
`manifest_id` hashes canonical manifest content excluding that field; the file's
ordinary SHA-256 additionally covers the field and trailing newline.

The original grammar is exported as `grammar.json` from `SCHEMA` in
`src/stencil/sc1_episodes.py`. Record operations are create/update/delete/get/list;
editing supports object-only JSON-pointer patches or complete raw text. Patch
arrays are bounded to 40 operations and 40 output lines; text has 40 output lines.
References use the same parser, executor, complete-result checker and explicit
protected predicates as generated outputs. Source-provided attack witnesses are
compiled with deterministic, ordered substitutes for inapplicable slots.

The renderer writes Qwen message delimiters directly and derives token boundaries
from one encoding's offsets. Tool results retain semantic tool roles even inside
the native user wrapper. SC1's bare JSON call requirement is stated in the system
block; native XML function-call framing is not accepted by this grammar. Final
message indices refer to zero-based public history messages, excluding the system
prefix. Filler v2 contains 512 distinct sentences (16 subjects × 4 verbs × 8
locations), disclosed in the compiler. Seeded sampling without replacement
spreads it round-robin across mixed user, assistant and tool non-evidence
turns, typically at least eight: designated turns × 600 must exceed 4,608 minus
rendered base history, allowing room for bases and whole-sentence packing. Every
authored base and final history turn is capped at 600 text tokens. The 4,608-token
history minimum is checked after each round-robin batch; it is not an exact length. It cannot move causal events or relabel age. Validation requires
candidate columns >= 2B and at least one rule budget skip. `validation.json`
records candidate columns, B, rule budget skips and echo omissions for each source.
The smoke audit also checks segmentation against LEG A with the real tokenizer
and verifies that constant-one classifier ranking produces different pins from
rule ranking. These are pressure/implementation checks, not model results.

For future production use, `validate BANK --freeze --stage1 FILE
--executable-freeze FILE --out DIR` creates a manifest after all 288 sources and
independent source reviews exist. Exact served author versions/settings and
retained transcript hashes are mandatory. Pairwise review keys use source IDs in
lexical order. Signatures bind both source IDs and both `source_spec_hash` values, plus the
independent reviewer/session and decision (content excludes review and provenance
metadata); the manifest separately hashes full source bytes, avoiding
circular signatures between reviews. The `commission` command exports a neutral
request envelope for an external fresh-session provider transport; it makes no
provider requests and cannot attest to provider-side context isolation.

`determinism --stage1 REGISTERED --manifest EXECUTABLE --out REGISTERED_RUN`
records four outputs per fresh process. Exactly two invocations form the eight
cells (two frozen smoke sources × two arms × two fresh processes). The verifier
checks retained full arm/output artifacts, episode/deployment/input hashes,
cross-process token identity, and an immutable allocation snapshot. An interrupted
partial process cannot be replaced by extra smoke generations under this schedule.
CPU tests exercise this producer twice in subprocesses with a fixed-token fixture;
they are not model determinism evidence.

`setup` requires the frozen production manifest and that model-determinism
certificate (two fresh processes, two smoke sources, two arms, eight outputs).
It generates only full/evicted outputs and measures clf/rule CPU paths. Its
certificate must be committed before `final` or `analyze` can read final outcomes.
`final` writes each arm durably, then its pair, and publishes a complete seal only
at 256 pairs. `analyze` refuses incomplete, changed, ungated or over-budget runs.

An external interruption is not an ordinary timeout or a failed response. Resume
uses `--interruption-evidence FILE`: allocation_id, infrastructure reason
(host_loss/process_loss/device_loss/resource_loss), total elapsed allocation,
external evidence, and an attempts array with episode_id/arm/attempt_id/elapsed.
Previously accounted time cannot decrease; completed arm bytes cannot change.
Device/resource exceptions retain an open attempt and require interruption
evidence before resume; completed generation failures are immutable scored rows.
Harness defects invalidate the bank. A hash-bound prepared output is recovered
without regeneration even when the subsequent journal append was interrupted.
Torn journal bytes remain in place with a durable recovery proof and appended
recovery event. No locks are waited on and no
process is signalled. The allocation ledger charges initialization, selector work,
checking, persistence and idle time while the allocation is held.

Production and determinism enforce Qwen3-4B before loading. Stage 1 must bind
`study_id`, an absolute `execution_root`, the science hash, exact deployment,
author versions/settings and contract/grammar hashes. A durable registry under
`.git/sc1-studies` binds that identity to its executable and production manifests.
The registry also binds production source fingerprints across study IDs: a new
registration cannot reuse an earlier causal source. Every invocation uses the
same directory and cumulative cost ledger. Changing
`--out` is refused; relocation is deliberately unsupported. Invalid, failed-setup
and cap-exhausted studies cannot restart through a new output path. `--out` is
required for setup/final/analyze/determinism/commission; CPU validation/smoke
output defaults to the supplied bank directory.

The grammar now requires typed answer literals linked to decisive evidence and
obligations, including call target IDs. Scope events require actual user turns;
state-bearing tool returns use canonical `{call,return}` envelopes reconciled with
the trace. JSON numerics stay exact Decimal values; integer schemas accept any
integral numeric spelling, with booleans distinct. Text permissions list editable
line indices, forbid insertion/deletion, and expose the `permitted_edits`
invariant. Negative identity uses canonical parsed JSON or production text
normalization; named obsolete attacks bind public source evidence. Review
signatures bind source and public-render hashes, and production sessions are
unique across sources. `commission --attempt N --history FILE` requires every
prior rejected request/transcript; repair transcripts retain the cumulative
input/response messages from the isolated author session.

Failure taxonomy: T excludes an EOS-terminated 255-token answer. The registered
four-token repetition detector covers periods 1, 2 and 4; R=0 does not establish
absence of other loops. Only the attention and residual intervention counters
have callable instrumented paths and appear in output records. SC1 has no
scope-resolver or digest intervention call path; no measured zero is claimed for
those absent functions.

These grammar/enforcement interpretations are listed as Stage-1 ambiguities in
WORKLOG.md. LEDGER-PLAN.md and the author contract are unchanged.
Neither production source commissioning nor model execution is authorized by this
CPU implementation handoff. Stage 1 is still prospective text; this directory is
an executable-freeze candidate, not a registration or a production setup pass.

## V3 pressure and cue audit (CPU, 2026-09-04)

`validation.json` now contains a per-episode `pressure` report. Each episode's
`layout_audit` includes `real_candidate_columns`, rule pin composition, and each
turn's role, position, token count, filler designation and necessary-evidence
status. Runtime arm records retain pin composition for both policies;
`analysis.json` reports it per episode/arm. "Real" here means a non-designated
turn, not semantic relevance. Original incidental base prose in a filler turn
counts with that turn. No classifier/model results were used in this audit.

| Episode | U columns | Real columns | B | Rule budget skips | Echo omissions | Rule filler/total pieces | Max turn tokens |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| smoke-00 | 2303 | 47 | 256 | 207 | 12 | 26/27 | 462 |
| smoke-01 | 2075 | 83 | 256 | 185 | 12 | 26/27 | 505 |
| smoke-02 | 2086 | 78 | 256 | 184 | 12 | 26/26 | 508 |
| smoke-03 | 2314 | 45 | 256 | 209 | 11 | 25/25 | 459 |
| smoke-04 | 2255 | 0 | 256 | 204 | 11 | 26/26 | 461 |
| smoke-05 | 2489 | 149 | 256 | 221 | 11 | 25/26 | 571 |
| smoke-06 | 2327 | 45 | 256 | 208 | 11 | 25/26 | 468 |
| smoke-07 | 2448 | 0 | 256 | 224 | 11 | 26/26 | 504 |

Role audit: all eight histories mix user, tool and assistant filler turns, but
only user/tool pieces enter U and user pieces have priority in the comparator.
Every governing event is in a user turn. Mixed roles do not remove the resulting
priority advantage for irrelevant old user prose. The largest turn is 571 tokens;
every authored base and final expanded history turn is now mechanically checked
against the 600-token text cap.

Position audit: the OLD dependencies occupy turns 0–2, with smoke-05's additional
canonical tool trace at turn 5; RECENT dependencies occupy turns 9–10 (smoke-04) and 8–10 (smoke-07). The newest
eligible old user turn is filler-designated in each smoke source. The comparator
therefore admits 25–26 filler pieces plus zero or one short non-designated piece,
and no complete OLD necessary evidence span. Pins overlap four governing-evidence
columns in smoke-00 and smoke-01, six obsolete-event columns in smoke-05, and
three governing columns in smoke-06; all decisive-fact intersections are zero.
This distinguishes fragment retention from complete dependency retention.
Real candidate content is only 1.9–6.0% of U on
OLD sources; RECENT evidence is in the suffix and contributes no old candidates.
U/B is 8.11–9.72 and every episode has a budget skip. These are measured smoke
geometry properties, not a constraint imposed on production author turn order.

Wording audit: shared filler uses the explicitly disclosed subject/verb/place
sentence template. Governing messages contain direct edit/cancellation/switch
instructions and exact seeded values; irrelevant prose has markedly different
wording. This gives a potential relevance cue even without a special marker.
The smoke geometry makes the pressure predominantly a competition against that
formulaic filler. These cues require prospective Stage 1/2 reconciliation with
the contract's no-position-only-relevance requirement; this audit does not
certify its absence or establish independent production sources. The proposal in
`../STAGE1-CLAUSES.md` records that limitation without changing the governing text.

V3 manifests bind `../registration-snapshot.md`, the byte concatenation of the
SC1 DRAFT v2 section and author contract, rather than the live ledger. Live
editorial notes cannot invalidate those hashes. Snapshot changes still invalidate
the freeze. This is a candidate snapshot; the proposal clauses have no effect
until the orchestrator adopts/reconciles them prospectively.

Commissioning publishes only author-visible input in `*.input.json`, with both
canonical input and file hashes recorded in the separate `*.request.json`
operator envelope. Private order streams remain in that envelope. The durable
registry remains local to `.git/sc1-studies`; each registration produces an
immutable execution-root audit receipt and a WORKLOG entry with registry and
source-owner hashes. Within-pool identifier reuse is explicitly reported as a
Stage 3 review flag; across-pool reuse remains a rejection.

QwenBackend itself returns timeout or raises exceptions; `GenerationFailure`
is currently exercised only by CPU fixtures. RuntimeError messages containing
cuda/nccl/device/out-of-memory indicators are provisionally infrastructure errors,
including possible harness bugs, and need operator evidence before missing work
can resume. Analysis carries this disclosure, the limited R periods, and the
absence of scope/digest execution paths. The determinism verifier requires
completed nonempty generated token observations, not successful task answers;
eight empty timeouts cannot qualify. No actual model determinism or GPU timing
has been performed by this CPU task.
