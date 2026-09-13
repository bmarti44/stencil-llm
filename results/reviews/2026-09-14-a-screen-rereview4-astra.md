**The screen still cannot launch. Valid mutations are being omitted from the audit, named support cases lost coverage, and evaluation can exceed its budget while reporting COMPLETE.**

Reviewed `38e9c350`. All 48 SCREEN and 576 TRAIN content hashes reproduce. Containment against `69cedb54`, with the 12 named authorizations, reports zero violations. I executed counterexamples using the existing scorer with test modules loaded in memory and pytest’s fixtures. The read-only sandbox prevented rerunning the subprocess-based 301-test suite. No GPU work or `data/bench/` access occurred.

| Finding | Disposition | Evidence |
|---|---|---|
| F7 / fixtures | **PARTIAL** | Identity corruption and first-checkpoint allocator corruption still pass; see findings below. |
| F12 | **RESOLVED** | Three empty arm files now report INCOMPLETE. [a_screen_summary.py:253](/home/bmarti44/stencil-llm/scripts/a_screen_summary.py:253) |
| F13 | **PARTIAL** | Over-budget training saves are refused, but interrupted spend and evaluation limits remain defective. [a_screen_train.py:292](/home/bmarti44/stencil-llm/scripts/a_screen_train.py:292) |
| F15 | **RESOLVED** | The guard checks all four requested fingerprints. I reproduced their named refusals. [a_screen_run.py:188](/home/bmarti44/stencil-llm/scripts/a_screen_run.py:188) |
| Private-rename check | **RESOLVED for the stated property** | The inventory reproduces 108 renames; my executable subset passed 77 renames across 35 slots. Suites remain unchanged during renaming. [a_screen_rename.py:56](/home/bmarti44/stencil-llm/scripts/a_screen_rename.py:56) |

1. **F7 — high: type association silently drops real cases, including undetected identity corruption.**

   `class_of` infers types from variable names. Its caller silently skips failures, despite the docstring promising a label. I found **13 skipped sites across eight slots**. Another **11 actual `replace` sites** are excluded because their first argument is an indexing expression or reader call. [a_screen_mutate.py:52](/home/bmarti44/stencil-llm/scripts/a_screen_mutate.py:52), [a_screen_mutate.py:134](/home/bmarti44/stencil-llm/scripts/a_screen_mutate.py:134)

   In S30’s second reply, change:

   ```python
   replace(old, contractor=contractor)
   ```

   to:

   ```python
   replace(old, order_id=contractor, contractor=contractor)
   ```

   With the first gold reply, **both checkpoints pass: J = 1**. Assigning `"Reyes Plumbing"` returns that string as the order ID; `get(returned.order_id)` returns `None`. The new create-after-update test checks the old record’s unit, description and contractor, but omits its ID. [s30.py:300](/home/bmarti44/stencil-llm/src/stencil/a_screen_pool/s30.py:300), [s30.py:392](/home/bmarti44/stencil-llm/src/stencil/a_screen_pool/s30.py:392)

   I also reproduced omitted identity mutations passing in S29, including its indexed `replace(self._entries[entry_id], ...)` form. [s29.py:340](/home/bmarti44/stencil-llm/src/stencil/a_screen_pool/s29.py:340)

   **Fix:** associate every actual update site with its record type, fail visibly on unresolved sites, and repair the resulting preservation failures.

2. **F7 — high: auditing only checkpoint 2 leaves a wrong first checkpoint undetected.**

   Add `self._counter = 0` at the start of S01’s first-reply `scale_recipe`. That **217-token reply passes checkpoint 1**. Then submit the ordinary **283-token second gold**, which restores the allocator behavior: checkpoint 2 passes, so **J = 1**.

   The first repository is already wrong: add A, add B, scale A, add C produces another `R1`, overwriting A; count remains two. Its first-checkpoint tests never create after scaling. The audit mutates only the checkpoint-2 gold. [s01.py:71](/home/bmarti44/stencil-llm/src/stencil/a_screen_pool/s01.py:71), [a_screen_mutate.py:199](/home/bmarti44/stencil-llm/scripts/a_screen_mutate.py:199)

   **Fix:** apply the existing corruption checks at both checkpoints where they change publicly reachable behavior, including first-checkpoint create-after-update sequences.

3. **F7 / authorized support edits — high: S45 and S47 lost the cases their requests explicitly name.**

   S45 names **retiring a section lead**. The replacement support test retires an ordinary singer twice. A second reply that warns only when `singer.section_lead` is true now earns **J = 1**. The public sequence add → promote → retire emits the prohibited warning. [s45.py:231](/home/bmarti44/stencil-llm/src/stencil/a_screen_pool/s45.py:231), [s45.py:264](/home/bmarti44/stencil-llm/src/stencil/a_screen_pool/s45.py:264)

   S47 names lending a tool with status **`"needs-repair"`**. Replacing that state with `"retired"` accepts a reply that warns specifically for `"needs-repair"`. I reproduced **J = 1** here too. Both warning mutations fail the old support tests and pass the amended ones. [s47.py:319](/home/bmarti44/stencil-llm/src/stencil/a_screen_pool/s47.py:319), [s47.py:354](/home/bmarti44/stencil-llm/src/stencil/a_screen_pool/s47.py:354)

   The fact that the gold does not branch on these fields establishes nothing about replies that do.

   **Fix:** restore the exact named notable cases without depending on private storage names; S45 can exercise promotion followed by retirement at checkpoint 2.

4. **F13 — high: the grace is not an upper bound, and a torn ledger line can erase a launch.**

   A checkpoint follows generation **and scoring**. Generation can take 299 seconds and still proceed to as many as six suites, each with a 90-second timeout. Model loading also has no 300-second bound. [a_screen_run.py:508](/home/bmarti44/stencil-llm/scripts/a_screen_run.py:508), [contracts.py:98](/home/bmarti44/stencil-llm/src/stencil/contracts.py:98)

   Executing the actual accounting function, a last checkpoint at 600 seconds followed by death at 1,200 seconds still charges **900 seconds**.

   There is also a direct zero-charge escape: a torn final JSON line followed by the next launch’s appended `start` becomes one malformed line. The reader silently skips it. If that launch dies during loading, its charge is **zero**. [a_screen_run.py:234](/home/bmarti44/stencil-llm/scripts/a_screen_run.py:234), [a_screen_run.py:256](/home/bmarti44/stencil-llm/scripts/a_screen_run.py:256)

   **Fix:** charge actual launch lifetime or a defensible bound covering unfinished work, and repair or refuse a torn ledger tail before appending.

5. **F13 — high: request 2 bypasses the budget guard, and over-budget evaluation reports COMPLETE.**

   I executed the actual session loop with a mocked clock and two successful 299-second generations:

   - Budget: 2,700 seconds.
   - Request 1 starts at 2,399 seconds.
   - Request 2 starts at 2,698 seconds—**two seconds remain**.
   - Completion: 2,997 seconds, **J = 1, status = COMPLETE**.

   The guard runs once per session; request 2 is unconditional. Final status checks only whether sessions were left unstarted. [a_screen_run.py:520](/home/bmarti44/stencil-llm/scripts/a_screen_run.py:520), [a_screen_run.py:569](/home/bmarti44/stencil-llm/scripts/a_screen_run.py:569), [a_screen_run.py:613](/home/bmarti44/stencil-llm/scripts/a_screen_run.py:613)

   **Fix:** guard every request start and make an evaluation that exhausts its budget report INCOMPLETE.

The seven classes remain a useful, bounded set. I would retain the restriction to state-writing methods; the demonstrated escapes already lie inside it. An eighth class is unnecessary. The type association needs complete coverage of the frozen pool’s actual call sites.

I found **no new demonstrated false J = 0** from requiring two records, non-default attributes, preserved identity or fresh IDs. Those requirements exercise preserved public behavior; the existing allocator defines its observable ID sequence. The ten contract-field edits retain their call assertions and remove unnecessary private reads. The two support-field substitutions weaken coverage as demonstrated above. The `--allow` mechanism itself correctly confines the exceptions. [a_screen_containment.py:73](/home/bmarti44/stencil-llm/scripts/a_screen_containment.py:73)

The training `over_budget` change works: a save ending at 14,420 seconds is marked `over_budget` and refused. The shared `dir_sha` hashes actual bytes and covers the current flat model directory; I found no defect introduced by moving it. [a_screen_train.py:279](/home/bmarti44/stencil-llm/scripts/a_screen_train.py:279), [a_screen.py:525](/home/bmarti44/stencil-llm/src/stencil/a_screen.py:525)

**Statistics and all five gates still match §7.** I recomputed McNemar’s 0.0625 for 5–0, 0.25 for 3–0, and the zero-discordance interval ±0.087249 at N = 48. [a_screen_summary.py:135](/home/bmarti44/stencil-llm/scripts/a_screen_summary.py:135), [a_screen_summary.py:315](/home/bmarti44/stencil-llm/scripts/a_screen_summary.py:315)

The supplied scoring arithmetic is correct: 99.9/528 = **0.189205 seconds/invocation**; evaluation costs **0.08325 hours**, or **0.124875 hours** with the factor. Including the pilot’s ordinary 132 suites and its additional 132 gold-timing suites gives approximately **0.146 hours** with the factor. That correction is small. Generation and reload costs still require the timing pilot; bad-reply timeout paths remain material to interruption accounting. [a_screen_run.py:351](/home/bmarti44/stencil-llm/scripts/a_screen_run.py:351)

The shortest launch-changing list is:

1. Cover omitted update sites and reachable corruption at both checkpoints.
2. Restore S45/S47’s exact notable-case coverage without private-name constraints.
3. Make interrupted spend durable and conservative, and enforce evaluation budgets per request.

**DO NOT LAUNCH**
