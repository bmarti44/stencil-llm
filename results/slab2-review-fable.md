# SLAB-2 harness review — one round (fable, independent reviewer)

2026-09-06. CPU only (check 46 holds the GPU). Reviewed commit d7784309:
src/stencil/focus/slab2.py, tests/test_focus_slab2.py, tests/fixtures/slab2_*,
WORKLOG entry, against results/composition-pilot-4-review-fable.md (my Section 5
ruling) and the build brief's registration items as restated in slab2.py's
module docstring and tests/fixtures/slab2_cpu_report.md. No data/bench and no
evaluation episode content read; all probes below use `generate_episode("dev", 0)`
regenerated locally. I ran the committed suite once
(`CUDA_VISIBLE_DEVICES='' pytest tests/test_focus_slab2.py
tests/test_no_side_effect_imports.py`: 92 passed, 1 xfail, 92 s) and ~40
adversarial parser/executor probes; no repo files were edited.

## Verdict

The harness is what was ruled: one fenced whole file plus a one-line trailer,
the harness writes the file and runs the frozen public tests itself, the tool
result is bounded (297 bytes at round 15; `assert < 8192`), and re-emission is
free (`changed_code` scores only new top-level definitions; an identical re-emit
yields `changed == ""`). Every rule text carries the literal replacement value,
the T-floor is a mechanical pre-registered rule (no floor -> `success is None`),
substitution witnesses have executed-trait denominators, and omission traits
reach `success` only through the floor. References pass the real path on all 72
episodes, every mutant fails, and DEV/eval are seed- and template-disjoint with
manifests hash-bound to the source.

Three things would make pilot 5 fail for a harness reason again, and one
registration gap decides GO versus STOP by a factor of 2.2. **NO-GO until H1-H3
and M7 are fixed; GO for the DEV pilot 5 after that** (8 episodes x R/N/T, ~1.1-1.4
GPU-h at the pilot-4 aggregate rate).

## Findings

### H1 (high) — a single syntax slip kills the lane for good; recovery is blocked by `wrong_family`

`Executor.run` writes the file *before* parsing it (slab2.py:379-386:
`target.write_text(code)` then `ast.parse(code)`). A reply with a syntax error is
`executed=True, breakage=True`, the broken file stays on disk, and
`last_parsable` keeps the old text only in memory. Probe (DEV-00, reference at
rounds 0-1, `def broken(:` into policy.py at round 2, references thereafter):

```
r2 broken: executed True breakage True functions {'core.py': ['identity']}
r3 (core.py, correct): breakage True semantic True success False
r4 (core.py, correct): breakage True semantic True success False
r5 (core.py, correct): breakage True semantic True success False
```

Every later round is `breakage` and `semantic` while the model works on the other
file. The feedback never names the broken file — policy.py simply disappears
from `functions` (slab2.py:391-397 skips the name on `SyntaxError`) — and the only
way to repair it is to emit policy.py on a core.py request, which
`check` scores as `wrong_family` (slab2.py:512). This is the whole-file analogue
of the pilot 2-4 spiral: one bad reply, lane dead through rounds 10-15 where every
denominator lives. Fix (~5 lines): parse first; on `SyntaxError` score the reply
as executed+breakage but leave the on-disk file at `last_parsable`, and put
`error="syntax error in policy.py"` in the result. The
`test_free_reemission_and_parsable_repair` case only recovers because the
reference rewrites the *same* file at round 14 (tests:98-101); add the cross-file
case.

### H2 (high) — cap 1024 is below the model's demonstrated verbosity, and the request text invites it

Per-file function counts at round 15 across both banks: {9: 12, 10: 21, 11: 26,
12: 13} episodes. At cap 1024 the budget is (1024 - ~60)/12 = **80 tokens per
function**. The reference spends ~31 (429 tokens for 12 functions); the pilot-4
model spent ~135 per function (pilot-4 review Section 3), which would cap the
scoped file from round ~7 and kill every witness round. The system prompt says
"Use short one-line docstrings" (slab2.py:60), but every request says the
opposite: DEV "Document the function and its boundary behavior"
(slab2.py:222-223), eval "Implement with an explanatory docstring"
(slab2.py:231). Pilot 4's docstring verbosity came from exactly this kind of
instruction. Fix: make the request wording consistent with the one-line
docstring rule (re-freeze manifests; same seeds), and raise `REPLY_CAP` to 2048
as the safety margin — `paired_context_gate` still passes (13,183 + 2,048 <<
32,768). If Brian keeps 1024 as ruled, register it explicitly as a bet that the
model writes <= 80 tokens/function, to be read off the DEV pilot's largest reply.
The report's "largest reply 577/1024" (slab2_cpu_report.md:27) is the *reference*
size, not a model measurement — the report says so, but the headroom claim
should not be quoted forward.

### H3 (high) — the 12 GPU-h gate outcome depends on an unregistered concurrency assumption

`measured_projection` (slab2.py:636-651) multiplies per-arm *lane seconds* by
64/16 and adds load and a 1.25 reserve. Whether a lane-second is a wall-second
under 4-way overlap (composition_pilot.py:313 `max_workers=4`, the pilot-4
setting that produced 24.7 tok/s aggregate) or a sequential second (11 tok/s per
stream) is not registered. Arithmetic on the frozen totals (594,408 output
tokens, 11.22 M input tokens, 2,560 calls, TTFT ~0.8 s/call):

| Rate | Output size | Hours | x1.25 | Action |
|---|---|---:|---:|---|
| 24.7 tok/s aggregate | reference (3.1-4.5k/lane) | 7.25 | **9.1** | 16-round |
| 24.7 aggregate | model-style x1.35 | 9.58 | **12.0** | on the fallback boundary |
| 24.7 aggregate | x1.5 | 10.58 | 13.2 | 12-round fallback |
| 11.0 tok/s per stream | reference | 15.58 | **19.5** | stop |
| 11.0 per stream | x1.35 | 20.83 | 26.0 | stop |

So the 12 GPU-h gate is reachable at 16 rounds only if (a) the registered run uses
the same lane concurrency as the pilot-4 pool and (b) the model's whole-file
output stays within ~1.35x the reference. Register now: `lane_seconds[arm]` =
GPU-held wall seconds of the DEV pilot divided by concurrently held lanes, with
the same `max_workers` in pilot and registered run; and require the DEV pilot to
report measured output tokens/lane per arm so the x-factor is a number, not my
guess. The report's phrase "measured, non-overlapping GPU-held lane allocations"
(slab2_cpu_report.md:14) is not operational as written.

### M4 (medium) — the delivery substitution witness is thin because format retirement masks it

`applicable["delivery"]` requires verbose format (slab2.py:439). Format goes
compact at 10-12 in every episode, and 3 of the 6 permutation shapes put format
before delivery, so the delivery -> ready witness has a denominator in only
half the shapes for 1-2 rounds. Census: DEV 7 opportunities in 6/8 episodes
(dev-01 and dev-07 have none); eval **47 opportunities in 36/64 episodes**.
Indent has 39/321, format (an omission trait) 39/316. My ruling made the
substitution witnesses primary and asked for a format trait with a literal value
(docstring shape); the commit kept format as delivery-omission. That is
defensible under the T-floor rule, but it leaves the primary process witness at
~0.7 opportunities per episode. Either schedule `completes delivery` strictly
before the format event (every episode then contributes 1-2 opportunities;
re-freeze), or register 47 paired opportunities as the acknowledged power for
the process clause. `pilot5_reading`'s ">= 2 kinds in >= 2 episodes" passes
either way (6 DEV episodes).

### M5 (medium) — the trailer parser is stricter than a model reply is likely to be

`parse_reply` (slab2.py:346-360) is a single `re.fullmatch`. Probed on
plausible variants of the DEV-00 reference (OK = parsed):

| OK | FAIL (scored breakage, counts against executed >= 90%) |
|---|---|
| implicit path, `# core.py` comment, trailing newline/space, indented fence | CRLF; leading prose ("Here is the file:"); trailing prose ("Done."); trailing period; `status=OK`; `delivery=` before `status=`; `status=ok task=A`; blank line between fence and trailer; ```` ```py ````, bare ```` ``` ````, ```` ```Python ````; `~~~` or four-backtick fence; `**report:**`; `Report:`; JSON trailer; trailer inside the fence; two fences; `<think></think>` prefix; extra key |

Rejecting two fences and a trailer inside the fence is right per the ruling.
The rest are the cheap tolerances that every pilot so far ended up adding *after*
the run. Register a bounded tolerance set now (strip a leading think block,
prose lines outside the single fence, CRLF -> LF, any key order, optional
trailing period, blank lines before the trailer, case-insensitive `report:` and
`ok`) and record a `tolerances` list in the result so their count is reported,
keeping the "exactly one fence" rule. Extend slab2_replies.json with these.

### M6 (medium) — the 12-round fallback is registered in prose only

`generate_episode` hard-codes `n = 16`, `event_times = (10, 11, 12)`, reinstate
13-15 (slab2.py:121-127); `dry_run` refuses anything but 16 (slab2.py:752);
`paired_clauses` requires 16 (slab2.py:826). A (12, 15] reading therefore costs
another coder round: events would move to ~6-8, shortening the pre-retirement
history (a science change, not a cost trim), plus re-freeze, DEV validation and
review. Either add a `rounds` parameter with the 12-round schedule frozen now
alongside the 16-round one, or register that the fallback path is a new
round. The docstring's "Only 16-round lanes implemented now" is honest; the
report's "triggers 12-round episodes" reads as if it were ready.

### M7 (medium) — no GPU driver exists for slab2

scripts/composition_pilot.py imports the slab v1 `Executor` and envelope.
Pilot 5 needs a driver that: passes `DecodeResult.truncated` into
`Executor.run(..., truncated=...)` (dry_run never does; slab2.py:800), records
`truncated` per row (consumed at slab2.py:598), writes `check()` records with
`eligible_traits=None` during the run, freezes the floor from the 128 T rows,
and only then re-scores. This is a build item, not a defect of the commit, but
launch is impossible on d7784309 alone.

### L8 (low) — R final >= 5/8 remains the gate my pilot-4 review said is unreachable on style alone

Round 15 always has indent applicable at the reinstated width and format compact.
If format floor-fails (pilot 4: delivery emitted on 348/348 rounds), success at 15
is integration + indent; pilot-4 R indent compliance after an event was ~25%.
The brief re-registered 5/8 knowingly; I note it so a 3/8 result is read as
predicted, not as a surprise.

### L9 (low) — feedback does not show the current file

My ruling said "shows the result plus the current file"; the harness shows
counts and function names only and relies on the model's own prior turn. With
H1 fixed, disk == the model's last parsable reply, so this is acceptable; without
H1 the model's belief and the disk diverge silently.

### L10 (low) — minor

- `max_context_per_arm` R/O 13,183 is a DEV lane (eval max 13,101); the report's
  wording "all 72" is correct.
- Production bound uses `assert` (slab2.py:411); fine unless run with `-O`.
- `mutants` under verbose+scoped relabels the drop-delivery mutant as `delivery`
  and then overwrites it (slab2.py:483-491), so "delivery omitted while verbose
  scoped" is never exercised as a mutant; it is caught by `satisfied["delivery"]`
  anyway.

## Verified as ruled (no finding)

- Interface: one fence + one trailer, path optional and restricted to
  core.py|policy.py (no traversal; symlink refused), 16 KiB reply bound,
  harness executes the frozen public tests (`legacy.evaluate_many`), feedback
  bounded and free of hidden cases (`"result ="` asserted absent).
- Literal values: every event text embeds `literal(key, value)` (test asserts it
  for all 72 episodes); T text lists effective obligations with literals.
- T-floor: `check` returns `success=None`/`floor_pending=True` without a floor;
  `freeze_t_floor` demands all 128 unique DEV T rounds, counts unobserved as
  failures, requires passed*2 >= total; compact and verbose have separate
  applicability so verbose compliance cannot lift the compact floor
  (test_compact_floor_cannot_borrow_verbose_success).
- Denominators: indent = stale indent present; delivery = stale and applicable
  (verbose + scoped); format = stale; delivery_scope and language = 0 (never in
  relapse). `raw_relapse` requires den and prior-trait-present.
- Reference/mutants/should_pass: 72 x 16 references pass through `Executor.run` +
  `check`; six mutant labels fail at every DEV round; `hidden_only` passes
  public and fails hidden; three should-pass variants; six authored fixtures.
- Disjointness: seed namespaces `seed*10000 + i` vs `+1000 + i`; template ids
  prefixed by family; `source_sha256` and six dependency hashes bound in the
  manifest; DATA_LINEAGE present in module, manifest, audit and report.
- Accounting reproduces: 4,608 calls; per-lane sums match; registered totals
  R/N 5.96 M/2.91 M in, 238,522 out each; T/O 0.86 M/1.49 M in, 58,682 out each.

## GO / NO-GO

**NO-GO on d7784309 as is.** Blocking before any GPU minute: H1 (do not persist
unparsable files), H2 (request wording vs one-line docstring; cap decision
registered), H3 (register lane-second semantics and concurrency), M7 (driver
with `truncated` plumbing). Recommended in the same pass: M5 tolerance set, M4
schedule decision. After those, **GO for pilot 5 on the 8 DEV episodes x R/N/T at
16 rounds** (~85 k output tokens, ~1.1 h at 24.7 tok/s aggregate, ~1.4 h at 1.35x),
reading in this order: caps and executed fraction, largest reply in tokens,
measured output tokens/lane per arm (the x-factor for H3), then the T floor.
