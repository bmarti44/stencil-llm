# BFCL harness v6 review (fable) — registration v7 + Amendments 1–3

Reviewed: commits 9fe7c3f (code) and c547811 (WORKLOG); HEAD 7b8de79 carries identical code (`git diff 9fe7c3f 7b8de79 --
src scripts tests` is empty). Governing text: LEDGER-PLAN.md:623-758 (v7 + LEG A A1/A2/A3), registration SHA-256
recomputed = `7f4078ece9263daed0d0fd28799318de098bd78e5d08c7da7249ca53d281674a` (matches WORKLOG; the extractor skips the
intervening LEG B Amendment 3 and ends at end-of-file).

WORKING-TREE NOTE. While this review ran, a v7 coder wrapper (brief 1fc346c, 13:06) began modifying `scripts/bfcl_mt.py`,
`src/stencil/bfcl.py`, `scripts/bfcl_seal_index.py`, `data/bench/bfcl_v3_mt/offsets.json` and `data/bench/pins-manifest.json`
(mtimes 13:14-13:17). Every line reference and every census number below is therefore against a `git archive 7b8de79`
mirror in the scratchpad (sha256 of the mirrored `scripts/bfcl_mt.py` = 71dae25f…, `src/stencil/bfcl.py` = f641e477…, both
verified against `git show 7b8de79:<path>`), with the repo's tokenizer symlinked in. One earlier census run (the coder's
30 % stub) executed in the live working tree between 13:04 and 13:23; it is reported as indicative only.

Hard rules: CPU only (`CUDA_VISIBLE_DEVICES=''`, the script also unsets it); no model, trunk, classifier weights or GPU
process launched or touched (the GPU shakedown preflight pid 98758 and the codex wrapper were left alone — nothing was
signalled); no sealed BFCL row and no IFEval input opened (the loader used is the registered dev-offsets loader; the
offsets index was inspected for its key structure only); no repo file written except this report. Disclosure: two census
invocations exceeded the 600 s tool limit and were moved to the background by the tool harness itself (not by me); I
neither launched anything with `nohup`/`&` outside a `wait`-ed foreground group nor signalled them; both completed normally.

## Bottom line

The v6 commit closes most of F1-F10 and BFCL-V4-1..7 mechanically, and the registered dev census passes under the coder's
stub scorer (11/115 evicting turns; 0 `match_impossible`; |echo_token_delta| ≤ 5). But re-running my own v4 census (same
pseudo-scorer, keep rates 0.1 and 0.3) against the committed code shows that the nearest matcher still produces a
resource-mismatched `clf_control` on 2 of the 11 dev evicting turns at rate 0.3 — reported as usable (`match_impossible`
False, `control_role_shortfall` False) with FEWER pinned columns than the treatment. On dev this fails the registered
per-role invariant and the preflight stops (`INVARIANT_FAILURE` → INCONCLUSIVE); in the sealed run nothing checks it, so
A1's estimand would silently change. That is F1 reopened at the implementation level (sol's BFCL-V6-1 finds the same
defect by construction; my census shows it fires on real dev data). A second registered-definition deviation is new in v6:
a `full` turn whose INITIAL PROMPT exceeds 40,960 positions (6 of the 11 dev evicting turns) is now recorded as a
truncated fail instead of NA, so `full`'s truncated baseline is inflated and every arm's `truncated <= full + 1` bound
loosens by one case per affected case (2 of 4 exposed dev cases). VERDICT: UNSOUND — two exact fixes, then re-run the
census with per-role equality asserted, then the registered preflight.

## Dev census (CPU, no model, stub scorers), committed v6 code

All 32 dev cases, 115 teacher-forced histories rebuilt through the vendored environments with the harness's own
`build_teacher_history`; eviction decided by `context_layout` (`history_end > K`); plans via the harness's own
`_turn_plan` for `clf_pinned_echo`, `clf_control`, `recency_pinned`, `tool_swap_echo`. Evicting turns: exactly 11, all
`long_context` (case24 t4/t5, case27 t1-t6, case28 t5, case31 t3/t4) — scorer-independent, as registered.

| scorer | impossible (any comparator) | echo_token_delta range | clamp residual max | per-role equality failures (no-shortfall clf_control) |
|---|---|---|---|---|
| coder's 30 % hash (live tree, indicative) | 0/33 | −5 … 0 | 5 | 0 |
| fable rate 0.1 (mirror) | 0/33 | −3 … 0 | 3 | 0 |
| fable rate 0.3 (mirror) | 0/33 | −7 … 0 | 7 | **2/11**: case24 t5 (control user 46 vs treatment 47, tool 262=262), case28 t5 (user 26 vs 35, tool 688=688) |
| stress user 0.5 / tool 0.1 (cases 24, 28) | 0 | −8 … 0 | 8 | 0 |
| stress user 1.0 / tool 0.05 (cases 24, 28; forces other-role fallback) | 0 | **−46, −35, −10** | 46 | n/a (shortfall turns; totals exact) |

Other census facts: `tool_swap_echo` and `recency_pinned` matched per-role columns exactly on every turn under every
scorer; comparator echo entries were always a subset of the comparator's pins and only the LAST entry was ever truncated
(the registered A3 allowance); width deltas were 0 for 90 %+ of matches (tool chunks) and −23…+115 for user sentences;
turn deltas −4…+3. Full prompt length exceeded 40,960 positions at 6/11 evicting turns (case27 t2 41,874; t3 41,990; t4
43,594; t5 43,674; t6 43,804; case31 t4 41,102; max over all 115 turns 43,804), so the dev A3 population is 5 turns / 4
clusters — reported, not gated.

## Findings by severity

### FV6-1 — CRITICAL — nearest matching stops on the AGGREGATE column total and discards the clamp's failure; on dev (rate 0.3) 2/11 evicting turns yield a short, mislabelled `clf_control`
Code (7b8de79): `_resource_match` pre-checks only `sum(permitted columns) < required` (bfcl.py:499), then round-robins the
targets `while sum(matched columns) < required` (bfcl.py:511) — a total, not per-target and not per-role. `build_matched_control`
(bfcl.py:585-604) then clamps to the treatment's PER-ROLE quotas but discards `clamped["match_impossible"]` and returns
`"match_impossible": False` unconditionally (line 604); `tool_swap_plan` does the same (line 741). Consequence: when the
same-role nearest matches are net narrower for one role and wider for the other, the loop ends with the total satisfied,
the clamp cannot fill the short role, and the control is returned short with `role_column_deltas` ≠ 0, `control_role_shortfall`
False, `match_impossible` False. Evidence: (a) synthetic — treatment user 10 + tool 128, pool user×100, tool×50×3 (150 tool
columns available, so NOT impossible under A3): result user 10, tool 50, deltas tool −78, impossible False, shortfall
False; (b) dev, rate 0.3: case24 t5 control 308 columns vs treatment 309 (user match −1 wide, another +7), case28 t5 714 vs
723 (user matches −23/−8/−4/−1 vs +0, tool exact). On dev these fail `assert_dev_invariants` `comparator_columns`
(bfcl_mt.py:1596-1606) → `INVARIANT_FAILURE` → the leg is INCONCLUSIVE by a harness bug. In the sealed run neither
`_turn_plan` nor `run_case_arm` nor the schema asserts comparator columns, so the turn runs with a different dose and A1
is reported as usable. The coder's census test (`test_real_dev_dry_census_nearest_matching_and_echo_clamp`) asserts
only `match_impossible` and the delta, not per-role equality, which is how this slipped through with a scorer that
selected almost no user sentences (9/11 turns had user = 0).

Fix (code, `src/stencil/bfcl.py`):
1. `_resource_match`: pass 1 — for EVERY target in `kept` order take the nearest unused candidate (key `(|Δwidth|, |Δturn|,
   stable source)`), same role first, other role only if `allow_role_fallback` and the same-role pool is empty (set
   `shortfall`). Pass 2 (supplementation, deterministic) — per role, while that role's matched columns < the treatment's
   role quota, add the unused same-role candidate whose width is nearest to the residual (same tie-break); if the same-role
   pool is exhausted and `allow_role_fallback`, continue from the other role and set `shortfall`; if nothing remains, return
   impossible. Never terminate on the aggregate. Keep `_match_target_index` for pass-1 matches; supplements carry the index
   of the last target of that role so `tool_swap_plan` keeps treatment order.
2. `build_matched_control` / `tool_swap_plan`: after the clamp, `match_impossible = clamped["match_impossible"]`; on no-
   shortfall turns assert `clamped["role_counts"] == needed`, on shortfall turns assert the total equals `sum(needed)`;
   raise (harness assertion, not a method outcome) if a "usable" plan violates either.
3. `scripts/bfcl_mt.py:_turn_plan`: after building the three comparators assert, for every comparator not
   `match_impossible`, the same per-role/total equality and `abs(echo_token_delta) <= 16` BEFORE any generation (sealed
   included), so the sealed path is fail-closed and not fail-open.
4. Tests: (a) the synthetic case above must yield user 10 / tool 128 (three tool rows, last truncated) — not impossible,
   not short; (b) two selected tool chunks with one wide disjoint replacement must be clamped to the exact tool quota with
   `match_impossible` False only if columns suffice; (c) extend the dev census test to assert
   `plan["selector"]["pinned_columns_by_role"] == treatment["pinned_columns_by_role"]` on non-shortfall turns and run it
   with at least two stub keep rates (0.1 and 0.3) plus a role-skewed stub that selects user sentences.

### FV6-2 — HIGH — `full` initial-prompt overflow (registered NA, excluded) is now a truncated FAIL, inflating `full`'s safety baseline
Code: `position_overflow_result` (bfcl.py:803-812) returns `pass=False, truncated=True` for every overflow; `run_case_arm`
(bfcl_mt.py:1016-1021) uses it at step 0 with `cache is None` (the initial-prompt case) as well as at later steps;
`_safety` (bfcl.py:1346) counts `turn["truncated"]` per case. Registration (v7): "Turns whose full prompt exceeds 40,960
positions are excluded from A3 and counted; at those turns full does not generate (per-turn pass NA; excluded from full's
final-pass reporting as position_overflow). Any arm whose WITHIN-TURN cache exceeds 40,960 … is a truncated event". A3 item 3
converts only the WITHIN-TURN case to a truncated fail (and forbids None), not the prompt case. Evidence: dev has 6/11
evicting turns with full prompt > 40,960 in cases 27 and 31 → `safety.counts.full.truncated` = 2 from non-generation
events → every arm's `truncated <= full + 1` allows 3 truncated cases on a 4-exposed-case dev primary set; CPU synthetic:
a treatment with 2 truncated cases vs full's 1 prompt-overflow "truncation" passes the check (`True`). On the sealed cohort
(16 long_context cases, similar lengths) this can admit ~half the exposed cases as free truncations. Secondary: the
competence floor `full_long_turn_passed` (bfcl_mt.py:1725) counts the NA turns as fails (conservative but not the
registered "NA"); `_arm_summary.final_pass` (bfcl.py:1187) excludes full cases on ANY overflow, including within-turn
ones that A3 says are counted fails (sol V6-6 agrees).
Fix: in `run_case_arm` record `overflow_phase` ∈ {`initial_prompt`, `within_generation`, `tool_step`}; for `arm == "full"`
and `initial_prompt`: `pass=False` (never None; A3 exclusion already keys on `prompt_positions > 40960`), `truncated=False`,
`position_overflow=True`, `na=True`; `_safety`'s `truncated` and the competence numerators must skip `na` turns;
`_arm_summary.final_pass` exclusion keys on `initial_prompt` only. Test: synthetic full record with `prompt_positions=50000`
→ `safety.counts.full.truncated == 0`, `a3.excluded_over_40960 == 1`; within-turn overflow → truncated 1 and final_pass False.

### FV6-3 — MEDIUM — the token-exact clamp can only truncate; a comparator with fewer/wider entries undershoots the treatment by the framing difference, which can exceed 16
Code: `_echo_clamp` (bfcl_mt.py:572-618) admits whole entries while ≤ target and truncates the first non-fitting one; if
every entry fits it returns residual = target − tokens. Each echo entry costs ~6 framing tokens (`\n- role: "…"`), so a
comparator built from fewer (wider) resources than the treatment's many short user sentences cannot reach the target.
Evidence: stress stub selecting every prior user sentence (forces other-role fallback to 128-column tool chunks):
case24 t4 delta −35 (13 treatment entries vs 5), t5 −46 (18 vs 7); case28 t5 −10. Registered census scorers stayed within
−8 … 0, so this is not a dev blocker, but A3's "holds by construction" is false in the fallback regime and the sealed
behaviour is then "uninformative A1" (summarize_records) rather than the registered harness assertion (sol V6-3).
Fix: (i) assert the delta in `_turn_plan` (FV6-1 item 3); (ii) report `echo_clamp_residual` and entry-count difference in
the preflight `selector_coverage`; (iii) text (orchestrator): either register the residual as the framing-count
difference bound (`6 × |entries_treatment − entries_comparator|`) or register that a comparator whose whole-entry echo is
shorter than the treatment's target is recorded (`echo_undershoot`) and stays usable when |delta| ≤ 16 — as now — with
larger undershoot a harness assertion. Test: a comparator with 3 fewer entries than the treatment must give
`abs(delta) <= 16` or raise, never silently proceed.

### FV6-4 — MEDIUM — sealed run has no comparator/echo assertion (fail-open); preflight report lacks `match_impossible` counts
Only `assert_dev_invariants` and the preflight `excessive_echo` list (bfcl_mt.py:1650-1665) check comparator columns and
deltas; `run --split sealed` never calls them. `preflight.json` reports `match_deltas` but no per-comparator
`match_impossible` count, so a dev `match_impossible` (A1 uninformative by construction) is invisible unless the reviewer
reads records. Fix: FV6-1 item 3 plus `invariants.match_impossible = {arm: count}` in the preflight report and a stop
when `clf_control` has any on dev (A1 uninformative on dev cannot be certified).

### FV6-5 — LOW — F5 residuals: manifest closure and provenance
`harness_manifest` (bfcl_mt.py:141-164) hashes the runner, eight `src/stencil` modules and the vendored checker tree
(`func_source_code/*.py` included via `rglob`). Not covered: `src/stencil/__init__.py`, the `stencil.bench` import chain
(`vendor/ifeval`, `langdetect`) pulled in only for `EOS` (sol V6-5), and the git commit/dirty flag I asked for. Fix: define
the two EOS ids in `bfcl_mt.py`; add `__init__.py` files; record `git rev-parse HEAD` and `git status --porcelain` (non-
empty → refuse sealed) in meta.

### FV6-6 — LOW — `seed` is dead but still registered as the tie-break
`_resource_match` does `del seed` (bfcl.py:485) — Amendment 3 makes ties stable-source, but the arm text still says
"frozen seed 20260903" and meta records `control_seed`. Fix: meta `control_tie_break: "nearest-width, nearest-turn,
stable-source"`; orchestrator to note in LEDGER that the seed is retained only for `same_role_control_spans` (v2 API).

## Disposition of prior findings (v6 code, 7b8de79)

| finding | status | evidence |
|---|---|---|
| F1 exact matching | **REOPENED (FV6-1)** | nearest key present; loop terminates on aggregate total; clamp failure discarded; fires on dev rate 0.3 (2/11) |
| F2 echo delta | **CLOSED on dev, residual FV6-3** | char-exact whole entries (`_decode_row`), token-boundary clamp of the last entry; census deltas −7…0; framing undershoot unbounded in the fallback regime |
| F3 full overflow None crash | **CLOSED, new deviation FV6-2** | no None reaches the summary (schema requires bool); prompt overflow conflated with within-turn truncation |
| F4 degenerate on truncated | CLOSED | `_degenerate` returns False when truncated; tests |
| F5 harness hash scope | PARTIAL (FV6-5) | manifest over listed modules + checker tree + template; no git provenance; import chain incomplete |
| F6 tool_swap order | CLOSED | replacements inserted at the tool target's position in `kept` order; verified on dev (entries_subset, order) |
| F7 scorer truncation count | CLOSED | `scoring_pair_token_count` measures the untruncated pair with the placeholder context |
| F8 bookkeeping | CLOSED | measured `current_turn_prefilled_before_eviction`; `pinned_columns` 0 when not evicted; events scoped to their arm; candidate index asserted in `select_history_spans` and in the invariant family; `treatment_role_counts`/`control_role_counts` |
| F9 reporting | CLOSED | `outcome` label from `primary_claim_status`; `non_evicting_stratum` (t ≥ 2, no eviction, treatment echo > 0); per-arm dose/event aggregates incl. nominal/actual B |
| F10 dev loads sealed rows | CLOSED | seek-only offsets loader; v5 test wraps `Path.open` and proves no read overlaps a sealed byte range (65 passed) |
| BFCL-V4-1 | CLOSED for reads (byte verification of used rows: sol V6-2, concur) | `load_cases` reads dev offsets only, id checked before decode |
| BFCL-V4-2 | CLOSED | preflight raises on every failed gate; certificate digest-bound; sealed CLI requires certificate, rejects `--limit`, arm/trunk/settings mismatch (CPU-checked: reduced-arm certificate refuses a full-arm sealed meta; gate dict without `passed` refused) |
| BFCL-V4-3 | CLOSED | `primary_claim_status` table tested; A2 separate; A3 split fields; A4 gated on treatment + tool_swap safety only |
| BFCL-V4-4 | CLOSED (name normalisation: sol V6-4, concur) | truncated-degenerate; unmatched tags invalid; echoed calls in the repeated set |
| BFCL-V4-5 | CLOSED | manifest; run identity in records; exact ordered cohort; extra/stale records refused |
| BFCL-V4-6 | CLOSED | six named families with `{passed, n}`; candidate source asserted twice |
| BFCL-V4-7 | CLOSED except overflow phase (FV6-2) | `pin_overflow_total` computed before the base/full early return (recorded only on the treatment arm); tool order; `prior_user_spans`; non-evicting stratum |

## CPU verification log
`pytest tests/test_bfcl_evict_v{2,3,4,5,6}.py -k "not real_dev_dry_census"` → 65 passed, 1 deselected (the census was
re-run by my own script instead). Scratchpad scripts (not committed): `v6_census.py` (mirror-rooted, scorer/case/turn
ranges; outputs `m_*.json/.log`), synthetic matcher check, synthetic overflow/certificate check. Registration hash
recomputed. No model, GPU, or sealed content touched.

## VERDICT: UNSOUND

Blocking for the registered preflight, in order:
1. FV6-1 — per-target then per-role supplementation matching; propagate the clamp's `match_impossible`; assert per-role /
   total equality and the echo delta in `_turn_plan` for every usable comparator (sealed included); census test asserts
   per-role equality under ≥ 2 keep rates and a user-skewed stub.
2. FV6-2 — separate `initial_prompt` overflow of `full` (pass=False, truncated=False, NA-flagged, excluded from safety
   `truncated` and from competence numerators, A3-excluded) from within-turn overflow (truncated fail, counted).
3. FV6-3/FV6-4 — residual reporting and the sealed-path assertion; text note on the framing undershoot.
4. FV6-5/FV6-6 — provenance and meta.
Then re-run the v2-v6 suites plus the extended census, re-register the harness manifest, and only then run the registered
dev preflight from a new output directory (the running `bfcl-evict-v2-preflight` shakedown was launched under pre-v6 code
and cannot become the certificate).
