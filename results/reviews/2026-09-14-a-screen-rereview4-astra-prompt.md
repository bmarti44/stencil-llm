# Re-review round 5: candidate-A screen after amendment 4 (still before any GPU work)

You have reviewed this screen four times: REJECT (15 findings), then DO NOT LAUNCH three times.
Round 4 said: "It accepts replies that corrupt record identity or future inserts, and interrupted
work still escapes the budget." You confirmed F1 and F3 RESOLVED, left F12/F13/F15/fixtures
PARTIAL, and gave five shortest changes. All five were worked, and two of your observations
changed the instruments rather than being patched around.

Your job: decide whether the screen may launch, and find what is still wrong.

Standing instructions from the owner: you review before the timing pilot, the two 4-hour
trainings and the 3 × 48 evaluation; and **"don't over engineer"** — a finding that adds
machinery without changing a decision is one you should not raise. Do NOT read `data/bench/`.
Do not add arms, models, benchmarks or review stages, and do not reframe the direction.

## What changed (read `results/a-screen/REGISTRATION-A-SCREEN.md` §16 first)

1. **Your two J = 1 escapes are now audit classes, not patched instances.** Class 6 sets a
   REQUIRED field during an update (both the `replace(` and `with_X(...)` forms) — your S01
   `recipe_id=tag` case. Class 7 resets the id allocator at the top of a state-writing method —
   your S05 `member_renew` and S45 `promote_lead` cases. At seven classes the audit found **65
   undetected across 34 of the 48 slots** (44 allocator, 21 identity). All 34 were repaired with
   the audit as the gate: every required field pinned on the returned record AND the public
   read-back, nothing stored under the corrupted value, plus a create-after-update sequence
   asserting a fresh id and the survival of earlier records. Class 7 is restricted to methods
   that already write state — a reset inside a pure reader is not a reply a model writes, and
   generating those would inflate the count without adding coverage. Attack that restriction if
   you think it hides a real case.

2. **Your false negative is closed, and your criticism of my disclosure is accepted.** §15.6 had
   called private seeding "weaker evidence" without admitting it REJECTS VALID REPLIES.
   `scripts/a_screen_rename.py` now tests the property directly: every private attribute the
   target assigns in `__init__` is renamed through the project source of both golds, never in the
   suites, and J must stay 1. **108 renames, 0 rejected**, after repairing 11 rejections in
   S26, S27, S28, S30, S31 (contract spies returning `self._mapping[key]` purely to have a
   return value, while the test asserts only the recorded call) and S45, S47 (support seeds of a
   state with no public writer). A grep found 4 slots; the executable check found 6, and S26 only
   it found. The 13 contract/support edits are authorised by an explicit
   `--allow SLOT:REQUEST:field` list — named entries only, stale entries reported, an incomplete
   list still fails. **Judge those 13 edits: does any of them weaken what its suite tested?**
   S45 and S47 substituted a publicly reachable non-default state for an unreachable one; §16.2
   says which property was substituted and why I claim it is preserved.

3. **One of my own fixes was vacuous and I replaced it.** For your low finding about S47's
   `Hold.borrower` mutant, I first counted such mutants by matching "unexpected keyword
   argument" in the suite message — which can never fire, because `stencil.contracts.run_tests`
   returns pytest's short summary. It is now static type association: 529 mutants emitted, 0
   naming a field their class lacks, and your `Hold.borrower` mutant is no longer generated. The
   count fell 601 → 529; the 72 dropped were never evidence.

4. **Budget and provenance.** `<out>.spend.jsonl` is a launch-level ledger independent of the
   record file, with `atexit` so a clean exit is charged its real elapsed time and only a killed
   process falls back to one request's grace. Your case now charges 900 s, not 600; a launch
   killed during model load charges 300 s, not 0. An allocation finishing past its budget is
   `over_budget` and refused by name. `loss.item()` now falls inside the measured micro-step. The
   guard validates `trainer_sha256`, `a_screen_sha256`, `a_train_pool_sha256` and a byte-level
   `hub_sha256`; a fabricated registered-looking log is refused with all four named. Empty runs
   report INCOMPLETE instead of raising `StopIteration`.

5. **Compute is closed by measurement, not by a condition.** You were right that resident time
   charges only the suites that ran. The pilot now measures the full scoring path on the gold for
   exactly the sessions it extrapolates from, and the same measurement over all 48 sessions gives
   528 invocations in 99.9 s = **0.189 s per invocation**, so the registered 1,584 cost **0.08 h**
   (0.12 h with the 1.5 factor) against §15.5's 4.41 s allowance. Check that arithmetic and say
   whether anything material is still uncounted.

## Where to look

- `results/a-screen/REGISTRATION-A-SCREEN.md` §16 (amendment 4); §12–§15 are the earlier freezes.
- `scripts/a_screen_mutate.py` (seven classes, type association), `scripts/a_screen_rename.py`
  (new), `scripts/a_screen_containment.py` (`--allow`), `scripts/a_screen_run.py` (spend ledger,
  guard, suite-cost), `scripts/a_screen_train.py` (`over_budget`, timing, identity),
  `scripts/a_screen_summary.py`, `src/stencil/a_screen.py` (`dir_sha`/`file_sha` now shared).
- `src/stencil/a_screen_pool/s01.py`–`s48.py`; `results/a-screen/AUTHORING.md` amendments 2 and 3.
- Current freeze: SCREEN `9168d17a9fbf2939` (was `4f5d59eb87bb99f8`), TRAIN `b8f504494a281858`
  unchanged. Clean-tree checks: audit **529/0 undetected**, rename **108/0 rejected**,
  containment **0 violations**, `tests/test_a_screen.py` **301 passed**.

## Questions (answer each; cite file:line)

1. For F7/fixtures, F12, F13, F15 and the new rename check: RESOLVED / PARTIAL / NOT RESOLVED.
2. Is there any remaining path by which a session scores J = 1 while the repository is wrong, or
   J = 0 while it is right? The second half now matters as much as the first: the fixtures demand
   two records, non-default attributes, preserved identity and a fresh id after an update. Does
   any of that reject an implementation a reasonable developer would write and the registered
   request permits?
3. Are the seven audit classes the right set, and is the type association sound — does it now
   SKIP a call site whose type it cannot resolve and thereby lose a real case?
4. Defects introduced by these fixes: the 34 repaired slots, the 13 authorised contract/support
   edits, the spend ledger's grace rule, the `over_budget` status, the shared `dir_sha`, the
   `--allow` mechanism.
5. Statistics and the five gates: still as §7 registered?
6. Anything else that would make the result uninterpretable.

End with one line: **LAUNCH** or **DO NOT LAUNCH**, and if DO NOT LAUNCH, the shortest list of
changes that would change your answer. Severity per finding: critical / high / medium / low with
a one-line fix. Write plainly; do not soften.
