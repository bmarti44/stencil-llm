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
