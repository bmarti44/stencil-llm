# BFCL harness v4 review (fable) — registration v7 + Amendments 1–2

Reviewed: commits a496212 (harness), cdad4ea (handoff), 9fd70bd (Amendment 2 text). Code files are byte-identical
between a496212 and 9fd70bd (`git diff a496212 9fd70bd -- src scripts tests` is empty). NOTE: while this review ran, a
v5 coder wrapper (brief 5578c17, `.review.lock` 11:50) began modifying `src/stencil/bfcl.py` and `scripts/bfcl_mt.py`
in the working tree (mtime 11:58). Every line reference and every CPU experiment below is against the COMMITTED
9fd70bd code (experiments were re-run on a `git archive HEAD` mirror in the scratchpad and reproduced identically).
Governing text: LEDGER-PLAN.md:623-730. Method: full read of `scripts/bfcl_mt.py`, `src/stencil/bfcl.py`,
`src/stencil/selector_v2.py`, `src/stencil/stats.py`, `src/stencil/qwen3.py:70-131`, the v2/v3/v4 tests, the
vendored executor; CPU-only experiments (pytest 32 passed; exact sign-flip brute-force cross-check; dev-slice plan
simulations through the harness's own `_turn_plan` with a deterministic pseudo-scorer — no GPU, no trunk, no
classifier weights loaded, no sealed content read, aggregates only).

## Bottom line

Item-by-item the harness is a faithful transcription of most of v7 (teacher forcing, message-index eviction,
overflow order, candidate pipeline, exact sign-flip + Holm, A3 gate, sealed guard, meta refusal). But two design
readings make the registered contrasts unreadable BY CONSTRUCTION on the dev slice itself, and the harness's own
preflight would stop on the first dev run:

* F1 (CRITICAL): "matched on token width and source-turn age" is implemented as EXACT width equality AND exact
  source-turn equality with no reuse (`_resource_match`, bfcl.py:459-505). On dev, 94.9% of user sentence
  candidates have no same-role exact-width partner and 27.2% have none in either role; every one of the 11 dev
  evicting turns contains such candidates; with a pseudo-scorer, `clf_control.match_impossible` fired on 5/11
  (keep-rate 0.1) and 7/11 (keep-rate 0.3) evicting turns, `tool_swap_echo.match_impossible` on 2/11. One
  `match_impossible` primary turn makes A1 (or A4) uninformative for the whole leg; A1 uninformative = INCONCLUSIVE
  (Amendment 2). The clamp rule of Amendment 2 only has a job if widths are matched approximately; under exact
  width matching the clamp is vacuous (quota == matched width), which shows the exact reading is not the intended
  one. fable's v5 review R6 warned exactly this.
* F2 (CRITICAL): the `abs(echo_token_delta) <= 16` rule cannot be met by the implemented echo construction. On
  dev evicting turns the simulated deltas were: `recency_pinned` −13…−115 on 10/11 turns (9/11 beyond 16),
  `clf_control` −131 and `tool_swap_echo` −118/−121/−131 on turns where the match succeeded. Two causes:
  (a) comparators are capped at the TREATMENT's echo token count (`_echo_cap(..., cap=classifier_echo_tokens)`,
  bfcl_mt.py:479,510,527) while their entry text is DECODED from token columns (leading spaces, trailing "\n"
  escaped in JSON — 659/1498 dev spans decode differently from their char text), so a +1…+3 token inflation drops a
  whole 128-token entry; (b) whole-span capping at E=1024 with B up to ~9,000 columns means the echo covers only
  ~7 of ~29 pinned entries, and the comparator's different span partition fills to a different whole-span total.
  Registration: "On dev, a larger delta stops preflight" → `preflight()` raises at bfcl_mt.py:1207-1210 on the
  first dev run. The leg cannot reach the sealed cohort with this code.

Plus one crash (F3), one registered-definition deviation in safety (F4), and freeze/report gaps. VERDICT: UNSOUND.
The fixes are exact and small; F1/F2 additionally need a text-only reading recorded in LEDGER-PLAN before the dev
preflight (the registration's "registered width/age matching rule" is never defined, and the echo clamp needs the
same truncated-entry allowance Amendment 2 already gives the column clamp).

## Findings by severity

### F1 — CRITICAL — exact-width/exact-turn matching makes A1 and A4 uninformative by construction
Code: `_resource_match` (bfcl.py:459-505): `same = [... row["role"] == target["role"] and int(row["turn"]) ==
int(target["turn"]) and len(_row_columns(row)) == width]`; fallback pool identical with `role !=`; `if not pool:
return [], True, shortfall` → `match_impossible`. `tool_swap_plan` (bfcl.py:637-682) uses the same matcher without
fallback. Evidence (dev slice, teacher histories built with the harness's own `build_teacher_history`, all 115
turns / 11 evicting turns, all long_context): user candidates 628, without same-role/same-turn/exact-width
disjoint partner 596 (94.9%); tool candidates 2602, 319 without (12.3%); 879/3230 (27.2%) without ANY-role
partner; per evicting turn the fraction of partner-less candidates was 0.59, 0.68, 0.09, 0.02, 0.03, 0.04, 0.05,
0.06, 0.41, 0.03, 0.05 — and a treatment turn pins up to 29 spans without reuse, so the joint probability that
every pin finds a distinct exact partner is tiny whenever any user sentence is selected. `_turn_plan` simulation:
`clf_control` impossible at case24 t4/t5, case27 t6, case31 t3/t4 (rate 0.1) and additionally case27 t4/t5,
case28 t5 (rate 0.3) — every turn where ≥1 user span was pinned; `tool_swap_echo` impossible at case24 t5 and
case28 t5 (rate 0.3). Consequence per registration: A1 uninformative → primary claim INCONCLUSIVE; A4
uninformative → no tool-source claim; this is decided by the harness design, not by the data.

Fix (code, `src/stencil/bfcl.py:_resource_match`):
1. Replace the exact filters with a nearest-match ranking. For each `target` in `kept` order, over `available`
   rows of the SAME role compute key `(abs(width(row) - width(target)), abs(int(row["turn"]) - int(target["turn"])),
   tie[id(row)], int(row["span"][0]))`; if the same-role pool is empty AND `allow_role_fallback`, use the other-role
   pool with the same key and set `shortfall = True`; take the minimum; remove it from `available` (no reuse).
   `impossible = True` only when `available` is empty before all targets are served.
2. After matching, keep `clamp_candidate_rows(matched, quotas=needed_by_role_after_fallback, ...)` so the total
   pinned columns equals the treatment's exact total (per-role exact on no-shortfall turns); the clamp now does its
   registered job. Set `match_impossible = True` if `clamp["match_impossible"]` (pool columns < quota) — that is the
   Amendment-2 definition ("cannot supply the exact total pinned-column quota").
3. Record per match: `width_delta`, `turn_delta`, role used; report their distributions in the preflight
   (`selector_coverage`) so the reviewer sees how far from exact the matches are.
4. `tool_swap_plan`: same ranking restricted to TOOL rows; `match_impossible` iff no disjoint TOOL candidate
   remains for a selected TOOL chunk or the clamp cannot reach the tool quota.
5. Text (orchestrator, before preflight): record in LEDGER-PLAN the reading "width/age match = nearest token width,
   then nearest source-turn distance, seed tie-break, one-to-one without reuse; the column clamp makes the count
   exact" as the definition of the "registered width/age matching rule". Unit tests: a selected user sentence with
   no equal-width sibling must match (not be impossible); a pool of one disjoint candidate for two targets must be
   impossible.

### F2 — CRITICAL — the comparator echo construction cannot satisfy `abs(echo_token_delta) <= 16`; preflight stops
Code: `_echo_cap(tokenizer, control["entries"], context, close, cap=classifier_echo_tokens)` (bfcl_mt.py:474-481,
506-512, 522-528); entries' text is `tokenizer.decode(context_ids[span])` (`_decode_row`, bfcl.py:400-415) for every
comparator row, truncated or not; the treatment's entries use the char-exact `context[char_start:char_end]`
(bfcl.py:279). Evidence (committed code, dev evicting turns, `_turn_plan` with pseudo-scorer): treatment echo
934-1015 tokens covering 7-9 whole entries of 29 pinned; deltas `clf_control` −3/−1/−131, `recency_pinned` −13, 0,
−112, −77, −29, −89, −66, −16, −91, −29, −74 (rate 0.1) and −57…−115 (rate 0.3), `tool_swap_echo` up to −131.
Registration (LEDGER-PLAN.md:668): dev delta > 16 stops preflight; in the sealed run it voids the contrast.

Fix (code):
1. `scripts/bfcl_mt.py`: replace the three comparator `_echo_cap(..., cap=classifier_echo_tokens)` calls with a new
   `_echo_clamp(tokenizer, entries, context, close, target_tokens=classifier_echo_tokens)` that admits whole entries
   while the measured echo token count ≤ target, then for the next entry binary-searches the longest Qwen-token
   prefix of that entry's pinned columns whose rendered echo makes the measured count exactly `target_tokens`
   (decode `context_ids[span0:span0+n]`, re-measure via `_echo_current_user`; if no n gives equality take the
   largest n below target and record the residual). Result: `echo_token_delta` is 0 (or a recorded residual ≤ the
   framing overhead, far below 16); keep the ≤16 assertion as the guard. Truncated entries are prefixes of pinned
   spans, so "echo = pinned spans only" holds.
2. `src/stencil/bfcl.py:_decode_row`: when `len(columns) == span width` (no truncation) keep `row["text"]` (the
   char-exact candidate text, identical construction to the treatment); decode from token columns only for the
   truncated row. This removes the systematic +tokens from leading spaces / escaped newlines.
3. Text (orchestrator, before preflight): extend Amendment 2's truncated-entry allowance from the column clamp to
   the echo clamp ("the comparator echo is clamped to the treatment's echo token count at a Qwen3-token boundary;
   its last entry may be a truncated prefix of a pinned span"). Unit test: a comparator whose whole-span echo would
   exceed the treatment's count by 3 tokens must yield delta 0, not −(entry length).

### F3 — HIGH — `full` within-turn position overflow yields `pass=None` and `summarize_records` crashes
Code: bfcl_mt.py:868-872 `{"valid": None} if turn_position_overflow and arm == "full"` regardless of whether the
overflow was the prompt (registered NA, excluded from A3 via `prompt_positions > 40960`) or a within-turn cache
exceedance (registered: "stops generating at that step; the turn is a truncated event for that arm and scores
fail"). `generate()` (bfcl_mt.py:280-283) also sets `truncated=True` for full in that case while
`position_overflow_result("full")` says `truncated=False` — the two paths disagree. CPU reproduction: a v3 fixture
record with `full.turns[0].pass=None` and `prompt_positions=9000` → `summarize_records` raises `TypeError: float()
argument ... 'NoneType'` (bfcl.py:1305,1315 `float(_turn_by_index(record,"full",...)["pass"])`). Sealed summary
would crash after all GPU work.
Fix: in `run_case_arm` record `prompt_position_overflow = position_action["position_overflow"] and cache is None`
separately from `turn_position_overflow`; score `valid=None` ONLY for `arm == "full" and prompt_position_overflow`;
otherwise (any arm, within-turn) `valid=False, truncated=True`. In `cluster_values`, guard: if either arm's
`pass is None` at a primary turn, count it in `excluded` (A3 population) and never call `float(None)`.
`_arm_summary.final_pass` exclusion should key on the prompt-overflow flag, not on any overflow.

### F4 — HIGH — `_degenerate` evaluates truncated generations (registered: non-truncated only)
bfcl_mt.py:638-642 ignores `truncated`. A 512-token repetitive loop counts as both truncated and degenerate for
every arm; `degenerate <= full` has no +1, so this asymmetric double count can breach safety. (sol found the
same.) Fix: `if truncated: return False` as the first statement; test `[1,2,3,4]*20, truncated=True` → False and
`truncated=False` → True.

### F5 — MEDIUM — the frozen "harness hash" covers only `scripts/bfcl_mt.py`
`artifact_meta` (bfcl_mt.py:1032): `"harness": sha256(__file__)`. All eviction/selection/comparator/statistics
logic lives in `src/stencil/bfcl.py`, `selector_v2.py`, `qwen3.py` (KVCache.evict, prefill_with_eviction),
`stats.py`, `bench.py` (EOS), `determinism.py`; a change there re-registers nothing. Fix: `"harness":
_tree_sha256([ROOT/"scripts/bfcl_mt.py", *(ROOT/"src/stencil"/f for f in ("bfcl.py","selector_v2.py","qwen3.py",
"stats.py","bench.py","determinism.py"))])`, and record the harness git commit (`git rev-parse HEAD`) plus a
dirty flag in meta; refuse to run sealed from a dirty tree.

### F6 — MEDIUM — `tool_swap_echo` echo order is users-then-tools, not treatment rank order
bfcl.py:672 `entries = users + matched["entries"]`. Registration: echo entries "most probable first", byte-identical
framing. Since the E cap is whole-span, the reordering changes which entries survive the cap and is a second,
unregistered difference between treatment and A4. Fix: walk `kept` in order, emitting the user row itself or the
tool row's match (keep a dict `match_for[id(tool_row)]`), so entry order equals treatment order.

### F7 — MEDIUM — `scorer_truncated_candidates` undercounts
selector_v2.py:104-109 counts `len(tokenizer(f"[{role}] {value}"))` > 192, but the scoring input is the PAIR
`("(no context)", "[role] text")` with `truncation="longest_first", max_length=192`; a candidate of 185-192 tokens
is truncated but not counted. Fix: count `len(self.tokenizer(context_or_placeholder, f"[{role}] {value}",
truncation=False)["input_ids"]) > 192`.

### F8 — LOW/MEDIUM — invariant bookkeeping is partly literal or duplicated
- `current_turn_prefilled_before_eviction: False` (bfcl_mt.py:757) and `passed_fraction: 1.0` (bfcl_mt.py:1191)
  are constants. The property IS enforced (qwen3.py:120-123 raises), but the report should carry the measured
  value: record `cache.length == history_end` at the eviction point and compute `passed_fraction` as
  checked_ok/checked.
- `control_role_shortfall`, `pin_overflow`, `pin_overflow_total`, `role_column_deltas` are copied from the shared
  plan into EVERY non-base arm's `eviction` row (bfcl_mt.py:746-760), so `assert_dev_invariants` counts one
  shortfall six times and `_arm_summary.control_role_shortfall` is reported for arms that have no control. Fix:
  store the shared turn facts once (`record["turn_facts"][turn]`) or zero them for arms they do not describe.
- `pinned_columns` on NON-evicting turns equals the plan's pin width (bfcl_mt.py:244-248 `else sum(end-start)`)
  although nothing was evicted or pinned; the `columns.pinned` mean is therefore wrong. Fix: 0 when not evicted.
- No explicit assertion that every candidate's `message_index < current user index` (invariant 6); it holds by
  construction (bfcl.py:238-239). Add `assert all(row["message_index"] < current_user_index for row in candidates)`.
- `build_matched_control` returns `"role_counts": needed` (treatment's), and `_turn_plan` exposes it as
  `selector.role_counts`; rename to `treatment_role_counts` and add the control's actual counts.

### F9 — LOW — reporting gaps against "Reported, not gated"
`reported.non_evicting_turns` is a count; the echo-only stratum has no per-arm pass. `scorer_truncated_candidates`,
`echo_dropped_control_tokens`, `pin_overflow_dropped_columns`, nominal-vs-actual B are per-turn only. No field
computes the Amendment-2 outcome label (A1 uninformative → INCONCLUSIVE; eligible A3 with A1 or A3 failing →
unsupported; A3 uninformative + A1 pass → "supported on A1 only"). Fix: add `reported.non_evicting_stratum`
(per-arm per-turn pass over non-evicting turns t ≥ 2 with a non-empty echo), aggregate the four counters per arm,
and add `outcome` computed mechanically from `holm`, `contrasts[*].status`, `safety`.

### F10 — LOW — dev-mode process loads sealed rows
`load_cases` (bfcl_mt.py:120-133) parses every row of `cases_*.jsonl`/`answers_*.jsonl` into memory and indexes
by id before selecting the cohort. Nothing sealed is printed, executed or scored, so the "not opened or executed"
claim survives in substance; hygiene fix: stream and keep only ids in `cohort[split]`.

## Item-by-item disposition

(1) Teacher-forced rendering — CONFIRMED. `build_teacher_history` (bfcl_mt.py:377-401) re-executes ground truth
through the vendored environments with a fresh instance key per (run_tag, arm, turn) (`execute_multi_turn_func_call`
keys instances by model_name+id+class in module globals), renders `<tool_call>` JSON + `<tool_response>`; no echo
or arm text from earlier turns is carried; pins/echo are recomputed per turn. Identity: `run_case` compares
`context_ids_by_turn` across all arms at every turn and raises (bfcl_mt.py:985-991) — this is the source-history
(pre-echo) render, as registered. Turn scoring: `ground_truth[:t]` + arm turn t, `ground_truth[:t+1]`
(bfcl_mt.py:855-863). Case all-or-nothing pass = all non-NA turns. Free-running restricted to base/clf_pinned_echo.
(2) Eviction — CONFIRMED with F3/F8 caveats. Range `(max(4, system_end_tokens), tokens_before(<|im_start|>user of
message index m))` by message index (bfcl.py:64-120); decision `history_end > K` at step 0 for `turn_index >= 1`
and `arm != "full"`; pre-query prefill asserts no current-turn id in cache; cache persists across steps
(`continuation_ids`), no second eviction, `columns_after_step` recorded; overflow drops whole lowest-ranked pins
(`kept` is in (P, recency, source) order; `kept.pop()` from the tail) and iterates the echo cap until stable
(bfcl_mt.py:441-457); `pin_overflow_total` when prefix + no-echo turn > K drops everything and empties echo for
all non-full arms (role_pinned too); comparators are built from the post-drop `kept`; prefix/current-turn ids are
outside the evict range by construction. Dev note: prefix 3.5-6.4k columns + K=8192 means pin_overflow fires on
8/11 dev evicting turns (actual pins 1,024-3,593 of nominal B 8,943-8,979) — a registered property, correctly
recorded, but it makes "B = 25%" nominal only; report it prominently.
(3) Selector — CONFIRMED except F7. Prior USER sentences via the frozen splitter; TOOL output newline-first
(`_tool_line_spans`), sentence-split, then 128-token consecutive chunks (`_chunk_char_span`; 0/2211 dev candidates
exceed 128 columns; 0/648 messages have overlapping candidate columns); candidates only from `message_index <`
current user; scored role-wise with empty context, `longest_first`, `max_length=192`; keep ≥ 0.5; rank (−P, −turn,
−message_index, source order); whole-span fill to `floor(0.25 × evictable)`, first non-fit ends; marker/special-id
drop counted (0 on dev). Echo: header, `- user:`/`- tool:` JSON-quoted, kept order = most probable first, whole
spans ≤ 1,024, inserted before the current user `<|im_end|>`, fixed across steps, only pinned entries.
(4) Comparators — FAILS (F1, F2, F6). Role quotas, shortfall fill/recording, arm-specific `match_impossible`
routing, recency ordering and clamp mechanics are implemented; the exact-width reading and the echo cap defeat them.
(5) Statistics — CONFIRMED. `exact_sign_flip` enumerates 2^k masks, keeps zeros, counts ties in the upper tail,
no mid-p; brute-force cross-check agrees on 7 vectors. Worked k=6: [100]*6 → 1/64 = 0.015625; [100]*5+[0] → 2/64;
[100]*5+[−33.3] → 2/64 (any single negative gives 1/32 at k=6); k=7 [100]*6+[−50] → 2/128 = 0.015625; Holm over
{A1 1/64, A2 2/64, A3 2/64}: A1 passes at 0.05/3 = 0.0167, A2 fails at 0.025, A3 blocked — matching decision (iii).
Holm restricted to `status == eligible`; A4 separate at 0.05; k < 6 → uninformative; primary clusters < 6 →
INCONCLUSIVE; A3 gate = cluster-mean(full − base) > 0 on the post-exclusion population, exclusions counted;
descriptive LB = continuity-corrected clustered bound (k=6 all-100 → 83.33). Tie tolerance 1e-12 is harmless at
these magnitudes (differences are multiples of 100/lcm(turn counts)).
(6) Safety — FAILS on F4; otherwise CONFIRMED: case-level any-substep counting on the primary set, per arm vs
full; timeouts=0; truncated/invalid/repeated ≤ full+1; degenerate ≤ full with the degenerate-only "≤1" guard when
full = 0; chat-control echo checked on the rendered echo; treatment breach → all contrasts `failed_safety`;
comparator/base/full breach → affected contrasts uninformative.
(7) Preflight/freeze — PARTIAL. Constants and hash list (registration text incl. Amendments 1-2, now
8be39890…; harness; selector manifest; trunk weights/tokenizer; cohorts 22cf69af… verified; chat template;
vendored checker tree incl. `func_source_code`) are written before model load and refused on any difference
(`_check_or_write_meta`). No `results/qwen/bfcl-evict-v4-*` exists yet, so the Amendment-2 hash will be the frozen
one. Gaps: F5 (harness hash scope), F8 (literal invariant fields), floors/feasibility/cost are reported but not
enforced as stops (sol's review covers gating; I agree it should raise), `n: 40` is a literal.
(8) Reported fields — PARTIAL (F9).
(9) Sealed guard — CONFIRMED: `ensure_split_allowed` requires `STENCIL_SEALED_RUN=1` at argument parsing;
`assert_gpu_free_or_owned` before load.
Non-evaluation BFCL reads: F10 only; `finder_labels.json` is not referenced by the harness. State across arms /
cases: none found — `prepare_case` deep-copies per arm and per turn, environment instances are keyed per
(run_tag, arm, turn), `history_call_raw` is rebuilt per turn in teacher mode, the scorer's truncation counter is
consumed as a per-call delta; the `functools.cache` on `sha256` is path-keyed and safe.

## CPU verification log
`uv run pytest tests/test_bfcl_evict_v{2,3,4}.py` → 32 passed. Scripts (scratchpad, not committed):
`signflip_check.py` (brute-force sign-flip + Holm), `none_pass.py` (F3 crash), `dev_match.py` (exact-width partner
census on the dev slice), `dev_plan_sim.py` (`_turn_plan` on the 11 dev evicting turns, pseudo-scorer keep rates
0.1/0.3), `dev_width.py` (chunk widths, prefix sizes). No model, GPU, or sealed content touched.

## VERDICT: UNSOUND

Required before the dev preflight, in this order:
1. F1 — nearest-width/nearest-turn one-to-one matching + registered clamp in `_resource_match`, `build_matched_control`,
   `tool_swap_plan`; record width/turn deltas; LEDGER text records the reading.
2. F2 — token-exact comparator echo clamp (`_echo_clamp`) replacing `cap=classifier_echo_tokens`; char-text for
   untruncated comparator entries in `_decode_row`; LEDGER text extends the truncated-entry allowance to the echo.
3. F3 — separate prompt overflow (full → NA) from within-turn overflow (all arms → truncated fail); None-guard in
   `cluster_values` with explicit exclusion accounting.
4. F4 — `_degenerate`: `if truncated: return False`.
5. F5 — tree hash over the executing modules + git commit/dirty flag in meta.
6. F6, F7, F8, F9, F10 as specified above.
Then re-run the v4 CPU suite plus new tests for: user-sentence match feasibility, echo delta = 0 under the clamp,
full within-turn overflow scoring, truncated-degenerate, and a dev-slice dry plan (no model) asserting
`match_impossible` and `abs(echo_token_delta) <= 16` on every dev evicting turn with a pseudo-scorer before any GPU
time is spent.
