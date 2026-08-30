# PRESS-PLAN program report — autonomous press timing

**Question:** after TIMED-SELECTOR proved the spotlight mechanism and
precisely diagnosed its controller's failure, can the WHEN-to-press
decision be made autonomous? **Answer: no — not by discrimination, not
by learned state, and not by a blind rhythm, each closed at its
registered rule; but the program's diagnostics rebuilt the deployment
recipe on two proven components and mapped the autonomy boundary from
four sides.** One sealed block was consumed (D); B, E, and the sealed
validation seeds were never touched.

## Registered ladder and outcomes

| Rung | Outcome |
|---|---|
| T0.1/T0.2 trace + score matrix | The T2b failure mechanically explained: the legacy address max-score ranged over ALL candidate types — cross-type hits forced the zero-false-press theta to 185,850, strangling recall. Type-restricted addressing dissolves that failure class on-distribution (323/323 live-over-lookalike ranking) |
| T0.3 press cost (paired single-press, n=220/condition) | B = +0.27 dU per correct press; wrong-SPAN press costs -0.33 (2.3% broken works); wrong-MOMENT press of the right span costs ZERO. Timing errors are cheap; addressing errors are the only costly class |
| T0.4 theta sweep | Superseded by the certification anatomy (recorded, not run — the constraint-vs-representation question was answered more directly) |
| T0.5 event-triggered baseline | PASS: reactive pressing (trigger on checker feedback, zero learning) recovers 0.875 of the oracle's recovery on post-violation opportunities; session adherence 44.3 -> 50.0. REGISTERED RECIPE COMPONENT |
| G0 certification (zero-new-training policy, sealed block D) | FAIL k=149/160: with real same-type hard negatives, the absolute cosine score cannot detect liveness when the live sentence is absent — discrimination was RANKING-only (the bi-encoder ceiling the research sweep predicted) |
| T1 trained candidate-or-null (hard negatives, decision-aligned margins) | Cut hazard leakage ~93% (30/48 pressure sessions -> 1/17) — large and real, but not certification-grade (1/17 -> U95 ~25% >> 5%); registered fallback consumed and failed (2/17); LINE CLOSED |
| T2 controller-state bakeoff (oscillator vs controls, frozen contract) | No contender reached zero leakage -> no pilot, no block. Science: the input-blind free-running oscillator TIES every trained state controller — state coupling added nothing measurable; pure statelessness was worst; joint retraining mildly hurt vs the plain T1 head |
| T3 blind rhythm (gated by the T0.3b wrong-type audit) | GATE NEGATIVE: all four (P, g) cells have expected dU < 0 (-0.03 to -0.125; harm scales with gain; 0-12/200 scheduled presses hit a matching moment). Grid skipped; LINE CLOSED |

## The three findings that matter

1. **The autonomy boundary is now mapped from four sides.** Autonomous
   pressing fails as absolute discrimination (no transferable liveness
   threshold exists in the frozen representations), as trained
   discrimination (93% better, still leaks), as learned state (a fixed
   clock ties it), and as blind scheduling (net harmful). What SURVIVES
   is timing from STRUCTURE (the parser knows the moments) and timing
   from FEEDBACK (the checker knows the failures). At this model scale
   and regime, the wave must be clocked by the environment, not by a
   learned internal judgment of relevance.
2. **The deployable recipe is proven and cheap.** Structured pressing
   (parser moment + active-ledger provenance + authoritative span,
   the T2b "oracle": +14.5 val adherence) layered with reactive
   pressing (0.875 of recoverable headroom, zero learning) — inside the
   measured cost asymmetry (mistimed right-span presses free; wrong
   spans are the only expensive error, which provenance guards
   eliminate structurally). This is the Miller stencil clocked by
   syntax and error signals — deployable today for code, where parsers
   and checkers exist.
3. **The wrong-span asymmetry reframes safety.** T0.3's measurement
   (wrong moment: free; wrong span: -0.33/press) means press-timing
   policies need no safety machinery at all IF span provenance is
   structural — the entire zero-false-press apparatus that strangled
   two programs guarded a boundary that provenance makes unreachable.

## Standing for the Miller program

Proven across programs: the wave's EFFECT (attention-gain press selects
stored behavior, at toy scale and on a frozen 1.7B code model); the
wave's ADDRESS (ranking live over lookalikes, 100% when the live entry
exists); the wave's CLOCK from structure and feedback. Closed honestly:
the wave's clock from learned relevance, learned state, or free-running
rhythm at this scale. The internal-wave question — a trained recurrent
state generating the bias natively, the toy-phase transplant result
scaled up — remains open and is now sharply posed: it must beat
structure+feedback clocking, a high bar this program quantified.
Flagged registration for the steering case: obligations with no checker
and no parser moment (pure user steering) are outside every current
benchmark; the banked recipe does not cover them and no autonomous line
survived to try.

## Process record

Preregistration with mechanical gates throughout; 14 sol review rounds
and 7 fable verification rounds across plan, G0, implementations,
amendments, and preregistrations; every high/critical finding either
fixed or ruled; two reviewer catches prevented sealed-block burns
(degenerate thresholds; value-vs-span certification semantics); one
administrative block void (A) disclosed; all seed blocks and their
single-use discipline honored (B, E, validation untouched); every
number in this report reproduces from pinned seeds and committed
artifacts (results/qwen/t0-*.json, t2-bakeoff.json, g0-certify-D.json,
t1-gates*.json, press logs, WORKLOG decision trail).
