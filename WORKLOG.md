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
