# Check40g prewritten reading

Unregistered, disclosed user-authorized development follow-up, 2026-09-06.
Fit/train: none. Profile-on: committed 40e competence replies for TS; fresh
synthetic 16-task cued competence banks for JSON/SQL and Python/Go, both sides,
all replies without success filtering. Evaluate-on: committed first16 40e P1
screen tasks (disclosed reuse for TS), fresh disjoint SQL/Go screen32 and Go
release168 expressions. No evaluation benchmark or sealed IFEval/BFCL input read.
No fitting, training, checkpoint selection, prompt rescue, or outcome-based tuning.

One bf16 Qwen3-30B-A3B load, inherited40e messages/Engine/greedy cap64,
sustained router bias on all48 layers and prefill/decode. Kernel parity required.
First: 1.5 * committed40c selected-bias (=alpha3 JS) on first8 40e P1 screen;
>=6/8 executable JS required; otherwise INVALID and STOP all inference.
TS: committed40e body direction alpha4.5 and6; first3 generated own positions
(one-based tokens1-3, including fence label) re-teacher-forced from the SAME32
committed competence replies; fence direction total Frobenius norm15.7 at alpha3.
Each TS configuration uses correct/shuffled/OFF/text-cue on first16 P1 screen;
OFF/text-cue shared across configurations. No best-dose selection. These are
16-task diagnostics: report raw counts; cannot meet the fixed20/32 GENERALIZES
bar, and do not silently extrapolate to32. MARGINAL if >=12 addressed successes,
else NOT under the literal reading, explicitly qualified as a16-task diagnostic.

P2 exact header: SQL table name: items (columns id INTEGER, value INTEGER). Rows:
Thresholds are integers strictly between sorted row values; both strict operators
< and >. Cued competence16 each side, >=14/16 BOTH required, then body profiles
and five-arm uncued screen32. Bias=3*(target mean - two-side mean), swapped=-bias,
shuffled seed40062 per-layer expert permutation; profiles token-weighted raw logits.
Go fresh40b-style cued competence16 each side: Python16/16 and Go>=14/16 required;
then same profile construction, scaled at alpha3 to exact frozen JS alpha3 band
Frobenius norm. Five-arm screen32. No inherited overlap veto added to user gates.
Go checker: gofmt parser, restricted zero-argument integer-return function,
optional package line, independently evaluate bounded +,-,* integer expression.
CPU go vet validates canonical functions; no arbitrary generated program executed.
All languages require exact name and arithmetic/table semantics, valid fence and
no truncation. JS positive control uses40e TS parser/transpiler with JS admitted.

Each32-task pair GENERALIZES iff correct addressed skill success>=20/32,
correct-only broken vs paired OFF<=2/32, shuffled addressed success<=4/32;
else MARGINAL iff correct>=12/32, else NOT. Absolute breakage also reported.
No competent screen => INELIGIBLE; interrupted => INCOMPLETE, no null claim.
If Go SET correct>=20/32 with ABSOLUTE broken<=2, run24 retained-history episodes:
Z SET/HOLD Go bias; SWITCH/HOLD_AFTER_SWITCH OFF; BACK/HOLD_AFTER_BACK Go bias;
CLEAR OFF. At SWITCH/BACK/CLEAR mask all preceding assistant bodies, preserve
positions and remaining KV. Zc and S share Z prefix through HOLD_AFTER_SWITCH;
Zc BACK biasOFF, S BACK shuffled; OFF full retained-history baseline.
Use EXACT40i decision function with Go renamed to JavaScript only in its input
count dictionaries: three Z SWITCH/BACK/CLEAR cells>=20 target and<=2 broken,
every Z step<=2 broken, paired switch and clear releases>=20, Zc/S BACK<=4 Go.
Report Go release separately from SET; mechanism generality requires Go closure.

Per-record consumed-dispatch counts/fractions for every layer, prefill/decode,
against unbiased router output at same hidden state (not counterfactual OFF path).
Records journaled immediately; profile statistics/bias tensors saved before screen.
One foreground allocation including load/checks/profiles/scoring/cleanup<=3600s.
Cooperative token deadline reserves cleanup; no process signals or termination.
Maximum generations:8+128TS+32SQLcomp+160SQL+32Gocomp+160Go+480release=1000.
Prior40i measured mean1.924s/generation +load374s; budget estimate with25% compute
reserve and150s profiles/checkers:374+1.25*(1000*1.924+150)=2966.5s. Instrumentation
may cost more: preserve exact task counts, cooperate at deadline and label incomplete.
Flags coordinated under short review lock; no other Stencil compute, pid2705 exempt.
Explicit pathspec commits, results force-added, no push.
