# Runner exception: the `off` baseline is not re-run

**Recorded 2026-09-13.  Status: ESTABLISHED by recomputation, not by assertion.**

`results/a-screen/runs/off-oldrunner.jsonl` records
`identity.runner_sha256 = 4acdb8f044c25a48`.  The current runner hashes
`f27bc5bc0690a918`, because on 2026-09-13 the adapter's minimum-elapsed-time
guard was replaced with a completion/step-count guard and a `--require-steps`
option was added.  `results/a-screen/analysis/compare.py` refuses a
`runner_sha256` mismatch between arms; this file is the exception it requires,
and the reason must be passed explicitly:

```
python results/a-screen/analysis/compare.py <off> <arm> \
  --runner-exception "results/a-screen/RUNNER-EXCEPTION.md, verified by runner_equivalence.py"
```

## What was verified

```
python results/a-screen/analysis/runner_equivalence.py
```

reports, against `git show 86282371:scripts/a_screen_run.py`:

```
old runner (86282371) sha16 4acdb8f044c25a48      <- the hash the baseline records
current runner        sha16 f27bc5bc0690a918
adapter guards: old 2, new 2
--require-steps options removed: old 0, new 1
outside those sites the two runners are AST-identical: True
adapter guard bodies that differ: [0] of 2
a.require_steps is read only inside an adapter guard: True
```

So every difference between the two runners lies in

1. the body of the **first** `if a.adapter:` guard (the second guard is
   unchanged), and
2. one added `ap.add_argument("--require-steps", ..., default=0)`, whose value is
   read nowhere except inside an adapter guard and whose default is falsy.

The baseline was produced with no `--adapter`, so it never entered either guard.
Under both runners it executes the same program, and re-running it would consume
about 1 GPU-hour to reproduce bytes that are already established to be identical
in origin.

## What this exception does NOT cover

* It says nothing about a **trained** arm.  Any arm with an adapter runs the
  changed guard and must be produced by the current runner; comparing two
  trained arms across runner versions is not covered here.
* It is not a licence to compare across any other identity field.  `compare.py`
  still refuses a mismatch in pool, `a_screen`, contracts, hub, prompt budget,
  `max_new`, deadline or session set, and `tests/test_a_screen_compare_guard.py`
  exercises each of those refusals.
* If `scripts/a_screen_run.py` changes again, this file is void until
  `runner_equivalence.py` is re-run and reports ESTABLISHED against the new
  file.  It exits non-zero when it cannot confirm the claim.
