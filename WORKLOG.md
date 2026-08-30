# Work log — GPT-2 era (light process)

- 2026-08-28, pivot (Brian): "use gpt2 small as the model to train/test.
  let's reframe everything around this in the repo, and let's not over
  engineer it - i want there to be deterministic verificaitons in place for
  everything so you can prove that the oscillator is working as expected."
  Plan approved (GPT2-PLAN.md); sol plan review explicitly waived by Brian
  ("let's not do the sol review of the plan this time - just start executing").
  Settled: 2 arms (base stateless-gate / osc), frozen trunk, 2 seeds, clean
  archive pivot. Toy phases + their governance moved untouched to archive/.
  Next: coder pass A (gpt2.py + weight conversion + verifications 1-4).
- 2026-08-28, pass A DONE: gpt2.py (3 arms, windowed attention, gate site, external oscillator controller), convert_gpt2.py (hand-parsed safetensors, HF pinned-oracle parity max|err|=0.00012, frozen bitwise fixture), verifications 1-4 GREEN (parity bitwise, inert graft bitwise + non-vacuity, frozen trunk bitwise, two-run training bitwise). Next: pass B — nl_task.py, hand-executed fixture first.
- 2026-08-28, pass B DONE (TDD): nl_task.py (minimal GPT-2 BPE, templated rules/updates/queries, separate targets, no external corpus); verifications 6-8 GREEN — vocab single-token test went RED on 'duke' first (swapped to 'wolf'), hand-derived fixture check, leakage guard, determinism, beyond-receptive-field distance guarantee. Next: pass C — zero-Jacobian test, arms runner, dial harness.
- 2026-08-28, pass C + gate + fleet s0: zero-Jacobian on GPT-2 GREEN (exact-zero
  beyond 756 for vanilla/base, boundary 700 nonzero, nonzero through wire);
  arms runner + dial harness done. Feasibility gate: frozen windowed GPT-2 =
  2/64 exact but 46/64 top-5 on fully in-window rules -> contingency applied,
  both arms got identical trainable logit_bias. base-s0 (57 min) and osc-s0
  (69 min): NEGATIVE — both flatline at ln(16)=2.77, validation at chance
  (6.25%) in every family/bin. Diagnosis: logit_bias learned the 16-word
  answer alphabet; 144 volume-knob gates cannot make a FROZEN trunk emit
  specific new content. Held base-s1/osc-s1 as pointless.
- 2026-08-28, LoRA iteration (Brian: "okay, great I understand - run it"):
  rank-4 LoRA on attn output proj, IDENTICAL in both arms (~600k params/arm),
  zero-init B so LoRA-off is bitwise inert; trunk still frozen + bitwise
  checked. TDD: test_lora_inert_and_pathway_classified went RED
  (no lora_rank), then GREEN; all 5 gpt2 verifications green. Runner writes
  <arm>-lora-s<seed>.* so the gate-only negatives stay untouched. Launching
  pilot pair base-lora s0 then osc-lora s0 (~70 min each).
- 2026-08-28, iteration 2 + sol MI review: Brian approved full-matrix rank-8
  LoRA + demo supervision + near curriculum; killed iteration-1 osc run and
  launched iteration 2. BREAKTHROUGH: base-lora8 near-curriculum loss 14.5 ->
  0.001 by step 600 — frozen trunk + full LoRA now APPLIES rules (old blocker
  falsified). Sol xhigh mechanistic review (results/gpt2-mi-review.md, session
  01a04889): remaining blocker is the ACTUATOR (144 post-softmax volume-knob
  gates can't inject content); wire already carries weak rule info (probe
  14.5% vs 6.25% chance on the FAILED run); runner hid results -> instrumented
  per sol finding 4 (query/demo split, near+train eval every 500 steps, gate
  quantiles, checkpoints; smoke-tested). Decision rule adopted: if osc beyond-
  window flat ~500 steps after the step-1000 transition, switch to additive
  residual wire injection; no more seeds until then.
- 2026-08-28, iteration-2 verdict + actuator proven inadequate: base-lora8
  final validation beyond-window at chance (5.5/1.8/9.9%) as the proof
  requires, within-bin barely above chance (near skill did not generalize to
  long within-reach distances). osc-lora8: near curriculum 76.6% held-out at
  step 999, then the standard phase FORGOT it (76.6->22.7->10.2%) with
  beyond-window flat through step 2000 — decision rule triggered, run stopped
  (ckpt kept). Oracle-wire ceiling diagnostic (scripts/oracle_wire_diag.py,
  results/gpt2/oracle-wire-diagnostic.txt): freezing everything and directly
  optimizing the wire state per example, 0/8 beyond-window answers reachable
  (best rank 2, typical 6-13, CE pinned ~chance) — the 144-scalar gate site
  CANNOT actuate answers regardless of what the wire carries. Iteration 3
  (designed, awaiting go): zero-init additive residual injection (symmetric,
  doorless room preserved), auxiliary wire-readout supervision, near-replay +
  distance-rung curriculum; Qwen3-1.7B ruled next rung after GPT-2 resolves.
- 2026-08-28, iteration 3 built (Brian: "do it"): additive residual injection
  (zero-init 128->768 into blocks 8-11, gate_bypass disables it; base arm
  gets identical stack via stateless 768->128 projector — doorless room
  preserved, reach tests green), auxiliary wire-readout head (train-only,
  outside the model, weight 0.3), 25% near-replay in phase 2. TDD red->green
  (test_injection_inert_and_bypassable, test_batch_mixed_families); 16 tests
  green; smoke-run verified incl. replay branch. Outputs <arm>-v3-s<seed>.*.
- 2026-08-28, v3 audit + cue-masking: Brian smelled something off; sol xhigh
  audit (results/gpt2-v3-audit.md, resumed session): iteration-3 wiring is
  CORRECT (all gradients live, optimizer complete, injection active both
  arms) — the aux-at-chance signal is real: oscillator raw state ~6e6 RMS
  from integrating all 1024 tokens; answer identity shifts the normalized
  code 0.0008 RMS; probes at chance even AT the rule token. Run stopped at
  1500 (near 100% held via replay; beyond chance). Cue-masking diagnostic
  (scripts/cue_mask_diag.py): same trained controller with filler zeroed
  decodes rules at 90.6%/33%/14%/28% vs 6-10% full-input — FILLER DROWNING
  CONFIRMED, encoder viable. Iteration 4 = learned salience gate on
  controller input (+ sol mediums: per-slot aux heads, aux in ckpt,
  tightened injection test). Pending go.
- 2026-08-28, iteration 4 built (Brian: "do it"): learned salience gate
  sigmoid(w.emb+b) on the controller's input forcing (both arms, no oracle
  spans; TDD red->green test_salience_gate_wired incl. closed-gate silences
  wire) + sol audit mediums: per-slot aux heads (Linear 128->64, slot-
  gathered CE), aux head saved in ckpt/final, connectivity test
  (test_injection_and_controller_connectivity — green on v3 code, confirming
  audit), salience quantiles logged at evals. 18 tests green; smoke-run
  verified. Outputs <arm>-v4-s<seed>.*.
- 2026-08-28, salience stall diagnosed + v5 (Brian: review, fix, rerun): sol
  gradient audit on osc-v4 ckpt-500 (results/gpt2-salience-review.md):
  hypothesis CONFIRMED — filler gradients on the shared salience weight are
  22-320x rule gradients and rule gradients point the WRONG (closing) way
  68-79% of the time; the task loss cannot teach the gate (critical/high).
  v5 per prescription: rule_spans recorded in NLSequence (statements,
  updates, demo statements), balanced-BCE salience loss weight 1.0 (train-
  only; eval computes salience from embeddings — honest, claim narrowed to
  supervised cue detector + oscillator carrier), bias init -3 (~5% open),
  salience optimizer group lr 3e-3 wd 0, rule-med/filler-p90 logging with
  sol stop criteria (separation by step 200; held-out aux CE <2.5 by 500).
  Preflight: standalone 769-param classifier AUC 0.985 after 100 minibatches
  — gate learnable. 18 tests green; smoke verified. Rerunning osc only
  (osc-v5-s0) per Brian; base-v5 deferred until osc shows life. Sol note:
  base-arm salience is norm-cancelled (medium) — base salience stats are not
  evidence; fine, its wire is a dead end by design.
- 2026-08-28, v5 result + v6: osc-v5 salience gate SOLVED (bimodal quantiles
  [0.0009..0.995], rule-med 0.99, sal loss 1.54->0.07; near 100% at step
  999) but aux stayed at chance 400+ steps post-separation -> sol's branch:
  capture/retention is the blocker, not routing. Stopped at 1000. v6 adds
  capture supervision: rule_events (last_pos, slot, answer) recorded at
  every slot statement/update; aux head now also reads the just-stated
  answer at statement ends; logs split aux q-ce (retention) vs r-ce
  (capture). TDD red->green (test_rule_events_recorded); 19 tests green;
  smoke verified. Rerunning osc (osc-v6-s0). Key discriminator: r-ce falling
  with q-ce flat = capture works, retention fails (oscillator decay/
  interference); both falling = storage works, watch beyond-window.
- 2026-08-28, v6 verdict — oscillator encoding is the terminal blocker: with
  routing SOLVED (salience bimodal, rule-med 0.99) and DIRECT capture
  supervision at statement ends, r-ce stayed at chance (2.75-2.80) through
  step 800. The two-cell undamped resonator cannot encode answer identity
  from gated GPT-2 embeddings even at the moment of statement. Run stopped.
  Blocker ladder to date: (1) adapter capacity -> solved by full LoRA;
  (2) actuator site -> solved by additive injection; (3) routing -> solved
  by supervised salience; (4) ENCODING -> open; controller replacement is a
  scope decision for Brian (latch keyed by salience / damped cells / gated
  cell), since it changes what "the wire" is.
- 2026-08-28, strategic review (Brian-requested, goal-anchored): sol
  recommends D (~85% confidence, results/gpt2-goal-review.md): (1) close the
  undamped-oscillator branch as a written negative (the autopsy is the
  valuable product — do NOT overclaim "oscillators can't work"); (2) build a
  FOCUS CACHE: event-gated keyed memory — contextual writer off blocks 0-7
  hidden states (not static embeddings), salience-accumulated span encoding
  committed by a hard/straight-through write, 4-8 keyed slots with exact
  no-write on filler (bitwise-zero state change over 10k filler tokens as a
  registered test), same-key overwrite for updates, query-conditioned read
  feeding the VALIDATED blocks-8-11 injection; compaction carry-over test
  (chunked==continuous) as a deliverable; hard step gates: capture CE<1.5 by
  100, near-aux>50% by 250, beyond-window >=15-20% by 500 — else close the
  GPT-2 era, no v8. Oscillator honestly demoted: optional timing/recency
  role only, on a benchmark where timing matters (none here — decorative).
  B (damped osc) only as a cheap controller-only comparator. Toy latch
  as-is judged insufficient (single-token overwrite; hard-coded token IDs).
- 2026-08-28, CORRECTION + fable second opinion: independent fable reviewer
  (full report in git history of this entry's commit) found the v6 verdict
  overstated: routing was NOT solved per the registered criterion —
  sal_filler_p90 logged 0.32-0.35 at EVERY step (registered bar: <0.1 by
  step 200), and measured non-rule forcing mass is 0.4-0.6x total rule mass
  (2-5x interference per single rule). "The oscillator cannot encode" is
  therefore unsupported; the supported statement is "cannot encode under
  leaky supervised routing (filler-p90 ~0.35)." Second gap: the injection
  actuator was never oracle-tested at beyond-window queries. Agreed plan:
  (1) oracle injection diagnostic first; (2) one hard-thresholded-salience
  oscillator rerun; (3) only then sol's focus-cache pilot (gates kept,
  compaction test demoted to verification, would/would-not text
  pre-registered). Neuron article recorded as originating citation in
  README (cell.com/neuron/fulltext/S0896-6273(23)00506-8).
- 2026-08-28, gates 1+2 (Brian: "do it"): code_override + hard_salience hooks
  (TDD, 9 gpt2 tests green). GATE 1 PASSED 8/8: oracle injection on the
  frozen osc-v6 ckpt drives every beyond-window answer to rank 1 (ce~0.001)
  — the additive injection actuator carries content (vs old gate site 0/8;
  scripts/oracle_inject_diag.py). GATE 2 launched: osc-v7 with straight-
  through BINARY salience (forward exactly reproduces the cue-mask
  condition; gradient via sigmoid). Per fable gates: capture r-ce <1.5 and
  acc >50% by step ~100-250 or the oscillator encoding verdict stands
  (upgraded to "cannot superpose four rules under exact routing" if slot
  asymmetry appears).
- 2026-08-28, fable results review — THIRD correction, the instrument was
  blind, not the oscillator: ridge probe on the EXACT code the aux head
  reads, at the EXACT statement-end positions, under the trained hard gate:
  slot-0 = 93% (chance 6.25%); the aux head's chance-level r-ce is a CE +
  weight-decay conditioning artifact (answer signal is 1-2% of the unit-
  normalized code; frozen-code head replication reproduces r-ce 2.806 vs
  logged 2.78-2.83; wd-free lr 1e-2 head crawls to only 9% in 3000 steps
  while closed-form ridge reads 93%). v7 routing is effectively EXACT:
  0.42% leak, all post-statement slot words in query lines; pre-statement
  leaked forcing mass exactly 0. sal_filler_p90<0.1 criterion RETIRED
  (unmeetable by construction for linear salience — same token, different
  label by position). THE REAL NEGATIVE: superposition — slots 1-3 at
  25/19/11% with within-class >= between-class variance; the 128-d linear
  resonator writes rule 1 deterministically and destroys concurrent rules.
  Gate 1 revalidated at unit-RMS (4/4 rank 1). Verdict: proceed to focus
  cache (keyed slots are precisely the superposition fix) WITH instrument
  fixes: ridge probe as capture metric of record + instrument non-vacuity
  precheck, aux heads exempt from weight decay, writer separation O(1) not
  O(0.01) (don't norm the signal away), adversarial filler (quoted slot
  words) for the no-write test. Analysis scripts: scripts/review/.
  osc-v7 left running: its beyond-window phase-2 readout is now live
  evidence for single-slot end-to-end.
- 2026-08-28, v8 focus cache built (Brian: "do it"): src/stencil/focus_cache.py
  (keyed slots, contextual writer off blocks 0-7, hard detached BCE-taught
  sal/commit gates zero-init exactly closed, hard same-key overwrite, state
  carryable across chunks) + "cache" arm in GatedGPT2 (reuses validated
  blocks-8-11 injection; bypass bitwise-vanilla). Deterministic pre-tests
  green (adversarial-filler zero-write, write isolation, overwrite, chunked
  == continuous). Runner train_cache: teacher-forced writes, BCE gate
  teachers, wd-free per-slot aux heads, RIDGE capture metric of record with
  instrument non-vacuity precheck. Smoke: ridge per-slot capture
  [0.84/0.72/0.84/0.64] after TWO steps — keyed slots abolish superposition
  by construction (oscillator ceiling was 0.25 on slots 1-3 fully trained).
  Launching cache-v8-s0. Registered gates (sol): capture >50% by step 100,
  read/near >50% by 250, beyond-window >=15-20% by 500, else close the era.
- 2026-08-28, fable review #3 (v7 trend + v8 code) — CORRECTIONS + fixes:
  (1) My ceiling attribution to Brian was WRONG: v7's beyond-window climb
  (13.9% pooled, p=4e-8) survives with the wire ZEROED (12.1% zero-code
  control) — ~87% of it is a trunk/LoRA elimination strategy, not memory.
  Wire-attributable: slot-0 only (+5.2 pts; query-position ridge 23/7/4/6%,
  retention decay 93%->23% statement->query). Conditioned v7 ceiling
  ~14-17%, not 25-35%. (2) v8 CRITICAL addressing bug found before launch:
  whole-span keys collapse the store (rules merge at cos 0.95-0.98; updates
  miss their own rule at 0.42-0.50) — fixed: slot-id store, teacher-forced
  addressing in training, key-binding margin loss; smoke occupancy 6.0.
  (3) New metrics of record: per-slot ridge on the READ code at queries
  (addressing-blind capture metric alone is insufficient), learned-gate
  precision/recall, slot occupancy, adversarial no-write count, and a
  ZERO-CODE differential eval. RE-REGISTERED v8 gates: capture ridge >50%
  by step 100; READ ridge >50% by step 500; DIFFERENTIAL beyond (learned -
  zero-code) clearly positive by step 1500 (500 after the phase-2
  transition) and >=8 pts at the final n>=128 eval, else close the era.
  Raw beyond comparisons vs v7 are dishonest (shared ~12% non-memory
  floor); teacher-forced-writes advantage must be disclosed in any writeup.
- 2026-08-28, STEP-1500 RESULT + dual meaning review (sol + fable): cache-v8
  held-out learned-gate eval: near 100%, within 100%, BEYOND-WINDOW 100%
  (59/59) vs 3.4% zero-code — differential ~97 pts; gate PR 1.0/1.0. The
  registered gate is passed decisively; the wire is causally responsible
  (fable probe: statement at pos 60, query at 995, answer travels only
  through the wire; 4-rules+update fully learned-addressed 4/4; PARAPHRASE
  GENERALIZATION confirmed — unseen phrasings commit and answer 4/4).
  Convergent verdict (sol: results/gpt2-meaning-review-sol.md; fable: in
  this commit's message trail): mechanism existence + causal isolation
  PROVEN to an unusual standard; the module itself is memory-network
  lineage (not novel machinery); USEFULNESS UNPROVEN — critical missing
  experiment is the trivial-baseline fight (re-insertion/pinning scores
  ~100% at zero cost; wire must win a token-budget-charged + robustness
  comparison) and an unsupervised/weak-label commit experiment before Qwen.
  Known walls (fable probes): quotes load-bearing for commit; closed
  16-answer content wall (novel words store garbage); advWrites leak of 1
  under learned gates; teacher-forced-write training advantage disclosed.
  Sol deployment ladder: finish run; final differential at n>=128 (extend
  final eval — n=64/family gives only ~118 beyond); second seed; transplant
  + shuffled-cache controls; then structured-API-first Qwen design.
- 2026-08-28, v8 closed early at Brian's call (saturated: 100% everything,
  identical evals 1500/2000; step-2000 ckpt = final artifact). CLOSING
  CHECKS (scripts/cache_final_checks.py): extended differential n=128 seqs
  (253 beyond queries): 100.0% learned vs 4.3% zero-code (+95.7 pts;
  registered >=8). Zero-code also kills within (3.9%) — model is fully
  wire-routed. TRANSPLANT 28/32 donor-rule answers on a statement-free
  tail with carried donor state; shuffled-values control 1/32. Protocol
  note: FINAL_SPACE seeds used for these checks outside the (superseded)
  single-shot marker ritual — recorded, not concealed. GPT-2 era verdict:
  mechanism existence, causal isolation, multi-slot dynamics, and state
  transplant all POSITIVE; usefulness pending experiments A (baseline
  fight), B (weak-label commits), C (derived instructions — Brian's
  agent-discovery question).
- 2026-08-28, Experiment A (baseline fight, scripts/exp_a_baseline_fight.py):
  compaction at first-query-40, tail repacked to pos 0. WIRE 80.2% with 0
  carried tokens (~5KB state; drop from 100% = position-shift on repacking,
  honest). BASELINE (base-v3 + pinned statements, recency policy, only
  statements still within reach at compaction, budget K): ceiling 22.1%
  flat from K=64; ~40% of queried rules were structurally UNPINNABLE
  (statements left reach before compaction) -> chance 3.9% there; even
  pinned slots only 34.5% (re-inserted text also suffers position shift).
  Caveat recorded: a baseline TRAINED on pinned layouts would beat 34.5%
  on pinnable slots; nothing rescues the unpinnable 40%. Headline: the
  wire wins exactly where pinning is impossible. Experiment B (teacher
  noise 30% drop / 10% spurious, TAG_SUFFIX=noise) wired + smoked;
  launching full run.
- 2026-08-28, Experiment C built (derived instructions — Brian's agent-
  discovery question): DERIVED_CLUES in nl_task (statement gives a clue,
  e.g. 'reply to "cat" with the color of the clear sky'; the answer token
  NEVER appears in any statement — leak-guarded test). Families derived/
  near_derived; DERIVED=1 runner mode (curriculum, evals, ridge all switch;
  tag cache-v8derived). TDD red->green; smoke ok. Queued behind Experiment
  B (noise run in flight). Honesty note: fixed clue phrasings mean success
  could be surface association rather than semantics; a paraphrase-clue
  probe at eval will separate them.
- 2026-08-28, Experiment B VERDICT (step-1500, run stopped saturated):
  differential SURVIVES teacher noise (30% dropped spans, 10% spurious
  writes): beyond 100% vs 3.4% zero-code, capture ridge 95-100%. Gates
  partially SELF-HEAL (commit precision 0.40 @1000 -> 0.73 @1500, recall
  1.0; salience back to 1.0/1.0); threshold calibration on the ckpt
  recovers precision to 0.97 @ recall 0.87 (sweep in this entry's commit).
  Conclusion: weak-label acquisition is viable; calibrate the commit
  threshold on a small clean set at deployment. Experiment C launching.
- 2026-08-29, Experiment C VERDICT (derived instructions, run stopped
  saturated at step 1500): beyond-window 100% vs 5.1% zero-code on rules
  whose answer token NEVER appears in the input — the wire stores
  CONCLUSIONS the frozen trunk infers from clues (knowledge in the frozen
  wiring supplies the inference; focus carries its result). Pre-registered
  paraphrase probe splits the system: DETECTION overfit in this run (0/8
  commits on novel clue phrasings — gate latched onto trained clue
  surface), but the VALUE pathway is SEMANTIC: with the write forced, 5/8
  correct on never-seen phrasings (chance 6.25%, p~2e-6). All three
  experiments now closed: A (wire beats pinning where pinning is
  impossible), B (differential survives label noise; gates self-heal +
  calibrate), C (wire carries inferred conclusions; writer semantic,
  detector the weak link). Next: era report + Qwen3-1.7B design.
- 2026-08-29, era report written: results/gpt2-report.md (result, three
  experiments, negative ladder, caveat register, Qwen design). Registered
  step 6 remainder: one sol xhigh results review of the report (held
  session), pending Brian's go.
- 2026-08-29, final review loop CLOSED in 2 rounds: round-1 highs from both
  reviewers fixed with committed artifacts (10k adversarial no-write: 0
  writes; external-ledger baseline 26.0%; paraphrase probe 8/8 commits /
  6/8 correct; threshold sweep 0.995/1.000; chunk claim narrowed; Exp C
  attribution fixed). Round 2: SOL SIGN-OFF (99%) + FABLE SIGN-OFF, no
  high/critical remaining (results/gpt2-round2-signoffs.md); sol's two
  non-blocking numeric nits applied. Both reviewers' Qwen plans received
  (sol: results/gpt2-final-review-sol.md part 2); synthesis into
  QWEN-PLAN.md is next, pending Brian.
- 2026-08-29, QWEN-PLAN.md written (merged sol+fable plans): six phases each
  <1 day, run-admission timing rule, open-content oracle in P0 (effort-
  ending risk first), structured focus API before autonomous salience,
  matched-trained baseline gauntlet with Pareto usefulness gate, the
  owner's discovery-driven scenario as P3's measured object, seven
  mechanical stop conditions (decisive: text-ledger Pareto dominance).
  Pending Brian's approval to begin P0.
- 2026-08-29, Brian burden-test pass on QWEN-PLAN: spine confirmed
  straightforward (own the forward for determinism/probes; oracle risk
  test day one; microfit; drift run with the proven instrument kit). Fat
  trimmed: slot metadata deferred until a test needs a field; the
  five-baseline gauntlet and the 64-session agentic battery moved behind a
  decision point AFTER the drift run proves mechanism at Qwen scale.
- 2026-08-29, QWEN P0 underway: Qwen3-1.7B pinned + downloaded; harness
  implementation src/stencil/qwen3.py (GQA + q/k-norm + RoPE + SwiGLU,
  fp32 norms/softmax, injection hook + return_hidden probe access);
  conversion scripts/convert_qwen3.py (hand-parsed safetensors, tied head
  verified, 310 tensors) — PARITY: 8/8 top-1 vs pinned HF oracle
  (transformers==4.51.0), worst bf16 max|err| 0.365, our outputs frozen as
  bitwise fixture; tests/test_qwen3.py green (bitwise parity + two-run
  determinism). TIMING PROBE (admission rule): top-8-block autograd, ctx
  2048, p90 1.04 s/step -> 192-step run ~3 min compute — far inside the 2h
  envelope. Remaining P0: session/task generator, visible-task >=80% upper
  bound, open-content oracle ceiling.
- 2026-08-29, QWEN P0 COMPLETE, all gates passed: (1) parity 8/8 top-1 +
  bitwise fixture + determinism (earlier entry); (2) timing p90 1.04s/step;
  (3) open-content task built (src/stencil/qwen_task.py: composed
  multi-token values, worked-example prompt; checker lesson: score decoded
  TEXT, not standalone-encoded ids — BPE context mismatch produced a false
  0/32); (4) VISIBLE-TASK UPPER BOUND 32/32 = 100% (gate 80%; task format
  iterated once — two-part values invited truncation, hyphen-joined fixed
  it); (5) OPEN-CONTENT ORACLE 8/8 first-token AND 8/8 exact continuation,
  CE -> 0.000 (scripts/qwen_oracle.py; gates 6/8 and 4/8) — stop-condition
  2 risk retired: injection at blocks 24-27 drives arbitrary multi-token
  generation through the frozen trunk with the evidence DELETED. Next: P1
  microfit (q3-api-micro-r8-s0).
- 2026-08-29, QWEN P1 microfit PASSED: q3-api-micro — cache (structured
  writes, no learned gates, NO LoRA per burden test) learns end-to-end on
  32 fixed sessions: evidence chunk written to state, DELETED, query chunk
  answers exact multi-token open-content values through the frozen trunk.
  TRAIN exact 1.00 (gate 0.95) vs zero-code 0.00 -> differential 100 pts
  (gate 50). Iteration ladder within the run: 64 steps flat (undertrained)
  -> 512 steps loss 0.87 exact 0 -> multi-vector reader (4 sub-values/slot
  so position-varying queries can walk a static write into a token
  SEQUENCE; the single-vector code lived in a <=4-dim simplex) -> 19% ->
  + grad-accum 4 + cosine decay -> loss 0.0005, 100%. Held-out 0.00 as
  expected at microfit (32-session memorization); generalization is P2's
  question (data scale). src/stencil/qwen_cache.py, scripts/qwen_p1_micro.py.
- 2026-08-29, SOL QWEN REVIEW (results/qwen-review-sol.md) — P2 halted per
  registered gate: step-500 held 0% / diff 0 decisively missed; continuing
  would be an unregistered rescue (a stray step-1000 eval showed held 2%
  before the kill landed — recorded, changes nothing). Highs accepted:
  (1) evaluator is teacher-forced and leaks prior gold answers — final
  claims need free-running generation; (2) stale metric confounded by
  first-token pool collisions (~12.5% floor) — replace with full-sequence
  stale-exact + likelihood margin; (3) the transcript design is honestly a
  "structured neural token memory" (~11KiB/slot fp32), NOT compact semantic
  focus — writeup language prescribed; (4) P0 "pretests" overclaim: cache
  pre-tests (non-vacuity, chunk-boundary, no-write) not yet implemented for
  the Qwen cache — implement or amend; (5) all P1/P2 results relabeled
  DEVELOPMENT (adaptive iteration on the same eval seeds); P1 = capacity
  proof, not a registered pass. Repair list before any confirmatory run:
  free-running eval, corrected stale metric, transcript validity mask +
  truncation handling, immutable artifact tags per variant, seed the new
  val_tok/tok_code/step_q layers (currently on global RNG — reproducibility
  defect), ablation battery (summary-only/transcript-only/shuffles/
  wrong-key transplant), amended QWEN-PLAN (schedule, no-LoRA, fp32 state
  bytes, dev-vs-confirmatory seed spaces). Then register ONE confirmatory
  config + ONE width fallback; both miss => stop condition 3. Fable
  correctness audit still in flight — repairs wait for it (a forward-pass
  bug would supersede everything).
- 2026-08-29, confirm1 MISSED its registered step-500 gate (free-running
  held 0%, differential 0 vs >=50%/>=15) — halted mechanically per
  Amendment 1; log results/logs/qwen-p2-confirm1.log, artifacts
  cache-p2-confirm1-*. Attempt 2 (confirm2) built per registration:
  content-addressed cross-attention reader over masked memory tokens
  (mem_key+slot_bias / mem_val, single masked softmax, no step schedule,
  no summary path), same declared schedule and gates, fresh validation
  seeds unchanged. Both-miss => stop condition 3.
- 2026-08-29, STOP CONDITION 3 FIRED — the fused Qwen focus-cache effort is
  closed as a registered negative: both confirmatory attempts (confirm1
  repaired transcript-walk; confirm2 content-addressed cross-attention)
  missed the step-500 gate (free-running held-out 0%, differential 0 vs
  >=50%/>=15) on fresh validation seeds under the declared schedule. The
  honest verdict: at Qwen3-1.7B with a frozen trunk and NO LoRA, the cache
  has proven CAPACITY (P1: 100% train exact, 100-pt differential) but did
  not GENERALIZE the value binding within two registered attempts (~6k
  fresh sessions each); the persistent diagnostic is first-value-token
  content at chance while format rides the prior. Named candidate causes
  for any future registered program (NOT rescues of this one): the no-LoRA
  trim (trunk cannot adapt its reading of the injected code), fp32 span
  encodings through a 1-layer writer, and the fused memory+selector design
  itself. Per QWEN-PLAN: no escalation to 7B on this line. NEXT DECISION
  (Brian-endorsed direction, pending his go): the SPLIT architecture —
  working memory stored as text/transcript (no contest with the ledger),
  the wire as a contentless SELECTOR/governor deciding which stored
  obligation presses on the current token (the Miller 'mobile stencil'
  claim proper). That is a new registered program, not an amendment.
- 2026-08-29, SELECTOR program launched (SELECTOR-PLAN.md registered; the
  Miller-faithful split: text ledger = working memory, wire = contentless
  attention-spotlight selector). S0 admission: first task too easy (97% —
  cue words gave selection away); ONE registered retune (format-identical
  post-ledger notes, authority-instruction-only selection, recency bias
  against the answer): base 32/64 = 50%, errors 29 stale-echo / 3 other —
  selection-shaped failure confirmed, gate PASSED. Next: S1 oracle
  spotlight (attention-logit bias toward the correct ledger span, layers
  20-27; gate >=50% of errors flipped without breaking correct cases).
- 2026-08-29, S1 REGISTERED PASS (scripts/selector_s1.py, fresh block 11.3M,
  evidence results/qwen/s1-oracle.json): base 28/64; grid verdicts — single
  layers insufficient ({20} b4: 25% rescue; {24} b4: 33%), {20-27} b2:
  rescue 27/36 = 75% with broken == 0 -> GATE PASSED; {20-27} b4 rejected
  by the strict broken==0 rule (94% rescue, 1 broken) — the registered
  criterion did real work. Wrong-span control 1/36 = 2.8% (<=10%).
  SELECTED CONFIG: layers 20-27, beta 2.0. Fable review addendum adopted
  for S2 framing: victory condition is ADDRESSABILITY (zero-selector ==
  base bitwise; point the spotlight elsewhere -> different governed
  behavior; trunk untouched), NOT raw accuracy — a LoRA reference arm is
  pre-expected to match oracle accuracy and cannot make those claims.
  Next: S2 learned selector (scorer on cached h20 features, hard argmax,
  config inherited), paired base/oracle/selector on n>=128.
- 2026-08-29, S2 REGISTERED PASS + baselines (results/qwen/s2-selector.json):
  learned selector address accuracy 128/128 on validation; paired behavioral
  eval base 55/128 (43%) / oracle 114/128 (89%) / SELECTOR 114/128 (89%) —
  net closure 1.00 (gate 0.5). The full Miller loop demonstrated: a learned
  contentless ~3-bit wire equals the oracle spotlight on a frozen trunk.
  BASELINES (same 128 sessions): oracle-line re-insertion 128/128 (embeds
  oracle selection; pre-registered as accuracy-trivializing); FULL-LEDGER
  re-insertion 128/128 at ~123 extra tokens/query (no selection knowledge
  needed). HONEST BOTTOM LINE: on this task, text re-insertion is a
  complete solution at modest token cost — the selector's registered win is
  addressability + zero-identity + cost (3 bits vs 123 tokens/query), not
  capability. Per plan ("let the trivial baselines decide whether S3
  deserves to exist"): S3's case must come from regimes where re-insertion
  is impossible (content compacted away before pinning — the GPT-2 Exp A
  structural case) or costly (large ledgers, latency). DECISION POINT for
  Brian: build S3 in that regime, or close the selector program as a clean
  mechanism-positive with the baseline verdict recorded.
- 2026-08-29, S3-A0 PASS (results/qwen/s3-a0.json): N=8 base 39% / reins
  100% @123tok; N=16 base 19% / reins 95% @255tok; N=32 base 5% / reins 84%
  @503tok. N*=32: selection is the bottleneck even with text re-supplied,
  and re-insertion is costly. A1 (oracle at N*=32) next.
- 2026-08-29, S3-A1 PASS at N*=32 (results/qwen/s3-a1-oracle.json): base
  3/64 (5%); oracle {20-27} beta=4 rescues 48/61 = 78.7%, broken 0;
  wrong-span 0/61. beta=2 insufficient at scale (25%) — the registered
  one-time dose re-check selected beta=4. Oracle ~80% vs re-insertion 84%
  @503 tok/query. A2 (learned selector at N=32) launching.
- 2026-08-29, S3-A2 PASS (val 3.9%->78.9%, closure 0.91, address 91.4%) and
  SEALED FINAL PASS on untouched 11.95M seeds: base 5/128 -> selector
  113/128 = 88.3% (oracle 124/128, closure 0.91, address 89.8%). SELECTOR
  PROGRAM COMPLETE — every registered gate passed through the sealed final.
  Report: results/selector-report.md. Scorer weights saved.
- 2026-08-29, AGENTIC-PLAN.md registered (G1 implicit-governance oracle ->
  G2 deterministic scripted-session benchmark -> G3 runtime -> G4 registered
  comparison -> G5 7B rung; stop conditions + review points). Executing G1.
- 2026-08-29, G1 PASSED via the registered re-check (results/qwen/
  agentic-g1.json, agentic-g1b.json): admission base mean compliance 67.7%
  (prefix 95%, doc 61%, hint 47% with 45% CONFLICT ADOPTION) — in band.
  Always-on oracle FAILED the gate instructively (suppresses conflicts to 0
  but wrecks generation: validity 95->56% @b2, 11% @b4 — continuous
  attention forcing starves code-writing of working context). The one
  registered re-check: TIMED oracle — spotlight the relevant obligation
  sentence only at its decision moment (post-'def ', docstring opener,
  annotation site), current prediction row only. b=4: mean compliance
  0.677 -> 0.901 (+22.4), conflict adoption 0/0/0, validity 0.938. The
  per-moment governance thesis confirmed: the wave presses transiently.
  Next per plan: sol+fable G1 reviews before the G2 benchmark build.
- 2026-08-29, G1 RECORD CORRECTED per dual review (sol:
  results/agentic-g1-review-sol.md; fable probes:
  results/qwen/g1-fable-review-report.json): the ALWAYS-ON oracle is the
  REGISTERED NEGATIVE — G1's gate was missed and AGENTIC-PLAN stops at its
  own stop condition. The timed spotlight was an actuator REDESIGN outside
  the dose/site allowance (three dimensions changed, same seeds, both
  betas tried) — my earlier "G1 PASSED" entry overstated it; also the
  admission band was per-obligation (prefix 95% out of band) and the
  registered validity gate failed strictly (0.953->0.938) and under
  ast.parse (63->56, McNemar p=0.016 — the regex 'valid' metric HID a real
  syntax regression). WHAT SURVIVES, now reviewer-verified beyond the
  original run: the timed per-moment mechanism is real — span-specific
  (wrong sentence: 0.516, 16 pts BELOW base, conflict adoption rises),
  time-specific (rate-matched random moments: 0.667 ~ base), fresh-seed
  stable (12.05M: +22.9), and the validity damage traces to ONE moment-
  detector false positive (closing-quote docstring refire leaking the
  opener word into code; 5/8 no-parse cases); with the opening-quote fix,
  parse-gated compliance is +20.8 at b=4 with validity intact (fable,
  verified). Learnability traps named: fixed template offsets allow
  address memorization (must randomize layout); regex-label distillation
  (must hold out obligation types, evaluate on own rollouts, report moment
  precision/recall with precision primary).
- 2026-08-29, T0 PASSED (results/qwen/timed-t0.json, fresh 12.3M seeds, AST
  + subprocess-execution scorer, randomized obligation order): SELECTED
  b=2 timed {20-27}: parse-gated mean 0.667 -> 0.885 (+21.9, gate +15),
  paired parse lost 0 (gate 0), parse rate 100%; b=4 correctly rejected
  (1 parse lost despite +22.9). Controls at signature: wrong-sentence
  0.411 with conflict adoption rising (harmful — span-specific);
  rate-matched random moments 0.630 ~ base (timing load-bearing). Conflict
  adoption at selected config: hint 58%->3%, doc 20%->5%. TIMED-SELECTOR-
  PLAN promoted from draft to governing (Brian: "continue with T0"). Next:
  T1 — learned timing head + learned address scorer, factorial arms.
- 2026-08-29, T1 PASSED at ceiling (results/qwen/timed-t1.json): AST-
  grounded moment labels (192 rollouts, 728 moments); timing head precision
  1.000 / recall 1.000 (tau frozen 0.5, all taus equivalent); address
  scorer 1.000; factorial on fresh val: base 0.646, oracle/oracle 0.859,
  learned/oracle 0.859, oracle/learned 0.859, LEARNED/LEARNED 0.859 —
  closure 1.00, paired parse lost 0. Honest note: ceiling scores partly
  reflect that these three moment types are strongly syntactic in h20 and
  addresses are template-matchable (order-randomized but same templates) —
  disclosed at registration; generality is T2's question (held-out
  formats/types). Next: T2 scripted-session benchmark DESIGN + the
  registered design review (sol+fable) before any T2 run.
- 2026-08-29, T2 DESIGN REVIEW verdicts — build BLOCKED pending contract v2:
  sol 6 HIGHs + 13 MUSTs (results/t2-design-review-sol.md); fable DO-NOT-
  BUILD with 7 MUSTs + a decisive probe (results/qwen/t1-obligation-
  blindness-probe.json): the T1 timing head fires 32/32 at syntax moments
  with NO obligations present (0 false fires /1502 in-dist) — timing is
  obligation-BLIND syntax detection, and T1's address was a forced choice
  among only the true sentences, so NO learned component has yet read an
  obligation. PROCESS DEBT RECORDED: T1's registration named parser-timed,
  always-on/oracle, and shuffled/wrong arms that were never executed; the
  pass went unqualified. Mapping note: oracle timing IS the regex parser,
  so oracle/learned == parser-timed + learned address (present under
  another name, 0.859); the genuinely missing arms (always-on/oracle,
  shuffled-timing/wrong-span) are being run now as T1-completion. Contract
  v2 will merge both MUST lists (single shared compaction survival rule;
  address candidates incl. superseded + distractor quotes; registered
  abstain mechanism with numeric false-press gate; scoreable held-out
  types incl. one at a TRAINED moment class; degenerate-pass-proof gate
  arithmetic with registered Ns and paired tests; component gates carried
  forward; parser-timed named as an arm).
- 2026-08-29, T1 RECORD COMPLETED (results/qwen/timed-t1-completion.json):
  the previously-unexecuted registered arms ran with textbook signatures —
  always-on/oracle destructive (parse 0.703, compliance 0.464 < base);
  shuffled/wrong == base (0.646); oracle/oracle and learned/learned
  reproduce 0.859 on deterministic retrain. T1's pass now stands fully
  qualified: timing = obligation-blind syntax parsing (probe), address =
  forced-choice among true sentences; the honest T1 claim is "learned
  syntax-timed pressing of harness-selected spans matches the oracle";
  obligation READING is untested until T2 v2. T2 CONTRACT v2 committed
  (merged MUSTs). Next: light round-2 review of v2, then the T2 build.
- 2026-08-29, T2 DESIGN REVIEW CLOSED — dual sign-off on CONTRACT v3 (fable
  round-2 sign-off on v2 MUSTs stands + sol round-3 SIGN-OFF on v3's four
  repairs: ledger survives compaction for all arms — the wire is tested on
  SELECTION, memory stays the ledger's job; full opportunity tuple + exact
  stale definition; >= 48-pair active/absent/cleared/stale-only
  counterfactual set per split; complete freeze list with single named
  fallback; absolute floors A_sel >= 0.70 and lift >= 0.10). Build order:
  (1) session generator (src/stencil/t2_sessions.py) + generator unit
  tests incl. counterfactual-set construction; (2) multi-turn arm runner +
  AST/exec/tokenize scorers; (3) selector training per frozen recipe; (4)
  post-build pre-run hash audit (mandatory); (5) dev shakeout, then val.
- 2026-08-29, T2 BUILD stage 1 done: session generator
  (src/stencil/t2_sessions.py) + unit tests (tests/test_t2_sessions.py, 5
  green): deterministic sessions; opportunity records match authored
  history for all cells; counterfactual coverage across 48 sessions =
  active 492 / absent 62 / stale_only 102 / cleared 76 (>= 48 each
  non-active cell); ledger survives compaction while turn 0 text ages out;
  held-out comment type appears only in val/final. Cell semantics
  clarified during build (stale_only = inactive WITH visible stale text in
  the surviving window; cleared = inactive without). Next: stage 2 — arm
  runner + scorers.
- 2026-08-29, T2 BUILD stage 2 done: arm runner + scorers
  (src/stencil/t2_runner.py): first-FunctionDef target policy; ast/
  source-text/exec scorers; adherence on active cells only; stale-action
  per v3 definition; env feedback names violated TYPE only (no value — no
  second memory channel); arms base/reinsertion(==pinned under v3,
  recorded)/oracle/selector-pluggable; spotlight beta=2 layers 20-27
  current-row on ledger-sentence spans located per-prompt. Smoke (1 dev
  session, 3 arms): 5 works, parse 5/5 everywhere, base 12/14 active-
  adherent, oracle 13/14, reinsertion 11/14, stale-actions 0. Note for the
  dev shakeout: single-session base looks strong — the oracle-headroom
  precondition (>= 0.10) will decide if T2 binds. Next: stage 3 selector
  training (frozen recipe), hash audit, dev shakeout at scale.
- 2026-08-30, T2 DEV SHAKEOUT — INCONCLUSIVE-BY-DESIGN branch fires
  (results/qwen/t2-shakeout.json, 24 dev sessions, 92 works, 244 active
  opportunities): base 61.9%, reinsertion 61.9% (stale 4.7->1.7%), ORACLE
  63.5%, selector 63.5% — headroom +0.016 vs the registered >= 0.10
  binding precondition. Per CONTRACT v3, T2 is recorded inconclusive-by-
  design: under the v3 memory rule (ledger survives every compaction) with
  6-12 obligations and one visible distractor at a time, the base model's
  failures are NOT attention-selection failures (the oracle cannot fix
  them), so the spotlight has nothing to govern. Consistent picture, not a
  contradiction: selection failure needs interference pressure (S0's three
  format-identical notes; S3's N*=32 scale) — the very pressure the v3
  ledger-survival repair (scientifically required) removed at this small
  N. The selector's proven value stands where registered: S2 (43->89%),
  S3 sealed (3.9->88.3% at N=32), G1-codegov (+21.9 under conflict).
  Stage 3 artifacts: timing 0.995/1.000; address 159/159; theta frozen at
  the zero-false-press rule (45/159 live kept — calibration bug found and
  fixed before any gated run). Hash audit written pre-run. DECISION POINT
  (Brian): (a) accept — record T2 as the boundary finding "multi-turn
  sessions with a surviving authoritative ledger at small N do not exhibit
  selection failure; the selector matters under interference/scale," and
  close the program with S0-S3 + G1 as the positive results; or (b) ONE
  new registered session design raising interference toward the proven
  regime (many surviving format-identical conflicting notes near work
  turns and/or N approaching 32 obligations) — a fresh registration round
  with both reviewers, not an amendment.
- 2026-08-30, T2b DEV SHAKEOUT (results/qwen/t2b-shakeout.json): HEADROOM
  BINDS (+0.193): base 37.6% under S0-style in-session interference,
  oracle 56.9% — real fixable selection failure inside multi-turn
  sessions. Re-insertion 55.3% (text competes hard here). LEARNED selector
  40.0% (closure 0.12): the zero-false-press theta keeps only ~25% of live
  presses; address accuracy 130/130 so the registered capacity fallback's
  trigger does not fire, and theta's rule is frozen — no registered knob.
  Proceeding to the single registered VALIDATION run (n=96, val split with
  OOD probes) to be judged as-is; a gate miss stops T2b per contract and
  the program closes on the honest composite: selection failure exists in
  sessions and the oracle fixes it, but the safety-constrained learned
  selector under-presses, and re-insertion captures most of the headroom.
- 2026-08-30, T2b VALIDATION (n=96 sessions, 1238 active opportunities):
  base 32.0 / oracle 46.5 (headroom +0.145 binds) / SELECTOR 32.3 (closure
  0.02 — GATE MISS) / re-insertion 52.9 (beats the oracle). Program CLOSED
  per contract at the registered stop rule. Report:
  results/timed-selector-report.md. Closing sol+fable verification next
  (per Brian's /goal).
- 2026-08-30, CLOSING VERIFICATION verdicts: fable VERIFIED (all headline
  numbers recomputed and matched; non-blocking nit on parser-timed mapping,
  already recorded). Sol NOT VERIFIED with one CRITICAL + one HIGH:
  (1) CRITICAL — t2_shakeout.py imported t2_train_selector for
  candidate_spans; that module RETRAINED ON IMPORT and re-saved the
  defective quantile-theta checkpoint before every evaluation, overwriting
  the registered max(abstain)+eps recalibration (t2b-val.log line 11 shows
  theta=172002.445, calib false-press 9/18). Every selector arm in T2 and
  T2b shakeouts/validation therefore ran an UNREGISTERED selector; the
  "calibration bug caught before any gated run" claim was false. The prior
  val run is invalid as a harness execution error (no information from it
  fed the artifact — heads and theta rule were frozen at registration).
  (2) HIGH — "code validity intact" unsupported: val parse rates
  base 0.873 / oracle 0.863 / reinsertion 0.856 and no paired parse/exec
  evidence was saved, so Gate 3's zero-paired-loss requirement was never
  demonstrated; "reinsertion wins outright" is supportable only as higher
  adherence. FIXES: candidate_spans moved to src/stencil/t2_select.py;
  t2_train_selector.py body guarded under main(); t2_recalibrate.py builds
  local heads; t2_shakeout.py imports the library and now records per-work
  paired parse/exec + paired_vs_base losses; static regression test
  tests/test_no_side_effect_imports.py. RERUN (write-ahead): T2B train ->
  recalibrate -> dev shakeout -> val with the registered selector, logs
  results/logs/t2b-*-r2.log; report to be corrected from the r2 numbers
  and re-verified by sol once before close.
- 2026-08-30, T2b REGISTERED RERUN COMPLETE (r2 logs): training reproduced
  bitwise (12329/837/134 examples, quantile theta 172002.445 identical),
  recalibration restored registered theta 185849.813 (0/18 false press,
  32/130 live kept). DEV: base 37.6 / oracle 56.9 (+0.193) / reins 55.3 /
  selector 40.0 (closure 0.12) — aggregates identical to the contaminated
  run. VAL (n=96, 1238 active): base 32.0 / oracle 46.5 (+0.145) / reins
  52.9 / SELECTOR 32.0 — the registered selector NEVER PRESSED (paired
  0/0/0/0, outputs identical to base), closure 0.00, GATE MISS confirmed
  on the registered artifact. NEW paired validity evidence (val, n=409
  works): oracle loses 7 parse / 11 exec (gains 3/5) — Gate 3's zero-loss
  bar NOT met at session scale (~1.7% validity tax; dev was 0/0);
  reinsertion churns (-24/+17 parse, -30/+46 exec, net exec +16). Report
  corrected accordingly (selector row, finding 1 validity tax, finding 3
  downgraded to adherence win, process record documents the CRITICAL).
  Sending report for one sol re-verification before close.
- 2026-08-30, SOL RE-VERIFICATION round 2: numbers accepted; two HIGH
  overclaim findings. (1) "never pressed / bitwise identical to base" was
  inferred from zero paired score deltas, not measured -> running
  scripts/t2b_press_audit.py (val seeds, base+selector arms, press
  counters + per-work sha256 of generated code) to evidence or narrow it.
  (2) "training reproduced bitwise" had no tensor-level evidence and the
  original checkpoint was overwritten in place (results/*.pt gitignored),
  so the claim is NARROWED in the report to "reproduced the recorded
  counts, thresholds, and calibration statistics exactly". Correction
  applies to the 05:27 entry above: read its "bitwise" as narrowed, and
  its "never pressed" as pending the press audit.
- 2026-08-30, PRESS AUDIT (results/qwen/t2b-press-audit.json, val seeds,
  base+selector with counters and per-work sha256): sol's HIGH was
  CORRECT — "never pressed" is REFUTED. Registered selector applied 14
  presses / 14794 steps (timing fired 941; theta vetoed 927); 407/409
  works token-identical to base; the 2 differing works scored identically
  (hence paired 0/0/0/0 and closure 0.00). Report finding 2 and ladder
  row corrected to the measured numbers. Earlier "never pressed" wording
  in the 05:27 entry is superseded by this entry.
- 2026-08-30, SOL ROUND 3: audit accepted, wording tightened (HIGH):
  hashes are of decoded code strings not token ids; 927 non-applied
  timing fires cannot all be attributed to theta (address may also
  reject ty-not-in-spans; audit does not split); "scored identically"
  for the 2 differing works narrowed to unchanged paired parse/exec +
  unchanged aggregate adherence. Report finding 2 + ladder row now use
  sol's prescribed formulation, plus one deterministic strengthening:
  score_work's only input is the code string, so the 407 identical code
  strings imply identical scores by construction. Round 4 confirmation
  requested.
- 2026-08-30, PROGRAM CLOSE: sol round 4 VERIFIED (identical-score
  inference explicitly accepted); fable re-verification VERIFIED (all
  numbers recomputed, provenance and guard test confirmed). Dual closing
  verification complete on results/timed-selector-report.md. The /goal
  ("prove out the focus mechanism deterministically for long agentic
  coding, verified by sol and fable") is DONE: mechanism proven
  (oracle +14.5 val / +19.3 dev under in-session interference, ~1.7%
  paired validity tax), learned safety-constrained selector honestly
  negative (closure 0.00, 14/14794 presses), re-insertion adherence
  baseline mapped (52.9% with paired churn). Verification trail:
  final-verify-sol.md, final-reverify-sol.md, final-reverify2-sol.md,
  final-reverify3-sol.md, fable transcripts summarized in this log.
- 2026-08-30, PRESS-PLAN.md drafted from the 4-lane research synthesis:
  P0 diagnostics (score matrix, attention-mass liveness, empirical
  false-press cost C, theta sweep, event-triggered baseline) -> G0 ->
  P1 joint candidate-or-null scorer (stop rule: 50% recall at real FP
  bound) -> P2 rhythm-default phase/gain -> P3 fork-and-judge -> P4
  oscillator-vs-controls bakeoff -> P5 structured-eligibility ceiling
  (always ships). Zero-false-press replaced by measured (C, p*) budget.
  Plan review by sol+fable is the registered next step before P0.
- 2026-08-30, PRESS-PLAN review round 1: sol NOT CLEARED (6 HIGH), fable
  NOT CLEARED (3 HIGH + mediums), heavily convergent. Decisive findings:
  (a) "no new GPU runs" false — registered T0.1 trace pass instead;
  (b) harness cannot express autonomous wrong-candidate selection (the
  runner redirects any type to the authoritative span) — span-level
  address API + press-event logging + wrong-span non-vacuity test
  registered as H1-H4; "WHERE proven 130/130" downgraded to a
  calibration-set claim pending the rejection split; (c) p* mixed units
  and pre-empted its own measurement — now symbolic H/(B+H) from paired
  single-press rollouts, press_stats.bayes_press_threshold requires
  B,H (no defaults); (d) decision tables completed (G0 mechanical,
  P0.5 two-way, T1 with one registered fallback for [0.25,0.5));
  (e) session-level independence units + Clopper-Pearson gates
  (0/160=1.85%, test-pinned); (f) seeds frozen (trace 13.00M, calib
  13.03M, fixtures 13.06M, dev 13.10M, val sealed 13.20M; 12.9xM
  legacy); (g) structured arm folded into every replay; bakeoff (T2)
  promoted ahead of generation rungs; P0.2 deferred behind G0; beta
  sweep demoted; T4 uses prefix recomputation (no KV cache exists).
  PRESS-PLAN rewritten as v2. Round 2 review next.
- 2026-08-30, PRESS-PLAN review round 2 (sol 6 HIGH, fable 3 HIGH, both
  NOT CLEARED — round-1 fixes confirmed real; new findings are v2's own
  precision gaps). v3 lands: registered VALIDITY RULE (U(work) =
  adherent count - 2*BROKEN; replay passes iff Delta-U_total >= 0.8 *
  adherence gain and > 0) cited by every gate; p* demoted to reporting;
  fixture single-use with select-on-trace/certify-once and block B
  (13.07M) for post-G0 policies; T0.5 ceiling replaced with the full
  oracle restricted to the eligible denominator + headroom
  precondition; T2 phase-scramble criterion inverted (>=20% degradation
  REQUIRED) and tie made computable (0.02 absolute); T1 table completed
  (useful-but-unsafe cell -> T4 trigger; INCONCLUSIVE -> one reserve
  re-draw on 13.11M then line closes); sealed val gets the same
  headroom precondition + registered closure formula; T4 blocked on a
  TDD'd incremental end-of-unit detector in its own preregistration;
  H1 contract expanded (callable returns span+diagnostics, runner
  applies and logs guards). Round 3 next.
- 2026-08-30, PRESS-PLAN round 3: fable CLEARED (medium F1 multiplicity
  + 2 lows, fixed same-day: initially Bonferroni, superseded); sol NOT
  CLEARED with 2 HIGH -> v3.1: one-policy-per-block certification (G0
  comparison is trace-only; single pre-named winner certified on block
  A; attention fallback / T1 retrain fallback / T2 winner each take a
  fresh reserve block from C 13.08M / D 13.09M; failure event defined
  BEFORE the ledger-membership guard); T0.5 recovery_closure =
  (A_reactive-A_base)/(A_oracle-A_base) on a frozen base-arm eligible
  set with headroom>=0.10 on that denominator. Round 4 = sol
  confirmation only (fable already cleared; its cleared version
  differed only by these two fixes it did not flag).
- 2026-08-30, PRESS-PLAN round 4 (sol 2 HIGH) -> v3.2: T0.1 trace-only
  with sealed one-job certifications after naming; ceiling certifies on
  block C 13.08M (pool now D 13.09M / E 13.095M, extension 13.30M+);
  T0.5 evaluation set = union of per-episode downstream sets (all later
  active opportunities of the violated type, frozen from base). Round 5
  = sol confirmation.
- 2026-08-30, PRESS-PLAN v3.2 DUAL-CLEARED (fable round 3, sol round 5
  after 2 targeted confirmation rounds; review trail
  results/press-plan-review*-sol.md + fable transcripts above).
  Checkpoint (i) satisfied. Beginning harness registration H1-H4
  (red/green): span-level policy arm with runner-applied guards +
  press-event logs, wrong-span non-vacuity fixture, trace writer.
  Legacy arms (base/reinsertion/oracle/selector) stay untouched for
  reproducibility; new arms: "policy" (autonomous, H1) and
  "structured" (type->authoritative redirect with active-ledger
  eligibility).
- 2026-08-30, H1-H4 harness landed (all TDD, 8 new tests green + GPU
  non-vacuity test passed 7.7s): run_policy_session (span-level policy,
  runner-applied guards, press log with below-threshold/out-of-ledger
  split), structured arm registered as alias of oracle (equivalence
  noted: _oracle_moment is a parser detector + active-ledger spans —
  the T2b "oracle" was already a deployable structured policy),
  press_log in run_session, TraceWriter with atomic close + digest.
  T0.1 smoke (1 session): 5 events, 3 legacy presses, fields verified;
  stale-print footgun caught and fixed. Launching full T0.1 (48 trace
  seeds).
- 2026-08-30, T0.1+T0.2 COMPLETE (results/qwen/t0-trace.pt, 381 events /
  48 sessions; t0-matrix.json). HEADLINE: the T2b selector failure is
  mechanically explained — the legacy address max-score ranged over ALL
  candidate types, so at inactive-type moments it scored up to 185,938
  (cross-type hits on active types' candidates), forcing the
  zero-false-press theta to 185,850 and killing recall (active scores
  start at 47,081). TYPE-RESTRICTED addressing (argmax only over
  candidates of the timing head's predicted type) makes all 58 trace
  negatives structurally unpressable (no same-type candidate exists
  in-window for cleared/absent types under this generator) and ranks
  the live sentence above in-window conflicting notes on 323/323 active
  events. All six families hit recall 1.000 / 0 false sessions / AUPRC
  1.000 on trace (t0_matrix.py; threshold rule: max recall with <=2
  false sessions of 48 — conservative reading, flagged). CAVEATS for
  G0: (a) tie-break (AUPRC) cannot separate the tied families —
  proposing cos_max (bounded scale; the raw qk scale drifted ~4x
  between calib and trace, making a frozen raw threshold fragile);
  (b) certification on fixture blocks is VACUOUS w.r.t. score
  discrimination under this generator (no same-type lookalike exists at
  inactive-type fire moments) — proposing a registered generator
  extension (notes for one inactive type per session) to make
  certification non-vacuous; (c) proposing T1 training be skipped in
  favor of the zero-training type-restricted policy judged under T1's
  behavioral table. G0 review round (sol+fable) launched on all three.
- 2026-08-30, G0 REVIEW COMPLETE (fable: verified all trace claims incl.
  leakage audit + prompt consistency, endorsed rulings with conditions,
  2 new HIGH; sol: verified, confirmed cross-type autopsy incl. the
  185,938 max being a cleared-prefix event won by a live DOC span,
  1 HIGH threshold bug, conditional approvals). CORRECTIONS accepted:
  (a) my "~4x raw-scale drift" claim was UNSUPPORTED — 68/323 = 21.1%
  of trace actives survive the old theta vs calib 24.6%: the evidence
  shows cross-type threshold pollution, not scale drift; (b) `uniq[0]-1`
  threshold enumeration froze cosine at -0.359 (would have burned block
  A); (c) +inf singleton margins were guaranteed false-pressers. ALL
  FIXED (nextafter boundaries, singleton abstention, counterfeit
  hard negatives in selection + secondary tie-break; 11 family tests
  green). CORRECTED MATRIX: cos_max recall 1.000 / 0 false sessions /
  hard-AUPRC 1.0000 @ threshold 0.6407741904258727; raw_max 0.901 (2
  false sessions); margins 0.907 (2); live_minus_best ceiling 0.833
  (singleton abstention cost disclosed — R_auto exceeds the "ceiling"
  under conservative semantics). G0 BRANCH: R_ceil 0.833 >= 0.50,
  R_auto 1.000 >= 0.5*R_ceil -> proceed. NAMED G0 WINNER (before any
  fixture block is touched): family cos_max, threshold
  0.6407741904258727, composed policy = zero-new-training reuse of the
  supervised timing/address heads + type-restricted cos_max argmax +
  runner guards. Plan amended with the G0 amendment section (tie-break,
  singleton semantics, fixture generator extension spec for ALL
  certification blocks, T1 one-way shortcut). NEXT: TDD the fixture
  generator extension; then the sealed block-A certification of the
  named policy; T0.3 running meanwhile.
- 2026-08-30, s0x fixture generator extension landed (TDD, 5 new tests +
  s0 regression green; s0 distribution bit-identical). Cells
  constructible: cleared + stale_only (absent-with-note contradicts the
  base plan — every type gets set; disclosed in the plan text).
  GENERATOR VERSION for all certification blocks: s0x @ this commit.
  NEXT: sealed block-A certification of the named policy (cos_max @
  0.6407741904258727, type-restricted, runner guards), queued behind
  the running T0.3.
- 2026-08-30, POST-G0 IMPLEMENTATION REVIEW (sol: 1 CRITICAL + 2 HIGH,
  NOT CLEARED; fable: 1 HIGH + 3 LOW, NOT CLEARED; both verified the
  cos math, tie handling, threshold reproduction, and s0/v3
  bit-identity across 250 seeds). CONSOLIDATED FIXES: (1) CRITICAL/HIGH
  press semantics — certification now uses provenance-by-span for BOTH
  failure counting and application (press_certify.certify_decision,
  sharing t2_runner.span_in_ledger with the runner; STRICTER than the
  trace's value-level selection semantics — disclosed in the
  certificate; fable measured ~7% of sessions eventually carry a
  live-valued note, so value-comparison was fragile); (2) s0x assertion
  bound to the targeted work turn + no-authoritative-candidate
  (press_certify.s0x_assertion_hit; held_out["s0x"]["work_turn"]
  recorded by the generator; cell_intent metadata made honest on
  fallback); (3) sealed job made FAIL-CLOSED: block/N hard-coded,
  artifact sha256 pinned (verified independently: selector e9922d70...,
  qwen 13bfabb5..., tokenizer aeb13307...), .started marker refuses
  reruns, atomic result write, model loading under main(). (4) BLOCK A
  ADMINISTRATIVELY VOIDED (sol's audit instantiated its sessions at
  generator level; conservative reading of single-use). NAMING (before
  the block is touched): the named policy (timing head +
  type-restricted cos_max @ 0.6407741904258727 + runner guards,
  provenance-by-span semantics) certifies on BLOCK D (13,090,000).
  Reserve pool: E only; extension 13.30M+. 5 new pure-logic tests; all
  CPU suites green. One targeted re-review of the diff before the
  sealed run.
- 2026-08-30, IMPL REVIEW round 2: DUAL CLEARED (sol: guard shared and
  exact, assertion target-bound, hashes match, block D frozen; fable:
  press condition bitwise-identical runner vs certify, no env knobs, no
  residual value comparison, s0x indices verified, one LOW TOCTOU nit —
  no seed-integrity impact). Sealed block-D certification authorized;
  runs when T0.3 frees the GPU.
- 2026-08-30, T0.3 COMPLETE (results/qwen/t0-cost.json, n=220/condition,
  paired single-press): B = +0.2727 dU per correct press (broken 0.45%);
  wrong-SPAN H = 0.3318 (broken 2.27%); wrong-MOMENT dU = 0.0 (broken
  0%, output changed 2.3%). KEY ASYMMETRY: mistimed presses of the
  right span are ~free; pressing the wrong span is the only costly
  error — the zero-false-press design guarded the cheap error class.
  p* (reporting only) = 0.332/(0.273+0.332) = 0.55 for span errors,
  ~0 for timing errors. VALIDITY RULE constants now instantiable.
  Launching sealed block-D certification (dual-cleared job).
- 2026-08-30, SEALED BLOCK-D CERTIFICATION: FAIL, k=149/160 (U95 0.961).
  Anatomy (results/qwen/g0-certify-D.json): 71 sessions with false
  selections — ALL 88 events value-WRONG at inactive-type moments
  (live=None): the policy presses the injected same-type note. The
  trace's perfect separation was RANKING-only (live beats lookalike
  when both present); the absolute cos score cannot detect liveness
  when the live sentence is absent — the bi-encoder ceiling the ML
  research lane predicted (RocketQA lesson: liveness is span+context).
  Fable's counterfeit hard negatives under-estimated real s0x scores
  (max counterfeit cos 0.6016 < threshold 0.6408 < real note scores) —
  counterfeit-based threshold transfer is now a documented failed
  instrument. 79 sessions failed the non-vacuity assertion (doc 53 /
  hint 22 / prefix 4): with the target obligation cleared, the model
  often does not generate that moment class — fixture design flaw, to
  be amended (make moment generation task-structural, e.g. the work
  prompt itself requests a docstring + annotations). VERDICT: the
  zero-new-training line FAILED certification honestly (PRESS-PLAN
  honest negative #1). Runner-up raw_max on block E would predictably
  fail the same way (ranking-only discrimination, threshold selected
  without real hard negatives) — burden-test proposal: skip it, spend
  the effort on T1 TRAINING (candidate-or-null with a real null head,
  hard negatives from s0x sessions) per the registered G0 amendment.
  Convening the T1 preregistration review (checkpoint iii) with:
  runner-up skip ruling, fixture assertion redesign, T1 training spec
  + new seed blocks, certification block accounting (E + 13.30M+
  extension).
- 2026-08-30, T1 PREREGISTRATION DUAL-CLEARED (fable v1 conditional —
  condition folded; sol round 3 after 2 revision rounds). v3 registered:
  results/t1-prereg-draft.md governs the T1 rung (decision rule frozen,
  total assertion coverage pretest, mechanical fallback/block table:
  B first cert, E fallback-only, immediate close on B-failure).
  Execution order: s0x2 TDD -> train-hard collection (13.12M) + pretest
  -> trace recompute -> training -> gates -> sealed block-B cert.
- 2026-08-30, T0.5 COMPLETE (results/qwen/t0-reactive.json, 24 dev
  sessions x4 arms): eligible downstream set n=100; base 31 / reactive
  45 / oracle 47; headroom_on_eligible 0.16 (binds); RECOVERY_CLOSURE
  0.875 >= 0.5 -> PASS: reactive event-triggered pressing is a
  REGISTERED COMPONENT of the final recipe (zero learning). Session
  adherence: base 44.3 / reactive 50.0 / oracle 59.4 / reinsertion
  63.8 (n_active 246). The crossfield lane's event-triggered-control
  prediction validated. Remaining T0 rung: T0.4 theta sweep (queued,
  lower priority — the certification anatomy already answered its
  question qualitatively). Next: T1 collector smoke -> train-hard +
  calib-hard collection + pretest.
- 2026-08-30, T1 COLLECTIONS COMPLETE (train 485 events/48 sessions,
  calib 246/24; digests in t1-*-features.pt). PRETEST: pressure PASSES
  30/48 >= 10; assertion coverage FAILS the total-coverage gate (38/48
  train, 17/24 calib). DIAGNOSIS (offline): not a generation failure
  (targeted works parse) and not late-turn decay (fires/work ~2-3 in
  every octile) — per-session variance: ~20% of sessions get zero
  target-type timing fires at the final work. Total per-session
  coverage is unattainable under the deployed tau-gated trigger.
  REDESIGN PROPOSAL (registered rule: redesign + re-register before
  training): keep generator s0x2; amend CERTIFICATION SEMANTICS —
  failures = false selections only; sessions without a target hazard
  stay in the denominator (they still test general false selection)
  but assertion-miss stops being a failure; new separately-gated
  fixture-quality statistic HAZARD_COVERAGE (fraction of sessions
  where the deployed trigger faced the target hazard) with floor 0.75
  and exact reporting. Review round launched (both reviewers) before
  any training.
- 2026-08-30, FLAGGED FUTURE REGISTRATION (from Brian's steering
  question): the T2b benchmark is structurally biased toward
  environment-checkable, parser-detectable obligations. User steering
  and self-discovered constraints have NO checker signal and often no
  syntactic moment — the reactive component is structurally useless
  there and the current evidence cannot measure that case. When the T1
  line resolves (either way), the next benchmark registration should
  include directives with no checker and no parser moment (pure
  steering), where the rhythm-default line (T3) is the natural
  candidate mechanism. Do not let this drop.
- 2026-08-30, AMENDMENT A1 DUAL-CLEARED (sol "112" ack on the floor;
  fable E1-E7 folded). Certification floor: n_h >= 112/160. Launching
  trace0 recompute (13.00M with the v2 collector), then training.
- 2026-08-30, T1 TRAINING round 1 (770 rows: 715 active, 55 inactive;
  t1-gates.json): address 1.0, recall 0.9942, margins 0.9942/0.90 —
  PASS; zero-NULL-error gate FAILS on exactly one session (13140011),
  n_h=17 countable. Per the registered fallback table: consuming the
  ONE fallback (4x reweight on inactive hard-negative rows), re-gating
  once. Write-ahead: if it passes, IT certifies on block B; if it
  fails, the discriminative line CLOSES.
- 2026-08-30, DISCRIMINATIVE LINE CLOSED (registered stop rule: fallback
  also failed the gates). Autopsy: round-1 head — address 1.0, recall
  0.9942, margins 0.9942/0.90, hazard leakage 1/17 sessions (both
  'hint' errors at the s0x hazard of 13140011); 4x fallback retrain —
  recall 0.9769, leakage 2/17 (added 13140001 'doc'). Verified the
  failing sessions are hazard-facing and errors are AT-hazard (gate
  implementation matches A1 semantics). HONEST SUMMARY: the trained
  candidate-or-null head cut the hazard failure mode by ~93% vs the
  zero-new-training policy (30/48 pressure sessions -> 1/17) — a large
  real improvement that is still not certification-grade (1/17 -> U95
  ~25% >> 5%); the zero-error screen did its job and saved block B from
  a probable burn. Blocks B and E remain untouched. TWO honest
  negatives now bracket the discriminative approach. REMAINING
  REGISTERED LINES: T2 controller-state bakeoff (head-only) and T3
  rhythm-default (the Miller-faithful line; also the natural mechanism
  for the flagged pure-steering case). Banked recipe: structured arm +
  reactive pressing (0.875 recovery) + T0.3 cost asymmetry. Next: T2/T3
  preregistration draft -> review round (checkpoint iii).
- 2026-08-30, T2/T3 PREREG v3.1 DUAL-CLEARED (fable r1 + sol r4; 4
  rounds total). T2 ARCHITECTURE TABLE (frozen BEFORE any T2 forward
  pass, per v3.1; only synthetic shape tests precede):
  COMMON: shared T1 head warm-started from t1-head.pt (round-1); state
  is per-TYPE (3 types); scorer augmentation identical for all:
  null_logit += W_z(state_flat) [Linear state_dim->1],
  q = Wq(h20) + W_qz(state_flat) [Linear state_dim->64]; event write
  applies only to the fired pred_type's slice via W_u [Linear 2048->8];
  score from z_pre, then write; D-clock (step gaps, inter-turn D=32).
  (a) oscillator: z_ty in C^4 (8 real dims/type, state_dim 24);
      transition z <- rho^D * exp(i*omega*D) * z; rho = sigmoid(r),
      r init 2.0 per dim; omega init linspace(0.1, 1.0, 4) per type
      (trainable); write adds W_u(h20) to Re/Im interleaved.
      Controller params ~18,017.
  (b) static: state = trainable per-type embedding (8/type, no
      recurrence) + same W_u event path feeding a per-event additive
      context (not persisted). ~18,017.
  (c) EMA: z <- (1-a)*z + a*W_u(h20) on fired type; a = sigmoid(tau)
      per dim, tau init logit(0.1). ~18,041.
  (d) GRU: per-type GRUCell(8,8) fed by W_u(h20); ~18,449.
  (e) null-oscillator: rho=1 fixed, omega FIXED = linspace(0.1,1.0,4),
      no W_u (no input coupling) — EXEMPT from the parameter match by
      design (control), disclosed; scorer heads only (~1,625).
  All counts within +-10% for (a)-(d). Code digest recorded at commit.
  Executing: T0.3b audit (GPU) in parallel with T2 implementation
  (synthetic tests first).
- 2026-08-30, T2 table correction (pre-forward, per the freeze rule):
  actual counts osc 18,041 / static 18,041 / ema 18,041 / gru 18,449 /
  nullosc 1,625 (my table said 18,017 for osc/static — arithmetic slip,
  omitted the 24 recurrence params; within-10% match unaffected). Shape
  tests 7/7 green; no real-data forward has occurred.
- 2026-08-30, T2 BAKEOFF COMPLETE (results/qwen/t2-bakeoff.json; frozen
  chain): hazard-leak sessions — osc 2, gru 2, nullosc 2, ema 3,
  static 5 (events equal; recall equal 0.9942 for the tied three; final
  tie-break params -> NULLOSC 1,625). No contender reached zero leakage
  -> registered outcome: RANKING AS SCIENCE, no generation pilot, no
  block consumed. SCIENCE: (i) the input-blind free-running oscillator
  ties every trained state controller — state coupling added nothing
  measurable to hazard rejection (the "cron job" diagnosis from the
  research sweep, now empirical); (ii) statelessness proper (static)
  is worst (5); (iii) none beat the plain T1 round-1 head's 1/17 —
  joint retraining with state channels mildly HURT. The oscillator-as-
  discriminator hypothesis is answered negatively at this scale/regime;
  oscillator-as-SCHEDULER (T3 rhythm, no discrimination at all) is now
  the last autonomous line, gated on T0.3b (running). Probes moot (no
  strict oscillator win).
- 2026-08-30, T0.3b COMPLETE (results/qwen/t0-costb.json): all four
  cells negative (P4g0.5 -0.03, P4g1.0 -0.08, P8g0.5 -0.065, P8g1.0
  -0.125; broken rate scales with gain 1%->4.5%; matching-moment hits
  0-12/200). GRID RULE fires: SKIPPED — THE RHYTHM LINE CLOSES (honest
  negative: blind scheduling presses off-moment and buys nothing).
  PROGRAM VERDICT (PRESS-PLAN "HONEST MAP" clause): all autonomous
  lines closed at their registered rules — (1) zero-new-training
  discriminative (certification FAIL, cross-type then absolute-liveness
  anatomy), (2) trained discriminative (93% hazard reduction, not
  certification-grade, fallback consumed), (3) state controllers (no
  pilot-eligible contender; input-blind clock ties trained state),
  (4) blind rhythm (net harmful). T4 never triggered. THE BANKED
  RECIPE STANDS: structured parser-timed pressing + event-triggered
  reactive pressing (0.875 recovery) within the T0.3 cost asymmetry.
  Closing report next; checkpoint (v) reviews to follow.
- 2026-08-30, CLOSING VERIFICATION round 1: sol NOT VERIFIED (1
  CRITICAL: finding 3's "no safety machinery" contradicted by T0.3b;
  4 HIGH: cert-anatomy attribution, T1 denominators, T2 tie wording,
  T0.3b class-count unit bug, round counts); fable NOT VERIFIED
  (numerically faithful; same finding-3 HIGH with the harm-attribution
  arithmetic; round-count corrections 17 sol / 9 fable; minors: 92.9%
  exact, block C absent from list, T0.4 never formally closed). ALL
  FIXED in the report: cert decomposed (71/160 false-selection, U95
  0.512, + 79 non-vacuity, 1 overlap); T1 stated on the reused calib
  screen 14/17 -> 1/17 (92.9%, unsealed disclosure); T2 exact tie
  structure + third-use disclosure; finding 2 rewritten as two
  operating points with the SUBSUMPTION note (reactive press set is a
  strict subset of structured's — composition untested claim removed)
  + oracle validity tax restored; finding 3 rewritten per both
  reviewers (provenance guards one error class; safety = provenance +
  moment/type-matched timing); T0.3b class counts WITHDRAWN (the
  classifier sliced decoded characters by token index — unit bug; the
  cell dU gate never used them and stands); round counts replaced by
  the reproducible convention (17 sol incl. 2 acks / 9 fable); block C
  added to the untouched list. T0.4 FORMALLY CLOSED as superseded (the
  certification anatomy answered the constraint-vs-representation
  question directly; recorded, not run). Re-verification round 2 next.
- 2026-08-30, closing rounds 2-3 (sol): round 2 NOT VERIFIED (3 HIGH:
  T0.3 overgeneralized, finding-1 nonexistence claim, count
  arithmetic) -> report v3; round 3 NOT VERIFIED (1 HIGH: count
  taxonomy + WORKLOG missing rounds 2-3 — this entry closes that gap).
  File evidence for the count: 18 artifacts = 15 substantive + 3
  one-word confirmations (press-plan-review5, t2t3-review4, a1-ack;
  wc -w = 2 each incl. the extraction header). Report v4 states the
  verified taxonomy. Round 4 next.
- 2026-08-30, PRESS-PLAN PROGRAM CLOSED — DUAL VERIFIED (sol round 4
  after 3 correction rounds; fable final confirmation of all five
  changed sections, incl. independent audit that no PRESS-PLAN-era
  review artifact was omitted from the count). Closing report:
  results/press-plan-report.md v4. Verdict: autonomous press timing
  closed on four honest negatives (discrimination x2, learned state,
  blind rhythm); the deployable Miller stencil = structured pressing
  (parser + ledger provenance) and reactive pressing (checker-
  triggered, 0.875 recovery) as two individually-proven operating
  points; the autonomy boundary quantified; internal-wave and
  pure-steering registrations flagged as the successors. Goal
  ("effectively apply the Miller wave so it's useful on real, long
  agentic coding") satisfied to the extent this program registered:
  mechanism + address + environment-clocked application proven;
  self-clocked focus honestly bounded, not achieved.
- 2026-08-30, INTERNAL-WAVE-PLAN v1 drafted (the PRESS-PLAN successor;
  Brian's /goal: prove out the internal wave). Core novelty vs the
  closed lines: DIFFERENTIABLE training signal (CE through the frozen
  trunk's attn_bias path), continuous bias field (no certified
  decision), recurrent state (W1) with the transplant demonstration
  (W2) as the Miller signature. Fresh seeds 13.4M/13.45M/13.5M. Review
  round 1 (checkpoint i) launched.
- 2026-08-30, INTERNAL-WAVE-PLAN v2 (round-1 reviews folded: fable
  CLEARED w/ 8 edits incl. the dose-starvation catch — the v1 field
  could not express the proven press; sol NOT CLEARED 3 CRITICAL +
  7 HIGH incl. nonexistent CE target -> W0.0 canonical reference
  builder, feedback_mode=none, W0.05 field-parameterization ceiling
  test, connectivity battery replacing my invalid gradient test — sol
  RAN the test and showed b.sum()=g has no q/k gradient — full
  decision tables, closed-line control arm + distillation probe,
  param count corrected to 264,321, 13.30M namespace bounded). Honest
  claim narrowed to the one real axis: the differentiable training
  signal. Round 2 next.
