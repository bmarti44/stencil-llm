# Deep web research brief (2026-09-06): what already exists that we could reuse — academic AND code sources

Purpose (Brian): with the current repo context and our outstanding problems, search academic sources (arXiv, ACL/ICLR/
NeurIPS, blogs of labs) AND code sources (GitHub, HF Hub repos/spaces, PyPI, vLLM/SGLang/TGI/transformers issues and
PRs) for work that has ALREADY solved or partly solved what we are building, and that could be reused in this project
EASILY. Do not force a fit: say "nothing reusable" where that is the honest answer. Also include anything else that
could help that we may not be thinking of.

Context to read first (CPU, read-only): AGENTS.md; results/focus-mechanism-composition-astra.md and
results/composition-design-review-fable.md (the current design + its review); results/quick-checks/README.md items
31-44b (one-paragraph results each) and results/quick-checks/check40g/README.md, check44b/RESULTS.md,
results/check44b-review-fable.md; results/admission-research-astra.md, results/moe-routing-research-astra.md,
results/neuron-granularity-research-astra.md (prior research memos — do NOT repeat them; extend them); memory of the
goal: a Miller-inspired focus mechanism on a frozen Qwen trunk ("synapses store; waves select"): select which stored
instruction/skill governs now, hold it, switch, clear — for agents on long-horizon coding sessions.

Outstanding problems (search for prior art on EACH; give reuse verdicts):
P1. ADMISSION: detecting standing rules/persistent instructions in user messages (span-level; multi-rule sentences;
    payload/quoted negatives). Prior art: instruction-following/constraint extraction datasets and models,
    "system prompt / persistent instruction" extractors, memory-write policies in agent memory systems (Mem0, Letta/
    MemGPT, Zep/Graphiti, LangMem, A-MEM, MemoryBank, Generative Agents), rule/constraint mining, span taggers.
    Reusable: datasets we could fit on (license, no evaluation-benchmark contamination), pretrained small taggers,
    label schemas.
P2. RELATIONS/REGISTER: tracking rule updates (supersedes/cancels/completes/reinstates) with version history — prior
    art in dialogue state tracking, belief-state updates, memory update/conflict resolution in agent memory
    frameworks, "instruction drift"/"context rot" mitigation, constitutional/system-prompt versioning, tool-use
    obligation tracking. Reusable: schemas, classifiers, benchmarks that are NOT our evaluation data.
P3. RENDERING CADENCE: our finding that re-rendering live rules in every request beats one-time statement; prior art
    on "instruction reinforcement", periodic re-injection, sliding system prompts, Anthropic/OpenAI agent-harness
    practices (Claude Code, Codex CLI, Cursor, Aider, OpenHands, SWE-agent), context engineering papers. Reusable:
    proven cadence/placement recipes.
P4. SKILL SELECTION IN THE WEIGHTS on an MoE: our router-logit bias (alpha 3, all layers) flips Python->JS on a weak
    prior but not on a strong one (40g); masking old outputs releases it. Prior art: SteerMoE, expert steering/
    routing intervention, expert pruning/"expert specialization" maps for Qwen3-30B-A3B / DeepSeek / Mixtral,
    router-bias load-balancing tricks, "MoE as skill library" papers, activation steering with MoE, task vectors/
    function vectors on MoE, LoRA-on-experts, "expert-level" adapters (reusable code? profiles?).
P5. ATTENTION MASKING AS RELEASE: position-preserving eviction of stale spans (our Z schedule); prior art: KV
    eviction/selective attention (H2O, SnapKV, StreamingLLM, selective context, "attention sinks"), "forgetting" via
    masks, context pruning agents, serving-engine support for per-request custom 4D masks and prefix caching with
    masks (vLLM, SGLang, TGI, transformers Cache classes). Reusable: implementations of persistent key masks with
    prefix caching.
P6. LARGER TEST: benchmarks of long-horizon instruction retention in agentic coding WITHOUT reusing our sealed data
    (MultiChallenge, LongMemEval, InstructionFollowing over dialog, IFEval-derivatives are OFF LIMITS as fit data but
    can be named as evaluation candidates), agent-harness evaluation frameworks we could run cheaply on one GPU.
P7. Anything else: neuroscience-inspired focus/gating in transformers (Miller's "waves" — bursts, beta/gamma gating,
    working-memory control), "cognitive control" layers, meta-controllers, learned routers over prompts, dynamic
    system prompts, HF custom-code repos shipping a runtime controller inside generate() (precedent for our ship form).

Output: results/reuse-research-<you>.md, structured per P1..P7: for each, (a) 3-8 most relevant items with links,
one-line what-it-does, license, maturity; (b) REUSE VERDICT: "drop-in", "adapt (<= 1 day)", "idea only", or
"nothing reusable"; (c) the concrete reuse step for anything drop-in/adapt; (d) risks (contamination with our
evaluation data, license, GPU cost). End with a ranked TOP-5 "do this next" list and a TOP-3 "things Brian may not be
thinking of". Prefer primary sources; cite real URLs you actually opened; mark anything unverified. No repo edits
except your report; CPU only; no model launches; never read anything under data/bench.
