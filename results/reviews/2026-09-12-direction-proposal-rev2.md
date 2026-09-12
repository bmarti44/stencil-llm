# Research direction proposal, rev 2 (2026-09-12): focal delivery of session conventions

Author: orchestrator. Rev 1 (`2026-09-12-direction-proposal.md`) was disproved by Astra
(`2026-09-12-direction-adversarial-astra.md`): every mechanism in candidate A had a direct
predecessor (TRACE, Answer Engineering, Kiro, Thinking Intervention, SafeRemind, Zep) and the
proposed experiment could not attribute a gain to anything new. Astra's stated bar for
novelty: "an identified new algorithm, guarantee, or demonstrated interaction". Rev 2 accepts
that bar and is built around a demonstrated interaction: the contribution is a theory-predicted,
so far unmeasured, interaction between two established techniques, and the artifact is the
vehicle that exploits it. A recombination whose parts are known is non-meaningless exactly when
the combination produces an effect that theory predicts and no part produces alone; the
experiment is designed so that a null interaction reads as "meaningless permutation" and is
published as such.

## 1. What the literature now establishes (all 2025-2026 unless noted)

1. **Prospective, not retrospective, memory is the failure.** TriggerBench (2606.23459):
   retrospective recall stays near 98% up to 100K tokens while prospective accuracy collapses
   from >90% to <40%; explicit constraint anchoring lifts state-tracking 57.4 → 100. PM-Bench
   (2607.12385): best agent F1 65.1, "no single strategy dominates". "Did You Forget What I
   Asked?" (2603.23530) replicates three human PM effects in LLMs (load, cue salience, temporal
   distance); a reminder placed *before generation* recovers 13-21 points, most at high load
   and long distance, but becomes unreliable under constraint stacking (+25 to −20).
2. **Compliance decays within one session as the model generates more code.** Instruction
   Adherence in Coding Agent Configuration Files (2605.10039, 1,650 Claude Code sessions,
   16,050 function-level observations): none of four file-structure variables matters; the
   dominant effect is within-session, OR 0.944 per additional generated function. Omission
   constraints decay with depth (2604.20911: 73 → 33% turns 5 → 16; 12 models), re-injection
   is *recommended but untested*. Governance Decay (2606.22528): constraint pinning across
   compaction restores 0% violation. ZORO (2604.15625, HCI): rules anchored to plan steps and
   proven with evidence; users report "context rot: rules are loaded initially but not
   continuously retrieved".
3. **Content matters less than presence and placement.** Guardrails Beat Guidance
   (2604.11088): random rules tie curated rules; shuffled equals ordered; "do not" rules help,
   "do" rules distort. Presentation, Not Mechanism (2607.16019): a rendering confound explains
   an 18-point ledger gain. Instruction Stacking Collapse (2608.02639): 96 → 20-60% at 20
   instructions, driven by pairwise conflicts; a prompt compiler helps weak models (+11) and
   not strong ones (−1.2).
4. **Our own data.** Exp 4C (`results/memorycode-long/RESULTS-4C.md`): a before-request
   reminder of evicted user sentences gave +2.05 points (p = .058) on Qwen3-4B. Interim
   diagnosis of the records (no claim): 119/278 outputs hit the 512-token cap; capped outputs
   score 0.014/0.028, uncapped 0.146/0.168; the model spends its budget on a prose preamble
   that *restates the guidelines* and then writes docstring-heavy code that violates them.
   The model recalls; it does not execute at the point of action. That is the TriggerBench
   pattern reproduced on a coding workload.

## 2. The direction: focal delivery (D) of live conventions inside one generation

**One sentence.** Deliver each live session convention *at the syntactic unit it governs*
while the code is being written (a `def`, `class`, assignment or `import` line), instead of
once before the request, and measure whether this converts the prospective-memory demand
into a retrospective one.

**The two established techniques and their combination.**

| part | technique | predecessors (established) |
|---|---|---|
| T1 | live-convention register: admission by the published sentence classifier, lifecycle by the frozen relations head (supersession = latest wins), rendered as text | FOCUS-3 runtime (this repo), TRACE (2606.13174), Zep temporal invalidation, MemGPT/Letta |
| T2 | in-generation insertion at a monitored trigger, with rollback to the line start and KV reuse | Thinking Intervention (2503.24370, `<think>` trigger), SafeRemind (2601.03662, newline/entropy trigger), Answer Engineering (2606.21121, DSL triggers, clinical), IterGen/Hydra (unit-level rollback) |
| D = T1 ∘ T2 | each register rule is typed by the unit it governs (function / class / variable / import / any) from its wording; the incremental parser of the partial output fires at the start of every such unit; the applicable rules are inserted as a comment block immediately above the unit; the model continues | no predecessor delivers *session* conventions *per governed unit inside one completion*; ZORO anchors rules to *plan steps* at agent level; Thinking Intervention delivers *fixed* text at a *fixed* trigger; 2604.20911 recommends per-turn re-injection without testing it |

**The claim that would make this non-trivial (the interaction), and the theory behind it.**

- **H1 (decay × delivery).** Compliance under a before-request reminder falls with the index
  of the generated unit within the output (the within-session decay of 2605.10039 transposed
  to within-output); under focal delivery the slope is flat. Theory: the multiprocess
  framework of prospective memory (McDaniel & Einstein; meta-analysis Anderson, Strube &
  McDaniel 2019, 289 effects): focal cues, processed as part of the ongoing task, are
  retrieved spontaneously; non-focal intentions require monitoring whose cost grows with the
  ongoing task. In a transformer the mechanism is concrete: a rule 250-2,000 tokens back
  competes with the growing output for attention; a rule 1-3 lines above the `def` does not.
  Du et al. (2510.05381) measure the distance penalty even with perfect retrieval.
- **H2 (rule type × delivery).** The benefit of focal delivery concentrates on *commission*
  rules (do X at unit Y) and is absent for rules that need no cue. 2603.23530 finds
  avoidance constraints "nearly immune to forgetting" and terminal/commission constraints
  losing up to 50 points; 2604.20911 finds the opposite ordering in a DevOps chat
  (suppression rules decay, "include X" persists, with an acknowledged auto-reinforcement
  confound). Code conventions let us separate them cleanly because every MemoryCode
  convention is a commission rule on a typed unit, and the checker (`vendor/memorycode/code/
  extract_objects.py`: FunctionDef, ClassDef, Assign, AnnAssign, Import, decorators,
  annotations) tells us the unit type without reading any item.
- **H3 (load × delivery).** With k live rules, before-request delivery stacks all k at once
  (Instruction Stacking Collapse: conflicts and dropping grow with k; 2603.23530: reminders
  unreliable under stacking); focal delivery presents only the rules typed for the current
  unit (typically 1-3). Prediction: the focal advantage grows with k.

Each hypothesis is a *sign* prediction from a theory that is replicated in humans and, for
H1/H3, already partially reproduced in LLMs; none has been measured for in-generation
delivery, in code, or for session conventions. If all three are null, the direction is a
meaningless permutation and the report says so.

**What is fixed by construction (not claimed as novel, but load-bearing).**

- Coverage guarantee: the incremental parser fires at *every* unit of a governed type, so a
  rule typed "function" is delivered at every function; delivery completeness is a property
  of the parser, not of attention. Missing units (the model never writes the class) are the
  one failure focal delivery cannot fix; they are counted separately (structure-missing rate).
- Measurement integrity: every inserted span is recorded with its offsets and stripped before
  scoring; the checker is AST-object based, so comments never satisfy a check; docstring
  and content checks are scored on the model's own tokens only.
- Same information in both arms: the before-request arm and the focal arm render the *same*
  rule text (same register, same lifecycle); only *where* and *when* it appears differs.
  Token accounting is reported per arm (prompt tokens, inserted tokens, generated tokens).

## 3. Why this can work here (likelihood) and what would kill it

- Uncapped compliance is 0.15 with rules that the model itself restates in its preamble.
  The failure is execution at the unit, the exact thing focal delivery targets.
- Cost: insertion happens at unit starts (a handful per output); rollback is to the current
  line start (≤ 10 tokens); KV reuse; Hydra/IterGen show this is cheap relative to repair.
  A 139-pair run took 3.4 GPU-h at 512 tokens; with a 1,536-token cap and insertion, ≤ 10 GPU-h
  for ~120 pairs.
- Kill criteria before GPU: (K1) rule typing from wording reaches ≥ 0.9 agreement with the
  checker's unit family on the SETUP dialogues' gold instructions (CPU; the extraction weak
  link); (K2) the incremental trigger fires on ≥ 95% of unit starts in the 278 stored Exp 4C
  outputs with zero false fires inside strings (CPU, replay on stored text; no generation).
- Known risks Astra should press: the inserted comment changes the continuation (the
  comparator for H1 must be *the same text at the request*, so the only difference is
  placement); triggers inside quoted examples; competing rules at one unit; the cap
  (process fix: 1,536-token output, 2,560-token window, total ≤ 4,096); outcome-exposed
  items (the 139 Exp 4C dialogues are exposed; confirmation uses the 57 unexposed long
  candidates plus any never-opened reserve; the exposed items may serve a disclosed screen
  only); functional correctness unmeasured (disclosed as in every prior registration).

## 4. Minimum registration (reusing the Exp 4C infrastructure verbatim)

- Arms (paired by item, same weights, same package, same register): `off` (no reminder),
  `before` (register rules rendered once before the request, Exp 4C renderer), `focal`
  (same rules typed and delivered at unit starts; nothing before the request), `both`
  (descriptive; the shipping configuration if `focal` wins).
- Primary estimand: `focal − before` on `fraction_required`, paired t with the Exp 4C
  statistics module; output-failure guard as registered (H ≤ +5 points, now on a 1,536 cap).
- Interaction tests (pre-registered, secondary): H1 slope of per-unit compliance on unit
  index, arm × index in a mixed model with item random effects; H2 arm × unit family;
  H3 arm × k (number of live rules, from the register, not labels).
- Readings: PROVEN-SCOPED if primary interval > 0 and guard holds (artifact ships with
  `both`); NOT PROVEN otherwise; the interactions are reported as demonstrated / not
  demonstrated with intervals and never change the primary reading.
- Stage 0 (CPU): K1, K2, and the two-line data-lineage statement (nothing fit on MemoryCode;
  rule typing uses the checker's public unit taxonomy, not item data).
- Stage 1 (GPU ≤ 2 h): 16 SETUP items, four arms, qualification of the insertion runtime
  (replay identity with the plain package when no trigger fires; deterministic re-runs).
- Stage 2 (GPU ≤ 8 h): N from timing as in Exp 4C on the unexposed candidates.

## 5. Fallback direction (X), only if D is disproved: verified exemplars instead of rules

Render each live rule as the newest *verified-compliant* code example from the session
itself (the monitor that types the rule also checks the exemplar), not as prose. Theory:
worked-example effect (Sweller; replicated), structural priming (Pickering & Branigan;
reproduced in LLMs), and the auto-reinforcement confound of 2604.20911 read as a mechanism
(the model's own recent compliant output is the strongest reminder). Interaction claim:
exemplar delivery beats prose delivery at equal token budget, and the gap grows for commission
rules. Predecessors: few-shot ICL, self-generated demonstrations (SG-ICL), repository-level
style copying; the new part is the lifecycle-verified selection under updates.

## 6. What Astra is asked to do

Disprove D on (a) novelty: a predecessor that delivers session conventions per governed unit
inside one completion, or a prior measurement of H1/H2/H3; (b) theory: show the multiprocess
framework or the LLM decay results predict a null or the opposite sign; (c) measurement: show
the design cannot attribute the effect to placement (confounds we missed); (d) usefulness: a
positive result would not change what a practitioner does; (e) likelihood: a mechanism reason
it fails on a 4B model at 2.5K-token windows. Then the same for X. If D survives, state the
minimum changes to section 4. If D falls, construct the strongest direction you can and
disprove that too.
