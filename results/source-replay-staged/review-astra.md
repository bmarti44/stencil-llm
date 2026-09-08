# Staged source-replay preparation — independent review

## Round 1 — 2026-09-08

Reviewer: native gpt-6-astra, xhigh, `/root/source_staged_review`,
author-disjoint from the preparation specification and prompts. The user's
native Astra/Sol/Kimi instruction supersedes the archived wrapper and Opus
reviewer policies for this task.

Score: 96/100

Disposition: ACCEPT

Open findings: 0 critical, 0 high, 0 medium, 0 low. The >=90 and zero-open-high/
critical requirements are met for this prospective preparation design only.
No finding is entered under the `source-replay-staged#N` identity in this round.

Purpose and threat model: find concrete ambiguities, invalid bounds, scientific
changes or preparation loopholes likely to mislead trusted-but-fallible agents.
This is not implementation acceptance, source-bank approval or launch approval.
Read the archived protocol and latest ledger STATE before substantive review.
No failed-bank source content, worker response, actual test data, benchmark,
tokenizer, model, GPU, API or container was executed or opened for this review.
No subagents were used. CPU work consisted of read-only template, arithmetic and
hash checks. Only this canonical review file was written.

### Exact reviewed subjects

All eight artifacts below were verified byte-identical to commit `b87c962c`.
The three staged files are the concrete design under review; the remaining
files supply inherited requirements and the accepted research decision.

| Artifact | SHA-256 |
| --- | --- |
| `results/source-replay-staged/PREPARATION.md` | `284a02a198eb1cd9aef7938ffc994ab88fb78de9876e6290bdca5df72dad3e4a` |
| `results/source-replay-staged/scaffold-prompt.txt` | `10da7a83cd76a6225e0eb5bde687511559b8e73726882cedfdd0d12a157b70a5` |
| `results/source-replay-staged/round-prompt.txt` | `28982adb50da11675fc3403501ee81f7435faae6248e714d64a58355113e89ab` |
| `results/source-replay/SPEC.md` | `01da819289d264926e8492a947b3bf8d6893b89c7559ff8142b9c4dabebda78c` |
| `results/source-replay/DATA-CONTRACT.md` | `6ae44a7794701686cf06a0c32551d9d92b96fb582cd042dee73be95a917a7e4a` |
| `results/source-replay/SCREEN-IMPLEMENTATION-BRIEF.md` | `40d3497277a0ccbea42213f856c4531cc290a5babb00956a95e6bc763786aa89` |
| `results/source-preparation-research/report-source.md` | `781ac84a440f524aad6cd4120157a6af6d4c2c7bcba5944644da20bd239835d4` |
| `results/source-preparation-research/review-astra.md` | `85c55188b6a88095419f7ba841c7f2a830e11c2e5b0b80e5a5a98210e26ffa28` |

### Verification and disposition rationale

The stage schemas and assembly are sufficiently concrete. Stage 0 authors the
description, lineage, initial module and three ordered groups of four source
texts plus target names. The assembler supplies only fixed administrative fields,
IDs, roles, path, round indices and the registered target-only request. The
public-only scaffold has an exact field set and omits all checks; lineage is
preserved separately. Stages 1/2 supply exactly one reference and the two check
arrays, and stage 3 additionally supplies the retirement mutant. Ordered prior
packets are immutable author artifacts for the same project. Mapping their keys
into the inherited public/private schema requires no hand-authored semantics.

Both prompt files are valid Python `string.Template` inputs. Their exact
placeholder sets are respectively `{project_id, domain}` and `{project_id,
round_index, scaffold, prior_packets, data_contract}`. A read-only substitution
check with inert dollar, backslash, newline and Unicode sentinel text confirmed
that inserted values are not recursively interpreted. JSON rendering options
are fixed, and the round prompt receives the exact inherited contract. The
scaffold prompt's literal request matches the specification after the expressly
required joining of its wrapped lines with single spaces. Author-supplied text
and code remain unchanged by deterministic serialization and assembly.

The call bound recomputes as four projects times one scaffold plus three packet
calls: sixteen maximum requests. Four stage barriers at a maximum of four
concurrent requests imply four HTTP waves; 4 x 450 = 1800 seconds leaves a nominal
600 seconds inside the 2400-second whole preparation allowance for assembly,
checks and publication. This is feasible arithmetic, not an observed performance
or completion guarantee. The whole deadline still dominates every call and CPU
step; it cannot reset at a stage boundary. Timeout and late publication yield
INCOMPLETE, unattempted slots remain explicit, and observation expiry does not
authorize a restarted job. The actual implementation must enforce these terms;
no deadline implementation was tested or approved here.

Validation acts on cumulative reference state through the existing real action
consumer and sandbox, running every active public/private case at each round.
The final retirement mutant must be a valid accepted replacement and fail its
named active private retirement check while the correct reference passes. This
does not admit syntactic invalidity as evidence that a retirement test works.
Exact fields/types, strict JSON, source visibility, intervals, duplicate checks,
active coverage and overlapping conflicting expectations are expressly checked.
Reference execution establishes satisfiability, while independent source review
still must establish support, permitted alternatives and actual retirement.

Full future schedule visibility is necessary for frozen inclusive expiry dates
in this chosen authoring procedure. It also creates a real opportunity for future
semantics to enter earlier expectations. Both the specification and round prompt
explicitly prohibit that leakage; prefix-valid IDs alone do not establish
compliance. The required final independent review covers all sources, references,
checks and cancellation scope. A semantic rejection stops this bank. There is
no correction, replacement, repeat-bank, shrinking or post-exposure rescue
permission; per-stage validation failure also prevents later dependent stages.

The generic request distribution is prospectively disclosed and cannot establish
isolated history recall. The design retains realistic initial and evolving code,
all authentic history, nearby-source support and the recent-source control. It
does not introduce baseline-failure, absence-from-code, perfect-selector or
manual-superiority gates. Substantive transformations, retained functionality,
interacting conditions, boundaries and meaningful retirement remain required.
No source-replay utility is inferred from accepted preparation.

The inherited schedule remains 36 worker plus 12 selector calls, with output
allowance 36 x 1024 + 12 x 128 = 38400 tokens. The historical arithmetic also
reproduces: 5777 / 307.083573153 = 18.8124683475716 tokens/second, and the allowance
divided by that rate is 2041.199447650199 seconds. The frozen scientific cost
projection, 3000-second whole screen ceiling, H/S/R practical gate, incomplete/
ineligible handling and larger untouched proof requirement are retained. The
old two-call result is technical qualification only; neither it nor this review
demonstrates full-screen affordability or authorizes a scientific run.

### Boundaries for subsequent work

The new specification correctly requires independently accepted preparation
code and reused validation paths before real authoring. The separate final
serialized-project preflight must exercise the actual screen consumer and
produce its launch-consumed receipt; stage records cannot replace it. The
parked six-file implementation remains unreviewed. New prepared data and code
need their own exact reviews and a current frozen launch approval.

Feasibility-only inspection confirmed that the parked launcher hardcodes the
old canonical review/specification paths and checks an exact file set. Its SHA
was `5f10804ff015b2d2f6eb0ce2de35fe4c2dcf85bb6fde28de4a74162b9da7ae0a`.
The preparation specification already requires the narrow path/provenance/binding
update and prohibits test-only overrides and old ACCEPT promotion. The qualified
review helper's SHA was
`ccb863333e27cee7a4253b881987c7d47c42c87dcbeaf7e1f2b0e94cd711d7a3`;
its machine parser requires the legacy literal `canonical_topic="source-replay"`.
If that unchanged helper is reused later, the literal is compatibility metadata;
the actual new canonical path and exact specification/code/data subject bindings
must remain authoritative. It confers no historical acceptance on a new bank.

I also spot-checked the parked contract's field sets and consumer imports
(`src/stencil/source_replay_screen.py` SHA
`eb759ead3e595c22c4f7cc8f96e4b3efaa156d41565d402532b2c3a65e765c01`).
These limited reads grant no code acceptance. The concurrently drafted Sol brief
was not reviewed. No machine launch-acceptance block is issued in this design-only
round. No additional framework or research loop is needed before the already
required bounded implementation and its independent review.

## Round 2 — 2026-09-08

Reviewer: the same native gpt-6-astra, xhigh, `/root/source_staged_review`.
The original 8976 bytes of Round 1 are preserved verbatim; their SHA-256 is
`6ddde9fe5009843122bedddb924f9b213602f7c58a5e180716c968dd26f5a322`.

Score: 84/100

Disposition: REJECT

Open findings: 0 critical, 1 high, 2 medium, 0 low. Preparation implementation
acceptance is blocked by `source-replay-staged#1`. Round 1 design acceptance
stands; no source bank, scientific runner or launch is accepted by this round.

Purpose and threat model: verify the concrete preparation implementation against
the accepted design for trusted-but-fallible agents and ordinary service/data
failures. Review covers the four new files and their actually reused structural,
action, JSON, source-splicing, sandbox and compact-rendering paths. It does not
audit the entire parked scientific runner or seek protection against a malicious
same-UID actor. The latest ledger STATE and accepted design were read first.
No failed-bank contents, scientific source/check data or worker responses were
read. No real API, tokenizer, model, GPU, container or scientific preflight was
invoked. Targeted synthetic CPU tests and mocked transport reproductions used
temporary directories only; no subagents or implementation edits were made.

### Findings

1. **High — source-replay-staged#1: socket timeouts and post-return checks do
   not enforce the registered active request/whole deadline.**
   `tools/prepare_source_replay.py:270–282` passes a relative timeout to
   `urllib.request.urlopen` and then calls `response.read()`. That timeout bounds
   blocking socket operations, not the total time across a sequence of reads.
   `_perform_http` checks elapsed time only after the transport returns and the
   response has been written (`:330–390`). The parent calls `future.result()`
   without a deadline, and the executor context waits for its threads to finish
   (`:586–633`). Thus a slow body that keeps making progress can hold active
   preparation beyond 450 seconds per call and beyond the 2400-second whole
   allowance. A late result is correctly rejected eventually, but the program
   cannot stop waiting and publish a terminal record at its registered deadline.

   Reproduction used a local socketpair, the real `http.client.HTTPResponse`
   reader and mocked `urlopen`, with zero network requests. A 40 ms socket timeout
   and six body bytes delivered every 25 ms caused the actual `_transport` to
   return normally after **153.360360 ms**, having consumed all six bytes. This
   isolates the timeout semantic mismatch without an expensive or malicious
   provider scenario. Root independently reproduced 152.219865 ms.

   Give the real transport/owner an enforceable absolute per-call and whole
   deadline; waiting and cleanup must not depend indefinitely on a live thread
   returning. Preserve known attempted/partial evidence, terminate only owned
   work, leave later slots unattempted and publish INCOMPLETE on expiry. Test the
   actual bounded transport/waiting path with a slow-progress or blocked-reader
   stand-in. Merely adding another elapsed check after `future.result()` cannot
   fix this. No general workflow or security framework is required.

2. **Medium — source-replay-staged#2: the real urllib error path discards an
   available HTTP error body and response metadata.**
   `tools/prepare_source_replay.py:270–282` does not catch `urllib.error.HTTPError`.
   Standard urllib raises that exception for HTTP error responses, so
   `_perform_http` takes its generic transport-exception branch (`:336–342`)
   before it can write the body or build the status/headers/timing receipt. The
   later `raw["status"] != 200` branch is reached by a transport returning such
   a dictionary, not by this real urllib path. This violates the registered
   preserve-raw requirement precisely when the provider returns useful failure
   evidence; the whole result does still fail closed.

   I injected a real `HTTPError(503)` with an `io.BytesIO` JSON error body into
   `urlopen` and called the actual `_perform_http` with actual `_transport`.
   Result: `PreparationFailure(kind="transport", response=None)`, no raw response
   file, while the exception's exact body remained readable. Root independently
   reproduced the same result. Consume HTTPError as a response through the same
   bounded raw-body/status/header recording path, then reject its HTTP status
   without retry. Add a consuming test using HTTPError, rather than only a mock
   dictionary with non-200 status.

3. **Medium — source-replay-staged#3: an invalid authored enum type escapes
   validation and leaves no terminal receipt.**
   The reused `src/stencil/source_replay_screen.py:179` tests membership of
   `check["behavior"]` in a set without first establishing a string type. A JSON
   list or object in that field raises TypeError. The preparation validation loop
   (`tools/prepare_source_replay.py:640–704`) handles ValueError and selected
   preparation exceptions, so this ordinary schema defect escapes the driver.

   Through the actual `run_preparation`, existing synthetic fixtures and injected
   transport, I changed a first-round private check's behavior to `[]`. After
   eight HTTP attempts, the driver raised `TypeError: unhashable type: 'list'`;
   `job.json` remained `IN_PROGRESS`, `terminal.json` was absent, and the stage-1
   receipt was absent. Root independently reproduced that full consuming path.
   This does not silently admit the malformed bank, but it loses the promised
   durable terminal classification and leaves misleading unfinished status.

   Reject invalid authored types through the normal validation failure path and
   ensure unexpected local validation errors still produce INCOMPLETE with
   preserved records. Do not coerce or repair the authored value. Exercise the
   real driver with list/object enum values and verify terminal state, known
   attempt records and no later authoring calls.

### Verification and limits

Independent targeted command:

```text
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q -p no:cacheprovider tests/test_source_replay_authoring.py tests/test_prepare_source_replay.py tests/test_source_replay_screen.py
```

Result: **27 passed in 4.27 seconds**. Sol's earlier red-first and Ruff/format/
absolute-help/dry-smoke results remain reported coder evidence; I did not replay
an earlier code version or claim to independently repeat those checks.

The four previously reported draft corrections are present: response identity
uses the independently established remote name `kimi-k3` while requests keep
`kimi-k3:cloud`; only normal `done_reason="stop"` is accepted; a returned response
over its per-call allowance is rejected with retained bytes; and interrupted
ordinary/mutant checks retain their locally accumulated result records. The
attempt-preparation regression and delivered-but-unvalidated transport siblings
are covered by the supplied tests. Finding #1 identifies the remaining
active-waiting gap, not a claim that late outputs are currently accepted.

Static and consuming inspection confirm the intended substantive dataflow:
frozen prompts plus fixed domains/IDs and prior accepted same-project author
packets form requests; thinking, validator feedback and worker responses do not.
Administrative assembly copies source/code/lineage/check values without semantic
editing. Prefix source-ID and inclusive interval checks, cumulative case execution,
real source splicing, final mutant application and strict JSON comparison are
used. The synthetic tests execute fresh isolated sandbox children, including
retained cases and mutant failure. The round barrier prevents dependent stages
after failure; no retry, correction, reference reset or substitute project path
was found. All final projects remain PREPARED_UNREVIEWED pending the separate
source review and final scientific preflight.

The freeze validates exactly sixteen static subjects plus the immutable review
snapshot, fixed configuration and root-recorded current review metadata. Per the
accepted brief, this is not another review parser: root must actually inspect
the canonical decision, copy its exact accepted bytes and bind the current
subjects. There is no actual accepted snapshot/freeze yet. This REJECT must not
be turned into an accepted receipt. Subsequent canonical appends should not
mutate a later accepted historical snapshot. Scientific registration bindings
and the legacy launch-helper topic compatibility remain separately required.

The coder's disclosed broad metadata search emitted truncated stopped-bank
response content contrary to its scope. That deviation remains on record. The
new prompts/domains were frozen before it, root independently established the
remote model name beforehand, and no future staged data exists. The reviewed
request builder and synthetic fixtures show no import or runtime dataflow from
that bank. This is a concrete code/dataflow assessment, not proof about the
coder's unobservable mental influence or permission to reuse old cases.

### Exact implementation bindings

All subjects below were verified byte-identical to candidate commit `9e6b9cdc`.
The first sixteen rows are the proposed static freeze subjects. The final two
are additional reviewed brief/test evidence. The future review snapshot has no
accepted hash at this point and is not fabricated here.

| Artifact | SHA-256 |
| --- | --- |
| `results/source-replay-staged/PREPARATION.md` | `284a02a198eb1cd9aef7938ffc994ab88fb78de9876e6290bdca5df72dad3e4a` |
| `results/source-replay-staged/scaffold-prompt.txt` | `10da7a83cd76a6225e0eb5bde687511559b8e73726882cedfdd0d12a157b70a5` |
| `results/source-replay-staged/round-prompt.txt` | `28982adb50da11675fc3403501ee81f7435faae6248e714d64a58355113e89ab` |
| `results/source-replay/SPEC.md` | `01da819289d264926e8492a947b3bf8d6893b89c7559ff8142b9c4dabebda78c` |
| `results/source-replay/DATA-CONTRACT.md` | `6ae44a7794701686cf06a0c32551d9d92b96fb582cd042dee73be95a917a7e4a` |
| `src/stencil/source_replay_authoring.py` | `8a6b42437d7a6459177ee176505870ebc715eaa56f15338dfccd61f5c20202d2` |
| `tools/prepare_source_replay.py` | `9c1474fd4449281803f2bc5329f2fa3abe04192d5ae6a5a3ffd63683c434f6a6` |
| `tests/test_source_replay_authoring.py` | `5c01d7dd5f98803f23a7ea34e5cf85b6d6a8f759df2d2398cccb527900a4e170` |
| `tests/test_prepare_source_replay.py` | `58faeb8f86490d5d374dcbd16b6df05a18f2432b0422f571a733bb2cee267d30` |
| `src/stencil/source_replay_screen.py` | `eb759ead3e595c22c4f7cc8f96e4b3efaa156d41565d402532b2c3a65e765c01` |
| `src/stencil/source_replay.py` | `19f3c7f1948fd74eb25767c007b4b9af567629c15656fed4c529542ffe485d55` |
| `scripts/coding_competence_dev.py` | `695e9e6228d6ed540d0235442ec3aa515ff1f00b6f3ad303ba76354feaa407a0` |
| `scripts/coding_worker_dev.py` | `41c33ad88fc1fca8d123a71580683d3f478d96c4f1f2f41889303f40c7551b26` |
| `src/stencil/focus/slab.py` | `3f3a9f04ee9bae3395c3fdf5d3011e2b8cca4b930332a72dd2edafce7de04b59` |
| `src/stencil/focus/slab_sandbox.py` | `3dad55e31b23fd859a9fcf805b3694acc99c8efdb48c35ed82ca78b16f9d7de8` |
| `src/stencil/focus/renderer.py` | `e1ec3da2f3cd1565746e2b11c24308330b1f8c4d76dfe15f70bf5fa2dc2996be` |
| `results/source-replay-staged/IMPLEMENTATION-BRIEF.md` | `eeb7dc16661c41c6c40cfdb4da22038731b689b55630eb728d5f48ddb1eaa8de` |
| `tests/test_source_replay_screen.py` | `8a520970788f563c3e2be811a1eb97c8fdf5ce75f6b06380b7abbd23b3aeb54d` |

## Round 3 — 2026-09-08

Reviewer: the same native gpt-6-astra, xhigh, `/root/source_staged_review`.
All 20494 prior review bytes are preserved verbatim, SHA-256
`154672df45ec8c2a471291c8dec80d5d979cb18e08c04d1621ded6f505fecd34`.

Score: 96/100

Disposition: ACCEPT

Open findings: 0 critical, 0 high, 0 medium, 0 low. Findings
`source-replay-staged#1`, `#2` and `#3` are resolved below; no new finding is
added. This accepts the preparation implementation and its actually reused
consumers against the accepted preparation design. It does not accept a prepared
source bank, the entire parked scientific runner, a scientific launch or the
larger project claim.

Purpose and threat model are unchanged: reverify the three fixes and introduced
regressions for trusted-but-fallible preparation. I read the latest ledger STATE,
the full four-file fix diff and the bounded fix brief. Tests used synthetic CPU
fixtures and local test HTTP servers only. No actual provider, model, tokenizer,
GPU, container, scientific source/check data or scientific preflight was used.
No stopped-bank contents were opened, no subagents were used, and only this
canonical review was edited. The earlier coder search-scope disclosure and the
limits of its code/dataflow assessment remain unchanged in Round 2.

### Finding closures

1. **High — source-replay-staged#1 (resolved 2026-09-08, Round 3): absolute
   transport waiting is now supervised.** The real transport explicitly uses
   the multiprocessing `spawn` context, including when called from the request
   thread pool. One owned child performs urllib operations and streams response
   metadata/body chunks to its parent. The parent polls against the absolute
   minimum of the per-call and whole deadlines, reserves 0.25 seconds for bounded
   owned termination/reaping, and preserves already received bytes on expiry.
   The thread now returns from its bounded transport instead of waiting for a
   remote body's eventual completion. Post-return and final-publication checks
   remain in place.

   The actual threaded local-server regression passes: continued body-byte
   arrivals no longer extend the read budget, a partial raw
   response is retained with `response_complete=false`, the result is a deadline
   failure and no child remains. That regression exercises the whole-deadline
   clamp with the normal longer per-request limit. I additionally separated the
   two limits in a local-server probe through the real `ThreadPoolExecutor` and
   `_perform_http`: per-request 0.45 seconds, whole 2 seconds. It returned a
   deadline failure in **0.218141188 seconds**, preserved **4 partial bytes**,
   recorded `attempted=true` and `response_complete=false`, and left zero active
   children. This measures the local owner/transport bound; it makes no claim
   about cancellation or billing inside the remote provider.

2. **Medium — source-replay-staged#2 (resolved 2026-09-08, Round 3): HTTPError
   follows the real response-evidence path.** `_transport_child` catches urllib's
   HTTPError and consumes it as a response, streaming its status, headers and
   available body through the same bounded path. `_perform_http` saves those
   exact bytes and the response receipt before rejecting the HTTP status. The
   actual local HTTP 503 regression passes, preserving the exact JSON error
   body and `X-Synthetic` header in the recorded transport failure, with no
   retry or success promotion.

3. **Medium — source-replay-staged#3 (resolved 2026-09-08, Round 3): invalid
   enum types now reach terminal validation failure.** The reused `_check`
   requires an exact string before enum membership. Both list and object values
   now raise normal ValueError, without coercion. Full-driver regressions pass:
   eight attempted calls, terminal/job INELIGIBLE, and all eight later slots
   UNATTEMPTED. An unexpected validator RuntimeError becomes INCOMPLETE with
   its local-validation error record. The final-assembly path also now catches
   unexpected local exceptions and produces INCOMPLETE; this latter branch was
   checked statically rather than claimed as separately fault-injected.

The process-start attempt-count regression found during the fix is also closed:
an explicit unsuccessful spawn carries `attempted=false`; the driver no longer
overrides it merely because its error kind is transport. The consuming injected
SpawnProcess.start OSError test passes through the actual driver/transport with
INCOMPLETE, zero attempts, four current ERROR slots and twelve later UNATTEMPTED
slots. This agrees with root's independent reproduction. Ordinary attempted
transport errors and delivered-but-unvalidated siblings retain their previous
correct behavior.

### Verification and acceptance boundary

The same three-file targeted command recorded in Round 2 independently produced
**33 passed in 6.17 seconds**. It includes the new actual transport tests and the
existing assembly, cumulative real-consumer, mutant, raw evidence, barrier,
strict-input, freeze, deadline and dry-default regressions. Sol's red-first,
Ruff/format/whitespace and absolute help/dry smoke results remain separately
reported coder evidence; they are not represented as additional reviewer runs.

The fix changes four files: the transport/driver, its tests, the one-line shared
enum type guard and that guard's test. The pure authoring module, exact prompts,
domains, current-request template, sixteen-slot schedule, CLI and seventeen-
subject freeze contract are unchanged. No new dependency, retry, source repair,
scientific gate or worker behavior change was introduced. The substantive
assembly and reference-validation conclusions from Round 2 continue to apply.

Root may now inspect this exact accepted round, create the immutable
`preparation-code-review-at-acceptance.md` snapshot, and bind the current sixteen
static subjects plus that snapshot in the actual preparation freeze. No snapshot
or freeze existed during this review, and none was manufactured for acceptance.
Real authoring still requires that exact validated freeze and the already
registered bounded launch. Any produced sources still need independent semantic
review and the distinct final actual screen preflight. The parked full screen
and its new registration bindings remain separately unaccepted; larger untouched
coding proof remains unmet.

### Exact current bindings

Every row below was verified byte-identical to stable fix commit `37c7fceb`.
The first sixteen rows are the current static freeze subjects. The final two
bind additional reviewed regression/brief evidence. The immutable review
snapshot will be a subsequent exact-byte copy, not a speculative hash here.

| Artifact | SHA-256 |
| --- | --- |
| `results/source-replay-staged/PREPARATION.md` | `284a02a198eb1cd9aef7938ffc994ab88fb78de9876e6290bdca5df72dad3e4a` |
| `results/source-replay-staged/scaffold-prompt.txt` | `10da7a83cd76a6225e0eb5bde687511559b8e73726882cedfdd0d12a157b70a5` |
| `results/source-replay-staged/round-prompt.txt` | `28982adb50da11675fc3403501ee81f7435faae6248e714d64a58355113e89ab` |
| `results/source-replay/SPEC.md` | `01da819289d264926e8492a947b3bf8d6893b89c7559ff8142b9c4dabebda78c` |
| `results/source-replay/DATA-CONTRACT.md` | `6ae44a7794701686cf06a0c32551d9d92b96fb582cd042dee73be95a917a7e4a` |
| `src/stencil/source_replay_authoring.py` | `8a6b42437d7a6459177ee176505870ebc715eaa56f15338dfccd61f5c20202d2` |
| `tools/prepare_source_replay.py` | `ba522c35ac7428ef992fd1d0982339522d14df8b59fdc64e0c20d1be54bbf61e` |
| `tests/test_source_replay_authoring.py` | `5c01d7dd5f98803f23a7ea34e5cf85b6d6a8f759df2d2398cccb527900a4e170` |
| `tests/test_prepare_source_replay.py` | `d89676d261a746e9658d6c397ac2b723d2f97206e131328940b46f542d855353` |
| `src/stencil/source_replay_screen.py` | `9bf16c3417e71a4c23b3298d394b2f15f11c9839f0c24ec5d5db970bfe0b8334` |
| `src/stencil/source_replay.py` | `19f3c7f1948fd74eb25767c007b4b9af567629c15656fed4c529542ffe485d55` |
| `scripts/coding_competence_dev.py` | `695e9e6228d6ed540d0235442ec3aa515ff1f00b6f3ad303ba76354feaa407a0` |
| `scripts/coding_worker_dev.py` | `41c33ad88fc1fca8d123a71580683d3f478d96c4f1f2f41889303f40c7551b26` |
| `src/stencil/focus/slab.py` | `3f3a9f04ee9bae3395c3fdf5d3011e2b8cca4b930332a72dd2edafce7de04b59` |
| `src/stencil/focus/slab_sandbox.py` | `3dad55e31b23fd859a9fcf805b3694acc99c8efdb48c35ed82ca78b16f9d7de8` |
| `src/stencil/focus/renderer.py` | `e1ec3da2f3cd1565746e2b11c24308330b1f8c4d76dfe15f70bf5fa2dc2996be` |
| `tests/test_source_replay_screen.py` | `635973b5f56462146401246c78cc06003ff2fd3738208cefdf802f6a934028bd` |
| `results/source-replay-staged/PREPARATION-FIX-BRIEF.md` | `53f5e8a4f960a0f7fa215d9ab9181c0692145ee9cfbbcdb619699ad664449dcf` |

## Round 4 — 2026-09-08

Reviewer: the same native gpt-6-astra, xhigh, `/root/source_staged_review`.
All 29236 prior review bytes are preserved verbatim, SHA-256
`fafc289017e10b669eaa66b1e86703ba905ab0310ba7901a7646ec9b6e0a06d8`.
The immutable preparation-code-review snapshot remains those exact prior bytes;
this reporting round is appended only to the canonical review.

Score: 96/100

Disposition: ACCEPT

Open findings: 0 critical, 0 high, 0 medium, 0 low. No new finding is added;
`source-replay-staged#1` through `#3` remain resolved. Acceptance covers the
stopped-run report's accuracy, evidence reconciliation and enforced stop only.
The preparation itself remains **INELIGIBLE**. This is not source-bank acceptance,
scientific-run approval or evidence of automatic reminder usefulness.

Purpose and threat model: verify consequential reporting claims for a
trusted-but-fallible recorder. I read the latest ledger STATE, report and audit,
the authorized current failed-run records, the relevant staged-04 source/check/
reference content and the unchanged actual consumer path. Other projects were
inspected for artifact/request/record integrity, not given a full semantic audit.
No earlier stopped-bank contents were opened. No reference or corrected-data
execution, input unwrapping, code/data repair, model/API/tokenizer/GPU/container
call, scientific preflight, subagent or restart occurred. Session 61895 was not
repolled. Only this canonical review was written.

### Diagnosis and scope of the result

The report's packaging diagnosis is supported independently by the saved source
and the actual consuming code. Staged-04 message m01 defines `events` as a list
of event dictionaries. Message m04 specifies the empty-window result. All eight
authored round-1 check inputs are singleton outer lists whose sole member is the
event list; the empty-window check `r1prv1` has input `[[]]`.

The preparation adapter copies `input` unchanged. `run_checks` supplies that
value to `_fresh_execute`, which serializes one `(symbol, value)` case, and the
isolated sandbox calls `env[name](value)`. It does not unpack an argument array.
The saved reference's loop therefore receives a list as its first `event`, and
its first `event.get("muted")` access has no such method. Every saved result is
`passed=false`, `actual=null`, `error="InvalidProgram: AttributeError"`, matching
that static diagnosis. The reference and before/after module hashes reconcile
with their saved exact text. No claim that corrected inputs would pass has been
tested or inferred, and no corrected artifact was constructed.

The report properly limits the three other first-round outcomes to their
recorded reference checks: staged-01 passes 10, staged-02 passes 11 and staged-03
passes 9. These are neither independent source-semantic approvals nor coding-worker
scores. The four stage-0 COMPLETE records establish the registered structural
checkpoint only. The report does not promote those partial successes into an
eligible bank, reduced-bank comparison or utility measurement.

### Independent integrity and arithmetic reconciliation

A read-only standard-library audit completed in 0.073495419 seconds, with zero
reference executions. It independently established:

- The audit manifest's exact file set equals all **28** files under
  `preparation-run-01`. Their sizes sum to **939100 bytes**; every file is under
  10 MB, hash-matches its manifest entry, is tracked by Git and is byte-identical
  to archive commit `5d33831c`.
- All **17** frozen subjects still match their hashes. The code-review snapshot
  is the exact accepted Round 3 file, and the job's embedded freeze and freeze
  hash match the immutable preparation freeze. Neither was changed for this
  reporting round.
- All **8** saved request bodies reproduce exactly from the frozen templates,
  JSON options, domains/IDs and deterministic same-project scaffold assembly.
  Stage-1 requests contain the full immutable scaffold, an empty prior-packet
  array and the unchanged data contract. No validator feedback, thinking or
  other-project material is inserted by that renderer.
- Every raw response matches its byte count/hash, saved envelope and parsed
  author value. Final-response and thinking sizes/hashes reconcile separately.
  All eight responses are complete HTTP 200 envelopes reporting remote model
  `kimi-k3`, `done=true` and `done_reason="stop"`. Their recorded durations fit
  their assigned request allowances and the original whole deadline. Every
  stage-1 request starts after all four stage-0 responses have ended.
- Service counters sum to **19241 prompt** and **77119 generated tokens**.
  These remain service-reported counters, as the report states, rather than
  an independent billing measurement.
- Saved reference results match the authored check IDs, inputs, symbols and
  expected values. Counts reconcile as **10 + 11 + 9 + 8 = 38**, with **30
  passes and 8 failures**. All eight failed-record summaries in the audit match
  the underlying call-0007 records exactly.
- The job and terminal agree on INELIGIBLE, terminal stage 1 and the reason
  `reference failed an active check`. Recorded elapsed time recomputes to
  **326.5759919609991 seconds**; terminal publication recomputes to
  **326.5799810299941 seconds** after the same start, within the 2400-second
  reservation. All sixteen slot identities/statuses reconcile with their call
  and stage records: eight attempts, then eight UNATTEMPTED slots. There are no
  final prepared projects or stage-2/3 request artifacts.

Driver PID 268799 was absent at review. The exact historical exec-session number
and exit 1 are root-supplied execution provenance; I did not query the finished
handle. The recorded terminal status agrees with the frozen CLI's INELIGIBLE to
exit-1 mapping. Nothing in this audit claims a new process execution or an
independent replay of that historical shell observation.

### Stop boundary and reviewed bindings

The registered whole-bank stop was applied: no correction, retry, replacement,
extra stage, reduced-bank scoring or repeat-bank permission follows from this
failure. Accepted preparation code and the separate historical two-call trial
remain their original limited evidence. No final bank, source approval, final
scientific preflight or scientific worker comparison was produced. The parked
scientific runner remains unaccepted as a whole, and larger untouched coding
proof remains unmet. No additional semantic approval or implementation work on
this stopped bank is needed to support the report.

The following artifacts were verified byte-identical to `5d33831c`. The audit's
bound manifest covers all 28 run files; the two calls named separately below
contain the failure's exact source and reference/check evidence.

| Artifact | SHA-256 |
| --- | --- |
| `results/source-replay-staged/PREPARATION-RESULTS.md` | `c2b5ef68e4f41789d0757aeb9704b11e8819e7661e721fd696e57cbd46f95ab5` |
| `results/source-replay-staged/preparation-root-audit.json` | `e91fc5c6c5cb2805abd43a2ee2296e8ab6a70b901d7561c265ae486c0407711c` |
| `results/source-replay-staged/preparation-freeze.json` | `d198d9462ba4577615d89ea41a1139dc4d018d8d7895fc0132d4c79404916302` |
| `results/source-replay-staged/preparation-code-review-at-acceptance.md` | `fafc289017e10b669eaa66b1e86703ba905ab0310ba7901a7646ec9b6e0a06d8` |
| `results/source-replay-staged/preparation-run-01/calls/call-0003.json` | `e22208e0831c1af4cb4603e93dc7c3b3e6ecfdf5ad1f305afc2a9b392172bc89` |
| `results/source-replay-staged/preparation-run-01/calls/call-0007.json` | `bd9468dc3eedf816125349a582b0d41454b9dfd3a11a67fb51e5e318275be5b5` |
| `results/source-replay-staged/preparation-run-01/job.json` | `171a8166719fedf8c5cc45e12adc24d87e5b2671911fb5c79b5f29571acda359` |
| `results/source-replay-staged/preparation-run-01/terminal.json` | `041c60fab165018ffb39340ff71938b668dc6b5bb00bede86f9c1274414e77f2` |
