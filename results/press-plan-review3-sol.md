codex
NOT CLEARED.

1. **HIGH — fixture “single-use per policy” still permits adaptive multiple certification.** Block A certifies every score family, then G0 selects the best certified family; the attention fallback is also designed after seeing A and certified on A ([PRESS-PLAN.md:114](/home/bmarti44/stencil-llm/PRESS-PLAN.md:114), [PRESS-PLAN.md:171](/home/bmarti44/stencil-llm/PRESS-PLAN.md:171)). Block B is reused for T1, its retrained fallback, and T2 contenders ([PRESS-PLAN.md:94](/home/bmarti44/stencil-llm/PRESS-PLAN.md:94)). Per-policy 95% CP bounds do not certify an adaptively selected winner. Either certify exactly one trace-selected policy per block, allocate fresh blocks to fallbacks/T2, or register simultaneous LTT/Bonferroni control over every possible policy. Also state that a session failure is any non-NULL decision after numeric threshold but **before** the ledger-membership guard; otherwise that structural guard can trivialize certification.

2. **HIGH — T0.5’s recovery gate still lacks its subtraction formula and fixed source denominator.** “Reactive recovery as a fraction of oracle recovery” could be implemented as `A_reactive/A_oracle`, which can pass with zero lift over base ([PRESS-PLAN.md:176](/home/bmarti44/stencil-llm/PRESS-PLAN.md:176)). Freeze the eligible set from base-arm violations, evaluate every arm on those same opportunity IDs, and define  
`recovery_closure = (A_reactive − A_base) / (A_oracle − A_base)`  
from raw numerators. Apply the ≥0.10 headroom precondition to that exact denominator.
