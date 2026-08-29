# GPT-2 era report — the knowledge/focus split on a real model

**Question** (README.md): can a tiny separate wire carry "what am I doing right
now" alongside a frozen real model, so the current task survives where
attention provably cannot reach?

**Answer: yes — proven mechanistically, with the causal chain isolated.**
Usefulness beyond this construction remains to be earned at the next scale.

## The result

GPT-2 small, trunk frozen (bitwise-asserted), windowed attention (receptive
field 756 < 1024; exact-zero Jacobian proves the base model cannot reach
early instructions). The **focus cache** (v8): a keyed, event-gated memory —
contextual writer over blocks 0–7, hard binary supervised gates, hard
same-key overwrite, query-conditioned read feeding zero-init additive
injection into blocks 8–11. ~1.9M trainable params; the carried state is
~5 KB.

| Check | Result |
|---|---|
| Beyond-window accuracy (held-out, learned gates) | **100%** (253/253; final-space offset, evaluated after checkpoint freeze, outside the superseded single-shot marker ritual; one training seed) |
| Same, wire zeroed (causal control) | 4.3% (note: zeroing also collapses within-reach accuracy to 3.9% — the trained system is fully wire-routed, so the differential measures the wire's totality, not only beyond-reach memory; transplant and Exp A supply the complementary causal evidence) |
| Cache-state transplant → donor's rules | 28/32 (shuffled control 1/32) |
| Adversarial no-write, learned gates | **0 writes / 10,000 tokens** of quoted-slot-word filler (scripts/adv_no_write_10k.py); init-closure test: 128 random tokens, bitwise zero; one shorter eval-time stream produced 1 occupied slot |
| Chunk carry-over | cache slot state bitwise equal across a safe boundary between complete events (registered test). Arbitrary-boundary streaming, full-model compaction equivalence, and a persisted pending-span accumulator are NOT established — a named deployment blocker |
| Trunk after training | bitwise unchanged |

## The three usefulness experiments

**A — vs text pin/re-insertion across compaction.** Wire: 80.2% with zero
carried tokens. Under the registered *restricted* policy (baseline may pin
only statements still visible at compaction): 22.1%. Under the stronger
*external-ledger* variant (every update retained and re-inserted regardless
of visibility, scripts/exp_a_external_log.py): 26.0% at every budget — the
wire still leads by 54 points, but the honest reason is that the baseline
reader was never trained on repacked/pinned layouts, a fixable training-
distribution problem, not structural impossibility. This experiment does
not establish deployment-grade superiority over an external task ledger;
that comparison, with a layout-trained baseline at matched cost, is a
registered Qwen-phase requirement.

**B — synthetic teacher corruption (30% dropped labels, 10% spurious
writes, same templates).** Differential unchanged: 100% vs 3.4%. Gates
self-heal (commit precision 0.40→0.73 during training), and threshold
calibration on the final checkpoint recovers 0.995 precision at 1.000
recall (scripts/threshold_sweep.py). This establishes tolerance of
registered synthetic label corruption; weak-label acquisition from natural
text remains untested.

**C — derived instructions (the answer token never appears in the input).**
100% vs 5.1% beyond-window: the trained frozen-trunk-plus-adapter pathway
derives and stores answer values from clue phrases ("the color of the clear
sky" → blue). The experiment does not isolate how much of the derivation
comes from pretrained trunk knowledge versus the trained adapters learning
the sixteen clue→answer associations. Novel-phrasing probes (committed:
scripts/para_probe.py): an independent reviewer's probe with fresh
phrasings found 8/8 autonomous commits and 6/8 fully-autonomous correct
answers (chance 6.25%); an earlier uncommitted probe with different
phrasings found 0/8 autonomous commits and 5/8 with forced writes — the
divergence between phrasings sets means detection generalization is real
but uneven, and the committed probe is the artifact of record.

## The negative that made it possible

The oscillator, as content storage, failed four escalating rescues and is
closed with a full mechanistic autopsy (WORKLOG.md, reviews in results/):

1. Adapter capacity — solved by full-matrix rank-8 LoRA.
2. Actuator site — 144 post-softmax gate scalars proven dead (oracle 0/8);
   replaced by additive injection (oracle 8/8 unconstrained; 4/4 under
   unit-RMS projection).
3. Routing — solved by supervised salience (hard binary gate).
4. Encoding — the undamped two-cell resonator stores **one** rule near-
   perfectly (93% ridge) but cannot superpose four (slots 1–3 at 25/19/11%),
   and its signal (~1–2% of the normalized code) blinds CE-trained readouts.
   Its end-to-end "climb" was ~87% non-wire (zero-code control).

Scope: this rejects *this* oscillator in *this* forcing regime — not
oscillatory mechanisms generally. A timing role (expiring subgoals, periodic
rehearsal) remains open; slots could hold oscillator states drop-in.

## Honest limits (the caveat register)

- **Supervised acquisition**: what to store, when to commit, and which slot
  were all taught (train-time only; eval uses learned components; teacher-
  forced writes during training are an advantage the baselines lacked).
- **Closed content space**: values select among 16 trained answers; a novel
  word commits but decodes garbage. Open-content values are the hard problem.
- **Detection brittleness**: quotes were load-bearing in the plain-rule run;
  novel-phrasing detection in the derived run is real but uneven across
  phrasing sets (8/8 vs 0/8 on two different probe sets); one occupied slot
  appeared on one short adversarial stream (0 writes on the 10k stream).
- **Novelty**: keyed slot memory is memory-network lineage. The contribution
  is the causally-instrumented retrofit protocol and the receipted negative
  ladder, not the module.
- **Instrument lessons** (three review-caught false verdicts): CE+weight-decay
  readouts cannot amplify small-scale signals — closed-form ridge is the
  metric of record, with a non-vacuity precheck; global quantiles hid a
  leaky gate; a capture metric must be addressing-aware.
- **Scale of "long horizon"**: 1024-token sequences, 4 slot words, 16
  answers, one templated grammar. Real horizons are orders of magnitude
  longer and untemplated.
- **Gate compliance**: the registered READ-ridge gate (>50% by step 500) was
  missed at step 500 ([0.08/0.33/0.42/0.50]) and recovered by 1500; the
  final differential gate was passed decisively. One training seed (s0)
  throughout; ~2.01M trainable params including the logit bias.

## Next rung (agreed)

Qwen3-1.7B instruction-drift benchmarks: structured focus API first
(`focus.set/clear` at message boundaries), baseline gauntlet (pinning,
re-insertion, summaries, retrieval) at matched cost, open-content values as
the central research risk, calibrated commit thresholds, provenance-guarded
writes (tool output read-only). Then 7B agentic coding.

*The main training and causal-control results reproduce from pinned seeds
and committed scripts (evals for Experiments B and C live in
results/logs/, as their progress files end at step 1400); probe and sweep
artifacts: scripts/para_probe.py, scripts/threshold_sweep.py,
scripts/adv_no_write_10k.py, scripts/exp_a_external_log.py with outputs in
results/gpt2/. History: WORKLOG.md.*
