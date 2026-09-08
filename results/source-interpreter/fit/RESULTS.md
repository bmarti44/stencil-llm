# Fixed FIT training and generation-cost result

2026-09-08. **Actual run complete; independent accuracy review pending.**
The fixed training/persistence and two-call cost measurement completed, but the
trained adapter's FIT response hit the registered cap and is incomplete JSON.
This is not a semantic or coding-utility success.

Fit-on: eighteen accepted query rows from six families assigned FIT before Kimi
K3 authoring. Generation timing used only the accepted longest FIT prefix,
row14 (2,966 IDs), with no target IDs or labels supplied. Development-on and
evaluated-on: none. No fresh heldout source, spent DEV bank, benchmark, old
adapter or old response entered this run. No new semantic data was generated.

The single launch was frozen at `fe1d0112`, using launch-plan.json SHA256
`396632617e32ea11c250b5d291dcf2030e88c1d75dae623a73d89ae3aff4b097`.
Exact exec session67209 terminated with exit0; it must not be restarted.
ObserverPID165749, supervisor/privategroup165750 and modelchild166299 all exited.
The outer receipt is COMPLETE_UNREVIEWED, the inner lifecycle COMPLETE. No
retry, cap change, repair, output extraction or extra model invocation occurred.

## Training and persistence

A fresh rank8 q/v FP32 LoRA adapter was trained on the original frozen BF16
Qwen3-4B, using the accepted three-epoch schedule: **54 validated updates**,
**89,343 presented sequence tokens**, **21,702 supervised target/EOS tokens**.
The 18 rows repeat three times; they are not54 independent examples. Every
row identity, label position and causal prediction position reconciles with the
saved preview and fixed schedule. All losses and aggregate adapter gradient/
update norms are finite and positive; no loss-decline or semantic gate was used.

All270 durable update transitions reconcile with the54 final step receipts.
The recorded before/after hashes of398 original tensors (4,022,468,096
parameters) match; the runtime identity/absent-gradient checks also pass.
Original byte verification covers the job endpoints, not every individual step.
All144 saved FP32 adapter tensor payloads match the final optimizer-step hashes.
Standard save, exact byte-part reconstruction and same-trunk reload equality pass.
The fresh final adapter has2,949,120 parameters and11,815,504 standard-file bytes;
SHA256 `1f9392f3fa99cb31a010176487a6f37999f02cdbc7be9b9cdb4a9b9380e592e3`.

## Two fixed FIT-only generation calls

| Mode, fixed order | Generated tokens | Whole generate latency | EOS | Strict JSON/schema result |
| --- | ---: | ---: | --- | --- |
| Original base, adapter disabled |703|40.517819119 seconds|Yes|Valid; response complete|
| Reloaded trained adapter |2048|123.050696406 seconds|No|Cap reached; invalid/incomplete JSON|

The base payload is2,867 UTF-8 bytes. The adapter payload is9,115 bytes; strict
parsing reports an unterminated JSON string. All prompt, complete-output,
generated and payload IDs and exact decoded bytes/hashes remain in the two
per-call receipts. Both calls used the same original trunk and source prefix,
with greedy decoding, EOS151645, pad151643 and max_new_tokens2048. Native resolved
configuration records max_length5014, min_length0 and repetition_penalty1.0;
forward/control arguments are separate. The raw stderr includes a warning that
`top_k` is inactive/ignored under this greedy path; no settings were changed.

Neither call hit its300second time reservation. The adapter reached the token
cap, not the time or context bound. A complete cost record does not turn that
failed response into a semantic pass. Base structural validity also does not
establish correct instruction selection. No FIT gold comparison or new-conversation
semantic evaluation was performed. Different output lengths and fixed call order
prevent interpreting this pair as a matched latency or token-rate benchmark.

## Observed resources and limits

Whole observed supervisor interval, including startup, training, generation,
final hashing, lifecycle publication, process exit and required group checks:
**351.821924262 seconds** (about5minutes52seconds), under the2,400second limit.
The outer observer saw the durable transition into base generation by
**161.890731962 seconds**, establishing the initial1,220second training/persistence
bound. This is an observed upper bound through training completion, not an
isolated optimizer or model-loading time. The inner lifecycle records
351.619755533 seconds; its final publication/exit tail is covered by the outer
interval. Child result timing350.190441937 seconds has a narrower scope.

The recorded pre-cleanup Torch peaks are16,003,383,808 allocated bytes
(14.904312611GiB) and27,353,153,536 reserved bytes (25.474609375GiB), onGB10 unified
memory. These are allocator measurements, not a separate nvidia-smi memory pool.
Runtime: Python3.12.13, Torch2.13.0+cu130, Transformers5.16.1, PEFT0.20.0.
Post-run checks find no GPU compute process, no RUNNING.flag and all three
recorded owned PIDs absent. No experiment process remains to poll or resume.

## Evidence and next decision

Root's standard-library reconciliation checks all54 step files/270 transitions,
row schedule, label positions,398 original hash pairs, all144 saved tensor bytes
against the final step, archive/reconstructed byte identity, both raw output
receipts and actual clock bounds. See root-reconciliation.json. This checks
recorded evidence without re-running the model; independent Astra audit is next.

The full and reconstructed standard checkpoint files remain local because they
exceed the10MB commit limit. Exact9,000,000 and2,815,504 byte archive parts,
configuration, per-step/per-call receipts and logs are retained for archival.
See adapter-description.md for reconstruction and contents.

The fixed run has produced an adapter and observed costs, plus one concrete
capped FIT failure. It does not establish transfer, useful automatic focus or
better coding. After independent audit, decide and prospectively cost the next
fresh same-base/adapter comparison while counting malformed/capped outputs as
failures. No perfect-FIT-format prerequisite is introduced, and no retry or
output-based recipe repair is authorized by this result. Adequate larger fresh
executable coding proof remains required for the full goal; automatic usefulness
comparable to good manual prose remains a meaningful benefit.
