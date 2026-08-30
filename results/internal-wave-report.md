# INTERNAL-WAVE program report — DRAFT (sealed verdict pending)

**Question:** can a small trained controller, riding a frozen model and
generating the attention field natively, govern long coding sessions —
the Miller wave produced inside rather than injected from outside?
**Answer: YES — SEALED WIN, causal attribution holds.** On 96 sealed
val sessions (held-out sentence format + a never-seen rule type), the
stateless wave reaches closure 1.488 (adherence 25.2% -> 44.8%),
beating the hand-built oracle (38.3%), its proxy twin (37.4%), and —
for the first time in the project — text re-insertion (43.0%, which
FAILED the validity rule with 30 broken works while the wave passed
with parse rate improved 84.8 -> 92.7). Causal re-test at seal: wave
raw gain 238 vs proxy 149, both valid — the CE-through-trunk training
signal generalizes better, not just scores better.

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

## Findings (draft; final numbers pend the seal)

1. **The differentiable press works and out-governs its teacher.** Trained
   only by "make the adherent continuation likelier," through the frozen
   trunk's attention path, the 264k-parameter wave beat the hand-built
   oracle press on dev at zero validity cost — with ablation-proven
   WHERE/WHEN/selectivity.
2. **The matched control isolated two stacked causes of the prior
   programs' failures.** The proxy objective, deployed through the
   continuous actuator, converges onto the oracle (the hard-threshold
   actuator was one killer); the CE signal adds a margin on top with
   zero breakage (the proxy signal was the other).
3. **Recurrence was unnecessary here — honestly bounded.** The temporal
   nulls are real and mechanistically explained, and scoped to the
   frozen architecture; the Miller-transplant question remains open for
   a rescaled-state successor, with the function-vector/KV-steering
   lineage as its citation base (see research-wave-prior-art.md).

## Prior art

Per the committed search (results/research-wave-prior-art.md): every
ingredient has published neighbors (PASTA/InstABoost attention biasing —
all training-free; Guiding Giants/CAST controllers — scalar/vector,
non-recurrent, residual-space; READ sidecars — PEFT, not decoding-time);
the conjunction (trained per-step positional attention field, hidden-
state-conditioned, CE-through-frozen-trunk, matched-control isolation,
zero-validity multi-turn evaluation) appears unpublished, stated
conservatively with two flagged unread items.

## Process record

Checkpoints i-iii dual-reviewed ([N] sol rounds, [N] fable rounds this
program; artifact-enumerated convention); two instrument errors caught
and fixed before verdicts (ceiling wrong-position control; G-W0b
denominator — with my overclaimed defense retracted on review); one
gate retired by ruling with its failure preserved; sealed job
fail-closed with pinned hashes ([w_seal.py sha256 2a0ef648...]); all
numbers reproduce from committed artifacts.
