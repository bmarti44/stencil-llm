# Independent adversarial self-audit of the frozen larger test — Astra, 2026-09-07

Author: gpt-6-astra, the experiment's author, acting as the explicitly requested self-auditor. This is not author-disjoint review. I did not read or coordinate with the independent larger-test Opus review. CPU-only saved-artifact analysis; no generation, bank instantiation, data/bench reads, GPU/container/flag access, process signals, code changes, or frozen-artifact changes. Only this report is written. Short artifact filenames below refer to `results/larger-test/` unless otherwise specified. Current user scope and Amendment 5 govern; the missing root PLAN/plan PROTOCOL were located in archive, and the ledger was read, not edited under the one-file restriction.

**The frozen result is correctly FAIL. Delivery has strong positive evidence; the conjunction failed on a real observed excess of failed editing episodes. The design does not identify a register-specific cause of that excess. Calling the entire result “positive,” or dismissing the failures as merely a bad gate, would repeat my previous overclaims.**

## 1. Accounting and integrity

I independently checked the saved bytes, rather than trusting audit.json's booleans.

- **3,328 unique expected keys exactly:** R/N/T each 1,024 = 64×16; Q 256 = 16×16; no duplicate, missing, unexpected ID, arm, or turn. All 52 frozen concurrency-four groups match the registered order, with Q only on 00–15. Sources: `results/larger-test/freeze.json:4`, `scripts/larger_test.py:207`, `src/stencil/focus/slab2_endpoint.py:235`; arm JSONL line 1 through 1024 (Q through 256).
- All 3,328 rows match their saved raw records field-for-field. All 3,328 HTTP completions match text, generated IDs, EOS, finish reason, token counts, prompt length, text SHA256, token/EOS SHA256 and same-run receipts. Independently verified **4,960/4,960 local-file hashes and sizes, and 3,344/3,344 receipt-file hashes and sizes**. The latter includes 16 determinism receipts, not another 16 evaluation observations. Evidence indexes: `results/larger-test/local-hashes.json:1`, `receipts-hashes.json:1`, `audit.json:1`; actual consumer correspondence: `report.py:42` and `:50`.
- Frozen commit **95fa7fc0c006518ef84c1ea20c152c079ae1798a** has author and committer time **2026-09-07 09:00:01 UTC**. Its registration is byte-identical to the saved registration. All **11** frozen source hashes match both Git objects at that commit and the isolated `/tmp/stencil-larger5-pinned` source files. `pin-verification.json:2`, `launch.json:40` identify that pin; frozen runner `scripts/larger_test.py:256` checks HEAD, tracked cleanliness, module locations and hashes before its bank call. This supports “the frozen SHA ran” under the repo's trusted-but-fallible audit model; it is not independent hardware attestation.
- Bank-open receipt time **1788771778.7459795 = 09:02:58.745980 UTC** follows registration. First evaluation request begins **09:11:41.176158 UTC**; earliest completion ends **09:11:47.327766 UTC**. Thus registration precedes first request by **700.176 seconds**. `evaluation-opened.json:2`, `records-R.jsonl:1`, `records-R.jsonl:49` and the record timing census support this ordering. Source `scripts/larger_test.py:276` rejects an existing marker and calls `bank(family="eval")` once at `:285`; its same objects feed execution and collection. One marker, one scheduled execution and one matching receipt per key support **one model pass**. Absence of an undisclosed earlier opening cannot be proved from a self-written marker alone. I did not reopen the generator or its bank to “verify” this claim.
- **The verdict is from the frozen consumer, not hand-written arithmetic.** `scripts/larger_test.py:193` persists records first, `:200` calls frozen `larger_reading()`, and `:203` writes the summary. I imported only the side-effect-free frozen endpoint with bytecode writing disabled, reconstructed minimal schedule objects from saved R journal events plus saved applicability, and obtained **exact dictionary equality with summary.json**, including its frozen final-success field. No bank was instantiated; this verifies the saved schedule/consumer path, not a fresh independent reconstruction of hidden test semantics. `summary.json:2` is FAIL; `:4041` gives excess 6. Only failed clause is `slab2_endpoint.py:300`; completeness and CPU control pass.
- Independently reconstructed all **276** saved compact R registers from journal events/defaults/generations using frozen Register/renderer code; all text hashes match the registered control, no delivery row or `trailer delivery=` substring. Coverage is 64 episodes. Independently reconstructed the **35** historical registers too: exact versions and text hashes agree with their saved pilot-7 targets (`composition-control.json:3`, frozen `scripts/larger_test.py:44`). Neither control establishes historical-context cleanliness.
- Server log has **3,384 successful completion calls = 3,328 main + 16 determinism + 40 replay**. `server.log:8` records bf16, TRITON_ATTN, context 32768 and max sequences 4; `launch.json:14` records batch invariance and `:17` the pinned image digest. `server.log:5944` records shutdown. No cap in any main record; max prompt+cap **12,047+2,048=14,095**, below 32,768. GPU-held **24,660.9007065 seconds = 6.8502501963 hours**; main tokens **844,905**, all phases **855,284** (`cost-audit.json:2`, `:20`). These are verified saved receipts, not current infrastructure inspection.

### Recomputed primary

Each event is selected by schedule, not a later successful write; the episode contributes one averaged sign. Exact fractions were used before testing. I separately recomputed the gains/sign tails from record satisfaction flags and the saved change lists; frozen consumer reconstruction also reproduces those lists from journal events. Holm is across all three registered families, not just the two that look favorable (`slab2_endpoint.py:16`, `:79`, `:95`, `:123`).

| Family | Paired episodes | R wins / N wins / ties | Mean paired gain | Exact one-sided p | Holm p | Missing-write-as-failure gain |
|---|---:|---:|---:|---:|---:|---:|
| delivery | 64 | 40 / 0 / 24 | 0.625 | 9.094947017729282e-13 | 2.7284841053187847e-12 | 0.625 |
| format | 58 | 24 / 9 / 25 | 0.25862068965517243 | 0.0067654934246093035 | 0.013530986849218607 | 0.234375 |
| indent | 54 | 9 / 5 / 40 | 0.037037037037037035 | 0.21197509765625 | 0.21197509765625 | -0.0703125 |

These reproduce `RESULTS.md:9`. Delivery is **64/64 vs 24/64** at its measured changes, with no R/N missing-write denominator loss there. It measures reporting the effective delivery value, not completing the code task. The constant-ready explanation is not supported: across all scheduled verbose, delivery-scoped rounds whose journal applicability requires draft/staged, R is **252/252** compliant and N **176/252**. These are descriptive round counts, not independent inference or a replacement primary; the common system example can still interact with reminders/history. The literal request and answer pair at `records-R.jsonl:4` and `local/main/slab2-eval-00/R/loop.jsonl:4` is one non-default witness.

### Cross-run control and the primary's margin

All **40/40** old pilot-7 files match their pre-frozen file hashes; old/new request JSON is identical and matches each frozen request hash. Text, generated token IDs and finish reason all agree. Thus **0/40 divergence; all eight within-episode rates 0/5; 0/8 any-divergence episodes**. Control receipts begin at **1788784865.2239985**, after T28–31 ended at **1788784865.221665**, and end **1788785254.213042**, before the next group begins at **1788785254.2296455**. This is the registered midpoint replay, not a substitute second evaluation pass (`freeze.json:692`, `reproducibility.json:4`, `scripts/larger_test.py:246`).

The primary's margin survives the **measured** divergence, which is zero. A transparent arithmetic stress check, not a rerun or adjusted result: adversarially reversing 12 of the 40 winning episode signs leaves 28–12 and even the conservative threefold p is **0.0248835051**; 13 reversals yield 27–13 and threefold p **0.0577159624**. This is not an uncertainty estimate or a guarantee against trajectory drift. The 40 R-only fixed DEV prompts are clustered in eight trajectories; they do not bound unseen eval or N/T divergence. The earlier 10/166 cross-start differences remain historical evidence, and cannot be multiplied by 64 and called a number of independent flipped episodes. `RESULTS.md:36` is appropriately qualified.

## 2. Findings: where I could still overstate this run

No critical integrity failure found. The high findings below limit substantive interpretation and successor design; they do not rescind or rescue FAIL.

| ID | Severity | Finding and evidence |
|---|---|---|
| H1 | **high** | **Real editing costs are obscured by describing only rule adherence and the favorable joint-final diagnostic.** R has 13/64 non-write episodes versus N 2/64, specifically 48 versus 2 rejected Python writes. Descriptive final semantic integration is **R 37/64 vs N 44/64**, while the alternative joint rubric is R12/N5. Final integration pairs are R-only1, N-only8, both36, neither19; exploratory exact two-sided p=**0.0390625**, unregistered and unadjusted. Neither test replaces the gate. `records-R.jsonl:44`, `records-N.jsonl:571`, `RESULTS.md:17`, frozen checker `slab2.py:666`. |
| H2 | **high** | **The breakage gate is an operational tolerance, not a calibrated detector of register-specific harm.** T, which has no register block, also fails it. Eight DEV episodes do not establish a sampling/error model for a one-episode margin at n=64. Conversely, T can suffer reminder-induced editing errors: treating it as incapable of *all rendering harm*, then declaring R's failures “not real,” is invalid. Details and negative-control application below. `REGISTRATION.md:11`, `slab2_endpoint.py:294`; my earlier lesson `full-program-review-astra.md:164`. |
| H3 | **high** | **Late indentation changes cause authentic syntax failures; repeated recovery attempts are not independent harms.** All R non-writes are syntax errors, principally indented top-level definitions or inconsistent indentation. Zero envelope-rejection/cap non-writes. This is not evidence that the old two-fence/parser bug recurred. It is a related history/recovery failure pattern with a different immediate cause. See complete episode census below and `slab2.py:525`. |
| H4 | **high** | **The experiment cannot isolate register representation from restatement, length, version/tombstone text and accumulated context.** R vs N changes all of these. T's current values are oracle-correct but its compact-format delivery prose is uncomposed; it also repeats stale “Not binding” text. `slab2.py:348`, `renderer.py:79`, `loop.py:363`. T29 breakage does not prove that rendering is harmless; R20 does not prove the structured block caused six extra failures. |
| M1 | medium | **Conditional denominators differ materially.** Own-arm written-change event counts (R/N/T/Q) are delivery64/64/62/16, format58/64/59/16, indent105/126/99/32; measured-episode counts are delivery64/64/62/16, format58/64/59/16, indent54/64/54/16. The paired primary has 64/58/54 episodes, and its indent gain reverses under missing-as-failure. Own-arm means in `RESULTS.md:26` are not paired treatment effects. No conditioning on a successful later recovery is permitted. |
| M2 | medium | **The displayed “joint final” is not the frozen joint-final field.** Frozen all-four-raw-satisfied totals are **R0/N0/T0/Q0**; the report's applicable-diagnostic rubric gives **R12/N5/T14/Q0**. This is disclosed at `RESULTS.md:13`, but “its stricter definition” suggests a simple nested metric. Frozen code requires all raw flags; report additionally requires a write and no wrong-family/breakage diagnostic (`slab2_endpoint.py:279` vs `report.py:142`). The definitions are not universally ordered. The change was committed in **7be6e488 at 09:06:43 UTC**, before first eval output, so it is not supported as an outcome-selected rescue; it is still a post-freeze descriptive metric change. Report both definitions by name, not a generic “final success” improvement. |
| M3 | medium | **Some measurements are not arm-neutral estimands even where the checker code is shared.** Indent measures `changed_code(last_parsable, code)`, not a common fixed set of changed definitions; different arm histories/re-emission choices change the measured widths. Missing-write conditioning further selects different samples. Q gets fresh gold files and no feedback/history, whereas R/N/T accumulate their own files/errors. T's format treatment differs from R's. `slab2.py:540`, `:620`, `composition_pilot5.py:186`, `RESULTS.md:22`. |
| M4 | medium | **Breakage is not all semantic failure, and adherence is not competence.** Public/runtime exceptions and syntax/parser/resource failures set breakage; wrong returned values and missing functions can fail integration without it. All 12 shared state-machine episodes break at t0, before the primary completion event, yet still contribute valid delivery-report measurements. `slab2.py:555`, `:563`, `:682`, `:694`. Strong delivery evidence on already broken trajectories is legitimate for that endpoint and weak evidence for useful coding. |
| M5 | medium | **The evaluation is 64 episodes from a small authored grammar, not 64 independent task families or external workloads.** IDs00–47 cycle four domains (12 each), IDs48–63 all use aggregate reduction. Rule templates/orderings, model, backend and system example are shared. The episode sign test implements the registered unit; independence/exchangeability across these authored instances is an inferential assumption, not proven by distinct IDs. `slab2.py:148`. Token/turn/file counts are audit denominators only. |
| M6 | medium | **“Opened once,” “no source changed,” and timing of discoveries must be bounded to evidence.** The source/hash/receipt chain strongly supports the recorded execution; it cannot prove historical absence of unlogged reads or temporary changes. The report-note commit supports pre-output clarification, whereas narrative alone would not. Registered raw HTTP/journals remain local: hashes enable verification but not reproduction from Git alone (`RESULTS.md:40`, `:44`). |
| L1 | low | **Compact-ready is a literal substring flag anywhere in the output, not parsed delivery adherence or causal stale-rule use.** `slab2_endpoint.py:274`; do not turn R25/N7/T27/Q16 into “25 relapses” or successful-format counts. The system worked example favors ready in every arm (`slab2.py:71`). |
| L2 | low | **Shared raw outcome labels remain traps.** R/N/T `success` is null with floor pending while Q populates it; `language=written` does not test general Python competence. `slab2.py:608`, `:628`; actual reported metrics use the explicit checker flags instead. |
| L3 | low | **Fixed R→N→T execution order within each chunk is not counterbalanced.** Registered grouping is followed, and the midpoint replay is reassuring, but arm, prompt length and within-chunk time are not experimentally separated. Do not call the design randomized or the control universal. `REGISTRATION.md:15`, `groups.json:1`. |

Applied earlier lessons explicitly: envelope/real-consumer/recovery lessons led to checking every rejected output's Python syntax rather than trusting “executed”; unit/denominator lessons led to episode tests and both missingness readings; gate lesson led to DEV and T negative-control checks; semantic/style separation led to final integration versus joint success; vacuity lesson led to retaining the nonempty-width condition; freeze/lineage lessons led to hashes/times and no bank regeneration; restart lesson led to payload-level comparison with episode clustering; causal-overclaim/reviewer-fallibility lessons prohibit “T is worse, therefore rendering caused no harm.” The earlier journal-commit/generic-renderer product bugs are not newly measured by this experiment; no asset-packaging, classifier, actuator or external benchmark claim is licensed. See `full-program-review-astra.md:153` through `:176`.

## 3. All 13 R non-write episodes, and all 20 breakage episodes

“13 non-writes” abbreviates **13 episodes containing 48 non-write rounds**. N has two such episodes and two rounds; T has 19 episodes and 51 rounds; Q has none. All **101** non-write rounds across R/N/T have `category="syntax_error"`; AST parsing the saved fenced bodies reproduces syntax errors. An `executed:true` flag here marks an attempted parse, not a written file. The parser sets it before AST parsing (`slab2.py:523`); invalid code is rejected before disk mutation. Every output nevertheless has a complete code fence/report envelope, and no cap explains it.

The following table classifies every R episode. Turn indices are zero-based; citations are JSONL physical lines. Literal witnesses preserve spaces using JSON string notation; `\n` denotes a real newline in the saved output. They are exact excerpts, not reconstructed or repaired code. Repeated variants and every failed turn are covered; the cited record contains the full literal response.

| Episode suffix | All non-write turns | Cause / literal syntax witnesses | Record lines |
|---|---|---|---|
| 02 | 11,12,13,14,15 | t11,12,13: unexpected indent; `"# policy.py\n    def identity(x):\n        return x"`; t14,15: unexpected indent; `"# policy.py\n  def identity(x):\n    return x"` | `records-R.jsonl:44`, `records-R.jsonl:45`, `records-R.jsonl:46`, `records-R.jsonl:47`, `records-R.jsonl:48` |
| 07 | 11,12,13,14,15 | t11,12,13,14: unexpected indent; `"# policy.py\n   def identity(x):\n       return x"`; t15: unexpected indent; `"# policy.py\n  def identity(x):\n    return x"` | `records-R.jsonl:124`, `records-R.jsonl:125`, `records-R.jsonl:126`, `records-R.jsonl:127`, `records-R.jsonl:128` |
| 12 | 11,12,13,14,15 | t11,12,13,14,15: unexpected indent; `"# core.py\n    def identity(x):\n        return x"` | `records-R.jsonl:204`, `records-R.jsonl:205`, `records-R.jsonl:206`, `records-R.jsonl:207`, `records-R.jsonl:208` |
| 18 | 11,12,13,14,15 | t11,15: unindent does not match any outer indentation level; `"    return x\n\n  def step_3(x):\n    \"\"\"Reset position to 8 on reset; otherwise advance by 1 modulo 9.\"\"\""`; t12,13,14: expected an indented block after function definition on line 5; `"\n    def step_3(x):\n    \"\"\"Reset position to 8 on reset; otherwise advance by 1 modulo 9.\"\"\"\n    result = 8 if x == \"reset\" else (x + 1) % 9"` | `records-R.jsonl:300`, `records-R.jsonl:301`, `records-R.jsonl:302`, `records-R.jsonl:303`, `records-R.jsonl:304` |
| 19 | 11,15 | t11,15: unindent does not match any outer indentation level; `"    return x\n\n  def step_3(x):\n    \"\"\"Count values in the inclusive range [2, 9].\"\"\""` | `records-R.jsonl:316`, `records-R.jsonl:320` |
| 22 | 12,13,14,15 | t12: unexpected indent; `"# core.py\n def step_12(x):\n    \"\"\"Reset position to 5 on reset; otherwise advance by 6 modulo 11.\"\"\""`; t13: unexpected indent; `"# core.py\n def step_13(x):\n    \"\"\"Reset position to 6 on reset; otherwise advance by 1 modulo 7.\"\"\""`; t14: unexpected indent; `"# core.py\n def step_14(x):\n    \"\"\"Reset position to 3 on reset; otherwise advance by 5 modulo 8.\"\"\""`; t15: unexpected indent; `"# core.py\n def step_15(x):\n    \"\"\"Reset position to 8 on reset; otherwise advance by 1 modulo 9.\"\"\""` | `records-R.jsonl:365`, `records-R.jsonl:366`, `records-R.jsonl:367`, `records-R.jsonl:368` |
| 26 | 12,13,14,15 | t12: unexpected indent; `"# core.py\n  def step_12(x):\n    \"\"\"Reset position to 5 on reset; otherwise advance by 1 modulo 6.\"\"\""`; t13: unexpected indent; `"# core.py\n  def step_13(x):\n    \"\"\"Reset position to 3 on reset; otherwise advance by 6 modulo 9.\"\"\""`; t14: unexpected indent; `"  def step_14(x):\n    \"\"\"Reset position to 7 on reset; otherwise advance by 1 modulo 8.\"\"\""`; t15: unexpected indent; `"  def step_15(x):\n    \"\"\"Reset position to 6 on reset; otherwise advance by 1 modulo 7.\"\"\""` | `records-R.jsonl:429`, `records-R.jsonl:430`, `records-R.jsonl:431`, `records-R.jsonl:432` |
| 38 | 11,12,13,14,15 | t11,15: unindent does not match any outer indentation level; `"    return x\n\n  def step_4(x):\n    \"\"\"Reset position to 4 on reset; otherwise advance by 4 modulo 8.\"\"\""`; t12,13,14: expected an indented block after function definition on line 5; `"\n    def step_4(x):\n    \"\"\"Reset position to 4 on reset; otherwise advance by 4 modulo 8.\"\"\"\n    result = 4 if x == \"reset\" else (x + 4) % 8"` | `records-R.jsonl:620`, `records-R.jsonl:621`, `records-R.jsonl:622`, `records-R.jsonl:623`, `records-R.jsonl:624` |
| 41 | 12,13,14,15 | t12,13,14,15: unindent does not match any outer indentation level; `"    return x\n\n  def step_3(x):\n    \"\"\"Service A needs step_3(x) to accept ordered inclusive intervals of width at most 8.\"\"\""` | `records-R.jsonl:669`, `records-R.jsonl:670`, `records-R.jsonl:671`, `records-R.jsonl:672` |
| 45 | 11 | t11: unexpected indent; `"# core.py\n    def identity(x):\n        return x"` | `records-R.jsonl:732` |
| 46 | 14,15 | t14: unexpected indent; `"# core.py\n  def identity(x):\n    return x"`; t15: unexpected indent; `"  def identity(x):\n    return x"` | `records-R.jsonl:751`, `records-R.jsonl:752` |
| 47 | 11,12 | t11: unindent does not match any outer indentation level; `"    return x\n\n  def step_4(x):\n    \"\"\"Count values in the inclusive range [6, 9].\"\"\""`; t12: expected an indented block after function definition on line 5; `"\n    def step_4(x):\n    \"\"\"Count values in the inclusive range [6, 9].\"\"\"\n    result = sum(1 for num in x if 6 <= num <= 9)"` | `records-R.jsonl:764`, `records-R.jsonl:765` |
| 56 | 12,13,14,15 | t12,13,14: unindent does not match any outer indentation level; `"def step_3(x):\n    \"\"\"Sum value times weight over records (zero for empty input).\"\"\"\n  result = 0\n  for record in x:"`; t15: unindent does not match any outer indentation level; `"def step_3(x):\n    \"\"\"Sum value times weight over records (zero for empty input).\"\"\"\n   result = 0\n   for record in x:"` | `records-R.jsonl:909`, `records-R.jsonl:910`, `records-R.jsonl:911`, `records-R.jsonl:912` |

For comparison, N35 t10 (`records-N.jsonl:571`) and N53 t10 (`:859`) both have the same inconsistent top-level indentation: literal `"    return x\n\n  def step_3(x):"`. N53 additionally says `"The service contract requires 3 spaces for indent, but the current code uses 2 spaces. The indentation is not compliant with the contract."` Both recover on their next scheduled turn; there was no experimental retry.

### Complete R breakage census

| Episode | First broken turn | Broken turns | Explanation and first-record citation |
|---|---:|---|---|
| 02 | 0 | 0–15 | State-machine input-shape runtime failure shared with N; retained through t15; also later syntax non-writes above; `records-R.jsonl:33` |
| 06 | 0 | 0–15 | State-machine input-shape runtime failure shared with N; retained through t15; `records-R.jsonl:97` |
| 07 | 11 | 11,12,13,14,15 | Indentation syntax failure; no round-zero breakage; `records-R.jsonl:124` |
| 10 | 0 | 0–15 | State-machine input-shape runtime failure shared with N; retained through t15; `records-R.jsonl:161` |
| 12 | 11 | 11,12,13,14,15 | Indentation syntax failure; no round-zero breakage; `records-R.jsonl:204` |
| 14 | 0 | 0–15 | State-machine input-shape runtime failure shared with N; retained through t15; `records-R.jsonl:225` |
| 18 | 0 | 0–15 | State-machine input-shape runtime failure shared with N; retained through t15; also later syntax non-writes above; `records-R.jsonl:289` |
| 19 | 11 | 11,15 | Indentation syntax failure; no round-zero breakage; `records-R.jsonl:316` |
| 21 | 0 | 0–15 | Interval-validator input-shape runtime failure; R-only versus N, also T; retained through t15; `records-R.jsonl:337` |
| 22 | 0 | 0–15 | State-machine input-shape runtime failure shared with N; retained through t15; also later syntax non-writes above; `records-R.jsonl:353` |
| 26 | 0 | 0–15 | State-machine input-shape runtime failure shared with N; retained through t15; also later syntax non-writes above; `records-R.jsonl:417` |
| 30 | 0 | 0–15 | State-machine input-shape runtime failure shared with N; retained through t15; `records-R.jsonl:481` |
| 34 | 0 | 0–15 | State-machine input-shape runtime failure shared with N; retained through t15; `records-R.jsonl:545` |
| 38 | 0 | 0–15 | State-machine input-shape runtime failure shared with N; retained through t15; also later syntax non-writes above; `records-R.jsonl:609` |
| 41 | 12 | 12,13,14,15 | Indentation syntax failure; no round-zero breakage; `records-R.jsonl:669` |
| 42 | 0 | 0–15 | State-machine input-shape runtime failure shared with N; retained through t15; `records-R.jsonl:673` |
| 45 | 11 | 11 | Indentation syntax failure; no round-zero breakage; `records-R.jsonl:732` |
| 46 | 0 | 0–15 | State-machine input-shape runtime failure shared with N; retained through t15; also later syntax non-writes above; `records-R.jsonl:737` |
| 47 | 11 | 11,12 | Indentation syntax failure; no round-zero breakage; `records-R.jsonl:764` |
| 56 | 12 | 12,13,14,15 | Indentation syntax failure; no round-zero breakage; `records-R.jsonl:909` |

The 12 shared round-zero failures are IDs **02,06,10,14,18,22,26,30,34,38,42,46**. This is not a newly discovered Python sandbox restriction. For example R02 outputs literally `result = 6 if x == "reset" else (x + 5) % 11`, but the saved prompt gives `Public case: [{"position":0,"signal":"step"},5]` (`local/main/slab2-eval-02/R/loop.jsonl:1`). Its branch compares a dict to a string and attempts dict+int. R21 outputs `result = len(x) <= 5 and all(x[i] <= x[i+1] for i in range(len(x)-1))` against public input `{"high":0,"low":0}` (`local/main/slab2-eval-21/R/loop.jsonl:1`), treating an interval mapping as a sequence. The disclosed public examples contain the needed input shape, so these are model mistakes, though better explicit schema prose might prevent them. Their persisted old functions explain later exceptions without 16 independent new mistakes. The executor collapses runtime exceptions to a boolean (`slab2.py:563`); exact exception text was not preserved in those records. The causal diagnosis here comes from literal code and public inputs, not a fabricated saved traceback.

**Decomposition:** R's 20 = 13 round-zero runtime-failure episodes + 7 other episodes with later syntax failure. Six of the 13 non-write episodes are already among the runtime failures, so their additional harm is invisible to an any-breakage flag. N's 14 = 12 shared runtime failures + 2 syntax-failure episodes. Thus the net six is **one extra runtime episode (21), plus seven new syntax episodes (07,12,19,41,45,47,56), minus two N-only syntax episodes (35,53)**. It is neither six separate rendered-block contradictions nor 48 independent failures.

There is historical resemblance to the pilot history-lock family: an initial bad representation persists in generated output/context and normal feedback fails to recover it. But the current immediate defect is invalid Python indentation at late rule changes, not the compact delivery trailer contradiction, malformed report envelope, whole-file append bug, cap exhaustion or cross-backend stop that variously affected the earlier pilots. Collapsing the first four pilots into a single “lock/format artifact family” would repeat the explicit error at `full-program-review-astra.md:160`. R's current compact block passes its CPU control; stale prior blocks still remain. Neither fact makes the rejected writes imaginary.

### Exact paired breakage test and intervals

At the registered episode unit: **R-only8, N-only2, both12, neither42** (`paired-breakage.json:2`; record census above). R31.25% versus N21.875%, paired excess **6/64 = 9.375 percentage points**. The exploratory exact McNemar/binomial test conditions on the ten discordant episodes:

- Two-sided **p = 2×(C(10,8)+C(10,9)+C(10,10))/2^10 = 0.109375**.
- One-sided R-more-breakage **p = 0.0546875**.
- Matched odds ratio **8/2 = 4.0**. Exact 95% Clopper–Pearson interval for the conditional R-only probability is **[0.4439045377, 0.9747892737]**; transforming θ/(1−θ) gives the matched odds-ratio interval **[0.7982524005, 38.6656560797]**.
- An explicit **conservative exact ≥95% interval for the paired population risk difference** is **[-0.0721398984, 0.2448071922]**, or **[-7.214, +24.481] percentage points**. Construction: take 97.5% two-sided exact binomial intervals separately for the two discordant-cell probabilities 8/64 and 2/64, then subtract opposite endpoints. Bonferroni gives ≥95% simultaneous coverage despite their dependence. This is intentionally conservative; it is not the odds-ratio interval mislabeled as a risk interval.

These are post-run explanatory statistics, not new registered decision rules. FAIL remains FAIL; non-significance cannot certify no harm. The narrower operational symptom is also concerning: **13 R-only versus 2 N-only non-write episodes**, no overlap, exact two-sided p=**0.00738525390625**; difference **11/64 = 17.1875 points**. This exploratory, unadjusted test is not a substitute endpoint or proof of register-specific harm.

### Why T is worse, and what that does and does not identify

T's **29 = 15 round-zero runtime episodes + 14 other episodes with syntax failure**. Its **19 non-write episodes / 51 rounds** are all syntax errors, with five episodes overlapping the initial runtime failures. The initial runtime set is the same 12 state-machine IDs plus interval IDs **01,13,21**. Its 14 additional syntax episodes are **00,03,04,12,15,19,20,27,28,36,44,45,47,54**. Example T00 t10 has the same `"    return x\n\n  def step_3(x):"` type of indented top-level definition (`records-T.jsonl:11`; exact full body in that record). This gives nine more broken episodes than R: two more round-zero episodes and seven more new syntax episodes. It has six more non-write episodes but only three more non-write rounds, so counting rounds would conceal the difference in propagation/recovery.

T supplies oracle *values*, not oracle Python output. Its prose does not guarantee that the model correctly reindents an accumulated whole file. It retains generated history, and its current literal format/delivery instructions are not composition-equivalent to R (`slab2.py:348`, `renderer.py:89`). The observed failure types therefore explain the count without invoking corrupt register state. They do **not** establish why the model chose those outputs: wording, recency, contradictory format text, prior examples and full-file edit behavior remain intertwined.

T excludes a **unique register-block explanation** as the only possible source of these failure types. T does **not** exclude harm from rendering/reminding at all: it is itself a rendering/reminder treatment. “T is worse, therefore rendering cannot hurt” is logically false. “R avoids this kind of harm because its block is correctly composed” is also false. To distinguish data structure from restatement, use matched content/history controls in a fresh experiment.

## 4. Was the harm clause well-formed?

**Well-formed as a frozen operational acceptance rule; inadequately calibrated as a test of mechanism-specific harm.** I must not turn those different statements into a retrospective PASS.

Applying the episode-level count rule to the actual eight pilot-7 DEV episodes gives **R3, N3, T3, Q3** any-breakage episodes (`results/quick-checks/composition-pilot-7/main-records.jsonl:1`, complete census). R/N have the same broken DEV set {02,04,06}; T has {00,04,06}, so T-vs-N has one discordance each way. All these count differences are zero. DEV non-write episodes were R1/N0/T0/Q0. Thus **the DEV T negative control would not have failed this clause**. Claiming that it already did would be an arithmetic error. Nor do eight passing DEV comparisons establish a good 64-episode margin.

At the actual 64-episode unit, **T−N = 29−14 = 15 > 1**: substituting the block-free oracle-prose arm into this *harm clause alone* fails it. T cannot suffer a register-block/version-store defect because it renders no register block; it can suffer the broader mechanism of repeated instruction rendering. This is the pertinent negative-control distinction. N against itself necessarily gives zero and is only a tautology, not a calibration experiment. Q also has 7/16 breakage against N4/16 on the same first 16 IDs, but applying that count comparison is descriptive only; Q is not a 64-episode eligible substitute and uses gold workspaces.

The rule never specified an acceptable sampling false-rejection rate or established noninferiority. The tolerance of one at n=64 is **1.5625 percentage points**. One at n=8 would be 12.5 points; carrying a fixed count to a larger bank is not rate calibration. Illustratively, with ten discordant pairs under a symmetric null, the clause fails when `2X−10>1`, whose conditional probability is **P(Binomial(10,.5)≥6)=0.376953125**. That is not a claimed empirical error rate for this run; it shows why a practical count cutoff must not be sold as a significance test. A strict product tolerance may deliberately reject such a draw, even without statistical evidence of a population harm.

**My plain answer: the FAIL reflects a real observed cost against a tight registered bar, not a demonstrated merely mis-set bar.** Forty-eight actual writes were rejected and R finished with seven fewer semantically integrated episodes. It would be dishonest to erase those because T was worse or breakage p exceeds .05. Equally, the gate is **mis-specified if advertised as isolating harm from the register data structure**: its negative comparator T also fails, and the intervention bundles other differences. The causal attribution and population size of the cost remain uncertain; the frozen operational failure does not. My earlier pilot-7 lesson is to calibrate the intended *claim* with the right negative control before freezing, not to invalidate any failed tolerance after observing a favorable primary.

## 5. Exact claim sentences

Section 4 of `results/full-program-review-astra.md:184` explicitly made its suggested abstract conditional on verified PASS. That abstract cannot now be pasted in unchanged. The result is **negative for the preregistered conjunction, positive for the named delivery endpoint, and inconclusive about register-specific causal harm or net generalized utility**. “Inconclusive experiment” alone would conceal that a complete registered test delivered a definite FAIL. “Positive experiment” alone would conceal the failed conjunction.

A write-up may contain these exact sentences:

> On 64 preregistered, authored, 16-round Python editing episodes using frozen Qwen3-30B-A3B and gold structured rule events, the register-rendering package improved delivery-value adherence at scheduled changes over retained plain history: 64/64 versus 24/64, with 40 winning, zero losing and 24 tied episode pairs, mean gain 0.625, exact one-sided p=9.094947×10⁻¹³ and Holm-adjusted p=2.728484×10⁻¹² across three obligation families.

> The complete preregistered experiment nevertheless returned FAIL because any-breakage episodes were 20/64 for R and 14/64 for N, exceeding the allowed one-episode excess; this operational failure is not replaced by a post-hoc significance test.

> Format adherence improved on 58 paired written episodes (24/9/25 wins/losses/ties; mean gain 0.258621; Holm p=0.013531), whereas indent had no registered positive evidence on 54 paired episodes (9/5/40; gain 0.037037; p=0.211975), and its missing-write-as-failure gain was negative, −0.0703125.

> R had 13 episodes containing 48 syntactically invalid non-writes, compared with two episodes and two such writes for N; T had 19 such episodes and 51 writes, and its 29 breakage episodes show that these failures are not unique to a structured register block.

> Final semantic integration was descriptively R37/64 versus N44/64 and T27/64; a separately disclosed applicable-trait joint-final diagnostic was R12/64, N5/64 and T14/64, while the frozen all-four-raw-satisfied final field was zero in every arm.

> T's own-written delivery-change adherence was 56/62 versus R64/64, with different measured denominators; this experiment does not establish a register-specific advantage over composition-equivalent current-state prose.

> All 3,328 scheduled records were present and the saved response audit passed; the registered midpoint control found zero divergent responses among 40 fixed R-only DEV payloads spanning eight episodes across the pilot-7 and larger-test containers, and total GPU-held time was 6.850250 hours.

> The evidence supports request-time restatement of current effective obligations in this bounded authored setting, alongside observed editing costs; it does not establish autonomous admission/updating, unique benefit of the register data structure, clean history, general coding improvement or absence of harm.

The write-up may **not** contain:

- “The larger test passed,” “the gate was wrong so this is effectively PASS,” or “an overwhelming primary makes this an unqualified positive result.”
- “The register caused exactly six extra broken episodes,” “rendering is harmless because T is worse,” or “there is no harm because McNemar p=.109375.” The contrast is a package, the interval is broad, and actual failed writes exist.
- “The FAIL was only the old formatting artifact.” The rejected code is syntactically invalid; the one extra R runtime episode is not even an indentation error.
- “R improves final executable coding success, 12 versus 5.” Those figures require the alternative joint rubric; semantic integration alone is 37 versus 44 and the frozen joint field is zero throughout.
- “All three families improved,” “no competence regression,” or “R's indent adherence is better.” The strict indent sensitivity is −0.0703125, with materially different missingness.
- “R beats correct prose reminders” or “the register data structure is necessary.” T is uncomposed and the R/N contrast changes restatement/history/length together.
- “0/40 proves restart determinism,” “64 independent constraint families,” or “3,328 independent tests.”
- “The mechanism removes stale instructions,” “no relapse remains,” “automatic focus from natural conversation works,” “generalized skill selection,” “actuator efficacy,” or “Miller's mechanism is validated.” None is measured here (`full-program-review-astra.md:190`).

## 6. Single most informative successor

**One fresh, matched three-arm representation experiment: structured effective-state rendering versus concise effective-state prose versus ordinary history, on 64 new paired 16-turn episodes.** This directly asks whether the register representation adds anything beyond current-state restatement while measuring the editing cost that now limits the package. No O or Q trajectory matrix, no re-pilot on this spent bank.

Both active renderings must come from the same gold state and include identical applicable obligations, explicit scope and composition policy; no T-only delivery contradiction, extra retired prose or hidden oracle advantage. Use the same neutral system example and explicit input-schema wording in every arm. Choose one declared history policy in advance: retain task/answer history but reconstruct prior user content from the original request so historical injected reminder blocks do not accumulate. Apply that consumer identically in both active arms and document its relation to plain history. This is a new package, not a repaired score for the old one.

Before any model run, CPU-check the real multi-turn consumer on whole-file indentation changes, malformed/recovery replies and mapping-input tasks; deliberately wrong outputs must fail loudly. Freeze a single primary structured-versus-prose contrast on an episode-level **usable change** measure requiring a parsed write, semantic integration and all applicable changed obligations at scheduled changes, with missing attempts counted as failures. Also report delivery separately and episode non-writes/breakage/final integration, with paired intervals. Specify a practically meaningful effect/power target before committing; 64 episodes cannot prove arbitrarily small equivalence or universal absence of harm. Plain history determines whether either active package still provides the expected restatement benefit. Any practical harm margin must be justified prospectively and applied to the reminder negative control at the same episode unit; do not inherit ≤1 by habit. Register fixed cross-start payload controls across arms and report clustering.

**Cost estimate:** 3×64×16 = **3,072 main generations**. Using the completed run's measured R/N/T group times (7,937.074957 + 7,328.790179 + 7,094.902754 seconds), a 25% reserve plus 497.437566 seconds startup and 1,200 seconds control/cleanup gives **8.235666 GPU-hours**. A prospective nine-hour ceiling is plausible, not guaranteed: different history/output length can change timing. Use CPU size checks before freezing and mark a deadline stop INCOMPLETE; never resize from observed outcomes. This audit proposes the design and estimate, not an authorized launch.

**New honest lineage, verbatim:** “Fit-on: none. Development-on: the eight original SLAB-2 DEV episodes, the now-spent 64-episode Amendment-5 evaluation bank and their disclosed audits, plus separately authored successor DEV fixtures. Evaluated-on: a newly authored and prospectively sealed successor bank with new task/schema productions, schedule seeds and literal instances, never previously model-evaluated or used for tuning. Prior failure types informed the successor design; this is a new confirmation of that revised recipe, not an independent confirmation of the untouched original design. No benchmark prompts or responses were used.” Freeze new authorship/exposure and hash manifests before opening it. Reusing the old generator with fresh IDs alone is not an honest claim of new family generalization.

## 7. Literal first non-write responses (audit appendix)

Each block below is the **entire first failed-write output** for one of the 13 R episodes. The earlier table lists all 48 failed turns and exact differing syntax witnesses. These are saved outputs, not model reruns. JSONL citations address the complete output and execution diagnostic together.

<details><summary>slab2-eval-02, t11; results/larger-test/records-R.jsonl:44</summary>

````text
```python policy.py
# policy.py
    def identity(x):
        return x

    def step_4(x):
        """Reset position to 8 on reset; otherwise advance by 1 modulo 9."""
        result = 8 if x == "reset" else (x + 1) % 9
        return result

    def step_5(x):
        """Reset position to 7 on reset; otherwise advance by 3 modulo 10."""
        result = 7 if x == "reset" else (x + 3) % 10
        return result

    def step_6(x):
        """Reset position to 3 on reset; otherwise advance by 5 modulo 8."""
        result = 3 if x == "reset" else (x + 5) % 8
        return result

    def step_8(x):
        """Reset position to 9 on reset; otherwise advance by 3 modulo 12."""
        result = 9 if x == "reset" else (x + 3) % 12
        return result

    def step_9(x):
        """Reset position to 9 on reset; otherwise advance by 4 modulo 13."""
        result = 9 if x == "reset" else (x + 4) % 13
        return result

    def step_10(x):
        """Reset position to 3 on reset; otherwise advance by 8 modulo 11."""
        result = 3 if x == "reset" else (x + 8) % 11
        return result

    def step_11(x):
        """Reset position to 2 on reset; otherwise advance by 1 modulo 3."""
        result = 2 if x == "reset" else (x + 1) % 3
        return result
```
report: task=B status=ok delivery=ready
````

</details>

<details><summary>slab2-eval-07, t11; results/larger-test/records-R.jsonl:124</summary>

````text
```python policy.py
# policy.py
   def identity(x):
       return x

   def step_4(x):
       """Count values in the inclusive range [2, 9]."""
       result = sum(1 for num in x if 2 <= num <= 9)
       return result

   def step_5(x):
       """Count values in the inclusive range [2, 8]."""
       result = sum(1 for num in x if 2 <= num <= 8)
       return result

   def step_6(x):
       """Count values in the inclusive range [2, 6]."""
       result = sum(1 for num in x if 2 <= num <= 6)
       return result

   def step_9(x):
       """Count values in the inclusive range [1, 10]."""
       result = sum(1 for num in x if 1 <= num <= 10)
       return result

   def step_10(x):
       """Count values in the inclusive range [4, 8]."""
       result = sum(1 for num in x if 4 <= num <= 8)
       return result

   def step_11(x):
       """Count values in the inclusive range [4, 10]."""
       result = sum(1 for num in x if 4 <= num <= 10)
       return result
```
report: task=B status=ok delivery=ready
````

</details>

<details><summary>slab2-eval-12, t11; results/larger-test/records-R.jsonl:204</summary>

````text
```python core.py
# core.py
    def identity(x):
        return x

    def step_4(x):
        """Keep multiples of 5, subtract 5 from each, preserve order."""
        result = [num - 5 for num in x if num % 5 == 0]
        return result

    def step_5(x):
        """Keep multiples of 5, subtract 1 from each, preserve order."""
        result = [num - 1 for num in x if num % 5 == 0]
        return result

    def step_6(x):
        """Keep multiples of 6, subtract 7 from each, preserve order."""
        result = [num - 7 for num in x if num % 6 == 0]
        return result

    def step_8(x):
        """Keep multiples of 2, subtract 6 from each, preserve order."""
        result = [num - 6 for num in x if num % 2 == 0]
        return result

    def step_9(x):
        """Keep multiples of 8, subtract 1 from each, preserve order."""
        result = [num - 1 for num in x if num % 8 == 0]
        return result

    def step_10(x):
        """Keep multiples of 8, subtract 7 from each, preserve order."""
        result = [num - 7 for num in x if num % 8 == 0]
        return result

    def step_11(x):
        """Keep multiples of 4, subtract 2 from each, preserve order."""
        result = [num - 2 for num in x if num % 4 == 0]
        return result
```
report: task=A status=ok delivery=ready
````

</details>

<details><summary>slab2-eval-18, t11; results/larger-test/records-R.jsonl:300</summary>

````text
```python core.py
# core.py
def identity(x):
    return x

  def step_3(x):
    """Reset position to 8 on reset; otherwise advance by 1 modulo 9."""
    result = 8 if x == "reset" else (x + 1) % 9
    return result

  def step_4(x):
    """Reset position to 5 on reset; otherwise advance by 2 modulo 7."""
    result = 5 if x == "reset" else (x + 2) % 7
    return result

  def step_5(x):
    """Reset position to 6 on reset; otherwise advance by 1 modulo 7."""
    result = 6 if x == "reset" else (x + 1) % 7
    return result

  def step_6(x):
    """Reset position to 4 on reset; otherwise advance by 8 modulo 12."""
    result = 4 if x == "reset" else (x + 8) % 12
    return result

  def step_8(x):
    """Reset position to 4 on reset; otherwise advance by 2 modulo 6."""
    result = 4 if x == "reset" else (x + 2) % 6
    return result

  def step_9(x):
    """Reset position to 4 on reset; otherwise advance by 1 modulo 5."""
    result = 4 if x == "reset" else (x + 1) % 5
    return result

  def step_10(x):
    """Reset position to 3 on reset; otherwise advance by 2 modulo 5."""
    result = 3 if x == "reset" else (x + 2) % 5
    return result

  def step_11(x):
    """Reset position to 9 on reset; otherwise advance by 1 modulo 10."""
    result = 9 if x == "reset" else (x + 1) % 10
    return result
```
report: task=A status=ok delivery=ready
````

</details>

<details><summary>slab2-eval-19, t11; results/larger-test/records-R.jsonl:316</summary>

````text
```python core.py
# core.py
def identity(x):
    return x

  def step_3(x):
    """Count values in the inclusive range [2, 9]."""
    result = sum(1 for num in x if 2 <= num <= 9)
    return result

  def step_4(x):
    """Count values in the inclusive range [3, 11]."""
    result = sum(1 for num in x if 3 <= num <= 11)
    return result

  def step_5(x):
    """Count values in the inclusive range [7, 15]."""
    result = sum(1 for num in x if 7 <= num <= 15)
    return result

  def step_6(x):
    """Count values in the inclusive range [7, 13]."""
    result = sum(1 for num in x if 7 <= num <= 13)
    return result

  def step_9(x):
    """Count values in the inclusive range [6, 13]."""
    result = sum(1 for num in x if 6 <= num <= 13)
    return result

  def step_10(x):
    """Count values in the inclusive range [5, 10]."""
    result = sum(1 for num in x if 5 <= num <= 10)
    return result

  def step_11(x):
    """Count values in the inclusive range [5, 12]."""
    result = sum(1 for num in x if 5 <= num <= 12)
    return result
```
report: task=A status=ok delivery=ready
````

</details>

<details><summary>slab2-eval-22, t12; results/larger-test/records-R.jsonl:365</summary>

````text
```python core.py
# core.py
 def step_12(x):
    """Reset position to 5 on reset; otherwise advance by 6 modulo 11."""
    result = 5 if x == "reset" else (x + 6) % 11
    return result
```
report: task=A status=ok
````

</details>

<details><summary>slab2-eval-26, t12; results/larger-test/records-R.jsonl:429</summary>

````text
```python core.py
# core.py
  def step_12(x):
    """Reset position to 5 on reset; otherwise advance by 1 modulo 6."""
    result = 5 if x == "reset" else (x + 1) % 6
    return result
```
report: task=A status=ok
````

</details>

<details><summary>slab2-eval-38, t11; results/larger-test/records-R.jsonl:620</summary>

````text
```python core.py
# core.py
def identity(x):
    return x

  def step_4(x):
    """Reset position to 4 on reset; otherwise advance by 4 modulo 8."""
    result = 4 if x == "reset" else (x + 4) % 8
    return result

  def step_5(x):
    """Reset position to 9 on reset; otherwise advance by 3 modulo 12."""
    result = 9 if x == "reset" else (x + 3) % 12
    return result

  def step_6(x):
    """Reset position to 2 on reset; otherwise advance by 5 modulo 7."""
    result = 2 if x == "reset" else (x + 5) % 7
    return result

  def step_8(x):
    """Reset position to 5 on reset; otherwise advance by 3 modulo 8."""
    result = 5 if x == "reset" else (x + 3) % 8
    return result

  def step_9(x):
    """Reset position to 2 on reset; otherwise advance by 4 modulo 6."""
    result = 2 if x == "reset" else (x + 4) % 6
    return result

  def step_10(x):
    """Reset position to 9 on reset; otherwise advance by 6 modulo 15."""
    result = 9 if x == "reset" else (x + 6) % 15
    return result

  def step_11(x):
    """Reset position to 8 on reset; otherwise advance by 4 modulo 12."""
    result = 8 if x == "reset" else (x + 4) % 12
    return result
```
report: task=A status=blocked delivery=ready
````

</details>

<details><summary>slab2-eval-41, t12; results/larger-test/records-R.jsonl:669</summary>

````text
```python core.py
# core.py
def identity(x):
    return x

  def step_3(x):
    """Service A needs step_3(x) to accept ordered inclusive intervals of width at most 8."""
    result = (x['low'] <= x['high']) and (x['high'] - x['low'] <= 8)
    return result

  def step_4(x):
    """Service A needs step_4(x) to accept ordered inclusive intervals of width at most 8."""
    result = (x['low'] <= x['high']) and (x['high'] - x['low'] <= 8)
    return result

  def step_5(x):
    """Service A needs step_5(x) to accept ordered inclusive intervals of width at most 10."""
    result = (x['low'] <= x['high']) and (x['high'] - x['low'] <= 10)
    return result

  def step_9(x):
    """Service A needs step_9(x) to accept ordered inclusive intervals of width at most 10."""
    result = (x['low'] <= x['high']) and (x['high'] - x['low'] <= 10)
    return result

  def step_10(x):
    """Service A needs step_10(x) to accept ordered inclusive intervals of width at most 5."""
    result = (x['low'] <= x['high']) and (x['high'] - x['low'] <= 5)
    return result

  def step_11(x):
    """Service A needs step_11(x) to accept ordered inclusive intervals of width at most 11."""
    result = (x['low'] <= x['high']) and (x['high'] - x['low'] <= 11)
    return result

  def step_12(x):
    """Service A needs step_12(x) to accept ordered inclusive intervals of width at most 8."""
    result = (x['low'] <= x['high']) and (x['high'] - x['low'] <= 8)
    return result
```
report: task=A status=ok
````

</details>

<details><summary>slab2-eval-45, t11; results/larger-test/records-R.jsonl:732</summary>

````text
```python core.py
# core.py
    def identity(x):
        return x

    def step_3(x):
        """Accept ordered inclusive intervals of width at most 8."""
        result = (x['high'] - x['low'] <= 8) and (x['high'] >= x['low'])
        return result

    def step_4(x):
        """Accept ordered inclusive intervals of width at most 10."""
        result = (x['high'] - x['low'] <= 10) and (x['high'] >= x['low'])
        return result

    def step_5(x):
        """Accept ordered inclusive intervals of width at most 11."""
        result = (x['high'] - x['low'] <= 11) and (x['high'] >= x['low'])
        return result

    def step_6(x):
        """Accept ordered inclusive intervals of width at most 9."""
        result = (x['high'] - x['low'] <= 9) and (x['high'] >= x['low'])
        return result

    def step_8(x):
        """Accept ordered inclusive intervals of width at most 13."""
        result = (x['high'] - x['low'] <= 13) and (x['high'] >= x['low'])
        return result

    def step_9(x):
        """Accept ordered inclusive intervals of width at most 12."""
        result = (x['high'] - x['low'] <= 12) and (x['high'] >= x['low'])
        return result

    def step_10(x):
        """Accept ordered inclusive intervals of width at most 6."""
        result = (x['high'] - x['low'] <= 6) and (x['high'] >= x['low'])
        return result

    def step_11(x):
        """Accept ordered inclusive intervals of width at most 13."""
        result = (x['high'] - x['low'] <= 13) and (x['high'] >= x['low'])
        return result
```
report: task=A status=ok delivery=ready
````

</details>

<details><summary>slab2-eval-46, t14; results/larger-test/records-R.jsonl:751</summary>

````text
```python core.py
# core.py
  def identity(x):
    return x

  def step_4(x):
    """Reset position to 5 on reset; otherwise advance by 4 modulo 9."""
    result = 5 if x == "reset" else (x + 4) % 9
    return result

  def step_5(x):
    """Reset position to 6 on reset; otherwise advance by 6 modulo 12."""
    result = 6 if x == "reset" else (x + 6) % 12
    return result

  def step_8(x):
    """Reset position to 6 on reset; otherwise advance by 2 modulo 8."""
    result = 6 if x == "reset" else (x + 2) % 8
    return result

  def step_9(x):
    """Reset position to 6 on reset; otherwise advance by 6 modulo 12."""
    result = 6 if x == "reset" else (x + 6) % 12
    return result

  def step_10(x):
    """Reset position to 8 on reset; otherwise advance by 1 modulo 9."""
    result = 8 if x == "reset" else (x + 1) % 9
    return result

  def step_11(x):
    """Reset position to 7 on reset; otherwise advance by 7 modulo 14."""
    result = 7 if x == "reset" else (x + 7) % 14
    return result

  def step_12(x):
    """Reset position to 7 on reset; otherwise advance by 2 modulo 9."""
    result = 7 if x == "reset" else (x + 2) % 9
    return result

  def step_13(x):
    """Reset position to 7 on reset; otherwise advance by 3 modulo 10."""
    result = 7 if x == "reset" else (x + 3) % 10
    return result

  def step_14(x):
    """Reset position to 3 on reset; otherwise advance by 6 modulo 9."""
    result = 3 if x == "reset" else (x + 6) % 9
    return result
```
report: task=A status=ok
````

</details>

<details><summary>slab2-eval-47, t11; results/larger-test/records-R.jsonl:764</summary>

````text
```python policy.py
# policy.py
def identity(x):
    return x

  def step_4(x):
    """Count values in the inclusive range [6, 9]."""
    result = sum(1 for num in x if 6 <= num <= 9)
    return result

  def step_5(x):
    """Count values in the inclusive range [4, 8]."""
    result = sum(1 for num in x if 4 <= num <= 8)
    return result

  def step_6(x):
    """Count values in the inclusive range [6, 13]."""
    result = sum(1 for num in x if 6 <= num <= 13)
    return result

  def step_9(x):
    """Count values in the inclusive range [7, 16]."""
    result = sum(1 for num in x if 7 <= num <= 16)
    return result

  def step_10(x):
    """Count values in the inclusive range [5, 8]."""
    result = sum(1 for num in x if 5 <= num <= 8)
    return result

  def step_11(x):
    """Count values in the inclusive range [2, 5]."""
    result = sum(1 for num in x if 2 <= num <= 5)
    return result
```
report: task=B status=ok delivery=ready
````

</details>

<details><summary>slab2-eval-56, t12; results/larger-test/records-R.jsonl:909</summary>

````text
```python policy.py
# policy.py
def identity(x):
    return x

def step_3(x):
    """Sum value times weight over records (zero for empty input)."""
  result = 0
  for record in x:
    result += record["value"] * record["weight"]
  return result

def step_4(x):
    """Sum value times weight over records (zero for empty input)."""
  result = 0
  for record in x:
    result += record["value"] * record["weight"]
  return result

def step_5(x):
    """Sum value times weight over records (zero for empty input)."""
  result = 0
  for record in x:
    result += record["value"] * record["weight"]
  return result

def step_8(x):
    """Sum value times weight over records (zero for empty input)."""
  result = 0
  for record in x:
    result += record["value"] * record["weight"]
  return result

def step_9(x):
    """Sum value times weight over records (zero for empty input)."""
  result = 0
  for record in x:
    result += record["value"] * record["weight"]
  return result

def step_10(x):
    """Sum value times weight over records (zero for empty input)."""
  result = 0
  for record in x:
    result += record["value"] * record["weight"]
  return result

def step_11(x):
    """Sum value times weight over records (zero for empty input)."""
  result = 0
  for record in x:
    result += record["value"] * record["weight"]
  return result

def step_12(x):
    """Sum value times weight over records (zero for empty input)."""
  result = 0
  for record in x:
    result += record["value"] * record["weight"]
  return result
```
report: task=B status=ok
````

</details>

**Honest headline: Delivery adherence improved strongly, but the preregistered test failed with excess broken editing episodes.**
