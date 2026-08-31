codex
NOT CLEARED. No criticals; four HIGH findings remain.

- HIGH — the single-use semantics contradict themselves. [C1](/home/bmarti44/stencil-llm/BENCH-WAVE-PLAN.md:136) says the 541 are touched exactly once, then schedules another full post-B4 zero-shot run. Vendoring the data and deriving its class inventory also technically constitute exposure. Define the invariant precisely: “No model generation, scoring, per-prompt inspection, or error analysis before sealed B4; post-seal reuse is exploratory and permitted.” Rebind H1’s stale “before B0.3” timing reference to “before B4.”

- HIGH — B0.1 parity lacks a pass criterion. [H2](/home/bmarti44/stencil-llm/BENCH-WAVE-PLAN.md:155) can be read as requiring bitwise-equal HF logits, which the custom forward cannot satisfy—the prior worst max error was 0.365. Freeze: token IDs bitwise equal; top-1 equal for every fixture; finite logits; `max_abs_error <=` a registered tolerance. File hashes establish checkpoint identity; numeric parity establishes conversion behavior.

- HIGH — the non-inferiority tests are promised, not registered. [H3](/home/bmarti44/stencil-llm/BENCH-WAVE-PLAN.md:164) still lacks the exact MMLU-Redux revision/size, margins’ inherited status, null hypotheses, α, confidence/test construction, and aggregation across subjects. State that B2 is blocked until checkpoint ii freezes these mechanically. Otherwise “paired non-inferiority” remains implementer-selectable after observing discordance.

- HIGH — B4’s two-seed and cross-benchmark decision tables remain incomplete. [C1 names only base/wave/proxy](/home/bmarti44/stencil-llm/BENCH-WAVE-PLAN.md:137), while [H6 requires two wave/proxy seeds](/home/bmarti44/stencil-llm/BENCH-WAVE-PLAN.md:186). Freeze the actual arms as `base, wave-s0, proxy-s0, wave-s1, proxy-s1` in one sealed job. Specify whether each seed must pass primary, causal, and do-no-harm gates; the external claim should require both seeds to pass primary and do-no-harm, while causal attribution should require both seed-specific causal gates.

  IFBench is currently named but not actually preregistered: no revision, split, metric, arm set, decoding, effect floor, statistical gate, or no-retraining rule exists. Freeze its complete protocol before B4 results—not afterward—or benchmark-selection adaptivity is replaced by metric-selection adaptivity.

Everything else from round 1 is faithfully addressed.
