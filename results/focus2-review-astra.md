FOCUS-2 DRAFT v2 + harness v1 — astra review, 2026-09-05

Reviewed checkout `a1eb64667f8f69e740a1d8fdc7320d827d883a81`, governing v2 at `LEDGER-PLAN.md:1889` and its CPU handoff. `git show --stat 8f4b76c` identifies exactly three implementation files: `scripts/focus2.py` (90 lines), `src/stencil/focus2.py` (2,588), and `tests/test_focus2.py` (1,093). I read those, the check-35/37/39 plumbing, the local Qwen trunk and tokenizer template, checks 34–39 READMEs, the four requested fable accuracy reviews, and the synthesis and both reviews. Historical numerical assessments below use those disclosed artifacts and independent reviews; I did not re-audit their raw response banks.

Scope and burden test: trusted but fallible implementation; block defects that can change the scientific decision, invalidate the intended history manipulation, leak, or prevent reproducible evidence. Two high findings remain in the harness; no critical finding. The text is scientifically coherent, with severe but disclosed limits on the probability of passing. This review does not register the experiment or authorize model execution.

Everything here ran on CPU, in the foreground. No model was constructed or launched, no process was signaled, and no benchmark input or sealed cohort contents were read. Only this report was written in the repository. The existing untracked `scripts/focus_check32.py` was left untouched. The legacy process/state files are under `archive/plan/`, as the handoff records; the brief's single-output restriction supersedes ledger-writing instructions.

**Validation actually performed**

The requested full command would violate the sealed-input hard rule: `tests/test_sealed_guard.py:33` calls `sealed.read_bytes()` from two tests. I inspected the test source before running and excluded precisely those readers:

```bash
CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 UV_NO_SYNC=1 UV_OFFLINE=1 \
uv run pytest -q -p no:cacheprovider \
  tests/test_focus2.py tests/test_eval_data_separation.py tests/test_sealed_guard.py \
  --deselect=tests/test_sealed_guard.py::test_sealed_ifeval_hash_matches_manifest \
  --deselect=tests/test_sealed_guard.py::test_sealed_ifeval_mode_is_read_only_after_hash_validation
```

Result: **64 passed, 2 deselected, 1 warning in 214.51 seconds**, exit 0. The warning is an existing invalid escape sequence in `scripts/b2_gsm8k.py` encountered by the source-scanning test. This is not a claim that the two sealed-file checks passed. Bytecode and pytest cache writes were disabled; pytest fixtures used temporary repositories outside this checkout.

Additional foreground, in-memory CPU checks reproduced both high findings and the terminal-token discrepancy below. I independently enumerated the power calculations using Python `math.comb`, verified the template hash, and called the real `verify_evidence()` against the actual historical files and commits: **PASS**, including the check-39 reading/source hashes and launch chronology. The immutable section hash recomputes to `5ddfd57854045bf17219ba4f1626bfc04cac9e2322c9784bb753cdec2ecbb40c`. `git diff --check` on the reviewed paths was clean. No real freeze/preflight or model compatibility success is claimed.

**Part A — text and decision logic**

The evidence is bound honestly. Check 39's receipt is prospective at `e24afd4`, recorded at `e30343d`, and is distinct from check 37's STOP. The v2 numbers match the receipt: surviving placeholder releases 60/59 versus intact 59/58; rebuilt 58/57 versus 59/58; zero versus four broken episodes per mode, with b=0, c=4 and harm p=1. Rebuilt release accuracy does not gate check 39. Its net-discordance rule is explicitly distinguished from FOCUS-2's raw h cap. The draft correctly limits the receipt to active-cue repair and explicit cancellation, discloses the change to contiguous fresh prefills, and makes no inference that check 39 proved benefit at a conflicting change.

Check 38's corrections are incorporated: inside-request means the cue and payload occupy the same user message; 27/32 versus adjacent-turn 11/32 remains a cross-check comparison with different demonstrations/cache construction and an unanswered-turn confound. The 31→12→2 account is qualified as development evidence with different lists and an unanswered filler, not a randomized causal decomposition. The ~10/32 demonstration share and 5/32 historical placement headroom are an expectation, not a proved ceiling for a four-family all-five endpoint. Complete pairs, directional reports, and the both-correct estimate are explicitly required. Check 34's descending HOLD weakness and check 36's unscaled cache differences remain visible.

The four-line text-restate template recomputes to `2658b026d6bd22d4ed460b34c543abc159e4e80ff56f367be4eaf5c035f8e8d7`. It cancels the retired rule, explicitly discourages imitation of earlier answers, restates current rules/schema/tag/obligations, and permits fact retrieval. It is repeated inside every scored request, including an explicit copy default. This is a strong, fair preselected text comparator. No evidence establishes a globally strongest wording; requiring a prompt search would undermine the frozen design. The fair claim is “beyond this strong frozen reminder,” not beyond every possible text prompt. I found no need to weaken or retune this template.

The main comparisons answer a scoped intervention question: does editing this context improve joint adherence beyond placement alone and this reminder? They do not isolate token shortening from demonstration removal, imitation from inferred rules, or a weight-circuit mechanism. The draft's scope ceiling and both-correct/delay reports are appropriate. A PASS can have a low absolute joint success rate, because there is no absolute Y floor; it establishes the registered relative improvement, not reliable control in general. A benefit confined to wrong prior answers must retain the error-cleanup reading even if the aggregate status says PASS. Secondary comparisons cannot rescue a primary failure.

There is no mathematically unreachable competence or primary gate. There are substantial false-stop probabilities, and the assistant-fact condition can deliberately veto an otherwise clear efficacy gain:

| Gate calculation | Recomputed result and interpretation |
|---|---|
| Competence 56/64 | Threshold is 87.5%; there are **12** cells, not eight: eight skills plus four defaults, 768 fixtures total. |
| Single competence cell at true p=.90/.92/.9375/.95 | Pass probabilities .813400/.932171/.982330/.995561. |
| All 12 independent cells at the same true p | Respectively .083879/.430474/.807400/.948010. These are illustrative common-p calculations, not predictions of this trunk; easier defaults/skills change the joint probability. No family dropping or outcome-driven retest is justified. |
| F6 h≤2 and exact harm p>.05 | Reachable, but the p clause adds no rejection once h≤2: its minimum over r≥0 is 1, .5, .25 for h=0,1,2. The effective veto is the raw count cap. Keep the requested p as a diagnostic; do not describe it as noninferiority evidence. |
| F6 exact one-sided upper bounds | h=0: 1.1633876%; h=2: 2.4387415%, matching v2. |
| F6 under a 1% both-only breakage probability | P[h≤2] = .527804 for n=256. At .5% it is .862105. This is stringent, not statistically impossible. |
| Practical text margin | 13/256 = 5.078125 points; 12/256 = 4.6875 and fails. |

For power, let q be the probability that the paired Y outcomes disagree, with a true **8-point Y gain**: P[b event]=(q+.08)/2 and P[c event]=(q−.08)/2. I exactly summed over D~Binomial(256,q), then b|D~Binomial(D,(q+.08)/(2q)), accepting only 2b−D≥13 and the registered exact upper-tail p at the stated alpha. These are finite-sample paired-model calculations, not a normal approximation:

| Discordance q | Margin + exact test at alpha=.05/3 | Margin + exact test at alpha=.025 | Margin + exact test at alpha=.05 |
|---:|---:|---:|---:|
| .10 | 95.27% | 95.27% | 95.27% |
| .15 | 86.87% | 89.75% | 90.74% |
| .20 | 74.59% | 79.67% | 86.53% |
| .25 | 63.58% | 69.58% | 79.58% |
| .30 | 54.60% | 60.96% | 72.39% |
| .40 | 42.14% | 48.90% | 61.31% |
| .50 | 34.42% | 40.74% | 53.21% |

The text test's Holm threshold depends on the other two p-values. Its probability of clearing its own requirement lies between the .05/3 and .05 columns; the full three-contrast PASS probability is not identified by this one contrast's q and effect. It also requires the other contrasts, competence and safety. Thus a true 8-point gain does not establish 80% power for this registration. An 8-point gain on one checkpoint is also not an 8-point gain on the all-five endpoint. The draft already says a null is neither absence nor established power; retain that sentence.

F12 has an especially sharp implication. If eviction loses every source memo, both has 64/64 assistant-fact failures; even **one** successful text-restate retrieval fails the no-greater-failure-count rule. Missing source memos fail both arms and cannot repair that difference. An invented memo can sometimes be guessed or regenerated, so this is not an unconditional mathematical impossibility. It is nevertheless likely to dominate the safety result when the retained arm recalls useful memos. This is an explicit, intentional cost veto in v2, not a coder bug or grounds for silently dropping F12. A result with efficacy benefit and that cost must report FAIL-SAFETY and both quantities; it cannot conclude that eviction lacked an adherence effect.

**Part B — blocking findings**

**FOCUS2-1 — HIGH, open: the tool fact uses a non-native Qwen chat serialization.**

Locations: `src/stencil/focus2.py:577`, `:635`, `:759`; `models/qwen3-4b-hf/tokenizer_config.json`'s `chat_template`; governing `LEDGER-PLAN.md:1913` and `:1920`.

`initial_history()` serializes a return as:

```text
<|im_start|>tool
{"tool_fact":18}<|im_end|>
```

The locally pinned Qwen template serializes a role=tool message as:

```text
<|im_start|>user
<tool_response>
{"tool_fact":18}
</tool_response><|im_end|>
```

I reproduced both strings on CPU by rendering `initial_history()` and evaluating the local Jinja template on an assistant tool call and tool response. The harness validator only validates its own invented role sequence. The existing test at `tests/test_focus2.py:223` positively asserts the non-native `<|im_start|>tool` form; it cannot establish compatibility with the actual consumer.

Why this blocks: every pilot/final episode includes this group, and tool-fact failure is a binding safety veto. Competence omits the group. A structurally unfamiliar tool exchange can therefore alter history adherence and collateral failure without being diagnosed before real execution, reintroducing the turn-format confound this study is supposed to remove. Internal role alternation is insufficient evidence of a valid Qwen tool exchange.

Exact fix: serialize the tool return with the frozen Qwen `user`/`tool_response` framing. Keep logical tool ownership and its public scope in separate metadata so eviction still preserves the whole group. Update validation, token maps and frozen renderer fixtures to check the model-facing framing. Preserve the registered historical assistant-body policy; this does not require wholesale substitution of every history with a template that strips its thinking prefill.

Required CPU regression: `test_tool_group_matches_pinned_qwen_template` must render a complete user→assistant tool-call→tool-result→assistant acknowledgement group through the actual history consumer and independently through the local tokenizer template, compare the tool-call/return framing and token IDs, and verify that all three interventions preserve the tool value and closure. Include a negative fixture containing the old raw tool-role header. Assert refusal before backend construction if the frozen renderer fixture no longer matches. No GPU test is needed to close this finding.

**FOCUS2-2 — HIGH, open: empty and capped delay answers enter “complete” clean histories.**

Locations: `src/stencil/focus2.py:623`, `:1298`, `:1306`, `:1463`, `:1538`; governing `LEDGER-PLAN.md:1919` and `:1937`.

The three shared delay generations are replayed unconditionally. `neutral_flags()` records empty/truncated/repetitive status, but neither `episode()` nor `validate_records()` enforces the prohibition on empty assistant bodies or cropped replies. `History.answer()` supplies a closing im_end even when generation hit the cap without EOS. Episode Y and breakage then aggregate only the five scored task answers.

CPU reproduction: with the real tokenizer, the first 512-delay pilot episode, an in-memory record store and a fake token-stream backend, return (a) EOS immediately for every delay, or (b) `Echo ` repeated 100 times, which the engine caps at 64 tokens. Return valid gold JSON for task requests. For (a), all three delay flags have `empty=True, broken=True`. For (b), all have `truncated=True, repetitive=True, broken=True`. **In both cases `validate_records(..., complete=True)` accepts the episode, all five arms have Y=True, and every arm's episode broken flag is False.** No files or model were needed for the reproduction.

Why this blocks: a run can count success under histories expressly forbidden by v2. The exogenous delay being shared does not repair this: its malformed or capped answer can interact with placement and eviction, and it invalidates the complete-pair interpretation. This is an unhandled protocol violation, not merely a missing descriptive column.

Exact fix: after persisting each actual delay response, require a nonempty visible body and a genuinely generated valid terminal before replay. If either fails, preserve the response and stop with INVALID for the prohibited history, or INCOMPLETE for a resource interruption already covered by that status; do not drop/redraw the episode, retry for a nicer answer, or synthesize a successful completion. Apply the same predicate in `validate_records()` so offline analysis cannot accept such a run as complete. The predicate need not reject a harmless period acknowledgement; F9's period prohibition applies to scored task outputs. Publish the recorded repetitive-delay flag without inventing an additional eligibility threshold.

Required CPU regressions: parameterize `test_invalid_delay_blocks_replay_and_complete_analysis` over empty EOS and cap-without-EOS. Exercise both execution and the actual offline consumer. Assert that the raw delay is retained, no dependent task prefill is scheduled, the fixed denominator is retained, and no COMPLETE/PASS certificate or analysis is possible. Include valid nonempty/EOS and EOS-on-the-cap controls, and preserve the existing test that wrong SET/HOLD answers remain unscreened. This closes the gap without selecting on task success.

**Remaining implementation assessment and nonblocking items**

The main intervention logic is substantially faithful: three current-request arms and two old-slot arms, retirement of cue text using the same event map, two actual common SET/PREHOLD replies, fixed task-event ownership, removal independent of correctness, no restoration at BACK, no HOLD/NEUTRAL2 refresh except text-restate, and empty-KV contiguous re-prefill. The event masks use public checkpoint/scope ownership; flags and memo extraction feed records/checkers rather than `intervene()`. Four family checkers, all-five Y, separate fact checks, F9, F11, fixed F12 denominators, Holm, signed paired tables and asymptotic paired intervals are present. Real backend prefill ignores the fake-backend testing metadata and forwards only token IDs; I found no answer or score fed into real model inputs by that interface.

The generator has fixed streams/counts and rejects semantic collisions without redraw. Template generation computes gold values only to validate checkers/caps; it does not insert target values into recaps. No benchmark file read or fitting path exists in the inspected FOCUS-2 execution path. The requested source-scanning separation tests pass. Historical check-39 outcomes are used only for the disclosed repair prerequisite. These statements are about the inspected sources, not a claim that the manifest is a security boundary against malicious arbitrary dependencies.

| Item | Severity / disposition |
|---|---|
| Terminal-token repair edge | **Medium.** `History.answer()` stores END=151643 outside `body`, and eviction preserves it. A retired END-terminated task becomes `assistant\n.<\|endoftext\|><\|im_end\|>\n`, reproduced on CPU. Check 37's body extends up to the normalized im_end, so its whole-body replacement also removes a preceding endoftext. Match that boundary: retain raw terminal metadata in the record, remove non-closure terminal tokens with the retired body, and test EOS/END/capped histories against the check-39 text primitive. Ordinary im_end-terminated answers already produce the correct period/header/closure form. No observed frequency of this edge is claimed. |
| Development coverage manifest | **Medium; freeze prerequisite remains open.** `validate_banks()` accepts all coverage labels with an empty fingerprint list; I reproduced acceptance of that manifest and all 2,672 generated payload fingerprints. The tests deliberately use it as fabricated provenance. It does not establish coverage of checks 31–39. Require the actual outcome-free manifest before freeze; a compact per-source input count/hash is sufficient evidence that coverage labels are populated. Do not open historical response banks to create it. |
| Model assets in Git | **Medium; cut unnecessary implementation burden before the real freeze.** `member()` requires Git membership and reads both worktree and `git show` contents in memory for every dependency, including the 7.5-GiB converted checkpoint. The checkpoint, 4B tokenizer/config files and imported 1.7B default config are all currently untracked and explicitly ignored. The fake positive fixture replaces them with tiny text files. Current preflight therefore cannot use the real local assets as they stand. Commit provenance descriptors with source revision, path, size and a streaming hash for external model assets; keep Git membership for source/readings/registration artifacts and bind the small configs. Document that distinction prospectively instead of forcing multi-gigabyte model blobs into Git. Verify real asset resolution/hashing on CPU before any model constructor is reachable. This is disclosed unfinished integration, not an unnoticed efficacy leak. |
| Resume | **Medium capability limitation, no scientific block by itself.** There is stage-to-stage continuation through certificates, but no interrupted-stage resume: `execute_stage():2384` rejects any existing destination, even one with valid completed records. Tests check refusal, not resumption. Raw partials are preserved and can be analyzed; that is safe but not “resume.” If resume is required, add only continuation from verified completed requests with cumulative allocation accounting and no regeneration/reselection; otherwise explicitly retain the one-attempt/INCOMPLETE policy. Do not add a broad retry framework. |

Budget controls are cooperative before load, prefill and decode. The 16-cell pilot uses every memo path for conservative timing, preserves raw costs, and projects 256 final episodes from the worst cell with 25% reserve and a load allowance. Stage certificates are recomputed from raw records. The third both-only broken episode stops further episodes; pilot counts are not pooled into final counts. The fake tests establish these control paths, not actual six-hour feasibility or peak memory. With 7,296 final generations, 456 pilot generations and 768 competence generations, the fixed design has **8,520 generation calls** including replay-delay generation; real timing remains necessary.

Two small interpretation choices should remain explicit at freeze. The immutable source section is still titled DRAFT; the later committed registration/launch record must explicitly promote that snapshot, as the manifest-based preflight expects, rather than pretending the source header changed. Also, `score()` enforces semantic JSON structure and exact values, not whitespace compactness. If “compact” in the prompt is intended to be a scored unchanged constraint, add a direct test; otherwise define it as a prompting instruction and keep semantic JSON scoring. Neither justifies a new experimental arm or an outcome-driven threshold change.

Keep the five-arm design, fixed denominators, source-validity reports, immutable request rows, committed evidence checks and targeted tests. Cut bulk model Git requirements and claims of resume that the code does not implement. Do not add more repair variants, a benchmark stage, a no-answer fleet or a prompt optimization loop to close this review. The two high findings need renderer/consumer fixes and CPU regression tests, followed by verification of the outstanding real freeze prerequisites.

VERDICT (A), registration readiness of the v2 scientific text: **SOUND**. Evidence binding, fair text comparator, statistical rules and restrictive safety interpretation are coherent. This does not approve the currently unfinished registration package or authorize model execution.

VERDICT (B), readiness for competence + pilot on the real trunk: **SOUND-WITH-FIXES**. Do not launch until FOCUS2-1 and FOCUS2-2 are fixed and their consumer tests pass, and the actual development manifest, model-asset binding, approved registration and committed launch receipt are in place. The 64 passing CPU tests do not close those gaps.
