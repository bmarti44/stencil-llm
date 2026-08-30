# INTERNAL-WAVE program report

**Question:** can a small trained controller, riding a frozen model and
generating the attention field natively, govern long coding sessions —
the Miller wave produced inside rather than injected from outside?
**Answer: YES — SEALED WIN, causal attribution holds.** On 96 sealed
val sessions, the stateless wave reaches closure 1.488 (adherence
25.2% -> 44.8%), beating the hand-built oracle (38.3%), its proxy twin
(37.4%), and — for the first time in the project — text re-insertion
(43.0%, which FAILED the validity rule with 30 broken works while the
wave passed, parse rate improved 84.8 -> 92.7). Causal re-test at
seal: wave raw gain 238 vs proxy 149 (+89), both valid. VAL EXPOSURE
SCOPE (sol audit, 276/276): every prefix-active work contained BOTH
the unseen ledger rendering AND the familiar training-format sentence
in-context — the seal demonstrates rendering-robust val performance,
NOT format generalization (that claim is retracted); the comment rule
type is a complete hold-out present in 96/96 sessions, with its
per-type performance recorded in the reproduction audit.

## Registered ladder and outcomes

| Rung | Outcome |
|---|---|
| Plan (checkpoint i) | Dual-cleared after 4 sol rounds + fable round 1 (8 edits): matched-control causal design, canonical reference builder, field-parameterization ceiling, feedback_mode=none |
| W0.0 reference builder | FROZEN at 178/178 verified canonical adherent completions (0 failures) |
| W0.05 field ceiling | A2 (peak-normalized, beta 2 — the proven dose) selected: correct-position CE improve 72.7%, wrong-position degrade 7.9% (after an instrument fix: run 1's control pressed the ledger header), replay validity dU +18/+22 |
| G-W0a connectivity | ALL PASS incl. detach self-test; zero field bitwise base-equivalent |
| W0 training | Wave (CE-through-trunk) and matched proxy twin (identical module/actuator/data/seeds, proxy labels): held CE improve 36.2% vs 4.1% |
| G-W0b | Formally FAILED (30.8% vs 50%); retired by sol ruling as a malformed diagnostic (redundant; my "provably impossible" defense was itself retracted as overclaim) |
| G-W0c + ablations | PASS 36.2%; binding-clean: K-perm keeps 9.8% of gain (WHERE real), gain-perm 32.5% (WHEN real), uniform 39.7% (selectivity real) |
| W0 dev replay | Wave closure 1.119 (adherence 29.1 -> 47.1), ZERO paired broken, parse rate 88.3 -> 98.9 IMPROVED; proxy closure 1.0 converging token-identically onto the oracle (92/94 works, verified); causal margin +5 adherence with zero breakage (sol's registered wording) |
| W1 recurrence | Held CE 34.6% PASS; BOTH temporal probes NULL (permute -0.04%, reset +0.01%): STATELESS SUFFICES under the frozen H3 architecture — fable's mechanism: state numerically invisible to the readout (|h20|~609 vs |s_t|~6; saturated gain logits); no W2 transplant (nothing state-borne to transplant); caveat: the architecture plausibly suppressed state learning — a rescaled-state design is future work |
| Sealed validation (val split: held-out sentence format + novel rule type; one attempt) | **SEALED WIN**: headroom 0.131 binds; wave closure 1.4875, dU 196 (valid; 21 broken), parse improved; causal re-test HOLDS (238 > 149, both valid); oracle 38.3 / proxy 37.4 / reinsertion 43.0 validity-FAIL |

## The three findings that matter

1. **The differentiable press works and out-governs its teacher.** Trained
   only by "make the adherent continuation likelier," through the frozen
   trunk's attention path, the 264k-parameter wave beat the hand-built
   oracle press on dev at zero validity cost — with ablation-proven
   WHERE/WHEN/selectivity.
2. **The matched control's supported statement (sol's registered
   wording):** with the identical continuous actuator, proxy training
   succeeds (converging token-identically onto the oracle), while CE
   training adds five raw successes on dev and 89 at seal with better
   measured validity. Actuator causality in isolation was NOT tested
   (no same-checkpoint discrete-actuator counterfactual was run).
3. **Recurrence: reset and cyclic-next-session-donor perturbations
   were null under teacher-forced held CE; behavioral state dependence
   was not tested** (replay skipped by ruling once the registered CE
   conjunction had already failed); no W2 followed. The
   scaling/saturation measurements (|h20|~609 vs |s_t|~6; saturated
   gain logits) make suppressed state learning PLAUSIBLE, not proven.
   The Miller-transplant question remains open for a rescaled-state
   successor (citation lineage: research-wave-prior-art.md).

## Prior art

Per the committed search (results/research-wave-prior-art.md): every
ingredient has published neighbors (PASTA/InstABoost attention biasing —
all training-free; Guiding Giants/CAST controllers — scalar/vector,
non-recurrent, residual-space; READ sidecars — PEFT, not decoding-time);
the supported search observation is: no identified prior work trains
a per-step positional attention-bias field with gradients through a
frozen trunk's pre-softmax path. The search's full conjunction included
a RECURRENT controller and a zero-validity evaluation; this program's
sealed finalist is STATELESS and recorded 21 paired breaks at seal, so
that full conjunction was NOT realized here — stated per the committed
search's own caveats (two flagged unread items).

## Process record

Checkpoints i-iii dual-reviewed (6 sol rounds — wave-plan-review{1-4},
w0-review, w1-review — and 3 fable verification rounds through
checkpoint iii, artifact-enumerated; closing rounds appended in
WORKLOG); one instrument error caught and fixed before its verdict (the ceiling
wrong-position control); G-W0b FORMALLY FAILED and was retired
POST-RESULT by reviewer ruling as a malformed diagnostic — my
"impossible bar" defense was retracted on review and no impossibility
was established; sealed job
fail-closed with pinned hashes (w_seal.py sha256 2a0ef6480d6a11cd...,
pinned in WORKLOG before execution); all
numbers reproduce from artifacts force-committed to the repo
(results/qwen evidence JSONs + seal marker + logs) and from the
deterministic reproduction audit (w-seal-audit.json: full-length
output sha256 per work, per-work paired records, per-type incl.
comment-class performance), whose regenerated outputs are
hash-verified against the sealed run's recorded values — REPRODUCTION
EXACT, 0 mismatches across all 480 works x 5 arms.
