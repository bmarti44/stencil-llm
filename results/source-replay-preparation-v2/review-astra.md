# Source-replay preparation v2 — independent design review

## Round 1 — 2026-09-08

Reviewer: native gpt-6-astra, xhigh, `/root/source_construction_review`,
author-disjoint from the proposed policy. The user's explicit native Astra xhigh
review instruction supersedes the older wrapper/Opus preferences. No reviewer
substitution occurred.

Score: 94/100

Disposition: ACCEPT — prospective construction design only.

Open findings: 0 critical, 0 high, 1 medium, 0 low. The >=90 and zero-open-high/
critical design acceptance requirement is met. This does not accept implementation,
authorize an authoring call, validate a source bank or supply a scientific result.

Purpose and threat model: find concrete methodological, budget and consumer-interface
mistakes in this bounded policy for trusted-but-fallible agents. Read archived
PROTOCOL.md and current LEDGER.md STATE/latest entries first. Inspected the named
proposal, inherited science/brief, ordinary prompts, accepted preparation research
and relevant current code. No stopped-bank source content, checks, references or
responses were opened. No model/API, tokenizer, container, sandbox/reference
execution, data generation or subagent was used. Only this review file was written.
Verification was static inspection plus standard-library text/AST/count checks;
the unavailable `python` executable was replaced with `python3` for those checks.

### Exact reviewed bindings

New candidate archived at `d930d9a1`:

| Artifact under `results/source-replay-preparation-v2/` | SHA-256 |
| --- | --- |
| `PREPARATION.md` | `a65931bbda8f413a9cb6278b49f96eda007b07397b3796f6f42294de8d2ce656` |
| `DATA-CONTRACT.md` | `02b18331d8731436f33faab1e1bbb3fdc8d63bf5109449d8c40eee0c9ca2c46b` |
| `correction-prompt.txt` | `e38bd6ef4e1b60840d9a154998c8146832c7b807cda6e877d27e796c4a6584b6` |

| Inherited subject | SHA-256 |
| --- | --- |
| `results/source-replay-staged/scaffold-prompt.txt` | `10da7a83cd76a6225e0eb5bde687511559b8e73726882cedfdd0d12a157b70a5` |
| `results/source-replay-staged/round-prompt.txt` | `28982adb50da11675fc3403501ee81f7435faae6248e714d64a58355113e89ab` |
| `results/source-replay/SPEC.md` | `01da819289d264926e8492a947b3bf8d6893b89c7559ff8142b9c4dabebda78c` |
| `results/source-replay/SCREEN-IMPLEMENTATION-BRIEF.md` | `40d3497277a0ccbea42213f856c4531cc290a5babb00956a95e6bc763786aa89` |

The static feasibility inspection used `source_replay_authoring.py` SHA
`8a6b42437d7a6459177ee176505870ebc715eaa56f15338dfccd61f5c20202d2`
and `tools/prepare_source_replay.py` SHA
`ba522c35ac7428ef992fd1d0982339522d14df8b59fdc64e0c20d1be54bbf61e`.
These are the existing implementation, not an implementation of this new policy.

### Findings

1. **Medium — source-replay-preparation-v2#1: distinguish check execution errors
   from the uncorrectable deadline/local-error boundary.** PREPARATION.md lines
   68–74 excludes deadline and unexpected local failures, but identifies eligible
   failures by `StageValidationError` from failed active checks. In the actual
   consumer, `scripts/coding_worker_dev.py:743` catches every `Exception` from
   `_fresh_execute` and records it as a failed result with `error` text;
   `src/stencil/focus/slab.py:635` converts child deadline/resource/setup failures
   to `InvalidProgram("sandbox deadline/resource failure")`. The authoring
   validator then raises the otherwise eligible `StageValidationError` at
   `src/stencil/source_replay_authoring.py:448`. Thus that exception class does
   not itself distinguish authored runtime errors from terminal execution
   infrastructure or sandbox deadline failures. An outer local exception can
   also contain an internal path, conflicting with the verbatim `error` projection
   and no-internal-path promise at PREPARATION.md lines 125–130.

   Clarify which deadline is meant and explicitly state the eligibility of
   sandbox resource failures and recorded outer local errors. A small rule in
   the policy/implementation brief, carried through the real consuming path,
   is sufficient; no general error framework is needed. Preserve raw diagnostics
   in the audit even when their failure class is terminal. Do not silently
   normalize arbitrary local errors into correction evidence. This is a bounded
   implementation-interface ambiguity, not evidence of evaluation leakage or a
   reason to reject the construction method. No live failure was executed here.

### Methodological assessment

Permitting the specified construction `actual` and `error` values is sound for
this design. The frozen schedule is authored before checks; the feedback comes
only from that same author's proposed reference/mutant and checks, before any
scientific worker answer exists. No scientific arm, selector, worker, prompt,
cap or decision threshold is adapted from measured worker outcomes. A codes-only
projection is not required to preserve that distinction and would discard useful
information for correcting a source-grounded reference or input representation.
This judgment does not establish that the single correction will be reliable.

Fixed check IDs, public/private partition, symbol, source IDs, behavior, intervals
and designated mutant check prevent mechanical deletion, relabeling, premature
expiry or public/private movement of failed coverage. They do not alone prove
that a changed input preserves a boundary or interaction: two differently named
checks can become equivalent, and an expectation can still be wrong while
passing its author's reference. The proposal adequately retains the independent
semantic obligation: every changed value and its original/corrected difference
must be reviewed against frozen sources, and no failed case's coverage role may
disappear. Apply that to substantive coverage, not just the unchanged metadata.
Semantic rejection is terminal. No new perfect-coverage or perfect-selector gate
is warranted.

Complete future-schedule visibility remains necessary for expiry authoring but
does not justify anticipating later behavior. Prefix-valid citations alone do
not establish prefix-valid semantics. The inherited independent source review
must still check permissions, retirement scope, accepted alternatives and future
rule leakage. The exact new contract is byte-prefixed by the entire inherited
contract; the sole added paragraph correctly describes the existing one-value
function call (`env[name](value)`), with no automatic argument repair.

### Bounds, state and integration

The maximum recomputes as four projects times four ordinary stages, plus at most
four corrections: 20 author calls. The one global correction can add one wave,
so five HTTP waves at 450 seconds equal 2250 seconds, leaving 150 nominal seconds
inside 2400. Neither there being no check-count maximum nor expensive checks
invalidates this arithmetic: the proposal explicitly disclaims completion and
requires the absolute whole deadline to dominate. No extra slot, time extension
or repeat is earned by a fast earlier response.

The barrier is project-independent: gather the ordinary stage's outcomes first,
stop for any ineligible failure category, and otherwise spend the single allowance
only on eligible failing projects. Reserve all 20 slots before calls, bind the
four possible correction slots to the actual trigger round, and retain unused
slots as unattempted. The existing driver needs its terminal-on-first-stage-failure
decision refactored to retain this outcome set; no separate runner is necessary.

Successful siblings are never requested or applied again. Each corrected packet
starts from the same pre-round module and accepted prefix, and only the accepted
corrected packet enters later `prior_packets`. The failed original remains audit
evidence and must not become another later-round authoring input. This follows
directly from the specified accepted-prefix contract and prevents an accidental
second opportunity to repair the same round through subsequent packets.

The correction template has exactly the seven declared placeholders:
`project_id`, `round_index`, `scaffold`, `prior_packets`, `original_packet`,
`diagnostics`, `data_contract`. One-pass `string.Template` substitution and the
specified strict compact JSON serialization fit the existing renderers. For an
active-reference failure, the projection includes failed active prior checks as
well as newly authored ones, in actual public-then-private order; prior checks
remain immutable. Mutant diagnostics come from the designated mutant execution,
not from an unrelated passing reference. Action rejections carry no check rows.

The proposed freeze count is exact: six specification/prompt subjects, four
preparation code/test files, seven reused consumers/dependencies and one new
immutable code-review snapshot = 18. The seven inherited dependencies are
`source_replay_screen.py`, `source_replay.py`, `coding_competence_dev.py`,
`coding_worker_dev.py`, `slab.py`, `slab_sandbox.py` and `renderer.py`. Actual
implementation review must check the new default paths, IDs/domains, maximum
requests, prompt loading and subject set, since all currently name the old
staged registration. The new snapshot must follow a real accepted current code
review; the old snapshot cannot approve the changed driver.

Both stopped banks remain ineligible and unavailable for this bank's authoring.
Their raw artifacts, reviews and freezes retain their original meaning; versioned
shared code changes do not rewrite historical launch code. Final source review,
scientific-runner acceptance, new bindings and actual CPU/token/cost preflight
remain future work. The original small technical qualification is not repeated.
The four-project H/S/R science, 48 scientific calls, existing utility/cost gate,
persistent code and full histories are preserved. Preparation success would
measure construction feasibility only. Larger untouched executable validation,
including useful manual reminders, remains necessary; failure of this last
custom preparation attempt ends this route rather than spawning another variant.

## Round 2 — 2026-09-08

Same author-disjoint native Astra xhigh reviewer and design-only scope. This
bounded follow-up checks only the clarification for finding #1 and its consuming
path; no expanded review, execution or research. All 10056 prior review bytes
remain unchanged, SHA-256
`3faa2b2941695bf85e46b78c4dd3b11957a48b63b90acf6fa4897379d39ec1fa`.

Score: 96/100

Disposition: ACCEPT — prospective construction design only.

Open findings: 0 critical, 0 high, 0 medium, 0 low.

Exact current candidate archived at `2eccbd66`:

| Artifact under `results/source-replay-preparation-v2/` | SHA-256 |
| --- | --- |
| `PREPARATION.md` | `a4de5fc781620a04c7104b0f938877336f0259f70c4110b84cfaa57e413f4ea3` |
| `DATA-CONTRACT.md` | `02b18331d8731436f33faab1e1bbb3fdc8d63bf5109449d8c40eee0c9ca2c46b` |
| `correction-prompt.txt` | `e38bd6ef4e1b60840d9a154998c8146832c7b807cda6e877d27e796c4a6584b6` |

**source-replay-preparation-v2#1 (resolved 2026-09-08).** Independently compared
the entire PREPARATION.md delta to the initial reviewed version and reread the
actual `run_checks`/sandbox/authoring return paths. The new policy permits only
null or thirteen exact `InvalidProgram: <label>` error strings. Other observable
errors, including the sandbox deadline/resource sentinel and path-bearing local
exception strings, make the bank INCOMPLETE without correction. The rule applies
before accepting any validation outcome, including a normally returned success
whose mutant failed because of such an error. This last case matters because
the existing validator otherwise accepts a failed designated mutant check
without classifying its error.

The text accurately limits this to observable labels: an opaque sandbox
`ValueError` can have more than one internal cause. It does not claim perfect
root-cause classification. The diagnostics section now expressly permits only
these labels or null. Together these changes resolve both the correction-boundary
ambiguity and arbitrary local-error text exposure without changing sources,
science, call counts or budgets. DATA-CONTRACT.md and the correction prompt
remain byte-identical to Round 1. No new finding or regression was identified.

The prospective design is accepted with no open findings. Sol implementation and
its real consuming tests remain to be reviewed independently before a new immutable
code-review snapshot, freeze or authoring launch. Neither this acceptance nor the
two stopped preparations establishes coding utility or completes the larger goal.
