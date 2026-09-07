# Open problem 6 for gpt-6-astra: extract the ONE method that reports NO compliance/competence tradeoff (2026-09-07)

Brian's question: "tell me about the published report without any tradeoff, how would we replicate that?"
We currently hold only Table 1 numbers and a one-line characterisation, cited in
results/dense-focus-research-astra.md and results/open-problem-5-compliance-competence-astra.md: DIRECTER,
ICLR 2026, https://arxiv.org/html/2603.06745v1, Table 1 and section 3.2. On Llama-3.1-8B the reported
format/task pairs are baseline 79.2/82.7; PASTA 99.2/48.1; tuned PASTA 98.9/62.7; SpotLight 98.8/38.0; tuned
SpotLight 95.4/78.7; DIRECTER 99.1/86.9 — the only row with BOTH numbers above baseline. Our memo describes it as
"instruction-aware attention control with dynamic rejection" that "retains instruction information and adds
decoding machinery; it is not text-free selection." That is all we have. Get the rest.
TASK:
1. OPEN THE PAPER PROPERLY and extract the METHOD, not the results: what exactly is instruction-aware about the
   attention control (how are heads/layers/positions selected, and is the selection per-instruction, per-token or
   fixed?); what precisely is "dynamic rejection" (what is rejected, on what signal, at what granularity, and what
   is the fallback?); what decoding machinery is added and at what inference cost; what is trained versus free;
   what hyperparameters exist and how were they tuned; what ablations does the paper run, and specifically does it
   show which component prevents the task-accuracy collapse that PASTA and SpotLight suffer.
2. CODE AND ARTIFACTS: is there a released implementation, checkpoint or config? License? Does it run on an
   arbitrary HF causal LM, and would it work on a mixture-of-experts trunk and through vLLM, or does it require
   custom attention hooks in the HF path (we have both paths qualified; see results/quick-checks/vllm-qual/)?
3. SCOPE AND LIMITS: their setting is single-turn with ONE fixed format constraint; ours is multi-turn agentic
   coding with obligations that CHANGE mid-episode. State plainly what transfers and what does not. Note our
   ceiling problem: on the axis their method improves, our plain-text baseline was already 16/16 (check 40j) and
   our register reaches 100% delivery adherence (results/larger-test/RESULTS.md), so their headroom does not exist
   for us there. The one family where our rendering still fails is STYLE/indent (register arm 9/54 paired episodes,
   no significant gain; 10/15 at change rounds in pilot 7) — assess whether their mechanism plausibly addresses
   that specific gap.
4. Compare it against the other partial successes our memos already opened: tuned PASTA and tuned SpotLight (are
   they just dose fixes?), ReCoVeR, SKOP, distribution-aware steering. Is DIRECTER's no-tradeoff result unique,
   replicated anywhere, or contested?
5. REPLICATION PLAN in stages, each with a cost and a pre-written GO/NO-GO:
   S1 faithful reproduction on THEIR model and benchmark (state the GPU cost on our GB10; their benchmark data may
      inform design but may NEVER be fit or selected on, per our standing rule; say exactly how the rule is kept).
   S2 the transferable idea only — dynamic rejection as a COMPETENCE GUARD in our harness: apply the control, run
      the hidden executable check, revert when the work regresses. Design this against our style/indent family with
      episode-level pairing and both compliance and executable quality measured together.
   S3 what would have to be true after S1 and S2 to justify anything larger.
End with a plain-language verdict for Brian: is this the method that breaks the tradeoff, is it replicable by us,
and what is the single cheapest step that would tell us.
Write results/open-problem-6-directer-astra.md. CPU and web only; the GPU is running Amendment 6b — do not touch it,
any RUNNING.flag, any container or any process. Never read anything under data/bench. Open what you cite; mark
anything you could not open as unverified; if the paper is inaccessible, say so plainly and give the best available
secondary evidence. Commit only that report with an explicit pathspec (git add -f); no push.
