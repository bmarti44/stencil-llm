# Composition pilot 4 — REGISTERED, not yet run

2026-09-06. Amendment 3 in ../composition-pilot-3/README.md governs the CPU
fixes and this run. Frozen order 00,01,06,07 then 02,03,04,05; R/N/T then optional
O. 9000 GPU-seconds, one qualified start, cold reverse C4 long-prompt replay
before first-eight cold/warm/mixed replay. Exact gates and cost formula are in
Amendment 3 and pilot3 prewritten registration; hidden states deferred.
Fit none; DEV only; no data/bench or evaluation episodes. Package path
outcome-unvalidated. No host signals, own container only; no push.

CPU regression: R executed 53 ->101/160 (63.125%); N49 ->77/160 (48.125%);
T65 ->84/140 (60%). Caps unchanged R59/N82/T52. All460 literal outputs traverse
Executor.run/check; format violations remain460/460 because old task strings
are preserved. Per-kind outcomes and source hashes: regression.json and
regression-records.jsonl. These do not predict amended model outputs.
Validation:30 targeted tests pass;96-call reference loop smoke passes.
HTTP streams remain local, excluded from git with size+sha256 manifest.
Any artifact above10,000,000 bytes likewise remains local; compact shards are
committed when necessary. tools/hooks/pre-commit checks staged blob sizes.
