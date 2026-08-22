# Review topic: scientific and methodological rigor of PLAN.md

Read PLAN.md in full (repo root; it governs) and README.md (it explains). No code exists yet; you are reviewing the pre-registered plan itself. Do not implement anything.

Adversarially scrutinize:

- The hypothesis structure (H1–H4): falsifiable? Any way to get a false positive that survives every gate?
- The determinism trick and the receptive-field bound `L * w`: is the reachability argument actually airtight given RoPE, pre-LN, softmax over masked positions, the final LayerNorm/readout, and B1's gate input? Could any architectural detail leak cue information beyond the claimed bound?
- The exact-zero-gradient test as specified: is exactly-zero truly implied by the construction, or could numerical or implementation details (mask form, attention kernel, weight tying, embedding sharing with the control pathway) make it fail or, worse, pass vacuously?
- The H2 dissipation-spectrum design: is M1 vs M1b vs B2 a fair, confounder-free comparison?
- H4 channel purity: is the "32 bindings cannot plausibly fit through 16 scalar gates per position" argument information-theoretically sound given gates exist at every position?
- Appendix C thresholds: well calibrated, pre-registered cleanly, any ambiguity in how they'd be evaluated?
- Kill criteria and the Appendix D root-cause tree: any path where a dead hypothesis gets rescued or a live one gets killed?

Score the plan's scientific soundness. Cite exact section names and quote the problematic text in every finding.
