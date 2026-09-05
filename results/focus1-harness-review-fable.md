# FOCUS-1 DRAFT v2 text + harness v1 review — fable, 2026-09-05

Scope: LEDGER-PLAN.md "## FOCUS-1 ... (DRAFT v2)" (lines 1710-1781) and the CPU handoff (1782-1800);
results/focus1-review-{fable,kimi}.md and the v2 "Review disposition"; src/stencil/focus1.py (3,121 lines, all
read), scripts/focus1.py, tests/test_focus1.py (all read); reused code src/stencil/qwen3.py (KVCache,
prefill_with_eviction, Qwen3.forward hook/capture sites), src/stencil/function_vectors.py (mean_difference,
make_residual_hook, repeated_4gram_fraction), src/stencil/sc1_episodes.py (parse_json/json_equal). Commit at
review: 9882411 (harness files unchanged since e3cd09e; SHA-256 of the reviewed v2 section recomputed =
746b354436a2007984f394fa995c68c6a455312c80bc4493dca9f9bc5f0e67fb, 23,197 bytes, 71 lines, matching
`REVIEWED_HASH`). CPU only; torch touched only inside pytest modules; no model, GPU, background process or signal;
no sealed IFEval/BFCL read; no repo file written except this one.

Test command (brief, verbatim): `CUDA_VISIBLE_DEVICES='' uv run pytest -q tests/test_focus1.py
tests/test_eval_data_separation.py tests/test_sealed_guard.py` -> **72 passed, 1 warning in 120.51 s** (the
warning is a pre-existing SyntaxWarning in scripts/b2_gsm8k.py, unrelated). Two scratchpad pytest probes
(pure-Python closed forms; `generate_banks` determinism; `score_reply`/`endpoints` behaviour; a bf16 dose-loss and
`cache_hash` cost measurement) were run from the scratchpad; numbers in Section 4.

## VERDICT

- **(A) Text v2: SOUND-WITH-FIXES.** Every fable finding is dispositioned as stated and the incorporated text is
  faithful to it; the claim ceiling is honest; no clause lets a run PASS without the swapped arm producing both
  directions on fresh operands (>=24/32 per stratum, McNemar over V and R). One HIGH remains: kimi H1's
  reformulation moved the F7/F8 copy-conjunction defect from the test endpoint into the selection floor
  (">=31/32 episodes per task in which CLEAR and replay BOTH copy BOTH lists"), where it can produce
  FAIL-ACTUATOR for every cell from trunk copy noise or in-context text effects that are identical across cells
  (A1). One text claim is false under its own floors (A3). No critical.
- **(B) Harness: SOUND-WITH-FIXES.** The code implements v2 clause-for-clause (Section 2 checklist); no leak of
  test outcomes into selection; sealed/eval guards intact; the hash-chained records, frozen manifests and
  analyze-only-from-records paths are real. One HIGH (B1): the timing smoke injects a unit-norm basis vector at
  alpha 2 and then runs the same non-vacuity `require` as a real cell; under bf16 a +2.0 perturbation is lost
  outright at |x| >= 512 and the stage goes INVALID, and because the harness refuses any second attempt of a stage
  and pins the experiment root, that single artefact kills the whole root. Plus the code side of A1 and two
  mediums (hashing cost, duplicated OFF competence decodes). No critical.

Findings are graded low/medium/high; fixes carry the exact code edit and test.

---

## 1. Part A — text

### Disposition audit (fable F1-F14, kimi)

| finding | v2 disposition | verified in text | note |
|---|---|---|---|
| F1 sustained-signal ceiling | accepted | yes (claim-ceiling paragraph, "independent forward passes given the enum") | ok |
| F2 descriptive transient-hold arm | accepted | yes; implemented (`Engine.transient`) | ok |
| F3 content-free lineage | accepted | yes | ok |
| F4 frozen layout | accepted | yes, plus exact token segmentation in handoff | ok |
| F5 shuffled retained, narrow reading | accepted | yes ("near-vacuous ... does not establish specificity by itself") | ok |
| F6 KEEP floors removed, CLEAR-UNCHALLENGED | accepted | yes | ok |
| F7/F8 harm endpoint, lower-tail binomial, zero impositions | accepted | yes for the TEST family | **re-introduced at selection, see A1** |
| F9 OFF schema gate; intervention-only stop | accepted-with-change | yes | ok |
| F10 default-coincident label | accepted | yes | ok |
| F11 redundancy disclosed; McNemar boundary | accepted-with-change | boundary numbers correct in isolation | **"paired tests can still bind" is false under the floors, see A3** |
| F12 conjunctive power statement | accepted-with-change | yes (0.945636 / 0.122662 recomputed, match) | ok |
| F13 asc/desc first | accepted | yes | ok |
| F14 transplant cut from test; setup certification; short-circuit | accepted | yes (512 setup decisions; test has four main arms) | ok |
| kimi H1 (29/32 selection, 32/32 copy gate, power caveat) | accepted-with-change | yes | 32/32 copy gate's rationale (C>=63) is gone, see A2 |
| kimi M1/M2/M3/L1-L4/S1/A1-A3/C1-C4 | as listed | consistent with the text | M3 hash binding implemented (`reviewed_section`, `registration_evidence`) |

### A1 (HIGH) — the selection joint-copy floor is the F7/F8 defect relocated; it can FAIL-ACTUATOR every cell for a reason unrelated to the actuator, and identically across cells

Text (line 1728): "Select FIRST eligible cell on setup: ... >=31/32 episodes per task in which CLEAR and replay BOTH
copy BOTH lists exactly; residual-harm count <=1/32 per task". Code: `selection()` fails the cell when
`joint_copy + 32 - neutral_n < 31` (src/stencil/focus1.py:2122-2127); tests/test_focus1.py
`test_selection_joint_pair_floor_abandons_before_keep` pins this ("shared errors still fail joint setup floor").

Why it is wrong:
1. Joint copy is a conjunction of four exact copies (two CLEAR, two replay) on a context that now contains a
   sorted answer. A shared CLEAR/replay failure is by v2's own definition *not* residual harm; it is a text-history
   or copy-competence effect. The v2 test family correctly scores only H; the selection floor still scores C AND P.
2. The replay is OFF from empty KV over a token history that, whenever the steered sort was correct, is the same
   bytes in every cell (prompt + the expected sorted JSON + EOS). Greedy decoding is deterministic, so a replay
   copy failure on an episode recurs in every one of the nine cells; if >=2/32 episodes in either task fail this
   way, the outcome is FAIL-ACTUATOR with certainty and no cell can rescue it.
3. Recomputed reachability with a *perfect* release (no harm) under per-copy retained-context accuracy q,
   CLEAR/replay perfectly correlated (two effective copies) / independent (four):
   q=0.995: P(pass per task) 0.960 / 0.868, both tasks 0.921 / 0.753;
   q=0.99: 0.867 / 0.639, both 0.752 / 0.408;
   q=0.98: 0.637 / 0.278, both 0.405 / 0.077;
   q=0.97: 0.429 / 0.104, both 0.184 / 0.011.
   The competence gate (64 copies at 32/32) only certifies q >= 0.05^(1/64) = 0.954 at 95%, and it does so on a
   context *without* a preceding sort answer, so q in the retained context can be lower. A trunk that copies at
   98% in that context fails the selection floor with probability ~0.6-0.9 for a perfect actuator.

Fix (text, replace the quoted clause): "residual-harm count <=1/32 per task (CLEAR fails a query whose clean
replay succeeds) and zero CLEAR old-task impositions; joint CLEAR/replay copy counts are reported per task
descriptively; a replay copy rate <29/32 in either task labels the cell RETAINED-COPY-WEAK in the manifest
(descriptive, not eligibility)." Keep the breakage floors as they are.
Fix (code, src/stencil/focus1.py:2122-2127): drop `r["joint_copy"] + 32 - r["neutral_n"] < 31` from the failure
condition (keep `r["harm"] > 1 or r["clear_impositions"]`), add `r["replay_copy"]` counter (both replay copies
exact) and the label. Test: invert `test_selection_joint_pair_floor_abandons_before_keep` — with two shared copy
failures and harm 0 the cell must be ELIGIBLE and KEEP must run; add a sibling where the fake policy fails only the
retained CLEAR fork on two episodes (`residual` flag) and assert REJECTED with reason containing "harm".

### A2 (medium) — the 32/32 copy competence gate no longer has a reason and is a 64-copy conjunction

Kimi H1 raised 31/32 -> 32/32 so that the C>=63 endpoint would be reachable; that endpoint was removed (F8).
P(INELIGIBLE | per-copy q) = 1 - q^64: q=0.995 -> 0.274, q=0.99 -> 0.474, q=0.98 -> 0.726. Because copy competence
no longer sits in any endpoint or (after A1) in selection, a 47% chance of closing the program INELIGIBLE at q=0.99
buys nothing. Fix: revert to ">=31/32 complete two-query neutral-copy pairs" (P(pass | q=0.99) = 0.867) and keep
the OFF schema gate. Code: `competence()` `sum(copies) == 32` -> `>= 31`; test
`test_competence_32_pair_floor_and_schema_separate` adjusts its expectation (31 exact pairs -> READY, 30 ->
INELIGIBLE). If Brian prefers the harsher gate, keep it but say in the text that it is a trunk gate with the
above miss probability, so an INELIGIBLE is not read as "no copy skill".

### A3 (medium) — "Floors grade magnitude; paired tests can still bind" is false under the registered floors

Recomputed by exhaustive enumeration of feasible tables (both + b >= 48, b - c >= 16, both + b + c <= 64): the
maximum one-sided McNemar p is 0.01465247336026465 at (b,c) = (32,16) < 1/60. The stated boundary "(33,17) passes,
(34,18) fails" is arithmetically right (0.016420 / 0.018242) but (33,17) needs both >= 15 and 15+33+17 = 65 > 64:
infeasible. So all three McNemar tests (S-O, W-V, W-R) are redundant with their count/net floors; the harness
handoff already notes this. Fix (text, line 1752, replace the sentence): "Under the >=48 count and >=16 net floors
every feasible paired table already has p <= 0.01465 < 1/60 (maximum at b=32, c=16); the exact McNemar p-values are
reported and implemented but cannot bind." This is a science-line edit and changes the reviewed hash (see B7).

### A4 (low) — SWITCH power at the selection floor is disclosed, but the selection rule maximises the chance of hitting it

First-eligible in lexicographic (alpha, L) picks the weakest passing dose; at exactly the 29/32 floor
P(sum(W) >= 48) = 0.1227 (recomputed, matches). Acceptable as registered, but a FAIL there is uninformative.
Optional label, no gate: when the swapped per-decision reliability across the four phases is >= 0.90 but
sum(W) < 48, report "UNDERPOWERED-AT-DOSE" beside FAIL. The `reliability()` groups already carry the numbers.

### A5 (low) — "run the cue-absent OFF prompt on sort0 separately for each task" is one prompt run twice

The OFF cue-absent prompt has no task; "per task" is the same bytes under greedy decoding, so the two 32-decode
passes are duplicates and the per-task schema/absent-exact numbers are necessarily identical. Either cut one pass
(-32 decodes) or, better, keep both and turn them into the missing real-determinism witness (B4).

### A6 (low) — budget feasibility is a genuine single-shot risk; say what follows an INCOMPLETE timing stage

Worst-case scheduled decodes recomputed: competence 128+64, extraction 192 prefills, selection 9 x 448 + 512
certification, test 1,472 -> 6,400. The projection multiplies every one by 1.25 x the retained *64-token* worst-case
rate plus check/persistence overhead. If that rate is >= ~2.7 s (plausible for a custom batch-1 bf16 forward plus
the hashing in B3), the smoke refuses to launch, the stage is INCOMPLETE, and the no-retry rule ends the program
at its first GPU step. That is the registered fail-closed behaviour and I do not propose loosening it; the text
should state that this outcome requires a new registration with a re-measured cap (it presently says only
"INCOMPLETE").

### Claim ceiling / PASS-without-answering

Honest. PASS needs sum(W) >= 48 with >= 24/32 per initial task, i.e. the swapped arm must produce descending on
initial-A episodes and ascending on initial-B episodes, each with a fresh operand set per decision, McNemar over V
and R; OFF's default direction is absorbed by the default-coincident label, HOLD/BACK are stated to be
re-applications, CLEAR-UNCHALLENGED is visible. I found no reading under which a content-bearing signal, a
default, or a single-direction effect reaches PASS.

## 2. Part B — harness

### Clause-by-clause implementation check (v2 -> code)

| v2 clause | code | status |
|---|---|---|
| competence: >=29/32 visible per task, 32/32 copy pairs, OFF schema >=31/32 | `competence()` 1898-1966 | matches (see A2/A5) |
| extraction on separate operand-balanced examples, fp32 mean difference at final prompt token, layers {12,16,20} | `extract_vectors()`, `normalize_pair()`; capture at layer INPUT via `capture_hidden=set` in `Qwen3.forward` (qwen3.py:421-427) | matches; per-pair fp32 difference before averaging; final-token identity enforced in `bank_layouts` |
| rho common norm, cosine>0.9 label, invalid-layer handling | `normalize_pair`, `selection`, `validate_selection` | matches |
| grid alpha {0.5,1,2} x L {12,16,20} lexicographic, first eligible, short-circuit sort->breakage->CLEAR/replay->KEEP breakage | `CELLS`, `selection()` | matches (A1 aside) |
| injection at final prompt position and every decode position, never earlier/delay tokens | `decode()`: hook-free `forward(suffix[:-1])`, hooked last token and each generated token; verified by `validate_run_records` (`absolute_position` schedule) | matches |
| four main arms on independently cloned canonical KV, equal prompt IDs/positions/KV/unhooked logits | `Backend.canonical()` (clone, data_ptr disjointness, per-layer zero delta, logits `torch.equal`) | matches |
| shuffled: per-episode gauss draws on randomA/randomB, rescaled to rho, indexed by correct schedule | `random_directions`, `main_decisions` | matches; re-derived and hash-checked in `validate_run_records` |
| arm order seeded once | `seed(...,"armorder")` shuffle | matches |
| enum-only carry, hooks off during 128 neutral tokens | HOLD/BACK layout = USER + 128 delay IDs + "\n\n"+prompt+TAIL; delay processed in `teacher_force` without hook | matches |
| descriptive transient-hold from SET's steered cache incl. last token, hook OFF | `Engine.transient` (`require(not hook_events)`) | matches |
| retained-KV CLEAR/KEEP forks of BACK incl. last token; two neutral queries; clean replay per query from empty KV over exact prior history | `Engine.neutral` | matches; replay for query 2 rebuilt from CLEAR's actual history |
| all-layer K/V max-abs deltas, first-decision logit delta, token equality; nonzero at layers >= L both K and V | `compare_caches(layer=L)`, pair audit records, `validate_run_records` | matches (conservative reading) |
| never `generate_injected(clear_after=...)` | not imported | matches |
| setup-only certification: transplant==swapped, sham==correct bitwise on 32x4 | `main_decisions(certification=True)`, 512 decisions, `validate_selection` re-check | matches |
| frozen manifest before test; run refuses changed artifacts; test.json opened only in run | `selection()` `frozen_artifacts`, `preflight`, `check_bank(test=stage=="run")`; test guard `test_all_modes_real_cli_fake_backend_and_integrity` | matches |
| S/O/W/V/R/C/P/H/K definitions, strata, nets, exact McNemar, lower-tail binomial, alpha_f=1/60, labels | `episode_rows`, `endpoints`, `mcnemar`, `binomial_lower` | matches; exhaustive McNemar test present; recomputed p(0..2) match to 1e-16 |
| breakage I/T/R once per episode per arm; stop on second broken episode in intervention arms only; controls scored zero | `score_reply`, `impossible()`, `endpoints` | matches |
| stop when an endpoint floor is already impossible | `impossible()` (count/stratum/net/harm/imposition), `StopRun` -> FAIL with observed denominators, no p-values when missing | matches |
| cost cap 21,600 s, 1.25x projection at retained maxima, reload reservations, deadline min(300, 4x), overrun marker | `Budget`, `execute_stage`, allocation log | matches |
| no resume/retry/overwrite | `preflight` refuses duplicate stage attempts; `Store.write` exclusive; hash chain | matches (this is also what makes B1 fatal) |
| raw per-decision JSONL before aggregates, required fields | `RECORD_FIELDS`, `answer()` writes attempt + record before scoring gates | matches |

Leaks: none. `selection()` sees only setup rows and the extraction manifest; test bytes are opened only in `run`
after the frozen chain passes (`check_bank(test=True)`), and the CPU test guard proves it. Eval/sealed guards:
focus1 references no `data/` path; MODEL_INPUTS are the model/tokenizer files only; the fixture forbids
`data/bench`, `data/b3`, `data/sc1`, `/models/`, `torch.load`, CUDA. Extraction examples are the seeded synthetic
bank (`seed()` string verified against the spec: SHA-256 of `focus1-v2:20260904:<split>:<episode>:<purpose>`,
big-endian). Banks are deterministic (regenerated twice, equal); rejection counts extraction 0 / setup 0 / test 4.

### B1 (HIGH) — timing-smoke dose is a unit basis vector; under bf16 it can be a no-op and the non-vacuity `require` then kills the root with no second attempt

`timing_smoke()` (2816-2830) builds `vectors["A"] = e_0`, `vectors["B"] = e_1` (norm 1) and runs
`main_decisions`, `transient`, `neutral` with alpha 2.0 at layer 20. `neutral()` calls `compare_caches(...,
layer=20)`, which raises `Invalid("vacuous affected-layer K/V residuals")` unless BOTH K and V differ at EVERY
layer >= 20. The model runs in bf16 (`load_backend`: `.to(dtype=torch.bfloat16)`); `make_residual_hook` adds
`vector.to(hidden.dtype) * alpha` to the last position. Measured: `bf16(600.0) + 2.0 == 600.0` and `bf16(1200.0) +
2.0 == 1200.0` (lost), `bf16(300.0) + 2.0 == 302.0` (kept). Qwen residual streams carry a few massive-activation
coordinates; if coordinate 0 or 1 at the final prompt position is >= 512 the perturbation vanishes and every delta
is exactly zero; even when it survives, a ~2e-3 relative change must produce a nonzero bf16 K and V entry at all
eight layers 20-27. If it does not, the timing stage ends INVALID; `preflight` then refuses every later stage
("duplicate stage attempt; no retries/resumption") and the driver pins `--out` to `results/qwen/focus1-v2`, so the
only way forward is a manual root replacement outside the protocol. The smoke is declared a cost measurement
("deliberately no eligibility scoring/selection"); it should not be able to invalidate the program on a
numerics artefact.

Fix (src/stencil/focus1.py, `timing_smoke`): derive a disposable scale from the smoke's own OFF capture and use
random directions, e.g. after the extraction loop keep `captured` from the OFF pass and set
`rho_smoke = float(captured[20][0, -1].float().norm())`, then `vectors = random_directions("setup",
row["episode"], width, rho_smoke)`; record `smoke_rho` and `smoke_vector_sha256` in the timing manifest with
`formal_score=False`. This matches the real dose regime (rho_L is the mean layer-input difference norm, same order
as the input norm) without touching extraction or eligibility. Additionally make the smoke's `neutral()` call
non-fatal on the non-vacuity check only: add `audit=True` parameter to `neutral()`/`compare_caches` and pass
`audit=False` from the smoke, recording deltas without the `require`. Tests: (1) in `test_all_modes_real_cli...`
assert `store.read("timing.json")["smoke_rho"] > 0` and that the smoke vector hash differs from the extracted
vectors; (2) a unit test where a fake trunk returns identical K/V for a hooked and unhooked pass (simulating the
lost perturbation) and asserts `timing_smoke` still returns READY while `Engine.neutral` (default `audit=True`)
raises `Invalid`.

### B2 (HIGH, code side of A1) — `selection()` joint-copy floor

See A1 for the edit and test. Not a separate defect; listed so the harness verdict carries it.

### B3 (medium) — `cache_hash` hex-in-JSON is the dominant CPU overhead per decision and inflates the retained maxima the projection multiplies

`tensor_hash` builds `bytes.hex()` (2x the tensor size) inside a JSON dict, then `canonical()` re-encodes it before
SHA-256. Measured on this CPU with a 28-layer, 8-head, 128-dim bf16 cache: 250 positions (29 MB) 0.144 s; 400
positions (46 MB) 0.254 s, plus the GPU->CPU copy on the real trunk. Calls per decision: one in `decode`
(`final_kv_sha256`), four in `canonical()` (one per arm) per phase, three plus two in `neutral()` per query. Order
0.5-1 s per decision x 6,400 worst-case decisions = roughly 1-1.5 of the 6 GPU-hours, all of it counted into the
"canonical"/"clear" maxima that the projection multiplies by 1.25. Fix: hash raw bytes — `h = sha256(); h.update(
canonical(dict(shape=..., dtype=...))); h.update(memoryview(tensor.cpu().contiguous().numpy()))` — and in
`canonical()` hash the prefix once (the per-arm equality is already proven by `data_ptr` disjointness and the
zero-delta `compare_caches`). Test: `tensor_hash` equal for equal tensors, different for a one-element change,
different for same bytes with different dtype/shape; `canonical()` still records one `prefix_kv_sha256`.

### B4 (medium) — the duplicated OFF cue-absent competence pass should become the real-determinism witness

`competence()` decodes the identical cue-absent prompt once under task A and once under task B (A5). The harness
has no real-trunk determinism check before the 512-decision certification (whose transplant/sham pairs are also
same-input repeats, but those run only after extraction). Fix: keep both passes and `require(tokens_A == tokens_B,
"nondeterministic OFF decode")` per episode, recording the comparison in the competence manifest; INVALID on
mismatch. Test: fake trunk that flips one token on the second identical prompt -> `competence` raises `Invalid`.

### B5 (low) — `comparison["nonvacuous"] = True` is hard-coded

`neutral()` sets the flag unconditionally after `compare_caches` returned; the actual guarantee is the `require`
inside `compare_caches` and the re-check of the recorded deltas in `validate_run_records`. Harmless, but the
record misdescribes what was measured. Fix: store `nonvacuous = all(d["k"] > 0 and d["v"] > 0 for d in
deltas[layer:])` computed from the returned rows, or drop the field and let `episode_rows` recompute integrity from
`kv_deltas`.

### B6 (low) — `exact` can be true on a truncated reply; C/P/K use it without the breakage flag

`score_reply("[1,2,3,4,5]", 64 tokens no EOS)` -> exact True, T True, broken True. `episode_rows` uses bare `exact`
for the copy indicators (S/O/W/V/R use `and not broken`). The handoff declares this choice; the intervention
breakage gates (<=1/64 for CLEAR/KEEP/replay) bound the exposure. Either keep and add one sentence to the text
("copy indicators are exact-match regardless of breakage; breakage is gated separately"), or use `exact and not
broken` uniformly. No behaviour change needed for the verdict.

### B7 (low) — any text fix changes `REVIEWED_HASH`, `CODE_INPUTS` and therefore the bank manifest

`reviewed_section()` pins the v2 bytes; `fingerprints()` includes `src/stencil/focus1.py` itself. Applying A1/A3
(text) and B1/B3/B4 (code) means: update `REVIEWED_HASH`, regenerate the bank on CPU into an empty root (banks are
deterministic, so operand contents are unchanged; only the manifest hash moves), and issue the registration
against the new hash. This is the intended process; noting it so nobody tries to register the old hash with new
code (`check_bank` would refuse).

### B8 (low) — one-attempt-per-stage plus a pinned root makes every infrastructure blip terminal

`preflight` refuses a stage that appears in the allocation log, and the root is fixed. This is v2's "no
resumption" rule and I do not propose changing it, but it is why B1 is HIGH rather than medium. A single documented
operator step for a dead root (move the root aside, log the reason in the ledger, new registration) belongs in the
text.

### Over-engineering (3,121 lines)

Roughly 80% of the file is protocol-mandated (records, budget, registration/BFCL evidence consumer, frozen
manifests, analyze-from-records re-validation). What could go without losing the answer: the four scratch
forwards and four cache hashes in `Backend.canonical()` (keep one, ~20 lines and real GPU time); `keep_only()`
duplicating `neutral(keep=True)` (~25); the hash-chain tail bookkeeping in `Store.append` (~30, an fsynced append
with a final file hash is enough given the immutable-manifest check); the prefill indirection in `Backend.forward`
(`prefill_with_eviction(history_end=0)` is exactly `model(tokens, cache=...)`; ~10); `validate_run_records` could
be halved by reusing `score_reply`/`layout` tables rather than re-deriving every mapping (~120). About 200-250
lines, i.e. under 10%; not worth a refactor before the run, since every edit regenerates the bank anyway. Do the
B1/B3/B4 edits, nothing else.

## 3. Prior findings — status

F1-F6, F9, F10, F12-F14: closed (incorporated, verified in text and code). F7/F8: closed for the test family;
**reopened at selection as A1 (HIGH)**. F11: boundary numbers corrected; **the replacement sentence is wrong (A3,
medium)**. Kimi H1: adopted; its 32/32 copy gate is now unmotivated (A2, medium). No prior finding deleted.

## 4. Recomputed numbers (scratchpad pytest, pure Python `comb` / torch inside pytest only)

| quantity | text / handoff | recomputed |
|---|---|---|
| alpha_f | 1/60 | 0.016666... |
| lower-tail Bin(64,0.10) p(0)/p(1)/p(2) | 0.0011790184577738583 / 0.00956314971305463 / 0.03890760910653732 | 0.0011790184577738603 / 0.009563149713054645 / 0.03890760910653739 (match to 1e-17) |
| McNemar (33,17) / (34,18) | 0.01641956878213424 / 0.01824170000417991 | 0.016419568782134242 / 0.018241700004179906 (match); (33,17) infeasible with >=48 |
| max feasible McNemar p under count+net floors | handoff 0.01465247336026465 at (32,16) | 0.01465247336026465 at (32,16) (match) |
| P(sum S >= 48 \| p=29/32) / P(sum W >= 48) | 0.945636 / 0.122662 | 0.9456359780 / 0.1226621171 (match) |
| 0.05^(1/32) / sqrt(0.75) / 0.75^(1/4) | 0.910632 / 0.866025 / 0.930605 | match |
| P(32/32 copy pairs \| q) q=0.995/0.99/0.98 | — | 0.726 / 0.526 / 0.274 |
| P(31/32 copy pairs \| q) | — | 0.960 / 0.867 / 0.637 |
| selection joint-copy floor, both tasks, correlated / independent, q=0.99 | — | 0.752 / 0.408 |
| same, q=0.98 | — | 0.405 / 0.077 |
| test decodes | 64*(16+2+2+2+1)=1472 | 1472; `remaining_work("run")` sums to 1472 |
| worst-case scheduled decodes/prefills, all stages | — | 6,400 (`remaining_work("competence")` sum) |
| reviewed v2 section | 23,197 bytes, 71 lines, 746b35...67fb | match |
| bf16 +2.0 at 40 / 300 / 600 / 1200 | — | 42 / 302 / 600 (lost) / 1200 (lost) |
| `cache_hash` 28x8x128 bf16 at 250 / 400 positions | — | 0.144 s / 0.254 s (CPU) |

## 5. Exact fixes required before registration / GPU

1. **A1/B2 (HIGH)** — text clause and `selection()` edit + inverted test, as written in A1.
2. **B1 (HIGH)** — smoke dose from the OFF capture norm with random directions, smoke non-vacuity recorded not
   required, two tests, as written in B1.
3. **A3 (medium)** — replace the "paired tests can still bind" sentence.
4. **A2 (medium)** — copy gate 32/32 -> 31/32 or add the disclosure sentence.
5. **B3, B4 (medium)** — raw-bytes hashing; OFF determinism witness.
6. Then: update `REVIEWED_HASH`, regenerate the bank into an empty root, re-run the exact test command, and
   register against the new hash (B7).

Unverified here and still unverifiable on CPU: real tokenizer facts (128-token delay boundary, final wrapper token
identity across the extraction triple — the code checks both at generation time), bf16 determinism of the real
trunk, competence, residual behaviour, memory and measured rates.
