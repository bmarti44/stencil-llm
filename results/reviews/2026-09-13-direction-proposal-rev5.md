# Direction proposal rev 5 (2026-09-13): candidate A in a prespecified operating domain, with a registered competence pre-check

Rev 5 takes Astra's round-6 first choice (candidate A, counterfactual training on
current-rule execution; `results/reviews/2026-09-13-direction-search-rev6-astra.md`) and
makes its conditional path concrete. Astra's bar for "good chance" is ≥ 60% before new
evidence; A sits at 35–55% under the open-domain objective and at a provisional 60–75%
*if* the operating domain is narrowed to a prespecified family of maintenance tasks with
supported mutable contracts and fresh authored evidence shows the unmodified model can
already execute those tasks under immediate instructions. This document fixes that
domain, the pre-check that establishes the condition, the screen, the confirmation, the
artifact, and the kill rules, so round 7 can attack a fixed target.

## 1. Direction A (unchanged from round 6, restated)

Train an optional, unmerged LoRA adapter on a frozen ≤ 4B trunk (Qwen3-4B, the trunk of
the existing `stencil_focus` package) on **pairs of session histories** that differ by a
legitimate instruction event (admission, authorised replacement, scoped exception,
reinstatement) which reverses which executable patch is correct. Objective: ordinary
completion loss on the current-rule solution plus a preference term (IOPO/RPO family)
favouring the current-rule patch over the stale-rule patch, with the preference reversed
in the counterfactual twin; consistency required under irrelevant history changes.
Deployment needs no teacher. Off switch: bypass the adapter; the same session memory,
reminder rendering, tools and generation budget remain.

**Recombination**: Ghost Attention (context distillation for multi-turn persistence,
2307.09288 §3.3) × IOPO (2411.06208) / RPO (constraint reversal for clean pairs,
2505.22172) × SelfCodeAlign (execution-filtered code training, 2410.24198) × the
retrieval-practice and completed-intention literature (Pan & Rickard 2018; Scullin et
al.) motivating training of retention *and deactivation*. Nearest predecessor: Supersede
(2606.27472, temporal memory updating in Qwen2.5-3B). **Gap**: temporal and scoped rule
selection coupled to correct code changes, with ordinary SFT on the same verified
solutions as the control that can show the recombination adds nothing.

## 2. The prespecified operating domain (frozen here, before any data is authored)

**Domain**: maintenance tasks on small Python packages (3–6 modules, 150–600 lines,
executable pytest suites) governed by **mutable project contracts** from a closed schema
of eight contract families. Each family has (i) a machine-checkable form, (ii) a defined
replacement, (iii) a defined scoped exception, and (iv) executable tests that fail when
the contract is violated:

| family | example contract | replacement | scope |
|---|---|---|---|
| missing-record policy | lookups return `None` | raise `KeyError` | per module/class |
| error surface | wrap I/O errors in `AppError` | propagate raw exceptions | per package |
| validation entry | validate at public API boundary | validate at storage layer | per subsystem |
| return shape | return dataclasses | return dicts | per API family |
| logging policy | log at WARNING with structured fields | no logging | per module |
| naming contract | public functions `verb_noun` | `noun_verb` | per module |
| dependency choice | use `json` | use `orjson` with fallback | per package |
| immutability | config objects frozen | mutable with copy-on-write | per type |

Everything the artifact will claim is stated in these terms; conventions outside the
schema (decorator sprinkling, docstring presence) are explicitly *not* the domain.

**Usefulness argument for the narrowed domain**: these are the contracts that actually
change during real maintenance and whose violation breaks behaviour (not style), so a
model that keeps the current contract over a long session is useful even if it never
learns a ninth family. This is the "useful" criterion for the narrowed scope.

## 3. Registered competence pre-check (the condition Astra attached to 60–75%)

Before any training: 32 authored development tasks from the domain (disjoint projects
from every later set), each presented to the **unmodified** 4B model with the current
contracts stated immediately in the request (no history). Outcome J = tests pass AND
all applicable contracts satisfied. **Eligibility**: J ≥ 50% (≥ 16/32) with function-only
success ≥ 60%. Below that the domain is INELIGIBLE for a 4B trunk and the program stops
before training (recorded as a negative about competence, not about A). This is the
"fresh authored evidence" the condition requires; it uses no evaluation data and no
benchmark. Cost: 32 generations, < 1 GPU-hour.

## 4. Screen (development gate, per Astra's common design)

- 48 newly authored small repositories with a frozen 12–20-turn history containing
  balanced stable rules, authorised replacements, scoped exceptions and irrelevant
  directives, followed by **two live requests** whose correct patches depend on the
  current contracts; private scoring tests unavailable to generation.
- Arms: `off` (adapter bypassed); `sft` (ordinary SFT on the same positive solutions and
  histories, matched compute); `cf` (A). Same session memory and reminder rendering in
  all arms; same generation and context budgets (≤ 4,096 tokens; short patches, not
  whole-program regeneration).
- Gate: ≥ 5 net J wins over `off` AND ≥ 3 net J wins over `sft`, no net function-only
  decline against either, all 48 count (timeouts and abandoned tasks are failures).
  Also reject if gains occur only on stable-rule cases while replacement/scope cases
  deteriorate. Failure = do not advance; not equivalence.
- Compute: training data generator + two LoRA trainings + 3 × 48 × 2 generations
  ≤ 16 GPU-hours, measured by a timing pilot first; cost-ineligible if exceeded.

## 5. Confirmation (registered only on a screen pass)

N = 256 authored sessions (disjoint projects and solution families), arms `off` vs `cf`,
paired exact McNemar two-sided on J, conservative paired interval, function-only
noninferiority guard with its own interval; PROVEN only if the J interval is entirely
above zero and the guard holds. Power at a true 10-point effect: 95% / 81% / 69% at
20 / 30 / 40% discordance (Astra's table). Total program 40–60 GPU-hours.

## 6. Data lineage

Training: authored project generator + counterfactual history generator + executable
tests, execution-filtered; development set: separate projects; screen and confirmation:
separate projects and solution families. Nothing from `data/bench/` or MemoryCode is
used for training, selection or tuning; MemoryCode-derived items are not used at all in
this program (their checker rewards conventions without functionality, the round-5
lesson). BFCL long-context stays the separate agentic check.

## 7. Artifact

`bmarti44/stencil-contract-qwen3-4b`: frozen trunk + unmerged adapter + session package;
`contract_focus=true/false` bypasses the adapter and nothing else. Card states the
domain (eight contract families), the screen and confirmation tables, function-only
results, cost, and the off-model pre-check numbers.

## 8. Kill rules and boundary

- Pre-check fails → program stops before training.
- `sft` ties `cf` → novelty claim retired; a useful SFT adapter may still be published as
  engineering, labelled so.
- Function-only decline → stop.
- Gains confined to stable-rule cases → stop (the mechanism claim is deactivation).
- A is the adapter + objective + counterfactual generator; adding memory training (C),
  recovery training (B) or gating (E) is a separate program.
