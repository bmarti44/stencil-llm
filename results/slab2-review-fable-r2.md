# SLAB-2 harness review — closing round (fable, independent reviewer)

2026-09-06. CPU only (check 47 holds the GPU). Reviewed fix commit 8e037722
("Fix SLAB-2 review findings and freeze Amendment 1") against my round-1 review
results/slab2-review-fable.md: SLAB-2 Amendment 1 (tests/fixtures/slab2_cpu_report.md),
src/stencil/focus/slab2.py, scripts/composition_pilot5.py, tests/test_focus_slab2.py,
tests/test_focus_slab2_driver.py, the re-frozen manifest/audit. No data/bench and no
evaluation episode content read; probes regenerate `generate_episode("dev", 0)`
locally, eval-family checks are aggregate counts only. No repo files edited; the
only files I created are under my scratchpad (worktrees for the SLAB-1 bisect, a
CPU-stub pilot output) and this report.

What I ran myself (all `CUDA_VISIBLE_DEVICES=''`):

- `pytest tests/test_focus_slab2.py tests/test_focus_slab2_driver.py tests/test_no_side_effect_imports.py`
  -> **110 passed, 1 xfailed, 74 s** (matches the report's final validation).
- 37 adversarial parser probes through `Executor.run` (table under M5).
- Cross-file syntax-error probe reproducing my round-1 H1 scenario (under H1).
- All 72 episodes x 12 rounds of the frozen fallback schedule through the real
  `Executor.run` + `check` path with freeze receipts: 0 failing rounds.
- Independent delivery-witness census for both schedules; cost-table arithmetic
  recomputed from the frozen audit totals.
- `scripts/composition_pilot5.py --cpu-stub --out <scratchpad>` (16 rounds):
  32 lanes / 512 calls in 6.7 s, floor.json written before scored.json,
  raw.jsonl rows carry `floor_pending=True, success=None`.
- The two SLAB-1 failures bisected across five pre-SLAB-2 commits in isolated
  scratchpad worktrees.

## Verdict

Every round-1 finding is closed by the artifact, with evidence below. Two new
items surfaced in the GPU adapter that were not observable in round 1 because the
driver did not exist; both are one-line transport settings, neither touches the
science, and one of them must be verified (or fixed) before the first GPU minute.
**GO for pilot 5** on the 8 DEV episodes x R/N/T at 16 rounds on the qualified
vLLM backend, conditional on the pre-launch instruction at the end.

## Round-1 findings

### H1 (high) — parse-before-write — **resolved**

`Executor.run` now parses before any disk mutation (slab2.py:461-478): on
`SyntaxError` the result is `executed=True, breakage=True,
category="syntax_error", error="syntax error in <path> at line N: <msg>"` and the
function returns before `write_text`, so disk stays at `last_parsable`. My round-1
probe, replayed on 8e037722 (DEV-00, references at rounds 0-1, `def step_2(:`
into policy.py at round 2, references thereafter):

```
r2 policy.py executed=True breakage=True error="syntax error in policy.py at line 15: invalid syntax"
disk == last_parsable[policy.py]: True
r3 core.py   breakage=False wrong_family=False success=False passed=3 failed=1
r4-r6 core.py same (the missing step_2 keeps one public test red; not breakage)
r7 policy.py breakage=False wrong_family=False success=True passed=8 failed=0
```

The lane is no longer dead: later rounds are neither `breakage` nor `semantic`
by contamination, and the repair at the next policy.py request scores as a
normal success, not `wrong_family`. `test_cross_file_syntax_recovery` covers
exactly this path (asserts bytes-identical disk, file and line in the error, no
wrong_family through round 15). Residual (low, L11 below): the file/line message
appears only on the offending round; rounds 3-6 show `failed=1` and the missing
name is only implicit in `functions`.

### H2 (high) — cap and docstring wording — **resolved**

`REPLY_CAP = 2048`, `SYSTEM_PROMPT` says "Reply cap 2048 tokens". I checked all
1,152 requests (8 DEV + 64 eval, 16 rounds): 1,152/1,152 contain "short one-line
docstring", 0 contain "explanatory", "boundary behavior" or "Document the".
Manifests and audit were re-frozen with the same seeds (SCHEMA 4; max context
R/O 13,333, N 7,171, T 8,234; 13,333 + 2,048 = 15,381 < 32,768; `paired_context_gate`
test updated to `REPLY_CAP`). Largest reference reply measured by me: 577 tokens
over all 72 x 16 (473 on DEV alone, per the CPU-stub summary). The report now
states explicitly that 577 is reference size, not model headroom. Budget at
cap 2048 with 12 functions is ~165 tokens/function, above the pilot-4 model's
~135.

### H3 (high) — lane-second semantics and cost table — **resolved**

- `MAX_WORKERS = 4`; `measured_projection` refuses any `max_workers` other than the
  registered 4 (test covers `max_workers=1`); `run_pilot` refuses
  `max_workers != 4`. Formula `(load + 1.25 * sum(lane_seconds[a] * {64,16}[a])) / 3600`:
  load charged once, reserve on lane allocations only, as the amendment says.
- Driver semantics: arms run sequentially, each arm as two fixed groups of 4
  DEV lanes; `lane_seconds = group_wall / len(group)` plus an equal share of the
  non-group overhead (`(held - charged) / 32`, which includes floor/rescore CPU
  time while the server is held — conservative). Registration.json records the
  definition string; summary.json records `lane_seconds`, `gpu_held_seconds`,
  `output_tokens_per_arm` (8 per arm) and `largest_reply_tokens`, so the x-factor
  is a number read off the pilot. `test_measured_lane_allocations_with_cpu_injected_decoder`
  checks the allocation sums to the held wall with a simulated clock.
- Cost table: recomputed from the frozen audit totals (594,702 output tokens =
  238,642 x 2 + 58,709 x 2; 2,560 calls; 0.8 s TTFT):
  9.071182 / 19.483270 / 11.997207 reserved hours — identical to the frozen
  `cost_table` in slab2_cpu_audit.json and the report table. Note
  `test_sensitivity_table_arithmetic` pins the formula on the *pre-amendment*
  total 594,408; it checks arithmetic, not the frozen table — fine, since I
  verified the frozen table directly.
- The registered run (64 episodes) must reuse the same grouping (same-arm
  groups of 4, 4 workers); the driver only knows DEV today, so that is a
  requirement on the future registered-run driver, not on this pilot.
- Context: the qualified backend (WORKLOG "vllm-qual", registration 22cbbfa9)
  measured B1 18.7 tok/s per stream and C4 aggregate 39.9 tok/s, better than
  the pilot-4 rates (24.7 / 11) the table assumes. The table is a pre-written
  sensitivity, not a projection; the pilot measures.

### M4 (medium) — delivery witness power — **resolved**

`generate_episode` swaps the delivery/format positions whenever the draw puts
format first (slab2.py:146-150), leaving the RNG stream and every other draw
intact. Independent census (both schedules): DEV 11 opportunities in **8/8**
episodes; eval 87 opportunities in **64/64** episodes (round 1: 7 in 6/8 and
47 in 36/64). Registered minimums (>=7/8, >=56/64) are enforced by
`witness_census` and recorded in the manifest. Format stays a floor-gated
omission trait, as registered. Side effect worth naming: the six ordering
shapes collapse to three (delivery always precedes format); that is a
registered choice, not a defect.

### M5 (medium) — parser tolerance set — **resolved**

`parse_reply` is now a staged grammar with a `tolerances` label list carried in
every execution result (and therefore in raw.jsonl). All 37 probes on the DEV-00
round-0 reference (policy.py, `report: task=B status=ok`):

| Accepted (executed, tests pass) with label | Rejected (executed=False, breakage, category) |
|---|---|
| CRLF (`crlf`); "Here is the file:" and a two-line paragraph before the fence (`leading_prose`); "Done." after the trailer (`trailing_prose`); trailing period; `status=OK` (`status_case`); reversed key order (`key_order`); one and two blank lines before the trailer (`blank_before_trailer`); ```` ```py ````, bare ```` ``` ````, ```` ```Python ```` (`language_tag_*`); `<think>...</think>` prefix (`leading_think`); `Report:`/`REPORT:` (`report_case`); all ten combined in one reply (ten labels); explicit path tag; trailing whitespace; indented fence; a code string containing three backticks; prose with the word "task" | `**report:**` and JSON trailer (`trailer_count`); `~~~` and four-backtick fences, two fences (`fence_count_or_kind`); trailer inside the fence and "Setting task=A now." before the fence (`misplaced_trailer`); extra key `note=x` and `delivery=a b` (`trailer_key_or_value`); `status=ok` after the trailer (`extra_trailer`); empty fence (`fence_syntax`); `<think>` block containing `<` (`think_block`) |

The accepted column is exactly the registered tolerance set; the rejected column
is the registered breakage set plus the "exactly one fence" rule I asked to keep.
slab2_replies.json grew from 6 to 18 rows with per-row `tolerances` asserted.
One observation, not a finding: the think regex is `[^<>]*`, so a think block
containing a `<` comparison is categorized breakage. The renderer forces the
non-thinking prefix `<think>\n\n</think>` (renderer.py:123), so the model does
not emit think blocks on this path; if a future run enables thinking, widen the
regex first.

### M6 (medium) — 12-round fallback — **resolved**

`n_rounds` (registered `validate_rounds` in {16, 12}) threads through
`generate_episode`, `bank`, `dry_run`, `freeze_t_floor` (96 rows), `pilot5_reading`,
`paired_clauses`, `witness_census` and the driver; `fallback_banks` are frozen
in the manifest. Verified on all 72 episodes at 12 rounds through the real
executor: 0 failing reference rounds; retirement 6/7/8; reinstatement DEV 9,
eval 10 (27) / 11 (37); task switches 2/4/5 in 72/72; largest 12-round reference
440 tokens. Cost rule: `pilot5_reading(..., 13, n_rounds=12)` -> `stop` (no
second fallback), and `run_pilot(n_rounds=12)` on GPU refuses without a measured
16-round projection in (12, 15]. The report's wording now says the fallback
"requires fresh complete 12-round DEV validation" rather than implying it is
free.

### M7 (medium) — GPU driver — **resolved, with two pre-launch items (N1, N2)**

scripts/composition_pilot5.py drives `loop.generate_once` with the same
`Session/Register/Request/Journal` construction as `dry_run` (I diffed the two:
identical request fields, `max_tokens=32768 - REPLY_CAP`, DEV `turn.events`).
`DecodeResult.truncated` is required by the decode wrapper, passed to
`Executor.run(..., truncated=...)`, stored per row, and consumed by
`pilot5_reading` as `cap_fraction`. `test_vllm_truncation_through_real_driver`
drives the real `VLLMDecoder` with an injected transport (turn 0
`finish_reason="length"`): row `truncated=True`, execution `category="truncated"`,
`executed=False`, journal `truncated: true`, EOS stripped from `output_ids` and
recorded separately. Raw records are written pending-floor as each round
completes; `floor.json` is written before `scored.json`; `rescore` reads the
saved per-round checks, never a later workspace. CLI smoke through `main()`
on CPU stub: 32 lanes, R final 8/8, null GPU cost, `eligible=False` — the
driver cannot mint eligibility from the reference. The script is listed in
`GPU_ENTRY_SCRIPTS` for the no-side-effect import test.

### L8 (low) — R final >= 5/8 on style alone — **open (by design; stands as a prediction)**

Unchanged; the gate is registered knowingly. Read a 3/8 as predicted.

### L9 (low) — feedback shows names, not the file — **resolved via H1**

With parse-before-write, disk equals the model's last parsable reply, so the
model's belief and the workspace no longer diverge silently.

### L10 (low) — minor — **open (low, unchanged, not blocking)**

`assert` for the production feedback bound and the mutant relabel under
verbose+scoped were not part of the fix pass; neither affects pilot 5.

## New items from the driver (not visible in round 1)

### N1 (medium) — HTTP timeout 300 s vs a capped 2048-token reply at 4-way concurrency

`VLLMDecoder._post` uses `urlopen(..., timeout=300)` (composition_pilot5.py:39).
At the qualified C4 aggregate 39.9 tok/s with 4 lanes, a stream runs ~10 tok/s,
so a reply that hits the 2,048 cap takes ~205 s plus prefill of a 13k prompt —
inside 300 s but with ~30% margin; at pilot-4 rates (24.7 aggregate, ~6 tok/s
per stream) it is ~330 s and times out. A timeout raises inside a lane, the
`future.result()` re-raises, and `run_pilot` aborts with no resume (raw.jsonl of
finished rounds is kept). One-line change: `timeout=1200`. The qualification
replay used `min(180, deadline)` at max_tokens 512, so 300 s was never tested
at this cap.

### N2 (medium) — EOS handling depends on the server returning the terminal id; no guard

The adapter sets `eos` only when `finish_reason == "stop"` and `token_ids[-1]`
is `<|im_end|>`/`<|endoftext|>` (151645/151643), else `eos=None` silently. With
`eos=None`, `loop.py:342-344` appends **no** terminator after the assistant
turn, so every later prompt in the lane would be malformed and the pilot would
be measuring a rendering bug. The qualified request set (results/quick-checks/
vllm-qual/request-parameters.json) passed `stop_token_ids=[151645,151643]` and
observed the stop token in the returned ids ("max_tokens 512 including stop
token"); the driver omits `stop_token_ids` and relies on the checkpoint's
generation_config `eos_token_id=[151645,151643]` producing the same behaviour,
and it uses `stream=False` where qualification used `stream=True`. Probably
identical, but "probably" is the wrong word before 1-2 GPU-h. Fix is two lines:
add `stop_token_ids=[151645, 151643]` to the payload (matching qualification)
and raise when `finish_reason == "stop"` and the last id is not terminal.

## The two SLAB-1 (v1) failures — confirmed pre-existing and unrelated

Reproduced at HEAD: `tests/test_focus_slab.py::test_manifest_hashes`
(`system_sha256` 0195e842... vs frozen b69bc792...) and `::test_dev_loop_dry_run`
(round-0 prompt 981 vs frozen 879). Bisected in isolated worktrees with the
tokenizer linked in: **both pass at de1e3182** (Amendment 2 registration);
`test_manifest_hashes` fails from **f83048fd** ("Fix composition append
boundaries and clarify registered indent values", which changed the v1 system
text); `test_dev_loop_dry_run` fails from **981658a8** (pilot-4 Amendment 3);
both fail unchanged at 244c701d, e4d5f2d0 (= d7784309^, the last commit before
SLAB-2 existed) and 8d02a037. So they are composition-pilot-4 amendment
fallout: the shared renderer/v1 system text moved and the v1 goldens
(slab_manifest.json, slab_dev_golden_amendment2.json) were never re-frozen.
SLAB-2 has its own fixtures and its own system prompt; nothing in slab2.py or
the SLAB-2 fixtures depends on the v1 goldens.

Do they matter? Not for pilot 5. They matter for suite honesty: two red tests
on main that everyone now knows to ignore is how a real regression gets ignored
next week. After the pilot, a coder should either re-freeze the v1 goldens with a
WORKLOG line naming f83048fd/981658a8 as the cause, or mark them superseded by
the Amendment-3 fixtures with an explicit skip reason. Not before launch.

## GO / NO-GO

**GO for pilot 5** — 8 DEV episodes x R/N/T (plus O for cost) at 16 rounds,
`max_workers=4`, on the qualified vLLM image, with the driver as committed
**after** the pre-launch instruction below. The science-side harness (interface,
parse-before-write, cap, wording, witnesses, floor, fallback, cost semantics)
is closed; nothing remaining is a science change.

Pre-launch instruction (GPU owner / one coder pass, no science change, rerun
`tests/test_focus_slab2_driver.py` afterwards):

1. In `VLLMDecoder`: add `stop_token_ids=[151645, 151643]` to the payload and
   raise `ValueError` when `finish_reason == "stop"` and `ids[-1]` is not a
   terminal id (N2); set `timeout=1200` (N1). If Brian prefers zero edits: make
   one manual `/v1/completions` call with `return_token_ids=true` at
   temperature 0 and confirm `token_ids[-1] in {151645, 151643}` on
   `finish_reason="stop"`, then after the first lane's first round check
   `loop.jsonl` has a non-null `eos` before letting the pool continue.
2. Launch with `--model`, `--endpoint`, measured `--load-seconds`, `--n-rounds 16`;
   register the pid per the process-ownership rule.
3. Read in this order: `cap_fraction` and `executed_fraction`;
   `largest_reply_tokens` against 2,048; `output_tokens_per_arm` per lane
   against the reference 3,131-3,720 (the H3 x-factor); `lane_seconds` and
   `projected_gpu_hours` against 12; only then the T floor and `kinds`. A
   projection landing in (12, 15] triggers the frozen 12-round fallback with a
   fresh DEV validation, never fewer arms; anything above 15 stops.
