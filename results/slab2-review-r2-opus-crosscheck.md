# SLAB-2 r2 cross-check (Opus reviewer, independent of fable)

2026-09-06 21:40-21:56, CPU only. Independent verification of
results/slab2-review-fable-r2.md against commit 8e037722. No GPU, no RUNNING.flag or
container touched, no data/bench or eval content read (eval enters as aggregate counts
only). No repo code edited; fable's r2 file is byte-identical to HEAD. Line numbers are
8e037722 blobs unless marked "(tree)". Ran myself: `pytest tests/test_focus_slab2.py
tests/test_focus_slab2_driver.py tests/test_no_side_effect_imports.py` -> **110 passed,
1 xfailed** (105 s); 16 adversarial parser probes; a cross-file syntax probe;
independent wording, census and cost recomputation.

| Finding | fable | Me | Evidence |
|---|---|---|---|
| H1 parse-before-write | resolved | **agree** | `ast.parse` slab2.py:470 precedes `write_text` :486; probe: broken policy.py at r2 -> `executed=True breakage=True category='syntax_error' error='syntax error in policy.py at line 1: invalid syntax'` (:475), disk bytes == `last_parsable`; r7 repair `wrong_family=False success=True` |
| H2 cap + wording | resolved | **agree** | `REPLY_CAP = 2048` :41; my scan of all 1,152 requests: 1152/1152 "short one-line docstring", 0 "explanatory"/"boundary behavior"/"Document the"; largest reference over 72x16 = 577 tokens |
| H3 lane-second cost | resolved | **agree** | `MAX_WORKERS = 4` :42, `measured_projection` :747; recomputed `cost_table` :1077 from frozen totals (238642x2 + 58709x2 = 594,702 out; 2,560 calls; 0.8 s TTFT): 9.071182 / 19.483270 / 11.997207 reserved h — bit-for-bit the frozen table |
| M4 delivery-before-format | resolved | **agree** | `witness_census(16)` :1057 = DEV 11 opp / **8/8**, eval 87 / **64/64**; minimums 7 / 56 enforced |
| M5 tolerance set | resolved | **agree** | my 16 probes reproduce fable's table exactly: CRLF, leading/trailing prose, trailing period, status=OK, key order, blank-before-trailer, py/bare/Python tags, leading `<think>`, `Report:` all accepted with correct `tolerances` labels (:364-432); two fences -> `fence_count_or_kind`, trailer inside fence -> `misplaced_trailer`; all ten combined in one reply parses with 8 labels |
| M6 n_rounds | resolved | **agree** | `validate_rounds` :45; dev-00 yields 12 and 16 turns, `n_rounds=14` refused; `freeze_t_floor(...,12)` demands 96 rows |
| M7 GPU driver | resolved | **agree** | `truncated` plumbed and consumed; `test_complete_cpu_driver_floor_and_cost` drives the real `run_pilot` (32 lanes, 512 rows, floor.json before scored.json, `eligible=False`); `test_measured_lane_allocations_with_cpu_injected_decoder` pins lane-second accounting |
| N1 timeout 300 s | new medium | **agree — real, already fixed, uncommitted** | 8e037722:40 `timeout=300`; tree:41 `timeout=1200` |
| N2 stop_token_ids / EOS | new medium | **agree — real, already fixed, uncommitted** | absent at 8e037722:54; tree:56 `stop_token_ids=[151645, 151643]`, tree:74 `raise ValueError("stop without terminal EOS token")` |
| SLAB-1 v1 failures | pre-existing | **agree** | v1 goldens only; SLAB-2 has its own system prompt and fixtures; not blocking |

Corrections and additions (none block launch):

- **Wording, H1.** "later rounds are neither breakage nor semantic" is too strong:
  rounds 3-6 are `breakage=False wrong_family=False` but `semantic=True` — the missing
  `step_2` genuinely fails its case until repaired. Narrow to breakage/wrong_family.
- **O1 (medium, mine): the N1/N2 fixes are uncommitted and unasserted.** No test checks
  `stop_token_ids` is in the payload or exercises the new raise
  (`test_vllm_truncation_through_real_driver` asserts `max_tokens == 2048` only). Commit
  them with an assertion, or a restorer can revert them unnoticed.
- **O2 (medium, mine): the tree is a moving target and was red mid-review.** An active
  coder (pid 3647888, "SLAB-2 Amendment 2": completion-by-evidence, arm Q, arm X) is
  editing `src/stencil/focus/{loop,register,journal,renderer,slab,slab2}.py` and the
  driver. At 21:53 the targeted suite was **2 failed, 108 passed** (`gpu_held_seconds`
  21 vs 17; arm Q changed the lane count); green again at 21:55.
- **Watch item, H3:** the x1.35 scenario reserves 11.9972 h against the 12 h gate; the
  16-round/fallback boundary is x1.3504. Read the measured x-factor first.

## GO / NO-GO

**GO for pilot 5** — 8 DEV episodes x R/N/T at 16 rounds, `max_workers=4`, on the
qualified vLLM backend — with fable's pre-launch instruction, plus: commit the N1/N2
driver lines with an assertion covering them, launch from that pinned commit with the
targeted suite green on it, and never launch out of the live working tree while the
Amendment-2 coder is running.
