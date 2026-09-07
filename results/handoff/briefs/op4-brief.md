# Open problem 4 for gpt-6-astra: A TRAINED SELF-MANAGING MODEL — co-emitted register ops + self-alignment rating (2026-09-07)

Brian's proposal, verbatim in intent: "much like we have models think/reason, could we also create something like a
LoRA fine tune to have the model evaluate how aligned its own response is to the current task it has been given, and
it manages the register of tasks in each response? is that possible, or could it work? is there any research that can
point in this direction?"
Treat this as TWO separable hypotheses and evaluate each on its own evidence:
  H-A (co-emitted register management): with each response the model also emits the structured register operations
      (add / supersedes / cancels / completes / reinstates with key, scope, kind, literal value, target version).
      One generation instead of two, with full context. Archetype prior art: MemGPT / Letta (a model managing its own
      memory through structured calls), Mem0, and the MemReader-style fitted 4B updater named in
      results/updater-research-fable.md. Our own check 46 is the frozen-model, separate-call version of this.
  H-B (self-alignment rating): the model rates how well its own response satisfies the currently live obligations.
      Counterweights to research honestly: Kadavath et al. on models "mostly knowing what they know" (internal signal
      is real) versus Huang et al. ICLR 2024 on LLMs not self-correcting reasoning without an external signal, plus
      the calibration literature on verbalized confidence. The recurring pattern is that the signal lives in the
      hidden state rather than in the model's spoken self-assessment; say whether the literature supports a TRAINED
      verbalized rating closing that gap.
IN-REPO VERIFICATION FIRST (file:line and real numbers; use results/full-program-review-astra.md as the corrected
claim ledger, not the original files): check 46 (trunk as updater, six-shot in-context: ~79% recall / ~90% precision,
relations 89%, supersedes 87%, 58/96 false-admission turns, 0/21 task-over-global); checks 44/44b/44c (admission
recall failures and their named miss families); check 48 (fitted 4B updater LoRA, COST-INELIGIBLE, never fitted, and
its registered recipe); check 49 and its Opus review (two LoRAs as a focus carrier: SET causally clean 12/12 vs 0/12,
cold-HOLD 10/12, SWITCH endpoint inadmissible, adapter-OFF parity exact, carrier undertrained at 2.3% of its ceiling);
check 45 (off-task probe, INSUFFICIENT DATA); and the LOCK phenomenon across pilots 3-7 (0 of 96 locked rounds
recovered in pilot 5; all four pilot-7 residuals were consecutive rounds of one episode) as the sharpest available
evidence about whether a model notices it is off task — note that the model was never ASKED and its feedback was an
opaque token, so treat it as suggestive, not decisive.
THE OBJECTION TO ADDRESS HEAD ON: the register is an AUTHORITY BOUNDARY. Its design forbids the model's own prose
from creating or retiring a rule. Co-emitted operations hand the model authority over its own constraints, whose
obvious failure is rationalisation (updating a rule to match what it just did). Research what is known about
self-serving or drifting self-edits in agent memory systems, and specify the safe shape: proposal plus deterministic
typed validation of authority, scope and exact target version, with the model's operations never committing directly.
Also cover: whether a single LoRA can carry both the answer and the side-channel without degrading the answer (our
check 40k found an internal intervention degrading task competence, and check 49 found adapter-off parity exact);
training-data construction for co-emission from our audited corpora plus the thousands of saved labelled rounds in
results/quick-checks/composition-pilot-{5,6,7}; and whether "thinking" modes or structured side channels are the
better carrier than a fine-tune.
Deliver TOP 3 ranked approaches with, for each, a QUICK TEST at <= 1 GPU-hour with a pre-written GO/NO-GO reading,
the exact unexposed evaluation bank to use (held-out sets 1-3 are EXPOSED; held-out-4 had its annotation conventions
used in a training repair; say what is clean), the data-lineage line, and what a null closes. Prefer tests that reuse
saved records and existing harnesses. End with a plain-language verdict for Brian on whether his proposal can work,
which half is the better bet, and the single cheapest experiment that would move it most.
Write results/open-problem-4-self-managing-astra.md.
PROTECTED: the registered 64-episode larger test is RUNNING on the GPU. CPU and web only. Do not touch the GPU, any
RUNNING.flag, any container, anything under results/larger-test/, or any code. Never signal any process. Never read
anything under data/bench, and do not read evaluation-bank episode CONTENT. Open what you cite; mark anything
unverified; "nothing reusable" is a valid answer. Write ONLY that one report file and commit it with an explicit
pathspec (git add -f); no push.
