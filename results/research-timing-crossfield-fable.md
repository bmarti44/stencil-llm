# Cross-field research — making autonomous pressing work (fable, 2026-08-30)

Lane: dynamical systems / control theory / optimal stopping / cognitive
architectures / left-field. Question: mechanisms for the WHEN-to-press
decision after T2b's honest negative (14/14794 presses under
zero-false-press).

## Lane 3 (reframes everything): is zero-false-press the right constraint?

Citations: Chow (1970, IEEE Trans. Info. Theory); Rigollet & Tong, NP
classification (2011, JMLR, https://arxiv.org/pdf/1102.5750); Tong, Feng
& Li, NP umbrella algorithm (2018, Science Advances,
https://www.science.org/doi/10.1126/sciadv.aao1659); Geifman & El-Yaniv,
SelectiveNet (2019, ICML,
https://proceedings.mlr.press/v97/geifman19a.html).

The controller's collapse is textbook-predicted: zero-false-press is the
Neyman-Pearson alpha=0 corner; unless the ROC has positive TPR at exactly
FPR=0, the only feasible policy is "never press."

Arithmetic with our numbers: needed press worth +14.5 adherence; false
press breaks code with p~1.7%; let C = adherence-cost of one broken code.
Bayes press threshold p* = 0.017C / (14.5 + 0.017C). At C=100, p*~0.105;
at C=500, p*~0.37. Zero-false-press asserts C=infinity. With a
deterministic checker, false presses are detectable/correctable, capping
C low. The safety rule, not the controller, is the likely bug.

Adaptation: (a) NP classification at alpha=1-5% false-press via the
umbrella algorithm (order-statistic threshold on held-out negative
scores — ~20-line change, no retraining); or (b) expected-cost threshold
after measuring C empirically via deliberately injected false presses.

Falsification (cheapest overall): inject deliberate false presses ->
empirical C; sweep press threshold on the ALREADY-TRAINED controller's
scores, plot adherence vs threshold. Peak at nonzero press rate =>
constraint was the failure cause; monotone toward abstention => the
score carries no signal and richer mechanisms are needed.

## Lane 2: event-triggered / intermittent control — press on checker feedback

Citations: Heemels, Johansson & Tabuada, event/self-triggered control
(2012, IEEE CDC,
https://kth.diva-portal.org/smash/get/diva2:586391/FULLTEXT02); Gawthrop
et al., intermittent control (2011, Biol. Cybernetics,
https://link.springer.com/article/10.1007/s00422-010-0416-4);
Alvarez-Martin et al., event-driven adaptive intermittent control (2023,
https://dx.doi.org/10.1177/09596518221147340).

Current controller is open-loop. ETC presses when a measured error
crosses a bound; the environment's deterministic checker is a free error
signal no arm consumes. Variants: (a) reactive ETC — press for the
implicated obligation when checker flags it (detection, not prediction;
near-zero false press by construction; one step late); (b) self-triggered
— schedule next press from the (deterministic/learnable) recurrence
clock, checker cancels/corrects. Add a refractory period.

Falsification: rule-based reactive trigger, no learning. If pressing one
turn after first violation recovers >8 of the +14.5, the learned
controller was solving the wrong problem; if violations are
unrecoverable once flagged, ETC-on-feedback is dead -> predictive timing.

## Lane 1: per-obligation oscillators — phase channels, WLC, CPGs

Citations: Lisman & Idiart (1995, Science); Lisman & Jensen, theta-gamma
code (2013, Neuron,
https://www.cell.com/neuron/fulltext/S0896-6273(13)00231-6); Rabinovich
et al., winnerless competition (2003, PRE,
https://pubmed.ncbi.nlm.nih.gov/12636530/; 2014 Frontiers,
https://www.frontiersin.org/journals/systems-neuroscience/articles/10.3389/fnsys.2014.00220/full);
Ijspeert, CPG review (2008, Neural Networks); Miyato et al., AKOrN (ICLR
2025, https://arxiv.org/abs/2410.13821); Lundqvist ... Miller, gamma/beta
bursts (2016, Neuron,
https://www.sciencedirect.com/science/article/pii/S0896627316001458).

Brian's "oscillator per memory" = Lisman-Idiart multiplexing (items as
gamma subcycles in a theta cycle; capacity 4-8; order by phase).
Miller-consistent: Lundqvist bursts say WM is discrete oscillatory
reactivation — periodic brief spotlighting is arguably MORE faithful than
sustained bias. Skeptical note: an open-loop oscillator is just a
periodic press schedule; it only beats a cron job if phase is ENTRAINED
by session events.

Adaptation: theta_k per obligation; dtheta_k/dt = omega_k + entrainment
from (i) checker feedback implicating k (phase reset), (ii) surface-cue
similarity, (iii) Kuramoto REPULSION between the K phases (anti-aligned
coupling per AKOrN) so obligations never collide. Press while
cos(theta_k) > threshold; scale bias by cos(theta_k) — soft spotlight
dissolves the zero-false-press cliff if damage is superlinear in bias
magnitude (measure it). Prior program proved oscillator state is
trainable + transplantable.

Falsification: null oscillator first (free-running, periods from
generator statistics, no entrainment). Also mistimed-bias magnitude sweep
(25/50/100%) -> code-break rate vs magnitude.

## Lane 4: cognitive architectures — when does a rule fire

Citations: ACT-R utility learning (Belavkin & Ritter OPTIMIST, ICCM 2004,
https://acs.ist.psu.edu/papers/belavkinR04.pdf); Laird, Soar (2022,
https://arxiv.org/pdf/2205.03854); Einstein & McDaniel, prospective
memory multiprocess theory (2005,
https://journals.sagepub.com/doi/10.1111/j.0963-7214.2005.00382.x,
https://pubmed.ncbi.nlm.nih.gov/16131267/).

(1) ACT-R: noisy utility competition + reward-driven updates from
environmental payoff (our checker!). Softmax-with-noise makes abstention
collapse impossible by construction. (2) Soar: an impasse is an EVENT
that spawns deliberation, not silence — our controller conflates "don't
know" with "don't press". Add an impasse band between two thresholds:
in-between -> cheap information-gathering action (re-read ledger) then
re-decide. (3) Prospective memory: focal cues retrieve spontaneously;
nonfocal cues need costly monitoring. Engineer the LEDGER PHRASING so
cues are focal (overlap what the model generates at press time) — a data
fix, not a mechanism fix.

Falsifications: 3-parameter online utility learner over 200 sessions;
focality-vs-classifier-accuracy correlation on EXISTING logs (one
afternoon, zero GPU).

## Lane 5: left-field, evidenced

- Astrocyte gating (Kozachkov PNAS 2023,
  https://www.pnas.org/doi/10.1073/pnas.2219150120; PLOS CB 2024):
  honest reading — a leaky-integrator gain field; collapses into Lane
  1's soft-bias variant. Low priority.
- Traveling waves (Muller et al. 2018, Nat Rev Neuro,
  https://www.nature.com/articles/nrn.2018.20): bias wave sweeping the
  ledger token axis = Lisman-Idiart with zero per-obligation parameters,
  order fixed by ledger order.
- Flip-flop attractors (Sussillo & Barak 2013; 2024 review
  https://pmc.ncbi.nlm.nih.gov/articles/PMC11004305/): tiny RNN holds
  "armed/discharged" per obligation — fixes controller statelessness.
  Cheap first check: were false presses mostly re-presses?
- Active inference precision (2024,
  https://www.ncbi.nlm.nih.gov/pmc/articles/PMC11431491/): vocabulary,
  not mechanism; equivalent to Lane 3 threshold math.

## Ranked top 3

1. Recompute the constraint (Lane 3) — a day's work on existing
   artifacts; may recover most of +14.5 with the controller already
   trained. Do first.
2. Event-triggered pressing on checker feedback (Lane 2) — no-training
   baseline directly tests whether late pressing recovers adherence.
3. Per-obligation phase channels with checker entrainment + soft bias
   (Lane 1) — the scientifically interesting one; earns its machinery
   only if the null-oscillator and soft-bias tests pass.

Through-line: four of five lanes independently indict (a) the hard
zero-false-press constraint and (b) the open-loop stateless trigger that
ignores checker feedback. The oscillator is real and precedented — as
the scheduler ON TOP of a fixed constraint and a closed loop, not the
rescue.
