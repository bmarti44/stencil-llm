# Check44b — NO-GO: high precision, insufficient standing-rule span recall

**First ship stays explicit structured rule entry; C is an assistive suggester.**
C fails the registered held-out micro overlap recall bar:151/207=72.95% versus
85% required. It meets the other point-rate requirements: no payload, quoted,
or non-user false admissions; two false-admission SETUP turns of 96. No runtime
replacement is registered and gate v9 is not authorized by this check.

The [pre-written reading](README.md) and recipe were committed in f03c4398;
three final checkpoints, thresholds and weight hashes in bab43b0d, before any
new held-out contents. Fable-2 arrived in 2b3cfc74 and was discovered at the third
recorded five-minute commit poll. Exactly330 held-out messages (176 positive,
154 gold-empty,207 gold spans,22 new domains,101 author scenarios) and 96 SETUP
turns were evaluated once per arm. The original Fable bank was never opened.
The source snapshot/hash and all 426 per-message records are preserved.

| Arm | Exact micro P / R | Overlap micro P / R | Exact macro P / R | Overlap macro P / R |
|---|---:|---:|---:|---:|
| C, admission-v1 seed0 | 82.24% / 60.39% | 99.34% / 72.95% | 82.78% / 71.02% | 99.67% / 78.69% |
| B, unchanged ft-v3 seed0 | 78.86% / 66.67% | 95.43% / 80.68% | 80.65% / 78.41% | 97.32% / 87.22% |

C predicts 152 spans: exact 125 matches, overlap 151. B predicts 175: exact 138,
overlap 167. Macro precision averages messages with predictions; macro recall
averages positive messages. Binary message P/R is C 100%/85.80% (151/176 detected),
B 99.40%/94.89% (167/176; one false-positive message). Those higher message/macro
recalls do not replace the registered one-to-one micro span metric.

| Gold-empty/role family | C false admissions; one-sided95% CP upper | B false admissions; one-sided95% CP upper |
|---|---:|---:|
| Payload/one-off | 0/97; 3.04% | 0/97; 3.04% |
| Quoted/reported | 0/57; 5.12% | 1/57 (1.75%); 8.05% |
| Non-user | 0/30; 9.50% | 0/30; 9.50% |
| All gold-empty | 0/154; 1.93% | 1/154 (0.65%); 3.04% |

The explicit role guard enforces non-user rejection. Zero observed errors do
not certify a population FPR<=3%: even the payload upper bound is 3.04%. Messages
share scenarios. [diagnostics.json](diagnostics.json) also groups using Fable's
`scenario` field: C is 0/80 payload scenarios (upper3.68%),0/47 quoted (6.18%),
0/28 non-user (10.15%), and 0/87 all-negative (3.38%). These secondary bounds
measure any error within a scenario, conditional on independent scenarios.
The inherited check44 primary aggregator recognizes only `scenario_id`, so its
`scenario_groups:null` fields are supplemented here, without changing the
registered message-level point-rate decision. Tool/assistant strata are in
[summary.json](summary.json). Scope and semantic-key prediction were not fitted.

**Recall diagnosis, saved records only.** Frozen splitter representability is
176/207=85.02%: every one of the31 two-rule messages places both gold clauses
inside a single candidate. This accounts for31 necessarily unmatched spans;
C misses another 25 representable spans. C recall by category is 101/114 one-rule,
25/62 two-rule and 25/31 rule+payload; B 109/114,27/62,31/31. No arm overflows on
this bank. The splitter and threshold were not revised after this diagnosis;
no clause rescue or second inference pass occurred.

| Development SETUP diagnostic,96 turns | C | B |
|---|---:|---:|
| Turns with any unmatched admitted span | 2/96 | 22/96 |
| Request-template false admissions | 0/96 | 15/96 |
| Overlap true spans / gold spans | 34/40 | 39/40 |
| Gold-empty turns with an admission | 0/72 | 14/72 |

This is head acceptance at each arm's frozen threshold, with the role guard,
not downstream register writes after scope/lifecycle guards. B uses its unchanged
preceding-sentence/history pairing; C receives the full current message. The
SETUP gold includes admit and supersedes events. C's two errors are the task
selection sentences “Work on task S1n1A.” and “Work on task S3n1A.” on otherwise
positive turns; neither is the formal request template. The <=2/96 registered
SETUP condition passes; the held-out recall failure still decides NO-GO.
SETUP was never used for fitting or threshold selection.

| Warm CPU latency,4 threads, milliseconds | C p50 / p95 | B p50 / p95 |
|---|---:|---:|
| Held-out (329 calls after first) | 50.67 / 60.27 | 48.60 / 54.82 |
| SETUP (95 calls after first) | 60.69 / 119.28 | 62.74 / 96.35 |

Timing includes tokenization and head decisions, excludes model loading; all-call
distributions and maxima are in summary.json. These are component latencies,
not a measured integrated shipping build.

**Fit lineage and stability.** Kimi 2872 with all 53 Opus label replacements plus
Opus 231 gives3103 messages/1493 spans. Patch `drop:true` removes invalid rules,
retaining negative messages, consistent with the audited after-counts. No author
scenario IDs exist in training: the conservative whole-domain split keeps source
batches and matched quote/adoption pairs together. Marketing/travel are DEV 309
(9.96% of messages;2/20 domains); fit 2794. Fit1346/DEV 147 gold spans; no exact
normalized message overlap within the corpus or with the new Fable bank.

| Seed | DEV threshold | Overlap micro P / R | Gold-empty false admissions |
|---|---:|---:|---:|
| 0, designated | 0.9883976740722434 | 97.83% / 91.84% (135/147 recall) | 3/183 (1.64%) |
| 1 | 0.9768228882950498 | 97.87% / 93.88% (138/147 recall) | 3/183 (1.64%) |
| 2 | 0.956549283252651 | 97.87% / 93.88% (138/147 recall) | 3/183 (1.64%) |

Each seed completed 468 updates/three epochs on 4990 candidates. DEV has614
candidates; no fit/DEV overflow. Seed0 was designated before fitting; seeds1/2
were never evaluated on Fable-2. All thresholds maximize DEV overlap recall
subject to<=2% false admissions on gold-empty messages, using the lowest feasible
observed probability threshold. The optional auxiliary flags were omitted;
the model is a binary standing-rule sentence tagger with whole-message context.

GPU allocation, conservatively including loading, CPU calibration and saving,
was 212.346/3600 seconds (3.539min); peak torch allocation 4.342GiB. The ten-update
pilot projected 498.247 seconds. All work ran in the foreground; the owned flag
was removed naturally. No process was signalled, no benchmark/sealed input read,
and nothing pushed. Weights stay local and untracked; metadata/hashes are committed.

Six focused tests and scoped lint pass; real CPU smoke validates full-message
pairing, overflow abstention and role rejection. [audit.json](audit.json) replays
all 426 records and all DEV calibrations, verifies frozen hashes and the GPU cap.
[independent-audit.json](independent-audit.json) independently checks852 arm
predictions using bitmask matching, macro recomputation, source snapshot identity,
cutoffs, B's raw-logit softmax, and the binomial-CDF equation for every CP bound.
B's nine checkpoint files match check44's original freeze. No audit reran inference.

## Orchestrator addendum after the fable accuracy review (2026-09-06; results/check44b-review-fable.md)
Numbers reproduced exactly against the held-out author's gold; no held-out look before the freeze. Two reporting
corrections: (1) the sentence splitter's candidate ceiling on held-out-2 is 176/207 = 85.02%, so the registered 85%
recall bar coincided with the ceiling — 31 of C's 56 misses are two-rule messages whose clauses share one splitter
sentence and no threshold or C/B head combination can recover them; (2) the held-out's two-rule messages are single
sentence lists (31/31) versus ~16% in the fit corpus (authoring-form shift). Consequence: check 44c must change
candidate generation (token-level span tagging), not only the data; held-out-3 is the next decision bank.
