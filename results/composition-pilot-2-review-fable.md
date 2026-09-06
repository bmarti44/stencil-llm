# Composition re-pilot (pilot-2) — independent review (fable, one round)

Scope: `results/quick-checks/composition-pilot-2/` (README, gate-analysis.json, parity-records.jsonl,
summary/run/audit/parity.json, run.log), amendment commit `0edebc74`, implementation `a3fd8613`,
and the CPU recovery of pilot-1 outputs (`results/quick-checks/composition-pilot/recovered-*.json*`,
`src/stencil/focus/pilot_recovery.py`). CPU only; DEV-00 only; no data/bench, no evaluation episode
content, no GPU. Every number below was recomputed from the records, not copied from the README.

## 1. Accuracy — all headline numbers reproduce; freeze order correct; tolerances match registration

Recomputed from the 64 rows of `parity-records.jsonl` (sha256 `df03870c…` matches audit.json):

| Claim | README | Recomputed | Verdict |
|---|---|---|---|
| Exact matches | 60/64 | `identical` true on 60 rows; false on indices 0-3 | OK |
| Divergent arm/round/first token | R/N/T/O, round 0, tokens 191/72/0/191 | (0,R,r0,191) (1,N,r0,72) (2,T,r0,0) (3,O,r0,191) | OK |
| All rounds 1-15 match in all arms | yes | 16 rounds per arm present; only round-0 rows differ | OK |
| Per-arm decode tok/s | 17.499/16.570/16.541/16.746 | sum(decode_steps)/sum(decode_seconds) = 17.499/16.570/16.541/16.746 | OK |
| Aggregate decode | 16.813 | 16.8128 | OK |
| Speedup vs eager 10.827 | ~1.55x | 1.5528 | OK |
| Seconds/call | 12.006/12.569/12.793/27.256; mean 16.156 | batch_wall mean per arm identical; 1033.98/64 = 16.156 | OK |
| Cap hits | T 10/16, others 0 | T truncated rounds 6-15 (512 ids); 0 elsewhere | OK |
| Max prompt | 5,394 / 11,050 / 11,050 / 9,727 | max(len(prompt_ids)) per arm identical | OK |
| Cache resets | 8 | cache_reset true at rounds 0 and 1 in every arm (4 initial + 4 post-mismatch) | OK |
| GPU-held | 1362.257 s = 0.378405 h | finished-started = 1362.257; /3600 = 0.378405 | OK |
| Load | 323.293 s | run.log weight-load bar ends at 5:15 (315 s) + tokenizer/config | plausible |
| Projection | 14.391 GPU-h | (5385.346+1362.257+323.293+1.25*[64*(205.930+193.346)+16*(437.335+202.352)])/3600 = 14.3908 | OK |
| Per-arm episode seconds | 205.930/193.346/437.335/202.352 | sum(batch_wall) + 16/64 of the 4.986 s outside-decoder overhead (e.g. R 204.683+1.247=205.930) | OK, allocation disclosed |

Note on "60/64": rounds 1-15 were replayed on the *frozen* prompts after a cache reset (teacher-forced
prefixes), so 60/64 is a per-prompt match rate under forced history, not an episode-level match rate.
A free-running episode diverging at round 0 would diverge at every later round; the README's wording
("every round 1-15 matches") is correct but should not be read as episode-level equivalence.

Freeze order: `0edebc74` (13:55:16, registers exactly two tolerances + grouped_mm gate; touches only
LEDGER + pilot-1 README) -> `4efdbdae` (13:55:39, throughput research, doc only) -> `a3fd8613`
(14:05:24, implementation; `git merge-base --is-ancestor` confirms 0edebc74 is an ancestor). The GPU run
started 14:05:46 (`started_at` 1788717946.52), after the implementation commit. Order is correct.

Tolerances in `src/stencil/focus/slab.py::parse_envelope` vs registration:
- (1) registered "remove only an extra `path` key from a `test` call" -> implemented: for each call
  with `op=="test"` and `"path"` present, `call.pop("path")`, journaled as `test_path`. Exact.
- (2) registered "only when `report` is absent and `calls` is present, lift present top-level
  status/task/delivery into `report`, dropping other top-level keys (including verbose, preserved in the
  journal); do not interpret nested verbose as task/delivery" -> implemented: guarded by
  `"report" not in payload and "calls" in payload`; lifts only the three top-level keys; `dropped`
  dict journaled; nested `verbose` never read. Exact.
- No Python-literal or bracket repair: `json.loads` failure raises `EnvelopeError("envelope")` and the
  executor returns the stable `{"error":"envelope","expected":'{"calls":[...],"report":{"status":"ok"}}'}`
  feedback (registered "never json-module exception text"). `check()` calls the same `parse_envelope`
  (registered "execution and checker share normalization"). The journal is attached to `self.tolerances`
  before the try block, so applications on subsequently rejected outputs are preserved (registered).
- Prompt: the three added sentences name the report keys and give the literal example; renderer layout,
  T obligation text, cap 512 and band 100-300 are untouched in the diff.

One residual accuracy nit: the README says "N changes docstring wording" for the token-72 divergence,
which is right, but the R/O round-0 grouped_mm outputs are more than "envelope" changes — they add a
nested `delivery` object (`{"task":"A","status":"ok","receipt":"public_tests_passed"}`) on a task-B
round. Under the amended parser that lifted `delivery` is a **process violation** (delivery reported when
not in scope), whereas the frozen eager output (`"status":"ok"` only) is clean. I.e. the backend
change flips a scored round-0 outcome in R and O and not in N. This matters for section 2.

## 2. The backend ruling — sound with three conditions; one registered gate is being superseded

Ruling under review: cross-backend byte parity is not a validity requirement; validity requires one
frozen backend used identically across all arms with run-to-run determinism; cross-backend divergence
vs the HF package path is a disclosed number, not a gate.

**Scientifically sound for the paired R-vs-N test, yes**, because the hypothesis is about the effect of
the rendered register on the trunk's behaviour, not about equality with a reference implementation. Any
backend is a numerical realization of the same weights; both arms share it; pairing removes shared
nuisance. The 4/64 gate result is itself the evidence that ~6% of *prompts* sit at greedy near-ties
across realizations (first-divergence tokens 0/72/191 are all whitespace/wording/envelope choices, no
logits captured), which compounds to a much larger *episode*-level divergence — so demanding
cross-backend byte equality was never going to be achievable and was never what the science needed.

Conditions that must hold for "one frozen backend used identically" to actually be identical:

1. **Determinism must be verified at the schedule level, not assumed.** R prompts are ~2x N's (11,050 vs
   5,394 tokens). Under continuous batching, a request's numerics depend on what it is co-scheduled with
   unless the backend is batch-invariant; R and N would then see *different* co-batching distributions
   simply because their prefill/decode shapes differ. This is arm-correlated noise, and with ~6%
   near-tie prompts it is not negligible. The qualification protocol step 4 (B1 cold/warm, B4/B8 in two
   orders, restart) with D=0 is the right test; `VLLM_BATCH_INVARIANT=1` is the mechanism; until D=0 is
   shown for mixed-arm batches, run B1 only. Record the exact backend build, flags, kernels, and a
   per-episode output-ID hash so any later rerun can prove determinism rather than claim it.
2. **Stop/cap semantics must be identical across arms and equal to the registered ones**: the same EOS
   set (`<|im_end|>` 151645; not also `<|endoftext|>`), the same 512 cap, the same 32,768 context bound.
   Truncation is scored as breakage, and R's outputs are longer (T already hits cap 10/16), so any
   stop-set difference is an arm-asymmetric bias, not just noise.
3. **Backend selection must be outcome-blind.** The grouped_mm gate (<=1 divergence) was *registered* in
   `0edebc74` as a proceed/stop criterion and it failed 4/64. Superseding it is acceptable only as an
   explicit amendment stating (a) the gate measured computational equivalence, not the science, (b) the
   backend is chosen on throughput/determinism from the DEV screen, frozen before any evaluation
   episode, and (c) no arm outcome under any backend informed the choice. Otherwise this reads as
   relaxing a registered gate after seeing it fail.

**Prefix caching confound**: with a correct block cache, cached KV blocks are bit-identical to what a
recompute would produce only if the backend is batch-invariant; otherwise a warm hit reuses KV computed
under a different batch composition. So caching is an *outputs* risk only in the non-invariant case
(covered by condition 1, cold-vs-warm D=0). In *cost* it favours R (longer shared prefixes, more
absolute savings) — that is fine to credit, but it must be measured on the DEV screen and the projection
must not assume it: the pilot-1 analysis already showed prefill is 3.6% of wall, so caching cannot be
the thing that gets the test under 12 h; decode speed is. The 12 GPU-h ceiling is an external gate
and cost asymmetry between arms does not bias the paired outcome.

**What the ship-package claim must report** (HF `custom_generate`/`retained_decode.py` path vs a
vLLM-served trunk):
- Which backend generated every piece of test evidence (version, flags, kernels), and that the
  controller/register/renderer/checker/executor bytes (hash) are identical between the served path and
  the package path — the mechanism being shipped is the controller, not the decoder.
- D_HF<->backend on the frozen prompt screen (this run gives D=4/64 eager<->grouped_mm under HF alone;
  the vLLM screen adds its own D), with first-divergence positions, split by arm and context, and the
  statement that D at episode level is larger than per-prompt D.
- Run-to-run D=0 for the served backend under the actual schedule used (condition 1).
- An explicit sentence that the HF custom_generate path is a byte-different realization: either run a
  small registered DEV subset end-to-end on it with its own answers fed forward (protocol step 8) and
  report outcome agreement, or state that the package path is unvalidated for outcomes and the
  behavioural claim attaches to backend X only.
- Hidden-state artifacts (layers 8/16/24/32/40) are an HF-path measurement; a served backend does not
  produce them. If check45 or any label needs them, register a separate replay cost; do not report the
  served run as "the same measured workload".

## 3. Competence — 0/8 is two interface-adjacent defects, not a checker error; it does threaten power

The DEV-00 checker is passable: replaying `reference()` through `Executor`+`check()` for all 16 rounds
gives final success True, integration True, zero violations (CPU, this review). The hidden cases test
exactly the requested transform (`v*6+3`, `v*4+7`, …) — nothing unrequested. So this is not a
checker-expectation problem.

The recovered lanes decompose cleanly. Per-round violation sets for sequential/R:
round 0 `{format, style}`; rounds 1-11 `{format, process, style, breakage}`; rounds 12-15
`{process, style, breakage}` (format clears when DEV-00 switches to compact at round 12). Two
independent causes, each fatal on its own for `success`, one fatal for `integration`:

**(a) Append without a separator — breakage+process from round 1 in all 6 executed lanes.** All 95
executed `edit` codes end without a trailing newline (0/95 `endswith("\n")`). `Executor.run` appends
raw (`path.write_text(path.read_text() + code)`), so round 1 produces `…return [v * 6 + 3 for v in x]def
step_1(x):`, the module stops parsing, public tests fail (`{"failed":1,"passed":0,"receipt":null}`),
`receipt` stays None (process violation) and the hidden batch raises InvalidProgram (breakage). Isolating
it: the reference with trailing newlines stripped -> `[breakage, process]` from round 1, final
integration False. The checker's own `check()` joins edits with `"\n"`, i.e. the evaluator already
assumes a newline boundary that the executor does not provide. Models emitting JSON strings rarely end
code with `\n`; without a fix this recurs in every arm, every episode, and no round-0 feedback can
prevent it (the break appears at round 1). Whether Qwen would notice `failed:1` at round 1 and repair with
`replace` is unknown — pilot-1 gave it no real feedback — but a test whose every episode depends on a
self-repair of a tool artefact is not the registered test.

**(b) Indentation obligation never followed — style violation in 95/95 executed replies.** DEV-00 sets
`indent=3` at round 0 (initial files use 2), supersedes to 2 at round 11, reinstates 3 at round 13; the
model used 4-space blocks in every one of 95 edits in every lane (widths `(4,4)`/`(4,4,4)`), including
N round 11 immediately after the explicit "supersedes indent -> 2". Isolating it: the reference re-indented
to 4 -> `[style]` only, final integration True, final success False. This is the trait under test, so it
cannot be tolerated away, but note how it is expressed: the request says `add indent -> 3.` and the
system prompt says "Style indentation denotes a block width; continuation alignment is free." That is a
cryptic phrasing against a very strong 4-space prior; even the T arm's "Effective obligations: …
indent=3" line got 0/15 compliance in batch T. Cause is therefore mixed: partly unnatural rule (3 spaces),
mostly unclear rendering of the rule. Style is checked on emitted code with `indent_widths`
(tokenize INDENT deltas, docstrings excluded) — the checker is not the problem.

**The 33 rejections are interface residue, not competence**: 16 sequential T = 6 Python-literal
`"verbose": True` (rounds 0-5) + 10 cap-512 truncations (rounds 6-15, unterminated string); 16 batch N =
"Extra data": the model appended a fabricated results/receipt array after the envelope; 1 batch T =
truncation. The amended prompt (literal example, "task (verbose format only)") targets the first two;
T's truncations come from T re-emitting prior steps cumulatively (outputs 192->333->474->cap) and will
recur under cap 512 unless T stops repeating — descriptive arm, not a gate. Format violations rounds 0-11
(report lacked `task` under verbose) are the old-prompt residue the amendment addresses.

**Power**: `paired_clauses` scores episode success as final `not any(violations)`; with (a) every
episode has breakage from round 1 and with (b) every episode has a style violation at the final round,
so R and N success are both ~0, gain = 0, and the primary clause (gain >= 8/64, McNemar p <= .05) cannot
pass regardless of what the register does. The 48/64 R floor (v2 review M2) is unreachable by a wider
margin. Relapse denominators are also 0 in the recovery because no executed emission ever carried the
retired trait, so the per-kind relapse gates are unobservable too. The bank is **not** fine as-is.

**Concrete CPU fixes (register before code, as with Day 5b; both arm-neutral; no evaluation content):**
1. `Executor.run`: on `edit`, insert `"\n"` between the existing file and the appended code when the
   file does not already end in a newline (and update `TOOL_SCHEMA["edit_semantics"]` to "edit appends
   Python on a new line"). This aligns the executor with the checker's existing `"\n".join`. Expect
   DEV replay workspace/receipt hashes in fixtures to change; refresh them and re-run
   `pilot_recovery` — the expectation is that integration recovers in R/N/O sequential lanes (semantic
   correctness of all 95 programs was established in the pilot-1 review), leaving style as the sole
   final-round violation.
2. Make the indent obligation legible without exemplifying it: one system-prompt sentence such as
   "indent N means every block body is indented by exactly N spaces" (a gloss of the existing "block
   width" sentence, not a probe exemplar), and render the round-0 obligation sentence with the same
   noun ("indent must be 3 spaces"). Then check compliance at round 0 on the DEV screen: if a 30B trunk
   still cannot produce 3-space blocks on request with a clear instruction, the trait is not a fair
   carrier for the register question and should be swapped (e.g. a lexical trait) before the larger
   test — a competence finding about the trait, not about the register.
3. Re-run `python -m stencil.focus.pilot_recovery` after (1) and report the recovered per-lane
   integration and the style-only residue; keep the current 0/8 record as the pre-fix baseline.
Fix 1 is a defect in the harness and should be uncontroversial. Fix 2 changes wording of the trait
rendering identically in every arm; it must be frozen before any evaluation episode is generated.

## Verdict

Accuracy: PASS — all gate numbers, the projection arithmetic, freeze order, and the two tolerances
reproduce exactly. Backend ruling: SOUND with conditions (verified schedule-level determinism, identical
stop/cap semantics, outcome-blind selection recorded as an amendment superseding the registered
<=1-divergence gate). Competence: 0/8 is a harness append defect plus an illegible indent rule, both
arm-neutral and both fatal to the primary endpoint; fix on CPU and re-recover before any larger launch.
