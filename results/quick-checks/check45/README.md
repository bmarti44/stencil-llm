# Check 45 — R4: INSUFFICIENT DATA (2026-09-06)

The [pilot README](../composition-pilot/README.md) declares **INELIGIBLE /
INCOMPLETE**. The requested eligibility gate therefore stops this check before
labels, hidden states, or any model are loaded. No probe was fitted.

The source additionally reports 128 calls (64 sequential and 64 batch diagnostic)
from DEV-00 alone, versus the required >=150 labelled rounds and eight DEV
episodes for leave-episodes-out CV. Even counting every reported call would be
insufficient. These are source-reported counts, not a new record/label audit.
The >=25 live-rule-violation requirement was not assessed: rejected envelopes
and breakage are not interchangeable with those labels. The pilot warns that
early checker exits make zero style/process flags inconclusive.

Prewritten readings: R1 requires best-layer AUROC >=.85, episode-bootstrap CI
lower bound >=.75, and >=.10 AUROC over similarity; R2 is .70–.85 diagnostic
signal; R3 is <.70; R4 is insufficient data. **Only R4 applies.** No claim about
presence or absence of pre-generation signal follows. No meter is registered.

AUROC, per-kind/stale-execution results, bootstrap CIs, calibration/Brier,
<=20% intervention precision/recall, similarity and prior baselines are all
**not run**, not zero. No follow-up fitting or intervention policy was run.

Planned lineage: fit-on = DEV pilot rounds only; evaluated-on = held-out DEV
episodes by fold; no benchmark data or evaluation-bank episodes. Actual lineage:
pilot README only; fit-on/evaluated-on = none.

Reproduce with `python3 scripts/focus_check45.py` (stdlib, CPU only).
[manifest.json](manifest.json) binds the source README and gate script by SHA256.
[per-fold.jsonl](per-fold.jsonl) is empty because zero folds ran. No probe-weight
`.npz` exists; the manifest's weight list is empty, so there are no weight hashes.
No GPU, model load, benchmark/evaluation content reads, process signals or push.
