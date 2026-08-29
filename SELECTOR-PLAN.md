# SELECTOR-PLAN — the contentless governor (Miller-faithful split)

New registered program (2026-08-29, Brian-directed), replacing the closed
fused-cache line. The split: **working memory is text** (the ledger, visible
in-context — no contest with storage), and the wire is a **contentless
selector**: it may only decide *which stored obligation governs the current
moment* and press the trunk toward it. It carries an address, never a value.
This is the "mobile stencil" claim proper (Miller et al.: synapses store,
wave dynamics select what is active).

Mechanism: the selector reads recent block-20 hidden states and emits an
**attention spotlight** — an additive attention-logit bias toward the token
span of the governing ledger entry, applied in trunk layers 20-27. It points
at positions; it cannot inject content. Zero-selector = base model exactly.

## Where governance pressure comes from (the task)

Selection must be able to FAIL for a selector to matter. The governance task:
a current-ledger block (N=8 obligations) + an interference block (stale
values of the same fields quoted in chatter, confusable lookalikes, other
fields' values) + queries. The base model sees everything; its failures are
selection errors (echoing stale/distractor values), not knowledge errors.

## Phases (oracle-first; each gated; halting is success too)

- **S0 admission:** base Qwen accuracy on the interference task must land in
  40-80% (headroom exists AND the task is fair), with errors demonstrably
  selection-shaped (stale/distractor echoes). Outside that band: retune the
  task ONCE, then stop if still outside.
- **S1 oracle spotlight (the decisive day-one test):** hand-place the bias on
  the correct span (positions known to the harness). Gate: flips >=50% of
  base errors to correct without breaking correct cases (net gain). Miss =>
  the spotlight actuator is inadequate — stop before building any selector.
- **S2 learned selector:** tiny head (query from h20, keys from span means,
  softmax over spans -> bias). Trained on fresh sessions; gates at step 500
  on fresh validation seeds: closes >=50% of the base->oracle gap, with a
  zero-selector control equal to base. Single registered attempt + one
  registered variant (bias strength/site), then stop condition.
- **S3 drift:** updates mid-stream + compaction with ledger re-insertion;
  measures stale-echo suppression in the owner's scenario shape.

Instruments carried: free-running per-query eval; full-sequence stale-echo
metric at first-divergent-token; immutable VARIANT tags; fresh-seed spaces
(dev 11M-, validation 11.5M-, final 11.7M- untouched); deterministic tests
for: zero-selector == base bitwise, spotlight touches only attention logits.

Stop conditions: S0 band unreachable after one retune; S1 oracle <50% error
flips; S2 both attempts miss; any result requiring unregistered rescue.
