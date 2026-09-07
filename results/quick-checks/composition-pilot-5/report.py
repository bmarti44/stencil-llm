"""Produce reviewable summary from preserved same-run pilot measurements."""
import collections
import importlib.util
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('pilot5_owner',HERE/'run.py')
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)

def main():
    phase='main'
    summary=json.loads((HERE/'main-summary.json').read_text())
    life=json.loads((HERE/'lifecycle.json').read_text())
    receipts=[]
    for p in sorted((HERE/'receipts').rglob('*.json')):
        receipt=json.loads(p.read_text())
        raw=HERE/'local/http'/(receipt['key']+'.json')
        receipt['http_sha256']=r.hashlib.sha256(raw.read_bytes()).hexdigest()
        receipts.append(receipt)
    with (HERE/'journals-index.jsonl').open('w') as f:
        for item in receipts: f.write(json.dumps(item,separators=(',',':'))+'\n')
    gate=[x for x in receipts if x['key'].startswith('gate-')]
    gate_wall=max(x['timing']['ended'] for x in gate)-min(x['timing']['started'] for x in gate)
    raw_projection=summary['projected_gpu_hours']
    # Conservative over-allocation: charge all remaining held wall, including
    # cleanup and gate preparation, to main lanes; remove only actual gate span.
    charged=sum(g['seconds'] for g in summary['groups'])
    overhead=max(0,life['gpu_held_seconds']-summary['load_seconds']-gate_wall-charged)
    complete_lanes=sum(g['lanes'] for g in summary['groups'])
    costs={a:v+overhead/complete_lanes for a,v in summary['lane_seconds'].items()} if complete_lanes else {}
    if all(a in costs for a in 'RNT'):
        corrected=(summary['load_seconds']+1.25*(64*(costs['R']+costs['N'])+16*(costs.get('O',costs['R'])+costs['T'])))/3600
        summary.update(group_only_projected_gpu_hours=raw_projection,projected_gpu_hours=corrected,lane_seconds=costs)
        failures=[x for x in summary['failures'] if x!='registered cost unmeasured or >12h']
        if not 0<corrected<=12: failures.append('registered cost >12h')
        summary.update(failures=failures,reading='INELIGIBLE' if failures else 'ELIGIBLE')
    summary.update(gpu_held_seconds=life['gpu_held_seconds'],determinism_gate_wall_seconds=gate_wall,
                   conservative_overhead_seconds=overhead,overhead_definition='All held time minus load, gate HTTP span, and measured groups, allocated equally to complete main lanes (includes cleanup).')
    references={e.episode_id:sum(len(r.s.qwen_encode(r.s.reference(e,i))) for i in range(16)) for e in r.s.bank()}
    rows=[json.loads(line) for line in (HERE/'main-records.jsonl').read_text().splitlines()]
    summary['written_file_floor_sensitivity']={k:dict(passed=sum(x['file_written'] and x['outcome']['satisfied'][k] for x in rows if x['arm']=='T' and x['outcome']['applicable'][k]),total=v['total']) for k,v in summary['floor']['traits'].items()}
    original={(x['episode_id'],x['turn']):x for x in rows if x['arm']=='R'}
    oracle=[x for x in rows if x['arm']=='O']
    summary['r_o_exact_outputs']=dict(total=len(oracle),exact=sum(all(x[k]==original[x['episode_id'],x['turn']][k] for k in ('output_ids','output','eos','truncated')) for x in oracle))
    for a,v in summary['per_arm'].items():
        v['harness_relapse']=v['relapse']
        v['relapse']={k:dict(numerator=sum(x['file_written'] and x['outcome']['raw_relapse'][k] for x in rows if x['arm']==a),denominator=sum(x['file_written'] and x['outcome']['trait_denominators'][k] for x in rows if x['arm']==a)) for k in r.s.TRAITS}
        for k, counts in v['relapse'].items():
            counts['prior_trait_present_denominator']=sum(x['file_written'] and x['outcome']['trait_denominators'][k] and x['outcome']['prior_trait_present'][k] for x in rows if x['arm']==a)
        lanes={eid:sum(x['output_tokens'] for x in rows if x['arm']==a and x['episode_id']==eid) for eid in references}
        v['lane_output_tokens']=lanes
        v['reference_output_tokens_per_lane']=references
        v['x_factor_vs_reference']=v['output_tokens']/sum(references.values()) if v['calls']==128 else None
        v['execution_categories']=dict(collections.Counter(x['execution'].get('category','written') for x in rows if x['arm']==a))
    summary['cost_scope']='Registered R/N x64 + O/T x16 at fixed C4, startup once, 25% reserve on future lanes; prior development excluded; Q not requested.'
    summary['determinism']=json.loads((HERE/'determinism.json').read_text())
    r.dump(HERE/'summary.json',summary)
    p=summary['projected_gpu_hours']
    lines=['# Composition pilot 5 — '+summary['reading'],'',
           'DEV only; pinned SLAB-2 `9f0c6d27`, qualified invariant vLLM bf16/Triton. User cap **1024**, 16 rounds, fixed same-arm C4 groups. T ran first to freeze its floor before success scoring; then R/N and optional O. No fitting, evaluation-bank or benchmark reads.','',
           '**Failing gates:** '+('; '.join(summary['failures']) or 'none')+'.','',
           '| Arm | Calls /128 | Parsed + written | Caps | Final success /8 | Largest reply | Output tokens | Model/reference x |',
           '|---|---:|---:|---:|---:|---:|---:|---:|']
    for a in 'RNTO':
        v=summary['per_arm'][a];x=v['x_factor_vs_reference']
        lines.append(f"| {a} | {v['calls']} | {v['executed']}/{v['calls']} | {v['caps']}/{v['calls']} | {v['final_success']} | {v['largest_reply']} | {v['output_tokens']} | {x:.3f} |" if x is not None else f"| {a} | {v['calls']} | {v['executed']}/{v['calls']} | {v['caps']}/{v['calls']} | {v['final_success']} | {v['largest_reply']} | {v['output_tokens']} | unmeasured |")
    lines+=['','Execution requires a parsed trailer and an actual file write. Syntax/parse-depth attempts are excluded even though the pinned executor labels them executed. Every cap is a failed attempt. Each R/N/T arm must independently reach 90% execution and at most 2% caps.','',
            'T-floor table (at least 50% applicable T observations must satisfy the trait):','',
            '| Trait / kind | Frozen T satisfied / applicable | Written-file-only sensitivity | Enters success | Episodes with substitution/relapse denominator |','|---|---:|---:|---|---:|']
    if summary['floor']:
        for k,v in summary['floor']['traits'].items():
            strict=summary['written_file_floor_sensitivity'][k]
            lines.append(f"| {k} / {r.s.TRAITS[k]} | {v['passed']}/{v['total']} | {strict['passed']}/{strict['total']} | {v['eligible']} | {len(v['opportunity_episodes'])} |")
    lines+=['','Only indent/style and delivery/process count toward the two-substitution-kind gate; omission traits remain floor-gated for success and descriptive for relapse. Floor was frozen from all128 T records before success scoring.','',
            '| Arm | Trait / kind | Relapse / denominator | Of denominator, prior trait present |','|---|---|---:|---:|']
    for a in 'RNTO':
        for k,v in summary['per_arm'][a]['relapse'].items():
            lines.append(f"| {a} | {k} / {r.s.TRAITS[k]} | {v['numerator']}/{v['denominator']} | {v['prior_trait_present_denominator']} |")
    lines+=['','Relapse denominators above require parsed-and-written files, consistently with the user execution definition. The pinned checker also counts parsed syntax-error attempts; those original counts remain in summary.harness_relapse and untouched per-round checks. Zero denominators are unmeasured witnesses. Per-round prior-trait flags, applicability, raw relapse and tolerances are preserved in the records.','',
            f"Registered-run projection: **{p:.3f} GPU-h**." if p else 'Registered-run projection: **unmeasured**.',
            f"O cost source: {summary['O_cost_source']}. Fixed C4 grouping must be reused. Startup {summary['load_seconds']:.3f}s; conservative extra main overhead {overhead:.3f}s. Formula `(load + 1.25*(64*(R+N)+16*(O+T)))/3600`, where each cost is mean group-wall allocation per episode. Prior pilot spend is excluded; Q is outside this user-scoped run.",
            f"GPU held **{life['gpu_held_seconds']:.3f}/5400s**, including startup, replay and cleanup. Pre-run replay HTTP span {gate_wall:.3f}s; all8 output-token/EOS/cap sequences match in forward and reverse C4 order."]
    if p and 12<p<=15:
        lines+=['',f"12-round proportional diagnostic: {p*.75:.3f}h (not a measured validation).",(HERE/'fallback.json').read_text() if (HERE/'fallback.json').exists() else 'See fallback artifacts for the fresh frozen12-round validation.']
    elif p and p>15: lines+=['','Projection exceeds15h: registered stop; no fallback or arm shrinking.']
    else: lines+=['','The (12,15]h fallback condition was not triggered.']
    lines+=['','The cap decision is the user-authorized 1024 bet documented in fable H2; later CPU defaults use2048. Blocking parser/repair fixes and N1/N2 transport guards were already committed. This pilot does not measure Q, a learned controller, HF hidden recovery, or held-out performance.','',
            'Artifacts: [registration](registration.md), [summary](summary.json), [same-run records](main-records.jsonl), [HTTP hash/timing index](journals-index.jsonl), [local journal hashes](local-hashes.json), [server log](server.log), [CPU audit](audit.json). Raw HTTP payloads and loop journals remain local and out of git. Own container stopped/removed; flag removed; no host process signals or push.']
    lines+=['',f"DEV O/R exact output text, token IDs, EOS and cap status: {summary['r_o_exact_outputs']['exact']}/{summary['r_o_exact_outputs']['total']}. This is DEV gold-event equivalence, not learned-controller evidence.",'','Execution categories (each row sums to attempted calls):']
    for a in 'RNTO': lines.append(f"- {a}: {json.dumps(summary['per_arm'][a]['execution_categories'],sort_keys=True)}")
    (HERE/'README.md').write_text('\n'.join(lines)+'\n')

if __name__=='__main__': main()
