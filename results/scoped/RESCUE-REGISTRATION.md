# Registration: the oracle-reminder rescue diagnostic

Frozen 2026-09-13, **before any generation**. Step 2 of Astra's forward review;
step 3 is running it. One registration, sufficient to implement without new
scientific choices.

## 1. The question it buys

*Can correct instruction presentation rescue executable behaviour?* If supplying
the applicable instruction does not rescue the frozen 4B on these blocks, then
building an automatic compiler to supply it cannot help either, and the direction
ends for a few tenths of a GPU-hour instead of five GPU-hours.

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
| `max_new_tokens` | **160** — one short function, tens of tokens |
| context ceiling | **4,096** total including generation (the shared GB10 rule) |
| prompt budget | 3,936 |
| per-generation deadline | **120 s** (short edits; the whole-file screen's 300 s does not apply) |
| scoring timeout | 30 s per case, in a **separate process** |

Model output is untrusted and is executed only by `scripts/scoped_score_one.py`
in a subprocess the runner kills on timeout. The gate's own trusted renderer
output runs in process; these are not the same path.

## 5. Measured prompt sizes (CPU, tokenizer only, already done)

Over all 32 cases with the shipping tokenizer:

| | min | median | max |
|---|---:|---:|---:|
| `off` prompt tokens | 150 | 216 | 268 |
| `oracle` prompt tokens | 186 | 253 | 303 |
| reminder cost | 23 | 36 | 68 |

**Limitation, stated before any outcome and not to be discovered afterwards:**
these development histories are 3–7 messages and fit **entirely** inside the
budget in both conditions. The shared ceiling is therefore satisfied as a
*ceiling*, but the reminder is **additive rather than displacing** — the oracle
prompt is 23–68 tokens longer. Two consequences, both binding on how the result
may be read:

1. This diagnostic measures **resolution with everything visible**, not retrieval
   under eviction. A rescue here is *not* evidence that memory beats recency
   packing under a real context turnover. That is what the 48-session
   confirmation exists for.
2. A rescue cannot be attributed to the reminder's *length*: the added tokens are
   a verbatim copy of a message already present in the same prompt.

## 6. Budget and stop rules

- **Pilot first:** the 4 longest-prompt cases, both conditions (8 generations).
  Record mean and max seconds per generation.
- **Projected total** = 1.5 x mean x 64 (the registered contention factor).
- **Hard stop:** if the projection exceeds **0.5 GPU-hours**, stop and report the
  measurement. Do not trim N, do not shorten `max_new_tokens`, do not drop a
  condition. Astra's finding, graded high: *"If they do not, stop this design
  rather than quietly shorten the horizon, remove controls, or reduce N after
  inspecting outcomes."*
- Chunks <= 50 minutes; `--budget-min` stops the runner before starting a new
  generation once spent, and the run is recorded **INCOMPLETE, never rescued**.
- Records are written atomically per generation, so a resumed run continues at
  generation granularity.
- GPU etiquette: `export STENCIL_GPU_SHARE=1`, launch through
  `tools/gpu_reserve.sh`, one Stencil GPU process at a time, message the peer
  session "looped-transformer" if the run will exceed 30 minutes.

## 7. Prespecified readings — Astra's thresholds, not renegotiable after seeing results

| outcome | reading |
|---|---|
| oracle succeeds on **>= 12/16** blocks **and** >= 6 wins with <= 1 loss | **RESCUED** — raise direction 1 from 28% to about **40%**; proceed to step 4 (the bounded automatic parser) |
| oracle succeeds on **<= 8/16** blocks, **or** <= 2 net rescued blocks | **NOT RESCUED** — reduce to about **12%**; stop this coding-workload direction under the present budget, publish the negative result |
| anything else | **INTERMEDIATE** — roughly 20–25%; do NOT launch the confirmation. At most, examine whether a clear instrument defect explains the ambiguity |

`scripts/scoped_rescue.py --summarize` prints the reading from these rules; the
arithmetic is in code so it cannot drift in prose.

**Ceiling warning, separate from the reading.** If the `off` condition already
succeeds on >= 12/16 blocks there is no headroom for a reminder to rescue, and
the prespecified rule cannot distinguish that from "the model cannot do it". The
summary prints a CEILING WARNING in that case; the reading still stands as
written, and the honest conclusion would be that the development blocks are too
easy, not that the direction is dead.

At N=16 the uncertainty is large. These thresholds are investment decisions, not
proof.

## 8. What was verified on CPU before any GPU time

`uv run pytest -q tests/test_scoped_blocks.py tests/test_scoped_rescue.py`
— 74 tests, including three full 64-generation pipeline runs with no model:

- `--stub-mode correct` -> 16/16 blocks in both conditions. **The positive
  control**: without it, a systematic extraction bug and a model that cannot do
  the task look identical.
- `--stub-mode rescue` -> 0/16 off, 16/16 oracle, READING: RESCUED. The decision
  arithmetic reports a rescue when there is one.
- `--stub-mode baseline` -> always answers the package default; scored wrong, not
  silently accepted.

Reply extraction is tested on fenced replies, unfenced replies, prose with no
function, the wrong function name, and trailing statements after the function.

## 9. Launch command (when, and only when, Brian lifts the GPU pause)

    export STENCIL_GPU_SHARE=1
    tools/gpu_reserve.sh scoped-rescue 30 12 -- \
      uv run python scripts/scoped_rescue.py \
        --out results/scoped/rescue.jsonl --budget-min 45
    uv run python scripts/scoped_rescue.py --summarize \
      --out results/scoped/rescue.jsonl

**GPU work is paused by Brian's standing instruction and nothing above may run
until he lifts it in his own words.**
