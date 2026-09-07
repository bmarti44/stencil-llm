# Open problem 1 for gpt-6-astra: AUTOMATICALLY ADMITTING AND UPDATING RULES (2026-09-07)

Brian's framing: "automatically inserting new rules, or updating the rules". Today rule entry is EXPLICIT and typed;
learned components are assistive only. In-repo evidence to verify and extend: checks 44, 44b, 44c (admission span
detection: 2.75% / 72.95% / 64.16% recall against an 85% bar; splitter ceiling; cue-less and multi-rule failures),
check 46 (the frozen 30B trunk as a structured updater, six-shot in-context, best recall so far at ~79% with ~90%
precision, relations 89%, supersedes 87%, but 58/96 false-admission turns on the gate template and 0/21 on
task-scoped overrides of global rules), check 48 (fitted Qwen3-4B updater LoRA: COST-INELIGIBLE, never fitted),
relations v2/v3 (96% on ordinary phrasing, 73% supersedes recall on override idioms; v3 NO-GO), the GLiNER probe
(idea only), and both updater research memos (results/updater-research-{astra,fable}.md). Include the security
angle: an automatic admitter is an authority boundary, so precision and role/provenance gating matter more than
recall alone. Consider trunk-proposer plus small fitted verifier, activated LoRA, better data for the named miss
families, constrained decoding, and anything the literature has that we have not tried.
Write results/open-problem-1-admission-astra.md.
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
