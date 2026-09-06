# Mechanical header repair, before any held-out prediction

The committed author bank has339 JSON lines: one summary object followed by the
registered338 messages. The initial loader treated every JSON object as an item
and stopped at its count assertion, after24GPU DEV calls and83.269454GPU seconds.
No held-out model call, score, item deletion, gold adjustment or outcome inspection
occurred. Only the header/schema/count were inspected to diagnose this mismatch.

Preserve that script, INVALID summary, original start receipt,24DEV records,
timing and raw console under preflight-v1/. The source bank was opened during
preflight and metadata diagnosis; “one look” here remains one prediction pass,
not a claim that the source bytes were opened only once. No message wording was
used to change the prompt, schema, weights, threshold, validator or GO bar.

Repair only the bank loader (skip exactly one leading {summary:...} object and
assert its338 count), audit loader, and a guarded resume path. Resume reuses the
same24DEV records, reloads the unchanged models, and carries83.269454 seconds into
the5400-second budget. The original run-start and an additional resume-start
receipt prohibit a second held-out pass. Original recipe and README remain
unchanged; repair-freeze.json binds the original/new script hashes and bank.
Synthetic header/no-header/extra-item/bad-header-count consumer tests pass;
original provenance/matching/bound selftests and lint pass. This repair is
committed before any held-out prediction. C remains skipped at the original
870-row arm-construction check; there is no new arm, fit or DEV inference.
