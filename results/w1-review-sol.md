codex
Not cleared: no critical model-wiring bug, but two HIGH items block checkpoint closure.

- **HIGH — the registered W1 connectivity gate is missing.** H3 requires G-W1a to mirror the real-CE connectivity battery, explicitly including GRU parameters ([INTERNAL-WAVE-PLAN.md](/home/bmarti44/stencil-llm/INTERNAL-WAVE-PLAN.md:211)). [w1_gates.py](/home/bmarti44/stencil-llm/scripts/w1_gates.py:55) runs only held CE and temporal ablations. Emit the real-CE gradient battery before finalizing “stateless suffices.” This is cheap and requires no retraining. I independently compared `w1-ce.pt` with its seed-0 initialization: every GRU tensor changed substantially and all checkpoint tensors are finite, so a dead optimizer path is unlikely—but that does not replace the registered artifact.

- **HIGH — the sealed-validation registration is under-specified and omits the central causal gate.** “Validation” must explicitly freeze `generate_t2(seed, 20, "val", interference="s0")`, `prompt_at(..., "val")`, greedy decoding, `max_new=120`, and the neutral-feedback substitution. Using the current hard-coded `"dev"` path would test only fresh seeds, not the held-out format/type. Also carry C1 forward: a full causal validation win requires both wave and proxy validity plus `wave adh_gain_raw > proxy adh_gain_raw`; closure ≥0.50 alone validates the mechanism, not the CE-over-proxy attribution.

Rulings:

1. **Behavioral W1 replay: SKIP RATIFIED**, conditional on the connectivity battery passing. Temporal success required both CE and behavioral probes. The valid reset CE probe already fails catastrophically (`0.0001 < 0.10`), so behavioral replay cannot reopen W2. Do not claim behavioral equivalence: claim only that recurrent history was unnecessary for held canonical CE and therefore failed the registered temporal conjunction.

2. **W1 implementation:** trainer conforms to score-after-write, state carry with detach across work turns, full within-work BPTT, session reset, and one optimizer step per session.

3. **Permutation probe:** the implementation is deterministic but not literally matched. Donor traces have 67–100 steps, and [w1_gates.py](/home/bmarti44/stencil-llm/scripts/w1_gates.py:48) cycles shorter donors with modulo. Record it as a cyclic next-session permutation, not an exactly matched sequence swap. No rerun is decision-relevant because the correctly implemented reset probe already fails the required conjunction.

4. **Stateless-suffices verdict:** RATIFIED once G-W1a passes. No W2.

5. **Sealed validation:** RATIFIED WITH AMENDMENTS above. Freeze the W0/proxy/model/tokenizer and validation-script hashes before execution; save raw opportunity numerators, paired parse/exec records, output hashes, and gain histograms. Headroom `<0.10` means inconclusive close; otherwise one attempt, no redraw.
