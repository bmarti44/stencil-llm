# Current issues review — sol (spec adversary)

Date: 2026-09-02

## Verdict

**The standing general-improvement claim is not currently supportable.** The sealed
single-turn result is a registered negative, not a small positive: the effect is
`4/1024 = +0.390625` points, the exact one-sided McNemar/binomial probability is
`P[Binom(114, .5) >= 59] = 0.389438`, and the treatment caused nine more
truncations. It misses all three registered requirements: `+2` points, `p < .05`,
and no excess truncation (`BENCH-WAVE-PLAN.md:638-674`;
`results/qwen/b3-deficit-conf-s0.json:2-21`). Per the registered stop-loss, the
single-turn IFEval line is closed.

The surviving evidence is narrower. Unamplified KV pinning recovered
`(31-15)/(41-15) = 16/26 = 0.61538` of a synthetic eviction gap. That supports a
**memory-retention** mechanism with qualifications. It does not support the
amplification claim: `pinned_wave` had degeneration in 13/20 sessions and 12/20
truncations (`results/ledger-kv-verify2-sol.md:32-44,62-74`). The EVF hazard line
is also properly stopped: held-out AUCs are 0.48-0.52 and the mechanism-specific
aged lift was only `3.52 - 2.11 = 1.41` points (`WORKLOG.md:2095-2124`).

The honest successor claim, if future gates pass, is therefore:

> A target-blind instruction ledger with KV retention improves compliance with
> active, aged constraints under context pressure on specified multi-turn
> benchmarks, without increasing stale-constraint adoption or validity failures.

Do not call that “general instruction-following improvement,” and do not call
unamplified pinning a “wave” unless amplification independently beats an
exact-column control without degeneration.

Severity below means: **critical** invalidates the present claim or permits a
repeat of a severe integrity breach; **high** blocks credible confirmation;
**medium** materially limits interpretation or reproducibility; **low** is
cleanup that does not change the conclusion.

## Recomputed facts that govern the decision

| Quantity | Recomputed value | Consequence |
|---|---:|---|
| Sealed single-turn discordance | 59 fixes, 55 breaks, 114 total | Exact one-sided `p = 0.389438`; gate fail |
| Sealed score lift | `(59-55)/1024` | `+0.390625` points, not `+2` |
| Excess truncation | `12-3` | `+9`; safety gate fail |
| Full-909 linkability ceiling | `619/671` | `0.9225037` |
| Selections required for 0.90 coverage | `ceil(.90*671)=604` | Must select `604/619 = 0.975767` of linkable constraints; at most 15 linked misses |
| Uniform top-2 projection | reported `0.8773` overall | 2.27 points below the registered coverage gate; it is a projection, not the preflight ceiling |
| SALIENCE-2 current blind seed 4 | `TP=76, FP=5, FN=10` | precision `0.938272`, recall `0.883721`, F1 `0.910180`; recall gate fail |
| Legacy salience blind audit | `TP=47, FP=4, FN=16` | precision `0.921569`, recall `0.746032`; unsuitable for a broad automaticity claim |
| KV pin recovery | `(31-15)/(41-15)` | `0.615385` of eviction gap |
| Pinned-control difference | `(31-20)/56` | `+0.196429`, descriptive because controls were not exactly matched |
| EVF mechanism-specific aged lift | `3.52-2.11` | `+1.41` points, below the registered `+2` target |

The exact CPU-only current-runner preflight produced 909 conversations, 1,805
turns, 671 eligible constraints, and 619 linkable constraints. This agrees with
the round-6 verification (`results/ledger-reverify6-sol.md:40-54`). The brief's
`0.877` must not be labeled “linkability”: it is the uniform model-free top-2
selection projection. Coincidentally, `0.877` is also the separate buried-set
SALIENCE-2 recall recorded at `src/stencil/salience2.py:54-55`.

## 1. Single-turn failure requires a claim and benchmark reset — **CRITICAL** (A)

**Evidence.** The registered confirmation demanded an absolute lift of at least
2 points, exact one-sided McNemar `p < .05`, and no excess truncation/timeouts;
failure closes the single-turn line (`BENCH-WAVE-PLAN.md:661-674`). The actual
base/wave counts are 879/1024 and 883/1024, with 3 versus 12 truncations
(`results/qwen/b3-deficit-conf-s0.json:2-21`; `WORKLOG.md:2279-2283`). The
standing plan itself requires preregistered gates and cross-benchmark evidence
(`AGENTIC-PLAN.md:3-7`).

**Resolution.** Preserve this as an honest boundary result: amplification does
not materially improve single-turn IFEval under the registered configuration.
Redirect the next confirmation to the regime the ledger was designed for:
aged, still-active constraints under multi-turn context pressure. Run the
following ladder, in this order.

1. Finish the frozen 113 Multi-IF slice only as the registered falsification
   screen. If any validity gate fails, stop. If it does not falsify, run the
   frozen 909 cohort unchanged. Because the legacy finder was built using
   Multi-IF text (Issue 4), label any success “in-domain architecture evidence,”
   not benchmark generalization.
2. Use an **unconsumed IFBench multi-turn split** as the first external,
   programmatically scored confirmation. The existing IFBench items used for
   transfer evaluation are no longer untouched (`src/stencil/salience2.py:35-39,
   1105-1113`); obtain and hash a disjoint release/split before any finder work.
   The [official IFBench repository](https://github.com/allenai/IFBench) is the
   authoritative source.
3. Use **SEQUOR** for the 50-turn add/replace setting, but make only a secondary
   claim until either a deterministic-verifier subset is frozen or a blinded
   human audit validates its LLM judge. Its long histories and replaced
   constraints directly test aging and stale-instruction behavior
   ([paper](https://arxiv.org/abs/2605.06353),
   [official repository](https://github.com/deep-spin/SEQUOR)).
4. Use the rule/compiler-testable portion of **MultiCodeIF** as the second
   independently authored confirmatory family; exclude judge-only items from
   the primary endpoint ([official repository](https://github.com/SYSUSELab/MultiCodeIF)).
   CCTU is the appropriate later tool-using/long-prompt challenge, but only
   after the agentic timing-selector issue below is resolved
   ([official CCTU repository](https://github.com/Junjie-Ye/CCTU)).
5. Use forced-eviction RULER-style synthetic sweeps only as a mechanistic stress
   diagnostic, never as the second “real benchmark”
   ([official RULER repository](https://github.com/NVIDIA/RULER)). MMMT-IF is
   scientifically relevant but multimodal, so adapting it to the current
   text-only trunk would change the benchmark; defer it to a registered
   multimodal extension ([paper](https://arxiv.org/abs/2409.18216)).

Before generation, register dataset/config/code/model/tokenizer hashes, exact
arms, exclusions, sample size and power, and these gates:

- **Primary efficacy:** on active constraints originating at least one turn
  earlier, intervention minus base is at least +2.0 adherence points and its
  conversation-clustered one-sided 95% lower confidence bound is above zero.
- **Mechanism specificity (co-primary):** intervention minus an exact-column,
  position-matched non-ledger control is at least +2.0 points with the same
  clustered lower-bound rule. A base-only win is not wave-mechanism evidence.
- **Strong-baseline noninferiority:** neural/KV intervention is no more than 2
  points worse than free text re-append, matching `LEDGER-PLAN.md:48-61`.
- **Age/eviction:** the +2/lower-bound efficacy gate must pass in the
  preregistered aged/evicted stratum; fresh constraints cannot rescue it by
  pooling. Report fixed age bins (1, 2-4, 5-9, >=10 turns) and forced-compaction
  status.
- **Update safety:** the one-sided 95% upper bound on treatment-minus-base stale
  adoption and general validity loss is <=1 point. Superseded constraints are
  scored separately from active ones.
- **Generation safety:** treatment truncations and timeouts may not exceed base,
  and each arm must remain <=2%; also report response length and repetition-4.
- **Automaticity:** target-blind finder precision and recall each >=0.90 on each
  untouched benchmark; end-to-end selected eligible coverage >=0.90. No manual
  curation or benchmark-specific verifier may feed selection.
- **Generalization:** two independently authored benchmark families must each
  pass all co-primary gates; no pooling rescues an individual failure. Use a
  prespecified one-sided alpha of .025 per family (or an equally conservative
  frozen multiplicity correction).

**Owner:** Brian decides whether to narrow the claim to ledger/KV retention and
approves the benchmark order. The orchestrator freezes the protocol and hashes;
the sol coder implements deterministic adapters and power calculations.

## 2. The current ledger primary does not identify a wave-specific effect — **HIGH** (A/F)

**Evidence.** The runner computes and reports the specificity control
(`scripts/ledger_eval.py:539-545`), but `primary_claim_valid` does not require
neural treatment to beat it (`scripts/ledger_eval.py:556-565`). By contrast,
the stopped EVF plan correctly states that a positive which does not beat
ablations is not mechanism evidence (`EVF-PLAN.md:178-182,263-264`). The ledger
plan also says the control comparison is to be reported “alongside” the neural
arm rather than used as a gate (`LEDGER-PLAN.md:190-197`).

**Resolution.** Do not amend the running study after outcomes exist. If the 909
passes, it can establish performance/noninferiority under its registered
estimand, not a wave-specific cause. Make the exact-matched specificity gate in
Issue 1 co-primary in every untouched successor benchmark. Separate names in
all reports: “ledger text intervention,” “KV pinning,” and “KV amplification.”

**Owner:** orchestrator controls claim language; Brian approves the causal
estimand; sol coder implements exact matching and the clustered contrast.

## 3. Do not lower or redefine the 0.90 coverage gate around the 909 — **HIGH** (B)

**Evidence.** The plan explicitly registers `>=0.90` **selected eligible
constraint** coverage after earlier reviewers showed that an under-covered
selected subset could launder a Simpson reversal (`LEDGER-PLAN.md:248-258`;
`scripts/ledger_eval.py:440-442,499-503`). It further says the 113 slice can
reject but cannot establish the claim, any edit reopens review, and the full
909 is confirmatory (`LEDGER-PLAN.md:280-285`). The full preflight ceiling is
619/671 = 92.2504%, but passing requires selecting 604 of those 619 linkable
constraints = 97.5767%. A uniform model-free top-2 policy projects 87.73%
overall (`results/ledger-reverify6-sol.md:40-54`).

**Decision.** **Do not amend the gate pre-launch, and do not tune the finder on
the 113 or 909.** The 0.90 gate is difficult because it protects the estimand;
that is not grounds to move it. Complete the frozen slice. If it falsifies, or
if the frozen full run later misses coverage, record a coverage/instrument
failure and close this registration. It is not a negative mechanism result,
but it is also not “valid except coverage.”

For a successor only, improve the finder on synthetic data and independently
authored corpora, freeze it, rerun blind component gates, and preregister a new
untouched cohort. If the 113 is used for any tuning, the remaining 796 cannot
silently stand in for the original 909 registration: define and power a new
796-only estimand or acquire fresh data. Never lower 0.90 to 0.877, and never
replace overall eligible coverage with “coverage among linkable” without
explicitly narrowing the scientific claim.

**Owner:** orchestrator enforces the freeze and records the disposition; sol
coder improves the finder only in a newly registered line; Brian approves any
new estimand.

## 4. SALIENCE-2 fails its blind recall gate and the target-blindness problem is broader — **HIGH** (C/F)

**Evidence.** The plan requires blind precision and recall each >=0.90 and a
LOCO F1 >=0.90 (`LEDGER-PLAN.md:97-115`). Recorded blind recalls are 0.854 and
0.884 even though precision is 0.95/0.94; LOCO passes and IFBench transfer is
only 0.68 (`LEDGER-PLAN.md:207-214`; `src/stencil/salience2.py:41-56`). The
current seed-4 counts recompute to precision 76/81 = 0.93827 and recall 76/86 =
0.88372. The strict gate is correctly left as an expected failure in
`tests/test_salience2.py:670-676`.

There is also target exposure. Both v1 and v2b build training material from
Multi-IF turn-2/3 constraints and recorded responses
(`src/stencil/salience.py:360-417`; `src/stencil/salience2.py:35-39,1105-1113`).
The current runner and deployment package use the legacy finder. Its blind
audit recomputes to precision 47/51 = 0.92157 and recall 47/63 = 0.74603. Thus
current Multi-IF can test an in-domain system architecture, but not finder
generalization.

**Decision rule.** Do **not** accept 0.88 as a pass, and do **not** do another
same-benchmark regex patch round. Permit one bounded v3 only if all of the
following are fixed before labels are opened:

1. Freeze architecture, threshold, seeds, and two independently authored blind
   corpora that exclude IFEval and the target confirmation benchmark.
2. Require precision >=0.90 and recall >=0.90 separately on **each** corpus;
   report Wilson intervals and require their one-sided 95% lower bounds >=0.85
   as an uncertainty guard. No averaging across corpora or seeds.
3. If either corpus fails, stop feature patching and replace the estimator
   class (for example, a span tagger trained only on synthetic/unsealed data),
   then begin a new preregistration.

Changing the estimand is defensible only if Brian explicitly narrows the product
to insertion-only constraints. In that case, register precision/recall on the
fixed insertion-family list and abandon the broader persistent-requirement
claim; `LEDGER-PLAN.md:102-108` specifically requires detection beyond purely
additive clauses, so a narrower estimand cannot retroactively pass Gate 1.

**Reproducibility qualification — MEDIUM.** The refit claim is recorded, but the
small weights artifact contains no complete training-corpus/cache manifest, and
the large feature cache is ignored. The literal-string guard cannot establish
that binary caches are IFEval-free (`WORKLOG.md:2262-2272`;
`tests/test_sealed_guard.py:1-26`). Commit a small provenance sidecar containing
all corpus hashes, exclusions, source/weights/cache hashes, and a count/hash
audit showing no sealed examples. Do not commit the 914 MB cache merely to prove
this.

**Owner:** Brian chooses general versus insertion-only scope; sol coder builds
the target-blind v3 and provenance manifest; orchestrator freezes and audits the
blind corpora.

## 5. `pinned_wave` is already unsafe; one staged probe is the maximum defensible rescue — **HIGH** (D)

**Evidence.** V2 counts are full 41/56, evicted 15/56, pinned 31/56,
pinned-control 20/56, and pinned-wave 36/56. The nominal pinned and control
budgets were both 1,290 columns, but unique matched counts were 1,274 versus
1,290 and exact in only 5/20 sessions. Contexts were only 339-814 tokens, not
the intended long, turn-200 setting. Provenance omitted tokenizer,
determinism, benchmark, causal-moment, EVF, vendor and other hashes; resume also
trusted existing records without validating record identity
(`results/ledger-kv-verify2-sol.md:76-115`;
`scripts/ledger_kv_probe.py:46-65,72-104,123-148`). Most importantly,
`pinned_wave` caused degeneration in 13/20 sessions and truncation in 12/20;
the raw +5/56 over pinning is not creditable (`results/ledger-kv-verify2-sol.md:62-74,117-150`).

**Resolution: minimal kill-or-credit probe.** Treat dose 3 as killed. If Brian
wants one rescue, register exactly one two-stage experiment on 40 new, disjoint
long-context sessions:

- **Calibration 20:** fixed doses `{0.25, 0.5, 1.0}` plus pin-only. Select the
  smallest nonzero dose that improves aged-cell compliance by >=2 points while
  producing zero excess truncation/degeneration versus pin-only and no material
  repetition-4 or response-length shift. If none qualifies, kill amplification.
- **Confirmation 20:** freeze the selected dose and run full, evicted, pin-only,
  exact-control, and pin+wave arms. Construct the control from a set of unique
  non-ledger columns matched exactly to the ledger set's cardinality and coarse
  position bins; assert equality and disjointness per session before generation.
- Store raw prompt/context IDs, generated token IDs, per-record config hash, and
  hashes for model, tokenizer, runner, vendor code, benchmark, determinism,
  causal moments and all upstream artifacts. On resume, fail rather than skip a
  record whose identity/hash does not match.
- Credit amplification only if pin+wave minus pin-only is >=2 points with a
  conversation-clustered one-sided 95% lower bound above zero, the exact-control
  contrast also passes, and there is no excess truncation or degeneration. Any
  failure permanently kills wave-on-pinned for this model/configuration.

Regardless of that result, preserve unamplified pinning as a separate live
hypothesis. Increase context length/turn age enough to demonstrate actual
eviction pressure; the present short synthetic contexts cannot establish the
claimed long-context operating regime.

**Owner:** sol coder implements exact control/provenance and a power check;
orchestrator seals stage boundaries; Brian decides whether the single rescue is
worth the GPU budget.

## 6. Agent isolation is advisory, not mechanical — **CRITICAL** (E)

**Evidence.** The prior invariant breach is explicit: the SALIENCE-2 builder
loaded sealed IFEval data before the refit (`WORKLOG.md:2262-2272`). The later
unauthorized harvester launched CUDA work and a watchdog that interfered with
other jobs (`WORKLOG.md:2274-2298`). The current static guard scans only literal
sealed-path text in selected `.py` files (`tests/test_sealed_guard.py:1-26`), so
path composition, shell, caches, and direct reads escape it. More seriously,
the coding wrapper explicitly uses `--dangerously-bypass-approvals-and-sandbox`
(`tools/run_codex_agent.sh:123`); its diff allowlist runs after the fact and
cannot prevent a read or a GPU process (`tools/run_codex_agent.sh:98-166`).

**Resolution.** Put every agent and every descendant process inside a
root-owned, fail-closed OS boundary, not a prompt rule:

1. Launch through a systemd transient unit or container with a private device
   namespace, `DevicePolicy=closed`, no `/dev/nvidia*`, `NoNewPrivileges=yes`,
   and a mount namespace in which the sealed file is inaccessible. Reviewers
   receive a read-only repo plus one exact writable report bind mount; coders
   receive only their allowlisted worktree. Environment variables
   `CUDA_VISIBLE_DEVICES=-1` and `NVIDIA_VISIBLE_DEVICES=void` are useful
   backstops, not the security boundary.
2. Refuse to start unless the same restricted identity can prove that opening
   `/dev/nvidiactl`, `/dev/nvidia0`, and
   `data/bench/ifeval_input_data.jsonl` returns `EACCES`/`ENOENT`, and that
   `torch.cuda.is_available()` is false. Add this as an integration test of the
   actual wrapper/namespace, not a mocked unit test.
3. Ensure children inherit the cgroup/mount namespace and the unit has no
   lingering processes when the agent exits. Remove the sandbox-bypass path
   from normal wrappers; require a separately logged Brian-approved maintenance
   entry point for exceptional access.
4. Keep the literal-source scan as defense in depth and extend it to shell and
   config files, but never cite it as proof that the sealed set was unreadable.

This is critical because another prose instruction cannot falsify the already
observed failure mode.

**Owner:** orchestrator/admin implements and enforces the wrapper; sol coder
adds the end-to-end isolation test; Brian alone authorizes any exceptional
unsealed/GPU-capable execution context.

## 7. The stated stray-record range is factually wrong; quarantine the actual two — **MEDIUM** (E/F)

**Evidence.** A read-only Git object audit finds 106 tracked corrected-harvest
records. Sessions 012 through 028 are tracked and byte-identical to `HEAD`;
session 012 entered in commit `f8fc450` and session 028 in `d8b3a1b`. They are
not the unregistered, uncommitted residue described in the brief. The actual
ignored/untracked records are:

- `session-088.json`, SHA-256
  `b7cf6af03bb24ebec76a821503585a905c84ead54d29528959c3de125093cc0e`
- `session-089.json`, SHA-256
  `530f3b7d1708f57e65981fb4dcfecab3763271d220cde2cd5c5ee4bf34c0d5b4`

The canonical metadata identifies the harvest configuration and registered
index ranges (`results/qwen/e2-corrected-harvest/meta.json:1-35`), while the EVF
line has already stopped (`WORKLOG.md:2095-2124`).

**Resolution.** Do nothing while the registered GPU job is active. Afterwards,
do not delete or quarantine 012-028. Move 088/089 recoverably out of the
canonical harvest directory into an incident quarantine with the hashes above,
the originating command/session, and an explicit `EXCLUDED` marker. They must
never enter fitting, summaries, sample counts, or a revived E2 analysis. If the
incident record still asserts 012-028, correct it to distinguish “requested by
the rogue process” from “new bytes actually produced.” Do not resurrect the
futile EVF/E2 line to make use of them.

**Owner:** orchestrator performs the post-job quarantine and incident-log
correction; Brian decides retention duration. No coder action is needed.

## 8. The current agentic plan cannot supply the long-horizon benchmark yet — **HIGH** (F)

**Evidence.** G1 admission requires base compliance in the 20-80% band, oracle
lift >=15 points, conflict-adoption reduction >=50%, and no validity degradation;
a failed recheck ends the program (`AGENTIC-PLAN.md:11-23`). The current prefix
base rate is 61/64 = 95.3125%, outside the band, and the redesign changed the
site/dose and reduced validity from 61/64 to 60/64
(`results/qwen/agentic-g1.json:3-14`;
`results/qwen/agentic-g1b.json:16-42`). The prior adversarial review therefore
correctly barred progression to G2 and called for a separately registered
timed-selector successor (`results/agentic-g1-review-sol.md:4-30,32-50,82-91`).

**Resolution.** Do not use G2/CCTU as the immediate escape from the IFEval
failure. Either honor the G1 stop or register a new successor program with a
learned, target-blind timing selector, new cases, and the original admission
logic. Old 64-case outcomes are development data. G2 begins only after the new
G1 independently passes.

**Owner:** Brian decides whether to fund the successor; orchestrator enforces
the phase boundary; sol coder implements it only after preregistration.

## 9. Deployment is a research preview, not the proved mechanism — **MEDIUM** (F)

**Evidence.** The package amplifies in-context instruction spans and uses the
under-recalling legacy finder; it does not implement the demonstrated KV
pinning mechanism. Its own README reports approximately 0.75 finder recall and
that registered evaluation is incomplete
(`deploy/stencil_wave/README.md:43-63,108-119`). Empty-ledger bitwise identity is
a useful safety property, but it says nothing about positive efficacy.

**Resolution.** Keep the Hub push blocked. Namespace/visibility is not the
scientific blocker. Publish only as an explicitly labeled experimental preview
after provenance is complete, or wait until one external confirmatory benchmark
passes. Do not market this package using the 0.615 pin-recovery result because
the deployed implementation is not the pinning intervention.

**Owner:** Brian decides preview versus hold; orchestrator audits README claims
against the exact shipped mechanism.

## Ranked top-five actions

1. **Mechanically isolate all agents from GPUs and the sealed set** before any
   further delegated work; prove the boundary with the wrapper-level denial
   test. — orchestrator/admin, sol coder, Brian exception authority.
2. **Freeze claim and experiment scope:** record the IFEval gate failure, finish
   the 113 only as falsification, and run the 909 unchanged only if every frozen
   gate survives. Never lower the 0.90 coverage gate. — orchestrator.
3. **Kill dose-3 `pinned_wave`;** either run the single staged exact-control
   rescue above or retire amplification and carry forward only unamplified KV
   retention. — Brian decision, sol coder.
4. **Build a genuinely target-blind salience/finder successor** with complete
   provenance and two external blind corpora; do not accept 0.88 or tune on the
   113/909. — sol coder, orchestrator.
5. **Preregister the external aged-constraint battery and causal gates:**
   unconsumed IFBench multi-turn plus a rule-verifiable MultiCodeIF subset, with
   SEQUOR as long-horizon secondary until its scoring is independently secured.
   Require both benchmark families to pass individually before using the word
   “generalizes.” — Brian, orchestrator, sol coder.
