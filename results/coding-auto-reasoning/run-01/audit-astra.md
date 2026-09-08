# Automatic reasoning pilot run-01 — independent terminal audit

2026-09-08. Native Astra xhigh, explicitly selected by the user; author-disjoint,
same reviewer continuity. Purpose: reconstruct the fixed run from authentic
sources, raw native exchanges, actual source transitions, check receipts and
owned lifecycle. Threat model: trusted but fallible actors and model outputs,
not malicious same-user modification. Writable scope was this audit only.
No model/server call, generated-code execution, new fixture, endpoint replay,
rescore, repair or partial-output salvage was performed. Static source parsing,
local token decoding, saved-record comparisons and hash verification were used.
Fit-on none; both fresh projects are now exposed DEV, not FIT or larger-test data.

**Disposition: the records support INCOMPLETE / no continuation.** The registered
batch ended correctly after a length-capped worker response. Five of six requests
completed; four of six passed their finite endpoint checks. All six selector
calls returned structurally valid focus, but the independently assessed later
Classroom views omit live standing constraints. Thus even the Classroom project's
three finite passes do not establish the registered usable automatic workflow.
The fixed recipe remains parked. Neither leftover time nor the narrow positive
code result permits another attempt, cap change or retrospective gate change.

The frozen readiness report remains unchanged. This audit accepts the accuracy
of the terminal evidence and its incomplete disposition, not the empirical
success of the pilot. Findings below describe observed output consequences;
they are not instructions to repair or rerun this frozen experiment.

## 1 — high: the final worker output is capped and the batch is incomplete

Call 11, request 5 (`build_manifest`), returned HTTP 200 with native
`finish_reason=length`, exactly 2,048 completion IDs, and no terminal EOS.
There is one start marker at index 0 and one end marker at index 1,025:
1,024 reasoning tokens + two delimiters + 1,022 unfinished final-argument tokens.
The last token is 5005. Exact local decoding matches the response's reasoning
and its raw tool-argument string; that string is incomplete JSON. This is a
capacity failure, not a usable action or an unrecorded successful edit.

The runtime preserved the entire exchange, marked the call and request
technical-incomplete, and stopped. No consumer call, candidate workspace or
terminal workspace exists for this request. Its pre/post call module hashes
are identical; `build_manifest` remains the original `return None` stub.
All 16 planned public and 26 planned private endpoint checks for request 5 are
listed unfinished and none ran. No second worker attempt was made because a
technical failure stops the batch, unlike a failed public functional check.

The authoritative prompt had 10,774 tokens; prompt plus full output reserve was
12,822, safely below 32,768. Owned elapsed time was below its reservation. The
observed failure therefore cannot be attributed to a context overflow or expired
wall-clock budget. Fitting the offline reference did not guarantee that the
model's own verbose final action would fit. No truncated source was compiled,
tested, extracted as a replacement edit or used to complete the endpoint.

## 2 — high: complete source-faithful focus is not established for a whole project

I compared each actual parsed focus and its complete rendering with the original
visible IDs, roles and source text. The assessment concerns current standing
constraints, including scope and permissions, rather than a mandatory list of
oracle phrases or repetition of the entire current algorithm. Missing incidental
API details alone are not treated as missing standing reminders. In particular,
grouping's no-extra-average output fields are not a separate completeness finding.

| Request | Source-specific focus assessment |
| --- | --- |
| Classroom 0, `validate_batch` | No material standing-rule defect found. It preserves arrival order and resubmissions, carries the currently live conditional two-decimal convention, and states JSON-safe object/no-exception behavior. The extra batch/error/count notes are supported by the current request. |
| Classroom 1, `group_submissions` | Retains no sorting, arrival order, attempts, delegation and unchanged errors. It omits the explicit project-wide JSON-safe-object/error/no-exception convention from m03. Citing m03 among six IDs does not render that missing constraint. It does not replay the retired two-decimal rule. I do not demand an average algorithm or an average-field prohibition as an additional focus phrase for this no-average task. |
| Classroom 2, `summarize_class` | Correctly carries best-score-once, grouping delegation, always-present errors and one-decimal assignment means. It loses m03's standing no-sorting/arrival-order convention and the project-wide JSON/error/no-exception behavior. Its text therefore does not completely preserve current standing rules even though the implemented summary obeys the relevant rules. The source's summary-specific best-score exception is valid; it is not a wrongful retirement of earlier functions' preservation of attempts. |
| Playlist 0, `normalize_tracklist` | Retains unknown-key precedence and alphabetical choice, but renders the exact-format rule as `unexpected key <name>` inside quotation marks around the whole phrase, losing the source's literal quotes around the substituted key. This is a precision defect in a convention expressly specified as exact. The task's full duplicate algorithm need not be repeated; its omission from this focus is not used to infer the later code defect. |
| Playlist 1, `sequence_playlist` | Correctly retains delegation and stable ties, and does not import the future manifest-only shortest-first plan or the assistant's unadopted title tie-break. The global rule is only referred to as “via house rule”; its precedence, alphabetical selection and exact error format are absent from the rendered reminder. I cannot certify that shorthand as a complete rendering of the applicable standing rule under the fixed definition. |
| Playlist 2, `build_manifest` | Correctly retires the old shortest-first preference in favor of longest-first and preserves equal-length sequenced order. However, it omits the source's artist-order-only restriction, leaving longest-first unqualified for duration mode. It also omits the explicit closed artist/duration permission boundary from m-r2-u2 despite citing that source. Added API prose says “integer/positive constraints” although zero gap is allowed, and says “assign IDs” although existing IDs must be carried through. The exact unknown-key-format precision issue recurs. These additions cannot be excused as harmless algorithm omissions. |

The strongest completeness failures are the explicit global omissions in the
later Classroom views and the lost scope/permission boundary in the final
Playlist view. The more local Playlist wording issues are also recorded rather
than silently normalized by the auditor. The renderer kept every returned item
and its text verbatim; these are selection/output issues, not lost renderer text.

Several objects cite assistant messages that merely restate supported user
instructions. Such a citation is not by itself proof of unauthorized adoption.
I found no actual adoption of the rejected shuffle mode, title tie-break,
dropped-errors suggestion or every-attempt summary suggestion. The observed
problem is incomplete or imprecise current focus, not a demonstrated general
promotion of assistant text to user authority. No causal claim is made that a
particular focus omission caused a worker defect; authentic sources were also
available to the worker throughout.

## 3 — high: Playlist implementation defects extend beyond its one finite failure

The saved `normalize_tracklist` reads and type-checks `allow_duplicates`, then
executes duplicate rejection unconditionally. There is no guard making that
rejection conditional on `allow_duplicates` being false. The sole saved private
failure, `chk-r0-obl-1`, is therefore a real source violation: two otherwise valid
case-insensitive duplicates with `allow_duplicates=true` returned
`{"ok":false,"error":"duplicate track 2"}` instead of retaining both tracks.
The check's input, expected output, definition hash and tested module hash match
the accepted bank. No oracle inconsistency or serialization-order mismatch was
found for this failure.

This function remains unchanged in `sequence_playlist`'s dependency state.
The next request's finite pass does not fix or erase the prior endpoint failure:
its terminal set includes cumulative functional checks and only its own current
obligation checks, not every previous obligation check. Source inspection shows
that delegated duplicate permission remains wrong even where it was not exposed
by that next finite set.

The sequencer itself adds two untested source defects. It tests arbitrary JSON
`order` values for membership in a Python set, so a list or object order raises
`TypeError` instead of the prescribed invalid-order error. It constructs the
normalization input using `payload["tracks"]`, so a missing tracks key with an
otherwise valid/default order raises `KeyError` rather than returning the
normalizer's payload error. These follow directly from the saved statements and
authentic task requirements; no new examples were executed or added to scoring.
The actual artist/duration sorting uses stable single-key sorting and preserves
IDs, with no title tie-break or future manifest preference in the sequencer.

For Classroom, I found no material implementation/dependency defect in the
three actual edits. Validation processes every input in order and carries helper
errors, grouping delegates without dropping attempts or sorting, and summary
selects the best score once per student/assignment, counts class-wide distinct
students, uses one decimal, handles the empty case and carries errors unchanged.
Earlier helpers and functions are preserved. This is a bounded positive source
inspection plus three finite passes, not a proof over every possible input or
an accepted automatic workflow with complete focus.

## Exact schedule, privacy and state reconstruction

All six planned request records remain present and none is unattempted. There
are six selectors and six first worker attempts, 12 render/generation pairs in
all. Each of the first five edits was applied and all of its cumulative public
checks passed, so public-only stopping legitimately selected attempt 0. There
was no public failure requiring a repair attempt in this run; it does not show
successful iterative repair from feedback.

| Request index | Task | Public checks | Private endpoint checks | Finite terminal result |
| ---: | --- | ---: | ---: | --- |
| 0 | Classroom validation | 9/9 pass | 11/11 pass | Pass |
| 1 | Classroom grouping | 12/12 pass | 15/15 pass | Pass |
| 2 | Classroom summary | 15/15 pass | 22/22 pass | Pass |
| 3 | Playlist normalization | 10/10 pass | 16/17 pass | Fail |
| 4 | Playlist sequencing | 13/13 pass | 21/21 pass | Pass; source defects remain |
| 5 | Playlist manifest | 0 executed, 16 unfinished | 0 executed, 26 unfinished | Technical incomplete |

Totals are 59 executed public checks with zero failures and 86 private endpoint
checks with one failure. “Private endpoint” here includes the registered initial
checks as well as cumulative private-functional and current-obligation checks.
I compared every saved check's definition hash, input, symbol, expected values,
rule IDs and module hash with the frozen source bank. This validates receipt
identity; it is not an endpoint rerun or new scoring exercise.

I reconstructed both projects independently from their exact initial modules.
For all six requests, the saved source event list exactly matches the authentic
prefix, and selector messages/payloads match reconstruction from those events
only. No code, checks, earlier tool outcome, generated reasoning, manual recap,
or private oracle object enters a selector request. All cited IDs are visible.
For all six worker calls, reconstruction from original source-role messages,
actual prior final tool calls and public tool results, actual current module,
cumulative public checks and the complete current rendered focus matches the
issued messages and request intent exactly. The fixed system and current prompt
label generated focus advisory and incapable of creating new user adoption.

For each of the five applied edits, the returned target source AST matches the
actual replacement function. The exact text of every non-target function is
unchanged across that transition. Saved attempt/terminal files, pre/post hashes
and next-request start files agree. Tool feedback is exactly reconstructed from
application state and public results; no terminal private outcome appears in
history, selects another attempt or resets a dependency. Original source-role
messages remain intact. Generated focus and generated reasoning are absent from
persistent worker history; final assistant tool-call arguments and matching
public tool responses remain. The incomplete final call leaves state unchanged.
These comparisons substantiate no manual replacement or output rescue in the
saved path; the parent also records zero human repairs.

## Native receipts and full raw cost

For every render and generation exchange, base64 bytes, textual bytes, lengths,
SHA-256 and parsed response agree. Each render and generation uses the exact same
request bytes; render completion precedes generation. All 24 HTTP responses are
200. Forced tool name and exact structured JSON schema match the intended
selector/worker tool. Actual native sampling reports max_tokens 2048,
thinking_token_budget 1024, temperature .6, top_p .95, top_k 20, min_p 0 and
seed 20260908. Enable-thinking/nonstreaming settings are present. Every response's
prompt IDs exactly equal its render IDs, and raw prompt/completion/total usage
matches the actual ID counts. No prompt contains a reasoning boundary; all
prompt lengths plus the full cap fit context.

Each of the 12 output sequences has one correctly ordered start/end pair.
Exact local decoding of reasoning and final suffix matches the native fields,
including final whitespace. Eleven responses have stop plus one terminal EOS and
valid returned JSON; the twelfth is the capped incomplete suffix described above.
Eight observed reasoning spans reach 1,024. The four shorter spans are 762, 597,
398 and 541. This establishes the observed bound and actual native propagation;
it does not establish the causal mechanism that ended reasoning.

| Call | Role | Prompt tokens | Completion tokens | Reasoning tokens | Final suffix tokens | Finish |
| ---: | --- | ---: | ---: | ---: | ---: | --- |
| 0 | selector | 855 | 1184 | 1024 | 157 | stop |
| 1 | worker | 2004 | 1207 | 1024 | 180 | stop |
| 2 | selector | 1180 | 1116 | 1024 | 89 | stop |
| 3 | worker | 3681 | 1144 | 1024 | 117 | stop |
| 4 | selector | 1582 | 946 | 762 | 181 | stop |
| 5 | worker | 5864 | 1385 | 1024 | 358 | stop |
| 6 | selector | 976 | 1145 | 1024 | 118 | stop |
| 7 | worker | 2285 | 1292 | 597 | 692 | stop |
| 8 | selector | 1526 | 482 | 398 | 81 | stop |
| 9 | worker | 6247 | 1459 | 1024 | 432 | stop |
| 10 | selector | 2219 | 733 | 541 | 189 | stop |
| 11 | worker | 10774 | 2048 | 1024 | 1022 | length |

“Final suffix” excludes delimiters/EOS and includes call 11's unfinished text.
Total raw cost is **39,193 prompt + 14,141 completion = 53,334 tokens**.
Completion decomposition is 10,490 reasoning + 3,616 final suffix + 24 boundary
markers + 11 EOS tokens. Of the final suffix tokens, 1,022 belong to the capped
unusable call. Selector raw usage is 8,338 prompt + 5,606 completion; worker raw
usage is 30,855 prompt + 8,535 completion. Classroom totals 22,148 tokens;
Playlist totals 31,186 including its final failed generation.

The runtime's validated-call aggregates contain 28,419 prompt + 12,093 completion
= 40,512 and omit the capped call's **10,774 + 2,048 = 12,822**. Its incomplete
accounting flag is therefore important. The raw response permits full cost
reconstruction, as the parent observation correctly does; this does not complete
request 5, validate its action or change `accounting_complete`/`pilot_go`.

Generation HTTP elapsed sums to **666.2795095319743 seconds**, native render HTTP
to **0.9065805140126031 seconds**. Selector generation accounts for
230.11852198798442 seconds and worker generation for 436.1609875439899 seconds.
These are observed whole-HTTP times, not separately measured decode-only rates.

## Freeze, owned time, cleanup and parent claims

Freeze commit: `9d40e0d11fb0f8ec760096b1d3e051c10f10b42b`. All 28 frozen tracked
SHA-256 values match both current file bytes and the corresponding frozen Git
blobs; all four model metadata hashes also match. The manifest's source/data
bindings agree with this freeze and the reviewed bank. This includes the
unchanged readiness report SHA-256
`03641b01ab211ee719d1096b2015d1b1b47e37938bd7498b0aa8ddc8e7319442`.
No new full-weight hash verification is claimed.

The saved container plan and server-launch command match exactly, including the
pinned image and Qwen3/Hermes configuration. The owned container is
`stencil-coding-auto-reasoning-d9980e189360`, ID
`f31cd4397dd6670d51e91d1bab21da88a7820dcdf1b6f1879053a73aca7c3464`.
Launcher PID 107739, server-launch client 108419, driver 109683 and all three
cleanup client PIDs are present in the ownership registry. Exact launcher session
47090 terminal exit 2 is reported by the parent; the saved driver exit and
lifecycle independently record exit 2. There is no evidence of a restart or
additional render/generation attempt.

The monotonic deadline is exactly start + 3,000 seconds and the driver absolute
deadline is 60 seconds earlier. Startup-to-driver time was 517.2090198993683
seconds, below the 600-second ceiling; 2,422 seconds were forwarded. Driver wall
time was 672.4473669528961 seconds, with 5.826125144958496 seconds after driver
exit through terminal lifecycle time. Entire owned elapsed time is
**1195.4825121320027 seconds**. Adding the prior smoke's 516.914703271992 gives
**1712.3972154039948 actual seconds** for this candidate. Unspent reservation
is not authority for another run or revised operating point.

All three recorded cleanup commands—logs, stop and remove—target that owned
container and returned zero. Lifecycle is DRIVER_EXITED, cleaned true and
cleanup_evidence_complete true. The run flag is absent. The parent separately
reports empty Docker and GPU-compute queries; this reviewer did not make a new
Docker/GPU query. Successful saved removal plus that parent observation supports
cleanup, without substituting a manifest boolean for its underlying receipts.

I reconciled the exact provisional `RESULTS.md` and `parent-observation.json`
versions bound below with the raw evidence, including every parent-bound call
receipt hash. Their counts, raw cost correction, frozen-hash statements and
INCOMPLETE/no-continuation disposition agree. Their source/focus review was
explicitly pending; this audit supplies it without changing finite results.
The narrow positive is three source-consistent Classroom edits made without
manual repair. It does not show three complete automatic focus views, isolate a
reminder benefit, demonstrate feedback repair, establish manual-prose parity or
reliability, or satisfy the larger goal.

## Evidence bindings

SHA-256 values below identify the inspected terminal evidence. The parent
observation also binds all 12 raw call-record hashes, independently verified here.
Request-record hashes bind the six actual focus views, history and endpoint
receipts; their module hashes were checked against all actual workspace files.
The provisional RESULTS hash is historical: a later parent append of this audit's
disposition is a new report version, not an alteration of the observed run.

| Artifact relative to run-01 | SHA-256 |
| --- | --- |
| `freeze.json` | `08634f8b0176e94d0738cb4622aa20d10a9b8a90926be4eed1601796e1eada2b` |
| `lifecycle.json` | `02734825b19c4b9e3aa328151d5c3470aca389c1d4ad2491113f3adf52882648` |
| `server-launch.json` | `9881bd834e06f6fa6354cbc5c023216a0d27ebd1e421bc484340f9481325e84f` |
| `driver-exit.json` | `95a6da47569da433463a393651b8995a63c7ce21043ae1019a8708af6b2eaaa1` |
| `cleanup-receipts.json` | `06449de29e54eaf8bd50dcf51a366442aaa722add5b8f64f07547b129b09c75c` |
| `container-command.json` | `451355e5e1809191719a9ec4b87273b8b08ded1c0d1058c725d61e5a125ec739` |
| `driver-command.json` | `45fc90c85bc093447f9e885df7400c6a047ef1cc3fa03f46590ef45a876508bf` |
| `calls/manifest.json` | `35f9a71db9eed0094e124c84133930d573a382cb0f27fc0714e62b8ecce02016` |
| `parent-observation.json` | `3ff11807a630595c0be5f622a1f6ed15188a5a7c41513f632ab79dfaaa55f17a` |
| `RESULTS.md` | `fa39ebee68f537413248cf8c50f9067384a04a9d17b4f3713b0d79c322bc3cda` |
| `calls/requests/request-0000.json` | `ef28eea424a969fa93f1b04c8f1ecd72c60c20a6d4513a69a73ce7a2cc8abf47` |
| `calls/requests/request-0001.json` | `183d31c03ef8bb3b6f17bbafdb8f82abe6686acc89de92e9e447d138c5281ede` |
| `calls/requests/request-0002.json` | `64715c58ab84d6b0bbd5e2dad195c03ed07b5d0f4aa01036ac59c70666f70cce` |
| `calls/requests/request-0003.json` | `e5ea94b1ebdc2d69de246f9b7b68c35f23b65d7e434fc59665e0e48fec0b4946` |
| `calls/requests/request-0004.json` | `824d94d54212f413d7c2978d6433f09136d547cf8277b49b624e083821ba1f8e` |
| `calls/requests/request-0005.json` | `cbc07d34cd0be95c8dac0a62bba033d5e6195f93d929d161093b82b2743f7b95` |
