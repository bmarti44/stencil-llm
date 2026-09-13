# Re-review round 9: candidate-A screen after amendment 8 (still before any GPU work)

You have reviewed this screen eight times: REJECT (15 findings), then DO NOT LAUNCH seven times.
Round 8 was the most valuable round so far, because its third item was not accounting: adding
`self._n = 0` to `OrderBook.collect` passed every suite at both checkpoints while `place` then
reissued a live order id — a demonstrated false J = 1 on the frozen pool. You were right about
where it came from, too: the audit's write detector, not the fixtures' strictness. All three items
were reproduced before anything was changed.

Your job: decide whether the screen may launch, and find what is still wrong.

Standing instructions from the owner: you review before the timing pilot, the two 4-hour
trainings and the 3 × 48 evaluation; and **"don't over engineer"** — a finding that adds
machinery without changing a decision is one you should not raise. Do NOT read `data/bench/`.
Do not add arms, models, benchmarks or review stages, and do not reframe the direction.

## What changed (read `results/a-screen/REGISTRATION-A-SCREEN.md` §20 first)

1. **A delegating writer is a writer.** `state_writers()` starts from the old direct-assignment test
   and closes the set over calls to other methods of `self`, to a fixed point, so a method that
   stores through `self.save(...)` is mutated like any other. Strictly a superset: nothing that was
   mutated before stops being mutated. It costs six new mutants pool-wide (961 → 967): `S35@1` and
   `S35@2` in `ready` and in `collect`, `S08@2` in `import_results`, `S10@2` in `load_feed`. All six
   were UNDETECTED on the pool as frozen at `e1329095`. Four fixtures close them — create, run the
   operation, create again, assert the new id is not a live one AND that the earlier record still
   resolves with its own values — in S08 `_C2_FUNCTIONAL`, S10 `_C2_FUNCTIONAL`, S35 `_C1_FUNCTIONAL`
   and S35 `_C1_REGRESSION`. S35 needs no checkpoint-2 fixture because request 1's functional and
   regression suites re-run at checkpoint 2 as `protected_function`.
   **This is the first amendment that changes pool files**, so the SCREEN pool is re-frozen:
   `fa633cceefe47562` → `ef802ce2160ee00c`. TRAIN is untouched. No arm has run, so no record carries
   the old hash.
   **Attack this**: is the closure actually a superset in every slot, is there another shape of
   state write it still misses, and do the new fixtures constrain any CORRECT reply?

2. **A handle is a receiver too, and that found a SECOND false J = 1 — mine, not yours.**
   Your finding asked the question about `self`; I asked it about every other name a function
   writes the store through. `refund(book, order_id, reason)` is S35's checkpoint-2 gold, lives in
   another module, and stores through `book.save(...)`: `book._n = 0` at its top passed every suite
   at checkpoint 2. Class 7b now mutates through a resolved handle as well as through `self`. The
   receiver's class must resolve — by parameter annotation, else by the unique project class whose
   methods cover every method called on the name — because an unresolved receiver produces a no-op
   mutation that reports a fake escape (S31's `join_club(roll: MemberRoll, ...)` calls `roll.add`,
   but `MemberRoll` owns no counter). Unresolved receivers are reported like unresolved update
   sites; the frozen pool has none. One fixture closes it, in S35 `_C2_FUNCTIONAL`.
   Class 7b generates 35 mutations pool-wide, in eleven slot-checkpoints, with zero unresolved
   receivers; exactly one escaped. A pool-wide probe that ignored the audit's own path rule and
   mutated every project file reported four more, and none survives contact: two are the no-op
   above, and the other two sit in request 2's target file at CHECKPOINT 1, where only request 1's
   target carries a reply — at checkpoint 2 class 7b generates both and the suites detect both.
   **Check that claim** — it is the one place where I decided something was out of scope rather
   than fixing it.

3. **The observation is timestamped by its probe.** Your backdating case reproduced at 300 s.
   `ledger_observe` now takes a clock and samples it after each successful pid probe; the runner
   passes no time at all. Astra's scenario now writes `t = 1000.0, elapsed_s = 1000.0` and charges
   1,000 s, and a read at 5,000 s still charges 1,000 s.

4. **An incomplete evaluation is not analysable.** Your S48@2 case reproduced with 12 gate lines and
   `provisional: GATE PASSED`. Incompleteness now takes the same short circuit as ineligibility:
   a `## Not analysable (rounds 6-8 F12)` block naming every reason, then the verdict, then stop.
   Verified: dropping S48@2 gives `INCOMPLETE (47/48 sessions complete…)` with **zero** gate lines;
   the complete control still gives `GATE PASSED` with twelve. An `assert not missing and not
   ineligible` guards the gate reading.

## Where to look

- `results/a-screen/REGISTRATION-A-SCREEN.md` §20 (amendment 8); §§12–19 are the earlier freezes.
  `results/a-screen/AUTHORING.md` AMENDMENT 6 is the fixture rule this round added.
- `scripts/a_screen_mutate.py` (`state_writers`, the class-7 loop), the four changed suites in
  `src/stencil/a_screen_pool/{s08,s10,s35}.py`, `src/stencil/a_screen.py` (`ledger_observe`,
  `score_checkpoint`), `scripts/a_screen_summary.py` (the short circuit and its assert),
  `tests/test_a_screen_spend.py` (your two cases by name).
- Current freeze and clean-tree numbers: §20.5.

## Questions (answer each; cite file:line)

1. For your three items: RESOLVED / PARTIAL / NOT RESOLVED.
2. Is there any remaining path by which a session scores J = 1 while the repository is wrong, or
   J = 0 while it is right? The allocator class is the one you broke twice, and my own probe broke
   it a third time — say whether the writer closure plus the handle rule is now the right boundary
   or still too narrow, and name the shape that escapes it. Check the path-rule argument above.
3. Do the five new fixtures reject any reply that is CORRECT under the registered request text?
   They are the first fixtures written against a mutation rather than against the request, which is
   exactly the direction in which a screen becomes unfair to the arm it is meant to measure. I
   checked this myself with four alternative replies that differ from the gold in construction —
   `collect` and `refund` building a record field by field instead of `replace`, `import_results`
   as an index loop, `load_feed` doing the read/parse/store itself instead of delegating — and all
   four score every suite (§20.5). Find a correct reply they reject, or say you could not.
4. Is there any remaining path by which a launch spends GPU time that the ledger does not charge, or
   by which an incomplete or ineligible evaluation reaches a gate reading? And the reverse: can a
   LEGITIMATE full run inside the registered compute be refused?
5. Statistics and the five gates: still as §7 registered?
6. Anything else that would make the result uninterpretable.

End with one line: **LAUNCH** or **DO NOT LAUNCH**, and if DO NOT LAUNCH, the shortest list of
changes that would change your answer. Severity per finding: critical / high / medium / low with
a one-line fix. Write plainly; do not soften.
