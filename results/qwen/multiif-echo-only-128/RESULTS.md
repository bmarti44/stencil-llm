# Exp 1 results: pin increment given echo, 128 distinct Multi-IF source prompts

Registered in `REGISTRATION.md` (2026-09-11) before any GPU spend; run 2026-09-11 in four
reserved chunks on the shared GB10 (Qwen3-1.7B, hand-rolled deterministic runtime); all
128 sources complete (`summary.json`, `manifest.json` with the sha256 of every record).
Label: post-hoc ablation on an exposed cohort (the 909-conversation run of 2026-09-02);
the two new arms were generated fresh, the five existing arms were reused after the
8/8 bitwise-identical replay (`replay.json`).

## Arms and pooled aged-adherence (points, mean over 128 sources)

| arm | mean | what it is |
|---|---:|---|
| `full` | 62.5 | no eviction (reference) |
| `evicted` | 12.6 | pre-query eviction of the history, nothing added |
| `clf_pinned` | 53.2 | eviction + classifier-selected KV pins |
| `clf_pinned_echo` | 57.4 | eviction + classifier pins + echo of the selected text |
| `role_pinned` | 59.0 | eviction + role-rule pins (newest-first prior-user sentences) |
| `clf_echo_only` (new) | 54.7 | eviction + classifier-selected echo, zero pins |
| `role_echo_only` (new) | 66.7 | eviction + role-rule echo at a standalone 256-token budget incl. header, zero pins |

## Registered contrasts (paired by source, 95% percentile bootstrap over sources, exact sign test on discordant sources, n = 128)

| contrast | mean | 95% interval | wins / losses (discordant) | two-sided p | reading (margin 2 points) |
|---|---:|---:|---:|---:|---|
| D1 = clf_pinned_echo − clf_echo_only | +2.67 | [−1.76, +7.29] | 19 / 14 (33) | 0.487 | INSUFFICIENT EVIDENCE at N = 128: the interval straddles +2; pins are neither shown to earn their place nor shown dispensable. The package ships text-only on cost grounds and says so. |
| D2 = role_pinned − role_echo_only | −7.62 | [−13.09, −2.08] | 16 / 37 (53) | 0.0055 | DEMONSTRATED HARM of pins given the role-rule echo: the interval lies entirely below 0. Adding KV pins to the role echo loses 7.6 points. |
| D3 = role_echo_only − clf_echo_only | +11.98 | [+6.18, +17.71] | 44 / 15 (59) | 0.0002 | ROLE RULE DEFAULT: the zero-parameter newest-first prior-user-sentence rule beats the trained classifier's selection by 12 points at the same echo budget. |

Descriptive, not registered: `role_echo_only` (66.7) exceeds `full` (62.5) by 4.2 points;
the interval for that difference was not registered and no claim is made beyond "the
role echo recovers at least the full-context level on this cohort".

## Safety (excess over `full`, counts over 128 sources)

No arm shows excess invalid, degenerate, truncated or timed-out outputs over `full`
(all excess counts ≤ 0; `summary.json`, `safety_excess_over_full`). No integer kill rule
was registered or applied.

## What this decides for the artifact (plan rev 7.1, section G)

- The artifact ships text-only (no KV pins): D1 is inconclusive and D2 is demonstrated
  harm, so pins cannot be a default component; they stay a parked Qwen-only backend.
- Selector evidence: at a fixed echo budget over an EVICTED region, recency (the role rule)
  beat the classifier's selection by 12 points on multi-turn instruction following. G's
  frozen primary policy for Exp 4 remains the classifier REGISTER (it is the only policy
  that can carry instructions from sessions outside the window; the role rule over the
  whole session would restate the newest sentences, which the window already shows). The
  frozen fallback is now stated precisely as the role rule over the TRUNCATED-AWAY region
  (newest-first mentor sentences outside the window), the analogue of this experiment's
  winning arm. This clarification was made before any Exp 4 item was generated.
- Multi-IF here is the multi-turn instruction-following check of the reminder machinery;
  it is not a coding-session result and is cited on the card as secondary evidence.

## Boundaries

Exposed cohort (a subset of the 909 conversations already used for the 2026-09-02 run),
one model, one benchmark, greedy decoding, 512-token cap, 2-point margin registered in
advance. The classifier and the role rule were never fit on Multi-IF (data lineage in the
registration). Instruction-ID scoring via `_score_fields` exactly as the original run.
