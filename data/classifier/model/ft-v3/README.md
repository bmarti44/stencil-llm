# ft-v3 admission model — 2026-09-06

Final FOCUS-3 v8 refit authorized by Brian; seed0 is fixed in advance and is the
runtime checkpoint. Seeds1/2 measure development stability only. Every seed
uses its final third epoch, with no checkpoint, seed or threshold selection.

Fit lineage is the exact committed v7 20,634-row admission corpus plus 300
in-session hand-written examples in `../../ft-enrich-requests.jsonl`: 200 NONE
one-shot requests and 100 standing-rule positives with payload context, across
ten domains. No bank sentence was added or removed by the exact-overlap check.
Historical v7 patch exceptions remain; this is not a new clean-corpus claim.
Fit/DEV are normalized-sentence-identity disjoint, not proven paraphrase or
scenario disjoint. Labels are `[none, rule, fact]`; roles are
`[user, assistant, tool, system]`. The runtime rule threshold remains .95.

The BAAI/bge-small-en-v1.5 encoder revision is
`5c38ec7c405ec4b44b94cc5a9bb96e735b38267a`. The unchanged v7 trainer uses paired
context/role-prefixed sentence inputs, CLS plus four role features, dropout .1,
batch32, three epochs, unweighted cross-entropy, AdamW3e-5/weight_decay .01,
the existing .06 warmup/linear schedule, clip1, max192 and only-first training
truncation. Runtime overlength inputs abstain. Each seed has 1767 updates.

| Seed | Fit / DEV | DEV correct | Rule admissions | Non-rule admissions | New-family NONE admissions | New-family rule admissions |
|---|---:|---:|---:|---:|---:|---:|
|0|18841 / 2093|1989 (95.03%)|668/719|18/1374|0/21|7/8|
|1|18840 / 2094|1977 (94.41%)|719/773|11/1321|0/20|7/7|
|2|18841 / 2093|1985 (94.84%)|722/763|16/1330|0/18|7/7|

The single author-disjoint Fable diagnostic gives seed0 318/363 (87.60%), the
same accuracy as ft-v2. Rule admissions remain111/124; non-rule admissions
worsen5→8/239. This previously used held-out is diagnostic, not an unseen test.
The ft-v2 comparator reuses committed logits on identical input rows and hashes.
No relation model fitting or further relation held-out evaluation occurred.

Each `seedN/head.pt` contains `head` (a float32 linear3x388 weight and length3
bias), labels, roles, and encoder hidden width384; dropout has no weights.
The encoder has its standard pretrained BGE tensor inventory, fine-tuned by
the stated recipe. Encoder configuration/tokenizer, head, DEV logits, split ids,
metrics and manifests are committed. Encoder `model.safetensors` remains local,
excluded from git as registered; its SHA-256 is bound by each seed manifest
and the run's `freeze.json`. `request-family-metrics.json` is additionally bound
by that freeze, written after the trainer's per-seed manifest.

Full registration, model/data hash receipts, raw evaluation records and runtime
outcome: [v8 RESULTS](../../../../results/quick-checks/focus3-gate/v8/RESULTS.md).
