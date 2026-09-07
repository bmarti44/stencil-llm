Fit-on: none. This review fits, tunes and selects nothing. It reads committed artifacts of
`results/larger-test-v2`, regenerates the two authored episode banks on CPU from pinned code, and
re-derives every reported statistic with independently written code. No GPU, container, process
signal, flag, or `data/bench` access. No repository file other than this one was written.

# Accuracy review — larger-test-v2 (Amendment 6b PASS) — opus, 2026-09-07

**Verdict: the PASS stands. Every registered gate is met, the arithmetic is exactly right, the
freeze is sound, and the harm clause is falsifiable rather than vacuous. What the PASS establishes
is narrower than "the mechanism works on a larger implementation": it establishes that restating
the currently effective obligations at request time — in the register block *or* in plain prose —
recovers a default-transition failure that plain retained history does not. The register form
itself is not shown to contribute anything; the prose control equals or beats it on all three
primary families and beats it significantly on final semantic integration.**

## 0. Method and review-integrity note

I re-derived, from the raw records and a CPU-regenerated bank, and without calling
`slab2_endpoint.primary` or `slab2_v2.harm` for any reported number: the three primary families
(schedule, pairing, within-episode exact-fraction averaging, one-sided sign, Holm-3), the
missing-write-as-failure sensitivity, both harm contrasts, the flip sensitivity, the final-semantic
-integration comparisons, and the record/HTTP/receipt accounting. I re-implemented `change_rounds`
from the registration text and confirmed it agrees with the frozen function on all 64 episodes, and
I recomputed `satisfied[delivery]` and `satisfied[format]` for all 3,328 records directly from the
raw model output text: **0 mismatches** against the stored `outcome`.

Integrity note: at review start (16:06–16:08 EDT) the run's final artifacts were still being
written; `RESULTS.md` changed under me at 16:07:58 and most result files were untracked. They were
committed mid-review at `bcb6f25f`. Everything below is bound to the committed bytes —
`RESULTS.md` sha256 `0df37485…f20c`, `records-R.jsonl` `7c0a78bf…0bf5`, `summary.json` and
`audit.json` byte-identical to my working snapshot. Reviewers of this file should re-hash before
reusing my line numbers.

---

## 1. Accounting and freeze — CLEAN

| Check | Result |
|---|---|
| 3,328 unique records | **Confirmed.** 1024/1024/1024/256 for R/N/T/Q; 3,328 distinct `(episode,arm,turn)` keys, zero duplicates; every lane has exactly 16 turns. |
| Episodes per arm | **Confirmed.** R/N/T 64 distinct episodes each, Q 16. Executing lanes 64/64/64 and 16/16 — note `RESULTS.md:16` correctly shows Q as 16, so "64/64 everywhere" is loose shorthand for R/N/T only. |
| Pinned SHA actually ran | **Confirmed by hash, not by assertion.** All 23 files in `freeze.json.source_hashes` hash identically to their blobs at `e20c3f9b` **and** to the current worktree. `pin-verification.json:2` records the same SHA and an isolated checkout at `/tmp/stencil-larger6b-pinned`; `scripts/larger_test_v2.py:124-132` asserts `rev-parse HEAD`, a clean `git diff HEAD`, `PIN != ROOT`, module resolution inside the pin, and per-file hashes before any GPU work. |
| Primary function unchanged from the frozen FAIL | **Confirmed.** `src/stencil/focus/slab2_endpoint.py` is byte-identical (`95dfa314…d2ec`) to its state at `95fa7fc0`. Amendment 6b changed only the wrapper (`slab2_v2.py:350-371`), which strips the superseded `<=1` breakage failure and adds the harm clause. |
| Registration committed before the first evaluation record | **Confirmed.** `REGISTRATION.md`, `freeze.json` (with `dev_calibrated: true` and `calibration_sha256`) and `dev-calibration.json` were committed in `e20c3f9b` at **13:55:54**; `evaluation-opened.json` records **13:56:29** (35 s later); the lane loop started at 13:56:31 and ended 16:04:24. The registration text is itself in `source_hashes` and matches the contract fixture `tests/fixtures/slab2_cpu_report.md:274-410` exactly, plus one appended DEV-calibration paragraph. |
| Bank opened exactly once | **Confirmed structurally.** `scripts/larger_test_v2.py:151-165` creates `evaluation-opened.json` with `open("x")` and refuses to run if it exists; only one such marker exists, and only one 52-group run is recorded (`groups.json`, 52/52 registered ids in order, zero errors). |
| Verdict computed by the frozen reading function | **Confirmed.** `collect()` (`scripts/larger_test_v2.py:62-79`) calls `slab2_v2.larger_reading` and dumps `summary.json`; `summary.json.reading == "PASS"`, `failures == []`. Not hand-written. `audit.json.frozen_reading_equal` is a re-execution equality check. |
| HTTP/receipt/cost reconciliation | **Confirmed to the unit.** 3,349 receipt files on disk = 8 gate-forward + 8 gate-reverse + 3,328 attempt-1 + 5 attempt-2; +40 cross-container replays = 3,389, matching `http-costs.json`. A 250-record random independent replay of receipt→record (text, token ids, prompt length, `max_tokens=2048`, `temperature=0`, `seed=20260906`, usage) gave **0 mismatches**, and all 5 receipt sha256s I checked matched `receipts.json`. 8,293 local-file hashes, 208 lane journals (64×3+16). GPU held 7,673.196 s = 2.131443 h against a 41,400 s budget. Zero truncation anywhere; max prompt 15,302 (+2,048 = 17,350 < 32,768). |

### Disjointness of the fresh bank — receipts verified, but they cannot fail

I regenerated all four banks and recomputed `lineage_receipt` myself: it is **byte-equal** to the
committed `lineage.json`, and fresh64's seeds, episode hashes, template ids and
content-without-identity fingerprints are disjoint from the spent Amendment-5 eval bank (64), the
DEV bank used by pilots 8 and 9 (8), and each other. I confirmed the DEV episodes generated by
`slab2_v2.bank("dev")` are content-identical to `slab2.bank("dev")`, so DEV really is covered by
the receipt.

**But all four receipts are true by construction and cannot fail** (finding H3):

- seeds: fresh base `2026090706…` vs spent `20260906…` — disjoint by choice of namespace;
- templates: `slab2_v2.py:80` appends `":scoped-realization-6"` unconditionally, so the five
  template families are *identical* after stripping the suffix;
- content / episode hashes: `slab2_v2.py:66-76` applies a fixed prose rewrite to every request; I
  verified the replaced substring is present in **1024/1024** spent-bank requests, so the content
  digest is guaranteed to differ.

Underneath the receipts, the "fresh" bank is largely the same tasks: **1,010 / 1,024 (98.63 %) of
turn-level task expressions already appear in the spent bank**; 198/203 distinct expressions and
244/251 distinct private case-sets overlap; all six obligation-schedule shapes are shared; and
**16 of 64 fresh episodes reproduce a spent episode's exact 16-task expression sequence**
(episodes 48–63, the `aggregate_reduction` family, which also share that sequence with each other
in both banks). The registration is partly honest about this — "same procedural distribution, no
new-family generalization" (`REGISTRATION.md:6-7`) — and the model is stateless across runs, so
this is not leakage into the model. It is a limit on the phrase "fresh bank" in `RESULTS.md:1`,
and it matters because `REGISTRATION.md:3-4` concedes the protocol change was informed by the
spent bank's outputs and audits. The correct description is: **a re-run of substantially the same
task pool under a protocol revised in the light of that pool's previous failures**, honestly
labelled a "successor recipe, not independent confirmation".

---

## 2. Independent re-derivation of the primary — CONFIRMED EXACTLY

My code, my schedule implementation, my exact-fraction sign test, my Holm:

| Family | n | W/L/T | mean gain | one-sided p | Holm-3 | pass |
|---|---:|---|---|---|---|---|
| delivery | 63 | **35/0/28** | 5/9 = 0.555556 | **2.910383046e-11** (= 1/2^35) | 8.731149137e-11 | yes |
| format | 63 | 25/4/34 | 1/3 = 0.333333 | 5.185790360e-05 (= 27841/2^29) | 1.037158072e-04 | yes |
| indent | 64 | 17/15/32 | **exactly 0** | 0.4300250330 | 0.4300250330 | no |

Every figure in `RESULTS.md:22-24` is confirmed to the last digit, including the closed forms.
Holm ordering and step-down are correct. `mean_gain > 0` is required for `pass`, so indent could
not have passed on p alone.

**Within-episode averaging is a no-op for the two significant families.** Each episode has exactly
one scheduled delivery change round and one format change round (64 and 64 in total); only indent
has two per episode (128). So delivery and format are one-observation-per-episode sign tests; the
averaging machinery only bites on indent, the family that failed.

### The missing 63rd episode

`slab2-v2-eval-56`, and nothing else. Its schedule is `indent [10,15]`, `format [12]`,
`delivery [11]`. R raised `IndentationError` at rounds 10–14, so there was no common parsed write
at rounds 11 and 12, and the episode drops out of delivery and format; it survives in indent
because round 15 wrote. Exactly **three** scheduled rounds were dropped run-wide — (56,10),
(56,11), (56,12) — all R-side.

**The exclusion is outcome-dependent, and it is dependent in R's favour**: the single episode
where R broke is the single episode removed from the two families R wins. This is the registered
rule ("common parsed writes"), and the registered sensitivity covers it. Re-deriving with
missing writes scored as failures:

| Family | n | W/L/T | mean gain | p | Holm-3 |
|---|---:|---|---|---|---|
| delivery | 64 | 35/1/28 | 17/32 = 0.53125 | 5.384209e-10 | 1.615263e-09 |
| format | 64 | 25/5/34 | 5/16 = 0.3125 | 1.624571e-04 | 3.249142e-04 |
| indent | 64 | 17/15/32 | 0 | 0.430025 | 0.430025 |

Both gains match `RESULTS.md:22-23`; both remain significant after Holm. **The verdict does not
depend on the exclusion.** `RESULTS.md` reports the sensitivity gains but not these p-values
(finding L3) — they should be printed, because "gain remains positive" is a weaker statement than
"Holm-significant under the adverse reading", and the stronger one is true.

### Cluster sensitivity (finding M4)

Because 16/64 episodes carry one identical task sequence, the 64 paired differences are not 64
independent task draws. Dropping that family, or collapsing it to a single unit, leaves both
results significant: delivery p = 3.7e-09 / 1.9e-09, format p = 3.8e-03 / 2.2e-03, indent
unchanged at ~0.5. The conclusion is robust; the nominal p of 2.9e-11 is nonetheless an
independence-assuming number applied to a bank that is 25 % one repeated task sequence.

---

## 3. The harm clause — LEGITIMATE, not unfalsifiable, but narrower than its own wording

**Re-derivation confirms `RESULTS.md:30-31` exactly**: R:N 61 episodes, 1/0/60, p = 1/2 (Holm-2
1.0), coverage 61 ≥ 48; T:N 61 episodes, 0/0/61, p = 1, coverage 61 ≥ 48; `calibrated = true`.

**DEV-calibrated before the freeze: yes.** `dev-calibration.json` (hash-bound into `freeze.json`
via `calibration_sha256`, both committed at 13:55:54) records pilot-9 FIX-CONFIRMED with R:N and
T:N each 6/8 common-attempt episodes, all ties, p = 1 — exactly at the 6/8 minimum, not comfortably
above it. `null-calibration.json`, also committed pre-run and hash-pinned, enumerates the null tail
and states the minimum detectable effect: **6 all-positive discordant episodes**, per-contrast size
≤ .025.

**Applied to its own negative control: yes**, and identically — `slab2_v2.harm:261` loops
`for arm in "RT"` through the same code path, and `calibrated` requires *both* contrasts to have
coverage and no signal (`:296`). This is precisely the correction the prior astra review demanded
(`results/larger-test-review-astra.md:184`: "Any practical harm margin must be justified
prospectively and applied to the reminder negative control at the same episode unit").

**Is it compliance-conditioned? Yes, in the required direction.** The pair enters only if
*both* arms attempted (`slab2_v2.py:270`), non-attempts are dropped rather than scored safe, and
an episode-level 75 % coverage gate (`:287`, `(3·64+3)//4 = 48`) blocks an arm from winning on
empty denominators.

**Is it unfalsifiable? No — and I can show the decisive fact.** The single real harm event
*entered the test*. At episode 56 the indent change rounds are 10 and 15; R broke at 10;
`indent_attempted` is `true` for R at all five broken rounds (the 4-space statements match the
requested width), so that episode contributes a common-attempt denominator of 2 and a gain of
+1/2 — which is exactly the observed `mean_gain = 1/122`. The clause passes because R broke in one
episode out of 61, not because breakage was defined out of view. Six such episodes would have
tripped it. **This is a bar that passes because the protocol changed, not because it became
unfalsifiable.**

Three genuine limits, none of which change the verdict:

- **M1 — the clause is structurally blind to reply-malformation and cap breakage.** Its own words
  are "syntax/protocol breakage conditional on attempted indent-change obligations"
  (`REGISTRATION.md:41`), but `attempted` returns `False` whenever `snippet()` raises
  (`slab2_v2.py:172-174`) — i.e. for every wrong-path, wrong-fence, malformed-trailer, oversize or
  truncated reply. Those are precisely the protocol breakages the clause names, and they can never
  reach its numerator. In this run there were **zero** such events in any arm, so nothing was
  hidden; but the clause cannot be described as covering protocol breakage in general.
- **M2 — the coverage gate is episode-level, and round-level attrition is unreported.** R attempted
  the new indent width at **90/128** scheduled rounds (70.3 %), N at 96/128 (75.0 %), T at
  **104/128** (81.2 %). 47 of the 61 contributing episodes contribute a denominator of 1 rather
  than 2, so only **75 of 128 (58.6 %)** R:N rounds enter the test while coverage reads 61/64.
  An arm could shed ~40 % of its obligation rounds and still clear the gate. `RESULTS.md:33`
  reports only the episode-level coverage.
- **M3 — one registered disjunct is not implemented.** `REGISTRATION.md:44` defines an attempt as
  the snippet condition "**or** the final parsed change satisfies indent"; `slab2_v2.attempted`
  implements only the snippet condition. The omission is strictly conservative (satisfied-indent
  implies a body line at the requested width), and I verified it changes nothing here.

**M6 — the honest framing of the re-scope.** Amendment 6 narrowed "breakage" to syntax/protocol
only, excluding runtime and semantic failures (`slab2_v2.py:224`, `REGISTRATION.md:29-30`). That
narrowing was recommended by the prior opus review (F1: the old metric mixed in semantic raises)
and was registered prospectively, so it is legitimate. Its consequence must nevertheless be stated
plainly: **the failure mode on which the register arm is now worst — final semantic integration —
has been moved outside the harm gate.** The harm clause passing therefore says nothing about the
cost documented in §5. `RESULTS.md:18` discloses the split; it does not draw the inference.

For completeness: the superseded `<=1` margin would also have passed. `summary.json.breakage_excess
= 1` (R 1 broken episode, N 0), and `src/stencil/focus/slab2_endpoint.py:294,300` fails only on `> 1`. **The
PASS does not depend on the Amendment-6b harm swap.**

---

## 4. The five surviving syntax errors — the repair mechanism has zero demonstrated efficacy

All five are `slab2-v2-eval-56`, arm R, rounds 10–14, all
`IndentationError: unexpected indent (core.py, line 3)`, offset 4. The submission at round 10,
verbatim:

````
```python core.py
def step_10(x):
  """Sum value times weight over records (zero for empty input)."""
    result = 0
    for record in x:
        result += record["value"] * record["weight"]
    return result
```
report: task=A status=ok delivery=staged
````

The requested width at rounds 10–14 is 4. The model put the **docstring at 2** and the
**statements at 4** — the exact hybrid the registration required to raise rather than be silently
normalised (`REGISTRATION.md:21-22`), and which `slab2_v2.snippet` preserves by anchoring only the
`def` line (`:140`). Rounds 11–14 repeat the identical body with the function name incremented.

**Why the repair turn did not fix them.** I verified from the raw HTTP receipts that the repair
prompt is a strict *extension* of the initial prompt (turn 10: 8,368 → 8,820 tokens, first
divergence at index 8,368) — so the feedback genuinely reached the model; the Amendment-6b
plumbing works. The appended diagnostic
(`scripts/composition_pilot8_driver.py:300-305`) is:

```
IndentationError: unexpected indent (core.py, line 3)
Offending line 3:
    result = 0
One syntax repair attempt remains. Correct and resubmit ONLY the same requested
function and its report trailer.
```

Despite the changed prompt, **all five repair responses are identical to their initial submission
in text *and* in generated token ids** — a stronger identity than `residual-errors.json`'s
`identical_text: true`, and one I confirmed directly against `local/http/main-attempt2/…`. The
mechanism is legible: Python blames line 3 (`    result = 0`), which is at the *correct* 4-space
width; the actual offender is the 2-space docstring on line 2. A model told "offending line 3:
`    result = 0`" and separately instructed to use 4-space indentation has been handed a
diagnostic that points away from the defect. Amendment 6's own diagnostic design — "exact Python
exception class/message, filename/line/offset and offending line" (`REGISTRATION.md:23-24`) — is
faithful to Python and pragmatically misleading here.

**Demonstrated efficacy: none.** GPU record: DEV pilot 9 triggered **0** repairs; the full run
triggered **5** and **0** succeeded. The exact one-sided 95 % upper bound on repair success
probability from 0/5 is **45.1 %** — the run cannot even exclude a coin-flip repair rate, let
alone demonstrate one. The only evidence the mechanism ever repairs anything is a CPU regression
that feeds it a hand-written corrected stub. `RESULTS.md:18` says "a zero repair count supplies no
GPU evidence of repair efficacy" — true for N/T/Q, but R's count is 5, and 0/5 is *evidence of
inefficacy*, not absence of evidence (finding L2). `RESULTS.md:9` gets the substance right
("PASS does not establish … effective model self-repair"); the table caption should not be the
sentence a reader takes away.

---

## 5. The caveat the PASS does not cover — tested, and it is the same pattern

Final semantic integration at round 15: **R 45, N 48, T 52, Q 16/16**. Episode-level exact paired
tests (my computation; unregistered and post-hoc, as the brief requests):

| Contrast | discordant | exact two-sided p | one-sided p |
|---|---|---|---|
| R vs N | 1 R-only, 4 N-only | **0.3750** | p(N>R) = 0.1875 |
| **R vs T** | **0 R-only, 7 T-only** | **0.015625** | **p(T>R) = 0.0078125** |
| N vs T | 0 N-only, 4 T-only | 0.1250 | p(T>N) = 0.0625 |

**R versus N (45 vs 48) is noise** — five discordant episodes, p = 0.375. Anyone reporting
"the register arm is lowest" as an R-vs-N competence cost is over-reading three episodes.

**R versus T (45 vs 52) is not noise.** Seven episodes flipped, all in the same direction
(`eval-17, -21, -29, -33, -37, -56, -57`), zero the other way, exact one-sided p = 1/2^7 =
0.0078125; Holm-adjusted across the three pairwise integration comparisons it is 0.0234, still
below .05.

So the plain answer to the question: **yes, this is the same compliance-versus-competence pattern
the program has hit repeatedly, and it has survived into the passing run — but the informative
contrast is R against the prose control, not R against plain history.** Against T, the register arm
buys nothing on any obligation family and gives up seven episodes of working code. Against N it
buys a large, real adherence gain at no measurable competence cost. Both statements are true
simultaneously and `RESULTS.md` reports only the second.

Supporting evidence that this is a pattern and not one metric:

- **Unregistered R vs T on the primary families** (my computation; T ≥ R everywhere):
  delivery 1/0/62 (mean gain +0.016, p = 0.5); format **1 win / 6 losses / 56** (mean gain
  −0.079); indent 10/13/41 (mean gain −0.031).
- **Unconditional adherence at scheduled change rounds** (missing write = fail): delivery
  R 63/64, T 63/64, N 29/64; format R 56/64, **T 62/64**, N 36/64; indent R 86/128, N 86/128,
  **T 90/128**.
- **T vs N is at least as strong as R vs N**: delivery 34/0/30, p = 5.8e-11; format 28/2/34,
  p = 4.3e-07.
- T's reminder is not weaker than the register's content: `t_text` is the full effective-obligation
  set plus the retired "Not binding" list (`slab2.py:348-352`), rendered by
  `renderer.py:117`. It is an information-equivalent prose oracle.

This is exactly the outcome `results/full-program-review-astra.md:189` pre-committed to: *"If T
matches R, report it; R−N alone cannot identify a register-specific advantage."* It is not
reported (finding H2).

### A second, sharper limit on the powered family (finding H1)

The delivery family alone powers the PASS. I checked what it actually tests:

**At all 64 scheduled delivery change rounds the required value is `ready` — 64/64 in the fresh
bank, 64/64 in the spent bank, 8/8 in DEV.** This is structural, not a seed accident: the
scheduled change is a completion/cancellation, after which delivery defaults to `ready`. And
`ready` is the literal printed in the arm-invariant worked example in the system prompt
(`src/stencil/focus/slab2.py:73`: `report: task=A status=ok delivery=ready`). An arm that simply
copied the example's trailer would score **64/64** on the endpoint that powers the verdict.

The endpoint therefore cannot, by itself, distinguish "reads the register" from "copies the
example". An **off-endpoint** diagnostic can, and it exonerates R: across *all* 395
delivery-applicable rounds, R emits the correct value **395/395** (draft 110/110, queued 85/85,
ready 86/86, staged 114/114); T 394/395; Q 91/91; and **N is 346/395 — perfect on draft, queued
and staged, and 37/86 on `ready`**. N's every failure is the same one: after a silent
default-to-`ready`, it keeps emitting the last explicitly stated value.

That is the real finding, and it is a good one: **the primary measures a single, specific,
systematic failure — an obligation that changes by default rather than by statement is not
inferred from retained history — and request-time restatement fixes it completely.** But it is one
transition type, replicated 63 times, whose correct answer coincides with a constant in the system
prompt. Neither `RESULTS.md` nor `REGISTRATION.md` states that the required value is invariant.
`RESULTS.md:39` does say "The scoped system example … remain[s] a possible influence"; the
quantitative form of that caveat belongs in the results table.

---

## 6. Reproducibility and fragility

- **Cross-run control**: `reproducibility.json` — 40 pilot-7 R payloads (8 DEV episodes ×
  turns 0,4,8,12,15), byte-identical requests re-verified
  (`reproducibility-audit.json.byte_identical_requests: true`), **0/40 divergent, 0/8 episodes with
  any divergence**. Executed mid-run after group `T28-31` as registered
  (`freeze.json.replay_after_group`). Correctly labelled descriptive and clustered, not a
  reproducibility claim.
- **Determinism gate**: 8 DEV initial-R payloads forward and reverse, 0 mismatches
  (`determinism.json`). Narrow but registered; it is 8 prompts, not the evaluation bank (L5).
- **Flip sensitivity** — independently re-derived and matching `flip-sensitivity.json` exactly:
  **indent 0** (already non-significant), **format 5**, **delivery 12** adversarial episode flips
  before Holm-3 significance is lost (resulting Holm p 0.0614 and 0.0895 respectively).
- **Is format robust this time? Yes.** The frozen run's format result tolerated **one** flip; this
  one tolerates **five**, and the underlying counts moved from marginal to 25 wins against 4
  losses. `RESULTS.md:35` correctly preserves the original caveat as a caveat about the frozen run
  rather than transferring the new robustness backwards. Five is real improvement but not
  comfortable: format is still the family that would fall first, and it is also the family where
  the prose control beats the register (6 losses to 1 win).
- **Cluster-robust check on the same question** (§2): collapsing the 16-episode repeated-task family
  leaves format at p = 2.2e-03 and delivery at 1.9e-09.

---

## 7. What may now be claimed

Reconciled with `results/full-program-review-astra.md:184-199` and the pre-declared confounds. The
following four sentences are supported by the artifacts as verified above and may be used verbatim:

> On 64 preregistered authored 16-round Python function-editing episodes with frozen
> Qwen3-30B-A3B and gold structured rule events, restating the currently effective obligations in
> the request improved delivery-value adherence at the scheduled change round over ordinary
> retained history — 35 R-wins, 0 N-wins, 28 ties over 63 common-write paired episodes, mean gain
> 0.5556, exact one-sided p = 2.91e-11, Holm-3 8.73e-11 — and improved compact-format adherence
> (25/4/34, Holm 1.04e-04); the indentation family showed exactly zero mean gain (17/15/32,
> Holm 0.43).
>
> The effect is one specific and systematic failure of retained history: at every scheduled
> delivery change the obligation defaults silently to `ready`, and the plain-history arm keeps
> emitting the previously stated value (37/86 correct on `ready`, 309/309 on all other values),
> while both restating arms are essentially perfect.
>
> The result does not identify any benefit of the register representation: the block-free prose
> arm, which receives the same effective obligations as text, equals the register arm on delivery
> (1/0/62), beats it on compact format (1 win to 6 losses) and indentation, and ends with
> significantly more semantically integrated episodes (52 vs 45; 7 discordant episodes all one
> way; exact one-sided p = 0.0078).
>
> The single registered harm contrast — syntax/protocol breakage conditional on both arms
> attempting the indentation change — showed no signal in either R:N (1/0/60) or the T:N negative
> control (0/0/61) at 61/64 episode coverage, on a test whose minimum detectable effect is six
> discordant episodes; this bounds syntax-level harm only, and expressly not the semantic-
> integration cost above.

**Sentences that must not appear**, in addition to the six already listed at
`results/full-program-review-astra.md:194-199` (all of which remain in force):

- "The larger implementation proves the mechanism." It proves request-time restatement, on
  substantially the spent task pool, for one obligation transition, with the register form
  unidentified.
- "A fresh 64-episode bank confirms the earlier design." 98.63 % of turn-level tasks are reused
  from the spent bank and 16/64 episodes reproduce a spent episode's task sequence; the disjointness
  receipts are true by construction.
- "The harm clause shows the register does not damage competence." It excludes semantic and runtime
  failures by registered definition, and that is where the only measured deficit lies.
- "The one-repair mechanism works" / "residual errors are a model limitation the harness handles."
  0/5 on GPU; upper 95 % bound 45.1 %.

**Direct answer to the brief's final question.** This PASS is **not** adequate proof of the
mechanism on a larger implementation. It is adequate proof of something narrower and genuinely
worth having: *on this authored distribution and frozen trunk, an agent that is shown its current
effective obligations at request time reliably tracks an obligation that changes by silent default,
and one that must infer it from retained conversation does not.* It supplies no evidence that the
structured register is the right vehicle for that restatement — its own prose control is at least
as good and semantically better — and it supplies no evidence about automatic admission, stale-rule
removal, generalised coding competence, or any actuator. `RESULTS.md:39`'s claim ceiling is
correctly drawn; the results tables above it do not yet contain the numbers that force a reader to
respect it.

---

## 8. Findings

| # | Grade | Location | Finding |
|---|---|---|---|
| H1 | **high** | `src/stencil/focus/slab2.py:73`; `results/larger-test-v2/RESULTS.md:22,26,39` | The delivery family that powers the PASS tests exactly one transition, and its correct answer is `ready` at **64/64** scheduled rounds — the literal constant in the arm-invariant worked example. Copying the example would score 64/64 on the endpoint. R is exonerated only by an unreported off-endpoint diagnostic (395/395 across all four values vs N 346/395). Neither the invariance nor the diagnostic appears in the results. |
| H2 | **high** | `results/larger-test-v2/RESULTS.md:20-33`; `results/full-program-review-astra.md:189` | R vs T is never reported. T equals or beats R on all three primary families (delivery 1/0/62; format 1 win/6 losses; indent 10/13/41), on unconditional adherence (format 62/64 vs 56/64), and on final semantic integration (52 vs 45, p = 0.0078). The prior program review pre-committed to reporting this exact case. |
| H3 | **high** | `src/stencil/focus/slab2_v2.py:60-111`; `results/larger-test-v2/REGISTRATION.md:74-76`; `RESULTS.md:1` | All four bank-disjointness receipts are true by construction (seed namespace, unconditional template suffix, unconditional prose rewrite of all 1024 requests) and cannot fail. Underneath them, 1,010/1,024 (98.63 %) turn-level tasks are reused from the spent bank and 16/64 episodes reproduce a spent episode's task sequence. "Fresh bank" overstates the receipts. |
| M1 | medium | `src/stencil/focus/slab2_v2.py:171-181,270`; `REGISTRATION.md:41` | The harm clause names "syntax/protocol breakage" but `attempted` returns `False` for every reply-malformation and cap failure, so protocol breakage can never reach its numerator. Zero such events occurred, so no material effect here. |
| M2 | medium | `src/stencil/focus/slab2_v2.py:287`; `RESULTS.md:33` | Coverage is gated at episode level only. R attempted 90/128 indent rounds vs N 96/128 and T 104/128; only 75/128 (58.6 %) of R:N rounds enter the contrast while coverage reads 61/64. Round-level attrition is unreported. |
| M3 | medium | `REGISTRATION.md:44` vs `slab2_v2.py:171-181` | The registered attempt disjunct "or the final parsed change satisfies indent" is not implemented. Conservative direction; verified to change nothing in this run. |
| M4 | medium | `src/stencil/focus/slab2_v2.py:60-89`; `RESULTS.md:22-24` | 16/64 episodes share one identical task sequence, so the exact sign test's independence assumption is not met for a quarter of the bank. Sensitivity: delivery p 1.9e-09, format p 2.2e-03 when that family is collapsed — conclusions hold, nominal p understates. |
| M5 | medium | `results/larger-test-v2/statistical-audit.json`; `RESULTS.md:43` | Described as an "Independent statistical audit", but no generating script exists in the repository, so its provenance is not reproducible from a clone. Its numbers are correct — I reproduced all five independently. |
| M6 | medium | `slab2_v2.py:224`; `REGISTRATION.md:29-30`; `RESULTS.md:18,28-33` | The registered narrowing of "breakage" to syntax/protocol moved the one failure mode where R is measurably worst (semantic integration) outside the harm gate. Prospective and disclosed, but the harm table's "no signal" must not be read as "no cost". |
| M7 | medium | `src/stencil/focus/slab2_endpoint.py:279-285`; `summary.json.per_arm` | `joint_final` is 0 for **every** arm including the gold fresh-context reference Q (0/16), because it requires `satisfied["delivery"]` to hold in compact rounds where the trailer must omit delivery. The metric is structurally unreachable and carries no information. Not gated; no effect on the verdict. |
| M8 | medium | `scripts/composition_pilot8_driver.py:143-146,176` | A record's `prompt_tokens` is the *final* attempt's prompt length, not the first. Sums reconcile exactly (record total 15,921,232 = 15,977,333 − 56,101 + 58,153) but the field name invites double-counting. |
| L1 | low | `RESULTS.md:18` | "A zero repair count supplies no GPU evidence of repair efficacy" is true for N/T/Q; for R the count is 5 with 0 successes, which is evidence of inefficacy (95 % upper bound 45.1 %), not absence of evidence. |
| L2 | low | `RESULTS.md:22-23` | Missing-write-as-failure is reported as a gain only. The adverse-reading p-values are strong (delivery Holm 1.6e-09, format Holm 3.2e-04) and should be printed. |
| L3 | low | `RESULTS.md:33` | "Coverage remains 75 % in both contrasts (6/8 DEV, 48/64 full run)" states the requirement where a reader may take it for the achievement; the achieved figure is 61/64, shown only in the table. |
| L4 | low | `RESULTS.md:11-16` | "Executing lanes 64" is right for R/N/T; Q's 16 is 16/16 of its allocation. Any summary saying "64/64 everywhere" is loose. |
| L5 | low | `results/larger-test-v2/determinism.json` | The determinism gate is 8 DEV prompts forward/reverse. Registered and passed, but it is not a determinism statement about the 3,328 evaluation calls. |
| L6 | low | run artifacts, 16:06–16:08 EDT | At review start the final artifacts were untracked and `RESULTS.md` changed on disk mid-review; they were committed at `bcb6f25f` before I finished. Reviewers should hash-bind before citing. No content discrepancy resulted — my snapshot is byte-identical to the committed files. |

No critical findings. No arithmetic error, no mis-stated count, no gate evaded, no post-hoc
threshold change, and no evidence of the frozen `95fa7fc0` FAIL being touched, re-scored, or
re-interpreted (its bytes and its reviews are unmodified; `RESULTS.md:35` preserves its caveat).

## 9. Verdict

The PASS stands. It was earned under a registration frozen 35 seconds before the bank was opened,
computed by an unchanged reading function on code that hashes to the pinned commit, and it survives
every sensitivity I could construct — missing-write-as-failure, cluster collapse, and 12
adversarial episode flips on the powered family. The harm clause is real: it is falsifiable at six
discordant episodes, it was calibrated on DEV and applied to its own negative control, and the one
harm event that occurred landed inside it.

What it establishes is that **request-time restatement of currently effective obligations recovers a
silent-default rule transition that retained conversation history does not** — decisively, on this
authored distribution, on largely the same tasks as the frozen FAIL. It does not establish that the
register representation is the thing doing the work: the block-free prose control matches it on
adherence and beats it on producing correct code. That gap, and the delivery endpoint's single
invariant transition, are what the next experiment has to attack.
