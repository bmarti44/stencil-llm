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
