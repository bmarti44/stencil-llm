# BFCL harness v8 review (fable) — LEG A v7 + Amendments 1–4

Reviewed: commits 2621509 (code) and a145340 (WORKLOG + census-test edit) = HEAD a145340. Governing text:
LEDGER-PLAN.md:623-771 (v7 + LEG A A1/A2/A3/A4). Registration SHA-256 recomputed through the harness's own
extractor = `d3e4e84c01a329c53e03950a83a7e9ca0699a89f7f67c8b63d40114d9721a745` (24,099 chars; contains LEG A
AMENDMENT 3 and 4, excludes LEG B AMENDMENT 3, ends at end-of-file). This value is not yet recorded in WORKLOG; the
preflight certificate would freeze it.

WORKING-TREE NOTE. A coder wrapper (function-vector-focus) held `.review.lock` throughout; `git diff HEAD --stat`
showed only `WORKLOG.md` and `tests/test_clf_probe_check.py` modified (no BFCL file). Every line reference, test and
census below is against a `git archive a145340` mirror in the scratchpad, made a throwaway git repo (clean tree) with
the repo's `models/` and `data/classifier/` linked in, so `git_provenance()` and the classifier manifest resolve.

Hard rules: CPU only (`CUDA_VISIBLE_DEVICES=''`); no model, trunk or GPU process launched or touched; nothing
signalled by me — disclosure: five census invocations exceeded the tool's 600 s limit and were killed by the tool
harness itself (exit 143); they were re-run split by case/turn group. No sealed BFCL row and no IFEval input opened:
every case load used the registered seek-only dev loader; the certificate probe fed a STUB `verified_inputs` dict to
`artifact_meta(split="sealed")` so no sealed loader ran; `test_v4_1_index_preserves_all_frozen_bfcl_files…` (hashes
the mixed files) and `tests/test_sealed_guard.py` were deselected. Only this file was written in the repo.

## Bottom line

The science-facing code is now right on dev: per-target-then-per-role matching with the clamp's failure propagated,
per-role equality asserted before generation on every pressure turn (dev and sealed), a two-directional token-exact
echo clamp, `full` initial-prompt overflow recorded NA and excluded from A3, the truncated baseline and the
competence numerators, the repeated-call canonicaliser shared with execution, a closed and stable module manifest,
and the complete primary-claim table. My census (7 stub scorers, 11/11 dev evicting turns each) reproduces the
coder's: 0 `match_impossible`, per-role equality on every usable comparator turn, |echo_token_delta| ≤ 8, no
`_turn_plan` assertion, 6/11 initial-prompt overflows.

But the harness cannot complete the leg as committed, and launching the registered preflight now would waste it:

* FV8-1 (CRITICAL, fail-closed): the preflight certificate binds `frozen_hashes` verbatim, which since v7 contains the
  per-row hashes of the cases the run LOADED (`verified_bytes.records`) and, on sealed, the mixed source-file hashes
  (`verified_bytes.source_files`, `bfcl_files.cases_*.jsonl`). A dev certificate and a sealed contract therefore differ
  by construction and `validate_preflight_certificate` refuses every sealed invocation. Fixing this changes the
  harness manifest hash that the certificate also binds, so a preflight run under a145340 can never be the certificate.
* FV8-2 (HIGH): `match_impossible` now fires when the unused RESOURCES are fewer than the treatment's targets even when
  the pool's TOTAL columns exceed the quota (dev: case 24 t5 under an all-user stub — 18 user targets/308 columns, 0
  unselected user sentences, 16 tool chunks/1,474 columns → impossible). Amendment 3.1 defines impossibility by total
  columns only; on dev this stops the preflight INCONCLUSIVE, on sealed it voids A1, in both cases by construction.

VERDICT: UNSOUND — two exact fixes (plus the MEDIUM sealed-path items below, which are cheap and change the same
files), re-run the CPU suites and this census, re-register the manifest, then launch the preflight.

## Dev census (CPU, no model, stub scorers), committed v8 code

All 32 dev cases, 115 teacher-forced histories rebuilt with the harness's own `build_teacher_history`; eviction by
`context_layout` (`history_end > K`); plans through the harness's own `_turn_plan` for the treatment and the three
comparators. Evicting turns = 11 (case24 t4/t5, case27 t1-t6, case28 t5, case31 t3/t4), scorer-independent; 6/11
have a full prompt > 40,960 (case27 t2-t6, case31 t4; max 43,804) — the A4.1(a) population, 5 turns / 4 clusters.

| scorer (stub) | user>0 / tool>0 turns | impossible (ctrl/rec/swap) | shortfall | per-role equality on usable turns | echo delta range | clamp residual max | entry-count delta | extension used |
|---|---|---|---|---|---|---|---|---|
| coder v8 `firstuser` (first USER sentence) | 11 / 0 | 0/0/0 | 0 | 33/33 | −4 … 0 | 4 | 0 | 0 |
| `user30tool0` (user 0.3, tool 0) | 11 / 0 | 0/0/0 | 0 | 33/33 | −2 … 0 | 2 | −1 … 1 | 1 |
| hash rate 0.1 | 5 / 9 | 0/0/0 | 0 | 33/33 | −3 … 0 | 3 | 0 … 3 | 0 |
| hash rate 0.3 | 6 / 11 | 0/0/0 | 0 | 33/33 | −7 … 0 | 7 | −1 … 5 | 1 |
| coder v6 30 % hash | 2 / 11 | 0/0/0 | 0 | 33/33 | −5 … 0 | 5 | −1 … 4 | 0 |
| stress user 0.5 / tool 0.1 | 10 / 9 | 0/0/0 | 1 (total exact) | 33/33 | −8 … 0 | 8 | −2 … 3 | 0 |
| stress user 1.0 / tool 0.05 | 10 / 9 | **1**/0/0 (case24 t5, FV8-2) | 9 | 32/32 usable | −1 … 0 on usable turns | 1 | −18 … 2 | 2 |

Other facts: comparator echo entries were always a subset of the comparator's pins; only the last entry was ever
truncated (A3 allowance) and every truncated/extended entry's text was the decoded prefix/extension of its source
columns (verified per entry); width deltas were 0 for ≥ 88 % of tool matches; `tool_swap_echo` cross-role matches 0;
no `_turn_plan` AssertionError on any turn under any scorer. v6's FV6-1 defect (short mislabelled control, rate 0.3
at case24 t5 / case28 t5) is gone: both turns now give exact per-role counts (309 = 309, 723 = 723).

Non-evicting turns (t ≥ 1, 104 turns, echo-only stratum, two stubs): `_turn_plan` never asserts (correctly gated on
pressure); under rate 0.3 `clf_control` is impossible on 9/104 and `tool_swap_echo` on 20/104 short-context turns
(tiny pools) — recorded, no contrast uses them; every NON-impossible comparator stayed within |delta| ≤ 5, so the
ungated schema/preflight delta checks (FV8-3) did not fire on dev.

Plan-building cost (FV8-4): on the six ~42k-token turns each `_turn_plan` call took 25–35 s mean, 68 s max (per
arm; 8 arms per turn), against 0.1–1.4 s on ordinary turns.

## Findings by severity

### FV8-1 — CRITICAL — the preflight certificate can never validate a sealed run (fail-closed leg blocker; a preflight run under a145340 is unusable)
Code: `certificate_payload` (bfcl_mt.py:251-280) copies `meta["frozen_hashes"]` whole; `artifact_meta` builds it
from `_load_cases_verified(args.split)` (bfcl_mt.py:1563-1619): `verified_bytes.records` = the per-row hashes of the
cases loaded for THAT split (32 dev ids on preflight, 64 sealed ids on the sealed run: bfcl_mt.py:360),
`verified_bytes.source_files` and `bfcl_files[cases_*.jsonl]` are populated only on sealed (bfcl_mt.py:361-363, 1602).
`validate_preflight_certificate` (bfcl_mt.py:292-311) requires `payload == certificate_payload(sealed_meta, {})`
exactly. CPU reproduction (dev meta from the real loader; sealed meta from a stub `verified_inputs` with different ids
and one source file, git provenance stubbed clean): payloads differ at `frozen_hashes/verified_bytes/records/*` (all
64 dev entries one-sided), `frozen_hashes/verified_bytes/source_files/…`, `frozen_hashes/bfcl_files/…cases_*.jsonl`.
The unit tests never compare a dev-built certificate with a sealed-built contract (v5 `test_v4_2_certificate_*` uses
one meta for both sides). Because the certificate also binds `frozen_hashes.harness`/`harness_files`, ANY code fix
after the preflight invalidates its certificate.
Fix (bfcl_mt.py): in `certificate_payload` replace the verbatim copy with a split-invariant contract:
`frozen = dict(meta["frozen_hashes"]); vb = dict(frozen.pop("verified_bytes", {})); vb.pop("records", None);
vb.pop("source_files", None); frozen["verified_bytes"] = vb; frozen["bfcl_files"] = {k: v for k, v in
frozen["bfcl_files"].items() if not k.endswith(".jsonl")}` and put `frozen` in the payload (offsets, pins_manifest,
cohorts, function_docs, checker, template, harness, trunk, selector all stay bound; the sealed rows are already
hash-verified by `_load_cases_verified` against the pinned index and `source_files_sha256`). Keep the full
`frozen_hashes` in meta/run identity. Test: build `meta_dev = artifact_meta(dev_args)` and `meta_sealed =
artifact_meta(sealed_args, verified_inputs=<stub with different record ids and a source_files entry>)` (git
provenance monkeypatched clean), write a passing certificate from `meta_dev`, and assert
`validate_preflight_certificate(path, meta_sealed)` returns the digest; assert it still refuses a changed
`offsets`, `harness`, trunk or checker hash.

### FV8-2 — HIGH — `match_impossible` is decided by resource COUNT in the one-to-one pass, not by TOTAL columns (Amendment 3.1)
Code: `_resource_match` pass 1 (bfcl.py:553-555) returns impossible when `take_nearest(required_visit=True)` finds
no unused candidate for a target (bfcl.py:529), after the total-column pre-check (bfcl.py:503-508) has already
passed. Evidence: case 24 t5, all prior user sentences selected (18 targets, 308 user columns): unselected user
resources 0, unselected tool resources 16 with 1,474 columns → pass 1 assigns one 128-column chunk to each of the
first 16 targets, runs out at target 17, returns impossible; the registered rule (combined pool 1,474 ≥ 308) says
possible with `control_role_shortfall`. Under user 0.9/tool 0.05 (14 targets, 20 resources) the same turn is
possible: 18 resources / 1,286 columns matched for a 240-column quota, clamped to exactly 240. On dev the trigger needs
the classifier to select nearly every prior user sentence on a turn whose remaining pool has fewer resources than
targets (0/11 under six stubs, 1/11 under the exhaustive stub; 9/104 non-evicting short-context turns at rate 0.3);
the sealed cohort's long-context pools are large, so the practical risk is a user-heavy selection, but the
consequence is INCONCLUSIVE by construction (preflight stop, bfcl_mt.py:1983-1992; sealed A1 uninformative). This is a
consequence of the v6 instruction "visit every target" (sol V6-1, my FV6-1) that neither of us reconciled with A3.1.
Fix (bfcl.py `_resource_match`): (1) in pass 1, when `take_nearest` finds no candidate for a target, do NOT return —
leave that target's group empty and continue; (2) in pass 2, supplement each under-filled group while candidates
remain; (3) after pass 2 return impossible iff `allow_role_fallback` and `sum(matched columns) < required` (already
excluded by the pre-check, so effectively never) — for `tool_swap_plan` (`allow_role_fallback=False`) keep the
per-target failure, which is A2's registered per-chunk definition; (4) `build_matched_control`'s shortfall quotas and
clamp already make the total exact. Then the echo: with 3 wide entries replacing 18 short ones the framing gap can
exceed the ±16 that the extension of one truncated entry can recover; register (text, orchestrator) and implement that
when the clamp+extension cannot bring |delta| within 16 the comparator is recorded `match_impossible=True,
reason="echo_unreachable"` (A1 uninformative, A4.3 wording) rather than a harness assertion. Tests: the case above as
a synthetic (18 user targets of 10-20 columns, 0 spare users, 16 tool rows × 128) must be possible with shortfall and
exact total; `tool_swap_plan` with two selected tool chunks and one spare must stay impossible.

### FV8-3 — MEDIUM — sealed-path fail-closed is implemented as a crash, and two delta checks are not gated on pressure
`_turn_plan` raises `AssertionError` on a column mismatch or |delta| > 16 (bfcl_mt.py:1012-1025) on every path;
Amendment 4.3 registers "a violation makes the affected contrast uninformative and is recorded". A raise inside the
sealed run aborts mid-cohort with no path to completion except a code change (new manifest hash, new registration,
cohort partly consumed). Separately, `assert_case_record_schema` (bfcl.py:1243-1246) and the preflight
`excessive_echo` stop (bfcl_mt.py:1993-2009) test |delta| > 16 on EVERY turn including non-evicting echo-only turns,
while `_turn_plan` and `assert_dev_invariants` gate on `pressure_triggered`; a non-evicting undershoot (all-whole
comparator entries, fewer entries than the treatment — nothing to extend) would crash `run_case` after the GPU work.
Dev census: no non-impossible non-evicting delta exceeded 5, so this is a sealed-robustness item, not a dev blocker.
Fix: (i) in `_turn_plan` on a pressure turn, instead of raising, set `match_impossible=True` with
`invariant_violation: "columns"|"echo_delta"` in the selector row (dev: `assert_dev_invariants` still fails the
family and stops the preflight; sealed: the contrast is uninformative and recorded — A4.3); (ii) gate the schema and
`excessive_echo` delta checks on `eviction["pressure_triggered"]`; (iii) test: a sealed-shaped record with a
non-evicting delta 17 validates; a pressure-turn delta 17 with `match_impossible=False` is refused.

### FV8-4 — MEDIUM — plan-building re-encodes the whole context per probe; ~4 min of CPU per 42k-token evicting turn, inflating `seconds` and the 30 GPU-h projection
`_echo_clamp.measure` (bfcl_mt.py:732-734) tokenizes the full echoed context on every probe; the truncation search
(bfcl_mt.py:749) probes up to 128 prefixes and the extension (bfcl_mt.py:775) up to 128 more, per comparator, and
`_turn_plan` rebuilds all three comparators for each of the 8 arm calls. Measured: 25–35 s mean / 68 s max per arm
call on the six ~42k-token dev turns (0.1–1.4 s elsewhere) → ≈ 4 min per evicting long turn, ≈ 45 min over the dev
preflight, counted in `arms[*].seconds` and hence in `projected_sealed_hours`. Fix (exact count, smaller work): measure
from the current user message's `<|im_start|>` marker only — `seg = context.find("<|im_start|>user\n",
<pool_start of the current message>)`; `measure(rows) = len(encode(_echo_current_user(context, rows,
close=close)[seg:])) − len(encode(context[seg:]))` — identical to the full-context difference because added/special
tokens split pre-tokenisation, so nothing before the marker changes; cache `encode(context)` once per turn (it is
computed at bfcl_mt.py:731 and again at 767) and binary-search the truncation prefix with a final linear scan only
around the boundary. Assert equality with the full-context measure in a unit test on a long fixture.

### FV8-5 — LOW — `full` case `final_pass` on records counts NA (initial-prompt overflow) turns as fails
`run_case_arm` (bfcl_mt.py:1419) filters `turn["pass"] is not None`, but A4/FV6-2 made NA passes `False`, so a
`full` case with an initial-prompt overflow has `final_pass=False`. `_arm_summary.final_pass` excludes such cases
(right), but the competence floor `full_long_cases` (bfcl_mt.py:2063-2064, 2100) uses the record field: on dev cases
27 and 31 can never count, so the 2/8 floor is judged on 6 cases (stricter than registered "excluded from full's
final-pass reporting"; could force a spurious 4B fallback). Fix: `all(turn["pass"] for turn in turns if not
turn.get("na"))` at 1419 and compute `full_long_passed` over long records without an `initial_prompt` phase (n
reported as the post-exclusion count). Test: synthetic record with one NA turn and all other turns passing →
`final_pass=True`.

### FV8-6 — LOW — manifest and provenance residuals
`harness_manifest` (bfcl_mt.py:206-249) is closed and stable: CPU check — the same 25-entry manifest before and after
importing every module the run path loads (`torch`, `stencil.qwen3`, `stencil.selector_v2`, `stencil.stats`);
`stencil.bench`/`vendor.ifeval` are NOT loaded by the BFCL import chain (EOS ids are inline at bfcl_mt.py:477).
Residuals: `scripts/__init__.py` is loaded (the `scripts.bfcl_mt` import path) but excluded; the `stencil.bench`
exclusion (bfcl_mt.py:236) silently tolerates it if some future path loads it — replace with an assertion
`"stencil.bench" not in sys.modules` at manifest time; git provenance is in meta (not the certificate — fine), and
`results/*.md` are not gitignored, so review files must be committed before a sealed run or
`assert_clean_git_for_sealed` refuses (intended, but note it in the launch checklist).

### FV8-7 — LOW — `tool_swap_echo`'s retained user rows carry no `_echo_source_columns`
`tool_swap_plan` copies treatment user rows with `dict(row)` (bfcl.py:780) without `_decode_row`, so
`_echo_clamp`'s extension (bfcl_mt.py:769-771) falls back to `source = pinned` and cannot extend them; on dev the
last entry was truncated, not under, so no effect. Fix: route them through `_decode_row(row, row["pinned_columns"],
tokenizer, context)`.

## Disposition of prior findings (v8 code, a145340)

| finding | status | evidence |
|---|---|---|
| FV6-1 / sol V6-1 nearest matching aggregate stop; clamp failure discarded | CLOSED (new deviation FV8-2) | per-target pass 1, per-group supplementation (bfcl.py:553-576); `match_impossible = clamp_failed` (bfcl.py:627-641, 789-794); `_turn_plan` asserts per-role/total before generation (bfcl_mt.py:1013-1025); schema repeats it on the sealed result path (bfcl.py:1264-1286); census 33/33 exact under 6 stubs, v6's two failing turns now exact |
| FV6-2 / sol V6-6 initial-prompt overflow NA | CLOSED except FV8-5 | `position_overflow_result(phase)` (bfcl.py:856-876): `na=True, truncated=False` only for full+initial_prompt; `run_case_arm` records phase (bfcl_mt.py:1214-1236); `_safety` counts `truncated` (False), `_arm_summary.final_pass` excludes initial_prompt only, `per_turn_pass` and preflight `full_long_turns` skip `na`, A3 excludes on `overflow_phase == "initial_prompt"`; v7 tests cover all three phases |
| FV6-3 echo undershoot | CLOSED on dev | extension of the last entry from `_echo_source_columns` (bfcl_mt.py:766-786, bfcl.py:409-412); census extension engaged on 4 turn-arms, residual ≤ 8; framing-gap regime remains (FV8-2 text) |
| FV6-4 / sol V6-3 sealed fail-open; preflight counts | CLOSED (FV8-3 on the crash form) | `_turn_plan` asserts on every path; `invariants.match_impossible/shortfall_counts/delta_counts/echo_clamp_residual_counts/echo_entry_count_deltas` (bfcl_mt.py:1849-1854, 1946-1951); preflight stops on any dev `clf_control` impossible (1983-1992) |
| FV6-5 / sol V6-5 manifest closure, git provenance | CLOSED (FV8-6 residuals) | closure verified by CPU import test; `git_provenance` in meta, sealed refuses dirty in `main()` and `artifact_meta` (bfcl_mt.py:179-203, 1558, 2245-2246) |
| FV6-6 dead seed | CLOSED | `seed` removed from all matcher APIs; `control_tie_break` in meta and certificate; `same_role_control_spans` keeps its seed (v2 API) |
| sol V6-2 bytes verified | CLOSED | per-row bounded read hashed against the pinned index before id/decode (bfcl_mt.py:130-147); function docs decoded from the verified bytes (373-386); checker files compared to pins; sealed additionally binds the mixed source files (334-341); mutation tests v7 |
| sol V6-4 canonicaliser | CLOSED | `canonical_call = normalize_call` shared by `call_to_python`, the repeated-call set and the decision point (bfcl.py:997-1022; bfcl_mt.py:633-673); qualified-name test v7 |
| v4 F1-F10, BFCL-V4-1..7 | CLOSED as in the v6 reviews | no regression found: seek-only loader, certificate gates, claim table (8-row test + code bfcl.py:1561-1587), truncated-degenerate, tool-swap order, scorer truncation count, invariant families with `{passed, n}`, non-evicting stratum, cohort-exact summaries |

## CPU verification log
`pytest -p no:cacheprovider tests/test_bfcl.py tests/test_bfcl_evict_v{2..8}.py -k "not real_dev and not
test_v4_1_index_preserves_all_frozen_bfcl_files"` in the mirror → 90 passed + the 5 git/weights-dependent tests
re-run after linking (all passed) = 95 passed, 3 deselected (two real-dev censuses, replaced by my own; the mixed-file
hash test). Scratchpad scripts (not committed): `v8_census.py` (evicting and non-evicting modes, 7 stubs, per-entry
provenance, plan timing), `v8_pool.py`/`v8_pool2.py` (FV8-2 pool probe), `v8_cert.py` (FV8-1), `v8_manifest.py`
(closure/stability), `v8_reg_hash.py`, `v8_span.py` (token spans cover candidate text: 3,230 candidates, 0 short).
No model, GPU, or sealed content touched.

## VERDICT: UNSOUND

May the registered dev preflight be launched under a145340? **No.** Its certificate would be refused by every sealed
invocation (FV8-1), and the fix re-hashes the harness that the certificate binds, so the preflight would have to be
repeated. Required, in order:
1. FV8-1 — split-invariant certificate contract + the dev-vs-sealed round-trip test.
2. FV8-2 — total-column impossibility for `clf_control` (per-target kept for `tool_swap_echo`); text note for the
   echo-unreachable case.
3. FV8-3 — record-and-uninformative instead of raise on the sealed path; gate the schema/preflight delta checks on
   pressure.
4. FV8-4/5/6/7 — local echo measurement (before the preflight, since it lowers the measured cost), NA-aware
   `final_pass`, manifest residuals, `_decode_row` for retained user rows.
Then re-run the v2–v8 suites and the census (per-role equality under ≥ 2 keep rates plus a user-exhaustive stub must
show 0 impossible), record the new registration hash `d3e4e84c…` and the new manifest hash in WORKLOG, commit, and
launch the preflight from a new output directory.
