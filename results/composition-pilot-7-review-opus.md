# Composition pilot 7 — independent accuracy review (Opus, max effort)

Reviewer: independent accuracy reviewer under Brian's 2026-09-06 ruling. One round, no code
edits, CPU only. No GPU, container, `RUNNING.flag` or process was touched; nothing under
`data/bench` and no evaluation-bank episode content was read. Every number below was
**re-derived from the records and the saved HTTP receipts**, not copied from the report.

Artifacts reviewed: `results/quick-checks/composition-pilot-7/{README.md, registration.md,
main-records.jsonl, main-summary.json, summary.json, report-audit.json, audit.json, audit.log,
composition-control.json, determinism.json, lifecycle.json, launch.json, ready.json,
main-floor.json, main-groups.json, local-hashes.json, journals-index.jsonl, cpu-validation.log,
runner.log, report.py}`, the gitignored journals under `local/main/*/*/loop.jsonl`,
`local/main/*/Q/q-*.jsonl` and `local/http/main/*/*/*.json` (literal prompts and completions),
the pinned tree `/tmp/stencil-pilot7-pinned` at `24ed80a4`, `src/stencil/focus/{renderer.py,
slab2.py, slab2_endpoint.py, register.py, loop.py, slab.py}`, `scripts/composition_pilot{5,7}.py`,
`tests/test_focus_slab2*.py`, `tests/fixtures/slab2_pilot6_registers.json`, and — for the
before/after contrast — `results/quick-checks/composition-pilot-6/{main-records.jsonl,
launch.json, local/**}` and `results/composition-pilot-6-review-opus.md`.

---

## 0. Verification receipts (independently reproduced)

Pinned tree `git rev-parse HEAD` = `24ed80a49edcea3359d0c45d361daf7fdf761745`; tracked tree
clean (only the gitignored `models/` tokenizer link). All seven model-facing sources are
**byte-identical** between the pinned tree and the live tree (`slab2.py`, `slab2_endpoint.py`,
`renderer.py`, `register.py`, `loop.py`, `slab.py`, `composition_pilot7.py`).

| Claim in README/registration | Re-derived | Verdict |
|---|---|---|
| 512 records, 128/arm, Q/R/N/T | 512; expected set == actual set exactly | confirmed |
| R compact `delivery=ready` **4/34** | 4 — dev-06 t12,13,14,15 and nothing else | confirmed |
| R compact format adherence **30/34** | 30; the 4 non-adherent cells are the same 4 | confirmed |
| all-35 ready emissions Q 34 / R 4 / N 3 / T 12 | 34 / 4 / 3 / 12 | confirmed |
| all-35 format adherence Q 1 / R 30 / N 32 / T 19 | 1 / 30 / 32 / 19 | confirmed |
| CPU control: contradiction removed on 34 matched **and** all 35 | 35/35 re-rendered: no `delivery` row, no `trailer delivery=` string; 35/35 `new_sha256` and `old_block_tokens` reproduced bit-exact | confirmed |
| all 35 old blocks carried the contradiction | 35/35 contain `trailer delivery=ready` | confirmed |
| 17,126 → 8,412 block tokens | 17,126 → 8,412 (−50.9%) | confirmed |
| Round-0 written 8/8, executing lanes 8/8, caps 0 (every arm) | 8/8, 8/8, 0 | confirmed |
| Written rounds Q/N/T 128, R 127 | R's only non-write = `slab2-dev-04 turn 12` | confirmed |
| Determinism D = 0/8 | `determinism.json` `mismatches: []`, 8 prompts, C4 forward+reverse | confirmed |
| Strict T floor 128/128, 29/39, 19/35, 48/49, four traits eligible | `ep.strict_floor(rows)` == reported floor, field for field | confirmed |
| PRIMARY delivery R 8/8 vs N 1/8, 7–0, p = 0.0078125, Holm 0.0234375 | reproduced by an **independent** re-implementation written from the registration prose | confirmed |
| PRIMARY format 7/8 vs 8/8, indent 10/15 vs 11/16, both n.s. | reproduced exactly, incl. T and Q columns | confirmed |
| Projection **6.985773357112** GPU-h | `(497.4678 + 1.25·(64·(106.955+96.361+82.334) + 16·89.962))/3600` = 6.985773357112 | confirmed |
| GPU held 3533.43 / 5400 s; startup 497.47 s | confirmed from `lifecycle.json` / `ready.json` | confirmed |
| Max prompt 10,994 (+2,048 = 13,042 < 32,768) | 10,994 (R dev-06 t15) | confirmed |
| Saved-response audit: 512 payloads + record fields | I re-verified all 512 independently: output text, `output_tokens`, `truncated`, `text_sha256`, `output_sha256`, `prompt_tokens` — **0 mismatches** | confirmed |
| 1,040 local files hashed | 1,040 files exist; 40/40 random `sha256`+`bytes` verified | confirmed |
| CPU suite "135 passed, 1 xfail" | I re-ran `tests/test_focus_slab2{,_amendment3,_amendment4,_driver}.py tests/test_no_side_effect_imports.py` → **135 passed, 1 xfailed, 72.10 s** | confirmed |
| Pilot-6 O byte-identical to R | 128/128 identical `output_sha256`, `output` text **and** `prompt_tokens` | confirmed |
| 34-cell control frozen before the run | fixture committed in `24ed80a4` (03:10:33), unchanged since; `registration.md` written 03:14:16; container launched 03:14:23 | confirmed |
| Gate logic frozen before the run | the reading is `ep.pilot_reading` at the pinned SHA; the only post-run `report.py` edit (`06f59e1c`→`9f1d8bf5`) adds literal trailers, artifact links and spacing — **no gate logic** | confirmed |

**The report is numerically honest. I found no arithmetic error, no mis-stated count, and no
overclaim anywhere in README.md, summary.json or report-audit.json.** Everything below is about
what the numbers mean and whether the gate that failed is a valid instrument.

---

## 1. THE GATE ITSELF

### 1.1 Is `INELIGIBLE` correctly applied under the registration as written?

**Yes. Plainly and mechanically yes.** `registration.md:55-58` requires
`R compact delivery=ready emissions<=2/34`; `slab2_endpoint.py:205-210` computes
`emissions = 4` and appends `"compact delivery=ready>2/34 or missing"`. Every other registered
item passes. `summary.json` `failures` contains exactly one entry, and it is the right one.
I checked all thirteen registered ELIGIBLE conditions individually; twelve pass, one fails.
The pilot did not fudge, did not re-match, did not move a threshold, and did not hide the
failure. The reading is exact.

### 1.2 One initiating event that locks, or four independent failures?

**One initiating event that then locks. The evidence is unambiguous.**

All four cells are `slab2-dev-06` rounds 12–15 — the *entire* compact window of that episode
(dev-06's compact window is exactly t12–t15). The four literal trailers, from
`report-audit.json` and re-derived from `main-records.jsonl`:

```
slab2-dev-06 t12  report: task=B status=ok delivery=ready
slab2-dev-06 t13  report: task=B status=ok delivery=ready
slab2-dev-06 t14  report: task=B status=ok delivery=ready
slab2-dev-06 t15  report: task=B status=ok delivery=ready
```

Byte-identical, four times.

**Round 11 (the round before)** — literal rendered block, `local/main/slab2-dev-06/R/loop.jsonl`
record 11. Format is still `verbose`, so the `delivery` row is present and `delivery=ready` is
the *correct* answer:

```
Active rules for this request (subject to system/developer instructions):
[{"default":false,"key":"format","kind":"format","text":"Workshop obligation: format must be verbose. format verbose = trailer includes delivery when task is delivery-scoped","value":"verbose","version":1},{"default":false,"key":"indent",...,"value":"2","version":2},{"default":false,"key":"language",...},{"default":false,"key":"test_record",...},{"default":true,"key":"delivery","kind":"process","text":"Workshop obligation: delivery must be ready. delivery ready = trailer delivery=ready when verbose and scoped","value":"ready","version":0}]
Retired rules (not binding):
Retired: indent v1; no longer binding; reason supersedes.
Retired: delivery v1; no longer binding; reason completes.
Apply the active rules while answering the request below.
Current user request:
[{"role":"tool","tool_results":[...]},{"role":"user","text":"completes delivery: Workshop obligation: delivery must be staged. delivery staged = trailer delivery=staged when verbose and scoped. Retired; use default delivery ready = trailer delivery=ready when verbose and scoped\nExtend workshop B: add step_11(x) in policy.py; ..."}]
```

R's reply at t11: `report: task=B status=ok delivery=ready` — **correct**, and it is the
*delivery* change round R wins in the primary.

**Round 12 (the initiating round)** — the format cancels to the default `compact`, and the
composed block **no longer contains a delivery row at all**:

```
Active rules for this request (subject to system/developer instructions):
[{"default":true,"key":"format","kind":"format","text":"Workshop obligation: format must be compact. format compact = trailer omits delivery","value":"compact","version":0},{"default":false,"key":"indent","kind":"style","text":"Workshop obligation: indent must be 2. indent 2 = block bodies indented by exactly 2 spaces per level","value":"2","version":2},{"default":false,"key":"language","kind":"language","text":"Workshop obligation: language must be Python. language Python = executable Python file","value":"Python","version":1},{"default":false,"key":"test_record","kind":"process","text":"Workshop obligation: test_record must be test-after-edit. test_record test-after-edit = harness runs public tests after file write","value":"test-after-edit","version":1}]
Retired rules (not binding):
Retired: indent v1; no longer binding; reason supersedes.
Retired: delivery v1; no longer binding; reason completes.
Retired: format v1; no longer binding; reason cancels.
Apply the active rules while answering the request below.
Current user request:
[{"role":"tool","tool_results":[...]},{"role":"user","text":"cancels format: Workshop obligation: format must be verbose. format verbose = trailer includes delivery when task is delivery-scoped. Retired; use default format compact = trailer omits delivery\nExtend workshop B: add step_12(x) in policy.py; ..."}]
```

R repeats its own t11 trailer verbatim. **Rounds 14 and 15 carry no register event at all** —
their user text is bare task prose (`"\nExtend workshop B: add step_14(x) …"`), and their
rendered rows are identical to t13's. There is no new stimulus at t14/t15 for either the
`format` or the `delivery` family; the only thing that changes is that R's own wrong trailer
accumulates in its context. Decoded from the actual prompt at
`local/http/main/slab2-dev-06/R/15.json` (10,994 tokens), the string
`report: task=B status=ok delivery=ready` occurs **four times**, at character offsets 30282,
33523, 37043, 40427 — R's own t11–t14 replies. Counting t14 and t15 as independent failures of
the register is not defensible.

Cross-episode confirmation that the first compact round decides and then the arm repeats
itself: in the seven other episodes R's first compact round is clean and R stays clean for
**31/31** remaining compact cells. In the whole run there are 5 opportunities to recover from
an emitting state (R dev-06 t13/14/15, N dev-00 t14/15) and **0 recoveries**.

I also ruled out the obvious lane-level explanations: dev-06's context is *not* unusual. At its
first compact round it carries 7 stale rendered `"key":"delivery"` rows — fewer than dev-00 (8)
and the same as dev-02 (7), both of which stayed clean; and 6 prior self-emitted `delivery=ready`
trailers — fewer than dev-01 (8), dev-03 (8) and dev-05 (7), all of which stayed clean. dev-02
is broken from round 0 exactly like dev-06 and stayed clean. There is no dose–response and no
structural property of dev-06 that predicts it. It is one stochastic lane.

### 1.3 Is a per-round limit of 2/34 consistent with the amendment's own registered unit?

**No, and the inconsistency is not cosmetic.**

`registration.md:21` declares "PRIMARY: … **episode as the unit**", adopting recommendation 2
of the pilot-6 review ("Declare the episode the unit of analysis. Round-level matched-cell
counts are reported as descriptive only", `composition-pilot-6-review-opus.md` §Pre-registration
changes). `registration.md:55-58` then makes a round-level count of the same phenomenon a hard
binary gate. The amendment's own justification for the episode unit — post-decision rounds are
deterministic repeats (pilot-6 finding H4) — applies with full force here: rounds 13, 14 and 15
of dev-06 are repeats of the decision at round 12, and I have quoted the prompts that prove
there is nothing else for the model to respond to.

**The correct episode-level reading is R = 1 of 8 episodes.** And the decisive number the
report does not draw out:

| arm | 34-cell `delivery=ready` emissions | episodes with ≥1 emission | cells |
|---|---:|---:|---|
| R (register) | **4/34** | **1/8** | dev-06 t12–15 |
| N (history only, **no rules block at all**) | **3/34** | **1/8** | dev-00 t13–15 |
| T (oracle text) | 12/34 | 3/8 | dev-00, dev-02, dev-07 |
| Q (fresh context) | 33/34 | 8/8 | everywhere but dev-01 t13 |

Exact McNemar on the 34 matched cells, R vs N: 4 R-only, 3 N-only, 0 both, 27 neither →
7 discordant, **two-sided p = 1.0000**. At the episode level R and N are **1/8 each**.

**The registered limit of 2/34 is below what the negative control itself achieves.** N has no
rendered rules block, so it cannot possibly suffer a delivery×format rendering contradiction —
and N scores 3, i.e. N fails the gate that was written to certify that the contradiction was
removed from R. A gate the control arm fails is not measuring the thing it names.

### 1.4 Why the threshold was mis-calibrated, and why another re-pilot cannot fix it

The threshold was set from pilot 6, where N scored **0/34**. That 0 was a single draw, not a
floor. I can prove it, because pilot 6 and pilot 7 sent **byte-identical HTTP payloads** for
166 of the 512 cells (N and T are unaffected by the renderer change wherever their history had
not yet diverged). I compared `request` JSON hashes and completion `token_ids` directly:

* **166 cells with byte-identical requests** (same prompt token ids, `temperature: 0`,
  `seed: 20260906`, same pinned vLLM digest, same flags — the only difference is the container
  instance).
* **10 of those 166 returned different completions** → **6.02% cross-run divergence**
  (Wilson 95% CI 3.3%–10.7%).
* Worked example, `slab2-dev-00 T turn 0`, prompt 557 tokens, elementwise-equal, identical
  params:
  * pilot 6: `    return [v * 6 + 3 for v in x]`
  * pilot 7: `    return x * 6 + 3`  ← a semantic error that then poisons the whole lane.

So the pilot's within-run determinism gate (D = 0/8 forward/reverse C4, exact) is real but
**only within one container**. Across container restarts this harness is ~94% reproducible.
That is exactly what happened to N's compact behaviour: 0/34 → 3/34 with **no code change that
touches N's rendering at all**. A 3-cell swing on this precise 34-cell instrument was produced
by run noise alone, in hand, in this data set. A 2-cell margin is inside the noise.

And a re-pilot cannot clear it. Every compact window in the bank is 4 or 5 rounds long
(4,4,4,5,5,5,4,4 = 35), and the observed failure mode locks from its onset round. A single
episode that locks at its first compact round contributes 4 or 5 emissions — already more than
double the limit. So `≤2/34` is operationally "**zero episodes may lock**". At the observed
per-episode rate of 1/8, P(0 locks in 8 episodes) = (7/8)^8 = **0.344**. Re-piloting to clear a
gate that passes about one time in three, when the no-block control fails it, is precisely the
loop AGENTS.md tells the orchestrator to terminate.

### 1.5 Ruling on the gate

* `INELIGIBLE` **is correctly applied under the registration as written**. The artifact is honest
  and the failing item is named exactly. Nothing here is a criticism of how pilot 7 was run.
* The gate is nevertheless **mis-specified** (round-level, contradicting the amendment's own
  declared unit) and **mis-calibrated** (threshold below the negative control's own value, and
  inside the measured run-to-run noise).
* **The registration's internal inconsistency should be corrected by a registered amendment
  before the larger test, not by another re-pilot.** This is a specification correction with the
  evidence attached and the amendment registered *before* the next launch — not an "amendment
  spiral": the endpoint under test passed, and the item being corrected is a secondary
  instrument-health check whose entire scientific content is already covered, deterministically
  and at 35/35, by a CPU control that does not consume GPU time and does not sample.

---

## 2. THE FIX

### 2.1 The CPU re-render control verifies, exactly

I rebuilt each of the 35 saved pilot-6 registers from `tests/fixtures/slab2_pilot6_registers.json`
(`Register.replay` with the saved `register_events`, `defaults`, `event_generations` and
`generation`), asserted the reconstructed `versions` equal the saved `after_versions`, and
re-rendered with the pinned `renderer.render`:

* **35/35** produce a live-row list with **no `delivery` key** and **no `trailer delivery=`
  substring anywhere in the block**; `contradictions: 0` in `composition-control.json` is exact.
* **35/35** of the recorded `new_sha256` and `old_block_tokens` reproduce bit-exact once the
  `"\nCurrent user request:\n"` suffix is excluded (the control's own convention).
* **35/35** *old* blocks contained `trailer delivery=ready`.
* 17,126 → 8,412 tokens (−50.9%), matching `registration.md` to the digit.

The responsible code is `renderer.py:76-90`: `compact_format` is derived from the live rows and
the `delivery` row is dropped from `rows`; provenance/scope metadata is gone from the row dicts
(`renderer.py:79-88`), the run-on style gloss is no longer concatenated, tombstones are plain
(`renderer.py:70-73`, no `replaced by` / `reinstated as` retargeting), and the
`Retired rules (not binding):` header is now conditional (`renderer.py:94`). Pilot-6 findings
H1, M1, M2, M3, L2 are all genuinely fixed in the live view. The behavioural effect is large:
on the fixed 34 cells, R went **25 → 4** emissions and **9/34 → 30/34** format adherence, and
from **6/8 → 1/8** episodes with any emission (5 discordant episodes, all improving; exact
one-sided p = 0.03125 — well outside the ~1-episode scale of the run noise demonstrated by N).

### 2.2 So why did dev-06 still emit? Three sources, and only one of them is history-copying

**(a) The composed block at t12–t15 is correct.** Quoted in full in §1.2. There is no delivery
row, and the block states `format compact = trailer omits delivery`. The live view is clean.

**(b) The proximate driver at t13–t15 is R copying its own prior trailer.** `loop.py:363`
appends `rendered.prefix_ids + output_ids + closure` to `history_ids` every turn, so R's own
replies are in its context verbatim. At t15 there are four literal copies of
`report: task=B status=ok delivery=ready` in the prompt (offsets quoted in §1.2). Rounds 14 and
15 have no register event.

**(c) But there *is* a residual rendering path, and it is not in the current block — it is in
the accumulated history.** Decoding the actual t15 prompt: the prompt contains **16 copies of
the rules block** occupying **3,811 of 10,994 tokens (34.7%)**, of which **7 still carry the
uncomposed delivery imperative**, the last at offset 27,954:

```
…,"key":"delivery","kind":"process","text":"Workshop obligation: delivery must be ready. delivery ready = trailer delivery=ready when verbose and scoped","value":"ready","version":0}]
```

The current block starts at offset 40,494; the last stale delivery row sits 12.5k tokens
earlier. Amendment 4 composed the *view*; it did not and cannot retro-compose the *context*.
Every R compact prompt in the run carries 4–8 such stale rows. So the honest answer to your
question is: **the composed block is correct, but this is not "pure" history-copying — R is
copying its own trailer out of a history that also still contains seven uncomposed delivery
imperatives.** N's history contains none, which is one reason N is the cleaner arm here.

**(d) A third driver is arm-invariant and untouched: the system prompt.** `slab2.py:71-73`:

```
"One worked shape example for task A requesting core.py in verbose format:\n"
"```python core.py\n# core.py\ndef identity(x):\n  return x\n```\n"
"report: task=A status=ok delivery=ready\n\n"
```

Q proves this is causal. Q has **no history, no tombstones, and a fully composed block** — I
checked `local/main/slab2-dev-06/Q/q-12.jsonl` and `q-13.jsonl`: no delivery row, and the block
literally says `format compact = trailer omits delivery`. Q still emits `delivery=ready` at
dev-06 t12–15 and at **33 of 34** compact cells overall (format adherence **1/35**). With the
delivery row removed and no history, the only remaining `delivery=ready` in Q's context is the
system prompt's verbose worked example. Note the direction: Q's compact format adherence went
**11/34 → 1/34** across the fix. Removing the delivery row did not help the arm that has nothing
else to go on; it removed the one place the guard clause ("when verbose and scoped") appeared.
Q's rendering changed in three ways at once, so I cannot isolate the cause to the composition
alone — but the residual attractor is unambiguously the system prompt, not the register.

---

## 3. THE PRIMARY RESULT

I re-implemented the endpoint **independently**, from the registration prose at
`registration.md:21-34`, without reading `slab2_endpoint.py` first, and then diffed. My
implementation reproduces every published figure exactly.

### 3.1 The numbers

| family | R | N | T | Q | paired eps | wins/losses/ties | one-sided p | Holm | mean gain | PASS |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| indent (style) | 10/15 | 11/16 | 12/16 | 5/16 | 8 | 1/1/6 | 0.750000 | 1.000000 | −0.0625 | no |
| format | 7/8 | 8/8 | 4/8 | 0/8 | 8 | 0/1/7 | 1.000000 | 1.000000 | −0.1250 | no |
| **delivery (process)** | **8/8** | **1/8** | 7/8 | 8/8 | 8 | **7/0/1** | **0.0078125** | **0.0234375** | **+0.875** | **yes** |

Exact test, checked by hand: 7 discordant episodes, all in R's favour, H1 `R>N`, so
p = P(X ≥ 7 | n = 7, p = ½) = 1/2⁷ = **0.0078125**. Holm step-down over three predeclared
families: 3 × 0.0078125 = **0.0234375** ≤ .05; the other two adjust to 1.0 with the
monotonicity constraint (`slab2_endpoint.py:123-128`). Correct.

### 3.2 Episode-level pairing, and averaging before the sign

Confirmed at `slab2_endpoint.py:94-106`: for each episode the R values and the N values over the
**common measured events** are averaged as `Fraction`s first, and only then does one signed
difference enter the sign test (`_sign`, `slab2_endpoint.py:48-59`). One episode, one sign.
`n = 8` in every family. For `delivery` there is exactly one change event per episode, so the
episode average is that single event — no pseudo-replication, and no dilution.

### 3.3 No outcome-dependent rematching

`change_rounds` (`slab2_endpoint.py:16-45`) reads **only** `episode.turns`, `t.events` and
`t.live`. It takes each `supersedes/completes/cancels/reinstates` event, walks forward to the
first round where the family is applicable, `break`s, and never looks past the next effective
change. No model output, no record, no outcome enters the selection. The schedules are
deterministic functions of the frozen generator seed. I re-derived them from `s.bank()` and got
the same rounds the summary reports.

The only outcome dependence anywhere is the registered `written` gate
(`slab2_endpoint.py:89-92`), and it is registered explicitly ("A paired event is measured only
when both R and N parse and write at that scheduled round") **and** shipped with its own
sensitivity: the strict "missing write = 0" variant gives **identical** results in all three
families (`summary.json` `strict_failed_attempts`, which I reproduced). There is exactly one
missing pair in the whole run (indent, dev-04 t12, R's single non-write) and it does not move
anything.

### 3.4 Is the effect real, or an artifact? Four artifacts ruled out

**(a) "R just always says `ready`, and completion always targets `ready`."** Ruled out
decisively. Over all 49 delivery-applicable rounds, split by what the register requires:

| arm | required = `ready` (post-completion) | required = non-default (`staged`/`queued`/`draft`) |
|---|---:|---:|
| R | **11/11** | **38/38** |
| Q | 11/11 | 38/38 |
| T | 10/11 | 38/38 |
| N | **2/11** | **38/38** |

R emits the *non-default* value correctly on all 38 rounds where the register says so. It is
tracking the rendered live value, not defaulting. **N's entire deficit is confined to the 11
post-completion rounds**, where it keeps emitting the retired value. That is exactly the
"release a retired rule" claim, and it is where the register wins.

**(b) Scoring asymmetry.** `slab2.py:637`: `delivery = report.get("delivery") == rules.get("delivery")`.
Same predicate for every arm; no breakage conjunction, no trait-set difference. The pilot-6
H2/H3/M5 defects are all fixed and tested (`tests/test_focus_slab2_amendment4.py:103-121`
asserts breakage-independence, empty-diff indent failure, and
`set(satisfied) == TRAITS == {language, indent, format, delivery}`).

**(c) N never sees the instruction.** No — the completion prose is in N's own context, in the
user message at the change round, including the new value:
`"…Retired; use default delivery ready = trailer delivery=ready when verbose and scoped"`. N has
the information and does not act on it. The user text is byte-identical across R, N and T.

**(d) Run noise.** 7/8 episodes in one direction, zero in the other, at a measured cross-run
divergence of 6% per cell. Not noise.

### 3.5 Is it the right effect to power the larger test on? Yes, with two honest caveats

**Yes.** It is the register's core claim, it is deterministic in structure (exactly one
`completes:delivery` event per episode → 64 paired episode observations at n = 64), the DEV
effect size is near-maximal (1.00 vs 0.125), and power at n = 64 is essentially 1 even if the
gap halves. It is also the only family that is *about* the register rather than about output
formatting.

Caveat 1 — **the credit belongs to "the current effective value is restated at request time",
not to the register data structure per se.** T, which gets a plain oracle prose line, scores
7/8 on the same endpoint. The right positive framing is: *the register recovers the oracle's
effective value from the event stream with no oracle, and matches oracle performance (8/8 vs
7/8), while plain history fails (1/8)*. The 64-run must not be reported as "registers beat
prose"; the registered contrast is R vs N and T is descriptive.

Caveat 2 — **the design is one-sided and therefore cannot report harm.** R's mean paired gains
on `format` (−0.125) and `indent` (−0.0625) are negative. Under the registered rule
(`slab2_endpoint.py:128` + `primary_evidence = any(pass)`) the 64-run will report
"primary evidence" on `delivery` while the other two families can only ever return
"no evidence". Both directions must be printed in the headline, as pilot 7 correctly does.

---

## 4. READINESS

**Projection — confirmed.** `slab2_endpoint.py:144-155` implements the registered formula
exactly. From `summary.json` `lane_seconds` (Q 82.3345, R 106.9550, N 96.3614, T 89.9621) and
`load_seconds` 497.4678:

```
(497.4678113460541 + 1.25*(64*(106.95503854006529 + 96.3614319190383 + 82.3344509229064)
                          + 16*89.96212818473577)) / 3600
= 6.985773357111547 GPU-h   (= 25,149 s)
```

Decomposition: startup 0.1382 + R 2.3768 + N 2.1414 + Q 1.8296 + T 0.4998. Lane seconds
reconcile with `main-groups.json` group totals ÷ 8 to 1e-4 s. At the report's own ~4% timing
noise the projection is 6.99 ± 0.28; even +30% leaves 9.1 h against the 12 h gate. **Confirmed,
with wide margin.**

**O's omission — justified.** `renderer.py:115-121` routes `rule_mode == "O"` through the `"R"`
branch with no text change, so O is byte-identical to R **by construction**, and pilot 6 measured
it: 128/128 identical `output_sha256`, identical `output` text, identical `prompt_tokens`.
Dropping it saves 0.587 projected GPU-h and loses no science. One caveat: O was the run's only
internal replication receipt. Since I have now shown that the *interesting* replication question
is cross-run (6% divergence) and O could never have answered it (O is same-run), the right
replacement is a registered cross-run control, not O. See the freeze list.

**`delivery_scope` removal — confirmed in code.** `slab2.py:59-64` `TRAITS` is
`{language, indent, format, delivery}`. `grep -rn delivery_scope src/ scripts/` returns nothing;
the only hits are a test asserting its absence and two frozen fixtures. Q is scored with
`eligible_traits=tuple(s.TRAITS)` (`composition_pilot5.py:253`) — now the same four traits as
R/N/T — and every measured quantity in the primary and the compact control reads
`outcome["satisfied"]`, which is trait-set independent anyway. Pilot-6 H3 is closed.

**Q's re-labelling — confirmed.** `summary.json` `arm_roles.Q = "fresh-context reference"`;
`registration.md:36-37` and `README.md:33` both state gold prerequisites, no feedback, "never a
ceiling". `run_q` (`composition_pilot5.py:186-266`) is as described: fresh `Session`, gold files,
register rebuilt as version-0 defaults, lifecycle prose stripped, no history.

**Vacuous-widths fix — confirmed in code and test.** `slab2.py:627-632`:
`indent = written and bool(widths) and all(w == int(rules["indent"]) for w in widths)`. The
`bool(widths)` guard closes pilot-6 M5, and
`tests/test_focus_slab2_amendment4.py:120` asserts an empty changed-diff now **fails** indent.
Breakage de-conjunction (`language = written`, no `not breakage`) closes H2.

**Other readiness items verified:** 512 complete records; D = 0/8; round-0 8/8 and lanes 8/8 in
every arm; caps 0; max prompt 10,994 + 2,048 = 13,042 < 32,768; strict T floor eligible on four
traits with 8 opportunity episodes each (indent 74.4%, delivery 98.0%, both ≥ 50%); primary
computable in 3/3 families and in 8/8 episodes with ≥2 nonzero paired families; GPU held
3,533.4/5,400 s; all 24 registered artifacts `git ls-files`-tracked; container stopped and
removed and own flag absent per `audit.json`; data-lineage line present and accurate
(fit-on none; DEV only; no benchmark content).

---

## 5. BOTTOM LINE FOR BRIAN — five lines

1. **`INELIGIBLE` is correctly applied as registered — and the gate it failed is not a valid
   instrument:** all four residual cells are one locked episode (dev-06 t12–15, R's own trailer
   copied forward with no register event at t14/t15), the no-block control N scores 3/34 against
   a limit of 2, McNemar R vs N is **p = 1.0**, and at the registered episode unit R and N are
   **1/8 each**.
2. **The fix works, and the CPU control proves it deterministically:** 35/35 saved registers
   re-render with no delivery row and no `trailer delivery=` string, 17,126 → 8,412 tokens, and
   behaviourally R went 25→4 emissions and 9/34→30/34 format on the same fixed cells (6/8→1/8
   episodes, p = 0.031); what remains is (i) R copying itself out of history and (ii) two
   uncomposed sources Amendment 4 never touched — 7 stale delivery rows still sitting in R's
   accumulated context (34.7% of the t15 prompt is old block copies) and the system prompt's
   verbose worked example at `slab2.py:71-73`, which alone drives Q to 33/34.
3. **The primary is real, correctly analysed, and I reproduced it from scratch:** delivery
   R 8/8 vs N 1/8, 7–0, exact one-sided p = 0.0078125, Holm 0.0234375; paired at the episode
   level with within-episode averaging before the sign; change rounds selected from the frozen
   schedule with zero outcome dependence; and the "R just always says ready" artifact is dead —
   R is 38/38 on the rounds where the register demands a **non-default** value while N is also
   38/38 there and only 2/11 after the completion.
4. **A further DEV re-pilot is not genuinely required and would be actively wasteful:** this
   harness is only ~94% reproducible across container restarts (10/166 byte-identical requests
   returned different completions; N's own compact score moved 0/34→3/34 with no code change
   affecting it), every compact window is 4–5 rounds so one locked episode always exceeds the
   limit, and P(clearing `≤2/34` again) ≈ (7/8)⁸ ≈ **0.34** — a one-in-three coin flip costing
   ~1 GPU-h to re-roll a gate the control arm fails.
5. **Authorize the 64-episode test now under a registered Amendment 5, on the delivery family of
   the per-obligation change-round endpoint, at 6.99 projected GPU-h (limit 12) — do not
   re-pilot.**

### Pre-registration items that must be frozen before launch

1. **Amendment 5, registered and committed before any container starts**, stating the reason the
   pilot-7 gate is superseded (control-arm calibration + episode unit + measured cross-run noise)
   and attaching this review's numbers.
2. **Instrument-health gate restated:** the *blocking* check on the composition fix is the
   deterministic CPU re-render control — 100% of scheduled compact registers must render with no
   `delivery` row and no `trailer delivery=` substring. Behavioural compact-trailer counts are
   reported at the **episode** level, descriptively, alongside N as the calibration arm. No
   round-level behavioural threshold.
3. **Unit declaration made global:** "the episode is the unit of analysis for every inferential
   and gating statement; round-level counts are descriptive only."
4. **Primary frozen exactly as Amendment 4 defines it**, at an unchanged model-facing pin
   (`24ed80a4` or a successor whose `renderer.py`/`slab2.py`/`loop.py`/`register.py` bytes are
   identical), with `delivery` named the powered family in advance.
5. **A `larger_reading()` implemented in code with tests**, mirroring `pilot_reading`: family
   PASS iff Holm-adjusted p ≤ .05 **and** positive mean paired gain; overall primary evidence iff
   ≥1 family PASS; all three family directions printed; no joint-final or Q-subset gate. Prose
   alone is not a frozen reading.
6. **The 64-episode evaluation bank frozen by id list + hash** before launch (`bank(family="eval")`,
   64 unique ids), with the data-lineage line: fit-on none; developed-on the 8 DEV episodes
   (thresholds included); evaluated-on the 64 template/seed-disjoint eval episodes; no benchmark
   content or responses.
7. **A registered cross-run reproducibility control**, since none exists: replay a fixed set of
   ≥16 saved prompts in a **second** container after the main run and report the fraction of
   byte-identical completions. Declare in advance that all round-level counts carry that noise.
   (Cost: minutes. This replaces the diagnostic value lost by dropping O.)
8. **Pre-declared known confounds, named in the registration so they cannot be discovered later:**
   the system-prompt worked example (`slab2.py:71-73`) is an arm-invariant `delivery=ready`
   attractor; R's accumulated history retains uncomposed delivery rows (`loop.py:363`); and T's
   oracle line is **not** composed (`slab2.py:348-350`), so T's format column is not comparable
   with R's.
9. **Budget:** registered formula, projection ≤ 12 GPU-h recomputed from measured lane seconds
   before launch, and an actual GPU-held cap (25,149 s projected; I suggest registering
   ≤ 32,400 s) with the existing no-fallback rule.
10. **Arms:** Q retained as fresh-context reference at 1.83 GPU-h; O dropped; T at ×16 as a
    descriptive oracle comparator.

---

## Findings

| # | Sev | Finding | Location |
|---|---|---|---|
| **C1** | **critical** | The blocking eligibility gate is mis-calibrated below its own negative control. `≤2/34` R compact `delivery=ready` emissions is stricter than the no-rules-block arm N achieves in this very run (3/34). R 4 vs N 3 → McNemar exact two-sided **p = 1.0000**; at the registered episode unit both arms are **1/8**. A gate the control arm fails cannot certify that a rendering contradiction was removed from the treatment arm. The threshold was set from pilot 6's N = 0/34, which was a single draw (see H1). | `slab2_endpoint.py:198-210`; `registration.md:55-58`; re-derived from `main-records.jsonl` |
| **H1** | **high** | **Cross-run nondeterminism is ~6% and was never measured.** 166 of 512 pilot-6/pilot-7 cells had byte-identical HTTP request payloads (identical prompt token ids, `temperature: 0`, `seed: 20260906`, same pinned image and flags); **10 of the 166 returned different completions** (6.02%, Wilson 95% CI 3.3–10.7%). Example `slab2-dev-00 T t0`: `return [v*6+3 for v in x]` (p6) vs `return x*6+3` (p7) — a lane-poisoning semantic error. N's own compact emissions moved 0/34 → 3/34 with no code change affecting N. The registered D = 0/8 gate is *within-container* only. No round-level threshold with a 2-cell margin on 34 cells is a reliable instrument in this harness. | `local/http/main/**/{0..15}.json` (both pilots); `determinism.json`; `launch.json` |
| **H2** | **high** | Registered unit inconsistency. `registration.md:21` declares the **episode** the unit of analysis for the primary; `registration.md:55-58` then gates eligibility on a **round** count of the same phenomenon. The four failing rounds are one locked episode: t14 and t15 carry **no register event at all** (bare task prose) and identical live rows, while R's prompt at t15 contains four literal copies of its own wrong trailer. 0 recoveries in 5 opportunities across R and N. | `registration.md:21` vs `:55-58`; `slab2_endpoint.py:198-210`; `local/main/slab2-dev-06/R/loop.jsonl` records 11–15 |
| **H3** | **high** | The composition fix was applied to the **live view only**; R's accumulated context still carries uncomposed delivery imperatives. At `slab2-dev-06` R t15 the 10,994-token prompt holds **16 copies of the rules block = 3,811 tokens (34.7%)**, of which **7 still contain** `"key":"delivery" … "delivery ready = trailer delivery=ready when verbose and scoped"` (last at offset 27,954; the current, clean block starts at 40,494). Every R compact prompt carries 4–8 such stale rows. This is a rendering-derived contradiction that survives Amendment 4 and exists only in the register arms. | `renderer.py:76-90` (fix) + `loop.py:363` (accumulation); decoded `local/http/main/slab2-dev-06/R/15.json` |
| **M1** | medium | T's oracle line is **not** composed. `slab2.py:348-350` builds `t_text` from `sorted(effective.items())` with `literal(k, v)` for every key, so under compact T still reads `Effective obligations: delivery ready = trailer delivery=ready when verbose and scoped; format compact = trailer omits delivery; …` — the exact contradiction removed from R at `renderer.py:89`. T is now the worst behavioural arm on compact format (12/35 emissions, 19/35 adherence) for a reason that is an arm-specific renderer asymmetry. Any R-vs-T format comparison is confounded. `t_text` is baked into the frozen episode schedules, so fixing it changes the bank; the cheap remedy is to say so in the registration. | `slab2.py:348-350`; `composition_pilot5.py:42`; `local/main/slab2-dev-06/T/loop.jsonl` records 12–15 |
| **M2** | medium | The residual `delivery=ready` attractor is the **system prompt**, and it is untouched. `slab2.py:71-73` ends its worked example with `report: task=A status=ok delivery=ready`. Q — fully composed block, zero history, zero tombstones — emits `delivery=ready` in **33/34** compact cells (format adherence **1/35**), and Q's compact adherence moved **11/34 → 1/34** across the fix, i.e. removing the delivery row made the no-history arm worse. Every arm receives this prompt, so it depresses R's and Q's format family in the 64-run. | `slab2.py:71-73`; `local/main/slab2-dev-06/Q/q-12.jsonl`, `q-13.jsonl`; `summary.json` `per_arm.Q.all_compact` |
| **M3** | medium | Dropping O removes the run's only internal replication receipt, and nothing replaces it — while the *material* replication question (cross-run, H1) has never been controlled at all. O could not have answered it (O is same-run and byte-identical by construction at `renderer.py:115-121`), so the fix is a registered second-container replay, not re-adding O. | `renderer.py:115-121`; `registration.md:38-40` |
| **M4** | medium | The larger-test PASS rule exists only as prose (`registration.md:31-36`). `slab2_endpoint.py` implements `pilot_reading` for DEV but no `larger_reading`. The DEV gate's credibility came precisely from being frozen in code and asserted against the summary (`report.py:26-35`); the 64-run needs the same. | `registration.md:31-36`; `slab2_endpoint.py:168-232` (no larger-test counterpart) |
| **M5** | medium | The registered design is one-sided (`alternative="R>N"`, `_sign` computes `P(X ≥ wins)`), so it can return "register helps" or "no evidence" but never "register hurts" — while R's DEV mean paired gains are **negative** on format (−0.125) and indent (−0.0625). Not hidden (both are printed), but the headline `primary_evidence: True` must never be reported without the other two directions. | `slab2_endpoint.py:48-59`, `:128-134`; `README.md` primary table |
| **L1** | low | `renderer.py:92` still emits `Active rules for this request (subject to system/developer instructions)`, explicitly subordinating the live rules to the system prompt whose worked example is the M2 attractor. Only R/Q carry this clause. Pilot-6 L1 unaddressed. | `renderer.py:92`; `slab2.py:71-73` |
| **L2** | low | `computable_episodes` pairs families to episodes by **list position** (`f["episodes"][i]` over `range(len(episodes))`), relying on dict insertion order to align three independently built detail lists. Correct today; fragile if the schedule dict is ever rebuilt. Prefer keying by `episode_id`. | `slab2_endpoint.py:136-140` |
| **L3** | low | The governing module docstring still describes the superseded five-arm Amendment-3 design ("R/N x64 plus nested O/T x16 and fresh-task Q x64", "R final >=5/8"), which Amendment 4 replaced. A reader resuming from source gets the retired spec. | `slab2.py:12-16` |
| **L4** | low | Scoring path asymmetry survives: `run_q` passes `eligible_traits=tuple(s.TRAITS)` (`composition_pilot5.py:253`) while `run_lane` passes `None` (`:172`), so `success`/`relapse` are populated for Q and not for R/N/T. Now cosmetic — every reported quantity reads `outcome["satisfied"]`, which is trait-set independent, and `report.py:40-49` computes joint-final uniformly — but the asymmetry is a trap for the next reader. | `composition_pilot5.py:172` vs `:253` |

## Not findings — checked and cleared

* Every number in `README.md`, `summary.json`, `main-floor.json` and `report-audit.json`
  reproduces exactly from the records. No arithmetic error anywhere.
* The 34-cell control set was frozen in the amendment commit (03:10:33) and is unchanged;
  `registration.md` was written 7 s before the container launched; the reading function was
  committed before the run and the only post-run `report.py` edit is presentational. **No
  outcome-dependent rematching and no post-hoc gate movement.**
* The primary endpoint's change-round selection is a pure function of the frozen schedule; the
  strict "missing write = 0" sensitivity is identical in all three families.
* Saved-response audit: I independently re-verified all 512 records against their HTTP receipts
  (text, token counts, truncation, both hashes, prompt tokens) — 0 mismatches. 40/40 sampled
  local hashes verified; 1,040 files present and hashed; 512 journal-index lines.
* The registered CPU suite is green on the live tree: **135 passed, 1 xfailed** — the exact
  figure claimed in `registration.md` and `cpu-validation.log`.
* Pilot-6 findings H1 (composition), H2 (breakage conjunction), H3 (`delivery_scope` in Q's
  rubric), M1 (provenance/scope metadata), M2 (run-on style gloss), M3 (tombstone retargeting),
  M5 (vacuous empty-diff indent pass) and L2 (dangling retired header) are all closed in code,
  and each has a regression test in `tests/test_focus_slab2_amendment4.py`.
* Cost accounting: the formula matches the registration byte for byte, Q is charged at ×64, and
  the ≤12 GPU-h gate passes at 6.9858 with ~70% headroom.
* No fitting, selection or tuning on evaluation content is visible. The pilot ran
  `family="dev"` only; the ≤2/34 and ≥26/34 thresholds were set from pilot-6 **DEV** results
  before pilot 7 launched, which is permitted development use — the error was calibration, not
  contamination.
* Backend: same pinned vLLM digest, `TRITON_ATTN`, `VLLM_BATCH_INVARIANT=1`,
  `--max-num-seqs 4`, cap 2048, `temperature 0`, `seed 20260906`; `system_sha256` identical to
  pilot 6; within-run determinism exact. The only backend finding is H1, which is about
  container restarts, not about this run's internal consistency.
