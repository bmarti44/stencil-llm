# fable-scope-validation — author-disjoint scope slice (2026-09-03)

File: `data/classifier/heldout/fable-scope-validation.jsonl` (292 rows, source `fable-scope-validation`).
Written by hand by fable against `data/classifier/LABELS.md` v2.1 only; no training, review, enrichment
or benchmark file was opened. Purpose: Opus scope-pass finding S6 — training scope signals are
template-concentrated, so this slice phrases every scope with unusual surface forms.

## Counts

| label | rows | share |
|---|---|---|
| rule | 103 | 35.3% |
| fact | 69 | 23.6% |
| none | 120 | 41.1% |

- hard: 178 / 292 (61.0%)
- roles: user 262, assistant 12, tool 16, system 2
- rows with `context` (string, speaker-prefixed): 11
- domains: 44 distinct (writing 33, chit-chat 46, coding 19, devops 15, translation 12, finance 11, email 10, ...)
- no two rows share a 4-word opening (checked mechanically, lowercase alphanumeric tokens); all rows parse as JSON.

## Coverage by scope phenomenon

- rule / task-scoped without scope words or training verbs: 38 (declaratives, verbless fragments, house style)
- rule / conversation-scoped without always/never/from now on: 25 (preferences with reasons, complaints, needs)
- rule / open expiry ("for now", "until the audit is over", "while X is out"): 10
- rule / sub-unit in progress ("for this section", "in the intro only", "verse two"): 9
- rule / change or cancel an earlier rule (with context): 7
- rule / mixed request + constraint (constraint clause wins): 7
- rule / persona, assistant commitments, system: 7
- fact: identifiers, dates, decisions, corrections, states, 7 tool lines and 2 assistant restatements
- none / single-reply constraints without the usual markers: 26
- none / continuations that are requests ("Okay, next paragraph.", "Same again for chapter two."): 13
- none / one-off tasks and questions: 12
- none / quoted, reported, hypothetical rules not adopted: 18
- none / meta, confirmation questions, chit-chat, finished sub-unit commentary: 33
- none / assistant prose: 8; none / transient tool output: 10

## Deliberate contrast pairs

"I hate emojis." (rule) vs "I used to hate emojis but I've come round." (none); "Enough with the disclaimers."
(rule) vs "Drop the caveats from that reply." (none); "No meat in anything you suggest for me." (rule) vs "I'm
vegetarian, by the way." (fact); "In the intro only, address the reader as 'you'." (rule) vs "Present tense was
right for that paragraph you just did." (none); "Spanish is easier for me than English." (rule) vs "Could you
answer that in French? He's French." (none).
