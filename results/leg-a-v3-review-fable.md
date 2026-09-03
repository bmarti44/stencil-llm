# Confirmation review: LEG A registration v3 — fable, 2026-09-03

Scope: WORKLOG.md last section ("LEG A registration v3", line 2656 to EOF), checked against results/leg-a-review-sol.md
(LEG-A-1..6, its replacement text) and results/leg-a-review-fable.md (the exact text changes). Also read for
evidence: scripts/bfcl_mt.py:299-305 (`_degenerate`), src/stencil/bfcl.py:820-850 (ROUND 7 safety fields),
src/stencil/ledger.py:27,340-359 (renderer/placement), LEDGER-PLAN.md:421-423. One CPU measurement: bge-small vs
Qwen3 tokenizer counts on synthetic BFCL-style tool strings (scratchpad tokratio.py; tokenizers only, no model, no GPU).
No process was launched or signalled beyond that script; the sealed IFEval input and the sealed BFCL cohort contents
were not read; `.review.lock` was not waited on. This file is my only output.

## 1. Adoption audit (every required change from both reviews)

Legend: ADOPTED = verbatim or equivalent; ADAPTED = a deliberate choice between the two reviews (recorded, no fix
needed unless noted); DILUTED / OMITTED = needs a fix (numbered F#, text in section 5).

### sol LEG-A-1..6

| finding | required change | v3 status |
|---|---|---|
| A-1 unit | one of: fresh end-to-end rollouts (primary) or common-history assay; never both under one claim | ADAPTED: teacher-forced primary, free-running secondary (sol's "either is defensible"). DILUTED: outcome rule still says "benefit on agentic dialogue", the end-to-end phrasing (F1). |
| A-2 eviction frozen | K trigger target; flush vs LRU named; sink/prefix union; prefix to end of system turn; suffix reserve; overflow rule; semantic-turn split | ADOPTED except: overflow rule differs (v3 "newest-first", sol "lowest-ranked") and the "protected + suffix alone exceeds K" case is unstated (F2); cache rebuild-vs-persist across turns unstated (F3). |
| A-3 controls | control echoes its own spans, same renderer, same token budget; recency comparator over the same user/tool universe; separate tool-swap arm for any tool claim; frozen seed, disjoint, quotas, fail-closed on impossible match | ADOPTED (clf_control echo, recency_pinned, tool_swap_echo/A4, seed 20260903, disjoint). ADAPTED: fable's role-shortfall fallback replaces sol's fail-closed rule (justified by the 24-308-column user pool, fable M1) — record the deviation and a no-shortfall sensitivity (F4). DILUTED: "exact echo-token equality" became "same template and cap" (F5); recency_pinned's echo is "echoed identically", undefined (F6). |
| A-4 segmentation / echo safety | newline → splitter → token chunks, no longest-line cap; rank P, recency, stable source order; whole-chunk admission; neutral header, JSON-quoted, fail closed on chat-control tokens; structural-replay safety count | ADOPTED: chunking (fable's 128-token rule, no cap), whole-chunk fill, neutral header + role prefixes. ADAPTED: fill stops at the first non-fitting chunk (fable) rather than sol's skip-and-continue — unambiguous, fine. DILUTED: no stable source-order tiebreak (F7); fail-close is a 5-string list, not "any chat-control token" (F8); JSON-quoting dropped (accept: the string list plus the role prefix covers the injection vector sol named, record as deviation); verbatim call replay is reported, not gated (F9). |
| A-5 primary / stats / A3 | pressure-exposed primary by outcome-independent rule; minimum exposed cluster count → INCONCLUSIVE; named p-value method; A3 manipulation check | ADOPTED: exposure = eviction fired (arm-independent under teacher forcing); A3 conditional on full − base > 0. OMITTED: no sealed minimum exposed-cluster count (F10). DILUTED: "one-sided cluster-robust; continuity 100/k" names the LEG B bound implicitly, not the test, the per-cluster A3 difference, or the Holm family size when A3 is ineligible (F11); the manipulation check is not said to be a point estimate or a test (F12). |
| A-6 safety / preflights | case (here: turn) counting; degenerate exclusive of truncation; invalid ≤ full; competence on full; determinism compares full traces; layout/control invariants hold in 100% of dev invocations; feasibility gated; coverage reported; cost cap + hash freeze | ADOPTED: per-turn counting, feasibility gate 4/8 + 4 tool-chunk turns, coverage, constants + harness hash. OMITTED: `degenerate` undefined, and the harness definition includes truncation (scripts/bfcl_mt.py:299-301 returns True when truncated) — F13; the dev invariant preflight (prefix survives, no current-turn id in cache at eviction, exact cache accounting, per-role pinned-column and echo-token equality across treatment/control/recency/tool_swap) is absent — F14; determinism does not say what is compared — F15. DILUTED: `invalid ≤ full + 1` kept without the rationale sol asked for (F16); competence measured on `base` not `full` (F17); hash list lacks trunk/tokenizer/manifest/template/checker (F18). |

sol's LEG-A-7/8 are outside the brief's required set; one note only: v3 lists fable's shortlist and sol's two
landing pages in one sentence with no priority order and keeps "registered after this leg", which sol flagged as too
late. Not verdict-bearing here; flag for the LEDGER-PLAN transfer.

### fable L1..L13 (exact text changes)

| id | v3 status |
|---|---|
| L1 chunking / longest_first / assertion | ADOPTED verbatim. New evidence on the assertion: 128 Qwen3 tokens of directory-listing text re-tokenize to 157-173 bge tokens (ratio 1.23-1.35; 1.46 on a short chunk); with the 5-token first segment and 3 specials the worst measured input is ~181 of 192. The margin is ~11 tokens on path/timestamp-heavy text, so the assertion can fire on real BFCL output and v3 does not say what happens when it does (F19). |
| L2 teacher-forced primary / free-running secondary | ADOPTED verbatim. |
| L3 per-turn primary on evicting turns | ADOPTED verbatim. |
| L4 control echo + cap E | ADOPTED. |
| L5 recency_pinned gated, role_pinned reported | ADOPTED. |
| L6 eviction decision per turn, message index, cache persists within turn | ADOPTED verbatim (across-turn behaviour still open, F3). |
| L7 whole-span fill, B a cap | ADOPTED. |
| L8 A3 conditional; > 40,960 turns excluded and counted | ADOPTED; what `full` does at those turns is unstated (F20). |
| L9 header/prefix, control-token drop, echo-copy override | ADOPTED except the explicit "supersedes LEDGER-PLAN.md:423" pointer is dropped (F21). |
| L10 shortfall rule, no "random" wording | ADOPTED. |
| L11 floor on primary unit, 4B path, 30 GPU-h + arm cut, same trunk | ADOPTED verbatim; the cut set's effect on A4 and on the free-running secondary is unstated, and "5 arms still over 30 GPU-h" has no rule (F22). |
| L12 lineage timeline; post-leg classifier data rule | ADOPTED. Model-card sentence is shorter than either reviewer's text: it omits the non-cohort aggregate analysis → tool-role label, the dev-split trunk selection, and "not pure-KV / not zero-shot" (F23). |
| L13 summarize_records replaced; alpha 0.05 supersedes; 4 determinism ids named | ADOPTED. |
| 3.5 "A2 uninformative if zero tool candidates" | MOVED to A4. Acceptable now that A4 carries the tool claim, and moot: preflight (3) already stops the leg if fewer than 4 exposed case-turns select a tool chunk, so the zero-tool case never reaches the sealed run. Delete or leave; not verdict-bearing. |

## 2. New contradictions introduced by the merge

C1 (vacuity guard vs timeouts). "if full has 0 events of a type, that type is judged '<= 1'" applies, as written, to
   every type including timeouts, where full will normally have 0 — it silently turns "timeouts 0" into "timeouts <= 1".
   Fix F24.
C2 (degenerate vs truncated). Under the harness definition (bfcl_mt.py:299-301) every truncated turn is also degenerate.
   An arm with full + 1 truncations passes "truncated <= full + 1" and then fails "degenerate <= full" (or is rescued only
   by the guard when full has 0). The +1 allowance is nullified by the second clause. Fix F13.
C3 (preflight 3 vs preflight 5). (3) permits "K may be re-registered lower before any outcome is viewed" AFTER the dev
   eviction rate has been viewed; (5) says K is not changed after the preflight. Lowering K on the dev exposure count is
   K tuning on BFCL dev (sol: "no ... K tuning"; fable 4.2a). Fix F25.
C4 (pin overflow vs exact-column control). The control is "built after the echo clamp" but the overflow drop happens
   after the echo clamp too (it needs the echo-bearing turn-t message length), and each arm's echo re-tokenizes
   different text, so arms can overflow by different amounts. Nothing says whether the control/recency/tool_swap arms
   inherit the treatment's post-overflow pinned columns or re-evaluate overflow themselves; if the latter, "A1 holds
   tokens, position and residency constant" is false on overflow turns. Fix F2.
C5 (teacher forcing vs "keeping the arm's pins"). "Before turn t every arm sees the ground-truth trajectory ... context
   ids are identical across arms" requires the cache to be rebuilt from ground truth at each turn (the arm's own turn
   t−1 output must be replaced). "evict ... keeping the arm's pins" and "history_columns" read as a cache that persists
   across turns with earlier pins retained — under which eviction firing depends on the arm's earlier pins, the primary
   population "turns where eviction fired" would be arm-dependent, and the identical-ids claim fails. Only the rebuild
   reading is consistent with the rest of v3. Fix F3.
C6 (A4 vs the cost cut). Preflight (4)'s reduced arm set drops tool_swap_echo; nothing states that A4 is then
   uninformative (not failed) or whether the free-running secondary survives the cut. Fix F22.
C7 (breaching arm). "A breaching arm fails its contrasts" — if clf_control breaches, is A1 failed (a negative result) or
   uninformative? sol's "every registered arm must be safety-intact" was a gate, not a sign. Fix F26.

Checked and consistent: teacher-forced primary + free-running secondary (never conflated, secondary never gated);
threshold-triggered flush named as such and consistent with the prefix/turn-index rules; A3 exclusions and manipulation
check are compatible with the Holm family (subject to F11/F12/F20); 30 GPU-h cap does not touch the cohort.

## 3. Outcomes that can still be read two ways

T1 Preflight (1) "overall final pass >= 15%": teacher-forced (all turns pass) or free-running final pass? (F17 text
   fixes both this and the base/full choice.)
T2 A3 with the manipulation check failing: v3 records "A3 uninformative", but the outcome rules only cover A3 pass/fail
   — "A1 & A3 pass" and "A1 or A3 failing" — so A3-uninformative + A1-pass is neither "supported" nor "unsupported"
   (F27).
T3 Holm over A1-A3 when A3 is ineligible: over three (with A3 counted as non-rejected) or over two? Different first-step
   alphas (0.0167 vs 0.025). (F11)
T4 "full − base > 0 on the primary": on the primary turns or on the primary minus the 40,960-position exclusions; point
   estimate or one-sided test. (F12)
T5 `full` at turns whose prompt exceeds 40,960 positions: not generated (turn NA), truncated, or generated past the
   position limit; and what any arm does when its within-turn cache passes 40,960 (a 5.5k prefix + 1k echo + a 31k tool
   dump is within ~3k of it). (F20)
T6 recency_pinned "echoed identically": the treatment's echo text, or its own spans' text under the same template/cap.
   (F6)
T7 Assertion "no candidate exceeds 192 encoder tokens" firing: harness abort (leg void), turn skipped, or candidate
   truncated. (F19)
T8 Sealed exposure too low (e.g. 3 of 16 long_context cases evict): under v3 the primary is run on 3 clusters and reported
   as a pass/fail; sol's INCONCLUSIVE floor is missing. (F10) Arithmetic for choosing the floor at the dev rate
   (4/8 → p = 0.5 per sealed long_context case, n = 16): P(fewer than 6 exposed) = 6885/65536 = 10.5%;
   P(fewer than 8) = 26333/65536 = 40.2%. sol's 8 would void the leg two runs in five at the dev rate; 6 is the largest
   floor with a ~10% void rate and leaves k = 6 clusters (continuity 100/6 = 16.7 pts per cluster mean — a per-turn,
   not per-case, mean, so still testable).
T9 Pin-overflow order for non-classifier arms: "newest-first" is a recency order that is meaningless for recency_pinned
   (it would drop exactly the columns that arm exists to keep) and undefined for exact-column controls. (F2)

## VERDICT: CONFIRMED-WITH-FIXES

v3 adopts the substance of both reviews: the teacher-forced/free-running split, the frozen flush with message-index
split and the prefix union, the 128-token chunking with whole-span fill, the echoing control, the recency comparator,
the tool-swap arm outside the family, the per-turn evicting-turn primary, the A3 manipulation check, the 4B path, the
30 GPU-h cap with a pre-registered arm cut, and the constants/hash freeze. What remains is (a) three omissions that
change what the sealed run can conclude — no sealed exposure floor (F10), no degenerate definition while the harness
folds truncation into it (F13/C2), no dev invariant preflight (F14) — and (b) a set of unresolved readings, of which
C1, C3, C5 and T2 are the ones that would let a single outcome be reported two ways. None requires a design change;
all are text. Apply the fixes below, then bind the amended text to the harness hash before the dev preflight.

## 5. Exact fix texts (insert/replace in the v3 section; "→" = replace the quoted v3 phrase)

F1  Outcome rules, first clause → "A1 & A3 pass with safety intact -> per-turn benefit under teacher-forced agentic
    evaluation supported post-development (the free-running final-pass difference is reported beside it and carries no
    claim)".
F2  Pin overflow → "If prefix + pins + the turn-t message (with its echo) exceed K, the treatment drops its lowest-P
    whole pins until it fits ('pin overflow', recorded with the dropped column count); clf_control, tool_swap_echo and
    recency_pinned are built AFTER this drop and pin exactly the treatment's final per-role column counts; they never
    re-evaluate overflow, and any difference between their turn-t message length and the treatment's is recorded as
    echo_token_delta (the cache may exceed K by that amount, recorded). If prefix + the turn-t message alone exceed K,
    all pins are dropped, the turn is recorded pin_overflow_total and proceeds (identical across arms); it stays in
    the primary."
F3  Eviction paragraph, add after "keeping the arm's pins": "At the start of every user turn t the KV cache is rebuilt
    from the ground-truth history (prefix + turns < t as rendered by the harness, without any echo or arm-generated
    token from earlier turns); pins and echoes never persist across turns. history_columns is therefore the full
    ground-truth history, the eviction decision, the evictable range and the candidate set are identical across arms,
    and 'eviction fired' is a property of the turn, not the arm."
F4  clf_control, after "recorded" → "recorded per turn as control_role_shortfall (this is a deliberate departure from
    sol LEG-A-3's fail-closed rule, taken because the prior-user pool is 24-308 columns on dev); A1 is additionally
    reported on the no-shortfall turns as a sensitivity."
F5  clf_control, "under the same template and cap" → "under the same template and cap, clamped to the treatment's
    echo token count by whole spans (the remaining delta, if any, is recorded as echo_token_delta and asserted <= 16
    tokens; larger deltas are a recorded method failure for that turn)". Apply the same sentence to recency_pinned and
    tool_swap_echo.
F6  recency_pinned, "echoed identically" → "receives the echo of its own spans' decoded text under the same template
    and cap, clamped as in clf_control".
F7  Selector, "(P desc, recency)" → "(P desc, recency, then stable source order within a message)".
F8  Selector, drop rule → "Any candidate whose text contains <|im_, <tool_call, </tool_call, <tool_response or
    </tool_response, or whose Qwen3 tokenization contains any special or added token id of the trunk tokenizer
    (tokenizer.all_special_ids plus added-token ids, e.g. <|endoftext|>, <think>, </think>), is dropped from pins and
    echo and counted (echo_dropped_control_tokens)."
F9  Safety clause, add: "calls repeated verbatim from history (normalized call identical to an earlier ground-truth or
    echoed call and absent from the turn's ground truth) <= full + 1;" and remove it from the reported-only list.
F10 Contrasts, add after "cluster = case": "If fewer than 6 sealed cases contribute an evicting turn, the leg is
    INCONCLUSIVE (no contrast is evaluated; exposure counts are reported). Under the dev rate the void probability is
    10.5%; a floor of 8 would be 40.2%."
F11 Contrasts, "one-sided cluster-robust" → "the LEG B continuity-corrected clustered lower bound: per-cluster mean of
    the per-turn difference, one-sided t on k-1 df, continuity 100/k subtracted; a contrast passes iff LB > 0. For A3 the
    per-turn difference is (clf_pinned_echo − base) − 0.5 x (full − base) computed turn by turn. Holm runs over the
    eligible contrasts only (three, or two when A3 is ineligible)."
F12 A3 condition → "evaluated only if the cluster-mean point estimate of full − base is > 0 on the A3 population (the
    primary turns minus the 40,960-position exclusions); its one-sided LB is reported. (This is a point-estimate gate,
    not sol's test-based gate, because a significant full − base at k <= 16 would make A3 ineligible by construction.)"
F13 Safety, define: "degenerate = the harness's 4-gram repetition test (scripts/bfcl_mt.py:_degenerate) evaluated ONLY
    on non-truncated generations; a truncated turn is counted under truncated and never under degenerate (the current
    `if truncated: return True` branch is removed before the preflight and covered by a unit test)."
F14 Preflights, add "(6) On every dev generation of every arm the harness asserts, and the preflight report shows 100%:
    the complete protected prefix survives eviction; no token of the turn-t user message or its steps is in cache at
    the eviction decision; columns_before − evicted + pinned = columns_after exactly; every candidate comes from a
    message with index < the turn-t user message; treatment, clf_control, recency_pinned and tool_swap_echo have equal
    per-role pinned-column counts and echo token counts within the F5 clamp; every shortfall/overflow/drop event is
    recorded. Any assertion failure stops the leg before the sealed run."
F15 Preflight (2) → "(2) BASE-vs-BASE bitwise determinism on the first dev id of each category: two fresh environments
    must produce identical generated token ids, normalized calls, tool outputs and checker traces at every turn."
F16 Safety, after "invalid <= full + 1": "(kept at +1 rather than sol's <= full because invalid is counted per turn on
    a ~24-40-turn primary where one event is 2.5-4 points, and the guard already admits one event when full has none)".
F17 Preflight (1) → "(1) competence of the FULL arm (identical to base on non-evicting turns) with the 1.7B trunk on the
    dev slice: teacher-forced per-case pass (all turns pass) >= 15% (5/32) AND per-turn pass on the 40 dev long_context
    turns >= 15% (6/40); if either fails, the 4B trunk ..." (rest unchanged).
F18 Preflight (5), add to the hash list: "selector artifact, trunk weights, trunk tokenizer, BFCL data manifest
    (cohorts.json sha256 22cf69af...), chat template, vendored checker".
F19 Selector, "the harness asserts no candidate exceeds 192 encoder tokens" → "candidates whose scoring input exceeds
    192 encoder tokens are truncated by the registered longest_first rule and counted (scorer_truncated_candidates,
    reported per turn); the harness never aborts on this. (Measured: 128 Qwen3 tokens of listing text re-tokenize to
    157-173 bge tokens, so the 192 window is met with ~11 tokens of margin, not by construction.)"
F20 Contrasts, after "excluded from A3 and counted": "at those turns the full arm does not generate (per-turn pass NA;
    excluded from full's final-pass reporting as position_overflow). Any arm whose within-turn cache exceeds 40,960
    positions at any step stops generating at that step; the turn is a truncated event for that arm and scores fail."
F21 Reported list, "(NO exclusion: ...)" → "(NO exclusion; this supersedes the 'echo-copy exclusion' at
    LEDGER-PLAN.md:423 for Leg A because copying a tool-returned identifier is the task)".
F22 Preflight (4), add: "The cut removes tool_swap_echo, clf_pinned and role_pinned and the free-running secondary; A4
    is then declared uninformative (not failed) before any sealed outcome. If the reduced set is still projected above
    30 GPU-h the leg stops (INCONCLUSIVE) before any sealed outcome."
F23 Model card → sol's paragraph verbatim (results/leg-a-review-sol.md, "Replace the eventual model-card sentence with
    this exact paragraph"), with fable's clause appended after its second sentence: "aggregate statistics over
    non-cohort BFCL cases motivated selecting over tool output and the tool-role label in the selector's training spec".
F24 Vacuity guard → "vacuity guard: for truncated, degenerate, invalid and repeated-call only, if full has 0 events of a
    type that type is judged '<= 1' and reported; timeouts remain 0 with no guard".
F25 Preflight (3), delete "(K may be re-registered lower before any outcome is viewed, recorded)". If a fallback is
    wanted it must be a single precommitted value written now (e.g. "K = 6144 is tried once; a second failure stops the
    leg"), noting that at the 5,494-column median prefix K = 6144 would trigger on nearly every category.
F26 Safety, "A breaching arm fails its contrasts" → "A breaching treatment arm (clf_pinned_echo) fails every contrast; a
    breaching control or comparator arm makes the contrasts that use it uninformative (recorded); in either case the
    leg cannot be reported as 'supported'."
F27 Outcome rules, add: "A3 uninformative (manipulation check failed) with A1 passing and safety intact -> supported on
    A1 only, labelled 'no measurable full-context headroom on this cohort'; A3 uninformative with A1 failing ->
    unsupported."
