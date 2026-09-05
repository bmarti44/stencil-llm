# Quick check 36 — recomputing downstream columns after cue overwrite

UNREGISTERED, disclosed quick check, authorized 2026-09-05; seed 36036;
frozen Qwen3-4B, bf16 hf_compatible, greedy, maximum 64 new tokens per answer.
Lineage: fit-on=none; evaluated-on=the 32 recorded check35 S1 synthetic episodes
(seed 35035 lists and actual SET/HOLD answers), deliberately reused for this paired
diagnostic. Donors use operand-free cue text. Nothing is fit, trained or selected;
no sealed IFEval input or sealed BFCL cohort contents are accessed.

## Fixed reading (written before GPU execution)

If R2 >=26/32 and R3 >=26/32 SWITCH B exact: the transplant is faithful and the
failure was stale downstream columns; switching via state requires recomputation,
and "state address" = "text + recompute" in this setup.
If R3 >=26/32 but R2 <=8/32: transplanted columns are unfaithful out of context.
If both R2 and R3 <=8/32: precedence/in-context pattern dominates even with
recomputation (but check35 S4/TEXT contradict a general inability to change tasks).
Other outcomes are inconclusive under these fixed thresholds. R4 and R5 are
reported descriptively. BACK A exact is reported for every arm.

## Fixed implementation choices (written before GPU execution)

Reuse scripts/focus_check35.py for cache writes, donors, appends, eviction,
generation and scoring. Reconstruct S1 SET/HOLD from recorded prompt, output,
EOS and trailing token IDs, including the original 128-token HOLD filler and
consecutive user turns. Assert both recorded history hashes in every episode.
Teacher-force prior answers with their original token-by-token forward boundaries;
no regenerated SET/HOLD answers. All five arms fork the same pre-SWITCH cache.

- R1: overwrite old columns 64–75 with B; retain downstream K/V (S1 replication,
  reference SWITCH 3/32 and BACK 32/32).
- R2: same overwrite; discard and re-prefill every retained column from 76 onward
  from the identical token history, then freshly prefill/decode the SWITCH request.
- R3: substitute actual B cue tokens at 64–71 (same four-token suffix at 72–75)
  and prefill the complete context from scratch; all remaining history IDs match R2.
  Causality predicts equivalence to R2 in exact arithmetic; bf16 batch/chunk effects
  need not be bitwise identical. Record per-layer K/V differences and output identity.
- R4: overwrite, evict all prior generated answer/EOS columns, then re-prefill all
  surviving downstream tokens. Keep their original absolute RoPE positions, replay
  contiguous surviving spans separately and skip answer-position gaps. Prompt and
  assistant-header tokens and manually added newlines remain, as in check35 c2.
- R5: append B's 12 columns at the recent position using the offset-matched
  operand-free donor, leaving A and old history intact. No existing columns follow
  the appended packet; prefill the normal list/request freshly (S2 replication,
  reference SWITCH 0/32 and BACK 32/32).

BACK applies the same arm operation with A after that arm's actual SWITCH output,
using the recorded S1 BACK list. R4 releases answers again at BACK. R3 substitutes
A and rebuilds its own history. R5 appends another packet. SWITCH histories are
paired; BACK histories can diverge because actual SWITCH outputs are retained.
Virtual cue-slot history IDs remain OFF placeholders in transplant arms; recompute
starts at 76, never interpreting those placeholders as the transplanted cue.
Score value-exact with check35's format-lenient parser; report strict exact,
A/B/copy/other and breakage alongside headline counts. No outcome tuning or reruns.

Sources: results/check34-review-fable.md (plain answer c, cheapest next test;
the supplied "item 10" label is not a numbered heading there) and
results/quick-checks/check35/README.md. GPU initially 0% with no compute apps;
no review lock. Foreground only, no process signals or termination. Cooperative
15-minute cap including model load, checked before forwards; exit if foreign GPU
compute appears. Preserve partial records. WORKLOG is the operational ledger;
legacy protocol and STATE are archived. Reading copied verbatim and hashed at launch.

## Results

Completed **32 episodes / 320 scored answers in 7.57 of 15 GPU-minutes**, including
model loading, source replay and donors. Fixed verdict: **PRECEDENCE_PATTERN**.
Peak allocated CUDA memory: 8,818,157,056 bytes. No GPU compute processes remained
after the foreground run exited.

| Arm | SWITCH B exact /32 | BACK A exact /32 | SWITCH strict | BACK strict |
|---|---:|---:|---:|---:|
| R1 overwrite only | 3 | 32 | 3 | 32 |
| R2 overwrite + recompute | 2 | 32 | 2 | 32 |
| R3 whole-context text rebuild | 2 | 32 | 2 | 32 |
| R4 release + recompute | 17 | 14 | 17 | 5 |
| R5 recent append | 0 | 32 | 0 | 32 |

All denominators below are 32; breakage is the inherited parse/repetition/cap
diagnostic, distinct from strict JSON validity.

| Arm | Step | A | B | Copy | Other | Breakage |
|---|---|---:|---:|---:|---:|---:|
| R1 | SWITCH | 28 | 3 | 1 | 0 | 0 |
| R1 | BACK | 32 | 0 | 0 | 0 | 0 |
| R2 | SWITCH | 29 | 2 | 1 | 0 | 0 |
| R2 | BACK | 32 | 0 | 0 | 0 | 0 |
| R3 | SWITCH | 29 | 2 | 1 | 0 | 0 |
| R3 | BACK | 32 | 0 | 0 | 0 | 0 |
| R4 | SWITCH | 14 | 17 | 0 | 1 | 0 |
| R4 | BACK | 14 | 0 | 11 | 7 | 0 |
| R5 | SWITCH | 32 | 0 | 0 | 0 | 0 |
| R5 | BACK | 32 | 0 | 0 | 0 | 0 |

## Plain-language conclusion

**Recomputing downstream columns does not make this old-position SWITCH work.**
R2 and R3 both score 2/32, and both continue ascending on 29/32 SWITCH lists.
They meet the fixed <=8/32 reading: the retained in-context pattern/old-position
precedence dominates even after rebuilding. Stale downstream K/V alone cannot
explain the failure, and this check does not select the unfaithful-transplant
reading because the plain-text rebuild fails equally. This conclusion is scoped
to these 32 histories and this cue placement.

R2 and R3 produce identical generated-token sequences in all 32 SWITCH and all
32 BACK answers. Their caches are **not bitwise identical**: across all recorded
layer comparisons, maximum absolute K/V differences are 18.37109375 / 38.0625.
The arms use different bf16 prefill shapes and chunk boundaries; the measured
result is behavioral agreement here, not byte equality or general transfer fidelity.

Releasing answers as well as recomputing helps SWITCH descriptively (17/32),
but BACK falls to 14/32 value-exact, only 5/32 strict JSON exact; 11 BACK outputs
copy the input and 7 are other. It does not supply reliable reversible switching.
Recent-position append remains 0/32. R1/S1 and R5/S2 reproduce all original
SWITCH and BACK generated-token sequences (32/32 for each arm and step).

Check35 TEXT was a B sentence in the **current user request**, scoring 27/32;
R3 changes the **old system-position cue**. Thus TEXT is not contradicted: its
different cue placement can overcome histories where the old-position cue fails.
Check35 S4 retained A in 27/32 after answer eviction without recomputation; its
non-answer cached history was still stale, unlike R4 here. No broad inability to
follow B, and no claim that stale columns contribute nothing, follows from this test.

## Reproduction and validation

Run: `.venv/bin/python scripts/focus_check36.py --run` (refuses output overwrite).
CPU checks: `.venv/bin/python scripts/focus_check36.py --self-test`.
Audit: `.venv/bin/python results/quick-checks/check36/validate.py`.

All 320 outputs were rescored and their post-intervention histories, absolute
positions, answer masks, operation references and hashes reconstructed on CPU.
All 64 original SET/HOLD hashes, 576 operation records, 192 donors, 32 cache
comparisons, script/source hashes and the preserved prewritten reading were
checked. CPU sparse-recompute tests exercise the actual consumer across internal
and trailing eviction gaps. Ruff and the five-script AST import-safety guard pass.

Artifacts: [summary](4b/summary.json), [records](4b/records.jsonl),
[source histories](4b/histories.jsonl), [operations](4b/operations.jsonl),
[donors](4b/donors.jsonl), [cache comparisons](4b/equivalence.jsonl),
[validation](4b/validation.json), [frozen reading](4b/prewritten-reading.md),
[raw run log](4b/run.log). No fitting/training, sealed inputs, signals, background
launches or push.
