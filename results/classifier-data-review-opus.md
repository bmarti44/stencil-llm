# Classifier data review + enrichment — opus (2026-09-02)

Reviewer/author: opus. Brief: review and enrich the kimi-written classifier data. Label spec: `data/classifier/LABELS.md`.
Outputs: `data/classifier/review/opus-patch.jsonl`, `data/classifier/opus-enrich.jsonl`,
`data/classifier/heldout/opus-heldout.jsonl`, this file. No other repo files touched. CPU only; no model or GPU process
launched; nothing under `data/bench/` was read.

## 1. What was reviewed

- `data/classifier/kimi/*.jsonl` — 72 files, **10,812 rows**, 36 domains, complete. All rows parse; every row carries
  exactly the seven fields `text/role/label/domain/hard/why/source`; no row has `context`.
  Corpus distribution: rule 3,932 / fact 3,563 / none 3,317; role user 8,883 / tool 947 / assistant 919 / system 63;
  hard 5,690 (52.6%).
- `data/classifier/kimi-ctx/*.jsonl` — **25 files present at review time** (the pass is still being written), of which
  **22 are non-empty**; `data-analysis-with-tools-ctx.jsonl`, `product-management-specs-ctx.jsonl` and
  `translation-and-localization-ctx.jsonl` were zero bytes. **3,134 rows**, all parse, all carry `context`.
  Distribution: rule 1,095 / fact 1,016 / none 1,023; role user 2,668 / assistant 319 / tool 147.

### Quality sample (single-sentence pass)

Stratified, seeded, reproducible: `random.Random(20260902)`, then for each of the 36 domains sample 6 rows of each
label without replacement, domains iterated in sorted order, rows keyed `<file-stem>:<0-based line>`.
**n = 648** (216 rule / 216 fact / 216 none; 18 per domain). Every sampled row was read and judged against LABELS.md.
The full id list is in §7.

## 2. Label error rates

| class | sampled | label errors | rate |
|---|---|---|---|
| rule | 216 | 1 | 0.46% |
| fact | 216 | 0 | 0.00% |
| none | 216 | 2 | 0.93% |
| **all** | **648** | **3** | **0.46%** (95% CI ≈ 0.1–1.3%) |

Separately, **5 of the 648 rows carried a wrong `role`** (0.77%) with the label itself correct — see §3.1; a targeted
whole-corpus scan found 57 such rows, so the sample rate understates it slightly.

Per-domain: 33 of 36 domains had zero label errors in their 18 sampled rows. The three with one each were
`creative-writing-collaboration`, `negotiation-and-procurement`, `medical-intake-and-triage`. Role errors clustered in
`customer-support-chat` (2/18), `teaching-assistant-grading` (2/18), `journalism-and-fact-checking` (1/18).

The three label errors:

- `creative-writing-collaboration-s1:152` — "I need the story to be more thematically rich." labelled **rule**. Vague
  adjectival critique of the draft in hand; nothing to pin or re-inject. → **none**. (Two siblings in the same template
  family, "more thematically consistent" and "more emotionally resonant", were patched with it.)
- `negotiation-and-procurement-s1:109` — "Hold off on sending anything to Gruber until I talk to legal." labelled
  **none**. This governs every later turn until a release event, and the corpus labels the structurally identical
  "Answer in emojis only until I say stop" and "stay in character until I say 'scene'" as rule. → **rule**
  (consistency fix, not a taste call).
- `medical-intake-and-triage-s2:136` — "I'll be out next Friday for my sister's wedding." labelled **none**. Durable
  availability the assistant must respect when it next schedules; the same content is `fact` in the scheduling and
  travel domains ("I'll be offline from the 5th to the 9th" is even labelled rule). → **fact**.

Headline: **kimi's single-sentence labelling is good.** In particular the "imperative ⇒ rule" bias the interim
classifier shows is *not* in kimi's labels — 1,429 of the 3,932 rule rows carry no literal scope word ("always",
"from now on"), and the bare-imperative one-off tasks I checked are consistently `none`. What the corpus lacks is
*volume and variety* of that contrast, which is what §5 supplies.

## 3. Systematic problems

### 3.1 Role mislabelling: user rules tagged `role: assistant` (57 rows)

The largest defect. `customer-support-chat-s1` lines 143–227 fall into a mechanical 4-row cycle
(assistant-rule / tool-fact / user-none / user-fact) in which the "assistant" slot is filled with a *verbatim
second-person user instruction* — "Whenever you mention a policy, quote the exact section number." — carrying the
`why` "assistant restating user rule". There is no restatement: no acknowledgement wrapper, no first-person verb.
Same defect, sparser, in `teaching-assistant-grading-s1` (19 rows), `journalism-and-fact-checking-s2` (5),
`data-analysis-with-tools-s1` (1), `ecommerce-order-management-tools-s1` (1). The label (`rule`) is right in all of
them; the speaker is wrong. Left unfixed, a role-aware model learns that assistants issue standing orders.

Patched with `new_role: "user"` (42 patch entries covering 70 rows, since several texts repeat).

Genuine assistant restatements elsewhere in the corpus are fine and plentiful ("Noted — five dinners max per plan",
"Understood, staged payments whenever fees pass £250k"); the scan that found the 57 used the absence of any
acknowledgement token plus an imperative opener, and I read every hit.

### 3.2 Template recurrence and near-duplicates

- 74 texts appear more than once (202 rows). Most are cheap ("ok cool" ×15); but
  `customer-support-chat-s1` repeats a 15-rule block twice inside the same file, so
  "Whenever a customer mentions 'cancel', offer a retention discount." exists three times.
- Four files are visibly templated (fraction of rows sharing a repeated 4-word opening):
  `customer-support-chat-s1` 147/229, `teaching-assistant-grading-s1` 65/299,
  `creative-writing-collaboration-s1` 38/156, `research-literature-review-s2` 13/183. E.g. eight rows beginning
  "From now on, the story ..." and six beginning "I need the story to ...".
- Cross-domain digit-swapped twins: card "ends in 4417" (travel s1:14), "ends in 4471" (travel s2:13), brokerage
  "ends in 4417" (financial-planning s2:43).
- A five-member family "Summarize every <X> I paste from now on into exactly <N> bullets/sentences" spans five domains.

**Recommendation for the trainer (not patched):** dedupe the training split on `(text, label, role)` before training,
and consider capping per-file 4-gram-opening repetition. I did not emit `{"drop": true}` for these because the patch
key is `(source, text)` and one `source` covers a whole file, so a drop would remove all copies including the legitimate
first occurrence.

### 3.3 Benchmark leakage by paraphrase (IFEval taxonomy) — 11 rows dropped

I scanned all 10,812 rows against 19 IFEval-family patterns (lowercase/uppercase casing, exact bullet/sentence/word
counts, P.S./postscript, wrapped double quotes, `<<title>>`, placeholders, JSON-only output, comma bans, keyword
frequency, start/end-with-exact-phrase, "two responses separated by six asterisks", highlighted sections, "repeat the
request first"). **No hits at all** for the double-quote wrapper, `<<>>`, JSON-format, comma-ban, two-response,
highlight or repeat-the-request families — those benchmarks are not being paraphrased wholesale. Eleven rows were
close enough to the taxonomy to drop:

- `research-literature-review-s2`: "start every response with 'Certainly!'" (startend:starter),
  "use the word 'elucidate' at least once in every summary" (keywords:frequency),
  "all your responses must be exactly 3 sentences long" (length_constraints:number_sentences, no domain hook).
- `children-story-writing-s2`: "the word 'adventure' appears at least once in every story ..." (keywords:frequency).
- `system-prompt-personas-s1`: "For every poem you write, use only lowercase letters." + its assistant restatement
  (change_case:english_lowercase).
- `academic-tutoring-s2`: "no caps in ur replies pls, lowercase everything" + its restatement — same casing taxonomy
  despite the casual register and the personal reason. Judgment call: I dropped them for consistency and wrote
  replacement casual style rules by hand in the enrichment.
- `email-drafting-and-etiquette-s1`: "Add a P.S. to this one mentioning the parking situation." (detectable_content:
  postscript is named explicitly in the brief's leak list, even though this row is domain-natural and labelled `none`).
- `web-browsing-agent-s1` and `smart-home-control-agent-s2`: the two "exactly three bullet points, **no more no less** /
  **no more, no fewer**" rows. The tautological tail is the IFEval tell; four plainer siblings
  ("summarize each screening call in exactly three sentences") were left in place as natural user preferences.

Borderline rows deliberately **kept**, with reasons: "From now on, you will only use passive voice" (not an IFEval
constraint type); "end every reply with a question about how I'm feeling" and "start every reply with one validating
sentence" (these carry real semantic content and a domain motive, unlike IFEval's contentless start/end checkers);
"Always credit photos with the agency name in all caps" and the several "if I type in all caps I'm distressed" rows
(all-caps as *meaning*, not as an output format).

I found no trace of Multi-IF / BFCL / tau-bench / S2 / B3 phrasing: no `functions.`-style tool schemas, no
tau-bench airline/retail policy language, no BFCL parallel-call framing.

### 3.4 Ambiguity classes worth pinning down in LABELS.md

These are not errors — kimi is internally consistent — but the boundary is thin and the held-out score will move on it:

1. **Session-scoped instructions.** "for the rest of today" / "for now" → `none`, but "until I say stop" / "for the
   rest of this debugging session" → `rule`. Both bind future turns. Suggest: any instruction whose scope extends past
   the current reply is `rule`, and say so explicitly.
2. **Preference stated as fact vs. as directive.** "My spouse prefers a matte finish" → `fact`; "I don't eat pork, so
   keep it out of any recipe" → `rule`. The operative distinction is the presence of a directive clause; worth writing
   down, because the retention mechanism arguably wants both pinned.
3. **Facts with an instruction riding on them.** "The corporate card ends in 4417, use that one for work trips only" →
   `rule`; "The corporate card on file ends in 4471" → `fact`. Consistent, but a single-label scheme forces a loss here.

## 4. Patch file

`data/classifier/review/opus-patch.jsonl` — 58 entries, every one verified to match at least one `(source, text)` pair
in `data/classifier/kimi/`:

| kind | entries | rows affected |
|---|---|---|
| `{"drop": true}` | 11 | 11 |
| `{"new_label": ...}` | 5 | 5 |
| `{"new_role": ...}` | 42 | 70 |
| total | 58 | 86 |

`new_role` is an additive field beyond the brief's schema; it was needed because the defect in §3.1 is a speaker error,
not a label error, and dropping those rows would throw away 70 perfectly good rule examples. A consumer that ignores
unknown keys will simply leave the roles alone.

I did **not** patch `data/classifier/kimi-ctx/` — those files were still being written during the review and line
offsets are unstable. §6 reports its defects instead.

## 5. What I wrote by hand

Everything below was written one row at a time, by hand, in the LABELS.md schema. No generation script, no templating,
no copying from any benchmark. Every text is unique within its file; zero overlap between the enrichment and the
held-out set; one incidental collision with kimi ("Book it.") was reworded.

### 5.1 `data/classifier/opus-enrich.jsonl` — 434 rows, `source: "opus-enrich"`

rule 178 / fact 45 / none 211; role user 391, tool 21, assistant 17, system 5; hard 292 (67%); 59 domains; 10 rows
carry `context`.

**First priority — the measured gap (quick-checks item 13): 154 one-off imperative TASK sentences labelled `none`**,
each written next to a look-alike standing rule labelled `rule`. Roughly 70 such minimal pairs, built so the *only*
discriminating signal is scope, not surface form:

- "Write a short account of the fundraiser for this month's newsletter." (none) ↔ "Write every newsletter piece in the
  third person." (rule)
- "Fix the failing test in the billing module." (none) ↔ "Fix failing tests before you touch anything else, as a habit."
  (rule)
- "Draft the email to the vendor about the late pallets." (none) ↔ "Draft vendor emails in a firm but polite register
  from here on." (rule)
- "Now add a closing section that thanks the volunteers." (none) ↔ "Always close the newsletter with a line thanking the
  volunteers." (rule)
- "Redact the card number in this one before you send it." (none) ↔ "Redact card numbers to the last four digits
  everywhere, no exceptions." (rule)
- "Do that for the other three as well." (none, closed set) ↔ "Do that for everything from now on." (rule)

Deliberate variation inside the negatives: two-word bare imperatives ("Deploy it.", "Roll it back.", "Cancel it.",
"Book it then."); sloppy lowercase ("draft the notice for the road closure pls"); over-polite 40-word requests
("If you have a moment, would you mind pulling together a one-page brief on the zoning change before Tuesday's council
meeting?"); imperatives that *contain* a conditional ("Grade this stack of quizzes and flag anyone under fifty
percent."); imperatives that contain a number or a format word without being format rules ("Summarise where we are for
the client, half a page.", "Cost out the new lamb dish at a 68 percent margin."). Domains span office, trade, clinical,
creative and agentic work, and 30+ of the 59 domains do not appear in kimi's list at all (veterinary clinic, brewery,
auto repair, beekeeping, tailoring, farm management, church admin, wine shop, archive, HVAC…), so this also broadens
domain coverage rather than only thickening the contrast.

Then the categories the brief named:

- **Long agentic sessions with many tool calls** (~25 rows, several with `context`): tool lines that *are* facts
  (`kubectl get pods → ledger-3a1b CrashLoopBackOff`, `git rev-parse HEAD → 4c81de9…`, `terraform plan → 0 to add,
  2 to change`) sitting next to tool lines that are *not* (`Fetching 42 objects…`, `Retrying request (attempt 2 of
  5)…`, `collecting … collected 215 items`), plus the user turns that consume them ("Revert to 4c81de9 and redeploy."
  → none; "Apply it." → none) and one standing gate ("Show me the plan before you apply anything, for the rest of this
  migration." → rule).
- **Assistant restatements** (17 rows) split deliberately: restating a standing rule → `rule`; restating a *one-off*
  scope → `none` ("Right, so for tonight's board pack only, I'll normalise these six and stop there."); completion and
  clarification prose → `none`; an assistant recording a corrected value → `fact`.
- **Cancellations and scoped rules** (~20 rows): cancel ("Ignore what I said about avoiding bullet points"), narrow
  ("Only ping me on deploys that touch payments now"), suspend then reinstate ("Suspend the no-spoilers rule until we
  finish the book." / "Right, spoilers are back off limits."), reaffirm-with-exception ("The no-jargon rule still
  stands, I just want this one to be technical."), and retract-the-retraction ("Actually never mind, keep doing what
  you were doing.") — all `rule`, against explicit single-reply overrides ("Just for this reply, go as long as you
  like.", "For this next message only, drop the formal register.") which are `none`.
- **Facts corrected later** (~8 rows): amount, date, identifier, job title, lease term, all as `fact`; plus a bare
  retraction with no replacement ("Ah, ignore that, I misread it.") as `none`, and an unreliable self-report ("I think
  I said Tuesday earlier but I honestly can't remember.") as `none`.
- **Multilingual / casual / sloppy** (~14 rows) in Spanish, French, German and text-speak, with the rule/none contrast
  preserved inside each language.
- **System-prompt personas** (5 system rows + 4 user rows): persona and prohibition as `rule`, system-supplied hours
  and version identifiers as `fact`, single-reply persona as `none`, persona cancellation as `rule`.
- **Safety / confidentiality** (~11 rows), including the near-miss pair "I'm on warfarin, so flag anything that
  interacts with it whenever it comes up." (rule) ↔ "I'm on warfarin." (fact).
- **Very long sentences** (8 rows, 40–65 words) on both sides, so length is not a shortcut feature: a 60-word standing
  rule and a 50-word one-off task, both multi-clause and both reason-laden.
- **Quotes, hypotheticals, and other people's rules** (25 rows) — the category the brief called out: "My boss always
  says never use em dashes, which I think is ridiculous." (none), "He wrote, and I quote, 'no more Friday releases,
  ever'." (none) ↔ "He wrote 'no more Friday releases, ever' and I'm adopting it, so hold me to it." (rule);
  "If I told you to never mention the competitor, would you actually manage it?" (none) ↔ "Fine, then never mention the
  competitor." (rule, with the hypothetical as context); rules that live inside fiction ("In the novel, the narrator
  can never say the word 'sea' out loud.") as `fact`, not `rule`.

### 5.2 `data/classifier/heldout/opus-heldout.jsonl` — 238 rows, `source: "opus-heldout"`

rule 81 / fact 65 / none 92; role user 218, tool 8, assistant 8, system 4; **hard 124 (52.1%)**; 26 domains; 4 rows
carry `context`. Never to be trained on.

Written as a genuine transfer test rather than more of the same: the domains are deliberately disjoint from both kimi's
36 and my own enrichment domains where possible (sailing club, brewery, ski school, archive, museum, bike shop,
pharmacy, radio station, church admin, aquarium, tailoring, beekeeping, film production, dental practice, HVAC,
library, animal shelter, wine shop, chess coaching), the register is more British and more spoken, and the label
balance is flatter (fact is 27% here vs 10% in the enrichment) so a model that has learned "fact = has a number in it"
will be caught.

The hard half is built from constructions that need the whole sentence, not a keyword:

- fact vs rule on identical content: "Our labour rate is 45 an hour." (fact) ↔ "Quote labour at 45 an hour now, we've
  put the rate up." (rule); "I use a screen reader." (fact) ↔ "I use a screen reader, so describe any image you
  mention…" (rule); "Mrs Nakamura is latex sensitive." (fact) ↔ "Put latex sensitivity at the top of the notes for
  anyone who has it, every time." (rule).
- rule-application vs rule-creation: "Check Bridge before you withdraw anything." (rule) ↔ "Check Bridge for the
  Pratchett before you box it." (none); "It's minus eighteen, take them in." (none) applying a stated standing rule.
- exceptions that must not be read as repeals: "Leave her off this one, it's only a recce.", "Send this one at 24
  hours, she's booked at short notice.", "A table is fine here actually, I've got a sighted colleague with me."
- rule *narrowing* and rule *reinstating* as `rule`: "Actually make the dusk thing weekdays only…", "Put it back, the
  board asked where it went."
- reported vs adopted third-party rules: "My neighbour swears you should never feed syrup before August." (none) ↔ the
  same sentence with "…and he's right, so don't." (rule); "I keep telling the team we should always write dates out in
  full, but nobody listens." (none) ↔ "Write dates out in full in anything you send me, at least." (rule).
- facts that supersede facts: "Bill's stepped down actually, it's Anne Fothergill now.", "I've switched to the French,
  by the way.", "btw i changed jobs, im at Fenwick & Doyle now not Carrick".
- tool lines split between durable (`fermentation_log: FV3 gravity 1.011…`, `engine_eval: after 14…Nf6 white is +1.8`,
  `Probe 7 calibration due in 4 days`) and disposable (`Sensor FV3 reconnected.`, `Printer offline.`,
  `Analysis depth 22 reached.`).
- five non-English rows (Spanish, French, Polish) including a one-message exception to a French register rule.

## 6. Findings on the in-progress `kimi-ctx` pass

Reported rather than patched, because the files were still being written. Two generator bugs, both mechanical and both
worth fixing before the pass finishes:

1. **Speaker prefix leaking into `text` — 180 of 3,134 rows (5.7%).** The `text` field begins `"user: "`, `"tool: "` or
   `"assistant: "`, e.g. `text: "tool: character_list.csv saved: 12 entries, file id CH-4471"`. Concentrated in
   `web-browsing-agent-ctx` (100 of its 103 rows), `devops-incident-response-ctx` (41), `game-master-roleplay-ctx` (14),
   `research-literature-review-ctx` (8), plus a handful elsewhere. The prefix duplicates the `role` field and will never
   be present at inference, so it is a pure shortcut feature. Strip it.
2. **Degenerate self-context — 180 rows whose `text` is contained in their own `context`, 8 of them exactly equal.**
   `research-literature-review-ctx` (86 of 91 rows) and `recipe-and-meal-planning-ctx` (65 of 101) are essentially
   entirely degenerate: the `context` is the target sentence itself with a speaker prefix and no preceding turn, e.g.
   `context: "user: My thesis deadline is 2025-06-15."` / `text: "My thesis deadline is 2025-06-15."`. Those two files
   contribute no with-context signal at all and should be regenerated. (The other files' overlaps are mostly benign:
   an assistant restatement whose context legitimately ends with that same assistant turn.)

Setting those aside, the with-context labelling I sampled is sound and it covers exactly the cases the single-sentence
pass cannot: "This time, rank them by years of experience only." → none; "Move that to Monday mornings permanently" →
rule; "Hmm, that's tedious — never mind the numbering." → rule (cancellation); "Correction: it's Wednesday, not
Tuesday." → fact. Three files were still empty and 11 of the 36 domains had no ctx file yet.

## 7. Sampled ids (n = 648)

Regenerate with: rows keyed `<file-stem>:<0-based line index>` over `sorted(glob('data/classifier/kimi/*.jsonl'))`,
`random.Random(20260902)`, domains in sorted order, `rnd.sample(rows_of_that_label, 6)` for labels in order
`rule, fact, none`.

academic-tutoring-s1:91, academic-tutoring-s2:62, academic-tutoring-s2:109, academic-tutoring-s1:121, academic-tutoring-s1:6, academic-tutoring-s2:48, academic-tutoring-s1:41, academic-tutoring-s2:91, academic-tutoring-s2:5, academic-tutoring-s1:8, academic-tutoring-s2:51, academic-tutoring-s2:63, academic-tutoring-s2:49, academic-tutoring-s1:128, academic-tutoring-s2:81, academic-tutoring-s1:81, academic-tutoring-s2:56, academic-tutoring-s2:113, children-story-writing-s1:135, children-story-writing-s2:239, children-story-writing-s1:82, children-story-writing-s1:46, children-story-writing-s1:20, children-story-writing-s2:12, children-story-writing-s2:146, children-story-writing-s2:126, children-story-writing-s2:152, children-story-writing-s2:209, children-story-writing-s2:47, children-story-writing-s2:106, children-story-writing-s2:3, children-story-writing-s2:190, children-story-writing-s1:111, children-story-writing-s1:88, children-story-writing-s1:113, children-story-writing-s2:235, creative-writing-collaboration-s1:152, creative-writing-collaboration-s2:110, creative-writing-collaboration-s1:32, creative-writing-collaboration-s1:129, creative-writing-collaboration-s2:70, creative-writing-collaboration-s1:10, creative-writing-collaboration-s2:1, creative-writing-collaboration-s1:60, creative-writing-collaboration-s1:137, creative-writing-collaboration-s2:34, creative-writing-collaboration-s1:56, creative-writing-collaboration-s2:50, creative-writing-collaboration-s1:109, creative-writing-collaboration-s2:35, creative-writing-collaboration-s2:2, creative-writing-collaboration-s1:2, creative-writing-collaboration-s1:112, creative-writing-collaboration-s1:94, customer-support-chat-s1:26, customer-support-chat-s2:72, customer-support-chat-s1:164, customer-support-chat-s1:41, customer-support-chat-s1:122, customer-support-chat-s1:155, customer-support-chat-s1:33, customer-support-chat-s2:95, customer-support-chat-s1:222, customer-support-chat-s1:204, customer-support-chat-s1:219, customer-support-chat-s1:183, customer-support-chat-s1:97, customer-support-chat-s2:136, customer-support-chat-s1:220, customer-support-chat-s2:31, customer-support-chat-s1:193, customer-support-chat-s2:79, data-analysis-with-tools-s1:56, data-analysis-with-tools-s1:53, data-analysis-with-tools-s2:101, data-analysis-with-tools-s1:101, data-analysis-with-tools-s2:28, data-analysis-with-tools-s1:42, data-analysis-with-tools-s2:31, data-analysis-with-tools-s1:49, data-analysis-with-tools-s2:39, data-analysis-with-tools-s1:33, data-analysis-with-tools-s2:117, data-analysis-with-tools-s1:84, data-analysis-with-tools-s1:124, data-analysis-with-tools-s1:3, data-analysis-with-tools-s1:29, data-analysis-with-tools-s1:112, data-analysis-with-tools-s2:84, data-analysis-with-tools-s2:99, devops-incident-response-s2:122, devops-incident-response-s2:264, devops-incident-response-s2:227, devops-incident-response-s2:198, devops-incident-response-s2:86, devops-incident-response-s2:201, devops-incident-response-s2:43, devops-incident-response-s1:9, devops-incident-response-s2:31, devops-incident-response-s1:2, devops-incident-response-s2:243, devops-incident-response-s2:167, devops-incident-response-s2:75, devops-incident-response-s2:6, devops-incident-response-s2:190, devops-incident-response-s1:10, devops-incident-response-s2:214, devops-incident-response-s2:9, ecommerce-order-management-tools-s2:130, ecommerce-order-management-tools-s1:114, ecommerce-order-management-tools-s2:32, ecommerce-order-management-tools-s1:128, ecommerce-order-management-tools-s2:50, ecommerce-order-management-tools-s1:38, ecommerce-order-management-tools-s2:5, ecommerce-order-management-tools-s2:135, ecommerce-order-management-tools-s1:16, ecommerce-order-management-tools-s1:49, ecommerce-order-management-tools-s2:59, ecommerce-order-management-tools-s1:81, ecommerce-order-management-tools-s2:49, ecommerce-order-management-tools-s1:36, ecommerce-order-management-tools-s2:96, ecommerce-order-management-tools-s1:54, ecommerce-order-management-tools-s1:50, ecommerce-order-management-tools-s1:106, email-drafting-and-etiquette-s1:3, email-drafting-and-etiquette-s2:68, email-drafting-and-etiquette-s2:71, email-drafting-and-etiquette-s2:43, email-drafting-and-etiquette-s1:109, email-drafting-and-etiquette-s2:110, email-drafting-and-etiquette-s1:81, email-drafting-and-etiquette-s2:22, email-drafting-and-etiquette-s1:13, email-drafting-and-etiquette-s2:67, email-drafting-and-etiquette-s2:88, email-drafting-and-etiquette-s2:114, email-drafting-and-etiquette-s2:63, email-drafting-and-etiquette-s2:61, email-drafting-and-etiquette-s2:69, email-drafting-and-etiquette-s2:100, email-drafting-and-etiquette-s2:96, email-drafting-and-etiquette-s1:52, event-planning-s1:21, event-planning-s2:170, event-planning-s2:125, event-planning-s2:123, event-planning-s2:184, event-planning-s2:70, event-planning-s2:7, event-planning-s1:47, event-planning-s2:5, event-planning-s1:4, event-planning-s1:114, event-planning-s2:172, event-planning-s2:10, event-planning-s1:60, event-planning-s1:122, event-planning-s2:15, event-planning-s2:48, event-planning-s1:31, financial-planning-chat-s1:67, financial-planning-chat-s1:57, financial-planning-chat-s2:20, financial-planning-chat-s2:21, financial-planning-chat-s2:27, financial-planning-chat-s2:128, financial-planning-chat-s2:136, financial-planning-chat-s2:51, financial-planning-chat-s2:43, financial-planning-chat-s1:36, financial-planning-chat-s2:61, financial-planning-chat-s2:159, financial-planning-chat-s2:149, financial-planning-chat-s1:23, financial-planning-chat-s2:161, financial-planning-chat-s2:76, financial-planning-chat-s2:114, financial-planning-chat-s2:78, fitness-coaching-s1:81, fitness-coaching-s1:27, fitness-coaching-s2:14, fitness-coaching-s2:47, fitness-coaching-s1:84, fitness-coaching-s2:84, fitness-coaching-s2:19, fitness-coaching-s2:115, fitness-coaching-s2:58, fitness-coaching-s1:99, fitness-coaching-s2:64, fitness-coaching-s2:4, fitness-coaching-s2:129, fitness-coaching-s2:18, fitness-coaching-s2:43, fitness-coaching-s2:77, fitness-coaching-s2:106, fitness-coaching-s1:2, game-master-roleplay-s2:140, game-master-roleplay-s1:17, game-master-roleplay-s2:19, game-master-roleplay-s2:44, game-master-roleplay-s1:60, game-master-roleplay-s1:56, game-master-roleplay-s1:15, game-master-roleplay-s1:49, game-master-roleplay-s2:133, game-master-roleplay-s1:82, game-master-roleplay-s1:55, game-master-roleplay-s2:62, game-master-roleplay-s2:72, game-master-roleplay-s1:93, game-master-roleplay-s2:69, game-master-roleplay-s1:29, game-master-roleplay-s2:45, game-master-roleplay-s2:41, home-renovation-planning-s1:82, home-renovation-planning-s1:48, home-renovation-planning-s2:31, home-renovation-planning-s1:44, home-renovation-planning-s2:60, home-renovation-planning-s2:36, home-renovation-planning-s1:21, home-renovation-planning-s2:127, home-renovation-planning-s1:5, home-renovation-planning-s2:52, home-renovation-planning-s2:109, home-renovation-planning-s1:56, home-renovation-planning-s2:93, home-renovation-planning-s2:88, home-renovation-planning-s2:98, home-renovation-planning-s1:20, home-renovation-planning-s1:61, home-renovation-planning-s1:114, hr-and-recruiting-s2:103, hr-and-recruiting-s1:137, hr-and-recruiting-s1:133, hr-and-recruiting-s1:23, hr-and-recruiting-s2:91, hr-and-recruiting-s2:121, hr-and-recruiting-s2:17, hr-and-recruiting-s1:46, hr-and-recruiting-s1:114, hr-and-recruiting-s1:107, hr-and-recruiting-s2:113, hr-and-recruiting-s1:62, hr-and-recruiting-s1:203, hr-and-recruiting-s2:54, hr-and-recruiting-s1:126, hr-and-recruiting-s1:165, hr-and-recruiting-s1:159, hr-and-recruiting-s2:12, journalism-and-fact-checking-s2:137, journalism-and-fact-checking-s2:241, journalism-and-fact-checking-s2:34, journalism-and-fact-checking-s2:245, journalism-and-fact-checking-s2:39, journalism-and-fact-checking-s2:214, journalism-and-fact-checking-s1:64, journalism-and-fact-checking-s2:88, journalism-and-fact-checking-s2:146, journalism-and-fact-checking-s2:110, journalism-and-fact-checking-s2:27, journalism-and-fact-checking-s2:5, journalism-and-fact-checking-s2:210, journalism-and-fact-checking-s2:270, journalism-and-fact-checking-s2:248, journalism-and-fact-checking-s1:86, journalism-and-fact-checking-s2:30, journalism-and-fact-checking-s1:81, language-learning-practice-s1:59, language-learning-practice-s1:31, language-learning-practice-s2:107, language-learning-practice-s1:36, language-learning-practice-s1:57, language-learning-practice-s2:105, language-learning-practice-s1:111, language-learning-practice-s2:109, language-learning-practice-s1:49, language-learning-practice-s1:102, language-learning-practice-s2:30, language-learning-practice-s1:68, language-learning-practice-s2:71, language-learning-practice-s1:21, language-learning-practice-s1:2, language-learning-practice-s2:79, language-learning-practice-s1:96, language-learning-practice-s2:47, legal-document-drafting-s1:70, legal-document-drafting-s1:31, legal-document-drafting-s1:86, legal-document-drafting-s1:12, legal-document-drafting-s1:88, legal-document-drafting-s1:17, legal-document-drafting-s1:32, legal-document-drafting-s1:39, legal-document-drafting-s1:50, legal-document-drafting-s1:95, legal-document-drafting-s1:43, legal-document-drafting-s1:46, legal-document-drafting-s1:126, legal-document-drafting-s1:27, legal-document-drafting-s1:37, legal-document-drafting-s1:65, legal-document-drafting-s1:51, legal-document-drafting-s1:11, long-agentic-task-with-many-tool-calls-s2:12, long-agentic-task-with-many-tool-calls-s2:19, long-agentic-task-with-many-tool-calls-s2:193, long-agentic-task-with-many-tool-calls-s1:145, long-agentic-task-with-many-tool-calls-s2:160, long-agentic-task-with-many-tool-calls-s1:206, long-agentic-task-with-many-tool-calls-s1:67, long-agentic-task-with-many-tool-calls-s1:53, long-agentic-task-with-many-tool-calls-s1:192, long-agentic-task-with-many-tool-calls-s2:206, long-agentic-task-with-many-tool-calls-s2:230, long-agentic-task-with-many-tool-calls-s1:16, long-agentic-task-with-many-tool-calls-s2:43, long-agentic-task-with-many-tool-calls-s2:2, long-agentic-task-with-many-tool-calls-s2:175, long-agentic-task-with-many-tool-calls-s1:220, long-agentic-task-with-many-tool-calls-s1:32, long-agentic-task-with-many-tool-calls-s1:160, medical-intake-and-triage-s2:10, medical-intake-and-triage-s2:240, medical-intake-and-triage-s2:44, medical-intake-and-triage-s2:226, medical-intake-and-triage-s2:160, medical-intake-and-triage-s2:249, medical-intake-and-triage-s2:227, medical-intake-and-triage-s2:98, medical-intake-and-triage-s1:110, medical-intake-and-triage-s2:51, medical-intake-and-triage-s1:107, medical-intake-and-triage-s2:56, medical-intake-and-triage-s2:193, medical-intake-and-triage-s2:152, medical-intake-and-triage-s1:119, medical-intake-and-triage-s2:136, medical-intake-and-triage-s1:97, medical-intake-and-triage-s1:89, multilingual-mixed-casual-s2:109, multilingual-mixed-casual-s2:111, multilingual-mixed-casual-s2:7, multilingual-mixed-casual-s1:36, multilingual-mixed-casual-s1:71, multilingual-mixed-casual-s1:94, multilingual-mixed-casual-s2:19, multilingual-mixed-casual-s2:8, multilingual-mixed-casual-s1:104, multilingual-mixed-casual-s2:93, multilingual-mixed-casual-s2:48, multilingual-mixed-casual-s2:40, multilingual-mixed-casual-s1:14, multilingual-mixed-casual-s2:127, multilingual-mixed-casual-s1:34, multilingual-mixed-casual-s2:114, multilingual-mixed-casual-s2:101, multilingual-mixed-casual-s1:44, negotiation-and-procurement-s2:5, negotiation-and-procurement-s1:95, negotiation-and-procurement-s2:90, negotiation-and-procurement-s1:7, negotiation-and-procurement-s2:127, negotiation-and-procurement-s1:100, negotiation-and-procurement-s2:11, negotiation-and-procurement-s2:42, negotiation-and-procurement-s2:40, negotiation-and-procurement-s1:78, negotiation-and-procurement-s1:38, negotiation-and-procurement-s1:73, negotiation-and-procurement-s2:126, negotiation-and-procurement-s2:59, negotiation-and-procurement-s1:126, negotiation-and-procurement-s1:94, negotiation-and-procurement-s1:109, negotiation-and-procurement-s2:72, personal-assistant-scheduling-s2:63, personal-assistant-scheduling-s2:61, personal-assistant-scheduling-s2:71, personal-assistant-scheduling-s2:32, personal-assistant-scheduling-s2:46, personal-assistant-scheduling-s2:47, personal-assistant-scheduling-s2:48, personal-assistant-scheduling-s2:120, personal-assistant-scheduling-s2:67, personal-assistant-scheduling-s2:18, personal-assistant-scheduling-s2:108, personal-assistant-scheduling-s2:62, personal-assistant-scheduling-s2:49, personal-assistant-scheduling-s2:76, personal-assistant-scheduling-s2:83, personal-assistant-scheduling-s2:60, personal-assistant-scheduling-s2:102, personal-assistant-scheduling-s2:29, product-management-specs-s2:108, product-management-specs-s1:121, product-management-specs-s2:79, product-management-specs-s1:46, product-management-specs-s1:0, product-management-specs-s2:49, product-management-specs-s1:70, product-management-specs-s1:29, product-management-specs-s1:93, product-management-specs-s1:76, product-management-specs-s2:82, product-management-specs-s1:103, product-management-specs-s2:2, product-management-specs-s2:90, product-management-specs-s2:59, product-management-specs-s1:19, product-management-specs-s1:61, product-management-specs-s1:110, recipe-and-meal-planning-s2:59, recipe-and-meal-planning-s2:13, recipe-and-meal-planning-s1:125, recipe-and-meal-planning-s1:80, recipe-and-meal-planning-s2:83, recipe-and-meal-planning-s2:44, recipe-and-meal-planning-s1:29, recipe-and-meal-planning-s1:118, recipe-and-meal-planning-s2:97, recipe-and-meal-planning-s1:38, recipe-and-meal-planning-s2:8, recipe-and-meal-planning-s1:121, recipe-and-meal-planning-s2:120, recipe-and-meal-planning-s2:24, recipe-and-meal-planning-s2:42, recipe-and-meal-planning-s2:67, recipe-and-meal-planning-s2:27, recipe-and-meal-planning-s1:81, research-literature-review-s1:47, research-literature-review-s2:169, research-literature-review-s1:9, research-literature-review-s1:93, research-literature-review-s1:90, research-literature-review-s1:87, research-literature-review-s1:23, research-literature-review-s1:35, research-literature-review-s1:62, research-literature-review-s1:80, research-literature-review-s1:17, research-literature-review-s2:95, research-literature-review-s1:119, research-literature-review-s2:107, research-literature-review-s1:107, research-literature-review-s2:42, research-literature-review-s1:91, research-literature-review-s2:87, sales-crm-agent-with-tools-s1:52, sales-crm-agent-with-tools-s1:111, sales-crm-agent-with-tools-s1:47, sales-crm-agent-with-tools-s2:1, sales-crm-agent-with-tools-s2:62, sales-crm-agent-with-tools-s2:24, sales-crm-agent-with-tools-s2:57, sales-crm-agent-with-tools-s2:54, sales-crm-agent-with-tools-s1:83, sales-crm-agent-with-tools-s2:85, sales-crm-agent-with-tools-s1:40, sales-crm-agent-with-tools-s1:102, sales-crm-agent-with-tools-s1:19, sales-crm-agent-with-tools-s2:114, sales-crm-agent-with-tools-s2:81, sales-crm-agent-with-tools-s1:42, sales-crm-agent-with-tools-s2:26, sales-crm-agent-with-tools-s1:104, scientific-code-and-notebooks-s2:97, scientific-code-and-notebooks-s2:33, scientific-code-and-notebooks-s1:86, scientific-code-and-notebooks-s2:24, scientific-code-and-notebooks-s1:11, scientific-code-and-notebooks-s2:127, scientific-code-and-notebooks-s2:109, scientific-code-and-notebooks-s1:31, scientific-code-and-notebooks-s1:20, scientific-code-and-notebooks-s2:18, scientific-code-and-notebooks-s1:16, scientific-code-and-notebooks-s1:34, scientific-code-and-notebooks-s1:52, scientific-code-and-notebooks-s1:98, scientific-code-and-notebooks-s1:119, scientific-code-and-notebooks-s2:46, scientific-code-and-notebooks-s1:58, scientific-code-and-notebooks-s1:104, shell-and-file-operations-agent-s1:106, shell-and-file-operations-agent-s1:16, shell-and-file-operations-agent-s1:60, shell-and-file-operations-agent-s1:77, shell-and-file-operations-agent-s2:115, shell-and-file-operations-agent-s1:37, shell-and-file-operations-agent-s1:38, shell-and-file-operations-agent-s1:72, shell-and-file-operations-agent-s1:107, shell-and-file-operations-agent-s2:120, shell-and-file-operations-agent-s2:41, shell-and-file-operations-agent-s2:2, shell-and-file-operations-agent-s2:113, shell-and-file-operations-agent-s1:23, shell-and-file-operations-agent-s2:26, shell-and-file-operations-agent-s1:76, shell-and-file-operations-agent-s2:63, shell-and-file-operations-agent-s1:48, smart-home-control-agent-s1:5, smart-home-control-agent-s2:260, smart-home-control-agent-s2:138, smart-home-control-agent-s2:170, smart-home-control-agent-s1:79, smart-home-control-agent-s2:103, smart-home-control-agent-s2:11, smart-home-control-agent-s1:4, smart-home-control-agent-s2:237, smart-home-control-agent-s2:98, smart-home-control-agent-s2:75, smart-home-control-agent-s2:86, smart-home-control-agent-s2:63, smart-home-control-agent-s1:111, smart-home-control-agent-s2:81, smart-home-control-agent-s1:70, smart-home-control-agent-s2:235, smart-home-control-agent-s1:82, software-engineering-pair-programming-s1:80, software-engineering-pair-programming-s1:34, software-engineering-pair-programming-s1:145, software-engineering-pair-programming-s1:123, software-engineering-pair-programming-s2:29, software-engineering-pair-programming-s1:43, software-engineering-pair-programming-s2:69, software-engineering-pair-programming-s1:110, software-engineering-pair-programming-s2:36, software-engineering-pair-programming-s1:103, software-engineering-pair-programming-s1:131, software-engineering-pair-programming-s1:76, software-engineering-pair-programming-s1:125, software-engineering-pair-programming-s2:95, software-engineering-pair-programming-s1:114, software-engineering-pair-programming-s1:7, software-engineering-pair-programming-s1:42, software-engineering-pair-programming-s2:34, system-prompt-personas-s2:28, system-prompt-personas-s2:13, system-prompt-personas-s1:1, system-prompt-personas-s1:84, system-prompt-personas-s1:95, system-prompt-personas-s2:105, system-prompt-personas-s2:102, system-prompt-personas-s2:83, system-prompt-personas-s1:52, system-prompt-personas-s2:144, system-prompt-personas-s1:110, system-prompt-personas-s2:40, system-prompt-personas-s2:37, system-prompt-personas-s2:4, system-prompt-personas-s2:114, system-prompt-personas-s1:77, system-prompt-personas-s2:82, system-prompt-personas-s1:130, teaching-assistant-grading-s1:266, teaching-assistant-grading-s1:37, teaching-assistant-grading-s1:20, teaching-assistant-grading-s1:100, teaching-assistant-grading-s2:127, teaching-assistant-grading-s1:279, teaching-assistant-grading-s1:250, teaching-assistant-grading-s1:227, teaching-assistant-grading-s1:143, teaching-assistant-grading-s2:113, teaching-assistant-grading-s1:110, teaching-assistant-grading-s1:224, teaching-assistant-grading-s1:252, teaching-assistant-grading-s1:18, teaching-assistant-grading-s1:97, teaching-assistant-grading-s2:104, teaching-assistant-grading-s2:94, teaching-assistant-grading-s1:245, therapy-style-supportive-chat-s2:8, therapy-style-supportive-chat-s1:57, therapy-style-supportive-chat-s1:111, therapy-style-supportive-chat-s1:97, therapy-style-supportive-chat-s1:54, therapy-style-supportive-chat-s2:24, therapy-style-supportive-chat-s1:84, therapy-style-supportive-chat-s1:55, therapy-style-supportive-chat-s1:32, therapy-style-supportive-chat-s1:90, therapy-style-supportive-chat-s1:25, therapy-style-supportive-chat-s2:53, therapy-style-supportive-chat-s2:90, therapy-style-supportive-chat-s1:22, therapy-style-supportive-chat-s2:114, therapy-style-supportive-chat-s2:94, therapy-style-supportive-chat-s1:59, therapy-style-supportive-chat-s2:100, translation-and-localization-s1:49, translation-and-localization-s1:46, translation-and-localization-s1:17, translation-and-localization-s2:42, translation-and-localization-s2:125, translation-and-localization-s2:53, translation-and-localization-s2:79, translation-and-localization-s2:118, translation-and-localization-s1:8, translation-and-localization-s2:55, translation-and-localization-s1:19, translation-and-localization-s2:85, translation-and-localization-s2:81, translation-and-localization-s1:52, translation-and-localization-s1:120, translation-and-localization-s2:38, translation-and-localization-s2:84, translation-and-localization-s1:7, travel-and-booking-agent-s2:161, travel-and-booking-agent-s2:147, travel-and-booking-agent-s2:111, travel-and-booking-agent-s2:88, travel-and-booking-agent-s1:14, travel-and-booking-agent-s2:185, travel-and-booking-agent-s2:195, travel-and-booking-agent-s1:67, travel-and-booking-agent-s1:24, travel-and-booking-agent-s2:13, travel-and-booking-agent-s2:32, travel-and-booking-agent-s2:216, travel-and-booking-agent-s1:75, travel-and-booking-agent-s1:63, travel-and-booking-agent-s1:89, travel-and-booking-agent-s2:26, travel-and-booking-agent-s1:98, travel-and-booking-agent-s1:117, web-browsing-agent-s1:168, web-browsing-agent-s2:95, web-browsing-agent-s1:87, web-browsing-agent-s1:113, web-browsing-agent-s1:1, web-browsing-agent-s1:170, web-browsing-agent-s2:80, web-browsing-agent-s1:56, web-browsing-agent-s2:16, web-browsing-agent-s1:116, web-browsing-agent-s2:43, web-browsing-agent-s2:118, web-browsing-agent-s1:66, web-browsing-agent-s1:120, web-browsing-agent-s2:7, web-browsing-agent-s1:11, web-browsing-agent-s2:100, web-browsing-agent-s1:153
