# Classifier data review — sol (2026-09-03)

## Outcome

I manually reviewed 738 stratified rows against `data/classifier/LABELS.md`: 648 rows from the stable single-sentence pass and 90 rows from the live context pass. Fourteen had an incorrect label (1.90%). The patch also removes corpus-hygiene failures that are not necessarily label mistakes: benchmark-taxonomy paraphrases, source-local duplicate clusters, malformed context targets, and contexts that disclose the target sentence.

The delivered artifacts are:

- `data/classifier/review/sol-patch.jsonl`: 516 unique `(source, text)` directives — 21 relabels and 495 drops.
- `data/classifier/sol-enrich.jsonl`: 421 training rows, including 160 deliberately paired one-off-imperative hard negatives and 160 similar-looking standing rules.
- `data/classifier/heldout/sol-heldout.jsonl`: 200 author-disjoint transfer rows; 141/200 (70.5%) are marked hard and none belongs in training.

I did not read any file under `data/bench/`, did not use an evaluation benchmark as a source, and did not launch a model, GPU process, or generation script. The new examples were written directly from ordinary work and conversation scenarios.

## Corpus inventory and sampling

The stable pass contained 72 filenames, of which 70 were nonempty: 10,812 valid JSONL rows across 36 domains. `legal-document-drafting-s2.jsonl` and `personal-assistant-scheduling-s1.jsonl` were empty.

The context directory was live while this review ran. I saw 36 distinct context filenames. At the final validation snapshot, all 36 paths existed, 28 were nonempty, and those readable files held 4,246 rows across 28 domains. The reviewed context supplement came from 30 domains that were populated at its sampling snapshot. This moving inventory is why the exact sampled IDs are recorded below rather than claiming the final snapshot can reproduce the sample from line counts alone.

For the stable pass, I sorted filenames, treated `L<n>` as the one-based physical JSONL line number, partitioned rows by `(domain, assigned_label)`, and sampled without replacement with `random.Random(20260903)`: six `fact`, six `none`, and six `rule` rows from every domain (36 × 18 = 648). For the context supplement I used seed `20260903 ^ 0xC7` and selected one row per assigned label in each of the 30 then-populated domains (90). The appendices list every ID.

## Label accuracy

Rates below are by the label originally assigned by kimi. A row dropped solely for leakage or duplication is not counted as a label error when its semantic label was otherwise correct.

| Assigned class | Reviewed | Errors | Error rate |
|---|---:|---:|---:|
| fact | 246 | 1 | 0.41% |
| none | 246 | 11 | 4.47% |
| rule | 246 | 2 | 0.81% |
| **all** | **738** | **14** | **1.90%** |

The stable-pass portion had 11/648 errors (1.70%): `fact` 1/216, `none` 10/216, `rule` 0/216. The context supplement had 3/90 errors (3.33%): `fact` 0/30, `none` 1/30, `rule` 2/30.

### Per-domain label error rate

The six domains with 18 reviewed rows lacked a populated context file at the supplement snapshot; the other domains have 21.

| Domain | Reviewed | Errors | Rate |
|---|---:|---:|---:|
| academic-tutoring | 21 | 1 | 4.76% |
| children-story-writing | 21 | 0 | 0% |
| creative-writing-collaboration | 21 | 1 | 4.76% |
| customer-support-chat | 21 | 0 | 0% |
| data-analysis-with-tools | 18 | 0 | 0% |
| devops-incident-response | 21 | 1 | 4.76% |
| ecommerce-order-management-tools | 18 | 0 | 0% |
| email-drafting-and-etiquette | 21 | 0 | 0% |
| event-planning | 18 | 0 | 0% |
| financial-planning-chat | 21 | 0 | 0% |
| fitness-coaching | 21 | 1 | 4.76% |
| game-master-roleplay | 21 | 0 | 0% |
| home-renovation-planning | 21 | 0 | 0% |
| hr-and-recruiting | 21 | 0 | 0% |
| journalism-and-fact-checking | 21 | 1 | 4.76% |
| language-learning-practice | 21 | 0 | 0% |
| legal-document-drafting | 21 | 0 | 0% |
| long-agentic-task-with-many-tool-calls | 21 | 0 | 0% |
| medical-intake-and-triage | 21 | 3 | 14.29% |
| multilingual-mixed-casual | 21 | 0 | 0% |
| negotiation-and-procurement | 18 | 0 | 0% |
| personal-assistant-scheduling | 21 | 0 | 0% |
| product-management-specs | 18 | 0 | 0% |
| recipe-and-meal-planning | 21 | 0 | 0% |
| research-literature-review | 21 | 1 | 4.76% |
| sales-crm-agent-with-tools | 21 | 0 | 0% |
| scientific-code-and-notebooks | 21 | 1 | 4.76% |
| shell-and-file-operations-agent | 21 | 0 | 0% |
| smart-home-control-agent | 21 | 0 | 0% |
| software-engineering-pair-programming | 21 | 1 | 4.76% |
| system-prompt-personas | 21 | 1 | 4.76% |
| teaching-assistant-grading | 21 | 1 | 4.76% |
| therapy-style-supportive-chat | 21 | 1 | 4.76% |
| translation-and-localization | 18 | 0 | 0% |
| travel-and-booking-agent | 21 | 0 | 0% |
| web-browsing-agent | 21 | 0 | 0% |

### Sampled label errors

| ID | Original → corrected | Why |
|---|---|---|
| `academic-tutoring-s1.jsonl:L99` | fact → none | “The chemical symbol for gold is Au.” is generic tool-provided knowledge, not conversation state that must survive. |
| `devops-incident-response-s2.jsonl:L159` | none → fact | The two MTTR values are computed incident facts needed in a later postmortem. |
| `fitness-coaching-s1.jsonl:L7` | none → fact | A knee acting up today affects later workout choices even though the prose is casual. |
| `journalism-and-fact-checking-s2.jsonl:L39` | none → fact | A postponed hearing is a durable event-state update. |
| `medical-intake-and-triage-s1.jsonl:L64` | none → fact | Current dizziness must survive later triage turns. |
| `medical-intake-and-triage-s1.jsonl:L74` | none → fact | The cut's cause and timing remain relevant in later wound-triage turns. |
| `medical-intake-and-triage-s2.jsonl:L158` | none → fact | The records scanner's recurring failure is a session-relevant world state. |
| `research-literature-review-s2.jsonl:L9` | none → fact | The user's assessment that the theoretical framework is weak should survive later revisions. |
| `scientific-code-and-notebooks-s2.jsonl:L44` | none → fact | A kernel restart and cleared variables directly constrain subsequent notebook actions. |
| `system-prompt-personas-s2.jsonl:L141` | none → fact | The logged incident timestamp is durable session state, not filler. |
| `teaching-assistant-grading-s2.jsonl:L101` | none → fact | Losing the annotations on batch two is durable workflow state. |
| `creative-writing-collaboration-ctx.jsonl:L8` | none → fact | “The second one is gorgeous — let's go with that.” commits a creative decision. |
| `software-engineering-pair-programming-ctx.jsonl:L81` | rule → none | “This improves code readability.” is rationale for a preceding rule, not itself an instruction. |
| `therapy-style-supportive-chat-ctx.jsonl:L104` | rule → none | “No details about the accident, just him.” is scoped to the current request. |

The patch contains seven additional relabels found during the corpus-wide hygiene pass: third-party rules mislabeled as `rule`, additional clinical and newsroom state mislabeled as `none`, and an assistant recap containing medication/lab facts. Together with the 14 sampled errors, that yields 21 relabel directives.

## Systematic findings

1. **`none` under-retains live session state.** Eleven of the fourteen sampled errors were originally `none`. Symptoms, a kernel reset, moved or postponed events, lost annotations, computed incident metrics, and an editorial assessment were treated as disposable because they were current, casual, or embedded in assistant/tool prose. The specification asks whether later turns need the information, not whether it is permanent in the everyday sense.

2. **Third-party rules need an adoption test.** Sentences such as “The customer asked that we never mention competitor names...” and “The publisher's style guide says no Oxford commas” describe somebody else's rule. Unless the user adopts it as an instruction to this assistant, they are `none`, not `rule`. The sample itself did not happen to include those two rows; the broader pass found and corrected them.

3. **Context helps, but the target still needs its own speech act.** A choice (“let's go with that”) becomes a durable `fact`; explanatory prose does not become a `rule` merely because it follows one; and a current-reply constraint does not acquire standing scope from nearby discussion.

4. **No sampled kimi-wide “imperative ⇒ rule” bias was observed.** One-off commands in the kimi sample were generally labeled `none` correctly. The measured failure is in the interim classifier, not obviously in kimi's sampled labels. I therefore targeted the training decision boundary directly with 160 adjacent pairs: a one-off imperative followed by a lexically similar standing rule.

5. **Tool lines need a relevance distinction.** Unique identifiers, computed incident values, and state changes are `fact`; routine telemetry/progress and generic reference knowledge are `none`. Role alone cannot decide the label.

6. **Benchmark-taxonomy paraphrase is widespread enough to require removal.** I conservatively marked 344 unique keys for removal. Patterns include all-lowercase/title/sentence casing; exact numbers of sentences, bullets, lines, words, or characters; fixed openings/endings/sign-offs; P.S. requests; forbidden/required words or phrases; and mandated bold, italics, headings, markdown, or bullets. Examples include “As agreed, my replies will stay in lowercase,” “Add a P.S. to this one...,” and “Summarize every chapter ... in exactly five bullet points.” These rows may have semantically correct labels, but their instruction shape mirrors the forbidden evaluation taxonomy. I found no `<<title>>` token and no double-quote-wrapping directive in the reviewed stable corpus.

7. **Exact and near duplicates would overweight synthetic phrasing.** In the stable pass, raw text had 74 duplicate groups covering 202 rows (128 excess rows; maximum multiplicity 15). Within identical `source` values there were 45 groups covering 125 rows (80 excess; maximum 5). Case/punctuation-normalized text had 77 groups covering 222 rows (145 excess; maximum 15). Repeated casual fillers included “ok cool” 15 times and “ok cool thanks” 9 times. The patch drops all 45 source-local duplicate keys; because the patch key is `(source, text)`, that conservatively removes every member of each cluster rather than selecting an indistinguishable keeper.

8. **The live context pass has structural generation defects.** The patch drops 71 targets that redundantly begin with `user:`, `assistant:`, or `tool:` even though `role` already encodes the speaker, plus 35 rows whose context contains the exact target sentence. Both defects give the classifier artifacts unavailable at real write time. The live files also changed population while being reviewed, so the snapshot counts above should not be treated as final generator totals.

## Patch accounting

All 516 patch keys are unique and matched the readable corpus at final validation. The 362 stable-pass directives comprise 18 relabels and 344 drops; because of duplicates, they currently affect 442 physical rows. The 154 context-pass directives comprise 3 relabels and 151 drops and currently affect 156 physical rows.

The 495 drop directives break down as:

- 344 benchmark-taxonomy or benchmark-like phrasing keys;
- 45 source-local exact-duplicate keys;
- 71 malformed, role-prefixed context targets;
- 35 targets copied verbatim into their own context.

## Enrichment

`sol-enrich.jsonl` contains 421 new, manually written training rows across 37 domains. Label counts are 211 `none`, 190 `rule`, and 20 `fact`; role counts are 394 user, 17 assistant, 6 tool, and 4 system. All 421 are marked hard, 16 include genuine preceding context, and there are no exact duplicate texts.

The first 320 rows are 160 adjacent contrast pairs. Each pair puts a one-off task (`none`) beside a similar standing instruction (`rule`) across journalism, email, code, DevOps, research, scheduling, shopping, legal, health, teaching, home, travel, finance, support, creative work, localization, and other domains. They vary directness, politeness, length, ellipsis, and follow-up wording so the useful feature is future scope rather than imperative mood.

The remaining 101 rows exercise under-produced boundaries: long tool-heavy agent sessions; tool identifiers versus disposable telemetry; assistant restatements versus ordinary prose; rule cancellation and replacement; “this time/this reply only” scope; fact corrections; multilingual, slangy, and typo-heavy messages; system personas; safety and confidentiality rules; long compound sentences; and rule-shaped quotations, hypotheticals, organizational-policy descriptions, and somebody else's preferences. Exact text overlap with the current kimi corpus is zero.

## Held-out transfer set

`sol-heldout.jsonl` contains exactly 200 rows from 34 domains, all with `source: "sol-heldout"`. It is author-disjoint from kimi and must not be included in training. Label counts are 89 `none`, 68 `rule`, and 43 `fact`; role counts are 132 user, 32 system, 29 tool, and 7 assistant. There are 141 hard rows (76 `none`, 50 `rule`, 15 `fact`), or 70.5%.

The held-out texts have no exact duplicates internally, no exact overlap with `sol-enrich.jsonl`, and no exact overlap with the readable kimi corpus. They independently cover one-off-versus-standing scope, third-party and quoted rules, tool state, corrections, persona/safety boundaries, and natural informal wording without copying the enrichment pairs.

## Appendix A — stable-pass sample IDs (648)

Each line is one domain; labels shown are the original kimi strata.

