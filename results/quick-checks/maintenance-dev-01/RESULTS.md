# Automatic maintenance DEV result

The frozen recipe did not maintain the standing obligations on these two exposed DEV conversations. This is a defect report for this recipe, not a general rejection of automated registers. Brian’s criterion remains: matching good manually maintained prose automatically can be a substantial benefit.

All 16 scheduled calls completed once, without retries or a coding worker. Five transactions passed structural validation; eleven were rejected (seven duplicate key/scope additions, two out-of-range evidence spans, two unauthorized tool-source proposals). Structural acceptance did not establish semantic correctness. Cold ETL stored an ingest-scoped `research_register` instruction instead of Python and error-handling rules; cold TypeScript stored a parser-scoped project description instead of the global strict-TypeScript rule. Later proposals mostly repeated those mistaken entries. The independent semantic and replay audit is recorded in [accuracy-review-astra.md](accuracy-review-astra.md).

The decoder used 36,185 prompt and 2,937 completion tokens across 16 calls. Driver elapsed time was 132.45 seconds; the conservative total GPU reservation, including startup and cleanup, was 620.47 seconds against the registered 900-second ceiling. The launcher recorded successful container stop/removal and no remaining container was observed afterward. These timings measure this run, not an automation cost advantage over prose.

Frozen implementation commit: `5d499362eb4e7537631a06b10201b6e52e2c1f8e`. [Freeze](freeze.json), [manifest](calls/manifest.json), [per-turn states](calls/rows.jsonl), exact HTTP receipts under `calls/calls/`, and [lifecycle](lifecycle.json) preserve the actual attempt. No model responses were edited, no old frozen run was rescored, and no larger screen was launched.

Fit-on: none. Development-on: two original Kimi-authored conversations, audited labels, and synthetic CPU controls. Evaluated-on: none. These conversations and responses remain exposed DEV material.

Next hypothesis, not established: the prompt specifies transaction syntax much more clearly than the semantic job of extracting durable user obligations. A future isolated revision should state that job plainly, distinguish standing constraints from project descriptions and one-off requests, and keep quoted/tool text from acquiring authority. Repeating this unchanged recipe or scaling it to a coding worker is not supported by this result. Any revision needs its own frozen DEV attempt; these outputs must remain unchanged.

## Independent accuracy addendum

Astra xhigh independently verified the 11 frozen file hashes against the pinned commit, all 16 exact HTTP response bodies and hashes, prompt reconstructions, compiler replays, pre/post snapshots, and actual carried state. Semantic agreement was **0/48 complete effective views and 0/2 whole trajectories**. All five accepted operations were wrong overall; the Python 3.12 update retained partial relevant content but had the wrong task scope. No retired versions were created, versus four in the audited gold trajectory inventories. View counts are descriptive and correlated, not 48 independent trials. The detailed audit is linked above.

Accounting clarification from Astra: the rejection breakdown lists the first recorded rejection reason, not all defects in each proposal. The TypeScript tool-source proposal also has an out-of-range span, but authorization is checked first.
