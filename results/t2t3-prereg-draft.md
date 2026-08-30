# T2 + T3 PREREGISTRATION — draft for checkpoint-iii review (2026-08-30)

Context: the discriminative line closed at its registered stop rule
(WORKLOG autopsy: trained head cut hazard leakage ~93% but 1-2/17
sessions still leak; zero-error screen saved block B). T2
(controller-state bakeoff — Brian's oscillator, controlled) and T3
(rhythm-default) are the remaining autonomous lines. Blocks B and E are
untouched and available; the banked recipe (structured + reactive) is
unaffected.

## T2 — controller-state bakeoff (head-only, cached features; frozen)

Question: does PERSISTENT STATE (an oscillator per ledger entry, or any
cheaper state) beat stateless heads at the press decision — attacking
the closed line's residual failure (absolute liveness at hazards) with
memory rather than a bigger discriminator?

Data: the collected feature corpora (t1-train/trace0; calib for
screens) EXTENDED with per-event history: for each event, the ordered
sequence of prior events in its session (features only, no new GPU).
State evolves over the event sequence within a session.

Contenders (equal trainable-parameter budgets +-10%, all consume the
same per-event inputs [h20, typed cand_feats] plus their own state):
(a) oscillator bank: per ledger TYPE a 4-d complex state z; update
    z <- rho * exp(i*omega) * z + u(event features); press scorer reads
    Re/Im(z) alongside the T1 head's logits; rho, omega, u trainable;
(b) static per-type embedding + MLP (stateless control);
(c) leaky/EMA integrator per type (tau trainable);
(d) keyed latch / tiny GRU (16-d per type);
(e) null-oscillator: free-running phase, period fixed from generator
    statistics, no input coupling.
All heads share the T1 architecture downstream (candidate-or-null
listwise + decision rule; warm-start; same loss incl. A1 margins); the
state vector is concatenated to h20 at the NULL/query heads only.
Optimizer/epochs/batch/seed: identical to the T1 frozen recipe.

Metric (registered): hazard-session leakage on calib-hard (the exact
statistic that closed the T1 line: sessions with >= 1 above-threshold
non-NULL decision at a hazard event, denominator n_h) AND active recall
(floor 0.41640866873065013). Verdict is mechanical:
- winner = fewest leaking hazard sessions; tie-break higher recall;
  second tie-break fewer parameters.
- The OSCILLATOR (a) earns a generation pilot ONLY if it (i) has
  strictly fewer leaking sessions than ALL of (b)-(e), (ii) passes the
  probes below, (iii) recall >= floor. A tie with any of (b)-(e) ships
  that contender and records the tie.
Probes (G0-amendment criteria): inert-token insertion (0/32/128 before
decision moments — recompute features for probe events only, one small
GPU pass) must degrade (a)'s metric < 10% relative; phase-scramble at
eval must degrade it >= 20% relative (a phase code MUST be hurt;
otherwise the phase is decorative and (a) cannot claim the win
regardless of ranking).
Certification path if any contender reaches zero calib leakage: name
it, certify on BLOCK B under A1 semantics (floor 112/160). Otherwise
T2 reports the ranking as science (no certification) and the
autonomous-press program closes to T3 only.

## T3 — rhythm-default press (generation pilot; the Miller-faithful
line; runs regardless of T2's outcome, gated by T2's verdict only for
its slot mechanism)

Mechanism: NO press decision at all. A scheduler of period P in {4, 8}
steps cycles through the LIVE ledger entries (round-robin by ledger
order; the T2 winner supplies per-entry gain/phase only if T2 produced
one — else uniform gain); at each scheduled step the spotlight presses
the CURRENT entry's authoritative span with soft bias
beta_soft = beta * g, g in {0.5, 1.0} (2x2 grid = 4 dev replays, all
judged by ONE registered table — multiplicity handled by naming the
best cell for any sealed run only after the grid is complete and only
via a fresh preregistration).
Safety by construction: only authoritative ledger spans are ever
pressed (provenance guard structural — no liveness decision exists to
get wrong; the T0.3 asymmetry says mistimed right-span presses are
~free, measured at beta; the beta_soft=0.5*beta cell probes the softer
regime).
Arms per dev replay (13.10M, s0 unextended): base, rhythm,
rhythm+reactive (rhythm plus the registered reactive component),
oracle, structured, reinsertion.
Registered table per cell (closure vs oracle from raw paired
numerators; headroom precondition >= 0.10; T0.3 validity rule):
- any cell with closure >= 0.50 AND validity pass -> T3 finalist
  candidate (fresh preregistration for a sealed validation follows);
- best cell closure in [0.25, 0.50) with validity pass -> the line
  records a partial positive; rhythm+reactive's marginal contribution
  over reactive alone decides (>= +0.10 closure -> finalist candidate
  path; else honest negative);
- else -> the rhythm line CLOSES (honest negative #3) and the program
  closes on the banked recipe.

## Accounting
No sealed blocks consumed by T2 screens or T3 dev replays. Block B
reserved for a T2 zero-leakage contender or a T3 finalist's
certification-equivalent (a T3 finalist needs no false-selection
certification — it makes no selection decisions; its sealed test IS
the validation run). Sealed validation (13.20M) untouched; one named
finalist total, per the plan.
