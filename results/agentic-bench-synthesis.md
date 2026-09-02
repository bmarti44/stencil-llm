# Agentic / long-horizon benchmark selection — synthesis of fable, sol, kimi (2026-09-02)

Sources: results/agentic-bench-fable.md (30 sources), agentic-bench-sol.md (40+), agentic-bench-kimi.md (56 tool calls).
Orchestrator checks: VerIFY dataset is "pending GDM approval" (README fetched 2026-09-02) → unavailable; BFCL data
README states apache-2.0 (fetched); no OpenAI key on this host (Lost-in-Conversation's shard simulator and tau2's
user simulator need one; an Anthropic key exists but a simulated user adds judge-noise and cost to a confirmatory run).

## Where the three agree (adopted as registered design rules)
1. Programmatic verifiers only; no LLM judge in the primary estimand (echo-leakage and judge bias).
2. Equal-context control = token-matched RANDOM-SPAN echo: at every ledger echo point inject a same-token-count span
   sampled from prior user turns with the identical template, pinned with the same keep= column budget. Holds tokens,
   template, position and KV residency constant; only SELECTION differs. Beating base but not this control = a
   nonspecific-text effect, not the mechanism.
3. Paired by episode; cluster-robust one-sided CI (clusters = episodes); Holm α = 0.025 across legs; ROUND 7 safety
   (timeouts ≤ 2%, truncation excess ≤ +2 pts, tool-call validity excess ≥ −2 pts, stale-adoption NI, echo-copy rate
   reported and copy-satisfiable items excluded).
4. Base-competence preflight on a DISJOINT dev slice before the sealed cohort is spent; a floor near zero voids the leg.
5. Finder-recall preflight (≥ 0.80 on ~100 labelled instruction/tool-schema spans from the target benchmark; the finder
   was fit on Multi-IF-style text and this is a distribution shift).
6. Qwen3-1.7B is at the floor on every open agentic benchmark (BFCL V3 multi-turn 7.8–10.3 overall, long_context 2.5;
   tau-bench retail 6.1 / airline 14.0 — verified by two reviewers). This is the concrete reason for the Qwen3-4B trunk.

## Where they differ, and the decision
| leg | fable | sol | kimi | decision |
|---|---|---|---|---|
| agentic | Lost-in-Conversation programmatic subset (MIT; needs GPT-4o-mini shard simulator) | BFCL V3 multi-turn, sealed 64-case cohort (Apache-2.0; predefined user turns; executable) | tau2-bench retail (MIT; LLM user simulator) | **BFCL V3 multi-turn** — the only simulator-free, executable, permissively licensed option; stratified 16 × {base, missing_params, missing_functions, long_context}; long_context supplies native pressure. ~28 GPU-h at 1.7B rates for the pair, re-estimated for 4B. |
| long-horizon instruction | SEQUOR single+add (50 turns; LLM judge; license unknown) | HANDBOOK.md 64-item diagnostic (frontier-only floor) | RULER variable-tracking 8k/16k (exact match; facts, not instructions) | **Registered S2 buried-constraint set, extended to ≥ 8k context so eviction is native**, plus the already-registered Multi-IF 909 text_ledger confirmation. RULER-VT kept as a cheap sanity leg (~5 GPU-h) for "aged dependency survives pressure", explicitly not an instruction claim. |

## Falsifier for "automatic benefit for agentic work" (adopted from fable, endorsed by sol/kimi)
At registered n with safety intact: LB(LEDGER − RANDOM-SPAN CONTROL) ≤ 0 on the BFCL primary; OR LEDGER beats BASE but
not CONTROL; OR the gain appears only under simulated sub-context eviction and vanishes under native pressure
(long_context category / ≥8k S2). A Multi-IF-only pass is registered as insufficient for the word "agentic".

## Cost and order
0. Preflights (dev slices, CPU + ≤ 3 GPU-h): base competence on 32 BFCL MT cases (1.7B and 4B); finder recall on
   100 labelled BFCL instruction/schema spans; BASE-vs-BASE rerun variance.
1. Leg A: BFCL V3 MT sealed 64-case cohort × {base, ledger, random-span control} on the trunk that passes preflight.
2. Leg B: S2 ≥ 8k buried-constraint set × 3 arms (~10 GPU-h) + Multi-IF 909 text_ledger (~30 GPU-h, registered).
3. RULER-VT sanity (~5 GPU-h), reported not gated.
Blockers to resolve first: an OpenAI-compatible chat/tool shim for the hand-rolled trunk (every harness assumes one);
non-thinking mode fixed and disclosed; Qwen3-4B parity (coder brief qwen3-4b-trunk).
