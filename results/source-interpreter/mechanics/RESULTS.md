# Four-update mechanics measurement: completed, audit pending

2026-09-08. The first and only registered run completed all four optimizer
updates and its standard adapter save/archive/reload checks. Exact outer session
10691 terminated with exit 0. The runner and outer observer report completion;
independent Astra result review remains pending. No semantic generation, held-out
evaluation or coding task ran. This is feasibility evidence, not learned transfer
or completion of the broader automatic-focus goal.

Fit-on: only accepted FIT conversation `source-fit-cal-20260908-04`, query 2,
preview row 14. Each update used the full 3,891-token sequence with 2,966 masked
prefix positions and 925 supervised target/EOS positions. The four updates repeat
one example; they are not four independent learning tests. The final loss call
also uses that same FIT example. Any later full training starts with a fresh
adapter and excludes this mechanics adapter.

| Recorded measurement | Result |
| --- | ---: |
| Entire supervisor process, including final publication and exit | 125.124811046 seconds |
| Registered outer limit | 600 seconds |
| Updates | 4: one warm-up, three timed |
| Timed forward/backward/optimizer mean | 3.316989359 seconds |
| Timed forward/backward/optimizer maximum | 3.320252671 seconds |
| Peak Torch allocated memory | 16,003,389,952 bytes (14.904 GiB) |
| Peak Torch reserved memory | 17,655,922,688 bytes (16.443 GiB) |
| Trainable FP32 adapter parameters | 2,949,120 in 144 tensors |
| Original parameters with unchanged recorded identities/bytes | 4,022,468,096 in 398 tensors |
| Standard saved adapter | 11,815,504 bytes |

Timed steps are the synchronized forward/backward/optimizer intervals, not the
entire step's receipt and validation overhead. The outer duration includes the
full supervisor process. Reported stage intervals include 3.762 seconds for
artifact qualification, 2.759 for runtime/tokenizer qualification, 77.818 for
model setup and initial checks, 0.257 for save/archive, 23.415 for reload and
final checks, and 0.255 for cleanup. These grouped intervals must not be relabeled
as isolated disk-load or adapter-inference timings.

All four step receipts report finite positive losses and nonzero aggregate
gradients/updates. The first update has 72 nonzero-gradient tensors; subsequent
updates have 144, consistent with the allowed zero-initialized LoRA factor.
Loss decreased on the repeated FIT row; loss decrease was not a pass criterion
and establishes no transfer. The post-reload, no-gradient FIT loss computation
completed without an optimizer update.

Root independently reconciled the four final step files with the result and all
20 recorded intent/pending/completion/validation transitions; exact causal-loss
positions; 398 matching before/after base-weight hashes; adapter header parameter
counts/dtypes/shapes; and full/part/reconstructed byte hashes. This audits the
recorded runtime evidence without rerunning training or loading a model.
The outer exit is 0.066388641 seconds after the runner's finalization timestamp,
covering its explicitly excluded final-publication/exit tail. Both owned process
exits are confirmed, the run flag is cleared, and a subsequent GPU process query
and run-flag scan are empty.

Evidence: [frozen launch plan](launch-plan.json),
[outer observation](observer-01.json), [full result](run-01/result.json),
[lifecycle](run-01/lifecycle.json), [step history](run-01/steps.jsonl),
[stage history](run-01/stages.jsonl), [binary description](adapter-description.md),
and [canonical independent review](../mechanics-review-astra.md).
Launch freeze: `a87a9e1de59a9d84eb1442ff035b92a6f69f5773`.
Result SHA-256:
`4829ecbbf212d02f7bf2b5b142fb28a42d3027565e2437551f952855880b9d07`.
Outer receipt SHA-256:
`dfb876be456264f83fceaee5127c8beebb95e9419e077e0496b447059511abcf`.

Next, if the audit accepts these measurements: cost and register a fixed full
FIT run and a fresh same-base-versus-adapter semantic experiment. That experiment
must test new conversations; useful coding behavior and adequate larger
executable proof remain separate, unestablished requirements. Automatic parity
with useful manual prose remains a meaningful benefit.
