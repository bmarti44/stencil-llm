Fit-on: none. Development-on: synthetic reviewer probes and the two original Kimi DEV episodes only. Evaluated-on: none. No benchmark, held-out examples, frozen run records, model calls or rescoring.

# Maintenance annotation adapter — independent code review

2026-09-07 · Round 1 · Reviewer: gpt-6-astra, xhigh reasoning. The user explicitly requested Astra xhigh, replacing the historical Opus reviewer assignment. Author-disjoint from Sol's implementation and tests. Only this review file is written; no code edit or commit.

**Score: 93/100. Accept the bounded CPU annotation adapter; no open high/critical findings.** This does not qualify automatic maintenance, a model runner, or evaluation readiness. Threat model: trusted-but-fallible authors and operators. Scope: `src/stencil/focus/maintenance_bank.py` and `tests/test_focus_maintenance_bank.py`, against the user correction and updater contract; archived protocol, current ledger STATE, prior design review, and actual `Register` semantics were read.

## Findings

### maintenance-code#1 — medium, open: typed validation accepts malformed schema/index types

`validate_allocation` (line 287) accepts `schema_version=True` and `schema_version=1.0`; `validate_episode` (lines 187–190) accepts round indices `False, True` for rounds 0 and 1. Reproduced by `dataclasses.replace` on a valid synthetic allocation. Consequently `canonical_json` can emit a supposedly validated schema version as `true` or `1.0`. The authored adapter already uses an exact integer check for input round indices and supplies the schema version itself, so the current JSON authoring path is unaffected.

The same boundary accesses child fields before checking child types: `rounds=({},)` and `episodes=({},)` raise `AttributeError` rather than `SchemaError`. Check typed children before dereferencing them and require exact integers for schema version and round indices. Add tests through these public validators and `canonical_json`; no additional parsing layer is needed.

### maintenance-code#2 — medium, open: completion's evidence label is not bound to a user role

In `validate_episode` (lines 235–243), changing a valid retirement to `completes`, changing its current message/source role to `developer` or `system`, and attaching `Evidence("user_event", that_message_id)` is accepted. The reference is current, but it does not identify a user event. The contract permits this completion policy only for explicit user closure; a correctly named reference alone does not establish its evidence kind.

Require the matched message/source role to be `user` for `user_event` completion, or reject completion entirely in this bounded module until supported. Exercise both a valid user completion and a non-user rejection. This is nonblocking for the present DEV adapter because its authored action vocabulary excludes `completes`.

## Verified behavior and limits

Independent CPU replay of `kimi-dev-reviewed.json` passed for 2 episodes, 16 rounds and 15 operations. Synthetic/mutated DEV probes reject an all-no-op trace, missing expected live keys, invented expected keys, wrong target scope, contradictory retirement value, and renamed exact conversation duplicates across DEV/evaluation allocations. The cross-split probe uses a relabeled synthetic fixture, not evaluation data. Parent-owned targeted pytest execution is separate from these reviewer probes.

The earlier version-only target problem is fixed: the adapter binds `target_event` to exact key and scope before passing its version to `Register`. Register validation then enforces lifecycle, kind, value and retirement constraints. Gold key/value expectations remain authored inputs; scope/kind enrichment comes from replay and is accurately disclosed as dependent. Every declared task plus global view is checked after each round. Source inspection finds no import-time file access, inference, fitting or message execution.

The included tests exercise the actual adapter/register consumer. Completion, broader request kinds, authority controls, independent inventory labels and a predicted-state updater remain outside the current two-seed qualification; their absence is not a demand to expand this module.

Reviewed SHA256: implementation `be51237f9b407bdab55a27c064c3f2bede3f51fd3cabb88c8012192fe1862ca0`; tests `2fb25cdb95cca3afabe30ce915b4954f4ac4631fc0bdec98b87a0427aa7c5853`; DEV input `e4f5d954841edea17d76f0cef6f2ee68333019321a23c29d4ba53624441b1553`.
