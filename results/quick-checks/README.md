# Quick checks (2026-09-02, orchestrator, GPU idle, ~40 min total) — sharpening the odds before the G0 pilot

All on the 20 H1' sessions (data/b3 mt-train-300 dev probe; NOT a gate benchmark), reference = the FULL arm's own
greedy output, same eviction plumbing as the registered probe (scripts/ledger_kv_probe.py) and the pilot (scripts/g0_oracle.py).

1. Leave-one-out loss oracle (oracle_check.py, oracle_check_loo.log): evict one span's KV columns, teacher-force the
   model's own 96-token continuation. Known constraint spans vs exact-column controls: AUROC 0.494 (mean delta),
   0.48-0.52 on every per-token readout (max, sum-positive, top-3, top-1 flips). NO SIGNAL. Cause: prior compliant
   assistant turns make each constraint sentence redundant (sol G0R-4 non-additivity, seen live).
2. Keep-one-in oracle (oracle_check_keepin.py, oracle_check_keepin.log): evict the whole range except one span.
   Gap all-evicted minus full = 2-4 nats/token; single spans recover up to 1.2. Constraint vs control AUROC 0.518
   (mean), 0.63 (top-3), 0.60 (top-1 flips back). WEAK: the "controls" are the task sentences the model also needs to
   reproduce its own continuation, and a 96-token prefix cannot see late-acting constraints. The loss oracle measures
   need-to-reproduce-content, not adherence to standing constraints.
3. BM25 query-time retrieval, CPU (in WORKLOG): constraint-token coverage at the finder's budget 0.37 vs random 0.13,
   recency 0.02. Lexical retrieval with the current turn as query misses delayed constraints.
4. ROLE RULE on checker outcomes (role_rule_check.py, role_rule.log): pin ALL prior user turns (no finder), evict the
   rest, score exactly as H1'. Aged constraints passed / 56:
   full 44 | evicted 14 | finder-pinned (H1') 37 | finder control 18 | ROLE 41 | role exact-column control 26.
   Recovery (41-14)/(44-14) = 0.90. Safety: role truncated 1, degenerate 1 (full: 1 / 2). Budget: role pins mean 89
   columns = 20% of evictable (finder: 47). Per session vs finder +4/-1/=15; vs full +3/-5/=12.
   A parameter-free rule with no selector recovers 90% of the eviction gap on this probe.
