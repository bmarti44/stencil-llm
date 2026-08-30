# T2 + T3 PREREGISTRATION v3 — post checkpoint-iii round 1 (2026-08-30)

Round 1: fable CLEARED with 4 mandatory edits; sol NOT CLEARED with 5
HIGH. All folded. Convergent items: wrong-type press cost unmeasured
(both), reactive arm missing (both), time-base and probe fixes,
explicit block re-binding.

## T2 — controller-state bakeoff (head-only; frozen contract)

Claim being tested (labeled honestly per sol): OPPORTUNITY-INDEXED
RECURRENCE WITH REAL-TIME PHASE — state updates at timing-fire events,
with phase advanced by the ACTUAL elapsed decoding steps between events
(fable: event-count clocks give omega 1-4 ticks and are unlearnable;
this bakeoff must test Brian's hypothesis, not the data plan). It is
not a token-by-token oscillator; that remains the internal-wave
program's question.

Training contract (frozen; sol item 1):
- State reset per SESSION; events ordered by (work_turn, step); phase
  advance z <- rho^D * exp(i*omega*D) * z then u-update, with D = step
  gap within a work turn and a REGISTERED inter-turn increment D=32.
- SCORE FROM THE PRE-UPDATE STATE, then write (the controller must not
  degenerate into a feed-forward layer).
- Batches = 8 whole sessions; loss = per-event CE+A1 margins summed,
  normalized by event count; full BPTT (sequences <= 19 events).
- Warm start: shared T1 components from t1-head.pt (round-1 head, NOT
  the fallback — registered), all trainable; optimizer/epochs/seed as
  the T1 recipe.
- Parameter accounting: CONTROLLER-specific parameter counts per
  contender within +-10% of each other, recorded in WORKLOG before
  training (the shared T1 head is excluded from the match).
- Contenders (a)-(e) as v1, all on the same D-clock (incl. the
  null-oscillator).

Metric and verdict (mechanical): hazard-session leakage on calib-hard
(primary), tie-breaks in order: leaking EVENT count, active recall,
fewer controller parameters. Screens: address >= 90%, recall >=
0.41640866873065013, A1 margins 90/90.

Probes (sol item 2 — CE-based, defined at zero leakage; scramble op
frozen: permute the oscillator's phase components across events with
torch.Generator seed 0):
- inert-token insertion (0/32/128; one small GPU pass for probe
  events): held-out mean CE_inserted <= 1.10 * CE_original;
- phase scramble: CE_scrambled >= 1.20 * CE_original AND >= 1 decision
  change (a phase code MUST be hurt).
The oscillator (a) wins ONLY if it beats (b)-(e) on the primary metric
chain AND passes both probes; ties ship the non-oscillatory contender.

Post-screen path (sol item 3, verbatim rules):
- Only the mechanically selected winner may use block B (explicit
  re-binding amendment: block B, previously bound to the T1 finalist,
  is re-bound to the T2 winner — named in WORKLOG before touching).
- Pilot eligibility = zero calib leakage + all screens.
- Block-B risk failure closes T2 (no runner-up certification).
- An A1 coverage VOID may consume block E once for the IDENTICAL
  frozen policy; a second void closes T2 inconclusively.
- Block-B pass -> the registered behavioral dev table (certification
  proves safety, not usefulness).
- Nonzero calib leakage for every contender -> ranking reported as
  science; no generation pilot; no block consumed.
Disclosure: calib-hard 13.14M is on its third selection use (T1 round
1, T1 fallback, T2 screen); block-B certification remains the guard.

## T0.3b — wrong-type authoritative press audit (GATES the T3 grid;
both reviewers)

t0_cost.py measured same-entry mistiming (free) and non-authoritative
wrong spans (costly); it NEVER measured pressing another entry's
authoritative span — which round-robin does at most scheduled steps.
Paired audit using the ACTUAL four (P, g) schedules on trace-seed
sessions: classify each scheduled press as (i) matching-type moment,
(ii) wrong-type authoritative at a moment, (iii) no recognized moment;
measure paired Delta-U, parse/exec loss, changed-output rate at both
gains, n >= 200 paired per gain. GRID LAUNCH RULE: the grid runs iff
at least one cell's schedule-frequency-weighted expected Delta-U > 0;
otherwise the rhythm line closes without the grid (and the
"safety by construction" wording is replaced everywhere by "provenance
safety by construction; semantic mistargeting measured separately").

## T3 — rhythm-default press (grid only if T0.3b clears)

Scheduler (exact, frozen): within each work turn, steps are zero-based
from the first generated token; a press occurs at every step with
step mod P == 0; the pressed entry is live-ledger entries in TYPES
order, indexed by (presses so far THIS work turn) mod n_live; the
ledger is fixed within a turn; n_live == 0 -> no press. No T2-supplied
gain/phase (sol: T2's event clock is incompatible; uniform gain g).
Grid: P in {4, 8} x g in {0.5, 1.0}.

Arms: base, rhythm, rhythm+reactive, REACTIVE (same-seed, seventh arm),
oracle, structured, reinsertion. The five rhythm-independent arms run
ONCE and are shared across the four cells (fable).

Decision table (judged arm = RHYTHM for the finalist rule):
- any cell: closure_rhythm >= 0.50 AND validity pass -> T3 finalist
  candidate (fresh preregistration for sealed validation; validation
  measures usefulness — no "certification-equivalent" language).
- best cell closure_rhythm in [0.25, 0.50) with validity pass ->
  marginal rule: marginal_closure :=
  (A_rhythm+reactive - A_reactive) / (A_oracle - A_base), raw
  numerators, same seeds; >= +0.10 -> finalist-candidate path for the
  COMBINED arm; else honest negative.
- any closure >= 0.25 with validity FAILING -> T4 trigger (preserved).
- else -> the rhythm line CLOSES; the program closes on the banked
  recipe.
Cell selection for any sealed run: only after the full grid, named via
fresh preregistration (multiplicity control = the sealed run itself).

## Accounting
No sealed blocks consumed by screens/T0.3b/dev replays. Block B
re-bound as above (explicit). Sealed validation 13.20M untouched; one
named finalist total.

## v3 ADDENDUM (sol round 2, four HIGHs; all frozen)

A. T2 architecture freeze: BEFORE training, WORKLOG records an
architecture/count table (or code digest) fixing per contender:
candidate-feature pooling, controller dims/activations, state routing,
rho/omega/tau parameterization + init, null-oscillator period, and the
warm-started head's extra-column init. Formal step contract:
  z_pre = transition(z_prev, D); logits = scorer(event, z_pre);
  z_next = write(z_pre, event).
Scramble op (frozen): permute phase components WITHIN each
(session, type, complex-component) group across that group's events,
preserving each event's magnitude; no cross-session or future-content
movement; torch.Generator seed 0. Inert CE bound (<= 1.10x) must hold
SEPARATELY at 32 and at 128 inserted tokens.

B. T2 screens/terminal table: winner metric stays target-hazard
leakage; PILOT ELIGIBILITY requires zero false-selection sessions
across ALL inactive candidate-bearing calib events (target-hazard
leakage reported separately — off-target leaks must not ride to block
B). Certification precedence: k_false > 3 is policy FAIL regardless of
coverage; only (k_false <= 3 AND n_h < 112) is VOID. T2-specific
behavioral table (T1's retrain fallback is consumed and unavailable):
closure >= 0.50 + validity pass -> finalist candidate; closure >= 0.25
with validity FAIL -> T4 trigger; validity-passing [0.25, 0.50) ->
partial result, T2 closes (no retraining); else close. Headroom >=
0.10 precondition with the one registered reserve re-draw preserved.

C. T0.3b estimator (frozen): >= 200 deterministic single-intervention
pairs per (P, g) cell; scheduled interventions selected in
(seed, work_turn, step) order from the UNPRESSED base trajectory
(which defines the schedule); each paired branch applies exactly one
press; expected_DeltaU_cell = mean over its pairs (category
frequencies are diagnostics only, never reweighted); U and BROKEN
exactly as T0.3.

D. T3 mechanical finalist selection (frozen before the grid): among
rhythm cells passing closure >= 0.50 + validity, select MAX closure;
ties -> lower g, then larger P. Partial path: the mechanically
selected best rhythm cell's COMBINED arm, which must itself pass the
validity rule to become finalist. T4 triggers inspect BOTH rhythm and
combined arms; a valid finalist takes precedence over any T4 trigger.
The post-grid preregistration RECORDS the mechanically selected cell
and validation machinery; it may not choose among cells after viewing
results.
