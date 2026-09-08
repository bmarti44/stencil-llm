# Independent automatic-reasoning readiness review — Astra

2026-09-08. Native Astra, xhigh, explicitly selected by the user; author-disjoint.
Purpose: the bounded automatic selector/worker loop, source authority and scope,
actual history/state, public/private separation, native fidelity, complete work
accounting and owned deadline/lifecycle. The threat model is trusted but fallible
authors, callers and model outputs, not a malicious same-user agent. This topic
will bind stable integration artifacts before any final readiness decision.

## Round 1 — runtime component 94/100; combined readiness PENDING

One open medium runtime finding; zero open high or critical runtime findings.
This is a preliminary component assessment, not final combined acceptance or
launch authorization. Corrected data, launcher, canonical preview and final
resource/freeze evidence were not settled when this round was reviewed. The
separate data-review findings retain their own status and are not waived here.

Stable runtime commit: `7e75f057`.

| Reviewed input | SHA-256 |
| --- | --- |
| `scripts/coding_auto_reasoning.py` | `758b99d48e7c3e8f8d817b32a1c4e97b0b348b710e07ef2588fa291266e8974f` |
| `tests/test_coding_auto_reasoning.py` | `86fb4e7ce04b61da3f712690707ad3e657728b7e70186410936fed4ed5590843` |
| Accepted `src/stencil/focus/native_reasoning_tool.py` | `79beddd2d8aa50f637895c071ad5d46b791efd7cf6b1fefbd8d1de17c33263d7` |
| `results/coding-auto-reasoning/RUNTIME-BRIEF.md` | `2f9cec123a742c229b05450182331b9c426f9165890e9240a8023d130317b64e` |
| Accepted `results/coding-auto-reasoning/DESIGN.md` | `6891d83ad2f6aac7d88bbec3d88a7c6337dd9337d011a1a95c9ccb3c3f9be1dc` |
| `results/coding-auto-reasoning/client-review-astra.md` | `1077006c3390ce85991e77716d28c1beb345a14be060f7a49f6d6daae6646d86` |

Reused native transport, exact edit/check consumer and sandbox boundaries were
inspected in their unchanged predecessor implementations. No moving launcher
was read. No real bank, model/server call, old-case replay or implementation/data
edit was performed. The authorized targeted tests use synthetic fixtures and
the existing CPU consumer/sandbox; they do not evaluate the fresh authored bank.

### Finding 1 — medium, open: preview's reference focus is an unprojected active-rule inventory

`scripts/coding_auto_reasoning.py:971`, `_reference_arguments`, serializes every
`oracle.effective_rules` entry as `text`/`source_ids`. It does not inspect the
current task handle or the entry's scope. `preview` then treats this object as
the `record_focus` reference action and uses its headroom for eligibility.

An active inventory may contain a future task's rule or rules pertaining to
other functions. The accepted design requires a complete, source-correct
**current** focus reference, including correct scope and dependencies. The
present transformation does not establish that meaning. It can include a future
obligation and does not establish whether a rule about a called dependency is
relevant or should be qualified in current prose. Grammar validation and token
counting cannot resolve that semantic question.

Use a narrow typed current-scope projection with an explicit independent
completeness/dependency review, or label the all-active serialization as a
diagnostic bound and separately bind a reviewed complete current-focus reference.
Do not infer applicability with regex/prose heuristics or alter runtime focus
using the oracle. Add a focused consuming check for a visible but other-task
rule so preview cannot silently identify the whole inventory as the current
reference again. This concerns prospective reference meaning and capacity;
the reviewed runtime does not send these private reference objects to a model.

### Execution-path assessment

The loader validates the two single-project inputs separately, retains both
receipts and rejects duplicate episode IDs. Each request appends only its
authentic source messages and current request to a separate event list. Selector
input contains original IDs, roles and text plus the current task handle, with
no module, worker call/result, prior generated focus, reference, oracle or check.
The source-ID enum is built from that exact prefix. The selector system states
user/adoption authority, scope, modality, permissions and retirement explicitly;
it does not promote quoted or assistant text.

Every returned obligation is rendered in order with its text unchanged and IDs
preserved. Empty focus remains empty. The selector action, parsed focus and
rendering are saved before the first worker call. Focus stays outside persistent
worker history and is fixed across the two attempts. Worker system and current
prompt label it fallible advisory guidance, subordinate to authentic sources and
incapable of establishing new user adoption.

Worker history retains original source roles/text and actual final native tool
calls with matching public tool results. Each project has independent state.
The current prompt uses the actual accumulated module and cumulative public
checks. The disclosed function subset matches the relevant consumer prohibitions.
Exact source arguments reach the unchanged splice/compile consumer; a rejected
patch receives factual public feedback, while an applied wrong patch stays in
state. The loop allows at most two worker attempts and stops early only after
an applied edit passes all cumulative public checks.

Only after that public decision does the loop run terminal initial/cumulative
private-functional/current-obligation checks. Their outcomes do not enter
history or select another attempt. A completed semantic failure remains failed
and later requests continue on the real state; no reference reset occurs.
The project gate requires all three endpoints for at least one project and
complete accounting for both projects. `pilot_go` stays null pending independent
source/focus review; mechanical success is not treated as semantic or scientific
acceptance.

All six planned request records are created before calls. Call records preserve
messages, request bytes/hashes, raw native exchange, module state, attempts and
failures. The shared client receives one monotonic deadline and performs its
render/cap/token/usage checks before accepting an action. The incremental check
helper reserves the inherited two-second sandbox allowance plus receipt reserve
before each check and writes each completed check and remaining IDs immediately.
Technical selector/worker failures stop the batch and retain later requests as
unattempted. Absolute server/driver termination and cleanup still require the
unreviewed launcher; client socket timeouts alone are not that guarantee.

### Independent validation and outstanding evidence

- `.venv/bin/pytest -q tests/test_coding_auto_reasoning.py`: **9 passed in
  20.25 seconds**.
- Ruff on the runtime and its targeted test file: **PASS**.
- Runtime/test hashes were rechecked unchanged after validation.

The tests exercise real data validation, exact edit application and sandbox
checks with a scripted client: source-only selector privacy, original quoted
assistant text, visible versus future IDs, empty and multi-item focus, ephemeral
history, actual wrong dependency carryover, two attempts, selector/worker failure
denominators, partial check persistence, project-level candidate decisions and
absolute-path CLI preview. The scripted transport does not itself test the
native client; that boundary has its separate accepted consumer review. Final
integration remains to be checked against the stable launcher and preview.

The preview appropriately marks serialized selector counts as local rather than
native prompt counts and disclaims knowledge of future generated history. It
uses the registered 1,021 final-token allowance and 128-token headroom, reports
18 renders/18 generations and accounts for maximum scheduled sandbox checks.
Finding 1 must be resolved before treating its current-focus reference capacity
as qualified. No actual corrected-bank preview or final resource plan is
accepted in this round.

Remaining before combined readiness: settle finding 1; accept corrected data
through its existing review; inspect stable launcher ownership, absolute budget,
freeze and cleanup; then bind the exact final preview/resource/code/data/review
hashes. Preserve this round and finding number when appending that decision.

## Round 2 — runtime component 96/100; combined readiness PENDING

2026-09-08. Narrow runtime delta, commit `117cc471`. Runtime SHA-256:
`4e11075af871ce8bad7d0d9e85005a407f6ebd422da29468e08271cf1f1770cb`.
Targeted test SHA-256:
`51d24fde085f2fd466477a67c33b5192d4dbfd7704b05f18b58a6bcb356b9c9a`.

**Finding 1 — medium, resolved 2026-09-08.** `_reference_arguments` now reads
the current request's task handle and includes exactly active entries whose
typed scope is `global` or that handle. Text, citation IDs and relative order
are preserved. The change affects offline reference preparation only. The new
regression invokes the actual preview consumer with current, global and visible
other-task entries, verifies the exact selected argument body and its actual
token count, and excludes the other-task text. Independent targeted result:
**1 passed, 9 deselected in 3.90 seconds**; Ruff on the two files — **PASS**.

The separately completed data review accepted the corrected bank at 96/100,
with no open findings, and explicitly verified this projection's semantic and
dependency boundary for these documents. Its SHA-256 is
`e287b5de9c44f1d26f78dd8ed92906a6dd44d72e31b818388b3e381e1998dbce`.
I verified the copies at `author-00/reviewed.json` and `author-01/reviewed.json`
retain the accepted hashes `1a5f91d4e0fac8ee467741bbcafd581a11a40e04ddcdb384b41a49e8d54617b0`
and `9e866c8ada769e6371615d509000ff02fd3d3dc6056e64e73213183417ee1dc8`.
The filter is not a general semantic proof, and accurate API notes do not require
the selector to repeat the full algorithm.

Zero open runtime findings. Final combined readiness remains pending stable
launcher review and terminal preview/resource/freeze evidence. Neither the
moving launcher nor the in-progress preview was read in this delta. No model,
server, real-bank execution or data/implementation edit was performed.


## Round 3 — final combined readiness 96/100; ACCEPTED for the fixed pilot

2026-09-08. Zero open low, medium, high or critical findings. Finding 1 remains
resolved; the final launcher now applies the same reviewed current-task scope
projection as the runtime. No new numbered finding was established. Earlier
rounds and their scores remain unchanged.

This accepts readiness for **one frozen 3,000-second automatic pilot** with two
projects, all six requests, one selector call per request and at most two worker
calls per request. The parent must independently accept this final report,
commit the exact bound files and pass the launcher's clean-freeze/exclusivity
checks before execution. The review does not itself launch anything or supply
new experiment permission. No automatic utility, useful manual-prose parity,
population reliability or larger paired proof follows from readiness.

The assessed direction is the accepted untrained, reasoning-enabled automatic
source-focus path. It does not revive the parked nonthinking reader or self-cue
recipe, and it does not establish or replace the separate supervised conditional
direction's empirical claims. A useful automated result can justify subsequent
engineering work without outperforming a perfect manual comparator. This pilot's
narrow continuation still requires independent inspection of a whole usable
three-request project and all three complete, source-correct focus views for
that project, together with full denominator and failure accounting. The runtime
properly leaves `pilot_go` unset; finite checks alone cannot decide that outcome.

### Final integration and consuming-path evidence

Reviewed the full stable launcher and targeted tests, commit
`037703d8ab95fbcabddf65a422c7152156846967`, including its integration delta from
`4a5a451d`. Its independent synthetic fixture now constructs the projected
reference body without calling the implementation under test. The actual
`validate_artifacts` consumer accepts global permission, the current rule and
a global exception while excluding a visible other-task rule. This agrees with
the runtime fix and the separately accepted source/dependency review; the typed
filter itself remains no general semantic proof.

The actual canonical artifact validator passed independently: two exact reviewed
input receipts, matching zero-call preflight nested inside preview, all six
request identities, 12 edit/focus reference bodies, fixed settings, complete
schedules and source/tokenizer hashes. I independently reconstructed all six
cold selector messages and request bytes through the payload path, matched their
visible source IDs, byte counts and hashes, and recomputed all six local cold
counts and all 12 reference argument counts with the pinned tokenizer. This
performed no HTTP request and invoked neither preview nor preflight. It checked
recorded capacity evidence without repeating the parent's 465 CPU executions.

Independent launcher validation:

- `.venv/bin/pytest -q tests/test_run_coding_auto_reasoning.py`: **8 passed in
  0.13 seconds**.
- Ruff on the launcher and its targeted tests: **PASS**.
- Absolute-path default dry-run from `/tmp`: exit **0**; the requested run
  directory and `RUNNING.flag` remained absent.
- Actual `validate_artifacts`, `validate_smoke_evidence` and unchanged trunk
  metadata qualification: **PASS** on the final canonical bytes.

The targeted launcher tests cover the actual artifact consumer, stale source
rejection before environment work, default dry-run, combined-budget rejection,
existing-run preservation, the reused lifecycle's exact driver/deadline
forwarding and removal of only the invocation's flag on prelaunch failure.
They mock process interfaces and do not start a daemon. Earlier runtime/client
results are retained in this report and their accepted component review; no
claim is made that these launcher tests independently reproduce native inference
or exhaust every inherited lifecycle failure path.

The launcher freezes 28 named tracked source/test/artifact/review/evidence files
and four model metadata files. It checks tracked cleanliness and exact HEAD,
then rechecks the snapshot and resources after exclusive flag reservation and
before server creation. Its review handling binds exact bytes; the parent, not
a brittle prose-score parser, makes the acceptance decision. The final report
must remain unchanged once frozen; terminal auditing belongs in a separate run
artifact. Model qualification checks the accepted 20-file, 61,078,009,236-byte
manifest's size/mtime and hashes the four metadata files. It does not claim a
new full-weight content hash pass.

The fixed container command exactly reuses the accepted smoke generator: pinned
image, read-only local model, Qwen3 reasoning parser, Hermes tools and 32,768
context. The loop retains the accepted client's same-byte render/generation,
forced named-tool schema, native setting checks, prompt/output ID and usage
validation, exact final whitespace and actual terminal EOS accounting. Actual
reasoning must have one valid boundary pair and stay within 1,024 tokens;
a measured count alone cannot establish that budget forcing caused termination.
The selector sees only the authentic source prefix. The worker gets all returned
current focus as fallible advisory text, actual accumulated code and final-only
worker tool history, with no prior reasoning replay or private endpoint feedback.
No reference focus substitutes for the returned selector action.

Ownership and budget use the unchanged reviewed `run_lifecycle`, not a copied
framework. Every launched process uses the ownership registry. The 3,000-second
monotonic reservation begins with server launch, includes a 600-second startup
ceiling and retains 60 seconds for cleanup. The external driver wait enforces
the absolute remaining deadline; the driver also receives its remaining budget.
Timeouts and unexpected exit codes retain partial logs/receipts and become
incomplete. Normal driver codes 0/1/2 are preserved. Cleanup targets the newly
created named container, or verifies its exact ownership label after uncertain
startup; cleanup failure, missing evidence or elapsed-budget excess prevents
success. The run flag persists when removal is unconfirmed. A preexisting run
is rejected, and `run_created` prevents failure receipts from overwriting a
directory this invocation did not create. Readiness is not a guarantee against
an unresponsive operating system or successful future cleanup; actual lifecycle
receipts and final resource absence must still be audited.

### Capacity, timing and limits

The final preview is PASS with zero model calls. Its standalone preflight is
identical to the nested receipt: 465 checks, 8.286304591980297 seconds;
full preview elapsed 8.343103285995312 seconds. These are preserved parent
executions, not reviewer reruns. Focus argument counts are 189/193/261 and
141/222/327; edit counts are 170/105/334 and 585/323/687. Against the 1,021-token
final allowance, minimum reference spare is **334**, above the registered 128.
This qualifies those complete reference serializations, not arbitrary future
model output or a requirement to repeat the whole algorithm in focus.

Cold selector JSON counts plus the full 2,048 reserve range **2,942–4,433**.
They are local request serialization counts, not native rendered prompt counts.
The maximum schedule has 18 renders, 18 generations, 36 HTTP requests and
262 live sandbox checks; the latter was independently reconstructed from the
cumulative public and terminal private schedules. Up to five earlier worker
action/result pairs and six module observations can accumulate. Their actual
future contents remain unknown. Each actual request must pass its authoritative
native render plus full output reserve before decoding. Overflow is incomplete
work; no truncation, cap increase, extra attempt or post-output rescue is allowed.

Recomputed resource arithmetic uses the richer-context historical effective
rate, 5777 / 307.08357315306785 = 18.812468347567442 tokens/second. The maximum
18 × 2048 generation estimate is 1959.551469744624 seconds. Adding 600 startup,
60 cleanup and 120 other work gives **2739.551469744624 seconds**, leaving
260.448530255376 inside the 3,000-second reservation. This is plausible planning
evidence, not a worst-case throughput guarantee. The tiny smoke's faster rate
was not substituted. The audited smoke's actual **516.914703271992 seconds**
plus this reservation is **3516.914703271992 seconds**, leaving only
83.085296728008 under the existing 3,600-second candidate ceiling. No further
run or budget is implied.

### Exact final bindings

The following SHA-256 values were independently rehashed after targeted
validation. The runtime's settled commit is `117cc471`; the shared client's
settled fix is `59f19d67`. The prior report bytes before this append had SHA-256
`0145923ae204a02ed3c8d34c32a0a24ba31e1987ba00a3d9f926dc68bac09e7d`.
This report's final hash is supplied separately to the parent and frozen by the
launcher; a report cannot contain its own final content hash.

| Input | SHA-256 |
| --- | --- |
| `src/stencil/focus/native_reasoning_tool.py` | `79beddd2d8aa50f637895c071ad5d46b791efd7cf6b1fefbd8d1de17c33263d7` |
| `scripts/coding_auto_reasoning.py` | `4e11075af871ce8bad7d0d9e85005a407f6ebd422da29468e08271cf1f1770cb` |
| `tools/run_coding_auto_reasoning.py` | `0c66ad012f00dd67f3f4e6b9acd3393b172042c29f1794f793a366b073698eb6` |
| `scripts/coding_competence_run.py` | `4e39d6f0fea4234643447bc1a31a2fb2caad7f1c5e35803537585c1d43812c94` |
| `scripts/coding_competence_dev.py` | `695e9e6228d6ed540d0235442ec3aa515ff1f00b6f3ad303ba76354feaa407a0` |
| `scripts/coding_worker_dev.py` | `41c33ad88fc1fca8d123a71580683d3f478d96c4f1f2f41889303f40c7551b26` |
| `src/stencil/focus/slab.py` | `3f3a9f04ee9bae3395c3fdf5d3011e2b8cca4b930332a72dd2edafce7de04b59` |
| `src/stencil/focus/slab_sandbox.py` | `3dad55e31b23fd859a9fcf805b3694acc99c8efdb48c35ed82ca78b16f9d7de8` |
| `tools/run_coding_competence.py` | `020d112e0980a38cff153dc396058d09b51a00ccfda80083aea3b1b0196c432f` |
| `tools/run_qwen_thinking_tool_smoke.py` | `e91c6075782cf304bf4d25e24672ca646024d1311ac86d2cc4183c4ce09dd0a4` |
| `scripts/qwen_thinking_tool_smoke.py` | `aa40011d5459e7e19455fe5baf828473cf65e478c64cc86a068ea366c1056746` |
| `tests/test_native_reasoning_tool.py` | `1c9cf384780f8a66cb9b66ad3cfacb7d9af2343f02733d93093bdf63704a22c4` |
| `tests/test_coding_auto_reasoning.py` | `51d24fde085f2fd466477a67c33b5192d4dbfd7704b05f18b58a6bcb356b9c9a` |
| `tests/test_run_coding_auto_reasoning.py` | `c7632cd8a5fcb6771c37916167ea2930196a9b55f257b74edd892af076c2b6a0` |
| `results/coding-auto-reasoning/DESIGN.md` | `6891d83ad2f6aac7d88bbec3d88a7c6337dd9337d011a1a95c9ccb3c3f9be1dc` |
| `results/coding-auto-reasoning/DATA-CONTRACT.md` | `502410a3f48b3355135e9cab1f3000fb040d3ff3fd77daf067bfaeb99e78cc5d` |
| `results/coding-auto-reasoning/RESOURCE-PLAN.md` | `ed9ce78cd73557b41eee7bee7636748f41147909ccd49aa70eba15703591b300` |
| `results/coding-auto-reasoning/preflight.json` | `7df5934ac42445a02f3d1549ba54dcf1d83c4dc09925ce1308cb411ca41547f4` |
| `results/coding-auto-reasoning/preview.json` | `86fbc268dfc44fc21f741c7cdc6200d5d1d8147112c10aa1072a48048ff977de` |
| `results/coding-auto-reasoning/author-00/reviewed.json` | `1a5f91d4e0fac8ee467741bbcafd581a11a40e04ddcdb384b41a49e8d54617b0` |
| `results/coding-auto-reasoning/author-01/reviewed.json` | `9e866c8ada769e6371615d509000ff02fd3d3dc6056e64e73213183417ee1dc8` |
| `results/coding-auto-reasoning/design-review-astra.md` | `d48acaa46d0a4b68335a979f90f503d1bf8b3b253e2d131a1b34b1bd9ab0231d` |
| `results/coding-auto-reasoning/client-review-astra.md` | `1077006c3390ce85991e77716d28c1beb345a14be060f7a49f6d6daae6646d86` |
| `results/coding-auto-reasoning/data-review-astra.md` | `e287b5de9c44f1d26f78dd8ed92906a6dd44d72e31b818388b3e381e1998dbce` |
| `results/coding-reasoning-smoke/run-01/lifecycle.json` | `c8d64291afeee558877ebc24c1a2c3836a47a6e65739e6232aa1a51537960697` |
| `results/coding-reasoning-smoke/run-01/audit-astra.md` | `100bfa17a70dbcb2e03581e087de9f1cdb9163e72b99e0246cb99005c95a2182` |
| `results/factorial-prep/current-trunk-hashes.json` | `db3962fe0b3fed68cd73e7041b5b2b18db14536def0290a39e19a0c3fb26153a` |
| `models/qwen3-30b-a3b-hf/tokenizer.json` | `aeb13307a71acd8fe81861d94ad54ab689df773318809eed3cbe794b4492dae4` |
| `models/qwen3-30b-a3b-hf/tokenizer_config.json` | `d5d09f07b48c3086c508b30d1c9114bd1189145b74e982a265350c923acd8101` |
| `models/qwen3-30b-a3b-hf/config.json` | `2850ddb3bf7aecad20b611e2d44f3077fc8193f4827c93beddd4c02ad63c2297` |
| `models/qwen3-30b-a3b-hf/generation_config.json` | `2325da0f15bb848e018c5ae071b7943332e9f871d6b60e2ed22ca97d4cb993d2` |
| `results/coding-auto-reasoning/CLIENT-BRIEF.md` | `dddc4b9234a4684bb2c1531d9aba3d3a2f5ac518d52211a3bff594fce1c181b7` |
| `results/coding-auto-reasoning/RUNTIME-BRIEF.md` | `2f9cec123a742c229b05450182331b9c426f9165890e9240a8023d130317b64e` |
| `results/coding-auto-reasoning/LAUNCHER-BRIEF.md` | `ee154653bf3ddd286569ddce87d258988616e53bbd99d12dfb2ec19d42ce28f1` |

The three implementation briefs are review inputs bound above; the launcher's
28-file tracked list binds the governing design/data contract, resource plan and
accepted reports along with implementation and evidence. No implementation,
authored data, earlier frozen review, old benchmark or model state was changed
by this review. The parent owns final freeze, exclusivity qualification, one
execution and terminal audit; no new permission question or extra GPU work is
introduced here.
