# SC1 harness v3 re-review — fable (2026-09-04, CPU-only, read-only)

Reviewed commit eff241b (HEAD c477397 adds only the WORKLOG handoff). Code files are byte-identical between the
manifest's `harness_commit` f470bd2 and eff241b (`git diff --stat f470bd2 eff241b` touches WORKLOG.md,
data/sc1/smoke/README.md and the regenerated smoke data only), so the freeze candidate is code@f470bd2 + data@d567eac,
as the handoff states. Inputs: results/sc1-harness-v2-review-astra.md (R1–R8 and its seven PARTIAL rows),
results/sc1-harness-v2-review-fable.md (N1–N10), WORKLOG.md "sc1-harness-v3 handoff" (finding -> commit + test map),
data/sc1/STAGE1-CLAUSES.md, data/sc1/registration-snapshot.md, data/sc1/smoke/* (README, manifest, validation), the
three code files, tests/test_sc1.py.

Hard rules kept: CPU only; no model or GPU process launched (the only model-adjacent work was the `tokenizers`
Qwen3-4B tokenizer); foreground only; no process signalled; no sealed IFEval/BFCL cohort file read; the only repo write
is this file (`git status` clean before and after apart from it). Probes ran as a pytest module from the scratchpad
(`test_sc1_probe_v3_fable.py`, 14 cases, harness functions only, temp directories only; the registration-log fixture
from tests/test_sc1.py was imported so no probe could touch WORKLOG.md).

## What I ran (CPU)

- `CUDA_VISIBLE_DEVICES='' uv run pytest -q -p no:cacheprovider tests/test_sc1.py` -> **127 passed in 346.95 s**
  (v2: 93; handoff's four-file run 136 = 127 + 9, consistent).
- `verify_manifest(data/sc1/smoke/manifest.json)` -> OK: manifest_id
  8b3bbb76a7e34ce005bd28c5a416b7e88e1c87da341b387438614d0e4b93222d, file sha256
  6b929695f9472a58aa13c5f9a36c2d81073bfdf93c48da3913aaee9463ac51e9, harness_commit f470bd2, 44 files, no
  `LEDGER-PLAN.md` entry, `science_hash` 37c5759e4a91f45389f49e93bbc4c13bf08ddf1d5a2c82616c64b78325e58d81 ==
  files[data/sc1/registration-snapshot.md]; `load_manifest_bank` -> 8; every frozen episode equals a fresh
  `expand_source` with the real tokenizer (dict and digest equality); in-memory `validate_bank(data/sc1/smoke)` ->
  references_pass 8.
- Snapshot bytes recomputed independently: LEDGER-PLAN.md from the second `## SC1` heading (line 912) to EOF is
  37,375 bytes, AUTHOR-CONTRACT.md is 16,642 bytes, the snapshot is 54,017 bytes and equals their concatenation with
  no inserted bytes; sha256 as above. The v2 section is the last top-level `## ` heading in the ledger.
- Real-tokenizer pressure report from `validate_bank` (my numbers; equal to README/validation.json):

| ep | U | real U | B | rule budget skips | echo omit | rule pins filler/real pieces (cols) | max turn tokens | filler turns | evidence turns |
|---|---:|---:|---:|---:|---:|---|---:|---|---|
| smoke-00 | 2303 | 47 | 256 | 207 | 12 | 26/1 (249/4) | 462 | 2–11 | 0,1 |
| smoke-01 | 2075 | 83 | 256 | 185 | 12 | 26/1 (249/4) | 505 | 3–11 | 0,1,2 |
| smoke-02 | 2086 | 78 | 256 | 184 | 12 | 26/0 (255/0) | 508 | 3–11 | 0,1,2 |
| smoke-03 | 2314 | 45 | 256 | 209 | 11 | 25/0 (252/0) | 459 | 2–11 | 0,1 |
| smoke-04 | 2255 | 0 | 256 | 204 | 11 | 26/0 (255/0) | 461 | 0–8,11 | 9,10 |
| smoke-05 | 2489 | 149 | 256 | 221 | 11 | 25/1 (249/6) | 571 | 3,4,6–11 | 0,1,2,5 |
| smoke-06 | 2327 | 45 | 256 | 208 | 11 | 25/1 (250/3) | 468 | 2–11 | 0,1 |
| smoke-07 | 2448 | 0 | 256 | 224 | 11 | 26/0 (250/0) | 504 | 0–7,11 | 8,9,10 |

  `real_candidate_columns` and `rule_pin_composition` were recomputed from `build_sc1_candidates` + `select_policy`
  with the same `filler_manifest.turns` indices and agree on all eight; a constant-1 scorer's clf pins are 25–27
  filler pieces / 0–1 real pieces as well, so the composition field reads both arms consistently. Every history turn
  <= 600 tokens; U >= 8B; a budget skip on every episode.
- Numeric probes through the harness (`localcontext(prec=5)` to expose any context arithmetic): `1e4096`,
  `-1e-4096`, 1024 ones, `0.<1022 zeros>1`, `1E+4096`, `1e04096`, `123456789012345678901234567890.5` all parse, canonical
  round-trip exactly, and `_wrong` yields the exact negation (`copy_negate`, no rounding); `1e4097`, `1e-4097`,
  `10e4096`, 1025 digits, `1e99999`, `[1e±9999999999999999999]`, `0e99999999` raise plain `ValueError("numeric ...")`,
  never `DecimalException`; `json_equal(Decimal("1e4096"), 10**4096)` True; `run_checker` on smoke-00 returns
  schema_valid False (no exception) for astra's 34-token patch, its negative-exponent twin and a 2000-digit integer.
- R3 variants on the real smoke-05 tool turn 5 through `validate_bank`: astra's pretty-printed block, an inline
  `note {"v": 1} end`, and `[{"v": 1}]` are rejected ("public state return missing from trace"); the canonical
  envelope pasted into user turn 0 is rejected; a non-JSON lookalike `{'v': 'x'}` and a non-state `{"note": ...}`
  block are accepted (see V4).
- R4 through the validated text fixture: reference altering a protected line or the line count is rejected before
  freeze; at runtime an appended line, a deleted line and a protected-line change are `permitted_edits` corruption
  while a wrong value inside editable line 0 is a plain failure; an initial state spelled `"Draft  \r\nHarbor"` is
  accepted because the baseline is the production-normalized initial artifact (consistent with the clause).
- R2: nested acquisition in-process raises "study execution is already owned"; the lock is released on exit and can
  be re-acquired; a child process holding `flock` on `<root>/.execution.lock` blocks the decorated consumer and the
  consumer succeeds after the child exits; a wrong `--out` is refused before any directory is created.
- R6 at RunStore level: `start` + torn `{"event":"completion_prepared",` fragment + `reconcile()` + `attempt_open`
  append -> reopen succeeds, a recovery proof exists, the arm is not completed and `pending` demands interruption
  evidence (the registered "open until evidence" state).
- R8/N2: smoke-00 with turn 0 grown by 400 sentences is refused ("turn 0 exceeds 600-token cap");
  `filler_turns=[3,4,5]` reports `base_tokens=207, capacity=1771, turns_needed=8`; eight designated turns expand to
  4,676 history tokens with 59 real columns.

## Finding-by-finding closure

Legend: CLOSED = code implements the fix and the named test fails on the old behaviour (judged by reading the test
against 68938ed). Line numbers are eff241b.

| Finding | Status | Code | Test (fails on old?) |
|---|---|---|---|
| astra R1 numeric output escapes checker | CLOSED | `parse_number` (episodes:415–437) bounds digits (<=1024) and exponent spelling (<=4 significant digits) before constructing the `Decimal`, checks stored and canonical exponents <= 4096, and converts `DecimalException`/`OverflowError` to `ValueError`; wired as both `parse_float` and `parse_int` (:404–410); `_wrong` uses `copy_negate` / zero->1 (:895–903); SCHEMA numeric_law states the bounds (:156–161). | `test_astra_r1_numeric_output_is_durable_failure` x2 (tests:1915–1951): astra's patch through `run_arm` with a fixed-token backend, durable scored row, `pending == []` on reopen, no invalid.json, one generate call — old code raised `InvalidOperation` out of `run_checker`, yes. `test_astra_r1_exact_numeric_mutations_and_bounds` (:1954–1968) under prec=2 — old `value + 1` rounded, yes. |
| astra R2 no exclusive owner | CLOSED | `exclusive_execution` (scripts:54–74): root must equal the registered `execution_root`, then `flock(LOCK_EX|LOCK_NB)` on `<root>/.execution.lock` (never unlinked), held through the consumer's `finally`; applied to `run_determinism`, `run_study`, `analyze` (:767, :992, :1265); `main` no longer binds determinism outside the lock (:1436–1442). | `test_astra_r2_execution_owner_refuses_second_consumer` x4 (:1971–2014): from inside the first backend constructor a second setup/final/determinism/analyze is refused before `Forbidden` is constructed, cost bytes and 510 arm files unchanged — old code had no lock, yes. |
| astra R3 multiline public JSON (F6 PARTIAL) | CLOSED | `validate_trace` (episodes:1120–1153) scans every turn with `JSONDecoder.raw_decode` from each `[`/`{`, recursing into values for state keys (`fields`, `initial_state` keys, call/return); any state-bearing block must be exactly the traced canonical envelope, in a tool turn, on its own line; nested blocks inside an accepted envelope are skipped by cursor advance. SCHEMA state_trace text updated (:218–224). | `test_astra_r3_multiline_public_state_through_bank` x3 (:2017–2026): positive with incidental prose, then astra's block / a multiline list / a nested `{"return": ...}` — old per-line parser accepted all three, yes. |
| astra R4 text permissions vs oracle (F8 PARTIAL) | CLOSED | `check_result` baseline is `normalize_text(initial)` (episodes:650); `expand_source` refuses text sources whose expected artifact has unauthorized changes or a nonempty `permitted_paths` (:1411–1419); for text `reference == expected_artifact` by construction (:1389–1390) so the reference is covered. | `test_astra_r4_permissions_use_original_artifact` (:2029–2042): astra's inconsistent source refused through `validate_bank`, runtime corruption on the adapted episode, wrong-value-in-line-0 still not corruption — old baseline was `expected`, yes. |
| astra R5 empty timeouts certify determinism (F11 PARTIAL) | CLOSED | `verify_determinism` requires `failure is None` and nonempty `token_ids` per retained arm (scripts:723–727) before the cross-process comparison. `run_arm` sets `failure` only to None / "timeout" / a GenerationFailure message (sc1.py:1271–1275, :1304); repetition/truncation are `flags`, so a deterministic malformed answer still qualifies. | `test_astra_r5_determinism_requires_completed_tokens` x4 (:2045–2070): all-timeout, one timeout, one empty, one completed failure — old verifier accepted all, yes. |
| astra R6 caught partial append (F16/M2 PARTIAL) | CLOSED | `RunStore.reconcile` (sc1.py:760–764) re-reads durable bytes through `_open`'s torn-tail law (proof file before the separating newline, :802–830); `record_exception` calls it before appending `attempt_open` (scripts:191–203). | `test_astra_r6_caught_partial_completion_is_recovered` (:2073–2105): partial `completion_prepared` fragment + OSError through the real handler, no invalid.json, prepared output recovered by hash, resume completes with 2 calls and immutable bytes — old handler appended onto the fragment ("altered complete record"), yes. |
| astra R7 raw-text scope attacks (F7 PARTIAL) | CLOSED | `validate_attack` text branch (episodes:1264–1290): raw artifacts in `old_id_work/obsolete_work/cancelled_work`, `mutation_key` on text, changed normalized lines must appear in the event's public evidence; text wrong-entity witness `{line,target_id,replacement_id,evidence_id}` (:1297–1322); `StopIteration` caught (:1340). `validate_dependencies` accepts `completion` as the cancelled-or-completed terminal (:1058–1078), closing astra's ambiguity-3 population restriction. | `test_astra_r7_text_scope_attack_through_bank` x3 (:2108–2180): validated overridden/old-ID/cancelled text sources with a named attack, the completion variant, then evidence removed -> "semantic attack" — old code raised JSONDecodeError on `parse_json(reference)`, yes. `test_astra_r7_text_wrong_entity_witness_through_bank` (:2400–2429). |
| astra R8 600-token cap only on filler (H1 PARTIAL) | CLOSED | `validate_turn_cap` on every authored base before expansion (episodes:1420) and on every final turn in `validate_episode` (:1672, :1751–1754); `layout_audit.turns` records per-turn role/tokens/designation/evidence (:1541–1555); README "V3 pressure and cue audit" carries the role/position/wording audit. | `test_astra_r8_all_turn_cap_through_bank` x2 (:2183–2187): governing turn 0 and filler base 3 grown by 400 sentences refused through `validate_bank` — old validator accepted 1,233-token turns, yes. |
| fable N1 filler-dominated pressure | CLOSED | `real_candidate_columns` and `rule_pin_composition` in `layout_audit` (:1526–1531); `pin_composition` recorded per arm at runtime (sc1.py:608–619, :1237–1239) and in `analysis.json` (:678–684); `validate` prints the per-episode pressure report (scripts:1498–1512); README table + clause disclosure. | `test_fable_n1_pressure_composition_report` (:2190–2221) — old audit lacked the field, yes. |
| fable N2 grammar capacity rule | CLOSED | SCHEMA expansion text (:238–248) states designated x 600 > 4608 − base (typically >= 8), the pool size and the batch-checked minimum; expander error reports base/capacity/turns_needed (:1444–1467). | `test_fable_n2_capacity_guidance_and_error` (:2224–2239): computed count in the message and exported grammar equality — old text said ">=3" and the error had no numbers, yes. |
| fable N3 live-ledger science hash | CLOSED (code) — see V1 for the test | `SCIENCE_SNAPSHOT` hashed instead of LEDGER-PLAN.md (scripts:47, :259, :295–296); `verify_manifest` rejects manifests without the snapshot binding or with a `LEDGER-PLAN.md` entry (:363–368); `verify_stage_freezes` demands `science_snapshot_path` + hash equal to the file and to the executable freeze (:459–468); production manifests must match the executable snapshot (:423). | `test_fable_n3_snapshot_manifest_survives_live_ledger_append` (:2242–2300): temp ledger appended after build -> `verify_manifest` and `verify_stage_freezes` pass; snapshot mutated -> both refuse — old code hashed the live ledger, yes. |
| fable N4 weak tests | CLOSED | F1 test wraps `read_text` and `read_bytes` and seeds one completion so `1 <= reads <= 2` (:1122–1160); M1 uses prefill=12 (:1225); `test_fable_n4_discriminating_regression_bounds` (:2303–2307) proves 28,960 > cap > 28,060; `test_fable_n4_strengthened_tests_detect_replay_and_old_projection` (:2432–2455) restores each defect and asserts the strengthened tests catch it. | Meta-test discriminates by construction. |
| fable N5 abandoned determinism allocation | CLOSED by proposal | STAGE1-CLAUSES "Determinism, abandoned work" paragraph; `run_determinism` still refuses replacement (scripts:794–800). | `test_fable_n5_abandoned_determinism_disposition` (:2310–2313) — binds the proposal file; see V3. |
| fable N6 registry unreviewable | CLOSED | `bind_study` writes an immutable `registration-audit.<stage>.json` (study digest, registry path/hash, entry, source-owner hashes) and appends it once to WORKLOG.md (scripts:140–157). | `test_fable_n6_registration_audit_is_reviewable` (:2316–2341) — idempotent append, hashes verified; old code wrote nothing, yes. |
| fable N7 private stream in author file | CLOSED | `commission` pops `input` into `*.input.json` and records its path/file hash in the operator envelope (scripts:1420–1429). | `test_fable_n7_commission_writes_separate_author_input` (:2344–2373) — old envelope carried `input` beside `private_assignment`, yes. |
| fable N8 within-pool identifier reuse | CLOSED (disclosed flag) | `independence_audit` reports `within_pool_literal_collisions` and sets `flag` (episodes:1835–1839). | `test_fable_n8_within_pool_collision_is_review_flag` (:2376–2384) — old row had no such key, yes. |
| fable N9 failure taxonomy disclosure | CLOSED | `FAILURE_DISCLOSURE` (sc1.py:41–50) carried in `analysis.json` (:685); README paragraph. | `test_fable_n9_failure_taxonomy_disclosure` (:2387–2392). |
| fable N10 code/data commit identity | CLOSED | WORKLOG v3 handoff records code@5458350 + data@00e4942 (v2) and code f470bd2 + data d567eac (v3); manifest `harness_commit` f470bd2 verified. | `test_fable_n10_historical_freeze_records_data_commit` (:2395–2397). |

astra's PARTIAL rows F6, F7, F8, F11, F16, H1, M2 map to R3, R7, R4, R5, R6, R8/N1/N2, R6 respectively and are CLOSED with
them; their v2 finding-named tests remain in the suite and passed. All 18 v2 findings (R1–R8, N1–N10) are closed by the
code at eff241b; no PARTIAL or OPEN items.

## New findings (residual-probe review of the fixes)

### V1 (MEDIUM, before freeze) — `test_fable_n3` binds the LIVE ledger tail, and tests/test_sc1.py is itself a frozen code file.
tests/test_sc1.py:2245–2249 asserts `snapshot == LEDGER-PLAN.md[second "## SC1" heading:] + AUTHOR-CONTRACT.md`. That
is true today because the v2 section is the ledger's last section, but the v2 section runs to EOF, so the assertion
fails on the first byte appended to LEDGER-PLAN.md after the snapshot is taken — the Stage 1 "REGISTERED" entry, dated
decisions, or the post-setup editorial notes v2 permits (LEDGER:953–955) — i.e. exactly the N3 scenario, moved from
the manifest to the registered test file. Because `tests/test_sc1.py` is in `CODE_FILES` (scripts:33–41) and hashed
into the executable manifest, the test cannot be repaired after the freeze without invalidating every gate, and the
handoff's acceptance step ("finding-named tests green") would be mechanically red for the rest of the study. The
manifest itself survives (verified by the same test on a temp copy), so this is an operational trap, not a leak.
Fix (before freeze, same re-freeze as the amendment): keep the byte-identity check but bind it to the snapshot's own
structure — assert the snapshot starts with the exact `## SC1 — LEARNED vs RULE SELECTOR ... (DRAFT v2` heading line,
ends with the exact AUTHOR-CONTRACT.md bytes, and that the ledger *contains* the snapshot's ledger part as a
substring (`section_bytes in ledger`), rather than equality with the ledger tail. Test: append a line to a temp copy of
the ledger and re-run the assertion logic; it must still pass.

### V2 (LOW, before freeze) — no snapshot producer; the amendment must land inside the snapshot.
`registration-snapshot.md` was hand-assembled (no `snapshot` subcommand; `grep SCIENCE_SNAPSHOT scripts/sc1.py` shows
only constants and checks). The clause says the snapshot is "the exact byte concatenation of the governing SC1 DRAFT v2
section and the v2 author contract" but the orchestrator is about to append SC1 AMENDMENT 1 to that section, after
which the current snapshot no longer equals the governing text and `verify_stage_freezes` will bind stale science.
Fix: define the snapshot algorithmically in the amendment (replacement text below) and regenerate it after the
amendment is appended, then re-run `smoke` so the executable manifest binds the new hash (harness_commit will move to
the commit containing the new snapshot; code bytes unchanged). A three-line `snapshot` subcommand is preferable to a
manual copy but not required if the amendment records the exact command.

### V3 (LOW) — two registered tests bind non-frozen prose files.
`test_fable_n5_abandoned_determinism_disposition` reads data/sc1/STAGE1-CLAUSES.md (proposal file) and
`test_fable_n10_historical_freeze_records_data_commit` reads WORKLOG.md. If the proposal file is superseded or renamed
once the amendment is adopted, N5's test goes red inside the frozen test file (same mechanism as V1). Fix: point N5's
assertion at the registration snapshot (which will contain the adopted clause) or drop it; N10's WORKLOG check is
append-only and safe.

### V4 (info, disclose in Stage 3 review guidance) — R3 is a JSON-syntax boundary.
The trace scan only sees blocks `JSONDecoder.raw_decode` accepts. Non-JSON lookalikes (`{'v': 'x'}`, YAML-ish
`v: impossible`) and JSON with non-state keys are accepted by construction (probed). This is consistent with the
proposed clause ("state-bearing public JSON"); the semantic review should be told that misleading non-JSON state
prose is its responsibility.

### V5 (info, clause precision) — the exclusive owner is an advisory same-host `flock`.
`fcntl.flock` on `<execution_root>/.execution.lock` is advisory and host-local (not reliable across NFS or hosts). The
registered `execution_root` is an absolute local path, so this matches the threat model; the clause should say so
(replacement text below) rather than imply a global guarantee. Verified: nested and cross-process acquisition refused,
release on consumer exit, no unlink.

### V6 (info, operational) — every consumer invocation may append to the tracked WORKLOG.md.
`bind_study` appends the registration receipt to WORKLOG.md on first binding per stage (scripts:151–157). That is the
intended N6 channel, but it is a harness write to a tracked repo file: run production consumers only when no codex
wrapper holds `.review.lock` (AGENTS.md drift rule) and commit the appended line with the run's other artifacts.

### V7 (info) — a completed generation whose total wall time exceeds 300 s is `failure="timeout"` (sc1.py:1272–1273)
and therefore does not qualify as a determinism cell even with a full token stream. Conservative and consistent with
the clause; note it in the determinism paragraph so an operator does not read such a cell as a verifier bug.

## STAGE1-CLAUSES.md — clause-by-clause judgment for "SC1 AMENDMENT 1"

Each clause was checked against the code it describes. "Correct" = matches the enforced behaviour; "conservative" =
narrows rather than widens v2; "sufficient" = the orchestrator can append it as-is.

1. **Registration identity and snapshot** — correct and conservative; NOT sufficient (V1/V2). Replace the second and
   third sentences of the first paragraph with:
   > `science_snapshot_path` is `data/sc1/registration-snapshot.md`; `science_hash` is its SHA-256. The snapshot is
   > produced mechanically at freeze time as the exact bytes of LEDGER-PLAN.md from the line beginning
   > `## SC1 — LEARNED vs RULE SELECTOR, BENCHMARK-FREE FROZEN-POLICY COMPARISON (DRAFT v2` through the end of that
   > file (which at freeze includes this amendment), immediately followed by the exact bytes of
   > data/sc1/AUTHOR-CONTRACT.md, with nothing inserted; the two part lengths and the file hash are recorded in the
   > handoff. It is regenerated, and the executable manifest re-frozen, whenever that ledger section or the contract
   > changes before Stage 2; after Stage 2 the snapshot is byte-frozen and later LEDGER-PLAN.md entries do not affect
   > any manifest or test. The Stage 1 JSON file is byte-frozen after registration; its SHA-256 (`registration_hash`)
   > is bound into the study identity by every consumer.
   The `deployment` paragraph is correct (all twelve keys verified against the manifest block). The `authors` paragraph
   is correct (`set(AUTHORS)` enforced; 32-bit seed mapping matches SCHEMA:186).
2. **Registry / audit receipt** — correct, conservative, sufficient. Add one sentence: "The receipt is appended to
   WORKLOG.md by the consumer itself; that append is committed with the run's artifacts."
3. **Exclusive execution-root lock** — correct and conservative; add for precision (V5): "The lock is an advisory
   `flock` on `<execution_root>/.execution.lock`, valid on the executing host only; the registered absolute
   `execution_root` must be a local filesystem path."
4. **Source geometry, pressure** — correct (FILLER 512, round-robin without replacement, per-turn 600 cap on bases and
   final turns, capacity rule, batch-checked 4,608 minimum, U >= 2B, one budget skip), conservative, sufficient. Optional
   precision: "`filler_turns` are zero-based indices into the authored `turns` list (public history, system prefix
   excluded)."
5. **Disclosure of the induced population** — correct (measured: filler 94–100% of U; rule pins 96–100% filler
   pieces; OLD retention decided by author turn order), conservative, sufficient. Keep the sentence that it is not a
   measured classifier advantage.
6. **Evidence, public tools, finite grammar** — correct (completion now accepted; user authority; canonical envelope
   on its own tool-turn line; incidental prose allowed), conservative, sufficient. Add for V4: "Only JSON-syntax blocks
   are mechanically checked; state-like non-JSON prose is a Stage 3 semantic-review item."
7. **Fingerprints / pair signatures / within-pool flag** — correct, conservative, sufficient.
8. **Numeric law** — correct (1024 digits, |exponent| <= 4096 stored and canonical, representation failures are
   schema-invalid outputs scored once, exact negation), conservative, sufficient. Optional precision: "an exponent
   spelled with more than four significant digits is rejected before construction."
9. **Text edit law and witnesses** — correct (baseline = production-normalized `initial_state`; expected artifact
   validated at freeze; replacement-only at `editable_lines`; raw-text witness fields), conservative, sufficient.
10. **Author transport / attempt history / separated input** — correct (matches `verify_author_chain` and the
    `*.input.json` split), conservative, sufficient.
11. **Determinism** — correct (2 processes x 2 lexically-first smoke x 2 arms, `failure is None`, nonempty token IDs,
    closed charged intervals, no replacement), conservative, sufficient. Add (V7): "A cell whose total wall time exceeds
    the 300 s deadline is recorded as `timeout` even if a full token stream was produced and does not qualify."
12. **Abandoned work / separate reporting** — correct and conservative; sufficient provided the orchestrator states
    the disposition it accepts (separate reporting vs carry-over) in the same amendment, as the clause itself demands.
13. **Failure records, R periods, counters, cost projection** — correct (FAILURE_DISCLOSURE text, persistence and
    initialization reserve terms), conservative, sufficient.

Freeze order implied by the above: append AMENDMENT 1 (with the replacement text in 1, 3, 6, 11 and the V1 test
change) -> regenerate the snapshot -> re-run `smoke` and `validate` -> commit code + data -> Stage 2 manifest. The V1
test edit and the snapshot regeneration both change manifest-hashed files, so they must precede the Stage 2 manifest.

## Verified unchanged core

Candidate segmentation, rank keys, whole-span admission, echo serialization/caps, two-stage eviction assertions,
McNemar/CP/power, gate i–iv, RunStore immutability/pair publication, allocation metering, the v2 blinded envelope,
study binding and resumable infrastructure errors: unchanged from the v1/v2 verified lists and re-covered by the
127-test run; `analyze` still re-verifies seal, pair hashes, arm fields, episode hashes, orders and intervention
counters before inference and now runs under the exclusive lock.

## VERDICT: SOUND-WITH-FIXES

All eighteen v2 findings (astra R1–R8 with every PARTIAL row; fable N1–N10) are closed by the code at eff241b with
finding-named consumer tests that fail on the old behaviour; the residual probes (exclusive owner across processes,
exact bounded numerics with no escaping exception, snapshot-bound manifest, nonvacuous determinism cells, recovered
partial appends, text law anchored to the original artifact, all-turn cap, pressure composition) hold with the real
tokenizer on the regenerated smoke bank. Before the Stage 2 artifact freeze: V1 (decouple `test_fable_n3` from the
live ledger tail — the test file is manifest-hashed and would be permanently red after the first post-freeze ledger
entry), V2 (regenerate the snapshot after AMENDMENT 1 is appended, with the algorithmic definition above), and the
clause precisions in 1, 3, 6 and 11; V3 can ride along. Nothing found can produce a wrong clf adoption or leak private
fields or evicted history.
