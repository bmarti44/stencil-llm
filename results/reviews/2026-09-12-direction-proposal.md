# Research direction proposal (rev 1, 2026-09-12): fixing the Stencil line

Author: orchestrator. Purpose: Brian's goal of 2026-09-12 ("find a novel, useful recombination
of techniques that is not technically novel based on a meaningless permutation, that is a
significant difference, and that has a good chance of actually working based on current
research, not only in the AI domains but also all other academic domains"; "also fix the
current direction, use your judgement and common sense"). Astra attacks this document
adversarially; the direction is adopted only when Astra cannot disprove it.

## 1. Diagnosis: why the current direction produced +2 points and not more

Exp 4C (`results/memorycode-long/RESULTS-4C.md`): restating evicted user sentences in a
256-token reminder before the request, on 139 paired MemoryCode-derived long coding sessions
through the shipping Qwen3-4B package: compliance 0.084 → 0.105, +2.05 points, 95% [−0.07,
+4.16], p = .058, strict 0 vs 1 of 139, output failures 60 vs 61.

Four causes, each visible in the records:

1. **Blind selection.** The reminder is the newest evicted user sentences regardless of
   relevance. Most restated sentences are not conventions at all; the ones that matter are
   often older than the 256-token budget reaches.
2. **Stale and superseded rules are restated as if live.** MemoryCode's hard cases are
   updates ("from now on use camelCase instead"); the reminder cannot tell an update from the
   rule it replaced. Proactive-interference results in LLMs (Wang et al. 2025, "Unable to
   Forget", 2506.08184) show later updates lose to earlier values even when both are in
   context, and prompt-level "forget" cues barely help.
3. **No enforcement at the point of action.** Even with the correct rules visible (Exp 4B's
   label-derived oracle reminder: 0.263), the model applies roughly a quarter of them.
   Compliance is a generation-time behaviour, and reminders act only through attention.
   TriggerBench (2606.23459) reports the same: prospective-memory accuracy degrades under
   overloaded triggers and "always-remind" heuristics overfit.
4. **Distance itself hurts.** Du et al. 2025 (2510.05381) show performance falls with
   separation distance even under perfect retrieval; a reminder 250 tokens before the
   request is still far from the `def` line where the rule applies.

Common-sense reading: the +2 points are the ceiling of "remind harder". A significant
difference needs the rules to be (a) correct and current, and (b) enforced where the code is
written. The rest of this document proposes how, with the evidence infrastructure already
built (package-path generation, receipts, qualification, audited statistics) reused as is.

## 2. Primary candidate (A): runtime-enforced session conventions

**One sentence.** Treat the conversation's coding conventions as a *runtime policy* and the
model's decoding as the *monitored program*: extract each convention when it is stated,
canonicalize it by readback, compile it into an executable monitor, version monitors on
update, and enforce them during generation with an edit automaton (suppress by rollback,
insert by cue) rather than by reminding.

**The recombination, with the source of each part.**

| part | technique | origin (domain) |
|---|---|---|
| A1 | admission of rule sentences | our published classifier `bmarti44/assistant-memory-sentence-classifier` (AI) |
| A2 | **readback**: after each admitted rule the assistant restates it in canonical if-then form ("IF I define a function THEN its docstring uses the Google style") in its own turn; the user can correct it | aviation ATC readback/hearback protocol (human factors); implementation intentions, Gollwitzer 1999, meta-analytic d ≈ .65 for goal attainment (psychology); the generation effect, Slamecka & Graf 1978 (cognitive psychology) |
| A3 | **compilation** of the canonical rule into an executable monitor (regex over the partial output; AST predicate on the partial parse; or, for content rules, a small LLM judge on the completed unit) | "Still Manual?" DSL-based LLM compilation of coding standards into linter configs, 2602.07783 (SE); MemoryCode's own regex checkers show conventions of this workload are monitor-expressible (AI) |
| A4 | **lifecycle**: an update compiles a new monitor that *retires* its predecessor; the retired rule is rendered once as an explicit contrast ("no longer X; now Y") at update time and never again | version control; Bjork's directed forgetting and the reconsolidation literature (cognitive science); PI findings in LLMs (2506.08184) motivate removing, not merely negating, the old rule |
| A5 | **enforcement at decode time**: monitors run on the growing output; on a trigger (e.g. a `def` line) the applicable intentions are inserted as an in-code cue at that point; on a violation the generation is rolled back to the last checkpoint (KV reused) and regenerated with the cue | edit automata, Ligatti, Bauer & Walker 2005 (security/runtime enforcement); Hydra checkpoint-and-rollback 2605.15238 and IterGen (AI/PL); cue-focal delivery from the multiprocess theory of prospective memory, McDaniel & Einstein (cognitive psychology); budget-forcing text insertion, s1 (AI) |

**Why this is not a permutation.** Each neighbouring system enforces a *different kind of
thing* or at a *different time*: ChopChop/MGD/type-constrained decoding enforce fixed
syntactic or semantic properties by token masking, not conversational conventions that
change mid-session and include content rules masking cannot express; "Still Manual?"
compiles standards into offline linter configs, not into decode-time monitors; Hydra rolls
back on compiler errors, not on policy violations; AgentSpec (2503.18666) enforces
tool-action policies between agent steps, not inside a completion; "Remember When It
Matters" (2607.08716) injects reminders between agent steps from a learned memory agent
(+8.3 pp Terminal-Bench) and does not enforce; the "intent continuity" pipeline retrieves
and verifies requirements before a task, not during generation. The new object is the
*policy-enforced completion*: conventions become a versioned runtime policy enforced by an
edit automaton over the token stream, with the rule text authored by readback. No existing
system we found has A2+A3+A4+A5 together, and A5 (suppress/insert enforcement of
natural-language conventions inside one generation) appears absent on its own.

**Why it has a good chance of working.** (i) Enforcement is mechanical for monitor-expressible
rules, so the effect is bounded below by the monitor coverage rather than by attention;
MemoryCode's checker families are regex/AST, so coverage on this workload is near total.
(ii) Cue-focal delivery is supported by the strongest human prospective-memory evidence and by
the LLM distance result (rule text adjacent to the point of use). (iii) Rollback-and-regenerate
with a cue is the same operation Hydra shows cuts latency 71% and tokens 70% relative to
post-hoc repair, so cost is tractable. (iv) Readback puts the canonical rule in the assistant's
own words in the assistant turn (generation effect analogue; recitation-augmented LMs), and
gives the user a correction point, which no prior system offers.

**Expected magnitude.** On the Exp 4C cohort, an enforced monitor set should lift
required-check compliance from ~0.10 to the checker-coverage ceiling minus judge/monitor
error; anything under +20 points would be a failure of the proposal. That is the "significant
difference" bar: an order of magnitude over the reminder effect.

**Falsifiable predictions.** P1: enforcement-on beats enforcement-off by ≥ +20 points on
`fraction_required` with output failures noninferior (+5-point margin), same package, same
weights. P2: readback canonical rules reproduce the gold MemoryCode instruction set with
≥ 0.9 F1 on the SETUP dialogues (extraction is the weak link if not). P3: on update items,
retiring the old monitor beats keeping both (the PI prediction). P4: cue-at-trigger beats
cue-before-request at equal cue text (the cue-focality prediction). Each is a paired test on
the existing infrastructure; P2 is CPU-only and runs first (kill criterion).

**Cost.** CPU: classifier + compiler + monitors (existing code paths). GPU: the same
qualification/evaluation machinery; rollback adds ≤ 1 regeneration per violated unit; a
139-pair run is ~3.5 GPU-h today, so ≤ 8 GPU-h with rollbacks.

**Risks Astra should press.** (1) Someone has done decode-time enforcement of NL conventions
with rollback (search: "constraint", "guardrail", "style", "policy", "edit automata", "runtime
verification", "LLM decoding"). (2) The gain is "just a linter": is the contribution then the
readback+lifecycle+cue-focal part, and is that enough? (3) Monitor compilation from NL is
brittle; "Still Manual?" numbers on config accuracy. (4) Judge-based monitors for content
rules re-introduce the attention problem. (5) Enforcement can harm functional correctness or
cause degenerate loops (guard: rollback budget, failure guard as registered).

## 3. Secondary candidates (fallbacks if A is disproved)

**B. Readback-only (A2 without A3-A5).** Cheapest; predicts a moderate gain from canonical
self-authored rules living in assistant turns plus user correction. Novelty is lower
(recitation/self-notes exist); the cross-domain import (ATC readback) is the new part.

**C. Cue-focal delivery only (A5 insertion without suppression).** Trigger-detected insertion
of the applicable rule at the `def`/`class`/`import` line inside one generation, no rollback.
Closest prior art: "Remember When It Matters" (between-step injection). Predicts a gain from
locality alone (2510.05381); smaller than A.

**D. Update-retirement rendering only (A4).** Render superseded rules as explicit
contrasts once and remove them thereafter; tests the PI hypothesis on MemoryCode update
items. Smallest scope; a component study, not a direction.

## 4. What Astra is asked to do

Try to disprove A on novelty (find the closest prior systems and say whether A reduces to
one of them), on significance (argue the expected gain is small or unattributable), on
likelihood (mechanism, brittleness, cost), and on the cross-domain grounding (are the
imported results real, replicated, and correctly applied?). Then do the same for B, C, D.
If A survives, say so and name the minimum registration for P1-P4. If A falls, name the
strongest direction that satisfies Brian's goal, with the same grounding standard.
