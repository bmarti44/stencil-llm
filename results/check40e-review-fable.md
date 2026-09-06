# Check 40e accuracy review (fable, one round)

Scope: commit 77dca63e, `results/quick-checks/check40e/` (README, P1-profiles.pt,
profiles/*.pt, P1-profile-statistics.json, banks.json, records.jsonl, freeze.json,
kernel.json, cpu.json, audit.json/py), `scripts/focus_check40e.py` and the
inherited `focus_check40.py` hook/engine; compared against
`check40b/profiles.pt`, `check40b/frozen-biases.pt`, `check40c/selected-bias.pt`
and `results/check43-review-fable.md`. CPU only; no model launch; no sealed
benchmark file read. All numbers below recomputed from the raw artifacts.

## Verdict in one line

Both readings are correct as measurements (P1 NOT, P2 INELIGIBLE), P1 is **not**
a dose-scale artifact this time (the TypeScript direction is norm-matched to the
JavaScript direction within 7%), P2 is a **prompt defect**, and generality of
router-bias language induction beyond Python -> JavaScript is currently
**unknown, not negative**: P1 lacks the positive control that would make its
zero interpretable, and P2 was never run.

## (a) P1, Python -> TypeScript

1. **Norm versus the 40b/40c JavaScript direction (same convention).**
   Both runs use `make_biases`: centered = side mean minus two-side mean, all
   48 layers, no normalization. Unit-direction Frobenius: TS (40e) **5.583** vs
   JS (40b) **5.220**, ratio 0.935. Alpha-3 bias norm: TS **16.75** vs 40c's
   alpha-3 JS cell (the 32/32 flip) **15.66**; 40b's alpha-4 JS 20.88. Per-layer
   JS/TS unit-norm ratio 0.70-1.22, median 0.90 (TS is slightly *larger* in
   most layers). Max per-expert shift at alpha 3: TS 2.82 vs JS 2.79. The 40e
   dose is therefore at or slightly above the dose that flipped JS 32/32.
   **P1 is not a dose-scale artifact.** The check43 diagnosis does not carry.
2. **Extraction statistic.** `profiles()` (script lines 424-466) teacher-forces
   each of the 32 cued competence replies with `capture_slice` starting at
   `len(input_token_ids)`, pools raw router logits at all generated non-EOS
   positions, token-weighted (TS replies 32-35 tokens, Python 25-28). Same
   generated-code-token statistic as 40b (20-22 tokens per reply there). The
   audit reproduces per-task sums against the saved replies (`audit.py` line
   104). Same model and prompts: the 40e Python mean and the 40b Python mean
   have per-layer cosine >= 0.9986 (Frobenius 423 vs 418), so the two runs are
   directly comparable.
3. **Was the bias applied?** Yes. Every screen record carries the arm's
   `bias_sha256` (correct 9b2c750c..., swapped 0b89a2fb..., shuffled d4935bc1...,
   OFF/text-cue None), each recomputed here from `P1-profiles.pt['biases']`
   and matching 32/32 per arm. `engine.generate` sets `h.bias` before prefill
   and clears it after the last decode step (focus_check40.py ~910/971), the
   same sustained path 40b/40c used; `kernel.json` verified changed dispatch
   under a nonzero bias on the real consumer. Direct evidence the bias reached
   the forward pass: generated token sequences differ from the paired OFF reply
   on correct 3/32, swapped 5/32, shuffled 9/32 (first divergence at generated
   index 12-18, inside the expression). The three correct-arm divergences are
   all TypeScript-style formatting inside Python (`return ((70*67)+(43*58))`
   with the extra outer parentheses, `(44 + 72) * (86 - 83)` with spaces, i.e.
   exactly the style of the TS competence bodies). So the bias acted on the
   code body and left the fence-label decision (generated token 2: `python`
   id 12669 vs `ts` id 2576) untouched 32/32.
4. **Route changes.** Not instrumented: unlike check43, 40e records carry no
   per-layer dispatch counts, so changed-route fractions cannot be recomputed
   from artifacts. Static proxy: adding the alpha-3 TS bias to the Python mean
   profile swaps 136 experts out of the per-layer top-8 sets across 48 layers
   (2.8/layer); the 40c alpha-3 JS bias does the same on the 40b Python mean
   for 104 experts (2.2/layer). By this proxy the TS bias disturbs routing at
   least as much as the JS bias that flipped 32/32.
5. **Collinearity with the JS direction.** Global cosine(TS dir, JS dir) =
   **0.756**; per layer 0.23-0.92 (lowest in layers 34-39 and 47). Decomposed,
   the TS direction has a component of 4.22 along the JS axis (81% of the JS
   direction's own 5.22) plus an orthogonal component of 3.66. If the flip
   were carried by the shared component alone, alpha 3 TS would deliver about
   an alpha-2.4 JS-equivalent dose, and 40c alpha 2 already flipped 25/32.
   Instead the fence label did not move once. That is genuinely surprising,
   and the artifacts cannot resolve why: candidates are (i) the flip is carried
   by the JS-specific (non-shared) component, (ii) the orthogonal TS component
   (type-annotation / `: number` / `ts` fence tokens) counteracts at the fence
   position, (iii) a harness difference invisible in the records. (iii) is not
   excluded, because 40e never ran the 40b/40c JS direction inside its own
   harness as a positive control. Without that control, P1's zero is a real
   negative for *this* TS direction at *this* dose but says nothing about
   whether a TypeScript address exists.
6. **Top-8 overlap** mean 75.52% recomputed from `P1-profile-statistics.json`
   (40b: 80.73%); the >90%-every-layer gate is correctly False.

## (b) P2, JSON -> SQL

1. **Prompt defect, not checker defect.** The user prompt (banks.json /
   `bank()` line 174) reads `Table items (columns id, value):` followed by the
   JSON rows. The word `items` is never marked as an identifier, and the
   SQL cue says only "Answer with a SQL query instead of a row list". All 16
   SQL replies are `SELECT * FROM table WHERE value <op> <threshold>;` with the
   correct predicate 16/16 (verified against each task's op/threshold), so the
   model understood the filter and did not understand the table name.
2. **Checker is correct to reject.** `table` is a reserved word in SQLite;
   `SELECT * FROM table ...` is a syntax error there, so relaxing the regex to
   accept `table` would not make the replies executable. Quoting/rewriting the
   identifier would be a checker-side rescue and was rightly not applied.
3. **One-line fix.** Replace the prompt header with
   `SQL table name: items (columns id INTEGER, value INTEGER). Rows:` and keep
   the cue; optionally strengthen the cue to "Answer with one SQL query against
   the table `items`". Either makes the identifier unambiguous without leaking
   the answer.
4. **A second P2 problem the README does not name.** The JSON default is
   itself weak on boundaries: OFF 25/32 correct, 7/32 broken, all seven on
   `>`/`>=`/`<=` thresholds equal to a row value (off-by-one, e.g. `>97`
   returned 98 and 97). JSON competence was 15/16 for the same reason. The
   frozen GENERALIZES rule requires correct-arm breakage <= 2/32 in absolute
   terms, while the OFF baseline already breaks 7/32; a perfect language flip
   with unchanged boundary competence would fail the gate. The follow-up should
   either use strict/non-boundary thresholds (threshold strictly between the
   sorted values) or make the breakage gate paired relative to OFF.

## (c) Go and the TypeScript choice

`which go gofmt rustc cargo` returns nothing; no `/usr/local/go`; `cpu.json`
records `go: null, gofmt: null`. Node v22 and the global `typescript` library
(sha f3165207...) are present, and the TS checker (parse, require annotation,
transpile, execute) is real. TypeScript was the authorized fallback per the
prewritten reading and ledger line 212. It is, however, the weakest possible
transfer test: TS bodies are JavaScript bodies plus `: number`, so a TS
direction shares 76% of its content with the JS direction and cannot show
a *different* language family. Rust is also unavailable (no rustc). Go can be
installed from the official tarball without root in a few minutes and gofmt
gives a free syntax checker; that is the family test the brief wanted.

## (d) Cheapest follow-up (one GPU run, ~20 min including a ~6 min load)

Norm-matching the TS direction is **not** the follow-up: it already is
norm-matched. Run instead, in the 40e harness with dispatch counts recorded
per record (the check43 instrumentation):

1. Positive control: 40c's frozen JS bias (`selected-bias.pt` x 1.5 = alpha 3)
   on the first 8 of the 40e P1 screen tasks (8 gens). If it does not flip
   >= 6/8 here, P1 is a harness result and everything else waits.
2. TS dose curve: correct arm at alpha 4.5 and 6 on 16 tasks (32 gens), with
   breakage tracked; and a fence-position TS direction (re-teacher-force the
   same 32 competence replies, pool only generated tokens 1-3, ~1 min) at
   Frobenius scaled to 15.7, 16 tasks (16 gens). This separates "the address
   exists but the body-pooled direction misses the decision position" from
   "no address at this actuator".
3. P2 with the prompt fix from (b) and non-boundary thresholds: competence
   32 gens; if SQL >= 14/16, profiles (32 teacher-forced) and the five arms on
   16 tasks (80 gens).
4. If Go is installed before the run, add Python -> Go competence (32 gens)
   so a real cross-family pair is profiled in the same load.
   Total about 200 generations at ~30 tokens each plus 64 profile forwards:
   roughly 8-10 GPU-min of compute on top of the load.

## What the README should say

- Add the magnitude context so the table is not read as a decisive null: TS
  unit direction 5.58 vs JS 5.22; alpha-3 bias 16.75 vs the 32/32 JS cell's
  15.66; cosine 0.756 between the two directions.
- State that no positive control (JS direction in this harness) was run and
  that dispatch counts were not recorded, so the P1 zero is uninterpreted.
- Report the token-level evidence that the bias acted (3/5/9 of 32 replies
  diverge from OFF, TS-style formatting inside Python).
- Name the JSON boundary weakness (7/32 OFF broken) and the absolute breakage
  gate it would collide with.
- Replace "does not establish a universal skill selector" with the plain
  statement: **generality beyond Python -> JavaScript is currently unknown;
  this check neither supports nor refutes it.**
