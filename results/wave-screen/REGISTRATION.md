# Exp 2a registration: wave utilization screen (Qwen3-1.7B, fresh synthetic episodes)

Registered 2026-09-11 before any GPU spend (plan/BACK-ON-TRACK-PLAN.md, section B,
Exp 2a). One bounded opportunity for the existing controller `results/qwen/w0-ce.pt`
(sha256 `eab4831f…7099`, the sealed finalist) to show that its gain is real and depends
on WHERE the field points. Script: `scripts/w_screen.py`.

## Method claim under test

Given the correct external ledger, the frozen 264k-parameter controller improves joint
executable-and-adherent success on fresh short governed-code episodes over (a) correct
prose restatement and (b) fixed attention steering on the known governing spans, and
the gain depends on WHERE the field points (not only WHEN / how much it presses).

## Data lineage

- Episodes: `t2_sessions.generate_t2(seed, 20, "final", interference="s0")`, seeds
  14,700,000 … 14,700,063 (64 episodes). This block was grep-verified unused by any
  training, selection, or prior evaluation (the seal used 13,500,000+, W3 13,600,000+,
  training 13,400,000+ dev seeds; smoke tests use 13,690,000+).
- The controller was trained on dev-split sessions (`scripts/w0_train.py`); nothing in
  this screen is fit or selected on the evaluation episodes.

## Prompts and works

- Every arm receives the identical prompt from `t2_runner.build_arm_prompt` with the
  neutral checker feedback line (as the seal), i.e. the correct live ledger is
  re-serialised at the top of every request. The `prose` arm additionally gets the
  "(Reminder) …" restatement inserted before the request (the sealed `reinsertion`).
- Works per episode: ALL scheduled work turns of the episode (`sess.work_turns`), so
  no per-episode selection is needed. If the Exp 0 pilot budget for 5 arms × 64
  episodes × all works exceeds 75 GPU-minutes, the registration is amended BEFORE
  launch to the first two work turns of each episode (`--works first2`) and that
  amendment is recorded here with the pilot numbers.
- Generation: greedy, at most 120 new tokens, stop at the closing code fence
  (as the seal). Reference tests: `t2_runner.score_work_multi` (three frozen input
  pairs per operation, `OP_TESTS3`), comment checker fixed (Exp 0).

## Arms

| arm | intervention |
|---|---|
| `base` | none |
| `prose` | oracle current-rule restatement in prose (sealed `reinsertion` construction) |
| `fixed_bias` | pre-softmax bias, layers 20-27, last query row, every step: softmax of (+6 inside every live ledger sentence span, −6 elsewhere), peak-normalised, × β = 2. A fixed-bias baseline in the PASTA/SpotLight family; NOT a reproduction of published SpotLight |
| `wave` | `w0-ce.pt` field: per-step controller on layer-20 features, peak-normalised, gain g_t = 2·σ(w·h20) |
| `wave_where_shuffled` | the `wave` field of the arm's own prefix at every step, then the P bias values permuted by a permutation fixed per (episode, work) from `torch.Generator().manual_seed(seed*100 + work_turn)`; preserves the bias-value multiset and the scalar gain at each step; removes WHERE, keeps WHEN and dose (the W0 K-perm ablation at evaluation) |

## Evaluator

One full-prefix forward per generated token; the layer-20 hidden states of the same
pass feed the controller through `Qwen3.forward(bias_hook=(20, fn))`. The sealed
evaluator ran two passes per token (`w_seal.py:57`). Qualification (Exp 0, `--qualify`):
8 dev sessions (seeds 13,690,000-007), single-pass vs two-pass `wave` arm; RESULTS
report max-abs logit drift, identical-code count and adherence agreement. No bitwise
claim is made between the two evaluators.

## Estimands

- Primary: per-episode binary JOINT success = every active opportunity adherent on
  every scored work AND `parse` AND `exec_ok` on the three frozen inputs.
  Contrasts: wave vs prose, wave vs fixed_bias, wave vs wave_where_shuffled.
  Exact McNemar (binomial on discordant episodes), one-sided for the PASS decision
  with Holm over the three, two-sided p and discordant counts always reported.
- Secondary (descriptive): mean per-episode adherence points with paired bootstrap
  95% intervals (10,000 resamples, seed 0); parse rate; paired-broken works as EXCESS
  over `base` (a work `base` parsed/executed that the arm did not), as a fraction of
  works.
- Breakage limit inside PASS: wave's excess paired-broken ≤ 5% of works (the original
  seal's 21/408 = 5.15% would fail this).

## Exhaustive readings

- PASS: all three contrasts positive at Holm-adjusted p ≤ .05 AND wave breakage ≤ 5%
  → Exp 2b (retrain seeds 1 and 2; same episodes and arms).
- NOT-DEMONSTRATED-WHERE: wave vs wave_where_shuffled not positive → "spatial
  contribution not demonstrated"; method claim not advanced; no further wave spend.
- NOT-DEMONSTRATED-BASELINE: wave not above prose or fixed_bias → "advantage over the
  tested baselines not demonstrated"; method claim not advanced; no further wave spend.
- Any other pattern → INSUFFICIENT EVIDENCE, published as descriptive with intervals;
  no further wave spend.
- No causal explanation is inferred from a nonsignificant contrast. A contrast whose
  two-sided adherence interval lies entirely below 0 is reported as demonstrated harm.
- Competence-harm disclosure travels with every mention of w0-ce: MMLU 48.05 → 45.83
  (175 degradations / 57 improvements), GSM8K noninferiority failed
  (WORKLOG.md:1586,1613).

## Budget and stopping

`BUDGET:` line added from the Exp 0 pilot (seconds per episode for five arms at the
longest prompt, × 64, × 1.5). Episodes are written atomically as `ep-<seed>.json` as
they complete; `--start/--limit` chunks ≤ 50 minutes; a run stops starting new episodes
when its reservation has 5 minutes left; budget exhaustion is recorded INCOMPLETE.

## Artifacts

`results/wave-screen/`: `qualification.json`, `ep-<seed>.json` × 64, `summary.json`,
`RESULTS.md`, and a seed-block assertion in `tests/test_w_screen.py` (no 13.6M or dev
seeds in the episode manifest).
