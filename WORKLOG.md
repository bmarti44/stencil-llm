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
