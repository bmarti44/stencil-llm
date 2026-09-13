# Candidate-A screen: the `off` baseline, and what it does and does not show

**Arm:** `off` (Qwen3-4B trunk, no adapter) · 48 sessions × 2 requests = 96 replies
**Run:** `results/a-screen/runs/off-oldrunner.jsonl`, COMPLETE, 61.6 min,
`runner_sha256 4acdb8f044c25a48` (see `RUNNER-EXCEPTION.md`)
**Status:** descriptive baseline. **One arm.** Nothing here compares an
intervention to anything, and nothing here is evidence that the candidate-A
objective works.

## The registered outcome

**J = 6/48.** J is all six suites passing at BOTH checkpoints. All six successes
are in the **`missing_record`** family; `naming` and `validation` contribute
zero. `function_only` is 39/96 replies. The aggregate hides that concentration
completely, which is why the breakdowns below are reported with every number.

## The exploratory outcome, and how it was chosen

J answers "did the whole session go right" and cannot say why a session failed.
After seeing `off` — **this endpoint was selected after the baseline was read,
and that is a selection effect that must travel with every use of it** — each
reply was additionally re-run against the contract suite for the state IN FORCE
and the suite for the OTHER state, giving five exhaustive categories: in-force /
alt / both / neither / output-failure.

The population key is whether the alternative state was **in force earlier in
that same session**. It is derived, not assumed, and the derivation is tested
over all 624 pool sessions (`tests/test_a_screen_supersession.py`):

* request 1 — true only for the 12 **reinstatement** sessions, whose prefix
  states a rule at turn 10 and replaces it at turn 12;
* request 2 — true whenever the event changed the convention (36 sessions).

An earlier version of this analysis called request 1 "no supersession yet" for
every session. That was **false**, and it inverted the headline. The corrected
reading is cleaner than the one it replaces.

| population | n | in force | **superseded / alternative** | neither |
|---|---:|---:|---:|---:|
| req 1, alternative **never** in force | 36 | 25 (69%) | **0 (0%)** | 11 (31%) |
| req 1, alternative **superseded in the prefix** | 12 | 5 (42%) | **4 (33%)** | 3 (25%) |
| req 2, convention **unchanged** | 12 | 7 (58%) | 1 (8%) | 4 (33%) |
| req 2, convention **changed** at the event | 36 | 11 (31%) | **12 (33%)** | 13 (36%) |

Fisher exact, two-sided:

* request 1, superseded-in-prefix vs never-in-force: **4/12 vs 0/36, p = 0.0025**
* request 2, changed vs unchanged: **12/36 vs 1/12, p = 0.139**
* pooled (not independent — the 12 reinstatement sessions appear in both rows):
  16/48 vs 1/48, p = 0.00007

**The pattern:** the model writes code obeying a convention only where a
convention has actually been superseded — 0 of 36 where nothing ever was, and a
consistent ~33% in both places where something was. The single "alt" reply in
the unchanged cell is the one arguable exception.

**The sharpest form of the failure:** in the changed-convention cell, **8 of 36
replies followed the superseded convention AND passed the functional suite** —
working code that implements a rule the user explicitly cancelled. A further 4
followed it and did not work.

## Breakdowns, where the alternative was superseded (n = 48)

| family | in force | superseded | neither |
|---|---:|---:|---:|
| missing_record | 9/16 | 7/16 | 0/16 |
| naming | 6/16 | 5/16 | 5/16 |
| **validation** | **1/16** | 4/16 | 11/16 |

| lifecycle | in force | superseded | neither |
|---|---:|---:|---:|
| reinstatement (24) | 9 | 7 | 8 |
| replacement (12) | 3 | 5 | 4 |
| scope (12) | 4 | 4 | 4 |

| transition | n | in force | superseded | neither |
|---|---:|---:|---:|---:|
| raise -> none | 8 | 6 | 2 | 0 |
| none -> raise | 8 | 3 | 5 | 0 |
| verb_noun -> noun_verb | 10 | 4 | 2 | 4 |
| noun_verb -> verb_noun | 6 | 2 | 3 | 1 |
| storage -> api | 7 | 1 | 2 | 4 |
| api -> storage | 9 | 0 | 2 | 7 |

`validation` is a competence problem, not a focus problem: 1/16 current-rule
successes and 11/16 "neither" means the trunk mostly cannot write the requested
change at all, in either state. A screen whose headline mixes that family in is
measuring two different things at once.

## Independent cross-check

`analysis/names.py` classifies the same replies syntactically — which
convention's method names the reply introduced — on the 16 `naming` sessions,
the only family where the two states differ by name (checked: `missing_record`
and `validation` gold share identical public method names in 32/32 requests).
It agrees with the executable measure on **30/32** requests. The two
disagreements (S08 req1, S11 req2) are replies with the right or wrong name
whose suite failed for an unrelated reason; the executable measure is the
stricter of the two, as intended.

## Confounds and limits, stated before any use of these numbers

1. **One arm.** No intervention is compared to anything here.
2. **Selection.** The contract-state endpoint was chosen after reading `off`.
   The registered outcome (J) is reported above and is not replaced.
3. **Supersession is confounded with prefix complexity.** Reinstatement sessions
   carry a third rule turn and a longer rule history, so the request-1 contrast
   compares "something was superseded" AND "one more rule statement" against
   neither. The p = 0.0025 does not separate them.
4. **The populations differ in more than the treatment**: project, request text
   and lifecycle all vary between cells.
5. **Not long-horizon retention.** The screen has two live requests over an
   authored 16-turn prefix, and the packer is told which rule turns to preserve
   (`session.rule_turns`). Nothing here tests finding or holding an instruction
   through a real agent session.
6. **Common-mode scoring defects can still bias an arm difference.** An
   under-sensitive checker applying identically to both arms does NOT imply it
   cannot manufacture a difference — different adapters make different kinds of
   undetected error. Any positive result must be read at the reply level.

## Is the screen a memorisation test? No.

The cf training run reached CE 0.0006 while `epochs_completed` was still 0 —
every example it learned on was unseen when it trained on it — which says the
gold is close to determined by the prefix under this generator. That raises the
question of whether an adapter could win the screen by reproducing text it has
already been fitted to. `analysis/overlap.py` measures it directly, with no
model: for each of the 192 screen golds, the most similar of the 2,304 training
golds.

| measure | min | p25 | median | p75 | max | >= 0.70 |
|---|---:|---:|---:|---:|---:|---:|
| token jaccard | 0.147 | 0.211 | 0.244 | 0.275 | 0.329 | 0/192 |
| difflib ratio | 0.035 | 0.105 | 0.124 | 0.138 | 0.254 | 0/192 |

Nothing in the screen resembles anything in the training pool at the text level,
so a positive result cannot be verbatim recall. What this does NOT rule out is
the **structural** template: 44/48 screen projects share the
dataclass-record/private-mapping idiom, and the jaccard floor of ~0.24 is that
shared vocabulary. A win would still need reading at the reply level.

## Instrument

`stencil.contracts.run_tests` shells out to `sys.executable -m pytest`. Under a
bare `python3` without pytest every suite returns False and **every reply
classifies as "neither"** — a complete, plausible, entirely empty table with
both contrasts at p = 1.000. That happened once on 2026-09-13. `stale2.py` and
`compare.py` now refuse to run unless a trivially passing suite passes, a
trivially failing suite fails, and gold satisfies its own contract suite on real
sessions.

## Reproduce

```
uv run python results/a-screen/analysis/stale2.py results/a-screen/runs/off-oldrunner.jsonl
uv run python results/a-screen/analysis/names.py  results/a-screen/runs/off-oldrunner.jsonl
uv run pytest -q tests/test_a_screen_supersession.py tests/test_a_screen_compare_guard.py \
               tests/test_a_screen_preflight_guard.py
```

Per-reply records: `results/a-screen/analysis/out/off-oldrunner-states.json`.
