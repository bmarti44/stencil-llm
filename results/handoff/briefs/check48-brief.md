# Check 48 for gpt-6-astra (GPU <= 60 min): Qwen3-4B generative REGISTER-UPDATER LoRA screen (2026-09-06)

Both research memos (results/updater-research-{astra,fable}.md) rank this second after check 46 (read check 46's
result first: if it read GO, run this only as a cost/latency comparison; if PARTIAL/NO-GO, this is the main bet).
Follow astra's Section 8 item 2 exactly (it is the registered recipe): BEFORE GPU settle the task contract and
conventions (span convention = fable held-out-3/4: framing cue excluded), compile a fixed 2,048 complete development
transitions (register state + message -> ops list JSON) converted from the audited corpora: kimi-admission (+opus
patch), kimi-admission-2 (+astra patch), kimi-admission-3 (audit it yourself first: patch file, same format),
kimi-relations/transitions/overrides (+patches), kimi-transitions-3 (audit first), opus/astra enrich sets; balanced
across add/none/updates and the miss families; max length 768; selection by a predeclared scenario rule; DEV held
out by scenario. One seed; Qwen3-4B (models/qwen3-4b-hf) BF16 LoRA attention+MLP rank 16 / alpha 32, LR 1e-4, one
epoch (PEFT; HF Trainer or a minimal loop; no vLLM needed for the fit); serve for evaluation with HF generate
(greedy, thinking off, strict ops schema, normalised verbatim span matching as in check 46).
SCREENING BANK: fable's fresh held-out-4 pair (data/classifier/heldout/fable-admission-heldout-4.jsonl and
fable-relations-heldout-4.jsonl — poll for the committed files; never fit on them) — this is the ONE look; plus the
v8 SETUP bank (96 turns; development diagnostic). Data lineage line first (fit-on = audited kimi/opus/astra corpora;
evaluated-on = held-out-4 once; no benchmark data).
Budget allocation (hard): 5 min load/smoke + 5 min throughput pilot + 25 min fit/save + 22 min evaluation incl.
SETUP + 3 min cleanup = 60 GPU-min; project completion from real throughput before the fixed run; INCOMPLETE /
COST-INELIGIBLE rather than a reduced sample. RUNNING.flag under results/quick-checks/check48/; never signal.
PRE-WRITTEN READINGS: SCREEN-GO = admission overlap recall >= 85% at precision >= 95%, payload/quoted FA <= 3% each,
non-user FA 0, relations accuracy >= 94% with supersedes recall >= 85%, SETUP <= 2/96 false turns with 36/36 admits,
p95 latency <= 1 s per message on the GPU -> licenses a registered full-data fit + larger validation (not shipping).
PARTIAL = one half passes. NO-GO = quality bars missed (no automatic refit; report per-family errors). Report the
per-family table (cue-less, multi-rule list, rule+payload, withdraw+replace, bare value+temporal, task-scoped
override, "actually B") for both tasks.
Outputs under results/quick-checks/check48/ (README with readings, conversion script, DEV records, held-out
records <= 10 MB, adapter under data/classifier/model/updater-4b-v1/ out of git with hashes in a manifest); item 48
in results/quick-checks/README.md; WORKLOG (<= 6 lines); dated section in results/relations-classifier-report.md.
Commit with explicit pathspecs; no push; never read anything under data/bench.

ADDED: Opus is auditing pass 3 (data/classifier/review/admission-3-opus-patch.jsonl, transitions-3-opus-patch.jsonl,
pass3-opus-audit.md). If those files exist when you start, apply them instead of auditing yourself; if not, wait up
to 30 minutes for them (poll), then audit yourself as originally specified and say which happened.
Opus audit is DONE (bafd6548): apply both patches; ALSO apply the rule-fixable systematics it recorded but did not
itemise: strip terminal punctuation from admission spans (186; fable's convention has none), recompute
transitions-3 target_span offsets mechanically from text (883 wrong ends), and treat whole-message spans as
non-replacement text (do not use them verbatim as the supersedes replacement value; derive the value field).
