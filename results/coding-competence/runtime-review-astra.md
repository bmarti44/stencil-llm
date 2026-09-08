# Coding competence runtime readiness — Astra review

Reviewer: Astra xhigh, `/root/competence_readiness_review`, 2026-09-08.
The user-selected reviewer supersedes the older default model instructions.
Author-disjoint review. Purpose: a fair M-only coding competence prerequisite,
with native transport, private-data separation, actual state, deadlines and
complete accounting. Threat model: trusted but fallible agents; malicious
same-uid defenses are out of scope. Reviewer writes only this file. No worker,
server or model was started, and no spent benchmark project was opened.

## Prospective sizing adjudication — before stable code handoff

Decision: ACCEPT the narrow prospective documentation clarification. This is
not runtime readiness acceptance; implementation review awaits stable hashes.

Reviewed draft hashes:

- `PROTOCOL.md`: `d99708acc6058b4726446df39d3747eaa203d1ac0a3af010b7b71d4a252a294b`
- `RUNTIME-BRIEF.md`: `d6328b6ffabc58160dd8ad175a57be517889a5dedb179c735c2ea5f63ec75023`
- Unchanged `NATIVE-CONTRACT.md`: `d324c5fa599e56ddeaac69c3dd44e8f3e338805a2c37903362e456f75c472374`
- Unchanged `DATA-CONTRACT.md`: `d107a5077bb88854ef816dbd93cd5cf94a6b5f365e46c2a5d0b8f650b6837796`

The former phrase "all contexts fit" did not explicitly require every globally
accepted source/result size to fit at every history slot. It was nevertheless
ambiguous as a prospective qualification, so silently bypassing a failed bound
would have been insufficient. The native contract already requires identical
request bytes to be authoritatively rendered before each generation and ends
the entire run on an actual context failure.

The initial implementation's generic envelope is mathematically unpassable
independent of the accepted data: `MAX_MODULE_BYTES = 65536` is included even
with zero prior actions, so `context_with_output_bound >= 65536 + 1024 > 32768`
before visible text and wrapper reserves. Its later allowances also use
`MAX_SOURCE_BYTES = MAX_RESPONSE_BYTES = 65536` for repeated history. A failed
upper bound proves that this bound does not certify fit; it does not prove an
actual request is too large. Independently read accepted initial module lengths
are 514, 1287, 978 and 1820 UTF-8 bytes. These lengths alone are not native token
counts or a proof of any future context's fit.

The clarified qualification is non-vacuous: the actual four known cold payloads
must be sized locally and pass provisionally; all 12 reference argument bodies
must preserve 128 generation tokens of headroom including the EOS allowance;
the 36 prospective slots must disclose repeated-module/history and resource
envelopes; and every actual native prompt plus the fixed 1024-token output
allowance must pass the authoritative 32768-token limit before decoding.
Future generated history is expressly unknown. A later overflow is terminal,
technically incomplete and ineligible, with no truncation, replacement history,
extra call, cap change or prompt rescue. Conditional eligibility is not a
prediction that all 12 requests will finish. The accepted draft changes no
project, code action, output cap, attempt count, reservation or success gate.

The prior accepted documents and their historical reviews remain evidence for
their original bytes; this paragraph accepts only the inspected prospective
sizing delta. Full readiness must bind the final code, tests, preview and
launcher qualification to these reviewed document bytes.

## Runtime review round 1 — launcher handoff pending

Score: 89/100. Full readiness is not yet assessed. One medium runtime timing
finding is open; no high or critical finding identified in the reviewed runtime.

Reviewed `scripts/coding_competence_run.py` SHA256
`5a06b47db19d6acc5915fb308e73b80bc92d2abd80afda9e4c119c1166966b3a`
and `tests/test_coding_competence_run.py` SHA256
`3bb45142817ab731f0d6e3ace0d60f6eaff00c33bc8bacb16c2474034af6c38f`.
Independent targeted suite: 8 passed in 6.05 seconds. No authored-bank checks
were rerun. In-memory native HTTP controls use synthetic data and real tokenizer
and seccomp execution; they do not start an HTTP/model server.

1. **medium — check admission does not reserve its possible execution time.**
   `_run_checks_incremental` admits a new check whenever more than the one-second
   receipt reserve remains. Its actual inherited sandbox starts a two-second
   self-exit timer, so the check can consume that reserve and overrun the driver
   deadline. Independent real-sandbox control: a synthetic infinite-loop check
   was admitted with 1.2 seconds remaining and returned after 2.028659 seconds,
   0.828659 seconds beyond that deadline. Its completed failure receipt survived,
   and the runtime marked the checks incomplete. This is a driver-reserve defect,
   not evidence that the owning 2700-second lifecycle exceeded its ceiling; the
   launcher has a separate cleanup reserve, whose full review is pending.
   Reserve the inherited two-second execution allowance plus the existing
   one-second receipt allowance before beginning each check, preserving already
   finished results and unstarted check IDs. No sandbox refactor is needed.

Other reviewed evidence:

- The real consuming run passed the 12-request/14-generation synthetic repair
  control, including rejected Python, applied wrong state, third-attempt repair,
  matching native IDs, identical render/completion bytes and current-only recap
  removal. Its terminal private check IDs match the registered cumulative set.
- Extra independent render controls returned an oversized token list and an
  incorrect argument schema. Each persisted its error after one render request,
  with zero generations and completion marked `NOT_STARTED`.
- Extra independent 12-request/12-generation synthetic control replaced the
  first candidate with a private-only functional mutant. Public stopping still
  ended that request after one call; the actual mutant appeared in the next
  request's module; its cumulative private failure remained; private check IDs
  never entered model payloads. The result was complete accounting and mechanical
  no-go, with no private-based attempt selection or gold reset.
- Native capacity, invalid-response JSON, prompt-ID mismatch and malformed usage
  each terminate the entire synthetic run, preserve raw response bytes and mark
  the remaining 11 requests unattempted. Driver `competence_go` remains null;
  source/dependency and lifecycle review are separate prerequisites.
- Initial preview SHA256
  `ebd333a108947d15f3ffbe6d1da3e1d371012b8bba369a48920f0f42b99e2fa9`
  binds bank `c9feaa9370244ccc4a84221ecb5b3db3ea85d11f9abd210536e78fd25cd6cdaa`
  and runtime `5a06b47d...`. Every reference argument body/source hash was
  independently reconstructed from the accepted bank without executing it.
  All 12 have at least 400 tokens headroom including one EOS token. The four
  cold local JSON-serialization counts are 1343, 2082, 1871 and 2121; these are
  explicitly provisional, not native prompt counts. All 36 diagnostic global
  envelopes fail to certify universal fit, consistently with the accepted
  prospective clarification.
- Resource arithmetic independently recomputes to 617 possible sandbox checks,
  11.393013 estimated CPU seconds from the accepted 851-check/15.713864-second
  CPU receipt, and 2394.083294 illustrative total seconds using the registered
  prior completion rate. The 305.916706-second margin is an estimate; actual
  render, prefill, generated-code execution and cleanup remain within the single
  hard reservation. These prospective estimates do not guarantee completion.

### Launcher handoff continuation, 2026-09-08

Reviewed `tools/run_coding_competence.py` SHA256
`a9e9c2b8fac11b8469f9690240e661aedbc474d909138c8031d9e9abc425cbd2`
and `tests/test_run_coding_competence.py` SHA256
`8107c73e16b8fa33b841b3bf9cf75cf8ae3916c5fda2d88abe2fbe941fe9c816`.
Independent targeted suite: 12 passed in 0.20 seconds. The actual canonical
`validate_artifacts()` consumer accepted bank `c9feaa93...`, CPU receipt
`552baba5...` and final-runtime preview `e9773cdd...`, with minimum reference
headroom 400 and the disclosed false diagnostic envelope aggregate.

2. **low — unexpected driver exit codes are not normalized to incomplete.**
   A synthetic owned driver exiting `-9` produces launcher return code `-9`
   (shell status 247) and lifecycle `DRIVER_EXITED`. Its raw `driver_exit_code`
   is correctly retained and owned cleanup succeeds, so this cannot create a
   false success. It nevertheless bypasses the registered 0/1/2 outward exit
   convention. Preserve the raw driver code but report outward 2 and
   `INCOMPLETE_DRIVER` for codes outside `{0, 1, 2}`. This is a nonblocking
   reporting defect, not a failure of scientific accounting or ownership.

An independent fake-process timeout control advances the actual lifecycle's
injected monotonic clock to its computed driver deadline. The launcher stops
only that owned driver, saves its partial stdout/stderr, removes its owned
container and returns 2/`INCOMPLETE_DRIVER`. The external driver deadline is
2740 when the reservation deadline is 2800: all 60 seconds of cleanup reserve
remain when driver termination begins. No second driver or model call is made.
The reviewed launcher binds code/data/contracts/reviews to tracked clean files
and exact hashes, rechecks its original freeze before server startup, uses both
required Hermes flags, reserves an exclusive new run directory and ownership
flag, and holds the review lock through the lifecycle. Cleanup failures override
driver success and retain the flag when removal is not established.

## Round 2 — final joint readiness review

Score: 96/100. ACCEPTED for the registered single prospective competence run.
Zero open findings; zero high or critical findings. This accepts preparation
and the inspected prospective sizing clarification, not worker competence or
automatic focus. No worker generation has occurred in this review.

Final inspected snapshots:

| Artifact | SHA256 |
| --- | --- |
| `scripts/coding_competence_run.py` | `4e39d6f0fea4234643447bc1a31a2fb2caad7f1c5e35803537585c1d43812c94` |
| `tests/test_coding_competence_run.py` | `ce991821aa703af3e93e690571e89f1ddfd35ae0db69c00d51730fbec948ef18` |
| `tools/run_coding_competence.py` | `020d112e0980a38cff153dc396058d09b51a00ccfda80083aea3b1b0196c432f` |
| `tests/test_run_coding_competence.py` | `77a44981c1f9b353042350eb4bdb7c4613821763a4f24a202d327d272e78a7f6` |
| `PROTOCOL.md` | `d99708acc6058b4726446df39d3747eaa203d1ac0a3af010b7b71d4a252a294b` |
| `RUNTIME-BRIEF.md` | `d6328b6ffabc58160dd8ad175a57be517889a5dedb179c735c2ea5f63ec75023` |
| `NATIVE-CONTRACT.md` | `d324c5fa599e56ddeaac69c3dd44e8f3e338805a2c37903362e456f75c472374` |
| `DATA-CONTRACT.md` | `d107a5077bb88854ef816dbd93cd5cf94a6b5f365e46c2a5d0b8f650b6837796` |
| `kimi-dev-reviewed.json` | `c9feaa9370244ccc4a84221ecb5b3db3ea85d11f9abd210536e78fd25cd6cdaa` |
| `preflight.json` | `552baba5438c530b8dfb88724e18d4d5f5d0b3d20c5a1a8df3fbcd2e4f4b45fd` |
| `preview.json` | `e9773cddb4613743b5e3b78a481d3d9adee928de4ac3d59d00c22ca01d98f0eb` |
| `RESOURCE-PLAN.md` | `b1af1ec1c44d9e49da8ea600906be8f8ced436267cf3284c51ee732637b88d5a` |
| `data-review-astra.md` | `97e700308e6316863e4a2622a0214c5297ae083f3a3ee7cfdb84de03a293bc8e` |

1. **medium (resolved 2026-09-08) — check admission reserve.** The final runtime
   reserves the inherited two-second sandbox allowance plus the one-second
   receipt allowance before each check. The added consuming-path control admits
   zero checks when only 1.2 seconds remain and saves every unfinished check ID.
   The earlier partial-completion persistence control still passes. Independently
   reran the targeted runtime suite after this change: **9 passed in 6.50 seconds**.

2. **low (resolved 2026-09-08) — unexpected driver exit normalization.** The final
   launcher retains the raw `driver_exit_code` and logs, but returns 2 with
   `INCOMPLETE_DRIVER` for codes outside `{0, 1, 2}`. The new `-9` consuming
   lifecycle test checks that classification, the raw code, partial stderr,
   owned cleanup receipts and flag removal. Independently reran the targeted
   launcher suite after this change: **13 passed in 0.25 seconds**.

The initial preview/resource snapshots remain separately preserved. I verified
that the final preview binds the corrected runtime and that its
`reference_actions`, `context_preflight` and `resource_bounds` are exactly equal
to the preserved initial preview. No bank checks, reference execution or model
calls were repeated for that verification. The argument/source hashes, 400-token
minimum reference headroom, four provisional cold counts, 36 diagnostic history
slots and stated resource arithmetic therefore remain supported by round 1.

The final source preserves the reviewed fair stopping rule and M-only treatment:
at most three native candidate calls per request, current-only manual reminders,
actual accumulated modules, native action/result history, public-only feedback,
and once-per-endpoint cumulative private checks. An endpoint failure cannot be
erased by a later request. Authoritative render validation precedes each decode;
any actual context/schema/native/accounting/cap/transport failure stops the entire
run with remaining requests incomplete or unattempted. No output-dependent cap,
prompt, data, history or retry repair is introduced by either fix.

The launcher freezes the exact committed inputs and reviewed code before server
startup and binds the accepted reviews. Its fixed 2700-second lifecycle, 600-second
startup ceiling and external driver deadline preserve the 60-second cleanup
reservation, including when the driver overruns its own internal deadline.
Ownership and cleanup failures cannot produce an accepted success. Parent must
perform the registered fresh environment/ownership checks and exact clean commit
freeze before invoking the single execution; these are the inspected launch
path, not requests for new human approval.

Known limits are disclosed and remain eligibility conditions: local cold sizing
is provisional; future worker histories are unknown; actual native grammar
compilation has not yet been exercised; throughput estimates do not guarantee
completion. A failed actual condition ends this operating point without rescue.
The driver's `mechanical_go` cannot establish final `competence_go`; the produced
code/dependencies, private endpoints, complete accounting and terminal owned
lifecycle still require independent result review. Keep this readiness file
unchanged after freezing and write the result audit to a separate artifact.
