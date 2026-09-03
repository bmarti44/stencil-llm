INVALID ORDERING — DO NOT USE AS EVIDENCE

This run (scripts/multiif_evict.py at commit 8018113) evicted AFTER the whole context was prefilled (sol harness review EVICT-1, CRITICAL). Stopped by Brian on 2026-09-03 at 145 of 909 conversations. Records retained per the never-delete rule. The corrected run (eviction before the current-turn prefill, commit 5c743f1) writes to results/qwen/multiif-evict-909-prequery.
