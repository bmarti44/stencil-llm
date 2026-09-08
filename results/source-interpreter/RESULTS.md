# Source interpreter preparation: accepted

2026-09-08. Six Kimi K3-authored FIT conversations and their eighteen correlated
query examples have passed independent Astra xhigh review. The labels faithfully
describe the instructions active at each query. The CPU preparation preserves
the exact source text and accepted target, masks source tokens from training
loss, and supervises target JSON plus EOS without truncation. This completes
preparation only; no training or semantic model evaluation has run in this unit.

The eighteen sequences contain 29,781 tokens: 22,547 source/prompt tokens and
7,234 supervised target/EOS tokens. Full lengths range from 499 to 3,891.
The longest is author-04, query index 2: 2,966 prefix plus 925 target/EOS.
These are six FIT families, not eighteen independent test cases.

The actual CPU preview completed in 3.056 seconds. Astra independently reconciled
all eighteen rows, tokenizer state, loss masks and artifact bindings and accepted
the preparation at 96/100 with zero open findings. The original labels needed
one guarded Kimi correction round; original sources and every correction remain
preserved. A prior compile-time launch syntax error is also preserved; it ran
no preview or model operation.

Evidence: [final review, round 7](review-astra.md),
[input lineage](accepted-inputs.json), [complete CPU receipt](preview.json),
[terminal job receipt](preview-job.json), and [preparation contract](PREP.md).
The final review SHA-256 is
`c6538d94d711494c69a0a201105daa51c34aa7c73e3591dcc2b94ac75f4a3e05`;
the preview SHA-256 is
`5760764f748a088d9d105b6f89b6188785941239ea28c1e60d706f9d028a0326`.
The frozen input manifest's historical CPU-preview-pending status is retained
as provenance; this document and the final review record its completion.

The next proposed step is a separately reviewed training mechanics measurement
on the longest FIT row. Feasible training, learned transfer, automatic focus
comparable to useful manual prose, and adequate larger executable proof all
remain unestablished. Earlier failed recipes stay frozen.
