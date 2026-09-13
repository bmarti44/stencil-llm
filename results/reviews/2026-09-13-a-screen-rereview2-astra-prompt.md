# Re-review round 3: candidate-A screen after amendment 2 (still before any GPU work)

You have reviewed this screen twice. Round 1 read **REJECT for launch** (15 findings). Round 2,
on amendment 1, read **DO NOT LAUNCH**: "It can award false session successes, reject correct
implementations, and evaluate request 2 without showing the file being edited," with six PARTIAL
findings and two new ones (F16, F17), and five shortest changes that would change your answer.

All five were worked, at commit `e80d02cd`. Your job: decide whether the screen may launch, and
find what is still wrong. Every counterexample you gave was reproduced before it was changed.

The owner's standing instructions: you review for bugs BEFORE the timing pilot, the two 4-hour
trainings and the 3 × 48 evaluation; and **"don't over engineer"** — a finding that adds machinery
without changing a decision is one you should not raise. Do NOT read `data/bench/`. Do not add
arms, models, benchmarks or review stages, and do not reframe the direction (round 8 closed that).

## What changed

Read `results/a-screen/REGISTRATION-A-SCREEN.md` **§14, amendment 2** first; it answers your five
items in order and states the claim in your own words (§14.6).

Against your five shortest changes:

1. **Request 2's target and context.** `render_request2_message` now renders the current content
   of every changed file AND of `request.target`. Separately, `pack` gained a `protect` set and a
   single `pack_session(session, messages, checkpoint, count)` helper is the only call path, so no
   site can omit it — this fixes the second defect found while fixing yours: the packer evicted in
   plain index order and dropped rule turn 8 of S47 while keeping later droppable chatter, though
   S47's required messages fit the 2,560 budget with 443 tokens spare. Caps unchanged (1,536 /
   2,560). All 48 slots pass the maximum-length-reply qualification.
2. **Protection, function-only, and the API check.** Request 1's REGRESSION tests are now
   protected (your S01 `find` mutation fails). The protected group is split: `protected_function`
   = request 1's functional + regression + the binding check; `protected_contract` = its contract +
   support. `function_only` reads only `protected_function` (F16). `api_preserved` is replaced by a
   generated test that imports the module and asserts every pre-existing public name still
   RESOLVES (F17); before replacing the AST check I measured that all 156 possible renames of a
   pre-existing public method across the 48 slots are already caught by the executable suites once
   request 1's regression tests are protected. Deletion still fails; `count = _count` now passes.
3. **TRAIN grandfathering (F8).** Both validation statements now say "for every operation added
   from now on" and "operations already in the file keep the arrangement they have". TRAIN
   re-frozen `f6b3d63e941e1d70` → `b8f504494a281858`. The 16 SCREEN validation slots were audited
   and already grandfather explicitly.
4. **Resume, summary and adapter provenance.** The summary refuses with a line number: a wrong
   `arm` label, a missing `identity`, two identities in one arm, a session outside the frozen
   manifest (your S49 case), a duplicate, a request 2 with no request 1, a `scores.all` that
   disagrees with the individual suites (your `contract=False, all=True` case), a pass whose
   terminal reason is not `applied`, and any `--pilot-adapter` record; it requires the arms to
   share every identity field but the adapter, and reads INCOMPLETE at N = 0. Resume matches the
   COMPLETE identity, refuses duplicate keys, and repairs a truncated final line. The hub is bound
   by content (`hub_sha256`). The adapter guard requires the frozen TRAIN pool hash, no `--limit`,
   positive completed steps and the registered 14,400-second allocation; `--pilot-adapter` is the
   one opt-out and stamps every record so the summary refuses it.
5. **Compute.** `--budget-min` is cumulative across launches and guards every session start
   including one with a saved request 1. The trainer reserves the longest measured save time,
   computes `final_update_loss` from the final update's own micro-steps, and writes an exhausted
   reference pass as `status: "incomplete"`, `final: false`, which the harness refuses.

`tests/test_a_screen.py`: 301 passed. SCREEN pool unchanged at `e0867688b60e1071`.

## Questions (answer each; cite file:line)

1. For each of F1, F3, F6, F7, F8, F12, F13, F15, F16, F17: RESOLVED / PARTIAL / NOT RESOLVED /
   WITHDRAWN, with the reason. For F1 and F7, construct the worst permitted pair of replies you
   can and say what it scores.
2. New defects introduced by THESE fixes. `protect` in the packer, `pack_session`, the split
   protected group, the generated binding test (it runs inside the suite subprocess and imports
   the package — can it pass or fail spuriously, or collide with a pool test filename?), the
   validating summary loader, the adapter provenance guard, the cumulative budget, the moved
   output-directory creation in the trainer. Can any of them fail a correct reply, pass an
   incorrect one, or differ between arms?
3. Is there any remaining path by which a session can score J = 1 while the repository is
   actually wrong, or score J = 0 while it is actually right? That is the whole question.
4. Does the larger request-2 message plus the `protect` set leave the screen's compaction
   pressure intact — is the screen still testing what it claims (rules surviving eviction), or has
   it become easy? Give the numbers you measure.
5. Compute against §8 and §14.4 with the 1,296 suite subprocess invocations counted.
6. Anything else that would make the result uninterpretable.

End with one line: **LAUNCH** or **DO NOT LAUNCH**, and if DO NOT LAUNCH, the shortest list of
changes that would change your answer. Severity per finding: critical / high / medium / low with a
one-line fix. Write plainly; do not soften.
