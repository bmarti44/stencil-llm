# POST-REBOOT NOTE (2026-09-05, power outage at ~18:27; machine up since 18:27)
The previous codex sessions died mid-task; the scratchpad was wiped. Artifacts committed in git are the only state.
GPU: a llama-server owned by Brian (pid 2705, Qwen3.8-27B Q4, ~16 GB) now runs permanently on the GPU. It is NOT a
Stencil job: treat the GPU as available for Stencil when no OTHER compute process (a .venv python) is present; never
touch pid 2705. Memory budget: 128 GB total minus the llama-server; Qwen3-30B-A3B bf16 (~61 GB) still fits. Coordinate
with other Stencil GPU checks via results/quick-checks/<check>/RUNNING.flag files (write yours while running, delete
after; wait if another Stencil flag exists). Never signal any process. All committed prior results stand; re-read the
relevant README/records rather than redoing completed work. Commit with explicit pathspecs; no push.
# Check 44 for gpt-6-astra: ADMISSION redesign test — frozen-LLM message-level extraction vs trained message detector (2026-09-06)

Source: results/admission-research-astra.md (your recommendation: one frozen Qwen3-1.7B message-level,
evidence-preserving structured extraction experiment with a GO bar; cut unattended admission from the first ship if it
fails). Implement YOUR OWN design from that memo (sections on the extractor schema, few-shot, decoding, evidence
spans, DEV timing, family-level FPR bounds, GO bar, stop rule) as check 44, with these orchestrator additions:
- EVALUATION BANK = data/classifier/heldout/fable-admission-heldout.jsonl (338 author-disjoint message items; untouched;
  one look only) — DEV/few-shot examples must come from elsewhere (write 24 dev/timing messages yourself, or use
  data/classifier/relations/kimi-admission.jsonl once it exists — it is being generated now; never fable's file).
- ARMS: (A) frozen Qwen3-1.7B (hf_compatible; thinking off; constrained JSON output with verbatim evidence spans;
  greedy; few-shot from your dev messages) extracting standing rules {text, key, scope}; (B) the v8 sentence
  admission head ft-v3 run message-wise (baseline); (C) OPTIONAL if data/classifier/relations/kimi-admission.jsonl has
  >= 1,500 rows by the time you reach this step: a message-level bge-small detector trained on it (span-level
  standing-rule tagging or sentence-pair scoring; thresholds on its own DEV) — else skip C and say so.
- METRICS on the held-out: per message, standing-rule detection precision/recall (span-exact and span-overlap),
  false admissions on one-off-with-payload items, on quoted/reported items, on tool/assistant roles; key/scope
  agreement; latency per message. GO bar (write before running): A or C reaches span-overlap recall >= 0.85 with
  false-admission rate <= 3% on payload items and <= 3% on quoted items and 0 on non-user roles; else NO-GO -> cut
  unattended admission from the first ship (explicit structured rule entry), as your memo says.
Cap 1.5 GPU-h. GPU: the diagnostic gate may hold it (results/quick-checks/focus3-gate/diag/RUNNING.flag) — wait; write
results/quick-checks/check44/RUNNING.flag; never signal. Outputs under results/quick-checks/check44/ (README with
pre-written reading, summary.json, per-message records with the extractor's raw JSON); item 44 in
results/quick-checks/README.md (5 lines); WORKLOG entry (<= 6 lines). Commit scripts/focus_check44.py + results (git
add -f) + README/WORKLOG with explicit pathspecs; no push. Foreground only; never terminate or signal any process;
never read the sealed IFEval input file or anything under data/bench; no fitting except arm C's own small fit.

ORCHESTRATOR NOTE: this is the QUICK version under Brian's quick-test-first rule (fable's 338-item held-out; the GO
bar above). Your memo's full 800-message two-author protocol with the zero-unsupported-writes bar is the DEEPER
verification, to be run only if this quick check is promising. Do not author the 800-message bank now.
