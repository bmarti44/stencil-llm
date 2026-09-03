# Review of the kimi SCOPE pass (data/classifier/kimi-scope/) — opus, 2026-09-03

Scope: 40 files, 4,954 rows, all `source = kimi-k3-scope:<domain>:<seed>` (one seed per domain).
Judged by hand against `data/classifier/LABELS.md` v2 (three scopes). CPU only; sampling, tallying and
exact-match/regex sweeps in python; no model or GPU process launched; nothing under the benchmark
directory read.

Outputs: `data/classifier/review/scope-pass-opus-patch.jsonl` (191 patch rows) and this file. No other repo edits.

## 1. Sample

Seeded stratified sample, `random.Random(20260903)`, **5 rows per label per file** (every file has >= 13 rows in
every class, so no cell was short), plus a forced include of all 12 rows whose `context` is a list.
**611 rows: 211 rule / 200 fact / 200 none.** The sample ids are reproducible from
`/tmp/.../scratchpad/w/sample.json` (file, line index, label, text); the sampler is 12 lines and is quoted in the
patch-generation script. Every sampled row was read and judged individually.

### Error rates on the sample

| original class | n | label errors | rate |
|---|---|---|---|
| rule | 211 | 0 | 0.0% |
| fact | 200 | 1 | 0.5% |
| none | 200 | 6 | 3.0% |
| **all** | **611** | **7** | **1.15%** |

A further **21/611 (3.4%)** sampled rows are hygiene problems rather than label errors (speaker-prefix leak,
benchmark-marker transposition, degenerate filler, verbatim duplicate) and are dropped, not relabelled.

Per-file: label errors appear in 5 of 40 files (academic-tutoring 1, email-drafting 2, legal-document-drafting 1,
multilingual-mixed-casual 1, personal-assistant-scheduling 2). Hygiene drops touch 12 of 40 files in the sample.

**Sampling caveat, stated up front:** 5-per-label-per-file deliberately under-weights the six oversized files
(recipe 360, technical-documentation 309, research-literature-review 303, journalism 285, sales-crm 280,
academic-tutoring 210 rows — 35% of the pass from 6 of 40 domains, against a 95-row median). The worst quality
problem in the pass (finding S4) lives in the *tails* of two of those files and is therefore
under-represented in the sample rate above. It was caught by whole-pass sweeps, not by the sample.

### Direction of the errors

All 7 sample errors are in the `none` -> `rule` / `fact` -> `rule` direction, i.e. **under-retention**: a standing
constraint labelled `none` teaches the write-time selector to forget it. There were **zero** `rule` -> `none`
errors in the sample, which is the reassuring half of the result — the pass does not over-fire.

## 2. What the brief asked me to watch for

**(a) `context` as a list rather than a string — no label errors.** 165 rows carry `context`; 153 are strings and
12 are lists (data-analysis 4, sales-crm 6, system-prompt-personas 2). I read all 12 joined; every one of them
supports its label (they are all `rule`, and each is a genuine artifact-scoped constraint or a cancellation whose
scope only reads correctly against the preceding turn). The type inconsistency is a *schema* problem for whatever
joins them, not a labelling problem, and `data/classifier/kimi_gen_context.py:56` would have rejected these rows
(`isinstance(o.get("context"), str)`) — `kimi_gen_scope.py` has no such check. Recommend the joiner coerce
`list -> "\n".join(...)` and the generator validator be aligned. Speaker prefixes inside `context` are also mixed
case (`user:` 107, `User:` 40, `assistant:` 4, `Assistant:` 2) — harmless but worth normalizing.

**(b) task requests with a trailing constraint labelled rule — this is a real inconsistency, and I normalized it
the other way from what the brief anticipated.** kimi applied an explicit, documented convention (visible in its
`why` fields: "constraint is main content, treat as rule"; once, candidly, "Ambiguous one-sentence case; per
instruction treat as rule"). Across the pass, 156 `rule` rows open with a creation/edit verb; the overwhelming
majority are constraints on an already-named artifact ("Write the postmortem timeline in UTC"), which v2 settles
as `rule`. The genuinely contested form is `Summarize <X> in <length>`: **18 labelled rule, 9 labelled none**. Of
the 9 `none`, 3 carry an explicit single-reply marker and are correct; the other 6 are verbatim-equivalent to rows
labelled `rule` — a near-duplicate sweep (Jaccard on number-masked token sets) returned
`"Summarize this in under 100 words." = rule` (5 files) against `"Summarize this in under 90 words." = none`
at **Jaccard 1.00**, and `"Keep this summary under 100 words." = rule` (6 files) against
`"Keep this particular summary under 100 words." = none`.
So this is a **contradiction, not an ambiguity**, and it had to be resolved in one direction. I normalized the 7
outliers to `rule` because (i) it is the pass's 18-vs-6 majority, (ii) v2's closing sentence says "a constraint on
how the work must be written is TASK-scoped (rule)" and a word cap is exactly that, (iii) the cap *is* echoed back
when the user says "redo that summary with the Q3 numbers", and (iv) the error is asymmetric — a wrong `rule`
costs a pinned KV column, a wrong `none` loses the constraint. I record explicitly that the opposite reading is
defensible and that **v2 should state which clause wins in a single sentence that both requests work and constrains
it**; if the spec is amended the other way, these 7 patch rows and the 18 majority rows flip together.
Bare requests with no constraint ("Summarize this article for me.") are correctly `none` throughout.

**(c) explicit single-reply constraints labelled rule — clean, zero hits.** A regex sweep of the whole
single-reply marker family ("just this once", "this time only", "for this message/answer/reply", "one-off",
"this one time", ...) returns 479 rows, **all 479 labelled `none`, none labelled `rule` or `fact`**. Scope (3) is
applied without exception. The mirror-image error does exist and is finding S2 below.

**(d) facts labelled rule — essentially clean; one preference misfiled as fact.** No declarative world-fact was
found labelled `rule`. The reverse: `"I prefer visual explanations."` is labelled `fact`, but LABELS.md's `rule`
line explicitly covers "preference ... that governs the assistant's FUTURE replies" — relabelled. Its three
siblings ("I prefer morning study sessions / studying at night / morning workouts") are left as `fact`: those are
user-state facts that inform planning, not constraints on the assistant's prose. Third-party preferences
("The customer prefers phone calls", "María prefers the Mexican Spanish variants") are correctly `fact`.
Note that fact/rule confusions are the cheap kind — the mechanism retains both.

**(e) near-duplicates and templated openings — the largest structural weakness of the pass.** See S4/S5 below.

**(f) benchmark-like phrasings — one systematic transposition, otherwise clean.** Sweeps for `<<...>>`,
"wrap in double quotes", "no commas", "letter X appears N times", "postscript", "repeat the request",
"two responses separated by 6 asterisks", JSON-only wrapping all returned **zero** hits. The pass is markedly
cleaner on this axis than the original kimi/ pass. What it does contain is finding S3.

## 3. Systematic findings (found by whole-pass sweeps, stated with the sweep that found them)

**S1 — Speaker prefix leaked into the `text` field (28 rows, dropped).**
Sweep: `^(Assistant|User|Tool|System):\s`. 28 hits across 8 files; **25 of the 28 are labelled `none`**, so the
literal string "Assistant: " is a near-perfect shortcut feature for the `none` class — the classifier can learn the
prefix instead of the semantics. The `role` field already encodes the speaker. Four of the 28 are worse: they pack
a whole multi-turn exchange into one `text` (e.g. `"Assistant: Here's the memo draft. User: Trim it, keep it under
90 words."`), which is a `context`/`text` split failure, and one of them (`teaching-assistant-grading:83`) is a
verbatim copy of a genuine `fact` row 30 lines earlier, labelled `none` — the same sentence with two labels.
All 28 dropped.

**S2 — System persona lines labelled `none` (8 rows; 7 relabelled to `rule`, 1 dropped under S1).**
Sweep: `^(System: )?You are\b|^Act as|^Pretend|persona` -> 18 rows, split 11 `none` / 7 `rule`.
kimi's `why` fields state an exclusion that appears nowhere in LABELS.md: "System prompt lines are excluded per
scope", "system preamble out of scope". LABELS.md says the opposite — `rule` explicitly covers **persona**, `system`
is a legal `role`, and `none` is only "everything else". kimi contradicts itself: `system-prompt-personas:0`
(`"You are Marina, a cheerful marine biologist who adores puns."`) is labelled `rule` while the identical construct
is `none` in six other files. Two of the mislabelled rows carry outright standing prohibitions
(`"...Never diagnose or prescribe."`, `"...Confirm destructive actions before executing."`) — these are rules by
any reading. Relabelled: email-drafting 88, language-learning 77, newsletter 45, smart-home 91, therapy 78,
travel 75, web-browsing 90. Correctly left alone: `"The system prompt is 'You are a helpful research assistant'."`
(a *description* of a rule -> `none`, per the spec's quotes/descriptions clause).

**S3 — IFEval title marker transposed into plain language and templated (21 rows; 20 dropped).**
Sweep: `angle brackets` -> 21 hits, **all `rule`, spread over 20 of the 40 files**: "Begin the report with a title
in angle brackets", "Begin the poem with a title in angle brackets", "Begin the summary with a title in angle
brackets", ... This is IFEval `detectable_format:title` ("a title, wrapped in double angular brackets, such as
`<<poem of joy>>`") with the markup spelled out; one row even carries the literal markup
(`Title the report sections with angle brackets, like <Returns>.`). Brief item (f) names `<<title>>` as an exact
marker to drop, and item-level disjointness is the registered policy, so all 20 template instances are dropped.
**One kept:** `translation-and-localization:10` ("Don't translate anything in angle brackets") — there angle
brackets are XML placeholders and the constraint is genuinely domain-native.
Three single rows dropped on the same policy: the literal `***Moon Soup***` markup (IFEval highlight/divider),
the one `P.S.` row, and the 4 `exactly N bullet points` rows (IFEval `detectable_format:number_bullet_lists`).
Deliberately **kept**: "square brackets" (11 rows) — bracketed ticket numbers/dates are a real domain convention
and are not the IFEval placeholder constraint; and plain-language length/format rules generally, per the disclosed
constraint-type overlap.

**S4 — Two files degenerate into vacuous templated filler (42 + 8 rows dropped).**
Sweep: `^The (meal plan|recipe|cookbook|review|document|draft)\b.*(should|must) be`.
`recipe-and-meal-planning` (360 rows, ~4x the 95-row median) loops from index ~227 to the end through
"The meal plan should be delicious / healthy / cheap / exciting / simple / a showstopper / a guilty pleasure",
strictly alternating rule/fact/none; `research-literature-review` (303 rows) does the same with
"The review should be well-written and engaging / visually appealing / free of errors / thorough and
comprehensive". These state no retainable, checkable constraint. Labelled `rule`, they teach the classifier that
*any* `The X should be Y` declarative is a rule — a very cheap and very wrong feature. 18 recipe rows and 24
research-lit rows dropped. Rows in the same runs that carry a concrete constraint are **kept**
(under 20 minutes, gluten-free and dairy-free, ~500 words, printable, for a family of four; at most N pages,
single-spaced, third person, .docx, structured chronologically). `research-literature-review` is also the only
file with same-source exact duplicates (4 texts x 2 copies); since `(source, text)` cannot address one copy, both
copies of each are dropped — all 8 are inside the degenerate tail anyway.

**S5 — Verbatim duplicates across files (39 texts, 111 rows; 72 dropped, first copy kept).**
Sweep: exact case-folded text equality. Worst offenders: `"Keep this summary under 100 words."` (6x, all `rule`),
`"Just this once, keep it under 100 words."` (6x, all `none`), `"For this message, reply in French."` (6x),
`"Summarize this in under 100 words."` (5x), `"Thanks, that looks great!"` (5x). Kept the first-occurring copy of
each and dropped the rest. This is only the exact-match tip; see S6.

**S6 — Template concentration (reported, not patchable row-by-row).** Frequency sweeps over the full pass:

| template | rows | label purity |
|---|---|---|
| single-reply marker family ("just this once", "this time only", "for this message", ...) | 479 (9.7%) | 100% none |
| "Now extend / add a closing ..." | 105 (2.1%) | 100% none |
| "under N words" | 127 | 97 rule / 30 none |
| "in (the) second person" | 37 | 100% rule |
| "British spelling" | 41 | 100% rule |
| "no contractions" | 17 | 100% rule |
| "angle brackets" (S3) | 21 | 100% rule |
| "Oxford comma" | 7 | 100% rule |

~24% of the `none` class is carried by one marker family and ~5% more by one opening. A classifier can reach high
accuracy on this pass from a dozen lexical cues without ever learning scope, and the held-out sets share the
author, so this will not show up as a validation gap. **The mitigation is not more patching** — it is (i) an
author-disjoint scope-specific held-out slice, and (ii) a generation round that varies surface form for the
single-reply and "now extend" families. I flag this as the highest-value follow-up from this review.

**S7 — "for now" / "temporarily" has no scope in v2 (6 rows relabelled to `rule`).**
Sweep: `^(for now|only for now|temporarily|for the time being|for the moment)` -> 16 rows, 15 `none` / 1 `rule`
(itself an inconsistency: `technical-documentation:68` "For now, treat the v2 endpoints as authoritative" = `rule`).
v2 scope (3) is *explicitly single-reply*; "for now" is until-further-notice, which is a different thing, and the
sentences in question constrain how the work is written, so scope (2) applies. Relabelled to `rule` the 6 that are
output constraints: `"For now, keep the draft in all lowercase..."`, `"For now, answer in English — I'll switch
later maybe."`, `"Only for now, keep the list to three items."`, `"For now, use 12-hour time in the schedule."`,
`"Temporarily, bold the deadlines in the plan."`, `"For now, answer in one sentence."`. **Left as `none`** the
sweep hits where "for now" modifies a one-off *task* ("For now, just list the overdue shipments", "For now, just
print the first twenty rows") and the two that do carry an explicit single-reply marker ("For now only, ...",
"For now, only this reply: ..."). Recommend v2 name this case explicitly.

**S8 — "for this section" read as single-reply (2 rows relabelled to `rule`).**
Sweep: `^(just )?for (this|the) (section|part|chapter|paragraph|page|draft|doc|file|piece)` labelled `none` -> 3 rows.
`legal-document-drafting:5` ("Just for this section, write in the passive voice") and `:57` ("For this section
only, use single spacing") are scoped to a *part of the artifact*, not to one reply — the constraint is echoed back
when that section is revised. kimi's `why` calls them "explicitly single-reply constraint", which misreads scope (3).
Relabelled. `research-literature-review:32` ("For this part, explain it like I'm five") left as `none` — there
"this part" is the explanation being given now.

## 4. What I patched

`data/classifier/review/scope-pass-opus-patch.jsonl` — 191 rows, addressed by exact `(source, text)` match.

| | rows in patch | rows affected in the pass |
|---|---|---|
| relabel -> `rule` | 23 | 23 |
| drop | 168 | 172 |
| **total** | **191** | **195** |

(191 patch rows address 195 pass rows: the 4 same-source duplicate texts in `research-literature-review` each match
two rows and both copies are intended to go.)

Relabels: 7 system personas (S2), 7 `Summarize <X> in <length>` outliers (b), 6 "for now"/"temporarily" (S7),
2 "for this section" (S8), 1 preference-as-fact (d). All 23 are `-> rule`; there is no `-> none` and no
`-> fact` patch, consistent with the sample finding that the pass never over-fires.

Drops: 72 cross-file verbatim duplicates (S5), 50 degenerate-tail rows (S4, incl. 8 same-source duplicates),
28 speaker-prefix leaks (S1), 20 angle-bracket title markers (S3), 6 other marker/hygiene singles
(`***`, `P.S.`, 4x "exactly N bullet points"), 1 two-sentence row with an embedded newline
(`slide-deck-and-report-writing:21`, whose two halves carry different labels).

Every `(source, text)` key in the patch was checked against the pass: all resolve to exactly one row except the
4 deliberate same-source duplicate pairs, which are listed above.

Resulting pass if the patch is applied: **4,954 -> 4,782 rows**; label distribution
2060/893/2001 (rule/fact/none) -> **2001/890/1891**. Three files are untouched
(`customer-support-chat` and two others are near-untouched at 1 row); the most-affected are
`teaching-assistant-grading` 13.2%, `research-literature-review` 10.6%, `devops-incident-response` and
`medical-intake-and-triage` 9.8%, `slide-deck-and-report-writing` 8.9%, `system-prompt-personas` 7.8%,
`recipe-and-meal-planning` 7.2%.

## 5. Verdict and recommendations

The scope pass is **sound on the thing it was written to fix**. Scope (3) is applied without a single exception in
479 rows; scope (1) markers are never mislabelled; the task/artifact-scoped `rule` class — the whole point of v2 —
is 0/211 wrong in the sample. Benchmark-marker contamination is one transposed template, not a pattern.
The 1.15% sample label-error rate is low and the errors are all one-directional (under-retention), which is the
safe direction for a write-time selector.

The real risks are structural, not per-row:

1. **Template concentration (S6)** — a dozen lexical cues can carry most of the label signal, and the held-out sets
   share authors, so this will not surface as a validation gap. Highest-value follow-up: an author-disjoint
   scope-specific held-out slice, plus surface-form variation for the single-reply and "now extend" families.
2. **Domain imbalance** — 6 of 40 domains supply 35% of the rows, and two of those degenerate (S4). Consider
   capping per-domain contribution at roughly the 95-row median after the patch.
3. **Two spec gaps to close in LABELS.md v2, both of which produced inconsistency here**: (i) whether a sentence
   that both requests work and constrains it is `rule` or `none` (finding b; I normalized to `rule`); (ii) that
   "for now"/"temporarily"/"for this section" are *not* scope (3) (S7, S8). Also worth one line: system-prompt
   personas are `rule`, and a *description or quote* of a rule stays `none` (S2).
4. **Schema**: align `kimi_gen_scope.py`'s validator with `kimi_gen_context.py`'s (`context` must be a string, or
   the joiner must coerce lists), and forbid speaker prefixes inside `text` and newlines inside `text` at
   generation time — both leaks would have been caught for free (S1, S2's leaked rows,
   `slide-deck-and-report-writing:21`).
