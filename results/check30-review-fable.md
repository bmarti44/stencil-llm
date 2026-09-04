# Check 30 review (fable) — function-vector focus

Reviewer: fable (independent). Date: 2026-09-04. CPU only; no model or GPU
process launched; no sealed file opened (the .venv interpreter refuses to start
while the GPU is owned, so `vectors.pt` was not loaded — see 5c).

Inputs read: `results/quick-checks/README.md` item 30;
`results/qwen/function-vector-focus/clf-probe.json`;
`results/qwen/fv-vectors/{grid,report,pairs,preregistered-summary}.json`;
`results/quick-checks/fv_{grid,probe}.log`; `scripts/function_vectors.py`,
`scripts/clf_probe_check.py`, `src/stencil/function_vectors.py`,
`src/stencil/qwen3.py` (hook plumbing), `scripts/ledger_kv_probe.py::run_arm`;
`tests/test_function_vectors.py`; `tools/codex-agents/function-vector-focus.md`
and `.allow`; WORKLOG 3597-3650, 3888-3889; `data/b3/train-manifest.json`;
`data/b3/mt-train-300.jsonl` (turn metadata for the 20 probe keys);
`results/qwen/ledger-kv-probe-h1p/session-*.json` (metadata fields only);
git history (`b0d70b3`, `6578806`, `f3aa99f`, `434beed`).

## 1. Recomputation from the probe rows — CONFIRMED

20 rows, 56 aged constraints (sum of `n_aged`); every arm's `aged_pass` equals
`sum(scores)` and every `scores` list has length `n_aged`.

Totals recomputed: full 44, evicted 10, clf_pinned 41, clf_pinned_echo 46,
clf_control 13, **fv_inject 14, fv_inject_echo 35, fv_clear 13** — identical to
`totals` and to README. The five baseline arms reproduce check 27 exactly
(deterministic re-run), which is itself a useful control.

Safety recomputed per arm = recorded: fv_inject truncated 14 / degenerate 1
(session 15) / invalid 0; fv_inject_echo truncated 15 / degenerate 1 (session 7)
/ invalid 1; fv_clear truncated 2 / degenerate 1 (session 16). Baselines: full
truncated 1, clf_pinned 2. Kill rule (degenerate > 2) not triggered for any FV
arm — `wave_killed` correct.

Paired counts. README reports **session-level** win/loss/tie triples; the JSON
stores **constraint-level** wins/losses (from `_paired`, which compares each
constraint's boolean). Both recompute:

| comparison | session-level (w/l/t) — README | constraint-level (w/l) — JSON |
|---|---|---|
| fv_inject vs evicted | 5 / 1 / 14 (matches) | 5 / 1 (matches; net +4 = 14-10) |
| fv_inject vs clf_pinned | 1 / 17 / 2 (matches) | not stored |
| fv_inject_echo vs clf_pinned_echo | 1 / 7 / 12 (matches) | 1 / 12 (matches; net -11 = 35-46) |

Qualification (cosmetic): the README's "1 / 7 / 12" and the JSON's
`{"wins": 1, "losses": 12}` describe the same data at two granularities; a
reader comparing them will think one is wrong. State the unit in the README.

## 2. Vector provenance and grid selection — CONFIRMED with two notes

Extraction (`scripts/function_vectors.py extract`): source is
`data/b3/train-v43.jsonl`; `report.json.source_sha256`
(`8a5b083c...`) equals the frozen v43 sha in `data/b3/train-manifest.json` and
the file on disk. 352 pairs = 32 x 11 types, from 214 distinct v43 rows (keys
0-700); every pair removes exactly the registered clause (`constraint_sentence`
present in `with_prompt`, absent from `without_prompt`, 352/352). The 11 types
are exactly the aged types of the 20 sessions (WORKLOG counts bullets 4, caps 5,
kw_exist 5, kw_forbid 7, kw_freq 5, lower 2, n_sent 6, n_words_max 5,
placeholders 7, postscript 4, title 6 — recomputed from the rows: identical).
`unknown_vector_constraints` = 0.

Not the probe sessions: the 20 H1' sessions are `mt-train-300` keys 0-19
(3 turns each); no v43 pair prompt equals any turn prompt of those sessions
(exact overlap 0). Not a benchmark: no code path in the three scripts touches
`data/bench/`; v43 is synthetic (`b3_gen43` over `base-texts.json`); the sealed
IFEval/BFCL files were not read by the scripts or by me.

Grid (`function_vectors.py grid`): 4 dev conversations = `train-v43` rows with
keys 0-3, single-turn, greedy, `evict_range=None` (constraint text in view),
vector = sum over the row's full combo at the grid layer; 3 x 3 cells as
registered. Rule implemented as `max(eligible, key=(alpha, -layer))` with
eligible = 0/4 degenerate: largest alpha, then smallest layer — matches the
WORKLOG-registered rule. Recomputed from `grid.json`: at alpha 2.0 only l12 has
0 degenerate (l16 1, l20 1), so **alpha 2.0 / layer 12** is the unique correct
selection. `clf-probe.json` records the grid and vector sha256 and both match
the files on disk; `clf_probe_check.py` refuses to run unless
`grid.status == "selected_before_probe"`.

Note 2a (mild, favours the FV arm, does not threaten a negative result): the
b3 streams share base texts (40 topics x 3 phrasings). 12 of the 16 distinct
base prompts in the 20 probe sessions also appear as base prompts among the
352 extraction pairs, and rows 0-3 (the grid conversations) are themselves pair
sources. The brief only forbade the probe sessions and benchmarks, so this is
within the brief, but "dev corpus" here means topic-shared, not topic-disjoint.

Note 2b (material for interpretation, see 5): the grid measured non-degeneracy
under a condition unlike the probe (single-turn, instruction text in view, no
eviction), and its eligibility rule ignores truncation: `degenerate` is
`rep4 > 0.5 on non-truncated output`, so a2.0-l16 (3/4 truncated, rep4
0.40-0.75) and a1.0-l20 (truncated, rep4 0.996) count as "not degenerate".
The winning cell happened to have 0/4 truncated, so the selection is not
affected, but the grid gave no warning of the 14/20 truncation the probe then
produced. Two of the four grid rows carry `n_words_min`, which has no vector.

## 3. Injection scope and clearing — CONFIRMED

- Placement: `Qwen3.forward` applies `residual_hook` at layer index i before
  `block i` runs, i.e. on the residual entering layer 12; `capture_hidden`
  records the same tensor at the same point, so extraction and injection
  address the same stream. Verified in `src/stencil/qwen3.py` 421-426.
- Positions: `make_residual_hook` writes `alpha * v` into `delta[:, -1, :]`
  only. During the current-turn prefill (`hook(0)`, passed via
  `current_forward_kwargs`, which `prefill_with_eviction` applies only to the
  post-eviction current-turn forward, never to the history forward) that is the
  final prompt token — the position that emits generated token 0, and the
  position the vectors were extracted from; thereafter one hook per generated
  token. History K/V are never modified. Commit `6578806` (Sep 3 14:40, after
  the pre-registration commit but before extraction at 16:02) narrowed the
  hook from all positions to the last; the shipped code is the narrowed one.
- Which constraints: `aged_types = combo[:n_aged]` of the evicting turn, i.e.
  exactly the aged (evicted) constraints; `combine_vectors` sums one vector per
  occurrence of a known type and reports unknowns (0 in this run).
- fv_inject / fv_clear substrate = the evicted arm (same
  `prefill_with_eviction` call as `run_arm`: `history_end=evict_range[1]`,
  `keep=()`, pre-query, greedy, same EOS set, same 512 cap and deadline);
  fv_inject_echo = pinned + echo + vector (`echo_ids`, `echo_range`,
  `keep=keep`) — "fv_inject on top of clf_pinned_echo" as briefed.
- Clearing: when `len(output) == 64` the cache is discarded, the prompt is
  re-prefilled without the hook and the 64 already-generated tokens are replayed
  without the hook, so from token 65 the forward is bitwise the unmodified
  conditional trajectory (`cache_rebuilt_at = 64`). This is stricter than
  merely disabling the hook. Tests cover hook layer/position, alpha=0 and
  zero-vector bitwise identity, the 63/64 boundary, and the rebuild sequence
  on a stub trunk.

Qualification 3a: the battery's "alpha = 0 -> bitwise clf_pinned logits" item
was exercised on a tiny CPU model at the single-forward level, not end-to-end
(`generate_injected(alpha=0)` vs `run_arm` on the trunk). The two code paths
are the same prefill call and the same greedy loop by inspection, so I accept
it, but it is inspection, not measurement.

Qualification 3b: the rows store neither the generated text nor `rep4`; the 14
truncated fv_inject outputs cannot be inspected after the fact, and because the
degenerate definition exempts truncated output, a 512-token loop counts as
"truncated, not degenerate". This cannot change the reading (see 4) but it
means "degenerate 1" understates what the outputs may have looked like.

## 4. Pre-registration and its application — CONFIRMED with one wording note

Timeline: `preregistered-summary.json` mtime 2026-09-03 14:38:34, committed in
`b0d70b3` at 14:39:35 and unchanged since (`git diff b0d70b3 HEAD` empty for
that file); `PREREGISTERED_READING` in `src/stencil/function_vectors.py` is
identical text. Extraction outputs 16:02:48, grid 16:07:48 (Sep 3); probe
`clf-probe.json` 2026-09-04 13:50:13 with `elapsed_seconds` 2958 (started
~13:01). The grid was therefore selected 21 hours before the probe and the
selection rule was fixed in WORKLOG before either GPU step. (The grid file was
only committed alongside the probe in `434beed`; the ordering rests on mtimes,
the WORKLOG hand-off, and the script guard, not on a prior commit.)

Application: harmful iff killed or fv_inject < evicted + 5: 14 < 15 -> harmful
= true. helps false (14 < 30), strong false (35 < 46, wins 1 < losses 12).
All three flags in `reading` are correct.

Wording note: README's "(fv_inject < evicted + 5; truncation breach)" reads as
if truncation were part of the registered harmful rule. It is not — the
registered rule has no truncation clause and would have fired on the margin
alone. The truncation is a (correct) observation, not a registered criterion.
Also, the margin is the thinnest possible: 14 vs a threshold of 15.

## 5. Is the conclusion warranted from one grid point?

5a. The result is, if anything, weaker for the vector than README says. The +4
of fv_inject over evicted is mostly a length artifact. All six n_sent aged
constraints are "at least 9/11 sentences"; fv_inject passes 5/6 (evicted 2/6),
and every one of those five passes sits on an output truncated at 512 tokens
(sessions 3, 5, 9, 11, 19). Of the five constraint-level wins over evicted,
three are n_sent-on-truncated-output; one is `lower` on a truncated output
(session 16); only one (n_words_max, session 12, not truncated) is an
unambiguous steering success. On the seven content/format types that cannot be
satisfied by rambling — kw_freq, kw_exist, caps, title, placeholders, bullets,
postscript — fv_inject scores **0/36** versus clf_pinned 24/36 and evicted
0/36. The vector recovers nothing of the 31-point pin gap; the honest number is
about +1, not +4.

5b. fv_inject_echo (35 vs 46) shows the injection actively damages a working
substrate: the same summed vector on top of re-injected text truncates 15/20
and loses 12 constraints. That is the strongest evidence in the check, because
it is not confounded by the missing instruction text.

5c. What one grid point does not establish. The claim "weight-side steering
under-delivers and truncates on this trunk" is supported at (alpha 2.0, layer
12, summed multi-type vectors). It is not established that a lower dose or a
single-type vector would also fail: (i) the grid chose the *largest* alpha
that was non-degenerate on single-turn prompts with the instruction still in
view — the mildest condition — and its eligibility rule ignored truncation;
(ii) the probe adds 2-4 type vectors, and layer-12 norms are 10-27 each, so
alpha 2 x sum is several times any single vector (I could not load
`vectors.pt` to compute the per-session summed norms because the project
interpreter refuses to start while the GPU is owned; the README's own norms
table supports the order of magnitude); (iii) 14/20 truncation is the classic
signature of an over-dosed steering vector, and the grid could not have seen it
because it never ran under the probe's evicted multi-turn condition.

5d. A fair follow-up, if one is wanted, would be: alpha in {0.25, 0.5, 1.0}
at layers 8 and 12; inject the single vector of each aged constraint's type
rather than the sum (or normalise the sum); select the grid on dev *sessions*
(`mt-dev-60`) under pre-query eviction with truncation counted against a cell;
save text and rep4 per arm; keep the same pre-registered thresholds. Cost:
the 11-arm probe took 49 min, so fv_inject alone is about 15 min per cell; a
3-alpha x 1-layer sweep of fv_inject alone is about 45 min of GPU plus a
20-minute dev grid — roughly one GPU hour.

5e. Worth it? For the program decision, no: even a generous reading of a
retuned vector would need >= 30/56 to matter beside re-injection at 41-46, and
the type-level pattern here (0/36 on every type that requires content) makes
that implausible. Re-injection stands regardless. The one thing a bounded
hour would buy is the right to say "weight-side steering fails on this trunk"
rather than "alpha 2 / layer 12 fails on this trunk". I would record the
narrower sentence in the README now and treat the hour as optional, to be
spent only if Brian wants the weights hypothesis retired on its own terms.
Recommended README wording: "one grid point (alpha 2.0 / layer 12, summed
vectors); the +4 over evicted is length-driven (n_sent passes on truncated
output); no recovery on any content type; retuning would need alpha <= 1 and
per-type vectors and is not required for the program decision".

## 6. Leakage

- Probe -> vectors: none (zero prompt overlap with the 20 sessions; grid rows
  are v43 rows 0-3, not sessions). Base-text sharing (note 2a) is topic-level
  and inherent to b3; it favours the FV arm and so cannot rescue a negative.
- Benchmarks: none. `train-v43`, `mt-train-300`, `ledger-kv-probe-h1p` are the
  only data paths; the scorer applies vendored IFEval-style checkers to
  synthetic prompts, which is how every prior check scored.
- Tuning on the probe: none. alpha/layer fixed on Sep 3 by rule; thresholds
  fixed 21 h before the probe; the probe was run once (single
  `clf-probe.json`, single log, `PROBE_EXIT=0`).
- Post-hoc drift: the only code change after pre-registration and before the
  GPU steps (`6578806`) narrowed the hook to the generated position, which is
  the briefed design, not a re-tune.

## Findings by severity

- medium: the harmful verdict is by a 1-point margin and the +4 is a length
  artifact; the README should say so and narrow "weight-side steering ...
  closes" to the tested operating point (5a, 5c, 5e).
- low: README "truncation breach" reads as a registered criterion; it is not (4).
- low: paired counts are session-level in README and constraint-level in the
  JSON without saying so (1).
- low: grid eligibility ignored truncation and ran under a condition unlike
  the probe (2b); generated text and rep4 not stored in the rows (3b);
  alpha=0 identity to clf_pinned verified by inspection only (3a).

## VERDICT: CONFIRMED-WITH-QUALIFICATIONS

The numbers, provenance, injection scope, clearing, pre-registration timing and
the mechanical application of the registered reading all verify. The
qualifications are about the strength of the closing sentence: the evidence
supports "the registered function-vector arm is harmful at alpha 2 / layer 12
and its small gain is truncation-driven" and supports keeping re-injection; it
supports "weight-side steering is closed on this trunk" only as a program
decision, not as a measured generalisation across doses and layers. A bounded
~1 GPU-hour retune (alpha <= 1, per-type vectors, dev grid under eviction) is
the fair follow-up if that generalisation is wanted; it is not needed for the
decision already taken.
