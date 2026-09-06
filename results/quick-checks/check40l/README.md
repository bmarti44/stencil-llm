# Check40l — competence direction and dose response

Prewritten before inference. ARM A is cut per fable's check40k review; R2
is unreachable. ARM B only: 24 text-only DEV generations, then 96 generations
on the same 32 check40k evaluation tasks. Second look disclosed; no selection,
fitting, training, tuning or task changes from evaluation outcomes.
Data lineage: fit-on = 8 check40k DEV + 16 fresh authored DEV replies, profile
only; evaluated-on = check40k's 32 disjoint evaluation tasks, second look.
Hidden Node tests never enter prompts. Frozen references validate all DEV tests.

Same unchanged check40k scorer, check40j literal text-only rule line, generation
function, bf16 trunk, greedy/non-thinking, cap768, all48 layers/prefill+decode,
fresh sessions. Reuse committed 40k text-only records iff every frozen harness
file and runtime recipe matches; if bytes differ rerun baseline within cap.
Teacher-force each DEV's actual non-EOS generated tokens at their OWN positions
(prompt length through final generated position, not predecessor positions).
Save raw logits [48,tokens,128] per reply in the same run. Across-expert centre
in float64 at each token; mean tokens within each reply, then mean passing
replies minus mean failing replies (equal reply weight). This interprets the
requested mean over replies literally; 40b instead token-weighted its classes.
Require >=6 passing and >=6 failing replies, else INELIGIBLE B without evaluation.
No DEV revision/resampling. This association is a candidate competence direction,
not a known-correct oracle; difficulty, length and output style may confound it.
Norm-match EACH layer to 1/3 and 2/3 of the frozen 40k alpha3 tensor's layer norm;
thus also matching global norms. No layer selection; zero direction => ineligible.
Shuffle larger-dose expert entries independently per layer, seed401207. One
larger-dose shuffled control is used for both registered competence contrasts.
Freeze tensors and profile before evaluation. Rotate three-arm order by task index.

Prewritten readings, R1 first: any competence arm wins-losses>=5, losses<=2,
exact one-sided sign p<=.05, and shuffled does NOT meet that same improvement
criterion => R1: reopen actuator line as competence actuator, registered follow-up
required, not shipping. No multiplicity adjustment (exploratory two-dose screen).
R2 dose-only unreachable because ARM A cut. R3: both tested competence doses
have losses-wins>=3 (40k's descriptive harm bar), and neither qualifies R1 =>
CLOSED for this tested family: router-logit bias on this trunk does not improve
task competence beyond a rendered rule; magnitude harms. This is restricted to
these tested directions/doses/tasks, not all conceivable biases or a proven
monotonic dose law. Anything else R4 INCONCLUSIVE, record, no enlargement.
INELIGIBLE/INCOMPLETE supersede substantive readings. Breakage reported separately.
Paired exact one- and two-sided sign tests, wins/losses/ties, pass counts with
95% CP CIs; paired difference CI uses check40k's conservative Bonferroni CP bounds.
A non-significant effect is not evidence of equivalence or harmlessness.

One model load, cap2700 seconds including load/profiling/freezing/cleanup;
cooperative deadline, no signals. Coordinate RUNNING.flag and review lock;
Brian's pid2705 exempt. Explicit-path local commits, no push.
