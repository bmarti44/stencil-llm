# Open problem 2 for gpt-6-astra: RENDERING RULES WITHOUT BLOWING UP THE CONTEXT (2026-09-07)

Brian's framing: "how to insert the instructions without drastically increasing the context window". This is measured,
not speculative. In-repo evidence to verify and extend: the pilot-7 Opus review measured the register arm's prompt at
about 13.2k tokens versus 6.4k for plain history, with 16 copies of the rule block in one prompt accounting for 34.7%
of its tokens because history is never re-composed (src/stencil/focus/loop.py:363, and 7 of those copies still carried
a superseded imperative); Amendment 4's block trim took a CPU re-render from 17,126 to 8,412 tokens; check 42
established that rendering in EVERY request is what works, so the naive fix of rendering less often is ruled out by our
own data; check 51 showed placement at current-user recency beats a retained transcript. Also relevant: the certified
attention-mask release (checks 40h/40i) which hides the model's own stale outputs while preserving positions, and the
fact that prefix caching keys on the prompt prefix so a changing block defeats reuse for everything after it.
Research the space: prompt/context compression, gist and soft-prompt tokens, KV-cache compression and eviction,
selective attention, structured or delta rendering (render only what changed plus a compact digest), re-composing or
masking stale copies of the block in history, cache-friendly placement, and anything shipping agent harnesses do.
Be explicit about the tension: cheaper rendering must not lose the every-request property or the recency placement.
Write results/open-problem-2-context-astra.md.
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
