# Source-only reader — independent code/readiness review

Reviewer: native Astra, requested xhigh reasoning, `/root/prose_data_review`, 2026-09-07. Author-disjoint from Sol implementation, Kimi data and parent registration. The current Astra instruction supersedes the historical Opus note. Reviewer owns only this review file for this task. No source edits, inference, network, GPU action, fitting or commits.

Fit-on: none. Development-on: exposed reviewed Kimi 2×8 prose-maintenance DEV and synthetic CPU transport controls. Evaluated-on: none. This review accepts experiment readiness, not model correctness or clean validation.

## Round 1 — 2026-09-07

Score: 95/100

**ACCEPT the settled implementation for one registered 48-view attempt after reviewed artifacts are committed/frozen. Zero open high/critical findings.** No new blocking finding was identified. Purpose/threat model: accidental gold/output leakage, wrong source/query coverage, authority bypasses, incomplete receipts and resource/claim errors under the approved source-reader protocol.

| Contract | Independent evidence |
| --- | --- |
| Exactly 48 independent views | Checked authored episode order, each turn 0–7, then GLOBAL and the two declared handles in order. Every case contains exactly the natural prefix through that turn; source IDs/roles/text are preserved. All prompt strings are built before the first decode. |
| No oracle or generated-state input | Source projection enumerates only ID/role/text. Independently replaced every gold value and rationale with synthetic sentinels while preserving adapter consistency: all 48 prompt strings remained identical. A fake decoder returned conspicuous wrong instructions; none entered any later prompt. |
| Non-user context is retained | Tool messages remain in chronological history. The three queries whose latest source is the tool message, indices 30–32, are actually called and recorded. There is no inherited host rule that skips them or substitutes prior notes. The prompt states source authority, adoption, lifecycle and one-off rules. |
| Preview equals actual consumer input | Rebuilt final preview exactly; through the real HTTP adapter with an in-memory fake opener, all 48 submitted request body bytes match the saved preview and per-call body/base64/hash records. Response raw bytes/hashes and candidates match their rows. No real network call occurred. |
| Output failure and deadline durability | Targeted controls cover `length`, character cap, invalid UTF-8, partial HTTP bodies and decoded lone surrogates. Raw/escaped evidence remains durable; no output is fed forward. Any technical error makes the run INCOMPLETE. Deadline control preserves the completed first receipt/row and the partial 48-case manifest. |
| Resource and source containment | Actual dry CLI checks of all four modes preserve 900 seconds for maintenance/cold/prose and use 2,700 only for source-reader; startup remains 600, cleanup reserve 60. The new mode binds the preview, reading, reviewed DEV, weight receipt and all repo source dependencies reported by the driver. Existing owned-process/container, committed-clean freeze, cooperative deadline, backstop and cleanup code are retained. |

Independently ran `python -m pytest -q tests/test_source_reader_dev.py tests/test_prose_maintenance_dev.py tests/test_maintenance_dev_check.py tests/test_maintenance_cold_diagnostic.py`: **22 passed**. Ruff and `git diff --check` passed. The additional fake-HTTP/sentinel test, all four actual launcher CLI dry runs and exact preview reconstruction passed. Dry runs left their requested run directories absent.

Independently rendered all 48 chat templates with the installed local tokenizer, thinking disabled and generation prompt included, then encoded the rendered strings. Counts exactly match `sizing.json`: **346–894 prompt tokens, 29,277 total**. Every prompt plus the 1,024 output-token cap fits below 32,768. This is local tokenizer reconstruction, not a server-rendered measurement or a prediction of output length. Whole source/history/prompt/response caps reject rather than truncate.

The source-reader launcher freezes 14 artifacts, including `results/source-reader/preview.json`; the driver's nine code hashes are all covered by that bound-file list. The narrow launcher diff changes mode dispatch, its bound-file list and use of the selected ceiling in remaining-time/final-budget checks. The reviewed receipt helpers and scalar guard are reused without new mutations to prior drivers.

| Reviewed artifact | SHA256 |
| --- | --- |
| `scripts/source_reader_dev.py` | `356cb4be6415426720c975a9eef8b2732f9dcf50f42c571491d33cac2245968b` |
| `tests/test_source_reader_dev.py` | `70b6f63d9de622836e9a891a96f3b2b9d3b64a8eccac77326c0b409f18f90383` |
| `tools/run_maintenance_dev.py` | `70e6eefc1123503755c43a6c046457221c0cd33e99b8a0c154bdb9ad80eace20` |
| `results/source-reader/PROTOCOL.md` | `fe31c0427c2221a304a54c7e8487f76f27a69734a268d237afe8bde84e85ef81` |
| `results/source-reader/preview.json` | `5336b215d2422622a5f1a9b21d04286e8d1af1ed84ae29614c666534fc0a6e43` |
| `results/source-reader/sizing.json` | `2a2cf9d92bb1013b80d63c401da2432e152ed6fb1a0af6f282f678e269f58086` |
| Reviewed DEV input | `dea370797abc792677f22adb6e2c8a0284115e6b6c3672c0d4483a1f6e2b67f9` |

The experiment intentionally performs no automatic semantic/citation scoring. A technically complete run must still receive an independent audit of all 48 meanings and supporting sources; substring correctness cannot certify applicability or completeness. The 2,700-second ceiling is the explicit prospective replacement resource plan, with qualified throughput extrapolation, not measured cost. No cleanup or GPU behavior was re-executed in this readiness review.

The three failed recurrent-updater recipes remain parked. This one request-time recipe has no semantic repair/retry path: failure parks it, and a complete semantic pass earns genuinely fresh, broader end-to-end coding preparation. Automatic parity with good manual reminders remains valuable; neither coding competence, long-session focus, completion handling, equivalence nor adequate proof is established by readiness or these exposed DEV views.
