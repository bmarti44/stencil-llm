# Original-source replay prospective review

Canonical topic: source-replay. Reviewer: gpt-6-astra, xhigh, native agent
`source_replay_review`, author-disjoint. Date: 2026-09-08. The current user's
explicit Astra xhigh selection supersedes the older Opus selection in AGENTS.md;
no availability substitution was made. No wrapper or additional agent was used.

Purpose: decide whether this bounded first screen and its separate technical
qualification are scientifically useful, fair, and concrete enough to implement.
Threat model: trusted but fallible authors and consumers, including accidental
metadata leakage, stale checks, history contamination, and optimistic costing.
This is a prospective document review, not implementation or data acceptance.

## Round 1

Score: 96/100

Disposition: ACCEPT the reviewed prospective documents for the stated next
implementation stage. Zero open high/critical findings; both medium findings
below were corrected and independently re-read before this initial round was
finalized. This does not authorize a screen launch or establish any model benefit.

### Reviewed versions

Repository base: `e8917b8911ac53c5e376ccf48a349f15dd27f183`, plus the reviewed
working-tree document changes. Final SHA-256 bindings:

| File | SHA-256 |
| --- | --- |
| `results/source-replay/SPEC.md` | `01da819289d264926e8492a947b3bf8d6893b89c7559ff8142b9c4dabebda78c` |
| `results/source-replay/DATA-CONTRACT.md` | `6ae44a7794701686cf06a0c32551d9d92b96fb582cd042dee73be95a917a7e4a` |
| `results/source-replay/QUALIFICATION-BRIEF.md` | `ecc52bc7a046e084aa0a84cb68859ce45e4b757c38f129e8d61fc9ca88b4ea31` |
| `results/source-evidence-research/report-source.md` | `a7e7cb46c51734ad3600fbad78714fe2c02aa62b8a592bf9ee94b979ec7ae220` |
| `results/source-evidence-research/feasibility-sol.md` | `522ffe2c0fae3edf62fd13ac0f9d4edec829338fcdc8a742857da49877ff765d` |

Initial reviewed SPEC/DATA/QUALIFICATION hashes were respectively
`61a9acc31b37e8e1a9c9d8c18d5a85f75092bc0e55cb88c7fb7a8bb6409bb20e`,
`d0f16c88e90d5cc19d848833bb78066f5258c4a6f46f8e26639fb2ede45865c3`,
and `82b9c5a9bfa4ab84aac89ef2c2d8aeab8da87df4610666b1ed57e3394676761c`.
The orchestrator made the changes; this reviewer wrote only this review file.

### 1. [medium] Public check metadata could disclose future retirement and authored interpretation (resolved 2026-09-08)

The initial DATA-CONTRACT made `active_through_round`, `source_ids`, `behavior`
and `rationale` part of each public check, while SPEC placed active public checks
in the worker envelope without defining a narrower projection. Serializing those
objects directly would disclose a future retirement endpoint and author-written
explanations of which sources govern behavior. That would make the history
control receive additional rule interpretation and could obscure the reminder
comparison. No implementation or exposure had yet occurred.

The final documents explicitly allow only `check_id`, `symbol`, `input` and
`expected_values` in worker case inputs. Interval, grounding and coverage fields
remain controller/audit metadata and are excluded from both prompts and public
tool feedback. This resolves the ambiguity without removing useful public cases
or adding a gold selector. Static inspection also confirmed that the reused
`run_checks` reads `rule_ids`; the specified internal `rule_ids=[]` adapter
provides compatibility without introducing obligation prose.

### 2. [medium] Two-call interface success did not define screen affordability (resolved 2026-09-08)

The initial documents required an affordable setup but gave no reproducible
mapping from qualification and actual check workload to a launch decision. A
tiny fixture completing within 600 seconds alone would not establish that the
48-call screen was sensibly projected within 3000 seconds; the check schema
also has minimum counts without a fixed maximum.

SPEC now defines `C` as all three arms' planned active check executions, `q` as
the maximum measured reference/mutant preflight check time, and `r` as the slower
qualification render time. Its explicit gate is
`600 + 2041.199447651 + max(120, C*q + 48*r + 60) + 60 <= 3000`.
The qualification brief requires this later gate independently of interface
eligibility. Excess projection stops preparation without reducing the workload
or changing the candidate.

This resolves the missing decision, not the uncertainty in extrapolation.
Generation cost remains historical; two short render timings and reference
execution timings do not bound larger histories or erroneous programs. SPEC
states those limits and retains the whole deadline and INCOMPLETE stop. A
representative performance benchmark or a new tuning opportunity is unnecessary
for this bounded preparation decision.

### Assessment supporting acceptance

- **Scientific utility and thresholds:** H/S/R isolate the practical addition of
  source reminders while exposing whether recent sources suffice. S may choose
  fewer messages than R under the same allowance; this is explicitly not a token
  or cardinality match. Four project trajectories, the absolute 9/12 and 3/4
  requirements, paired improvement rules and cost ceilings are usable screening
  decisions. They cannot establish significance, equivalence, general coding
  competence or superiority over useful manual reminders. The larger untouched
  comparison remains required, and automating useful manual behavior remains a
  valid benefit. No extra arm or perfect-source-selection prerequisite is needed.
- **History and authority:** Original source/request text, each arm's actual
  assistant/tool history, and permanent work envelopes survive. Only the
  registered supplemental reminder is ephemeral. Separate evolving modules and
  actual failed actions prevent reference resets or cross-arm repair. Ordered
  complete messages preserve provenance without promising correct applicability.
  All authored roles are user, so broad cross-role authority is properly outside
  the claim. The selector receives no code trajectory, results or private tests.
- **Checks and data:** Inclusive intervals, versioned changed expectations,
  source-grounded independent review, sequential references and one retirement
  mutant per project address concrete test validity risks. Old checks remain
  active only while their expectations apply. Hidden boundary/interaction cases
  and explicit retained/retirement coverage make this more than an extraction
  quiz. The test counts are never independent experimental units. Actual source
  correctness and adequate coverage remain to be checked on the future data;
  this acceptance supplies neither by assumption.
- **Arithmetic:** `4*3*(3+1)=48` generations comprise 36 worker and 12 selector
  calls, with 48 authoritative renders: 96 corresponding HTTP POSTs. Output
  allowance is `36*1024+12*128=38400`. Independently recomputed historical rate
  is `18.8124683475716` tokens/second, giving `2041.1994476502` generation
  seconds and `2821.1994476502` seconds for the initial planning sum. The
  600+3000 reservation allocation is 3600 seconds. These are allowances and
  estimates, not successful work or measured successor speed.
- **Minimal qualification and implementation boundary:** The two-call fixture
  checks delivery/action and reports behavior separately. Keeping the native
  worker unchanged and adding a narrow selector/renderer is appropriate.
  `set_deadline` can share the pair's remaining allowance across render and
  generation; the specification now states this explicitly. The parameterized
  existing lifecycle accepts a driver and reservation plan, so reuse is a
  plausible static boundary. Actual driver deadlines, authoritative token
  accounting, fixture/reference output encoding, history isolation and prompt
  projections still require the planned focused implementation tests and review.
  None was executed here.

### Inspection record

Read AGENTS.md, the archived protocol, the latest ledger STATE, the five context
documents above, and relevant existing client/action/check/lifecycle source
sections only. Exact inspected implementation-file SHA-256 values:

| File | SHA-256 |
| --- | --- |
| `scripts/coding_competence_run.py` | `4e39d6f0fea4234643447bc1a31a2fb2caad7f1c5e35803537585c1d43812c94` |
| `scripts/coding_competence_dev.py` | `695e9e6228d6ed540d0235442ec3aa515ff1f00b6f3ad303ba76354feaa407a0` |
| `scripts/coding_worker_dev.py` | `41c33ad88fc1fca8d123a71580683d3f478d96c4f1f2f41889303f40c7551b26` |
| `tools/run_coding_competence.py` | `020d112e0980a38cff153dc396058d09b51a00ccfda80083aea3b1b0196c432f` |

No code imports, tests, models, GPU/Ollama calls, prior banks, recorded evaluation
responses, commits or other file edits were performed. Research citations were
used as accepted preparation context; this review makes no new literature claim.

## Round 2

Score: 96/100

2026-09-08. Same author-disjoint Astra xhigh reviewer and canonical topic.
Disposition: ACCEPT the authored mechanical fixture for the planned new-consumer
preflight. No new findings; zero open high/critical findings. Findings #1 and #2
remain resolved. This round reviews source/test grounding and preserved authoring
evidence only, not Sol's evolving implementation, native delivery, or utility.
Round 1 is unchanged; its complete pre-append SHA-256 was
`3194ddc51e0a32b1fc5baf2bdbdbf8d0f31972b309e9b7797d98b195cf26523d`.

### Exact reviewed fixture records

All eight files below independently matched their committed bytes at
`785e3158`. Paths are relative to `results/source-replay/`.

| File | SHA-256 |
| --- | --- |
| `qualification-authoring-prompt.md` | `81dd02f61b05c76a13c7144c497fd20c8f0103bdf58e1384a26d97d3ef5b9296` |
| `QUALIFICATION-BRIEF.md` | `ecc52bc7a046e084aa0a84cb68859ce45e4b757c38f129e8d61fc9ca88b4ea31` |
| `qualification-authoring/author-00/request.json` | `9a4e5ed33a6a50f1d92d9dc96e5960d1a6bb5bfcb11f9c26b01c66dbefcae2bb` |
| `qualification-authoring/author-00/response.json` | `7ce9946bb202201065e6cf2ab9d6864b42a30562ead05c3b6d945b91bcb3d892` |
| `qualification-authoring/author-00/authored.json` | `ff167de40c52227c2a5eae1eda34194197d7d1c92337b1c37740aec9c6f8578c` |
| `qualification-authoring/author-00/receipt.json` | `7f6a229da0dd0b6b53a4a0884e5ecfaddd0113b1c9de01ef0b90fad08be77e38` |
| `qualification-authoring/job.json` | `887dd3d37dbf85fb595546be0d3f411afadb2735b7a9fc3a45b3cc6bd80fb821` |
| `qualification-authoring/root-source-check.json` | `b729c9a181d08984782919a54447c416bc0bc67a55700b10ec790fc38ae0acc3` |

### Source, schema and scope audit

The fixture has the requested fields, one original user source `m01`, one direct
user request `m02`, one existing synchronous one-argument function, its complete
replacement, and three distinct finite integer cases. Source/request texts are
105/231 UTF-8 bytes, below 640 each. The initial function and five-line reference
use only elementary arithmetic; no external dependency or changing-rule puzzle
is introduced. Native token headroom is not measured by this source audit and
remains part of the actual preflight.

The source restricts counted coins to quarters and dimes, and the request
explicitly requires taking as many quarters as possible before dimes and ignoring
the remainder. Thus the three cases follow directly:

| Input | Quarters | Remaining cents | Dimes | Required count |
| --- | --- | --- | --- | --- |
| 35 | 1 | 10 | 1 | 2 |
| 7 | 0 | 7 | 0 | 0 |
| 60 | 2 | 10 | 1 | 3 |

No source-permitted alternative allocation is forced out: quarters-first is
explicit. The initial implementation omits dimes, exactly the requested change.
The reference implements that arithmetic and agrees with all three expected
outputs. Root's preserved action/module hash independently equals the exact
reference UTF-8 hash
`853e53c63702d9825b622cb00c6dda0910ed0e1063a9cdae1eff7060b07473b7`.
The recorded unchanged-consumer audit reports all three passes in
0.051326780987437814 seconds and explicitly marks `new_consumer_preflight:false`.
Those execution results were inspected, not rerun or represented as this
reviewer's execution.

One case repeats the request's explicit example, and all inputs are positive.
That is appropriate for the registered delivery fixture. It establishes no
general negative-input behavior, reminder benefit, hidden-benchmark performance,
or complete-focus target. The request itself restates the relevant coin rule;
requiring a selector usefulness challenge here would change the accepted scope.
Reference/check objects must still stay outside future model payloads.

### Provenance and cost audit

The exact request prompt equals the frozen authoring prompt. Parsing the raw
response's `response` string reproduces the complete authored object without
semantic edits; request, response, response-text and authored hashes match the
receipt. The response-text SHA-256 is
`05e898462be610f7445fc24c70e9d6f3eab60f288ffd2f47405199b3d7e6e8af`.
The job records one request and no automatic retry. Its request names
`kimi-k3:cloud`, with `stream:false` and `think:true`; the service response names
`kimi-k3` and reports `done:true`, `done_reason:stop`. The new fixture purpose is
explicit while the reused helper's legacy purpose is preserved separately.

Raw response and receipt agree on 647 prompt tokens and 1682 generated service
tokens, totaling 2329. Service duration is 32.198658203 seconds; receipt elapsed
time is 32.32867383956909 seconds; whole authoring-job elapsed time is
32.33978819299955 seconds. These distinct measures reconcile and are authoring
costs, not local qualification or coding-worker measurements.

The request contains fresh-authoring instructions and no old dataset/example
payload. The lineage statement is an authorship record, not proof of universal
novelty for this commonplace arithmetic task. No stronger novelty claim is
needed. Read-only JSON/hash/arithmetic checks were performed with standard
library tooling; no repository code import, repeated sandbox test, model,
tokenizer, GPU, API call, old-bank read or other file edit was performed.

## Round 3

Score: 82/100

2026-09-08. Same author-disjoint Astra xhigh reviewer. Disposition: REJECT the
first-stage implementation at `8651ab66` pending the two high findings below.
Open findings: source-replay#3 high, #4 high, #5 medium. Findings #1/#2 remain
resolved; Rounds 1 and 2 are unchanged. Their combined pre-append SHA-256 was
`7e487f81f169f956d1734e4e4cb518dc432b1f71da575287bed0ad3c3befc11d`.
The orchestrator received concrete reproductions before this round finalized.
No actual fixture preflight or native qualification is accepted by this round.

### Reviewed bytes and scope

The eight implementation/test files matched both archived commit `8651ab66` and
the handoff `results/source-replay/implementation-sol.json`, SHA-256
`51408a3f77fda296fdd3b48ffef8e34c0851a24539f1711343994d39dbf19467`.
SPEC/DATA/QUALIFICATION-BRIEF remained at Round 1's final bindings. The additional
IMPLEMENTATION-BRIEF SHA-256 is
`f8cda57f72d5c7b995e80b0c7a5f86091b35b32635b2beaf10ac1938d49c9148`.

| File | SHA-256 |
| --- | --- |
| `src/stencil/source_replay.py` | `19f3c7f1948fd74eb25767c007b4b9af567629c15656fed4c529542ffe485d55` |
| `src/stencil/focus/native_source_selector.py` | `f08f1c14d6b8e3001fa3694edfcf7b59f2ed2c7869136686e8f27a03c639fda2` |
| `scripts/source_replay_qualification.py` | `f0a2b2d53ab6c0dcf40a1dab74659d625ea97c5a78005a11c8fc939bcf60e9ce` |
| `tools/run_source_replay_qualification.py` | `761bad5b047c3e68560553617236297e1079a4669482c8fb3a060030ac3c1c6e` |
| `tests/test_source_replay.py` | `6872eecf6190ab9f75613b14606bcb8e742bb22a055d3a7ef43ef998afa6c48f` |
| `tests/test_native_source_selector.py` | `71bc04742e747f1d5f76a5d265125523dad9ba243a8bd0392992700b060c6e41` |
| `tests/test_source_replay_qualification.py` | `c911796aa3df0bfb731d0b22872de372d621821a79c66f6584ab92b8b8b8af47` |
| `tests/test_run_source_replay_qualification.py` | `100aa3834e085789f80bea183a020b0bda2f5ada91e07f028d7396107f2ba24f` |

Review covers only the first-stage renderer, selector client, two-call driver,
launcher and their tests. The future multi-project runner, broader utility and
manual-reminder comparison are not implementation prerequisites here.

### 3. [high] Historical acceptance text can authorize an unaccepted implementation (open)

`tools/run_source_replay_qualification.py:187–222` checks each acceptance by
searching the complete bound file for accepted-disposition and zero-open-finding
phrases. Those phrases remain in this append-only review after a later round
rejects work. The same file can also be labeled specification, fixture and
implementation without verifying the corresponding reviewed subjects or hashes.
Matching the file's current digest does not establish that its current review
accepts the code being launched.

**Consumer reproduction:** constructed only temporary CPU stand-ins, with valid
declared fixture/preflight/tokenizer/code hashes. The bound review contained
Round 1 ACCEPT/zero open high findings followed by Round 3 REJECT/open high
finding. Passed that one file under all three required acceptance kinds to the
actual `validate_freeze`, retaining its actual required acceptance set. Validation
returned successfully. This is a stale-acceptance failure in the consumed path,
not a hypothetical malicious file replacement.

**Required small fix:** validate the latest applicable canonical disposition,
score threshold and open-finding state, and bind required reviewed subject
hashes to the frozen specification, fixture and implementation. A narrow machine
block in this existing review file or a local parser for its actual format is
sufficient. Preserve historical rounds; do not reuse an incompatible legacy
review format or build a general review framework. A latest rejected round and
an accepted review of different subject hashes must fail the actual consumer.

### 4. [high] Docker launch delivery can consume the cleanup reservation (open)

The new plan sets both `reservation_seconds` and `startup_ceiling_seconds` to
600. In the reused lifecycle, the initial `docker run -d` subprocess receives
`min(global_remaining, startup_ceiling_seconds)` before health waiting begins.
It can therefore consume the whole reservation. At that point the lifecycle
skips ownership recovery/stop/remove work because its deadline has expired,
potentially leaving the owned GPU container running.

This finding is specifically about initial Docker command delivery.
`wait_for_server` already subtracts its cleanup reserve; ordinary slow model
health startup is not the uncovered path.

**Consumer reproduction:** called the actual unchanged `owned.run_lifecycle`
with the new plan and injected CPU clock/process objects. The fake Docker command
returned a container ID after using its allowed 600 seconds. The lifecycle
returned `CLEANUP_FAILED`, `cleaned:false`; its only issued command was Docker
run, and the run flag remained. With the identical probe and an effective startup
ceiling of 540, the lifecycle returned `INCOMPLETE_STARTUP`, `cleaned:true`, and
issued logs/stop/remove operations within the remaining reserve. No Docker or
network command was actually executed.

**Required small fix:** clamp the new plan's effective startup allowance to
`min(registered_startup_ceiling, reservation_seconds-cleanup_reserve_seconds)`.
For this qualification that is 540 seconds. This implements the registered
subordinate limits without changing the frozen lifecycle or increasing cost.
Exercise late Docker delivery through the reused lifecycle, not just plan-field
assertions. Preserving the flag when cleanup fails is correct but does not by
itself enforce the reservation.

### 5. [medium] A live sandbox serialization dependency is absent from the bindings (open)

Both `PREFLIGHT_CODE_FILES` and `CORE_BOUND_FILES` omit
`src/stencil/focus/renderer.py`. Its `compact` function is actually used by
`coding_worker_dev._fresh_execute` to serialize cases and by
`slab._execute_cached` to serialize the code/case payload delivered to the
sandbox. A change to that serializer would not invalidate the current preflight
or required launch bindings, despite changing a consumed execution dependency.

Add this one existing file to both required hash sets and verify the mismatch
path. No transitive-import framework or binding of unused modules is needed.
The inspected renderer SHA-256 is
`e1ec3da2f3cd1565746e2b11c24308330b1f8c4d76dfe15f70bf5fa2dc2996be`.

### Checks that support the otherwise narrow implementation

- Public builders use original source/request objects; the selector receives
  no module, reference or tests. The qualification worker receives its initial
  module and an empty public case list. Executable public-check projection strips
  interval/grounding/rationale fields. Copies are chronological, Unicode text
  survives JSON decoding, and supplements are omitted from permanent history.
- The selector omits unsupported `uniqueItems` while rejecting duplicate IDs
  in its actual consumer. Enum, maximum length, exact argument keys, forced tool,
  nonthinking mode and 128-token cap remain fixed. Render and generation reuse
  exact request bytes and reconcile schema, prompt IDs, output IDs and usage.
  This implements the previously verified compatibility resolution; it does not
  claim runtime qualification of the pinned image.
- The preflight producer invokes the actual action/check path once. Runtime
  consumes a bound receipt rather than rerunning references. It encodes the
  native serialized source-argument JSON, adds one EOS token of allowance, checks
  headroom, and records code/fixture/tokenizer identities. Source inspection
  confirms that the local token-counter path names the existing Qwen3-30B-A3B
  tokenizer. No tokenizer was loaded or native headroom measured in this review.
- The earlier unconditional-reference-PASS, duplicate reference execution,
  boolean schema-version and annotation defects are corrected in the inspected
  paths. Applied wrong behavior remains a separate observation from technical
  delivery. Action rejection is no-go, transport/cap/deadline failure is
  incomplete, and output directories cannot silently resume an existing run.
- Each native call pair receives the shared deadline; late return, call receipt
  and final positive-manifest publication paths are checked. Launcher eligibility
  also requires successful driver exit, timely lifecycle and proven cleanup.
  Unproven cleanup retains the run flag. These are useful guards, subject to the
  startup-reserve correction above.
- Existing model identity checking compares current file size/mtime against a
  bound prior hash inventory; it does not compute fresh weight hashes. That is
  the stated narrow metadata qualification, not a stronger model-identity claim.

### Independent validation performed

Ran only the four new targeted CPU test files with bytecode/cache-provider
writing disabled: **43 passed in 1.28 seconds**. Their fixture stand-ins use an
injected byte counter, not a native tokenizer. Separately exercised the two
failure reproductions above using temporary files and mocked processes/clocks.
No actual accepted-fixture preflight, tokenizer/model load, GPU/container/API
launch, old-bank access, code edit or commit occurred. Only this review file was
edited in the repository.

Read selected reused consumer/lifecycle source sections. Their four original
hashes still match Round 1. Additional inspected dependency hashes are
`src/stencil/focus/slab.py` =
`3f3a9f04ee9bae3395c3fdf5d3011e2b8cca4b930332a72dd2edafce7de04b59`
and `src/stencil/focus/slab_sandbox.py` =
`3dad55e31b23fd859a9fcf805b3694acc99c8efdb48c35ed82ca78b16f9d7de8`.

## Round 4

Score: 96/100

Disposition: ACCEPT the first-stage implementation at `1f8a69dd` for actual CPU
preflight and subsequent frozen technical qualification under the accepted brief.
Open findings: none. Zero open high/critical findings.

2026-09-08. Same author-disjoint Astra xhigh reviewer. This round rechecks only
fixes for #3/#4/#5 and resulting regressions. Rounds 1–3 are byte-preserved; their
combined pre-append SHA-256 was
`b5a02250788d64d016b95a6cf2a6a28fe3e37d30244a3c6de0b8b809090690b6`.
This is implementation acceptance, not an actual preflight result, native-model
delivery claim, source-selection benefit, or acceptance of a future scored run.

### 3. [high] Historical acceptance text can authorize an unaccepted implementation (resolved 2026-09-08)

The actual launcher now isolates the latest canonical Round section, requires
exactly one machine block within that section, and checks the topic, heading
round, visible score and visible disposition against the block. It requires
ACCEPT, score 90–100 and zero high/critical findings. Exact specification,
fixture and eight-file implementation subject hashes must equal the freeze's
corresponding bindings. Acceptance entries point to the bound canonical review.
Earlier accepted text or an older block no longer authorizes a later round.

Independently ran actual `validate_freeze` regression cases covering a latest
rejected round without a block, a rejected block, low score, open findings and
wrong subject hashes, together with the accepted/bound-file-mismatch case. All
passed. The machine block below expresses this reviewer's actual decision and
exact reviewed bytes; the final review is additionally checked through the
actual `_validate_review` consumer before handoff.

### 4. [high] Docker launch delivery can consume the cleanup reservation (resolved 2026-09-08)

The new plan now supplies an effective startup allowance of
`min(600,600-60)=540` seconds to the unchanged lifecycle, covering the initial
Docker command as well as health waiting. The registered 600-second whole limit
and 60-second cleanup reserve are unchanged. Independently ran the regression
through the actual reused lifecycle with fake process/clock objects: Docker
delivery consuming its full allowance ends as INCOMPLETE_STARTUP, cleanup issues
logs/stop/remove, `cleaned` is true, and the owned flag is removed. No real
container or network operation was used.

### 5. [medium] A live sandbox serialization dependency is absent from the bindings (resolved 2026-09-08)

Both the CPU preflight code hash set and required launch bindings now include
`src/stencil/focus/renderer.py`. Its unchanged reviewed SHA-256 remains
`e1ec3da2f3cd1565746e2b11c24308330b1f8c4d76dfe15f70bf5fa2dc2996be`.
Independently ran the actual qualification consumer with a temporary stand-in
preflight whose renderer digest was changed; it rejects the stale receipt before
model calls. This closes the live-dependency omission without broader machinery.

### Validation and final bindings

Reviewed the complete four-file delta from `8651ab66` to `1f8a69dd`, and verified
current hashes. Only driver/launcher and their two tests changed; the other four
implementation/test files, accepted specification documents and original fixture
retain their prior hashes. Independently ran the nine relevant regression cases:
**9 passed in 0.10 seconds**. Did not repeat the unchanged broader test set or
actual accepted-fixture preflight. CPU stand-ins used injected counters; no
tokenizer/model load, GPU/container/API operation, old-bank access, code edit or
commit occurred. Earlier metadata-only model-identity qualifications remain.

The following is the single machine-readable acceptance record for this round.
Its subject dictionaries are exact, not examples or placeholders.

<!-- SOURCE_REPLAY_REVIEW_MACHINE_V1
{
  "schema_version": 1,
  "canonical_topic": "source-replay",
  "round": 4,
  "score": 96,
  "disposition": "ACCEPT",
  "open_findings": {
    "high": 0,
    "critical": 0
  },
  "subjects": {
    "specification": {
      "results/source-replay/SPEC.md": "01da819289d264926e8492a947b3bf8d6893b89c7559ff8142b9c4dabebda78c",
      "results/source-replay/DATA-CONTRACT.md": "6ae44a7794701686cf06a0c32551d9d92b96fb582cd042dee73be95a917a7e4a",
      "results/source-replay/QUALIFICATION-BRIEF.md": "ecc52bc7a046e084aa0a84cb68859ce45e4b757c38f129e8d61fc9ca88b4ea31"
    },
    "fixture": {
      "results/source-replay/qualification-authoring/author-00/authored.json": "ff167de40c52227c2a5eae1eda34194197d7d1c92337b1c37740aec9c6f8578c"
    },
    "implementation": {
      "src/stencil/source_replay.py": "19f3c7f1948fd74eb25767c007b4b9af567629c15656fed4c529542ffe485d55",
      "src/stencil/focus/native_source_selector.py": "f08f1c14d6b8e3001fa3694edfcf7b59f2ed2c7869136686e8f27a03c639fda2",
      "scripts/source_replay_qualification.py": "39eee1fffb32ffefb1ab3d6abdef14a80f6825dc928c32e83b8f8ed29fbc6782",
      "tools/run_source_replay_qualification.py": "ccb863333e27cee7a4253b881987c7d47c42c87dcbeaf7e1f2b0e94cd711d7a3",
      "tests/test_source_replay.py": "6872eecf6190ab9f75613b14606bcb8e742bb22a055d3a7ef43ef998afa6c48f",
      "tests/test_native_source_selector.py": "71bc04742e747f1d5f76a5d265125523dad9ba243a8bd0392992700b060c6e41",
      "tests/test_source_replay_qualification.py": "592a6fcdad6d9dfeff4bde36e3c99521f564030ed7c45bf21dffd7cad8266238",
      "tests/test_run_source_replay_qualification.py": "e1b636dd0dc51a8054a54309575fbc731eb0bb879cd6cc64effac1b73259b87b"
    }
  }
}
-->

## Round 5 — completed technical qualification result audit

Score: 96/100
Disposition: ACCEPT the completed one-shot technical qualification's delivery,
result integrity and bounded report. This is not authorization to repeat the run
or acceptance of a four-project utility result.
Open findings: none. Zero open high/critical findings. Findings #1–#5 remain
resolved; this audit opens no new numbered finding.

2026-09-08. Same author-disjoint Astra xhigh reviewer, independently auditing the
archived completed run at `d611a052`. Rounds 1–4 are byte-preserved; their combined
pre-append SHA-256 was
`f9a082a7d80222165b781ecd139910c628578a51bcbeb3a491136b0fb57ae165`.
This round uses read-only artifact inspection and standard-library consistency
checks. No model, tokenizer, API, GPU, container, reference implementation or
runtime check execution occurred; no prior evaluation bank was accessed.

### Delivery, evidence and result integrity

Independently reconciled all 18 run files against the root audit's artifact hashes
and their archived bytes. Verified all ten recorded raw body representations
(five per call, covering four HTTP exchanges) against base64, UTF-8 bytes, lengths,
SHA-256 and parsed JSON. Each call's render and generation request bodies match
exactly; rendered prompt IDs match completion-response prompt IDs. The two
responses' numeric usage fields agree with the recorded prompt/output ID counts.
Raw optional `prompt_tokens_details: null` is preserved. Comparing its full usage
object with the consumer's normalized three-field object was an audit shape
error; comparing the numeric fields correctly reconciles them without changing
any run artifact or rerunning inference.

The selector returned only `m01`, the sole eligible original message. Its native
request retains the registered schema, cap and sampling parameters. Worker
messages contain the original source and request, exact copied historical
evidence, and the registered work envelope. The permanent history retains the
actual worker tool call and feedback while excluding the temporary evidence
supplement. The model-facing work envelope has no private check or reference
content. Before-workspace bytes equal the authored initial module; after-workspace
bytes equal the actual replacement argument and recorded module hash. The
resulting quarters-then-dimes expression agrees arithmetically with the three
source-grounded checks, `35 → 2`, `7 → 0`, `60 → 3`; all three recorded consumer
results pass without error. This is an audit of the recorded execution, not an
independent rerun or a claim that worker and reference source strings are equal.

Verified the terminal's embedded manifest and lifecycle against their separate
files, driver stdout against its manifest/log, and launch-preflight bindings
against the frozen document. All 22 non-model bound files matched their frozen
hashes before this review append. The tokenizer identity agrees between frozen
and preflight receipts; it was not loaded or independently rehashed in this
round. Original model identity retains the accepted existing metadata/size/mtime
scope, not a fresh full-weight hash claim. The exact launch-time Round 4 review
is reproducible from commits `260bbca0` and `6ec12be8` with its frozen hash above.
This result-review append does not alter that historical freeze.

### Timing, cleanup and claim limits

Recomputed whole lifecycle time as **439.667978465 seconds**, and elapsed time
through positive terminal publication as **439.674058504 seconds**, leaving
160.325941496 seconds within the 600-second reservation. Driver and launcher
receipts report exit zero. Cleanup logs, stop and remove commands each return
zero for the same owned container; lifecycle cleanup is complete and the running
flag is absent. The report's empty post-run Docker/GPU queries are root-observed
supplementary evidence; this reviewer did not repeat runtime queries. Both call
pairs completed within their recorded request/pair and overall deadlines.

The driver manifest spans **3.725712025 seconds**; the driver-exit receipt spans
**3.812367201 seconds** of process wall lifetime. The final report's append-only
precision addendum correctly distinguishes these intervals without changing the
whole-run result. Native usage reconciles to **826 prompt + 56 completion tokens**:
379/10 for the selector and 447/46 for the worker. Both finish with stop below
their respective 128/1024 generation caps. The slower measured render is
**0.011698220972903073 seconds**, correctly retained as prospective `r`.

Accept the report's limited technical conclusion: the actual native selector,
verbatim historical reminder, frozen worker and consumer delivered the mechanical
fixture successfully. One eligible source and three simple checks provide no
evidence of difficult source selection, general negative-input correctness,
coding utility or superiority to manual prose. The later four-project screen
remains preliminary and its affordability gate remains unevaluated: actual
project `C` and CPU `q` are still required, and the registered historical
2041.199447651-second generation estimate is not replaced by this short fixture's
throughput. No significance, full-screen qualification or larger proof is
claimed. No new launch-acceptance machine block is issued in this result round.

### Exact reviewed evidence hashes

Paths below are relative to `results/source-replay/`. The root-audit file's exact
digest additionally binds its complete 18-file run inventory; every entry was
independently checked, including the command receipts and server/driver logs.
Specification, original fixture and eight implementation subjects retain their
exact Round 4 hashes.

| File | SHA-256 |
| --- | --- |
| `QUALIFICATION-RESULTS.md` (including precision addendum) | `933eff7a582a5f9ac1e403fd9703e7b7f565e328261c870c3a451806264e8247` |
| `qualification-root-audit.json` | `d90b0be6cbd39d3a07a7c25a674b4605a3848483896561b3d7a915d73dbafb57` |
| `qualification-freeze.json` | `903f8382d12ebaafd15515e2828bdad510f08fc28e282b3ae8771bba8a70c54b` |
| `qualification-run-01/launch-preflight.json` | `ba7b75f098070d3f3334db0d43d6eb5f3577fc906d7e97b60163011fa1841cfb` |
| `qualification-run-01/launch-plan.json` | `9be5a6979f5dae46d8215b9c1f35e956aaf6946898565c243a40e9aa645db942` |
| `qualification-run-01/qualification-terminal.json` | `4b09613bd953a0e47f0960f0b968f746677973fa13568b76b6a825cfccba3938` |
| `qualification-run-01/lifecycle.json` | `4c077e9cb419d136e22eb0e0d891185fb1ddc1c3cec487b0b15a4c9e6f8b0f92` |
| `qualification-run-01/cleanup-receipts.json` | `d0999c55c7c86dc428e702bba8296650951dc73922ad40e6caf68881dec82ed7` |
| `qualification-run-01/driver-exit.json` | `350f5f0c013cb66dac0cb2c2bfd410316a4e53b8a0a2d9ff57b462f7cb572f66` |
| `qualification-run-01/qualification/manifest.json` | `1571cb3e902d0709c4c4ff8cc2b7bc25307b0b6ecaf8968e05b3c80a773617c1` |
| `qualification-run-01/qualification/preflight.json` | `cc3538442612999daeed95ce9bca6d1b1d52ea1e0ed27fbbe6ac7ceaaa5efa5c` |
| `qualification-run-01/qualification/calls/call-0000.json` | `08610568af1b17b91e4693012c4a301197b92d64b11087d200b39b6077a32c6f` |
| `qualification-run-01/qualification/calls/call-0001.json` | `8617f87caa07d3900f41382200bd0b6fd0dc0aa47c902d6e7b6fe65b63a292ba` |
| `qualification-run-01/qualification/workspaces/before.py` | `54bdc654b57070983878684ddaaa5f2357e32e379fd9cfbf3339a389a61c7ba5` |
| `qualification-run-01/qualification/workspaces/after.py` | `f10275e9cbe51fa746252dcc19f10a07900699b3186147f65ac2c864ed522276` |

## Round 6 — original four-project source, test and schema audit

Score: 68/100
Disposition: REJECT the original four-project bank for preparation/launch
eligibility. Collect the verified defects below for the single permitted
pre-exposure Kimi correction batch; do not repair originals or substitute projects.
Open findings: #6 high, #7 high, #8 high, #9 low, #10 low. Three open high and zero
open critical findings. Findings #1–#5 remain resolved.

2026-09-08. Same author-disjoint Astra xhigh reviewer. Rounds 1–5 are
byte-preserved; their combined pre-append SHA-256 was
`5fc706b05aaafa433676060a1fe0e40a57a5692eaf25d8081fff97b814b65a4e`.
All four original authoring requests are terminal. This review reads their
original public sources, checks, references and mutants, not evolving screen
implementation or any scientific worker response. No reference/module execution,
consumer preflight, tokenizer/model load, API/GPU operation or old-bank access
occurred. Static JSON/AST inspection does not qualify actual consumer execution
or native output-token headroom.

### 6. [high] Two original responses do not form complete JSON documents (open 2026-09-08)

`author-00/response.json` and `author-02/response.json` preserve complete outer
service responses, but their `response` text fails JSON parsing at end of input:
respectively character 20546 (line 1, column 20547) and character 27674 (line 1,
column 27675), with `Expecting ',' delimiter`. Neither has an `authored.json`.
Service `done: true` / `done_reason: stop` does not make these valid project
objects. The recorded authoring errors are accurate.

The existing `public` and `private` child values are complete and separately
readable directly from each original string. This reviewer decoded those child
values only in memory to audit their contents; no repaired root object was
constructed, saved or passed to a consumer. Their content review below does not
waive root JSON validity. The author must return complete valid documents for
the same projects in the permitted correction batch, preserving already sound
content except verified corrections. Root must not append missing syntax itself.

### 7. [high] replay-02 is an unfinished project with no executable private validation (open 2026-09-08)

`author-01/authored.json` parses but has `private.rounds: []`: all three
references, hidden checks and required new/retained/retirement coverage are
absent. Round 2's request is the placeholder `m06b` / `x`, instead of `m10` and a
substantive request. Round 3 has no source messages and its `m15` request is also
`x`. The final mutant is `x`, an expression rather than a replacement function;
its designated `c-prv-08` check does not exist. Thus neither complete chronology
nor the final retirement counterexample can be consumed or reviewed.

The original grant-allocation module and available round 1/2 sources identify
the same project to complete. Its three existing round 1 public checks are
arithmetically/source-correct, but cannot supply the missing private checks or
later rounds. The author must complete this project under the unchanged contract,
including inclusive check versions, sequential references and a real obsolete
mutant. Do not replace it with a different project or infer missing requirements
from its description alone.

### 8. [high] replay-04 wraps all three reference functions in the wrong field type (open 2026-09-08)

Every `private.rounds[*].reference_patch` in `author-03/authored.json` is an object
with `path`, `symbol`, `source`; the contract's reference field is the replacement
function source text. The target already supplies the path and symbol. This is
not the registered source-string representation, even though each object's
`source` value describes the intended function. Ask the author to supply those
same source strings directly, without wrapper objects; do not introduce an
extra accepted schema or silently normalize the authored document.

There is no escape defect: the three parsed sources contain 4/8/6 actual newline
characters, and the mutant contains four; all have zero literal backslash-n
sequences. Static AST parsing succeeds on each. The initial/ref1/ref3 sort-key
lambdas do not trigger the unchanged action validator's prohibition on nested
function/class definitions. Actual consumer execution remains pending.

### 9. [low] replay-03 misdescribes its starting digit predicate (open 2026-09-08)

The original `m01` says that today's `validate_code` accepts exactly four ASCII
digits, but the supplied initial function uses `tail.isdigit()`, whose accepted
digits extend beyond ASCII. This is a discrepancy between the description and
starting code, not a verified wrong expected output: round 1 explicitly requires
ASCII `0-9`, targets that function, and its reference uses explicit ASCII
membership. Existing checks are compatible with that requirement. A narrow
author correction can align the claimed starting behavior and initial code;
no broad new negative-input guarantee or additional check gate is requested.

### 10. [low] replay-04's p08 rationale overstates which threshold was retired (open 2026-09-08)

The round 2 private `p08` rationale claims that preserving any trace of the
`1000/5000` thresholds mislabels 1250. The authoritative `m07` scheme and correct
reference preserve the 5000 standard/premium boundary. This case establishes
retirement of the old 1000 budget boundary only. Expected `1250 → budget` is
correct; narrow the rationale to that effect without changing its input/output
or treating the still-applicable 5000 boundary as cancelled. This metadata never
belongs in model prompts and is not evidence of a wrong grading label.

### Complete available source and check audit

Read all 106 extant checks: replay-01 has 11 public/15 private, replay-02 3/0,
replay-03 25/28, replay-04 11/13. Independently reasoned their accepted values from
the original visible sources, including interactions, scope and boundaries.
Found no wrong expected value, source-permitted alternative incorrectly excluded,
conflicting active output for the same symbol/input, or additional semantic
coverage deficit in the three complete legible project contents. No gold selected
IDs or perfect-selection/manual-prose-superiority criterion was imposed.

- **replay-01:** total includes negative amounts, period sums use the fixed hour
  boundaries, and classification changes propagate through the helper call.
  The negative `refund` label is explicitly retired for `classify` in round 2;
  this does not cancel signed summation or change `bucket`. Round 3 separately
  replaces the flag threshold with inclusive 400 and adds absolute exposure for
  large-labelled events only. Old whole-output checks expire before changed
  labels/new keys would invalidate them. Private round 1 p02/p04 cover surviving
  behavior; round 2 p02/p08/p09 do so while p05/p06 exercise retirement. Round 3
  retains earlier classify/bucket cases and p14's period boundaries, with
  retirement witnessed by p05/p06/p11/p15 and new functionality by p12/p13.
  The final mutant incorrectly uses `amount > 500`; p11's amount 420 separates
  it from the required flag result. Active public/private counts are 3/4, 6/7,
  6/10 over the three rounds.
- **replay-03:** ASCII/case/length restrictions and boolean-rank rejection
  remain applicable. Sealing and invalid-data decisions precede the urgent
  silver/gold lane; round 3 inserts numeric weight strictly above 500 before
  that lane, ignoring the specified non-numeric/boolean weight types. The
  platinum-to-review step alone is retired; `tier_of` still returns platinum.
  The old private review outcome expires after round 1 and its new version
  requires ok from round 2. Multiple retained cases survive every round;
  private retirement cases prv203/prv204/prv210 remain active into round 3,
  which adds prv303/prv306. New private functionality is present each round,
  including unseen inputs and interaction/boundary cases. The mutant restores
  the platinum review branch and would disagree with prv306's required ok.
  Active public/private counts are 6/8, 15/17, 25/27.
- **replay-04:** ascending price/name order from round 1 survives the tier edit,
  then orders the in-stock and out-of-stock groups in round 3. Tier retirement
  p07/p08 remains active; the later cancellation of rank filtering is explicitly
  limited to `rank_items`, leaving `cheapest_in_stock` filtering intact. Old
  c02/p02/p09 expectations expire through round 2 inclusive. Round 1 p03/p04
  cover unchanged behavior; later rounds retain those and earlier valid cases.
  New private functionality appears in each round. Round 3's active retirement
  coverage includes p07/p08 and p12, so it does not need a second new tagged
  retirement case merely to meet a count. The final mutant excludes stock-zero
  items and would fail p12 by omitting `gone`. Active public/private counts are
  5/4, 7/9, 9/11.

Checked exact extant child-object/check keys, duplicate keys/IDs, finite JSON
values, visible source references and inclusive intervals. Complete projects
have m01–m15 in the required 4+1 order per round. All extant source/request texts
are within 640 UTF-8 bytes; per-project maxima are 410, 369, 532 and 296 bytes.
Initial modules and complete references/mutants are far below the 65536-byte
limit and statically parse with the intended single-argument target names, no
imports/decorators/annotations/nested definitions or top-level computation.
Only replay-02's placeholder mutant fails that shape. AST inspection establishes
no actual sandbox result or native token count. The complete references and
mutants appear consistent with their source/check semantics by inspection;
the registered actual consumer preflight remains necessary after correction and
implementation acceptance.

### Provenance, costs and exact reviewed hashes

Each request contains the frozen common authoring prompt verbatim, followed only
by its fixed project ID and distinct broad domain. All use `kimi-k3:cloud`,
`stream: false`, `think: true`, with no earlier project/model answer included.
The receipt request/response/raw-text hashes match original bytes. The two
existing authored JSON files equal the parsed service text semantically; the
other two are correctly absent. The four service receipts reconcile to
**7529 prompt tokens and 89208 service-generated tokens**. Concurrent job elapsed
time is **438.034577104 seconds**; it is not the sum of per-request times.
Authoring is terminal with two parsing errors, no automatic retry and no
scientific worker call. These costs are separate from native qualification or
future screen costs. No full-bank affordability or utility claim follows.

Paths below are relative to `results/source-replay/`; hashes are SHA-256.

| File | SHA-256 |
| --- | --- |
| `SPEC.md` | `01da819289d264926e8492a947b3bf8d6893b89c7559ff8142b9c4dabebda78c` |
| `DATA-CONTRACT.md` | `6ae44a7794701686cf06a0c32551d9d92b96fb582cd042dee73be95a917a7e4a` |
| `PROJECT-AUTHORING-PROMPT.md` | `be1e373d63302ea68388e8d6b0afca444878f79017a937249e947cce6b7aaed1` |
| `project-authoring/job.json` | `a2396678063b7fa93fde35ccb3a12874e237322059c452d785753b4aff81677d` |
| `project-authoring/author-00/request.json` | `4e81febac26f6618a076542f24a56c72f42f29226a11fa7a16e3c2bd3e07d714` |
| `project-authoring/author-00/response.json` | `79616e59dfd29dd7bac0582812cc2782789db84dda300440f903f20c31b35b6e` |
| `project-authoring/author-00/receipt.json` | `644d82c7a6807ce784652e4064fe28d4f9e1a41fba2c033af4d6415ca9941e15` |
| `project-authoring/author-01/request.json` | `1240c2c3d10fe4bf8ee35e392e3869a1906203267bcea793e1e0fb0cf36f64f8` |
| `project-authoring/author-01/response.json` | `76c249fcb92261f1f804674d7f45c3d3d1be81612ab7ab177d8fdc0204aa2f3c` |
| `project-authoring/author-01/receipt.json` | `6fa6f7008c9e7a1e90c58f5171820ce0e163146a5a1f09f07c231e3194298daf` |
| `project-authoring/author-01/authored.json` | `dd208ea8eb058a912ed41b998a9ce1793d72902785b71d7f63db3ba9f3e0223f` |
| `project-authoring/author-02/request.json` | `5215126f989be4b67cfcbc196bce529dd48046a2ae3e899b93996308845faf3d` |
| `project-authoring/author-02/response.json` | `6f51d55e38bbf54d1c856a76c57ed21a7c82d0e4750d476380e00d49d5076e0a` |
| `project-authoring/author-02/receipt.json` | `fa70ffe6ea1691f78e38e2866b1cdbc82f0c3a2df79abecc6b3f74bb72b5dde6` |
| `project-authoring/author-03/request.json` | `916bf669c653e5bcd184324ba2e9ef0338d1e78a473b2a2b500ed2aa6cdb03fc` |
| `project-authoring/author-03/response.json` | `080b37b9d291e0a1cb58a437575584065fe755a81ed98bf55f94b1bf16b35cf1` |
| `project-authoring/author-03/receipt.json` | `b6b152c6d7dd8853c631d4cfa81e56bb723e1fd211cb30cedfb7d5801465169e` |
| `project-authoring/author-03/authored.json` | `a535a8b65519ed0764b8327a345fc6565f7f3aa466561b0ddd4a46f168b05d18` |

The unmodified response-text SHA-256 values are, in authored order:
`4d1fadc21e2b90107d701207816f893b029689abc9f9b2d9dd4f5fec50fe781c`,
`18c4a072373c09e8c9909d80a1bf1494f4f068aaaf618607dea66f218a357248`,
`4eed8c87b38d052629d217e9dbed13b284db3cc4a59d1c1100e882169f8cb871`,
`cd6cd412671763fcf1a1eb58d360fadfdc2eb1bedf3ed9d91c01688f419c09e2`.
No original project/response was changed. Corrected outputs require independent
review; if the sole correction batch cannot yield an accepted complete bank,
stop this preparation under the existing specification.

## Round 7 — sole correction batch re-review and preparation stop

Score: 84/100
Disposition: REJECT the corrected bank. Stop this preparation under the accepted
single-correction-batch rule; no scientific screen launch is eligible.
Open findings: #11 high. One open high and zero open critical findings.
Findings #6–#10 are resolved below; findings #1–#5 remain resolved.

2026-09-08. Same author-disjoint Astra xhigh reviewer. Rounds 1–6 are
byte-preserved; their combined pre-append SHA-256 was
`066cef6b1f749c137914cbf77de4be3aa798824bf3876138d8e86fb5ce9d2f18`.
All four requests in the sole correction batch are terminal. This round verifies
their permitted changes, fully audits the newly completed replay-02 content and
checks correction regressions. Unchanged checks retain their Round 6 review;
they were not rerun or needlessly re-audited. No reference/module execution,
consumer preflight, tokenizer/model load, API/GPU operation or old-bank access
occurred. Only this canonical review was edited; no commit was made.

### 6. [high] Two original responses do not form complete JSON documents (resolved 2026-09-08)

Corrected author-00 and author-02 now return complete valid root JSON. Both
authored files match their raw response text semantically and their recorded
hashes. Independently compared original readable field values with corrected
values using JSON representations that distinguish booleans from numbers.
Author-00 changes no original field value. Author-02 changes only the permitted
initial digit predicate described under #9. The invalid originals remain intact;
their historical error status is not relabelled as success.

### 7. [high] replay-02 is an unfinished project with no executable private validation (resolved 2026-09-08)

Corrected author-01 preserves its original identity/description/lineage, initial
module, entire first public round and second round's m06–m09 source messages and
target. It supplies genuine m10–m15 chronology, three complete private rounds,
source-string references and an actual final mutant naming c-prv-12. The
structural omissions and placeholders are resolved. Its newly authored final
request introduces a separate source-design defect, #11; closing this original
incompleteness finding does not accept the corrected project.

### 8. [high] replay-04 wraps all three reference functions in the wrong field type (resolved 2026-09-08)

Corrected author-03 supplies each exact original reference source string directly
as `reference_patch`, removing only its wrapper. No function source, newline,
target or check outcome changed. All other field values are unchanged apart
from the authorized p08 rationale correction under #10. No alternate schema or
root normalization was introduced.

### 9. [low] replay-03 misdescribes its starting digit predicate (resolved 2026-09-08)

The initial `validate_code` now checks each of the four suffix characters for
membership in `0123456789` before returning true. Non-string rejection, the
case-sensitive INV-only prefix and exactly-four length remain unchanged. The
other initial helper ASTs and module docstring match their originals. Every
public instruction, reference, check/input/output/interval/rationale and mutant
is unchanged. This aligns the starting implementation with m01 without adding
a new testing requirement.

### 10. [low] replay-04's p08 rationale overstates which threshold was retired (resolved 2026-09-08)

The new rationale correctly says 1250 becomes budget because the old 1000 budget
boundary was retired in favor of 1500. It explicitly preserves the 5000
standard/premium boundary and says this case does not exercise that boundary.
No input, expected value, cited source or interval changed.

### 11. [high] The completed project's final request restates every surviving target rule (open 2026-09-08)

Corrected replay-02's newly authored m15 directs the worker to keep
`need*3 + tenure`, apply truthy hardship `+15`, then subtract 5 for request above
700, and keep the long-service bump removed at every tenure. These are all the
current `priority_points` rules, including the surviving need/tenure formula and
earlier bonus retirement. The complete target logic is supplied in the current
request itself; m13 also recaps the surviving scoring and band rules.

The frozen SPEC's data section explicitly requires: “Current requests identify
the change and do not restate all surviving rules.” This completion violates
that registered source-design constraint. The correction prompt additionally
forbids inventing a manual recap. The issue is the substantive target-rule recap,
not the function name, action shape or a harmless reference to keeping earlier
behavior. It materially changes one of only four project units in a prospective
original-history reminder screen. Correct arithmetic and schema validity do not
establish conformity to that workload requirement.

The root independently confirmed the exact m15/target match and the existing
SPEC wording. This is a regression in newly completed content, not a new
perfect-selector, hidden-negative-case or manual-prose-superiority gate. No
worker outcome was used to identify it. Fixing it would require another authored
instruction change, but the only permitted correction batch has already been
used. Therefore do not hand-rewrite m15, obtain another correction, drop or
replace this project, relax the source constraint, or proceed to scientific
consumer preflight/launch as an accepted bank. Apply the registered preparation
stop. This rejection is a data-preparation result; it does not demonstrate that
the frozen reminder mechanism improves or harms coding utility.

### Audit of the newly completed replay-02 checks and references

The completed project has seven public and twelve private checks, sixteen more
than its three preserved public checks. All nineteen accepted values agree with
their visible sources by independent arithmetic and scope review. Round 1
returns zero for ineligible awards, otherwise caps the positive request and
applies the 40 floor. Round 2 changes only `priority_points`: need weight 3,
face-value tenure, truthy hardship +10, with the +25 long-service bump removed.
Round 3 raises hardship to +15 and subtracts 5 only above request 700. The
eligibility, floor, cap and band-threshold rules remain applicable. Quoted
restoration material does not reactivate the retired bonus.

Inclusive intervals correctly retire c-prv-03/c-prv-04 after round 1 and the
round 2 hardship expectations c-pub-04/c-prv-05 after round 2. The same input
formerly checked by c-prv-05 receives a distinct c-prv-09 version with the new
value 140. No simultaneously active conflicting output was found. Round 1
c-prv-03/c-prv-04 supply retained coverage; round 2 retains c-prv-01/c-prv-02,
while c-prv-07/c-prv-08 exercise bonus retirement. Round 3 keeps both retirement
cases plus c-prv-12, and retains earlier award/cap/eligibility behavior. Each
round introduces multiple private cases with new functionality; the new
deduction includes above-threshold and exact-700 cases. Thus absence of new
`retained` tags in later rounds is not a coverage failure.

Active public/private counts are **3/4, 5/6, 6/9**. The reference patches are
316, 146 and 204 UTF-8 bytes; their ASTs define the intended synchronous
single-argument targets without prohibited statements/decorators/annotations
or nested definitions. The 262-byte final mutant restores the +25 branch.
Its designated active private retirement case c-prv-12 requires
`44*3 + 13 = 145`; the mutant's restored branch would yield 170. This is static
reasoning, not an executed consumer result or measured native-token headroom.
No wrong expected value or disallowed alternative was found in this completion.

Checked its exact key sets, 15-message chronology, source visibility, finite JSON
values, check-ID uniqueness, interval endpoints, target names and source bounds.
Its longest source/request is 369 UTF-8 bytes. The corrected four-project bank
contains **122 checks: 26 + 19 + 53 + 24**; unchanged project contents retain the
previous static source/coverage review. These observations do not override #11.

### Correction provenance, cost and exact reviewed hashes

Verified every frozen correction request contains the unchanged common
instructions/DATA contract, its project-specific authorized corrections and
the exact unmodified text of that project's own original author response.
The requests retain `kimi-k3:cloud`, `stream: false`, `think: true` and supply
no coding-worker answer. All raw response, raw text, parsed document and receipt
hashes reconcile. Comparison of typed JSON values establishes only the permitted
deltas summarized above; the new m15 defect lies within the author-completed
missing content, not an undisclosed replacement of an existing valid source.

The four correction receipts total **24693 prompt tokens + 51989
service-generated tokens**. The concurrent batch elapsed **234.452679139
seconds**, distinct from the earlier original-authoring batch and native
qualification. There was no automatic retry or scientific worker call. All
returned outputs parse, but delivery completion is not source acceptance.
No new launch-acceptance machine block is issued.

Paths below are relative to `results/source-replay/`; hashes are SHA-256.
SPEC/DATA and original artifacts retain their exact prior-round identities.

| File | SHA-256 |
| --- | --- |
| `PROJECT-CORRECTION-PROMPT.md` | `4b2dc1344c16c862ca615cc24988975a0b50f116c1b65dca912abdb5729d87b2` |
| `project-authoring/correction-01/job.json` | `4e37a621dcc48e3bd36dfec9eb8aba0e80f20cc0a2f737f4daeb743fe274caa3` |
| `project-authoring/correction-01/author-00/request.json` | `db829be200f908f479b135b9177253d7fab85e69e0683cbcb7c1c6e2b40567a8` |
| `project-authoring/correction-01/author-00/response.json` | `72529dbfa3710f91a42ceb7c763cc18a5f0f85d8db0329081b3a3eaf294aed4b` |
| `project-authoring/correction-01/author-00/receipt.json` | `cc74f4e499bda62fc5282c74836673b7bafe6beeb2d855f3ab337ff804d205ef` |
| `project-authoring/correction-01/author-00/authored.json` | `3747941287d143e360cdd4192155442ba0308012962cf84072f9a858b9db7c35` |
| `project-authoring/correction-01/author-01/request.json` | `3905eba7ee9a8855d2b5d32c1ce2e01e8221ee018d0a7053ab797cbdcc0ad16a` |
| `project-authoring/correction-01/author-01/response.json` | `b08737bc92ca7fb054d3ec94ab5bb748bbf44178be0e764b58027cd8bc9e6b2e` |
| `project-authoring/correction-01/author-01/receipt.json` | `0411bbc7b056b2e2e3367345b3dfe1f1fa76d7be4202ef56f81cca9316a80210` |
| `project-authoring/correction-01/author-01/authored.json` | `2ba6b215e23361f993c79a313185f24df32f27b973a9286bf8bd1d373a61b0bd` |
| `project-authoring/correction-01/author-02/request.json` | `b0623f319a2ab2d4a717add132cd712ce6a3e484e31ac882da6b1c05d3829daa` |
| `project-authoring/correction-01/author-02/response.json` | `bbaa48bc1a6023eaee7f8cbff6a256e5d5a09e3a14e239ffd9820455a898f03b` |
| `project-authoring/correction-01/author-02/receipt.json` | `2a2bbee08665a927c685bcc9a9db26bc2d326bcae184cbe51832f738a4826779` |
| `project-authoring/correction-01/author-02/authored.json` | `cc218e25e99e63d24cf277b9995bfe702f923c4737f7cf4babb6e33db7fdf5b8` |
| `project-authoring/correction-01/author-03/request.json` | `cabaabe52a1d9ce1ce57fd70b6a34c80cfa7469e74cafbf5f34cd4828db2a412` |
| `project-authoring/correction-01/author-03/response.json` | `e7806f7c6f80cc4190d8f64dd714d7d33c2f5bd92a3e02f5313c89abf629a77a` |
| `project-authoring/correction-01/author-03/receipt.json` | `0a9ce8eb82b9dc9069b781766299e027112def11941e32175ad3c9a61a125801` |
| `project-authoring/correction-01/author-03/authored.json` | `2c3e80b435683050b93f21f97054eb822ae7451471d225fb0c561740592c8748` |
