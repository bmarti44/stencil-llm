# Composition DEV re-pilot — INCOMPLETE: parity gate failed

**STOP: grouped_mm diverged on4/64 frozen sequential prompts (allowed<=1).**
All64 comparisons completed; no amended re-pilot was launched. R/N/T episodes
00,01,06,07,02,03,04,05, optional O, both-length competence and check45 trajectories
are **UNRUN**. No larger experiment is eligible under this gate.

CPU amendment registered in0edebc74 before code; implementation freeze a3fd8613.
Exactly two journaled strict-JSON tolerances: lift top-level status/task/delivery
when report is absent (journal discarded keys), and remove path from test.
The prompt now names report keys and gives a literal example; errors give stable
expected-envelope feedback. No Python-literal/bracket repair, renderer-layout,
T-obligation, cap512 or band100–300 change. Eager remains an explicit fallback
flag; this single load used grouped_mm, bf16, SDPA, greedy, sequential, actuator OFF.

| Frozen DEV00 gate arm | Exact matches | First divergent token (round0, zero-based) | Decode tok/s | Seconds/call including prefill | Cap hits | Max prompt |
|---|---:|---:|---:|---:|---:|---:|
|N|15/16|72|17.499|12.006|0/16|5,394|
|O|15/16|191|16.570|12.569|0/16|11,050|
|R|15/16|191|16.541|12.793|0/16|11,050|
|T|15/16|0|16.746|27.256|10/16|9,727|

**60/64 match exactly; every round1–15 matches in all four arms.** R/O round0
change the report envelope; N changes docstring wording; T changes JSON layout
from token0. [gate-analysis.json](gate-analysis.json) preserves decoded windows;
no logits/margins were captured, so near-tie causation is not established.
Eight cache initializations/resets: four initial lanes, then four resets to the
frozen round1 prompts after mismatches; all subsequent prefixes were retained.

Aggregate decode **16.813 tok/s**, about1.55x prior eager10.827
(<1.84x reviewed target); mean **16.156 seconds/call**.
Gate truncation10/64=15.625% comes from the **old frozen interface**, not amended
re-pilot responses. Max prompt11,050 +512 reserve=11,562<=32,768; no32-round
trajectory was measured. GPU-held **1362.257/7200s=0.378405h**, including
load323.293s and cleanup; peak allocation65,129,094,656 bytes. Normal exit,
RUNNING.flag removed, no process signals or push.

**Re-pilot cost projection: UNAVAILABLE.** Diagnostic projection from the completed
frozen16-round replay only: **14.391 GPU-h>12** for R/Nx64 + O/Tx16.
Formula `(prior5385.346 + this1362.257 + reload323.293 +
1.25*[64(cR+cN)+16(cT+cO)])/3600`; measured gate cR/N/T/O=
205.930/193.346/437.335/202.352s, including allocated non-decoder overhead.
No batching credit or unmeasured32-round normalization. Failed parity and the
old interface make this a diagnostic, not an amended-pilot eligibility estimate.

Re-pilot executed-call rate, final success/integration, per-kind relapse and
executed-trait denominators are **unavailable**, not measured zeros. DEV mask
trigger **NOT ESTABLISHED**; no re-pilot R/O evidence in>=2 episodes. The registered
ELIGIBLE/INELIGIBLE thresholds were not tested after amendment because the parity
prerequisite failed; INCOMPLETE is the prewritten gate-stop reading.

CPU recovered outcomes remain separate: **95/128 responses execute190 tools;
final success0/8 lanes and final integration0/8**. All95 parsed responses violate
indentation; append snippets lack separating newlines and invalidate cumulative
files. N's discarded verbose wrappers contain4 unscoped delivery claims, preserved
as diagnostics rather than a third tolerance. All recovered executed-trait relapse
denominators are0. [Recovered report and per-kind results](../composition-pilot/README.md)
include every128-row tolerance/execution/outcome record; these are frozen-output
replays, not model continuations after repaired feedback.

Artifacts: [parity-records.jsonl](parity-records.jsonl) has64 complete prompt/output
ID records and timing; records.jsonl is empty because the re-pilot was not run.
[renderer-check.json](renderer-check.json) verifies16 original-system/feedback
prompts against the unchanged GPU golden. [audit.json](audit.json) verifies literal
IDs, first positions, cache prefixes, frozen sources and all128 hidden hashes/shapes.
[hidden-manifest.json](hidden-manifest.json): local float16(5,2048), post-block
layers8/16/24/32/40, last-prompt-token and generated-mean. Ten cap-side means are
partial, labeled by exact forward counts. Arrays remain out of git and are parity
artifacts, not amended re-pilot labels for check45.

Fit/train none. **Scope deviation:** an inadvertently broad CPU test selection
instantiated synthetic evaluation-bank generator/witness cases. It finished without
signals (134 passed,2 stale-fixture failures); no data/bench read, evaluation-model
inference, or evaluation-performance use in scientific decisions. Final validation
uses a DEV-only construction guard. Fixture refresh reuses that run's metadata
receipt without further evaluation generation: episode/hidden/turn hashes unchanged;
public/system hashes refreshed, +49 prompt tokens derived algebraically, DEV replay
verified unchanged renderer/event/workspace hashes. Original GPU golden is untouched.
The metadata-only fixture refresh occurred after GPU exit and is audited separately
from frozen inference sources. CPU accounting remains a reference estimate.

Reproduce CPU recovery: `python -m stencil.focus.pilot_recovery`.
Reproduce gate audit: `python -m stencil.focus.pilot2_audit` (requires local hidden/).
`python -m stencil.focus.pilot2_report` reproduces summary/hidden manifest and a
basic report; this README also documents the audit and scope deviation.

Final validation: **56 passed**, with a fail-loud DEV-only construction guard;
18 DEV constructions, zero evaluation constructions in that final invocation.
The first guarded invocation stopped a legacy test's evaluation-freeze subcheck
before construction (55 pass/1 guard rejection); its log is retained separately.
The replacement DEV fixture test checks the same real dry-run accounting/render/
event/workspace fields without that evaluation subcheck. Scoped Ruff and diff
checks pass. [validation.json](validation.json) and [validation.log](validation.log)
record final results; the earlier guard rejection is not hidden or called a pass.
