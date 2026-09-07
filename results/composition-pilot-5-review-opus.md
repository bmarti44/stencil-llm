# Composition pilot 5 — independent accuracy review (Opus, 2026-09-07)

Reviewer: independent accuracy reviewer under Brian's 2026-09-06 ruling. One round, no code
edits, CPU only. Nothing under `data/bench` or the evaluation bank was opened; all episode
content read here is authored DEV (`slab2-dev-00..07`), which the pilot's own lineage record
marks as development-only.

**Disposition: INELIGIBLE stands.** Every headline number in
`results/quick-checks/composition-pilot-5/README.md` reproduces exactly from the records.
**But the README's account of *why* is wrong in emphasis. The headline a reader takes away —
"the rendered register block executes 63/128 against plain history's 112/128" — is an
INSTRUMENT artifact and must not be reported as a register effect. Separately, the artifact
does contain a real, matched, underpowered signal that the README does not report at all,
and it points the same direction: on the 9 rounds where all three arms produced a valid
file after a rule change, R complies with the new indent 0/9 while N and T comply 8/9.**

---

## 0. What reproduced exactly

Recomputed from `main-records.jsonl` (512 lines = 4 arms x 8 episodes x 16 rounds), not from
the report:

| Claim | README | Recomputed | Status |
|---|---|---|---|
| Parsed+written per arm | 63 / 112 / 104 / 63 | 63 / 112 / 104 / 63 | exact |
| Caps | 0/128 all arms | no record has `truncated=true`; max reply 776 < cap 1024; all 512 `eos=151645` | exact |
| Largest reply | 776 / 738 / 598 / 776 | same | exact |
| Output tokens | 36079 / 31784 / 31854 / 36079 | same | exact |
| Model/reference x | 1.352 / 1.191 / 1.194 | 36079/26686=1.3520, 31784/26686=1.1910, 31854/26686=1.1937 (reference total recomputed with the pinned tokenizer) | exact |
| Final success /8 | 0 / 4 / 3 | 0 / 4 / 3, recomputed from `outcome.diagnostics` and `floor.eligible_traits` | exact |
| T floor table | 72/128, 13/128, 22/35, 42/49, 0/44 | identical; `eligible_traits=[language,format,delivery]` | exact |
| Relapse table (20 rows) | as printed | all 20 numerators, denominators and prior-present counts identical | exact |
| Projection | 7.774 GPU-h | 27988.158622622492/3600 = 7.774488506284026 | exact to 1e-9 |
| GPU held | 4869.993/5400 s (81.17 min) | `lifecycle.json` 4869.9926381111145 | exact |
| Overhead | 9.022 s over 32 lanes | 4869.9926 - 494.2840 - 29.7773 - 4336.9089 = 9.0225 | exact |
| R/O output identity | 128/128 | 128/128 outputs **and** 128/128 byte-identical prompts | exact |

Provenance re-derived, not taken on trust: I replayed 7 full lanes (112 rounds) through the
pinned `run_lane` with the real Qwen tokenizer and compared the reconstructed
`rendered.prompt_ids` against the recorded HTTP request payloads — **0 mismatches** — and
every `execution` / `outcome` / `output_ids` / `prompt_tokens` field reproduced. The pinned
tree `/tmp/stencil-pilot5-pinned` is at `9f0c6d27f32815010c81a02d3959102459c55e8f`, clean,
and byte-identical to `git show 9f0c6d27:src/stencil/focus/{slab2,renderer,loop}.py`. The
launch command matches `results/quick-checks/vllm-qual/attempts.json[0].command` in all 36
argv positions except `--name` and the host port. `RUNNING.flag` is gone, no
`stencil-pilot5-*` container survives, no RUNNING.flag exists anywhere under `results/`.

---

## 1. The central question: the 65 R non-executions, cause by cause

### 1.1 Structural classification of all 105 R/N/T non-executions

Classified by the structure of the literal reply, not by the harness label:

| cause | R | N | T |
|---|---:|---:|---:|
| empty reply | 0 | 0 | 0 |
| no fenced block at all | 0 | 0 | 0 |
| unterminated single fence | 0 | 0 | 0 |
| prose before the fence | 0 | 0 | 0 |
| model answers the rendered rules instead of emitting a file | 0 | 0 | 0 |
| fence present, trailer missing or malformed | 0 | 0 | 0 |
| **two complete fenced blocks (fence count 4)** | **32** | **16** | **16** |
| **odd fence count 3 (path line, then a re-opened fence)** | **31** | 0 | 0 |
| three complete fenced blocks (fence count 6) | 1 | 0 | 0 |
| parsed, but Python syntax error, so no file written | 1 | 0 | 8 |
| **total** | **65** | **16** | **24** |

Not one reply lacks a fence, is empty, puts prose first, or answers the rules. Every
`fence_count_or_kind` failure in every arm is **too many fences**. `execution.tolerances`
across all 512 rounds contains only `blank_before_trailer` — no `leading_prose`,
`leading_think`, `crlf` or `report_case` label appears anywhere in the run.

### 1.2 The failures are decided at round 0 and locked — the metric is 8 trials, not 128

Per-episode, per-round (`W` written, `F` fence failure, `S` syntax error, turns 0..15):

```
R  dev-00 FFFFFFFFFFFFFFFF   N  dev-00 WWWWWWWWWWWWWWWW   T  dev-00 WWWWWWWWWWWSSSSS
   dev-01 WWWWWWWWWWWWWWWW      dev-01 WWWWWWWWWWWWWWWW      dev-01 WWWWWWWWWWWWWWWW
   dev-02 WWWWWWWWWWWWWWWW      dev-02 FFFFFFFFFFFFFFFF      dev-02 WWWWWWWWWWWWWWWW
   dev-03 FFFFFFFFFFFFFFFF      dev-03 WWWWWWWWWWWWWWWW      dev-03 WWWWWWWWWWWWWWWW
   dev-04 WWWWWWWWWWWWSWWW      dev-04 WWWWWWWWWWWWWWWW      dev-04 WWWWWWWWWWWWWWWW
   dev-05 FFFFFFFFFFFFFFFF      dev-05 WWWWWWWWWWWWWWWW      dev-05 FFFFFFFFFFFFFFFF
   dev-06 WWWWWWWWWWWWWWWW      dev-06 WWWWWWWWWWWWWWWW      dev-06 WWWWWWWWWWWWWWWW
   dev-07 FFFFFFFFFFFFFFFF      dev-07 WWWWWWWWWWWWWWWW      dev-07 WWWWWWWWWWWWWSSS
```

**No fence failure ever occurs after a clean round 0, and no lane ever recovers from one.**
0 recoveries in 96 locked rounds. The 105 non-executions arise from **9 initiating events
across 24 lanes**: 6 round-0 fence draws (R 4, N 1, T 1), 2 T syntax onsets (dev-00 t11,
dev-07 t13), 1 transient R syntax error (dev-04 t12, recovered the next round). The other
**96 are deterministic repeats**.

The mechanism is self-imitation. `loop.py:363` appends the previous rendered prompt *and the
previous assistant reply* to `history_ids`, so from round 1 the model copies its own round-0
layout. The only counter-signal is the failure feedback at `slab2.py:556-561`, which is
opaque:

```json
{"breakage":true,"category":"fence_count_or_kind","error":"fence_count_or_kind",
 "executed":false,"failed":0,"functions":{},"passed":0,"tolerances":[],"truncated":false}
```

Nothing there restates the required shape. The lane cannot escape.

Decoding is `temperature=0, seed=20260906` under `VLLM_BATCH_INVARIANT=1`
(`composition_pilot5.py:48-56`), so each lane is one deterministic trajectory. The correct
unit of analysis is the episode lane, n=8 per arm.

**Episode-level round-0 fence failure: R 4/8, N 1/8, T 1/8. Fisher exact two-sided p = 0.282
(R vs N), 0.282 (R vs T), 0.129 (R vs N+T pooled).** The 63-vs-112 headline is a 4-vs-1
comparison multiplied by 16.

### 1.3 Five R non-executions with the paired N reply, same episode and round

**(a) dev-00 t0.** R (4 fences, 107 tok). The request is "Extend workshop B: add step_0(x)
in policy.py":

~~~
```python
# policy.py
def step_0(x):
    """Map each integer v to v * 6 + 3, preserving order."""
    return [v * 6 + 3 for v in x]
```

```python
# core.py
def step_0(x):
    """Map each integer v to v * 6 + 3, preserving order."""
    return [v * 6 + 3 for v in x]
```

report: task=A status=ok delivery=ready
~~~

N, same episode and round (written, 59 tok):

~~~
```python
# policy.py
def step_0(x):
    """Map each integer v to v * 6 + 3, preserving order."""
    return [v * 6 + 3 for v in x]
```
report: task=A status=ok delivery=ready
~~~

**(b) dev-03 t0.** R (3 fences, 60 tok) — path on its own line, fence re-opened:

~~~
```python
core.py
```python
def step_0(x):
    """Sum values strictly above 6, then add 7."""
    return sum(n for n in x if n > 6) + 7
```

report: task=A status=ok delivery=ready
~~~

N (written, 62 tok) is `` ```python `` / `# core.py` / body / fence / trailer. **The only
structural difference between the failing and passing layout is the `# ` before the
filename.**

**(c) dev-05 t0.** R (4 fences, 81 tok) — invents a second file:

~~~
```python
# core.py
def step_0(x):
    """Check if count >= 2 and enabled is true."""
    return x["count"] >= 2 and x["enabled"]
```

```python
# policy.py
def policy(x):
    """Policy function for workshop A."""
    return step_0(x)
```

report: task=A status=ok delivery=ready
~~~

N (written, 53 tok): the single `# core.py` block plus trailer.

**(d) dev-07 t3.** R (3 fences, 174 tok): `` ```python `` / `policy.py` / `` ```python `` /
four `step_*` defs / fence / trailer — the same re-opened-fence shape as (b). N on that
round: single `# policy.py` block, written, 188 tok.

**(e) dev-05 t9.** R (4 fences, 433 tok) still emits the invented
`def policy(x): """Policy function for workshop A."""` block nine rounds later, verbatim
lock-in. N on that round: single `# policy.py` block, written, 161 tok.

**(f) dev-00 t15**, for the lock-in: R's reply is still exactly two blocks (`core.py` then
`policy.py`), 776 tokens — the largest reply in the run, and the source of the README's
"largest reply" column for R.

### 1.4 The same failure mode occurs in every arm, and R wins where N loses

N dev-02 t0 (`fence_count_or_kind`, 4 fences) is the identical mode: a `# policy.py` block,
then a `# core.py` block with the same body, then the trailer. **R on that same
episode/round succeeded** (2 fences, written). T dev-05 t0 fails the same way while N
dev-05 succeeds. The mode is arm-independent and the effect is not monotone in the register.

### 1.5 Where the mode comes from

`slab2.py:63`, the system prompt, identical in all arms:

~~~
"containing the WHOLE requested file: ```python core.py or ```python policy.py, "
~~~

One sentence containing two fence openers and both filenames. Every observed failure is a
duplication of exactly that pattern — two blocks, one per named file, or an opener followed
by a bare path followed by a second opener. The register block adds ~350 tokens ahead of it
and flips the greedy choice in 4 of 8 lanes; N's shorter prompt flips it in 1 of 8; T's in
1 of 8.

---

## 2. R vs N prompt diff

Reconstructed from the pinned renderer and verified byte-for-byte against the recorded HTTP
payloads.

**What R adds, and where.** `renderer.py:100-131` prepends to the *user* envelope, ahead of
everything the user actually said:

1. `Active rules for this request (subject to system/developer instructions):`
2. one line of compact JSON — the live rules as objects with
   `key/version/kind/value/text/scope/provenance/default` (1445 characters at dev-00 t0)
3. `Retired rules (not binding):` and the retirement lines — **empty, with a blank line, at
   round 0** (`renderer.py:110`)
4. `Apply the active rules while answering the request below.`
5. `Current user request:` then the ordinary user payload.

N (`renderer.py:132-133`) gets item 5's payload only. T (`renderer.py:134-135`) gets one
prose line (`Effective obligations: ...` / `Not binding: ...`) then the same payload.

**Yes, it is rendered on tool continuations.** `render()` runs on every request, and
`loop.py:244-273` folds the tool result into `request.text`, so the harness feedback appears
*inside* the register-prefixed envelope, after `Current user request:`. And `loop.py:363`
puts every rendered prompt into `history_ids`, so by round 15 R's context carries **16 copies
of the block**. Measured: R total prompt tokens 835,742 vs N 387,314 (**2.16x**); R round-15
mean 13,806 vs N 6,707; R max 16,933 of a 32,768 window.

**Anything in it that competes with the output-format instruction?**

- **No fences.** There is not a single backtick in any R register block across the 32 rounds
  I reconstructed. The two-block failure is not fence contamination from the prompt.
- **Yes, for the trailer.** `register.py:420-424` appends configuration defaults *after* the
  explicit rules, so the `delivery` default is always the **last** row, sitting immediately
  before `Apply the active rules while answering the request below.` At dev-01 t12 the block
  ends with

  ```json
  {"default":true,"key":"delivery",...,"text":"Workshop obligation: delivery must be ready.
   delivery ready = trailer delivery=ready when verbose and scoped","value":"ready","version":0}
  ```

  while the *first* row says `format compact = trailer omits delivery`. T renders the same
  two facts alphabetically, delivery first and format second. R relapses on `format` in
  **16/16** opportunities (4/4 episodes); T in **4/23** (1/6); N in **5/31** (2/7).
  Episode-level Fisher: R vs T p=0.048, R vs N p=0.061.
- More generally the block makes rule **values** salient and rule **negations** invisible:
  `delivery=ready` is a value in the last row, `trailer omits delivery` is a clause inside
  the first row's prose. §5.2 shows R emits the value and drops the omission on matched data.
- Amendment 2's `value_gloss` (`renderer.py:19-23`) duplicates the indent sentence in the R
  block only: `"indent 3 = block bodies indented by exactly 3 spaces per level indent 3 =
  block bodies indented by exactly 3 spaces."`
- Roughly 55% of the block is `scope:{"request_kinds":[],"task_handle":null}` and
  `provenance:{"message_id":"m0","role":"user","span":null}` noise.

---

## 3. Is the execution metric arm-neutral?

| definition | R | N | T | O |
|---|---:|---:|---:|---:|
| README/registration: parsed trailer **and** file written | 63/128 (49.2%) | 112/128 (87.5%) | 104/128 (81.2%) | 63/128 |
| pinned executor: `executed=True` set at `slab2.py:512`, before `ast.parse` | 64/128 (50.0%) | 112/128 (87.5%) | 112/128 (87.5%) | 64/128 |

**The exclusion is arm-neutral in direction and changes nothing material.** It moves R by 1
round, N by 0, T by 8. Ranking under the strict definition is N > T > R; under the pinned
definition N = T > R. All three arms fail the 90% gate either way (pooled R/N/T 72.7% vs
75.0%). R is worst under both. The strict definition is the conservative one and was
registered before the GPU ran. No finding here.

One divergence to record: `slab2.pilot5_reading` (`slab2.py:747`) computes execution from
`outcome.observed` — the inclusive definition — and was **never called**; `run.py:107-121`
implements its own gate. See F9.

---

## 4. R and O are byte-identical — expected, and no arm shared state

**Expected by construction.** `renderer.py:132-137` routes `rule_mode="O"` through the R
branch (only `"N"` and `"T"` are special-cased; `"R"` and `"O"` both fall through to the full
render). In DEV, `run_lane` feeds `turn.events` — gold events — for every arm
(`composition_pilot5.py:129`, `event_schedule is None`), so O's register state is R's. Same
prompt, same greedy decode, same output. **I verified all 128 R and O HTTP request payloads
are byte-identical, not merely the outputs.** The README's caveat ("DEV gold-event
equivalence, not learned-controller evidence") is correct and should be kept.

**No shared history or cache.** Each lane calls `Path(directory).mkdir(exist_ok=False)`
(`composition_pilot5.py:104`) under `local/main/<episode>/<arm>/` and constructs its own
`Session`, `Register`, `Journal`, `Executor` and materialized workspace. Arms ran in disjoint
windows (`run.log`: T 0-1410 s, R 1410-2685 s, N 2685-3623 s, O 3623-4862 s). vLLM
`--enable-prefix-caching` is on (94.7% hit rate) but is KV reuse, not a result cache; the
determinism gate (8 prompts, forward and reverse C4 order, concurrency 4) shows 0 mismatches,
and R≡O over 128 rounds at prompts up to 16,933 tokens, measured ~35 minutes apart, is a far
stronger batch-invariance receipt than the gate itself.

By-product: R and O are the **identical workload run twice**, and their measured lane costs
differ by 2.9% (159.55 s vs 155.09 s per episode). That bounds timing noise in the cost
measurement — and it means R's +35.7% wall over N (159.55 vs 117.60) is far outside noise and
**real**.

---

## 5. Verdict

**INELIGIBLE stands.** But the README names five failing gates as if they were five findings.
There are two blockers and one unreported result.

### 5.1 Blocker A (fixable, arm-neutral): an absorbing round-0 format lottery

96 of 105 non-executions are deterministic repeats of 9 events. All three arms trip it. The
system prompt supplies the failure mode (`slab2.py:63`). The tool feedback cannot correct it.
Per-round execution rates measured under this regime are uninterpretable for any arm
comparison.

### 5.2 The unreported result: R's compliance deficit on matched data

The one comparison in this artifact that is *not* contaminated by the lottery is the set of
rounds where **all three arms produced a valid file**: 47 matched cells across episodes 01,
04 and 06.

| trait | R | N | T |
|---|---:|---:|---:|
| indent (style) | **0/47** | 8/47 | 8/47 |
| format (omission) | **0/12** | 10/12 | 8/12 |
| delivery (value) | **19/19** | 15/19 | 18/19 |
| language | 31/47 | 31/47 | 31/47 |
| delivery_scope | 0/16 | 0/16 | 0/16 |

Restricting further to rounds after the relevant rule change with no breakage in any arm
(dev-01 t11-15 and dev-04 t11,13,14,15):

- **indent: R 0/9, N 8/9, T 8/9.** The one round all three fail is dev-04 t11.
- **format: R 0/8, N 7/8, T 8/8.**

This is real, matched, and independent of the fence artifact — but it rests on **2
discordant episodes**, so the episode-level sign test is p = 0.5 and it proves nothing on
its own. The mechanism is coherent with §2: R alone renders the obligations as JSON, R alone
gets the duplicated indent gloss, R alone puts the `delivery` value in the last row before
the instruction, and R alone dilutes the change line across a 2.16x longer prompt. Note the
direction on `delivery` is the opposite — R is best at emitting the correct *value*. The
plausible summary is that this serialization strengthens value recall and weakens style and
omission compliance. **That, not the execution table, is what deserves the next registered
test.**

### 5.3 Blocker B: the T floor's denominator, not model incapacity

I first read `indent 13/128` as the model being unable to follow a non-default width. That
is wrong, and the correction matters. Per-turn satisfaction among written rounds:

```
turns 0-10:  R 0/44  N 0/77  T 0/77
turns 11-15: R 0/19  N 20/35 T 13/27
```

Not one arm satisfies the indent obligation before turn 11; N and T comply readily after it.
The `supersedes indent` event fires at turn 10, 11 or 12 depending on episode
(`schedule["indent"] in {n-6,n-5,n-4}`); the two episodes whose event lands on turn 10
(dev-02, dev-06) are the breakage lanes, so they contribute no clean post-change round.
The model ignores a standing obligation stated once at turn 0 — even when T restates it in
prose every single round, and even when R renders it in JSON every single round — and
complies once a fresh *change* event names it. I verified none of the 33 passes is vacuous:
every one has real measured widths from non-empty changed code, matching the required value
(`indent_widths` returns `[]` for empty code and `all([])` is True, so this was worth
checking; it did not fire).

Consequence: `freeze_t_floor` puts all 128 T rounds in the denominator, ~11 of 16 per episode
being pre-change rounds the model was never going to satisfy, so `indent/style` can never
reach 50% and `kinds<2` fails by construction. This is a **floor-design defect**, not a model
limit and not a register effect. It is also the single most interesting scientific
observation in the run and the README does not mention it.

### 5.4 Is the R execution deficit REAL or INSTRUMENT? — INSTRUMENT

1. Identical failure mode in all three arms (§1.4).
2. R succeeds on dev-02 where N fails; N succeeds on dev-00/03/05/07 where R fails. Not
   monotone.
3. Correct unit is the lane: 4/8 vs 1/8, Fisher two-sided p = 0.282.
4. 0/96 recoveries — the per-round rate is a 16x amplifier on 6 draws.
5. The knife-edge is one token wide (`# core.py` passes, `core.py` on its own line fails).
6. Restricted to episodes where R executed, R final success is 0/4 vs N 1/4 (p = 1.0). The
   0/8-vs-4/8 headline is 3 lanes of lock-in plus 1 real loss.

The compliance deficit in §5.2 is a separate question and is not settled by this run.

### 5.5 Minimal registered fix, and its predicted effect

Three arm-symmetric changes, none touching a scoring definition:

1. **`slab2.py:62-64`** — replace the sentence that names both files behind two fence
   openers with one worked example showing a single opener carrying the path, using a filename that is neither `core.py` nor `policy.py`, and drop the `or` that
   names both files in one sentence. This changes `system_sha256` and must be re-registered.
2. **`slab2.py:556-561`** — on `ReplyError`, add one string field to the feedback restating
   the required shape and the observed fence count. The round still scores as a failure; the
   point is only to let a lane leave the absorbing state.
3. **Register the episode lane as the unit for the execution gate** (a lane is executable iff
   its round-0 reply parses), and report the per-round rate conditional on a clean round 0
   beside it.

**Prediction.** Round-0 fence failures go to 0/24 lanes. Execution: R ≈ 120-127/128,
N ≈ 127-128/128, T ≈ 118-124/128 — all three clear 90% and the execution gate passes.
(T keeps its two syntax-onset lanes; those begin at the indent supersede, where the model
starts indenting `def` lines as well as bodies.) R's real residual costs survive unchanged:
2.16x N's prompt tokens, +35.7% lane wall, and the §5.2 compliance direction. The `kinds<2`
gate still fails until the floor denominator is restricted to post-change rounds (§5.3).
**The right next step is a ~10 GPU-minute, 8-lane DEV screen of changes 1+2 — not a re-run of
the full pilot, and certainly not the 64-episode registered run.**

### 5.6 If it had been real

It is not. Had the execution deficit been real, the honest statement would be "rendering a
JSON register block ahead of the request degrades output-format compliance in this harness,"
and the larger test would have had to move the block out of the user envelope before any
composition claim. The artifact does not license that statement about *execution*. It does
raise it as an open question about *rule compliance* (§5.2), on 2 episodes.

---

## 6. The remaining verification items

### 6.1 T-floor procedure — correct as executed
`run_phase` iterates arms `TRNO` (`run.py:127`); `run.log` shows T's two C4 groups complete
at 928.9 s and 1410.4 s, before R starts. `freeze_t_floor` (`slab2.py:713`) hard-refuses
anything but all 128 unique DEV T rounds. `summarize` computes the floor only when
`len(byarm['T'])==8*n` and passes it to `rescore` (`composition_pilot5.py:338`) for success
scoring. The floor is therefore frozen from all 128 T records before any success was scored,
and never changes on later recomputes. I reproduced all five trait rows and `eligible_traits`
exactly. Restricting the two-kind gate to `('indent','delivery')` is exactly what
`registration.md` registered. The *denominator* is the problem (§5.3), not the procedure.

### 6.2 Zero caps — correct
No record has `truncated=true` at either level; the largest reply is 776 of a 1024 cap (24%
headroom); all 512 rounds ended on `eos=151645` (`<|im_end|>`). The audit's HTTP-level
assertion `row['truncated']==(finish_reason=='length')` covers this independently. The cap
never bound. Note the three largest replies in the run (776, 738, 736) are all lock-in
rounds, so "largest reply" is also measuring the artifact.

### 6.3 Projection arithmetic — correct; survives an R fix, in the favourable direction
Group walls sum to 4336.909 s; `(4869.9926 - 494.2840 - 29.7773 - 4336.9089)/32 = 0.281952 s`
per lane of conservative overhead; lane costs 159.550 / 117.601 / 110.996 / 155.095 all
reproduce; `(494.284 + 1.25*(64*277.151 + 16*266.091))/3600 = 7.774488506284026`.

**Does it survive R's execution rising? Yes, and it falls.** The projection is monotone in
each arm's lane cost, and fixing the lock-in strictly reduces R's and O's work: one file per
reply instead of two, and no doubled history. Evidence — R's output/reference ratio is
**1.735 on its four locked lanes and 0.990 on its four clean lanes**, and the max-token lane
in each R C4 group is a locked lane (dev-00 at 7745, dev-05 at 6022) while group wall tracks
the max lane. Scaling R and O by the clean-lane ratio (x0.732; decode-dominated at 94.7%
prefix-cache hit) gives lane costs 116.8 / 113.5 and a projection of **6.59 GPU-h**. The
honest range is **6.6-7.8 h against the 12 h gate**; 7.774 is an upper bound with respect to
this fix. The real risks to the gate are elsewhere: EVAL episodes are not DEV episodes
(different domains, including a held-out `aggregate_reduction`, and longer prose), and the
omitted Q arm (F8).

### 6.4 Pinned-commit and launch verification — correct
`run.py:main` asserts `git rev-parse HEAD == SHA`, `git diff HEAD --exit-code` and
`s.__file__.startswith(PIN)` before touching the GPU; `audit.py` re-asserts all three. I
re-verified independently: the pinned worktree is at 9f0c6d27, clean, and the three harness
files match the commit byte-for-byte. `validation.json` records 11 pre-GPU CPU driver tests
passing in 7.53 s plus a CPU cap-override lane smoke. The GPU-exclusivity check, the
`.review.lock`, the other-flags scan and the `x`-mode `RUNNING.flag` all ran before START.

---

## Findings

**HIGH — F1. Per-round execution rates are reported as if the 384 R/N/T rounds were
independent; 96 of the 105 non-executions are deterministic repeats of 9 initiating events.**
`README.md:9-12,14`; mechanism at `loop.py:363` and `slab2.py:556-561`. The "Parsed +
written /128" column is a 16x amplifier on 24 lane draws. Report lane-level execution (R 4/8,
N 7/8, T 7/8 clean at round 0) as primary, with the per-round rate conditional on a clean
round 0 as secondary.

**HIGH — F2. The README's framing supports "the register makes the model worse at
executing," which the artifact does not.** `README.md:5,9`. The failure mode is
arm-independent (N dev-02, T dev-05 fail identically), R beats N on dev-02, and the
episode-level comparison is 4/8 vs 1/8, Fisher two-sided p = 0.282. Under this repo's "claim
only what the artifact measures" rule, state the lane counts and the p-value or drop the
comparison.

**HIGH — F3. The one clean R-vs-N/T comparison in the run is not reported at all.**
On the 47 matched cells where all three arms wrote a file, R is 0/47 on indent (N 8/47,
T 8/47) and 0/12 on format (N 10/12, T 8/12), while being best on delivery (19/19 vs 15/19,
18/19). On matched, non-breakage, post-change rounds: **indent R 0/9, N 8/9, T 8/9; format
R 0/8, N 7/8, T 8/8.** Two discordant episodes, episode-level sign test p = 0.5 — so this is
a lead, not a result — but it is the only uncontaminated signal in the artifact and it is
absent from `README.md`. It should be reported with its n and its p, and it should set the
next experiment.

**HIGH — F4. The "Model/reference x" column is an artifact of the lock-in, not a model
property.** `report.py:54`, `README.md:9-12`. R is 1.735x on its four locked lanes and
**0.990x on its four clean lanes**; on the three episodes clean in all arms (01/04/06) the
arms are 1.061 / 1.065 / 1.091 — indistinguishable. The reported spread
(1.352 / 1.191 / 1.194) is entirely the six broken lanes. The direction is conservative for
cost, but the number will be read as a verbosity constant for the 64-episode run and is 37%
too high for R.

**HIGH — F5. No recovery path from a parse failure, so one bad draw destroys a 16-round
lane.** `slab2.py:556-561` returns `{"category":"fence_count_or_kind",
"error":"fence_count_or_kind"}` and nothing more; `loop.py:244-273` embeds it verbatim.
0/96 locked rounds recovered. Any future run of this harness carries the same 16x variance
amplifier regardless of arm.

**MEDIUM — F6. The T floor's `indent` denominator makes the primary substitution witness
unpassable by construction.** `slab2.py:713-734` counts all 128 T rounds; ~11 of 16 per
episode precede the `supersedes indent` event, and **no arm satisfies indent before turn 11
(R 0/44, N 0/77, T 0/77 written rounds) while N and T satisfy it readily after (20/35 and
13/27)**. The trait is not unmeasurable — the model ignores a standing obligation and obeys a
fresh change event — but the floor as written can never clear 50%, so `kinds<2` fails
regardless of what any arm does. Restrict the floor denominator to post-change rounds, or
score "obligation in force and restated" separately from "obligation last changed this
round."

**MEDIUM — F7. The system prompt supplies the failure mode.** `slab2.py:63`:
the literal text
`containing the WHOLE requested file:` followed by two fence openers naming `core.py`
and `policy.py` in one sentence. All 96 fence failures duplicate that pattern.
Arm-neutral, so it does not bias the comparison, but it is the root cause and the cheapest
thing to fix.

**MEDIUM — F8. The register renderer always puts the `delivery` default last, directly
against the `format compact` rule.** `register.py:420-424` appends defaults after explicit
rules; `renderer.py:129` then says "Apply the active rules" immediately after. R relapses on
format 16/16 (4/4 episodes) vs T 4/23 (1/6) and N 5/31 (2/7); episode-level Fisher p = 0.048
(R vs T), 0.061 (R vs N). Register an ordering control — defaults first, or sorted by key as
T does — before any composition claim, or this confound will be inherited by the 64-episode
run.

**MEDIUM — F9. The 7.774 h projection excludes an arm the pinned governing module declares
mandatory.** `slab2.py:9-11`: *"Registered run alone: R/N x64 plus nested O/T x16 and
fresh-task Q x64 ... Q is secondary to the full 64 pairs; its measured cost is mandatory."*
`registration.md` narrows this on the user's instruction ("No Q cost charged"), which is
legitimate, but `README.md:53` prints **"Registered-run projection: 7.774 GPU-h"** against a
12 h gate written for a Q-inclusive run. A Q lane at N-like cost adds
`1.25*64*117.6/3600 = 2.61 h` → **~10.4 h**, consuming 62% of the 4.2 h margin, and Q's cost
is unmeasured. Print both figures.

**MEDIUM — F10. The pinned, reviewed eligibility function was never exercised, and it
disagrees with the one that was.** `run.py:112-121` reimplements the gate;
`slab2.pilot5_reading` (`slab2.py:735-786`) is dead code in this run. On the
substitution-kind gate they differ: the pinned function takes all eligible traits with >=2
opportunity episodes → `{format, process}` = **2 kinds, PASS**; `run.py` restricts to
`('indent','delivery')` → `{process}` = **1 kind, FAIL**. `run.py` follows `registration.md`
and is the conservative reading, which is the right call — but this is one of the five
reported failing gates and the divergence belongs in the README, not left for a reader to
find.

**LOW — F11.** `value_gloss` (`renderer.py:19-23`) duplicates the indent sentence in R's
block only: `"indent 3 = block bodies indented by exactly 3 spaces per level indent 3 =
block bodies indented by exactly 3 spaces."` Uncontrolled arm-specific text in the exact
trait §5.2 finds R failing.

**LOW — F12.** `renderer.py:110` emits `Retired rules (not binding):` followed by an empty
line whenever there are no retirements — every R round 0 through the first lifecycle event.

**LOW — F13.** `run.py` does real work at import: it mutates `s.REPLY_CAP` and
`s.SYSTEM_PROMPT` at module level, and both `report.py:8-11` and `audit.py:8-11`
`exec_module` it. Against AGENTS.md's no-side-effect-import rule. Benign here (GPU work is
under `main()`), but any future import of `report.py` silently rewrites the pinned module's
globals.

**LOW — F14.** The determinism gate covers only 8 round-0 R prompts (~740 tokens each). The
stronger receipt already in hand is R≡O across 128 rounds at prompts up to 16,933 tokens run
35 minutes apart; `README.md:63` under-sells it as "gold-event equivalence." It is that *and*
a full-context batch-invariance receipt.

**LOW — F15.** `README.md`'s "no host process signals or push" is contradicted by repo state:
`origin/main` is at `37c3affd` ("Complete pilot 5"), so the pilot commits were pushed. The
run script performs no git operations; scope the sentence to the run.

**LOW — F16.** Early-round `wrong_family` (16 / 16 / 22 written rounds in R / N / T) is
driven by the system prompt's literal example trailer `report: task=A status=ok
delivery=ready` (`slab2.py:64`), which the model copies before it learns the task letter
varies. Arm-neutral, but it burns success headroom and is trivially neutralized.

**LOW — F17.** The GPU-exclusivity guard in `run.py` hardcodes an exemption for pid `2705`,
so another compute process was permitted to share the device during the cost measurement.
The R≡O replication bounds the resulting timing noise at 2.9%, immaterial against the 12 h
gate — but the exemption belongs in `launch.json`, not inlined in the guard.

---

## Bottom line

Every number in the report is arithmetically correct and fully reproducible from the
committed records; the provenance chain (pinned commit, HTTP payloads, prompt-ID replay,
hash manifest, container lifecycle) is the strongest in this project, and I re-derived 112
rounds of it independently. INELIGIBLE is the right verdict.

What the pilot established is not that the register arm cannot execute. It is that this
harness has a **one-token, round-0 format lottery with no recovery path**, which turns 9
coin-flips into a 105-round execution deficit and makes any per-round arm comparison
uninterpretable; that its **style-substitution floor counts rounds the model was never going
to satisfy**, so `kinds<2` fails by construction; and that on the small matched subset where
all three arms did produce files, **R complies with a just-changed indent 0/9 where N and T
comply 8/9** — a lead worth one properly powered test, not a result.

**The register arm's execution deficit is an instrument artifact, not a real effect.**
