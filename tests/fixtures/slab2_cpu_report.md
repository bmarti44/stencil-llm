SLAB-2 CPU audit and pilot-5 registration (2026-09-06)

SLAB-2 Amendment 1 — registered 2026-09-06 BEFORE implementation
Review: results/slab2-review-fable.md:33-166 (H1-H3, M4-M7).
Data lineage: fit-on=none; authored DEV development; evaluation grammar/seeds disjoint. No evaluation episode content inspected; regeneration/accounting automated with aggregate output only.
H1: parse before disk mutation; syntax attempts are executed+breakage, name file/line, retain last_parsable on disk; cross-file recovery must remain possible.
H2: reply cap 2048; every request and system use short one-line docstrings. Re-freeze same seeds and rerun full tokenizer accounting/context gate. Historical 577/1024 is reference size, NOT a model measurement.
H3: max_workers=4 in pilot and registered run. Each fixed concurrent group charges GPU-held wall / concurrently held lanes to each lane (including CPU preparation/checking while GPU held); per-arm mean is lane_seconds. Load charged once, then 1.25 reserve on projected lane allocations. Pilot records measured output tokens/lane by arm. CPU timings never qualify cost.
Pre-written projection formula: (output_tokens * size_factor / rate + calls * 0.8) / 3600; reserve x1.25; load separately once. Recompute these three rows from amended reference accounting before GPU: aggregate 24.7 tok/s reference; per-stream 11 tok/s reference (sequential sensitivity); aggregate 24.7 tok/s model-style x1.35 (assumption, not measurement).
M4: preserve RNG draws/seeds; swap delivery/format positions whenever needed so delivery completes strictly before format retirement. Require delivery opportunities in >=7/8 DEV and >=56/64 eval; format remains a floor-gated omission trait.
M5 bounded tolerances, labelled per reply: CRLF; leading/trailing prose outside exactly one triple-backtick fence; trailing trailer period; case-insensitive report/status; any unique task/status/delivery key order; blank lines before trailer; py/python/Python/bare tags; one leading <think></think> block. Unknown/duplicate keys, extra fences, other fences, misplaced/malformed trailers and other variants are categorized breakage.
M6: n_rounds in {16,12}, default 16. Fallback only if measured 16-round projection is (12,15]; >15 stop, <=12 retain 16. At 12 rounds retirement times are 6/7/8, reinstatement DEV9/eval10/11; task switches 2,4,5 (same RNG draws retained). Freeze both schedules now; fallback requires fresh complete 12-round DEV validation and cost <=12 before evaluation; never reduce arms.
M7: scripts/composition_pilot5.py drives loop.generate_once with vLLM adapter; captures DecodeResult.truncated in Executor and records, pending-floor raw records first, complete DEV T floor then rescore. CPU injected decoder smoke uses this exact path. No GPU execution in this fix pass.

Amendment 1 verification (CPU only)

2026-09-06 pre-launch N1/N2 applied (already committed in bdc5f115): timeout=1200, stop_token_ids=[151645,151643], ValueError on stop without terminal EOS; CPU regression assertions added; requested suite before commit: 116 passed, 1 expected xfail (68.05s).
O2/H3: launch only from the pinned, post-commit CPU-green SHA recorded below; verify checkout and clean tracked files before GPU access. Read MEASURED x-factor first: historical RNTO x1.3504 boundary / 11.9972h at x1.35 is not headroom; current Amendment-2 Q-inclusive measured projection governs.

Pilot-5 pinned CPU-green code commit: `9f0c6d27f32815010c81a02d3959102459c55e8f`. Post-commit validation with tracked tree identical to that SHA: `CUDA_VISIBLE_DEVICES='' .venv/bin/python -m pytest -q tests/test_focus_slab2_driver.py tests/test_focus_slab2.py tests/test_no_side_effect_imports.py` — **116 passed, 1 expected xfail, 64.66s**. Ruff and whitespace checks pass. This receipt is committed separately; it does not change the pinned code.

Before any GPU access, the GPU owner must use an isolated checkout of `9f0c6d27f32815010c81a02d3959102459c55e8f`, verify `git rev-parse HEAD` equals that full SHA and `git diff HEAD --exit-code` succeeds, and ensure runtime sources resolve from that checkout (not the moving live tree). Abort on mismatch. No pilot/model x-factor was measured in this CPU task; read the pilot's measured output x-factor before interpreting its measured Q-inclusive lane-cost projection. The historical 11.9972h sensitivity is not available headroom. No GPU launch is performed by this handoff.

72 episodes x 16 rounds x four arms = 4,608 real-loop reference stub calls. No model competence or measured GPU-cost claim. Evaluation generation/checking was automated; only aggregate counts and hashes were inspected.
Manifests freeze both 16- and 12-round schedules with the same seed namespaces. Both have delivery witness opportunities: DEV 11 in 8/8 episodes; eval 87 in 64/64. Format remains an omission trait gated by the actual DEV T floor.

| Arm | Max context | Registered input tokens | Registered output tokens | Reference output tokens/lane (eval) |
|---|---:|---:|---:|---:|
| R | 13,333 | 6,047,483 | 238,642 | 3,136–4,466 |
| N | 7,171 | 3,000,048 | 238,642 | 3,136–4,466 |
| T | 8,234 | 883,725 | 58,709 | 3,136–4,466 |
| O | 13,333 | 1,506,970 | 58,709 | 3,136–4,466 |

Context gate passes for all 288 lanes: maximum 13,333 + reserved reply 2,048 = 15,381 < 32,768. Registered totals use R/N x64 and frozen nested O/T x16; the audit covers all four arms in all 72 episodes.
Largest reference reply: 577 tokens against cap 2048. Historical 577/1024 was reference size, not model measurement or demonstrated model headroom.

Pre-written cost table for GPU checks 46–50 (frozen before any pilot-5 GPU execution): amended reference output 594,702 tokens, 2,560 calls, assumed 0.8 s/call TTFT. Input tokens are counted above; these sensitivity estimates do not model prefill separately. Add actual load hours once to the reserved column. Only measured four-worker lane allocations determine the 12 GPU-h gate.

| Scenario | Output factor | Hours | With x1.25 reserve (before load) | Cost-rule action at zero load |
|---|---:|---:|---:|---|
| aggregate reference (24.7 tok/s) | 1 | 7.256946 | 9.071182 | 16-round |
| per-stream reference (sequential sensitivity) (11 tok/s) | 1 | 15.586616 | 19.483270 | stop |
| aggregate model-style assumption (24.7 tok/s) | 1.35 | 9.597765 | 11.997207 | 16-round |

The x1.35 scenario leaves only about 10 seconds for load under 12 hours; rounded 12.0 must not decide the gate. No GPU projection is measured by this CPU pass.

Driver: scripts/composition_pilot5.py --cpu-stub --out /tmp/NEW-DIRECTORY; GPU owner instead supplies --model, --endpoint and measured --load-seconds for an already-held vLLM server. Four concurrent lanes, 8 DEV episodes in R/N/T plus O for directly measured O cost. Raw records retain pending-floor scores; freeze all 128 DEV T rows (96 for cost-selected fallback), then write separate scored records. Per-lane allocations and measured output tokens are in summary.json; CPU summaries have null GPU timing/projection. The driver never launches or terminates a server.

Pilot-5 science eligibility remains: complete DEV R/N/T, executed >=90%, caps <=2%, T floor >=50% per eligible trait, >=2 eligible kinds with retirement opportunities in >=2 DEV episodes, R final >=5/8, and measured registered cost <=12 GPU-h. A syntactically invalid file attempt counts executed+breakage but never reaches disk. O DEV lanes measure cost; they do not enter the pilot science gate. CPU reference compliance never freezes a model's floor.

Validation provenance: full requested selection (`CUDA_VISIBLE_DEVICES='' .venv/bin/python -m pytest -q tests/test_focus_*.py tests/test_no_side_effect_imports.py`) completed: 324 passed, 3 failed, 1 expected xfail (827.77 s). One new arithmetic test had been collected before its expected-value correction; the corrected arithmetic plus all five driver tests pass (6 passed). The other two failures are SLAB-1 test_manifest_hashes and test_dev_loop_dry_run: both reproduce unchanged on isolated pre-fix commit 8d02a037 (2 failed, 1.60 s), including prompt 981 vs frozen 879. No SLAB-1 science fixtures were re-frozen by this amendment. Full log: /tmp/slab2-amendment1-tests.log; isolated baseline log: /tmp/slab2-amendment1-baseline.log. Final SLAB-2/import suite result is recorded below.

Final validation: `CUDA_VISIBLE_DEVICES='' .venv/bin/python -m pytest -q tests/test_focus_slab2.py tests/test_focus_slab2_driver.py tests/test_no_side_effect_imports.py` — 110 passed, 1 expected xfail, 70.27 s. Current full-selection status after the correction: 325 passing, 2 confirmed pre-existing SLAB-1 fixture failures, 1 expected xfail. Ruff and whitespace checks pass; source/manifest/accounting hashes match. The 12-round CPU CLI smoke completed all 32 DEV lanes (384 calls), R final 8/8, with null GPU cost and no model eligibility. No GPU execution, process signalling, or push occurred.

SLAB-2 Amendment 2 — registered 2026-09-06 BEFORE implementation
STATE: adoption CPU implementation next; user-scoped report is this pass's write-ahead ledger. Archived PLAN/PROTOCOL are historical; current task's explicit allowlist/CPU/mock-only instructions govern. Fit-on=none; DEV authored development only; evaluation seeds/content remain sealed to human/agent inspection, automated manifest regeneration allowed.
Scope: adoption rows 2,3,4,10,12 only. First fix fable-r2 N1/N2: 1200s timeout, explicit terminal IDs, fail closed on stop without EOS.
Authority: only authenticated direct adopted transport entries can mutate rules. Quoted/tool/assistant prose is inert; forged roles and absent/wrong authority fail transactionally and are journaled. Evidence-free authenticated completes is a pending PROPOSAL, never a retirement. Evidence is typed test_receipt (SHA256 passing executable public/hidden run), confirmed tool_result ID, or explicit user_event; transport confirms the evidence independently of entry text. Register direct API remains trusted; malformed evidence fails closed. Pending proposals are a separate single renderer line only when present; N/T unchanged.
Gold schedules attach deterministic passing public-reference test receipts from the preceding task, with a source/run binding; these are GOLD schedule evidence, not claims about trajectory-model success. No evaluation prompts/results are used to fit anything.
Q: one probe for EACH round's task, in turn order before any R/N/T/O trajectory. Fresh session and clean workspace seeded with gold prerequisite files; correct current live rules plus those files and current request, no conversation history. Execute the same checker with all traits; qualify iff every scheduled task passes. Pilot Q is diagnostic only, separately journaled, and its mean lane allocation x64 is included in the reserved cost projection. Full-bank primary remains the 64 pairs. Also prewrite Q-subset PASS: same exact one-sided paired p<=.05; gain >=ceil(n/8); breakage excess <=floor(n/64); no increase in common-opportunity relapse; complete observations required. Empty subset is INSUFFICIENT, never PASS. No selection using R/N outcomes.
Rerun diagnostic: scheduled CPU orchestration only, NOT RUN in this pass except a stub. Fixed DEV indices 0,1; replay saved prefix outputs/feedback/workspace up to first false admission, remove exactly its event at that turn, then freshly decode every remaining round. Keep other scheduled events (a dependent invalid event fails closed). Compare paired final success, any-round breakage and relapse over complete saved trajectories. Diagnostic, never primary or a fitting label in this pass.
Subsets: both 16/12-round manifests carry domain, constraint kind-count mix, and lifecycle shape (ordered retirement kinds plus reinstatement round). Preserve DEV recipes. Eval indices 48..63 use an additional aggregate-reduction domain absent DEV; indices 32..63 add one process test-after-edit obligation (kind mix absent DEV). Existing late reinstatement shapes remain absent DEV. Freeze membership before model trajectories; RESULTS reports R-minus-N final success per subset descriptively, without subgroup claims or multiplicity-adjusted PASS.
External X: same episodes, renderer and executor, R/N only; Anthropic Messages API, claude-sonnet-5 default configurable; cap=max_tokens=2048, max_tokens stop is truncated, end_turn is EOS, other stops rejected. Injected mock client ONLY now; runtime real calls require a separate explicit spend-approval CLI flag. Record API usage and estimated USD using configurable per-million-token rates; unverified default planning assumption $3 input/$15 output, no cache discounts. Project 8 DEV and 64 bank at both R/N: 256/2048 calls; conservative per-call 30,720 input +2,048 output token budget, no price or competence claim. Never log credentials. Q is local diagnostic, not part of X.
Validation: requested tests/test_focus_*.py and tests/test_no_side_effect_imports.py on CPU; report exact counts and any pre-existing failures. Commit only allowlisted paths; WORKLOG at most six added lines; no push, GPU, real API, or process signals.

Amendment 2 implementation ledger (CPU)
Fable-r2 N1/N2 fixed first and isolated transport selection passed 5/5. Completion claims use DecodeResult.completion_claims; the finite bare markers done/Done/done./Done. create an UNBOUND proposal with no inferred retirement target. Other prose stays inert and is preserved verbatim in the journal. Confirmation removes a pending proposal for that exact retired version; replay accepts saved pending proposals separately from committed events.
V1 compatibility: shared Entry serialization gains evidence. Re-froze ONLY events_sha256 in slab_dev_golden_amendment3.json from DEV; assertions proved accounting, rendered_sha256 and final_hashes identical. The two older SLAB-1 failures documented by fable remain historical debt; no old prompt golden is silently rewritten. AST boundary remains strict: no regex or lowercasing in register/loop; receipt syntax is validated as structured hexadecimal metadata.
External Messages transport follows https://platform.claude.com/docs/en/api/messages/create (max_tokens, end_turn, usage). Cost estimates below use UNVERIFIED configurable planning rates, not a fetched price for claude-sonnet-5. API usage is authoritative for billing; Qwen IDs remain local renderer/context accounting, not Anthropic token IDs. No real API calls or spend occurred.

| X R/N budget envelope | Calls | Input tokens (assumed API-token budget) | Output cap tokens | Total tokens | USD estimate ($3/$15 per million) |
|---|---:|---:|---:|---:|---:|
| 8 DEV x16 rounds | 256 | 7,864,320 | 524,288 | 8,388,608 | $31.45728 |
| 64 episodes x16 rounds | 2,048 | 62,914,560 | 4,194,304 | 67,108,864 | $251.65824 |

This is a conservative planning envelope, not an API-token upper bound inferred from a different tokenizer. Reprice with --prices and obtain Brian's spend approval before --spend-approved-by-brian. Mock smoke: 256 calls; mock usage 1,289,589 input /53,372 output, simulated $4.669347, actual spend $0. The mock uses Qwen token lengths and is not a real-model cost measurement.
RESULTS writer: composition_pilot5.write_results reads saved R/N/Q rows plus manifests and frozen floor, checks complete aligned records, emits RESULTS.json and RESULTS.md with full-set and Q-subset statistical PASS/FAIL readings and descriptive R-minus-N final success per preregistered group. Pilot eligibility/cost remain separate gates. Q qualification is fixed independently of R/N outcomes; an empty subset prints INSUFFICIENT.

Amendment 2 final reference accounting (automated execution; only aggregates/manifests inspected)
Schema 5 freezes 72 x16 and 72 x12 manifests. Both schedules: DEV 4/eval 5 domains (1 absent DEV), DEV 1/eval 2 kind-count mixes (1 absent DEV), DEV 7/eval 18 exact lifecycle shapes (all 18 absent DEV). Constraint-family labels measure kind multiplicities: the extra process obligation is an additional test-after-edit audit obligation, not evidence of a novel semantic rule kind.
R/N/T/O audit: 4,608 calls, 288 lanes; maximum prompts R/O 14,127, N7,171, T8,234, hence 14,127+2,048=16,175<32,768. Registered input/output tokens: R6,310,658/232,352; N2,971,639/232,352; T883,725/58,709; O1,506,970/58,709. Above Amendment-1 numbers remain historical, superseded by this schema-5 accounting.
Q audit: 64 episodes x16=1,024 fresh-context reference probes, 64/64 reference-qualified (NOT model capability); 1,249,708 input,232,352 output, max prompt1,909. Pilot CLI reference smoke:40 DEV lanes/640 calls, Q8/8, Q26,686 output tokens, null GPU projection and eligible=false. Five-arm measured_projection now REQUIRES Q and charges Q x64; omission is rejected.
Updated registered sensitivity includes Q: 3,584 calls,814,474 reference output tokens; assumed .8s TTFT, x1.25 reserve, load separately once. Aggregate24.7 tok/s:9.956071h /12.445089h reserved; sequential11 tok/s:21.363970h /26.704962h; aggregate x1.35 output:13.161940h /16.452425h. These sensitivities do not model prefill separately and are NOT measured GPU eligibility. The actual five-arm pilot projection alone selects <=12 retain16, (12,15] fresh12-round validation, >15 stop. Historical RNTO-only cost_table is retained as a component; cost_table_with_q is the amended complete sensitivity.

Amendment 2 validation and handoff
Full requested command: CUDA_VISIBLE_DEVICES='' .venv/bin/python -m pytest -q tests/test_focus_*.py tests/test_no_side_effect_imports.py. Actual full-run result:362 passed,4 failed,1 expected xfail,766.84s. It collected before the AST/evidence-hash fixes: two failures were test_all_explicit_modules_import_and_pass_ast_fence and test_amended_dev_fixture_without_evaluation_construction; both pass on final code. The other two are fable-confirmed pre-existing SLAB-1 test_manifest_hashes and test_dev_loop_dry_run (old system/prompt goldens), left unchanged. Final explicit four-failure recheck:2 passed,2 historical failures. Do not misrepresent the original full invocation as green.
Final affected selection (adoption,boundary,composition,event_log,episode,pilot_amendment,slab2,driver,import safety):241 passed,1 expected xfail,83.20s. Subsequent tightened Q-cost/report/manifest checks:8 passed,139 deselected; final external/driver/adoption/import selection after adding API episode/arm/turn provenance:48 passed,1 expected xfail. One RESULTS writer test was added after the full selection's collection and is included in the final affected selection. All new failures are repaired; only the two recorded historical fixtures remain red.
Logs: /tmp/slab2-adoption-full.log, /tmp/slab2-adoption-final-targeted.log, /tmp/slab2-adoption-cost-final.log, /tmp/slab2-adoption-external-final.log, /tmp/slab2-adoption-failures-recheck.log. Final mock CLI:256 calls, actual spend0, identical simulated token totals; receipts bind episode/arm/turn, request SHA, model and source/driver SHA. Source/dependency/manifest/audit hashes and whitespace/lint checks verified. Whole-trajectory diagnostic only exercised with the registered stub; no real diagnostic/model run, GPU, API call, process signal, benchmark data read, or push. Existing WORKLOG.md receives the requested <=6-line handoff.


## SLAB-2 Amendment 3 — registered 2026-09-07 BEFORE code

User-authorized instrument repair; prior pilot-5 records and INELIGIBLE reading stand.
Fit-on=none; evaluated-on=authored DEV only for this repair/screen; no benchmark or
sealed evaluation content is read. Saved pilot-5 outputs are diagnostic, never fitting.

1. All R/N/T/O/Q requests share one system instruction and ONE complete worked example:
   opener `python core.py`, Python body, closing fence, then report trailer. Select only
   the requested file; a filename inside the body must be a Python comment, never bare.
   Example values are illustrative; task/status/delivery follow the current request/rules.
2. Every ReplyError adds `expected_shape` (one line, <=256 characters) and `fences_seen`
   (count of triple-backtick markers, the parser's count) to the existing feedback JSON.
   This is journaled by the existing tool feedback path; whole feedback remains <8192 bytes.
3. Strict round execution means parsed trailer plus actual file write (syntax/depth/write
   failures and caps excluded). A lane executes iff at least one of its 16 rounds writes;
   an all-failed lane counts once. Report round-0 execution/fence failures, lane execution,
   and descriptive per-round execution (also conditional on round-0 execution). ELIGIBLE
   requires >=90% executing lanes independently in R/N/T/Q, <=2% caps per arm, complete
   8-episode records, R final >=5/8, the existing two primary substitution kinds
   (indent/style and delivery/process), and mandatory Q-inclusive measured cost <=12h.
4. Only indent's floor denominator changes: applicable rounds at/after the episode's
   first indent supersede, derived from its registered DEV schedule (including later
   reinstatement). Missing/capped/failed attempts remain failures. Other trait floors
   stay unchanged; raw applicability/diagnostics remain unchanged. Freeze from all 128 T
   records before success scoring. Saved pilot-5 recomputation: language 72/128 YES;
   indent 13/39 NO; format 22/35 YES; delivery 42/49 YES; delivery_scope 0/44 NO.
   Eligible kinds: language, format, process; primary substitution kinds: process only.
   Actual DEV supersedes occur at turns 10–12, not uniformly turn 11.
5. Mandatory cost = (load + 1.25*(64*(R+N+Q)+16*(O+T)))/3600. Historical measured
   Q-exclusive estimate 7.774h; repair sensitivity 6.6–7.8h; Q at N-like cost adds
   2.613h, giving ~10.4h at the measured upper endpoint. Q cost was previously unmeasured.
6. Screen: first two DEV episodes (00/01), R/N/T/Q, 16 rounds, cap1024 as pilot5,
   qualified invariant bf16 vLLM, max four concurrent lanes, own container, <=900 GPU-held
   seconds including startup/cleanup. Two fixed mixed groups, each episode's R/N/T/Q;
   this screen measures output/reference x, not a same-arm-C4 full-run cost projection.
   SCREEN-PASS iff complete 128 records, zero round-0 fence failures, lane execution8/8,
   and per-round execution >=90% in EACH arm. Any round-0 fence failure => SCREEN-FAIL:
   stop, publish literal failures, no enlargement. Other incomplete/low-execution cases
   are SCREEN-NOT-PASS and do not authorize enlargement. SCREEN-PASS authorizes full
   pilot6 (8 DEV episodes, R/N/T/Q,16 rounds); only pilot6 ELIGIBLE authorizes larger64.
   No full pilot fits implicitly inside this screen's 900-second budget.

Validation required: tests/test_focus_slab2*.py + tests/test_no_side_effect_imports.py.
New green code SHA will be recorded after explicit-path commit and post-commit validation.

Amendment-3 pre-commit validation: **121 passed, 1 expected xfail, 95.73s** with the
required selection. New tests first failed on the old prompt, feedback, floor and
lane/screen gate; they now pass, including the actual next-prompt/journal consumer.
Ruff, whitespace and screen CLI smoke pass. The manifest was regenerated automatically;
only public/system hashes change per episode, including the12-round fallback. Historical
CPU token tables/audit above belong to the prior pin and are not new-prompt measurements.
No new model output or x-factor has been measured yet. check49 currently owns the GPU flag.

Amendment-3 **pinned CPU-green SHA: `4ab3e21884e0e5decd6d4fd78607abd6a69cf95d`**. Isolated checkout
`/tmp/stencil-pilot5-screen-pinned`; `git diff HEAD --exit-code` clean. Post-commit
required test selection: **121 passed, 1 expected xfail, 96.43s**, with PYTHONPATH
pointing to that checkout's src. This receipt is separate from the pinned code commit.
Screen launcher verifies HEAD, tracked cleanliness and imported source path before GPU use.

## SLAB-2 Amendment 4 — registered 2026-09-07 BEFORE code

STATE: CPU repair and endpoint implementation next; this report is the task write-ahead
ledger, following Amendment 2's archived-protocol disposition. User authorizes this
repair and DEV pilot 7. Source: results/composition-pilot-6-review-opus.md (fully read)
and pilot-6 README addendum. Fit-on=none; evaluated-on=eight authored DEV episodes;
saved DEV pilot-6 registers/responses are diagnostic controls, never fitting data.
No data/bench or evaluation-bank content is read or generated in this task.

Renderer: suppress the delivery row in the live rendered view when the applicable
format value is literally compact; retain register state/value and verbose rendering.
Composition is independent of arm and applies wherever that live view is rendered,
including fresh-context Q. Preserve literal values; no inference from user prose.
Remove live-row provenance/scope metadata and redundant style gloss; retirement text
identifies the retired version and reason only, never retargets to a current version.
Control: re-render saved pilot-6 registers on the exact 34 R/N/T/Q matched compact
cells (the 35th compact cell was an unwritten T attempt), asserting no delivery
imperative remains. Also check all 35 scheduled compact cells, other values/scopes,
unchanged register state, and O/R byte identity. Old results/reading stand.

PRIMARY: per-obligation change-round adherence, R versus N, episode as the unit.
Families fixed: indent/style, format/format, delivery/process. For each key's
supersedes/completes/cancels/reinstates event, select the first applicable scheduled
round at/after the event and before the next effective change; coalesce same-key
same-round events (cancel+reinstate is one effective change). Never substitute a
later successful execution. A paired event is measured only when both R and N
parse and write at that scheduled round; report missing events explicitly and
strict failed-attempt sensitivity (missing write=0) alongside conditional adherence.
Per episode/family compare the mean adherence over common measured events; the
sign of that difference contributes ONE win/loss/tie. Exact one-sided binomial sign
test on discordant episodes, H1 R>N, alpha .05, Holm across the three fixed families;
zero discordances p=1, zero paired episodes unmeasured, never PASS. Larger-test
primary family PASS requires Holm-adjusted p<=.05 and positive mean paired gain;
report each family separately, no joint-final or Q-qualified-subset gate. Overall
primary evidence requires >=1 family PASS; execution/caps/floor/cost remain separate.
Language and style are conditional on parsed file writes, independent of semantic
or runtime breakage; indent requires nonempty measured widths. Breakage remains a
separate episode-paired descriptive outcome. Joint final success is DESCRIPTIVE only.
Drop delivery_scope from every arm's trait set; Q uses the same four traits and is
a FRESH-CONTEXT REFERENCE (gold prerequisites, no feedback), never a ceiling.
O is byte-identical to R by construction; pilot6 provides 128/128 output-hash
replication. DROP O from pilot7 and larger test: another duplicate would consume
0.587 GPU-h projected without new science. Keep compatibility rendering and its test.
New measured projection: (load+1.25*(64*(R+N+Q)+16*T))/3600, four-worker same-arm
lane allocations, startup once. Historical five-arm functions/results remain legacy.

Pilot7: only after explicit-path CPU commit, required tests green, and a separately
recorded pinned SHA; isolated clean checkout and source resolution verified before
GPU. Eight DEV x16 rounds x Q/R/N/T, same-arm C4 groups 00..03 then04..07; Q first.
Qualified invariant bf16 image/flags from pilot6; cap2048; determinism replay first,
eight round0 R prompts forward/reverse C4, exact body IDs/EOS/cap D=0 required.
Budget <=5400 GPU-held seconds including startup/replay/cleanup; own RUNNING.flag,
wait for other Stencil flags/compute; never signal a host process or touch Brian's
server. Only stop/rm this run's container. No 12-round fallback in this bounded task.
PRE-WRITTEN READING: ELIGIBLE iff complete 512 records, D=0, R compact delivery=ready
emissions<=2/34 AND format adherence>=26/34 on the FIXED pilot6 34-cell control set
(no outcome-dependent rematching), zero round0 nonwrites, 8/8 executing lanes and
>=90% written rounds in each arm, caps<=2% per arm, context+2048<=32768, both
indent/style and delivery/process pass strict T floor>=50% with retirement
opportunities in >=2 episodes (Amendment3 indent denominator), primary endpoint
nonzero paired denominators for >=2 families in >=6 episodes each, measured larger
projection<=12GPU-h, and actual budget<=5400s. Report all35 compact cells too.
ELIGIBLE authorizes the larger64 test on this endpoint; do not launch it in this
task. Otherwise INELIGIBLE naming failed items (INCOMPLETE for interrupted records).
No significance or joint final success requirement gates DEV eligibility.
Validation: tests/test_focus_slab2*.py + tests/test_no_side_effect_imports.py;
regressions for every item, saved-register composition control, CPU driver smoke.

Amendment 4 CPU verification: required selection **135 passed, 1 expected xfail,
70.45s**; full 512-call DEV CPU-stub driver and artifact consumer pass. Saved
register versions/live views reproduce exactly on all35 compact cells; all34
matched cells lose the contradictory delivery imperative. Two historical tests
were corrected because they relied on empty-diff indent passing. Lint/whitespace
pass. Episode schedules/manifests are unchanged; only source/dependency hashes
and Amendment4 metadata were refreshed. The requested existing CPU suite includes
automated synthetic reference/manifest checks; no benchmark files or evaluation
prompts/results were inspected, and no model evaluation-bank execution occurred.
Conservative denominator clarification before GPU: additionally require >=6 episodes
each with >=2 nonzero paired family denominators (not merely separate six-episode
sets). No threshold is selected using new model output.

Amendment-4 **pinned CPU-green SHA: `24ed80a49edcea3359d0c45d361daf7fdf761745`**.
Isolated `/tmp/stencil-pilot7-pinned`, tracked tree clean; required post-commit suite:
**135 passed, 1 expected xfail, 70.80s**; pinned CLI CPU smoke PASS. Initial isolated
validation failed solely because its gitignored tokenizer was absent (105 failed,
30 passed, 1 xfail); linking the existing local model directory repaired the setup,
with no source changes. Final log: composition-pilot-7/cpu-validation.log. All35 saved
compact rule blocks:17126 old tokens ->8412 new tokens; zero delivery imperatives.
Pilot7 launches next from this SHA; determinism first, <=5400 GPU-held seconds.
Fit-on: none; development-on: the 8 DEV episodes only; evaluated-on: the 64 frozen evaluation episodes, opened once after this commit, never previously model-evaluated. No benchmark content or responses.

# SLAB-2 Amendment 5 — frozen larger test

Authorized by Brian's 2026-09-07 instruction, [Opus review](../composition-pilot-7-review-opus.md) and the [pilot-7 addendum](../quick-checks/composition-pilot-7/README.md). This supersedes the earlier larger-test brief and Amendment-4 larger-test reading/allocation; historical pilot results and their code retain their original readings. No further DEV re-pilot.

The episode is the unit for every inferential and gating statement. Within-episode observations are averaged before a sign enters inference. Round counts, hashes, token/time accounting and the requested payload reproducibility fraction are descriptive audit measurements, never independent observations for inference. Delete the per-round compact emission/adherence thresholds from this larger-test contract. They are invalid: R4/34 versus block-free N3/34, McNemar two-sided p=1, both1/8 episodes; all four R emissions represent one locked episode. Prior cross-container noise was10/166=6.02% (reported Wilson CI3.3–10.7%); that cell CI is historical and ignores clustering.

**Primary:** delivery family of per-obligation change-round adherence, exactly `slab2_endpoint.primary`. Effective change events select the first applicable round before the next change, using schedule only. Paired parsed writes define measured events; average common events within each episode using exact fractions, then exact one-sided sign test R>N. Holm across delivery, format, indent at alpha=.05; family evidence requires Holm p<=.05 and positive mean paired gain. Report all three directions and conditional missingness plus missing-write-as-failure sensitivity. No substitution of later writes. The delivery family alone powers the overall verdict. Joint final success is descriptive only: DEV Q0/8 and all-arms-agree0/128 cannot establish that endpoint.

**Frozen mechanical reading:** `slab2_endpoint.larger_reading()` returns PASS iff delivery passes after Holm, R's any-breakage episode count minus N's is<=1, CPU composition control passes, and every expected record is present exactly once. Completed runs missing that conjunction are FAIL. Unrun rounds/episodes give INCOMPLETE, including deadline/resource/error stops; no partial PASS, no dropped/replaced episodes or unpaired rescue. Exactly64 unique episodes,16 rounds, R/N/T on all64, Q on IDs00–15 (fresh-context gold-prerequisite reference), O dropped as128/128 byte-identical R in pilot6. No joint-final, Q-qualified subset, T floor, absolute breakage or compact-behavior gate. Breakage is the frozen checker's `outcome.diagnostics.breakage`, any round per episode. Duplicate/unregistered records hard-fail the accounting audit. Pre-run determinism failure stops before evaluation inference and yields INCOMPLETE; no second attempt.

**Only blocking composition check:** CPU reconstruction of all35 saved DEV compact registers must reproduce pilot7's exact SHA256s and versions. After the freeze, before GPU, every compact register in the frozen64 schedules is rendered both from forward state and event-log reconstruction: identical text hashes, no delivery row, no `trailer delivery=` anywhere. Preserve every hash and all64 episode coverage. Renderer/register/loop/slab2 and existing driver bytes remain identical to24ed80a4; no new model-facing instruction. `freeze.json` binds source bytes, existing manifest file,64 IDs, per-episode hashes, ID hash and bank ID/hash map hash. Read manifests only before this commit, not evaluation content. The fresh bank is instantiated once by the frozen runner after commit; the same objects feed execution and reporting.

**Execution:** isolated checkout of this freeze commit, tracked-clean and module-path/source-hash verified before any GPU check/access. Frozen same-arm concurrency4 groups: increasing chunks00–03,...60–63; within each chunk R,N,T then Q for chunks through12–15. Exact group list in `freeze.json`; no dynamic allocation by outcomes. Each lane sequentially runs16 rounds through the unchanged real executor/history/journal consumer. Before main inference, the eight DEV round0 R prompts replay forward then reverse at concurrency4, exact token-body/EOS/cap equality required (diagnostic only, no DEV episode re-pilot). Qualified pinned vLLM image and exact flags copied in `freeze.json`, bf16 Qwen3-30B-A3B, cap2048, seed20260906, temperature0, context32768, batch invariant/TRITON_ATTN, max-num-seqs4. No fallback/retry or alternative model.

**Cross-run reproducibility:** exactly40 fixed saved pilot7 R payloads: all eight DEV episode IDs, rounds0,4,8,12,15 each. File and request hashes are frozen before launch. Reissue byte-identical request JSON (same prompt IDs and sampling parameters) after group T28–31, midway through bank execution, in this run's new container. Compare text, generated token IDs and finish reason to the old container's saved response. Report divergent/40 and fraction beside the result, plus eight within-episode divergence rates and any-divergence episode count. No independent-cell inference or reproducibility threshold; this is a registered cross-container control, not a rerun of a DEV trajectory. Missing control must be disclosed as an execution-protocol failure, never claimed complete. Replay receipts stay outside git and are hashed. No additional container restart required because pilot7 supplies the first container instance.

**Known confounds and claim ceiling:** T's oracle prose delivered7/8, so PASS credits “the current effective value restated at request time,” not the register data structure per se or superiority over prose. Old rendered blocks persist because history is never re-composed (`loop.py:363`). The arm-invariant worked system example (`slab2.py:71–73`) attracts `delivery=ready`, with Q emitting33/34 on DEV compact rounds; these are emissions, not format successes. T's oracle prose remains uncomposed, confounding R-vs-T format comparisons. Report negative format/indent gains explicitly; a one-sided test does not establish absence of harm. The [v2 claim ceiling](../focus-mechanism-composition-v2-astra.md) applies: bounded explicit-rule rendering package on one frozen trunk and authored distribution; no free-text admission, universal selection, autonomous long-horizon engineering, actuator efficacy, or absence-of-stale-influence claim. This run uses gold structured events, not learned admission/updating or an actuator.

**Cost and stop:** corrected allocation projection from committed pilot7 lane times is `(497.4678113460541 +1.25*(64*(106.95503854006529+96.3614319190383+89.96212818473577)+16*82.3344509229064))/3600 =7.11290131147537h`. Add1200s for replay/determinism/cleanup:7.446234644808703h<12h. No fresh cost pilot. GPU-held cooperative deadline41400s (11.5h) includes startup and cleanup; hard ceiling43200s. Stop new groups with1500s reserve; stop new requests180s before deadline; requests bounded to1200s and remaining time minus60s. Wait time separately recorded. Only own named container may be stopped/removed; never signal a host process or touch Brian's server. Own `results/quick-checks/larger-test/RUNNING.flag` acquired under review lock after other flags/compute clear and removed after cleanup.

**Artifacts:** same-run loop/raw/HTTP journals and per-round output SHA256 receipts, records persisted before aggregates; final arm JSONL files each<=10MB, summary, episode tables, control, cost audit, server log and RESULTS.md under this directory. HTTP/full journals out of git with hash manifest. CPU replay audits raw responses against every saved record before reporting. Explicit `git add -f`/commit paths, verify tracked artifacts, update quick-check index and <=8 new WORKLOG lines; no push.

Amendment5 pre-freeze CPU verification:37 passed,1 expected xfail in11.47s;
DEV-derived synthetic tests only, all35 saved hashes exact, lint/whitespace clean.
No evaluation episode opened or GPU access before this registration commit.

Fit-on: none; development-on: the eight DEV episodes only; evaluated-on: a new
frozen 64-episode bank, opened once for model evaluation. The spent Amendment-5
outputs and both disclosed audits informed the requested protocol change; this
is a successor recipe, not independent confirmation of the original recipe.
No benchmark inputs or responses. New seeds AND realized task/request templates,
not fresh IDs alone; same procedural distribution, no new-family generalization.

# SLAB-2 Amendment 6 — successor scoped edits and one syntax repair

Registered 2026-09-07 BEFORE implementation, under Brian's explicit fix-and-rerun
instruction. Amendment5 SHA95fa7fc0 remains FAIL, its bank spent and bytes untouched.
The current instruction supersedes archived phase orchestration for this bounded
Codex implementation. Historical science/driver functions remain byte-preserved;
successor modules carry the changed protocol and reading.

All R/N/T/Q requests use the SAME scoped-function protocol: emit only the named
function in one path-labelled Python fence plus the existing report trailer.
The harness puts the function's def at column zero, retaining its body indentation
verbatim (no automatic body repair), and splices only that definition into the
current top-level file. Reject other definitions/statements; preserve unrelated
bytes. The request supplies the current target file. Existing four-space docstring /
two-space body hybrids MUST raise, not be silently normalized. Exactly ONE repair
turn for a syntax-invalid submission: exact Python exception class/message,
filename/line/offset and offending line returned with a request to correct the
same function and resubmit its trailer. Same budget/instructions in every arm,
no extra rule event, no semantic repair. Final attempt alone scores the round;
both attempts, errors, token costs and repair use are saved before aggregates.
A remaining syntax failure is breakage. Rejected malformed/scoped/capped writes
also are breakage; semantic wrong values AND runtime test exceptions are EXCLUDED
from this metric everywhere, separately reported as integration failures.

Primary is UNCHANGED: slab2_endpoint.primary, per-obligation adherence at its
scheduled first applicable change round, common parsed writes, exact-fraction
within-episode averaging before one-sided R>N sign; Holm across indent, format,
delivery at .05, DELIVERY powers PASS. Missing-as-failure and denominators reported.
The previous format result tolerates only ONE adversarial flip before loss of
significance; keep that caveat and report successor flip sensitivity separately.
No claim of superiority to prose, removed stale influence, or general competence.

Harm clause candidate (DEV calibration required before evaluation freeze):
syntax/protocol breakage CONDITIONAL ON ATTEMPTED indent-change obligations.
An attempt is observable before scoring: initial or repair target snippet contains
at least one positive body indentation equal to the requested new width (includes
mixed-width broken bodies), or the final parsed change satisfies indent. No claimed
intent inferred from prose. For each episode and each contrast R:N and T:N, use
ONLY common attempted scheduled indent changes, average binary FINAL breakage
within episode, then exact one-sided sign for greater harm; Holm over those TWO
contrasts at .05. T is the block-free reminder negative control for register-specific
harm, not a claim that reminders cannot harm. Apply IDENTICAL candidate test and
coverage rule to T:N on the eight DEV episodes BEFORE freezing eligibility;
a significant T:N result rejects calibration and STOPS. No threshold adaptation
or evaluation tuning. Require common attempted denominators in at least 75% of
episodes (6/8 DEV;48/64 evaluation) in BOTH contrasts; insufficient coverage cannot
PASS by noncompliance. Report attempted counts/missingness, all-arm unconditional
breakage, semantic integration and conditional episode rates. Noncompliant rounds
are absent from conditional risk, never counted as safe; coverage gate prevents
an ignoring arm from winning by empty denominators. This selected-population test
is descriptive of comparable attempts, not a causal adjustment or noninferiority
proof. No inherited <=1 or arbitrary practical margin. Six all-positive discordant
episodes yield p=1/64, conservative Holm .03125; five yield .0625. Thus the eight
DEV calibration has limited power and passing cannot establish absence of harm.
The full reading fails if either harm contrast signals or coverage fails, applying
the same harm requirement to the reminder control. DEV numerical calibration and
null-tail enumeration receipts must be committed before evaluation opens.

Pilot8 FIX-CONFIRMED iff all512 scheduled DEV records present, zero surviving
indentation SyntaxErrors in EVERY arm, 8/8 executing lanes in EVERY arm, and >=2
primary families with nonzero paired denominators. Determinism must pass before
main generation. Otherwise report the failing item and STOP. Harm calibration
is an additional evaluation prerequisite, not a changed FIX-CONFIRMED definition.
Pilot budget5400s including startup/replay/cleanup; no second pilot after failure.

Fresh evaluation seed namespace2026090706,64 episodes,16 rounds, R/N/T all64,
Q fixed indices00..15. Assert disjoint episode seeds, hashes, realized template
identities and content fingerprints excluding IDs against spent bank and DEV;
record full receipts before freeze. Prior system example and rule/history behavior
retained except scoped protocol. DEV tasks/schedules retain original identities.
Freeze green code and REGISTRATION.md first; isolated tracked-clean checkout,
module/source hash verification and CPU consumer smoke before GPU. Qualified vLLM
image/flags from Amendment5, C4 same-arm groups, cap2048 each attempt, seed20260906,
bf16 Qwen3-30B-A3B. Determinism eight DEV initial R payloads forward/reverse first.
Cross-run control: the SAME40 pilot7 R payloads (eight DEV, turns0,4,8,12,15),
byte-identical JSON midpoint replay with per-episode clustering; also preserve
pilot8 payloads for inspection. No universal reproducibility claim.
Evaluation cooperative41400s including cleanup, hard43200s; preserve records on
error/deadline before INCOMPLETE reading; no dropped/replaced episodes or retries.
Wait on other Stencil flags/compute; own RUNNING.flag; never signal any process;
only stop/rm own named container. Main records<=10MB per file, raw/HTTP hash receipts,
repair counts per arm, results/larger-test-v2/RESULTS.md; DEV under composition-pilot-8.
Required tests/test_focus_slab2*.py and tests/test_no_side_effect_imports.py;
explicit pathspec commits with forced result artifacts and tracked-file verification,
quick-check README and WORKLOG updates; no push. Implementation regressions cover
literal indentation shapes, splice scope, exact error/one-repair consumer, every
arm, semantic exclusion, primary equality, attempted-risk nonvacuity, negative
control calibration, bank disjointness, frozen reading and import safety.

# SLAB-2 Amendment 6b — scoped feedback and Pilot 9

Registered 2026-09-07 BEFORE code, under Brian's explicit Amendment 6b instruction.
Fit-on: none; development-on: eight original DEV episodes and committed pilot8
failure records; evaluation-on: unchanged fresh64 Amendment6 bank, model-unopened.
The original95fa7fc0 and pilot8 frozen STOP remain untouched and uninterpreted anew.
This bounded user-directed task supersedes archived phase orchestration.

Initialize scoped failures directly, never by submitting empty output to the old
executor. Every rejection reports the actual number of triple-backtick markers,
correct literal opening fence, and “emit only the function <name>, nothing else”.
Scope violations name offending extra definitions. Syntax failures retain exact
Python diagnostics and the existing one syntax-only repair; protocol rejections
receive actionable feedback for the next scheduled request, no new repair budget.
Replace the old system worked example with ONE scoped example, arm-neutral R/N/T/Q,
explicitly requesting the function shown, with no extra identity definition and no
hash before the opening-fence path. Preserve unrelated history/rules and primary.
Consumer regressions inject both observed failures, check feedback actually reaches
the next model call, and accept a corrected second submission with files preserved.

Coverage feasibility (schedule-only CPU check before registration): each DEV00–07
has TWO indent change rounds: [11,13],[11,13],[10,13],[12,13],[12,13],[12,13],
[10,13],[11,13]. Therefore maximum common-attempt episode coverage is8/8, exceeding
6/8. The requirement is achievable; pilot8's2/8 was observed compliance, not a
structural impossibility. RETAIN75% in BOTH contrasts:6/8 DEV,48/64 evaluation.
Before freeze, exercise the exact harm consumer on all8 actual DEV schedules with
compliant scoped stub responses (T:N negative control, both contrasts8/8,p=1),
empty-attempt failure, and episode-level injected harm; enumerate the null sign
thresholds. Preserve empirical pilot9 calibration, including insufficient coverage;
no outcome-driven relaxation. FIX-CONFIRMED and harm eligibility remain separate
as in Amendment6; full evaluation needs both and the<=12h projection.

Pilot9:512 records, R/N/T/Q each8x16, <=3600 GPU-held seconds including startup,
determinism and cleanup. FIX-CONFIRMED requires complete accounting, determinism,
per-lane execution8/8 EVERY arm, ZERO surviving syntax (including indentation)
errors, ZERO INITIAL round-zero rejections EVERY arm, and primary computable with
nonzero episode denominators in>=2 families. Otherwise name failures and STOP,
never open fresh64. No significance requirement on DEV primary. Preserve all
attempts and same-run per-round records. Pinned green SHA, isolated clean checkout,
source binding and CPU smoke before GPU. On eligible clean pilot, commit numerical
calibration then execute exactly Amendment6 full64 allocation/control/41400s budget
under results/larger-test-v2. No process signals, no data/bench, no push; own named
container only, shared flags, forced explicit artifact paths for local commits.
