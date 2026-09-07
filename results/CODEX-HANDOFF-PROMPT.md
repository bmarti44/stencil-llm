You are taking over the Stencil project at /home/bmarti44/stencil-llm (Brian Martin's repo, one GB10 GPU, aarch64, CUDA 13). Read results/HANDOFF-astra.md first, in full, before doing anything. It is the governing state document and it is current as of 2026-09-07. Then read AGENTS.md.

THE GOAL, in Brian's words:
"continue finding a generalized way to implement a miller inspired focus mechanism. use fable, sol, and kimi sub agents to review your work for accuracy. do not over engineer. make sure you can iterate quickly to prove out a hypothesis, and only continue after you have adequate proof on a larger implementation. if you get stuck, do not stop, spin up fable, sol, and kimi sub agents to do deep web research to get you unstuck."

Miller's framing: knowledge is stored in the weights, and a separate selection process decides which stored instruction or competency governs right now, then holds it, switches it, and clears it. The practical target is a coding agent that keeps the right instructions in focus over a long session.

WHERE THINGS ACTUALLY STAND
Two 64-episode runs are complete and both are FROZEN. Neither may be rescored, reinterpreted or rerun.
- results/larger-test/ (SHA 95fa7fc0) FAILED its preregistered conjunction. Primary delivery adherence 40 wins / 0 losses / 24 ties, p = 9.09e-13, but register-arm breakage was 20 episodes against plain history's 14 with a margin of 1 allowed. Every non-write was an indentation SyntaxError.
- results/larger-test-v2/ (pinned e20c3f9b) PASSED its gates after Amendments 6 and 6b introduced scoped-function submission and one syntax repair turn. Breakage fell from 20 to 1. Delivery 35/0/28, Holm 8.73e-11; format 25/4/34, Holm 1.04e-04; indent not significant.
THE PASS IS NARROW AND THE "ADEQUATE PROOF" GATE IS NOT MET. Two independent maximum-reasoning reviews agree. The hand-written prose comparator equals or beats the register on every obligation family and on adherence, and beats it on producing semantically correct code (45 vs 52, seven discordant episodes all one way, p = 0.0078). So nothing establishes that the register representation contributes anything over simply restating the right rule at the right time. Repair efficacy is zero. The fresh bank reuses 98.63% of its turn-level tasks from the spent one.

THE ONLY SUPPORTABLE CLAIM: request-time restatement of the currently effective obligations, whether from the register or as plain prose, recovers one specific silent-default rule transition that ordinary retained history does not, with gains that survive clustering and adversarial flips.

WHAT IS CLOSED, and do not reopen without a new hypothesis: router-logit expert steering on the MoE trunk (it flips output language but reduced hidden-test success from 16/32 to 7/32); dense-model activation, neuron, SAE and KV-transplant steering; concept-level routing. Adapters as a focus carrier are parked with one clean positive (set a mode 12/12 against 0/12 for a scrambled control, at zero prompt tokens) and an inadmissible switch test.

WHAT IS UNSOLVED, each with a research report and a costed test in results/NEXT-TESTS-PLAN.md: automatic rule admission from natural text; the context cost of rendering; off-task detection; a model that co-emits register operations; and whether compliance can be bought without competence loss.

THE AGREED NEXT EXPERIMENT, specified but NOT authorized: one fresh 32-episode paired factorial, 16 rounds, crossing whole-file against scoped submission with the plain-history, register and composed-prose arms; 3,072 calls; about 5.32 GPU-hours; primary is per-episode paired private-test integration plus adherence; on a separately frozen bank with new semantic parameterizations. It separates the protocol effect from the mechanism effect, which the passing run confounds. Get Brian's approval before spending GPU time on it.

HARD RULES, never violate:
- Never fit, select, tune or calibrate on any evaluation benchmark or any exposed bank. Write the data-lineage line (fit-on, development-on, evaluated-on, disjoint) FIRST in every brief and registration. Never read data/bench/ifeval_input_data.jsonl.
- Pre-register: write the pass/fail reading before running anything; one look per held-out bank; no threshold or prompt changes after the look; INCOMPLETE and INELIGIBLE are not null results; never silently shrink a sample.
- Every result gets an independent accuracy review at maximum reasoning effort before it is believed. Reviewers write only their own review file and never edit code. Apply the review's corrections as an addendum to the result file rather than editing the original claims.
- Test any gate against its own negative control at the registered unit before freezing it. Two gates in this project failed because they were never calibrated, and one would have failed an arm that could not suffer the harm it measured.
- The episode is the unit of analysis. Rounds within an episode are correlated, and treating them as independent produced false findings twice.
- No string matching or regular expressions in the register path; typed fields or classifiers only. Retirement masks a rule, never deletes it. Every live obligation is rendered in every request.
- results/* is gitignored: commit registered artifacts with git add -f and explicit pathspecs. Never commit a file over 10 MB. HF_TOKEN and ANTHROPIC_API_KEY are in the environment; never print them and never spend on the API without Brian's approval.
- GPU coordination is by RUNNING.flag files under results/quick-checks/<check>/. Wait for any other flag to clear. Register every background launch in .stencil-owned-pids. Never signal a process you did not launch. Stop and remove only your own containers.
- Do not over-engineer. Rank hypotheses, run a quick check under one GPU-hour, get it reviewed, and only then consider anything larger. Three failures of the same bar means park the line.

PRACTICALITIES: the qualified serving stack is the vLLM image vllm/vllm-openai:cu130-nightly with VLLM_BATCH_INVARIANT=1, prefix caching and max-num-seqs 4, digest and flags recorded in results/quick-checks/vllm-qual/. The trunk is models/qwen3-30b-a3b-hf. A dense Qwen 3.8 27B candidate was screened and the decision was to stay, on cost and on its hybrid attention layout. Hand-authored data is written by kimi-k3 through a local ollama server. Every brief and chain script from this work is committed under results/handoff/.

START HERE: read results/HANDOFF-astra.md, then results/NEXT-TESTS-PLAN.md, then check whether anything is running with `ls results/quick-checks/*/RUNNING.flag` and `nvidia-smi`. Report what you find and what you propose before you spend anything.
