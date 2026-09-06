# Check40l — R4

DEV **15 pass / 9 fail**: ARM B eligible. Same 32 evaluation tasks as 40k, disclosed second look; unchanged text-only rule, greedy, cap768, scorer and hidden tests. Baseline reused after byte/runtime checks; all eight original DEV replies also reproduced token-for-token.

| Arm | Pass / 32 | Exact 95% pass-rate CI | Broken | Truncated |
|---|---:|---:|---:|---:|
| Text-only (reused 40k) | 16 | [31.89, 68.11]% | 0 | 0 |
| Competence 1/3 | 14 | [26.36, 62.34]% | 0 | 0 |
| Competence 2/3 | 13 | [23.70, 59.36]% | 1 | 0 |
| Shuffled competence 2/3 | 15 | [29.09, 65.26]% | 2 | 0 |

| Contrast vs text-only | Wins / losses / ties | Difference (pp) | Conservative paired 95% CI (pp) | Exact p benefit / two-sided |
|---|---:|---:|---:|---:|
| Competence 1/3 | 1 / 3 / 28 | -6.250 | [-27.342, +16.825] | 0.9375 / 0.625 |
| Competence 2/3 | 3 / 6 / 23 | -9.375 | [-37.421, +21.207] | 0.91015625 / 0.5078125 |
| Shuffled competence 2/3 | 1 / 2 / 29 | -3.125 | [-23.031, +17.814] | 0.875 / 1 |

**R4 — INCONCLUSIVE.** Neither competence dose meets R1. R3 also fails: the smaller dose loses net two tasks, below the prewritten net-loss threshold of three (inherited from 40k); the larger dose loses net three. Both point estimates are negative, but this screen establishes neither benefit nor statistical harm. Keep the line parked; no enlargement or shipping change.

**R2 is unreachable:** ARM A was cut per fable’s 40k review. No low-dose JS run was made. Failure to meet R1 does not prove that an oracle-known correct bias cannot help: this dev pass-minus-fail profile is an observational association, potentially confounded by task difficulty and output style. No evaluation outcomes selected the direction, doses or tasks. Two unadjusted competence comparisons make this exploratory.

One model load; total GPU reservation **1345.206/2700 s (22.420 min)** including load and cleanup. 24 DEV +96 evaluation generations. RUNNING.flag removed; no process signals or push.

Recipe `aa1fa772929fee08e61b26f7e59931a54f4ac799`; profile freeze `74086c4383aa5810632263b2a35471918b773fbd` before evaluation. Fit-on: 24 DEV replies only (8 prior DEV +16 freshly authored); evaluated-on: the same 32 check40k tasks, second look disclosed. No DEV revisions, resampling or evaluation-informed tuning.

All paired losses are valid, unbroken JavaScript. The one larger-dose and two shuffled breakage flags are the inherited repetition heuristic; none is truncated. Independent SciPy binomial tests and beta-quantile CIs reproduce the reported statistics.

All 120 new records and 32 reused baseline records rescored; token IDs/prompts, hidden-test scores, per-token profiles, tensor reconstruction, norm matching, freeze hashes and summary audited. Audit command: `./.venv/bin/python scripts/focus_check40l.py audit`. Exact sign tests use discordant pairs; the conservative Bonferroni CP difference interval is not an equivalence test and is not dual to the sign test.

Stored float32 tensor Frobenius norms: 5.219855442, 10.439710884, shuffled 10.439710884; target alpha3 norm 15.659566344. Each layer also matches its target fraction within float32 rounding. The inherited inference harness casts bias to bf16; reported norm targets refer to stored tensors.

Binary artifacts: `profiles/*.pt` store each DEV record ID, task ID, generated non-EOS token IDs, own teacher-forced positions and raw bf16 router logits [48, token_count, 128]. `competence-profile.pt` stores float64 reply means [24,48,128], pass labels, centred pass-minus-fail direction [48,128], three float32 biases [48,128], and int64 per-layer expert permutations [48,128]. These are measurements/profile statistics only; no trunk weights were fitted. `freeze.json` binds the profile; `artifacts.json` hashes final local artifacts. Full preregistration follows.

---

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
