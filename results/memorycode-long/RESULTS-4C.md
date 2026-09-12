# Exp 4C results: final package-path confirmation of `stencil_focus` (Qwen3-4B)

Registration: `REGISTRATION-4C.md` (Astra binding decision, owner-delegated single D2
exception). Summary: `screen_long_4c-4b-package-role_evicted/summary-4c.json`, computed once
at 2026-09-12 17:40Z on the complete run (git `678bf41e` analysis code; scipy 1.18.1).
Records, raw outputs, attempt log and process receipts live in the same directory;
qualification receipts under `qualification-4c/`.

## Terminal reading: NOT PROVEN, FINAL

The registered primary interval includes zero. By the readings table this is the final
outcome of the program: no HF release, no further revision on any outcome. Exp 4B remains
FAILED. The artifact `bmarti44/stencil-focus-qwen3-4b` is withheld as a claim and is NOT
pushed to HuggingFace.

## Qualification (44 generations, all passed)

| check | result |
|---|---|
| package-off vs plain upstream `AutoModelForCausalLM`, 16 SETUP prompts | 16/16 prompt-id and raw-token matches |
| package replay of the 8 timing calls after reload | 8/8 prompt-byte, prompt-id and raw-token matches |
| effective EOS (what the package passes to `generate`) | `[151645]`, frozen in every fingerprint |
| t_max (max of the 8 timing calls; 351-99 focus, capped at 512 tokens) | 68.689 s, measured with a co-resident 1.7B training job |
| N by the timing-only rule floor(28,800 / 3 t_max) | 139 (first 139 of the 196 registered candidates; 128 SCREEN + 11 reserve) |
| qualification resident time | 2,749 s of 3,600 (two processes; the first stopped cleanly at its slice limit after 42 calls) |

## Evaluation, N = 139 paired dialogues, both arms through the shipping package

Primary: `fraction_required` (equal weight per required regex check; missing required
structure or a timeout scores 0), D = on − off, paired t.

| quantity | value |
|---|---|
| mean compliance, off (`stencil_focus=false`) | 0.0845 |
| mean compliance, on (`stencil_focus=true`) | 0.1049 |
| mean D | +2.05 points |
| sample SD of D | 12.59 points |
| paired t (138 df) | 1.915 |
| 95% interval (registered primary) | [−0.07, +4.16] points |
| two-sided p | 0.058 |
| wins / losses / ties | 25 / 17 / 97 |
| percentile bootstrap (10k, seed 0; companion, cannot replace the primary) | [+0.14, +4.30] points |
| exact sign test, two-sided (companion) | p = 0.28 |
| strict compliance (all required checks + structure) | off 0/139, on 1/139; McNemar p = 1.0; paired interval [−3.1, +4.5] points |

The companion bootstrap interval excludes zero while the registered primary does not; the
registration names the paired t as the sole decision statistic and forbids substituting a
companion, so the reading is NOT PROVEN. The honest description is a small positive average
effect of about two points that this sample cannot distinguish from zero.

### Output-failure guard (union of invalid / capped / degenerate / timed out)

| quantity | off | on |
|---|---|---|
| failure rate | 0.432 (60/139) | 0.439 (61/139) |
| invalid (no parsable code) | 48 | 46 |
| truncated at the 512-token cap | 59 | 60 |
| degenerate (4-gram repetition) | 1 | 0 |
| timed out | 0 | 0 |

Discordant: 9 on-only, 8 off-only. Mean H = +0.72 points, 95% interval [−5.17, +6.60],
p = 0.81, McNemar p = 1.0. U_H = +6.60 > 5, so the registered noninferiority gate is NOT met
either; no increase is demonstrated (L_H < 0) and equivalence is not established.

### Descriptive subsets (never a decision input)

| subset | n | off | on |
|---|---|---|---|
| original SCREEN-LONG 128 | 128 | 0.0822 | 0.1048 |
| added reserve dialogues | 11 | 0.1114 | 0.1058 |

### Prompt accounting and mechanism activity

Every pair has equal prompt token counts (3,584 in both arms, package == research
builder), 512-token generation, 300 s deadline, prompt + output ≤ 4,096. The reminder was
non-empty on every focus item, using on average about 247 of its 256 tokens; kept-sentence
source spans, the eviction boundary and a thread digest are recorded per focus arm.

### Completeness, validity and cost

139/139 pairs terminal and valid (per-arm fingerprints equal to the qualification manifest;
raw→scored EOS transformation, termination/timeout/cap agreement, prompt hashes/counts,
item identity and strict agreement all checked; every record re-scored from its stored text
with the frozen checker and re-decoded from its ids). No missing, duplicate, extra or
malformed records. Generation spending 9,101 s of the 28,643 s ceiling (attempt log incl.
interrupted attempts: none); evaluation resident overhead 372 s of 2,700; qualification
2,749 s of 3,600; four 55-minute reservations, each stopped cleanly at its per-process
limit. Total additional GPU allocation about 3.4 h of the 10 h authorized.

## Disclosures

- Instrument bug, disclosed: the first terminal summary read INCOMPLETE because the
  validator looked for the prompt text/hash/count and window inside each generation while
  the runner persists them in the linked raw-output file. The validator was fixed to merge
  those fields from the raw file after cross-checking the attempt id, arm, item and raw ids
  (test added); no output was regenerated. The defective summary is kept as
  `summary-4c-INVALID-validator-bug.json`.
- Owner rule change during the run (ledger 16:50Z): interim results were inspected at 75 and
  100 pairs (+2.2 [−0.1, +4.5] p=.056; +2.0 [+0.2, +3.8] p=.032). The run was never stopped or
  extended on that basis; N = 139 was frozen before the first evaluation generation.
- t_max was measured with a peer training job co-resident on the GPU; a solo measurement
  would likely have given a smaller t_max and a larger N (up to 196). The registration ties
  N to the measured value and forbids post-launch changes, so N = 139 stands.
- Prior history: Exp 4 (1.7B, register policy) NOT PROVEN with a failed fallback; Exp 4B (4B,
  per-constraint primary) FAILED its qualification gate; this run followed an owner-delegated
  override of the stop rule and outcome-informed development, all recorded in the ledger.
- Research-runtime results are not attributed to the package (generation parity failed
  earlier); everything above was generated through the package itself.

## What this means for the artifact

The modification (restating evicted user sentences in a 256-token reminder under a
3,584-token prompt budget) produced a small positive average effect on required-convention
compliance that is not statistically distinguishable from zero at N = 139, with output
failures unchanged. Absolute compliance is low in both arms (about one required check in
ten) and strict compliance is essentially never reached. The package stays in the
repository with this table on its card as a documented negative; it is not published as a
model with a claim.
