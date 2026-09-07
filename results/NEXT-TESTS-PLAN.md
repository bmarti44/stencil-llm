# Combined successor and six-open-problem test plan — 2026-09-07

Both larger runs are complete and frozen: [FAIL](larger-test/RESULTS.md) and [narrow PASS](larger-test-v2/RESULTS.md). Neither may be rescored. The adequate-proof gate is not met. All tests below are prospective and require their own bank, recipe, authorization and timing checks; this is not a launch queue.

## Agreed main successor

A fresh 32-episode paired factorial, 16 rounds, whole-file/scoped × N/R/composed-prose T: 3,072 calls, estimated 5.31645 GPU-h (about 5.32), proposed 6h ceiling. Use final private-test integration and joint integration-plus-adherence as primary outcomes; freeze semantic parameterizations, content-matched comparators, scope contrasts and multiplicity before evaluation. New bank/registration/implementation and measured preflight remain outstanding. [Design and cost derivation](larger-test-v2-review-astra.md).

A concurrent later [ledger entry](../plan/LEDGER.md) records automatic-maintenance preparation and defers this factorial; see the [handoff conflict note](HANDOFF-astra.md). The earlier agreed design remains costed here, but must not be mistaken for the live session’s next launch.

## Admission bank status and report-to-test map

The [clean admission bank](../data/classifier/heldout/clean-admission-bank-v1.jsonl) now exists and is tracked, reserved for admission screens according to the [problem 5 report](open-problem-5-compliance-competence-astra.md). The former claim that none exists is stale. This docs audit verified presence, not unexposed lineage or fitness for any screen: independently certify authoring, access history and scenario-disjoint allocations before opening it. Heldout sets 1–4 remain exposed or development-informed. This is not a coding bank; the factorial bank remains to be authored.

| Open problem and report | Costed next test and dependency |
|---|---|
| [1: automatic admission](open-problem-1-admission-astra.md) | CPU verifier preservation screen: 0 GPU-h; CPU fit capped at 90 wall-minutes. Original authored fit/DEV only; frozen replay of check46 is exposed diagnostic evidence, not certification. Generative alternatives each cap at 1 GPU-h and require separately reserved clean screens. |
| [2: context cost](open-problem-2-context-astra.md) | 35-fixture CPU codec test: 0 GPU-h, all state/provenance invariants, ≥40% block-token saving, no fixture larger. Conditional fresh-bank behavior screen ≤0.75 GPU-h; mask alternative 0.90h, FP8 alternative 0.75h. |
| [3: off-task detection](open-problem-3-offtask-astra.md) | Public shadow verifier and episode-held text baseline: 0 GPU-h. Original 192-prompt hidden-feature proposal caps at 1 GPU-h; the narrower [inventory proposal](probe-data-inventory-astra.md) projects 11.44 prefill minutes for 87 records, excluding a full occupied-time guarantee. Choose and freeze one allocation. |
| [4: self-managing co-emission](open-problem-4-self-managing-astra.md) | Frozen answer-plus-proposals comparison, CPU authority/source audit first; 48 DEV calls plus 96 fresh-bank calls, 1 GPU-h total ceiling. New independent bank and operation contract required. |
| [5: compliance without competence](open-problem-5-compliance-competence-astra.md) | Three alternative 4B feasibility screens, each ≤1 GPU-h, requiring fresh executable banks and zero extra competence losses against the specified text comparator. Not three authorized hours; main 32-episode factorial is the agreed larger-trunk successor. |
| [6: DIRECTER reproduction/guard](open-problem-6-directer-astra.md) | CPU paper/code/scorer reconciliation first. Faithful reproduction expected 12.82–22.85 GPU-h under stated rate assumptions, 30h stop-loss and admission projection ≤24h. Cheaper transactional-guard transfer: 4–8 CPU engineer-hours, ≤45min DEV then projected 5.08h evaluation, total 5.83h and 6h stop-loss. Missing scorer and three reported paper/code discrepancies prevent turnkey reproduction. |

The report costs are proposals, not measurements of completed successor tests. Historical “running” restrictions in the reports describe their creation time; they grant no current launch authority. The selected test must resolve overlapping bank allocations and inconsistent draft endpoints prospectively.

## Tier 0 — zero GPU, preparation proposals
| # | Test | Question it answers | Pass reading |
|---|---|---|---|
| T0.1 | Text-side detector on saved pilot-7 rounds (rendered prompt, emitted text, trailer, diff), leave-episodes-out over 7 groups | Can we flag an off-task round from text alone, before paying for internals? | Beats the base-rate predictor on held-out groups by a stated margin; else this fixed text recipe fails; other text detectors remain open |
| T0.2 | Compact-rendering comparison on CPU: current block versus a delta-plus-digest rendering of the same live view | How much of the block is removable without losing any live obligation? | Token reduction with byte-identical obligation content on every scheduled register; a loss of any live value fails |
| T0.3 | Proposer-plus-verifier prep: build the verifier contract and run it over saved check-46 proposals | Does a verification pass convert the trunk's 79%/90% into something safe? | Precision rises with recall loss under a stated bound, on development data only; not a certification |

## Tier 1 — projected 11.44 prefill minutes, after authorization and timing
| # | Test | Question it answers | Pass reading |
|---|---|---|---|
| T1.1 | Hidden-state recovery on pilot 7's 87 matched arm-round records (five layers, last-prompt-token, forward passes only, no generation), then a contrastive probe fit leaving episodes out | Brian's question: can a probe read task alignment, fitted on aligned versus misaligned matched pairs? | Beats both the base rate and T0.1's text baseline on held-out episodes; a null closes the cheap version and leaves the 4B judge as the fallback |

Inventory receipts: 87 distinct records; indent 10 cells across 4 episodes, format 16 across 4, delivery 9 across 7;
1,781,760 raw bytes; 11.44 projected prefill minutes. Pooling all pilots costs 143 minutes and does not cure the
eight-episode limit, so start with pilot 7 alone. Saved hidden states DO exist from the earlier HF-era runs; none
exist in pilots 5-7 because the vLLM path never returns them.

## Tier 2 — about one GPU-hour each, after Tier 1 reports
| # | Test | Question it answers |
|---|---|---|
| T2.1 | Admission proposer-plus-verifier screen on a newly certified reserved allocation | Does verification make automatic admission safe enough to ship as assistive-plus-adopt? |
| T2.2 | Structured suffix for co-emitted register proposals, no fine-tune | Brian's self-managing idea, cheapest form: can the model propose register ops alongside its answer at usable precision? |
| T2.3 | Verbalized self-rating versus an activation probe, same data, same splits, plus a base-rate baseline | Does the model's spoken self-assessment add anything over its internal state? |

## Tier 3 — only if Tier 2 earns it
Fine-tuned updater (the fitted version of T2.2); learned prefix or gist compression for the rule block; the
corrected check-49 successor for adapters as a focus carrier.

## Standing constraints for all of the above
Fit or select on no evaluation benchmark or its recorded responses; no evaluation-outcome selection. Exposed DEV-only diagnostics must be explicitly separated from certification; data-lineage line first; pre-written readings; one
look per bank; the episode is the unit; Opus at maximum reasoning reviews every result; either frozen larger run’s
records must never become training data for any of these fits.
