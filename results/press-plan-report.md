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
| T0.3 press cost (paired single-press, n=220/condition) | B = +0.27 dU per correct press; wrong-SPAN press costs -0.33 (2.3% broken works); the ONE tested mistiming perturbation — a single same-entry press at fire_step+3 — cost zero. (T0.3b later showed other provenance-valid blind-time presses ARE harmful; "timing errors are cheap" holds only for the exact tested perturbation) |
| T0.4 theta sweep | Superseded by the certification anatomy (recorded, not run — the constraint-vs-representation question was answered more directly) |
| T0.5 event-triggered baseline | PASS: reactive pressing (trigger on checker feedback, zero learning) recovers 0.875 of the oracle's recovery on post-violation opportunities; session adherence 44.3 -> 50.0. REGISTERED RECIPE COMPONENT |
| G0 certification (zero-new-training policy, sealed block D) | FAIL k=149/160, decomposed: 71/160 sessions with FALSE SELECTIONS (the policy's error evidence; U95 = 0.512 >> 5%) plus 79 fixture non-vacuity misses (1 overlap). With real same-type hard negatives, the absolute cosine score cannot detect liveness when the live sentence is absent — discrimination was RANKING-only (the bi-encoder ceiling the research sweep predicted) |
| T1 trained candidate-or-null (hard negatives, decision-aligned margins) | On the reused (unsealed) calib screen, hazard leakage fell 14/17 sessions -> 1/17 (92.9% relative) — large and real, but not certification-grade (1/17 -> U95 ~25% >> 5%); registered fallback consumed and failed (2/17); LINE CLOSED |
| T2 controller-state bakeoff (oscillator vs controls, frozen contract) | No contender reached zero leakage -> no pilot, no block. Science (on the third-use, 17-hazard-session calib set): the input-blind free-running oscillator ties the trained oscillator and GRU at 2 leaking sessions and beats EMA (3) and static (5) — state coupling added nothing measurable; pure statelessness was worst; joint retraining mildly hurt vs the plain T1 head (1/17) |
| T3 blind rhythm (gated by the T0.3b wrong-type audit) | GATE NEGATIVE: all four (P, g) cells have expected dU < 0 (-0.03 to -0.125; harm and broken-work rate scale with gain, 1% -> 4.5%). Grid skipped; LINE CLOSED. (The audit's per-press moment-class counts were computed with a token/character unit bug and are withdrawn; the cell-level dU gate does not use them and stands) |

## The three findings that matter

1. **The autonomy boundary is now mapped from four sides.** Autonomous
   pressing failed its registered gates as absolute discrimination (the
   registered cosine policy found no transferable liveness threshold —
   a statement about THESE policies and gates, not a nonexistence proof
   for the representations), as trained discrimination (92.9% better on
   the calib screen, still leaks), as learned state (a fixed clock ties
   it), and as blind scheduling (net harmful). What SURVIVES
   is timing from STRUCTURE (the parser knows the moments) and timing
   from FEEDBACK (the checker knows the failures). At this model scale
   and regime, the wave must be clocked by the environment, not by a
   learned internal judgment of relevance.
2. **Two deployable operating points, individually proven.** Structured
   pressing (parser moment + active-ledger provenance + authoritative
   span, the T2b "oracle": +14.5 val adherence, carrying its previously
   reported ~1.7% paired validity tax — 7 parse / 11 exec losses over
   409 works, so the registered zero-loss gate was NOT met) and
   reactive pressing (0.875 of recoverable headroom, zero learning).
   These are NOT a tested composition: reactive's press set is a strict
   subset of structured's (flagged active types vs all active types at
   parser moments), so where both are available structured subsumes
   reactive; reactive is the operating point for feedback-only
   environments. This is the Miller stencil clocked by syntax and error
   signals — a candidate deployment for code, where parsers and
   checkers exist; composition and deployment remain untested.
3. **Provenance guards one error class, not safety.** T0.3 measured
   that a non-authoritative span press is the expensive error
   (-0.33/press) and a single off-by-3 same-entry press is free.
   Structural provenance eliminates the first class. But T0.3b showed
   provenance-valid presses at BLIND times are still net harmful in
   every cell (broken rates to 4.5%) — semantic mistargeting among
   authoritative entries is real. Safety therefore requires provenance
   PLUS moment/type-matched timing from a parser, checker, or validated
   selector — which is finding 1 restated as a safety requirement.

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

Preregistration with mechanical gates throughout. Review counting
convention (reproducible): PRESS-PLAN-era sol artifacts committed under
results/ through closing round 1 = 18 (16 substantive reviews + 2
one-word acks): press-plan-review{1-5}, g0-review, impl-review{1,2},
t1-prereg-review{1-3}, s0x2-amend, a1-ack, t2t3-review{1-4},
press-close; subsequent closing-verification rounds are recorded in
WORKLOG. Fable rounds per WORKLOG = 9 plus its closing verifications. Every high/critical finding
either fixed or ruled; two reviewer catches prevented sealed-block
burns (degenerate thresholds; value-vs-span certification semantics);
one administrative block void (A) disclosed; all seed blocks and their
single-use discipline honored (B, C, E, and validation untouched; C's
provenance-ceiling certification was retired before use); T0.4 formally
closed as superseded (WORKLOG); every
number in this report reproduces from pinned seeds and committed
artifacts (results/qwen/t0-*.json, t2-bakeoff.json, g0-certify-D.json,
t1-gates*.json, press logs, WORKLOG decision trail).
