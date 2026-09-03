# BFCL harness v10 review (fable) — LEG A v7 + Amendments 1–5

Reviewed: commits 14caed8 (code, closes FV8-1..7 on top of v10 b755a35), a298bc9 (schema legacy default), 1a475df
(WORKLOG) = the brief's HEAD. The live HEAD at review time was 3c4fca8; `git diff 1a475df 3c4fca8 --stat` touches
only `WORKLOG.md`, so every harness byte below is the 1a475df byte. Governing text: LEDGER-PLAN.md:623-782 (v7 + LEG A
A1–A5). Registration SHA-256 recomputed through the harness's own extractor =
`dd2b6eaa1a8c251c012bde10c5c26de7a78c9c4b786cebaaa57f380ccbc4dcbc` (25,220 chars; contains LEG A AMENDMENT 5,
excludes LEG B AMENDMENT 3) — equals WORKLOG's v11 entry and sol's v9 value. Harness manifest SHA-256 =
`6d9aaf4d7eadc1e78a6727d7f9a124e1f5da1f6eb9d6632a8e9d81ac7f609ea1` (26 entries, now including `scripts/__init__.py`)
— equals WORKLOG's v11 entry.

WORKING-TREE / HARD-RULE NOTE. All code reading, tests, the census and the certificate probe ran in a
`git archive 1a475df` mirror in the scratchpad, made a throwaway git repo (clean tree) with the repo's trunk weights,
`data/classifier/model/ft/encoder/model.safetensors` and `results/quick-checks` linked in (gitignored paths only, so
`git_provenance()` reports clean). CPU only (`CUDA_VISIBLE_DEVICES=''` set inside every script); no model, trunk or GPU
process launched; the registered classifier was NOT run (hard rule) — only stub scorers; nothing signalled, everything
foreground, no tool-time-out kills this time (the local echo clamp made the census ~10× cheaper). No sealed BFCL row and
no IFEval input opened: every case load used the registered seek-only dev loader; the sealed "contract" in the
certificate probe was built by `artifact_meta(split="sealed")` exactly as `main()` does before any sealed read (its
`verified_bytes.records`/`source_files` are empty by construction); `test_v4_1_index_preserves_all_frozen_bfcl_files…`
(hashes the mixed files) and the two real-dev census tests were deselected. Only this file was written in the repo.

## Bottom line

v10 closes every prior finding I could re-verify, including all seven of my v8 findings: the certificate is
split-invariant and round-trips from a REAL dev `artifact_meta` through the REAL producer (`issue_preflight_certificate`
with an on-disk `meta.json` + 32 records) to a REAL sealed contract (FV8-1); `match_impossible` is decided by total
columns (FV8-2 — the v8 case-24-t5 resource-count impossibility is gone: 16 tool resources now serve 18 user targets,
shortfall recorded, total exact 308 = 308); sealed-path violations are recorded as uninformative instead of raising
(FV8-3, sealed half); the echo clamp measures locally and is token-identical to the full-context measure on every one of
the 345 evicting arm-turns and 312 non-evicting arm-turns I probed, at 2.5–8 s per plan instead of 25–68 s (FV8-4);
`final_pass` ignores NA turns (FV8-5); the manifest binds `scripts/__init__.py` and asserts `stencil.bench` out
(FV8-6); retained tool-swap user rows carry `_echo_source_columns` (FV8-7). sol's V9-1/V9-2 are closed as coded and
tested (v10 suite green; the producer refuses a mutated dev-record or harness digest with `ARTIFACT_DRIFT`; base/full
safety or method breach → `INCONCLUSIVE`, never `SUPPORTED*`). Dev census: 0 `match_impossible` on every evicting turn
under the five realistic stubs, per-role equality 33/33, |echo_token_delta| ≤ 8, no `_turn_plan` exception, 6/11
initial-prompt overflows excluded from full's baseline.

Two things still block launching the registered preflight, both small and CPU-testable:

* FV10-1 (HIGH): the v11 change that stops `_turn_plan` from raising also stops the DEV preflight from failing. A
  pressure-turn column mismatch or |delta| > 16 on `recency_pinned` / `tool_swap_echo` is now recorded as
  `match_impossible=True`, which makes `assert_dev_invariants`'s `comparator_columns`/`comparator_echo` families PASS
  (they accept `or match_impossible`) and the preflight's `excessive_echo` stop can never fire (it requires
  `not match_impossible`). Verified by probe: such a record validates 100 % and certifies. Registered: "On dev, a larger
  delta stops preflight"; "Any assertion failure stops the leg before the sealed run".
* FV10-2 (HIGH, operational): the post-run drift check compares the whole unbound meta including `git`
  (commit/dirty/status). Any commit or untracked file in the repo during the ~7-GPU-h preflight (this review file
  included) produces `ARTIFACT_DRIFT`, no certificate, and — because `meta.json` then no longer matches — no resume:
  the preflight must be repeated from scratch. Verified by probe (git-only drift → refused).

VERDICT: SOUND-WITH-FIXES — apply FV10-1 and FV10-2 (≈25 lines + 3 tests), register the echo-unreachable rule as text
(FV10-3), re-run the CPU suites, re-record the manifest hash, commit everything, then launch.

## Dev census (CPU, no model, stub scorers), v10 code at 1a475df

All 32 dev cases, 115 teacher-forced histories rebuilt with the harness's own `build_teacher_history`; eviction by
`context_layout` (`history_end > K`); plans through the harness's own `_turn_plan` for the treatment and the three
comparators. Evicting turns = 11 (case24 t4/t5, case27 t1–t6, case28 t5, case31 t3/t4), scorer-independent; 6/11 have a
full prompt > 40,960 (case27 t2–t6, case31 t4; max 43,804) — the A4.1(a) population. The "realistic" stub mimics the
registered classifier's measured behaviour on the 17 real dev records of the v5 shakedown
(`results/qwen/bfcl-evict-v2-preflight`, 58 turns t ≥ 1: user candidates eligible 97/295 = 33 %, median 0.33 per turn,
all-eligible on 1/58 turns; tool candidates eligible 156/177 = 88 %).

| scorer (stub) | user>0 / tool>0 turns | impossible (ctrl/rec/swap) | shortfall | per-role equality on usable turns | echo delta | clamp residual max | entry-count delta | extension used | local == full measure | plan s/arm max |
|---|---|---|---|---|---|---|---|---|---|---|
| `firstuser` (coder/sol census stub) | 11 / 0 | 0/0/0 | 0 | 33/33 | −4 … 0 | 4 | 0 | 0 | 33/33 | 2.9 |
| `realistic` user 0.3 / tool 0.9 | 3 / 11 | 0/0/0 | 0 | 33/33 | −2 … 0 | 2 | — | 0 | 33/33 | 5.6 |
| hash rate 0.3 | 6 / 11 | 0/0/0 | 0 | 33/33 | −7 … 0 | 7 | −1 … 5 | 1 | 33/33 | 6.6 |
| user 0.5 / tool 0.1 | 10 / 9 | 0/0/0 | 1 (total exact) | 33/33 | −8 … 0 | 8 | −2 … 3 | 0 | 33/33 | 5.8 |
| `all` user 1.0 / tool 1.0 (budget-capped) | 6 / 11 | 0/0/0 | 2 (total exact) | 33/33 | −2 … 0 | 2 | −13 … 2 | 2 | 33/33 | 8.0 |
| `userall` user 1.0 / tool 0.05 | 10 / 9 | **1**/0/0 (case24 t5, `invariant_violation=echo_delta`, see FV10-3) | 9 | 32/32 usable | −5 … 0 on usable | 5 | −8 … 2 | 2 | 33/33 | 6.8 |

Other facts: every comparator echo entry was a subset of that comparator's pins; every truncated/extended entry's text
was the decoded prefix/extension of its source columns (0 provenance failures in 6 × 33 arm-turns); non-whole entries
never exceeded one per role (`clf_control`, `recency_pinned`) or one per tool target group (`tool_swap_echo`), i.e. the
per-role/per-target clamp of A5; `tool_swap_echo` cross-role matches 0 everywhere; `clf_control` cross-role matches only
on shortfall turns; no `_turn_plan` AssertionError/ValueError on any turn under any scorer; treatment echo tokens
(`_echo_cap`, full-context measure) equal the recorded value on every turn. v8's FV8-2 turn (case24 t5 under `userall`:
18 user targets / 308 columns, 0 spare user sentences, 16 tool chunks) is now POSSIBLE by matching — 16 cross-role
matches, exact total 308 = 308, shortfall recorded — and only fails at the echo (FV10-3).

Non-evicting turns (t ≥ 1, 104 turns, echo-only stratum, rate 0.3): no exception; `clf_control` impossible on 2/104
(v8: 9/104 — the FV8-2 fix) and `tool_swap_echo` on 20/104 short-context turns (tiny pools) — recorded, no contrast uses
them, `invariant_violation` correctly None on every non-pressure turn; every non-impossible comparator within
|delta| ≤ 4; local == full measure on all 312 arm-turns.

Plan-building cost (FV8-4): 2.2–2.9 s per `_turn_plan` call on the six ~42k-token turns under `firstuser`, ≤ 8.0 s
under the heaviest stub (v8: 25–35 s mean, 68 s max). The whole 11-turn × 4-arm census takes 81–195 s (v8: > 600 s per
stub, split across runs).

## Certificate, manifest, normalization, claim table

* Certificate round trip (FV8-1, sol V8-1/V9-1), real path: `_load_cases_verified("dev")` → 32 rows / 64 record
  hashes; `artifact_meta(dev)` → `verified_bytes.records == bfcl_manifest.dev_records` (True), `bfcl_files` contains no
  `.jsonl`; `bind_run_identity`; `meta.json` + 32 stub records written; `issue_preflight_certificate` (which re-runs the
  real `artifact_meta(args)` as the drift check) issued a schema-3 payload whose `frozen_hashes` has no `verified_bytes`;
  `validate_preflight_certificate(preflight.json, artifact_meta(sealed))` returned the digest (TRUE). Negative controls,
  all refused: changed `harness`, `offsets`, `trunk_weights`, `vendored_checker`, `registration_sha256`, a classifier
  file hash, `arms` (arm-cut mismatch), `trunk` 4b; a one-byte record edit after issuance ("record digest mismatch"); a
  harness-file digest drift between run and issuance (`ARTIFACT_DRIFT`, `preflight.json` status INCONCLUSIVE, no
  certificate). The certificate binds the bytes actually loaded: `dev_verified_bytes.records` are the per-row SHA-256s
  produced by the bounded `_read_indexed_row` reads, and the validator requires them to equal the pinned index's
  `dev_records` and the evidence to be `split=dev` with empty `source_files`, so a `--limit` or sealed-built certificate
  cannot pass (and `parse_args` already refuses `--limit`/`--arm-cut` on preflight).
* Manifest: 26 entries; identical before and after importing every module the run path loads (`torch`, `stencil.qwen3`,
  `stencil.selector_v2`, `stencil.stats`, the checker/utils, all nine environment modules); no repo-local `.py` loaded
  outside the manifest; `stencil.bench` not loaded and now asserted out. The post-run drift check re-hashes the same
  manifest, so a run-time import cannot silently change it (FV8-6 closed; see FV10-2 for the `git` field).
* Normalization: `canonical_call = normalize_call` still feeds `call_to_python`, the repeated-call set and the decision
  point; none of these functions changed between a145340 and 1a475df (diff hunk list), and the v7 qualified-name test is
  green.
* Primary claim table (`primary_claim_status`, bfcl.py:1578-1611): k<6 → INCONCLUSIVE; A1 uninformative → INCONCLUSIVE;
  treatment breach → UNSUPPORTED; base/full safety or base-method breach → INCONCLUSIVE (sol V9-2, tested for base,
  full and `match_impossible`); safe A3-uninformative (no headroom / post-exclusion k<6) with A1 passing →
  SUPPORTED_A1_ONLY with the registered wording; with A1 failing → UNSUPPORTED; eligible both pass → SUPPORTED; else
  UNSUPPORTED. A2 separate; A4 local. A comparator safety breach on `clf_control`/`recency_pinned` marks that contrast
  uninformative (→ A1 uninformative → INCONCLUSIVE). This matches the registered outcome rules; complete.

## Findings by severity

### FV10-1 — HIGH — dev-path invariant violations are laundered into `match_impossible`; the registered preflight stop no longer fires
Code: `_turn_plan` (bfcl_mt.py:1173-1192) sets `match_impossible=True, invariant_violation="echo_delta"|"columns"` on
a pressure turn instead of raising (my FV8-3 asked for exactly this on the SEALED path, with the dev path still failing
the family). But `assert_dev_invariants` (bfcl_mt.py:2075-2107) accepts `… or eviction["match_impossible"]` in both
`comparator_columns` and `comparator_echo`, and the preflight `excessive_echo` stop (bfcl_mt.py:2266-2276) requires
`not match_impossible` — which is now always False when a delta violation occurred. `invariant_violation` is written
only to `selector.turns[i]` (never to the `eviction` dict) and nothing reads it. CPU probe (scratchpad `v10_launder.py`,
`_v8_record` fixture): a pressure-turn `recency_pinned` column mismatch or a `tool_swap_echo` delta of 29 recorded the
v10 way → `assert_dev_invariants` PASSES (families 100 %), no preflight stop predicate fires, the schema accepts →
the certificate would be issued with a violated registered invariant. For `clf_control` the preflight still stops, but
via `match_impossible["clf_control"]` with the misleading message "dev clf_control matching is impossible". Registered:
A4.2/A5 "asserted fail-closed on the dev path (preflight invariants)"; v7 "On dev, a larger delta stops preflight";
(6) "Any assertion failure stops the leg before the sealed run". Not triggered on dev under any stub (0 violations on
pressure turns except FV10-3's), so this is a robustness defect that a cheap fix removes before the run.
Fix: (i) `run_case_arm` `first_eviction` (bfcl_mt.py:1471-1500): add
`"invariant_violation": plan["selector"].get("invariant_violation")`; (ii) `assert_dev_invariants`, inside
`if pressure_triggered and arm in comparator_arms` (before the existing checks):
`violation = eviction.get("invariant_violation") or selector.get("invariant_violation");
check("comparator_columns", violation != "columns"); check("comparator_echo", violation != "echo_delta")`;
(iii) `preflight()`: replace the `excessive_echo` predicate with
`turn["eviction"].get("invariant_violation") == "echo_delta" and bool(turn["eviction"].get("pressure_triggered"))`
(drop the `not match_impossible` clause) and make the `clf_control` stop message say whether it was a pool
impossibility or an `invariant_violation`; (iv) `assert_case_record_schema` stays as is (sealed: uninformative +
recorded). Tests: `_v8_record` with `recency_pinned` pressure turn `match_impossible=True` +
`invariant_violation="columns"` → `assert_dev_invariants` raises `comparator_columns`; same with `"echo_delta"` and
`echo_token_delta=29` → raises `comparator_echo`; a genuine `match_impossible=True` with `invariant_violation=None`
still passes; the schema accepts all three.

### FV10-2 — HIGH (operational, fail-closed) — the post-run drift check binds `git` provenance, so any repo change during the preflight voids it and forbids resume
Code: `issue_preflight_certificate` (bfcl_mt.py:347-349) requires `artifact_meta(args) == _unbound_meta(frozen_meta)`;
`artifact_meta` embeds `git_provenance()` = `{commit, dirty, status}` (bfcl_mt.py:1727-1729, 1815). Probe: a
`git.commit` change alone → `ARTIFACT_DRIFT: post-run artifact metadata differs …`, `preflight.json` INCONCLUSIVE, no
certificate. The same field is in `run_identity_sha256`, so re-invoking the preflight afterwards fails
`_check_or_write_meta` ("registered constants or provenance differ from meta") and the 32-case run (≈ 7 GPU-h at the
v5 shakedown's 340–1,900 s/case) cannot be resumed. Today's commit log shows dozens of orchestrator commits per day, and
an untracked review file (e.g. this one) flips `dirty`. Registered text (5) binds hashes; a WORKLOG commit is not a
"later change" of a frozen quantity, and the byte-binding is already carried by `harness_files`.
Fix (bfcl_mt.py `issue_preflight_certificate`): compare with `git` excluded —
`def _drift_view(m): view = _unbound_meta(m); view.pop("git", None); return view` and
`if _drift_view(fresh_meta) != _drift_view(frozen_meta): drift(...)`; add `"git_at_freeze": frozen_meta.get("git"),
"git_at_issue": fresh_meta.get("git")` to `preflight_evidence` (the validator ignores extra evidence fields; verified
by reading bfcl_mt.py:405-411). Keep `git` in meta and in the run identity. Test: the v10 producer test with
`fresh["git"]["commit"]` changed must issue; with a `harness_files` digest changed must still refuse. Until then, the
launch checklist must say: commit everything (including review files) before `preflight`, and make no commit or
untracked file in the repo until `preflight.json` is written. If resume across an unrelated commit is wanted, relax
`_check_or_write_meta` the same way and adopt the on-disk `run_identity_sha256` — larger change, optional.

### FV10-3 — MEDIUM (text) — the echo-unreachable regime exists on dev and is unregistered as a method failure
Census: case24 t5 under `userall` — treatment pins 18 short user sentences (308 columns, 390 echo tokens); the only
disjoint resources are 16 tool chunks; nearest matching gives 7 entries (widths 10–70) summing exactly to 308 columns;
after truncation and the +14-token extension of the last entry, the echo is 361 tokens (delta −29): the missing 11
`- tool: "…"` framings cannot be recovered by extending one entry. v10 records this as `match_impossible=True,
invariant_violation="echo_delta"` (A1 uninformative on sealed; preflight stop on dev). The registered text says the
opposite in two places (A3.2: "any larger delta is a harness assertion failure, not a method failure"; A4.2:
"asserted … fail-closed") and A3.1 defines `match_impossible` by columns only. The code's behaviour is the right one
(my FV8-2 asked for it) but it needs registering before the preflight: LEG A AMENDMENT 6 — "a comparator whose echo,
after the registered truncation and last-entry extension, cannot reach |echo_token_delta| ≤ 16 is recorded
match_impossible with reason echo_delta; on dev this stops the preflight (registered stop); on sealed the affected
contrast is uninformative". Likelihood with the real classifier: needs (nearly) all prior user sentences selected on a
turn whose leftovers are few and wide — the real classifier was user-exhaustive on 1/58 shakedown turns and selects
tools at 88 %, so I expect 0/11 on dev; under `realistic`, `firstuser`, `r0.3`, `user50` and `all` it never fires. If
it does fire, the only registered remedy is a further text amendment letting the extension walk earlier entries
(never beyond their source spans) — do not tune anything else.

### FV10-4 — LOW — `final_score.valid` still counts NA turns
`run_case_arm` (bfcl_mt.py:1586-1588) computes `final_score = {"valid": all(pass for turns if pass is not None)}` while
`final_pass` (1614-1616) skips `na` turns; a `full` case with an initial-prompt overflow has `final_pass=True` and
`final_score.valid=False`. No consumer reads `final_score` (schema-required only), so reporting is unaffected. Fix:
use the same `if not bool(turn.get("na"))` filter, and note that an all-NA case gives `all([]) == True` — harmless
because `full_case_final_reporting_eligible` excludes it from every case-level population.

### FV10-5 — LOW — residual notes (no action required before launch)
* `_echo_cap` (treatment) still re-encodes the full context per entry (2 encodes × ≤ 20 entries); measured ≤ 3 s per
  call on the 42k-token turns — acceptable, and its full-context measure equals the local one on every turn.
* Non-whole comparator entries occur once per role / per tool target group (A5 per-role clamp), not once per
  comparator; the v8 wording "only the last entry is truncated" should be read per group.
* `results/*.md` is not gitignored: this file must be committed before any sealed run (`assert_clean_git_for_sealed`)
  and, per FV10-2, before the preflight starts.

## Disposition of prior findings (v10 code, 1a475df)

| finding | status | evidence |
|---|---|---|
| fable FV8-1 / sol V8-1 / sol V9-1 certificate split-invariance and producer binding | CLOSED | real dev→sealed round trip TRUE; 8 contract mutations + record tamper + producer drift all refused; `main()` validates before `_load_cases_verified("sealed")`; v9/v10 tests green |
| fable FV8-2 total-column impossibility | CLOSED | `_resource_match` pass 1 no longer returns on a fallback target miss (bfcl.py:552-558), pass 2 breaks instead of failing (575-580), final total check (581-583); case24 t5 `userall` now possible/shortfall/308 = 308; `tool_swap_plan` keeps per-target failure; v11 test |
| fable FV8-3 sealed record-not-raise; delta checks gated on pressure | CLOSED on sealed; dev half REOPENED as FV10-1 | `_turn_plan` records; schema (bfcl.py:1254-1259, legacy default fail-closed) and preflight gate on `pressure_triggered`; v11 test |
| fable FV8-4 echo clamp cost | CLOSED | local measure from the current `<|im_start|>user` marker with cached ids; identical to the full-context measure on 657 arm-turns; 2.5–8 s vs 25–68 s |
| fable FV8-5 NA-aware `final_pass` | CLOSED (FV10-4 cosmetic residual) | bfcl_mt.py:1614-1616; competence uses `full_case_final_reporting_eligible` |
| fable FV8-6 manifest residuals | CLOSED | `scripts/__init__.py` bound; `stencil.bench` asserted; stability verified |
| fable FV8-7 `_decode_row` for retained user rows | CLOSED | bfcl.py:786-790; v11 test |
| sol V8-2 per-role vs shortfall (A5) | CLOSED | census: exact per-role on every usable non-shortfall turn, exact total on the 12 shortfall turn-arms, deltas recorded |
| sol V8-3 NA out of competence denominators | CLOSED | `preflight_competence` eligible populations (bfcl_mt.py:2149-2223) |
| sol V9-2 A3 reference breach → not SUPPORTED | CLOSED | `a3_safety_intact`/`a3_integrity_failures` (bfcl.py:1783-1814) → INCONCLUSIVE with the breached arm named; v10 tests |
| v6 FV6-1..6 / sol V6-1..6; v4 F1–F10 / BFCL-V4-1..7 | CLOSED, no regression | 119 CPU tests green (test_bfcl + v2–v11); census facts above reproduce the v8 closures (nearest matching, bidirectional clamp, overflow phases NA/truncated, tool order, scorer truncation count, seek-only loader, invariant families with `{passed, n}`) |

## CPU verification log
In the mirror: `pytest -p no:cacheprovider tests/test_bfcl.py tests/test_bfcl_evict_v{2..5}.py -k "not real_dev and not
test_v4_1_index_preserves_all_frozen_bfcl_files"` → 63 passed, 1 deselected; `tests/test_bfcl_evict_v{6..8}.py -k "not
real_dev"` → 32 passed, 2 deselected; `tests/test_bfcl_evict_v{9,10,11}.py` → 24 passed. Total 119 passed, 3
deselected (two real-dev censuses replaced by my own; the mixed-file hash test). Scratchpad scripts (not committed):
`v10_census.py` (evicting/non-evicting, 6 stubs, local-vs-full echo identity, provenance, plan timing), `v10_cert.py`
(real producer/validator round trip + 11 negative controls), `v10_manifest.py` (registration hash, manifest closure and
stability), `v10_launder.py` (FV10-1). No model, GPU, or sealed content touched.

## VERDICT: SOUND-WITH-FIXES

May the registered dev preflight be launched under 1a475df? **Not yet — but nothing about the science needs
re-thinking.** Required, in order, before `preflight --split dev --trunk 1.7b`:
1. FV10-1 — dev path fails the `comparator_columns`/`comparator_echo` families on any recorded `invariant_violation`;
   record the field in `eviction`; fix the `excessive_echo` predicate and the stop message; three tests.
2. FV10-2 — exclude `git` from the post-run drift comparison (record both provenances in the evidence); one test. Until
   merged, treat "no commit / no untracked file during the preflight" as a hard launch rule.
3. FV10-3 — register LEG A AMENDMENT 6 (echo-unreachable → `match_impossible`, reason `echo_delta`; dev stop, sealed
   uninformative) so the code and the text agree before any outcome exists.
4. Re-run the v2–v11 suites, record the new manifest hash beside `dd2b6eaa…` in WORKLOG, commit (including this file),
   and launch from a fresh output directory. FV10-4/5 can ride along or wait.
