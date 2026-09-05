Brian, we have drifted substantially. The retention program answers a different question; it is not testing a complete Miller analogue.

1. **Toy era, August 21–28:** an oscillator carried task state across an unreachable attention gap:
   100% versus the 12.5% cue-blind ceiling; a linear probe read the job at 87.5%; transplanting state switched rules 45/45.
   This was the closest causal demonstration of “same wiring, different active job.” But a latch matched or beat
   the oscillator. That justified dropping claims that oscillation was necessary, not dropping task-state switching. [Archive](../archive/README.md)
2. **Original GPT-2 test, August 28:** frozen GPT-2, windowed attention, oscillator-driven head gates.
   It already mixed two questions: remembering newly supplied word mappings and selecting pretrained competencies.
   GPT-2 scored only 2/64 even with rules visible; the first gate-only arms stayed at chance.
   Later oracle gates scored 0/8; additive injection scored 8/8. Four-rule oscillator encoding also failed.
   The successful replacement was a keyed ~5 KB content cache with a trained writer/readout and additive injection:
   100% versus 4.3% zeroed, donor-state adoption 28/32. That was latent-content memory, not the original gate experiment.
   **First departure: gates became content injection.** Evidence forced abandoning those implementations;
   it did not force treating their replacement as proof that a wave selected existing circuits. [GPT-2 report](gpt2-report.md)
3. **SELECTOR, August 29:** after two Qwen latent-cache attempts failed held-out value binding, we separated storage
   from control: text held the obligations; a hard 5-bit address pointed attention at one entry.
   Sealed accuracy rose 3.9% → 88.3%. This was our cleanest content-free control signal on a real frozen model.
   Text storage here was an explicit, evidence-motivated simplification; the intervention itself did not repaste text.
   Still, it selected a text location, not an independently identified stored skill. It was extended to ongoing
   generation because named-rule questions were narrow—not because this result failed. [SELECTOR report](selector-report.md)
4. **TIMED-SELECTOR / PRESS, August 29–30:** the question became “which obligation, at which generation step?”
   Threshold scoring, trained discrimination, learned state, and blind rhythm each failed their registered gates.
   The session selector nearly stopped acting; blind pressing was harmful. Text reinsertion beat the session oracle
   on adherence, with its own validity costs. These negatives justified changing the controller/training recipe,
   not declaring internal focus impossible. [Timed report](timed-selector-report.md), [PRESS report](press-plan-report.md)
5. **Internal wave, August 30:** a 264k-parameter controller read hidden states and learned a continuous attention
   spotlight through completion loss. Sealed adherence rose 25.2% → 44.8%; targeting/timing ablations mattered.
   This was our closest learned, moment-by-moment focus controller. It still read prompt memory.
   Recurrence perturbations were null, so the real-model state-transplant test never ran. Hidden-state/state scale
   mismatch plausibly suppressed recurrence; that was not settled. The winner was stateless and broke 21 previously
   valid works at seal. Its positive result was superseded for generality, not refuted on its harness. [Report](internal-wave-report.md)
6. **Benchmarks, August 30–September 2:** scaling beyond synthetic coding was necessary.
   But B3 made constraints active throughout each answer, removed the gain penalty, and retired the timing ablation:
   we had already narrowed “focus” to instruction amplification. That was partly benchmark/task convenience.
   Evidence then rejected the tested recipes: synthetic confirmation gained just 0.39 points (p=.389), with extra
   truncations; broader transfer failed do-no-harm gates; amplification on retained KV repeatedly degenerated.
   Several earlier “no headroom” conclusions were instrument errors and were retracted. Those are not negatives
   against focus. The corrected failures justify closing these recipes, not every possible focus signal. [Plan](../BENCH-WAVE-PLAN.md), [Log](../WORKLOG.md)
7. **Retention/classifier, September 2–4:** pin selected historical KV, echo its text near the query, classify what to keep.
   **This is the decisive move to retrieve-and-reinject text.** Preservation worked where amplification failed;
   choosing it as a product route was evidence-based. Making it the main route to Miller was goal drift.
   Leg B: 59.2% with pin+echo versus 16.7% evicted and 65.2% full; NOT SUPPORTED: one invalid event versus full's zero.
   The role rule beat classifier pinning at equal columns; the classifier does not even read the current task when ranking.
   Leg A's teacher-forced retention test is pending. SC1 compares classifier versus rule retention; production episodes/results are absent.
   These can test memory selection, but none requires a transient signal to switch stored competencies. [Program review](astra-program-review.md)
8. **Function vectors, September 3–4:** this briefly returned toward activation control, but mixed skill selection
   with recovering deleted instruction details. A generic “title” vector cannot identify an arbitrary deleted title.
   Sustained injection scored 14/56 versus 10/56 evicted, truncating 14/20; clearing scored 13/56 with 2/20 truncations.
   That rejects this calibration/task combination. It does not settle content-free switching between known skills.

Miller's proposed mechanism rapidly coordinates overlapping neural ensembles: slower control rhythms regulate
where and when faster activity can express stored representations, without rewiring for each thought.
It includes suppression, timing and release—not simply making an instruction louder. The traveling-wave/analog
account remains a theory. “Content-free” is our engineering restriction, not a claim that biological waves carry
zero information. It permits a task address while excluding task answers or arbitrary memory values. [MIT account](https://picower.mit.edu/news/cognition-and-consciousness-arise-analog-computations-says-new-theory)
An artificial analogue must transiently select among demonstrated frozen competencies, hold/switch that selection,
and clear it. Pin+echo supplies content for ordinary attention to interpret; it does not establish those properties.
Transformers already separate fixed weights from transient activity. We need to demonstrate useful additional control.

**The smallest return to your question is one set–hold–switch–clear experiment, with an oracle first.**
Use frozen Qwen and two short-output skills it demonstrably already performs, such as ascending/descending sorting.
Keep novel operands visible. Remove only the task cue; paired decision prompts and starting KV must be identical.
Carry only A/B/OFF. Reuse function-vector extraction on separate, operand-balanced examples to locate candidate
activity directions, and existing layer/gate hooks to modulate them. Freeze one actuator and dose before 64 test episodes.
Compare correct, swapped, shuffled and OFF addresses; transplant at matched decisions. Score complete switching episodes and breakage.
Require operand-sensitive answers to follow the donor task, survive delays, switch back, and stop imposing the old task
after clear. Check subsequent neutral work and residual KV effects; merely disabling a hook does not prove clearance.
This oracle screen tests controllability, not autonomous focus. Only if it passes, adapt the internal-wave controller
to choose A/B/OFF through fixed gain patterns; its current positional checkpoint is not a ready-made skill selector.
Use its gradient-through-frozen-trunk training recipe on separate examples. Compare recurrence with a latch;
normalize state inputs and require reset/transplant dependence for memory; oscillation additionally needs a win over non-oscillatory controls.
Reuse SC1's checker infrastructure and, when available, a separately reserved development episode bank for later realism;
never tune on SC1 setup/final episodes or alter its frozen comparison. No arbitrary-ID recovery test in this first pilot.
Estimated first screen: 8–16 implementation hours, 2–6 GPU-hours; a subsequent learned-controller pilot roughly 8–24 GPU-hours.
These are planning estimates requiring a timing smoke, not measured costs or experiments run for this assessment.

The questions overlap: remembering preserves what could matter; focus chooses what governs now and stops it governing later.
Neither solves the other. **For your stated scientific aim, spend the next new experiment on the small focus screen first.**
Let already authorized work finish under its stop rules. SC1 is the better first choice only if usable assistant memory is
the priority. My earlier [§6 recommendation](astra-research-blockers.md#6-miller-inspired-focus-external-positives-do-not-warrant-another-wave-now) prioritized that engineering goal; it was not a roadmap to proving Miller.
