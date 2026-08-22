# Stencil

An oscillatory control-field gating pathway for transformers, built and validated at toy scale with deterministic proof obligations, then scaled only after every gate is green.

Save this file as `PLAN.md` at the repo root. This document is the single source of truth. The agent executes it phase by phase and never proceeds past a red gate.

## Amendment log

- v1.5, 2026-08-21, human-authorized (standing directive: the plan must be executable largely autonomously, with adversarial sol reviews plus the deterministic verifications keeping the work honest in place of human checkpoints). Added the Autonomy policy to Section 2b. Wherever this plan previously required human sign-off for honesty reasons, the requirement becomes: a written amendment or decision that passes an adversarial sol@xhigh review before taking effect, recorded in the ledger. Human touchpoints are reduced to the short list in the Autonomy policy. This entry is itself the standing human authorization for that delegation.
- v1.4, 2026-08-21, human-directed (resolve all high/critical findings from adversarial review round 1, docs/reviews/plan/{science,spec,process}.md), executed by the orchestrator before Phase 0 began and before any experiment ran. Major corrections: (1) Task A's null is now the exact cue-blind Bayes optimum — the old "chance = 1/16" claim was mathematically wrong for k < 16 — with a Latin-rectangle rule construction making that optimum exactly 1/k for k <= 16 and 1/16 for k = 32, and G3.1 rethresholded per cell. (2) The oscillator's conservation claim and Phase 2 energy tests now target the discrete invariant that symplectic Euler actually conserves, not the continuous energy, and closed-form tests compare against the exact discrete solution. (3) A causal next-token alignment contract added to Section 6 (the answer token was previously allowed to leak into its own prediction). (4) H4 reframed as claim-limiting empirical side-channel measurement — the "16 gates cannot carry 32 bindings" capacity argument was information-theoretically unsound. (5) H2 reworded: M1 vs M1b isolates dissipation; B2 is a separate architectural baseline, and a decision rule is registered. (6) Controller tensor shapes fully specified (c_t = final cell [y;z]); param-match claim corrected; period_max now parameterized to bracket the longest task delay at every scale. (7) Zero-grad proof test extended to all vocab logits, all answer positions, multiple seeds, and trained checkpoints, with explicit mask/window conventions. (8) Eval protocol frozen (10k fresh sequences, final checkpoint, per-cell min-seed bars). (9) Appendix D rewritten as an exhaustive outcome table; gate states green / green-with-M1b-primary / red defined; rule 3 vs Appendix C contradiction resolved (thresholds frozen once a phase's runs begin, no exceptions). (10) Section 2b hardened: finding IDs with reviewer-concurrence closure, write-ahead ledger triggers, gate acceptance checklist, review serialization, orchestrator direct edits restricted to non-implementation files, Phases 5-7 brought under review, pilot-benchmark budgeting. Tooling hardened to match (severity-aware acceptance, append-only round history, drift hard-fail, repo lock). All threshold edits comply with operating rule 3 since no phase has started.
- v1.3, 2026-08-21, human-authorized, before Phase 0 began. (1) Added Section 2b, the execution toolchain and adversarial review protocol: all implementation code is written by the Codex CLI running model `gpt-5.6-sol` ("sol") at medium reasoning effort, all reviews are performed by sol at xhigh reasoning effort as adversarial reviews that carry forward their prior review context, findings are graded low/medium/high/critical, and the orchestrating agent verifies and resolves every high and critical finding before the work is accepted. (2) Added tools/ (codex wrapper scripts copied from the distiallation repo and adapted) to the repo layout. (3) Added a "Work log and ledger" section, placed before the appendices, recording all completed work, current findings, and next steps, so a restarted session can resume from this file alone. A separate LEDGER.md is explicitly deferred; the ledger lives here for now. No thresholds changed.
- v1.2, 2026-08-21, human-authorized, before Phase 0 began. Added the plain-language summary section below. Added README.md to the repo layout as a governed artifact carrying the same explanation plus a table mapping every repository component to it and a gate status table. Extended operating rule 5 so each green-gate commit updates that status table. Added README placement to Phase 0 tasks. Required a closing plain-language results section in the Phase 7 report. No thresholds changed.
- v1.1, 2026-08-21, human-authorized, before Phase 0 began and before any experiment ran. Changes driven by a prior-art survey. (1) B1 respecified as the published Qwen G1 headwise gate, upgrading the stateless baseline from a strawman to a production mechanism. (2) M1b, an oscillator with learnable damping in the style of D-LinOSS, promoted to a first-class variant, and H2 reframed from a binary to a dissipation spectrum with literature priors stated. (3) Task M, an MQAR anchor cell following the Zoology task structure, added for literature calibration and as a channel-purity discriminator (new H4). (4) Prior-art map (Appendix F) and reuse inventory (Appendix G) added, and the Phase 7 report now requires a lineage section. (5) Fairness fix, all recurrent variants now initialize in a slow-forgetting regime with learnable dissipation. All threshold edits comply with operating rule 3 since no phase has started.
- v1.0, 2026-08-21, initial plan.

---

## Plain-language summary

This is the project explained without jargon. README.md at the repo root carries the same explanation plus a table mapping every repository component to it. This file governs, README.md explains, and rule 5 keeps its status table current.

A new brain theory holds that knowledge and the sense of the current task live in different mechanisms. The brain's wiring stores what it knows, while slow electrical waves sweeping across that wiring decide which circuits are switched on at each moment. Today's AI models have no such split. What a model knows and what job it is currently doing share the same memory and compete for space, which is why assistants drift off their instructions during long jobs.

Stencil builds the split, a tiny separate wire that carries only the job description and nothing else.

Result one is proof the wire works, designed so it cannot be faked. An instruction is buried so far in the past that the model's normal memory provably cannot reach it, a fact verified by an exact-zero-gradient calculation before any training. The normal model is then provably capped at a guessing ceiling computed in advance (it still sees the question, so it can guess better than blind chance, and we compute exactly how much better), and the model with the wire scores far above that ceiling, so the instruction must have traveled through the wire.

Result two is that the wire is a dial. Reading it reveals which task the model believes it is on. Overwriting it switches the model's task on command.

Result three is a check that the wire does not make a somewhat larger model worse at ordinary language.

Fine print. Tiny models, simple puzzle tasks, instructions that appear in the input. Passing every gate proves the mechanism exists, shows where it lives, and shows it can be steered. It does not prove it improves large models, and every prediction was frozen in this file before experiments ran, so failures are informative too.

---

## 1. Hypothesis and proof structure

Theoretical anchor. Miller, Brincat, and Roy (J Neurosci 2026, doi 10.1523/JNEUROSCI.0711-26.2026) argue that slow oscillatory fields select which neural subpopulations process information, while synapses store the representations themselves. The transformer translation tested here is a slow, stateful, oscillatory pathway that multiplicatively gates attention heads, separate from the content stream.

Related ML anchors the agent may consult for equations only, not for scope creep. LinOSS (arXiv 2410.03943) and D-LinOSS (arXiv 2505.12171) for the oscillator cells. Wave-RNN (arXiv 2309.08045) for the waves-as-memory result. The full prior-art map is Appendix F.

### Claimed contribution (scoped by the prior-art survey)

Every individual component here has an ancestor. Per-head sigmoid gating after SDPA is deployed in production (Qwen Gated Attention). Recurrent carriers next to sliding-window attention exist at scale (Samba, Jamba family). Damped oscillatory recurrence shaping gated attention exists at 7B (Mega, Megalodon, via CEMA). Slow controllers multiplicatively modulating a target network exist in the RNN and continual-learning literature (NM-RNN, hypernetworks). What does not exist, per the survey, is the combination claimed here, namely (a) a strict control/content separation where the recurrent state writes nothing into the residual stream and only modulates, (b) an oscillatory controller with a tunable dissipation spectrum, and (c) a provable-necessity harness, meaning exact-zero-gradient reachability tests, bitwise identity controls, and causal control-state patching as pass/fail criteria rather than rhetoric. The contribution is the combination and the proof method, and the writeup must say exactly that.

### Hypotheses (pre-registered)

- H1 (necessity). On a task constructed so the controlling cue is information-theoretically unreachable through attention, the base model and the stateless Qwen-style gate are pinned at the cue-blind Bayes optimum by construction — the best achievable accuracy given the operand but not the cue, which the registered rule construction makes exactly 1/k for k <= 16 and 1/16 for k = 32 (see Task A) — while the oscillatory-gated model solves the task far above that ceiling. Success above the ceiling can only flow through the control pathway. Because B1 is now the published G1 mechanism, whose gains the Qwen paper attributes to nonlinearity and sparsity, any M1 minus B1 delta isolates statefulness specifically.
- H2 (dissipation spectrum, replaces the old H2a/H2b binary). M1 and M1b are the same cell class and provably differ only in dissipation (M1's damping is a frozen zero buffer, M1b's is learnable; a bitwise test enforces that this is the only difference), so the M1 vs M1b comparison isolates dissipation cleanly. B2 is a separate architectural baseline from the first-order decay family — it differs in recurrence order, depth, and nonlinearity, not only in energy handling — and its results are read as "what a simpler fading-memory architecture achieves," never as a third point on a controlled dissipation axis. Literature prior, stated in advance so the result reads honestly either way: D-LinOSS showed rigid dissipation limits representation and that forgetting is crucial for long-range reasoning, and Megalodon's damped complex rotation works at 7B, so the prior is M1b >= M1 >= B2 on the registered estimand. Decision rule, registered now: the primary estimand is mean exact-match accuracy over seeds {0,1,2} at Task A (2048, 32); the prior ordering is supported if each adjacent pairwise gap is >= 3 points in the prior's direction, refuted if any adjacent pair is reversed by >= 3 points, and inconclusive otherwise. Task B's switching curves and stale-rule rates (Phase 5) are secondary descriptive evidence for the M1 vs M1b dissipation question only.
- H3 (mechanism). The control state linearly encodes the active rule, and causally patching the control state from a rule-i context into a rule-j context flips the model's behavior to rule i.
- H4 (channel use, claim-limiting). The 16 real-valued gates per position are NOT a proven information bottleneck — fp32 scalars at every position could in principle carry arbitrary content, and no capacity bound is claimed. H4 is therefore an empirical measurement of whether trained models in fact route content through the gates, operationalized by Task M. Interpretation is asymmetric by design: high beyond-window Task M accuracy through the gates is positive evidence of a content side-channel and forces the strict control/content separation claim in Section 1 to be withdrawn or qualified in REPORT.md (not merely recorded); low accuracy is consistent with a rule-only channel but proves nothing about capacity and must be reported as "no evidence of content routing," never as proof of purity.

### The determinism trick

The base model uses causal sliding-window attention with window `w` and depth `L`. Information from position `s` can reach position `t` through attention only if `t - s <= L * w`. Place the cue at distance `N > L * w` before the query. Then

- B0-local (no gate) and B1 (stateless Qwen G1 gate) provably cannot see the cue at query time. B1's gate at layer l reads that layer's post-norm input, which depends on at most `(l-1) * w` positions back, and the gated head outputs reach at most `l * w` back, so the full-depth bound `L * w` holds and the ceiling is the cue-blind Bayes optimum. This is verified by an exact-zero-gradient test, not by benchmark deltas.
- M1, M1b, and B2 receive the cue through their recurrent control state. Any accuracy above the cue-blind optimum is attributable to the pathway.

Mask and distance conventions, fixed. The sliding-window mask allows position `t` to attend to position `s` iff `0 <= t - s <= w - 1` (self plus `w - 1` back), implemented as a boolean mask whose excluded entries become exact `-inf` before softmax, so excluded attention weights are exactly zero. The true maximal lag after `L` layers is therefore `L * (w - 1) < L * w`; using `L * w` as the unreachability cutoff is deliberately conservative. All non-attention operations (pre-LN, RoPE, MLP, readout) are strictly tokenwise and cannot extend reach. Cue distance is always measured in token positions from the cue token to the input position whose logits predict the answer token (the answer-decision position, see Section 6); generators assert that this distance strictly exceeds `model.receptive_field() = L * w` for every unreachable placement, which absorbs every off-by-one.

This converts "our thing scores higher" into "the baseline cannot succeed and ours does," which is the deterministic proof at toy scale. Note for the writeup, the beyond-window argument itself is not novel, B'MOJO (arXiv 2407.06324) states that a window-restricted transformer drops to random guess when key-value pairs fall outside the window. What is claimed as new is operationalizing it as a verification harness.

### Kill criteria

If Gate G3 fails after one pass through the root-cause tree in Appendix D, stop. Write `results/POSTMORTEM.md` explaining which hypothesis died and why, commit, and end the project. Do not tune hyperparameters to rescue a dead hypothesis. A clean negative result gets published too. Per Appendix D item 3, if M1 fails necessity but M1b passes, the project does not die, pure conservation dies, and M1b becomes the primary variant with that result recorded prominently.

---

## 2. Operating rules for the agent

1. TDD. Every phase lists tests to write first. Write the failing test, watch it fail, implement, watch it pass. No implementation before its test exists.
2. No mocks. This repo is pure computation on real tensors. There is nothing to mock. If you feel the urge to mock something, the design is wrong. Raise it instead.
3. Never weaken a test or a threshold to make a gate pass. Thresholds in Appendix C change only by amendment (review-gated per the Autonomy policy) to this file, and only before the affected phase's first run has been launched. Once a phase's first run launches (a write-ahead ledger entry records that moment), its thresholds are frozen permanently — there is no post-hoc edit path, with or without rationale.
4. Root cause before knobs. On a G3 failure, execute the decision tree in Appendix D before touching a hyperparameter. On any other gate failure (G0, G1, G2, G4, G6), diagnose the root cause, record it in the ledger, fix only the diagnosed defect, and rerun; after three failed fix attempts on the same gate, stop and escalate to the human. Never weaken the failing test.
5. One commit per green gate, message format `gate(GN): <one-line result>`. Gate states are green, green-with-M1b-primary (G3 only, per Appendix D.3), and red; the commit message and README row must name the exact state. Intermediate commits are fine but gates are the milestones. Each gate commit also updates the corresponding row of the status table in README.md, whose status values are restricted to: not started, in progress, green, green-with-M1b-primary, red, killed.
6. Determinism is a feature with tests. Any change that breaks the determinism test (Section 3) is a regression, full stop.
7. On a real ambiguity in this spec, take the most conservative reading, record the choice in the ledger, and flag it for the next review round (Autonomy policy, v1.5); ask the human only at the policy's mandatory touchpoints. Do not invent scope. Anything not specified here and not forced by a test is out of scope for v1.
8. Reuse per Appendix G only. Reference implementations inform equations and fixtures. Do not vendor or port external training code into this repo. (The codex wrapper scripts in tools/ are process tooling, not training code, and are exempt.)
9. Toolchain per Section 2b. All implementation code is written by sol via the Codex CLI, all reviews are sol adversarial reviews at xhigh effort, and no work unit is accepted with an open high or critical finding.
10. Ledger discipline per the Work log and ledger section. Update the ledger in the same working session as the work it records, before ending the session.

---

## 2b. Execution toolchain and adversarial review protocol (added v1.3)

Roles, fixed:

- Orchestrator: the Claude Code session driving this plan. It decomposes phases into work units, writes briefs, launches sol, verifies review findings, resolves what must be resolved, maintains this file's ledger, and makes gate/commit decisions. It does not write implementation code directly.
- Coder: the Codex CLI (`codex exec`) running model `gpt-5.6-sol` at `model_reasoning_effort=medium`, invoked via `tools/run_codex_agent.sh` with a brief in `tools/codex-agents/<name>.md`. Writes all implementation code and tests, following TDD per rule 1.
- Reviewer: the same model at `model_reasoning_effort=xhigh`, invoked via `tools/run_codex_review.sh <phase> <topic> <threshold>`. Performs adversarial review of the work, scored 0 to 100, writing to `docs/reviews/<phase>/<topic>.md`.

Review protocol:

1. Every review is adversarial: the reviewer's job is to break the work, not to bless it. Findings are graded low / medium / high / critical.
2. Context carry-over: each review round's prompt includes the prior rounds' full review file verbatim (the wrapper does this), so the reviewer always sees what it previously found, what was claimed fixed, and scores the delta. Round logs are append-only.
3. Finding identity and closure: a finding's identity is `<topic>#<number>` and its number is stable across rounds. The orchestrator independently verifies every high and critical finding (reads the code, reruns the test, or reproduces the claim), then either fixes it or prepares a refutation with evidence. Closure requires reviewer concurrence: only a subsequent reviewer round may mark a finding `(resolved ...)` or `(refuted ...)` after checking the fix or the refutation evidence itself; the orchestrator never edits reviewer-authored review files. `tools/check_review_scores.py` treats any unmarked high/critical finding as open and fails regardless of score. A human may override a deadlocked finding; the override is recorded in the ledger with rationale.
4. Resolution scope: fixes to implementation code and tests go through a coder brief (TDD per rule 1). The orchestrator may directly edit only non-implementation files: this file, README.md, configs, docs, and process tooling under tools/. Work is accepted only when zero high/critical findings remain open and the review score meets the threshold (default 90). Medium and low findings are recorded in the ledger and may be deferred with a stated reason.
5. Cadence: at minimum one review per phase before its exit commit — including Phase 5 (topic `tradeoff`) and Phase 7 (topic `report`), which have no test gate but still require review acceptance — plus a review of any change to this file's governed content (hypotheses, thresholds, architecture). The gate's own tests (Appendix C) remain the scientific pass/fail authority; review scores gate code quality and cannot substitute for a green gate, and vice versa.
6. Gate acceptance checklist, all items required before a gate commit: (a) gate tests green (or the exact Appendix D.3 state recorded), (b) the phase's review at or above threshold with zero open high/critical findings, verified by `tools/check_review_scores.py`, (c) ledger entry written, (d) README status row updated, (e) commit message names the gate state. No item may be waived by the agent.
7. The wrappers' file-write policy is mandatory: reviewers write only their canonical review file; coders write only what their brief scopes. Uncontained drift is a hard wrapper failure, not a warning. Wrapper runs are serialized per repo via `.review.lock`; never run a coder and a reviewer concurrently in this repo, and never edit repo files while a wrapper is running (its drift restorer will clobber the edits).
8. Budget discipline: before launching any multi-run matrix, run one pilot cell, record measured steps/sec and peak memory in the ledger, derive per-run and total wall-clock estimates, and set each run's timeout to 4x its pilot estimate. A matrix projected within 2x the phase's stated budget may launch with the projection recorded in the ledger; beyond 2x, pause for the human.

Autonomy policy (v1.5). The project runs autonomously by default; honesty is enforced by the adversarial review protocol above and by the deterministic proof tests, not by human checkpoints. Concretely: wherever this plan says an amendment or decision is "human-authorized," the autonomous path is that the orchestrator drafts the amendment with rationale, a sol@xhigh review of it is run (topic `amendment`, same wrapper), and it takes effect only once that review is accepted with zero open high/critical findings; the ledger records it and the human can audit asynchronously. Threshold freezes at first run launch remain absolute — no review can undo a freeze. Ambiguities in this spec (old rule 7) are resolved autonomously by choosing the most conservative reading, recording the choice in the ledger, and flagging it for the next review round, rather than blocking on the human. The only mandatory human touchpoints are: (1) a review finding deadlocked after two full resolve-or-refute round trips, (2) a gate still red after three fix attempts (rule 4), (3) projected spend beyond 2x a phase budget, (4) renting external compute or any spending beyond this machine (Phase 7), and (5) anything destructive or outward-facing. Everything else proceeds without asking.

---

## Work log and ledger (added v1.3)

Purpose: a restarted session must be able to resume from this file alone. This section is append-only within an entry's day, newest entry first. A standalone LEDGER.md is deliberately deferred; if this section outgrows the file, migrating it out requires an amendment-log entry.

Each entry records: date, actor (orchestrator / coder / reviewer), work done, findings or results (review finding IDs with severity and open/resolved/refuted status), and next steps. Long-running work uses write-ahead entries: BEFORE launching any codex agent, review, or training run, append an entry with the exact command, log path, expected artifact paths, and (once known) the codex session or process id, then update or supersede it when the work lands. Entries for runs record run_id, config path, and git SHA. Update triggers: launching background work (write-ahead), completing a work unit, finishing a review round, a reviewer closing or the orchestrator refuting a high/critical finding, flipping a gate, the first run launch of each phase (freezes that phase's thresholds per rule 3), and ending a session with work in flight (record exactly where things stand and the exact next command). A cold-started session resumes by reading this section top down, then reconciling: check the listed log paths and artifact paths for work that finished or died after the last entry, and check `git status` for uncommitted state.

### Ledger

- 2026-08-21, orchestrator. Review round 1 landed: plan/science 38, plan/spec 32, plan/process 54, all FAIL, 30+ findings. Every high/critical was independently verified by the orchestrator; the standouts confirmed by direct calculation: science#1/spec#1 (cue-blind null is 1/k, not 1/16 — G3.1 would have failed a correct baseline), science#2/spec#3 (symplectic Euler does not conserve the continuous energy — the registered G2 tests were unpassable), science#6/spec#2 (causal target shift unspecified — answer-token leakage), science#3/spec#14 (H4 capacity claim unsound). Resolved via amendments v1.4 (all high/critical resolutions: corrected null + Latin-rectangle rules, discrete-invariant tests, causal alignment contract, H4 claim-limiting, H2 decision rule, tensor shapes, eval freeze, Appendix D rewrite, governance hardening) and v1.5 (autonomy policy per human directive). Tooling hardened: check_review_scores.py now blocks on open high/critical findings, review_round_tracking.py enforces append-only rounds, run_codex_review.sh hard-fails uncontained drift and serializes via .review.lock; unit-checked. Deferred with reason (medium/low): process#11 partial (coder-brief schema — will be defined with the first Phase 0 brief), science#10 caveat registered in the patch test rather than redesigning to boundary-state patching (recorded in Phase 4 spec), spec#9 partially (Phase 1 fixtures are generate-then-hand-verify per the amended test spec). Next: commit the pre-registration baseline, run review round 2 for concurrence on all resolutions, then Phase 0.
- 2026-08-21, orchestrator (write-ahead, superseded above). Launched review round 1: `bash tools/run_codex_review.sh plan {science,spec,process} 90`, logs /tmp/codex-plan-*.log, outputs docs/reviews/plan/*.md.
- 2026-08-21, orchestrator. Amended plan to v1.3 (toolchain, review protocol, this ledger). Copied and adapted codex wrapper tooling from the distiallation repo into tools/ (run_codex_agent.sh, run_codex_review.sh, review_diff_allowlist.py, review_round_tracking.py, check_review_scores.py, codex-prompts/_common-header.md); defaults now gpt-5.6-sol, coder effort medium, reviewer effort xhigh, severity scale low/medium/high/critical. Launched sol@xhigh adversarial review of this plan (phase `plan`, topics: science, spec, process). Findings: pending. Next: verify and resolve all high/critical plan-review findings, then begin Phase 0.

---

## 3. Determinism contract

Every training or eval entrypoint must satisfy the following.

- Single source of randomness. One `torch.Generator` per component (data, init, dropout is disabled entirely in v1), seeded from the config.
- `torch.use_deterministic_algorithms(True)` and `CUBLAS_WORKSPACE_CONFIG=:4096:8` set in a shared `determinism.py` imported by every entrypoint.
- fp32 for all toy-phase training and all proof tests. bf16 is permitted only in Phase 6 and never in proof tests.
- Every run writes `results/<run_id>/config.json`, `metrics.jsonl`, and `env.json` (git SHA, torch version, GPU name, driver). `run_id = sha256(config)[:12]`.
- `scripts/verify_determinism.py` trains seed 0 for 200 steps twice in-process and asserts the loss sequences are bitwise identical. Runs in CI (`make verify`) and as a pytest marker `@pytest.mark.determinism`.

Hardware note. Bitwise reproducibility is guaranteed same-machine same-config. The target machine is a DGX Spark (GB10, aarch64, 128 GB unified memory). All toy runs are single-device fp32 and fit trivially.

---

## 4. Repo layout and stack

```
stencil/
  PLAN.md                  # this file, governs
  README.md                # plain-language explanation, component map, gate status table, explains
  Makefile                 # gate targets: make gate-0 .. gate-4 and gate-6 run that gate's tests/checks;
                           #   no gate-5 (Phase 5 and 7 exit on reviewed artifacts); make verify = determinism
  pyproject.toml           # uv-managed, deps: torch, pytest, ruff, numpy, matplotlib
  src/stencil/
    determinism.py
    data.py                # task generators (Task A, Task B, Task M)
    oscillator.py          # unified damped-oscillator cell, decay cell, sequential oracle + scan impl
    gates.py               # gate projection and application, incl. Qwen G1 headwise for B1
    model.py               # base transformer, variant assembly
    train.py               # single-run trainer
    evaluate.py            # exact-match eval at answer positions
    probes.py              # linear probes on control state and on gate vectors
    patching.py            # control-state causal interventions
  scripts/
    run_matrix.py          # runs the full model x seed x task grid from configs
    make_report.py         # aggregates metrics.jsonl into results/summary.md tables
    verify_determinism.py
    gen_jax_fixtures.py    # one-time oracle fixture generation, see Appendix G
  tools/                   # codex wrappers (Section 2b): run_codex_agent.sh, run_codex_review.sh,
                           #   check_review_scores.py, review_*.py, codex-prompts/, codex-agents/
  docs/reviews/            # canonical adversarial review files, <phase>/<topic>.md
  configs/                 # one json per cell of the experiment matrix
  tests/
    fixtures/              # committed npz reference trajectories from JAX oracles
  results/                 # gitignored except *.md at its root (summary.md, tradeoff.md, mechanism.md,
                           #   REPORT.md, POSTMORTEM.md, data_samples.md, params.md) and results/figures/
```

README.md is a governed artifact, provided alongside this plan. Material changes to hypotheses, variants, tasks, or gates require a matching update to its mapping table in the same commit, and every green gate flips its status table row per rule 5. If the two files ever disagree, this file wins and README.md has a bug.

Stack decisions, fixed. Plain PyTorch, no Lightning, no Hydra. Configs are flat JSON loaded into a frozen dataclass. `uv` for env, `pytest` for tests, `ruff` for lint. No wandb in v1, metrics are JSONL plus generated markdown tables. Sliding-window masking via plain SDPA with an explicit boolean mask, which is the deterministic default. FlexAttention or other kernels are out of scope for v1.

---

## 5. Architecture spec

### 5.1 Base transformer (shared by all variants)

| item | value |
|---|---|
| type | decoder-only, pre-LN, causal |
| d_model | 256 |
| layers L | 4 |
| heads H | 4 (head_dim 64) |
| d_ff | 1024 (adjusted per variant for param matching, see 5.5) |
| positional | RoPE |
| attention | causal sliding window, w = 64 (B0-full uses full causal) |
| dropout | none |
| vocab | 64 synthetic tokens (see task spec) |
| params | ~3.2M |

Attention receptive field after L layers is `L * w = 256` positions. This number is load-bearing. Recompute it in code (`model.receptive_field()`) and use it in tests, never hardcode 256 in tests.

### 5.2 Control pathway (M1 and M1b, unified cell)

A stack of oscillatory state-space cells running left-to-right over the token embeddings, independent of the transformer's residual stream. Independence is deliberate. The control state is then a deterministic function of the input sequence alone, which makes causal patching in Phase 4 clean.

Continuous system per cell, diagonal `A >= 0`, diagonal damping `G >= 0`, input `u_t` = token embedding (256):

```
y'(t) = z(t)
z'(t) = -A y(t) - G z(t) + B u(t)
```

Discretization is symplectic in the conservative part with the damping treated implicitly, so `G = 0` recovers the conservative IMEX update through the identical code path:

```
z_{k+1} = ( z_k + dt * (-A y_k + B u_k) ) / (1 + dt * G)
y_{k+1} = y_k + dt * z_{k+1}
```

Numerical facts, registered so the tests are honest (v1.4). This update is symplectic Euler with implicit damping. With `G = 0` it does NOT conserve the continuous energy `H = z^2 + A y^2` — at `dt = 1` and period 8 the per-step excursion of `H` is tens of percent — it exactly conserves a modified discrete quadratic invariant (for symplectic Euler on `y'' = -A y`, the shifted energy `H_d = z^2 + A y^2 - dt * A * y * z`; derive and verify the exact form for this code path during implementation and record it in a code comment). "Conservative" throughout this plan means: the discrete invariant is exactly conserved, hence trajectories are bounded for all time and nothing is forgotten; it does not mean pointwise conservation of the continuous `H`. Stability requires `dt * sqrt(A) < 2`; period_min = 8 gives `dt * sqrt(A) = 2 * pi / 8 ~ 0.785`, satisfied with margin, and `A` is re-checked against the bound after training. Closed-form comparisons in tests use the exact discrete solution (matrix power of the one-step map in fp64), not the continuous solution.

Verify both the undamped and damped forms against the LinOSS (arXiv 2410.03943) and D-LinOSS (arXiv 2505.12171) equations during implementation. If they differ materially, record the discrepancy and the chosen resolution as a review-gated amendment (Autonomy policy) — external code never silently overrides the governing equations. Cross-check numerically against committed JAX fixtures per Appendix G (pinned commits and versions listed there).

Tensor shapes, fixed (v1.4). Cell 1: `B_1 in R^{64 x 256}` reads token embeddings; states `y_1, z_1 in R^64`, initialized to zeros. Between cells: GLU `u_2 = (W_a y_1) * sigmoid(W_b y_1)` with `W_a, W_b in R^{64 x 64}`. Cell 2: `B_2 in R^{64 x 64}` reads `u_2`; states `y_2, z_2 in R^64`, zeros init. The control output is `c_t = [y_2 ; z_2] in R^128` — the final cell's full state, no extra readout (the "readout" is the gate projection in 5.3). Phase 4's probed and patched object `c` is exactly this `c_t`. Per-cell parameters `a_raw, g_raw in R^64`. No biases on `B_i`, `W_a`, `W_b`.

| item | value |
|---|---|
| oscillator pairs m | 64 (state dim 128: y and z each 64) |
| cells stacked | 2, with a GLU nonlinearity between, per LinOSS block structure |
| dt | 1.0 (frequencies absorb scale) |
| frequency init | `sqrt(A)` log-spaced so periods span [period_min, period_max] = [8, 2 * longest task delay at this scale] (toy: [8, 4096]; Phase 6: [8, 16384]) |
| A parameterization | `A = softplus(a_raw)` elementwise, keeps A >= 0 |
| G parameterization | `G = softplus(g_raw)` elementwise, keeps G >= 0 |
| G in M1 | frozen buffer of exact zeros (not a parameter) |
| G in M1b | learnable, `g_raw` init -9 (G ~ 1.2e-4) |
| B, readout | dense, standard init |

The log-spaced period range must bracket every delay used in the tasks at the scale being trained, which is why period_max is parameterized rather than fixed. This is the "slow control field" claim made concrete. Frequencies are learned but initialized slow. The M1b damping init is deliberately near-conservative (retention over 2048 steps roughly 0.7 at init) so early training matches M1 and gradient descent discovers useful dissipation, which is the fair test of H2, rather than initializing M1b already forgetting.

### 5.3 Gate application (recurrent variants)

Control output `c_t` (dim 128 from final cell's y) maps to per-layer, per-head gates:

```
g[l, h, t] = 2 * sigmoid(W_g[l,h] · c_t + b_g[l,h])      # scalar per (layer, head, position)
head_out[l, h, t] *= g[l, h, t]                           # after attention, before W_O concat
```

16 gates total (4 layers x 4 heads). Gates initialize near 1 (`b_g = 0` gives g = 1.0 at c = 0, and init W_g small so early training matches baseline behavior). MLP gating is out of scope for v1.

### 5.4 Variants

| id | attention | gate pathway | purpose |
|---|---|---|---|
| B0-full | full causal | none | ceiling reference, efficiency comparison |
| B0-local | window 64 | none | provably-at-chance control |
| B1 | window 64 | Qwen G1 headwise: per layer, `g[l,h,t] = sigmoid(w[l,h] · x_norm[l,t])` where `x_norm[l,t]` is that layer's post-norm attention input, gate multiplies the head output after SDPA | provably-at-chance beyond the window, isolates statefulness against the published, deployed stateless mechanism (Qiu et al., NeurIPS 2025, see Appendix F). Headwise granularity chosen to match M1's 16 scalar gates. The paper's strongest elementwise form is a record-only extra, see Appendix E |
| B2 | window 64 | diagonal decay SSM: `s_{k+1} = λ s_k + B u_k`, `λ = sigmoid(raw)` learnable, init 0.999, state dim 128, gates via 5.3 plumbing | fixed-form first-order decay, the fading-memory pole of the dissipation spectrum |
| M1 | window 64 | oscillatory cell (5.2), G frozen at 0 | exact conservation pole |
| M1b | window 64 | oscillatory cell (5.2), G learnable | learned-dissipation point, the literature-favored regime |

Six variants. All share the base transformer code path. B0 variants must literally be M1 with the gate module set to `None`, not a separate model class. M1 and M1b must be the same cell class differing only in whether `G` is a frozen zero buffer or a parameter. B2 is a deliberately different architecture (first-order, no oscillation, no GLU stack) and is compared as such per H2's v1.4 wording. Init fairness note, B2's λ init moved from 0.99 to 0.999 in v1.1 so the variants with learnable dissipation (M1b, B2) start in a slow-forgetting regime and learn their forgetting rate; M1's dissipation is frozen at zero by design as the conservative pole.

### 5.5 Parameter matching

Counting rule: `count_params()` counts all trainable parameters (frozen buffers such as M1's `G` excluded, embeddings included). With the v1.4 shapes the additions are roughly: M1/M1b pathway ~31k (B_1 16384 + GLU 8192 + B_2 4096 + a_raw/g_raw 256 + gates 16 x 129 = 2064), B2 ~35k (B 32768 + λ 128 + gates 2064), B1 ~4k (16 x 256 gate vectors) — exact values come from code, not this paragraph. Configs for the other variants widen `d_ff` until all six variants match within 1.0 percent of the largest; the chosen `d_ff` per variant and the six exact counts are written to `results/params.md` (committed) when configs are generated in Phase 2. A test asserts the match from the actual configs.

---

## 6. Task spec

All generators live in `data.py`, are pure functions of `(config, seed)`, and yield `(tokens, loss_mask, metadata)`. Vocabulary is partitioned into disjoint ranges (Appendix B). Disjointness is asserted in tests.

Causal alignment contract, fixed (v1.4). The model reads `tokens[0..T-1]`; `logits[p]` predicts `tokens[p+1]`. `loss_mask[p]` is true iff `tokens[p+1]` is an answer token, so the answer token itself is never an input to its own prediction. Training loss is cross-entropy of `logits[p]` vs `tokens[p+1]` at masked `p`; eval exact-match compares `argmax logits[p]` to `tokens[p+1]` at the same positions. The answer-decision position is `p` (the input position immediately before the answer token), and all cue distances and reachability assertions are measured to `p`. Miniature example, Task A with N=2: tokens `[cue, d, d, QRY, x, ans]` at positions 0..5; `loss_mask = [F, F, F, F, T, F]`; the model predicts `ans` from `logits[4]` (input `x`); cue distance is 4.

### Task A. Cued rule application with delay

```
[cue_i] [d_1 ... d_N] [QRY] [x] [answer = rule_i(x)]
```

- Rules are k fixed permutations of the 16-symbol operand alphabet, sampled once per dataset seed with a Latin-rectangle construction (v1.4): sample a uniformly random 16 x 16 Latin square with the dataset-seed generator; for k <= 16 the rules are its first k rows; for k = 32, two independently sampled Latin squares stacked. Each row is a permutation, and for every operand `x` the k rule outputs are all distinct (k <= 16) or exactly balanced two-per-answer (k = 32). Exact functions, exact scoring.
- Cue-blind null, exact by construction (v1.4). A model that sees `x` but not the cue faces k equiprobable, per-x-distinct (or balanced) answers, so its Bayes-optimal accuracy is exactly `1/k` for k <= 16 and exactly `1/16` for k = 32. The old flat "chance = 6.25 percent" claim was wrong for k < 16 and is retired. Per-cell nulls: k=2 -> 50%, k=8 -> 12.5%, k=32 -> 6.25%. `data.py` exposes `cue_blind_bayes(config)` returning this value, and G3.1 thresholds are null + 2 points per cell (Appendix C).
- Distractors are uniform over the distractor range, sampled independently of the rule. Zero mutual information with the rule by construction, asserted by a generator test (rule resampled with distractors held fixed produces every rule with correct frequency).
- Grid: `N in {128, 512, 2048}`, `k in {2, 8, 32}`, where N counts distractor tokens; the cue-to-decision distance is N + 2 and unreachable placements assert distance > `receptive_field()` (Section 1 conventions). N = 128 is inside the receptive field (both B0s should solve it, sanity). N = 512 and N = 2048 exceed `L * w`.

### Task B. Rule switching under interference

R segments, each `[cue] [delay ~ U{32..256} distractor tokens] [QRY] [x] [answer]`, active rule is the most recent cue. R in {2, 8, 32}. Sampling semantics, fixed (v1.4): k = 8 rules built with the Task A Latin-rectangle construction from the same dataset seed; each segment's cue is uniform over the 8 rules except that consecutive segments must differ (resample on repeat); operands uniform over the operand range, independent per segment. Metrics:

- accuracy vs number of prior switches
- stale-rule error rate: over wrong answers at answer-decision positions, the fraction equal to `rule_j(x)` for at least one previously cued rule j of that sequence other than the active rule (counted once regardless of how many stale rules collide); reported as null when a cell has no wrong answers. This diagnostic separates failure modes. Conservation without overwrite predicts stale errors. Decay predicts errors at the cue-blind rate.

### Task M. MQAR anchor and channel-purity discriminator (added v1.1)

Follows the Multi-Query Associative Recall structure of the Zoology line (Arora et al., 2023, github.com/HazyResearch/zoology), which is the canonical synthetic for recall in efficient architectures and correlates with language modeling performance. Adapted to this repo's fixed 64-token vocabulary and infinite-data regime (fresh sequences every step, a documented deviation from Zoology's fixed datasets).

```
[k_1 v_1 k_2 v_2 ... k_P v_P] [gap] [QRY] [k_{q1}] [ans = v(k_{q1})] [k_{q2}] [ans] ...
```

- Keys drawn without replacement from the 32-token cue range (reused as keys, cues do not appear in Task M); P = 32 uses every key each sequence, in random order. Values drawn with replacement, uniform over the 16-symbol operand range. 8 queried keys sampled without replacement uniformly from the 32 pairs, query order random. Chance = 6.25 percent (values are uniform and independent of the queried key, so the cue-blind and key-blind null really is 1/16 here).
- Two placements, each trained separately. In-window, gap = 0, pairs immediately precede queries, this is the literature-calibration cell. Beyond-window, gap = `model.receptive_field() + 64` uniform distractor tokens, which makes every pair's value token lie more than `receptive_field()` before every answer-decision position; the generator asserts the distance.
- Purpose one, calibration. B0-full at or above 95 on the in-window cell is a sanity requirement showing our MQAR implementation is learnable by full attention, the established paragon on this task. Because our cell deviates from Zoology's fixed-dataset regime (documented above), a miss triggers diagnosis — generator bug, optimization, or capacity — recorded in the ledger before any fix; it is not automatically an implementation deviation, and any fix beyond a diagnosed generator bug requires an amendment.
- Purpose two, H4 (claim-limiting, per the v1.4 hypothesis wording). Task M is content recall, not rule application. The beyond-window accuracy of M1 and M1b measures whether trained models route content through the gate pathway, with pre-registered interpretation bands in Appendix C. High accuracy forces withdrawal or qualification of the separation claim; low accuracy is "no evidence of content routing," not proof of purity.

### Loss and eval

Cross-entropy at masked answer-decision positions only, per the causal alignment contract above. Eval protocol, frozen (v1.4): evaluation uses 10,000 fresh sequences per cell drawn from the eval stream (`seed_data + 1_000_000`, never seen in training), scored at the final checkpoint (step 20k) only — no best-checkpoint selection. Metric is exact-match accuracy pooled over all answer-decision positions; per-seed accuracy is reported, and every Appendix C bar applies to the stated aggregate (mean over seeds, or min seed) computed per cell. Binomial 95 percent CI half-width at n = 10,000 is under 1 point at all relevant accuracies, comfortably inside the +2-point gate margins. Rules are shared between train and eval streams by construction (they are fixed per dataset seed; the task tests rule application at delay, not rule generalization). Results are written per cell as JSON: `{cell, variant, seed, n_sequences, n_answers, accuracy}`.

---

## Phase 0. Scaffold and determinism harness

Objective. Empty repo to green determinism gate.

Tests first:
- `test_determinism_two_runs_bitwise`. Uses the committed `configs/test_tiny.json` (d_model 64, L 2, H 2, w 16, batch 8, 200 steps, dummy copy task, fp32, single device); trains twice in-process from identical seeds and asserts the two 200-entry loss sequences are bitwise identical.
- `test_config_hash_stable`. Config hashing is `sha256` of the canonical JSON encoding — keys sorted, separators `(",", ":")`, floats via `repr` — of the full config dict, `run_id` = first 12 hex chars of `sha256(canonical_json + git_sha)` (v1.4: code identity is part of run identity). Test asserts key-order independence and stability against a committed known-answer pair.
- `test_seed_isolation`. Changing `seed_data` leaves the initial `state_dict` bytes identical and changes the first batch's token tensor; changing `seed_init` does the reverse.

Run-directory policy (v1.4): `results/<run_id>/` is created fresh per run; if it already exists the trainer refuses to start unless `--force` is passed (which deletes and recreates it). Metrics are never appended across invocations.

Tasks: repo layout, place the provided README.md at the repo root with every status row set to not started, `determinism.py`, config dataclass + hashing (the loader validates: unknown fields rejected, `damping_learnable` must be consistent with `variant`, task fields required iff the task uses them), minimal train loop on a dummy copy task, Makefile with `verify` and `gate-0`.

Gate G0: `make gate-0` runs the three tests plus ruff. Exit: green, commit.

## Phase 1. Data generators

Tests first:
- `test_task_a_exact_output` (fixed seed, assert exact token sequences against committed fixture files for k=2, N=8 miniatures; the fixtures are generated once by the generator itself, then decoded, hand-verified against the Section 6 spec by the orchestrator, recorded as verified in the ledger, and committed — after which they are frozen regression anchors)
- `test_rules_are_permutations` (bijectivity per rule)
- `test_vocab_ranges_disjoint`
- `test_distractor_rule_independence` (frequency check described in Section 6: resample the rule assignment 10,000 times with distractors held fixed, assert each rule's frequency within 5 sigma of uniform)
- `test_rules_latin_rectangle` (for each dataset seed tested: every row a permutation, every column of the k x 16 output table has distinct entries for k <= 16 and exactly-two-per-answer balance for k = 32, and `cue_blind_bayes(config)` returns exactly 1/k or 1/16 accordingly)
- `test_loss_mask_positions` (mask true exactly at answer positions, all three tasks)
- `test_task_b_active_rule_tracking` (metadata's active-rule labels match most-recent-cue semantics on constructed cases)
- `test_task_m_bindings` (keys unique within a sequence, every query key appeared as a pair, answers match the binding, exact miniature fixture at P=4)
- `test_task_m_gap_exceeds_receptive_field` (beyond-window placement's minimum pair-to-query distance strictly greater than `receptive_field()` from the model config it will be paired with)

Gate G1: all data tests green, plus a generated `results/data_samples.md` showing 3 decoded samples per task and placement for human eyeball. Exit: green, commit.

## Phase 2. Models and plumbing proofs

Tests first, in this order:

1. `test_oscillator_matches_discrete_closed_form` (v1.4, replaces the continuous-solution test, which the registered first-order integrator cannot pass at dt = 1). Single oscillator, zero and constant forcing, G = 0 and G > 0: compare the sequential implementation against the exact discrete solution (matrix power of the one-step map plus the forced particular solution, computed in fp64) over 1000 steps within 1e-5. A separate non-gating analysis records the discrete-vs-continuous deviation versus dt for the report.
2. `test_discrete_invariant_conserved` (v1.4). Zero input, random init, G = 0: the registered discrete invariant `H_d` (Section 5.2) drifts less than 1e-5 relative in fp64 and 1e-3 in fp32 over 10k steps, and the continuous energy `H = z^2 + A y^2` stays bounded (max excursion below 2x its initial value, no trend in the windowed mean over the last 5k steps). `test_damped_energy_decays`: with G > 0, windowed means of `H` over consecutive 1k-step windows are strictly decreasing and `H` at step 10k is below 1e-2 of its initial value at the registered init scale. `test_decay_ssm_energy_decays` for B2's cell, same windowed criterion.
3. `test_damping_zero_matches_m1_bitwise`. Instantiate the unified cell as M1b, set the damping to exactly zero through the code path built for M1's frozen buffer (a `zero_damping` flag that bypasses `softplus`, since `softplus(g_raw)` can never be exactly 0 for finite `g_raw`), assert forward outputs are bitwise identical to the M1 configuration in fp32. Guarantees M1 and M1b differ only in dissipation.
4. `test_cell_matches_jax_fixtures`. Sequential PyTorch cells reproduce the committed reference trajectories from the official JAX implementations within 1e-5 (fixtures, pinned oracle commits/versions, and workflow per Appendix G; the fixture npz records shapes, seeds, dtype, and the oracle git SHA in its metadata).
5. `test_scan_equals_sequential`. Runs (and gates G2) only if a parallel scan implementation exists in the repo; it must match the sequential oracle within 1e-5 on random inputs. The sequential loop is the oracle forever. (Sequential is acceptable for v1 speed. Scan is an optimization, gated by this test when present.)
6. `test_gate_identity_recovers_baseline_bitwise`. Build M1 and B0-local from the same seed with shared-submodule init (the base transformer is constructed first from `seed_init` so both variants consume identical RNG streams for shared modules; pathway modules draw from a separate derived generator), force the gate multiplier to exactly 1.0 via a bypass flag (not by driving the sigmoid), assert forward logits are bitwise identical in fp32. Repeat for B1's gate bypassed to 1.0.
7. `test_cue_unreachable_exact_zero_grad`. B0-local, fp32, untrained models from seeds {0, 1, 2}, Task A samples from both unreachable cells (N = 512 and N = 2048). For every answer-decision position, compute the Jacobian of the full vocab logit vector with respect to the input-embedding activation at the cue position (the activation at that position, not the embedding table row). Assert every entry is exactly zero, and assert the gradient object is a real zero tensor, not `None` (a `None`/detached graph fails the test — it means the path was never connected, which would make the test vacuous). Repeat for B1. Then assert the same Jacobian is nonzero for M1, M1b, and B2 at the same placements. After Phase 3 training, rerun this test on the trained B0-local and B1 checkpoints as a regression guard. This is the load-bearing proof test.
8. `test_cue_reachable_when_close`. Same machinery with the cue placed so the cue-to-decision distance is exactly `receptive_field()` (reachable by one path): gradient nonzero for B0-local. Guards against a masking bug that silently blinds the model everywhere, and pins the boundary convention.
9. `test_param_match_within_1pct` across the six variant configs, and generation of `results/params.md` (Section 5.5).

Gate G2: tests 1 through 9 green (5 when present). Exit: green, commit. These tests are permanent regression guards, never deleted.

## Phase 3. Toy proof runs

Training config, fixed for all variants: AdamW (betas 0.9/0.95, eps 1e-8, weight_decay 0.1, no decay on biases, norms, or oscillator parameters), lr 3e-4, cosine to 3e-5, warmup 500, 20k steps, batch 64, grad clip 1.0, fp32, seeds {0, 1, 2}. Fresh data every step from the seeded generator (infinite regime, no memorization axis). Eval per the frozen Section 6 protocol.

Pilot first (rule/2b budget discipline): before the matrix, run the single cell M1 at (2048, 8) seed 0 to completion, record steps/sec, peak memory, and wall clock in the ledger, project the full matrix, and set per-run timeouts at 4x the projection. Phase budget: 72 GPU-hours; within 2x of that, launch with the projection recorded in the ledger, beyond 2x pause for the human (Autonomy policy).

Matrix:
- Task A: 6 variants x 3 seeds x cells {(512, 8), (2048, 8), (2048, 32)}, plus the sanity cell (128, 8) for B0-local and M1 only.
- Task M: variants {B0-full, B0-local, M1, M1b, B2} x 3 seeds x 2 placements.
- Roughly 90 to 100 runs at ~3M params. Budget expectation is a weekend of Spark time worst case. `run_matrix.py` executes it, `make_report.py` writes `results/summary.md` with mean and min-seed accuracy per cell.

Gate G3 (thresholds from Appendix C, evaluated on the summary table; every bar is applied per cell, min-seed bars at each cell separately):
- G3.1 construction holds: B0-local and B1 at or below the cell's cue-blind null + 2 pts on every unreachable Task A cell (nulls per Section 6: 12.5 for k=8, 6.25 for k=32), and B0-local at or below 8.25 on the beyond-window Task M cell.
- G3.2 necessity: M1 mean >= 95 at (512, 8) and >= 90 at (2048, 8), min seed >= 85 at each of those cells.
- G3.2b necessity for M1b: same bars as G3.2.
- G3.3 sanity: B0-local >= 95 at (128, 8).
- G3.4 efficiency reference: M1 within 3 pts of B0-full at (512, 8).
- G3.5 dissipation spectrum (record-only, no kill): evaluate the H2 decision rule (Section 1) at (2048, 32) and record supported / refuted / inconclusive.
- G3.6 Task M: B0-full >= 95 on the in-window cell (sanity; a miss triggers diagnosis per Section 6 before proceeding). Beyond-window M1 and M1b accuracy recorded under H4 bands (Appendix C).

Exit states (v1.4): G3 is green when G3.1 through G3.4 plus the G3.6 sanity clause hold, with G3.5 and H4 recorded. G3 is green-with-M1b-primary when everything holds except G3.2, with G3.2b green, reached only through Appendix D.3; the commit message and README row must say `green-with-M1b-primary`, G3.2 is reported as failed everywhere the result appears, and M1b becomes the primary variant for Phases 4 through 7. Anything else is red: run Appendix D once, then fix the single diagnosed defect and rerun the affected cells once, or kill per Section 1. Commit.

## Phase 4. Mechanism proofs

Tests and analyses, on the trained (2048, 8) checkpoints of the primary oscillatory variant (M1, or M1b per D.3):

- `test_probe_decodes_rule`. Multinomial logistic probe from `c_t` (the 128-dim control output, Section 5.2) at the answer-decision position to rule id: full-batch L-BFGS, no regularization, max 500 iterations, probe seed 0, trained on 10k fresh sequences from the eval stream and evaluated on a further held-out 10k; classes balanced by construction (uniform cues). Threshold >= 95 percent held-out accuracy.
- `test_patch_flips_rule`. 1000 donor/recipient pairs, identical token sequences except the cue token, with donor rule != recipient rule AND `rule_donor(x) != rule_recipient(x)` (different counterfactual answers, so a flip is identifiable; pairs violating this are resampled). Run the donor, capture the `c_t` trajectory, replay the recipient with `c_t` overwritten at every position. Preconditions asserted first: the unpatched recipient outputs its own rule's answer >= 95 percent, and a sham patch (donor = recipient sequence) changes no output. Threshold: patched recipient outputs `rule_donor(x)` >= 90 percent. Because the control pathway reads embeddings only, this splice is exact and requires no approximation. Caveat, registered: patching the full trajectory transplants the donor's control state after it has seen the operand too, so this test establishes that the pathway causally carries the behavior-determining signal; it does not by itself distinguish rule identity from computed content — that distinction rests on H4's measurement and the probe.
- `test_shuffled_gates_destroy_performance`. One fixed derangement of the 16 (layer, head) gate channels, sampled with seed 0, applied at eval on 10k eval-stream sequences; accuracy must drop by >= 30 pts versus the same checkpoint unshuffled. Five additional random derangements (seeds 1-5) reported as mean drop, analysis only.
- Conditional on the H4 side-channel band triggering in G3.6: one bounded channel-capacity analysis, a linear probe from the 16-dim gate vector at the answer position to the queried value identity on beyond-window Task M, reported in `results/mechanism.md`. No architecture changes in response, v1 only measures.
- Analysis, not a gate: FFT of `g[l,h,t]` trajectories, report spectral peaks vs learned `sqrt(A)`, learned damping spectrum `G` for M1b, and 2D projection of `c` colored by rule. Written into `results/mechanism.md` with figures.

Gate G4: the three tests green. Exit: commit. H3 is now proven causally, not correlationally.

## Phase 5. Switching and the dissipation tradeoff

Train M1, M1b, and B2 (seeds {0, 1, 2}) on Task B, R in {2, 8, 32}. Report accuracy vs prior-switch count and stale-rule error rate. No pass/fail gate. The deliverable is `results/tradeoff.md` answering H2 on the switching side with the diagnostic curves, plus the learned `G` and `λ` spectra after training, which show what dissipation the task actually demanded. The v1.0 forcing-gain contingency is removed to non-goals, learnable damping in M1b is the principled overwrite mechanism and it is already in the matrix.

Exit: tradeoff doc committed, after a sol review (topic `tradeoff`, Section 2b cadence) is accepted.

## Phase 6. Scale sanity

Only reached with G3 and G4 green (or green-with-M1b-primary) and Phase 5's reviewed tradeoff doc committed.

Freeze-before-start rule (v1.4). Phase 6 as written below is a sized sketch, not yet a runnable spec. Before Phase 6 begins, an amendment (review-gated per the Autonomy policy) must freeze the full configuration: corpus and tokenizer (already subject to human sign-off), exact d_ff and parameter calculation for the ~125M target, the B0-local-widened widening rule (widen d_ff to match the oscillatory variant within 1 percent), token budget, seed count, optimizer schedule, validation split and eval cadence, the text-rendered task mixture cells (Task B cells must fit context 8192), period_max = 16384 per Section 5.2, and the paired-reduction rule if the 48h halving triggers (both variants reduced identically). Phase 6 runs may not launch before that amendment lands.

- Model: ~125M decoder-only (d_model 768, L 12, H 12, w 256, context 8192). Receptive field 3072, so text-rendered Task A uses N = 6144.
- Data: 95 percent small-corpus LM text (corpus choice goes through the review-gated amendment path of the Autonomy policy before downloading), 5 percent Task A/B rendered as text with the same disjoint-marker discipline.
- Variants: B0-local-widened vs the primary oscillatory variant only. bf16 permitted, determinism relaxed to seed-logged (bitwise not required at this phase), proof tests from Phase 2 still run in fp32 on the scaled architecture before training starts.
- Budget: day-scale runs on the Spark. If a single run exceeds 48h wall clock, halve tokens and note it.

Gate G6:
- G6.1 val LM loss regression vs baseline <= 1 percent relative (loss, not perplexity, here and in Appendix C).
- G6.2 synthetic-suffix exact accuracy: primary variant minus baseline >= 10 pts at N = 6144.
- G6.3 Phase 2 proof tests green on the 125M architecture.

Exit: green, commit.

## Phase 7. Writeup and decision

Produce `results/REPORT.md`: hypothesis table with outcomes, the summary and tradeoff tables, mechanism figures, honest limitations (toy vocabularies, permutation rules only, single hardware), a required lineage section that positions the work against every entry in Appendix F and scopes the contribution exactly as Section 1 states it, a closing plain-language results section in the same register as README.md stating in ordinary terms what was and was not shown, and a costed proposal for the next scale step. The report ships only after a sol review (topic `report`, Section 2b cadence) is accepted. Human decides whether to rent compute. The agent's job ends at the report.

---

## Appendix A. Config schema (single flat dataclass)

```
seed_data, seed_init, seed_train         int
variant                                  b0_full | b0_local | b1 | b2 | m1 | m1b
d_model, n_layers, n_heads, d_ff, window, vocab, context_len, rope_theta
osc_pairs, osc_cells, period_min, period_max, damping_learnable
task                                     a | b | m
task_N, task_k                           (a)
task_R, task_delay_min, task_delay_max   (b; k for b is task_k)
task_P, task_queries, task_placement     (m: in_window | beyond_window)
lr, lr_min, warmup, steps, batch, clip
adam_beta1, adam_beta2, adam_eps, weight_decay
eval_examples (default 10000), eval_seed_offset (default 1000000)
precision                                fp32 | bf16
```

Loader validation (v1.4): unknown fields rejected; `damping_learnable` must equal (`variant == m1b`); task-specific fields required for the active task and must be null otherwise; `period_max >= 2 * ` the task's longest delay. Phase 4/5 analysis settings (probe/patch/shuffle seeds and sizes) are fixed in this file's phase specs, not configurable. Test miniatures (for example Task M at P=4) override fields explicitly in test code.

## Appendix B. Vocabulary map

```
0            PAD (unused in v1, reserved)
1..32        cue tokens (Task A/B), reused as key tokens (Task M)
33           QRY
34..49       operand/answer alphabet (16 symbols), reused as value alphabet (Task M)
50..63       distractor alphabet (delays and Task M gap filler)
```

## Appendix C. Pre-registered thresholds

Fixed before any experiment ran, last amended v1.4 before Phase 0. Per operating rule 3, a phase's thresholds freeze permanently the moment its first run launches (write-ahead ledger entry marks it); before that moment, edits require an amendment with rationale, review-gated per the Autonomy policy.

| gate | metric | threshold |
|---|---|---|
| G3.1 | B0-local, B1 on unreachable Task A cells; B0-local on beyond-window Task M | <= cue-blind null + 2 per cell: k=8 cells <= 14.5, k=32 cells <= 8.25; Task M <= 8.25 |
| G3.2 | M1 mean (512, 8) / (2048, 8), min seed per cell | >= 95 / >= 90, >= 85 |
| G3.2b | M1b, same cells | same bars as G3.2 |
| G3.3 | B0-local (128, 8) | >= 95 |
| G3.4 | B0-full minus M1 at (512, 8) | <= 3 |
| G3.5 | H2 decision rule at (2048, 32) | record-only; supported / refuted / inconclusive per the Section 1 rule (>= 3-pt adjacent gaps), prior M1b >= M1 >= B2 |
| G3.6 sanity | B0-full, Task M in-window | >= 95 (miss triggers diagnosis per Section 6) |
| G3.6 H4 | M1 and M1b, Task M beyond-window | record-only bands: <= 11.25 (chance + 5) reads as no evidence of content routing (not proof of purity), >= 50 reads as content side-channel — triggers the Phase 4 capacity probe AND withdrawal/qualification of the separation claim in REPORT.md — between the bands reads as partial leakage, reported as measured |
| G4 | probe / patch flip / shuffle drop | >= 95 / >= 90 / >= 30 (protocols frozen in Phase 4 spec) |
| G6 | val-loss regression / suffix advantage | <= 1 pct relative / >= 10 pts |

## Appendix D. Root-cause tree for G3 failures

Run top to bottom, stop at the first match, fix only the diagnosed defect, rerun the affected cells once. "Above the null" means above that cell's G3.1 threshold; "solves it" means clears the G3.2 bars. All comparisons at the registered eval protocol.

1. B0-local or B1 above the null on an unreachable cell. The construction is broken. Check the zero-grad tests actually cover this config's `(N, L, w)`, check for cross-batch leakage in the generator, check RoPE or mask off-by-one, check the causal-alignment shift (a same-position implementation leaks the answer), and for B1 check the gate reads the layer input and not a longer-range signal. Do not proceed anywhere until these are at their nulls.
2. M1, M1b, and B2 all fail G3.2 bars. First separate plumbing from learning with evidence: (a) all three must already have solved the (128, 8) sanity cell — if not, it is plumbing, check gate saturation histograms (all gates pinned at 0 or 2 means W_g init too large), gradient norms through the control cell vs the trunk, and that `c_t` varies with the cue on an untrained forward pass; (b) if the sanity cell was solved and the diagnostics are clean, this is a genuine capacity/optimization negative at delay — go to item 4's single sweep, and if that fails, kill per Section 1. An optimization defect may be claimed only with a specific diagnosed-and-fixed bug, never as a standing excuse.
3. M1 fails G3.2, M1b passes G3.2b. Exact conservation is the pathology, not the pathway. Check learned period spectrum and energy conditioning for M1, try only the documented fallback, freeze A for the first 2k steps, rerun M1's failed cells once. If M1 still fails, record the result prominently, set gate state green-with-M1b-primary (Phase 3 exit states), and continue the plan with M1b primary. This outcome is a substantive finding about H2, not a project failure.
3b. M1 passes G3.2, M1b fails G3.2b. Learnable damping hurt. Run item 2's optimization diagnostics on M1b once; if no defect is found, record the H2-relevant negative prominently, M1 remains primary, and G3 is green with G3.2b reported as failed (this combination does not block, since necessity is proven by M1).
3c. Only B2 clears its bars, both oscillatory variants fail. The recurrent pathway works but the oscillatory mechanism does not. This kills the oscillatory hypothesis: write POSTMORTEM.md recording that first-order decay sufficed where oscillation failed, and kill per Section 1. B2's success is reported as the salvage finding.
4. Oscillatory variants mid-range (well above the null, below threshold), after item 2's checks. Capacity or horizon. Run exactly one sweep: `osc_pairs in {64, 128, 256}` at (2048, 8), seeds {0, 1}. Any success at 128 or 256 pairs is a NEW pre-registered-by-this-clause variant (M1-wide / M1b-wide), reported as such — it does not retroactively pass the 64-pair spec, and continuing with it requires an amendment naming it primary. If 256 pairs does not clear G3.2 bars for any oscillatory variant, the mechanism as specified does not carry 32-way rule identity over 2048 tokens. Record and kill per Section 1.

H4 note: a >= 50 beyond-window Task M result is not a G3 failure and does not enter this tree; its consequence is the mandatory claim withdrawal in Appendix C.

## Appendix E. Explicit non-goals for v1

MoE or expert gating, MLP-channel gating, ephaptic feedback (control reading the residual stream), phase or complex-valued residual features, parallel-scan performance work beyond the equivalence test, input-dependent forcing gain on the oscillator (moved here in v1.1, M1b covers the overwrite mechanism), the elementwise Qwen gate variant for B1 (record-only extra if time permits, headwise is the matched-granularity baseline), other Qwen gating positions (G2 through G5), porting or vendoring the JAX reference codebases, any dataset beyond the three tasks plus the Phase 6 corpus, wandb, multi-GPU.

## Appendix F. Prior-art map (added v1.1)

The Phase 7 lineage section must position against each of these. Distances are stated so the writeup does not overclaim.

| work | what it established | distance from Stencil |
|---|---|---|
| Qwen Gated Attention, Qiu et al., NeurIPS 2025, github.com/qiuzh20/gated_attention, deployed in Qwen3-Next | head-specific sigmoid gate after SDPA improves quality, stability, long context, gains attributed to nonlinearity and sparsity, 30 variants at 15B MoE / 1.7B dense on 3.5T tokens | same gate site, stateless gate computed from the current hidden state. This is B1 verbatim. Stencil's delta is the stateful recurrent controller |
| Samba, Ren et al., ICLR 2025, arXiv 2406.07522, github.com/microsoft/Samba, and the wider hybrid family (Jamba, Zamba, Nemotron-H) | a recurrent pathway interleaved with sliding-window attention carries information far beyond the window at 3.8B / 3.2T, perfect 256K passkey recall | content configuration, the recurrence writes representations into the residual stream. Stencil's recurrence writes nothing and only modulates |
| Mega, Ma et al., arXiv 2209.10655, and Megalodon, arXiv 2404.08801 | damped (Mega) and complex-damped (Megalodon CEMA) moving-average recurrence shaping gated attention, competitive with Llama2 at 7B / 2T | closest single ancestor. Recurrence is content-entangled (feeds Q/K and output gating), damped by construction, never causally analyzed. Also the strongest evidence for the H2 prior favoring damping |
| LinOSS, Rusch and Rus, arXiv 2410.03943, and D-LinOSS, arXiv 2505.12171 | forced-harmonic-oscillator SSMs, stable, universal, scan-parallel. D-LinOSS shows rigid dissipation limits representation, forgetting is crucial for long-range reasoning, learnable damping wins | supplies the cell. Neither work uses the oscillator as a control pathway over a transformer |
| Zoology / MQAR, Arora et al., 2023, github.com/HazyResearch/zoology, plus B'MOJO, arXiv 2407.06324, and FoX, arXiv 2503.02130 | MQAR as the calibrated recall synthetic correlating with LM quality, the state-size vs recall tradeoff, and the beyond-window drop-to-chance argument stated rhetorically | Task M imports the structure. Task A replaces value retrieval with rule application, meaning control not content. The zero-grad harness operationalizes what B'MOJO argues in prose |
| NM-RNN (Costacurta et al., 2024), task-conditioned hypernetworks (von Oswald et al., 2019), HyperRNN (Ha et al., 2016), NeuMoSync (2026) | a slow neuromodulatory controller multiplicatively scaling a target network's weights, low-dimensional context switches framing | concept ancestors, RNN-era or continual-learning-focused, not oscillatory, not gating transformer attention, no necessity proof. NM-RNN reportedly forgets quickly under sequential training, worth citing when discussing Task B |
| S2-Net, arXiv 2605.01656, and the oscillatory SNN line | rhythmic timing as a top-down control mechanism, in spiking networks | nearest neuroscience-faithful implementation of waves-as-control, different substrate entirely |
| Wave-RNN, arXiv 2309.08045, and Huginn, arXiv 2502.05171 | waves encode the recent past in RNNs, latent recurrence scales test-time compute | context for the writeup's framing, not direct competitors |

## Appendix G. Reuse inventory (added v1.1)

| resource | use | rule |
|---|---|---|
| github.com/tk-rusch/linoss and github.com/jaredbmit/damped-linoss (both JAX) | numerical oracles only. `scripts/gen_jax_fixtures.py` installs jax[cpu] in a throwaway uv env, runs the reference cells on fixed random inputs for both undamped and damped configurations, and writes `tests/fixtures/*.npz`. Fixtures are committed once, the fixture script is documented but not part of CI, and `test_cell_matches_jax_fixtures` runs in CI against the committed files | never import or vendor their code into src/ |
| github.com/qiuzh20/gated_attention | reference for B1's G1 plumbing, gate input point, and initialization details | read for fidelity, implement B1 in our codebase, cite in REPORT.md |
| github.com/HazyResearch/zoology | task-structure reference for Task M, and the source of the standard MQAR configuration our in-window cell calibrates against | replicate the spec in data.py, do not depend on the package |
| github.com/microsoft/Samba | framing reference for Phase 6 hybrid positioning | read-only |
| hand-rolled, no reuse | base transformer, SDPA boolean-mask sliding window, oscillator and decay cells, gate plumbing, determinism harness, all generators | these carry the proof obligations, imported code would dilute the guarantees |
