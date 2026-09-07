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

## Orchestrator addendum after the Opus maximum-reasoning review (2026-09-07; results/composition-pilot-5-review-opus.md)
Every headline number reproduces; the pinned tree, launch command and 112 replayed prompts verified. INELIGIBLE
stands, but the report's central framing is WRONG and is corrected here.
THE REGISTER ARM'S EXECUTION DEFICIT IS AN INSTRUMENT ARTIFACT, NOT A REAL EFFECT. Causes:
1. All 65 R non-executions are "too many fences" (64) plus one syntax error — the model emits BOTH core.py and
   policy.py, or re-opens a fence after a bare path line. N's 16 and T's 24 are the same modes. Zero empty replies,
   zero missing fences, zero replies answering the rendered rules.
2. Failures are per-EPISODE, not per-round: R fails all 16 rounds of four lanes, N all 16 of one, T all 16 of one.
   No fence failure ever occurs after a clean round 0 and 0 of 96 locked rounds recover — the model copies its own
   round-0 layout out of history and the feedback it receives is an opaque category token. So 105 non-executions
   come from 9 initiating events; the correct unit is the LANE: R 4/8 vs N 1/8 vs T 1/8, Fisher two-sided p = .282.
   R also succeeds on the lane where N fails, so the effect is not even monotone. The knife-edge is one token:
   "# core.py" parses, "core.py" alone does not.
3. Root cause is the SYSTEM PROMPT (slab2.py:63 "…```python core.py or ```python policy.py"), not the rendered
   register block, which contains no backticks and nothing implying two files.
4. The execution metric is arm-neutral (strict 63/112/104 vs pinned-executor 64/112/112; ranking unchanged).
   R == O is expected and verified byte-identical at the PROMPT level; no arm shared history or cache.
TWO REAL FINDINGS THE REPORT OMITTED: (a) the indent floor fails BY CONSTRUCTION — no arm satisfies indent before
turn 11, so the floor counts rounds nobody could satisfy and `kinds<2` cannot pass; (b) on the 47 cells where all
three arms wrote a file, R is 0/47 on indent and 0/12 on format while best on delivery (19/19), and on matched
post-change non-breakage rounds indent is R 0/9 vs N 8/9 and T 8/9 (two discordant episodes, sign-test p = .5 — a
LEAD to investigate, not a result).
COST: the projection is exact and FALLS if execution rises (honest range 6.6-7.8 h); the real risk to the 12 h gate
is the omitted mandatory Q arm at roughly +2.6 h, giving ~10.4 h.
REGISTERED NEXT STEP: rewrite slab2.py:62-64 so one worked example shows a single fence opener carrying the path;
add a shape restatement to the ReplyError feedback; register the LANE as the execution unit; fix the floor
denominator. Then a ~10 GPU-minute 8-lane screen, NOT a full re-pilot.
