# Direction proposal rev 3 (2026-09-13): dependency-aware delivery of session conventions

Supersedes rev 2 (direction D, focal delivery at syntactic units), which Astra round 3
disproved on the "good chance of working" criterion (~20%) with one decisive mechanism
objection: **a syntactic boundary is often later than the decision the convention
constrains.** A decorator rule needs an import before the `def`; a naming rule binds
callers written before the definition; a class rule needs the structure chosen before
any class boundary exists; a `try` rule reorganises a body rather than its first
token. Rolling back one line cannot repair an earlier commitment. The v3–v6 pilots
show exactly this: rules were followed at the cue (`x_` names, `@retry`, `ud_..._n`)
while the code broke (unbound decorators, self-decoration, wrong algorithm).

Everything below is written before any run and is the object of adversarial round 4.

## 1. Primary direction E1: deliver each obligation at the earliest decision that must account for it

**Claim.** For a set of live session conventions R and a coding request, let each rule
r have a *dependency point* d(r): the earliest decision in the output that must
account for r (an import, an interface/signature choice, a structure choice, the first
call site, the first definition). Delivering r, together with what executing it
requires (the import line, the decorator's module, the name mapping for callers), at
d(r) yields higher **joint** (tests pass AND convention met) success than (a) the same
rules once before generation, (b) the same rules at the syntactic unit they name
(D), and (c) the same rules delivered on the same *schedule* but at unrelated
positions (staggered, unaligned control), at equal rule content and equal total
delivered tokens.

**What is recombined, and from where.**

| component | source | what E1 takes |
|---|---|---|
| rule lifecycle from corrections | TRACE 2606.13174, ZORO 2604.15625 | rules are scoped, superseded, attached to execution |
| program-context guidance during generation | Monitor-Guided Decoding 2306.10763 | global program facts steer local choices |
| controlled validation + rollback | IterGen 2410.07295, Hydra 2605.15238 | bounded regeneration with a retained prefix |
| dependency order in instruction | Kester, Kirschner & van Merriënboer 2006 (declarative vs procedural timing); Cognitive Load Theory element interactivity | information that other decisions depend on must precede them |
| decision-point delivery in other fields | Kawamoto 2005 (CDSS at the decision point), Shojania 2010 | delivery at the point of decision, modest effects, workflow integration matters |

**The gap** (what none of these test): whether timing delivery by *dependency
structure* rather than by syntactic unit or by request boundary improves functional
compliance under evolving session rules, against a relevance-matched up-front packet
and a schedule-matched unaligned control. ZORO attaches rules to plan steps (agent
boundary, not intra-output dependency). MGD constrains identifiers, it does not deliver
prose obligations. Answer Engineering §6.8 reports local repair failing against earlier
commitments, which is the failure E1 is built to avoid, but it does not test
dependency-timed delivery.

**Why it is not a meaningless permutation.** The manipulated variable (delivery timed
to dependency order) is predicted by CLT/element-interactivity and by the repository's
own failure records to change the outcome; D's variable (delivery at the named unit)
was predicted only by proximity and is now shown insufficient. E1 changes *what*
information is delivered (the obligation plus its dependencies) and *when* (before the
commitment), not the wording or the channel.

**Where it lives in the artifact.** The published model wrapper (`stencil_focus`
session interface) already holds the live rule set. E1 adds a dependency planner that
runs before generation on the request and the rule set (oracle map first; a
rule-typed static map second; a learned map never before the oracle test passes) and a
delivery scheduler that uses the existing user-turn channel (the v6 arm that avoided
imitation), not inline comments. Off switch: no planner, no scheduler, same window.

## 2. First cheap disconfirming test (registered before any GPU spend)

- **Tasks**: 24–32 small, independently authored Python development tasks with
  executable tests, written by this program (never from `data/bench/`; data-lineage
  line: authored 2026-09, evaluated-on only). Half with genuinely local conventions
  (naming, docstrings, try) and half with dependency-bearing conventions (decorators
  needing imports, interfaces used by callers, structure choices). Each task comes
  with a session history in which at least one rule changed after related code was
  written (the MemoryCode-derived rendering, same renderer as Exp 4).
- **Arms** (frozen history, equal rule content, equal delivered tokens): `base`;
  `before` (relevance-matched, dependency-complete packet once before generation);
  `unit` (D: at the named syntactic unit, user-turn channel); `dependency` (E1, oracle
  dependency map); `staggered` (E1's schedule shifted to unrelated positions, same
  packets, same count).
- **Outcome**: joint success per task (tests pass AND every applicable convention met
  under the query-required scorer with missing required units counted as failures);
  secondary: convention-only, tests-only, obsolete-pattern propagation, tokens, latency.
- **Readings**: E1 continues only if `dependency` beats `before` AND `staggered` on
  joint success by a practically meaningful margin (≥ 10 points mean, wins on a
  majority of dependency-bearing tasks) with no net functional harm versus `base`.
  If `before` (relevance-matched, dependency-complete) performs equally well, the
  special-delivery claim is retired and the useful residue is "dependency-complete
  packets", which is a packaging improvement, not a research direction.
- **Kill rules**: oracle map shows no advantage → E1 dead, no learned router built to
  rescue it; functional harm → dead; advantage only on local-convention tasks → the
  effect is D's, already disproved.

## 3. Fallback E2: rules retained, plus session examples revalidated after changes

**Claim.** Keep the authoritative rule in prose; attach one minimal, previously
successful session example only while its rule version, dependencies and tests remain
valid; invalidate or replace it when any changes. Prediction: rules + revalidated
examples beat rules alone and rules + ordinary (stale-able) examples on joint success
and on obsolete-pattern propagation, at equal budget.

**Sources**: worked-example effect (Sweller) and Show and Tell 2511.13972 (rules +
examples > either alone for coding), TRACE's correction lifecycle, temporal
invalidation (Zep 2501.13956). **Gap**: whether validity-checking examples against
changed conventions prevents harmful copying while keeping the demonstration benefit.
**First test**: sessions with a rule change followed by a related but algorithmically
different task; arms rules-only / rules+examples / rules+revalidated examples.
**Kill**: rules + ordinary examples equal → novelty dead; maintenance cost exceeds the
benefit or copying of an inappropriate algorithm rises → usefulness dead.

## 4. What is explicitly NOT claimed

- No claim that D's local cueing works; D is stopped.
- No claim from oracle-map results about the live register (admission, supersession,
  scope errors are separate, already-measured error tables).
- No claim that a positive package on/off comparison explains *why* it works; the
  `staggered` and `before` arms exist to attribute the effect.
- "Long input" is not "long agentic session"; the first test is terminal generation
  with one rule change; the agentic check (BFCL long-context, Exp 5) stays separate.

## 5. Boundary of "correctly built E1" (so it cannot be rescued by redefinition)

E1 is: a dependency map from rules to earliest decision points + delivery of the
obligation with its dependencies at those points through the user-turn channel. It
is NOT: global planning, iterative repair loops, learned routers, example memory, or
adaptive scheduling. Adding any of those is a new direction with its own round.
