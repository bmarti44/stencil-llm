# Re-review round 10: candidate-A screen after amendment 9 (still before any GPU work)

You have reviewed this screen nine times: REJECT once, then DO NOT LAUNCH eight times. Round 9
returned two high findings and both reproduced exactly before anything changed: writes through a
stored-record alias escaped the allocator audit (13 mutations across S34, S36 and S37), and every
duration in the spend ledger was `time.time()` arithmetic, so a backward adjustment undercharged a
run and a forward one discarded a complete one.

(Dating note: review files and registration sections from round 5 on carry a `2026-09-14` stamp
written a day ahead; `git log` dates all of them 2026-09-13, and this file uses the true date.)

Your job: decide whether the screen may launch, and find what is still wrong.

Standing instructions from the owner: you review before the timing pilot, the two 4-hour trainings
and the 3 × 48 evaluation; and **"don't over engineer"** — a finding that adds machinery without
changing a decision is one you should not raise. Do NOT read `data/bench/`. Do not add arms, models,
benchmarks or review stages, and do not reframe the direction.

## What changed (read `results/a-screen/REGISTRATION-A-SCREEN.md` §21 first)

1. **The writer narrowing is GONE, not widened a fourth time.** Your alias-write finding was the
   third round running (4, 8, 9) in which the allocator audit's "does this method write state?" test
   was too narrow. Rather than add alias writes to the detector, I deleted the test from class 7 and
   from class 7b and measured what it had been buying:

   | rule | allocator mutations | undetected |
   |---|---|---|
   | with the writer restriction, as frozen at `a0469f71` | 255 | 0 |
   | the same rule with the writer test deleted (the measurement) | 340 | **85** |
   | what ships: writer test gone, typing kept | 311 | 0 |

   All 85 escapes are cases the restricted rule never generated. What remains in class 7b is TYPING,
   not plausibility: a receiver resolves by its parameter annotation, by the annotation or
   initialiser of the attribute for a `self.<attr>` receiver, or by the unique project class whose
   methods cover every method called on it; a parameter annotated as a counter-owning class is a
   handle even when the body only reads it; anything untypable is reported as UNRESOLVED, and the
   frozen pool reports none. The 29 mutations the throwaway measurement generated and the shipped
   rule does not are `_counter = 0` on a `dict`, which raises `AttributeError` — a detection that
   detects nothing; a coverage check confirms all 85 escapes are still generated.

   Scope boundary I am stating rather than hiding: class 7b's receiver is a NAME, so a store reached
   through a subscript or a call (`stores[0]._n = 0`) is outside it. An AST scan finds eleven
   non-name attribute receivers across the mutable targets and every one is a record, a string or a
   path, never a store — so nothing on this pool escapes that way. Say if you disagree.

2. **One generic fixture in twenty-three slots.** Removing the narrowing needs coverage that does
   not depend on knowing which methods matter, so every slot whose target owns an id allocator
   carries `test_no_public_call_disturbs_the_id_allocator` in its checkpoint-1 `regression_tests`.
   It creates a record, calls **every public callable of the object and of its module** with
   arguments that name no existing record, then creates again and checks the allocator. AUTHORING
   amendment 7 states the rule. **This re-freezes the SCREEN pool:** `ef802ce2160ee00c` →
   `7789e34aec0e9b55`. TRAIN is untouched; no arm has run, so no record carries the old hash.

   Three drafting traps were found by RUNNING the fixture — against your thirteen escapes, then
   against the whole audit — and all three are in §21.3. The two worth attacking: (a) the junk loop
   can consume the reissued id ITSELF — `close_account` sorts before `open_account` in `dir()`, so
   the reset fired, the loop's own junk call to the creator minted `A1` again, and the reader then
   found *a* record under `A1`; two of your thirteen still escaped, and the fixture now deep-copies
   the first record before the loop and asserts the reader returns THAT record. And (b) "every
   public callable of the package" first meant only the store and the modules its own imports named:
   the full audit then found `S11@2`'s `InvoiceArchive.invoice_archive(store, number_text)`, a METHOD
   of a second class in a second module, still escaping — 1 undetected of 1,155. The fixture now
   walks every module with `pkgutil.walk_packages` and constructs an instance of every class they
   define.

   Cost, because the per-arm ceiling is derived from it: measured A/B on five slots, the same suite
   with and without the fixture differs by +7, +6, +3, −4, −4 ms against a 0.13 s pytest invocation.
   §16.7's `SUITE_COST_S = 0.189`, `arm_budget_min() = 47.27` and the 50-minute ceiling are unchanged.

   What the fixture does NOT reach, said plainly: junk arguments reach a reset at the TOP of a
   method and nothing deeper, because a reset placed after the lookup that raises for an unknown id
   never runs under it. That half is amendment 6's per-operation create-after-operation tests, which
   run each operation on a record that EXISTS; they stay, and the audit's mutation model is
   top-of-method, so the fixture matches what the audit generates.

3. **Durations are monotonic.** Realtime now does exactly two jobs: the calendar timestamp in a
   record and the launch id. `ledger_mark` writes a monotonic reading `m` and the kernel `boot_id`
   beside `t`; `ledger_observe` takes a `clock` and a separate `wall` and calls the clock exactly
   once, after the probe; `ledger_charges` spans a live launch from the earliest `m` of the same
   boot, falling back to realtime only for a cross-boot or legacy record; `scripts/a_screen_run.py`
   takes every duration from `time.monotonic()`. Your two scenarios on the fixed code: the backward
   step charges 900 s for a 900-second launch, and the forward step charges 45.0 minutes for a
   45-minute run. `test_no_duration_is_measured_on_the_wall_clock` scans the three source files for
   a `time.time()` adjacent to a subtraction so a future edit cannot reintroduce one.

4. **Fairness, mechanically, on all twenty-three slots.** For every slot at both checkpoints, every
   callable the reply ADDS keeps its name, signature and behaviour while its body moves to a
   module-level delegate that reaches the store through a handle — the body is moved, not rewritten,
   so any suite that fails is reading the gold's structure instead of the request. Run twice, with a
   private delegate and with a public one (which the new fixture's loop then calls with junk
   arguments): **46 alternatives, 0 rejected**, each run. Because that check preserves behaviour
   exactly, four alternatives were also written by hand to differ in record identity, validation
   order, exception message and idempotence (S34@1, S04@1, S17@1, S38@1): **4 more, 0 rejected**.

## Where to look

- `results/a-screen/REGISTRATION-A-SCREEN.md` §21 (amendment 9); §§12–20 are the earlier rounds.
  `results/a-screen/AUTHORING.md` AMENDMENT 7 is this round's fixture rule.
- `scripts/a_screen_mutate.py` (the class-7 loop, `handle_allocator_mutants`, `receiver_class`,
  `attribute_classes`, `expression_class`), the twenty-three changed suites under
  `src/stencil/a_screen_pool/`, `src/stencil/a_screen.py` (`ledger_mark`, `ledger_observe`,
  `ledger_charges`, `boot_id`), `scripts/a_screen_run.py`, `tests/test_a_screen_spend.py`.
- Current freeze and clean-tree numbers: §21.6.

## Questions (answer each; cite file:line)

1. For your two round-9 items: RESOLVED / PARTIAL / NOT RESOLVED.
2. Is there any remaining path by which a session scores J = 1 while the repository is wrong, or
   J = 0 while it is right? The allocator boundary is the one you have broken twice and I have
   broken twice more. It now has no plausibility narrowing left — only typing. Say whether the
   typing rule is itself too narrow, and name the shape that escapes it. A shape that the audit's
   path rule (only the reply's own target file can be wrong) makes unreachable is not a finding.
3. Does the generic fixture reject any reply that is CORRECT under the registered request text? It
   calls every public callable with junk arguments, which is the widest thing any fixture in this
   pool does; if a correct reply can add a public callable that makes it fail, that is a false J = 0
   in twenty-three of forty-eight slots and it is the most damaging thing you could find this round.
   My own check (§21.4) is mechanical over all twenty-three slots and therefore weak in one
   specific way — it preserves behaviour exactly — so four hand-written alternatives cover the
   behavioural axis instead. Find a correct reply the fixture rejects, or say you could not.
4. Is there any remaining path by which a launch spends GPU time the ledger does not charge, or by
   which an incomplete or ineligible evaluation reaches a gate reading? And the reverse: can a
   LEGITIMATE full run inside the registered compute be refused? The boot-id fallback in
   `ledger_charges` is the one place the fixed code still reads the adjustable clock.
5. Statistics and the five gates: still as §7 registered?
6. Anything else that would make the result uninterpretable.

End with one line: **LAUNCH** or **DO NOT LAUNCH**, and if DO NOT LAUNCH, the shortest list of
changes that would change your answer. Severity per finding: critical / high / medium / low with a
one-line fix. Write plainly; do not soften.
