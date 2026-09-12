# Direction proposal rev 4 (2026-09-13): compiled current-rule demonstrations (E3)

Supersedes rev 3. Astra round 4 disproved E1 (dependency-aware delivery: the safe
implementation collapses into a dependency-complete up-front packet; the deployable map
inherits D's difficulty) and E2 (revalidated session examples: no admissible example is
guaranteed after a rule change, and source validity does not predict useful transfer)
on the "good chance of working" criterion. It named E3 as the replacement it would
investigate, at 30–50% for a useful small-screen result, while stating plainly that
reviewer survival is not efficacy evidence. This document specifies E3 so that round 5
can attack a fixed target rather than a moving one.

## 1. Claim

Keep the authoritative session conventions in prose (the existing register/reminder).
For each supported convention family, when a rule is admitted or changed, **compile** a
small executable demonstration from a frozen, family-specific template using the
current rule text and its actual dependencies (the import the decorator needs, the
module it comes from, the name pattern applied to a trivial body). The demonstration is
task-independent by construction: a deliberately trivial body that teaches naming,
imports, decorators, structure, docstring/try placement, and nothing about any prior
task's algorithm. It is built without access to the next request, its tests, or any
target solution. It is rendered next to the prose rule in the reminder, within the same
token budget accounting as today.

Prediction: rules + compiled demonstrations beat (a) rules alone and (b) rules + the
best available *session* example (the ordinary few-shot practice) on **joint success**
(executable tests pass AND every applicable convention met under the query-required
scorer, missing required units counted as failures), with lower propagation of stale
conventions and lower inappropriate algorithm copying than (b), at equal delivered
tokens.

## 2. What is recombined

| component | source | what E3 takes | what E3 does not claim |
|---|---|---|---|
| rules + compact demonstrations for style control | Show and Tell 2511.13972 | demonstrations complement prose | its (near-ceiling, single-task) results as task-success evidence |
| self-generated demonstrations when no pool exists | Self-ICL (EMNLP 2023) | demonstrations can be manufactured | free-form generation; E3 uses frozen templates, not a model |
| correction-derived rules with a lifecycle | TRACE 2606.13174 | rule admission/supersession events trigger compilation | the lifecycle itself |
| specification compiled to executable artifacts | Synquid (PLDI 2016), SkillOps 2605.13716 | an executable, checkable artifact per rule | executed skills; E3's artifact only conditions a generator |
| validity of a stored derivative checked against changed requirements | PlanFence 2609.03340, Zep 2501.13956 | recompile on change instead of revalidate | a memory system |
| worked-example effect, element interactivity | Sweller; Renkl | a minimal example lowers the load of instantiating an abstract rule | that examples always help; the template keeps interactivity minimal |

**The gap**: whether compiling *changing* conventions into *task-independent executable*
demonstrations improves functional convention transfer while avoiding both stale
examples and source-algorithm copying. No cited work tests that comparison; the closest
(Show and Tell) uses hand-written examples on one task; SkillOps executes skills rather
than conditioning generation; Self-ICL generates from the model without dependency facts.

**Why not a meaningless permutation**: the manipulated variable is the *provenance* of
the demonstration (compiled from the current rule + dependencies vs recalled from
session history vs absent). It predicts a specific pattern: (b) shows stale-convention
propagation and algorithm copying that (c) does not, and (c) beats (a) on
dependency-bearing families (decorators, imports, structure) more than on purely local
ones. If (c) merely equals (b), the direction is engineering, not research.

## 3. First cheap disconfirming test (registered before GPU spend; a development screen with intervals, never a confirmation)

- **Tasks**: 32 authored Python tasks with executable tests (authored 2026-09, evaluated-on
  only; never from `data/bench/`; no shared template clusters counted as independent).
  Each task has a session history (MemoryCode-derived renderer, same as Exp 4) with at
  least one rule change after related session code exists, and a related but
  algorithmically different request. Half of the families dependency-bearing
  (decorator+import, structure, interface), half local (naming, docstring, try).
  Specification consistency checked before freezing: the current conventions must be
  satisfiable together with the tests and the real library APIs.
- **Arms** (frozen common history; equal delivered tokens; equal generation and context
  budgets; base = the shipping package with the modification off):
  `base`; `rules` (current prose rules, once before generation);
  `rules+session_example` (the most recent session code that satisfied the *previous*
  rule version, i.e. ordinary few-shot practice);
  `rules+compiled` (E3). Templates frozen before any generation; the compiler never sees
  the request, tests or any solution.
- **Outcome**: joint success per task; secondary: tests-only, conventions-only, stale
  convention propagation, inappropriate copying (template or session algorithm fragments
  in the output), construction cost, tokens, latency.
- **Decision rules**: paired exact McNemar on discordant tasks, two-sided, with the
  conservative paired interval; N = 32 is a screen (Astra's table: 78–408 pairs for a
  10-point effect at 80% power), so the screen's only decision is CONTINUE / STOP:
  CONTINUE if `rules+compiled` wins ≥ 6 more tasks than it loses against **both**
  comparators with no treatment-only functional failures beyond `base`'s; anything else
  STOPs the direction. A CONTINUE authorises a registered N ≥ 128 run, not a claim.
- **Kill rules**: no joint-success gain over `rules` → dead; gain appears only against a
  deliberately stale session example → dead (that is defeating a straw man); template
  behaviour copied into outputs damages tests → dead; gain confined to local families
  → engineering only, no research claim.

## 4. What is explicitly not claimed

- Nothing about D (unit-level cues), E1 (dependency timing) or E2 (revalidation).
- No claim that a positive screen explains *why*; the session-example arm attributes
  the effect to provenance, not to "examples help".
- The wrapper cannot edit historical session code; tasks are scored on the new
  completion only, and the report says so.
- Oracle rules first; the live register's admission and supersession errors are a
  separate, already-measured table.

## 5. Boundary of E3

E3 is: frozen per-family templates + a compiler from (rule text, dependency facts) to
one trivial executable demonstration + rendering next to the rule. It is NOT:
model-generated demonstrations, retrieval over session code, dependency-timed delivery,
repair loops, or adaptive selection. Any of those is a new direction with its own round.
