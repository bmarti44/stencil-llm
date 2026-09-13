# Candidate-A screen: the `off` baseline, and what it does and does not show

**Arm:** `off` (Qwen3-4B trunk, no adapter) · 48 sessions × 2 requests = 96 replies
**Run:** `results/a-screen/runs/off-oldrunner.jsonl`, COMPLETE, 61.6 min,
`runner_sha256 4acdb8f044c25a48` (see `RUNNER-EXCEPTION.md`)
**Status:** descriptive baseline. **One arm.** Nothing here compares an
intervention to anything.

> **Revision 2, 2026-09-13.** Astra's forward review
> (`results/reviews/2026-09-13-a-screen-direction-astra.md`) found six
> overclaims in revision 1 and one defect in the screen itself that changes how
> every number below should be read. All are corrected here. Revision 1 is in
> git history at commit `1b2953ed`; nothing has been deleted to hide it.

## READ THIS FIRST: the screen admits a trivial policy

**The whole 48-session screen can be passed by "obey the most recent rule
statement and copy the existing code."** Verified directly, not inferred:

* **Reinstatement does not require recovering anything.** All 12 reinstatement
  events restate the restored rule in full. S20's event says *"validation lives
  in the public functions, which raise ValueError before calling the table"* —
  that is the restored state, spelled out. The model never has to remember what
  the original convention was.
* **Scope is indistinguishable from a global replacement.** All 12 scope
  sessions' request 2 targets a file **inside** the exception (S03 → `fines.py`
  when the exception is "FineLedger only"; S07 → `stops.py` when it is
  "`busboard/stops.py` only"). The screen never asks for a fresh operation
  **outside** the scope, which is the only thing that separates "apply this rule
  here" from "apply this rule everywhere".
* **Preservation is testable by copying.** Existing implementations are visible
  in the prompt, so a reply can preserve protected behaviour without having
  retained the rule that governs a new operation.

So the lifecycles are labels on the data, not tests of the behaviour they name.
A future arm could win this screen decisively while doing nothing but following
the latest instruction. **Any result from this screen — including the baseline
below — measures "does the model follow the most recent instruction and leave
working code alone", not instruction retention or selective revision.**

Fixing this requires fresh operations outside a scope exception, restoration
that refers back without restating the value, and trivial-policy baselines that
must fail. That is a new registration, not an amendment.

## The registered outcome

**J = 6/48 sessions.** J is all six suites passing at BOTH checkpoints. All six
successes are in the **`missing_record`** family; `naming` and `validation`
contribute zero. `function_only` is 15/48 sessions, or 39/96 replies — different
units of the same run, not inconsistent numbers.

## The exploratory outcome, and how it was chosen

J cannot say why a session failed. After seeing `off` — **this endpoint was
selected after the baseline was read, which is a selection effect that travels
with every use of it** — each reply was re-run against the contract suite for
the state in force and the suite for the other state: in-force / alt / both /
neither / output-failure.

The population key is whether the alternative state was in force earlier in that
same session. It is derived, not assumed, and tested over all 624 pool sessions
(`tests/test_a_screen_supersession.py`): at request 1 this is true only for the
12 reinstatement sessions; at request 2, whenever the event changed the
convention. Revision 1 of this analysis called request 1 "no supersession yet"
for every session, which was false and inverted the headline.

**"Superseded" here means superseded for the scored operation, not erased from
the session's valid rules.** A scope exception leaves the alternative in force
everywhere else; a prospective replacement leaves it governing existing code.

| population | n | in force | alternative | neither |
|---|---:|---:|---:|---:|
| req 1, alternative never in force | 36 | 25 (69%) [53–82] | 0 (0%) | 11 (31%) [18–47] |
| req 1, alternative superseded in prefix | 12 | 5 (42%) [19–68] | 4 (33%) [14–61] | 3 (25%) [9–53] |
| req 2, convention unchanged | 12 | 7 (58%) [32–81] | 1 (8%) [1–35] | 4 (33%) [14–61] |
| req 2, convention changed | 36 | 11 (31%) [18–47] | 12 (33%) [20–50] | 13 (36%) [22–52] |

Brackets are Wilson 95% intervals. Fisher exact, two-sided:

* request 1, superseded-in-prefix vs never: **4/12 vs 0/36, p = 0.00254**
* request 2, changed vs unchanged: **12/36 vs 1/12, p = 0.139**

The two contrasts share the 12 reinstatement sessions, so they are not
independent of each other. A pooled count across requests is 16/48 vs 1/48;
**no pooled p-value is reported**, because the two observations within a session
are dependent and an independence-based test would not be justified.

**The pattern, stated without exclusivity:** alternative-convention replies are
common wherever a supersession exists (33% in both such cells) and rare where
none does — 0/36 at request 1, and 1/12 in the unchanged cell at request 2. That
single unchanged-cell reply is a real counterexample to any "only where"
phrasing, and revision 1 was wrong to wave it through as arguable.

### What "followed the superseded rule and it worked" actually means

Among the 36 changed-convention request-2 replies:

| | n | passes `functional` | passes `function_only` | passes all six |
|---|---:|---:|---:|---:|
| followed the rule in force | 11 | 6 | **3** | 3 |
| followed the superseded rule | 12 | 8 | **7** | 0 |

`functional` is the new suite alone. `function_only` additionally requires
regression and protected-function success, and is the better proxy for "a user
would accept this". Revision 1 said "8 replies wrote working code implementing a
cancelled rule" on the strength of the narrow suite; the `function_only` figure
is **7**, and the corresponding figure for correct replies is **3**. No reply
that followed the superseded rule passes all six suites, because the in-force
contract suite fails by construction.

## Breakdowns where the alternative was superseded (n = 48)

| family | in force | alternative | neither |
|---|---:|---:|---:|
| missing_record | 9/16 | 7/16 | 0/16 |
| naming | 6/16 | 5/16 | 5/16 |
| validation | 1/16 | 4/16 | 11/16 |

| lifecycle | in force | alternative | neither |
|---|---:|---:|---:|
| reinstatement (24) | 9 | 7 | 8 |
| replacement (12) | 3 | 5 | 4 |
| scope (12) | 4 | 4 | 4 |

| transition | n | in force | alternative | neither |
|---|---:|---:|---:|---:|
| raise → none | 8 | 6 | 2 | 0 |
| none → raise | 8 | 3 | 5 | 0 |
| verb_noun → noun_verb | 10 | 4 | 2 | 4 |
| noun_verb → verb_noun | 6 | 2 | 3 | 1 |
| storage → api | 7 | 1 | 2 | 4 |
| api → storage | 9 | 0 | 2 | 7 |

`validation` reaches the in-force contract once in 16 and lands in "neither" 11
times. **"Neither" means neither contract suite passed; it does not say why.**
Missing components, wrong routing, incomplete implementation and instruction
failures all produce it, and they can coexist. Revision 1 called this "a
competence problem, not a focus problem" — that is not supported by this
measurement. Isolating a competence ceiling needs a matched current-rule-only
condition, which has not been run.

## Independent cross-check

`analysis/names.py` classifies the same replies syntactically on the 16 `naming`
sessions, the only family where the two states differ by method name
(`missing_record` and `validation` gold share identical public method names in
32/32 requests). It agrees with the executable measure on **30/32**; the two
disagreements are replies with the right or wrong name whose suite failed for an
unrelated reason.

## Is the screen a memorisation test?

Only one statement is licensed by what was measured:

> **No screen gold is an exact duplicate of an enumerated training gold.**
> (Zero exact whole-file matches, 192 screen golds against 2,304 training golds.)

Revision 1 went further and said a positive result "cannot be verbatim recall".
That is withdrawn, for three reasons Astra established:

1. `overlap.py` prints "max over ANY training gold", but its difflib maximum is
   taken over only the **eight** candidates pre-selected by identifier-set
   Jaccard. The description is inaccurate.
2. The reassuring magnitude is an artifact of the measure. `SequenceMatcher`
   applies popularity filtering by default; disabling it moves the maximum over
   the same candidate sets from **0.254 to 0.517** (S48 req 2 `none`: 0.146 →
   0.517). Recomputed and confirmed.
3. Gold-to-gold overlap does not measure what a model recalls while generating.
   It misses reused fragments, code copied from the prompt, renamed routines and
   learned construction templates.

Relatedly, "every training example was unseen" (from `epochs_completed = 0`) is
misleading: there are 1,152 positive examples but only **1,007 distinct chosen
completions**, and 121 of the 1,072 contributing microsteps repeat a completion
already encountered.

## Confounds and limits

1. **The screen admits a trivial policy** — see the top of this document. This is
   the limitation that matters most.
2. **One arm.** No intervention is compared to anything here.
3. **Selection.** The contract-state endpoint was chosen after reading `off`.
4. **Supersession is confounded with prefix complexity.** Reinstatement sessions
   carry a third rule turn and a longer rule history, so the request-1 contrast
   compares "something was superseded" AND "one more rule statement" against
   neither. p = 0.00254 does not separate them.
5. **The populations differ in project, request text and lifecycle** as well as
   in the treatment.
6. **Not long-horizon retention.** Two live requests over an authored 16-turn
   prefix, with the packer told which rule turns to preserve
   (`session.rule_turns`).
7. **Common-mode scoring defects can still bias an arm difference.** An
   under-sensitive checker applying identically to both arms does not imply it
   cannot manufacture a difference — different adapters make different kinds of
   undetected error.

## Instrument

`stencil.contracts.run_tests` shells out to `sys.executable -m pytest`. Under a
bare `python3` without pytest every suite returns False and **every reply
classifies as "neither"** — a complete, plausible, entirely empty table with both
contrasts at p = 1.000. That happened once on 2026-09-13. `stale2.py` and
`compare.py` now refuse to run unless a trivially passing suite passes, a
trivially failing suite fails, and gold satisfies its own contract suite on real
sessions. That self-check samples S01–S03, all `naming`; it does not yet prove a
family-specific execution failure would be caught.

## Reproduce

```
uv run python results/a-screen/analysis/stale2.py results/a-screen/runs/off-oldrunner.jsonl
uv run python results/a-screen/analysis/names.py  results/a-screen/runs/off-oldrunner.jsonl
uv run pytest -q tests/test_a_screen_supersession.py tests/test_a_screen_compare_guard.py \
               tests/test_a_screen_preflight_guard.py
```

Run under `uv run python`, never bare `python3`. Per-reply records:
`results/a-screen/analysis/out/off-oldrunner-states.json`.
