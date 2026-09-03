# Harness review — kimi-k3 (2026-09-03)

```markdown
# Harness review — Multi-IF real-eviction harness + preflight (2026-09-03)
Reviewer: kimi-k3 (cross-model). Method: static review of the pasted sources only +
arithmetic recomputation by hand. CPU-only; no process launched, signalled or
terminated; no repo edits; the sealed IFEval input was never read (nothing in the
pasted harness references it — `scripts/multiif_evict.py` module docstring and data
path `data/bench/multiif_en.jsonl` only).
Evidence note: the paste carried no line numbers, so citations are
function/snippet-level (file + function + quoted code), plus recomputed numbers.
Where verification needed something NOT in the paste, it is listed under
"Could not check" rather than asserted.

=====================================================================
## Item 1 — Eviction is REAL: VERIFIED, with one unverifiable core component
=====================================================================

### 1a. Protected prefix / evictable range — correct by construction (analysis)
`context_layout()`:
- `system_end` is the char offset after the system block's `<|im_end|>` (+1 for the
  trailing `\n`); `protected_end = max(4, _prefix_token_count(..., system_end))`.
- `eviction_end = _prefix_token_count(..., current_marker)` where
  `current_marker = context.rfind("<|im_start|>user\n", 0, turns[-1][0])` — so the
  evict range is exactly "everything before the current user turn" and the current
  turn + opener can never be evicted. `protected_end > eviction_end` raises.
- Both boundaries are computed by re-encoding string PREFIXES. This equals the
  column index in the full encoding because every cut point sits immediately after
  `<|im_end|>\n` and is followed by a special token (`<|im_start|>`) — Qwen BPE
  cannot merge across a special token, so the prefix encoding is an exact prefix of
  the whole-string encoding. Boundary-safe. ✔

### 1b. No system prompt is ever built — registration clause is vacuous (LOW)
`_generate_history` starts `history = ""` and both history and the final context
are `<|im_start|>user\n…<|im_end|>\n<|im_start|>assistant\n…` segments only; no
`<|im_start|>system\n` block is ever prepended. So in every record the protected
prefix degenerates to `max(4, 0) = 4` columns = the first turn's
`[<|im_start|>, user, \n, first-content-token]`. Record conv-000 confirms:
`"protected_prefix": [0, 4]`, `"evict_range": [4, 881]`. This matches the
registration's letter ("system prompt + first 4 columns in every arm") with an
empty system prompt, and is uniform across all six arms — but the model card
should not imply a protected system prompt on this leg. (LOW)

### 1c. KVCache.evict called with keep = pinned spans — VERIFIED at call site
`run_arm`: `index_map = cache.evict(*evict_range, keep=keep)`; `keep` is exactly
the clamped pinned spans (`arm_inputs`): evicted `[]`, clf_pinned `pinned`,
clf_pinned_echo `pinned` (on echo ids), clf_control `control`, role_pinned
`role_pins`, full `None`. `pinned_columns` is recovered through `index_map` and
recorded; `cache_cols_before/after` instrumented. ✔ at the call site.
INTERNALS of `KVCache.evict` (src/stencil/qwen3.py) are NOT in the paste —
see "Could not check" #1 (position policy). The meta claims
`"position_policy": "no_reindex_positions_continue"`; nothing in the pasted code
implements or verifies that claim.

### 1d. Identical context ids across arms — VERIFIED
Five arms share `layout["context_token_ids"]`; `clf_pinned_echo` deliberately uses
`echo_ids` (echo = ledger context inserted per the registration "before the final
user `<|im_end|>`"), and an assertion enforces
`echo_layout["evict_range"] == layout["evict_range"]` — if ledger.py ever inserted
the echo inside the prior-history region the run crashes loudly. Record: the
visible head of `echo_context_token_ids` is byte-identical to
`context_token_ids` ✔ consistent with insertion after the evict-range end.
Each arm re-prefills a fresh `KVCache` (`run_arm` creates it per call). ✔

### 1e. Control exact-column, post-clamp; role recency-clipped — VERIFIED NUMERICALLY
On the pasted record: selected span `[35,80]` (score 0.998 ≥ 0.5; other two
candidates 0.009, 0.011 < 0.5 ✔ threshold behavior demonstrated) ⇒
`classifier_spans=[[35,80]]`, 45 columns; `pinned_cols` = 45 for
clf/clf_echo/control/role, 0 for full/evicted ✔.
- Control: replaying `matched_control_spans` on pinned=35..79, range [4,881):
  targets 35–49 take the nearest free columns below (20–34), targets 50–79 take
  80–109 ⇒ exactly `[[20,35],[80,110]]` = the record's `control_spans`.
  Exact-column (|chosen| = |pinned| by construction; RuntimeError if the range
  can't match), built AFTER the clamp in `clamp_and_match_control`
  (clamped pinned → matched control). ✔✔
- Role: prior-user columns = turn1 [4,80) + turn2 [430,447); recency tail of
  budget 45 = last 17 (turn 2) + last 28 of turn 1 ⇒ `[[52,80],[430,447]]` =
  the record's `role_spans`. Clipped to the classifier's column count by
  recency (`sorted(set(columns))[-budget:]`). ✔✔
- Runtime cross-checks assert clf/control/role pinned-column counts are equal
  per conversation (three `AssertionError`s in `evaluate_conversation`) and the
  record carries them (`pinned_cols`, `cache_cols_before`, `evicted_cols`). ✔

### 1f. First token from PRE-eviction logits (LOW)
`run_arm`: `logits = model(ids, cache)` → `cache.evict(...)` →
`next_token = argmax(logits[0,-1])`. So every eviction arm's FIRST decoded token
is chosen from the full, pre-eviction context; tokens 2+ attend over the evicted
cache. This is inherent to the registered prefill-then-evict design, identical
across arms, and worth one line in the write-up (the "evicted" arm is "saw it in
prefill, KV deleted", not "never saw it"). (LOW)

### 1g. Record id-prefix anomaly — almost certainly a paste/slimming artifact (LOW, verify on disk)
The slim record's `context_token_ids` begin `[151644, 872, 198, 7985("You"), …]`
= `<|im_start|>system\n…` (~82 tokens through `151645,198`), yet
`protected_prefix=[0,4]`, `evict_range=[4,881]`, and every span implies
token 3 = `29187("Write")`, i.e. ids `[151644, 77091(user), 198, …]`. These are
jointly IMPOSSIBLE from the pasted code: had the string begun with a system block,
`context_layout` would yield `protected_end=max(4, 82)=82`; had the tokenizer
prepended one, span `[3,35]` could not land on "Write…". Most likely the slimmed
paste spliced ids from elsewhere (several other fields are visibly mid-value
truncated). VERIFY on disk: conv-000's first ids, and
`meta.harness_sha256 == sha256(scripts/multiif_evict.py@8018113)` — if the on-disk
record genuinely combines a system header with protected=[0,4], the preflight ran
different code than registered ⇒ CRITICAL. No other evidence points that way. (LOW,
one-command check.)

### Findings graded for item 1
- [MEDIUM-priority verification; HIGH if wrong, LOW prior] KVCache.evict internals
  and the post-eviction RoPE/position continuation ("no_reindex_positions_continue")
  are unverifiable from the paste. Failure signature if wrong: decode positions
  restart at the COMPACTED cache length and collide with/invert against the
  retained current-turn phases — degrading evicted/clf/control/role arms uniformly
  (contrasts among them stay fair; C3's comparison to full is still interpretable).
  Prior working use of the same eviction machinery in the dev probe
  (registered pin+echo 46/45/44) argues against breakage, but qwen3.py must be
  read before the 909 outcomes are INTERPRETED. Does not waste the run.
- [LOW] 1b (no system prompt), 1f (first token pre-eviction), 1g (record anomaly).
- [LOW] Past assistant turns in history are stored WITHOUT the empty-think opener
  that the live turn uses ("non-thinking template"); uniform and identical across
  arms, so fairness is intact; template asymmetry worth noting.
- [LOW] Generated text is reinserted into history verbatim. `invalid_output()`
  flags chat-control tokens for the safety metric but the RAW text still enters
  history; a sampled `<|im_start|>` (EOS membership of 151644 lives in
  `stencil.bench`, not pasted) would later crash `user_turns` ("unterminated user
  turn") or, if a fake `…user\n…<|im_end|>` parses, silently re-slice turns for
  that conversation. Empirically dormant: 0 invalid / 0 chat-token events in
  ~160 preflight generations. Consider asserting control-token-free history text.

=====================================================================
## Item 2 — Selector path: VERIFIED (hashes 3/3 match; two unverifiable diffs)
=====================================================================
- Prior USER turns only: `user_turns(context)[:-1]` in `select_prior_user_sentences`. ✔
- Registered splitter: `split_sentences` is declared "the exact registered splitter
  from clf_score_sessions.py" — that file is not in the paste; diff UNVERIFIED
  (review limitation, not a defect). The splitter itself (quote tracking,
  single-capital abbreviation guard, trailing quote/paren absorption, ≥2-letter
  filter) is sane and deterministic.
- WITHOUT context: `scorer(texts, role="user", contexts=[""]*len)`; `selector_v2`
  maps empty → the literal string "(no context)" — i.e. "no context" IS the
  training convention per the module docstring ("using empty context exactly as
  registered"); training-side code not pasted, so the convention match is asserted,
  not diff-verified. `truncation="only_first"` protects the sentence; with empty
  context nothing of the candidate is truncated. ✔
- role "user" ✔ (harness call + `meta.selector_role="user"`; unknown roles raise).
- threshold: `row["score"] >= 0.5` where score = P(rule)+P(fact) returned by the
  scorer; `meta.threshold=0.5`; inclusive `>=` matches "keep iff P ≥ 0.5". ✔
- FINAL seed-0 artifact, meta vs LEDGER-PLAN registration (commit 48d670e list):
  head.pt 191b3372…be3e ✔ identical; encoder/model.safetensors 22328135…d830 ✔
  identical; encoder/tokenizer.json 56827b4e…6f00 ✔ identical. The remaining tree
  (config.json d4b2c4e7…, tokenizer_config.json c9c2e0ff…, metrics.json ba2fd941…)
  could not be checked against `results/quick-checks/ft_final2_s0_sha256.txt`
  (not pasted) — review limitation.
- Nothing else selects: the only selection paths in the harness are (i) the
  threshold rule above, (ii) the registered role rule, (iii) the deterministic
  position-matched control. No argmax-over-runs, no seed shopping, no per-benchmark
  threshold. Scorer is eval()+no_grad on CPU, artifact hash-pinned per run
  (`classifier_files_sha256` in meta). Seeds 1–2 are probe-only per registration
  and appear nowhere in this harness. ✔
- Demonstrated on the record: candidates 0.009 / 0.998 / 0.011 ⇒ exactly the
  middle sentence pinned. ✔

=====================================================================
## Item 3 — Scoring: VERIFIED vs the registration (two components uncheckable)
=====================================================================
- Checkers: vendored `ifeval.utils.process_results` on `{"prompt",
  "instruction_id_list", "kwargs"}` of the LAST turn, response = generated text
  only (opener excluded; `skip_special_tokens=False` so control tokens survive for
  the invalid check). Primary gating uses strict instruction-level — matches
  "vendored Multi-IF/IFEval process_results; truncations scored as-is". ✔
  Equivalence with `scripts/ledger_eval.py` (checker versions, the
  `sha256(key:turn)` per-turn `random.seed`, `langdetect.DetectorFactory.seed=0`)
  COULD NOT BE CHECKED — ledger_eval.py was not provided. The seeding is at least
  FAIR: identical per (key, turn) across all six arms of a conversation, sequential
  execution, deterministic. (review limitation)
- Per-turn semantics: only the final turn is scored; `aged = all[:len(turn_{T-1}
  ids)]` — "introduced in turns 1–2, checked at turn 3" given Multi-IF's
  cumulative per-turn id lists. The cumulative structure is strongly supported by
  the preflight totals: `all_n − aged_n = 73 − 53 = 20` = exactly ONE new
  instruction per conversation at turn 3. ✔ (data file itself not inspected.)
- Contrasts: cluster units = per-conversation aged pass PERCENTAGES
  (`100*sum/len`, vacuous cluster raises); contrasts are PAIRED per-conversation
  differences, one-sided t with the −5/n continuity mean penalty, Holm α=0.05
  over the three registered contrasts, descriptive echo−full excluded. All match
  the registration. Recomputed means from the summary's cluster means:
  C1 = (0.6375−0.466667)×100 = 17.0833 ✔; C2 = 1.25 ✔;
  C3 = (0.6375−0.3375)×100 − 0.5×(0.575−0.3375)×100 = 30 − 11.875 = 18.125 ✔;
  descriptive = 6.25 ✔. Holm recomputed: order (c3 0.0505, c1 0.0922, c2 0.7569);
  cutoffs 0.05/3=0.0167, 0.05/2=0.025, 0.05; sequential stop ⇒ all fail ✔.
- Safety integer clause implemented EXACTLY as registered: timeouts==0;
  truncated ≤ full+1; degenerate ≤ full; invalid ≤ full; per arm vs full;
  `intact` = all arms pass; `registered_contrasts_pass` = intact AND all Holm —
  and it is correctly false at preflight on both grounds. ✔
- [LOW] stats sanity: from C1's p (0.0922, df 19, mean−0.25) the implied
  per-conversation SD ≈ 55.6; from C1's lower bound (−3.0827, t95) the implied
  SD ≈ 39–52 depending on which mean the bound uses. One SE cannot reconcile both;
  presumably a method detail inside stats.py's `t_continuity` bound (not pasted).
  The GATE runs on `p_one_sided` via Holm, and the p's are plausible and
  conservative (continuity penalty present: `t_lower_bound_descriptive −
  lower_bound = 5.0` exactly). Verify in stats.py before quoting bounds.
- [MEDIUM — registered-design risk, NOT an implementation error] The integer
  safety clause at n=909 is noise-dominated. Under EQUAL per-arm truncation/
  degenerate rates, each non-full arm has ≈50% chance of exceeding
  `full+1`/`full` on binomial fluctuation alone; needing all five non-full arms
  to pass gives safety_intact of order 0.5⁵ ≈ 3% even when the mechanism is
  perfectly safe. Preflight (truncated 0–3/20, degenerate 1–3/20, full 0/0/0/0)
  suggests exactly this regime. The clause is registered and AMENDMENT 1 doubles
  down on it, so the harness is CORRECT to compute it this way — but expect
  `registered_contrasts_pass=false` at 909 almost regardless of the mechanism,
  and the outcome write-up must attribute that to the registered gate rather
  than to the arms "becoming unsafe". Decision-makers: read the contrast rows,
  not just the gate flag.
- [LOW] `summarize_records` raises on any conversation whose aged slice is empty;
  at that point all 909×(2+6) generations are done (records safe/resumable; the
  fix is trivial). Multi-IF cumulative lists make it unlikely (all 20 preflight
  conversations had ≥1 aged constraint).

=====================================================================
## Item 4 — Leakage: CLEAN; AMENDMENT 1 changed exactly one configuration input
=====================================================================
- Multi-IF is read ONLY for prompts and scoring docs; nothing is fit, tuned, or
  selected on it; no `results/` file is read by the harness; the classifier is
  inference-only (eval, no_grad, hash-pinned); threshold 0.5 fixed since check 13;
  seeds deterministic; scorer never sees gradients. ✔
- Provenance/resume guards match the registration ("records are resumable and are
  never deleted"): atomic tmp+replace per conversation from the FIRST completion;
  `resume_indices` re-validates schema + ci/key identity; `_check_or_write_meta`
  hard-fails on any meta drift within an outdir (code/data/model/tokenizer/
  classifier/stats hashes all pinned per run). Cross-run (preflight vs 909)
  comparison of metas is manual — both are committed artifacts. ✔
- What AMENDMENT 1 changed — exact list:
  (1) the preflight GPU-hour GATE 12 → 24 (22.1 projected after viewing the
      preflight; rationale: idle GPU, wall-time not money);
  (2) an explicit decision to NOT cut the cohort (a seeded subset would be a
      post-hoc choice);
  (3) reaffirmation that the ROUND-7 integer safety clause applies UNCHANGED to
      the 909 counts;
  (4) reaffirmation of resumable, never-deleted records and of starting with the
      registered arms/contrasts/threshold/artifacts.
  Nothing else: cohort 909, arms, contrasts, Holm, threshold, seed-0 artifacts,
  data file, and outcome rules all byte-identical to the registration.
- One nuance the team should own in the write-up (LOW, procedural): the amendment
  quotes the preflight ARM TABLE — the go/no-go budget decision was therefore made
  WITH n=20 outcome knowledge. No configuration parameter depends on those
  outcomes (cap is orthogonal to every score), the outcome rules forbid iterating
  the classifier on Multi-IF results, and the 909 analysis is fully fixed — so
  the fixed-analysis validity of the 909 contrasts is unaffected; but "we raised
  the cap after seeing the preflight numbers" should be stated verbatim later.
- [LOW/cosmetic] The code's `full_run_allowed_by_preflight` still compares against
  a hard-coded `12.0`; the amended 24 exists only in the amendment text. The 909
  summary.json will therefore carry a stale-looking `false` flag. Harmless;
  annotate, don't "fix" mid-run.

=====================================================================
## Item 5 — Preflight arithmetic: recomputed (marginals-only; see limitation)
=====================================================================
From the 20-record summary (per-record recomputation was IMPOSSIBLE: only 1 of 20
records was provided, and it is truncated — the 19 others, their per-conversation
cluster values, and their seconds breakdowns are not in the paste):

- Aged totals/rates (n=53): full 30 → 0.5660377358490566 ✔; evicted 18 →
  0.33962264150943394 ✔; clf_pinned 31 → 0.5849056603773585 ✔;
  clf_pinned_echo 33 → 0.6226415094339622 ✔; clf_control 22 → 0.41509433962264153 ✔;
  role_pinned 29 → 0.5471698113207547 ✔. All match AMENDMENT 1's arm table
  (30/18/31/33/22/29 of 53) ✔ and its "C1 +17.1 (LB −3.1, p 0.09), C2 +1.2
  (p 0.76), C3 +18.1 (p 0.05)" ✔.
- All-constraint totals (n=73): 46/32/48/49/37/48 → 0.63014/0.43836/0.65753/
  0.67123/0.50685/0.65753 ✔ all exact.
- Contrast means from cluster means: C1 17.0833, C2 1.25, C3 18.125, descriptive
  6.25 — recomputed exactly (item 3). `73−53=20` ⇒ exactly one new instruction
  per conversation at turn 3 (structural check).
- Seconds: 1747.5269425765146 / 20 = 87.37634712882573 ✔ = seconds_per_conversation.
  Projection: 87.37634712882573 × 909 / 3600 = 22.062527650028497 ≈
  22.062527650028496 (float) ✔ = "87.4 s/conversation, 22.1 GPU-h" in AMENDMENT 1 ✔.
  `> 12.0` ⇒ `full_run_allowed_by_preflight=false` ✔; `≤ 24` ⇒ the amended gate is
  satisfied ✔.
- Safety table internal consistency: degenerate ⊇ truncated per arm
  (2≥2, 3≥3, 2≥1, 2≥2, 2≥2) ✔; quoting only in the echo arm (1) and the detector
  returns False for non-echo arms by construction ✔; the per-arm checks
  (`truncated ≤ 0+1` fails at 2–3; `degenerate ≤ 0` fails at 1–3) match every
  boolean in the summary ✔; `intact=false` and `registered_contrasts_pass=false`
  follow ✔.
- Holm block recomputed: cutoffs 0.0167 / 0.025 / 0.05; all `passed=false` ✔.
- NOT independently recomputable from marginals (needs the 20 cluster vectors +
  stats.py): the p-values and the t_continuity lower bounds (see item 3 finding),
  `conversation_mean_aged_rate` per arm, and the history/selector/arms seconds
  decomposition.

=====================================================================
## Could not check (materials not in the paste; no shell)
=====================================================================
1. src/stencil/qwen3.py — KVCache.evict semantics and the post-eviction
   RoPE/position policy behind "no_reindex_positions_continue" (HIGH if wrong;
   read before interpreting 909 outcomes). Also `stencil.bench.EOS` membership.
2. scripts/ledger_eval.py — the required checker/aged-definition comparison;
   equivalence with the REGISTRATION text was verified instead.
3. src/stencil/ledger.py — Entry/render_text_ledger/text_ledger_context (echo
   format/placement; a crash-guard assertion does bound its coordinate impact,
   and the record's echo-token head matching the context head is consistent).
4. src/stencil/stats.py — t_cdf/clustered_lower_bound internals (item 3 tension).
5. src/stencil/determinism.py — what assert_gpu_free_or_owned does/doesn't pin
   (bitwise cross-arm reproducibility of identical-id arms is assumed, not shown;
   greedy argmax ties make practical risk negligible).
6. scripts/clf_score_sessions.py — the "exact registered splitter" diff.
7. 19 of 20 preflight records; the untruncated conv-000 (id-prefix anomaly, 1g);
   results/quick-checks/ft_final2_s0_sha256.txt (full artifact hash list);
   tests/test_multiif_evict.py (coverage); data/bench/multiif_en.jsonl itself
   (909-row count is enforced at runtime; sha256 unverifiable from here).
8. Any runtime/GPU behavior (hard rules: nothing launched).

=====================================================================
## Consolidated graded findings
=====================================================================
- [MEDIUM — verify before interpretation] KVCache.evict / position continuation
  unverifiable (would be HIGH if wrong; does not waste the run either way).
- [MEDIUM — registered design] n=909 safety integer clause is noise-dominated
  (≈0.5⁵ pass probability under equal rates); implementation is exact; attribute
  the near-certain gate failure to the gate, not the arms.
- [LOW] record id-prefix vs protected=[0,4]/spans inconsistency — impossible from
  the pasted code ⇒ presumed paste-splice; one on-disk check settles it (escalate
  to CRITICAL only if the file itself shows the combination).
- [LOW] no system prompt exists in any arm context ⇒ protected prefix = 4 columns
  incl. turn-1's first content token (registered clause vacuous).
- [LOW] first decoded token in every eviction arm comes from pre-eviction logits.
- [LOW] history turns lack the live-turn empty-think opener (uniform asymmetry).
- [LOW] raw generated text re-enters history; special-token echo could crash or
  silently re-slice `user_turns` (dormant at preflight: 0 events).
- [LOW] C1 p vs lower bound not jointly reproducible with one SE from marginals —
  stats.py method detail; gate uses the p's, which are plausible/conservative.
- [LOW] `full_run_allowed_by_preflight` hard-codes 12.0; will print `false` in the
  909 summary under the amended 24 GPU-h gate.
- [LOW] summary hard-raises on a hypothetical empty-aged conversation after all
  compute (records safe; Multi-IF structure makes it unlikely).
- Review limitations (not defects): items in "Could not check".

VERIFIED with exact arithmetic (highlights): control spans `[[20,35],[80,110]]`
reproduced column-for-column from the matching algorithm; role spans
`[[52,80],[430,447]]` from the recency rule; selection behavior on all three
candidates; all six aged and all-constraint totals/rates; all four contrast
means; Holm ordering/cutoffs/outcomes; safety booleans; seconds/conversation
87.37634712882573; projection 22.0625276500285 GPU-h; all three registered
artifact hashes in meta.

VERDICT: SOUND-WITH-FIXES
The run should NOT be stopped — no defect found that would waste the 909
compute; the "fixes" are pre-interpretation verifications (read qwen3.py's
evict/position path and stats.py; spot-check on-disk conv-000 + harness hash)
plus registration-compliant documentation notes. Eviction is real, the selector
path matches the registration hash-for-hash, scoring and contrasts match the
registered definitions, leakage is clean, and AMENDMENT 1 changed only the
12→24 GPU-h gate while explicitly refusing a post-hoc cohort cut.
```