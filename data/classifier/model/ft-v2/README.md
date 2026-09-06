# Admission classifier v2 (FOCUS-3 v7, 2026-09-06)

**Experimental; v7 is INELIGIBLE.** Seed0 is the predetermined consumer path:
`data/classifier/model/ft-v2/seed0`. Seeds1/2 are DEV stability checks, not
alternatives selected by results. Original model/ft remains unchanged.

Base BGE revision5c38ec7c405ec4b44b94cc5a9bb96e735b38267a; three epochs per seed,
paired context and `[role] text`, CLS+role3-way none/rule/fact head. Runtime
admission remains P(rule)>=.95 with192-token overflow abstention. Corpus has
20634 rows: original ft lineage with six pinned admission patch files plus
582 source-derived negative sentences before dedup;18571fit/2063DEV each seed.
Source sentence identities cannot cross fit/DEV. The original corpus's282
category-drop exceptions persist; exact historical training bytes were not
reconstructed. No benchmark inputs or recorded responses used in this refit.

`seedN/manifest.json` hashes all checkpoint/tokenizer/DEV artifacts and lists
split identities. `encoder/model.safetensors` is local and ignored by git;
`head.pt` is the small compatible3-way linear head. `dev-records.json` stores
row/logit evidence; `metrics.json` reports fixed.95 and argmax DEV measurements.
No epoch or seed was selected on held-out performance.

Fable diagnostic: one363-row inference after freeze, following one unscored
identity preflight. Seed0 accuracy318/363 vs original315/363; nonrule admissions
5/239 vs9/239, rule admissions111/124 vs114/124. These historically used inputs
are diagnostic; one sentence-only generic acknowledgement overlaps the training
pool but full paired inputs and declared source authors are disjoint.

Runtime replay:36/36 authorized admissions,11/12 transitions,19unauthorized
applications.10cross-key proposals dropped. No trunk/O/gate inference followed.
[Registration, lineage caveats, corrections and results](../../../../results/quick-checks/focus3-gate/v7/RESULTS.md).
