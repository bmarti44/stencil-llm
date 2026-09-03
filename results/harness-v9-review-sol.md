# BFCL harness v9 review — LEG A v7 + Amendments 1–5

Reviewer: sol, 2026-09-03. Target commits: `fb17fc9` and `8049e8f`
(`8049e8f` changes only `WORKLOG.md`; the reviewed harness code is from
`fb17fc9`). Governing text: `LEDGER-PLAN.md:623-end`, including LEG A
Amendments 1–5. Prior findings rechecked: every finding in
`results/harness-v4-review-{sol,fable}.md`,
`results/harness-v6-review-{sol,fable}.md`, and
`results/harness-v8-review-sol.md`; no `harness-v8-review-fable.md` is present.

All review execution was foreground and CPU-only with CUDA hidden. No model or
GPU process was launched, waited on, signalled, or terminated. BFCL reads were
limited to the registered dev offsets and non-content index/manifest metadata;
no sealed BFCL case/answer row and no sealed IFEval input was opened. The only
repository file written by this review is this report. Pre-existing unrelated
changes to `WORKLOG.md` and two untracked scope-review reports were left alone.

## Bottom line

**No: the REGISTERED dev preflight may not be launched under harness v9.**

The three explicit v8 repair targets are substantially implemented. A genuine
dev certificate now has a split-invariant contract that validates before the
sealed row loader; Amendment 5's exact-total `clf_control` shortfall exception
is applied consistently while every other usable comparator remains exact by
role; and full initial-prompt-overflow cases are removed from the case-level
competence baseline. The requested dev census is green.

Two untested consumer/reporting defects nevertheless remain:

1. The certificate written after preflight is built from a fresh metadata/data
   read, not the frozen metadata and run identity that produced the preflight
   records. Mid-preflight drift can therefore authorize sealed execution under
   bytes different from those whose outcomes passed the gates.
2. The primary outcome table maps an A3 reference-arm safety failure to
   `SUPPORTED_A1_ONLY`, despite the registered requirement that this label is
   available only with safety intact and that a comparator safety breach cannot
   be reported as supported.

The first is a sealed-authorization defect; the second can overclaim the
registered primary result after the one-shot run. Both block launch.

## Blocking findings

### BFCL-V9-1 — CRITICAL — the emitted certificate is not tied to the bytes/run identity that produced the passing preflight

`main()` obtains the actual dev row/runtime inventories, constructs `base_meta`,
binds its run identity, and writes `meta.json` at
`scripts/bfcl_mt.py:2341-2353`. But it calls `preflight()` without that metadata
at lines 2358–2366. `preflight()` in turn calls `run()` without `meta` at lines
2087–2096, causing a second metadata construction at `run():1762-1766` (which
does at least have to equal the just-written meta at the start of the run).

After all cases and gates have completed, certificate issuance performs a
third, independent `artifact_meta(args)` read at line 2308 and immediately
builds the certificate from it at lines 2310–2314. That final object is never
compared with the metadata/run identity used by the records. Consequently, if
a dev row, function document, checker, module source, selector artifact, model
file, tokenizer, template source, or registration text changes after records
were generated but before line 2308, the old passing outcomes can receive a
certificate naming the new bytes. The sealed validator will then accept the
new contract. This violates Amendment 5's requirement that the certificate
bind the DEV cohort's verified bytes and preflight (5)'s before-run freeze.

The direct metadata path itself is good: it recomputed 64 bounded dev
case/answer record hashes and they exactly equalled
`bfcl_manifest.dev_records`; it also verified 8 function documents, 15 checker
files, the template, offsets, pins, selector, and trunk artifacts. The defect is
the certificate producer's provenance handoff, not the byte-hashing primitive.
The v9 tests construct a payload directly from a selected `dev_meta`; none
exercises the actual end-of-`preflight()` certificate producer against the
metadata used by `run()`.

Required code fix:

1. Pass the already constructed, bound `meta` from `main()` into `preflight()`,
   and pass that same object to `run(..., meta=meta)`. Do not let the registered
   preflight reconstruct its run metadata internally.
2. Build the certificate from that frozen metadata (copying it only to apply
   the registered full/reduced arm decision), never from a fresh unvalidated
   `artifact_meta(args)` result.
3. Before issuing the certificate, recompute `artifact_meta(args)` solely as a
   fail-closed drift check. Require its split-independent contract **and its
   complete dev `verified_bytes` inventory** to equal the frozen pre-run meta.
   On any mismatch, write `INCONCLUSIVE`/`ARTIFACT_DRIFT`, emit no certificate,
   and raise.
4. Bind the preflight run identity (or an equivalent digest of the exact frozen
   meta) into `preflight_evidence`, and validate that evidence against the
   report's `meta.json`/records before certification.
5. Add a consumer-path test that changes or monkeypatches one dev-record digest
   and one harness/module digest between `run()` completion and certificate
   issuance. Both must refuse certification; a green test must also assert that
   `certificate.preflight_evidence.dev_verified_bytes` equals the inventory in
   the metadata whose `run_identity_sha256` appears in every preflight record.

### BFCL-V9-2 — HIGH — an A3 comparator safety breach can be reported as `SUPPORTED_A1_ONLY`

`summarize_records()` correctly marks A3 uninformative when base safety fails
(`src/stencil/bfcl.py:1722-1741`) or full safety fails (lines 1742–1743). It then
collapses statistical/headroom uninformative states and safety-uninformative
states into the same `a3_claim_eligible=False` value at lines 1775–1777.
`primary_claim_status()` receives only treatment safety (lines 1778–1785), so
its lines 1581–1586 return `SUPPORTED_A1_ONLY` whenever A1 passes and that
collapsed A3 flag is false.

CPU reproduction: six synthetic exposed clusters with passing A1/A3 arithmetic
and `full.turns[0].timeout=True` produced:

```text
full safety passed = false
A1 status = eligible, p = 1/64
A3 status = uninformative
primary_claim = SUPPORTED_A1_ONLY
reason = no measurable full-context headroom on this cohort
```

That reason is false: A3 was uninformative because its reference arm breached
safety, not because headroom was absent. The governing safety clause says a
breaching comparator makes its contrast uninformative and the leg cannot be
reported as supported; the A1-only outcome rule additionally requires safety
intact. The existing eight-row unit table covers k, A1, treatment safety,
headroom/A3 eligibility, and A1/A3 rejection, but omits this branch.

Required code fix:

1. Keep separate booleans for A3's measurement/statistical eligibility
   (`ceiling_positive` and post-exclusion `k >= 6`) and A3 safety integrity
   (`clf_pinned_echo`, `base`, and `full` safety for that contrast). Do not fold
   a safety failure into the no-headroom/k-floor branch.
2. Extend `primary_claim_status()` with an explicit A3-safety/method status.
   After the existing global-k, A1-uninformative, and treatment-safety ordering,
   return a non-supported status for a base/full safety breach (conservatively
   `INCONCLUSIVE`, with the exact breached-arm reason). Reserve
   `SUPPORTED_A1_ONLY` for A3 that is uninformative because of nonpositive
   measurable headroom or post-exclusion `k < 6` **with relevant safety
   intact**.
3. Preserve A2 and A4 as their registered separate/local claims; a reporting-
   only arm must not gate A1/A3.
4. Add summary-level tests for both `base` and `full` safety breaches asserting
   that `leg_status`, `outcome.label`, and `primary_claim.status` are not any
   `SUPPORTED*` value. Keep positive controls showing that a safe nonpositive-
   headroom or post-exclusion-k case still yields `SUPPORTED_A1_ONLY` when A1
   passes.

## Requested dev census

The CPU/no-model census reconstructed all 32 dev cases and 115 teacher-forced
turn histories through the harness's seek-only dev loader, BFCL environment,
`context_layout()`, and `_turn_plan()`. Its deterministic scorer kept the first
USER sentence and rejected TOOL candidates on every scoring call.

- Evicting turns: 11, all dev `long_context`; USER columns were selected on
  11/11.
- Comparator turn-arms: 33 (11 each for `clf_control`, `recency_pinned`, and
  `tool_swap_echo`).
- `match_impossible`: 0/33; `control_role_shortfall`: 0/11 control turns.
- Per-role treatment/comparator equality failures: 0/33.
- Echo-token deltas: `clf_control` -4..0, `recency_pinned` -4..0,
  `tool_swap_echo` 0..0; all satisfy the registered absolute-16 clamp.
- Full initial-prompt overflows: 6/11 evicting turns, at 41,102–43,804
  positions, in two long-context cases. The real overflow geometry passed
  through `preflight_competence()` with full overall `n=30` (2 cases excluded),
  full long-context cases `n=6` (2 excluded), and full long-context turns
  `n=34` (6 NA turns excluded). Initial overflow is `na=true,
  truncated=false`; within-turn overflow remains a counted truncated failure.

This closes the requested nearest-match, per-role-dose, echo-clamp, and
Amendment-4/5 baseline census checks. It does not exercise BFCL-V9-1's
post-run certificate handoff or BFCL-V9-2's sealed summary decision branch.

## Certificate, manifest, normalization, and claim-table checks

- Registration SHA-256 is
  `dd2b6eaa1a8c251c012bde10c5c26de7a78c9c4b786cebaaa57f380ccbc4dcbc` and
  includes LEG A Amendments 1–5.
- Current harness manifest SHA-256 is
  `47f75457e8f104e7148294a75dd9a7c25703dbfeba394b8f7698e041115764ca`.
  It contains 25 repo-local entries: runner, Stencil package initializers and
  BFCL/statistics/selector/Qwen/cache modules, BFCL package initializers,
  checker utilities, and all nine dynamically imported environment modules.
  The dry runtime-import closure is a subset of the manifest; the unrelated
  `stencil.bench`/IFEval chain is absent.
- A dev certificate payload and sealed preauthorization contract are now
  split-invariant. A rejected certificate precedes the sealed loader, and an
  authorized bounded row is still checked against the offset index before
  decode. BFCL-V9-1 is the remaining producer-side identity gap.
- `canonical_call()` and `call_to_python()` both consume the one
  `normalize_call()` implementation (qualified-name stripping, object
  arguments, identifier validation); prior ground truth, echo entries,
  current-turn exclusions, generated calls, and executable checker strings
  pass through it. The execution-normalization regression is green.
- Exact sign-flip/Holm calculations and the registered primary table's existing
  eight branches are green, including A2 separation and A4-local gating.
  BFCL-V9-2 is the missing A3-reference-safety branch, so the primary claim
  table is not complete as registered.

## Prior-finding disposition

| Prior finding(s) | v9 disposition |
|---|---|
| sol BFCL-V4-1; fable F10 | **CLOSED.** Dev uses bounded indexed reads, verifies each row before decode, and touches no sealed row range. |
| sol BFCL-V4-2 | **PARTIAL / BLOCKER (V9-1).** Gate stops and pre-sealed-row certificate validation are present; certificate production is not bound to the run's frozen metadata. |
| sol BFCL-V4-3; fable F9 | **REOPENED / BLOCKER (V9-2).** Registered statistical branches/report fields exist, but A3 comparator-safety uninformative is mislabeled supported. |
| sol BFCL-V4-4; fable F4 | **CLOSED.** Truncation, malformed tags, echoed/prior repetition, and execution normalization are correct. |
| sol BFCL-V4-5; fable F5 | **PARTIAL / BLOCKER (V9-1).** Module/run/record manifests and resume refusal are sound; the final certificate can name metadata different from the records' run identity. |
| sol BFCL-V4-6 | **CLOSED.** Six named invariant families have measured numerators/denominators and candidate-source assertions. |
| sol BFCL-V4-7; fable F1/F2/F3/F6/F7/F8 | **CLOSED under Amendment 5.** Nearest matching, bidirectional clamp, overflow phases, tool order, scoring count, shared facts, and per-role/exact-total rules are implemented and census-green. |
| sol BFCL-V6-1; fable FV6-1 | **CLOSED.** Every target is visited, supplementation/clamp failures propagate, and current dev comparators have exact registered doses. |
| sol BFCL-V6-2 | **PARTIAL / BLOCKER (V9-1).** Actual bounded bytes are hashed, but certificate issuance is detached from the inventory used by the run. |
| sol BFCL-V6-3; fable FV6-3/FV6-4 | **CLOSED.** Echo clamp is bidirectional and both generation and record paths fail closed above 16; event counts are reported. |
| sol BFCL-V6-4 | **CLOSED.** Safety and executable call construction share normalization. |
| sol BFCL-V6-5; fable FV6-5/FV6-6 | **CLOSED.** Runtime local-module closure and stable-source tie-break provenance are explicit. |
| sol BFCL-V6-6; fable FV6-2 | **CLOSED.** Initial versus within-turn overflow, shared pressure, safety, final reporting, and competence populations are separated. |
| sol BFCL-V8-1 | **PARTIAL / BLOCKER (V9-1).** Cross-split contract and authorization order are fixed; the actual preflight producer can certify a fresh post-run inventory. |
| sol BFCL-V8-2 | **CLOSED by Amendment 5.** `clf_control` shortfalls use exact total plus recorded role deltas; all other usable cases require exact per-role columns on dev and sealed record paths. |
| sol BFCL-V8-3 | **CLOSED.** Initial-prompt-NA cases/turns are excluded from the registered full competence populations and reported. |

## Verification log

- `tests/test_bfcl_evict_v7.py tests/test_bfcl_evict_v8.py
  tests/test_bfcl_evict_v9.py`: **30 passed in 144.48 s**.
- Selected registered sign-flip/Holm, primary-table, safety, repetition, and
  report regressions from v4/v5: **14 passed in 2.04 s**.
- Independent dev census: **32 cases, 11 evicting turns, 33 comparator checks**;
  results as reported above.
- Independent synthetic A3-safety consumer probe reproduced BFCL-V9-2.
- `git diff --check` is clean for `fb17fc9` and the current tree.

## Launch instruction

Do not launch the registered 1.7B dev preflight and do not treat any v9
shakedown as a certificate. Implement BFCL-V9-1 and BFCL-V9-2 exactly as above,
add the producer-path drift and A3-safety decision regressions, rerun the safe
CPU suite and this census, recompute the registered harness identity, and obtain
review closure. Only then may the registered dev preflight start in a fresh
output directory.

**VERDICT: UNSOUND**
