# Check 40c — router dose and first-k generated tokens

Unregistered, disclosed, 2026-09-05. Same Qwen3-30B-A3B, seed 40040,
32 uncued synthetic check40b screen tasks, frozen JS direction, greedy fresh-KV
SET-only requests, inherited prompt, router hook and 64-token cap. No fitting or
training. Profile-on: prior 32 cued competence responses; prior alpha selected on
eight setup tasks. Evaluated-on: same already-observed 32 synthetic screen tasks;
this is an exploratory reuse and cell selection, not a fresh held-out confirmation.
No benchmark or sealed IFEval/BFCL input is read.

## Pre-written reading (fixed before new outcomes)

Four new arms, 32 each: alpha 2 sustained; alpha 3 sustained; alpha 4 first 3
generated tokens then OFF; alpha 4 first 8 then OFF. Recorded check40b alpha 4
sustained and OFF are reference rows only, never regenerated. All 128 generations
run once; no outcome-based retries, cap changes, additional arms or task reduction.
POSSIBLE iff some NEW cell has valid unbroken JavaScript >=20/32 and breakage
<=2/32. Freeze the first qualifying cell in the listed arm order for the next
screen (deterministic tie-break, no subsequent screen authorized here). Otherwise
report the dose curve. If any first-k-only cell reaches JS >=20/32, read this as
the language decision being made in the first tokens and sustained bias driving
syntax breakage; report the actual paired breakage change to qualify that reading.
This comparison retains biased prefill and its KV effects: it does not isolate
decode-only causality or prove a general mechanism.

Token boundary: prefill predicts generated token 1 and uses bias, exactly as 40b.
The forward predicting token j uses bias iff j<=k; forwarding token k to predict
token k+1 is OFF. Count generated tokens including fence pieces, not code tokens.
Sustained uses bias on all prefill positions and decode calls. Same cached prompt
effects persist after OFF. Trace every prediction forward and its active state.

Score using unchanged 40b Python/Node parsers, coarse task check and breakage
flags. Report first token, first three tokens and fence labels; breakage by all
three task families; separately count replies containing JavaScript => arrows
and -> neighbours. Arrow reporting does not repair/change the coarse checker.
Thresholds use valid unbroken JS, not fence labels or coarse task success.

Explicit interpreter: PYTHONNOUSERSITE=1 .venv/bin/python -s -B; require
transformers==5.16.1 imported from .venv. Assert real router tuple slot 0 equals
F.linear(hidden_states, weight) before bias; test consumer/OFF and token boundary
on CPU, then assert raw-slot contract on every model layer before generation.

Expected cost from 40b: 314.04 s load + 128*(6194/224)/15.05 = 549.22 s;
25% reserve gives 686.52 s (<15 minutes). Capped conservative projection:
(314.04 + 128*64/15.05 + 128)*1.25 = 1232.95 s (<0.5 GPU-h).
GPU allocation includes load/kernel checks and cleanup; cooperative per-forward/
per-token deadline, no signals. Foreground only. Poll check41b/check42 RUNNING.flag
and GPU availability every 300 seconds; publish our own RUNNING.flag only while
running and remove after. No process termination, background launch or push.

## Results

PENDING.
