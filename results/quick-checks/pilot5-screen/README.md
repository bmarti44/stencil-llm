# Pilot-5 Amendment 3 screen — awaiting GPU

Registration: `tests/fixtures/slab2_cpu_report.md`, SLAB-2 Amendment 3, written before code.
Fit-on none; screen evaluated-on authored DEV00/01 only. No benchmark reads or fitting.
The corrected saved pilot-5 floor is [recorded here](pilot5-corrected-floor.json):
language72/128, indent13/39, format22/35, delivery42/49, delivery_scope0/44.
Language, format, delivery qualify; only process qualifies among the two primary
substitution kinds (style/process). The historical pilot remains INELIGIBLE.

Historical projection: measured Q-exclusive7.774h; estimated repair range6.6–7.8h;
mandatory Q at N-like cost adds2.613h, yielding approximately10.4h at the upper end.
Q's actual cost must be measured in the full pilot before the larger test.

Eight lanes only: DEV00/01 × R/N/T/Q,16 rounds,cap1024, qualified invariant bf16
vLLM. Same system text in every arm. Lane execution means at least one actual file
write; all16-failed lanes count once. Report strict per-round execution descriptively.
Two fixed C4 groups (one episode's R/N/T/Q each). Mixed-arm screen timings cannot
replace the registered same-arm-C4 full-run cost projection.

PRE-WRITTEN READING: SCREEN-PASS requires all128 records, zero round-0 fence failures,
executing lanes8/8, and >=90% strict round execution in every arm. It authorizes full
pilot6 (8 DEV episodes,R/N/T/Q,16 rounds), whose ELIGIBLE reading authorizes the larger64.
Any round-0 fence failure is SCREEN-FAIL: publish literal outputs and do not enlarge.
Other incomplete/low-execution outcomes are SCREEN-NOT-PASS; no enlargement.
Screen budget900 GPU-held seconds including startup/cleanup; no host process signals.
