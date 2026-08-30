# Prior-art search — the internal wave (fable, 2026-08-30)

Question: has the W0/W1 mechanism been published? Searched arXiv +
venues through Aug 2026. Conclusion (conservative): every ingredient
has neighbors; the conjunction appears unpublished.

## Nearest neighbors by facet

1. Attention steering over context positions on frozen LMs — ALL
   training-free to date: PASTA (ICLR 2024, arXiv:2311.02262,
   user-specified spans, fixed coefficient, profiled heads); AutoPASTA
   (arXiv:2409.10790, self-prompted span selection, no gradients);
   Spotlight Your Instructions (arXiv:2505.12025, per-step dynamic
   re-proportioning, heuristic, user-specified spans); InstABoost
   (arXiv:2506.13734, CONSTANT additive logit bias on instruction keys
   — our intervention site exactly, unlearned and static). No published
   trained module emitting per-step positional attention-bias fields
   with gradients through the frozen pre-softmax path.
2. Hidden-state-conditioned trained controllers on frozen trunks:
   Guiding Giants (arXiv:2505.20309) — closest controller (trained,
   inference-time) but feed-forward, scalar/per-layer gains on a fixed
   residual vector, activation-space not attention; CAST
   (arXiv:2409.05907) similarity-gated fixed vector.
3. Recurrent sidecars beside frozen backbones: READ (arXiv:2305.15348)
   — GRU side network reading backbone states, output fused into the
   model output; a PEFT method, not a decoding-time controller with
   session state, no attention pathway. No published recurrent sidecar
   carrying state across generation steps to steer decoding.
4. Multi-turn adherence via attention: diagnostic (arXiv:2605.12922)
   and the training-free lines above; none learned, none with a
   validity/no-regression evaluation.
5. State-borne task transfer: Function Vectors (ICLR 2024,
   arXiv:2310.15213), Task Vectors (arXiv:2310.15916), KV Cache
   Steering (arXiv:2507.08799) — behavior rides on internal state at
   LM scale (the W2 lineage to CITE); no transplant of an EXTERNAL
   controller's learned recurrent state between sessions.

## Conservative novelty statement (for any report)

Unpublished as a conjunction, per this search: (i) a TRAINED module
emitting a bounded per-step position-indexed attention-bias field
(learned pointing at the currently-relevant instruction), (ii) via a
RECURRENT controller conditioned on the frozen trunk's hidden state,
(iii) optimized by ordinary CE on target completions with gradients
through the frozen pre-softmax attention path — plus the matched-
control causal isolation and the zero-validity-damage multi-turn
evaluation. W2's transplant must cite the function-vector/cache-
steering lineage; its narrower novelty is the external controller's
recurrent state as the transplanted object. Caveats: arXiv:2602.00333
not fully characterized (read before claiming); sweep the aussieai
attention-steering index for uncatalogued entries.
