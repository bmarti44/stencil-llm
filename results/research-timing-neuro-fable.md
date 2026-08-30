# Neuroscience research — how the brain times the press (fable, 2026-08-30)

Framing: our failure (abstention collapse of a learned WHEN-controller
under zero-false-press, with a perfect WHICH-chooser) is the predicted
optimum of the architecture. The brain never learns "when" as a free
binary from sparse outcome reward. It (a) runs a default rhythm and
learns only phase/gain, (b) triggers on a fast detector with its own
supervision, or (c) separates evidence from a criterion set by a
different mechanism.

## 1. Miller lab post-2023
- Han, Brincat, Buschman, Miller 2025, Neuron
  (https://doi.org/10.1016/j.neuron.2025.09.031): WM readout CYCLES with
  frontal theta phase — items occupy phases, readout is obligatory
  rhythmic sampling; the animal never decides when to press. Translation:
  phase-scheduled sampler — bias applied every k~4-8 steps with a
  raised-cosine envelope; learner chooses only slot allocation + gain
  (the sub-problem we already solve 130/130).
- Chen et al. 2026, Current Biology
  (https://doi.org/10.1016/j.cub.2025.11.072): spatial computing
  validated — control = moving spatially-structured INHIBITORY mask;
  default state is inhibited. Translation: two-sided mask — standing
  negative bias on non-ledger context, RELEASED over the target span;
  the null action then costs something, structurally removing the
  free-abstention optimum.
- Lundqvist et al. 2024 TiCS "Beta: bursts of cognition"
  (https://doi.org/10.1016/j.tics.2024.03.010); Lundqvist 2018 Nat
  Commun (https://www.nature.com/articles/s41467-017-02791-8); 2023 Nat
  Commun (https://doi.org/10.1038/s41467-023-36555-4): gamma bursts are
  ITEM-SPECIFIC and anticipatory (timed to expected need); beta is
  default inhibition, interrupted for readout.

## 2. Theta-gamma phase coding — "one oscillator per memory"
Supporting: Heusser et al. 2016 Nat Neurosci
(https://www.nature.com/articles/nn.4374) — theta phase of item gamma
codes serial position, fidelity predicts success; Bahramisharif et al.
2018 PLOS Bio — serial reactivation at item-selective sites; Qasim et
al. 2021 Cell + Zheng et al. 2024 Nat Hum Behav — human phase
precession.
Contradicting (strong): Lundqvist 2016/2018 — PFC gamma bursts sparse
and irregular, not one-per-cycle; Daume et al. 2024 Nature
(https://www.nature.com/articles/s41586-024-07309-z) — PAC functionally
central but NO strict phase segregation; PAC decreases with load; failed
replications of capacity prediction (PMC9496728); Keitel et al. 2025
arXiv:2507.15639 — field controversies.
VERDICT on Brian's idea: phase-tagging half is supported; the
independent-oscillator-per-item half is not. Correct reading: ONE shared
scheduler + per-item phase offsets. Translation: single "theta" counter
period T; each ledger sentence gets learned phase offset phi_i and gain;
bias = g * raised-cosine(phase_distance). Continuous dense-gradient
parameters replace the per-step Bernoulli. Do not hard-partition; let
windows overlap (Daume).

## 3. Basal ganglia / PBWM — how biology gets the FP/miss tradeoff right
- O'Reilly & Frank 2006 (Neural Comp 18:283), Frank et al. 2001: press
  is an OPPONENT Go/NoGo pair trained by dopamine RPE — misses and false
  presses train DIFFERENT populations; threshold is a separate network
  property (STN "hold your horses"), modulated online by conflict.
- Soni & Frank 2025 eLife (https://elifesciences.org/articles/97894):
  gating ops are themselves the units of RL with per-op RPE — per-op
  credit is what makes gating learnable.
- Chatham, Frank & Badre 2014 Neuron: output gating is a distinct
  selection-time operation.
- Traylor, Merullo, Frank, Pavlick 2024 (arXiv:2402.08211) — BRIDGE TO
  OUR SUBSTRATE: attention-only transformers trained on PBWM tasks
  spontaneously implement role-addressable input/output gating in the QK
  operation. Our additive attention bias is the correct homolog of BG
  output gating; the missing piece is BG's LEARNING architecture, not
  the gating primitive.
Translation: (i) opponent Go/NoGo press head, symmetric loss; (ii) keep
the FP constraint OUT of the training loss — train a calibrated evidence
score, set the operating criterion post-hoc (signal-detection criterion
shift); our 14/14794 is a criterion pathology masquerading as a policy
failure; (iii) per-op credit via local proxy (did the target ledger
token's logprob rise?).

## 4. Neuromodulation as the press signal
- Cholinergic transients (Howe et al. 2013 J Neurosci; Gritton et al.
  2016 PNAS; Sarter & Lustig 2020): sub-second PFC ACh transients occur
  ONLY on hit trials, largest on incongruent hits; optogenetic transient
  converts miss->hit. The press is a bottom-up cue DETECTOR with dense
  local supervision, not an outcome-trained policy.
- Phasic LC/NE (Aston-Jones & Cohen 2005; Vazey et al. 2018 PNAS; Sales
  et al. 2019 PLOS CB; Bouret & Sara "network reset"): one-shot,
  self-terminating, REFRACTORY burst; precision-setting interrupt.
Translation: train the press head as a supervised detector on ~10^4
per-step proxy labels ("a ledger fact is due now": entropy spike,
ledger-attention-mass drop, top-1/ledger mismatch, entity-slot opening)
— abstention may be gradient starvation; enforce the FP budget through
DYNAMICS (refractory period R, fixed decaying burst envelope), not the
loss.

## 5. Sharp-wave ripples — event-triggered, not clock-triggered
- Yang ... Buzsaki 2024 Science
  (https://www.science.org/doi/10.1126/science.adk8261): awake SWRs fire
  at STATE CHANGES (reward consumption); content selected by
  reactivatability; trigger and target decided by DIFFERENT mechanisms —
  the factorization we already have (perfect chooser, broken timer).
- Joo & Frank 2018 Nat Rev Neuro; Norman et al. 2019 Science (human
  ripples precede recall by 1-2s); Cordoba et al. 2025 Neuron — only
  LARGE ripples drive reactivation; amplitude is the functional
  variable.
Translation: allow presses only in decoder state-transition windows
(clause/sentence boundary, hidden-state velocity spike, confidence
drop) — cuts the opportunity set 14794 -> ~500-1500, raising base rate
10-30x; make the press GRADED in amplitude within permitted windows.

## Top-3 translations, ranked
1. Kill the binary press: default rhythm + learned phase/gain per ledger
   item (Han 2025; Fiebelkorn & Kastner 2019; Lundqvist). The controller
   never decides whether — only where in phase and how strongly. Reuses
   the proven 130/130 chooser; converts sparse discrete to
   dense-gradient continuous. Watch: load smearing (Daume) — mitigate
   with gain, not hard slots. Cost: LOW.
2. Cue-detector press head with dense local supervision + refractory
   burst (Sarter ACh; phasic LC; Buzsaki state-change triggering).
   Directly tests whether abstention was gradient starvation. Cost:
   MEDIUM (build proxy labels).
3. Opponent Go/NoGo head, post-hoc criterion, per-op credit (PBWM; Soni
   & Frank 2025; Traylor 2024). Most likely mechanistic explanation of
   the failure: a single-unit terminal-credit gate under hard zero-FP
   loss is SUPPOSED to go silent. Cost: MEDIUM.
Honorable mention: invert the default (standing negative bias on
non-ledger context, released over the chosen span) — the null action
then costs something.

(Full citation list preserved in the session transcript; key DOIs/URLs
inline above.)
