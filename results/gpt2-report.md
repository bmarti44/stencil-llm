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
| Beyond-window accuracy (held-out, learned gates) | **100%** (253/253, sealed offset, n=128 seqs) |
| Same, wire zeroed (causal control) | 4.3% |
| Cache-state transplant → donor's rules | 28/32 (shuffled control 1/32) |
| Filler writes (10k adversarial tokens, init) | bitwise zero (registered test) |
| Chunked-with-carried-state ≡ continuous | bitwise equal (registered test) |
| Trunk after training | bitwise unchanged |

## The three usefulness experiments

**A — vs the trivial baseline (pin/re-insert text across compaction).**
Wire: 80.2% with zero carried tokens. Pinning: 22.1% ceiling at any budget —
~40% of rules were structurally unpinnable (statements left the window before
compaction) and pinned text itself suffers position-shift. *Caveat:* a
baseline trained on pinned layouts would improve the pinnable share; nothing
rescues the unpinnable share.

**B — noisy teachers (30% dropped labels, 10% spurious writes).**
Differential unchanged: 100% vs 3.4%. Gates self-heal (commit precision
0.40→0.73 during training) and threshold calibration recovers 0.97 precision
at 0.87 recall. Weak-label acquisition is viable.

**C — derived instructions (the answer token never appears in the input).**
100% vs 5.1% beyond-window: the wire stores *conclusions* the frozen trunk
infers from clues ("the color of the clear sky" → blue). Paraphrase probe:
the value pathway is semantic (5/8 on never-seen phrasings with the write
forced, chance 6.25%), while the detection gate overfit clue surface in this
run (0/8 autonomous commits on novel phrasings).

## The negative that made it possible

The oscillator, as content storage, failed four escalating rescues and is
closed with a full mechanistic autopsy (WORKLOG.md, reviews in results/):

1. Adapter capacity — solved by full-matrix rank-8 LoRA.
2. Actuator site — 144 post-softmax gate scalars proven dead (oracle 0/8);
   replaced by additive injection (oracle 8/8, incl. unit-RMS).
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
  clue-surface overfit in the derived run; one adversarial false write under
  learned gates.
- **Novelty**: keyed slot memory is memory-network lineage. The contribution
  is the causally-instrumented retrofit protocol and the receipted negative
  ladder, not the module.
- **Instrument lessons** (three review-caught false verdicts): CE+weight-decay
  readouts cannot amplify small-scale signals — closed-form ridge is the
  metric of record, with a non-vacuity precheck; global quantiles hid a
  leaky gate; a capture metric must be addressing-aware.

## Next rung (agreed)

Qwen3-1.7B instruction-drift benchmarks: structured focus API first
(`focus.set/clear` at message boundaries), baseline gauntlet (pinning,
re-insertion, summaries, retrieval) at matched cost, open-content values as
the central research risk, calibrated commit thresholds, provenance-guarded
writes (tool output read-only). Then 7B agentic coding.

*All numbers reproduce from pinned seeds; every claim above has a test,
script, or logged eval in this repository. History: WORKLOG.md.*
