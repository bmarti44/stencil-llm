# Sol xhigh: prospective four-project source-replay screen

Read SPEC.md, DATA-CONTRACT.md and the latest canonical review. Fit-on none.
Scientific projects are authored independently by Kimi K3/Ollama; do not read
actual authored project files or any old bank during implementation. Synthetic
CPU stand-ins exercise software only. Root owns data/launch/docs, you own code.
The two-call qualification is terminal; never rerun it or change its frozen code.

Allowlist (six new files only):
- src/stencil/source_replay_screen.py
- scripts/source_replay_screen.py
- tools/run_source_replay_screen.py
- tests/test_source_replay_screen.py
- tests/test_source_replay_screen_driver.py
- tests/test_run_source_replay_screen.py

Implement only the accepted 4-project x3-round H/S/R comparison. No general
memory framework, training, new model, changed prompt/cap, retry or intervention.
Reuse unchanged source_replay.py builders, NativeSourceSelectorClient,
NativeToolClient, consume_action, run_checks and owned run_lifecycle. Reuse
qualified low-level receipt/deadline/path/review helpers where their actual
semantics fit, but do not call fixture-specific qualification orchestration or
its 600-second freeze validator with disguised screen inputs. Never edit a
reused helper to serve this screen. Narrow new screen-specific glue is expected.

Data and actual CPU preflight:
- Validate exactly DATA-CONTRACT, including finite/strict JSON types, all source
  and request IDs/order/byte bounds, existing targets and a revisited target,
  allowed AST subset and module sizes, three rounds, exact private/public
  fields, check visibility/intervals/uniqueness, and active conflicting cases.
- Keep source-grounding review separate from structural acceptance: passing
  reference tests or author tags do not prove that sources justify expectations.
  Root supplies independent source-review hashes before a model launch.
- Support an explicit root-authored input manifest listing exactly four project
  paths/hashes in authored order; no copied/edited project JSON or extra project
  fields. Choose and document the smallest concrete manifest/receipt schema.
- Implement one actual CPU preflight entry point with injected tokenizer in
  tests and the existing local tokenizer in actual CLI use after code review.
  Apply references sequentially using the exact action consumer; execute all
  active public and private cases once per round in the real sandbox. On the
  final reference workspace, apply the final obsolete mutant and execute its
  designated active private retirement case; it must fail and reference pass.
  Preserve actual records, timing and hashes, not aggregate-only output.
- Count the native serialized reference argument plus one EOS; require at least
  128 tokens of headroom under1024 for every reference. Record tokenizer/code,
  project/public/private/source-review identities, all reference/mutant results,
  C=3*sum(active public+private case counts across12rounds), and maximum observed
  per-check CPU time q. Preflight failure is no model launch. Runtime consumes
  the bound receipt and does not repeat references or use them in prompts.
- Read the immutable qualification call receipts for r=max(render HTTP times),
  verified against their hashes and successful qualification evidence. Freeze
  projection 600+2041.199447651+max(120,C*q+48*r+60)+60 <=3000 before execution.
  Short fixture generation speed is never substituted. Report all costs.

Runtime and schedule:
- Maintain exactly three H/S/R states per project, each initialized once from
  the same initial module.
  Preserve each arm's actual module/history thereafter, including failed edits.
- Project/round arrays use zero-based enumeration for rotation only:
  offset=(project_zero_index+round_zero_index)%3; rotate [H,S,R] left by offset.
  External authored round indices stay1,2,3. Run projects in authored order,
  rounds in order, arms in rotated order, no model concurrency. Select directly
  before S; exactly36worker+12selector planned calls. Record all48slots before
  first model exposure with attempted/unattempted states, then update durably.
- Add each round's four original user messages and request to each arm's
  permanent history. Eligible selector sources are all earlier original source
  messages and requests, excluding the current request and all generated history.
  Selector is fresh every S attempt; no module/test/feedback/private inputs.
- H has no supplement. S uses selected0..4 originals; R uses the last min(4,N).
  Use the exact qualified renderer, including an empty evidence list for valid
  empty S selection. Supplements are archived in issued messages only. Preserve
  original history, actual assistant/tool calls and work envelopes permanently.
- Run every active check, including still-active earlier checks, on each arm's
  actual state after its attempt. Even rejected patches receive check records
  on unchanged state, but applied=false always makes that round unsuccessful.
  Actual public feedback exposes only action status and executable public case
  results, never hidden outcomes/metadata. Use internal rule_ids=[] only.
- HTTP/schema/render/token/context/cap/deadline failures make whole INCOMPLETE;
  preserve partials and unattempted slots, never continue with fake empty sources.
  Valid native tool calls rejected by the action consumer are completed failed
  attempts and leave the prior workspace intact. Applied wrong code persists.
  A valid stop at its cap is allowed. No retry, reference reset or arm copying.
- Native client pair deadlines are min(global driver deadline, now+181), with
  one shared180-second render+generation allowance using the unchanged reserve.
  Archive exact raw bodies/requests/render/response/schema/token IDs/usage/times,
  genuine feedback, state changes and actual attempts through the consumers.
- Record intervention events explicitly and actual commands; no empty log alone
  claimed as proof of no intervention. Authoring/review/technical operations
  are separate disclosures, not in-task hand selection or code repair.

Outcome and owned launch:
- Implement exactly SPEC's practical gate, no significance or equivalence test:
  S>=9/12rounds and>=3/4finals; S-H>=2rounds; at least2projects improved, none
  worse; S>=Rrounds; S including selectors <=2xH tokens and HTTPtime; zero
  in-task interventions. Require complete eligible schedule and nonzero H cost.
  Retain project trajectories, all-three/final/round outcomes, and new/retained/
  retirement failures with actual coverage. No promotion of R on S failure.
- New launcher defaults to dry plan, supports standard five driver flags via
  unchanged owned run_lifecycle, original pinned image/model/container flags,
  3000whole/600startup/60cleanup. Effective startup also clamps to whole-cleanup.
  Register owned processes, enforce existing resource exclusivity, do not touch
  unowned processes, preserve flags if cleanup is unproven, exclusive run path.
  Partial and positive publication must obey the whole deadline including cleanup.
- Bind every live consumed dependency (including renderer.py), current data,
  preflight, qualification evidence and required review subject hashes. Use
  latest applicable canonical approval for current exact subjects; stale accepts
  must not authorize new code/data. Reuse the narrow existing review parser with
  screen-specific required subject sets if suitable; no general review engine.
  Root/reviewer supply actual accepted records only after stable code/data audit.
- Runtime terminal reports INCOMPLETE/INELIGIBLE/complete gate disposition with
  original evidence intact. Failed scientific gate parks the recipe. A pass is
  only permission to prepare a larger fresh evaluation, not goal completion.

Tests first through the real consumers: strict project validation; cumulative
active/expired and retirement cases; sequential reference and mutant vacuity;
public/private leakage; arm isolation/failure persistence/ephemeral evidence;
exact schedule and48attempt slots; native failures/no retries/shared deadlines;
project-level gate negative controls and both cost denominators; stale/mismatched
approval/receipt rejection; actual owned lifecycle cleanup and late publication.
Use narrow synthetic stand-ins, not actual Kimi data. Do not build a test that
only mirrors an implementation formula or stub the semantic consumer under test.

Run only these six/new targeted files plus existing source-replay tests when
reuse integration changes justify them; no broad legacy/full suite. Ruff check,
format and diff checks, direct absolute --help/dry plan from/tmp. No model,
actual tokenizer, GPU/container/API/Ollama, package installation or scientific
preflight during coding. Main guards on all scripts. Do not commit. Send root
exact red/green evidence, changed hashes, concrete input/preflight/freeze CLI
schema and any real ambiguity promptly; continue unaffected work independently.
