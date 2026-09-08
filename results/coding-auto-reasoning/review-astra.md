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
