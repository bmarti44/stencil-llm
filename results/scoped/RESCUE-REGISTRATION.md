# Registration: the oracle-reminder rescue diagnostic

Frozen 2026-09-13, **before any generation**. Step 2 of Astra's forward review;
step 3 is running it. One registration, sufficient to implement without new
scientific choices.

**Amendment 1, same day, still before any generation** — Astra's implementation
review (`results/reviews/2026-09-13-scoped-instrument-astra.md`, VERDICT REPAIR)
raised six high findings against the instrument and this document. All are
applied below and marked **[A1]**. No generation has occurred, so nothing here is
fitted to an outcome.

## 1. The question it buys

*Can correct instruction presentation rescue executable behaviour?* If supplying
the applicable instruction does not rescue the frozen 4B on these blocks, that is
grounds to stop spending under the registered rule.

**[A1] It is not a proof of impossibility.** A failure of this particular cue
does not demonstrate that no compiler could help; the prior review explicitly
rejected that upper-bound reading, and the earlier wording here came close to it.
A negative result justifies the registered spending stop and nothing stronger.

It is a **diagnostic condition, not a candidate intervention.** The oracle arm
reads the resolved applicability and can never ship.

## 2. Data lineage

Fit or select on development material only. The 16 development blocks
(`src/stencil/scoped_dev_blocks.py`, gate in `results/scoped/STEP1.md`) are
authored from the semantics in `results/scoped/SEMANTICS.md`. **Nothing was fit,
selected or tuned on any evaluation benchmark; `data/bench/` was not read.** The
confirmation projects are separately authored and frozen before any model outcome
is inspected; these blocks never become confirmation material.

## 3. Units, arms, and the estimand

- **Unit:** the block. 16 blocks x 2 matched applicability cases x 2 conditions =
  **64 generations**.
- **A block succeeds** only if BOTH its cases pass all four oracle suites
  (functional, contract, preservation, obligation).
- **Conditions**
  - `off` — ordinary recency context: the session's messages packed newest-first
    into the prompt budget, the entering file, and the request.
  - `oracle` — identical, plus a compact action cue rendered immediately before
    the request: the applicable instruction **quoted verbatim from its source
    message, with that message's number**, and any live obligation statements.
    The oracle supplies the instruction only — never code, expected values, or a
    gold patch. `tests/test_scoped_rescue.py` asserts the reminder contains no
    `def `, `return `, `MissingEntry(key)` or `table.get`.
- **Reported:** blocks succeeded per condition; paired wins (oracle only) and
  losses (off only); per-condition invalid / truncated / timed-out counts and
  median generated tokens.

## 4. Frozen generation settings

| setting | value |
|---|---|
| trunk | `deploy/stencil_focus/build/hub-4b`, frozen, **no adapter** |
| decoding | greedy, `do_sample=False`, thinking disabled |
| chat format | **[A1]** the shipped tokenizer's chat template, `add_generation_prompt=True`, `enable_thinking=False`. The first version tokenized raw text, so "thinking disabled" was registered but never applied and there was no assistant boundary at all |
| `max_new_tokens` | **160** — one short function; the longest correct answer across all 96 gold and alternative spellings is **43** tokens |
| context ceiling | **4,096** total including generation (the shared GB10 rule) |
| prompt budget | 3,936 |
| per-generation deadline | **120 s** (short edits; the whole-file screen's 300 s does not apply) |
| scoring timeout | 30 s per case, in a **separate process** |

Model output is executed only by `scripts/scoped_score_one.py`, in a subprocess
the runner kills on timeout. **[A1] That buys crash separation and a timeout, not
a filesystem or information sandbox** — the earlier claim that it uses "the
repository's existing sandboxed path" was inaccurate and is withdrawn. The gate's
own trusted renderer output runs in process; these are not the same path.

**[A1] Reply extraction is syntax-aware.** The reply is parsed with `ast`;
imports, definitions and constants are kept and module-level calls and prose are
dropped rather than executed. The line-based first version had three defects that
each scored a *correct* answer as a total failure: it dropped an `import` above
the function, it took the first fence even when the code was in the second, and
it truncated a multiline `def` signature. Those failures would have fallen
disproportionately on the `oracle` condition, since a formal instruction cue is
exactly what makes a model answer more formally.

**[A1] The public prompt carries the contract the hidden oracle enforces**, in
both conditions identically: the package `__init__.py` with its documented
default, and a conventions block stating prospectivity, specificity, non-reviving
cancellation and express reinstatement. Without the docstring, C4's `core` case
asked the model to follow documentation it was never shown. These are task
specification, not gold labels.

## 5. Measured prompt sizes (CPU, tokenizer only, already done)

Over all 32 cases, through the chat template the runner actually applies:

| | min | median | max |
|---|---:|---:|---:|
| `off` prompt tokens | 329 | 399 | 447 |
| `oracle` prompt tokens | 363 | 442 | 497 |
| reminder cost | 25 | 37 | 75 |
| longest correct answer | 13 | 28 | **43** |

**Limitation, stated before any outcome and not to be discovered afterwards:**
these development histories are 2–6 messages and fit **entirely** inside the
budget in both conditions. The shared ceiling is therefore satisfied as a
*ceiling*, but the reminder is **additive rather than displacing**. Two
consequences, both binding on how the result may be read:

1. This diagnostic measures **resolution with everything visible**, not retrieval
   under eviction. A rescue here is *not* evidence that memory beats recency
   packing under a real context turnover.
2. **[A1] The comparison does not isolate a single mechanism.** The earlier claim
   that a rescue "cannot be attributed to the reminder's length, because the
   added tokens are a copy of a message already present" is **withdrawn as
   wrong**. Duplication changes length, repetition, position and salience, and
   the header "Instruction in force for this edit" adds authority on top. Any
   rescue is attributable to that bundle, not to applicability resolution alone.

**[A1] And the cue is privileged.** Quoting the *winning* statement supplies the
selection decision, which in a three-value task is most of the behavioural
answer; reinstatement reminders additionally resolve the historical reference.
Calling it "source text" does not remove the privilege, and the banned-substring
test only shows that certain code spellings are absent. This is consistent with
the intended diagnostic — *can the model implement the task when correct
applicability is supplied?* — and becomes uninterpretable only if it is ever
presented as evidence that an automatic compiler can identify that instruction,
or that compilation beats source-memory replay. It may not be.

## 6. Budget and stop rules — **[A1] implemented, not merely stated**

- **Pilot:** `scripts/scoped_rescue.py --pilot` runs the 4 longest-prompt cases in
  both conditions (8 generations), then projects
  `1.5 x mean_seconds x 64 / 3600` GPU-hours.
- **Hard stop, enforced in code:** a projection above **0.5 GPU-hours** returns
  exit 4 and refuses. Do not trim N, shorten `max_new_tokens`, or drop a
  condition. Astra's finding, graded high: *"stop this design rather than quietly
  shorten the horizon, remove controls, or reduce N after inspecting outcomes."*
  The 8 pilot generations count toward the total.
- **Budget accounting:** `--budget-min` stops before starting any generation whose
  worst case (`deadline + scorer timeout`) would not fit in the remaining time,
  rather than after overrunning. The reservation minutes passed to
  `tools/gpu_reserve.sh` must be **>=** the runner's `--budget-min`; the earlier
  launch command reserved 30 and allowed 45, which was incoherent.
- Records are appended per generation. **[A1]** A partial trailing line from an
  interrupted append is skipped and reported rather than aborting a resume; the
  earlier word "atomically" overstated the implementation.
- **[A1] Every record carries a configuration fingerprint** — fixture, engine,
  runner and scorer hashes, trunk, `max_new`, budget, deadline, and whether it
  came from `--stub`. A resume into a file written under a different
  configuration is refused (exit 3).
- GPU etiquette: `export STENCIL_GPU_SHARE=1`, launch through
  `tools/gpu_reserve.sh`, one Stencil GPU process at a time, message the peer
  session "looped-transformer" if the run will exceed 30 minutes.

The pilot must also record actual output lengths, EOS/cap/timeout frequency,
model-loading and scoring overhead, total resident time, memory peak and
concurrent load. Longest prompts do not guarantee longest outputs.

## 7. Prespecified readings — Astra's thresholds, not renegotiable after seeing results

| outcome | reading |
|---|---|
| oracle succeeds on **>= 12/16** blocks **and** >= 6 wins with <= 1 loss | **RESCUED** — raise direction 1 from 28% to about **40%**; proceed to step 4 (the bounded automatic parser) |
| oracle succeeds on **<= 8/16** blocks, **or** <= 2 net rescued blocks | **NOT RESCUED** — reduce to about **12%**; stop this coding-workload direction under the present budget, publish the negative result |
| anything else | **INTERMEDIATE** — roughly 20–25%; do NOT launch the confirmation. At most, examine whether a clear instrument defect explains the ambiguity |

**[A1] Completeness is checked before any reading is printed.** The registered N
is **64 unique records from one configuration**. Astra fed the first consumer a
48-record prefix with oracle wins and no losses and it printed `RESCUED`, because
a missing case silently became a failure. The consumer now stops at
`READING: INCOMPLETE` on any missing record, duplicate key, or mixed
configuration, and refuses any efficacy reading for a `--stub` run. A
`timed_out` generation never counts as a success. An incomplete dataset is never
rescued.

`scripts/scoped_rescue.py --summarize` prints the reading from these rules; the
arithmetic is in code so it cannot drift in prose.

**[A1] The thresholds are investment rules, not significance tests.** The summary
also prints the exact two-sided paired sign test on the discordant blocks: six
wins and one loss is **p = 0.125**; six wins and no losses is **p = 0.03125**.
`RESCUED` is a decision to keep spending, never a claim of proof.

**Ceiling, separate from the reading.** If the `off` condition already succeeds on
>= 12/16 blocks there is no headroom for a reminder to rescue, and the
prespecified rule cannot distinguish that from "the model cannot do it". The
summary says so in one consistent form: a `NOT RESCUED` under a ceiling means the
development blocks are too easy to measure this, **not** that the model cannot
implement the task.

At N=16 the uncertainty is large.

## 8. What was verified on CPU before any GPU time

`uv run pytest -q tests/test_scoped_blocks.py tests/test_scoped_rescue.py`
— **95 tests**, including three full 64-generation pipeline runs with no model:

- `--stub-mode correct` -> 16/16 blocks in both conditions. **The positive
  control**: without it, a systematic extraction bug and a model that cannot do
  the task look identical.
- `--stub-mode rescue` -> 0/16 off, 16/16 oracle, READING: RESCUED with its
  p-value. The decision arithmetic reports a rescue when there is one.
- `--stub-mode baseline` -> always answers the package default; scored wrong, not
  silently accepted.

Reply extraction is tested on fenced replies, unfenced replies, prose with no
function, the wrong function name, trailing statements, an `import` above the
function, code in the second fence, a multiline signature, and a top-level helper
the answer calls. Module-level side effects are dropped rather than executed.

**[A1] Regression tests lock in every counterexample Astra reproduced**: the bulk
gather that returns `[None]`, the function that rebinds an existing one to a
broken lambda, the function that logs after reading the table and not at all on
failure, the raise that names the wrong key, and the two wrong resolvers that
passed 16/16. The consumer refuses the 48-record prefix, duplicates, mixed
configurations and stub records; the non-thinking chat template is asserted to
produce an assistant boundary and an empty thinking block.

## 9. Launch command (when, and only when, Brian lifts the GPU pause)

    export STENCIL_GPU_SHARE=1
    # 1. the registered pilot: 8 generations, then a projection and a refusal
    tools/gpu_reserve.sh scoped-pilot 20 12 -- \
      uv run python scripts/scoped_rescue.py --pilot \
        --out results/scoped/pilot.jsonl --budget-min 15
    # 2. only if the pilot printed OK (exit 0, not exit 4)
    tools/gpu_reserve.sh scoped-rescue 60 12 -- \
      uv run python scripts/scoped_rescue.py \
        --out results/scoped/rescue.jsonl --budget-min 45
    uv run python scripts/scoped_rescue.py --summarize \
      --out results/scoped/rescue.jsonl

**GPU work is paused by Brian's standing instruction and nothing above may run
until he lifts it in his own words.**
