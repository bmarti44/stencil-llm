# Final confirmation: LEG A registration v5 — fable, 2026-09-03

Scope: WORKLOG.md last section ("LEG A registration v5", line 2741 to EOF) checked against every fix in
results/leg-a-v3-review-sol.md (ten numbered findings + its exact-text blocks) and results/leg-a-v3-review-fable.md
(F1-F27). Read for evidence only: results/leg-a-review-sol.md:330-339 (the model-card paragraph v5 claims to quote),
src/stencil/ledger.py:340-359 (what text_ledger_context echoes). CPU-only text review; no process launched or
signalled; sealed IFEval input and sealed BFCL cohort contents not read; .review.lock not waited on. This file is my
only output. Arithmetic below was recomputed by hand (binomial tails, sign-flip minima, Holm steps).

## 1. Adoption audit

### sol v3 fixes (ten findings; exact-text blocks)

| sol | v5 status |
|---|---|
| 1 identical-ids claim; case pass definition; free-running scope | ADOPTED verbatim ("byte-identical rendered source-history ids ... not claimed identical after ..."; all-or-nothing = every branched turn passes; free-running for base and clf_pinned_echo only). Residual: the reported list still says "final all-or-nothing pass per arm (teacher-forced and free-running)", the phrase sol flagged (R8). |
| 2 pin overflow: lowest-rank drop, drop the echo entry with the pin, terminal case | DECIDED (iv) for fable F2: lowest-P drop, comparators built after, pin_overflow_total stays in the primary. The "drop each pin's corresponding echo entry at the same time" clause is in neither the decision nor the text; whether the echo is drawn from the pins or from all kept candidates is unstated (R5). |
| 3 resource-identified comparators; fail-closed | ADOPTED for recency_pinned and tool_swap_echo (impossible exact match -> uninformative; no other-role fallback); DECIDED (i) for clf_control (other-role fill + control_role_shortfall + no-shortfall sensitivity). Residual contradiction between the fill and the "exact per-role" equalities (R3); "exact" columns at whole-span granularity is undefined (R6). |
| 4 newline -> splitter -> 128-token chunks; P/recency/stable order; JSON-quoted labelled echo; fail-closed filter; replay gated | ADOPTED verbatim (all five). |
| 5 exact paired sign-flip, zeros retained, Holm over A1-A3, A4 separate; k floor; A3 and its check on the identical exclusion set; test-based A3 gate | ADOPTED (test, zeros, Holm/A4 placement, identical A3 population). DECIDED (iii) floor 6 not 8; DECIDED (ii) point-estimate gate not test-based. Residual: the "unanimity" disclosure attached to (iii) is arithmetically wrong at k = 7 and incomplete at k = 6 (R4); the floor is not applied to A3's own k after the 40,960 exclusions (R7). |
| 6 case-level safety; invalid <= full; duplicate-call <= full; no blanket <= 1 at a zero baseline; every arm safety-intact | PARTLY ADOPTED: case-level counting, nontruncation-degenerate, chat-control = 0, timeouts = 0 without guard, F26 breach rule ("cannot be reported as supported" = sol's "claim fails"). NOT ADOPTED and NOT among the four recorded decisions: invalid <= full + 1, repeated-call <= full + 1, and the <= 1 vacuity guard are fable's v3 positions kept over sol's explicit contrary fix, with a rationale ("2.5-4 points on a ~24-40-turn primary") that describes per-TURN counting and is stale under the adopted per-CASE unit (R2). |
| 7 full competence floors; determinism traces; 100% dev invariants; full hash list; no K escape | ADOPTED (both full floors 5/32 and 2/8 present beside fable's; (2) enumerates ids/calls/outputs/checker traces; (6) added; (5) hash list complete; K change forbidden). Residual: "full final pass" and "base overall final pass" in (1) do not say teacher-forced vs free-running (fable T1, half-fixed by F17) (R8). |
| 8 zero-tool rule covers A2 and A4 | ADOPTED verbatim. |
| 9 cost cut disposes of A4 (uninformative, not failed) | ADOPTED verbatim; free-running secondary and clf_pinned/role_pinned named in the cut; second-failure stop present. |
| 10 A2 non-rejection wording; INCONCLUSIVE label, no "void" | ADOPTED ("void" survives only as "void probability" in the decision preamble, descriptive). |

sol's model-card requirement (results/leg-a-review-sol.md:330-339, also fable F23): NOT ADOPTED. v5 says "sol's
paragraph verbatim ... with fable's clause" but the text that follows is a different, shorter paraphrase. Missing from
it: "20,054 hand-written, item-disjoint rows"; "its dev split also selected the 1.7B/4B trunk by a frozen rule"; "not
a pure-KV ... result" (v5 keeps only "not zero-shot transfer"); "Inference-time scoring of BFCL user/tool text applies
the frozen selector and performs no fitting"; and "'Repo-level no-contact zero-shot' is reserved for the separately
frozen family, and does not assert absence from trunk pretraining." A registration that claims a verbatim quote must
carry it (R1).

### fable F1-F27

F1, F3, F5, F6, F7, F8, F9, F10, F11 (as merged into sol's test: LB reported beside it, per-turn A3 difference
defined, Holm over eligible only), F12, F13, F14, F15, F16, F17, F18, F19, F20, F21, F22, F24, F25, F26, F27: ADOPTED
verbatim or equivalently. F2 and F4: adopted by decisions (iv) and (i). F23: NOT ADOPTED (R1 above). F16's rationale
sentence is adopted but now mismatches the counting unit (R2).

## 2. The four decisions — internal consistency

(i) Control shortfall. Consistent with the clf_control clause, the recording fields and the outcome rules. INCONSISTENT
with two clauses that survived from the no-fallback world: the same clf_control sentence says "after all clamps matches
exact per-role pinned columns" and then, in the same sentence, "same-role shortfall filled from the other role"; and
preflight (6) asserts on every dev generation that "treatment, clf_control, recency_pinned and tool_swap_echo have
equal per-role pinned columns" with "any assertion failure stops the leg before the sealed run". On a shortfall turn
the control's per-role split necessarily differs from the treatment's, and shortfall turns are expected on dev (the
24-308-column user pool is the reason for the decision), so as written (6) stops the leg on the first turn where (i)
is exercised. Readable only after R3.

(ii) A3 gate. Consistent: the point-estimate gate, "LB reported", the Holm family size "three, or two when A3 is
ineligible", and the F27 outcome rows all agree. No residual.

(iii) Floor 6. Consistent with the INCONCLUSIVE rule and the outcome rules. The attached disclosure "with 6 <= k < 8 a
Holm-corrected pass requires unanimity" is a claim and it is wrong as stated. Recomputed for the exact one-sided
sign-flip with zeros retained (p = #{patterns with sum >= S} / 2^(k - z), z = zero case means): at k = 6, z = 0 the
minimum p is 1/64 = 0.0156, which passes Holm step 1 (0.05/3 = 0.0167) and step 2 (0.025) only with all six case
means strictly positive, but step 3 (0.05) and the separate A4 family (0.05) admit p = 2/64 or 3/64, i.e. one
negative case mean of small magnitude; one zero case mean at k = 6 raises the minimum to 1/32 = 0.031, so steps 1-2
become unpassable; at k = 7 the minimum is 1/128 and a pattern with one small negative mean gives 2/128 = 0.0156,
which passes step 1, so unanimity is NOT required at k = 7. With A3 ineligible (two contrasts) step 1 is 0.025 and
the k = 6 conclusion is the same. The decision stands (this does not make an outcome unreadable); the sentence must
be corrected (R4). Binomial tails in the preamble verified: P(X < 6 | 16, 0.5) = 6885/65536 = 10.5%; P(X < 8) =
26333/65536 = 40.2%.

(iv) Pin overflow. Consistent with the eviction paragraph, the recording fields, the comparator construction and the
primary definition. One dependency is left implicit: "total overflow ... proceeds identically across arms" is true
only if the echo is composed of the (post-drop) pinned spans, so that zero pins means zero echo for every arm. v5
defines Echo as entries "most probable first, capped at E" without saying whether the entries are the pins or all
kept candidates (E and B are independent caps, so the two readings differ whenever B < E or on overflow).
src/stencil/ledger.py:351-352 echoes "the same entries" as the pins, which is the reading that makes (iv) and sol's
"drop the echo entry with the pin" both hold. Must be written down (R5).

## 3. Remaining two-way readings

R3, R4, R5 as above, plus:

R6 "exact per-role pinned columns" for clf_control, "exact per-role pinned-column quota" for recency_pinned, and
   "exact total pinned columns" for tool_swap_echo are required at whole-span granularity (whole-span fill; "never
   partially pin while echoing a whole chunk" in sol's v1). Spans have arbitrary widths, so an exact column sum from
   whole disjoint spans is a coincidence, and "an impossible exact match makes A2/A4 uninformative" would then fire on
   almost every turn — A2 and A4 unreadable by construction. Two readings: the "clamp" truncates the last comparator
   span at a token boundary to hit the exact count (then "impossible" means only a pool too small), or the clamp is
   whole-span with a tolerance (then "exact" is false in four places and (6) needs a tolerance). Also unstated:
   whether an impossible match voids the whole contrast or only drops that turn.
R7 Each contrast has its own k (A3's population excludes 40,960-position turns), but the floor 6 is stated once on
   "sealed cases contribute an evicting turn". If A3's k falls below 6 after exclusions nothing says whether A3 runs.
R8 Preflight (1): "full final pass >= 5/32 overall" and "base overall final pass >= 15%" — teacher-forced all-or-
   nothing or free-running? (The first duplicates the teacher-forced 5/32 floor if teacher-forced; base free-runs in
   the secondary, so the free-running reading is available.) Reported list: "final all-or-nothing pass per arm
   (teacher-forced and free-running)" vs "free-running ... base and clf_pinned_echo only".
R2 (see table, sol 6): the invalid/repeated-call +1 and the vacuity guard are a fifth sol-vs-fable disagreement that
   v5 resolved silently for fable and justified with a per-turn rationale under a per-case rule. Also, the guard is
   vacuous for truncated, invalid and repeated-call (each already carries +1, so full = 0 already yields <= 1); it
   changes only degenerate. Either reading of "the guard" is a rule change relative to sol; it must be recorded.

## VERDICT: CONFIRMED-WITH-FIXES

v5 adopts every sol v3 fix and every fable F# except the model-card paragraph (R1) and the safety +1/guard trio (R2,
unrecorded rather than omitted), and the four recorded decisions are consistent with the rest of the text except for
the per-role equality clauses under decision (i) (R3), which as written stop the leg on dev the first time the
decision is exercised. R1-R8 are text; none requires a design change. Apply them, then bind the amended text to the
harness hash before the dev preflight.

## Exact fix texts ("->" = replace the quoted v5 phrase)

R1 Model card. Replace everything after "Model card (sol's paragraph verbatim, results/leg-a-review-sol.md, with
   fable's clause):" through "(15:30) that motivated it." with: "The selector was fit on 20,054 hand-written,
   item-disjoint rows; no BFCL item or item-level paraphrase was used. BFCL was not untouched: its dev labels,
   schemas/template/checkers, and aggregate non-cohort analyses preceded the final selector and influenced tool-fact
   labels, protected roles, candidate roles, and harness choices; its dev split also selected the 1.7B/4B trunk by a
   frozen rule. Aggregate statistics over non-cohort BFCL cases motivated selecting over tool output and the tool-role
   label in the selector's training spec; the tool-role fact label (2026-09-02 20:28) post-dates the BFCL population
   analysis (15:30) that motivated it. The 64-case cohort was hashed in advance and its sealed item contents were not
   opened or executed before the final freeze. LEG A is a post-development, end-to-end comparison of KV retention plus
   source-labelled text reinjection, not a pure-KV or zero-shot result. Inference-time scoring of BFCL user/tool text
   applies the frozen selector and performs no fitting. 'Repo-level no-contact zero-shot' is reserved for the
   separately frozen family, and does not assert absence from trunk pretraining."

R2 Decisions preamble, add "(v) Safety allowances — invalid <= full + 1, repeated-call <= full + 1 and the <= 1 guard
   for degenerate are kept (fable F16/F24) over sol's invalid <= full, unexpected_duplicate_call <= full and no guard,
   because under case-level counting on a k = 6-16-case primary one event is one case (6-17 points) and full itself
   is a stochastic single run." Safety clause: "(kept at +1: one event is 2.5-4 points on a ~24-40-turn primary)" ->
   "(kept at +1: decision (v))"; "Vacuity guard for truncated, degenerate, invalid and repeated-call only: if full has
   0 events of a type, that type is judged '<= 1' and reported." -> "Vacuity guard for degenerate only (the +1 types
   already admit one case at a zero baseline): if full has 0 degenerate cases, degenerate is judged '<= 1' and
   reported." (If sol's version is preferred instead, write invalid <= full, repeated-call <= full, delete the guard,
   and delete decision (v); either way the choice must be recorded.)

R3 clf_control: "after all clamps matches exact per-role pinned columns" -> "after all clamps matches the treatment's
   exact total pinned columns and, on turns without shortfall, its exact per-role pinned columns". Preflight (6):
   "have equal per-role pinned columns and echo tokens within the clamp" -> "have equal total pinned columns, equal
   per-role pinned columns except on turns recorded control_role_shortfall (clf_control only), and equal echo tokens
   within the clamp". Pin overflow: "pin exactly the treatment's final per-role column counts" -> "pin exactly the
   treatment's final per-role column counts (clf_control: total, with the per-role split recorded, on shortfall
   turns)".

R4 Decision (iii): "with 6 <= k < 8 a Holm-corrected pass requires unanimity, disclosed." -> "disclosed: at k = 6 the
   smallest sign-flip p is 1/64 = 0.0156 (all six case means strictly positive; a single zero case mean raises it to
   1/32 and no Holm step-1/2 rejection is possible), so the first two Holm rejections require six strictly positive
   case means, while the third step and the A4 family (alpha 0.05) admit up to p = 3/64; at k = 7 one small-magnitude
   negative case mean can still pass step 1 (2/128 = 0.0156)."

R5 Echo definition: "entries as source-labelled JSON-quoted strings ... most probable first, capped at E = 1,024
   tokens (whole spans)" -> "entries = the arm's pinned spans after any overflow drop (never a candidate that is not
   pinned), as source-labelled JSON-quoted strings ..., most probable first, capped at E = 1,024 tokens (whole spans);
   a pin dropped on overflow drops its echo entry, so pin_overflow_total turns carry no echo in any arm".

R6 Add to the Arms paragraph after "Arms (teacher-forced):": "Column clamp for every comparator: matched spans are
   admitted whole in match order until the next would exceed the treatment's quota; the last admitted span is
   truncated at a Qwen3 token boundary so that the pinned column count is exact, and its echo entry is the truncated
   text. 'Impossible exact match' means the disjoint pool of the required role has fewer columns than the quota (or,
   for tool_swap_echo, no disjoint TOOL chunk within the registered width/age match for a selected chunk); it is
   recorded per turn (match_impossible) and makes the affected contrast uninformative as a whole, not a turn drop."
   (Alternative, if partial spans are unwanted: replace every "exact" pinned-column equality with "within 16
   columns, delta recorded" and add the same tolerance to preflight (6).)

R7 Contrasts: "If fewer than 6 sealed cases contribute an evicting turn, the leg is INCONCLUSIVE" -> "If fewer than 6
   sealed cases contribute an evicting turn, the leg is INCONCLUSIVE; the same floor applies to each contrast's own
   k (A3 after the 40,960-position exclusions): a contrast with k < 6 is uninformative (A3: the F27 rows apply)".

R8 Preflight (1): add at its start "(all 'final pass' floors here are teacher-forced all-or-nothing case pass; the
   free-running secondary carries no floor)". Reported list: "final all-or-nothing pass per arm (teacher-forced and
   free-running)" -> "final all-or-nothing pass per arm (teacher-forced for every arm; free-running for base and
   clf_pinned_echo only)".
