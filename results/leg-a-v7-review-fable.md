# Final confirmation: LEG A registration v7 — fable, 2026-09-03

Scope: LEDGER-PLAN.md last section ("... LEG A ... v7", line 623 to EOF) checked against every fix in
results/leg-a-v5-review-sol.md (items 1-6, the two undeclared decisions, the "other two-way readings", and all eight
exact-text blocks) and results/leg-a-v5-review-fable.md (R1-R8). CPU-only foreground text review; no process launched
or signalled; sealed IFEval input and sealed BFCL cohort contents not read; .review.lock not waited on. This file is
my only output. Decisions (i)-(vii) are not re-opened.

## 1. Adoption audit

sol v5 exact-text blocks:

| sol block | v7 |
|---|---|
| Reported-metrics lead-in | verbatim |
| clf_control + recency_pinned resource text | verbatim |
| Preflight (6) equality sentence | verbatim, BUT the old lead-in it replaced was not deleted (residual A below) |
| Pin-overflow paragraph incl. "cache persists ... may exceed K" | verbatim |
| Exact-test sentence + A3-specific floor | verbatim |
| Comparator-delta disposition | verbatim |
| Preflight (1) metric-explicit text | verbatim |
| Model card (F23 text) | verbatim (sol's version) |
| Decisions (v)/(vi) on inferential rule and safety | recorded as (vii) and (vi) verbatim |

sol's items 1-6 and the three "other two-way readings" (preflight metric, comparator method failure, A3 cluster count)
are all closed by those blocks. sol's "line 2781 exceedance identical across arms" objection is closed by the new
"Each arm's within-turn cache may exceed K; per-arm columns and exceedance are recorded."

fable R1-R8:

| R | v7 |
|---|---|
| R1 model card | sol's F23 text verbatim; the timestamp clause in my R1 ("the tool-role fact label (2026-09-02 20:28) post-dates the BFCL population analysis (15:30) that motivated it") is absent (residual B) |
| R2 safety decision + clause + guard | recorded as "(v, superseded wording)" and (vi); clause "(kept at +1: decision (v))" and the degenerate-only guard verbatim |
| R3 per-role equality carve-out | equivalently, via sol's clf_control and preflight-(6) replacements (subject to residual A) |
| R4 unanimity correction | verbatim in (iii); consistent with "no separate unanimity condition is imposed" |
| R5 echo = pinned spans, linked drop | verbatim; consistent with the pin-overflow paragraph and decision (iv) |
| R6 column clamp / match_impossible | verbatim |
| R7 per-contrast k floor | verbatim (A3 rows named by description instead of "F27") |
| R8 preflight (1) prefix + reported list | prefix verbatim; reported list via sol's equivalent block |

## 2. Contradiction / two-readability check

Cross-read pairs that could conflict and do not: (i) preamble vs clf_control clause and (6); (iii) preamble vs "no
separate unanimity condition"; (iv) preamble vs R5 echo definition and the overflow paragraph; R6 "exact" clamp vs the
four "exact per-role/total pinned columns" statements; delta <= 16 vs "equal echo tokens within the clamp"; the two
k<6 INCONCLUSIVE sentences (duplicate, identical); preflight (1) metric vs the reported-list metric vs SECONDARY
"never gated"; safety (v)/(vi) vs the safety clause (same substance, one cross-reference to the superseded label).

Residuals:

A. Preflight (6) — dangling fragment (required). The text reads: "every candidate comes from a message with index <
   the turn-t user message; treatment, clf_control, recency_pinned and tool_swap_echo Treatment, `recency_pinned`, and
   `tool_swap_echo` have equal per-role pinned columns and echo tokens within the clamp." The un-deleted lead-in
   "treatment, clf_control, recency_pinned and tool_swap_echo" can be read as a fifth subject of "have equal per-role
   pinned columns", which puts clf_control back under the per-role equality on every turn — exactly the shortfall
   contradiction R3/sol-(i) removed. Two-readable as written.

B. Model card (required for "R1 verbatim"; no outcome effect). v5 carried the timestamp lineage disclosure; R1 kept
   it; v7's "F23 verbatim" drops it.

C. Cross-reference (optional). "(kept at +1: decision (v))" points at the item labelled "(v, superseded wording)";
   (vi) is the operative statement of the same choice. Not two-readable (both say the same thing), but a cleaner
   pointer is "(kept at +1: decisions (v)/(vi))".

## 3. Exact residual text (LEG A AMENDMENT 1)

A. In preflight (6), replace
   "every candidate comes from a message with index < the turn-t user message; treatment, clf_control, recency_pinned and tool_swap_echo Treatment, `recency_pinned`, and `tool_swap_echo` have equal per-role pinned columns and echo tokens within the clamp."
   with
   "every candidate comes from a message with index < the turn-t user message; Treatment, `recency_pinned`, and `tool_swap_echo` have equal per-role pinned columns and echo tokens within the clamp."
   (the following sentence "On no-shortfall turns `clf_control` meets the same per-role equality; ..." stays as is).

B. In the model card, after "... the tool-role label in the selector's training spec." insert
   "; the tool-role fact label (2026-09-02 20:28) post-dates the BFCL population analysis (15:30) that motivated it."
   (i.e. replace "training spec. The 64-case cohort" with "training spec; the tool-role fact label (2026-09-02 20:28) post-dates the BFCL population analysis (15:30) that motivated it. The 64-case cohort").

C. (optional) "(kept at +1: decision (v))" -> "(kept at +1: decisions (v)/(vi))".

## VERDICT: CONFIRMED-WITH-FIXES

v7 carries every sol v5 exact fix and every fable R1-R8 fix verbatim or equivalently, and decisions (i)-(vii) are
mutually consistent with the body, except for one un-deleted lead-in in preflight (6) (residual A, which re-creates the
clf_control per-role reading on shortfall turns) and one dropped R1 disclosure clause (residual B). Apply A and B (C
optional) as LEG A AMENDMENT 1 before the harness hash is bound; nothing else needs to change.
