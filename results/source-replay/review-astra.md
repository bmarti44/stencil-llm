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
