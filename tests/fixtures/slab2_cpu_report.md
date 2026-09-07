SLAB-2 CPU audit and pilot-5 registration (2026-09-06)

fit-on=none; development-on=authored DEV grammar; evaluated-on=authored evaluation grammar, template/seed-disjoint; no benchmark content or responses.
72 episodes, 16 rounds, all four arms: 4,608 real-loop stub calls. No GPU inference.
All references pass public/hidden tests and all live traits. This does not measure model competence or GPU cost.
Evaluation updater is a public-text CPU test double; no evaluation gold events are passed to the loop.
T-floor must be frozen on actual DEV T responses before evaluation; stub compliance does not qualify traits.
Compact omission and unscoped delivery omission have separate denominators; verbose compliance cannot raise their floor.

Pilot-5 ELIGIBLE: executed (parsed trailer + file written) >=90%; caps <=2%; T-floor >=50% with >=2 kinds having nonzero retirement denominators in >=2 episodes; R final >=5/8; measured registered projection <=12 GPU-h.
Cost applies only to R/N x64 + nested O/T x16 at 16 rounds. Prior pilots are development cost, excluded.
A measured projection in (12,15] GPU-h triggers 12-round episodes with a shortened lifecycle schedule re-frozen and DEV-validated before evaluation; keep every arm. Above 15: stop. Only 16-round lanes implemented now.
Projection API uses measured, non-overlapping GPU-held lane allocations plus load and a 1.25 reserve; no CPU timing is substituted.

| Arm | Max context | Registered input tokens | Registered output tokens | Output tokens/lane min–max (eval) |
|---|---:|---:|---:|---:|
| R | 13,183 | 5,959,731 | 238,522 | 3,133–4,466 |
| N | 7,005 | 2,913,678 | 238,522 | 3,133–4,466 |
| T | 8,068 | 861,943 | 58,682 | 3,133–4,466 |
| O | 13,183 | 1,485,155 | 58,682 | 3,133–4,466 |

Context excludes the reserved 1,024-token reply; every arm satisfies paired_context_gate at 32,768.
slab2_cpu_audit.json contains each of 288 lanes and all 16 per-round input/output counts. Registered totals count only the frozen nested subset for O/T; the CPU audit covers all four arms on all 72 episodes.
Six independently authored interface fixtures are in slab2_replies.json. Pilot-4 literal outputs were not reused.
CPU final audit journal/checker files: /tmp/slab2-cpu-final-20260906 (local, not committed).

Validation: `CUDA_VISIBLE_DEVICES='' .venv/bin/python -m pytest -q tests/test_focus_slab2.py tests/test_no_side_effect_imports.py` — 92 passed, 1 expected xfail (88.87 seconds). Ruff and whitespace checks pass.
Output tokens per DEV lane: 3,125–3,720; per evaluation lane: 3,133–4,466; largest individual stub reply: 577 tokens.
