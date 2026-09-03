# BFCL harness v10 review — LEG A v7 + Amendments 1–5

Reviewer: sol, 2026-09-03. Reviewed commits `14caed8`, `a298bc9`, and
`1a475df` against `LEDGER-PLAN.md:623-782`, including LEG A Amendments 1–5.
`HEAD` is `3c4fca8`; the commits after `14caed8` change only
`src/stencil/bfcl.py`'s legacy pressure default or documentation/WORKLOG bytes,
not the reviewed v10/v11 execution design.

Prior findings rechecked: every finding in
`results/harness-v4-review-{sol,fable}.md`,
`results/harness-v6-review-{sol,fable}.md`,
`results/harness-v8-review-{sol,fable}.md`, and
`results/harness-v9-review-sol.md`.

All review execution was foreground and CPU-only with
`CUDA_VISIBLE_DEVICES=''`. No model or GPU process was launched, waited on,
signalled, or terminated. BFCL content access was limited to bounded reads of
the registered dev offsets. I did not open the sealed IFEval input or any
sealed BFCL case/answer row. The mixed-source hash test was deliberately
excluded because it would read bytes spanning sealed rows. No repository file
was written except this report; the two pre-existing untracked scope-review
files were left unchanged.

## Bottom line

**Yes. The REGISTERED dev preflight may be launched under this harness, from a
fresh output directory.**

No open finding remains. The v9 certificate is now tied to the exact metadata,
dev bytes, record set, record bytes, arm set, and run identity that produced
the passing preflight. The late fable-v8 findings are also closed: control
impossibility is based on total eligible columns rather than resource count;
echo clamping is bidirectional and measured against the actual generated
prompt; sealed-path comparator violations become recorded, contrast-wide
`match_impossible` states; and the manifest contains the runtime import chain.
The Amendment-5 `clf_control` shortfall exception remains exact-total with
recorded per-role deltas, while every other usable comparator and every
non-shortfall control is exact by role.

## Finding-by-finding disposition

| Prior finding | v10 disposition |
|---|---|
| sol BFCL-V4-1; fable F10 | **CLOSED.** `_load_cases_verified()` uses the pinned offset index and bounded per-ID reads. The dev run verifies only its 64 case/answer record digests and leaves `verified_bytes.source_files` empty; the census did not touch a sealed range. |
| sol BFCL-V4-2 | **CLOSED.** All five registered gates stop on failure; sealed CLI settings are constrained; a schema-3 passing certificate is mandatory and is validated before `_load_cases_verified("sealed")` or model loading (`scripts/bfcl_mt.py:389-463,2474-2503`). |
| sol BFCL-V4-3 | **CLOSED.** A1/A3 drive the primary table, A2 is separate, A4 is local, post-exclusion A3 `k` is explicit, and the v9 A3-reference-safety branch can no longer emit `SUPPORTED_A1_ONLY` (`src/stencil/bfcl.py:1578-1611,1796-1827`). |
| sol BFCL-V4-4; fable F4 | **CLOSED.** Truncated output is never tested as degenerate; malformed/unmatched tags are invalid; prior ground-truth and echoed calls enter the repeated-call set; execution and safety share one normalizer. |
| sol BFCL-V4-5; fable F5 | **CLOSED.** The module manifest, exact arms/order, cohort IDs/order, per-record run identity, resume checks, extra-record refusal, data/model hashes, and sealed clean-tree guard are live. Certificate production is now bound to the preflight records rather than a fresh post-run identity. |
| sol BFCL-V4-6 | **CLOSED.** The six registered invariant families have measured `{passed,n}` counters; candidate source indices are asserted in production and in the preflight consumer. |
| sol BFCL-V4-7; fable F8; fable F9 | **CLOSED.** Shared pressure/total-overflow facts, arm-scoped events, all-prior-USER reporting, comparator/order fields, non-evicting outcomes, dose/event aggregates, and registered outcome labels are present. |
| fable F1 | **CLOSED.** Nearest width, then nearest age, then stable-source matching is implemented without reuse; clamp failure propagates; the dev census has no impossible comparator. |
| fable F2 | **CLOSED.** Comparator text is source-faithful, column and echo clamps use Qwen token boundaries, and the echo clamp truncates or extends its last entry as Amendment 4 requires. |
| fable F3 | **CLOSED.** Initial-prompt overflow and within-turn overflow are distinct; no `None` pass reaches `summarize_records()`. |
| fable F6 | **CLOSED.** `tool_swap_echo` follows treatment target order. |
| fable F7 | **CLOSED.** Scorer truncation uses the actual untruncated encoder pair. |
| sol BFCL-V6-1; fable FV6-1 | **CLOSED.** Every required target is visited where the arm requires one-to-one matching, deterministic supplementation fills the dose, and failed clamps cannot be reported usable. The Amendment-3/FV8-2 total-column exception for fallback control is handled separately and is census-green. |
| sol BFCL-V6-2 | **CLOSED.** Indexed case/answer bytes are hashed before ID check/decode; function documents are decoded from verified bytes; checker/template/cohort/offset/pin bytes are recomputed; sealed mixed sources are verified only after certificate authorization. |
| sol BFCL-V6-3; fable FV6-3; fable FV6-4 | **CLOSED.** Echo clamping works in both directions. A pressure-turn residual above 16 is recorded as `match_impossible`; dev stops on an A1 impossibility, sealed summaries make the affected contrast uninformative, and non-pressure deltas are outside this invariant. Counts are in the preflight report. |
| sol BFCL-V6-4 | **CLOSED.** `canonical_call()` and `call_to_python()` both consume `normalize_call()` (`src/stencil/bfcl.py:1009-1034`), including qualified-name stripping, argument-object validation, and identifier validation. The strings passed to the vendored checker therefore use the same normalization as repeated-call safety. |
| sol BFCL-V6-5; fable FV6-5 | **CLOSED.** The canonical manifest contains the runner, package initializers, Stencil modules, checker utilities, and all nine dynamic environments. `stencil.bench` is absent and explicitly forbidden. |
| sol BFCL-V6-6; fable FV6-2 | **CLOSED.** Shared pressure survives pre-generation overflow, and initial-prompt NA versus within-generation/tool-step truncation controls A3, safety, final-pass reporting, and competence consistently. |
| fable FV6-6 | **CLOSED.** The dead matcher seed is gone; `control_tie_break` records stable-source ordering. |
| sol BFCL-V8-1; fable FV8-1 | **CLOSED.** The certificate contract is split-invariant, while dev actual-byte evidence is separate. Sealed validation precedes sealed row access; post-authorization bounded rows are still verified and enter the sealed run identity. |
| sol BFCL-V8-2 | **CLOSED by Amendment 5.** A usable `clf_control` shortfall must match exact total columns with per-role deltas recorded. Non-shortfall control, recency, and tool-swap must match treatment exactly by role on both generation and record-schema paths. |
| sol BFCL-V8-3 | **CLOSED.** Full cases/turns with initial-prompt NA are excluded from all registered full competence denominators and the exclusion counts are reported. |
| fable FV8-2 | **CLOSED.** Fewer fallback resources than targets does not itself make `clf_control` impossible when their total columns can supply the quota (`src/stencil/bfcl.py:477-583`). Same-role `tool_swap_echo` retains its registered per-target requirement. |
| fable FV8-3 | **CLOSED.** Pressure-turn echo/column violations are converted to recorded `match_impossible` states rather than sealed-run assertions; schema validation rejects contradictory usable records. Delta validation is pressure-scoped. |
| fable FV8-4 | **CLOSED.** `_echo_clamp()` reuses cached context IDs and re-encodes only the current-user suffix (`scripts/bfcl_mt.py:871-947`). The independent dev check found zero differences between local measurement and the full prompt's actual token delta. |
| fable FV8-5 | **CLOSED.** `run_case_arm.final_pass` omits NA turns, and `preflight_competence()` applies the shared full-case eligibility predicate. |
| fable FV8-6 | **CLOSED.** `scripts/__init__.py` is manifested and `stencil.bench` entering the runtime closure raises. |
| fable FV8-7 | **CLOSED.** Retained USER rows in `tool_swap_echo` pass through `_decode_row()` and retain `_echo_source_columns`. |
| sol BFCL-V9-1 | **CLOSED.** `main()` passes one bound `meta` through `preflight()` into `run()`. `issue_preflight_certificate()` then re-derives metadata only as a drift check, compares the exact on-disk meta and records, requires their run/arm identity, and hashes them into evidence (`scripts/bfcl_mt.py:323-386,2226-2461,2474-2518`). The consumer re-hashes that evidence before sealed authorization. |
| sol BFCL-V9-2 | **CLOSED.** A3 measurement eligibility and A3 method/safety integrity are separate. Base/full safety or base-method failure yields `INCONCLUSIVE`, never a supported label; safe no-headroom/post-exclusion cases retain the registered A1-only branch. |

## Requested dev census

I independently reconstructed all 32 registered dev cases and every
teacher-forced history with a fresh prepared environment per turn. The scorer
kept the first USER sentence and rejected every other USER sentence and every
TOOL candidate on each call. No model was loaded.

| Check | Result |
|---|---:|
| Dev cases | 32 |
| Evicting turns | 11 |
| Evicting turns selecting USER columns | 11/11 |
| `clf_control` `match_impossible` | 0/11 |
| `recency_pinned` `match_impossible` | 0/11 |
| `tool_swap_echo` `match_impossible` | 0/11 |
| `control_role_shortfall` | 0/11 |
| Registered per-role/exact-total equality failures | 0/33 comparator turns |
| `clf_control` actual echo-token delta | -4 to 0 |
| `recency_pinned` actual echo-token delta | -4 to 0 |
| `tool_swap_echo` actual echo-token delta | 0 to 0 |
| Local-clamp versus full-prompt token-delta mismatches | 0/33 |

There are six full initial-prompt overflows among the 11 evicting turns, in two
long-context cases, at 41,102–43,804 positions. All are the Amendment-4
initial-prompt NA class, not truncated failures. Passing the real geometry
through `preflight_competence()` produced these denominators:

- full overall: `n=30`, two cases excluded;
- full long-context cases: `n=6`, two cases excluded;
- full long-context turns: `n=34`, six turns excluded;
- base overall: `n=32`; and
- base long-context turns: `n=40`.

Thus initial-prompt overflow cannot depress full's registered competence
baseline, while within-turn overflow remains a counted failure.

## Certificate, manifest, normalization, and claim table

- Registration SHA-256 is
  `dd2b6eaa1a8c251c012bde10c5c26de7a78c9c4b786cebaaa57f380ccbc4dcbc`.
  It covers LEG A v7 plus Amendments 1–5 and excludes the intervening LEG B
  amendment.
- Harness/module manifest SHA-256 is
  `6d9aaf4d7eadc1e78a6727d7f9a124e1f5da1f6eb9d6632a8e9d81ac7f609ea1`.
  It has 26 entries. A dry runtime import closure contained 24 repo-local
  Python modules, all present in the manifest; `stencil.bench` was not loaded.
- The dev metadata contained 64 actual bounded record digests (case + answer
  for 32 cases), exactly equal to `bfcl_manifest.dev_records`; eight verified
  function-document digests; 15 verified checker/environment digests; matching
  offsets and pins digests; and an empty mixed-source map. Certificate issuance
  uses this same metadata and record identity, then re-reads every artifact as
  a drift check. This is the byte inventory actually used by the preflight,
  not copied expected strings.
- Call normalization is single-source: canonical safety keys and executable
  checker call strings both use `normalize_call()`. The qualified/unqualified
  regression is green.
- The primary claim table now contains all registered branches: global `k<6`,
  A1 uninformative, treatment safety, A3 comparator/method safety, safe A3
  no-headroom/post-exclusion, A1/A3 Holm outcomes, A2 separation, and A4-local
  safety. Base and full safety counterexamples return `INCONCLUSIVE`.

## CPU verification

- BFCL eviction regressions v2–v11: **111 passed, 1 deliberately deselected in
  241.49 s**. The deselected test hashes complete mixed BFCL source files and
  was excluded to preserve the sealed-content boundary.
- Independent production-shaped dev census: **32 cases, 11 evicting turns, 33
  comparator checks**, with the results above.
- Independent full-prompt echo check: **0 local/full measurement mismatches**.
- Actual dev metadata/import audit: **64 verified record digests, 26 manifest
  entries, zero missing runtime modules**.
- `git diff --check` is clean for the reviewed changes and current tree.

## Launch instruction

The registered 1.7B dev preflight may now start under these bytes. Use a fresh
output directory; do not promote any earlier shakedown. Preserve the generated
`preflight.json` together with its sibling `meta.json` and `records/`, because
schema-3 sealed authorization re-hashes all three. Apply the registered 4B
fallback only if the 1.7B competence gate requests it. Any later change to the
registration, harness/module manifest, selector, trunk/tokenizer, template,
checker, or BFCL manifest requires a new identity and fresh preflight. The
sealed run still requires a clean committed worktree and a passing certificate.

Open code-level instructions: **none**.

VERDICT: SOUND
