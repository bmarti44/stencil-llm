# Pre-replay consumer correction — 2026-09-06

CPU code audit, before held-out/setup/gate inference, found that substituting
semantic slugs for storage keys changes Register.add version counts across tasks.
The user requires everything else from v6 unchanged. Preserve storage/provenance
keys and versions; maintain semantic key slugs separately for proposal matching.
This is a runtime-only correction, with a synthetic two-task version regression
fixture. Fitting continues unchanged; no admission corpus, split, model, threshold,
optimizer or epoch alteration. The initial recipe receipt is preserved, and the
corrected receipt hashes only changed runtime/test/audit-consumer source.

A separate loader audit establishes that the historical script's present broad
patch glob includes later relation patches and now yields20069 rows. The v7
loader pins the six admission patch files named in ft/metrics.json and yields
20054 original-lineage rows. Equal cardinality does not prove exact historical
training-row identity; no exact-reconstruction claim is made. Original282
category-drop exceptions are preserved, not a new benchmark-input read.
