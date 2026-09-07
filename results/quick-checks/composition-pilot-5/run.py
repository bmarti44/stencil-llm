"""User-scoped pilot orchestration; pinned science source, bounded owned server."""
import concurrent.futures as cf
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time
import traceback
from urllib.request import Request, urlopen

ROOT = Path('/home/bmarti44/stencil-llm')
OUT = ROOT / 'results/quick-checks/composition-pilot-5'
PIN = Path('/tmp/stencil-pilot5-pinned')
SHA = '9f0c6d27f32815010c81a02d3959102459c55e8f'
sys.path[:0] = [str(PIN / 'src'), str(PIN / 'scripts')]
import composition_pilot5 as d
s = d.s
s.REPLY_CAP = 1024
s.SYSTEM_PROMPT = s.SYSTEM_PROMPT.replace('2048', '1024')
LOCAL = OUT / 'local'
END = float('inf')
LOCK = threading.Lock()
TIMINGS = {}

def dump(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2) + '\n')

def hashobj(x):
    return hashlib.sha256(json.dumps(x, separators=(',', ':'), sort_keys=True).encode()).hexdigest()

def cmd(args):
    p = subprocess.run(args, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if p.returncode:
        raise RuntimeError(f'{args[:3]}: {p.stdout}')
    return p.stdout.strip()

def factory(e, arm, turn, phase='main'):
    key = f'{phase}/{e.episode_id}/{arm}/{turn}'
    def transport(payload):
        if time.time() >= END - 180:
            raise TimeoutError('cooperative stop-new-work boundary')
        begin = time.time()
        receipt = dict(key=key, started=begin, request=payload)
        path = LOCAL / 'http' / (key + '.json')
        dump(path, receipt)
        try:
            req = Request('http://127.0.0.1:18085/v1/completions', data=json.dumps(payload).encode(), headers={'Content-Type':'application/json'})
            with urlopen(req, timeout=min(1200, END-time.time()-60)) as r:
                receipt['response'] = json.load(r)
            return receipt['response']
        except Exception as exc:
            receipt['error'] = repr(exc)
            raise
        finally:
            receipt['ended'] = time.time()
            receipt['seconds'] = receipt['ended'] - begin
            dump(path, receipt)
            with LOCK:
                TIMINGS[key] = {k:receipt[k] for k in ('started','ended','seconds')}
    base = d.VLLMDecoder('http://127.0.0.1:18085/v1', '/model', transport)
    def decode(rendered):
        result = base(rendered)
        receipt = dict(key=key, prompt_sha256=hashobj(list(rendered.prompt_ids)),
                       output_sha256=hashobj([list(result.output_ids), result.eos]),
                       text_sha256=hashlib.sha256(result.text.encode()).hexdigest() if hasattr(result,'text') else None,
                       timing=TIMINGS[key])
        dump(OUT / 'receipts' / (key+'.json'), receipt)
        return result
    return decode

def rows_for(phase):
    rows = []
    for p in sorted((LOCAL / phase).glob('slab2-dev-*/*/raw.jsonl')):
        for line in p.read_text().splitlines():
            row = json.loads(line)
            key = f'{phase}/{row["episode_id"]}/{row["arm"]}/{row["turn"]}'
            row['output_sha256'] = hashobj([row['output_ids'],row['eos']])
            row['text_sha256'] = hashlib.sha256(row['output'].encode()).hexdigest()
            row['timing'] = TIMINGS.get(key)
            row['file_written'] = bool(row['execution']['executed'] and row['execution'].get('category') not in {'syntax_error','parse_depth','file_write'})
            rows.append(row)
    with (OUT / f'{phase}-records.jsonl').open('w') as f:
        for row in rows:
            f.write(json.dumps(row,separators=(',',':'))+'\n')
    return rows

def summarize(phase, groups, load, n):
    rows = rows_for(phase)
    byarm = {a:[r for r in rows if r['arm']==a] for a in 'TRNO'}
    floor = s.freeze_t_floor(byarm['T'],n) if len(byarm['T'])==8*n else None
    if floor:
        dump(OUT / f'{phase}-floor.json',floor)
        scored = d.rescore(rows,floor)
    else:
        scored = rows
    costs = {a:sum(g['seconds'] for g in groups if g['arm']==a)/8 for a in 'TRNO' if sum(g['lanes'] for g in groups if g['arm']==a)==8}
    projection = None
    if all(a in costs for a in 'TRN'):
        projection = (load+1.25*(64*(costs['R']+costs['N'])+16*(costs.get('O',costs['R'])+costs['T'])))/3600
    perarm = {}
    for a, rr in byarm.items():
        perarm[a] = dict(calls=len(rr), executed=sum(r['file_written'] for r in rr), caps=sum(r['truncated'] for r in rr),
                        final_success=sum(r['outcome']['success'] is True for r in scored if r['arm']==a and r['turn']==n-1),
                        output_tokens=sum(r['output_tokens'] for r in rr),
                        largest_reply=max([r['output_tokens'] for r in rr],default=0),
                        relapse={k:dict(numerator=sum(r['outcome']['raw_relapse'][k] for r in rr),denominator=sum(r['outcome']['trait_denominators'][k] for r in rr)) for k in s.TRAITS},
                        tolerances={k:sum(k in r['execution']['tolerances'] for r in rr) for k in sorted({k for r in rr for k in r['execution']['tolerances']})})
    kinds = sorted({s.TRAITS[k] for k in ('indent','delivery') if floor and floor['traits'][k]['eligible'] and len(floor['traits'][k]['opportunity_episodes'])>=2})
    fails=[]
    for a in 'RNT':
        v=perarm[a]
        if v['calls']!=8*n: fails.append(a+' incomplete')
        if v['executed']/(8*n)<.9: fails.append(a+' executed<90%')
        if v['caps']/max(1,v['calls'])>.02: fails.append(a+' caps>2%')
    if len(kinds)<2: fails.append('T floor substitution kinds<2')
    if perarm['R']['final_success']<5: fails.append('R final<5/8')
    if projection is None or not 0<projection<=12: fails.append('registered cost unmeasured or >12h')
    summary=dict(phase=phase,n_rounds=n,reading='INELIGIBLE' if fails else 'ELIGIBLE',failures=fails,per_arm=perarm,
                 floor=floor,substitution_kinds=kinds,lane_seconds=costs,groups=groups,load_seconds=load,
                 projected_gpu_hours=projection,O_cost_source='measured' if 'O' in costs else 'R gold-equivalent proxy',
                 fallback_proportional_hours=projection*.75 if projection else None)
    dump(OUT / f'{phase}-summary.json',summary)
    return summary

def run_phase(phase,n,load):
    episodes=s.bank(n_rounds=n)
    groups=[]
    for arm in 'TRNO':
        if arm=='O':
            rwall=sum(g['seconds'] for g in groups if g['arm']=='R')
            if time.time()+1.25*rwall+180>=END:
                break
        for offset in (0,4):
            if time.time()>=END-180: return summarize(phase,groups,load,n)
            started=time.time()
            errors=[]
            with cf.ThreadPoolExecutor(4) as pool:
                futs=[pool.submit(d.run_lane,LOCAL/phase/e.episode_id/arm,e,arm,lambda e,a,i:factory(e,a,i,phase),n_rounds=n) for e in episodes[offset:offset+4]]
                for f in futs:
                    try: f.result()
                    except Exception as exc: errors.append(repr(exc))
            groups.append(dict(arm=arm,offset=offset,lanes=4 if not errors else 0,seconds=time.time()-started,errors=errors))
            summary=summarize(phase,groups,load,n)
            print(json.dumps(dict(phase=phase,arm=arm,offset=offset,elapsed=time.time()-START,counts={a:v['calls'] for a,v in summary['per_arm'].items()},errors=errors)),flush=True)
            if errors: return summary
    return summarize(phase,groups,load,n)

def gate():
    episodes=s.bank()
    prompts={}
    class Captured(Exception): pass
    for e in episodes:
        def capture(e,a,i):
            def decode(rendered):
                prompts[e.episode_id]=rendered
                raise Captured()
            return decode
        try: d.run_lane(LOCAL/'capture'/e.episode_id/'R',e,'R',capture)
        except Captured: pass
    answers={}
    for label,order in [('forward',list(range(8))),('reverse',list(reversed(range(8))))]:
        for off in (0,4):
            ids=order[off:off+4]
            with cf.ThreadPoolExecutor(4) as pool:
                futs={i:pool.submit(factory(episodes[i],'R',0,'gate-'+label),prompts[episodes[i].episode_id]) for i in ids}
                for i,f in futs.items():
                    r=f.result()
                    answers[label,i]=dict(ids=list(r.output_ids),eos=r.eos,truncated=r.truncated)
    mismatches=[i for i in range(8) if answers['forward',i]!=answers['reverse',i]]
    dump(OUT/'determinism.json',dict(prompts=8,concurrency=4,forward=list(range(8)),reverse=list(reversed(range(8))),mismatches=mismatches,outputs={f'{k[0]}-{k[1]}':v for k,v in answers.items()}))
    if mismatches: raise RuntimeError('determinism gate failed')

START=0

def main():
    global START,END
    assert cmd(['git','-C',str(PIN),'rev-parse','HEAD'])==SHA
    cmd(['git','-C',str(PIN),'diff','HEAD','--exit-code'])
    assert str(s.__file__).startswith(str(PIN))
    if '--cpu-smoke' in sys.argv:
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            e=s.generate_episode('dev',0)
            lane=d.run_lane(Path(tmp)/'lane',e,'R',d.stub_factory)
            assert len(lane['records'])==16 and all(r['execution']['executed'] for r in lane['records'])
        print('CPU pinned lane/cap override smoke PASS');return
    with (ROOT/'.stencil-owned-pids').open('a') as f: f.write(str(os.getpid())+'\n')
    with (ROOT/'.review.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        others=list((ROOT/'results/quick-checks').glob('*/RUNNING.flag'))
        if others: raise RuntimeError(f'Other flags: {others}')
        gpu=cmd(['nvidia-smi','--query-compute-apps=pid,process_name','--format=csv,noheader'])
        if any(line.strip() and not line.strip().startswith('2705,') for line in gpu.splitlines()): raise RuntimeError('Other GPU compute: '+gpu)
        START=time.time();END=START+5400
        with (OUT/'RUNNING.flag').open('x') as f: json.dump(dict(pid=os.getpid(),start=START,deadline=END),f)
    name=f'stencil-pilot5-{int(START)}'
    args=json.loads((ROOT/'results/quick-checks/vllm-qual/attempts.json').read_text())[0]['command']
    args[args.index('--name')+1]=name
    args[args.index('-p')+1]='127.0.0.1:18085:8000'
    dump(OUT/'launch.json',dict(command=args,pinned_sha=SHA,source=s.__file__,system_sha256=hashobj(s.SYSTEM_PROMPT),cap=1024,start=START))
    launched=False
    try:
        container=cmd(args);launched=True
        dump(OUT/'container.json',dict(name=name,id=container))
        while time.time()<END-180:
            if cmd(['docker','inspect','--format','{{.State.Status}}',name])!='running': raise RuntimeError('server exited at startup')
            try:
                with urlopen('http://127.0.0.1:18085/health',timeout=2) as r:
                    if r.status==200: break
            except Exception: pass
            time.sleep(3)
        else: raise TimeoutError('startup deadline')
        load=time.time()-START
        dump(OUT/'ready.json',dict(load_seconds=load,ready=time.time()))
        print(f'Server ready after {load:.3f}s',flush=True)
        gate();print('Determinism 8/8 exact',flush=True)
        summary=run_phase('main',16,load)
        projection=summary['projected_gpu_hours']
        if projection and 12<projection<=15:
            estimate=sum(g['seconds'] for g in summary['groups'] if g['arm'] in 'RNT')*.75*1.25
            if time.time()+estimate+180<END:
                run_phase('fallback',12,load)
            else: dump(OUT/'fallback.json',dict(status='UNVALIDATED: remaining 5400s budget insufficient',estimated_seconds=estimate,remaining_seconds=END-time.time()))
    except Exception:
        (OUT/'error.txt').write_text(traceback.format_exc());raise
    finally:
        if launched:
            stop=cmd(['docker','stop','-t','20',name])
            (OUT/'server.log').write_text(cmd(['docker','logs','--timestamps',name])+'\n')
            remove=cmd(['docker','rm',name])
            dump(OUT/'cleanup.json',dict(name=name,stop=stop,remove=remove))
        dump(OUT/'lifecycle.json',dict(start=START,end=time.time(),gpu_held_seconds=time.time()-START,budget_seconds=5400))
        (OUT/'RUNNING.flag').unlink(missing_ok=True)
        manifest={str(p.relative_to(OUT)):dict(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in LOCAL.rglob('*') if p.is_file()}
        dump(OUT/'local-hashes.json',manifest)

if __name__=='__main__': main()
