**The screen still cannot launch. Interrupted spend can be undercharged, and the summary can authorize progression from an over-budget evaluation.** The previous scoring counterexamples are closed.

Reviewed amendment 5 at `6f539bc6`. All 48 SCREEN and 576 TRAIN content hashes reproduce; containment reports zero violations with the seven authorizations. I executed 688 mutations across 35 slots with in-memory test modules: zero escapes. Seventy-seven private renames passed. The read-only environment prevented the full subprocess audit; packing tests skipped because `transformers` was unavailable. No GPU work or `data/bench/` access occurred.

| Previous blocking item | Disposition | Evidence |
|---|---|---|
| Omitted update sites and checkpoint-1 corruption | **PARTIAL** | Both original counterexamples now fail. Both checkpoints are audited, but the new reachability filter incorrectly excludes two publicly observable S35 mutations. Existing fixtures already detect them. [a_screen_mutate.py:524](/home/bmarti44/stencil-llm/scripts/a_screen_mutate.py:524) |
| S45/S47 named support cases | **RESOLVED** | Both conditional-warning replies now fail their checkpoint-1 support suites. The tests assert successful public seeding. [s45.py:274](/home/bmarti44/stencil-llm/src/stencil/a_screen_pool/s45.py:274), [s47.py:330](/home/bmarti44/stencil-llm/src/stencil/a_screen_pool/s47.py:330) |
| Interrupted accounting and evaluation budgets | **PARTIAL** | Tail repair and both request guards work. The interrupted-work cap remains unjustified, and INCOMPLETE does not reach the summary’s verdict. [a_screen.py:644](/home/bmarti44/stencil-llm/src/stencil/a_screen.py:644), [a_screen_summary.py:360](/home/bmarti44/stencil-llm/scripts/a_screen_summary.py:360) |

1. **F13 — high: the interrupted-spend cap still is not an upper bound.**

   Model loading has no enforced 600-second limit. The warning runs only **after loading returns**. A launch killed during loading at 900 seconds, read at 1,200 seconds, is charged **600 seconds**. I reproduced that result with `ledger_charges`. Your repaired 600/1,200 checkpoint example works; this loading case does not. [a_screen_run.py:261](/home/bmarti44/stencil-llm/scripts/a_screen_run.py:261), [a_screen_run.py:274](/home/bmarti44/stencil-llm/scripts/a_screen_run.py:274), [a_screen.py:650](/home/bmarti44/stencil-llm/src/stencil/a_screen.py:650)

   The post-load bound also assumes every gap contains at most six suites, but the four-session pilot runs **44 suites** before its next mark. That path is outside the claimed bound. [a_screen_run.py:342](/home/bmarti44/stencil-llm/scripts/a_screen_run.py:342), [a_screen_run.py:361](/home/bmarti44/stencil-llm/scripts/a_screen_run.py:361)

   **Fix:** remove caps unsupported by enforced termination or a verified termination timestamp; charge a conservative lifetime when termination is unknown.

2. **F12/F13 — high: an over-budget evaluation can still produce the authoritative `GATE PASSED` verdict.**

   Executing the actual session loop with a mocked clock:

   - Budget: 2,700 seconds.
   - Request 1 starts at 2,097; generation takes 299 seconds.
   - Request 2 starts at 2,396; generation takes 299 seconds.
   - Final scoring takes six seconds; completion is at **2,701**.
   - Both checkpoints pass. The runner correctly prints **INCOMPLETE**.

   That status exists only in console output. The records carry no budget eligibility result, and the summary reads neither spend nor runner status. Supplying complete synthetic 48-session records with this over-budget spend and passing count gates produces **`Verdict: GATE PASSED`**. Its text explicitly authorizes CONFIRM. [a_screen_run.py:619](/home/bmarti44/stencil-llm/scripts/a_screen_run.py:619), [a_screen_summary.py:233](/home/bmarti44/stencil-llm/scripts/a_screen_summary.py:233), [a_screen_summary.py:360](/home/bmarti44/stencil-llm/scripts/a_screen_summary.py:360)

   **Fix:** persist budget eligibility and require the summary to report INCOMPLETE for an exhausted registered budget, even with all 48 sessions recorded.

3. **F7 — low, nonblocking: `writable_fields` excludes reachable S35 behavior.**

   `OrderBook.save(order)` publicly stores an arbitrary `Order`. This checkpoint-1 sequence sets a non-default note without touching private storage:

   ```python
   order = book.place("Dev", "cake", 1, 2400)
   book.save(replace(order, note="no nuts"))
   book.ready(order.order_id)
   ```

   Nevertheless, the filter omits resetting `Order.note` in both `ready` and `collect`. Its keyword/constructor scan overlooks whole-record writers. Both excluded mutants already fail existing tests, so this is an audit omission, **not a demonstrated false J**. The nine other exclusions have defensible reachability arguments in the frozen projects. [a_screen_mutate.py:222](/home/bmarti44/stencil-llm/scripts/a_screen_mutate.py:222), [s35.py:47](/home/bmarti44/stencil-llm/src/stencil/a_screen_pool/s35.py:47), [s35.py:155](/home/bmarti44/stencil-llm/src/stencil/a_screen_pool/s35.py:155)

   **Fix:** include whole-record public writers when determining writable fields.

For **question 2**, I found no new demonstrated false J = 1 or false J = 0 in the executed subset. The third/fourth insertions test public preservation: unique live IDs, retained records and unchanged values. Full identity read-back likewise checks behavior the request preserves. It does not require a particular private representation. [s15.py:138](/home/bmarti44/stencil-llm/src/stencil/a_screen_pool/s15.py:138), [s21.py:402](/home/bmarti44/stencil-llm/src/stencil/a_screen_pool/s21.py:402)

For **question 3**, the inventory reproduces **131 sites, zero unresolved, 959 emitted mutants**. Runtime instrumentation exercised 92 sites with zero type mismatches. However, mis-typing is still possible generally: `_env` uses assignments from the whole function. I reproduced `old = A(...); replace(old, status=...); old = B(...)` being typed as **B**, although the updated object is **A**. Shared keywords pass validation. I found no instance in the exercised frozen sites; a general type-inference rewrite is not a launch requirement. [a_screen_mutate.py:293](/home/bmarti44/stencil-llm/scripts/a_screen_mutate.py:293), [a_screen_mutate.py:401](/home/bmarti44/stencil-llm/scripts/a_screen_mutate.py:401)

For **question 4**, the seed parameters are appropriate. S45 request 2 still requires promoting an existing singer, preserving its fields and obeying the current missing-record policy. Creation-time seeding does not implement that operation. S47 request 2 concerns `HoldBook`, unaffected by tool seeding. All changed gold lines reproduce as the two seed-line changes. The session-list identity correctly rejects subset pilots. [s45.py:349](/home/bmarti44/stencil-llm/src/stencil/a_screen_pool/s45.py:349), [s47.py:405](/home/bmarti44/stencil-llm/src/stencil/a_screen_pool/s47.py:405), [a_screen_summary.py:71](/home/bmarti44/stencil-llm/scripts/a_screen_summary.py:71)

For **question 5**, all five gates and statistics still match §7. I recomputed McNemar **0.0625** for 5–0, **0.25** for 3–0, and the zero-discordance interval **±0.0872490536** at N = 48. The defect is budget eligibility reaching the verdict, not the statistical calculations. [a_screen_summary.py:143](/home/bmarti44/stencil-llm/scripts/a_screen_summary.py:143), [a_screen_summary.py:315](/home/bmarti44/stencil-llm/scripts/a_screen_summary.py:315)

For **question 6**, I found no additional demonstrated interpretability blocker within this review’s execution limits.

The shortest launch-changing list is:

1. Make unfinished-launch charges conservative across loading and every interval between marks.
2. Make the summary enforce durable budget eligibility.

**DO NOT LAUNCH**
