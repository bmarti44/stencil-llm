# Staged source-replay preparation — prospective draft

2026-09-08. DRAFT, not accepted; no authoring or scientific launch yet.
Decision basis: ../source-preparation-research/report-source.md. The earlier
source-replay bank remains stopped and excluded. This is a new preparation
attempt for the same automatic original-source reminder hypothesis, with an
explicitly different request-authoring process. No outcomes may be pooled.

## Inherited science and exact changes

Retain ../source-replay/SPEC.md, DATA-CONTRACT.md and the scientific parts of
SCREEN-IMPLEMENTATION-BRIEF.md: four independent projects, three rounds, H/S/R,
original local Qwen3-30B-A3B, full authentic histories and persistent per-arm code,
same selector/worker prompts and interfaces, 128/1024 output caps, selection and
recent-source allowance, arm rotation, 48 generation calls, scoring and practical
gate, 3000-second screen ceiling, cost projection, incomplete/failure handling,
and larger untouched proof requirement. The two-call qualification is historical
accepted evidence; do not rerun it or claim a full-screen affordability result.

Overrides apply only to this new bank:
- Kimi authors one source scaffold and three round packets per project instead
  of one whole project. Deterministic assembly adds administrative fields.
- The exact current request is `Update {symbol} in module.py to implement the
  latest changes described in our conversation while preserving all still-applicable
  behavior.` This is one line with single spaces; substitute the existing target
  identifier only. No formula, source list or generated recap is inserted.
- At most sixteen authoring requests; no correction batch, retries, project
  replacement, extra stage, hand repair or repeat-bank authority.
- New registration, source/launch reviews and results live in this directory.
  Existing frozen documents and old review history are never overwritten.

This changes communication style prospectively. A generic request does not prove
historical recall is needed. Keep the same source-design constraints and review
where requirements are specified; do not add absence-from-code, baseline-failure,
perfect-selector or manual-prose-superiority gates. Recent-source replay remains
a control, not a candidate to promote afterward.

## Lineage and author inputs

Fit-on: none. Evaluation: four wholly fresh Kimi-authored projects, disjoint
from every spent/frozen bank, benchmark example, worker response and trained
adapter. Authors receive no concrete old cases, examples, expected answers or
model outputs. Reusing general contracts and implementation is allowed.

Fix project IDs staged-01 through staged-04 and broad domains before calls:
inventory transformations; scheduling records; document metadata processing;
sensor-event summarization. Domains are context only, not implemented rules.
Substantive behavior, prose, code, expected values and source rationales are Kimi's.
Natural-language conditional requirements, boundaries, interacting conditions,
retained behavior and actual retirement remain required by the inherited contract.
No simplification to instruction copying, format-only or arithmetic-only quizzes.

Stage requests use only existing http://127.0.0.1:11434/api/generate with
model=kimi-k3:cloud, stream=false, think=true; no format, options, new credentials
or backend. Freeze the exact common authoring prompts, stage input rendering,
request template, domains, specification and reviewed preparation code before
the first call. Subsequent request bytes include earlier author outputs through
that fixed renderer; record each exact request and input hashes before sending.

The exact prompt files are scaffold-prompt.txt and round-prompt.txt. Render their
dollar placeholders in one pass with Python string.Template.substitute; inserted
values are never interpreted as templates. project_id/domain are JSON strings,
round_index is its decimal integer, scaffold is the assembled public-only
scaffold with no checks, prior_packets is the ordered array of prior stage1..r-1
packets (empty at round1), data_contract is the exact inherited DATA-CONTRACT.md.
JSON values use ensure_ascii=false, allow_nan=false, sort_keys=true and compact
comma/colon separators. The assembled scaffold has exactly project_id,
description, initial_file and rounds; round objects omit public_checks until
packet assembly. Kimi's lineage prose is stored separately and copied unchanged
to the final project's lineage; it is not hidden substantive task information.

## Four stages per project

Stage 0 returns exactly:
`{description, lineage, initial_source, rounds}`. All prose/code fields are
nonempty strings. rounds is exactly three objects, in round order, each exactly
`{source_texts, target_symbol}`. source_texts is exactly four nonempty strings,
each <=640 UTF-8 bytes; target_symbol is an existing initial-module function.
At least one target repeats. Existing initial-module restrictions apply.

The assembler creates schema_version=1, author=kimi-k3:cloud, the fixed project
ID, initial_file={path:module.py,text:initial_source}, and round indices1..3.
For each round it assigns four source IDs then the request ID, m01..m15 in
order, role=user. It copies source texts unchanged and fills the fixed request
template. It creates target={path:module.py,symbol:target_symbol}. The scaffold
contains no tests, reference solutions or manually assembled live-rule list.
Freeze its full instruction schedule before any round-packet call.

Stages 1 and 2 return exactly `{reference_patch, public_checks, private_checks}`.
Stage 3 adds exactly `obsolete_mutant`. Reference/check/mutant semantics and exact
check keys are those in the inherited DATA-CONTRACT. The assembler places each
packet's public checks in its public round and private checks/reference in its
private round; the final mutant goes in private.obsolete_mutant. No extra authored
fields, key coercions, semantic edits or duplicated copied interpretations.

Each packet author sees the complete immutable scaffold plus prior accepted
packets for that same project. Future sources are needed to set inclusive check
expiry intervals. Nevertheless, the reference and expectations for round r must
follow only the prefix through round r; citations cannot name later IDs. No
future semantics may be anticipated. All current source constraints must be
explicitly grounded; source-ID validity alone cannot prove this.

No packet author receives worker outputs, another project, validator diagnostics,
review feedback or a proposed repair. Reference workspace execution is a local
validation step; it is not an agent answer or a training example.

## Validation and stop boundary

Use strict JSON: exactly one complete object, unique keys, finite values, valid
Unicode, exact fields and types; reject code fences/prose, partial JSON, NaN and
duplicate keys. Preserve the raw envelope/body before parsing. Normal HTTP/done
status does not imply a valid project. Never append braces or coerce types.

After stage0, validate source sizes, template/ID construction, safe initial module,
targets and repetition. After each packet, validate exact fields, safe replacement,
unique checks, introduction/expiry intervals, visible source IDs, active coverage
and conflicting overlapping expectations. Use the inherited check requirements;
do not replace semantic review with tags or a new label-based acceptance gate.

Apply each reference once to the accumulated reference workspace through the
actual consume_action and run all active public/private cases through run_checks,
adapting only internal rule_ids=[] as already specified. Record inputs, output
records, elapsed CPU time and before/after hashes. At stage3 validate the named
retirement mutant through the same consumer and checks. Any validation/action/test
failure ends bank preparation without dependent authoring or correction calls.

Launch each stage as a barrier across the four independent projects, with at most
four requests concurrent. Do not start a later stage unless all four current
stage validations pass. Preserve already in-flight responses on a failure. There
is no random seed search, author reroll, reduced-bank score or replacement domain.

Authoring/assembly active wall-clock ceiling is2400seconds, including its CPU
checks and final publication; independent review time is separate and reported.
Each HTTP request ceiling is min(450seconds, remaining whole-job time). Deadlines
cannot be reset by stages. On timeout or late publication, preserve partial/raw
evidence, mark preparation INCOMPLETE, and start no additional requests. These
are chosen prospective bounds, not measured performance forecasts or provider
output caps. Record all sixteen planned slots as attempted or unattempted.

Register the launched owner PID in .stencil-owned-pids before model calls. Use
absolute paths and exclusive new output directories. A missing observation or
tool timeout does not authorize restarting a request or job. Preserve exact
returned exec handle and follow it to authoritative terminal state.

## Independent review, final preflight and launch bindings

Before real authoring, Sol's narrow preparation code and reused validation paths
must be independently accepted; CPU mocks/targeted synthetic tests only during
implementation. After assembly, Astra reviews all source/test/reference alignment,
intervals, permitted alternatives and retirement semantics, explicitly checking
future-rule leakage. Rejection stops this bank; no repair authorization exists.
Passing sources and actual references do not measure automatic coding usefulness.

The final serialized projects must pass the actual screen consumer and its final
preflight. That final execution verifies the assembled bytes and creates the
launch-consumed receipt, distinct from per-stage validation. The parked six-file
screen implementation remains unreviewed; its acceptance is also required before
scientific preflight/use. Existing qualified helper files remain unchanged.

The parked launcher hardcodes the old canonical review/specification paths and
requires an exact bound-file set. A narrow prospective binding update is required:
include this specification and new authoring provenance, point to this bank's
canonical review, and retain all inherited scientific/code/evidence bindings.
Do not bypass the real acceptance consumer using test-only override arguments.
Do not copy old ACCEPT text into a new review or use the rejected old bank review.
Exact metadata changes and regression tests belong in the later Sol brief.

Only accepted exact sources/code, final actual CPU preflight and a frozen current
launch approval can permit the inherited one-shot screen. If it passes, register
a larger wholly fresh executable evaluation including useful manual reminders,
measured costs and actual human interventions. Neither preparation, the technical
trial nor a four-project result alone satisfies the overall project goal.
