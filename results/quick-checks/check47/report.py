"""Report the prespecified screen without treating missing model efficacy as zero."""
import hashlib,json
from pathlib import Path
OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[2]
def read(p):return json.loads(p.read_text())
def lines(p):return [json.loads(s) for s in p.read_text().splitlines()]
def main():
 d=read(OUT/'dev-summary.json');j=read(OUT/'js-summary.json');life=read(OUT/'lifecycle.json'); attempts=read(OUT/'attempts.json')
 baseline=read(ROOT/'results/quick-checks/composition-pilot-4/summary.json')
 b=[e for e in baseline['endpoints'] if e['arm']=='R' and e['episode'] in ('slab-dev-00','slab-dev-01')]
 assert len(b)==2
 http=lines(OUT/'http/records.jsonl');jh=[h for h in http if h['pass_name']=='check40k']
 jsagg=sum(len(h['output_token_ids']) for h in jh)/j['seconds']
 jsdecode=sum(h['decode_tokens'] for h in jh)/sum(h['decode_seconds'] for h in jh)
 max_tokens=max(s['output_tokens'] for s in d['per_episode'].values())
 startup=attempts[0]['ready_at']-life['start']
 projections=[]
 for rounds in (16,32):
  for concurrency,agg,label in [(2,d['aggregate_tok_s'],'observed DEV C2'),(4,jsagg,'observed JS C4 rate applied to DEV tokens; cross-workload proxy')]:
   tokens= 160*max_tokens*rounds/16
   serving=tokens/agg
   projections.append(dict(rounds=rounds,concurrency=concurrency,rate_basis=label,tokens=tokens,aggregate_tok_s=agg,fp8_hours=(startup+1.25*serving)/3600,bf16_estimate_hours=(startup+1.25*2*serving)/3600))
 jsrows=lines(OUT/'js-records.jsonl')
 result=dict(reading='STAY',loadable=True,model='Qwen3.8-27B local FP8',dev=d,js=dict(j,caps=sum(r['truncated'] for r in jsrows),aggregate_tok_s=jsagg,decode_tok_s=jsdecode,seconds_per_call=sum(h['wall_seconds'] for h in jh)/32),moe_matched_endpoints=b,projection_sensitivity=projections,startup_seconds=startup,gpu_seconds=life['gpu_held_seconds'],bf16_measured=False,full_workload_measured=False,reason='Executed rate 0/32 < matched MoE 32/32. Neither final success nor format/breakage improves. No switch regardless of projection sensitivity.')
 (OUT/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
 rows=['# Check 47 — STAY on Qwen3-30B-A3B','',
 '**The local dense FP8 checkpoint loads, but fails the prespecified switch screen.** It executes 0/32 DEV calls versus the MoE’s 32/32 on the same episodes. Neither trunk finishes either episode successfully. Every dense DEV response begins with a JSON fence (19 unclosed, 13 closed); the unchanged pilot4 parser rejects all 32. No prompt/parser rescue or candidate selection.', '',
 f'The disclosed JavaScript second look passes **{j["success"]}/32** hidden-test tasks versus the MoE’s **16/32**. This is descriptive across trunks/precisions/backends, not an isolated architecture effect. No fit or tuning; only DEV00/01 gold events and the check40k authored bank. No benchmark access.', '',
 '| Matched R episodes | Dense FP8 | MoE bf16, committed pilot4 |','|---|---:|---:|',
 '| Executed responses | 0/32 (0%) | 32/32 (100%) |','| Caps | 0/32 | 0/32 |','| Final success | 0/2 | 0/2 |',
 f'| Round-0 indent compliance (executed) | {d["round0_indent"]["compliant"]}/2 | {sum(e["metrics"]["round0_indent"]["compliant"] for e in b)}/2 |',
 '| Violations language/style/format/process | 0/0/32/0 | 0/30/10/17 |','| Breakage | 32 | 0 |','',
 'Dense zero style/process counts do not establish compliance: no code ran and the rejected envelopes provide no valid reports. Empty executed-trait denominators are unavailable evidence. Same original pilot4 indentation tasks, 512-token cap, retained history, gold R events, renderer and checker; no later lexical swap or SLAB-2 changes.', '',
 '| Dense measurement | DEV R (2 streams) | JavaScript (4 streams) |','|---|---:|---:|',
 f'| Decode tok/s per stream (pooled) | {d["decode_tok_s"]:.3f} | {jsdecode:.3f} |',
 f'| Schedule aggregate output tok/s | {d["aggregate_tok_s"]:.3f} | {jsagg:.3f} |',
 f'| Seconds/call (latency) | {d["seconds_per_call"]:.3f} | {result["js"]["seconds_per_call"]:.3f} |',
 f'| Schedule seconds | {d["schedule_seconds"]:.3f} | {j["seconds"]:.3f} |',
 f'| Caps | 0 | {result["js"]["caps"]} |','',
 'Aggregate rates include HTTP, barriers, tools/checking and long tails; output totals include EOS. Decode rates exclude first-chunk tokens and prefill. Concurrent call latencies are not summed as GPU cost. DEV has only two independent episodes; JS uses four workers. MoE matched-episode decode rates were 9.403/9.806 tok/s and latencies 19.519/20.055s, within pilot4’s different C4 schedule (24.731 aggregate tok/s across all arms); this is not a matched scheduling speed experiment.', '',
 '**Larger-test cost sensitivity (R/N ×64 + O/T ×16 = 160 episodes).** All-arm costs are unmeasured. These extrapolations assign every arm the larger observed R episode token total, scale linearly to 16 or 32 rounds, add 25% serving margin plus one measured startup. Longer contexts and O recovery can cost more. The registered conservative long-episode comparison is the 32-round row; 16 rounds are an optimistic sensitivity, not a complete forecast.', '',
 '| R-like rounds/episode | Rate basis | FP8 GPU-h | bf16 estimate GPU-h |','|---:|---|---:|---:|']
 for p in projections:rows.append(f'| {p["rounds"]} | {p["rate_basis"]} | {p["fp8_hours"]:.2f} | {p["bf16_estimate_hours"]:.2f} |')
 rows += ['', 'bf16 estimate uses **2× FP8 serving time** as a weight-bandwidth proxy, not a measurement or guaranteed bound. Startup is held fixed; native bf16 kernels and actual cache costs remain unqualified. The JS C4 rate is a cross-workload sensitivity, not measured C4 DEV performance. These are incremental future-run estimates; they exclude sunk prior pilots and unmeasured HF recovery. No complete ≤12 GPU-h claim is established. The failed execution criterion independently decides STAY.', '',
 f'**Feasibility and resources.** Qualified image digest `sha256:3dbe092ec5b2cef63b6104d33fa75d6ce53a7870962529ada69f78bbbc38e776`, vLLM 0.19.2rc1.dev134+gfe9c3d6c5, Transformers 5.6.0. CPU registry supported `Qwen3_5ForConditionalGeneration` and both configs; native FP8 loaded on GB10. Text-only fallback unneeded. The example `python` entrypoint was absent; rerun with `python3` passed. Both CPU probes used no GPU device and network disabled. Original errors and registry output are retained.', '',
 f'Startup **{startup:.3f}s**; total container-held **{life["gpu_held_seconds"]:.3f}/2400s** including startup, inference, idle and cleanup. Own container removed and RUNNING.flag deleted; Brian’s pid 2705 was not signaled. No checkpoint downloaded, no disk approval needed, no push. STAY is a screen result under this renderer/backend, not evidence the dense trunk is generally inferior.', '',
 'Exact commands and container exit/removal receipts: [attempts.json](attempts.json). EOS mapping uses local generation config `[248046,248044]` (the text config names 248044); both follow the qualification client’s EOS accounting. JavaScript preserves check40k prompts, thinking-disabled template, cap 768 and all four hidden Node tests per task. Prompt/response/token journals retained; no hidden tests supplied in prompts.', '',
 'A first audit rejected live source drift from a concurrent session. The successful audit extracts `src/` and `scripts/` from `184cb321` into a temporary directory, checks the frozen hashes, and exactly reproduces all 32 saved prompts, controller states, executions and outcomes. No live files were restored and no inference repeated. Recipe frozen at `184cb321` before inference. [registration.json](registration.json) pins committed source hashes; unrelated dirty SLAB-2 files were unused. [audit.json](audit.json) verifies 64 HTTP token/EOS/cap records, 32 exact DEV consumer replays and 32 hidden-test rescoring/prompt replays. [cpu-smoke.log](cpu-smoke.log): 32 reference calls through the new-tokenizer consumer. [summary.json](summary.json) contains per-episode violations, indent evidence and all timing/projection arithmetic. [artifact-manifest.json](artifact-manifest.json) pins compact records (each ≤10 MB); generated workspace/journal duplicates stay local.', '']
 (OUT/'README.md').write_text('\n'.join(rows))
if __name__=='__main__':main()
