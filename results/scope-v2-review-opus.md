# scope-v2 relabel review — opus (2026-09-03)

Reviewed by hand, row by row, all 461 proposed `none -> rule` flips in
`data/classifier/review/scope-v2-patch.unreviewed.jsonl` (the 8 `note` entries were ignored) against
`data/classifier/LABELS.md` v2. Approved entries written verbatim to
`data/classifier/review/scope-v2-opus.jsonl`.

## Counts

| | n |
|---|---|
| proposed flips judged | 461 |
| **kept (approved as `rule`)** | **95** |
| rejected (stay `none`) | 366 |
| extra flips added (missed by kimi-k3) | 0 |

## Decision procedure applied uniformly

A flip was kept only if all three held:

1. **HOW, not WHAT-to-do.** The sentence states a constraint on how work must be written/done
   (form, length, structure, format, register, tone-as-target-state, language, voice, persona,
   process) or a standing behavioural commitment — not the work request itself.
2. **Scope survives the turn.** Scope is the conversation, the session/day/week/project, or an
   ongoing artifact (email, memo, letter, document, story, chapter, plan, table, code file).
   Rejected if scoped to a single assistant reply/answer/message ("this time", "just this once",
   "for this answer", "for this reply"), or to a single completed action/step.
3. **Not a bounded override of a standing rule.** One-time exceptions ("ignore the cap just this
   once", "for the ski trip, forget the Delta preference") are rejected: pinning them would
   misgovern later turns, which is the exact failure mode the v2 third scope excludes. Sentences
   that *restore* or *re-scope* a rule going forward ("after this, go back to listing only new
   ones") were kept.

Secondary lines drawn, applied consistently:

- **Whole deliverable vs sub-unit.** A tone/style constraint on a whole deliverable ("make the
  press pitch punchier", "make the rejection letter kind") persists through later revisions and was
  kept; the same wording aimed at a sentence, paragraph, lede or line ("make this sentence
  punchier", "rewrite paragraph two so the quote leads") is a one-shot edit and was rejected.
- **Maintainable property vs completed operation.** Numeric/structural targets ("two sentences",
  "fit one page", "under twenty words", "double-spaced", "APA 7th") were kept; bare operations
  with no target ("make it shorter", "trim the third sentence", "swap the second and third
  assumptions") were rejected.
- **Request-headed sentences rejected.** Where the sentence's head is the work request and the
  constraint is a trailing modifier ("Write the job ad ..., 300 words or so", "Draft the banner
  text, max 15 words", "Summarize this witness statement in five bullet points"), the row is a
  one-off task under v2 and was rejected. Pure-constraint sentences that follow a request in a
  separate turn ("Make it about six lines long.") were kept.
- **Content vs form.** One-off content additions to a single item ("include the Q3 revenue
  figures", "add a compliment about their service", "make the dragon purple", "call the badger
  Gunter") are the WHAT of a one-off task and were rejected; structural placement conventions that
  v2 names explicitly ("begin with ...", "end with a P.S.", "add a tl;dr") were kept.

The bar is deliberately strict: v2 leaves the reply/artifact boundary ambiguous in places, and
AGENTS.md directs the conservative reading when a spec is ambiguous. The false-positive cost here
is asymmetric — a pinned one-off exception actively misgoverns later turns, while a missed
task-scoped constraint only loses recall.

## 20 example rejections (index in the unreviewed patch)

| # | text | why rejected |
|---|---|---|
| 0 | "Just for this one, write it in Python so I can paste it into the notebook." | Explicit single-instance override of a standing TypeScript rule. |
| 8 | "Put that in a table for me this once, I'll export it." | "this once" — one-time exception to a screen-reader accessibility rule. |
| 20 | "Because the trustees meet on the 14th ... get it down to four pages ..." | Long and reason-laden, but one document, one meeting: a work request. |
| 21 | "For this paper only, I'll keep the existing tone and just cut length." | Assistant prose restating a one-off scope; creates nothing standing. |
| 57 | "For this reply, be very brief." | Scoped to a single reply — v2 scope (3). |
| 68 | "Make it quick, I only have a minute right now." | Reply-scoped urgency, not a constraint on any artifact. |
| 94 | "Swap the second and third assumptions, please." | Completed edit operation; nothing to maintain later. |
| 102 | "List them by age, oldest first." | One-off ordering of one tool result. |
| 128 | "For the 38 GB frame in the next cell, you may mutate in place to save memory." | Single-cell exception to a rule the user called permanent. |
| 156 | "For the red-eye to New York next week, ignore that — I need the 6 AM flight." | One-trip override; the 9 AM rule stands. |
| 190 | "Explain the electoral college like I'm a golden retriever." | Style-flavoured one-off explanation request. |
| 208 | "Make the dragon purple." | Story content decision, not a constraint on how the work is written. |
| 218 | "Just this once, let the bad guy win." | Explicit one-time exception. |
| 242 | "Make it shorter." | Bare comparative operation; no maintainable target. |
| 260 | "Rewrite the menu descriptions to sound fancier." | Rewrite request — the parent's canonical wrong-flip shape. |
| 291 | "Rewrite this rejection email so it sounds less robotic, thanks." | One-off work request. |
| 348 | "Stir the polenta constantly so it doesn't go lumpy." | Assistant recipe prose, not an instruction to the assistant. |
| 391 | "Turn this bullet list of comments into full sentences." | One-off transformation task. |
| 400 | "Grade this essay quickly, I need it in five minutes." | One-off grading task with reply-scoped urgency. |
| 457 | "Compare the serial numbers ... and stop there without updating inventory ..." | Long but strictly bounded single task. |

## Missed flips

None added. Two systematic sweeps over the remaining `none` rows found nothing that should flip:

- Conversation-scope markers (`from now on`, `always`, `never`, `whenever`, `for the rest of`,
  `going forward`) over 58 unproposed `none` user rows: every hit is a quotation, hypothetical,
  third-party maxim, or a "never mind" retraction — correctly `none` under v2's explicit
  quotes/hypotheticals/descriptions carve-out.
- Artifact-constraint markers (`keep it under`, `max N`, `use tabs`, `begin with`, `end with`,
  `oxford comma`, `in this document`, `throughout`) over unproposed `none` rows: 12 hits, 11 of
  which carry an explicit `this time` / `for this one reply` / `just this once` marker and are
  correctly `none`.

The single genuine near-miss is `kimi-k3-ctx:email-drafting-and-etiquette:5013` /
"Cut it down to under 100 words for this specific email." — a maintainable numeric cap on an
ongoing artifact, which my criteria would keep. It is **deliberately not added**, because
`data/classifier/review/sol-patch.jsonl` already marks that exact row `"drop": true`
("One-off numeric output-length task mirrors benchmark taxonomy"); re-labelling a row queued for
removal on contamination grounds would be the wrong move.
