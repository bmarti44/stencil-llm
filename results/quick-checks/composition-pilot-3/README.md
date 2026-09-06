# Composition pilot 3 — INELIGIBLE

Completed 460 calls; R final success **0/8**. Round-0 R indent **2/8 required responses**; strictly executed/parsed eligible subset **2/4**; diagnostic emitted JSON-prefix code **2/8**. Prefix inspection never repairs or executes a rejected response. Determinism **D=0**, 48 calls across completed starts.

Failed/unmeasured gates: incomplete required R/N/T DEV trajectories; R round0 indentation <50% or incomplete; R executed-call rate <90%; R truncation >2%; N executed-call rate <90%; N truncation >2%; T executed-call rate <90%; T truncation >2%; R final success <5/8; registered projection >12h even setting unmeasured O cost to zero; check45 HF teacher-forced recovery cost unmeasured (prewritten full-cost condition).

| Arm | Calls executed | Caps | Final success | Stale execution | Wrong skill | Breakage | Decode tok/s | s/call |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
|R|53/160|59|0/8|7|1|140|10.460|35.844|
|N|49/160|82|0/8|13|6|133|10.770|38.026|
|T|65/140|52|0/4|7|0|77|11.758|30.739|
|O (UNRUN)|0/0|0|0/0|0|0|0|—|—|

Per-episode results (violations and relapse numerator/denominator in language/style/format/process order):

| Episode/arm | Success | Integration | Stale | Wrong | Breakage | Violations L/S/F/P | Relapse L/S/F/P |
|---|---:|---:|---:|---:|---:|---|---|
|slab-dev-00/R|False|False|0|0|15|0/3/16/3|0/0, 0/0, 0/4, 0/0|
|slab-dev-01/R|False|False|0|0|16|0/11/16/16|0/0, 0/3, 0/6, 0/0|
|slab-dev-06/R|False|False|0|1|32|0/0/32/1|0/0, 0/13, 0/14, 0/0|
|slab-dev-07/R|False|False|7|0|13|7/7/32/26|0/0, 7/13, 0/15, 0/0|
|slab-dev-00/N|False|False|0|0|15|0/2/16/2|0/0, 0/0, 0/4, 0/6|
|slab-dev-01/N|False|False|0|1|9|0/7/16/3|0/0, 0/0, 0/6, 0/0|
|slab-dev-06/N|False|False|0|3|32|0/0/32/3|0/0, 0/13, 0/14, 0/16|
|slab-dev-07/N|False|False|13|1|13|7/7/32/19|0/0, 7/13, 0/15, 11/11|
|slab-dev-00/T|False|True|0|0|0|0/0/16/12|0/0, 0/5, 0/4, 0/0|
|slab-dev-01/T|False|False|0|0|12|0/5/16/4|0/0, 0/0, 0/6, 0/0|
|slab-dev-06/T|False|False|0|0|32|0/0/32/0|0/0, 0/0, 0/0, 0/0|
|slab-dev-07/T|False|True|7|0|0|0/7/32/30|0/0, 7/13, 0/15, 0/0|
|slab-dev-02/R|False|False|0|0|16|0/0/16/0|0/0, 0/0, 0/0, 0/0|
|slab-dev-03/R|False|False|0|0|16|0/0/16/0|0/0, 0/0, 0/0, 0/0|
|slab-dev-04/R|False|False|0|0|16|0/1/16/0|0/0, 0/0, 0/5, 0/0|
|slab-dev-05/R|False|False|0|0|16|0/0/16/0|0/0, 0/0, 0/0, 0/0|
|slab-dev-02/N|False|False|0|0|16|0/0/16/0|0/0, 0/0, 0/0, 0/0|
|slab-dev-03/N|False|False|0|0|16|0/0/16/0|0/0, 0/0, 0/0, 0/0|
|slab-dev-04/N|False|False|0|1|16|0/5/16/5|0/0, 0/0, 0/5, 0/6|
|slab-dev-05/N|False|False|0|0|16|0/0/16/0|0/0, 0/0, 0/0, 0/0|
|slab-dev-02/T|INCOMPLETE|—|0|0|11|0/0/11/0|0/0, 0/0, 0/0, 0/0|
|slab-dev-03/T|INCOMPLETE|—|0|0|0|0/11/11/4|0/0, 0/0, 0/0, 0/0|
|slab-dev-04/T|INCOMPLETE|—|0|0|11|0/1/11/0|0/0, 0/0, 0/0, 0/0|
|slab-dev-05/T|INCOMPLETE|—|0|0|11|0/0/11/0|0/0, 0/0, 0/0, 0/0|
|slab-dev-00/O|UNRUN|—|—|—|—|—|—|
|slab-dev-01/O|UNRUN|—|—|—|—|—|—|
|slab-dev-02/O|UNRUN|—|—|—|—|—|—|
|slab-dev-03/O|UNRUN|—|—|—|—|—|—|
|slab-dev-04/O|UNRUN|—|—|—|—|—|—|
|slab-dev-05/O|UNRUN|—|—|—|—|—|—|
|slab-dev-06/O|UNRUN|—|—|—|—|—|—|
|slab-dev-07/O|UNRUN|—|—|—|—|—|—|

Per-episode timing and cost allocation (observed calls only). Allocated seconds = output tokens / measured whole-schedule aggregate rate; this partitions shared schedule cost by tokens, rather than measuring isolated episode GPU use. Startup/checks/cleanup are charged separately in the total.

| Episode/arm | Calls | Tokens | Decode tok/s | Seconds/call | Allocated schedule seconds |
|---|---:|---:|---:|---:|---:|
|slab-dev-00/R|16|7909|11.191|44.752|282.893|
|slab-dev-01/R|16|3650|9.538|24.880|130.555|
|slab-dev-06/R|32|16270|10.747|49.358|581.953|
|slab-dev-07/R|32|7666|9.337|27.286|274.201|
|slab-dev-00/N|16|7898|10.473|47.456|282.499|
|slab-dev-01/N|16|7112|10.061|44.692|254.385|
|slab-dev-06/N|32|15966|11.434|44.054|571.079|
|slab-dev-07/N|32|7884|10.950|23.005|281.998|
|slab-dev-00/T|16|3564|10.064|22.420|127.479|
|slab-dev-01/T|16|7786|12.150|40.663|278.493|
|slab-dev-06/T|32|15922|12.197|41.280|569.505|
|slab-dev-07/T|32|7941|10.784|23.660|284.037|
|slab-dev-02/R|16|4385|9.567|29.077|156.845|
|slab-dev-03/R|16|3914|9.721|26.087|139.998|
|slab-dev-04/R|16|6030|10.580|36.571|215.684|
|slab-dev-05/R|16|8122|11.858|43.783|290.511|
|slab-dev-02/N|16|8001|11.019|45.641|286.183|
|slab-dev-03/N|16|3949|10.369|24.203|141.250|
|slab-dev-04/N|16|7657|10.811|44.752|273.879|
|slab-dev-05/N|16|6315|10.141|39.397|225.878|
|slab-dev-02/T|11|4700|12.718|33.911|168.112|
|slab-dev-03/T|11|2301|10.868|19.680|82.303|
|slab-dev-04/T|11|2530|10.830|21.721|90.494|
|slab-dev-05/T|11|5030|13.165|35.233|179.915|

Passing main-run gates: determinism D=0; maximum actual context 31949 <=32256; executed-trait opportunities in at least two R episodes for kinds ['style', 'format']. These do not override the failed gates.

Actual fixed C4 schedule (including C2 long tails, HTTP, tools/checker and barriers) **27.958 tok/s**. GPU-held **8796.278/9000s** (all starts), load **428.536s**. Served-only conservative projection **UNAVAILABLE GPU-h**. Formula and all per-episode timing/token costs are in [summary.json](summary.json): prior spend + this run + measured reload +1.25 × [64(max R+max N tokens)+16(max O+max T tokens)] / measured aggregate rate. Max per-arm counts include32-round episodes. Overlapping request seconds are latency, not summed GPU cost. The known R/N/T contribution gives a registered-projection floor of **33.933h** even setting O cost to zero; this is a lower bound on that conservative projection, not a complete workload forecast. HF recovery remains unmeasured; full check45-inclusive eligibility receives no unmeasured credit.

DEV mask trigger **NOT ESTABLISHED**, kinds=[]; all four kinds and executed-prior-trait denominators are in summary. No masks enabled. T cumulative multi-function re-emissions: 0 parseable responses (names listed in summary); capped malformed responses are counted as breakage, not silently repaired.

Rejected Python-literal boolean residues (outside quoted code strings): {'R': 0, 'N': 0, 'T': 0, 'O': 0}. These are CPU classifications of literal journaled outputs, not parser repairs.

Gold events drive R in DEV only; no fitting, evaluation episode construction or data/bench reads. **package path outcome-unvalidated**. Backend uses qualification image digest `sha256:3dbe092ec5b2cef63b6104d33fa75d6ce53a7870962529ada69f78bbbc38e776`, exact flags/env and request parameters in [registration.json](registration.json). Prior HF divergence5/64 (R1/16) stands; this pilot does not remeasure HF trajectories.

[records.jsonl](records.jsonl) contains same-run v2 records, execution/tolerances, checker and per-call timings; [http/records.jsonl](http/records.jsonl) retains actual streamed token IDs/chunks/usage. [schedule.jsonl](schedule.jsonl) fixes episode lanes and round barriers. Hidden states are **not captured** on vLLM; check45 needs teacher-forced HF prefill. [transcript-manifest.json](transcript-manifest.json) lists the full HF final-input files under hf-transcripts/ (including system prefix), per-episode output and every prompt+body+EOS hash required, with layer/body-position convention. The separate retained-history hashes describe session state without the system prefix; those files alone are not HF prefill inputs.

[Unsubmitted calls](unsubmitted.jsonl): 20 required and 160 optional. UNRUN/None endpoints are unavailable, not observed failures or zeros. All planned episodes remain in eligibility accounting.

Stale execution counts rounds with actual executed tools and an observed retired-trait relapse. Per-kind relapse conditions on prior executed trait plus registered opportunity; style measures executed code, format/process measure emitted report traits. Current execution and attempted violations remain separate in records. Empty indentation is not compliant.

The conservative bound stopped the first trajectory runner at R round30 (estimated32657/28519). The registered [continuation](continuation/README.md) restores every saved response on CPU and uses exact rendered lengths, asserted again in the actual loop, to enforce the same32256 limit. Earlier outcomes are retained, never regenerated. [Continuation records](continuation/records.jsonl), [HTTP records](continuation/http/records.jsonl), schedule and lifecycle are separate; the summaries merge by episode/arm, replacing only partial bookkeeping receipts with their later complete receipt. The initial tuple/list hash-writer interruption and its500.353s charge are also retained.

Conditional lexical style screen: **COMPETENCE FAIL**, 2/8 compliant required responses, 2/2 eligible executed edits. This is round-zero competence only and does not change pilot3 ineligibility. [Style records, CPU witnesses, audit and summary](trait-swap/README.md); full HF input hashes are in trait-swap/transcripts.jsonl. Its 764.957s is included in the total above.

Validation: [targeted DEV-only tests](validation.log), [96-call CPU smoke](smoke.json), [640-call/32-receipt scheduling smoke](schedule-smoke.json), and [adapter EOS/cap cases](adapter-smoke.json). The final [CPU audit](audit.json) replays each saved actual prompt, controller state, output, execution and checker result and verifies backend identity, determinism, transcript hashes and cleanup. No full pytest suite or evaluation episodes were run.

[Prewritten registration](prewritten.md) follows unchanged.

# Composition pilot 3 — REGISTERED, not yet run

2026-09-06, gpt-6-astra. Fit/train-on: none. Evaluated-on: authored DEV episodes
00,01,06,07,02,03,04,05 only, disjoint from evaluation; no data/bench access.
Gold events drive R in DEV only. Actuator OFF in every arm.
**package path outcome-unvalidated**: outcomes attach to the qualified vLLM build.
The archived process protocol was read; this explicit pilot brief governs scope.

## Gates frozen before GPU

All are required for ELIGIBLE; otherwise INELIGIBLE, naming failed or unmeasured
items. Complete R/N/T trajectories for all eight DEV episodes (six 16-round and
two 32-round) are required. No episode exclusions or replacements.

- Determinism: first eight frozen qualification prompts (DEV00 rounds0/1, R/N/T/O
  each) single-stream cold, warm repeat, then fixed mixed-arm C4 waves; complete
  output IDs including EOS and cap must match, D=0. Failure stops episodes.
- R round-0 indent compliance >=50% of the eight required edits. A compliant edit
  must execute, contain nonempty indentation widths, and match the live width;
  invalid/missing/capped edits count noncompliant. Also report parsed attempted
  edit and executed edit denominators by arm. If <50%, freeze a CPU trait swap
  after this run and re-pilot only that trait under the remaining 2.5h budget;
  if insufficient budget, explicitly mark swapped-trait GPU re-pilot unrun.
- Executed response rate >=90%; truncation <=2%, pooled R/N/T and separately per
  arm (conservative all-arm requirement). T cumulative re-emission retains its
  original obligation and cap and counts as breakage identically to other arms.
- R final all-obligation success >=5/8; nonzero executed-trait denominators in
  >=2 DEV episodes for >=2 kinds in R (also disclose all arms).
- Every actual context <=32,768-512; conservative pre-render bounds checked too.
- Cost R/N x64 + O/T x16 <=12 GPU-h: measured schedule aggregate output tokens /
  actual wall including callback overhead; use max measured per-episode token
  count per arm to cover both lengths. Add all prior pilot/qualification spend,
  this GPU-held run, one measured reload, and25% future reserve. No unmeasured
  O, HF-recovery, long-context, or concurrency acceleration credit: missing O or
  HF recovery timing leaves the full check45-inclusive projection unestablished.
  Report served-only projection separately; no inference of full eligibility.

## Frozen execution contract

Reuse qualification attempts.json successful command VERBATIM except unique
owned container name. Image digest
`sha256:3dbe092ec5b2cef63b6104d33fa75d6ce53a7870962529ada69f78bbbc38e776`,
TRITON_ATTN, bf16 model/auto bf16 KV, invariant env1, prefix caching,
max-num-seqs4, context32768, token batch2048, utilization0.70. One start, no
configuration fallback. Raw token-ID completions through loop.generate_once;
controller/register/renderer/checker/executor stay in the CPU caller.
Qualification request parameters are reused exactly, including stop IDs151645
and151643 (both are also in the actual HF generation_config). Amendment2's
single-EOS prose conflicts with those artifacts: the user's explicit qualified
backend reuse and identical HF/arm semantics govern; record all terminal IDs.
Cap512 includes EOS, no retokenization of returned IDs, no chat template.

Fixed schedule: two episode groups [00,01,06,07], [02,03,04,05]. For each group,
run R to completion, then N, then T. At each round submit active episodes in
that listed order to up to four workers and wait for all before advancing.
Thus each episode has R then N then T; dependent rounds never run ahead.
The two long episodes continue at C2 after the short episodes finish, fully
charged in the measured schedule rate. Only after all R/N/T, run O in the same
fixed episode groups if the measured conservative estimate fits the deadline.
No new calls in the last180s; HTTP requests bounded, cleanup reserved. GPU cap
9000s includes startup, determinism, episodes and owned-container stop/removal.
Write RUNNING.flag only after other Stencil flags and GPU python processes clear.
Never signal host processes; stop/rm only this run's successfully created container.

Corrected newline append, shared indent gloss, strict amended parser and explicit
report example are frozen unchanged. Only the two registered parser tolerances
are allowed and journaled. Python True/False and malformed JSON remain rejected.
Journal all v2 FIELDS in the same run plus backend identity and per-call streaming
IDs/timing, execution/tolerances/outcomes, context bounds and source hashes.
Hidden states are NOT captured on vLLM. Check45 requires teacher-forced HF prefill
of exact final transcripts; manifest lists per-call prompt+body+EOS ID hashes and
per-episode final transcript/output hashes. No HF-recovery timing is invented.
DEV mask trigger uses v2 section3: R >=15% relapse, >=20 executed-trait
opportunities of a kind, relapse in >=2 episodes; O same kind in >=2 episodes
with verified state/render. All kinds/denominators reported. No mask run authorized.

## Pre-trajectory startup correction

The first owned start was stopped during determinism, before any DEV trajectory,
after a CPU check exposed tuple+list concatenation in the episode output-hash
writer. Exact interrupted calls/logs/lifecycle and original source registration
are preserved under initial-attempt/. This is an orchestration defect, not a
backend determinism failure or an outcome-selected change. The hash writer now
normalizes IDs to a list. The full scheduling/episode-writer path is CPU-smoked
before restart. Backend command/env remain unchanged; no model/prompt/checker
changes. First GPU-held spend 500.353s is subtracted from the restart's9000s
allowance and included in all cost totals. No completed DEV episode is repeated.
