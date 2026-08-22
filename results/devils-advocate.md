The high-level idea is old. The exact Stencil conjunction is not. Crucially, the literature has not shown the broad idea to be useless; most close attempts report positive results. The strongest case for killing Stencil is therefore not “prior work already failed,” but “the proposed experiment manufactures a need for an unnecessarily complicated solution while omitting simpler task-memory baselines.”

## 1. What has actually been tried

### Tried and worked

| Prior attempt | Resemblance to Stencil | What happened |
|---|---|---|
| **FiLM — Perez et al., 2018** | An RNN encodes a question; its output produces feature-wise multiplicative and additive modulation of a separate processing network. This is already a “control representation modulates content computation” architecture. | Strong positive result: FiLM roughly halved then-state-of-the-art CLEVR error. It became a general conditioning pattern, not a failed idea. It is static after encoding the instruction, rather than a per-token slow controller. [FiLM](https://ojs.aaai.org/index.php/AAAI/article/view/11671) |
| **HyperNetworks/HyperLSTM — Ha, Dai & Le, 2016** | A small recurrent hypernetwork dynamically generates scaling vectors and biases for a larger recurrent network at each timestep. This is extremely close to “a slow pathway dynamically modulates a target network.” | Positive sequence-modeling results, including near-state-of-the-art character LM. HyperLSTM did not become a standard architecture after Transformers arrived, but the paper did not show it was useless. Its disappearance is adoption evidence, not failure evidence. [HyperNetworks](https://arxiv.org/abs/1609.09106) |
| **Context-dependent gating/XdG — Masse, Grant & Freedman, 2018; HAT — Serra et al., 2018** | Explicit task identity produces multiplicative masks over network units. | HAT substantially reduced continual-learning forgetting. XdG alone was inadequate—about 61% mean accuracy after 100 permuted-MNIST tasks—but XdG plus synaptic stabilization reached about 95%. This is the cleanest genuine partial negative: a task gate by itself does not solve continual learning. It does not test instruction persistence. [XdG](https://pmc.ncbi.nlm.nih.gov/articles/PMC6217392/), [HAT](https://proceedings.mlr.press/v80/serra18a/serra18a.pdf) |
| **CA-MTL — Pilault et al., 2021; HyperFormer — Mahabadi et al., 2021** | Learned task embeddings condition Transformer attention, layer normalization, and generated adapters. HyperFormer even removes T5’s textual task prefixes and substitutes task-conditioned modules. | Positive multi-task results. These are direct Transformer precedents missing from Appendix F’s high-level map. [CA-MTL](https://arxiv.org/abs/2009.09139), [HyperFormer](https://aclanthology.org/2021.acl-long.47/) |
| **HyperPrompt — He et al., 2022** | A hypernetwork converts task identity into task-global memories that condition Transformer self-attention. | Outperformed prompt-tuning and HyperFormer++ baselines on GLUE/SuperGLUE with about 0.14% extra task-conditioning parameters. Again positive, although static and externally task-indexed. [HyperPrompt](https://proceedings.mlr.press/v162/he22f.html) |
| **HINT — Ivison et al., 2023** | Encodes natural-language instructions and demonstrations once, then generates adapters and prefixes for a Transformer, eliminating repeated instruction processing. This is probably the closest prior attempt to the claimed practical use case. | Positive: more than 10% improvement over strong baselines under compute control, according to the paper. It is not recurrent and also supplies an encoded instruction to the decoder, so it does not enforce Stencil’s strict pathway claim. [HINT](https://aclanthology.org/2023.acl-long.631/) |
| **IA³ — Liu et al., 2022** | Task-specific learned vectors multiplicatively scale Transformer key, value, and feed-forward activations. | Strong positive parameter-efficient adaptation results. It demonstrates that very simple static multiplicative modulation is sufficient when task identity is known. [IA³/T-Few](https://arxiv.org/abs/2205.05638) |
| **NM-RNN — Costacurta et al., 2024** | A low-dimensional, slow neuromodulatory recurrent subnetwork dynamically scales the recurrent weights of an output-generating network. This is the closest dynamical conceptual ancestor. | Positive on small timing and multitask problems; it matched LSTM/higher-rank RNN performance and beat an unmodulated low-rank RNN in reported comparisons. It was only tested around 100 neurons and is not a Transformer, but it was not a failure. [NM-RNN](https://proceedings.neurips.cc/paper_files/paper/2024/hash/03bec5d9f651c1fb89be07a4120238a0-Abstract-Conference.html) |
| **MEGA/Megalodon; Samba; Qwen gated attention** | Recurrent or moving-average state shapes gated attention; hybrid recurrence carries long-range information; per-head attention gating works at LLM scale. | All report positive results. Megalodon scaled complex damped recurrence plus gated attention to 7B/2T; Samba scaled recurrent state plus sliding attention to 3.8B/3.2T; Qwen’s simple stateless gate improved quality and stability. None enforces task/content separation. [MEGA](https://arxiv.org/abs/2209.10655), [Megalodon](https://arxiv.org/abs/2404.08801), [Samba](https://arxiv.org/abs/2406.07522), [Qwen gated attention](https://arxiv.org/abs/2505.06708) |

### Tried, then largely not followed up

HyperLSTM, Fast-Slow RNNs (Mujika et al., 2017), Clockwork RNNs (Koutník et al., 2014), Phased LSTM (Neil et al., 2016), Neural Programmer-Interpreters (Reed & de Freitas, 2016), and several learned-routing architectures produced promising toy or specialist results but did not become mainstream general-purpose sequence models. That history supports a pessimistic prior about architectural complexity and ecosystem fit. It does not establish that the mechanisms failed.

The rhythmic precedent is particularly unhelpful to Stencil: Phased LSTM used oscillation to schedule computation for irregular event streams, not to store task identity, and still remained niche despite positive results. [Phased LSTM](https://papers.nips.cc/paper_files/paper/2016/hash/5bce843dd76db8c939d5323dd3e54ec9-Abstract.html)

### Actually negative or superseded evidence

There are three meaningful negatives:

- **Gating alone is insufficient for continual learning.** XdG needed synaptic stabilization. A task wire does not automatically prevent interference or forgetting.
- **Architectural parameter efficiency may not be system efficiency.** Mundra et al. (2023) found that adapters’ small parameter count did not translate into training/deployment gains; they added latency and could be beaten operationally by simpler full or multi-task fine-tuning. Stencil’s serial per-token controller faces a worse version of this objection, while Phase 6 registers no throughput criterion. [A Comprehensive Analysis of Adapter Efficiency](https://arxiv.org/abs/2305.07491)
- **Rigid/non-dissipative oscillatory memory has an adverse prior.** D-LinOSS explicitly argues that forgetting is important and shows learnable damping outperforming more rigid oscillatory formulations. This is serious evidence against M1, but Stencil already contains M1b, so it does not kill the overall controller idea. [D-LinOSS](https://arxiv.org/abs/2505.12171)

### Never really tried

I do not know of a serious prior experiment combining all of the following:

1. natural-language instruction encoding;
2. a persistent recurrent state constrained to carry task rather than instance content;
3. no additive write into Transformer representations;
4. modulation only through attention-head gains;
5. comparison against pinned/global instruction KV, prompt repetition, static task registers, simple recurrent controllers, and content-memory hybrids;
6. natural long-horizon instruction-following evaluation at meaningful scale.

That exact experiment has not been tried and failed. Appendix F’s claim of an untested conjunction is plausible, but its high-level survey is incomplete because it omits FiLM, CA-MTL, HyperFormer, HyperPrompt, HINT, HAT/XdG, and IA³. [Appendix F](/home/bmarti44/stencil-llm/PLAN.md:517)

## 2. Why success could still be a dead end

The strongest objection is that task identity is piecewise constant metadata, not a signal that naturally calls for a continuously driven oscillator.

For an ordinary full-attention decoder, the instruction’s keys and values remain in the KV cache. With bounded attention, simpler remedies already exist:

- retain or globally attend to the instruction tokens;
- pin a small instruction prefix in the cache;
- repeat or retrieve the instruction periodically;
- encode it once into static prefix KVs;
- use a task embedding, FiLM/conditional normalization, IA³ vector, or HINT-style generated module;
- maintain a literal task register updated only at authenticated instruction boundaries.

Longformer, ETC, and BigBird demonstrated local attention plus a small number of global tokens years ago. A cue marked global would destroy Stencil’s “room with no doors” at linear rather than quadratic cost. [Longformer](https://arxiv.org/abs/2004.05150), [ETC](https://research.google/pubs/etc-encoding-long-and-structured-inputs-in-transformers/), [BigBird](https://papers.nips.cc/paper/2020/file/c8512d142a2d849725f31a9a7a361ab9-Paper.pdf)

Prompt and prefix tuning provide even simpler persistent task control. Prefix-tuning places task-specific activations at every Transformer layer, while prompt tuning becomes more competitive as model scale increases. [Prefix-Tuning](https://aclanthology.org/2021.acl-long.353/), [Prompt Tuning](https://aclanthology.org/2021.emnlp-main.243/)

The argument is not completely fatal because retained context is not reliably used: *Lost in the Middle* showed severe position effects even in long-context models. [Liu et al., 2024](https://aclanthology.org/2024.tacl-1.9/) But that establishes a retrieval/allocation problem, not that an oscillator is the right fix.

Worse, Stencil is not structurally content-free. Its controller ingests every token embedding into a 128-dimensional state and emits 16 real-valued gates at every position. Multiplication is still a communication channel. The plan explicitly admits that these gates are not an information bottleneck and could carry arbitrary content. [Architecture](/home/bmarti44/stencil-llm/PLAN.md:207) Calling this a protected “task-only lane” is therefore false unless training happens to use it that way. Task M can detect one particular form of content routing; it cannot establish conditional independence from content.

Finally, the serial controller imposes training and inference costs. If its recurrence is parallel-scanned, that engineering is excluded from v1; if it remains serial, it attacks the Transformer’s main systems advantage. Phase 6 tests LM loss and synthetic accuracy, but not tokens/sec, latency, memory, or energy. [Phase 6](/home/bmarti44/stencil-llm/PLAN.md:424)

## 3. Why the toy proof is rigged to succeed

The experiment proves that an added path can carry information after every competing path is deleted. It does not prove that this particular path is useful.

- **The baseline is deliberately disconnected.** B0-local and B1 are constructed to have exactly zero access to the cue; M1, M1b, and B2 receive it through an unbounded recurrence. Any recurrent register, one global cue token, pinned KV, or periodic cue repetition should win. The exact-zero gradient proves the graph was cut, not that oscillatory control is needed. [Section 1](/home/bmarti44/stencil-llm/PLAN.md:60)
- **B1 is a straw baseline for memory.** A stateless Qwen gate is not intended to recover information beyond its receptive field. Beating it isolates statefulness tautologically.
- **The missing baseline is devastating.** There is no task-triggered latch that copies the cue embedding and holds it until the next cue; no GRU/LSTM controller; no global cue token; no pinned prefix; no instruction reinjection; and no HINT/HyperPrompt-style static conditioning. B2 is a continuously updated decay SSM, not the obvious piecewise-constant task register.
- **The data advertise the shortcut.** Cue, distractor, operand, and query vocabularies are disjoint. Rules are fixed across train and evaluation. The model need only map one of 32 atomic cue IDs to a gate signature selecting a memorized permutation. It never has to understand an instruction, infer a new rule, or distinguish instruction text from ordinary content. [Task A](/home/bmarti44/stencil-llm/PLAN.md:285)
- **The task is algebraically ideal for gating.** Output is exactly `f(task_id, local_operand)`: preserve a small discrete task ID, then modulate local computation. That is almost a constructed demonstration of conditional computation.
- **Parameter matching does not match information access or sequential cost.** Giving one model a path to the answer and denying it to another dominates a 1% parameter-count adjustment.
- **Mechanism evidence is partly circular.** A probe decoding the rule from a state directly driven by the cue is unsurprising. Patching the entire state trajectory also transplants state after it has seen the operand; the plan itself acknowledges that this does not separate rule identity from computed content.
- **Phase 6 still does not test the motivating claim.** A 95% corpus/5% synthetic mixture followed by synthetic-suffix accuracy and “no LM-loss regression” does not evaluate real instruction drift, conflicting instructions, prompt injection, nested goals, natural task switching, or task generalization. The README correctly concedes that success would not establish large-model benefit. [README limitations](/home/bmarti44/stencil-llm/README.md:60)

## 4. Kill-argument grades

| Kill argument | Grade | What would settle it |
|---|---|---|
| “This broad architecture was tried and shown useless.” | **WEAK** | A direct negative comparison of a recurrent task controller against strong task-conditioning and memory baselines. Existing close evidence is mostly positive. |
| “Prompts/KV already solve task persistence, so the wire solves no problem.” | **SERIOUS** | Natural long-horizon instruction tests comparing full KV, pinned/global instruction KV, periodic reinjection, retrieval, and Stencil at matched quality, memory, and latency. |
| “The pathway is not content-free and therefore does not instantiate the motivating separation.” | **FATAL** to the separation claim | Restrict controller input to a trusted instruction channel or instruction-boundary updates, plus adversarial content-interference and capacity tests. Task M alone is insufficient. |
| “A piecewise-constant latch or static task embedding dominates an oscillator.” | **SERIOUS**, potentially fatal to the oscillator contribution | Add matched latch, GRU, EMA/decay, IA³/FiLM, global-token, and generated-prefix baselines. Compare accuracy, switching, stability, and throughput. |
| “The toy result is guaranteed by unequal reachability.” | **FATAL** to any usefulness inference from G3 | Give every comparator a cheap route to task identity, then test which representation is most robust and efficient. Also require unseen rules and natural instructions. |
| “Sequential controller overhead makes it noncompetitive.” | **SERIOUS** | Report training throughput, decode latency, memory, and energy at 125M and larger scales; include a scan implementation and pinned-KV/global-token alternatives. |
| “Undamped oscillatory memory is already disfavored.” | **SERIOUS** for M1, **WEAK** for the project | M1 versus M1b versus latch/GRU/EMA on both persistence and switching, including natural tasks. |
| “Non-adoption of HyperLSTM/Phased-LSTM/HINT proves abandonment.” | **WEAK** | Non-adoption is not a controlled result. Evidence would require later head-to-head studies showing worse quality–cost tradeoffs, not merely fewer citations or deployments. |

## 5. Verdict

**No: the project should not be killed on prior-art-futility grounds.** The broad concept has been tried repeatedly, but it was generally shown to work—not shown useless. The exact task-only recurrent modulation experiment has not received a decisive negative test.

The single most load-bearing reason is that the closest evidence—FiLM, HyperLSTM, HyperFormer/HyperPrompt/HINT, IA³, and NM-RNN—is positive. Silence or non-adoption cannot be converted into a failure result.

However, the current plan cannot establish high-level usefulness. Without global/pinned instruction tokens, prompt reinjection, a literal task latch, GRU, and HINT/FiLM-style conditioning baselines, a green G3 would mean only: “a recurrent bypass crosses a barrier that the experiment deliberately made uncrossable.” If those baselines are not added, the usefulness claim—not necessarily the mechanistic proof-of-concept—should be killed.