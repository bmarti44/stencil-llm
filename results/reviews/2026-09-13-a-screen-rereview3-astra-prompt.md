# Re-review round 4: candidate-A screen after amendment 3 (still before any GPU work)

You have reviewed this screen three times: REJECT (15 findings), then DO NOT LAUNCH twice. Round 3
said: "It can award J = 1 after an edit deletes unrelated records, and the summary can still turn a
failed gate into a pass," confirmed F6/F8/F16/F17 RESOLVED, left six PARTIAL, and gave five
shortest changes. All five were worked.

Your job: decide whether the screen may launch, and find what is still wrong. Every counterexample
you gave was reproduced before it was changed, and two of your observations were adopted as the fix
rather than patched around.

Standing instructions from the owner: you review before the timing pilot, the two 4-hour trainings
and the 3 × 48 evaluation; and **"don't over engineer"** — a finding that adds machinery without
changing a decision is one you should not raise. Do NOT read `data/bench/`. Do not add arms, models,
benchmarks or review stages, and do not reframe the direction.

## What changed

Read `results/a-screen/REGISTRATION-A-SCREEN.md` **§15, amendment 3** first. Against your five:

1. **Request 2 renders EVERY current file**, exactly as request 1 does. Your S03 case
   (`Fine`/`frozen=True` in `model.py`) is therefore in the window. Measured over 48 slots: the
   required messages plus every file need at most 2,383 of the 2,560-token budget. The self-check
   asserts every file is present, applied reply and unapplied. Compaction measured in §15.1.
2. **The multi-record and field-preservation gap was closed pool-wide, by audit rather than by
   argument.** `scripts/a_screen_mutate.py` now generates FIVE mutation classes on both target
   files of every slot: a lookup that starts raising, a write-back that is gone, a write-back that
   REPLACES the whole mapping (your S01 `self._recipes = {recipe_id: scaled}` case), an update that
   resets an unrelated defaulted attribute at a `replace(rec, ...)` call site, and the same reset
   through a record helper (`rec.with_status(...)`) — your second S01 case, which class 4 could not
   reach because such a target has no `replace(` call site at all. At five classes it found **82
   undetected mutations across 38 of the 48 slots** (61 whole-mapping replacements, 21 attribute
   resets), all from single-record fixtures with default field values. All 38 were repaired: every
   functional and regression fixture of both requests now stores at least two records, carries
   non-default values in the defaulted attributes the operation does not set, reads the other record
   back THROUGH THE STORE's own public reader, pins the count, and guards every survival assertion
   with an explicit non-`None` check so it cannot pass vacuously. The audit now reads
   **292 mutations, 0 undetected** and the registration makes that a standing requirement.
   A sixth class (persisting under a wrong key) was considered and declined with a stated reason in
   §15.6 — attack that reasoning if it is wrong.

   Three limits are stated rather than engineered away, and §15.6 lists them: requirement 2 is
   vacuous in slots with no unrelated defaulted attribute (the neighbour carries the non-default
   value instead); four seeds are unreachable through the public API at the checkpoint that needs
   them and are written into the store's own mapping with `dataclasses.replace`, the idiom the pool
   already used; and S29 has no public price setter until request 2, so a second pin using only the
   public API was added to request 2's regression suite.

   Nothing outside the two fixture fields changed. `scripts/a_screen_containment.py` proves it
   mechanically: it rebuilds each of the 38 changed slots from git and compares every session and
   request field except `functional_tests` and `regression_tests` — 0 violations — and it also
   reports any slot whose file changed without a fixture body changing. Its own non-vacuity was
   checked by injecting six edits: a project file, a request text, a contract suite, a support
   suite and a no-op change inside a gold builder are each reported; an added functional test and an
   added regression test are correctly not.
3. **Summary.** `function_only` is recomputed from its three suites; strata come from the frozen
   manifest and a disagreeing label is refused; every `SHARED_IDENTITY` field is required and the
   one shared identity must match the CURRENT freeze; an empty stratum is reported rather than
   divided by, and gate 4 cannot pass on an empty subset. Both of your flip-the-verdict cases were
   re-executed and are refused.
4. **Provenance.** `dir_sha` hashes every file's actual bytes (8.06 GB in 5.9 s); verified that a
   one-byte change in `tokenizer.json`, `vocab.json` or a weight shard changes the fingerprint. The
   adapter's `adapter_config.json` is hashed in, and the deadline is recorded and must equal the
   registered 300 s. The adapter guard requires the frozen TRAIN pool, no `--limit`, the evaluation
   trunk, `steps >= 1` as an int, at least half the allocation elapsed, and every registered
   hyperparameter; your fabricated log is refused with all deviations named.
5. **Budget and trainer.** `--budget-min` counts resident wall time via a per-record `resident_s`
   stamp, carried across relaunches, with the five-minute starting margin. Resume completes a valid
   final record's newline instead of deleting it, discards only malformed bytes, and refuses an
   output file containing another arm's or identity's records before generating. The trainer shares
   `pack_session`, includes the optimizer step in its stop estimate, will not let a periodic save
   eat the final save's reserve, and sets `status: "complete"` only with at least one completed
   step. §15.5 adopts your corrected **1,584** evaluation suite invocations (1,716 with the pilot)
   and states that the registered pilot's `resident_s` is the instrument for the §8 decision, with
   the re-run reserve given up first if it does not fit.

## Where to look

- `results/a-screen/REGISTRATION-A-SCREEN.md` §15 (amendment 3) — read first; §12, §13, §14 are the
  earlier freezes and amendments.
- `src/stencil/a_screen.py` — schema, packing (`pack`, `pack_session`, `required_indices`,
  `drop_first_order`), the six suites and `score_checkpoint`.
- `scripts/a_screen_run.py` (harness, adapter guard, resume, `resident_s`, `dir_sha`),
  `scripts/a_screen_train.py` (trainer), `scripts/a_screen_summary.py` (loader + five gates),
  `scripts/a_screen_mutate.py` (five-class audit), `scripts/a_screen_containment.py` (new),
  `scripts/a_screen_freeze.py`.
- `src/stencil/a_screen_pool/s01.py` … `s48.py` — 39 changed since round 3; `results/a-screen/AUTHORING.md`
  amendment 2 is the standard they were held to.
- Current freeze: SCREEN pool `4f5d59eb87bb99f8` (was `eb9c5c97e2d42d61`), TRAIN pool
  `b8f504494a281858` unchanged. `tests/test_a_screen.py` 301 passed; audit 292 mutations, 0
  undetected; containment 0 violations. All three were run on a clean tree.

## Questions (answer each; cite file:line)

1. For each of F1, F3, F12, F13, F15 and the pool-fixture work: RESOLVED / PARTIAL / NOT RESOLVED.
   For F1 and the fixtures, construct the worst permitted pair of replies you can and say what it
   scores.
2. Is there any remaining path by which a session scores J = 1 while the repository is wrong, or
   J = 0 while it is right? If you find one, give the mutation class so it can be added to the
   audit. Are the five audit classes the right ones, is any of them generating mutants that a
   model reply could not actually produce (a false sense of coverage), and is the declined
   sixth class genuinely redundant?
3. New defects introduced by these fixes. The all-files rendering, the strengthened fixtures (38
   slot modules changed; do any now pass for the wrong reason, or constrain a legitimate
   implementation that the registered request does not forbid — in particular, does requiring a
   second stored record or a preserved non-default attribute reject a reply a reasonable
   developer would write?), the manifest strata, the identity and freeze checks, the byte-level hashing,
   the resident-time accounting, the trainer's save reserve.
4. Statistics and the five gates: still as §7 registered, given that `function_only` and the strata
   now come from different sources than before?
5. Compute against §15.5. Is the pilot the right instrument, and is giving up the re-run reserve
   first the right order?
6. Anything else that would make the result uninterpretable.

End with one line: **LAUNCH** or **DO NOT LAUNCH**, and if DO NOT LAUNCH, the shortest list of
changes that would change your answer. Severity per finding: critical / high / medium / low with a
one-line fix. Write plainly; do not soften.
