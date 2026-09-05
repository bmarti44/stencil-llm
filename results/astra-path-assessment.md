**Brian: no, we are not currently on the best path. Confidence: high, about 90%.**

The target is right. An agent should preserve your goal, binding instructions, exact facts and unfinished work,
use them when relevant, and stop following instructions you have replaced or cancelled.
Remembering a sentence is only part of that: focus also means choosing the right next action and checking that it worked.

Pin+echo—keeping selected internal memory and restating its text—produced a real, useful retention result.
But 59.2% compliance versus 16.7% after deletion and 65.2% with full history came from short conversations,
and the registered failure limit was breached. The simple role/recency rule beat classifier pinning.
We have not established that internal pins add value beyond a good text-memory system, or that either improves long coding sessions. [Program review](astra-program-review.md)

SC1 fixes a legitimate question: does the frozen learned importance filter earn its cost against an independent recency rule?
Its fair budgets and final-task checks are improvements. But it still asks for one final answer after a scripted history,
with scope handling and summaries switched off. It cannot establish sustained coding through repeated history-shortening or recovery from its own mistakes.
My Stage 2 review rejected consequential filler/position shortcuts; fable accepts a narrower reading of the same measurements.
A repair is now underway. Fixing that validity problem does not fix the distance from Brian's target. [Astra review](sc1-stage2-review-astra.md), [fable review](sc1-stage2-review-fable.md)
I recommended SC1 and underestimated its implementation cost. The program is drifting into evaluation machinery; I would demote SC1.

The scope register—what applies to which task, what changed, what is finished—is central to focus.
The digest test—a short summary with original-text fallback—is directly relevant to repeated compaction, but remains unproven.
BFCL/4B is a bounded check that the model can use tools; weak basic ability can conceal memory benefits.
Finish only the existing authorized preflight/fallback decision, honoring its stop rule. Make further BFCL work secondary. [Blocker research](astra-research-blockers.md)

Production practice supports a more direct route. Codex supports persistent project instructions and local memory files;
OpenAI also provides compaction: shortening conversation history to fit the model's working space. These capabilities do not guarantee retention. [Codex memory](https://learn.chatgpt.com/docs/customization/memories), [compaction](https://developers.openai.com/api/docs/guides/compaction)
Claude Code keeps project rules and automatic notes, reloads root rules after compaction, and retrieves detailed notes as needed.
Its documentation explicitly says these instructions are not guaranteed to be followed. [Claude Code memory](https://code.claude.com/docs/en/memory)
Anthropic's 2025–2026 coding work combines progress records, bounded work units and executable checks.
Its newer model let it remove an earlier context-reset mechanism: scaffolding must earn its place as models improve. [2025 experiments](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents), [2026 follow-up](https://www.anthropic.com/engineering/harness-design-long-running-apps)

There is positive evidence: Cursor reports that training Composer to summarize its own work halved compaction-related errors
while using one-fifth as many summary tokens on its internal coding evaluation. That supports testing memory through completed coding work;
it does not show our frozen 4B can obtain the same benefit from an added summarizer. [Cursor, March 2026](https://cursor.com/blog/self-summarization)
There is counterevidence too: an independent 2026 study found repository instruction files did not generally improve task success,
while increasing cost by over 20% on average. Better instruction adherence and better task completion are different outcomes. [Study, revised June 2026](https://arxiv.org/abs/2602.11988v2)

Starting today, I would take these three steps:

1. **Establish the actual failure.** Build 16 development coding sessions in small real repositories, with working tests,
   changing user instructions, exact identifiers and at least two compactions. Let agents execute their own edits and tool calls.
   Reuse repository tests and a small driver; do not build another scenario language or evaluation framework.
   Compare ordinary compaction with a diagnostic version given the relevant original instructions at each continuation.
   Classify failures as lost information, wrong retrieval, stale instructions, ignored visible instructions, or basic coding inability.
   Use the existing coding agents for a reality check; use the single GPU for local 4B trials only where it can do the underlying work.

2. **Build one small working memory loop.** Keep the original history, a concise current-task note, and source-backed active rules/facts.
   Update cancellations and corrections before selecting reminders; retain exact identifiers verbatim and retrieve originals on demand.
   Start with simple retrieval and text reminders. Check mechanically enforceable restrictions in tools.
   Keep the digest as one bounded accuracy/cost experiment; count writing, reading and fallback costs together. A smaller summary alone is not a saving.

3. **Test the complete loop on 32 new coding sessions**, frozen before outcomes, against the same agent's normal compaction and project rules.
   Give both versions the same time and context limits. Score finished working code, instruction violations throughout the run,
   stale actions, repeated work, interventions and total cost. Use separate task-authoring and checking agents.
   This is a new feasibility study, not a smaller SC1 or proof of a small gain. Fund larger confirmation only if it warrants it.
   Then test one component at a time: learned selection, internal pins, or digest. Each must improve the working baseline.

Cut wave revival, classifier retraining, switching benchmarks to find a win, and requiring SC1 or BFCL to pass before testing actual coding memory.
Stop growing the general evaluation framework; retain independent checks, clean evaluation data, recorded outputs and honest stop rules.
Do not waive SC1's validity defect: defer it, or complete a narrowly bounded repair and keep its claim narrow.
