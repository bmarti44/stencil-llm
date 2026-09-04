# kimi SCOPE pass review — sol (2026-09-03)

## Method

Reviewed data/classifier/LABELS.md v2 before adjudication. The source pass contains 4,954 rows in 40 files. I used seed 20260903 and ranked each row by SHA-256 of seed|basename|label|1-based-line; for every file I took the first five rows in each of rule, fact, and none. I then judged all 600 sampled rows by hand. This is exactly 15 rows per file and five per class per file.

No model or GPU process was launched. The review was foreground/CPU-only, and no evaluation-benchmark directory was read.

The source files have no unique row-id field, and source repeats within each file. Accordingly, the auditable row IDs below are basename:L<1-based line>.

## Label error rates

Label errors exclude hygiene-only drops. Overall: **19/600 = 3.17%**.

| Original class | Errors | Rate |
|---|---:|---:|
| rule | 9/200 | 4.50% |
| fact | 4/200 | 2.00% |
| none | 6/200 | 3.00% |

Per file (each class denominator is 5; overall denominator is 15):

| File | rule | fact | none | Overall |
|---|---:|---:|---:|---:|
| academic-tutoring-scope.jsonl | 0/5 | 0/5 | 0/5 | 0/15 (0.00%) |
| children-story-writing-scope.jsonl | 1/5 | 0/5 | 0/5 | 1/15 (6.67%) |
| creative-writing-collaboration-scope.jsonl | 0/5 | 0/5 | 0/5 | 0/15 (0.00%) |
| customer-support-chat-scope.jsonl | 0/5 | 1/5 | 0/5 | 1/15 (6.67%) |
| data-analysis-with-tools-scope.jsonl | 1/5 | 0/5 | 0/5 | 1/15 (6.67%) |
| devops-incident-response-scope.jsonl | 1/5 | 0/5 | 0/5 | 1/15 (6.67%) |
| ecommerce-order-management-tools-scope.jsonl | 0/5 | 0/5 | 0/5 | 0/15 (0.00%) |
| email-drafting-and-etiquette-scope.jsonl | 0/5 | 0/5 | 0/5 | 0/15 (0.00%) |
| event-planning-scope.jsonl | 0/5 | 1/5 | 0/5 | 1/15 (6.67%) |
| financial-planning-chat-scope.jsonl | 1/5 | 0/5 | 0/5 | 1/15 (6.67%) |
| fitness-coaching-scope.jsonl | 1/5 | 0/5 | 0/5 | 1/15 (6.67%) |
| game-master-roleplay-scope.jsonl | 1/5 | 0/5 | 0/5 | 1/15 (6.67%) |
| home-renovation-planning-scope.jsonl | 0/5 | 0/5 | 0/5 | 0/15 (0.00%) |
| hr-and-recruiting-scope.jsonl | 1/5 | 0/5 | 0/5 | 1/15 (6.67%) |
| journalism-and-fact-checking-scope.jsonl | 0/5 | 0/5 | 0/5 | 0/15 (0.00%) |
| language-learning-practice-scope.jsonl | 0/5 | 0/5 | 0/5 | 0/15 (0.00%) |
| legal-document-drafting-scope.jsonl | 0/5 | 0/5 | 1/5 | 1/15 (6.67%) |
| long-agentic-task-with-many-tool-calls-scope.jsonl | 0/5 | 0/5 | 0/5 | 0/15 (0.00%) |
| medical-intake-and-triage-scope.jsonl | 1/5 | 0/5 | 0/5 | 1/15 (6.67%) |
| multilingual-mixed-casual-scope.jsonl | 0/5 | 0/5 | 0/5 | 0/15 (0.00%) |
| negotiation-and-procurement-scope.jsonl | 0/5 | 0/5 | 0/5 | 0/15 (0.00%) |
| newsletter-and-blog-writing-scope.jsonl | 0/5 | 0/5 | 0/5 | 0/15 (0.00%) |
| personal-assistant-scheduling-scope.jsonl | 0/5 | 0/5 | 2/5 | 2/15 (13.33%) |
| poetry-and-lyrics-scope.jsonl | 0/5 | 0/5 | 1/5 | 1/15 (6.67%) |
| product-management-specs-scope.jsonl | 1/5 | 0/5 | 0/5 | 1/15 (6.67%) |
| recipe-and-meal-planning-scope.jsonl | 0/5 | 0/5 | 0/5 | 0/15 (0.00%) |
| research-literature-review-scope.jsonl | 0/5 | 0/5 | 1/5 | 1/15 (6.67%) |
| sales-crm-agent-with-tools-scope.jsonl | 0/5 | 0/5 | 0/5 | 0/15 (0.00%) |
| scientific-code-and-notebooks-scope.jsonl | 0/5 | 0/5 | 0/5 | 0/15 (0.00%) |
| shell-and-file-operations-agent-scope.jsonl | 0/5 | 2/5 | 0/5 | 2/15 (13.33%) |
| slide-deck-and-report-writing-scope.jsonl | 0/5 | 0/5 | 0/5 | 0/15 (0.00%) |
| smart-home-control-agent-scope.jsonl | 0/5 | 0/5 | 0/5 | 0/15 (0.00%) |
| software-engineering-pair-programming-scope.jsonl | 0/5 | 0/5 | 0/5 | 0/15 (0.00%) |
| system-prompt-personas-scope.jsonl | 0/5 | 0/5 | 0/5 | 0/15 (0.00%) |
| teaching-assistant-grading-scope.jsonl | 0/5 | 0/5 | 0/5 | 0/15 (0.00%) |
| technical-documentation-scope.jsonl | 0/5 | 0/5 | 0/5 | 0/15 (0.00%) |
| therapy-style-supportive-chat-scope.jsonl | 0/5 | 0/5 | 0/5 | 0/15 (0.00%) |
| translation-and-localization-scope.jsonl | 0/5 | 0/5 | 0/5 | 0/15 (0.00%) |
| travel-and-booking-agent-scope.jsonl | 0/5 | 0/5 | 1/5 | 1/15 (6.67%) |
| web-browsing-agent-scope.jsonl | 0/5 | 0/5 | 0/5 | 0/15 (0.00%) |

## Label findings and examples

- **One-off task plus an embedded constraint is still none.** Nine sampled rule rows were complete work requests rather than constraints governing later replies. Examples: data-analysis-with-tools-scope.jsonl:L54 (“Summarize this in under 100 words”), children-story-writing-scope.jsonl:L4 (“Write the story in second person…”), and devops-incident-response-scope.jsonl:L36 (“Write the Slack update as plain text, no links”). I also reviewed the anchored Summarize… pattern across the whole pass and patched every exact source/text instance that survived hygiene drops.
- **Artifact scope is not reply scope.** legal-document-drafting-scope.jsonl:L6 (“Just for this section…”), personal-assistant-scheduling-scope.jsonl:L75 (“For this email only…”), and poetry-and-lyrics-scope.jsonl:L79 (“Only for this stanza…”) were none but are rule: the constraint remains binding if that section/email/stanza is revised later.
- **“For now” usually persists until changed.** personal-assistant-scheduling-scope.jsonl:L80 and research-literature-review-scope.jsonl:L43 were changed to rule. Corpus-wide exact matches were inspected individually; immediate actions such as “For now, just list the overdue shipments” stayed none.
- **Facts cannot contain an operative instruction.** customer-support-chat-scope.jsonl:L89 (“treat them as VIP”) and shell-and-file-operations-agent-scope.jsonl:L83 (“avoid restarts then”) were fact but are rule. Four such errors appeared in the sample.
- **System instructions count.** travel-and-booking-agent-scope.jsonl:L76 is a system persona/instruction and therefore rule, not none. The full-pass role audit found the same issue in seven other You are … system rows.
- **Explicitly single-reply constraints were handled correctly.** The seeded sample contained many this answer, this reply, and this message cases labeled none; none was incorrectly labeled rule. A full-pass scan of rule rows found no exact single-reply-scope false positives.
- **No sampled fact was mislabeled rule.** Declarative artifact policies such as “The report should…” are constraints and correctly remain rule; durable names, dates, identifiers, and recorded decisions remain fact.

## Context-list check

Twelve corpus rows use a JSON list for context: four in data-analysis-with-tools, six in sales-crm-agent-with-tools, and two in system-prompt-personas. I inspected all twelve after joining their elements in trainer order. Each context remains coherent and each associated rule label still makes sense; no context-list patch was needed.

## Hygiene findings

The sample had **20/600 = 3.33%** hygiene drops, separate from the label-error numerator.

- **Benchmark-like markers:** dropped 20 angle-bracket title/heading prompts, four exact-N-bullet prompts, one P.S. prompt, one exact “in all lowercase” prompt, and one output-in-double-quotes prompt. Plain-language constraints without those exact marker phrasings were retained. No literal <<title>> occurred.
- **Exact duplicates:** byte-identical text grouping found 39 duplicate groups covering 111 physical rows (72 redundant occurrences before overlap with other drops). After marker/template overlaps, the patch contains 67 exact-duplicate drop keys and retains one canonical non-dropped occurrence where the (source,text) key permits it.
- **Near duplicates and cyclic templates:** a punctuation-normalized similarity candidate sweep (threshold 0.88), followed by hand inspection, exposed a repeated 19-slot cycle at research-literature-review-scope.jsonl:L140-L303 and a repeated recipe/cookbook/inventory/meal-plan tail at recipe-and-meal-planning-scope.jsonl:L285-L360. Those blocks are dropped (164 and 76 physical rows). The sampled sales-crm-agent-with-tools British-spelling near-duplicate at L207 is also dropped, retaining L105.
- **Templated openings:** a three-/five-word opening census found 119 From now on…, 81 Just this once…, 74 For this message…, and 50 Now extend the… openings. These are a distributional warning, but I did not blanket-drop semantically distinct plain-language rows because those scope cues are part of the intended v2 boundary. Exact duplicates and the two cyclic blocks were removed.
- **Malformed units:** eight mixed multi-sentence or embedded multi-speaker rows were dropped, including the sampled slide-deck-and-report-writing-scope.jsonl:L22. A sentence classifier should not assign one label to both a task sentence and a separate constraint or to several speaker turns.

## Patch summary

data/classifier/review/scope-pass-sol-patch.jsonl contains **394 exact (source,text) patch keys**: **54 relabels** and **340 drops**. Because four keys match duplicate physical rows within one source, the patch affects 398 physical rows (54 relabels and 344 drops). Relabel transitions are:

- 28 none → rule
- 19 rule → none
- 6 fact → rule
- 1 none → fact

Every patch entry uses only source, text, one of new_label/drop, and a reason.

## Sample IDs

Five IDs per class per file; line order below is ascending for readability, not selection order.

| File | rule IDs | fact IDs | none IDs |
|---|---|---|---|
| academic-tutoring-scope.jsonl | L7, L26, L51, L138, L210 | L19, L24, L52, L83, L107 | L22, L37, L50, L157, L208 |
| children-story-writing-scope.jsonl | L1, L4, L15, L22, L32 | L35, L40, L43, L46, L47 | L50, L51, L54, L57, L77 |
| creative-writing-collaboration-scope.jsonl | L2, L9, L10, L23, L25 | L41, L45, L47, L52, L53 | L67, L84, L89, L92, L95 |
| customer-support-chat-scope.jsonl | L5, L12, L37, L64, L67 | L3, L30, L50, L59, L89 | L8, L23, L46, L63, L65 |
| data-analysis-with-tools-scope.jsonl | L13, L32, L53, L54, L63 | L12, L18, L23, L48, L85 | L30, L51, L58, L67, L84 |
| devops-incident-response-scope.jsonl | L13, L18, L27, L31, L36 | L41, L45, L47, L48, L50 | L65, L68, L77, L79, L85 |
| ecommerce-order-management-tools-scope.jsonl | L14, L15, L59, L63, L68 | L6, L29, L62, L78, L89 | L5, L7, L60, L64, L69 |
| email-drafting-and-etiquette-scope.jsonl | L10, L26, L27, L33, L36 | L42, L45, L46, L47, L49 | L56, L64, L85, L87, L91 |
| event-planning-scope.jsonl | L2, L18, L21, L31, L91 | L22, L45, L60, L62, L99 | L17, L25, L29, L61, L97 |
| financial-planning-chat-scope.jsonl | L3, L47, L50, L57, L68 | L21, L26, L51, L76, L87 | L41, L45, L69, L78, L91 |
| fitness-coaching-scope.jsonl | L4, L9, L20, L31, L40 | L42, L44, L47, L48, L49 | L56, L57, L59, L72, L73 |
| game-master-roleplay-scope.jsonl | L18, L22, L39, L48, L72 | L16, L37, L41, L50, L91 | L11, L29, L63, L66, L73 |
| home-renovation-planning-scope.jsonl | L28, L32, L59, L69, L72 | L12, L54, L58, L89, L100 | L52, L60, L73, L88, L97 |
| hr-and-recruiting-scope.jsonl | L4, L12, L18, L21, L30 | L45, L48, L51, L52, L53 | L65, L71, L74, L83, L87 |
| journalism-and-fact-checking-scope.jsonl | L11, L83, L122, L180, L253 | L18, L23, L24, L249, L279 | L43, L117, L217, L222, L230 |
| language-learning-practice-scope.jsonl | L2, L4, L15, L23, L31 | L43, L44, L46, L53, L54 | L57, L62, L77, L84, L87 |
| legal-document-drafting-scope.jsonl | L25, L54, L57, L67, L70 | L7, L47, L63, L76, L79 | L6, L9, L17, L33, L74 |
| long-agentic-task-with-many-tool-calls-scope.jsonl | L19, L48, L62, L69, L79 | L14, L22, L35, L64, L71 | L4, L34, L38, L50, L94 |
| medical-intake-and-triage-scope.jsonl | L1, L5, L10, L35, L38 | L17, L31, L43, L67, L71 | L18, L45, L55, L61, L66 |
| multilingual-mixed-casual-scope.jsonl | L7, L10, L19, L27, L39 | L44, L45, L48, L49, L54 | L56, L68, L79, L80, L87 |
| negotiation-and-procurement-scope.jsonl | L6, L72, L81, L94, L97 | L17, L26, L31, L41, L77 | L8, L28, L38, L40, L52 |
| newsletter-and-blog-writing-scope.jsonl | L11, L14, L61, L62, L73 | L16, L20, L22, L26, L29 | L34, L44, L88, L92, L93 |
| personal-assistant-scheduling-scope.jsonl | L2, L3, L7, L18, L38 | L41, L43, L46, L53, L54 | L55, L75, L80, L87, L92 |
| poetry-and-lyrics-scope.jsonl | L9, L21, L28, L30, L32 | L41, L42, L43, L45, L50 | L56, L64, L67, L73, L79 |
| product-management-specs-scope.jsonl | L2, L14, L64, L82, L83 | L21, L35, L66, L76, L85 | L20, L29, L33, L68, L78 |
| recipe-and-meal-planning-scope.jsonl | L13, L169, L261, L320, L324 | L177, L223, L256, L287, L305 | L5, L66, L119, L204, L280 |
| research-literature-review-scope.jsonl | L36, L222, L231, L265, L300 | L16, L27, L96, L188, L230 | L43, L156, L218, L251, L258 |
| sales-crm-agent-with-tools-scope.jsonl | L41, L105, L207, L231, L279 | L97, L104, L222, L246, L274 | L9, L58, L153, L165, L168 |
| scientific-code-and-notebooks-scope.jsonl | L9, L21, L28, L31, L37 | L43, L44, L48, L49, L50 | L56, L66, L75, L82, L85 |
| shell-and-file-operations-agent-scope.jsonl | L2, L10, L33, L35, L42 | L80, L83, L87, L89, L91 | L57, L63, L67, L73, L78 |
| slide-deck-and-report-writing-scope.jsonl | L13, L15, L16, L22, L23 | L43, L47, L49, L50, L52 | L55, L67, L73, L79, L81 |
| smart-home-control-agent-scope.jsonl | L6, L8, L18, L26, L39 | L43, L46, L49, L53, L55 | L63, L68, L69, L74, L85 |
| software-engineering-pair-programming-scope.jsonl | L6, L25, L27, L32, L40 | L41, L45, L46, L49, L52 | L58, L63, L83, L89, L90 |
| system-prompt-personas-scope.jsonl | L1, L14, L22, L29, L30 | L41, L43, L44, L50, L51 | L69, L75, L77, L87, L88 |
| teaching-assistant-grading-scope.jsonl | L4, L23, L24, L26, L31 | L42, L44, L48, L53, L54 | L55, L69, L72, L81, L84 |
| technical-documentation-scope.jsonl | L54, L140, L189, L243, L271 | L82, L117, L274, L291, L295 | L133, L232, L254, L273, L277 |
| therapy-style-supportive-chat-scope.jsonl | L3, L7, L9, L16, L20 | L43, L44, L45, L51, L55 | L59, L67, L68, L90, L95 |
| translation-and-localization-scope.jsonl | L4, L14, L21, L31, L91 | L19, L29, L35, L46, L69 | L12, L15, L54, L82, L87 |
| travel-and-booking-agent-scope.jsonl | L25, L28, L36, L38, L39 | L41, L44, L45, L49, L50 | L62, L64, L76, L81, L87 |
| web-browsing-agent-scope.jsonl | L7, L15, L28, L29, L33 | L44, L45, L49, L51, L53 | L60, L68, L71, L72, L74 |
