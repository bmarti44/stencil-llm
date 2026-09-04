# SC1 harness v1 code review — fable (2026-09-04, CPU-only, read-only)

Reviewed at HEAD 08b8a3d (code identical to manifest commit b32e394; `git diff b32e394 HEAD -- src scripts tests` is empty).
Governing text: LEDGER-PLAN.md:912-1291 (SC1 DRAFT v2), data/sc1/AUTHOR-CONTRACT.md (v2). Code: src/stencil/sc1.py,
src/stencil/sc1_episodes.py, scripts/sc1.py, tests/test_sc1.py, data/sc1/smoke/* (manifest, README, smoke-00 source, all
eight expanded episodes), WORKLOG.md:3949-4032. Frozen helpers compared: src/stencil/bfcl.py:196-321 (segmentation),
src/stencil/selector_v2.py:20-145 (sentence splitter, ClassifierScorer), src/stencil/qwen3.py:60-140 (KVCache.evict,
prefill_with_eviction, Qwen3.forward kwargs at :387-436).

Hard rules kept: no model or GPU process launched (only the `tokenizers` tokenizer and file hashing on CPU); foreground
only; nothing signalled; no sealed IFEval/BFCL cohort file read; the only repo write is this file.

## What I ran (CPU)

- `CUDA_VISIBLE_DEVICES='' uv run pytest -q tests/test_sc1.py` -> **22 passed in 20.39 s**.
- `tests/test_eval_data_separation.py tests/test_sealed_guard.py tests/test_no_side_effect_imports.py` -> 9 passed, 1 xfailed
  (the pre-existing legacy inventory xfail).
- `verify_manifest('data/sc1/smoke/manifest.json')` on the current tree -> OK; manifest_id
  8f4668b6ffeb1f49f6074f220a0f9c8acadab57d8d31c323f902c20bf2c43753, 44 files, harness_commit b32e394; file sha256
  651d703a... matches WORKLOG:3967. The five LEG B classifier hashes equal LEDGER-PLAN.md:603 and
  results/quick-checks/ft_final2_s0_sha256.txt (tracked).
- Independent recomputation (scratchpad sc1_recompute_fable.py, Fraction arithmetic):
  McNemar b=13,c=0 -> 1/8192 = 1.220703125e-4; b=8,c=3 -> 29/256 = 0.11328125; b=9,c=2 -> 67/2048 = 0.0327148;
  b=20,c=7 -> 160703/16777216 = 0.0095786; b=0,c=0 -> 1; b=4,c=0 -> 1/16; b=5,c=0 -> 1/32. All equal `sc1.mcnemar`
  to 1e-15. Clopper-Pearson (independent 80-step bisection on the exact binomial survival, tails 0.0125 each = two-sided
  97.5%): k=13,n=256 -> (0.0248241, 0.0906019); k=7 -> (0.0095850, 0.0600122); identical to `sc1.clopper_pearson`.
  Union interval for b=13,c=0: [0.0078525, 0.0906019] (L_b - U_c, U_b - L_c) as registered. Exact power q=.20, D=.05:
  0.5085746 (joint 0.4972492), matching the v2 text, power.json and the manifest.
- Sampler digest by hand: sha256("SC1-v2|20260904|final|0|author|0") = 20d8776715fcf6e6..., first byte 0x20 = 0b0010...,
  top two bits 00 -> kimi-k3; style bit 1 -> tool-work; origin bit 1 -> tool; age bits 01 -> old; scope 00 ->
  continuing; order bit 0 -> clf first. `commission_slot("final", 0)` returns exactly these; setup/0 (fable, 11 -> recent)
  and final/255 also agree. Content streams change with ATTEMPT, factor/order streams do not (sc1_episodes.py:229-230).
- Real-tokenizer probe (sc1_probe_fable.py, Qwen3-4B tokenizer.json only) on all eight smoke episodes: SC1
  `build_sc1_candidates` equals the frozen `select_history_spans` candidate list restricted to [P,R) on every episode
  (text/role/message_index/char_span/span); zero zero-width tokens; LEG A unsafe drop count 0.

## Findings

Severity legend: critical = decides SC1 wrongly or leaks; high = invalidates the registered claim or the executable
freeze; medium = execution/freeze defect that cannot produce a wrong adoption but can waste or block the study;
low = editorial/robustness.

### H1 (HIGH) — the frozen expander does not realize the registered pressure setting; on in-contract episodes the rule
arm pins ALL old user/tool content and clf is a subset, so the comparison is structurally one-sided.

Evidence (real tokenizer, all eight smoke episodes): history 4,608-4,698 tokens, C = 3,584-3,674, B = 256, but the
common candidate list U has 2-7 pieces totalling **18-108 columns**; `rule` admits every piece (skips = 0), the echo holds
every pin (omitted = 0, 39-164 tokens of E = 256), and a constant-1.0 clf stub yields pins and echo **identical** to rule.
The cause is src/stencil/sc1_episodes.py:61-70 (an 8-sentence FILLER pool) and :906-931 (one designated `filler_turn`
grown to the fixed 4,608-token target): 4,378-4,466 of ~4,620 history tokens (95%) are the same eight sentences repeated
~43 times inside ONE assistant message, which is never a candidate (sc1.py:208-210). Consequences:

1. The v2 clause "B=256 always (8.33%-3.57% of removable history) ... a single frozen pressure/echo setting"
   (LEDGER:1053-1055) is nominal: removable *candidate* content is 0.5%-3% of C and below B, so `admit_whole_spans`'s
   budget-skip path (sc1.py:324-325) and `build_sc1_echo`'s omission path (sc1.py:371-372) never execute on compliant
   episodes. The only way the arms can differ is clf's threshold EXCLUDING a span the rule keeps; clf can only lose
   information relative to rule. The registered null result ("no worthwhile learned advantage") is then near-certain by
   construction, and the setup headroom gate measures "full vs no content", not headroom over a recency comparator.
   Production sources (300-800-token specs, contract §"Structured source specification") will have the same shape.
2. `filler_turn` is author-chosen with only "not an evidence turn" enforced (:913). If an author designates a user or tool
   turn, U gains ~340 identical-text filler candidates; when that turn is the newest old user message the rule pins 256
   columns of filler and loses every real span while clf (scoring them below 0.5) keeps the real ones. The arm difference
   is then an author/expander artifact, not selector quality. The contract's "mixing roles ... relevance must not be
   revealed by a special marker, role or position alone" (CONTRACT:72-74) and v2's "audit role/position/wording markers
   and shared filler on smoke sources before executable freeze" (LEDGER:1004-1005) are not met; no such audit is recorded.
3. Both arms see 43 verbatim repeats of eight sentences; a repetition-prone trunk may loop (R flag) in both arms,
   inflating concordant failures.

This is an executable-freeze defect, not a leak; it cannot produce a false clf adoption, but it makes the study unable to
answer its question. v2 permits exactly this remedy: "Smoke work cannot tune the frozen science; if it reveals the need
for a scientific change, reopen Stage 1 prospectively before production exists" (LEDGER:947-948).

Exact fix (Stage 1 amendment + expander change, before any production authoring):
- sc1_episodes.py: replace `filler_turn` with `filler_turns` (>= 3 non-evidence turns, at least one user or tool turn
  whose token span lies in [P,R)); draw from a disclosed pool of >= 256 distinct role-neutral sentences (FILLER_VERSION
  bump); distribute round-robin with a per-turn cap so no message exceeds ~600 tokens; keep the fixed length target.
- sc1_episodes.py `validate_episode`: after layout, build U with `build_sc1_candidates` and reject the source unless
  `sum(span widths of U) >= 2*B` and `rank_rule` admission on U has at least one `budget` skip ("registered pressure not
  realized"); record both numbers in `layout_audit`.
- Register the audit v2 already requires: report per-episode U columns / B, rule skips and echo omissions on smoke.
Test: `test_pressure_binds_on_every_smoke_episode` — with `load_tokenizer("4b")`, for each smoke episode assert
`sum(b-a for a,b in spans(U)) >= 2*layout["B"]`, `select_policy(..., "rule")["admission"]["skips"]` non-empty, and that a
constant-1.0 clf stub does NOT reproduce rule's pins. This test fails on the current bank (skips = 0 on all eight).

### M1 (MEDIUM) — resume refuses a legitimately completable study: the pre-loop cost check projects 512/64 attempts
regardless of how many remain. scripts/sc1.py:441 `meter.can_start(512 if stage == "final" else 64)`. Example: 400 arms
done, spent 5.5 h, per-attempt estimate 30 s: project(512) = 5.5 h + 512*1.25*30 s = 10.8 h > 8 h -> "INCOMPLETE" is
returned and nothing is written, although project(112) = 6.7 h fits and the in-loop check (:495) would pass. v2:
"During final execution replace 512 by the number of remaining arm attempts" (LEDGER:1207). A silent INCOMPLETE on
every retry converts a valid study into a NOT-completed one (no wrong adoption, but the study is lost).
Fix: move the `remaining = sum(len(store.pending(...)) ...)` computation above :441 and pass it; keep 512/64 only when
no arm has completed. Test: fake-backend setup run (as in test_setup_workflow) with `cost.json` pre-seeded so that
`spent + 64*1.25*t > COST_CAP` but `spent + pending*1.25*t <= COST_CAP` after 60 arms are already durable; assert the
run completes and writes the certificate instead of returning INCOMPLETE.

### M2 (MEDIUM) — any exception, including device/resource loss, permanently INVALIDATES the bank.
scripts/sc1.py:519-530 catches `Exception`, writes an exclusive `invalid.json`, and :420-423 refuses every later run.
v2 defines device/resource loss as a journaled infrastructure interruption that is resumable (LEDGER:1173-1179,
RunStore.interrupt reasons sc1.py:781-786), but a CUDA OOM/`RuntimeError("CUDA error ...")`/`OSError` raised inside
`run_arm` takes the INVALID path, and `atomic_json(..., exclusive=True)` makes it irreversible. Conservative (no wrong
decision) but converts one transient fault into a lost 8-GPU-h study and contradicts the registered resume rule.
Fix: classify `torch.cuda.OutOfMemoryError`, `RuntimeError` whose message contains "CUDA"/"NCCL"/"device", and `OSError`
as infrastructure: journal an `attempt_open` event with `repr(exc)`, checkpoint the allocation, re-raise WITHOUT
`invalid.json`; harness bugs (AssertionError/ValueError/KeyError from sc1 code) keep the INVALID path.
Test: backend `generate` raising `RuntimeError("CUDA error: device-side assert triggered")` -> no `invalid.json`, the
attempt's last journal event is `start`, `store.pending` demands interruption evidence, and after
`--interruption-evidence` the arm reruns with `prior_elapsed` > 0 while the first arm's bytes are unchanged.

### M3 (MEDIUM) — the executable freeze cannot produce the artifact it requires. `setup` demands a model-determinism
certificate (scripts/sc1.py:395-399, format enforced at :323-348: 8 rows, two `process_id`s, two episodes, both arms,
`executable_manifest_id`, `allocated_seconds`), but no mode of scripts/sc1.py generates it (`choices` at :659). Producing
it needs new code in a CODE_FILES member, which changes `files[...]` and `manifest_id` -> the Stage 2 freeze must be
redone after the determinism run, contradicting "Freeze executable artifacts ... BEFORE production authoring"
(LEDGER:943-947). Fix: add a `determinism` mode now (two smoke episodes x two arms, fresh process per invocation,
metered by AllocationLedger, writing rows in the exact `verify_determinism` schema) before the freeze. Test: run it
twice with a fake backend in two subprocesses, then `verify_determinism` accepts the merged certificate and rejects it
when one token id is altered.

### L1 (LOW) — truncation flag fires on a voluntarily stopped 255-token output. sc1.py:519 `truncated = len(ids) >= 256
and invalid`; `ids` includes the EOS token, so 255 visible tokens + EOS with a schema failure is recorded T (and I).
F is unaffected (the gate is the union), only the taxonomy is off. Fix: `truncated = len(ids) >= 256 and ids[-1] not in
EOS and invalid`. Test: `output_flags("x", [0]*255 + [151645], False, tok)["T"] is False`.

### L2 (LOW, spec-conformant, disclose) — repetition detects period 1, 2 and 4 token loops only. sc1.py:514-517
implements v2 literally (a 4-token block at 8 consecutive block positions). A loop of period 3, 5, 6... (e.g. one
13-token sentence repeated ten times: probed, R = False) is not flagged. No code change under v2; note it in the
failure-taxonomy disclosure so "R = 0" is not read as "no degenerate loops".

### L3 (LOW) — smoke stories are excluded from production only by the `pool` field. `_check_cohort` (scripts/sc1.py:351-360)
and `independence_audit` (sc1_episodes.py:1180-1241) never compare production fingerprints/literals with the smoke bank.
Fix: in `_check_cohort`, load data/sc1/smoke sources and reject any production `source_fingerprint`, `source_id`,
entity name/identifier collision. Test: a production row copied from smoke-00 with pool="final" is rejected.

### L4 (LOW) — segmentation identity is tested only with a character tokenizer (tests/test_sc1.py:569-589). I verified
identity with the real Qwen3-4B tokenizer on all eight smoke episodes (above); add that assertion to
`test_smoke_all_styles_and_six_mutations_use_real_local_tokenizer` so the freeze carries the proof.

### L5 (LOW) — `InterventionCounter` counts for `scope_resolver` and `digest` (sc1.py:36-41) are not wired to any entry
point; `forward` (:447-455) instruments the five real Qwen3.forward kwargs (inj, residual_hook, attn_bias, bias_hook,
deficit_hook), and no scope-resolver/digest function exists in src/ to instrument. The two counters are therefore
structurally zero, which v2 calls a hard-coded metadata zero; either drop them from the record or document why.

### L6 (LOW) — default `--out` is the smoke bank directory (scripts/sc1.py:663). A `setup`/`final` invocation without
`--out` writes `setup/`, `cost.json`, `invalid.json` into data/sc1/smoke, which the manifest hashes by directory glob.
Fix: no default for `--out` in setup/final/analyze.

## Verified correct (v2 item by item, with the code path)

1. Common unscored U: `build_sc1_candidates` sc1.py:195-256 uses `split_sentence_spans`, `_tool_line_spans`,
   `_chunk_char_span(…,128)`, `_token_span`, CONTROL_MARKERS and the added-token set exactly as bfcl.py:221-300; no
   assistant/prefix/final-request candidates; whole-piece straddle drop (:238-244), duplicates and every reason recorded;
   identical U/hash across arms asserted by test :85-103 and by my real-tokenizer probe. Threshold: key
   `[-s if s>=0.5 else inf, -message_index, char_start, char_end]` (:299-303), 0.5 eligible, nonfinite/out-of-range raises
   (:293-294); rule key `[role!=user, -message_index, -char_start, char_end]` (:264-269), reads no scores;
   `select_policy(…, "rule", scorer=None)` proves scorer independence; constant-0/1 stubs tested.
2. Geometry: `window_geometry` :95-107 R=max(P,H-1024), C=R-P over ALL removable columns, B=min(256,C//4);
   P/H come from one encoding's offsets with a boundary-crossing guard (:172-177), never rfind/re-encode.
3. Admission: `admit_whole_spans` :311-334 scans the whole list, skips infinite keys, admits iff |union| <= B, records
   `budget` skips and continues; never splits/clips; pins = column runs. Not `budget_history_spans`.
4. Echo: `build_sc1_echo` :337-388 selects oldest-first by (span, char_span) independent of rank, keeps an entry only if
   insertion tokens (incl. header, labels, JSON quoting, "\n\n") <= 256 AND the retokenized final-message increase <= 256,
   skips and continues, no header when empty, control-marker assertion; header/entry format exact (:343-349);
   inserted before the final request inside the user message (:167). Per-role pin/echo counts and omission rate recorded.
5. E counts header/labels; B and E are ceilings only; no dose matching.
6. Eviction: `prefill_sc1` :458-508 requires a fresh cache, routes every forward through the intervention counter, uses
   `prefill_with_eviction(eviction_timing="pre-query", keep=pins)`; asserts per-layer widths after history and after
   query prefill, mapping == retained positions, absolute counter == full length; generation asserts widths each step
   (:940-945). `full` arm passes evict_range=None; `evicted` passes empty pins; both final arms use the same [P,R).
   History IDs/H are asserted unchanged by the echo (:1017-1021). 40,960 guard at render (:190-191).
7. Checker: `run_checker` sc1_episodes.py:546-607 is the single path for reference, mutations, constructs and model
   outputs; strict JSON (duplicate keys, NaN/Infinity, 1e999 via canonical, extra text, fences rejected — probed: fenced
   and `<tool_call>`-wrapped references are invalid); text normalization identical for both sides; complete result +
   protected set + unauthorized-change diff (:500-543); tool executor validates fully before mutating a deep copy
   (:388-441); no eval/network/filesystem. Six distinct negatives, obligation linkage, >= 2 type-valid, reject-all and
   no-op detection, generic-safe and recency-only constructs, full coverage, trace replay (:1085-1172). Reference <= 256
   tokens enforced (:1090). Expander determinism enforced twice (:1087, :1257).
8. Sampler: contract string, bit mappings, ATTEMPT=0 for assignment/order streams (:219-258); recomputed above.
9. Gates: `require_setup` recomputes counts from the 32 committed pair files (scripts/sc1.py:263-320), demands
   committed bytes, cost gate and manifest identity; `main` calls it before the tokenizer/backend for final and analyze
   (:678-679); `analyze` re-verifies the seal, every pair hash, arm fields, episode hashes, orders and intervention
   counters before `analyze_pairs` (:614-653). Exact McNemar, p=1 at b+c=0, union CP interval, adoption i-iv, U and K as
   registered, N=256 with no exclusions (sc1.py:528-637).
10. Flags: I/T/R evaluated on every output including truncated; F union; NFKC/casefold/whitespace normalization; tests
    cover consecutive vs scattered.
11. Latency: candidate/scoring/admission/echo/render/prefill/generation/worst_token/check/prior_attempts/total; gate iv on
    mean total (:1037-1046, :610). Cost: reserve 300 s per attempt, projection formula with r^2/r scaling and max-only
    estimates (:640-683), allocation ledger charges the whole interval and never decreases (:1088-1164).
12. Persistence: per-arm exclusive files, write-ahead completion hash, chained journal, interrupt only with an
    infrastructure reason, resume only of a missing attempt, pair written in the same run, seal at 256 (:686-861,
    scripts :531-606). Arm order from the `order` stream per episode; fresh KVCache per arm; shared weights read-only.
13. Lineage: no `data/bench`, IFEval, BFCL or Multi-IF reference in the four SC1 files; classifier bytes are checked
    against the LEG B record at every setup/final/analyze invocation (`verify_manifest` -> `classifier_hashes`);
    nothing fits/tunes on SC1; smoke README and provenance mark the bank disposable/informed.

## VERDICT: SOUND-WITH-FIXES

The scored pipeline (candidates, keys, admission, echo, two-stage eviction, checker, statistics, gates, sealing) implements
v2 faithfully and I could not find a way for it to adopt clf wrongly or to leak private fields or evicted history. The
executable freeze is nevertheless not acceptable as it stands: H1 means the frozen expander produces episodes on which the
registered pressure never binds, so the study would answer "does clf's threshold ever hurt?" rather than the registered
question. Fix H1 (Stage 1 reopen, prospective, before production authoring), M1-M3 (before the Stage 2 freeze, since each
changes CODE_FILES), then re-run `smoke` to re-freeze the manifest.
