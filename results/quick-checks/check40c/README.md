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

**POSSIBLE**. Freeze **alpha2_sustained** for the next screen.

| Cell | Valid JS | Valid Python | Broken | Coarse task pass | Truncated | => replies (valid JS / coarse pass) |
|---|---:|---:|---:|---:|---:|---:|
| alpha2_sustained | 25/32 | 7/32 | 0/32 | 32/32 | 0 | 0 (0 / 0) |
| alpha3_sustained | 32/32 | 0/32 | 0/32 | 32/32 | 0 | 0 (0 / 0) |
| alpha4_first3 | 25/32 | 3/32 | 4/32 | 25/32 | 0 | 0 (0 / 0) |
| alpha4_first8 | 26/32 | 0/32 | 6/32 | 25/32 | 0 | 1 (1 / 0) |
| alpha4_sustained_reference | 26/32 | 0/32 | 6/32 | 25/32 | 0 | 1 (1 / 0) |
| OFF_reference | 0/32 | 32/32 | 0/32 | 32/32 | 0 | 0 (0 / 0) |

Breakage by task family (same denominators in every cell):

| Cell | screen_0: ((a+b)*(c-d)) | screen_1: ((a*b)+(c*d)) | screen_2: ((a-b)-(c+d)) |
|---|---:|---:|---:|
| alpha2_sustained | 0/11 | 0/11 | 0/10 |
| alpha3_sustained | 0/11 | 0/11 | 0/10 |
| alpha4_first3 | 1/11 | 0/11 | 3/10 |
| alpha4_first8 | 1/11 | 0/11 | 5/10 |
| alpha4_sustained_reference | 1/11 | 0/11 | 5/10 |
| OFF_reference | 0/11 | 0/11 | 0/10 |

Opening-token and fence counts (literal decoded strings; labels do not determine parser identity):

- alpha2_sustained: first token {"```": 32}; first three {"```javascript\n": 25, "```python\n": 7}; fence {"javascript": 25, "python": 7}.
- alpha3_sustained: first token {"```": 32}; first three {"```javascript\n": 32}; fence {"javascript": 32}.
- alpha4_first3: first token {"```": 29, "solve": 3}; first three {"```dart\n": 4, "```javascript\n": 25, "solve_screen_": 3}; fence {"(bare)": 3, "dart": 4, "javascript": 25}.
- alpha4_first8: first token {"```": 29, "solve": 3}; first three {"```dart\n": 4, "```javascript\n": 25, "solve_screen_": 3}; fence {"(bare)": 3, "dart": 4, "javascript": 25}.
- alpha4_sustained_reference: first token {"```": 29, "solve": 3}; first three {"```dart\n": 4, "```javascript\n": 25, "solve_screen_": 3}; fence {"(bare)": 3, "dart": 4, "javascript": 25}.
- OFF_reference: first token {"```": 32}; first three {"```python\n": 32}; fence {"python": 32}.

Paired first-k comparisons with recorded alpha-4 sustained:

- alpha4_first3: first-k token IDs identical 32/32; broken→unbroken 2, unbroken→broken 0; valid JS→valid Python 1.
- alpha4_first8: first-k token IDs identical 32/32; broken→unbroken 0, unbroken→broken 0; valid JS→valid Python 0.

The fixed early-token JS criterion is met by alpha4_first3, alpha4_first8. Language selection survives turning off the direct bias after those first tokens; the paired breakage counts above measure whether sustained bias adds syntax failures. The dose curve is clean at alpha 2 and 3: zero broken replies in every task family, with alpha 3 reaching 32/32 JS. Both cutoff arms still fail the <=2/32 breakage bar. First-3 fixes two broken -> replies by switching them to Python lambdas, and also switches one valid JS arrow to Python; all four Dart-style invalid replies persist. First-8 retains all six original breaks. Thus early tokens suffice for the observed JS rate, but the evidence does not support assigning all syntax failure to sustained late bias. Alpha 2 is frozen by the prewritten first-qualifying arm order; alpha 3's better descriptive JS count is also reported. Biased prefill and earlier biased KV remain in both cutoff arms; this is not a decode-only causal isolation. This exploratory synthetic task reuse does not test persistence, SWITCH/CLEAR, other skills, benchmark transfer or fresh-task reliability.

The inherited coarse checker remains unchanged and can reject valid arrow assignments. Arrow counts denote replies containing =>; the separate -> counts in summary.json are literal substring counts and can include Python return annotations. Both parser outcomes, flags, first-token IDs, fence labels and forward schedules are retained per reply.

128 new generations, 3850 generated tokens; 64 recorded references copied without regeneration. Allocation **629.25 s = 10.49 GPU-min**, including load (377.61 s), kernel checks and cleanup; cap 1800 s, overrun 0.00 s. Peak allocated 57.65 GiB. CPU reconstruction passes; raw-logit slot equality verified on all 48 layers; grouped_mm dispatch and exact OFF verified. No fitting, training, sealed reads, signals, background launch or push.

**Correction (astra full review, 2026-09-05)**: (F1, F6) Alpha3 was selected after exploratory screen results; a fresh same-family bank yielded32/32 SET, while the originally selected alpha2 yielded6/32. No general dose robustness is established. For checks 40b/40c/40d/41b, the provenance description is “locally frozen before execution according to run receipts”. Their freeze files first entered Git with results; matching local hashes and timestamps do not independently establish pre-outcome Git commitment. Checks 41/40e/43 have pre-generation Git anchors. Some checks 34–38 have launch-copy/hash evidence; check39’s exact reading was committed before its recorded start. These are not all committed preregistrations; no fabricated chronology was found. Biased prefill plus the first few biased predictions can preserve the observed language rate. These arms neither isolate decode-only causality nor establish that sustained late bias causes all breakage.
