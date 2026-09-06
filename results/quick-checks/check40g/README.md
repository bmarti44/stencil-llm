# Check40g — INVALID: JavaScript positive control failed

Unregistered, disclosed follow-up. **3/8 JavaScript**, below the frozen **6/8**
positive-control gate; the other **5/8 were valid Python**, with **0 broken**.
As required, all further inference stopped. **Generality beyond Python/JavaScript
remains unknown; this run neither supports nor refutes it.**

| Pair / measurement | Reading | Evidence |
|---|---|---|
| Frozen JS alpha3 in40e harness | INVALID | JS3/8, Python5/8, broken0/8 |
| Python → TypeScript | INVALID / not run | Dose and fence-position diagnostics gated off |
| JSON → SQL | INVALID / not run | Corrected fixtures frozen; competence and SET not run |
| Python → Go | INVALID / not run | CPU toolchain checks passed; fresh competence/profile, SET and release not run |
| Router release generality | Unmeasured | Go SET prerequisite never reached |

The control is exactly1.5×40c's committed selected-bias tensor, alpha3 with
Frobenius norm15.65956497, sustained through prefill/decode at all48 layers.
Input token IDs match the corresponding committed40e OFF records8/8. The separate
40c syntax/coarse scorer agrees8/8 with the40e-based executable scorer; no arrow
function or scoring ambiguity accounts for the failed gate. JavaScript appeared
on P1_screen_01,02,04; Python on00,03,05,06,07. Prior40e OFF was Python8/8.

Consumed top8 sets changed on 22699/32640 (69.54%) prefill layer-token observations
and 8143/10128 (80.40%) decode layer-token observations, with zero consumer mismatches.
These compare biased/unbiased dispatch at the same current hidden state; they
are not counterfactual OFF-trajectory comparisons. All48 layers were recorded for
every generation. Kernel verification passed: grouped_mm adopted, measured parity
error0, exact OFF next-token restoration, and nonzero dispatch/output changes.
The actuator was applied; the40c success rate did not carry to this40e task/prompt
harness. The prompt and arithmetic values differ from40c; this control does not
isolate which difference causes the reduced response. Prior committed results stand.

Go1.27.1 linux/arm64 installed without root at
`$HOME/.local/lib/check40g-go/go`; official tarball SHA256 verified against
[Go's download metadata](https://go.dev/dl/?mode=json). CPU `gofmt` and `go vet`
passed. CPU preparation passed288 canonical cases, negative fixtures, the real
routing consumer, and paired/release decision boundaries. No Go model outcomes.

One model load,8 actual generations,219 generated tokens; allocation including
load/kernel/scoring/cleanup **396.984/3600 seconds
(6.62 GPU-minutes)**; peak allocated57.653GiB.
Foreground pipeline raw exit0; own flag removed; no signals, fitting, training,
benchmark/sealed-input reads, or push. Data lineage: only the fixed first8 committed
40e P1 screen tasks evaluated; all planned new profiling/evaluation gated off.
Recipe commit `c4dca2e5` predates inference. TS16 diagnostics were explicitly frozen
as insufficient to establish the literal20/32 generality bar; none were run.

Evidence: [prewritten reading](prewritten-reading.md), [records](records.jsonl),
[summary](summary.json), [control comparison](control-comparison.json),
[CPU audit](audit.json), [audit source](audit.py), [recipe hashes](freeze.json),
[CPU/toolchain checks](cpu.json), [kernel](kernel.json), [raw log](run.log).
