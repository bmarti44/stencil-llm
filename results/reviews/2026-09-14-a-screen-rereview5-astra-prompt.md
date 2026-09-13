# Re-review round 6: candidate-A screen after amendment 5 (still before any GPU work)

You have reviewed this screen five times: REJECT (15 findings), then DO NOT LAUNCH four times.
Round 5 said: "Valid mutations are being omitted from the audit, named support cases lost
coverage, and evaluation can exceed its budget while reporting COMPLETE", with three shortest
changes. All three were reproduced against the built fixtures before anything was changed, and
two of them changed an instrument rather than patching an instance.

Your job: decide whether the screen may launch, and find what is still wrong.

Standing instructions from the owner: you review before the timing pilot, the two 4-hour
trainings and the 3 × 48 evaluation; and **"don't over engineer"** — a finding that adds
machinery without changing a decision is one you should not raise. Do NOT read `data/bench/`.
Do not add arms, models, benchmarks or review stages, and do not reframe the direction.

## What changed (read `results/a-screen/REGISTRATION-A-SCREEN.md` §17 first)

1. **Both of your omissions are closed by rebuilding the site finder, not by adding cases.**
   `scripts/a_screen_mutate.py` now finds update sites in the AST and types each first argument
   by inference (local assignment, a mapping's annotation, a method's return annotation, a
   parameter annotation, then the naming convention), validates every resolution against the
   keywords the call already passes, and treats an UNRESOLVED site as a visible failure that
   exits 1. Sites went from 75 matched to **131 found, 0 unresolved** — your
   `replace(self._entries[entry_id], …)` and `replace(table.get_shift(id), …)` forms included.
   `main()` mutates and scores **both checkpoints**. Your two counterexamples were reproduced
   first (S30 `order_id=contractor` J = 1 with `class_of("old") is None`; S01's first-reply
   `scale_recipe` allocator reset J = 1) and both now score J = 0.

2. **That exposed 61 undetected mutations across 28 slots**, which are now fixtures: 970
   mutations, 52 escapes at checkpoint 1 and 9 at checkpoint 2. §17.2 has the table. Two honest
   details: S15 and S17 MINT before they increment, so a reset allocator first mints an id nobody
   holds and only the fourth insertion collides — those two pins use four records; and nine
   defaulted-field mutants are no longer emitted at checkpoint 1 because **no code at that
   checkpoint can make the field non-default**, so the mutated repository behaves identically
   (`writable_fields`). That is my reading of your own words, "where they change publicly
   reachable behavior". **Attack it if it hides a real case**: the alternative was to grow the
   project source a writer it has no use for, or to seed through private storage.

3. **Your rejection of my S45/S47 substitution is accepted in full**, including the reasoning:
   the gold not branching on a field establishes nothing about replies that do. I reproduced both
   (a reply warning only for `singer.section_lead`, one warning only for `"needs-repair"`: J = 1
   each). The named cases are restored and reachable publicly at the checkpoint whose request
   names them, by adding the seeding parameter to the PROJECT SOURCE
   (`add_singer(name, part, section_lead=False)`, `add_tool(name, status="in")`), pinned in the
   regression suite, with the support test asserting the seed took effect so it cannot go vacuous.
   Both replies now score J = 0 on the support suite at checkpoint 1. These are the first
   authorised changes to `Session.files`; containment gained a `SLOT:session:field` form and this
   round's authorisations are exactly four. **Judge whether a seed parameter is the right
   instrument, or whether it weakens what request 2 asks for.**

4. **Interrupted spend is now bounded above, and the ledger is repaired before it is appended
   to.** An unfinished launch is charged `max(last mark, min(lifetime, last mark + bound))` with
   the bound = one generation at the registered deadline plus one scoring of every suite at its
   timeout (300 + 6 × 90 = 840 s), or 600 s before the model is loaded. Your 600/1,200 case is
   charged 1,300 s read at 1,300 s, and 1,440 s read a day later — never 900. `ledger_repair`
   truncates a torn tail before anything is appended, and a malformed line anywhere else is
   refused rather than skipped, so your zero-charge escape is gone. The ledger moved into
   `src/stencil/a_screen.py`; `tests/test_a_screen_spend.py` carries your exact numbers.

5. **Every request start is guarded and an over-budget evaluation reports INCOMPLETE.** Your
   mocked-clock scenario (budget 2,700 s, request 1 at 2,399 s, request 2 at 2,698 s, finish at
   2,997 s, COMPLETE) now refuses request 2 and reports INCOMPLETE with `request2_not_started`;
   the saved request-1 record lets a later launch finish the session. `run_status` also reports
   INCOMPLETE whenever total spend exceeded the budget, because a request admitted inside the
   margin can still overrun it.

6. **Carried from round 4, unprompted:** the run identity now includes the session selection, and
   the summary refuses any record whose identity is not the frozen 48 ("a subset run is a pilot,
   not the screen"), so a pilot file can no longer be resumed or analysed as a real arm.

## Where to look

- `results/a-screen/REGISTRATION-A-SCREEN.md` §17 (amendment 5); §12–§16 are the earlier freezes.
- `scripts/a_screen_mutate.py` (AST site typing, `writable_fields`, both checkpoints),
  `src/stencil/a_screen.py` (`work_bound_s`, `ledger_repair`, `ledger_charges`, `may_start`,
  `run_status`, `SUITE_TIMEOUT_S`), `scripts/a_screen_run.py` (per-request guard, status),
  `scripts/a_screen_summary.py` (session selection), `scripts/a_screen_containment.py`
  (`SLOT:session:field`), `tests/test_a_screen_spend.py`.
- The 28 repaired slots in `src/stencil/a_screen_pool/`, S45 and S47 especially;
  `results/a-screen/AUTHORING.md` AMENDMENT 4 replaces the substitution rule that caused F3.

## Questions (answer each; cite file:line)

1. For each of your three blocking items: RESOLVED / PARTIAL / NOT RESOLVED.
2. Is there any remaining path by which a session scores J = 1 while the repository is wrong, or
   J = 0 while it is right? Both halves matter: the new checkpoint-1 pins demand a third (and in
   two slots a fourth) insertion and a full identity read-back. Does any of that reject an
   implementation a reasonable developer would write and the registered request permits?
3. Is the reachability rule in `writable_fields` sound, or does it excuse a mutation whose effect
   IS publicly observable at that checkpoint? Is the AST typing now complete — can a site still be
   mis-typed rather than reported?
4. Defects introduced by these fixes: the 28 repaired slots, the two `Session.files` changes, the
   spend bound, the per-request guard, the identity's session list.
5. Statistics and the five gates: still as §7 registered?
6. Anything else that would make the result uninterpretable.

End with one line: **LAUNCH** or **DO NOT LAUNCH**, and if DO NOT LAUNCH, the shortest list of
changes that would change your answer. Severity per finding: critical / high / medium / low with
a one-line fix. Write plainly; do not soften.
