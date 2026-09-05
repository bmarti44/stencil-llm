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
