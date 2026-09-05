# Breakthrough hypotheses — kimi-k3 (2026-09-04)

I can't write to the repo or shell anything, so the deliverable is below as the exact file content to save at `results/hypotheses-kimi.md`. What I could not check: whether `results/quick-checks/focus1-probe/` exists or what check 31 returned (the paste says "pending"); the tail of the FOCUS-1 CLEAR audit (truncated in the paste); and no live web search was possible — rankings use the pasted repo record plus knowledge through 2026, flagged inline. Sealed IFEval/BFCL files untouched; no GPU/model process launched or signaled; no other repo edits.

```markdown
# hypotheses-kimi.md — ranked breakthrough hypotheses: Miller focus on frozen Qwen (kimi, 2026-09-05)

Process per Brian: screens only; every result below goes to sol/fable review before any deeper verification.
Could-not-check: (a) check 31 output under results/quick-checks/focus1-probe/ — H1 is written so it applies
identically as "score existing output" or "run the screen"; (b) no live web available — 2024-2026 priors from
memory only: steering/function-vector results are dose-sensitive and brittle under sustained injection (matches
checks 28/30), and I know of no demonstrated zero-shot content-free skill-switching on an instruct trunk, which
caps H1 at 40%; cross-context KV transplant onto a foreign prefix is largely unsupported, capping H3 low.

Evidence spine (repo): content-recovery steering failed — fv_inject 14/56 vs evicted 10, trunc 14/20 (check 30);
deficit-gated bias wave killed, degenerate 8/20 (check 28); bench amplification on retained KV degenerated.
Text-address selection works — SELECTOR 3.9->88.3; check 27 pins recover 0.91 of the eviction gap; pin+echo 46
> full 44; Leg B role_pinned 0.605 > classifier 0.572. A learned WHERE/WHEN controller is real — internal wave
sealed 25.2->44.8, causal 238 > proxy 149; recurrence null with |h20|~609 vs |s_t|~6 (scale mismatch, unsettled).
Open question (astra-drift): set/hold/switch/clear between two DEMONSTRATED skills, operands visible, cue removed.

## 1. H1 — Oracle A/B/OFF residual DIRECTIONS at decision points only, between two ≥90% skills (asc/desc sort)
- Hypothesis: a rho-normalized mean-difference residual direction, added only at decision positions, selects which
  of two existing competencies governs, because only a 1-bit task signal must be supplied, never content.
- Why here: every residual failure asked the vector to RECOVER deleted constraint content (check 30: 14/56,
  truncating 14/20; check 28: killed). Selection with operands visible is categorically easier; FOCUS-1 gates
  skill-existence at ≥29/32 cue-visible first. Sustained high-dose injection — the degeneration mode — is excluded
  by design (alpha∈{0.5,1,2} × L∈{12,16,20}, decision positions only).
- QUICK TEST (2.0 GPU-h): extraction on 64 operand-balanced triples (focus1-v1 seed law); 9-cell grid on the
  32-episode setup slice (scripts/focus1.py + function_vectors.mean_difference/make_residual_hook); then the
  64-episode test at the FIRST eligible cell. Measurement: per-task cue-absent exact sorts /32; complete
  4-decision switch episodes /64; swapped-arm donor-task answers on RECIPIENT operands /32; shuffled-control /64;
  CLEAR copy-pairs /32; KEEP old-task impositions /32; breakage /32 per arm.
- PASS/FAIL (written before running): PASS = an eligible setup cell (≥24/32 both tasks, CLEAR ≥31/32, KEEP ≥4/32,
  ≤1/32 breakage each arm) AND test ≥40/64 complete switches, swapped ≥16/32, shuffled ≤8/64. FAIL-ACTUATOR = no
  eligible setup cell → close the residual-direction branch for this pair; no grid expansion, no fallback to 4B.
- Trivial explanations excluded: operand/answer memory (fresh operands; adoption scored on recipient lists);
  hook-as-noise (norm-matched shuffled arm, OFF arm); hidden cue KV (cue removed pre-tokenization; KV hashes
  checked equal across arms); "clear"=hook-off artifact (CLEAR scored on retained contaminated KV vs KEEP, plus
  replay from empty cache).
- Pass unlocks: H2 controller pilot; >2-skill address sets; long-delay holds.
- P(pass): 40%.

## 2. H2 — Controller-in-the-loop, internal-wave recipe, 3-way A/B/OFF address head on H1's frozen actuator
- Hypothesis: a 264k-param controller trained by CE-through-trunk can choose the address (and WHEN to switch)
  that the oracle supplies in H1 — TIMED-SELECTOR/PRESS failed with blind/hand actuators and trained
  discrimination, but the wave recipe produced the sealed win with ablation-proven WHERE/WHEN; it has never been
  pointed at discrete selection+switching rather than amplification.
- QUICK TEST (3.5 GPU-h; run ONLY if H1 passes): 160 synthetic switch episodes (96 train / 32 dev / 32 test,
  focus1-style law, disjoint splits); controller reads hidden states, outputs address logits + gain capped to H1's
  frozen cell; train as INTERNAL-WAVE-PLAN W0 with the matched proxy twin (same module/data/seeds, oracle-label
  training); two variants: stateless, and recurrent with state input RESCALED (the W1 |h|~609 vs |s|~6 fix);
  3 seeds, per-seed + mean (check-19 rule).
- PASS: dev complete-switches ≥20/32 (mean), address-argmax at decision points ≥90%, breakage ≤1/32, controller
  > proxy twin, address-permutation ablation destroys the gain (selectivity real — the K-perm analogue); recurrent
  must beat stateless by ≥4/32 else stateless wins.
- Trivial explanations excluded: cue copying (cue absent at all measured decisions; only hidden states + enum
  schedule available); operand-order leak (balanced, counterbalanced); dose degeneracy (actuator frozen from H1).
- Pass unlocks: the actual deliverable — a learned, content-free selector; then session-scale delays, >2 skills.
- P(pass | H1 pass): 50%; unconditional: 20%.

## 3. H3 — Single-position KV/residual "task capsule" transplant on the real trunk
- Hypothesis: the cue-visible final-prompt-token state (per-layer K,V + residual) carries the task bit as a real
  computed state; appended as ONE position to a cue-absent recipient prefill it makes recipient operands follow
  the donor task — the real-trunk analogue of the toy 45/45 transplant this program was founded on, never run
  (W1 null recurrence removed the state; check 30 tested mean-difference VECTORS, not captured KV).
- QUICK TEST (1.5 GPU-h): 32 episodes, own-seed law; arms: task capsule; sham (cue-absent donor capsule);
  same-task/other-operands capsule; layer-shuffled capsule. Measurement: donor-adoption = exact sorted JSON of
  RECIPIENT operands in the DONOR direction, /32 per task; degenerate count.
- PASS: ≥20/32 both tasks, sham ≤2/32, layer-shuffled ≤4/32, 0 degenerate. Else close prefill-state transplant
  and record the negative.
- Trivial explanations excluded: answer smuggling (donor operands differ; answer must match recipient list);
  generic "sort" suggestion (direction must SWAP with swapped capsules); position artifact (shuffled control).
- Pass unlocks: a storable/transplantable state → genuine hold/switch/clear substrate and transplant-based memory
  tests, reopening what W1 could not test.
- P(pass): 15%. Blunt: long shot — GPT-2 oracle gates scored 0/8 and needed a trained 5 KB cache; a foreign
  position is off-distribution for every trunk layer.

## 4. H4 — Hybrid: content-free hard address switching a minimal text echo (functional focus; NOT the mechanism)
- Hypothesis: an addressable store of short obligation texts + a trivial switcher of which address is echoed at
  each turn delivers the AGENT goal (right instruction governs now, stops later) — the only near-term route with
  evidence: SELECTOR 3.9->88.3; check 27 pin+echo 46 > full 44; Leg B a ROLE RULE (0.605) already beat the
  trained retriever (0.572), so switching logic may need to be 20 lines, not learned.
- QUICK TEST (2.0 GPU-h): 24 own-seed synthetic 8-turn sessions alternating two formatting competencies (fresh
  per-turn operands); arms: base / static-both-rules / oracle-address echo / rule-triggered address echo.
  Measurement: per-turn adherence, switch lag, degenerate count.
- PASS: oracle ≥90% adherence, rule ≥85%, lag ≤1 turn, 0/192 degenerate, base ≤50% (headroom exists).
- Trivial explanations excluded: echo supplies the rule, never answers (answers scored on fresh operands);
  turn-order artifacts (counterbalanced rule order).
- Pass unlocks: the ship-path bar that H1/H2 must beat — a wave that cannot beat a 20-line rule on
  adherence+degeneracy is not a win.
- P(pass): 60%. Blunt: highest raw probability, lowest Miller value — this is the astra-drift §7 route; bank it
  as ceiling/control, never as the mechanism result.

## 5. H5 — Sparse binary gate-pattern selection over attention heads (discrete actuator; closure test)
- Hypothesis: zeroing a tiny address-indexed head set flips the skill without the continuous-steering degeneration
  that killed checks 28/30. Direct negative on record: GPT-2 oracle gates 0/8 vs additive 8/8 (gpt2-report) — this
  is a cheap permanent-closure shot, included to end the branch cleanly either way.
- QUICK TEST (1.5 GPU-h): own-seed 32-pair cue-visible mini-bank; rank heads by knockout Δlogit gap on the
  first output token (asc vs desc); cue-absent: gate top-k per address, k∈{1,4,16}, on 20 episodes.
- PASS: ≥20/32 exact sorts per task with a direction-correct swap arm and 0/20 degenerate. Any other outcome:
  CLOSE discrete gates for this skill pair permanently.
- Trivial explanations excluded: gating amplifies existing logits only (require the swapped gate set to flip the
  direction); seed noise (3 seeds, mean + per-seed).
- Pass unlocks: a degeneration-proof discrete actuator for H2. P(pass): 10% — long shot, priced accordingly.

## Recommended order (single sequence) and total GPU-h
1. H1 (2.0) — score check-31 output if it exists (≈0 GPU-h, CPU only), else run the screen as pre-registered.
2. H4 (2.0) — independent of H1; establishes the bar and the fallback.
3. H2 (3.5) — ONLY on H1 pass; skip on FAIL-ACTUATOR (saves 3.5).
4. H3 (1.5) — mechanism swing, cheap.
5. H5 (1.5) — closure test either way.
Total: 10.5 GPU-h worst case; 4.0 GPU-h unconditional core (H1+H4); all within the ≤4 GPU-h per-test cap,
≤1 day each, own seeds everywhere, zero benchmark/SC1 data.
```

Bottom line: fund the H1 oracle screen and the H4 rule-based address-echo ceiling first (4 GPU-h, both likely decidable in a day); H2 is the real deliverable but only worth its 3.5 GPU-h if H1's actuator exists; H3/H5 are cheap long shots run to close branches cleanly, not because I expect them to pass.