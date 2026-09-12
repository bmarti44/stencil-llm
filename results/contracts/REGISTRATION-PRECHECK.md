# Registration: competence pre-check for the contract domain (proposal rev 5 §3)

Registered 2026-09-13 before any generation on the registered task set. Owner decision
(2026-09-13): the goal criterion "good chance of actually working" is a 25% bar on
Astra's artifact-success forecast; Astra round 7 placed rev 5 (candidate A) at ~20% as
written and ~27% conditional on this pre-check passing. This pre-check is therefore the
gate for the goal criterion; a pass sends rev 5 back to Astra (round 8) at the 25% bar.

## Frozen inputs

| item | value |
|---|---|
| task set | `src/stencil/contract_projects_reg.py`, `registered_tasks()`: 32 tasks, 8 projects (inventory, mailer, catalog, auth, ledger, exporter, settings, queue), each pairing two contract families in a pairing unused by the development set; every family appears in exactly 2 projects (8 tasks) |
| sha256 (first 16) | contract_projects_reg.py `44d4b0afb1e44b0c`; contracts.py `a93819483330eade`; contract_precheck.py `0767d0a51fe67c11` |
| self-check | `tests/test_contracts.py`: 145 passed (gold reaches J on every task; every cross-state gold fails J; unmodified target fails functionally) |
| model | unmodified shipping package `deploy/stencil_focus/build/hub-4b` (Qwen3-4B trunk), `stencil_focus` irrelevant (single request, no history), chat template with thinking disabled |
| rendering | `render_request(task, contracts_in_request=True, mode="plain")`: files, contracts in force, request, output format |
| decoding | greedy, `max_new_tokens=1536`, EOS from config, seed 0 |
| outcome | J = functional tests AND contract tests pass in the sandbox (`stencil.contracts.score`); functional-only reported |
| record | `results/contracts/precheck.jsonl`, one line per task written as it completes (resumable) |

## Decision rule (frozen)

- ELIGIBLE: J ≥ 16/32 AND functional ≥ 20/32.
- INELIGIBLE otherwise: the domain is recorded as beyond the unmodified 4B model's
  competence under immediate instructions; the rev 5 program stops before training.
- Exact binomial 95% intervals are reported with the counts; the rule is the count, not
  the interval (Astra round 7: 16/32 has interval 31.9–68.1% and does not establish
  reliable competence; the pre-check is a stop screen, not a competence proof).
- Descriptive companions (not part of the rule): per-family and per-project J; failure
  modes (missing-record handling, invented kwargs, precedent copying); comparison with
  the exposed development runs (`dev16.jsonl` plain, `dev16-explicit.jsonl` explicit
  precedence note).

## Data lineage

Authored 2026-09-13 for this program; evaluated-on only; disjoint projects from the 16
development tasks (which were exposed and inspected); nothing from `data/bench/` or
MemoryCode. No model, prompt or threshold was tuned on these tasks; the rendering and
decoding are those used on the development set before the registered set existed.

## Cost

32 generations at 9–29 s each on the shared GB10 (peer job ~30 GB resident): under 20
minutes including model load; reservation `contract-precheck`, 12 GB, 30 min.
