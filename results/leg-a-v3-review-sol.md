# Confirmation review: LEG A registration v3 — sol, 2026-09-03

Scope: only the last `WORKLOG.md` section, “LEG A registration v3”, checked against
`results/leg-a-review-sol.md` findings LEG-A-1 through LEG-A-6 and the exact text changes in
`results/leg-a-review-fable.md`. This was a foreground, CPU-only text review. I launched no model/GPU process, did not
signal or terminate any process, did not inspect `.review.lock`, and did not read the sealed IFEval input or any sealed
BFCL cohort contents.

## Bottom line

V3 adopts the intended high-level experiment: teacher-forced per-turn mechanism testing is primary; free-running base
and `clf_pinned_echo` trajectories are secondary; eviction is explicitly a threshold-triggered history flush; A4 is a
separate, unadjusted tool-source test outside the A1-A3 Holm family; the 40,960-position A3 exclusion is recorded; and the
preflight has the fable floors, the one-step 4B fallback, and the 30 GPU-h cap without cohort reduction.

It does **not** adopt every required change from the two reviews. Several omissions are outcome-changing rather than
editorial. Most importantly, its control arms do not freeze the exact resources sol required, the inferential method is
still unnamed, the safety “vacuity guard” contradicts the preceding safety limits, the K escape tunes on BFCL preflight
evidence, and the cost-cut path removes the arm needed for A4 without disposing of A4. Outcomes can still be read in
more than one way until the fixes below are incorporated.

## Adoption check

Adopted adequately:

- The teacher-forced primary/free-running secondary distinction, scoring of each teacher-forced turn, two-arm
  free-running scope, and first-divergence record.
- One eviction decision at step 0, before the current semantic user turn is prefilled; message-index boundary; persistent
  within-turn cache; complete protected system turn; moving `missing_functions` boundary; same two-stage schedule for
  `full`; and the intervention named as a threshold-triggered flush rather than native capacity eviction.
- Fable's 128-token tool chunking, `longest_first`, 192-token assertion, whole-span budget fill, B-as-cap, literal
  control-token filter, neutral role-labelled echo, and E=1,024 cap.
- A1's control echo in principle, the recency comparator, reported user-only role arm, A3's positive-gap condition, and
  explicit counting/exclusion of full prompts above 40,960 positions.
- A4 is explicitly `clf_pinned_echo - tool_swap_echo > 0` at alpha 0.05 outside the A1-A3 Holm family and is the only
  tool-source claim.
- Fable's base floors (overall final pass and dev-long-context per-turn pass, both at 15%), one-step 1.7B-to-4B fallback,
  same-trunk rule, named determinism IDs, feasibility counts, 30 GPU-h cap, five-arm cost cut, cohort preservation, and
  constant/harness freeze.
- The required post-BFCL classifier-data restriction, development-benchmark disclosure, and pre-contact no-contact
  shortlist.

Omitted, diluted, or contradictory:

1. **LEG-A-1: “identical context ids” remains false as written.** Teacher forcing makes the rendered source history
   identical before intervention. Actual arm inputs cannot be identical after deletion, pinning, and echo. The later
   phrase “final all-or-nothing pass per arm (teacher-forced and free-running)” also conflicts with the earlier rule that
   only two arms free-run, and “teacher-forced final pass” does not say how independent turn branches become a case pass.

2. **LEG-A-2: pin overflow is not the required rule and has no terminal case.** Sol required dropping lowest-ranked pins;
   v3 says newest-first. It does not say that the corresponding echo entry is dropped, so dropping a pin need not reduce
   the echo-bearing suffix. It also gives no result when protected prefix plus the original, no-echo current-turn suffix
   cannot fit K. Thus “until it fits” can fail to terminate scientifically even if the code terminates.

3. **LEG-A-3: A1/A2/A4 are not resource-identified.** `clf_control` matches aggregate columns, but does not freeze
   one-to-one role, width, source-turn age, exact echo-token count, or a fail-closed exact-match rule. Its other-role
   shortfall fallback directly dilutes “same role pool.” `recency_pinned` does not require the treatment's per-role quota
   or exact echo-token count. `tool_swap_echo` inherits unspecified “control rules”; because those rules permit an
   other-role fallback, A4 can change more than tool source. “Pinned and echoed identically” does not resolve which
   quantities are exact.

4. **LEG-A-4: two sol requirements are absent.** Tool text is not split newline-first and then with the registered
   sentence splitter; a nonempty line goes directly to 128-token chunks. Probability/recency ties lack stable source
   order. Echo remains raw “verbatim” text rather than source-labelled JSON-quoted data. The substring filter is useful
   but is not equivalent to a quoted renderer plus a zero chat-control-event invariant. Unexpected normalized replay is
   only reported, not safety-gated.

5. **LEG-A-5: the test and manipulation check remain two-readable.** “One-sided cluster-robust” names neither the
   p-value method nor zero/tie handling at small k. “`full - base > 0`” can mean a merely positive observed mean or the
   registered one-sided manipulation test. No minimum number of pressure-exposed sealed cases is registered. The
   40,960-position exclusion itself is clear, but v3 does not expressly apply the same exclusion set to the A3
   manipulation check.

6. **LEG-A-6: the safety merge is internally contradictory and weaker than required.** Sol required case-level counts,
   `invalid <= full`, nontruncation-degeneracy, unexpected-duplicate-call safety, zero chat-control events, and every arm
   safety-intact. V3 instead counts invalidity per turn and retains `invalid <= full + 1`. Worse, its “vacuity guard” says
   that *any* type with zero full events is judged `<=1`; literally that overrides `timeouts 0`, `degenerate <= full`, and
   even types that were meant to require zero. This is not a vacuity guard—it creates an extra event allowance at the
   zero baseline. “A breaching arm fails its contrasts” also leaves unclear whether safety is global or only local to a
   contrast.

7. **LEG-A-6 preflight requirements are incomplete.** V3 adopts fable's base floors but omits sol's `full` competence
   floors (`>=5/32` overall and `>=2/8` long-context). “Bitwise determinism” does not enumerate generated IDs, normalized
   calls, tool outputs, and checker traces in fresh environments. The 100% layout/cache/control invariants, coverage
   fields, and complete registration/harness/selector/trunk/tokenizer/manifest/template/checker hash set are absent.
   Finally, “K may be re-registered lower” after learning the BFCL dev feasibility result contradicts both “otherwise
   ... not launched” and “constants ... not changed after [preflight]”; it is precisely the no-refit escape sol forbade.

8. **The fable zero-tool rule was moved, not adopted.** Fable required A2 to be declared uninformative before sealed
   execution if dev long-context evicting turns select zero tool candidates. V3 applies that trigger only to A4. That is
   not verbatim or equivalent.

9. **The 30 GPU-h merge strands A4.** The prescribed over-cap arm set omits `tool_swap_echo`, but A4 remains registered
   below with no cost-cut disposition. A reader can treat A4 as waived, failed, still required, or uninformative.

10. **The A2 outcome overclaims non-rejection.** Failure to reject `clf_pinned_echo > recency_pinned` does not establish
    that recency “suffices”; it supports only “no learned-ranking advantage detected,” followed by a predeclared
    simplicity choice. Likewise, a failed competence/feasibility preflight should have the single registered label
    `INCONCLUSIVE`, not the undefined label “void.”

## Exact text fixes

Replace the two occurrences of the identical-context claim and clarify the reported case metric with:

> Before intervention at turn t, every teacher-forced arm receives byte-identical rendered source-history IDs. Arm input
> IDs are not claimed identical after arm-specific eviction, pinning, control selection, or echo insertion. Arms are
> paired by case and turn. Teacher-forced case all-or-nothing pass is 1 iff every independently branched scored turn in
> that case passes. Report teacher-forced case pass for every arm; report free-running final pass and first divergence
> only for `base` and `clf_pinned_echo`.

Replace the pin-overflow sentence with:

> For every non-full arm, if protected prefix plus the original no-echo turn-t suffix cannot fit K, mark that case-arm
> infeasible and fail safety. Otherwise, if protected prefix plus pins plus the projected echo-bearing turn-t suffix
> exceeds K, drop pins from lowest to highest registered rank (reverse probability/recency/stable-source order), dropping
> each pin's corresponding echo entry at the same time, until it fits. Re-clamp treatment and comparator resources to the
> exact matched quantities below. Record this as `pin_overflow`; never drop current-turn or protected-prefix IDs.

Replace the candidate-order and echo-rendering clauses with:

> Prior TOOL output is split newline-first; empty pieces are dropped; every nonempty piece is then split with the
> registered sentence splitter and each resulting piece longer than T=128 Qwen3 tokens is chunked consecutively at token
> boundaries. Rank kept candidates by probability, recency, then stable source order. Echo entries are source-labelled
> JSON-quoted strings under the header `Earlier context restated verbatim:` with `user:` / `tool:` prefixes; treatment and
> controls use byte-identical framing. The registered literal control-token filter remains fail-closed, and any emitted
> chat-control echo event is a safety failure.

Replace the three inferential comparator arm clauses with:

> `clf_control` uses frozen seed 20260903 to choose disjoint nonselected candidates one-to-one matched to selected
> candidates on role, token width, and source-turn age; after all clamps it matches exact per-role pinned columns and
> exact added echo tokens, without repetition or rotation. A same-role pool shortfall is filled from the other role only
> for a recorded descriptive fallback arm; any such fallback makes A1 uninformative and cannot enter A1.
> `recency_pinned` selects the most recent candidates from the same user/tool universe under the treatment's exact
> per-role pinned-column quota and exact added-echo-token budget, without reading classifier scores; an impossible exact
> match makes A2 uninformative.
> `tool_swap_echo` keeps every selected USER span fixed and replaces each selected TOOL chunk only with a disjoint TOOL
> chunk matched on token width and source-turn age, with exact total pinned columns and echo tokens. The other-role
> fallback never applies to this arm; an impossible match makes A4 uninformative.

Replace the statistics sentence with:

> For each contrast, compute within each case the mean binary turn difference over that case's primary evicting turns.
> Let k be the number of sealed cases with at least one such turn. Use the exact one-sided paired sign-flip p-value over
> the k case means (enumerate all 2^k sign assignments; retain zeros/ties), with Holm step-down alpha 0.05 over A1-A3.
> A4 uses the same exact test at alpha 0.05 as a separately declared family and is not included in the A1-A3 Holm
> correction. If k<8, the leg is INCONCLUSIVE and all contrasts are reported descriptively only. A3 and its prerequisite
> use the identical subset after excluding and counting turns whose full prompt exceeds 40,960 positions. A3 is eligible
> only if the exact one-sided paired sign-flip manipulation test `full-base>0` passes at alpha 0.05; a merely positive
> observed mean is insufficient.

Replace the entire Safety paragraph with:

> Safety is counted by case on the primary set: a case is counted once for a type if any generation sub-step has that
> event. `invalid` means a `<tool_call>` block failing `parse_tool_calls` or `call_to_python`;
> `nontruncation-degenerate` excludes truncation; `unexpected_duplicate_call` means an unexpected normalized call replayed
> from prior history/echo. Required for every registered arm versus full: timeouts=0; truncated<=full+1;
> nontruncation-degenerate<=full; invalid<=full; unexpected_duplicate_call<=full; chat-control echo events=0. There is no
> blanket `<=1` rule when full is zero: at a zero full baseline the applicable displayed inequality is evaluated
> literally (only truncation retains its explicit +1 allowance). Every arm entering a reported support claim must be
> safety-intact; otherwise that claim fails. This integer case-level clause replaces the rate-based ROUND 7 fields in
> `src/stencil/bfcl.py:summarize_records`.

Replace Preflight items (1)-(5) with:

> (1) With the 1.7B trunk, `full` final pass must be >=5/32 overall and >=2/8 on dev long-context cases, and `base` must
> have overall final pass >=15% and per-turn pass on the 40 dev long-context turns >=15%. If any floor fails, use the 4B
> trunk for the whole leg and re-check every floor once; if any 4B floor fails, stop and label the leg INCONCLUSIVE. The
> preflight and sealed run use the same trunk.
> (2) On the first dev ID of each category, two fresh-environment BASE runs must be bitwise identical in complete
> generated-ID, normalized-call, tool-output, and checker traces.
> (3) In 100% of dev invocations, assert the complete system/tool prefix survives, no current-semantic-turn ID is present
> at eviction, physical cache accounting is exact, candidates come only from prior semantic turns, and every inferential
> comparator meets its registered pin/role/echo equalities without an inferential fallback. Report selected and eligible
> spans by source role, nominal and actual B, capacity rejections, fallback counts, and exposed/no-pressure cases. At
> least 4/8 dev long-context cases must be pressure-exposed and at least four exposed case-turns must select a tool chunk;
> otherwise stop without changing K or refitting and label the leg INCONCLUSIVE. A BFCL-driven K change requires a new
> registration and cannot rescue this leg.
> (4) Project the selected trunk and all arms over the registered 64-case mix. The cap is 30 GPU-h. If exceeded, before
> any sealed result is viewed run only `base | clf_pinned_echo | clf_control | recency_pinned | full`; never cut the
> cohort, and declare A4 uninformative because `tool_swap_echo` was not run.
> (5) Before preflight, record and freeze K, B, T, E, threshold, header, seed, registration hash, harness hash, selector
> hash, trunk revision/hash, tokenizer revision/hash, BFCL manifest hash, template hash, and checker hash. Any later
> change re-registers the leg; no preflight evidence may tune these choices.

Append to Outcome rules:

> If the selector keeps zero tool candidates on dev long-context evicting turns, declare both A2 and A4 uninformative
> before sealed execution; A1/A3 may then test only a user-span mechanism. Non-rejection of A2 means “no learned-ranking
> advantage detected”; recency is preferred only by the registered simplicity rule, not by an equivalence claim.
> Competence, invariant, feasibility, or sealed-cluster-floor failure is INCONCLUSIVE and launches no sealed inference.

## VERDICT

**REFUTED.** V3 incorporates the intended teacher-forced/free-running split, named flush, A4 family placement, A3
position exclusion, and 30 GPU-h policy, but it does not yet adopt all required LEG-A-1..6 and fable changes equivalently.
The unresolved control, inference, safety, preflight, and cost-cut contradictions can change which outcomes count as
support, failure, or uninformative.
