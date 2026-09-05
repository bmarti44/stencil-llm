# Breakthrough hypotheses for a Miller-style focus mechanism — fable, 2026-09-05 (CPU-only; no GPU launched)

Goal (Brian): a transient, content-free signal on a frozen trunk that SETS which stored competency governs now, HOLDS it,
SWITCHES it, CLEARS it. Sources read: README, astra drift/path assessments, quick checks 1-30, FOCUS-1 v2, internal-wave
plan/report, selector report, archive README, GPT-2 report, prior-art survey, astra blockers §6, and the check-31 partial
records (results/quick-checks/focus1-probe/1.7b/, status "running" at read time). Web evidence cited where it moved a rank.

## Finding 0 (free, from check 31's own records — changes every ranking below)

Re-scoring the 99 recorded rows with string->int coercion: visible-cue ASC 28/32 correct (every one emitted quoted
strings `["-17","-1",...]`, so the strict scorer counts 27/27 invalid); visible-cue DESC only 10/32 correct — 16 are
genuinely wrong orders (dropped signs, invented values); OFF ("Process these integers") = copy 27/32. Two conclusions:
(a) the strict "integer-only JSON" scorer (also in FOCUS-1 v2) fails the trunk's correct answers (quoted ints, ```json
fences) — a scorer artifact, not a competence fact; (b) descending sort with negatives is NOT a demonstrated 1.7B
competency, so asc/desc will be INELIGIBLE regardless of any actuator. Every test below uses a pair the trunk actually
performs at >=29/32 (candidate: ASC-sort vs REVERSE-input; confirm in a 5-minute competence pass, coercing digits) and
scores value-exact, format-lenient. Do not spend an actuator budget on asc/desc at 1.7B.

## What the record says about actuators (why each hypothesis is shaped as it is)

- Sustained additive residual vectors truncate (check 30: 14-15/20 hit the cap) and cache-column attention bias on
  retained history degenerates (check 28: 8/20). Both are CONTINUOUS, per-step, dose-sensitive interventions.
- The two things that worked cleanly were (i) a discrete address feeding a bounded spotlight on PROMPT text at beta 2
  (S1: 75% rescue, 0 broken; sealed 88.3%) and (ii) a small module trained by CE THROUGH the frozen trunk (W0: 25->45%,
  ablation-proven WHERE/WHEN). Neither has been pointed at skill selection; both are reusable today.
- 2025-26 literature: one-shot KV-cache edits are reported more dose-stable than per-step activation steering
  (Belitsky et al. 2025, arXiv:2507.08799; Memory Inception 2026, arXiv:2605.06225, frozen Llama-3.1-8B/Qwen3-30B);
  LEARNED task vectors beat extracted mean-difference vectors and act at arbitrary layers/positions (ICLR 2026,
  arXiv:2509.24169); mean-difference steering is unreliable and sometimes anti-steerable (arXiv:2602.17881, 2511.18284);
  learned soft head gates on a frozen trunk isolate task-sufficient sub-circuits (Causal Head Gating, arXiv:2505.13737).
  Net: extracted residual vectors (check 30, check 31) are the weakest family in the literature too; move budget away.

## Ranked hypotheses (each: claim / why here / quick test / pre-registered reading / unlocks / P(pass))

### 1. MENU-SPOTLIGHT — the SELECTOR actuator selects a skill, not a rule sentence.  P(pass) 50%, ~1 GPU-h
Claim: a 2-bit address driving the proven beta=2 spotlight (layers 20-27) at a fixed 3-entry skill menu in the prompt
("A: sort ascending. B: reverse the order. C: copy.") makes the frozen trunk execute the addressed skill on fresh operands
with no textual cue about which entry applies. Why here: this is the exact actuator that went 3.9->88.3% with 0 broken at
S1 and 0/61 wrong-span; check 28's failure was deficit-gated bias on retained HISTORY, not a bounded spotlight on a short
fixed menu. Hybrid text-address + activation: the menu is content, the choice is not. Test: 64 fresh lists (own seed,
disjoint sets), arms OFF(menu, no spotlight) / A / B / C / wrong-entry / shuffled-columns, decisions SET, HOLD (128
neutral tokens then re-apply), SWITCH, BACK, CLEAR (spotlight removed; KV untouched — actuator clear is exact by
construction, behavioural clear measured on two copy queries). Reuse scripts/selector_s1.py spotlight code + check-31
banks/prompt wrapper. Pass: addressed-skill exact >=48/64 for each of A and B, OFF-with-menu <=16/64 on either sorted
form, wrong-entry follows its own entry (proves address specificity), broken <=1/64 per arm, CLEAR copy = OFF copy rate.
Fail otherwise. Rules out: text leakage (OFF-with-menu arm), dose artifact (shuffled columns), default coincidence
(C entry). Unlocks: an address-driven actuator with a proven safety record -> hypothesis 5 immediately.

### 2. LEARNED ADDRESS PREFIX — a content-free KV state trained through the frozen trunk.  P(pass) 55%, ~2 GPU-h
Claim: 8 virtual KV positions per skill (learned K/V at all 28 layers, ~1M params/skill, trunk frozen, requires_grad=False),
trained with ordinary CE on cue-absent prompts (W0 recipe: scripts/w0_train.py gradient path, never imported), act as an
opaque task address: present = SET, kept = HOLD, swapped = SWITCH, removed = CLEAR (KV restored bitwise). Why here: this
is the GPT-2 v8 lineage (state, not text; transplant 28/32) on the real trunk, and the two Qwen latent-cache failures
were about VALUE binding, which this design deliberately does not attempt (task address only, per astra's definition).
Blunt: this is prefix-tuning; the science is in the matched-KV hold/switch/clear/transplant dynamics, not the training.
Test: train on 256 seeded lists (disjoint from test), 300 steps, one seed; evaluate as in #1 with the same 64 lists and
decisions; transplant = insert the donor's prefix at a matched decision. Pass: same floors as #1; additionally the
DONOR-prefix arm must follow the donor >=48/64 and a random-init prefix of equal norm <=16/64 (rules out "any prefix
perturbs into sorting"). Fail: <48 or breakage >1. Unlocks: the actuator for #5 with an address the controller can emit
as a softmax over {A,B,OFF}; the state-transplant claim the internal wave never ran.

### 3. ONE-SHOT KV ADDRESS — edit the prompt's K/V once, then decode hook-free.  P(pass) 30%, ~1.5 GPU-h
Claim: adding a fixed direction ONCE to the K and V of the final prompt token(s) after prefill (cache steering; V-Steer
style value edits at selected heads) switches the skill for the whole answer, holds through 128 neutral tokens without
re-application (the only arm in FOCUS-1 that tests hold WITHOUT reapplication), and clears by restoring the original
tensors. Why here: check 30 truncation is the signature of sustained injection; one-shot KV edits do not touch decode
steps, and this is the cheapest genuine STATE test on the real trunk (transplant = copy edited K/V). Not residual
steering at decode. Test: directions = learned (per arXiv:2509.24169, 100 steps, CE through frozen trunk) OR mean-diff
from 64 paired triples (report both; learned is primary), applied to K,V at the last 1/4/16 prompt positions, 3 doses;
64 lists; arms as in #1 plus hook-free HOLD. Pass: addressed skill >=48/64, hook-free HOLD >=40/64, truncation <=1/64,
restore-clear = OFF behaviour and K/V max-abs delta 0 after restore. Fail: truncation >1/64 or <48 (then the family is
closed with check 30). Rules out: sustained-dose artifacts (no decode hook), prompt leakage (OFF has identical tokens).
Unlocks: a hold-without-reapplication mechanism -> the transient/recurrent claim in #5 becomes testable.

### 4. HEAD-GATE PATTERN SELECTION — the address is which circuits are on, nothing is added.  P(pass) 25%, ~2 GPU-h
Claim: a per-skill multiplicative gate vector over attention-head outputs (28x16 = 448 scalars in [0,2], learned by CE
through the frozen trunk, L1 to the identity) selects the skill on cue-absent prompts. This is the most literal Miller
analogue in the brief (select which stored circuits express; content-free; no additive vector) and the one no Stencil
program has run. Why it might work: CHG (arXiv:2505.13737) finds sparse task-sufficient sub-circuits with exactly this
object on frozen Llama-3; the "routing absorption" negative (arXiv:2603.02227) concerns co-trained Q/K/V and does not
apply to a frozen trunk. Blunt long shot: 448 multiplicative scalars may lack capacity to override a copy default when
no cue exists, and gate patterns could just damage the copy circuit (that is why OFF-vs-gate breakage is gated). Needs
~30 lines: a per-head scale hook in src/stencil/qwen3.py _Block (fake-trunk test first; identity gate must be bitwise
base-equivalent). Test: 64 lists; arms OFF / gate_A / gate_B / gate_A on B-cued prompt (override) / random gate at
matched sparsity. Pass: addressed skill >=40/64 (lower floor: capacity), random gate <=16/64, breakage <=2/64, gate
removal = OFF bitwise. Fail: <40 or breakage >2. Rules out: destruction-as-selection (random gate control), leakage.
Unlocks: a switch that is literally "which heads", i.e. Miller's claim in its cleanest engineering form; if #2 also
passes, compare additive-address vs gate-address on hold/clear cost.

### 5. CONTROLLER-IN-THE-LOOP — the internal-wave recipe emits A/B/OFF, recurrence vs latch.  P(pass) 30%, <=4 GPU-h
Claim: a 264k-class controller (src/stencil/wave.py shapes; gain head -> softmax over {A,B,OFF}) reading normalized h20
learns, from CE on completions across a 3-decision episode where the cue appears ONCE at episode start and is then
absent, to set, hold across neutral filler, and switch on a second cue — i.e. autonomous focus, not oracle control.
Why here: W0 proved CE-through-frozen-trunk training of a controller works (25->45%, WHERE/WHEN real); W1's null
recurrence had a diagnosed cause (|h20|~609 vs |s|~6, saturated gains) that the FOCUS-2 sketch already fixes
(separate normalization). Requires an actuator from #1 or #2 (this is why it is ranked after them, not below them in
value). Test: 128 training episodes (own seeds), 3 seeds x {stateless, latch, GRU}, 48 test episodes; report reset and
donor-state perturbation. Pass: any controller >=32/48 complete SET-HOLD-SWITCH episodes with breakage <=1/48; the
MEMORY claim additionally needs reset to cost >=10 episodes and GRU or latch > stateless by >=8 (McNemar p<=0.05).
Fail: <32 for all three. Rules out: "the controller reads the cue text" (cue absent at every measured decision),
"stateless suffices" (the W1 confound, now testable behaviourally). Unlocks: FOCUS-2 registration and the long-horizon
coding claim's first honest ingredient (a focus that persists without re-cueing).

Not ranked (long shots at 1.7B, stated for completeness): SAE-feature addresses (no Qwen3-1.7B SAE in repo; 2510.01246
finds no reliability advantage over mean-diff); oscillatory controls (only after #5's latch comparison); pure prompt
"menu" without spotlight (that is the S3-A0 negative: re-insertion loses at scale, and it is text).

## Recommended order and budget

0. (CPU/5 GPU-min) Competence pass for ASC vs REVERSE vs COPY with the lenient-exact scorer; this decides the pair.
1. #1 menu-spotlight (1 GPU-h) — proven actuator, cheapest, and its OFF-with-menu arm is the leakage control every
   later test needs.  2. #2 learned address prefix (2 GPU-h) — highest P(pass); gives the transplant test.
3. #3 one-shot KV address (1.5 GPU-h) — the hold-without-reapplication question.  4. #4 head-gate (2 GPU-h).
5. #5 controller (<=4 GPU-h), only if 1 or 2 passed.  Total <= 10.5 GPU-h; each result reviewed before the next.
Single recommended first test: #1, with Finding 0's pair/scorer fix — it is the only hypothesis whose actuator has a
sealed zero-breakage record on this trunk, and a fail there (with the menu-OFF control) closes prompt-spotlight skill
selection in one hour instead of six.
