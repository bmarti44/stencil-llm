# Review topic: internal consistency and testability of PLAN.md

Read PLAN.md in full (repo root; it governs) and README.md (it explains). No code exists yet; you are reviewing the spec itself. Do not implement anything.

Cross-check every number against every other number, and every named artifact against the phases that need it:

- Vocabulary map (Appendix B) vs task specs in Section 6: range sizes, cue/key counts, operand/value ranges, distractor ranges, Task M's "keys drawn without replacement from the 32-token cue range" vs P=32.
- Architecture table (5.1) vs control pathway (5.2): d_model vs oscillator input dim, "control output c_t (dim 128 from final cell's y)" vs y being 64-dim per cell, state dims, gate count arithmetic in 5.3.
- Receptive-field arithmetic everywhere it appears (Sections 1, 5.1, 6, Phase 6), including whether the B1 bound as stated in Section 1 is internally consistent.
- Param-matching claim (5.5) vs the variants' actual added parameter counts.
- Experiment matrix run counts in Phase 3 vs the stated "roughly 90 to 100 runs".
- Config schema (Appendix A) completeness vs everything Phases 0–6 need to configure.
- The discretization equations in 5.2 vs the stated continuous system (is the IMEX/symplectic claim correct as written?).
- Every named test in Phases 0–4: is it implementable exactly as specified (inputs, fixtures, tolerances, fp32/fp64), or would a coding agent have to guess?
- Repo layout / Makefile / results policy vs what the phases actually produce, including Section 2b tooling and plan/reviews/.

Flag every contradiction, every underspecified decision a coder would have to invent, and every place two parts of the file disagree. Cite exact section names and quote the text.
