# fable-validation — author-disjoint validation set for the remember-me classifier

File: `data/classifier/heldout/fable-validation.jsonl` (363 rows, one JSON object per line, all parse).
Author: fable (Claude), 2026-09-02. Written by hand, one row at a time, from `data/classifier/LABELS.md` only —
no kimi / kimi-ctx / *-enrich / review/ file, no other heldout file, and nothing under the benchmark directory was
opened; no items or instruction taxonomy from the external instruction-following or tool-calling suites were drawn
on. Fable supplied no rows to the split the classifier is fitted on.

## Counts

| label | rows | share |
|-------|------|-------|
| rule  | 124  | 34.2% |
| fact  |  89  | 24.5% |
| none  | 150  | 41.3% |

| role      | rows | rule | fact | none |
|-----------|------|------|------|------|
| user      | 294  | 106  |  69  | 119  |
| assistant |  24  |  10  |   1  |  13  |
| tool      |  33  |   0  |  16  |  17  |
| system    |  12  |   8  |   3  |   1  |

- hard = true: 191 / 363 (52.6%) — rule 53, fact 42, none 96.
- context present: 165 / 363 (45.5%), 1–3 preceding sentences with speaker prefixes.
- domains: 39 distinct (accessibility, agentic-tools, automotive, coding, cooking, creative, data-analysis,
  ecommerce, education, email, event-planning, finance, fitness, formatting, gaming, gardening, health-intake,
  home-automation, hr, journalism, legal, long-sentences, marketing, multilingual, music, onboarding, ops,
  parenting, persona, photography, productivity, real-estate, research, science, security, sloppy-text, support,
  translation, travel).
- fields on every row: text, role, label, domain, hard, why (3–12 words), source = "fable-validation"; context optional.

## What the hard cases target

- One-off imperative tasks (none) placed directly after the look-alike standing rule, usually with that rule in
  `context` ("Show me the diff…" vs "Whenever you show a diff…"; "Roll back the deploy…" vs "Whenever a deploy fails…").
- Plain-language formatting preferences as rules: lowercase-only, no headings, no bullets / bullets max three,
  sentence and word limits, British spelling, bold summary line, yes/no-first, no emojis, no em dashes, grams not cups.
- Rule cancellations and narrowings (rule): "forget the TypeScript rule", "drop the butler act", "you can use headings
  again", "full names are fine internally — initials externally", "stop prefixing the cluster name".
- Reply-scoped exceptions (none): "just for this one", "this once", "go long on this one", "exclamation marks allowed
  this time", "show me the roll for this one".
- Corrected facts (fact): branch name, order number, on-call person, metformin dose, passenger count, rent, tempo,
  guest count, character age, timezone (correcting a system-supplied fact).
- Tool lines: identifiers the user later relies on (PR number, pod name, deployment/rollback ids, booking reference,
  tracking number, commit hash, file paths written, DOI, OBD code, device ids, running budget total) as fact, beside
  routine telemetry (CPU/MEM, heartbeat, "214 passed", "Plan: 0 to add", "nothing to commit", "Step 3/7", "→ ok") as none.
- Third-party rules not adopted (none): tech lead's tabs, SRE handbook, the previous rep, the travel-agent friend, the
  editor's "never open with weather", the PI's SI units, the school's screen rule, legal's recruiter policy, the
  quoted Slack injection — contrasted with third-party constraints the user explicitly adopts (physio's no-hills,
  cardiologist's grapefruit ban, teacher's three sig figs) labelled rule.
- Assistant restatements of user rules (rule): eleven commitments ("Understood — every code sample… TypeScript",
  "I'll ask for confirmation before any --force command", "one question at a time…") plus assistant prose that merely
  references a rule ("Here's a two-sentence version, as you asked") as none.
- Persona rules and triggers ("faro speaks", "ship it", "go long") with the one-off invocation labelled none.
- Multilingual rows (Spanish, French, German, Portuguese) and sloppy text ("frm now on dont ask me clarifying qs",
  "also STOP using emojis omg", "wat") across all three labels; four long-sentence rows carrying a rule, a buried
  fact, a recap of facts, and a one-off request wrapped in meta-talk.
- System rows: personas and prohibitions (rule), environment/date/user facts (fact), and one meta line (none).

## Judgement calls worth flagging

- Assistant sentence stating an identifier it created ("I've opened a branch called fix/typo-readme") is labelled
  fact (durable, role-agnostic), the only assistant fact in the set.
- "APPROVE" typed after a rule that requires it is none (one-off authorization), not a rule.
- The user's decision sentences ("I'll take the brass one, size medium", "Decided: Tomé is alive…") are fact.
- "My teacher only accepts three significant figures, so do the same in every worked answer" is rule (adopted);
  "My teacher is strict about sig figs, it's kind of annoying" is none.
