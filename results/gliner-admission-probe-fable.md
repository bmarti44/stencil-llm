# GLiNER2.5-small zero-shot standing-rule admission probe (fable, 2026-09-06)

Development-only CPU probe following astra's TOP-5 item 1 (results/reuse-research-astra.md, P1):
try a pretrained boundary extractor with NO sentence splitter in the output path as a
standing-rule admission candidate. No fine-tuning; no held-out or benchmark data opened.

## Pre-written reading (written before the numbers)

Worth a fine-tune arm in a future 44d if, on dev, zero-shot representability >= 95% AND
overlap recall >= 60% at <= 10% false admissions on gold-empty messages; else idea only.

## Model, lineage, install

- Checkpoint: `fastino/gliner2.5-small-v1`, revision `cab1bddfd30fda7b803a4691c41f90378a2d517a`
  (HF API: 73,881,879 F32 params, last modified 2026-08-22). Config: `architecture: boundary`
  (BoundaryExtractor, `candidate_budget` 192, `start_top_k`/`end_top_k` 24, `overlap_policy: flat`,
  `max_len` 4096), backbone `microsoft/deberta-v3-xsmall`.
- License: Apache-2.0 (HF card + repo + PyPI). Package `gliner2==2.0.0` (PyPI, 2026-08-24).
- Lineage: NOT verifiable. Card, config, GitHub README and HF metadata list no training datasets,
  no synthetic-generation description, no benchmark list. I cannot establish that its training data
  is free of instruction-following evaluation benchmarks (IFEval/Multi-IF etc.). Per the brief this
  probe is therefore development-only; nothing here is a registration.
- Environment: repo python3 (torch 2.11.0+cu128, transformers 5.2.0) left untouched. gliner2 was
  installed with `--no-deps` into a scratchpad venv created with `--system-site-packages`
  (PEP 668 blocks `pip --user`); its declared pin `transformers<5` is violated by the repo's 5.2.0
  but load and inference worked. Run with `CUDA_VISIBLE_DEVICES=""`; model on `cpu`, 8 threads.
  Nothing installed into the repo.

## Data (development only)

`data/classifier/relations/kimi-admission-2.jsonl`: 1,577 rows, 1,289 gold spans (all offsets verified
`message[start:end]==text`). Gold span length mean 66 chars (median 64). Categories (overlapping):
negatives 769 (of which quoted/reported 424, hard 417); one-rule 367; two-plus-rule 441;
rule+payload 534 (rules present AND `one_off_request`); buried 93 (`"buried"` in `why`).

## Method

`AutoExtractor.extract_entities(msg, labels, include_confidence=True, include_spans=True, threshold=0.0)`,
one call per message, all returned candidates kept with confidence; thresholds applied post hoc.
Label phrasings: L1 "standing rule"; L2 "persistent instruction for future replies";
L3 "constraint that applies from now on"; L4 "instruction"; L5 = union of L1+L2+L3 in one call.
Scoring: micro exact-span P/R; micro overlap P/R (pred overlaps any gold / gold overlapped by any pred);
false admissions = fraction of gold-empty messages with >= 1 predicted span; representability = fraction
of gold spans overlapped by any candidate at threshold 0; plus IoU-based representability because
character overlap at threshold 0 is trivially satisfiable by short noun-phrase candidates.
Offset defect: 12-43 phantom trailing "." candidates per config with `end` one past the message
length (`text != message[start:end]`); dropped and counted.

## Numbers

Latency (CPU, per message, incl. ~170-char texts): L1 mean 96 ms / p95 105; L2 96 / 104;
L3 115 / 151; L4 167 / 218; L5 (3 labels) 133 / 215. Model load 7.5 s.

Representability at threshold 0 (any-overlap): L1 1.000, L2 0.997, L3 0.998, L4 0.998, L5 1.000
(10-40 candidates/msg, median candidate length 6-7 chars vs gold median 64).
IoU representability at threshold 0 (fraction of gold spans with some candidate at IoU>=0.5 / >=0.8 / exact):
L1 .144/.059/.036; L2 .249/.086/.047; L3 .109/.030/.020; L4 .417/.174/.110; L5 .299/.110/.072.

Threshold sweep, all rows (predN, exactP, exactR, ovP, ovR, FA on gold-empty):

| cfg | th | predN | exP | exR | ovP | ovR | FA |
|---|---|---|---|---|---|---|---|
| L1 | 0.1 | 3776 | .011 | .033 | .358 | .808 | .999 |
| L1 | 0.5 | 1621 | .010 | .013 | .328 | .389 | .780 |
| L2 | 0.1 | 2345 | .020 | .037 | .378 | .604 | .912 |
| L2 | 0.5 |  491 | .014 | .005 | .228 | .085 | .362 |
| L3 | 0.1 | 3348 | .007 | .019 | .368 | .767 | .987 |
| L3 | 0.5 | 1416 | .006 | .006 | .362 | .372 | .700 |
| L4 | 0.1 | 3308 | .042 | .108 | .392 | .848 | .991 |
| L4 | 0.5 | 1437 | .043 | .048 | .340 | .366 | .744 |
| L5 | 0.1 | 4958 | .017 | .065 | .399 | .929 | .982 |
| L5 | 0.5 |  962 | .025 | .019 | .419 | .300 | .420 |

Gate operating point (first threshold with FA <= 10%): L1 never (FA .139 at th .99, ovR .016);
L2 th .93 -> ovR .003; L3 th .99 -> ovR .018; L4 never (FA .163 at .99); L5 th .85 -> ovR .056.

Per-category overlap recall at th 0.5 / 0.1 (best single-label L4 "instruction"): one-rule .450/.842;
two-plus-rule .333/.850; rule+payload .300/.811; buried .563/.941. FA at th 0.5 / 0.1: all negatives
.744/.991; quoted/reported negatives .861/.998; hard negatives .767/.993. Quoted/reported negatives are
admitted MORE often than plain negatives in every config (the model finds entity-like spans inside quotes).

## Reading against the pre-written gate

- Representability >= 95%: met only in the vacuous any-overlap sense. With IoU>=0.5 the best config
  covers 42% of gold spans; exact 11%. Zero-shot, the head proposes NER-style noun phrases
  ("uppercase keywords", "twenty lines"), not clause-length rules.
- Overlap recall >= 60% at <= 10% FA: FAILS by a wide margin (best 5.6% overlap recall at 10% FA).
  Confidence does not separate rule-bearing from rule-free messages; quoted negatives are worst.

## Reuse verdict

**Idea only** for zero-shot GLiNER2.5-small as an admission candidate. Both gate conditions fail on dev;
no fine-tune arm is justified by this evidence. What survives: the pretrained boundary machinery
(start/end pairing, offsets that map back to the source, ~100 ms CPU/message, Apache-2.0) is a viable
substrate ONLY if trained, and training is blocked until lineage is cleared (astra's own condition).
Given the unverifiable lineage and the repo's existing clean encoder/corpus, astra's fallback stands:
original boundary/BIO head on the clean encoder rather than this checkpoint. Do not substitute gliner2-base-v1.

Artifacts: raw candidates + latencies + scorer in the session scratchpad (not committed);
this report is the registered output. Data lineage: fit on nothing; evaluated on kimi-admission-2 dev only.
