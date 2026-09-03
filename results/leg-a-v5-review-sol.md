# Final confirmation: LEG A registration v5 — sol, 2026-09-03

Scope: only the last `WORKLOG.md` section, “LEG A registration v5”, checked against
`results/leg-a-v3-review-sol.md` and `results/leg-a-v3-review-fable.md`. This was a foreground, CPU-only text review. I
launched no GPU/model process, did not wait on or inspect `.review.lock`, did not terminate or signal any process, and
did not read the sealed IFEval input or sealed BFCL cohort contents. This file is the only repo output.

## Bottom line

V5 adopts most fixes, and the A3 point-estimate gate is internally consistent. It is not confirmable as written.
There are six non-equivalent adoptions, two additional reviewer conflicts not included among the four declared
decisions, and residual contradictions in three of the four declared decisions. Several can change whether an observed
result passes, is uninformative, or stops the leg.

## 1. Omissions or non-equivalent adoptions

1. **Sol fix 1 is re-opened by the reported-metrics clause.** Lines 2763-2772 correctly define teacher-forced case pass
   for every arm and free-running output for only `base` and `clf_pinned_echo`. Line 2831 then again says “final
   all-or-nothing pass per arm (teacher-forced and free-running)”. That is the second occurrence the sol replacement
   explicitly required removing. It can mean either two free-running arms or every arm.

2. **Fable F6 is still two-readable.** `clf_control` explicitly echoes its own spans, but `recency_pinned` only says
   “echo clamped as in clf_control” (lines 2810-2812). It never says whether the text is its own selected spans or the
   treatment's text. F6 required the former explicitly.

3. **Sol's exact-test tie rule is incomplete.** Lines 2823-2826 retain zeros but omit “ties”. With an exact discrete
   test, inclusive-tail versus mid-p handling can change a Holm decision at this k.

4. **Fable F11's decision rule is not adopted.** F11 says a contrast passes iff the continuity-corrected clustered
   lower bound is positive. V5 instead makes the exact sign-flip p-value inferential and the lower bound descriptive
   (lines 2752-2753 and 2823-2827). This is an explicit, readable choice, but it is not verbatim or equivalent adoption
   of F11.

5. **Sol's safety replacement is not adopted, and Fable F16's rationale is incompatible with v5's unit.** Sol required
   `invalid <= full`, `unexpected_duplicate_call <= full`, and literal zero-baseline inequalities except for the
   truncation `+1`. Lines 2835-2842 instead use Fable F16/F24's `+1` and zero-baseline guard. These rules can produce
   different safety outcomes. Moreover, F16 justified the allowance because invalidity was counted per turn; v5 counts
   by case but retains the “2.5-4 points on a ~24-40-turn primary” rationale. That rationale is false for a case-level
   count. This safety disagreement is not one of the four declared decisions.

6. **Fable F23's required model-card paragraph is not present verbatim or equivalently.** Lines 2754-2762 omit the
   registered 20,054-row count, BFCL dev labels, dev-split trunk selection, the “not pure-KV” qualification,
   inference-time no-fitting statement, and the limitation on the separate no-contact zero-shot claim. Calling the
   shorter text “sol's paragraph verbatim” does not cure those omissions.

The remaining F1-F5, F7-F10, F12-F15, F17-F22, and F24-F27 changes are present in substance, subject to the
contradictions below. Sol's remaining v3 fixes are also present in substance, except for the expressly decided
departures and items 1, 3, and 5 above.

## 2. The four declared decisions

### Control shortfall — internally contradictory and outcome-unreadable

The decision permits an other-role fill and keeps those turns in A1, with a no-shortfall sensitivity (lines 2744-2747
and 2803-2809). The same arm nevertheless claims exact per-role pinned-column equality, and preflight (6) requires that
equality in 100% of invocations and stops the leg on any failure (lines 2804-2806 and 2861-2866). An actual role
shortfall therefore both proceeds under the decision and stops the leg under the invariant. A1 is unreadable when a
shortfall occurs. This does not re-litigate the chosen fallback; the invariant must be carved around that choice.

There is also no terminal rule if neither role contains a disjoint width/age match. “No repetition or rotation” rules
out the obvious fallback, but A1 is not declared uninformative.

### A3 point-estimate gate — consistent

The top decision, A3 definition, 40,960-position population, lower-bound reporting, Holm family when A3 is ineligible,
and A3-uninformative outcome branch agree. I do not re-litigate this decision.

### Exposed-cluster floor 6 — rule is clear, but the unanimity claim contradicts it

The floor itself is consistently six. The statement that every Holm-corrected pass with `6 <= k < 8` “requires
unanimity” is false for the registered magnitude-sensitive sign-flip test. At `k=7`, case means
`[1,1,1,1,1,1,-epsilon]` have an inclusive exact upper-tail p-value of `2/128 = 0.015625`, which can pass the first
three-test Holm threshold `0.05/3`, despite one negative case. A reader could apply the exact test or impose the stated
unanimity condition. The latter must be removed; this is not an objection to the floor of six.

### Pin overflow — internally incomplete and outcome-unreadable

The chosen fable path is stated, but the body does not say that dropping a pin simultaneously drops its echo entry.
Without linked removal, dropping a pin need not shrink the echo-bearing turn message, and total overflow need not leave
the non-full arms identical. Equal-P pins also have no frozen drop order, despite the registered recency/source
tiebreaks. Finally, a comparator may be up to 16 echo tokens longer than treatment, but v5 omits F2's disposition that
it may exceed K by the recorded delta without re-running overflow. These omissions conflict with “comparators built
after”, “never re-evaluate overflow”, and “proceeds identically across arms”.

The earlier statement that a within-turn cache exceedance is “identical across arms” (line 2781) is independently
false: `full`, `base`, treatment, and comparators have different post-intervention cache lengths, and v5 explicitly
records `echo_token_delta`. The policy can be identical; the exceedance need not be.

## 3. Other remaining two-way readings

- **Preflight metric:** “full final pass” and “base overall final pass” can mean teacher-forced case all-or-nothing or
  free-running final pass. The latter would also contradict “FREE-RUNNING ... reported, never gated”. The duplicated
  full overall floor does not resolve the unit.
- **Comparator method failure:** an `abs(echo_token_delta) > 16` event is called a method failure “for that turn”, but
  v5 does not say whether the turn is excluded, its contrast becomes uninformative, or the leg stops.
- **A3 cluster count after position exclusions:** the global floor is evaluated before the A3 exclusions. V5 does not
  say what happens if the primary has at least six clusters but the A3 population has fewer than six.

## 4. Exact text fixes

The following replacements preserve the four declared choices rather than revisiting them.

Replace the reported-metrics lead-in at lines 2831-2834 with:

> Reported, not gated: teacher-forced case all-or-nothing pass for every arm; free-running final pass and
> first-divergence turn only for `base` and `clf_pinned_echo`; non-evicting turns (echo-only stratum); `role_pinned` and
> `recency_pinned - role_pinned`; tool-call validity; echo-copy rate (NO exclusion; this supersedes the echo-copy
> exclusion at LEDGER-PLAN.md:423 for Leg A because copying a tool-returned identifier is the task); columns and echo
> tokens per arm and turn; overflow, shortfall, delta and drop events.

Replace the `clf_control` and `recency_pinned` resource text with:

> `clf_control` uses frozen seed 20260903 and disjoint nonselected candidates matched one-to-one on token width and
> source-turn age, without repetition or rotation. On no-shortfall turns it also matches the treatment's role
> one-to-one and exact per-role pinned columns. A same-role shortfall may be filled from the other role; such turns match
> exact total pinned columns, record `control_role_shortfall` and per-role column deltas, remain in the prespecified A1,
> and are excluded only from the separately reported no-shortfall sensitivity. If no disjoint width/age match exists in
> either role, A1 is uninformative. `clf_control` receives the echo of its own spans' decoded text under the common
> framing and clamp.
> `recency_pinned` selects the most recent candidates from the same user/tool universe under the treatment's exact
> per-role pinned-column quota and echo budget, without reading classifier scores; it receives the echo of its own
> spans' decoded text under the same template and cap, clamped as in `clf_control`; an impossible exact match makes A2
> uninformative.

Replace the corresponding preflight-(6) equality sentence with:

> Treatment, `recency_pinned`, and `tool_swap_echo` have equal per-role pinned columns and echo tokens within the clamp.
> On no-shortfall turns `clf_control` meets the same per-role equality; on `control_role_shortfall` turns it matches
> exact total pinned columns and the harness asserts and reports the per-role deltas permitted above.

Replace the pin-overflow paragraph and the final sentence before it with:

> The cache persists across the steps of a turn (assistant/tool tokens appended; no re-render and no second eviction).
> Each arm's within-turn cache may exceed K; per-arm columns and exceedance are recorded.
> If prefix plus pins plus the echo-bearing turn-t message exceed K, treatment drops whole pins in reverse registered
> `(P, recency, stable-source)` rank, dropping each pin's corresponding echo entry at the same time, until it fits.
> Record `pin_overflow` and dropped columns. Build `clf_control`, `tool_swap_echo`, and `recency_pinned` only after that
> drop; they pin treatment's final registered quantities and never re-evaluate overflow. A comparator may exceed K by
> its recorded `echo_token_delta`. If prefix plus the original no-echo turn-t message alone exceeds K, drop every pin
> and corresponding echo entry, record `pin_overflow_total`, and let all non-full arms proceed with zero pins and echo;
> the turn stays primary. Never drop current-turn or protected-prefix IDs.

Replace the exact-test sentence and append the A3-specific floor sentence with:

> For each contrast, compute within each case the mean binary turn difference over that contrast's registered primary
> turns. Use the exact one-sided paired sign-flip p-value over the k case means, enumerating all `2^k` sign assignments,
> retaining zero-valued case means, and counting test-statistic ties in the upper tail (no mid-p). Apply Holm step-down
> alpha 0.05 over eligible A1-A3; A4 is a separate alpha-0.05 family. The p-value grid and k are reported; no separate
> unanimity condition is imposed. If the primary population has k<6, the leg is INCONCLUSIVE. For A3, recompute k after
> the 40,960-position exclusions; if that A3 population has k<6, A3 is uninformative while the other contrasts proceed.

Replace the comparator-delta disposition with:

> `abs(echo_token_delta) <= 16` tokens is required. On dev, a larger delta stops preflight. If first encountered in the
> sealed run, a larger delta makes that comparator's contrast uninformative; no affected turn is selectively excluded.

Replace preflight (1) with metric-explicit text:

> (1) With the 1.7B trunk, `full` teacher-forced case all-or-nothing pass must be at least 5/32 overall and 2/8 on dev
> `long_context`, and its teacher-forced per-turn pass on the 40 dev `long_context` turns must be at least 6/40. `base`
> teacher-forced case all-or-nothing pass must be at least 5/32 overall, and its teacher-forced per-turn pass on those 40
> turns must be at least 6/40. No free-running metric gates preflight. If any floor fails, use the 4B trunk for the whole
> leg and re-check every floor once; if any 4B floor fails, stop and label the leg INCONCLUSIVE. Preflight and sealed run
> use the same trunk.

Replace the model-card text with F23's required text (including its appended clause):

> The selector was fit on 20,054 hand-written, item-disjoint rows; no BFCL item or item-level paraphrase was used. BFCL
> was not untouched: its dev labels, schemas/template/checkers, and aggregate non-cohort analyses preceded the final
> selector and influenced tool-fact labels, protected roles, candidate roles, and harness choices; its dev split also
> selected the 1.7B/4B trunk by a frozen rule. Aggregate statistics over non-cohort BFCL cases motivated selecting over
> tool output and the tool-role label in the selector's training spec. The 64-case cohort was hashed in advance and its
> sealed item contents were not opened or executed before the final freeze. LEG A is a post-development, end-to-end
> comparison of KV retention plus source-labelled text reinjection, not a pure-KV or zero-shot result. Inference-time
> scoring of BFCL user/tool text applies the frozen selector and performs no fitting. “Repo-level no-contact zero-shot”
> is reserved for the separately frozen family, and does not assert absence from trunk pretraining.

Two further decisions are unavoidable because the requested review fixes directly conflict. No wording can adopt both
members of either pair as the operative gate. If v5's current choices are intended, add exactly:

> (v) Inferential pass rule — sol's exact paired sign-flip/Holm rule is adopted as the operative decision rule; fable
> F11's `LB > 0` pass rule is not adopted, and the continuity-corrected clustered LB is descriptive only.
> (vi) Safety tolerance — fable F16/F24's one-case allowances are adopted over sol's stricter zero-baseline safety
> inequalities. Safety is counted by case, so the allowance is a prespecified one-case tolerance; the per-turn
> “2.5-4 points” rationale does not apply and is deleted.

If those two departures are not intended, the authors must instead select the opposite rule or register a conjunction
before preflight. They cannot continue to claim that every sol fix and every F1-F27 fix was adopted.

## VERDICT

**REFUTED.** The A3 decision is coherent, but v5 does not adopt every specified fix, silently contains two additional
reviewer disagreements, and leaves control-shortfall and pin-overflow cases with contradictory dispositions. The exact
edits above make the four declared choices readable; the inferential and safety conflicts still require explicit
decisions before this can be confirmed.
