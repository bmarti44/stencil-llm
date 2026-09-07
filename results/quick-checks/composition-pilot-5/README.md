# Composition pilot 5 — INELIGIBLE

DEV only; pinned SLAB-2 `9f0c6d27`, qualified invariant vLLM bf16/Triton. User cap **1024**, 16 rounds, fixed same-arm C4 groups. T ran first to freeze its floor before success scoring; then R/N and optional O. No fitting, evaluation-bank or benchmark reads.

**Failing gates:** R executed<90%; N executed<90%; T executed<90%; T floor substitution kinds<2; R final<5/8.

| Arm | Calls /128 | Parsed + written | Caps | Final success /8 | Largest reply | Output tokens | Model/reference x |
|---|---:|---:|---:|---:|---:|---:|---:|
| R | 128 | 63/128 | 0/128 | 0 | 776 | 36079 | 1.352 |
| N | 128 | 112/128 | 0/128 | 4 | 738 | 31784 | 1.191 |
| T | 128 | 104/128 | 0/128 | 3 | 598 | 31854 | 1.194 |
| O | 128 | 63/128 | 0/128 | 0 | 776 | 36079 | 1.352 |

Execution requires a parsed trailer and an actual file write. Syntax/parse-depth attempts are excluded even though the pinned executor labels them executed. Every cap is a failed attempt. Each R/N/T arm must independently reach 90% execution and at most 2% caps.

T-floor table (at least 50% applicable T observations must satisfy the trait):

| Trait / kind | Frozen T satisfied / applicable | Written-file-only sensitivity | Enters success | Episodes with substitution/relapse denominator |
|---|---:|---:|---|---:|
| language / language | 72/128 | 72/128 | True | 0 |
| indent / style | 13/128 | 13/128 | False | 8 |
| format / format | 22/35 | 19/35 | True | 8 |
| delivery / process | 42/49 | 41/49 | True | 8 |
| delivery_scope / process | 0/44 | 0/44 | False | 0 |

Only indent/style and delivery/process count toward the two-substitution-kind gate; omission traits remain floor-gated for success and descriptive for relapse. Floor was frozen from all128 T records before success scoring.

| Arm | Trait / kind | Relapse / denominator | Of denominator, prior trait present |
|---|---|---:|---:|
| R | language / language | 0/0 | 0 |
| R | indent / style | 0/20 | 6 |
| R | format / format | 16/16 | 16 |
| R | delivery / process | 0/5 | 5 |
| R | delivery_scope / process | 0/0 | 0 |
| N | language / language | 0/0 | 0 |
| N | indent / style | 6/33 | 18 |
| N | format / format | 5/31 | 31 |
| N | delivery / process | 8/10 | 8 |
| N | delivery_scope / process | 0/0 | 0 |
| T | language / language | 0/0 | 0 |
| T | indent / style | 0/27 | 9 |
| T | format / format | 4/23 | 23 |
| T | delivery / process | 2/9 | 9 |
| T | delivery_scope / process | 0/0 | 0 |
| O | language / language | 0/0 | 0 |
| O | indent / style | 0/20 | 6 |
| O | format / format | 16/16 | 16 |
| O | delivery / process | 0/5 | 5 |
| O | delivery_scope / process | 0/0 | 0 |

Relapse denominators above require parsed-and-written files, consistently with the user execution definition. The pinned checker also counts parsed syntax-error attempts; those original counts remain in summary.harness_relapse and untouched per-round checks. Zero denominators are unmeasured witnesses. Per-round prior-trait flags, applicability, raw relapse and tolerances are preserved in the records.

Registered-run projection: **7.774 GPU-h**.
O cost source: measured. Fixed C4 grouping must be reused. Startup 494.284s; conservative extra main overhead 9.022s. Formula `(load + 1.25*(64*(R+N)+16*(O+T)))/3600`, where each cost is mean group-wall allocation per episode. Prior pilot spend is excluded; Q is outside this user-scoped run.
GPU held **4869.993/5400s**, including startup, replay and cleanup. Pre-run replay HTTP span 29.777s; all8 output-token/EOS/cap sequences match in forward and reverse C4 order.

The (12,15]h fallback condition was not triggered.

The cap decision is the user-authorized 1024 bet documented in fable H2; later CPU defaults use2048. Blocking parser/repair fixes and N1/N2 transport guards were already committed. This pilot does not measure Q, a learned controller, HF hidden recovery, or held-out performance.

Artifacts: [registration](registration.md), [summary](summary.json), [same-run records](main-records.jsonl), [HTTP hash/timing index](journals-index.jsonl), [local journal hashes](local-hashes.json), [server log](server.log), [CPU audit](audit.json). Raw HTTP payloads and loop journals remain local and out of git. Own container stopped/removed; flag removed; no host process signals or push.

DEV O/R exact output text, token IDs, EOS and cap status: 128/128. This is DEV gold-event equivalence, not learned-controller evidence.

Execution categories (each row sums to attempted calls):
- R: {"fence_count_or_kind": 64, "syntax_error": 1, "written": 63}
- N: {"fence_count_or_kind": 16, "written": 112}
- T: {"fence_count_or_kind": 16, "syntax_error": 8, "written": 104}
- O: {"fence_count_or_kind": 64, "syntax_error": 1, "written": 63}
