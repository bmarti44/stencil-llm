# Check 50 for gpt-6-astra (GPU <= 60 min, Qwen3-4B dense proxy): SKILL ADAPTERS per language — does a baked skill improve performance, and does selection/switch/clear work? (2026-09-06)

Brian: "I like the rule-baked-in-adapter idea, maybe per programming language or some other skill, and we can
measure that it improves performance for that skill." Read results/quick-checks/check49/README.md first (rule
baking; if 49 read NO-GO on HOLD, still run this: skill adapters are a different object) and both dense-focus
research memos. Design (all data authored/self-generated; NEVER any coding benchmark; data-lineage line first):
1. TASK BANKS (CPU, author yourself with hidden node/python tests, as in checks 40k/40l): a TRAIN pool of 160
   small programming tasks per language for JavaScript and Python (varied: strings, arrays/lists, objects/dicts,
   parsing, formatting, small algorithms), and a fresh EVAL bank of 32 tasks per language, disjoint by construction
   (different task ids/specs; assert no shared spec text). Keep the 40k 32-task JS bank as an extra eval (disclosed
   third look).
2. SELF-DISTILLATION WITH VERIFICATION: with the rendered rule "Live rules: (1) Write all code in <L>." the base
   Qwen3-4B generates solutions for the TRAIN pool (greedy + 3 temperature samples); keep only solutions passing
   their hidden tests; that verified set (prompt WITHOUT the rule line -> solution) is the adapter's training data.
   Report the yield per language.
3. ADAPTERS: LoRA rank 16 (attention+MLP), one epoch per language (JS adapter, Python adapter), PEFT, bf16; a
   few minutes each. Parity check: adapter OFF reproduces base token-for-token on 16 prompts (zero diffs).
4. EVAL on the 32 fresh tasks per language (paired by task), greedy, hidden tests:
   arms = text-only rule | adapter-on, no text | adapter-on + text | WRONG adapter + text (interference) | OFF (no
   rule, no adapter). Then SWITCH/CLEAR: a 12-round session per language pair alternating JS/Python tasks where
   the controller swaps adapters (no text) — count correct-language executable solutions per round; CLEAR =
   adapter off -> default language.
5. PRE-WRITTEN READINGS: SKILL-GAIN = adapter-on+text beats text-only on paired hidden tests with wins - losses >=
   5/32 and exact sign-test p <= .05 for at least one language, with breakage not higher; SELECT = adapter-on-no-
   text >= 26/32 correct-language executable; SWITCH/CLEAR = >= 10/12 correct-language rounds and CLEAR default
   >= 13/16. GO = SKILL-GAIN and SELECT and SWITCH/CLEAR -> the skill-library-as-focus line opens (register the
   27B follow-up, with astra's/fable's caveats on hybrid attention). PARTIAL = SELECT+SWITCH pass but no
   SKILL-GAIN -> adapters are a text-free carrier without a competence benefit (say so plainly; ship value =
   token savings only). NO-GO otherwise -> weight-side closed for dense.
Budget: <= 60 GPU-min hard (10 distillation + 10 fits + 30 eval + 10 overhead); RUNNING.flag under results/quick-
checks/check50/; never signal. Outputs (README with readings, banks, verified training sets, records <= 10 MB,
adapters under data/classifier/model/skill-lora-4b/ out of git with hashes); item 50 in results/quick-checks/
README.md; WORKLOG (<= 6 lines). Commit with explicit pathspecs; no push; never read anything under data/bench.

AMENDMENT: reuse check 49's two adapters and task-authoring harness where possible (same tokenizer-bounded task
style); the SKILL-GAIN arms (adapter+text vs text-only on fresh hidden-test banks, wrong-adapter interference) are
the new content here; SELECT/SWITCH/CLEAR are already covered by 49's contract — reference its numbers rather
than re-running them unless 49 was INCOMPLETE. Self-distillation with verification remains the TRAINING-DATA
method for the larger skill sets (report yield); astra's CPU-authored 128/mode sets are the minimum.
