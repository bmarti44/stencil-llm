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
