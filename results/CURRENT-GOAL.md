# The current goal — 2026-09-07

## Brian's subsequent correction — automation is a benefit

Brian clarified: “i don't know that the register must determine a huge advantage over prose - if the register can be fully automated over manual prose, that is a huge win/benefit”.

This supersedes the requirement below to outperform ideal manually maintained prose and the immediate priority of the factorial. The target is automated selection, maintenance, switching and clearing of the right obligations, with useful executable performance and an acceptable measured quality/cost tradeoff. Matching good manual reminders can be valuable when the register maintains them automatically. Measure update accuracy, end-to-end task outcomes, latency/tokens and actual human interventions; do not infer equivalence from a nonsignificant small-sample contrast. A larger untouched, preregistered validation and independent accuracy review remain required before claiming adequate proof. The factorial remains an optional protocol diagnostic. Current preparation is recorded in [the correction and next test](factorial-prep/USER-CORRECTION.md).

The text below records the prior framing; its manual-prose superiority requirement is historical, not the current acceptance criterion.

## Brian's standing instruction (unchanged, governs everything)
"continue finding a generalized way to implement a miller inspired focus mechanism. use fable, sol, and kimi sub
agents to review your work for accuracy. do not over engineer. make sure you can iterate quickly to prove out a
hypothesis, and only continue after you have adequate proof on a larger implementation. if you get stuck, do not
stop, spin up fable, sol, and kimi sub agents to do deep web research to get you unstuck."

## What the evidence has done to that goal
The weight-side reading of "focus" is closed. Steering experts, neurons, activations and cached state either did
nothing or bought surface compliance while reducing task success (router bias took hidden-test success from 16/32
to 7/32). The context-side reading works: restating the currently effective obligations at request time changes
behaviour decisively. But the two frozen 64-episode runs leave the central question unanswered, because a
hand-written prose restatement matches or beats the structured register on every obligation family and beats it on
producing correct code.

## The current goal, stated as the falsifiable question the next work must answer
**Does a maintained, versioned register of live obligations contribute anything over simply restating the correct
current rules in prose at request time — and can either be done without costing task competence?**

Three sub-questions, in priority order:
1. REPRESENTATION. Isolate register versus prose with everything else held identical. If the register adds nothing,
   say so plainly and the shipped artifact becomes the renderer plus whatever maintains it, not the data structure.
2. COMPETENCE. Both restatement methods currently cost semantic correctness relative to doing nothing on some
   measures, and the register costs more than prose (45 vs 52, p = 0.0078). A focus mechanism that degrades the work
   is not useful. Find whether the cost is intrinsic or an artifact of the task protocol.
3. AUTONOMY. Rules are entered explicitly today. Automatic admission from natural conversation failed three times.
   Without it the mechanism needs a harness that emits structured rule events, which is realistic for an agent
   framework and not for raw chat.

## What would count as done
A pre-registered run on a fresh, unexposed bank showing that the mechanism improves executable task outcomes over
BOTH ordinary retained history AND correct prose restatement, at matched cost, without a significant competence
regression, with the episode as the unit and an independent maximum-reasoning review confirming it.

## The immediate next step, specified and NOT authorized
One fresh 32-episode paired factorial, 16 rounds, crossing whole-file against scoped submission with the
plain-history, register and composed-prose arms. 3,072 calls, about 5.32 GPU-hours. Primary is per-episode paired
private-test integration plus adherence. It separates the protocol effect from the mechanism effect, which the
passing run confounds. See results/NEXT-TESTS-PLAN.md for the other open problems and their costed tests.
