# BFCL harness v12 review (fable) — final gate, LEG A v7 + Amendments 1–6

Reviewed: 6c86017 (code + tests/test_bfcl_evict_v12.py) and 919a8ab (WORKLOG) = HEAD 919a8ab. Scope per brief: re-run
my FV10-1 and FV10-2 probes only, confirm the FV10-4 residual, recompute the recorded hashes. Everything ran in a
`git archive HEAD` mirror in the scratchpad (throwaway git repo, clean tree; trunk 1.7b weights, the ft encoder
safetensors and `results/quick-checks` linked in at gitignored paths), `CUDA_VISIBLE_DEVICES=''`, CPU only, no model or
GPU process, stub scorers only, foreground only, nothing signalled. No sealed BFCL row and no IFEval input opened
(the sealed-input guard denied even a `stat` of the IFEval file in my first command; I did not retry). Only this file
was written in the repo.

**May the REGISTERED dev preflight launch under v12? YES — 919a8ab may launch the recorded 1.7b dev preflight command
from a fresh output directory.**

## Hashes (recomputed through the harness's own functions in the mirror)

| quantity | WORKLOG v12 entry | recomputed | match |
|---|---|---|---|
| registration SHA-256, LEG A v7 + A1–A6 (`registration_text_and_hash`) | `bab228f9e65e92bb1047e0681c9a2b551ec5b56124fc3064dee44b1fc21c76f5`, 26,048 chars | same, 26,048 chars; contains `### LEG A AMENDMENT 1..6`, excludes `### LEG B AMENDMENT 3` | YES |
| harness manifest SHA-256 (`harness_manifest`) | `6e12641f700adb18ba70189e8f12e47bdb985653556797a802272539d8bf64ae`, 26 files | same, 26 entries (scripts/__init__.py, scripts/bfcl_mt.py, 8 stencil modules, 15 vendored checker files, `chat_template:render_prompt`), stable across two calls | YES |

Both values also appear verbatim in the real `artifact_meta(dev)` built by the certificate probe below
(`registration_sha256`, `frozen_hashes.harness`).

## FV10-1 re-probe (dev-path invariant violations) — CLOSED

Code at v12: `_turn_plan` (bfcl_mt.py:1180-1198) no longer sets `match_impossible` on a pressure-turn delta or column
failure; it records `invariant_violation ∈ {"echo_delta","columns"}` and `echo_unreachable`; `run_case_arm`
(1466-1481) copies both into the durable `eviction` record; `assert_dev_invariants` (2101-2156) fails
`comparator_columns` on `"columns"` and `comparator_echo` on `"echo_delta"` for all three comparators before any
`match_impossible` exemption; the preflight `excessive_echo` predicate (2310-2316) keys on `invariant_violation ==
"echo_delta"` without the `not match_impossible` clause; the schema (bfcl.py:1254-1262) refuses an unknown label and
refuses a record carrying BOTH `invariant_violation` and `match_impossible=True` (the v10 laundered shape);
`summarize_records` (bfcl.py:1757-1808) makes A1/A2/A4 uninformative on any recorded violation.

Probe (`v12_launder.py`, `_v8_record` fixture, pressure turn), all 6 arm×kind combinations
(`recency_pinned`/`tool_swap_echo`/`clf_control` × `columns`/`echo_delta` with delta 29), recorded the v12 way
(`match_impossible=False`): `assert_dev_invariants` RAISES the right family every time; the same with the field only
on the selector row (eviction lacking it) also raises; the sealed schema accepts (retains) each record. The v10
laundered shape (`match_impossible=True` + violation) now raises in `assert_dev_invariants` AND is refused by the schema
("invariant violation is not match_impossible"). Genuine `match_impossible=True` with `invariant_violation=None` still
passes both, with the `clf_control` stop firing only in that (now correctly described) case. An end-to-end
`preflight()` with a v12-shaped `clf_control` echo violation raises "registered preflight invariant failed", writes
`preflight.json` = `{INCONCLUSIVE, INVARIANT_FAILURE, "dev invariant failed: comparator_echo"}` and never reaches
`issue_preflight_certificate`.

Real-regime check on the one dev instance (FV10-3, case24 `multi_turn_long_context_188` t5 under the `userall` stub)
through the harness's own `_turn_plan` at v12: `clf_control` → `match_impossible=False`,
`invariant_violation="echo_delta"`, `echo_token_delta=-29`, residual 29, 16 cross-role matches, total 308 = 308 —
i.e. exactly the Amendment 6 record shape (`echo_delta`, `echo_unreachable`), and on dev it would stop the preflight.
`recency_pinned`/`tool_swap_echo` on that turn: delta 0, no violation. The residual note stands: the registered
classifier is expected not to hit this regime (0/11 evicting turns under the realistic stubs in v10); if it does, the
only remedy is a further text amendment.

## FV10-2 re-probe (post-run drift check) — CLOSED

Code at v12: `issue_preflight_certificate` compares `drift_view(fresh) != drift_view(frozen)` where `drift_view` =
`_unbound_meta` minus `git` (bfcl_mt.py:346-353); `git_at_freeze`/`git_at_issue` are added to `preflight_evidence`
(385-386). `git` stays in `artifact_meta` and hence in `run_identity_sha256`.

Probe (`v12_cert.py` = the v10 round trip + extensions), real path: `_load_cases_verified("dev")` → 32 rows / 64 record
hashes; `artifact_meta(dev)` (`verified_bytes.records == bfcl_manifest.dev_records`, no `.jsonl` in `bfcl_files`);
`bind_run_identity`; `meta.json` + 32 stub records; certificate issued (schema 3, no `verified_bytes`) and
`validate_preflight_certificate` against a real sealed contract → TRUE. Negative controls all refused: harness, offsets,
trunk weights, vendored checker, registration, classifier hash, arm cut, trunk 4b; record tamper ("record digest
mismatch"); harness-file drift between run and issuance (`ARTIFACT_DRIFT`, `preflight.json` INCONCLUSIVE). New:
git-only drift (commit changed) → ISSUED, evidence `git_at_freeze == meta.git`, `git_at_issue.commit` = the drifted
commit, and the git-drifted certificate VALIDATES against the sealed contract (the validator ignores the extra evidence
fields); dirty-only drift (untracked `results/harness-v12-review-fable.md` during the preflight) → ISSUED; constant
`k`, `cohorts` hash, `registration_sha256`, a classifier hash and a `verified_bytes` record hash drift → each REFUSED
with `ARTIFACT_DRIFT`. So a commit or an untracked file during the ~7-GPU-h preflight no longer aborts it.

Residual (operational, by design, not blocking): `_check_or_write_meta` still compares the whole meta including `git`,
so a preflight that dies mid-run cannot be RESUMED after a commit ("registered constants or provenance differ from
meta"); it must be restarted from a fresh directory. Certificate issuance is unaffected. Launch rule: if resumability
matters, avoid committing until `preflight.json` is written; otherwise commit freely.

## FV10-4 residual — CLOSED

`_teacher_final_score` (bfcl_mt.py:1284-1293) filters `na` turns and `None` passes; used at 1611. The v12 test
(`test_fv10_4_teacher_final_score_excludes_na_turns`) passes; all-NA → `all([]) == True`, harmless because
`full_case_final_reporting_eligible` excludes such cases from every case-level population. No consumer reads
`final_score` beyond the schema.

## Tests (mirror, CPU)

`tests/test_bfcl_evict_v{9,10,11,12}.py` + `tests/test_sealed_guard.py` → 33 passed, 1 failed; `tests/test_bfcl.py` +
`v2..v8` (`-k "not real_dev and not test_v4_1_index_preserves_all_frozen_bfcl_files"`) → 95 passed, 3 deselected.
Total 128 passed + 3 deselected + the 1 failure = the coder's 132. The single failure is
`test_sealed_ifeval_mode_is_read_only_after_hash_validation`: it asserts the IFEval file's on-disk mode is read-only,
and `git archive` does not preserve 0444 in my mirror — a mirror artifact, not a harness defect (I could not verify the
repo mode because the sealed-input guard blocks any access to that file; the coder reports it green in the repo).

## Minor notes (no action)

* The `excessive_echo` stop in `preflight()` is now unreachable (`assert_dev_invariants` raises on the same predicate
  first); harmless redundancy.
* Sealed runs still require a clean tree (`assert_clean_git_for_sealed`): this file and sol's must be committed before
  any sealed invocation; that is unchanged and correct.

## VERDICT: SOUND

The registered dev preflight may launch under 919a8ab exactly as recorded in WORKLOG's v12 entry (1.7b dev teacher
preflight into `bfcl-evict-v12-preflight-1.7b`) from a fresh output directory, with the recorded hashes `bab228f9…`
(registration) and `6e12641f…` (manifest).
