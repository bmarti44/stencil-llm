# Spec-v2 relabel review — sol

Reviewed all 461 proposed `new_label` entries in `data/classifier/review/scope-v2-patch.unreviewed.jsonl` by hand against `data/classifier/LABELS.md` v2. Note-only rows were ignored.

## Counts

- Proposed flips kept: **105**
- Proposed flips rejected: **356**
- Additional missed flips found in existing `none` data: **26**
- Total approved entries written to `data/classifier/review/scope-v2-sol.jsonl`: **131**

The decision boundary was persistence: a conversation/session rule or a constraint that remains binding while the same artifact or task is revised was kept. A request merely asking the assistant to perform one piece of work, a current-answer exception, a fact, and assistant prose were rejected.

## Example rejections

1. `Just for this one, write it in Python so I can paste it into the notebook.` — Explicitly limited to the current answer.
2. `Keep this one short.` — “This one” scopes brevity to the immediate response.
3. `Ha, do the butler voice for this answer only.` — Explicit single-answer persona exception.
4. `explain it simply this time` — “This time” makes it a one-reply explanation request.
5. `Can you use a couple of em dashes in this paragraph just to see how it reads?` — One experimental edit pass, not a persistent constraint.
6. `Write to him about the delay, apologetic but not grovelling.` — One-off request to write a letter.
7. `Patch the typo in the migration warning and leave the rest alone.` — One targeted code edit.
8. `Make it quick, I only have a minute right now.` — Immediate time pressure on one response.
9. `Compare LVP, tile, and hardwood for us.` — One-off comparison request.
10. `Tool, look up the price for item 4482.` — One-off lookup request.
11. `assistant: Use runbook KF-114, the one titled Consumer Lag Remediation v3.` — Assistant prose, not a user rule.
12. `Candidate ID 88231 asked to be called "Sam", but that's just for this one call.` — Assistant-authored transient fact.
13. `Bookmark that URL—we'll reference it throughout this project.` — Bookmarking is a one-off action; the latter clause is a fact about intended use.
14. `Draft the shipping delay banner text, max 15 words.` — A single work request with an embedded output limit.
15. `Rewrite this rejection email so it sounds less robotic, thanks.` — One-off revision request.
16. `Summarize this witness statement in five bullet points for the morning meeting.` — One-off summarization request.
17. `Turn this bullet list of comments into full sentences.` — One-off format-conversion request.
18. `Grade this essay for content only, ignore spelling.` — One-off grading request, not an ongoing grading policy.
19. `Marinate the tofu for at least four hours for the best texture.` — Assistant-authored recipe prose.
20. `Change the dragon in this story into a shy salamander.` — One-off story revision rather than a continuing writing constraint.

## Missed existing `none` rows approved under v2

These exact `(source, text)` pairs were absent from the proposed patch and were added to the sol approval file:

- `kimi-k3-ctx:academic-tutoring:5005` — `Actually, just for this explanation, avoid the mathematical formulas—use only analogies.`
- `kimi-k3-ctx:academic-tutoring:5005` — `For this explanation only, avoid the economic terminology and use plain language.`
- `kimi-k3-ctx:creative-writing-collaboration:5004` — `For this intro only, mimic a hardboiled 1940s voice.`
- `kimi-k3-ctx:devops-incident-response:5007` — `For the next ten minutes only, answer everything in single sentences.`
- `kimi-k3-ctx:devops-incident-response:5007` — `For this incident only, tag every message you send with [SEV1-ACTIVE].`
- `kimi-k3-ctx:financial-planning-chat:5015` — `For the next three months only, assume I'm extremely risk-averse.`
- `kimi-k3-ctx:game-master-roleplay:5016` — `For this scene only, play him as warm and grandfatherly.`
- `kimi-k3-ctx:game-master-roleplay:5016` — `Keep it under fifty words for this speech only, he's winded.`
- `kimi-k3-ctx:game-master-roleplay:5016` — `Use whatever NPC stats you like for this fight only.`
- `kimi-k3-ctx:hr-and-recruiting:5018` — `For the calibration meeting only, ignore that cap — we need full detail.`
- `kimi-k3-ctx:hr-and-recruiting:5018` — `Keep the summary under two pages, but only for this version.`
- `kimi-k3-ctx:sales-crm-agent-with-tools:5012` — `Use bullet points in each email this time.`
- `kimi-k3-ctx:journalism-and-fact-checking:5028` — `For this guide only, omit ward numbers after names.`
- `kimi-k3-ctx:journalism-and-fact-checking:5028` — `For this package only, omit the corrections box.`
- `kimi-k3-ctx:journalism-and-fact-checking:5028` — `In this sidebar only, omit field dates for brevity.`
- `kimi-k3-ctx:legal-document-drafting:5008` — `Yes, include pandemic language in this clause only.`
- `kimi-k3-ctx:scientific-code-and-notebooks:5025` — `For the abstract sentence only, round to one significant figure for readability.`
- `kimi-k3-ctx:scientific-code-and-notebooks:5025` — `For this one presentation slide only, switch to grayscale because the journal requires it.`
- `kimi-k3-ctx:teaching-assistant-grading:5035` — `This semester only, use each student's local time for deadlines.`
- `kimi-k3-ctx:therapy-style-supportive-chat:5029` — `Just this session, then delete.`
- `kimi-k3:hr-and-recruiting:1036` — `Wait, actually hold off on that offer until I talk to finance.`
- `kimi-k3:language-learning-practice:2029` — `For this exercise only, ignore my accent mistakes.`
- `kimi-k3:system-prompt-personas:1062` — `For this email only, be extra formal.`
- `sol-enrich` — `Act like a skeptical editor while you review this grant abstract.`
- `sol-enrich` — `Ignore my aisle-seat preference for this flight only; my daughter wants the window.`
- `sol-heldout` — `For this trip only, ignore my usual preference for direct routes.`
