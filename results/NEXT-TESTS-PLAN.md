# Combined test plan for the four open problems — 2026-09-07

Sources: results/open-problem-{1-admission,2-context,3-offtask,4-self-managing}-astra.md and
results/probe-data-inventory-astra.md. Ordered cheapest first. Nothing here touches the running 64-episode test.

## The one hard blocker, and the long pole
**No clean evaluation bank exists for automatic rule admission.** Held-out sets 1-3 are exposed; set 4 had its
annotation conventions used in a training repair; the gate SETUP bank is development-only. Every admission or
updater claim therefore needs a NEW author-disjoint bank before it can be certified. That authoring is CPU-only and
independent of everything else, so it starts first and runs while the other tests proceed.

## Tier 0 — zero GPU, runnable now
| # | Test | Question it answers | Pass reading |
|---|---|---|---|
| T0.1 | Text-side detector on saved pilot-7 rounds (rendered prompt, emitted text, trailer, diff), leave-episodes-out over 7 groups | Can we flag an off-task round from text alone, before paying for internals? | Beats the base-rate predictor on held-out groups by a stated margin; else the text side is closed and only internals remain |
| T0.2 | Compact-rendering comparison on CPU: current block versus a delta-plus-digest rendering of the same live view | How much of the block is removable without losing any live obligation? | Token reduction with byte-identical obligation content on every scheduled register; a loss of any live value fails |
| T0.3 | Proposer-plus-verifier prep: build the verifier contract and run it over saved check-46 proposals | Does a verification pass convert the trunk's 79%/90% into something safe? | Precision rises with recall loss under a stated bound, on development data only; not a certification |

## Tier 1 — about 11 GPU-minutes, the moment the GPU frees
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
| T2.1 | Admission proposer-plus-verifier screen on the NEW bank | Does verification make automatic admission safe enough to ship as assistive-plus-adopt? |
| T2.2 | Structured suffix for co-emitted register proposals, no fine-tune | Brian's self-managing idea, cheapest form: can the model propose register ops alongside its answer at usable precision? |
| T2.3 | Verbalized self-rating versus an activation probe, same data, same splits, plus a base-rate baseline | Does the model's spoken self-assessment add anything over its internal state? |

## Tier 3 — only if Tier 2 earns it
Fine-tuned updater (the fitted version of T2.2); learned prefix or gist compression for the rule block; the
corrected check-49 successor for adapters as a focus carrier.

## Standing constraints for all of the above
Fit or select on no evaluation benchmark and no exposed bank; data-lineage line first; pre-written readings; one
look per bank; the episode is the unit; Opus at maximum reasoning reviews every result; the running experiment's
records must never become training data for any of these fits.
