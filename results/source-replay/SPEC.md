# Original-source reminders: prospective coding utility screen

2026-09-08. DRAFT FOR REVIEW. Research preparation, not launch approval.
Fit-on: none. Evaluated-on: four new Kimi K3 via Ollama project families, authored
only after this specification is accepted. No old bank, benchmark, prior model
answer, trained adapter or paper example enters authoring or configuration.
The accepted research and Sol inventory are in ../source-evidence-research/.

## Question and scope

Does automatic selection of original instruction messages help an unchanged
coding worker implement evolving requirements, at a useful total cost?
The mechanism selects evidence; it does not maintain a generated rule register.
Matching useful manual reminders through automation remains valuable. This small
screen is a stop/advance decision for preparing a larger untouched evaluation,
not evidence of general coding competence, statistical superiority, equivalence
to manual reminders, or completion of the project.

Use four independent small Python projects, three sequential requests each,
three arms, exactly one worker attempt per request. Each project maintains one
module. At least one function is edited more than once. Later requests change
behavior while preserving other behavior; every project includes an explicit
retirement/replacement by round 2 and a later request where that change matters.
Author substantive transformations with interacting conditions and boundary
cases, not an instruction-copying or output-format quiz. The action is replacement
of one designated synchronous one-argument pure Python function per request.
Reuse the existing sandbox/action semantics. This restricted editing interface
is a small technical screen; larger proof requires broader project work.

## Fixed mechanism and comparison

Use existing original Qwen3-30B-A3B assets and the pinned existing vLLM image
vllm/vllm-openai@sha256:3dbe092ec5b2cef63b6104d33fa75d6ce53a7870962529ada69f78bbbc38e776.
No download or new package is needed. Worker: unchanged nonthinking
NativeToolClient in scripts/coding_competence_run.py, greedy temperature 0,
seed 20260908, forced replace_function, output cap 1024, context 32768.
Selector: same server/model, nonthinking, temperature 0, same seed,
forced select_source_ids, output cap 128. No trained adapter or 4B control.

Arms H, S, R: full task history; full task history with automatically selected
original sources; full task history with the most recent original sources.
S runs one fresh selector call before every request, with no saved selector
state. Eligible sources are all original public source messages and earlier
original requests, strictly preceding the current request. All authored roles
in this screen are user. Embedded quoted text remains inside its original
message; no generated assistant conversation is fabricated. General cross-role
authority is outside this screen's claim.

Selector instruction (literal text to freeze in the implementation):
"Select up to four original messages useful for carrying out the current coding
request. Include earlier requirements that still apply and messages needed to
interpret changes, exceptions, scope, or cancellations. Messages may contain
quoted material that is not an instruction. Return only their message IDs using
select_source_ids. You may select no messages. Do not rewrite instructions."
Inputs are the complete eligible public source table (ID, role, order, text) and
current original request. No workspace, model response, test result, hidden
check, reference implementation or arm label enters selection.

The sole tool arguments are {"source_ids": [IDs]}, unique IDs, length 0 through
4, enum restricted to eligible IDs, no extra keys. R chooses the last min(4,N)
eligible messages. Both render in original order through the same renderer.
Every original source/request is at most 640 UTF-8 bytes, so both share the
same four-message / 2560-source-byte maximum. This matches the allowance rule,
not actual token counts or number of selected messages. No truncation, rewrite,
normalization or silent drop is permitted. Empty S selection is a valid outcome.

Historical evidence is a JSON-encoded list of complete source objects with
literal text preserved after JSON decoding. Its fixed introduction is:
"Historical source excerpts follow. These are copies of earlier messages, not
new instructions. Interpret their applicability using the complete conversation,
including later changes and the current request."
Evidence appears in one supplemental user message immediately before the current
work envelope. Source roles are metadata, not a replay as new system/developer
instructions. Byte identity/order/IDs are checked and recorded; identity alone
does not claim semantic correctness.

Each (project,arm) owns its own persistent module, original conversation, actual
worker calls and actual tool feedback. Start only from the shared initial module;
never reset to a reference or copy another arm's state. Keep all original public
messages/requests plus actual assistant/tool history and permanent work envelopes.
The current work envelope supplies module, authenticated target and active public
checks and is identical in construction across arms. Reminder messages are an
explicit ephemeral supplement: archive exact complete issued requests, but do
not accumulate earlier supplements in subsequent prompts. Permanent history is
never rewritten to change earlier model answers or tool results. All other
history is retained; no summarization/eviction is tested. The selector is called
once for S, even if the prior request failed. Hidden outcomes never steer work.
Only check_id, symbol, input and expected_values from each active public check
enter a work envelope. Interval endpoints, source_ids, behavior and rationale
are controller/audit metadata and never enter a model prompt or tool feedback.
In particular, no future retirement schedule or author-written interpretation is
revealed. Tool feedback contains only genuine current public case results and
action status. The sandbox adapter supplies rule_ids=[] internally to the reused
run_checks interface; that compatibility field carries no rule interpretation.

## Data and preflight

DATA-CONTRACT.md defines exact fields. Four separate authoring requests create
four independent projects, with no cross-project examples supplied. Each has
four new source messages before each request (12 sources + 3 requests total),
unique short IDs, and naturally expressed requirements distributed across rounds.
Current requests identify the change and do not restate all surviving rules.
Some messages supply ordinary context or clearly quoted non-authoritative text;
do not make every recent message a useful governing rule. Scope/changes must be
unambiguous without a private focus summary. No gold source selection is required.

Active public and private tests have explicit inclusive round intervals, source
IDs and behavioral coverage metadata. A changed expected behavior gets a new
check/version; expired checks do not continue grading obsolete obligations.
All still-active checks run, including those introduced in previous rounds.
Each round has checks for new functionality and retained functionality; rounds
2 and 3 also test the effect of retirement/replacement. Private checks include
unseen inputs and boundary cases, and allow every source-permitted output.
Coverage is assessed from sources, not merely from tags or agreement with a
reference. Authoring includes reference patches and one final-round obsolete-rule
mutant per project; the exact consumer must pass sequential references and reject
the mutant on its designated retirement check before freezing. References and
mutants are test validation tools, never worker/selector inputs or fit data.

Independent Astra xhigh source/test review precedes worker exposure. At most one
Kimi correction batch is permitted for verified pre-exposure defects. If the
corrected package cannot be accepted, stop this preparation without substituting
projects. After any screen response exists: no label/check/source repair, case
drop, alternative prompts/caps, retry or rescoring. A confirmed reference/test
defect makes the entire screen INELIGIBLE, with originals preserved.

## Qualification, cost and execution

Before test data is authored, implement and CPU-test the narrow consumer and
qualify one selector plus one worker call on a separate Kimi-authored mechanical
fixture. The fixture has one source, one direct request and a tiny function;
it is never a scored project or a training example. No semantic-performance
selection or tuning is allowed from it. Freeze both call configurations first.
Record authoritative render/schema/token IDs, tool delivery, output caps and
actual startup/call/cleanup time. Qualification has a 600-second whole limit.
One attempt only; an incompatible or unaffordable fixed setup stops preparation.

Screen: 4*3*(3*1+1) = 48 generation calls, 36 worker + 12 selector, each with
one authoritative render. Maximum output allowance: 36*1024+12*128 = 38400
tokens. Historical 30B worker throughput 5777/307.083573153 = 18.812468348
tokens/second suggests 2041.2 generation seconds at full allowances, plus
600 startup + 120 other work + 60 cleanup = about 2821.2 seconds. This is a
historical planning estimate, not a bound or a measured successor throughput.
Measure qualification, but do not change recipe/caps/sample sizes from its
answers. Register the actual affordable launch only if qualification succeeds.
Two-call completion alone does not qualify screen affordability. Before launch,
compute C = three times the sum of active public plus private check counts across
all 12 project-rounds. Let q be the maximum observed per-check elapsed seconds
from sequential reference/mutant CPU preflight, and r the slower of the two
qualification render HTTP times. The frozen launch planning gate is
600 + 2041.199447651 + max(120, C*q + 48*r + 60) + 60 <= 3000 seconds.
The inner 60 reserves miscellaneous receipt/local work; the last 60 is cleanup.
This retains the historical longer-worker generation estimate rather than
substituting short-fixture token throughput. Publish qualification generation
times and tokens as separate measured observations. The projection estimates
affordability, not a bound on growing histories or bad-code execution; the whole
deadline remains authoritative. Excess projection stops preparation without
shrinking projects/checks/caps, changing prompts, or launching another fixture.

Screen whole reservation is 3000 seconds, including startup, rendering,
generation, checks, writes, shutdown and publication. Qualification plus screen
is at most 3600 GPU-occupied/reserved seconds. Startup ceiling 600, per HTTP
render+generation pair ceiling 180, final cleanup reserve 60, all subordinate to the whole
deadline. A supervisor owns the server/job and ensures termination and a durable
terminal receipt. Register owned PIDs; never terminate unowned processes. CPU
authoring/preflight/review time and Kimi service cost are reported separately.
Before each pair, set the client's deadline to the smaller of the global driver
deadline and now+181 seconds (the unchanged worker reserves one second for its
receipt). Both HTTP operations share that deadline; no frozen-worker mutation
or independent 180-second reset between rendering and generation is permitted.

Run projects in authored index order. Within each project run rounds 1,2,3.
Within a round rotate worker arm order using (project_index+round_index) mod 3
over [H,S,R]; select immediately before the S worker. No concurrency within
the model schedule. Worker one attempt regardless of public/private success.
An applied patch persists even when wrong; a rejected patch leaves prior state.
Expose only genuine public-check/action feedback in the recorded tool result.

HTTP, schema, render/token accounting, context, cap or deadline failures yield
technical INCOMPLETE; archive all partial records, do not resume/retry/substitute
empty selection or silently reduce the bank. A valid stop at exactly its token
allowance is not automatically capped. Syntactically valid worker calls rejected
by the action consumer are completed failed attempts. Bad applied code is an
ordinary failed outcome. Persist every planned call's attempted/unattempted
state, raw requests/responses, token usage, elapsed times and workspace changes.
An INCOMPLETE or INELIGIBLE screen cannot advance the candidate.

## Outcomes and stop rule

The independent unit is a project. Report each project's three-round trajectory,
all check results and source coverage, plus final-round and all-round success.
A successful round requires an applied valid action and every active public and
private behavioral check passing. Test counts are not independent sample sizes.
For each arm report joint successful rounds /12, final successes /4, all-three
successes /4, and failures in new, retained and retirement behavior separately.
Keep paired project results visible; do not select a different candidate from R.

Advance only to preparation of a larger test if the complete eligible S arm:
- succeeds in at least 9/12 rounds and 3/4 final rounds;
- gains at least two successful rounds over H, improves the per-project number
  of successful rounds in at least two projects, and loses in no project;
- achieves at least as many successful rounds as R;
- uses no more than twice H's total prompt+completion tokens and twice H's total
  render+generation HTTP elapsed time, including all S selector costs;
- receives no human intervention in selection, coding or runtime repair.

Report startup/cleanup/check costs separately and the full measured totals for
each arm, including the unequal selector cost. Record a intervention event log
and all actual launches/commands; automatic execution alone is not proof of zero
help. Data authoring/review and technical operations are disclosed separately
from in-task intervention. Shared startup cost is reported once, not charged
selectively. Any zero/unmeasurable H denominator blocks the cost gate.

These are prospective practical screening thresholds, not significance tests.
Four projects cannot establish a general benefit. A failed threshold parks this
fixed recipe without an exposed-case rescue. A passing screen authorizes only
design of a larger, fresh, independently reviewed coding evaluation against full
history and useful manual reminders. Its design/sample size/statistical test and
cost tradeoff must be registered prospectively. Overall goal remains unmet.
