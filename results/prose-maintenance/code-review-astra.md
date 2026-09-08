# Prose maintenance DEV driver — independent code and registration review

Reviewer: native Astra at requested xhigh reasoning, session `/root/prose_data_review`, 2026-09-07. Brian's current Astra instruction supersedes the historical Opus reviewer note. Author-disjoint from Sol's code, Kimi's data and parent's registration. Reviewer writes only assigned review files; no inference, network, fitting, GPU action, implementation edit or benchmark evaluation was performed.

Fit-on: none. Development-on: new reviewed Kimi 2×8 DEV conversations plus fake-response CPU controls; design informed by exposed prior maintenance results. Evaluated-on: none. Existing driver compatibility tests were exercised without inference. The full goal remains automatic selection/maintenance/switching/clearing with useful task performance; ideal-manual-prose superiority is not required.

## Round 1 — 2026-09-07

Score: 95/100

Disposition: ACCEPT the final code and prospective reading for one registered exposed-DEV attempt after the reviewed files are committed and frozen. Zero open high/critical findings. This accepts an auditable experiment, not successful maintenance or adequate proof of the full goal.

Purpose/threat model: detect accidental oracle leakage, wrong carried state, source-authority failures, incomplete receipts, resource-accounting errors and claims beyond the trial's scope. Reviewed the final new driver/tests, narrow launcher diff, shared persistence-only diff, `PROTOCOL.md`, approved data and cold preview. Direct source inspection confirms no training, automatic semantic repair, gold reset, evaluation-bank access or extra model call path in the driver.

| Contract | Independent verification |
| --- | --- |
| Own actual prose state | Notes initialize once per episode, successful user candidates replace them verbatim, and every next turn receives the actual previous applied note. An intentionally wrong fake note was carried forward; the oracle never repaired it. |
| Natural inputs only | `_source` enumerates only message ID, role and text. Prompts use those messages, own notes, task handles, request kind and the static maintenance instruction. Operations, expected states, author rationale and the other episode never enter prompts. All seven prior sources are retained without slicing/truncation and saved separately in rows. |
| Authority and failure boundary | Tool candidates are called, recorded and blocked from state; subsequent prompts retain the prior note. Transport/length/character-cap/invalid-scalar failures retain prior notes. Raw rejected candidates remain available. A later user response is applied without manual edits. |
| Bounded run | Exactly 2×8, one attempted call per turn, no workers/retries. Actual launcher CLI routes all three modes correctly; prose binds new data/reading plus the existing CPU weight receipt. Existing 900-second lifecycle, 600-second startup, 60-second cleanup reserve, owned container/PID, resource checks and committed-clean freeze controls are retained. No live server was launched during review. |
| Receipt integrity | Independent fake-opener run through the real HTTP consumer checked all 16 request bodies against saved base64/hash/JSON, all response-byte hashes, prompt content and pre/post-note hashes. Source histories/episode resets and the blocked tool candidate were checked turn by turn. Partial-deadline and malformed-output controls pass. |
| Preview and interpretation | Rebuilt preview exactly matches `cold-preview.json`: two cold prompts, no invented future notes, no output directory creation. `COMPLETE` measures attempted-call accounting, so an errorful fake run correctly stays semantically unevaluated. Registration requires independent applied-state/candidate review of all 16 turns, 48 views and two trajectories. |

### Findings raised during preparation, independently verified resolved

1. **HIGH — Invalid Unicode could prevent durable receipts or enter notes.** (resolved before final Round 1, 2026-09-07) The final scalar-check wrapper rejects decoded lone surrogates before application. Both shared JSON persistence helpers use `ensure_ascii=True`, preserving rejected decoded content safely as escapes. Exact raw response bytes remain in base64. The targeted actual-HTTP control verifies a lone surrogate, malformed UTF-8, partial HTTP body, truncated completion and oversize candidate are recorded without changing notes. HTTP `_json_bytes` remains unchanged; the common-file diff changes only local persistence escaping and its comment.

2. **MEDIUM — Whole-input bounds and source provenance needed explicit preservation.** (resolved before final Round 1, 2026-09-07) Final code rejects oversize whole source/history/prompt/notes rather than truncating, records source IDs/roles/text and full prior natural history, and uses the complete at-most-seven-message prefix. Caps are 16,384 source characters, 32,768 history characters, 131,072 prompt characters and 8,192 note characters; output is capped at 1,024 tokens and server context at 32,768. CPU controls verify input-cap rejection. These character caps do not purport to equal token counts.

3. **MEDIUM — Prose freeze initially omitted the CPU weight receipt it consumes.** (resolved before final Round 1, 2026-09-07) `PROSE_BOUND_FILES` now includes `results/factorial-prep/current-trunk-hashes.json`, so the launcher's committed-clean/hash freeze applies to the existing weight-provenance receipt as well as the new reading/data/code. All three actual CLI dry runs preserve existing mode paths and leave run directories absent.

### Checks and content binding

Independently ran `python -m pytest -q tests/test_prose_maintenance_dev.py tests/test_maintenance_dev_check.py tests/test_maintenance_cold_diagnostic.py`: **16 passed**. Ruff passed on the four implementation/test files; `git diff --check` passed. Additionally ran the 16-call fake-HTTP consumer control on the newly reviewed bank, all three launcher CLI dry runs, and exact preview reconstruction. These are CPU controls with fake responses, not model outcomes.

| Reviewed file | SHA256 |
| --- | --- |
| `scripts/prose_maintenance_dev.py` | `0d40360d1e0d2eaf3d4058ccbcc16490db8b2c1b9da86768a2f9139e395b4ef5` |
| `tests/test_prose_maintenance_dev.py` | `5ed5425922b45d7a466b3b3dc638e49dd6485d806f70cad122ba80210d19e10a` |
| `scripts/maintenance_dev_check.py` | `1b3c1495069007f62bed6811f45b699e86635e8ec4e799b79708f6d737410db8` |
| `tools/run_maintenance_dev.py` | `cb9f70255bfd5053d7d3f4c002e24c158989afd426a16f722e6c89f736101f84` |
| `results/prose-maintenance/PROTOCOL.md` | `4dc69b98a99bb0087e992e5ff808aeca603f5250d004181ea00839872cfa6093` |
| `results/prose-maintenance/kimi-dev-reviewed.json` | `dea370797abc792677f22adb6e2c8a0284115e6b6c3672c0d4483a1f6e2b67f9` |

Registration correctly distinguishes blocked non-user candidate defects from applied-state errors, treats any incorrect applied state or transport/cap failure as failure of error-free maintenance, and makes no independence claim for correlated views. It preserves the existing three-failure stop-loss and excludes another near-identical prompt rescue. Successful seeds would support a broader fresh test only; completion handling, executable coding competence, long-session maintenance, human-time saving and adequate proof remain unmeasured.
