# Work log — GPT-2 era (light process)

- 2026-08-28, pivot (Brian): "use gpt2 small as the model to train/test.
  let's reframe everything around this in the repo, and let's not over
  engineer it - i want there to be deterministic verificaitons in place for
  everything so you can prove that the oscillator is working as expected."
  Plan approved (GPT2-PLAN.md); sol plan review explicitly waived by Brian
  ("let's not do the sol review of the plan this time - just start executing").
  Settled: 2 arms (base stateless-gate / osc), frozen trunk, 2 seeds, clean
  archive pivot. Toy phases + their governance moved untouched to archive/.
  Next: coder pass A (gpt2.py + weight conversion + verifications 1-4).
- 2026-08-28, pass A DONE: gpt2.py (3 arms, windowed attention, gate site, external oscillator controller), convert_gpt2.py (hand-parsed safetensors, HF pinned-oracle parity max|err|=0.00012, frozen bitwise fixture), verifications 1-4 GREEN (parity bitwise, inert graft bitwise + non-vacuity, frozen trunk bitwise, two-run training bitwise). Next: pass B — nl_task.py, hand-executed fixture first.
- 2026-08-28, pass B DONE (TDD): nl_task.py (minimal GPT-2 BPE, templated rules/updates/queries, separate targets, no external corpus); verifications 6-8 GREEN — vocab single-token test went RED on 'duke' first (swapped to 'wolf'), hand-derived fixture check, leakage guard, determinism, beyond-receptive-field distance guarantee. Next: pass C — zero-Jacobian test, arms runner, dial harness.
- 2026-08-28, pass C + gate + fleet s0: zero-Jacobian on GPT-2 GREEN (exact-zero
  beyond 756 for vanilla/base, boundary 700 nonzero, nonzero through wire);
  arms runner + dial harness done. Feasibility gate: frozen windowed GPT-2 =
  2/64 exact but 46/64 top-5 on fully in-window rules -> contingency applied,
  both arms got identical trainable logit_bias. base-s0 (57 min) and osc-s0
  (69 min): NEGATIVE — both flatline at ln(16)=2.77, validation at chance
  (6.25%) in every family/bin. Diagnosis: logit_bias learned the 16-word
  answer alphabet; 144 volume-knob gates cannot make a FROZEN trunk emit
  specific new content. Held base-s1/osc-s1 as pointless.
- 2026-08-28, LoRA iteration (Brian: "okay, great I understand - run it"):
  rank-4 LoRA on attn output proj, IDENTICAL in both arms (~600k params/arm),
  zero-init B so LoRA-off is bitwise inert; trunk still frozen + bitwise
  checked. TDD: test_lora_inert_and_pathway_classified went RED
  (no lora_rank), then GREEN; all 5 gpt2 verifications green. Runner writes
  <arm>-lora-s<seed>.* so the gate-only negatives stay untouched. Launching
  pilot pair base-lora s0 then osc-lora s0 (~70 min each).
