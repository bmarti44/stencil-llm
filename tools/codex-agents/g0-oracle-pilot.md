# Brief: g0-oracle-pilot — label-free counterfactual salience oracle, 30-dialogue sanity check per corpus

## Objective
Registered text: LEDGER-PLAN.md "GENERALIZING SELECTION — G0 PILOT" (read it first; it governs). Design rationale:
results/research-generalizing-synthesis.md. Build scripts/g0_oracle.py + src/stencil/g0.py (shared helpers) that, for
a dialogue with a reference continuation, measures the utility of each candidate span as the teacher-forced NLL
increase on later reference tokens when ONLY that span's KV columns are evicted (QwenFocusCache.evict, see
scripts/ledger_kv_probe.py:367-390 for the eviction/pin plumbing and src/stencil/qwen_cache.py). Never delete text
to simulate eviction.

Corpora — HARD RULE (Brian, 2026-09-02): Multi-IF and BFCL are EVALUATION-ONLY gate benchmarks. Do NOT read them
here, not even non-cohort cases, and never read anything under data/bench/. Pilot corpora are DISJOINT public sets,
fetched once with `huggingface_hub` (HF_TOKEN is in the env for auth ONLY — never print or log it), store ONLY the drawn
subset (≤ 200 dialogues per corpus, jsonl) under data/g0/ with the upstream dataset revision, sha256 of the subset,
the draw procedure, and the license recorded in data/g0/MANIFEST.json (the raw downloads stay in the HF cache; do
not commit them; `rank_bm25` is not installed — write the 40-line BM25); 30 dialogues each, deterministic first-N after a
seed-20260903 shuffle (ids listed in the output meta):
- chat: OpenAssistant/oasst2 — English multi-turn branches with ≥3 assistant turns. Reference continuation for the
  last assistant turn = the BASE MODEL'S OWN greedy response to the full context (generate once, max_new 256, store
  it; self-distillation, label-free). Context = chat-templated prior turns.
- tool: Salesforce/APIGen-MT-5k (fallback: Team-ACE/ToolACE) — multi-turn function-calling dialogues with gold
  assistant tool calls and tool outputs. Reference for the last assistant turn = its gold tool call(s) rendered in the
  Qwen3 <tool_call> JSON format (document the renderer); the tools schema goes in the system turn as the BFCL harness
  does (read scripts/bfcl_mt.py for the template only — not its data). Cap context at 16k tokens; prefer dialogues
  with ≥3 prior assistant turns and real tool-role outputs.

Candidate spans: role-tagged (system/schema, user, assistant, tool), sentence-bounded within a message, merged to
64–128 tokens; ≤12 per dialogue stratified by role (round-robin over roles, seeded). Also 12 position-matched NULL
spans: random spans with the same role, length bucket, and age bucket (distance from the current turn) as each
candidate. Record token column ranges for every span.

Measurement per dialogue: one full prefill → NLL_full over reference tokens (teacher-forced, mean per token). For each
candidate and null span: restore the cache, evict exactly its columns, teacher-force the same reference → NLL_evicted.
utility = NLL_evicted − NLL_full (signed; keep). Also record: top-1 agreement rate of the evicted run vs full on
reference tokens; for bfcl whether the argmax-decoded call string still parses/matches (report, not gate).
Joint check: for the top-3 utility spans, evict all three jointly and record the joint delta vs the sum.

Zero-training policies, scored on the same dialogues at a fixed budget B = total tokens of the top-25% candidates:
(a) role rule: protect system+schema, keep all prior user spans (truncate to B by recency);
(b) recent+sinks: first 4 columns + most recent B tokens;
(c) archive retrieval: BM25 (rank_bm25 or a 40-line implementation) over ALL candidate spans with the current user
    turn as the query, top spans to budget B;
(d) salience2 linguistic finder (the SHIPPED src/stencil/salience2_weights.json, refit 2026-09-02 on b3 synthetic data only — commit e19f67f) on user/system spans
    — disclose that lineage;
(e) attention mass: mean attention received by each span's columns from the current-turn query tokens (use the
    trunk's attn_probe / attention output; document which layers/heads are averaged), top spans to B.
Recovery(policy) = sum of positive utilities of spans the policy retains / sum of positive utilities of all candidates
(and the same with the null spans' utilities subtracted as a baseline). Report per corpus, per role.

Outputs (results/qwen/g0-pilot/): per-dialogue JSON records written atomically from the first dialogue (fields: corpus,
id, turn, n_context_tokens, spans[{role,start,end,n_tok,text_sha,utility,top1_agree}], nulls[...], joint{...},
policies{name:{kept_span_idx, recovery, recovery_null_adj}}, seconds); meta.json (commit, model sha, corpus shas,
seed, ids); summary.json (utility distribution per corpus/role vs null: mean, median, p90, fraction > null p90;
policy recovery table; per-dialogue seconds mean/max). Resumable; never delete records.

## Allowlist
See g0-oracle-pilot.allow.

## Tests first (TDD, rule 1)
CPU tests (no model): span candidate construction is deterministic, role-stratified, ≤12, within message bounds, and
null spans match role/length/age buckets; recovery arithmetic on synthetic utilities; BM25 ranking on a toy; a guard
test that scripts/g0_oracle.py and src/stencil/g0.py never reference data/bench (string scan) and refuse any input path
under data/bench; record schema has every registered field (dry-assert on a stub record). RED first. Run ONLY your new
test file(s). DO NOT run the full suite.

## GPU policy
Use the GPU only when `nvidia-smi --query-compute-apps=pid --format=csv,noheader` is empty; if a job is present,
re-check later — never wait on a lock, never signal any process. Foreground only. Run the pilot on the 1.7B trunk
(`models/qwen3-1.7b.pt`). First run 2 dialogues per corpus and report seconds/dialogue BEFORE launching all 30+30;
if projected total > 4 GPU-h, stop after the 2+2 and report the timing instead.

## Acceptance
Tests green; ruff clean; 2+2 timing reported; 30+30 records + summary.json produced if within budget; commit
(`git add -f` the results) before finishing.

## Ledger handoff
Append to WORKLOG.md: timing, the utility-vs-null distribution, the policy recovery table, anomalies (e.g. spans with
large NEGATIVE utility), and every place the spec was ambiguous and what you chose.
