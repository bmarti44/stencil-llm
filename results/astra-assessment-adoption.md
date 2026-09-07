# Adoption of the astra repository assessment (2026-09-06)

Source: results/astra-repo-assessment-2026-09-06.txt (Brian's shared astra assessment of the whole repo, saved
verbatim). Decisions below are the orchestrator's; each is either ALREADY DONE, ADOPT NOW (built by astra in the
adoption pass), or DEFER (research track, after the larger test). Nothing here changes the registered readings of
running checks.

| # | Recommendation | Status | Where |
|---|---|---|---|
| 1 | Two tracks: usable system (explicit state, deterministic transitions, strong renderer, no steering by default) vs research track | ALREADY DONE | composition v2; loop.py actuator=off; router line CLOSED (40k/40l) |
| 2 | Proposed vs committed state; ambiguous cases preserve prior state and expose the proposal; authority boundary tested as a security boundary | ALREADY DONE (explicit entry; classifiers assistive; abstain path); ADD security-boundary tests | register.py tests |
| 3 | Completion events from external evidence (test receipt, confirmed tool result, explicit user cancel), not the model writing "done" | ADOPT NOW | register/renderer: `completes` requires an evidence field (test receipt hash or user event); model-claimed completion = proposal only |
| 4 | Establish capability before persistence: preregistered capability-qualified subset (same task, correct current instructions, fresh context) reported beside the full benchmark | ADOPT NOW | larger test: per-episode capability probe arm Q (fresh context, correct rules) run before the trajectories; PASS reported on full and Q-qualified subsets |
| 5 | Decisive state-by-actuator crossed design (gold vs auto state x render / established attention method / learned wave) + untreated history + matched-budget fine-tune baseline | PARTLY DONE (R/N/T/O = state x render); DEFER the attention-method (PASTA/SpotLight) and fine-tune arms to the research track after a rendering PASS | larger-test registration notes the deferred arms |
| 6 | Train for intervention benefit Δ(z,a), not failure probability | DEFER; fold into check 45 (off-task probe) design: label = benefit of re-render/mask, from paired rollouts | check 45 brief (later) |
| 7 | Concrete code fixes: gain-penalty per-token normalisation, recurrent feature normalisation, cache prompt projections, profile separately, sparse locations/bounded doses | DEFER (wave-era code is archived/legacy; no live actuator); profiling separation ALREADY DONE in journal | archive/ |
| 8 | Qualify each backend; never confound backend with intervention | ALREADY DONE (vLLM qualification; one frozen backend for all arms; HF divergence disclosed) | vllm-qual |
| 9 | Causal task-state transplantation | DONE as nulls (checks 32/33 KV transplant; register-state transfer is trivial by construction) | quick-checks README |
| 10 | Revocation/task-switching under adversarial interference; exact live state at every decision; whole-trajectory rerun from the intervention point for false admissions | PARTLY DONE (SLAB bank, per-round register state); ADOPT NOW the preregistered "rerun-from-intervention" diagnostic on a fixed DEV subset | larger-test registration (diagnostic, not primary) |
| 11 | Joint success and harm; hidden executable tests; episode-level pairing; predefined minimum benefit and regression margin | ALREADY DONE | v2 section 2; SLAB-2 |
| 12 | Genuine distribution shift: hold out entire constraint families, interaction structures, domains, wording; multiple seeds; more than one architecture; a capable larger open model; a strong external-model baseline with the same renderer | ADOPT NOW: preregistered held-out-family subsets in the 64-episode bank; external-model baseline arm X (Claude via API, same renderer, same bank) built now, RUN ONLY with Brian's approval of the API spend; Qwen 3.8 27B = check 47; seeds/architectures DEFER | SLAB-2 manifests; scripts/external_baseline.py |
| 13 | Strong prompting baseline = concise, correctly scoped, current-state rendering (not "repeat everything") | ALREADY DONE (T = every-request correct restatement; R = live-view rendering) | renderer golden |
| 14 | Neuroscience is motivation, not validation; ML claims stand alone | ALREADY DONE in v2 claim ceilings; carry into the write-up | — |
| 15 | Most defensible objective: learn when/where to intervene so the model executes evolving task state better than rendering alone, at matched cost, without competence loss | ADOPTED as the research-track objective; check 45 + the Δ(z,a) framing | memory: research objective |

Adoption pass (astra, CPU): items 2 (security tests), 3, 4, 10, 12 — with tests; registered as SLAB-2 Amendment 2
before code; no change to pilot-5 readings other than adding the Q probe as a diagnostic.
