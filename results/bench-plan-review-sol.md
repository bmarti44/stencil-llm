codex
NOT CLEARED. One CRITICAL and six HIGH findings change execution.

The checkpoint identity is nearly resolved already: local Hugging Face metadata names revision `70d244cc86ccca08cf5af4e1e306ecf908b1ad5e`, and its config—EOS `151645`, 40,960 positions—matches post-trained `Qwen/Qwen3-1.7B`, not `Qwen3-1.7B-Base`, whose EOS is `151643` and context is 32,768. Scope every claim to “Qwen/Qwen3-1.7B@70d244…, post-trained non-thinking chat mode, greedy,” not generically “Qwen3-1.7B.” [Official post-trained config](https://huggingface.co/Qwen/Qwen3-1.7B/blob/3f1b00af457d7003d437d3e65dbd0e2c0afb1415/config.json), [official Base config](https://huggingface.co/Qwen/Qwen3-1.7B-Base/blob/main/config.json).

1. CRITICAL — the “sealed” IFEval set is consumed before B3 freezes.

[B0.3 and B1](/home/bmarti44/stencil-llm/BENCH-WAVE-PLAN.md:27) run all 541 prompts and expose per-prompt outcomes; B3 details are only registered afterward at checkpoint ii. B4’s claim that the same prompts are “untouched” is false. This permits adapting the generator, proxy, or training recipe to observed errors.

Fix the order:

- B0 uses hand-built fixtures and performance smoke prompts only.
- Fully freeze B3 generator, proxy, recipe, and evaluation code.
- Run base/wave/proxy together on all 541 as the single B4 sealed job.
- Move B1 after B4, or restrict it to a permanently excluded development subset.

2. HIGH — the runner path and runtime are not executable as a quick-turnaround program yet.

Choose one implementation; [“Google or lm-eval”](/home/bmarti44/stencil-llm/BENCH-WAVE-PLAN.md:21) is an unregistered fork. Use a direct deterministic runner with a commit-pinned copy of the official Google data/verifiers for IFEval. Use a pinned lm-eval adapter only for MMLU/GSM8K. Its custom model interface introduces additional `generate_until`, stopping, and chat-template behavior that IFEval does not need. [Official IFEval evaluator](https://github.com/google-research/google-research/blob/master/instruction_following_eval/evaluation_main.py), [lm-eval custom-model interface](https://github.com/EleutherAI/lm-evaluation-harness/blob/main/docs/model_guide.md).

Five verifier fixtures are inadequate for 25 instruction classes. Require positive and targeted-negative goldens for every class present in the 541 prompts, plus four-metric aggregate parity against the pinned upstream implementation.

More importantly, [`Qwen3.forward`](/home/bmarti44/stencil-llm/src/stencil/qwen3.py:132) has no KV cache. Hundreds of potentially 1,000-token generations across several arms will not preserve the prior sub-two-hour cadence. Before B0.3, require:

- an actual 20-prompt generation timing admission test;
- exact `max_new`, EOS IDs, truncation accounting and template bytes;
- either a full-forward runtime below the bound or a KV-cache implementation with token-by-token parity against full forward, including wave bias.

3. HIGH — checkpoint verification must cover provenance and templating, not merely architecture config.

Amend B0.1 to record the exact repository/revision and SHA-256 of config, tokenizer, index, shards and converted weights. Fresh parity must compare:

- identical token IDs from the pinned chat template;
- `enable_thinking=False`;
- identical last-token logits/top-1 against Transformers 4.51.0 loading that exact revision.

Greedy non-thinking is appropriate for deterministic paired experiments, but it is not matched to Qwen’s recommended sampled non-thinking settings; therefore 68.2 remains an anchor only. Qwen recommends temperature 0.7/top-p 0.8 for non-thinking. [Official Qwen guidance](https://huggingface.co/Qwen/Qwen3-8B/blob/main/README.md#enable_thinkingfalse).

4. HIGH — B2 cannot currently support a “do no harm” claim.

The research note names MMLU-Redux, while [B2 says MMLU](/home/bmarti44/stencil-llm/BENCH-WAVE-PLAN.md:42). Select and pin one dataset, revision, prompt format and few-shot policy. A seeded subset is not reproducible without exact item IDs and sampling-order rules.

The GSM8K `n=200`, 1-point bound is statistically impossible at 95% confidence: even zero adverse flips gives a one-sided binomial upper bound of about 1.49%. Either:

- run at least 300 items—and preferably all 1,319—with a registered paired non-inferiority test; or
- call the thresholds practical point-estimate gates and retract the evidential “no harm” claim.

Also freeze the four demonstrations and extractor: current lm-eval GSM8K defaults to five-shot, not four-shot. [Pinned task specification](https://github.com/EleutherAI/lm-evaluation-harness/blob/main/lm_eval/tasks/gsm8k/gsm8k.yaml), [GSM8K split size](https://github.com/tensorflow/datasets/blob/master/docs/catalog/gsm8k.md).

5. HIGH — B3’s synthetic separation is insufficient for the proposed generalization claim.

Same taxonomy with new wording and parameters establishes phrase/parameter transfer within seen constraint families. It does not establish constraint-family generalization. Freeze:

- disjoint semantic tasks, templates, parameters and canonical responses;
- a constraint compatibility matrix;
- exact train/dev manifests and normalized leak checks;
- per-family seen-versus-unseen evaluation.

The listed canonical families are constructible individually. Arbitrary combinations are not: JSON conflicts with bullets and external start/end text; whole-response case can break JSON literals or case-sensitive keywords; exact length interacts with wrappers; exclusions can occur in semantic payloads. Every accepted combination needs a passing canonical response and a targeted mutation that fails the intended verifier.

6. HIGH — the proxy twin is not causally matched.

[“Press at response start”](/home/bmarti44/stencil-llm/BENCH-WAVE-PLAN.md:61) gives the proxy one supervised row while CE trains through every canonical response token. A wave win could merely show that one-row proxy labels are inadequate.

Use identical response-row support: proxy gain positive across every teacher-forced response row—or a preregistered per-constraint relevance mask—and span CE over all active constraint spans at those same rows. Keep architecture, actuator, initialization, optimizer and step count identical. Otherwise scope the claim to “CE beats a start-only heuristic,” not training-signal causality.

7. HIGH — cross-benchmark confirmation and B4 causal gates remain gameable.

The +2-point IFEval primary is coherent: on 541 prompts it requires exactly at least 11 net strict-prompt gains, plus one-sided McNemar `p<.05`. Keep it. The published +3–7 band uses different models and decoding, so it should not set this threshold.

But “wave > proxy” needs its own paired test, not a one-prompt raw inequality. Make causal support require one-sided prompt-level McNemar `p<.05`; otherwise report performance without causal attribution.

Do not choose benchmark #3 after seeing B4. Pre-register IFBench now as the cross-taxonomy test: it explicitly supplies 58 OOD verifier families. Multi-IF is useful but is a three-turn extension of IFEval, not a long-horizon benchmark; describe it as exploratory three-turn transfer. [Official IFBench specification](https://github.com/allenai/IFBench/blob/main/README.md), [Multi-IF paper and harness](https://github.com/facebookresearch/Multi-IF).

Finally, replace the two generic seeds with exact train/dev/calibration streams, model-initialization seeds, dataset revisions and committed item manifests. One trained seed supports an artifact-specific result; require a second frozen training seed before claiming broad external validation.
