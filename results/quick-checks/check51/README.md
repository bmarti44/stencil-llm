# Check 51 — CONTROL-PASS 8/8, with disclosed protocol deviation

2026-09-07 · gpt-6-astra · recipe/readings frozen before GPU work in `8b73a78b`.

**Completed: CONTROL-PASS, 8/8 mode switches with executable correctness, 54.407/600 GPU-held seconds.** All eight comparisons pass CPU replay. The no-second-look source-read violation below prevents an unqualified protocol-compliance claim.

CONTROL-PASS = >=6/8 switch to mode B with executable correctness preserved: a carrier CAN beat a retained transcript when placed at recency, so check49's SWITCH cell is a placement artifact and the corrected re-run is authorized (fourth text-at-recency arm, output cap96 ->160, spend the registered fitting ceiling).
CONTROL-FAIL = <=3/8: no carrier tested so far can flip a mode against a retained transcript; record that as the finding, and the switch question moves to the register's MASKING contingency (checks40h/40i) rather than to any carrier.
4–5/8 = INCONCLUSIVE at n=8; record and stop. These are practical thresholds, not statistical estimates. A missing call or budget interruption is INCOMPLETE, never CONTROL-FAIL.

## Frozen design and measurements

Exactly eight greedy SWITCH generations: square, negate, lengths and product SETUP families, each Python->JavaScript and JavaScript->Python. The same function name and task repeat with an additive constant2,3,4; only that constant changes. Two CPU-authored correct mode-A answers are supplied as literal assistant history, with check49's neutral exchange before HOLD. No extra history generations are sampled. This instantiates the same SET/HOLD/SWITCH history layout but does not test self-generated prior answers; the two directions within a family are related. Original setup tasks have no changing constant, so these setup-only variants append a fixed additive-offset clause. No task is selected using generated outcomes.

Fit-on=none. Input-on=four check49 setup families and CPU-authored constant variants. Evaluate-on=the eight frozen SWITCH cases in inputs.json. No training, adapter loading, teacher sampling, or benchmark access. Harness reuse is limited to setup(), messages(), render(), execute() and utility functions; prepare(), training(), evaluation(), run() are never invoked. The local frozen bf16 Qwen3-4B uses the same SDPA, nonthinking chat template, greedy cache decode and cap96 as check49. Cap160 belongs to the conditional corrected run, not this probe.

The real production renderer (src/stencil/focus/renderer.py) renders a trusted structured language entry in its active-rules JSON form in the CURRENT user turn immediately before the request. System content stays exactly check49.SYSTEM. No adapter, mask, cache reuse, or transcript deletion. All model parameters have requires_grad=False; inference only. Fresh cache per request.

Success is check49's executable-semantics scorer AND mode-B language AND no cap truncation. Presentation and syntax are also recorded without adding new success gates. "Copied structure" means exact lexical-token equality to the preceding mode-A answer after replacing numeric literals and ignoring whitespace, retaining identifiers, operators and language. This narrow deterministic measurement does not purport to detect all semantic copying. "First divergent token" is a zero-based Qwen token comparison against the CPU-authored retained-transcript continuation (the preceding reference with only constant3 changed to4, plus EOS); it is not a separately sampled counterfactual. Records include token ID, token piece and decoded text on each side, full completion, executable score, structure result and input/output token IDs. Literal messages, references and executable test cases are in inputs.json.

CPU preflight:48 reference executions passed, all8 stale-constant answers fail the SWITCH executable tests, all8 histories and active-rule placements checked. freeze.json binds the runner, inputs, reused harness and renderer. Budget600 GPU-held seconds including load/cleanup; cooperative stop at540s, no new call after500s. Own RUNNING.flag, no signals. No other Stencil flag was present at initial preflight; recheck at launch.

## Protocol deviation — disclosed before inference

A source-range read of scripts/focus_check49.py:100–128 accidentally extended beyond setup() into evaluation() and displayed the first evaluation-generator branches (prefix, rotate, unique, gaps). This violated the user's explicit no-second-look constraint. No evaluation data.json or records.jsonl was opened, no evaluation function was called, and none of those families supplies this probe. The exposed material was not used for task selection or tuning. Nevertheless this run cannot claim a clean no-second-look audit. Preserve the numerical threshold reading, but any CONTROL-PASS must carry this deviation and the authored-history limitation; it cannot silently certify the full original protocol. No corrected experiment is executed as part of this eight-generation check.

## Results

| Setup family | Switch | Emitted language | Executable correct | Copied prior structure | First divergent token (zero-based) |
|---|---|---|---|---|---|
| square | python → js | js | yes | no | 1: `python` (12669) → `javascript` (14073) |
| square | js → python | python | yes | no | 1: `javascript` (14073) → `python` (12669) |
| negate | python → js | js | yes | no | 1: `python` (12669) → `javascript` (14073) |
| negate | js → python | python | yes | no | 1: `javascript` (14073) → `python` (12669) |
| lengths | python → js | js | yes | no | 1: `python` (12669) → `javascript` (14073) |
| lengths | js → python | python | yes | no | 1: `javascript` (14073) → `python` (12669) |
| product | python → js | js | yes | no | 1: `python` (12669) → `javascript` (14073) |
| product | js → python | python | yes | no | 1: `javascript` (14073) → `python` (12669) |

Both directions pass4/4. All8 outputs have recognized syntax, fenced presentation and correct executable semantics; no truncations. All share the opening fence token, then diverge at its language label. The CPU audit rebuilt all8 production-rendered prompts and input token sequences, decoded all completions, reran the original executable scorer, and reproduced all8 structure/divergence measurements without discrepancies. Records occupy20,279 bytes (<10MB).

**Reading:** text at current-user recency CAN overcome these supplied retained same-family answers on frozen Qwen3-4B. This meets the pre-written CONTROL-PASS threshold. Per the user's conditional reading, the corrected check49 design earns a fourth text-at-recency arm, cap160 and the registered fitting ceiling. This check does not fit adapters or execute that follow-up. The placement-artifact interpretation is supported on these setup controls; generalization to the original self-generated evaluation trajectories is unmeasured, and the source exposure means the no-second-look requirement was not satisfied. The result does not measure adapter superiority, nor require the MASKING contingency on this control.

Runtime: load40.752s; total54.407s (0.907GPU-min), peak allocated8,211,945,472 bytes. PyTorch2.13.0+cu130 / Transformers5.16.1. Exactly8 generation calls, no adapters loaded or trained. Process exited normally and removed its own RUNNING.flag; no process signals, container, push, or data/bench reads.

Evidence: [inputs](inputs.json), [records](records.jsonl), [summary](summary.json), [CPU audit](audit.json), [freeze](freeze.json), [runner](run.py), [audit runner](audit.py), [raw run log](run.log). The raw records and pre-GPU freeze are unchanged.
