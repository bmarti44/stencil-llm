"""CPU-only analysis of recorded qualification outputs; no new inference."""
import collections, hashlib, json, re
from pathlib import Path
OUT=Path(__file__).resolve().parent

def read(name, default=None):
    p=OUT/name
    return json.loads(p.read_text()) if p.exists() else default

def difference(a,b):
    return next((i for i in range(max(len(a),len(b))) if i>=len(a) or i>=len(b) or a[i]!=b[i]),None)

def metricfile(name):
    p=OUT/name
    d=collections.defaultdict(float)
    if p.exists():
        for line in p.read_text().splitlines():
            if line.startswith('#') or not line.strip():continue
            parts=line.split()
            if len(parts)==2:
                key=parts[0].split('{')[0]
                try:d[key]+=float(parts[1])
                except ValueError:pass
    return d

def main():
    frozen=read('frozen.json'); path=OUT/'records.jsonl'
    rows=[json.loads(s) for s in path.read_text().splitlines()] if path.exists() else []
    groups=collections.defaultdict(dict)
    for r in rows:
        assert r['index'] not in groups[r['pass_name']]
        assert r['prompt_token_ids']==frozen[r['index']]['prompt']
        groups[r['pass_name']][r['index']]=r
    comparisons={}
    for name,reference in [('hf_vs_b1','hf'),('b1_vs_repeat','b1_repeat'),('b1_vs_b4','b4'),('b1_vs_b8','b8')]:
        pairs=[]
        for i,r in groups['b1_first'].items():
            ref=frozen[i]['output_ids'] if reference=='hf' else groups[reference].get(i,{}).get('output_token_ids')
            ok=reference=='hf' or groups[reference].get(i,{}).get('complete')
            if ref is not None and r['complete'] and ok:
                pos=difference(ref,r['output_token_ids'])
                pairs.append(dict(index=i,arm=r['arm'],round=r['round'],first_divergence=pos,reference_length=len(ref),actual_length=len(r['output_token_ids']),reference_token=ref[pos] if pos is not None and pos<len(ref) else None,actual_token=r['output_token_ids'][pos] if pos is not None and pos<len(r['output_token_ids']) else None))
        comparisons[name]={'paired':len(pairs),'diverged':sum(x['first_divergence'] is not None for x in pairs),'cases':pairs}
    passes=[]
    for p in read('passes.json',[]):
        name=p['name'];g=list(groups[name].values());m0=metricfile(name+'-before.prom');m1=metricfile(name+'-after.prom');delta={k:m1[k]-m0[k] for k in m1 if not k.endswith('_created') and not k.endswith('_bucket')}
        subset=[r for r in g if 5000<=len(r['prompt_token_ids'])<=11050 and r['complete']]
        p.update(aggregate_tok_s=p['tokens']/p['wall_seconds'] if p['tokens'] else None,aggregate_scope='full64' if p['complete']==64 else 'partial diagnostic only',decode_tok_s_5k_11k=sum(r['decode_tokens'] for r in subset)/sum(r['decode_seconds'] for r in subset) if subset and sum(r['decode_seconds'] for r in subset) else None,context_subset_n=len(subset),metrics_delta=delta)
        p['prefix_cache_hit_rate']=delta.get('vllm:prefix_cache_hits_total',0)/delta['vllm:prefix_cache_queries_total'] if delta.get('vllm:prefix_cache_queries_total') else None
        prefill_time=delta.get('vllm:request_prefill_time_seconds_sum',0)
        p['fresh_prefill_tokens']=delta.get('vllm:request_prefill_kv_computed_tokens_sum')
        p['fresh_prefill_tok_s']=p['fresh_prefill_tokens']/prefill_time if prefill_time and p['fresh_prefill_tokens'] is not None else None
        p['prefill_request_seconds']=prefill_time
        p['prefill_rate_semantics']='fresh computed KV tokens / summed per-request prefill-phase seconds; concurrency sums overlap, not GPU kernel time'
        passes.append(p)
    spent=read('initial-lifecycle.json',{}).get('gpu_held_seconds',0)+read('lifecycle.json',{}).get('gpu_held_seconds',0)
    deterministic=all(comparisons[k]['paired']==64 and comparisons[k]['diverged']==0 for k in ['b1_vs_repeat','b1_vs_b4'])
    b1=[p for p in passes if p['name'] in ['b1_first','b1_repeat']]
    speed=bool(len(b1)==2 and all(p['complete']==64 and p['decode_tok_s_5k_11k'] is not None and p['decode_tok_s_5k_11k']>=20 for p in b1))
    projection={}
    weights=dict(R=64,N=64,O=16,T=16)
    overhead=dict(R=0.6307437069827984,N=0.5111739080014104,T=0.5013349559960716,O=0.4857189519814824)
    attempts=read('attempts.json',[])
    loads=[a['ready_at']-a['started'] for a in attempts if 'ready_at' in a]
    reload=max(loads) if loads else None
    prior=5385.346+1362.257
    fixed=prior+spent+(reload or 0)
    if len(b1)==2 and all(p['complete']==64 for p in b1):
        costs={a:max(sum(r['wall_seconds'] for r in groups[p['name']].values() if r['arm']==a) for p in b1)+overhead[a] for a in weights}
        projection['b1_arm_episode_seconds']=costs
        projection['b1_gpu_hours']=(fixed+1.25*sum(weights[a]*costs[a] for a in weights))/3600
    bp=next((p for p in passes if p['name']=='b4' and p['complete']==64),None)
    if bp:
        totals={a:sum(len(r['output_token_ids']) for r in groups['b4'].values() if r['arm']==a) for a in weights}
        workload=sum(weights[a]*totals[a] for a in weights)
        projection['b4_weighted_output_tokens']=workload
        projection['b4_gpu_hours']=(fixed+1.25*(workload/bp['aggregate_tok_s']+sum(weights[a]*overhead[a] for a in weights)))/3600
    projection.update(prior_spent_seconds=prior,qualification_seconds=spent,reload_seconds=reload,reserve=0.25,scope='frozen16-round diagnostic; excludes unmeasured32-round/controller changes/HF hidden recovery; B4 assumes measured aggregate transfers to nested arm mix')
    b4_speed=projection.get('b4_gpu_hours',float('inf'))<=12
    summary=dict(status='QUALIFIED' if deterministic and (speed or b4_speed) else 'NOT QUALIFIED',determinism_pass=deterministic,b1_speed_pass=speed,comparisons=comparisons,passes=passes,records=len(rows),gpu_held_seconds=spent,projection=projection,b4_budget_pass=b4_speed,near_tie_diagnosis='not measured',notes=['Backend qualification does not certify larger-test eligibility; projection limitations are explicit.','No output records means unmeasured, never zero divergence.'])
    (OUT/'summary.json').write_text(json.dumps(summary,indent=2))
if __name__=='__main__':main()
