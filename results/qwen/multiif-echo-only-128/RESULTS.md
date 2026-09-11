# Exp 1 results: pin increment given echo, 128 distinct Multi-IF source prompts

Registered in `REGISTRATION.md` (2026-09-11) before any GPU spend; run 2026-09-11 in four
reserved chunks on the shared GB10 (Qwen3-1.7B, hand-rolled deterministic runtime); all
128 sources complete (`summary.json`, `manifest.json` with the sha256 of every record).
Label: post-hoc ablation on an exposed cohort (the 909-conversation run of 2026-09-02);
the two new arms were generated fresh, the five existing arms were reused after the
8/8 bitwise-identical replay (`replay.json`). Audited by Astra
(`results/reviews/2026-09-11-exp1-result-audit-astra.md`): every number below was
independently recomputed from the records and reproduced; the interpretation was
REJECTED once and rewritten here (rev 2) per the audit's minimum edits.

## Arms and aged adherence (source means over 128 sources, points)

| arm | mean | what it is |
|---|---:|---|
| `full` | 62.5 | no eviction (reference) |
| `evicted` | 12.6 | pre-query eviction of the history, nothing added |
| `clf_pinned` | 53.2 | eviction + classifier-selected KV pins (original context, no echo) |
| `clf_pinned_echo` | 57.4 | eviction + classifier pins + echo of the selected text |
| `role_pinned` | 59.0 | eviction + role-rule KV pins under the classifier-sized column budget (original context, NO echo; pins cut sentences mid-way in 70/128 conversations) |
| `clf_echo_only` (new) | 54.7 | eviction + classifier-selected echo text, zero pins (the original selected text, no packing rule) |
| `role_echo_only` (new) | 66.7 | eviction + role-rule echo (newest-first prior-user sentences) at a standalone 256-token budget incl. header, zero pins |

Rendered echo lengths (tokens incl. header, audit reconstruction): classifier echo mean
48.3 (0-160), role echo mean 76.2 (31-184); the role echo is longer in 125/128
conversations and identical in 3. The 256-token budget never bound: zero packing stops,
zero empty role echoes (the registered zero-count requirement holds). Every candidate
prior-user sentence fit in every conversation.

## Registered contrasts (paired by source, 95% percentile bootstrap over sources, exact sign test on discordant sources, n = 128)

| contrast | mean | 95% interval | wins / losses / ties | two-sided p | reading (margin 2 points) |
|---|---:|---:|---:|---:|---|
| D1 = clf_pinned_echo − clf_echo_only | +2.67 | [−1.76, +7.29] | 19 / 14 / 95 | 0.487 | INSUFFICIENT EVIDENCE at N = 128: the interval straddles +2; the pin increment GIVEN echo is neither shown to earn its place nor shown dispensable. This is the only contrast that isolates pins given echo. |
| D2 = role_pinned − role_echo_only | −7.62 | [−13.09, −2.08] | 16 / 37 / 75 | 0.0055 | DEMONSTRATED HARM of choosing the role-PINNED policy over the role-ECHO policy: the interval lies entirely below 0. This is a policy comparison (pins without echo, under a borrowed column budget, versus echo without pins at a 256-token budget); it does NOT measure the incremental effect of adding pins to an echo. |
| D3 = role_echo_only − clf_echo_only | +11.98 | [+6.18, +17.71] | 44 / 15 / 69 | 0.0002 | ROLE RULE DEFAULT (registered reading: interval above 0): the registered role-echo policy beat the registered classifier-echo policy. The two echoes differ in content AND length (role echo longer in 125/128); the budget never bound, so this does not test recency selection under a binding budget and the gain is not attributable to selection quality independently of retained content and length. |

Descriptive, not registered: `role_echo_only` had a higher observed source mean than
`full` (66.7 vs 62.5, +4.17 points on this cohort); no interval was registered for that
difference and no noninferiority or superiority claim is made.

## Safety (excess over `full`, counts over 128 sources)

Invalid and timed-out counts are zero for every arm. Degenerate / truncated counts:
full 41 / 35, evicted 12 / 12, clf_pinned 32 / 28, clf_pinned_echo 28 / 27, role_pinned
26 / 23, clf_echo_only 33 / 31, role_echo_only 33 / 31. Every excess over `full` is
≤ 0 (`summary.json`, `safety_excess_over_full`). No integer kill rule was registered.

## Cost and process disclosures

- Recorded conversation-loop time 4,598 s over the four chunks (32.7, 16.7, 18.2,
  9.0 min) plus 175 s for the replay: 79.6 min of generation, excluding model load and
  reservation overhead; within the 177-min registered ceiling.
- The Exp 0 pilot's maximum context was 1,322 tokens; the role arm's longest prompt was
  1,414 tokens, so the pilot did not cover the single longest new-arm input (budget still
  held with margin). The runner chunks by count; the registered "stop starting new items
  5 minutes before the reservation ends" rule was not enforced in code for this run (the
  wrapper records an ETA and waits). Both are disclosed here and fixed for later runs
  (`--budget-minutes` exists in `scripts/memorycode_screen.py`; Exp 4's pilot uses the
  imposed window, the true maximum).
- The reuse gate (8/8 identical replay) is sampled compatibility evidence, not a proof
  covering every reused output; supporting evidence: tokenizer hash unchanged, harness
  function ASTs unchanged relative to the original run.

## What this decides for the artifact (plan rev 7.1, section G)

- No KV pins in the artifact: D1 is inconclusive at the 2-point margin and D2 shows the
  role-pinned policy losing to the role-echo policy. Pins stay a parked Qwen-only backend.
- Text selector for a Multi-IF-style reminder package: the registered D3 reading selects
  the role rule as the default text selector for THIS construction (echo of prior-user
  sentences over an evicted region, budget not binding).
- Exp 4 evaluates a DIFFERENT bundle (classifier admission + lifecycle relations rendered
  over long coding sessions, budget binding). Exp 1 does not test that bundle and does not
  decide which policy wins there. G keeps the classifier register as Exp 4's primary as an
  explicitly UNPROVEN maintenance hypothesis, chosen before any LONG generation for a
  research reason (it is the automatic-maintenance mechanism the program set out to
  test), not as a conclusion from D3. The frozen fallback (role rule over the
  truncated-away region) is the Exp 1-derived alternative and also carries instructions
  from outside the window; no policy is "the only one" that can.
- Multi-IF here is the multi-turn instruction-following check of the reminder machinery;
  it is not a coding-session result and is cited on the card as secondary evidence.

## Boundaries

Exposed cohort (a subset of the 909 conversations already used for the 2026-09-02 run),
one model, one benchmark, greedy decoding, 512-token cap, 2-point margin registered in
advance. The classifier and the role rule were never fit on Multi-IF (data lineage in the
registration). Instruction-ID scoring via `_score_fields` exactly as the original run.
Tests cover statistics, summary and packing; source-selection determinism and schema-2
generation were verified by the audit's independent reconstruction, not by unit tests.
