"""Recheck source boundary, complete outputs, counters, arithmetic and cleanup."""
import collections, hashlib, json, subprocess
from pathlib import Path
OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[2]
def main():
    def read(name):return json.loads((OUT/name).read_text())
    registration=read('registration.json');source=ROOT/'results/quick-checks/composition-pilot/records.jsonl'
    assert hashlib.sha256(source.read_bytes()).hexdigest()==registration['source_sha256']
    assert hashlib.sha256((OUT/'frozen.json').read_bytes()).hexdigest()==registration['frozen_sha256']
    refs=[json.loads(x) for x in source.read_text().splitlines()];refs=[x for x in refs if x['oracle_checker_results'][0]['mode']=='sequential']
    frozen=read('frozen.json');assert len(refs)==len(frozen)==64
    for r,f in zip(refs,frozen):
        d=r['oracle_checker_results'][0];assert d['episode']=='slab-dev-00'
        assert f['prompt']==r['rendered_token_ids'] and f['arm']==d['arm'] and f['round']==d['round']
        assert f['output_ids']==r['output_token_ids']+([r['eos']] if r['eos'] is not None else [])
    rows=[json.loads(x) for x in (OUT/'records.jsonl').read_text().splitlines()]
    assert len(rows)==256 and len({(r['pass_name'],r['index']) for r in rows})==256
    completed=[r for r in rows if r['complete']];unstarted=[r for r in rows if not r['complete']]
    assert len(completed)==201 and len(unstarted)==55
    for r in unstarted:
        assert r['pass_name']=='b8' and not r['output_token_ids'] and not r['chunks'] and 'no new call' in r['error']
    for r in completed:
        chunks=[c for chunk in r['chunks'] for c in chunk['response'].get('choices',[])]
        prompts=[c['prompt_token_ids'] for c in chunks if c.get('prompt_token_ids') is not None]
        assert prompts==[frozen[r['index']]['prompt']]
        ids=[tok for c in chunks for tok in c['token_ids']]
        assert ids==r['output_token_ids'] and ids and all(type(t) is int for t in ids)
        assert r['usage']['completion_tokens']==len(ids)<=512 and r['usage']['prompt_tokens']==len(prompts[0])
        assert r['first_chunk_tokens']==1 and r['decode_tokens']==len(ids)-1 and r['decode_seconds']>0
        if r['finish_reason']=='stop':assert ids[-1] in [151645,151643]
        else:assert r['finish_reason']=='length' and len(ids)==512
        assert not any(t in [151645,151643] for t in ids[:-1])
    summary=read('summary.json')
    assert summary['status']=='QUALIFIED' and summary['determinism_pass'] and not summary['b1_speed_pass'] and summary['b4_budget_pass']
    assert summary['comparisons']['hf_vs_b1']['diverged']==5
    assert summary['comparisons']['b1_vs_repeat']['paired']==summary['comparisons']['b1_vs_b4']['paired']==64
    assert summary['comparisons']['b1_vs_repeat']['diverged']==summary['comparisons']['b1_vs_b4']['diverged']==0
    for p in summary['passes']:
        rr=[r for r in completed if r['pass_name']==p['name']];m=p['metrics_delta']
        assert p['complete']==len(rr)==m['vllm:request_success_total']==m['vllm:request_prefill_time_seconds_count']
        assert p['tokens']==sum(len(r['output_token_ids']) for r in rr)==m['vllm:generation_tokens_total']
        assert sum(len(r['prompt_token_ids']) for r in rr)==m['vllm:prompt_tokens_total']
    q=summary['projection'];weights=dict(R=64,N=64,T=16,O=16)
    fixed=q['prior_spent_seconds']+q['qualification_seconds']+q['reload_seconds']
    b1=(fixed+1.25*sum(weights[a]*q['b1_arm_episode_seconds'][a] for a in weights))/3600
    assert abs(b1-q['b1_gpu_hours'])<1e-9 and q['b1_gpu_hours']>12>q['b4_gpu_hours']
    workload=sum(weights[r['arm']]*len(r['output_token_ids']) for r in completed if r['pass_name']=='b4')
    overhead=dict(R=0.6307437069827984,N=0.5111739080014104,T=0.5013349559960716,O=0.4857189519814824)
    rate=next(p['aggregate_tok_s'] for p in summary['passes'] if p['name']=='b4')
    b4=(fixed+1.25*(workload/rate+sum(weights[a]*overhead[a] for a in weights)))/3600
    assert workload==q['b4_weighted_output_tokens'] and abs(b4-q['b4_gpu_hours'])<1e-9
    assert summary['gpu_held_seconds']<2700
    assert not (OUT/'RUNNING.flag').exists() and not (OUT/'READY').exists()
    names=subprocess.check_output(['docker','ps','-a','--format','{{.Names}}'],text=True).splitlines()
    for name in [read('initial-container.json')['name'],read('container.json')['name']]:assert name not in names
    samples=[json.loads(x) for x in (OUT/'scheduler-samples.jsonl').read_text().splitlines()]
    occupancy={}
    for p in summary['passes']:
        s=[x for x in samples if p['start']<=x['time']<=p['end']]
        occupancy[p['name']]={key:max((float(g.split()[-1]) for x in s for g in x['gauges'] if g.startswith('vllm:'+key+'{')),default=None) for key in ['num_requests_running','num_requests_waiting']}
    output=dict(passed=True,completed_api_calls=len(completed),unsubmitted_deadline_rows=len(unstarted),source_cases=64,first_chunk_tokens=1,stop_counts=dict(collections.Counter(r['finish_reason'] for r in completed)),sampled_scheduler_maxima=occupancy,cleanup_verified=True,source_and_frozen_hashes_verified=True,raw_metrics_counts_match=True)
    (OUT/'audit.json').write_text(json.dumps(output,indent=2));print(json.dumps(output,indent=2))
if __name__=='__main__':main()
