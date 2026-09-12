# Exp 4B results: SETUP-LONG qualification at Qwen3-4B — FAILED (SCREEN never opened)

Registration: `REGISTRATION-4B.md` (+ amendment 1). Run: 2026-09-12 11:16-11:46Z, one 55-minute
slice, 48 generations, cumulative primary-arm generation time 1,187 s of the 3,430 s ceiling,
no timeouts, prompt token counts equal on all 16 items, 16/16 records valid
(`setup_long-4b-role_evicted/summary.json`, `--primary fraction`). Everything on this page is
DESCRIPTIVE (n = 16, SETUP cohort); no confirmatory reading exists for Exp 4B.

## Qualification object (registration item 3, read mechanically from summary.json)

| condition | value | threshold | result |
|---|---|---|---|
| (a) oracle mean `fraction_required` | .263 | ≥ .20 | pass |
| (b) focus-only output-failure discordance | 1/16 = .0625 | ≤ .05 (zero items at n = 16) | **fail** |
| (c) focus − base bootstrap upper bound | +9.5 points | > 0 | pass |

**Status: FAILED.** By the registration, SETUP-LONG is published as the negative and the
SCREEN-LONG run (128 items) is never opened. This was the program's second and last policy
revision (rule D2), so no further revision of the mechanism, estimand or gate is available
without Brian. The per-constraint efficacy signal is positive and is reported below exactly as
measured; it does not rescue the gate, which was frozen before generation and noted by the
implementation review to permit zero focus-only failures at n = 16.

## Per-constraint compliance (`fraction_required`, frozen denominator)

| arm | mean | strict passes | invalid | truncated | degenerate |
|---|---|---|---|---|---|
| base (flag off) | .066 | 0/16 | 5 | 7 | 0 |
| focus (role_evicted, E = 256) | .109 | 0/16 | 3 | 6 | 0 |
| oracle (label-derived live set) | .263 | 0/16 | 4 | 8 | 1 |

Paired contrasts (points of 100; 95% percentile bootstrap, seed 0, 10,000 draws; sign test
on discordant items):

| contrast | mean | interval | wins / losses / ties | sign p |
|---|---|---|---|---|
| focus − base | +4.3 | [+0.1, +9.5] | 4 / 1 / 11 | .375 |
| oracle − focus | +15.4 | [+4.0, +27.3] | 8 / 3 / 5 | .227 |
| oracle − base | +19.7 | [+7.8, +33.1] | 9 / 1 / 6 | .021 |

Strict compliance is 0/16 on every arm (no discordant pairs; McNemar undefined). Output-failure
discordance vs base: focus 1 focus-only item (184-14, unparsable output) against 1 base-only
item (186-14), net rate difference 0; oracle 4 oracle-only against 3 base-only.

## Per item (first query; fr = fraction_required; end = eos/cap; fail: i invalid, t truncated, d degenerate)

| item | required checks | base fr / end / fail | focus fr / end / fail / reminder tok / kept | oracle fr / end / fail / tok |
|---|---|---|---|---|
| 161-9 | 3 | .000 cap it | .000 cap it 246 19/119 | .000 cap it 46 |
| 163-9 | 2 | .000 eos - | .000 eos - 246 16/71 | .000 eos - 46 |
| 184-14 | 3 | .000 eos - | .000 eos **i** 256 18/172 | .000 cap t 97 |
| 185-14 | 5 | .000 cap it | .000 cap t 249 14/163 | .000 cap it 73 |
| 186-14 | 5 | .000 cap it | .333 eos - 249 19/252 | .833 eos - 95 |
| 189-14 | 3 | .000 cap it | .200 cap t 237 16/204 | .000 cap it 110 |
| 212-19 | 4 | .000 eos - | .000 eos - 249 17/262 | .250 cap t 132 |
| 228-19 | 5 | .167 cap t | .333 cap t 255 20/305 | .500 eos - 90 |
| 302-49 | 7 | .214 eos - | .143 eos - 252 16/1001 | .643 eos - 254 |
| 312-49 | 9 | .143 eos - | .143 eos - 250 17/975 | .500 eos - 245 |
| 313-49 | 10 | .000 eos - | .000 eos - 247 17/809 | .421 eos - 250 |
| 314-49 | 7 | .273 eos - | .273 eos - 250 16/866 | .818 cap t 254 |
| 326-49 | 10 | .154 eos - | .154 eos - 250 18/870 | .000 eos - 254 |
| 351-99 | 12 | .000 cap it | .000 cap it 244 17/1784 | .000 cap itd 254 |
| 352-99 | 12 | .031 cap t | .094 cap t 241 17/2075 | .062 eos - 247 |
| 359-99 | 10 | .069 eos - | .069 eos - 249 13/1990 | .172 cap t 252 |

The focus reminder kept 13-20 of 71-2,075 evicted mentor sentences per item (newest-first,
budget 256 tokens); the oracle reminder carried the complete live set on 10 items and was
packed on the six dialogue-49/99 items.

## What this does and does not show

- The Qwen3-4B trunk applies stated conventions where 1.7B did not: oracle .263 here against
  .063 at 1.7B on the same 16 items, and oracle − base +19.7 [+7.8, +33.1].
- The shipping mechanism (verbatim newest-first evicted mentor sentences) moved the
  per-constraint score by +4.3 points [+0.1, +9.5] on 16 items, with 11 ties. Descriptive.
- The gate failed on one unparsable focus output among 16; the same arm produced fewer
  invalid outputs than base overall (3 vs 5). The rule counts focus-only discordance, not net
  excess, and was frozen that way.
- Nothing here is a claim about the artifact; the 4B SCREEN was never run, and the 1.7B
  SCREEN was never run. The artifact `bmarti44/stencil-focus-qwen3-4b` is NOT PROVEN and is
  withheld as a claim.

Data lineage unchanged: nothing in the artifact was fit on MemoryCode; only `oracle` uses
gold labels to construct its intervention; item selection, scoring and the error table read
labels; the focus policy reads none.
