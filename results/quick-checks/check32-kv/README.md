# Quick check 32 (Q4): operand-free KV packet transplant

Unregistered, disclosed quick check; seed 32040; 2026-09-05. Q2 was declined by Brian and never run to completion. Sources: `results/hypotheses-fable.md` #3 and `results/hypotheses-astra.md` #4. This tests extracted latent instructions, not training or a claim of content-free circuitry.

## Fixed reading — written before any Q4 model execution

For each trunk, 64 paired episodes, each with SET(A), HOLD(A), SWITCH(B), BACK(A), CLEAR(copy). **PASS** requires correct-packet SET/HOLD/SWITCH/BACK jointly value-exact in >=40/64 episodes; text-cue bar jointly >=48/64 (otherwise **INELIGIBLE**); swapped packet jointly follows B/B/A/B in >=40/64; shuffled packet produces either task on ANY of the first four decisions in <=8/64; correct-packet breakage on ANY of five decisions <=2/64; correct-packet CLEAR impositions (A or B output) <=2/64; and the per-layer residual audit is reported. **MARGINAL** requires correct SET alone >=32/64 and shuffled induction <=8/64, provided the text bar is eligible. **FAIL** otherwise. Incomplete matrices are **PARTIAL**, with counts and no extrapolated verdict. The layer >=12 diagnostic cannot rescue the primary all-layer verdict. HOLD without reapplication is reported separately. Thresholds will not change after outcomes.

Breakage means truncated output, repeated 4-gram fraction >0.2, duplicated output integers, or inability to parse a list of integers after format-only leniency. Leniency accepts code fences, quoted integer entries and a single list embedded in prose; it never drops/adds values, changes signs or reorders. Strict JSON integer-list exactness is recorded too. Because reverse(input) cannot equal a distinct input, “exclude already in A- or B-form” is conservatively implemented as rejecting ascending AND descending inputs; this also ensures A, B and copy targets differ. All 320 unordered operand sets are unique, with 5–8 distinct integers in -20..20.

## Frozen implementation choices and lineage

Extraction-only, fit-on=nothing: 32 operand/answer-free authored cue paraphrases each for A, B and OFF, with seed-shuffled order separate from the seed-32040 evaluation RNG. Donor and recipient suffix positions are identically 80–83 (zero-based absolute positions). A generic JSON-format system prefix and explicit space-token padding align all inputs; the suffix is exactly four tokens, ` The context is ready`. No donor cue columns are copied. Each packet averages suffix post-RoPE K and V in fp32, then casts to bf16 for cache replacement. Per-layer K/V norms and joint cosine(A,B) are reported. No benchmark inputs or recorded benchmark responses are accessed; no fitting, training, tuning or test-driven selection.

Six arms: correct all layers, swapped all layers, per-episode independent random K/V with each layer's K and V norm matched to the corresponding packet, OFF throughout, text-cue bar with no cache edits, correct at layers >=12 only (zero-based). Same lists across arms and trunks. SET is a one-shot four-column write before the operand query; HOLD retains those columns across a 128-token neutral filler turn and makes zero writes. SWITCH/BACK overwrite those columns; CLEAR restores packet_OFF there without rebuilding any other columns. OFF is installed once and retained throughout. Text bar has A in its initial system prompt, no new cue for HOLD, B at SWITCH, A at BACK, and an explicit copy request at CLEAR. All generated tokens and EOS stay in history; greedy hook-free generation, maximum 64 output tokens per decision.

A simultaneous teacher-forced OFF replay receives the treated arm's identical token IDs with identical forward-call boundaries, using the second row of a batch of two. It begins from the same neutral recipient prefix plus packet_OFF, never task packets. Thus full-cache residuals isolate changed cache state on identical histories without differences caused by separately generated answers or prefill chunking. At CLEAR record per-layer K/V max-absolute differences for the four restored positions, all remaining positions, and the whole cache, plus bitwise-equality flags. In the subset arm, low layers remain the clean neutral prefix and the shadow matches that baseline. Text bar has no surgery; its shadow is an identical text replay and is labelled accordingly. Restored-column equality alone does not establish whole-cache clearance; residuals are descriptive, not an additional zero-residual pass threshold.

GPU precheck: compute-app query and pmon empty; no holders of `/dev/nvidia0` or `/dev/nvidia-uvm`. GB10 utilization remained fixed at 96%, memory activity 0%, power 19W; disclosed as apparently stale utilization telemetry. Compute processes are checked again before loading and periodically during execution; any foreign compute process aborts the run cooperatively. Foreground only; no process signals; 90 GPU-minutes total, 4B first. The cap includes extraction, loading and audit work, with partial records flushed as produced.

## Results

**ABORTED BEFORE GPU EXECUTION — both trunks NOT RUN.** The final pre-launch compute query reported PID 281741, a Q2 `check32/resume_segments.py 4b 34 50` process. Brian required abort on any compute process. Q4 launched no model process, extracted no packets, and used **0 GPU-minutes**. No process was terminated or signalled. The fixed reading above remains prospective; no PASS/FAIL scientific verdict is available. Initial apparently stale utilization telemetry did not authorize sharing the GPU once a compute process appeared.

| Checkpoint | Arm | Completed episodes | SET | HOLD | SWITCH | BACK | CLEAR | Residual audit |
|---|---|---:|---|---|---|---|---|---|
| 4B | correct | 0/64 | — | — | — | — | — | Not measured |
| 4B | swapped | 0/64 | — | — | — | — | — | Not measured |
| 4B | shuffled | 0/64 | — | — | — | — | — | Not measured |
| 4B | off | 0/64 | — | — | — | — | — | Not measured |
| 4B | text | 0/64 | — | — | — | — | — | Not measured |
| 4B | layers_ge12 | 0/64 | — | — | — | — | — | Not measured |
| 1.7B | correct | 0/64 | — | — | — | — | — | Not measured |
| 1.7B | swapped | 0/64 | — | — | — | — | — | Not measured |
| 1.7B | shuffled | 0/64 | — | — | — | — | — | Not measured |
| 1.7B | off | 0/64 | — | — | — | — | — | Not measured |
| 1.7B | text | 0/64 | — | — | — | — | — | Not measured |
| 1.7B | layers_ge12 | 0/64 | — | — | — | — | — | Not measured |

4B: No Q4 packet extraction or task episodes ran, so this quick check says nothing about whether the 4B trunk can set, hold, switch, or clear a transplanted task packet. HOLD without reapplication and bitwise clear-by-restore remain untested on the real trunk.

1.7B: The secondary trunk was not started because the GPU precondition failed before the primary trunk. There are no competence, packet, task-following, or residual measurements for 1.7B.

The script passed CPU scorer and verdict boundary checks, unique-list checks, direct KV write/residual checks, and complete five-decision fake-trunk execution for all six arms through the actual cache consumer. The fake-trunk runs checked every generated token and EOS was retained, HOLD performed no edit and kept its packet bitwise, and CLEAR restored the target columns while auditing the rest. These are implementation checks, not model results. Ruff and import-side-effect checks passed. `abort.json` records the pre-results reading hash; each summary reports the abort and each records file is empty. Packet norms/cosines and per-layer real-trunk residuals are unavailable because extraction never began. Re-running requires a fresh authorized attempt after the GPU is idle; the script refuses to overwrite these summaries.
