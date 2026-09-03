# Review: commit 5cb696e — classifier-gated deficit wave probe arms (fable, 2026-09-03)

Scope: brief tools/codex-agents/clf-gated-wave.md; coder handoff WORKLOG.md "2026-09-03 — classifier-selected
deficit-gated wave probe arms". Files: scripts/clf_probe_check.py, scripts/ledger_kv_probe.py (run_arm),
src/stencil/qwen3.py (_apply_deficit_gate, _Block.forward, Qwen3.forward), tests/test_clf_probe_check.py.
CPU only; no model loaded; no GPU work; sealed IFEval input not read. Repo edits: this file only (untracked;
results/* is gitignored).

## Re-verification of the handoff claims

- `uv run pytest tests/test_clf_probe_check.py tests/test_multiif_evict.py -q` (CUDA_VISIBLE_DEVICES=""):
  16 passed, 2 skipped (GPU-identity test: "GPU busy with registered 909 run"; test_multiif_evict full-prefill
  test: CUDA unavailable). Matches the handoff.
- `ruff check` on the four touched files: clean. `git diff --check 5cb696e~1 5cb696e`: clean.
- results/qwen/b3-deficit-cal.json: sha256 f0dd561b…cb2b (recomputed, matches handoff); `selected` = t30-b3,
  tau = 0.3, b_max = 3.0. `load_wave_calibration` reads `results[selected]`, no re-tuning.
- Final scores file sha 6d7608b5…41fd not recomputed here (not load-bearing for this review); the probe records
  `scores_sha256` itself at run time.

## Brief items, verified from the code

(1) Bias only on classifier-selected columns, only at deficient decode steps, capped at b_max per span.
- Spans: `arm_configuration` builds `deficit_spans` from `selected`, which is exactly the post-`clamp` aged list
  (same list that defines `keep` for clf_pinned). `run_arm` maps each span through `imap` from the eviction
  (columns that survived), drops empty/zero-cap spans, and builds one boolean mask per span sized
  `cache.k[0].shape[2] + 1` (T_total at that decode step). Only masked columns receive bias
  (`b_amt[..., None] * span_mask`).
- Steps: the hook is installed only inside the decode loop; `prefill_with_eviction` is called without
  `deficit_hook`, so prefill and the first generated token (argmax of prefill logits) are ungated — same as the
  registered v4.5 hook (`make_deficit_hook` returns `{}` during prefill). Per decode step, per (head, row),
  `_apply_deficit_gate` computes psi = softmax(att)[span].sum() on the masked+attn_bias-free scores (att already
  includes the causal mask, so psi is the true natural mass), sets `need = psi < tau`, and biases only where
  `need` is true by `min(b_max, logit(tau) - logit(psi))`. Since need implies logit(tau) > logit(psi) the bias is
  strictly positive where applied, zero elsewhere.
- Layers: `deficit_hook = (20, fn)`; `Qwen3.forward` calls fn at layer 20 and applies `gates.get(i)` for
  i >= 20; `gates` has keys WAVE_LAYERS = range(20, 28). Identical layer set to the calibrated hook.
- Cap: per span `clamp(max=cap)`; caps are honored per span. Spans are disjoint in the final scores (checked:
  72 selected spans across 20 sessions at p >= 0.5, 0 overlaps), so no column can accumulate more than its own
  span's cap. (If overlapping spans ever appeared the sum could exceed b_max; not the case here.)
- The pre-existing legacy call shape `(mask, tau, b_max)` is detected by `isinstance(gate[0], Tensor)` and still
  routes through the same math, so scripts/b4_multiif.py and bench.make_deficit_hook are unchanged in behavior.

(2) Confidence arm: `confidence_cap(p, b_max) = b_max * (p - 0.5) / 0.5`, raises outside [0.5, 1]; linear and
monotone (test asserts 0.0 / 1.5 / 3.0 at p = 0.5 / 0.75 / 1.0). Only clf_pinned_wave_conf uses it; the other two
wave arms use b_max directly. Threshold default 0.5 guarantees p >= 0.5 for every selected span.

(3) Zero deficit reproduces clf_pinned bitwise. Code path: `_apply_deficit_gate` returns the *same* `att`
object when no gate fires (`changed` False), so the post-gate tensor is the untouched fp32 score matrix. The
only remaining path difference would be the SDPA fast path in `_Block.forward`, which is skipped whenever
`deficit_gate is not None` — but the fast path is gated on `self.hf_compatible = n_head*head_dim != d_model`,
and for the registered 1.7B (16 x 128 = 2048 = hidden_size, models/qwen3-1.7b-hf/config.json) that is False, so
clf_pinned and the wave arms both take the manual fp32 path at every layer. Hence at a zero-deficit step the
logits are bitwise identical, on GPU as well as in the CPU toy test (which exercises the same `changed`-False
return). run_arm's other changes (`KVCache(m.cfg)` with cfg = the 1.7B config = the old default;
`device` from parameters = cuda) are behavior-preserving for the registered run.

(4) Echo+wave arm evicts before the current-turn prefill. `arm_configuration("clf_pinned_echo_wave")` returns
probe_arm "pinned_echo", echo_ids, echo_range, keep and eviction_timing = args (pre-query). run_arm calls
`prefill_with_eviction` first, and that function in pre-query mode prefills `tokens[:, :history_end]`, hard-asserts
`cache.length == history_end == columns`, evicts, then prefills the rest — so current-turn (and echo) ids cannot
reach the cache before eviction; the hook is installed only afterwards. The stub-trunk test records exactly this
event order (history / evicted current turn / gated decode), and test_multiif_evict covers the real function.

(5) wave_kill_rule and per-arm safety counts: `safety[arm] = {truncated, timeout, degenerate, invalid}` summed
over sessions; `wave_kill_rule = "degenerate > 2/20 kills the arm"`; `wave_killed[arm] = degenerate > 2` for the
three wave arms; both are in clf-probe.json and the stdout summary. Per-row `timed_out` and `invalid` were added.
`is_degenerate` = truncated OR rep4 > 0.5 (registered), unchanged.

(6) Existing five arms untouched. Same ARM_SPECS entries, same probe_arm strings, same ids/evict_range/keep
routing (now via `arm_configuration`, whose outputs for the five arms equal the old inline expressions).
`deficit_spans=[]` -> `mapped_deficits=[]` -> `deficit_hook=None` -> `m(..., deficit_hook=None)`, which is the
parameter default. POST_PREFILL_TOTALS unchanged. Same code path as check 27 (9c4e721) modulo the two
behavior-preserving run_arm edits above.

## Findings

- F1 (medium, interpretation, not code): the confidence arm cannot discriminate on this data. Every selected
  span in results/quick-checks/clf_scores_final_s0.json has P(keep) in [0.9921, 0.9986], so the per-span caps are
  2.95–2.99 vs 3.0. clf_pinned_wave_conf is a ~1% perturbation of clf_pinned_wave and will almost certainly
  reproduce it (differences, if any, are argmax flips from a <0.05 logit change). Brian's "how much" question is
  not answerable from a saturated classifier; report the arm honestly as a near-duplicate rather than as an
  independent test of confidence scaling. No code fix needed; the formula is as registered.
- F2 (medium, interpretation): the absolute kill flag `degenerate > 2` is confounded with the baseline. In
  check 27 (results/qwen/ledger-kv-probe-prequery/clf-probe.json) clf_pinned ALREADY has 3/20 degenerate
  (sessions 3, 16 truncated; 17 rep4) and full has 2/20. A wave arm that merely inherits clf_pinned's three
  degenerate sessions would be flagged `wave_killed` without the wave having caused anything. Read the rule as
  excess over the same-run clf_pinned (or clf_pinned_echo for the echo arm): killed if
  degenerate(wave) - degenerate(base) > 2, and always report which sessions. Suggested one-line fix (optional):
  also emit `degenerate_excess_over_base` per wave arm. The current output contains everything needed to
  compute it by hand.
- F3 (low): the calibration t30-b3 was selected for a SINGLE governing span per step (make_deficit_hook picks
  the best span); here all selected spans (avg 3.6/session) are gated simultaneously, each against the pre-bias
  natural mass. That is what the brief asked for ("per each saved instruction"), and per-span caps are honored,
  but the total injected mass per step can be several times the calibrated regime (e.g. three spans at
  psi = 0.05 each receive +2.1 and jointly end near 0.6 of the row's mass). Degeneracy risk is therefore higher
  than the single-span calibration suggests — which is exactly what the kill rule is for. No change; flag for
  interpretation.
- F4 (low): the CPU zero-deficit test uses tau = 1e-9 on a 1-layer toy; it proves the no-fire return path, not
  that tau = 0.3 does not fire on real attention. That is fine — "zero deficit" is defined by need being false —
  and the GPU identity test is correctly skipped-with-reason rather than faked.
- F5 (low, hygiene): WORKLOG.md shows as modified in the working tree after the commit (git status " M"); the
  orchestrator should check that is its own ledger write and not coder drift.

No high/critical findings.

## What the probe result would mean (pre-registered reading)

Comparators from check 27 (pre-query, same 20 sessions, 56 aged constraints): full 44, clf_pinned 41,
clf_pinned_echo 46, clf_control 13, evicted 10. Primary contrast: clf_pinned_wave vs clf_pinned (paired by
session; the wave arm differs from clf_pinned only by the gated bias). Secondary: clf_pinned_echo_wave vs
clf_pinned_echo. Report the per-session paired differences, not only totals; 20 sessions is small, so use the
exact sign test on non-tied sessions.

- Wave HELPS: not killed (degenerate excess over clf_pinned <= 2, F2 reading) AND clf_pinned_wave >= 44
  (closes the full gap; +3 over clf_pinned) with paired wins > losses (sign test p < 0.05 if possible;
  otherwise at least 4 more winning than losing sessions), AND no increase in truncation/timeout/invalid over
  clf_pinned. A result >= 46 would additionally put the gate on par with re-injection (clf_pinned_echo), which is
  the interesting claim: attention amplification substituting for echo. For the echo arm, "helps" means
  clf_pinned_echo_wave > 46 with paired wins > losses; anything <= 46 says the wave adds nothing on top of
  re-injection.
- NEUTRAL: not killed, total within [39, 43] (+/-2 of clf_pinned, i.e. inside one or two argmax flips), or a
  larger total driven by one or two sessions with paired wins ~= losses. This is the prior record's outcome
  (sol: 15 repairs / 12 regressions, net ~0) and is the expected result; it also covers clf_pinned_wave_conf
  reproducing clf_pinned_wave (F1).
- HARMFUL: killed (degenerate excess over the base arm > 2), OR total <= 38 (-3 or worse) with paired losses >
  wins, OR any rise in truncation/timeout/invalid attributable to the wave. Because the base arm already has
  3/20 degenerate, a wave arm at exactly 3/20 on the same sessions is NOT evidence of harm; a wave arm at 5/20
  or more, or degenerating sessions that clf_pinned completed, is.
- Degeneracy rule as coded: `wave_killed = degenerate > 2` (absolute). Apply the excess-over-base reading
  above when interpreting; the emitted counts allow it.

## Verdict

VERDICT: SOUND-WITH-FIXES — the plumbing is correct against all six brief items and the battery is honest
(GPU test skipped with reason, not faked). The "fixes" are interpretive and optional: (F2) read/emit degeneracy
as excess over the same-run base arm so the absolute >2 flag is not confounded with clf_pinned's existing
3/20; (F1) state up front that the confidence arm is a near-duplicate because the classifier is saturated
(caps 2.95–2.99 of 3.0). No code change is required before the orchestrator runs the deferred command.
