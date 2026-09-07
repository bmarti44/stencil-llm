# Open problem 3 for gpt-6-astra: DETECTING WHEN THE MODEL IS GOING OFF TASK (2026-09-07)

Brian's framing: "how to track when the model is getting off task". In-repo evidence to verify and extend: check 45
(the off-task probe) read INSUFFICIENT DATA and was never fitted, because the pilot that was to supply hidden states
was ineligible; the design was a linear probe on last-prompt-token hidden states with leave-episodes-out folds and a
text-similarity baseline. Critically, the repo now contains a very concrete off-task PHENOMENON to detect: the LOCK.
Pilots 3 through 7 repeatedly show that once a lane emits a malformed or non-compliant reply, the model copies its own
prior output and never recovers, with 0 of 96 locked rounds recovering in pilot 5 and all four residual failures in
pilot 7 being consecutive rounds of one episode. Also relevant: the style-imitation finding in check 40j (the model
copied its own indentation 16/16 while obeying the stated rule), the ReBIND relapse probe from the reuse research
(AUROC about 0.9 for predicting relapse to a revoked constraint), and the fact that we now have thousands of saved
labelled rounds from pilots 5, 6 and 7 with hidden checker outcomes per round, which may be enough to fit a detector
on CPU without any new GPU generation.
Research and rank: pre-generation probes on hidden states, cheap post-generation detectors on the emitted text,
self-consistency or verifier calls, uncertainty and entropy signals, drift detection over a trajectory, and what
detection would be FOR: triggering a stronger re-render, the certified mask, a repair turn, or an escalation.
Write results/open-problem-3-offtask-astra.md.
PROTECTED: the registered 64-episode larger test is RUNNING on the GPU. CPU and web only. Do not touch the GPU, any
RUNNING.flag, any container, anything under results/larger-test/, or any code. Never signal any process. Never read
anything under data/bench, and do not read evaluation-bank episode CONTENT (manifests, summaries and hashes only).
Read results/full-program-review-astra.md first: it is the corrected claim ledger, and several repo claims are marked
OVERSTATED or CONTRADICTED. Do not rely on a repo claim without checking it there. Also read results/HANDOFF-astra.md
(corrected 2026-09-07) for state, and results/CLAIMS-CORRECTIONS.md.
METHOD: (1) VERIFY IN-REPO FIRST — enumerate exactly what has already been tried for this problem, with file:line and
the real numbers, and say what each attempt actually established and where it stopped. Do not repeat prior work.
(2) DEEP WEB RESEARCH — arXiv, ACL/ICLR/NeurIPS/EMNLP, GitHub, HF Hub, vLLM/PEFT/transformers docs and issues, and
engineering write-ups from shipping agent harnesses. Open what you cite; mark anything unverified. "Nothing reusable"
is a valid answer; do not force a fit.
(3) TOP 3 most likely solutions, ranked, each with: what it is, the evidence it works, why it fits OUR constraints
(frozen trunk; one HF download; no string matching in the register path; retirement by masking never deletion; never
fit or select on any evaluation benchmark; audited data lineage), the effort in hours, and the risks.
(4) A QUICK TEST for each of the three, designed so we can run it fast: <= 1 GPU-hour (state the number), a
pre-written GO/NO-GO reading with concrete thresholds, the exact evaluation bank to use and whether it is already
author-disjoint and unexposed (check the per-bank exposure table in the handoff; held-out sets 1-3 are EXPOSED and
held-out-4 had its annotation conventions used in a training repair), the data-lineage line, and what a null result
would close. Prefer tests that reuse existing harnesses and saved records over new infrastructure.
End with a one-paragraph plain-language verdict for Brian: is this problem solvable with what we have, and what is
the single cheapest experiment that would move it most.
Write ONLY your one report file and commit it with an explicit pathspec (git add -f); no push.
