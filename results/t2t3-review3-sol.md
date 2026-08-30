codex
NOT CLEARED. Two HIGH ambiguities remain.

1. HIGH — architecture freeze occurs too late

[t2t3-prereg-draft.md:117](/home/bmarti44/stencil-llm/results/t2t3-prereg-draft.md:117) says “before training,” which still permits evaluating alternative implementations on the already overused calib set before recording the winner.

Change this to: architecture table/code digest must be written to WORKLOG before any T2 forward pass or metric on train, trace0, calib, or probe data. Only synthetic shape/unit tests may precede it.

2. HIGH — partial-path cell selection still lacks a tie-break

[t2t3-prereg-draft.md:152](/home/bmarti44/stencil-llm/results/t2t3-prereg-draft.md:152) defines mechanical selection only for full-pass cells. Register:

```text
If no valid full-pass rhythm cell exists:
eligible partial cells = validity-pass cells with 0.25 <= closure < 0.50
select maximum closure
ties -> lower g, then larger P
evaluate only that cell’s combined arm
```

This removes the remaining post-grid discretion over the sealed-validation candidate.
