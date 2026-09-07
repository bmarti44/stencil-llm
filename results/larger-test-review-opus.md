Fit-on: none. This review fits, tunes and selects nothing. It reads the frozen
artifacts of `results/larger-test/` at SHA `95fa7fc0c006518ef84c1ea20c152c079ae1798a`,
re-derives the registered statistics on CPU from the committed records and the
CPU-rebuilt evaluation bank, and adds descriptive cross-checks computed from
those same records. No GPU, no rerun, no reinterpretation of the frozen verdict.
No file under `data/bench` was read.

# Independent accuracy review — SLAB-2 Amendment 5, 64-episode larger test

Reviewer: Opus, single round, under Brian's 2026-09-06 ruling. Governing contract
`tests/fixtures/slab2_cpu_report.md:241-265` (= `results/larger-test/REGISTRATION.md`),
authorization `results/composition-pilot-7-review-opus.md:474-514`.

## 0. Bottom line

The run is **clean, complete and correctly read**. Every accounting claim
verifies. The registered primary reproduces exactly, bit for bit, from an
independent re-implementation. The `FAIL` is the frozen code's own output on the
committed records, and I reproduce it.

The two natural readings of the FAIL — "the mechanism works and the harm bar was
mis-set" and "the mechanism has a real cost" — are **both partly right, and the
second is the load-bearing one**. Specifically:

- The registered breakage clause is **poorly formed** (a fixed integer on a
  saturated binary metric whose definition does not match the definition the
  tolerance was written for), and the excess it reports, 20 vs 14, is **not
  statistically distinguishable from zero** (exact McNemar two-sided p = 0.109).
- But the clause is not a false alarm. Under the breakage definition the
  tolerance was actually written for — invalid program, excluding semantic test
  failures (`results/focus-mechanism-composition-v2-astra.md:113`) — the excess is
  **13 vs 2 episodes, one-sided exact p = 0.0037**, i.e. larger and significant.
  The FAIL is robust to fixing the instrument; fixing the instrument makes it worse.
- The cost is fully characterised and is **not register-specific**. Every one of
  the 48 R, 51 T and 2 N non-write rounds in the entire run is an *indentation*
  `SyntaxError`, and nine of the ten differential-breakage episodes have their
  first failing round **exactly** on their indent-change round (the tenth,
  `slab2-eval-21`, breaks at round 0 before any rule change). Arm T — which
  receives a correct, non-accumulating, current-valued prose statement of the
  same indent rule every turn — has *more* of this failure than R (29 vs 20 episodes; T-vs-R two-sided
  p = 0.035). The cost attaches to *acting on a restated style obligation in a
  whole-file re-emission protocol*, not to the register data structure.

So: **the mechanism does what the primary says it does, at a real and measurable
competence cost that the registered clause detected for roughly the right reason
with roughly the wrong instrument.** The honest headline is neither "it works" nor
"it fails", but "it works on the endpoint it was powered for, and the same
restatement that makes it work makes the model break its own files more often."

---

## 1. ACCOUNTING — verified, no exceptions

| Check | Result |
|---|---|
| Records present | 3328 = 64x16x3 (R/N/T) + 16x16 (Q). Exact. |
| Uniqueness | 3328 distinct `(episode_id, arm, turn)` keys; 0 duplicates; 0 records outside the registered set. |
| Episode completeness | 64/64 episodes with 16/16 turns in each of R, N, T; Q on exactly `slab2-eval-00`..`15`, as registered (`REGISTRATION.md:11`). |
| Arm labelling | 0 mislabelled rows in any file. |
| Caps | 0 truncated records in any arm; max prompt+cap 12047+2048 <= 32768. |
| Frozen SHA | `95fa7fc0…` is a real commit dated 2026-09-07 05:00:01 -0400 adding `REGISTRATION.md`, `freeze.json`, `scripts/larger_test.py`, `src/stencil/focus/slab2_endpoint.py`, `tests/fixtures/slab2_cpu_report.md`, `tests/test_focus_slab2_amendment5.py`. `git log` shows **no post-freeze edit** to any of them. |
| Source bytes | All 11 files in `freeze.json.source_hashes` hash identically on disk today. Zero drift. |
| Bank identity | I rebuilt the bank on CPU (`slab2.bank('eval')`) and its 64 `episode_sha256` values match `freeze.json.episode_hashes` **exactly**, and the ID list matches. The schedule I re-derive is therefore the frozen one. |
| Registration precedes evaluation | freeze commit 1788771601 -> `evaluation-opened.json` 1788771778.75 (+177.7 s) -> container 1788771780.20 -> **first evaluation record started 1788772301.18** (+700 s after the commit). Strictly ordered. |
| Bank opened once, never before | `scripts/larger_test.py:276` `assert not (OUT/"evaluation-opened.json").exists()`; one `launch.json`/`container.json`/`lifecycle.json`; 208 lane dirs (64R+64N+64T+16Q), each created with `exist_ok=False`. Repo-wide search finds **no prior model-response artifact on any `slab2-eval-*` ID**; the only pre-freeze appearances are the CPU token-accounting fixture `tests/fixtures/slab2_cpu_audit.json`, which is marked `"stub_only": true` and contains no `output` field, and `tests/fixtures/slab2_manifest.json`, whose `banks.eval` episode hashes already equal the frozen ones. |
| Episodes dropped | None. All 52 frozen groups in `groups.json` ran with `errors: []`. `summary.json.missing_records == []`. GPU held 6.8503 h against a 11.5 h cooperative deadline — 4.65 h of unused headroom, so no deadline path was taken. |
| Reading computed by frozen code | **Verified by re-execution.** I called `slab2_endpoint.larger_reading(records, bank, q_ids, cpu_control=True)` on the committed records and CPU-rebuilt bank: the result is **byte-identical to the committed `summary.json`** under sorted-key JSON comparison. `reading=FAIL`, `failures=['R episode breakage exceeds N by more than one']`, `breakage_excess=6`. |
| Receipt integrity | Sampled 400 records: `text_sha256 == sha256(output)` in 400/400; `output_sha256 == hash([output_ids, eos])` in 400/400; 200 sampled on-disk receipts match their records in 200/200; `output_tokens` consistent with `len(output_ids)` in 3328/3328. |
| Tracked artifacts | 33 files under `results/larger-test/` are tracked despite the `results/*` gitignore; `receipts/` and `local/` are deliberately untracked with hash manifests, as registered (`REGISTRATION.md:23`). Nothing that should be tracked is untracked. |

**A1 (low) — the CPU-composition conjunct in the reading cannot fail.**
`scripts/larger_test.py:399` passes `control["passed"]`, and `composition_control()`
returns `passed=True` as a literal (`scripts/larger_test.py:104`) after a chain of
bare `assert`s. The real gate is those asserts, which abort before the container
is launched (`scripts/larger_test.py:289` precedes GPU acquisition), so the
protection is genuine — but `slab2_endpoint.py:302`'s `if cpu_control is not True`
conjunct is decorative: any run that reaches the reading has already satisfied it.
No consequence here; worth removing or wiring to a real boolean in a successor.

**A2 (low) — the composition control reports but does not assert 64-episode coverage.**
`scripts/larger_test.py:102` asserts `len(historical) == 35 and receipts`; the
`scheduled_compact=276` and `episode_count=64` values in
`composition-control.json` are reported, not enforced. Both are in fact correct
(276 compact rounds exist in the bank, spread over all 64 episodes — I recount
276 from the rebuilt bank). REGISTRATION.md's "Preserve every hash and all64
episode coverage" is satisfied in fact, not by construction.

---

## 2. THE PRIMARY — re-derived independently, confirmed exactly

I re-implemented `change_rounds`, the within-episode exact-fraction averaging, the
one-sided exact sign test (p = sum_{j=w}^{d} C(d,j) / 2^d over discordant pairs
d = wins + losses), the Holm step-down over the three families, and the
missing-write-as-failure sensitivity, from the registration text, without
importing `slab2_endpoint`. Episodes and schedules come from the CPU-rebuilt bank
whose hashes match the freeze.

| Family | n | R/N/ties | mean gain | one-sided p | Holm | pass | sensitivity gain |
|---|---:|---|---:|---:|---:|---|---:|
| delivery | 64 | **40 / 0 / 24** | 0.625 | **9.094947e-13** | 2.728484e-12 | yes | +0.625 |
| format | 58 | 24 / 9 / 25 | 0.2586207 | 6.765493e-03 | 1.353099e-02 | yes | +0.234375 |
| indent | 54 | 9 / 5 / 40 | 0.0370370 | 2.119751e-01 | 2.119751e-01 | no | **-0.0703125** |

**Every figure in `RESULTS.md:9-11` is confirmed, including 40/0/24 and
p = 9.09494702e-13.** p = 2^-40 exactly, because all 40 discordant pairs favour R.
Holm: delivery x3, format x2, indent x1, with monotone enforcement — correct.

Structure of the primary, which matters for interpretation:

- **Delivery has exactly one change round per episode** (64 change rounds over 64
  episodes; 0 episodes with more than one). Within-episode averaging is therefore
  vacuous for the primary; each episode contributes one binary paired observation
  and the test is an exact McNemar. This is the strongest possible form of the
  registered design and removes any aggregation concern.
- **Zero missing paired writes on delivery.** Both arms wrote at all 64 delivery
  change rounds, which is why the conditional and missing-write-as-failure
  sensitivities are identical (both 0.625). The primary carries no missingness
  problem at all.
- Arm rates on those 64 rounds: **R 64/64 (1.000), N 24/64 (0.375), T 56/62
  conditional (0.903) / 56/64 strict, Q 16/16.**
- **No outcome-dependent selection.** `change_rounds` (`slab2_endpoint.py:16-45`)
  reads only `turn.events` and `turn.live` — schedule, never records. All 64
  episodes enter every family. The group schedule is read verbatim from
  `freeze.json.schedule`; `scripts/larger_test.py:244-245`'s `if errors: break` is
  fail-stop, which can only produce `INCOMPLETE`, never a curated subset. No
  retries, no seed changes, no alternative model, no fallback exist in the code
  path. Nothing was dropped.

**P1 (medium) — the primary's 64 observations are one event type with one correct answer, and that answer coincides with an arm-invariant attractor. RESULTS.md does not say so.**
All 64 delivery change events have `action == "completes"`; the required value at
the measured round is `ready` in **64 of 64** episodes; the round is turn 10 (43)
or 11 (21). The arm-invariant system prompt states in plain English *"After
cancellation/completion format defaults to compact and delivery defaults to
ready"* and its worked example ends `report: task=A status=ok delivery=ready`.
A degenerate policy that always emits `delivery=ready` scores 64/64 on the
registered primary. `RESULTS.md:44` mentions the worked example only as attracting
`delivery=ready` (a format-family confound); it does not disclose that the
attractor is the primary's correct answer in every episode.

**P2 — the same records refute the degeneracy, and this belongs in the report.**
Across all 400 delivery-applicable rounds in the bank, split by whether the
required value is the attractor:

| arm | required = `ready` | required != `ready` |
|---|---|---|
| R | 79/87 (0.908) | **313/313 (1.000)** |
| N | 32/87 (0.368) | 234/313 (0.748) |
| T | 71/87 (0.816) | 310/313 (0.990) |
| Q | 23/23 (1.000) | 75/75 (1.000) |

R emits the correct **non-default** delivery value 313 times out of 313.
Episode-paired descriptive sign test on non-`ready` rounds only: R 16 / N 0 /
ties 48, p = 1.53e-05. R is therefore *not* the degenerate policy; the register
conveys the value, not just the attractor. (All 8 of R's misses on `ready` rounds
are syntax-error non-writes at turn 11 — see Section 3; none is a wrong value.)

**P3 — N's failure mode is self-repetition, not ignorance.** I decoded the actual
prompts. In **64 of 64 episodes all three arms are told the new effective value in
the current user message**, e.g. `"completes delivery: Service contract requires
draft for delivery … Retired; use default delivery ready = trailer delivery=ready
when verbose and scoped"`. Classifying N's 40 failures: **40/40 emitted the retired
value**; 0 omitted the trailer; 0 emitted anything else. R: 64/64 correct. So the
primary measures *whether the model acts on the current instruction or repeats its
own stale trailer*, with the correct answer available in the current turn and in
the system prompt. That is a stronger and more interesting result than "the
register supplied missing information", and it should be stated that way.

**P4 (medium) — the conditional/strict divergence on `indent` is caused entirely by R.**
The 6 episodes dropped from the format family and the 10 dropped from the indent
family are **all** members of R's 13-episode non-write set; 5 more indent episodes
are partially reduced, all by R or N non-writes. The conditioning on "common
parsed writes" therefore removes precisely R's failures, which biases every
conditional estimate in R's favour by construction. `RESULTS.md:32` flags the
indent sign flip and points to `summary.json`, but does not say the missingness is
one-sided and R-caused. That sentence should be added.

**P5 (medium) — the published joint-final numbers are not the frozen field, and the frozen field's value is not disclosed.**
`slab2_endpoint.py:279-284` defines `joint_final` as all four *raw* satisfaction
flags at the last round. Under that frozen definition the value is **R 0, N 0,
T 0, Q 0** (`summary.json.per_arm`). `RESULTS.md:17-20` publishes R 12 / N 5 /
T 14 / Q 0 from `report.py`'s applicable-trait rubric. `report-notes.md` discloses
the substitution and the rubric itself was committed at 05:06:43, before the
server was ready (05:11:17) and before any evaluation response (05:11:41) — the
timing claim checks out. But the *per-arm table row* was switched from the frozen
field to the report rubric in the final post-run commit at 11:58:50, with all
outcomes visible, and RESULTS.md nowhere states that the frozen definition yields
zero for every arm. Not a verdict issue (joint final is descriptive by
registration), but the reader is entitled to both numbers. For the record, the
descriptive paired contrast under the applicable-trait rubric is R-only 9,
N-only 2, one-sided p = 0.033 — R ends more episodes fully compliant than N.

---

## 3. THE FAILING CLAUSE — R 20 vs N 14

### 3.1 Complete classification of every differential breakage episode

`outcome.diagnostics.breakage` is set in three places: a capped reply
(`slab2.py:513` — never fired, zero caps), a `SyntaxError`/`RecursionError` on the
emitted file (`slab2.py:527-541`), and a `SyntaxError`/`RecursionError`/
`InvalidProgram` raised while *evaluating* a test case
(`slab2.py:563-565` public, `slab2.py:687-689` private).

Composition of every breakage round in the run:

| arm | breakage rounds | of which emitted-file `SyntaxError` | of which semantic-raise |
|---|---:|---:|---:|
| R | 231 | 48 | 183 |
| N | 194 | 2 | 192 |
| T | 277 | 51 | 226 |
| Q | 7 | 0 | 7 |

Episode-level decomposition of the 20 / 14:

- **12 episodes are broken in R *and* N *and* T from round 0 and stay broken**
  (`slab2-eval-02,06,10,14,18,22,26,30,34,38,42,46` — index = 2 mod 4 up to 46).
  Their round-0 rows are identical in kind across arms:
  `breakage=True, semantic=True, integration=False, category=None`. All three arms
  write near-identical code; the episode's own public case raises. This is an
  **episode-generator property, not an arm effect**. It saturates 12 of R's 20 and
  12 of N's 14 and contributes nothing to the excess.
- **R-only, 8 episodes:** `07, 12, 19, 21, 41, 45, 47, 56`.
- **N-only, 2 episodes:** `35, 53`.
- Excess = 8 - 2 = 6 = `summary.json.breakage_excess`. Confirmed.

**Every single differential episode except one is the same failure, and it is an indentation `SyntaxError` on the exact round the indent rule changes.**

| episode | arm | indent-change turns | first breakage turn | error |
|---|---|---|---|---|
| eval-07 | R | 11, 15 | **11** | `unexpected indent` (policy.py line 2) |
| eval-12 | R | 11, 15 | **11** | `unexpected indent` (core.py line 2) |
| eval-19 | R | 11, 15 | **11** | `unindent does not match any outer indentation level` |
| eval-41 | R | 12, 15 | **12** | `unindent does not match any outer indentation level` |
| eval-45 | R | 11, 15 | **11** | `unexpected indent` |
| eval-47 | R | 11, 14 | **11** | `unindent does not match any outer indentation level` |
| eval-56 | R | 12, 15 | **12** | `unindent does not match any outer indentation level` |
| eval-21 | R | 12, 14 | 0 | semantic-raise at round 0, *before any change* |
| eval-35 | N | 10, 15 | **10** | `unindent does not match any outer indentation level` |
| eval-53 | N | 10, 15 | **10** | `unindent does not match any outer indentation level` |

Coincidence rate of first-failure round with indent-change round: **9 of 9**
(eval-21 excluded as a round-0 semantic-raise, unrelated to any rule change: R
wrote `result = len(x) <= 5 and all(x[i] <= x[i+1] for i in range(len(x)-1))`
which raises on the case, N wrote `result = len(x) <= 5` which does not).

Across the whole run, **every non-write round in every arm is an indentation
`SyntaxError`** — R 48 (26 `unexpected indent`, 15 `unindent does not match`,
7 `expected an indented block`), N 2, T 51. There is not one truncation, one
malformed fence, one wrong-path write, one recursion failure, or any other error
kind, in 3328 records.

Literal outputs. R, `slab2-eval-07`, turn 11, where the rendered block reads
`"key":"indent" … "text":"Service contract requires 3 for indent. indent 3 = block
bodies indented by exactly 3 spaces per level" … "value":"3"`:

````text
```python policy.py
# policy.py
   def identity(x):
       return x

   def step_4(x):
       """Count values in the inclusive range [2, 9]."""
       result = sum(1 for num in x if 2 <= num <= 9)
       return result
…
report: task=B status=ok delivery=ready
```
````

The model applied "3 spaces" to the *file*, not to *block bodies*, indenting the
top-level `def`s. R, `slab2-eval-19`, turn 11 shows the half-applied variant —
`def identity` left at column 0, every other `def` indented by 2 — giving
`unindent does not match any outer indentation level`. N, `slab2-eval-35`, turn 10
does exactly the same thing and even narrates it at `slab2-eval-53`:

```text
report: task=B status=blocked delivery=staged

The service contract requires 3 spaces for indent, but the current code uses 2 spaces.
```

This is one coherent family: **an attempted global re-indent of a whole file,
mis-scoped, producing invalid Python.** It is *not* the pilot-7 lock/format
artifact family, which was `delivery=ready` emission inside compact windows. It is
lock-*shaped* — 4 of the 7 R cases persist to round 15, 3 recover (eval-19
recovers at 12-14 and re-breaks at 15; eval-45 breaks once; eval-47 twice) — but
it is a different family with a different trigger and, unlike pilot 7's zero
recoveries, it recovers 3 times in 7.

### 3.2 The 13 R non-writes and the answer to "is it the rendered block?"

R's 13 non-write episodes are `02, 07, 12, 18, 19, 22, 26, 38, 41, 45, 46, 47, 56`.
Six of them (`02, 18, 22, 26, 38, 46`) are already in the both-arms-broken set, so
they add nothing to the excess; seven are the indent-syntax episodes above.
Non-write rounds are strictly a subset of breakage rounds in every arm.
Their distance from the most recent indent-change round: R 23 at distance 0,
12 at 1, 9 at 2, 4 at 3 — i.e. the failure starts *on* the change and persists.
N: 2 at distance 0.

At each episode's **first** indent-change round:

| arm | satisfied | written but not satisfied | `SyntaxError` |
|---|---:|---:|---:|
| R | 43 | 9 | **12** |
| N | 54 | 8 | **2** |
| T | 36 | 12 | **16** |

Over **all** 128 indent-change rounds: R 73 satisfied / 32 written-miss / 23 syntax;
N 82 / 44 / 2; T 74 / 25 / 29. Note that R and N *attempt* at indistinguishable
rates (43+12 = 55 vs 54+2 = 56); R's attempts are syntactically invalid far more
often. Note also that **N's unconditional indent adherence is higher than R's**
(82/128 vs 73/128) — which is exactly the negative missing-write sensitivity of
-0.0703 in `RESULTS.md:11`. **The failing breakage clause and the negative indent
sensitivity are the same 48 rounds reported twice**, not two independent findings.

Was the rendering itself responsible? No. Decoding the prompts:

- R's block at the failing round is explicit and correct: *"indent 3 = block bodies
  indented by exactly 3 spaces per level"*. The model mis-executed an unambiguous
  instruction; the rendering is not defective.
- Context length is not the driver either. Mean prompt tokens at turn 11 are
  R 7360, N 4454, T 5124 — yet T, in the middle, has the most syntax errors.

### 3.3 The exact paired test, and the T comparison

Exact McNemar on any-breakage episodes, b = R-only = 8, c = N-only = 2:

- **one-sided exact p = 0.054688; two-sided exact p = 0.109375.**
- paired difference 6/64 = 0.09375; Wald 95% CI **[-0.0003, +0.1878]** (includes 0).
- conditional odds ratio 4.00, Liddell exact 95% CI **[0.798, 38.67]** (includes 1).
- Clopper-Pearson 95% CI on b/(b+c) = 0.80 is [0.444, 0.975] — includes 0.5.

**The reported excess is not statistically distinguishable from zero at
alpha = .05 by any standard paired test.** The run failed a point estimate.

But the *non-write* channel is significant: R-only 13, N-only 2,
**one-sided exact p = 0.00369**, two-sided 0.00739. The any-breakage metric is
diluted by the 12 arm-invariant semantic-raise episodes, which are concordant and
therefore statistically inert, and which also censor 6 of R's 13 real failures
from the excess. So the metric that failed the run is the *weaker* view of a
*real* effect.

Cross-arm paired breakage:

| contrast | discordant | one-sided p | two-sided p |
|---|---|---:|---:|
| R vs N | R-only 8, N-only 2 | 0.0547 | 0.1094 |
| T vs N | T-only 17, N-only 2 | 0.00036 | 0.00073 |
| **T vs R** | **T-only 12, R-only 3** | **0.0176** | **0.0352** |
| T vs R (non-write) | T-only 12, R-only 6 | 0.119 | 0.238 |

**What T's 29 implies.** T receives, every turn, a single-line, non-accumulating,
correct-valued oracle statement of the live obligations — e.g. *"Effective
obligations: delivery ready = …; indent 3 = block bodies indented by exactly 3
spaces per level; …  Not binding: delivery=queued; indent=2"* — and it breaks
**significantly more** than R and **far** more than N, with the identical error
family (41 `unindent does not match`, 6 `expected an indented block`, 4
`unexpected indent`). Therefore:

1. **Breakage cannot be attributed to "rendering a register block."** The arm with
   no register block at all, but with a correct current-valued restatement, is the
   worst.
2. **It can be attributed to restating a style obligation at request time**, in a
   protocol that requires re-emitting the whole file. Both R and T pay it; N,
   which mostly ignores the indent change, does not.
3. It follows that **the harm the clause detected is a cost of compliance, not a
   cost of the representation** — and that any successor that restates obligations
   in any form, prose included, will pay it.

**Classification verdict, in the terms asked:** not (a); partly (b) in the weak
sense that R's block is what reliably informs R of the change, but decisively not
in the sense that the block itself causes the failure; and (c) yes — a genuine
cost of the mechanism, correctly understood as a cost of *acting on the restated
obligation*, shared by any faithful restatement.

### 3.4 Is the clause well-formed?

No, on four independent grounds — and the answer does not rescue the run.

1. **Definition mismatch (high).** The tolerance was written in
   `results/focus-mechanism-composition-v2-astra.md:113`, which defines breakage as
   "malformed tool call, invalid required complete program, empty/repetitive/
   truncated reply, resource failure or unintended workspace damage" and instructs:
   *"Keep language mismatch, style/format/default violations, **semantic test
   failures**, fact loss and process violations separately."* The implemented
   `outcome.diagnostics.breakage` sets breakage on a semantic exception
   (`slab2.py:563-565`, `slab2.py:687-689`), so **183 of R's 231, 192 of N's 194
   and 226 of T's 277 breakage rounds are semantic test failures the definition
   excludes.** Computed on the definition-matched metric (emitted-file invalidity
   only) the clause reads **R 13 vs N 2, excess 11**, still > 1, and now
   significant at p = 0.0037. The FAIL survives the correction and strengthens.
2. **Threshold does not scale (high).** "<= 1 episode" is an absolute count, not a
   rate or a test. At the DEV n = 8 where it was last looked at it tolerated a
   12.5% excess; at n = 64 it tolerates 1.6%. The same clause is ~8x stricter at
   the size it was actually applied at. No power analysis exists for it.
3. **Never calibrated on DEV (correcting the premise).** The clause was not
   derived from the eight DEV episodes. It originates in the v2 design memo, is
   disclaimed there in the same sentence — *"this practical tolerance is not a
   noninferiority proof"* — and was carried verbatim into
   `REGISTRATION.md:11` and `slab2_endpoint.py:294,300-301`. The pilot-6 and
   pilot-7 DEV data (R 3/8, N 3/8, R-only 0, N-only 0 in both) merely never made
   it bind. `results/composition-pilot-7-review-opus.md`, the authorization, does
   not propose it, mention it, or list it among its ten freeze conditions
   (`:478-514`); its item 5 (`:493-496`) contains no breakage conjunct at all.
   The clause entered the PASS rule from the design memo, not from the review that
   authorized the run.
4. **Saturated instrument (medium).** "Any breakage in 16 rounds" has a 22%
   baseline in the control arm, 12/64 of it arm-invariant. It has poor resolution
   and it censors: 6 of R's 13 genuine failure episodes are invisible to the
   excess because N already fails those episodes for an unrelated reason.

And the arm that would fail this clause worst — T at 29, excess 15 over N — was
explicitly exempted: `REGISTRATION.md:11` "No … T floor, absolute breakage or
compact-behavior gate." A tolerance applied to the treatment arm but not to the
oracle comparator that exceeds it is asymmetric by construction.

**Conclusion on 3.4:** the clause is not well-formed as a decision rule, but it is
not a false positive either. It fired on a real, mechanistically explained,
statistically significant cost, using an instrument whose numeric threshold was
arbitrary and whose definition was wrong in a direction that *understated* the
effect. The verdict FAIL should stand exactly as written and must not be
re-litigated.

---

## 4. THE PRE-DECLARED CONFOUNDS, QUANTIFIED

### 4.1 T's oracle prose comparability (`REGISTRATION.md:17`)

Measured, not assumed:

- Delivery at the registered change round: **R vs T paired 6 R-wins / 0 T-wins /
  56 ties, one-sided p = 0.0156 conditional; 8 / 0 / 56, p = 0.0039 strict.**
  Arm means R 1.000, T 0.903 conditional (0.875 strict).
- On the 313 non-`ready` delivery rounds: R 313/313, T 310/313.
- T vs N on delivery: 33 / 1 / 28, p < 1e-6. Q vs N: 14 / 0 / 2, p = 6e-5.

So **all three arms that restate the current value beat plain history by a wide
margin, and the register beats correct prose by a small, unregistered, post-hoc,
uncorrected margin.** Two of R's eight strict wins over T come from T's own indent
syntax errors, not from a delivery miss.

*Blocks:* any sentence of the form "the register beats prose", "the data structure
causes the gain", or "the register is necessary". The registered contrast is R-N,
and T is descriptive, exactly as `results/composition-pilot-7-review-opus.md:380-385`
required.

*Additionally:* T's oracle line is uncomposed under compact — at
`slab2-eval-07` turn 12 it reads `"… delivery ready = trailer delivery=ready when
verbose and scoped; format compact = trailer omits delivery; …"`, carrying the
delivery clause the composed R block removes. So R-vs-T **format** comparisons are
confounded, as registered. R-vs-T **indent** comparisons are not — T's indent line
is correct and unambiguous — which is what makes T's higher indent-syntax rate
decisive in Section 3.

### 4.2 History is never re-composed (`loop.py:363`, `REGISTRATION.md:17`)

Measured on decoded prompts, `slab2-eval-07`, the indent change at turn 11
(2 -> 3):

| arm | prompt tokens | rendered "Active rules" blocks | "requires **2** for indent" | "requires **3** for indent" |
|---|---:|---:|---:|---:|
| R turn 11 | 6957 | **12** | **12** | 2 |
| R turn 15 | 10074 | **16** | **14** | 6 |
| N turn 11 | 4265 | 0 | 1 | 1 |
| T turn 11 | 3458 | 0 | 1 | 1 |

R's prompt at the decisive round carries **eleven stale copies of the superseded
rule against one current copy**, and 63% more tokens than N's. The mechanism adds
a current statement; it removes nothing.

*Blocks:* "the mechanism removes stale instructions", "history is clean", "no
stale influence remains", and any absence-of-stale-influence claim.
*Supports, in the other direction:* R attains 64/64 on delivery **despite** an 11:1
stale-to-current ratio, which is the strongest thing in the run — a single current
rendered statement dominates eleven stale ones.

### 4.3 The arm-invariant system worked example (`slab2.py:71-73`, `REGISTRATION.md:17`)

The system prompt is identical in all four arms and contains both a worked example
ending `report: task=A status=ok delivery=ready` and the sentence *"After
cancellation/completion format defaults to compact and delivery defaults to
ready."*

- **Q is the clean measurement of its force:** fresh context, a fully composed
  register block with no delivery row, no history at all. Q emits `delivery=ready`
  in a compact round in **16/16 episodes** and has **0.0000 format adherence**
  (`RESULTS.md:20,27`). The example alone is sufficient to produce the compact
  format violation.
- Therefore the format family's absolute level is depressed in every arm, and
  **the R>N format gain cannot be attributed to composition**: composition without
  history (Q) yields 0%.
- And, per P1, the example's `delivery=ready` is the primary's correct answer in
  all 64 episodes.

*Blocks:* attributing the format-family result to the composition fix; reading the
primary's 100% as evidence of value-conveyance *by itself* (P2's non-`ready`
analysis is what licenses that, not the registered primary).

---

## 5. THE CROSS-RUN REPRODUCIBILITY CONTROL

**What it measured.** 40 fixed pilot-7 **R payloads** — the eight *DEV* episode IDs
at rounds 0, 4, 8, 12, 15 — with request JSON hashes frozen before launch, reissued
byte-identically in this run's new container after group 27 (a 389 s window between
group 27's end and group 28's start, matching `cost-audit.json`), and compared on
response text, generated token IDs and finish reason.

**Result:** 0/40 divergent (0.0%); 0/8 episodes with any divergence; episode-mean
divergence 0.0% (`reproducibility.json`). 95% Clopper-Pearson upper bound on the
true per-payload divergence rate: **8.8%**. The historical observation was
10/166 = 6.02%. `RESULTS.md:36` states correctly that this preselected R-only DEV
set neither establishes universal reproducibility nor negates the prior figure.
The determinism gate (forward/reverse replay of the same 8 DEV round-0 R prompts
at concurrency 4) also returned 0 mismatches on exact token bodies.

**Does the primary's margin survive the measured divergence rate?** Overwhelmingly.
Adversarial flip analysis on the delivery family (converting R-wins into N-wins,
the worst case):

| flips | R/N | one-sided p | Holm(x3) | still passes |
|---:|---|---:|---:|---|
| 0 | 40/0 | 9.09e-13 | 2.73e-12 | yes |
| 4 | 36/4 | 9.29e-08 | 2.79e-07 | yes |
| 8 | 32/8 | 9.11e-05 | 2.73e-04 | yes |
| 12 | 28/12 | 8.30e-03 | 2.49e-02 | yes |
| **13** | 27/13 | 1.92e-02 | 5.77e-02 | **no** |

The delivery result tolerates **12 adversarial episode flips out of 40** — a 30%
corruption. At the historical 6.02% rate, the expected number of affected delivery
change rounds is ~3.9 of 64; flipping four of them adversarially still leaves
Holm p = 2.8e-07. **The primary is robust to any plausible divergence rate.**

**The format family is not (high).** It fails Holm at **two** adversarial flips
(22/11 -> Holm 0.0801). At a 6% divergence rate over 58 measured episodes the
expected number of affected episodes is ~3.5. `RESULTS.md:10` prints
"Evidence: True" for format with no fragility note. **The format family's
Holm-significant result must not be quoted without stating that it is destroyed by
two episode flips and is therefore not robust to the historically observed
cross-container divergence rate.** This is the single most important omission in
RESULTS.md.

---

## 6. WHAT MAY NOW BE CLAIMED

### 6.1 Sentences that are supportable, exactly as written

> On 64 pre-registered, authored, 16-round whole-file Python editing episodes run
> once on a frozen Qwen3-30B-A3B with gold structured rule events, rendering the
> current effective obligations into the request improved adherence to the
> delivery obligation at scheduled rule changes over ordinary retained history:
> 40 episode wins, 0 losses, 24 ties over 64 paired episodes, exact one-sided
> sign-test p = 9.09e-13, Holm-adjusted p = 2.73e-12 across three pre-declared
> families, mean paired gain 0.625, with zero missing paired writes so the
> missing-write-as-failure sensitivity is identical.

> The registered run reads FAIL, because the conjunction also required that the
> register arm's any-breakage episode count exceed the plain-history arm's by at
> most one, and it exceeded by six (20 vs 14).

> The delivery obligation is not information the plain-history arm lacked: in all
> 64 episodes the current user message states the new effective value, and all 40
> of that arm's failures consist of re-emitting its own retired trailer value. The
> register's effect is to prevent self-repetition of a superseded value, not to
> supply an absent one.

> The register arm emitted the correct non-default delivery value on 313 of 313
> applicable rounds where that value was not the system prompt's default, against
> 234 of 313 for plain history (descriptive, unregistered).

> Every non-write in the run, in every arm, is an indentation SyntaxError produced
> by attempting a whole-file re-indent, and every differential-breakage episode's
> first failing round is exactly its indent-change round.

> The excess breakage is a cost of acting on a restated style obligation, not of
> the register representation: the oracle-prose arm, which restates the same
> obligations correctly and without accumulation every turn, breaks more often
> than the register arm (29 vs 20 episodes; paired two-sided p = 0.035) and has
> more non-write episodes (19 vs 13).

> The reported excess of six any-breakage episodes is not statistically
> distinguishable from zero (exact McNemar two-sided p = 0.109; 95% CI on the
> paired difference [-0.0003, +0.188]). The underlying cost is nevertheless real:
> on the definition of breakage the tolerance was written for — invalid program,
> excluding semantic test failures — the excess is 13 versus 2 episodes,
> one-sided exact p = 0.0037.

> Every accounting requirement of the registration was met: 3328/3328 records,
> unique, complete on 64/64 episodes in R/N/T and 16/16 in Q, zero caps, zero
> dropped groups, source bytes and bank hashes identical to the freeze, the bank
> opened once 177 seconds after the freeze commit and 700 seconds before the first
> evaluation record, the reading produced by the frozen `larger_reading()` and
> reproducible bit-for-bit from the committed records, and the 40-payload
> cross-container control completed at 0/40 divergent.

> GPU held 6.8503 h against a 7.4462 h projection and an 11.5 h cooperative
> deadline; no deadline path was taken.

### 6.2 Sentences that are NOT supportable

- "The mechanism passed." It did not; the registered reading is FAIL and that is
  the result.
- "The register beats correct prose reminders", "the data structure causes the
  gain", "registers beat prose." T reaches 0.903 on the same endpoint and 310/313
  on non-default values; the R-vs-T contrast is unregistered, post-hoc and
  uncorrected.
- "The mechanism removes stale instructions" / "history is clean." R's prompt at
  the decisive round carries eleven stale copies of the superseded rule against one
  current one.
- "Composition fixed the compact format." Q has a fully composed block, no history,
  and 0/16 format adherence.
- "Rendering causes breakage" or "the register damages code." T breaks more.
- "The excess breakage proves the mechanism harms competence." The registered
  clause is a practical tolerance, not a noninferiority test; the any-breakage
  excess is not significant on its own terms. (The *non-write* excess is — say
  that instead, with its own numbers.)
- "Format adherence improved." Not without the fragility statement: the format
  family loses Holm significance after two episode flips and is not robust to the
  historically observed 6.02% cross-container divergence rate.
- "Indent adherence improved." Unconditionally it regressed: 73/128 for R against
  82/128 for N, sensitivity gain -0.0703.
- "R ends more episodes successfully" without the caveat that under the *frozen*
  joint-final definition every arm scores 0/64, and the published 12/5/14 uses a
  report-side rubric whose per-arm presentation was adopted after outcomes were
  visible.
- "Deterministic and exactly reproducible across restarts." 0/40 on a preselected
  DEV R-only set, 95% upper bound 8.8%, against a prior 10/166.
- Everything on `results/full-program-review-astra.md:190-197` remains prohibited,
  unchanged.

### 6.3 Reconciliation with `results/full-program-review-astra.md` Section 4

- **The "permitted abstract" at `:184-186` is void.** It is explicitly conditional
  on a verified PASS ("**Permitted abstract, three sentences, conditional on a
  verified PASS**"). There is no PASS. Section 6.1 above replaces it. The
  substance of its third sentence — "This supports restating current effective
  state in this bounded setting, not a unique benefit of the register
  representation" — is *confirmed and strengthened* by the final data, and should
  be carried forward verbatim.
- `:182` "PASS additionally requires … at most one extra R any-breakage episode" —
  **confirmed as the operative and sole failing clause.**
- `:188` "If the missing-write-as-failure sensitivity fails or changes direction,
  say that prominently" — **triggered** (indent +0.037 conditional, -0.0703
  strict) and reported at `RESULTS.md:32`, though without disclosing that the
  missingness is entirely R-caused (P4).
- `:188` "If T matches R, report it; R-N alone cannot identify a register-specific
  advantage" — **triggered and reported** (`RESULTS.md:26`, T 0.9032/62). This
  review adds the paired R-vs-T numbers.
- `:195` "'PASS proves safety/no competence harm' must not appear" — the situation
  is now the mirror image, and the mirror sentence is equally prohibited: **FAIL
  does not prove competence harm either.** `RESULTS.md:30` already carries the
  correct hedge ("this is not a separately registered test of harm"). What may be
  said is the definition-matched non-write result, which *is* a powered
  comparison.
- `:139` "Pilot 7 DEV significance — high fragility … needs the registered
  independent 64" — **refuted as a fragility worry for delivery**: the independent
  64 returned 40-0 at p = 9.09e-13 and tolerates 12 adversarial flips. **Not
  refuted for format**, which tolerates one.
- `:134`/`:141` cross-container reproducibility 156/166 — **still open**; the two
  receipts (0/40 here, 10/166 historically) are on differently selected samples
  and RESULTS.md's caveat is the honest reading.

### 6.4 The direct question

**Does a FAIL on the conjunction with an overwhelming primary mean the mechanism
works and the harm bar was mis-set, or that the mechanism has a real cost?**

Both, and the ordering matters:

1. **The mechanism does what the primary was powered to detect**, at an effect size
   (0.375 -> 1.000) and a p-value that no plausible reproducibility or analysis
   choice can touch. That is established.
2. **The harm bar is mis-set** — wrong definition of breakage, an unscaled integer
   threshold, no power analysis, applied asymmetrically to the treatment arm but
   not to the oracle comparator that exceeds it, and computed on a metric saturated
   by 12 arm-invariant episodes.
3. **And the mechanism nevertheless has a real cost**, which the mis-set bar
   detected anyway. Correcting the bar's definition makes the cost larger and
   significant, not smaller. Any claim that the FAIL is a bookkeeping artifact is
   false.
4. **The cost is not specific to the register.** It is the cost of the model acting
   on a restated style obligation in a whole-file re-emission protocol; the prose
   oracle pays it more heavily. A successor that swaps the representation will not
   avoid it. A successor that changes the *edit protocol* might.

The result to bank is: *restating current effective state at request time
converts a 37.5% obligation-adherence rate into 100%, and simultaneously raises
the number of episodes containing a syntactically invalid file from 2 to 13 in 64
(23 of 128 indent-change rounds against 2).* Both halves are the same mechanism.

---

## 7. NEXT STEP — the single most informative follow-up

**Run the same 64 frozen episodes with the register unchanged and the edit
protocol changed from whole-file re-emission to a scoped edit that cannot
re-indent untouched code — one arm, R-only, against the already-frozen R lane as
its own control.**

Why this and nothing else:

- It is the only intervention that separates the two halves of the banked result.
  The entire measured cost is a whole-file re-indent going syntactically wrong on
  the indent-change round; if a scoped edit protocol removes it, the mechanism's
  benefit survives with no measurable competence cost, and that is the claim worth
  having. If the cost persists, the cost is intrinsic to obligation restatement and
  the program should say so and stop trying to engineer it away.
- It needs no new statistical machinery: the endpoint is the already-registered
  non-write episode count, where the current effect is R 13 vs N 2 at p = 0.0037,
  and the pre-registered success criterion can be stated in advance as "R-protocol
  non-write episodes <= 4", i.e. within the arm-invariant floor.
- It requires a **new recipe and honest lineage**: a new registration, a new freeze
  commit, an explicit statement that the 64 episodes have now been model-evaluated
  once and that this is therefore a *second* pass over the same bank — so either a
  fresh evaluation bank at a disjoint seed (`slab2.bank` supports it) or an
  explicit "re-used bank, not independent" line. Do not silently re-use the bank.
- Fix three things in the same freeze: define breakage as the v2 memo defines it
  (exclude semantic-raise, `slab2.py:563-565,687-689`), state the tolerance as a
  paired test with a power statement rather than an integer, and apply it
  symmetrically to any comparator arm.

**Cost.** One arm x 64 episodes x 16 rounds = 1024 requests. The frozen R lane
measured 106.96 s/lane, so 64 lanes at concurrency 4 is ~1.9 h of group time; with
model load (~500 s), the determinism gate and cleanup, budget **~2.5 GPU-h**, and
register a 4 h cooperative deadline. That is a third of this run and about a
seventh of the 11.5 h that was held.

Explicitly do **not** do next: re-run the same recipe hoping for a different
breakage draw; re-litigate the ≤1 clause against the frozen result; add arms;
or scale to more episodes. The frozen result stands as written.

---

## Findings

| # | Sev | Where | Finding |
|---|---|---|---|
| F1 | **high** | `src/stencil/focus/slab2.py:563-565,687-689` vs `results/focus-mechanism-composition-v2-astra.md:113` | The gating breakage metric includes semantic test failures, which the definition the tolerance was written for excludes. 183/231 R, 192/194 N and 226/277 T breakage rounds are semantic-raise. On the definition-matched metric the clause reads 13 vs 2 (excess 11, p = 0.0037) rather than 20 vs 14 (excess 6, p = 0.109). The FAIL is correct either way; the reported form understates the effect. |
| F2 | **high** | `results/larger-test/RESULTS.md:10` | The format family is printed as "Evidence: True" with no robustness statement. It loses Holm significance after **two** adversarial episode flips, against a historically observed 6.02% cross-container divergence rate over 58 episodes. It must not be quoted without that caveat. (Delivery, by contrast, tolerates 12 flips.) |
| F3 | **high** | `REGISTRATION.md:11`, `src/stencil/focus/slab2_endpoint.py:294,300-301` | The `<=1` breakage clause is not well-formed as a decision rule: absolute count with no scaling in n (12.5% tolerance at n=8, 1.6% at n=64), no power analysis, applied to R but explicitly not to T which exceeds R, and computed on a metric 12/64 saturated by arm-invariant episodes. It originates in a design memo that disclaims it ("not a noninferiority proof"), not in the authorizing review, which proposes no breakage gate at all (`results/composition-pilot-7-review-opus.md:478-514`). |
| F4 | medium | `results/larger-test/RESULTS.md:9,44` | The primary's 64 observations are all `action=completes` with required value `ready`, which is exactly the value shown in the arm-invariant system prompt's worked example and stated in its "delivery defaults to ready" sentence. A degenerate always-`ready` policy scores 64/64. RESULTS.md does not disclose this. Mitigated within the same records (R 313/313 on non-`ready` rounds, paired R>N 16/0/48, p = 1.5e-5) — that analysis should be added. |
| F5 | medium | `results/larger-test/RESULTS.md:32` | The conditional-vs-strict divergence on indent and format is one-sided: all 6 format-dropped and all 10 indent-dropped episodes are R non-write episodes. Every conditional estimate is therefore biased toward R by construction. RESULTS.md flags the sign flip but not the one-sidedness. |
| F6 | medium | `results/larger-test/RESULTS.md:17-20`, `report.py:135-167` vs `slab2_endpoint.py:279-284` | The published joint-final column (R 12 / N 5 / T 14) uses a report-side applicable-trait rubric; the frozen field is **0 for every arm** and that value appears nowhere in RESULTS.md. The rubric was authored pre-outcome (05:06:43, before the first response at 05:11:41) and is disclosed in `report-notes.md`, but the per-arm row was switched to it in the post-run commit at 11:58:50. Descriptive only; no verdict impact; both numbers should be printed. |
| F7 | medium | `results/larger-test/RESULTS.md:30,34` | The failing clause is reported with no uncertainty statement. Exact McNemar two-sided p = 0.109; 95% CI on the paired difference [-0.0003, +0.188]; conditional OR 4.0 with exact 95% CI [0.80, 38.7]. The correct reading — "a practical tolerance failed on a point estimate; the powered version of the same cost is the non-write comparison at p = 0.0037" — is not stated. |
| F8 | low | `scripts/larger_test.py:104,399`, `slab2_endpoint.py:302` | `cpu_control` is a literal `True`; the reading's CPU-composition conjunct can never be false. The protection is real (asserts abort before the container launches) but the conjunct is decorative. |
| F9 | low | `scripts/larger_test.py:102` | The composition control asserts 35 historical hashes and per-register bit-equality, but reports rather than asserts the registered "all 64 episode coverage" (`episode_count=64`, `scheduled_compact=276`). Both are correct in fact. |
| F10 | low | `tests/test_no_side_effect_imports.py:16-25` | `scripts/larger_test.py` is not in `GPU_ENTRY_SCRIPTS` and `results/larger-test/report.py` is outside the scanned tree. Both are clean against the repo's own criterion and both have `main()` guards, but neither is covered by the test that enforces the rule. |

No critical findings. No accounting, provenance, statistical or protocol error was
found in the frozen run. The published verdict, the published primary numbers and
the published descriptive counts all verify.
