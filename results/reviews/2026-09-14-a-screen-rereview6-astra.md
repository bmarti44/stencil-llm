The screen still cannot launch. A silent final interval remains undercharged, and missing spend evidence still permits `GATE PASSED`.

**1. Previous findings**

| Finding | Disposition |
|---|---|
| Interrupted-launch accounting | **PARTIAL** — healthy-ticker examples pass; ticker failure leaves an unbounded tail. |
| Durable budget eligibility | **PARTIAL** — recorded overruns are refused; missing ledgers are accepted. |
| S35 whole-record reachability | **RESOLVED** — both note-reset mutants are emitted and detected. [a_screen_mutate.py:285](/home/bmarti44/stencil-llm/scripts/a_screen_mutate.py:285) |

**2. Remaining accounting and eligibility defects**

- **F13 — high: “intact” describes the recorded prefix, not the final silent interval.** I executed a ledger with ticks through 600 seconds, ticker failure afterward, death at 1,200 seconds, and reading at 1,500 seconds. It charges **780 seconds**, with zero malformed lines. The same ledger could describe death at 600 seconds; heartbeat absence cannot distinguish those histories. I also injected an append failure into the actual ticker: its thread died while the main thread continued. Three intervals of slack provide no termination guarantee. [a_screen.py:655](/home/bmarti44/stencil-llm/src/stencil/a_screen.py:655), [a_screen.py:672](/home/bmarti44/stencil-llm/src/stencil/a_screen.py:672)

  **Fix:** use verified termination evidence for a bounded charge; otherwise account conservatively through the observation time. Do not infer death from silence.

- **F12 — high: a missing or empty ledger becomes zero spend.** On complete synthetic 48-session records, the real summary refuses a status claiming 39 minutes over a 2,701-second ledger. Removing or emptying that ledger changes the verdict to **`GATE PASSED`**. This defeats the independent evidence check through an ordinary missing sidecar. [a_screen.py:621](/home/bmarti44/stencil-llm/src/stencil/a_screen.py:621), [a_screen_summary.py:249](/home/bmarti44/stencil-llm/scripts/a_screen_summary.py:249)

  The over-budget refusal also still prints **12 gate PASS lines** before saying the gates were not read. Only the final verdict is suppressed. [a_screen_summary.py:387](/home/bmarti44/stencil-llm/scripts/a_screen_summary.py:387)

  **Fix:** require a present, nonempty ledger covering the recorded launches, and bypass gate calculation and printing when eligibility fails.

- **Medium: the 45-minute sizing omits the five-minute admission margin.** Using the registered estimates—22.5 seconds per generation and 0.189 seconds per suite—with a three-minute load, the real admission guard refuses request 96 at **2,416.158 seconds**. All 96 requests would finish at **2,439.792 seconds: 40.66 minutes**. The final-start constraint permits approximately **2.73 minutes** of loading and other overhead, not §18.2’s claimed 7.3 minutes. [a_screen_run.py:583](/home/bmarti44/stencil-llm/scripts/a_screen_run.py:583), [REGISTRATION-A-SCREEN.md:1066](/home/bmarti44/stencil-llm/results/a-screen/REGISTRATION-A-SCREEN.md:1066)

  **Fix:** include the five-minute admission reserve in the pilot-derived ceiling calculation before any evaluation arm runs, retaining the registered 16-hour total and reserve-surrender rule.

The reverse risk therefore exists. A legitimate workload can fit the ceiling yet be stopped early. One conservative interruption charge can also exhaust the remaining allowance; fifteen interruptions are not necessary once useful work has consumed most of the budget.

**3. Scoring**

I found **no new demonstrated false J = 1 or false J = 0** in the executed subset: **690 mutations across 35 slots, zero escapes; 77 private renames, zero rejections**.

The nine excluded default resets remain defensible in the frozen projects: their records are frozen, and I found no public path that supplies those non-default values at the excluded checkpoint. S35’s public `save(order)` supplies that path, and its two mutants are now covered. The nine undetected mutations alone would not prove unreachability; the public-API examination supports it. [s35.py:47](/home/bmarti44/stencil-llm/src/stencil/a_screen_pool/s35.py:47), [a_screen_mutate.py:266](/home/bmarti44/stencil-llm/scripts/a_screen_mutate.py:266)

**4. Other defects and the new code**

- **Medium: full evaluations can exceed the frozen output cap.** The actual CLI validation accepts `--max-new 2048`. With that setting shared across all three arms, complete synthetic records and valid budget artifacts produce **`GATE PASSED`**. Agreement between arms does not establish compliance with the registered 1,536-token limit. [a_screen_run.py:111](/home/bmarti44/stencil-llm/scripts/a_screen_run.py:111), [a_screen_run.py:474](/home/bmarti44/stencil-llm/scripts/a_screen_run.py:474), [a_screen_summary.py:268](/home/bmarti44/stencil-llm/scripts/a_screen_summary.py:268)

  **Fix:** enforce the registered output cap for full evaluations and validate it in the summary.

- **Low, nonblocking: the blanket ambiguous-name guarantee remains false.** `old` becomes UNRESOLVED as intended. But `a = B(); replace(a, status=...); a = A()` is resolved as **A**, although the updated object is **B**: after `_env` drops `a`, naming fallback restores a type. No frozen-pool mismatch was demonstrated. [a_screen_mutate.py:331](/home/bmarti44/stencil-llm/scripts/a_screen_mutate.py:331), [a_screen_mutate.py:412](/home/bmarti44/stencil-llm/scripts/a_screen_mutate.py:412)

  **Fix:** make recorded ambiguity override naming fallback.

I found no separate demonstrated concurrent-line corruption defect. The 3,078-write sample does not establish thread survival; the uncaught ticker exception above is the consequential failure. The parse-time budget restriction itself works, and the durable status closes the original console-only omission.

**5. Statistics and gates**

Still §7’s five gates. I recomputed McNemar **0.0625** for 5–0, **0.25** for 3–0, and the zero-discordance interval **±0.0872490536** at N = 48. [a_screen_summary.py:143](/home/bmarti44/stencil-llm/scripts/a_screen_summary.py:143), [a_screen_summary.py:195](/home/bmarti44/stencil-llm/scripts/a_screen_summary.py:195), [a_screen_summary.py:353](/home/bmarti44/stencil-llm/scripts/a_screen_summary.py:353)

**6. Interpretability and verification limits**

All 48 SCREEN and 576 TRAIN content hashes reproduce, including both registered pool hashes. I found no additional demonstrated interpretability blocker. Scoring verification used in-memory modules because the workspace is read-only; it was not the full subprocess audit. No GPU work, repository edits, or `data/bench/` access occurred.

The shortest launch-changing list is:

1. Close the unbounded final silent interval in interrupted-launch accounting.
2. Require complete spend evidence and suppress gate readings on eligibility failure.
3. Include the five-minute admission reserve in pre-arm budget sizing.
4. Enforce the frozen output-token cap.

**DO NOT LAUNCH**
